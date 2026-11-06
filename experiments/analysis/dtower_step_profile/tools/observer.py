"""Step-breakdown hook for T-2026-11-06-dtower-step-profile, loaded through TOWER_SEARCH_OBSERVER.

``scripts/tower_search_common.load_observer`` imports this file when the environment names
it; unset, the search scripts run as before. No file is changed: the hooks are installed at
run time on objects of the running process (module hooks, instance attributes and module
globals), and they leave the loop's order and every update as they are. They only add
``torch.cuda.synchronize()`` at the boundaries below, read clocks, count frames and
record memory. The detector stops through its own ``TOWER_SEARCH_CONTROL_STEPS``.

One step is the interval from the model's forward being entered at step k to the same at
step k+1 (the same boundary as T-2026-11-06-tower-batch-probe). Inside it, the existing loop
(``util/engine.py`` ``train_one_epoch_acc``) runs, in this order:

    B0 forward entered (outer model's forward pre-hook)                 -- step start
    B1 criterion entered for the first time in the step                  -- forward = B1 - B0
    B2 outer model's forward returned (loss_dict is complete)           -- loss = B2 - B1
    B3 / B4 DataPrefetcher.next() entered / returned (next batch)        -- data wait = B4 - B3
    B5 / B6 accelerator.backward entered / returned                      -- backward = B6 - B5
    B7 optimizer.step returned (clipping and the norm log are in B6..B7) -- optimizer = B7 - B6
    (B2..B3 the loss sum, B4..B5 zero_grad, B7..next B0 the scheduler, the logging reduce
     of loss_dict and its .item(), the metric logger) -- in the rest

At every boundary the CPU clock is read before (``*_pre``) and after a
``torch.cuda.synchronize()``; the synchronised values are the breakdown, the unsynchronised
ones are kept to show what the breakdown would read without the synchronisation.

Inside the loss window, ``HungarianMatcher.forward`` (synchronised at its entry and exit) and
``scipy``'s ``linear_sum_assignment`` (CPU only, not synchronised) are timed as well. With two
processes, explicit ``torch.distributed.all_reduce`` calls outside the logging reduce (the
criterion's box count) and ``accelerator.reduce`` (the logging reduce of loss_dict) are
timed with a synchronisation on each side; DDP's gradient all-reduce runs inside backward and
is not separable here.

``PROBE_NO_LOAD=1`` replaces the prefetcher: the rank's first batch is built once in the main
process from the rank's batch sampler (the DataLoader is never iterated, so no worker starts),
put on the GPU, and handed over again at every step.

Written to ``$PROBE_OUT`` (outside the repo): ``reads_det_pid<PID>.txt`` (every frame the
dataset loaded, from every process) and ``steps_rank<R>.json`` (written once, at the end).
"""
from __future__ import annotations

import json
import os
import time
import types
from pathlib import Path

import torch

OUT = Path(os.environ["PROBE_OUT"])
RANK = os.environ.get("RANK", "0")
NO_LOAD = os.environ.get("PROBE_NO_LOAD") == "1"


def _write(name, value):
    path = OUT / name
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _read(name):
    with open(OUT / f"reads_det_pid{os.getpid()}.txt", "a") as handle:
        handle.write(f"{name}\n")


def _memory(device):
    return {"max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
            "device": str(device), "device_name": torch.cuda.get_device_name(device),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "alloc_conf": os.environ.get("PYTORCH_CUDA_ALLOC_CONF")}


def _checksum(batch):
    images, targets = batch
    total = sum(float(image.double().sum()) for image in images)
    boxes = sum(float(t["boxes"].double().sum()) for t in targets)
    return {"images_sum": total, "boxes_sum": boxes,
            "image_ids": [int(t["image_id"]) for t in targets]}


def install_detector(detector, work):
    import datasets.coco as coco
    import models.matcher.hungarian_matcher as hungarian
    import util.engine as engine
    from util.collate_fn import collate_fn
    from util.misc import to_device

    load_image = coco.CocoDetection.load_image

    def logged_load_image(self, image_name):
        _read(image_name)
        return load_image(self, image_name)

    coco.CocoDetection.load_image = logged_load_image

    steps = []
    state = {"tower": "detector", "rank": RANK, "no_load": NO_LOAD, "steps": steps,
             "oom": None, "error": None, "initial_fetch": None, "cached": None}
    flags = {"in_reduce": False}

    def current():
        return steps[-1] if steps else None

    def mark(record, name):
        before = time.perf_counter()
        torch.cuda.synchronize()
        after = time.perf_counter()
        record[name + "_pre"] = before
        record[name] = after
        return after

    # -- data: the prefetcher the loop constructs (module global of util.engine) ----------
    class TimedPrefetcher(engine.DataPrefetcher):
        def next(self):
            record = current()
            if record is None or "data_start" in record:
                started = time.perf_counter()
                batch = super().next()
                state["initial_fetch"] = {"seconds": time.perf_counter() - started}
                return batch
            mark(record, "data_start")
            batch = super().next()
            mark(record, "data_end")
            return batch

    class CachedBatch:
        def __init__(self, loader, device):
            shard = getattr(loader, "loader", loader)  # the search's LimitedBatches wraps it
            indices = list(next(iter(shard.batch_sampler)))
            started = time.perf_counter()
            batch = collate_fn([shard.dataset[i] for i in indices])
            self.batch = to_device(batch, device)
            torch.cuda.synchronize()
            state["cached"] = {"indices": indices, "build_seconds": time.perf_counter() - started,
                               "at_start": _checksum(self.batch)}
            state["cached_batch"] = self

        def next(self):
            record = current()
            if record is not None and "data_start" not in record:
                mark(record, "data_start")
                mark(record, "data_end")
            return self.batch

    engine.DataPrefetcher = CachedBatch if NO_LOAD else TimedPrefetcher

    # -- matcher: CPU assignment (module global) -------------------------------------------
    assign = hungarian.linear_sum_assignment

    def timed_assign(*args, **kwargs):
        started = time.perf_counter()
        result = assign(*args, **kwargs)
        record = current()
        if record is not None:
            record["lsa_s"] = record.get("lsa_s", 0.0) + time.perf_counter() - started
            record["lsa_calls"] = record.get("lsa_calls", 0) + 1
        return result

    hungarian.linear_sum_assignment = timed_assign

    # -- explicit collectives outside the logging reduce ----------------------------------
    all_reduce = torch.distributed.all_reduce

    def timed_all_reduce(*args, **kwargs):
        record = current()
        if record is None or flags["in_reduce"]:
            return all_reduce(*args, **kwargs)
        before = time.perf_counter()
        torch.cuda.synchronize()
        started = time.perf_counter()
        result = all_reduce(*args, **kwargs)
        torch.cuda.synchronize()
        record["coll_s"] = record.get("coll_s", 0.0) + time.perf_counter() - started
        record["coll_presync_s"] = record.get("coll_presync_s", 0.0) + started - before
        record["coll_calls"] = record.get("coll_calls", 0) + 1
        return result

    torch.distributed.all_reduce = timed_all_reduce

    outer = detector.train_one_epoch_acc

    def probed(**kwargs):
        model, accelerator, optimizer = kwargs["model"], kwargs["accelerator"], kwargs["optimizer"]
        device = accelerator.device
        inner = accelerator.unwrap_model(model)
        import models.bricks.ms_deform_attn as msda
        loader = kwargs["data_loader"]
        state.update({"epoch": kwargs["epoch"], "steps_per_epoch": len(loader),
                      "dataset_frames": len(loader.dataset),
                      "num_workers": loader.num_workers, "pin_memory": loader.pin_memory,
                      "persistent_workers": loader.persistent_workers,
                      "batch_sampler_batch_size": getattr(loader.batch_sampler, "batch_size", None),
                      "mixed_precision": accelerator.mixed_precision,
                      "num_processes": accelerator.num_processes,
                      "ddp_wrapped": type(model).__name__,
                      "sync_batchnorm_modules": sum(isinstance(m, torch.nn.SyncBatchNorm)
                                                    for m in inner.modules()),
                      "ms_deform_attn_cuda_ext_loaded": msda._C is not None,
                      "cuda_device_name": torch.cuda.get_device_name(device)})

        def pre(_module, args):
            targets = args[1]
            record = {"frames": len(targets), "image_ids": [int(t["image_id"]) for t in targets]}
            steps.append(record)
            mark(record, "t0")
            record["wall0"] = time.time()

        def post(_module, _args, _output):
            mark(current(), "loss_end")

        def criterion_pre(_module, _args):
            record = current()
            record["criterion_calls"] = record.get("criterion_calls", 0) + 1
            if "loss_start" not in record:
                mark(record, "loss_start")

        def matcher_pre(_module, _args):
            torch.cuda.synchronize()
            current()["_matcher_t"] = time.perf_counter()

        def matcher_post(_module, _args, _output):
            torch.cuda.synchronize()
            record = current()
            record["matcher_s"] = record.get("matcher_s", 0.0) + time.perf_counter() - record.pop("_matcher_t")
            record["matcher_calls"] = record.get("matcher_calls", 0) + 1

        handles = [model.register_forward_pre_hook(pre), model.register_forward_hook(post),
                   inner.criterion.register_forward_pre_hook(criterion_pre),
                   inner.criterion.matcher.register_forward_pre_hook(matcher_pre),
                   inner.criterion.matcher.register_forward_hook(matcher_post)]

        backward = accelerator.backward
        step = optimizer.step
        reduce = accelerator.reduce

        def timed_backward(*args, **kw):
            record = current()
            mark(record, "bwd_start")
            result = backward(*args, **kw)
            mark(record, "bwd_end")
            return result

        def timed_step(_self, *args, **kw):
            result = step(*args, **kw)
            mark(current(), "opt_end")
            return result

        def timed_reduce(*args, **kw):
            record = current()
            before = time.perf_counter()
            torch.cuda.synchronize()
            started = time.perf_counter()
            flags["in_reduce"] = True
            try:
                result = reduce(*args, **kw)
                torch.cuda.synchronize()
            finally:
                flags["in_reduce"] = False
            record["reduce_s"] = record.get("reduce_s", 0.0) + time.perf_counter() - started
            record["reduce_presync_s"] = record.get("reduce_presync_s", 0.0) + started - before
            record["reduce_tensors"] = sum(1 for _ in _leaves(args[0]))
            return result

        accelerator.backward = timed_backward
        # a bound method: the epoch-0 LinearLR wraps optimizer.step through __self__/__func__
        optimizer.step = types.MethodType(timed_step, optimizer)
        accelerator.reduce = timed_reduce
        torch.cuda.reset_peak_memory_stats(device)
        try:
            return outer(**kwargs)
        except torch.cuda.OutOfMemoryError as exc:
            state["oom"] = {"step": len(steps), "message": str(exc).splitlines()[0], **_memory(device)}
            raise
        except Exception as exc:  # recorded, then re-raised unchanged (ControlComplete too)
            state["error"] = type(exc).__name__
            raise
        finally:
            for handle in handles:
                handle.remove()
            accelerator.backward, optimizer.step, accelerator.reduce = backward, step, reduce
            torch.cuda.synchronize()
            state["end"] = time.perf_counter()
            state["end_wall"] = time.time()
            state["memory"] = _memory(device)
            cached = state.pop("cached_batch", None)
            if cached is not None:
                state["cached"]["at_end"] = _checksum(cached.batch)
            _write(f"steps_rank{RANK}.json", state)

    detector.train_one_epoch_acc = probed


def _leaves(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _leaves(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _leaves(item)
    else:
        yield value

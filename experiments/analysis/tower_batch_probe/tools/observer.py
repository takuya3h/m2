"""Measurement hook for T-2026-11-06-tower-batch-probe, loaded through TOWER_SEARCH_OBSERVER.

``scripts/tower_search_common.load_observer`` imports this file when the environment
names it; unset, the search scripts run as before. Nothing here changes an update: the
hooks only read timestamps, batch sizes, frame names and memory counters, and stop the
phase tower after ``PROBE_STEPS`` micro-steps. The detector tower stops through its own
``TOWER_SEARCH_CONTROL_STEPS``.

Written to ``$PROBE_OUT`` (outside the repo):

- ``reads_<tower>_pid<PID>.txt``: one line per frame the dataset actually loaded, from
  every DataLoader worker (the image file name / frame id).
- ``steps_rank<R>.json``: per step, the wall time at which the step started (detector:
  the model's forward is entered; phase: the loader handed the batch over, after the
  previous step's GPU work was synchronised), the number of frames in the batch, and the
  frame ids; the full epoch's step count; torch's peak allocated / reserved bytes; an
  out-of-memory error with the step it happened in.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import torch

OUT = Path(os.environ["PROBE_OUT"])
RANK = os.environ.get("RANK", "0")


def _write(name, value):
    path = OUT / name
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _read(tower, name):
    with open(OUT / f"reads_{tower}_pid{os.getpid()}.txt", "a") as handle:
        handle.write(f"{name}\n")


def _memory(device):
    return {"max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
            "memory_allocated_bytes": int(torch.cuda.memory_allocated(device)),
            "memory_reserved_bytes": int(torch.cuda.memory_reserved(device)),
            "device": str(device), "device_name": torch.cuda.get_device_name(device),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "alloc_conf": os.environ.get("PYTORCH_CUDA_ALLOC_CONF")}


def install_detector(detector, work):
    import datasets.coco as coco

    load_image = coco.CocoDetection.load_image

    def logged_load_image(self, image_name):
        _read("det", image_name)
        return load_image(self, image_name)

    coco.CocoDetection.load_image = logged_load_image
    outer = detector.train_one_epoch_acc

    def probed(**kwargs):
        model, accelerator = kwargs["model"], kwargs["accelerator"]
        device = accelerator.device
        import models.bricks.ms_deform_attn as msda
        state = {"tower": "detector", "rank": RANK, "epoch": kwargs["epoch"],
                 "steps_per_epoch": len(kwargs["data_loader"]),
                 "dataset_frames": len(kwargs["data_loader"].dataset),
                 "mixed_precision": accelerator.mixed_precision,
                 "num_processes": accelerator.num_processes,
                 "ms_deform_attn_cuda_ext_loaded": msda._C is not None,
                 "step_start": [], "frames": [], "image_ids": [], "oom": None, "error": None}

        def pre(_module, args):
            state["step_start"].append(time.perf_counter())
            targets = args[1]
            state["frames"].append(len(targets))
            state["image_ids"].append([int(t["image_id"]) for t in targets])
            _write(f"steps_rank{RANK}.json", state)

        handle = model.register_forward_pre_hook(pre)
        try:
            return outer(**kwargs)
        except torch.cuda.OutOfMemoryError as exc:
            state["oom"] = {"step": len(state["step_start"]), "message": str(exc).splitlines()[0],
                            **_memory(device)}
            raise
        except Exception as exc:  # recorded, then re-raised unchanged (ControlComplete too)
            state["error"] = type(exc).__name__
            raise
        finally:
            handle.remove()
            state["end"] = time.perf_counter()
            state["memory"] = _memory(device)
            _write(f"steps_rank{RANK}.json", state)

    detector.train_one_epoch_acc = probed


class _Stop(SystemExit):
    pass


def install_phase(cfg, work):
    import stage1_ptower_r3 as r3
    import stage1_ptower_r3_dist as dist_path

    steps = int(os.environ["PROBE_STEPS"])
    get_item = r3.FoldFrames.__getitem__

    def logged_get_item(self, index):
        _read("phase", self.frames[index]["frame"])
        return get_item(self, index)

    r3.FoldFrames.__getitem__ = logged_get_item
    state = {"tower": "phase", "rank": RANK, "probe_steps": steps, "step_start": [],
             "gpu_done": [], "frames": [], "frame_ids": [], "oom": None, "error": None,
             "ft_batch_size": int(cfg.ft_batch_size), "ft_accum_steps": int(cfg.ft_accum_steps),
             "world_size": int(os.environ.get("WORLD_SIZE", "1"))}

    class TimedLoader:
        def __init__(self, loader):
            self.loader = loader
            state["steps_per_epoch"] = len(loader)
            state["dataset_frames"] = len(loader.dataset)

        def __len__(self):
            return len(self.loader)

        def __iter__(self):
            iterator = iter(self.loader)
            while True:
                if state["step_start"]:
                    torch.cuda.synchronize()
                    state["gpu_done"].append(time.perf_counter())
                if len(state["step_start"]) == steps:
                    state["end"] = state["gpu_done"][-1]
                    state["memory"] = _memory(torch.cuda.current_device())
                    _write(f"steps_rank{RANK}.json", state)
                    print(f"PROBE_COMPLETE rank={RANK} steps={steps}", flush=True)
                    raise _Stop(0)
                batch = next(iterator)
                state["step_start"].append(time.perf_counter())
                state["frames"].append(int(batch[1].numel()))
                state["frame_ids"].append(list(batch[2]))
                state["input_shape"] = list(batch[0].shape)
                _write(f"steps_rank{RANK}.json", state)
                yield batch

    def timed_factory(original):
        def make(*args, **kwargs):
            loader = original(*args, **kwargs)
            is_train = kwargs.get("shuffle") or kwargs.get("batch_sampler") is not None
            return TimedLoader(loader) if is_train else loader
        return make

    r3.DataLoader = timed_factory(r3.DataLoader)
    dist_path.DataLoader = timed_factory(dist_path.DataLoader)

    def guarded(function):
        def run(config):
            try:
                return function(config)
            except torch.cuda.OutOfMemoryError as exc:
                state["oom"] = {"step": len(state["step_start"]),
                                "message": str(exc).splitlines()[0],
                                **_memory(torch.cuda.current_device())}
                _write(f"steps_rank{RANK}.json", state)
                raise
        return run

    r3.finetune = guarded(r3.finetune)
    dist_path.finetune = guarded(dist_path.finetune)

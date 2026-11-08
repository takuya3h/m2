"""Measurement hook for T-2026-11-06-dtower-batch-search, loaded through TOWER_SEARCH_OBSERVER.

``scripts/tower_search_common.load_observer`` imports this file when the environment names it.
Nothing here changes an update: the hooks read the DataLoader, the learning rate the step uses,
the frames each step receives, clocks and the evaluator's precision array. Written to
``$PROBE_OUT`` (outside the repo):

- ``loader_rank<R>.json``: the DataLoader's batch size, length, workers; per epoch the set and
  count of frames handed to the model per step (must equal the level's per-GPU batch).
- ``warmup_rank<R>.json``: the learning rate of every optimizer group at every step of epoch 0
  (read before the step, i.e. the value the step uses) and the first step at which group 0 reaches
  the target learning rate (``DTOWER_LR``) within 1e-12 relative.
- ``eval_epochs.json`` (main process): per epoch the evaluation wall time, COCO stats, per-class AP
  (area all, maxDet 100, the evaluator script's computation), the target and negative group AP.
- ``reads_det_pid<PID>.txt``: the video id of every image the datasets loaded (training and the
  per-epoch validation), one line per image.

``PROBE_EXPECT_BATCH`` makes the first training step raise when the frames handed to the model
differ from the level's batch (a stop condition of the prereg).
"""
from __future__ import annotations

import json
import math
import os
import time
from collections import Counter
from pathlib import Path

OUT = Path(os.environ["PROBE_OUT"])
RANK = os.environ.get("RANK", "0")
TARGET = ("Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory")
NEGATIVE = ("Gauze", "Mouth Gag", "Suction Cannula", "Tweezers")


def _write(name, value):
    path = OUT / name
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _group(per_class, names):
    values = [per_class[n] for n in names if n in per_class and math.isfinite(per_class[n])]
    return float(sum(values) / len(values)) if values else None


def install_detector(detector, work):
    import datasets.coco as coco

    load_image = coco.CocoDetection.load_image

    def logged_load_image(self, image_name):
        with open(OUT / f"reads_det_pid{os.getpid()}.txt", "a") as handle:
            handle.write(Path(str(image_name)).name[:2] + "\n")
        return load_image(self, image_name)

    coco.CocoDetection.load_image = logged_load_image
    expect = int(os.environ["PROBE_EXPECT_BATCH"]) if os.environ.get("PROBE_EXPECT_BATCH") else None
    target_lr = float(os.environ["DTOWER_LR"])
    loader_state = {"rank": RANK, "epochs": []}
    warmup = {"rank": RANK, "target_lr": target_lr, "lr_per_step": [], "first_step_at_target": None}
    outer = detector.train_one_epoch_acc

    def probed(**kwargs):
        model, optimizer, loader = kwargs["model"], kwargs["optimizer"], kwargs["data_loader"]
        epoch = kwargs["epoch"]
        loader_state.update({"batch_sampler_batch_size": getattr(loader.batch_sampler, "batch_size", None),
                             "loader_length": len(loader), "num_workers": loader.num_workers,
                             "pin_memory": loader.pin_memory, "dataset_frames": len(loader.dataset)})
        frames = Counter()

        def pre(_module, args):
            size = len(args[1])
            frames[size] += 1
            if expect is not None and size != expect:
                raise RuntimeError(f"frames per step {size} differ from the level batch {expect}")
            if epoch == 0:
                lrs = [float(g["lr"]) for g in optimizer.param_groups]
                warmup["lr_per_step"].append(lrs)
                if warmup["first_step_at_target"] is None and abs(lrs[0] - target_lr) <= 1e-12 * target_lr:
                    warmup["first_step_at_target"] = len(warmup["lr_per_step"])

        handle = model.register_forward_pre_hook(pre)
        started = time.time()
        try:
            return outer(**kwargs)
        finally:
            handle.remove()
            loader_state["epochs"].append({"epoch": epoch, "frames_per_step": dict(frames),
                                           "steps": sum(frames.values()), "seconds": time.time() - started})
            _write(f"loader_rank{RANK}.json", loader_state)
            if epoch == 0:
                warmup["steps_in_epoch0"] = len(warmup["lr_per_step"])
                _write(f"warmup_rank{RANK}.json", warmup)

    detector.train_one_epoch_acc = probed
    evaluate = detector.evaluate_acc
    history = []

    def timed_evaluate(model, data_loader, epoch, accelerator=None):
        started = time.time()
        result = evaluate(model, data_loader, epoch, accelerator)
        seconds = time.time() - started
        if accelerator is None or accelerator.is_main_process:
            ce = result.coco_eval["bbox"]
            precision = ce.eval["precision"]
            names = {cid: c["name"] for cid, c in data_loader.dataset.coco.cats.items()}
            per_class = {}
            for k, cid in enumerate(ce.params.catIds):
                p = precision[:, :, k, 0, -1]
                p = p[p > -1]
                per_class[names.get(cid, str(cid))] = float(p.mean()) if p.size else float("nan")
            history.append({"epoch": epoch, "seconds": seconds, "stats": [float(v) for v in ce.stats],
                            "ann_file_images": len(data_loader.dataset),
                            "per_class_ap": {k: (v if math.isfinite(v) else None) for k, v in per_class.items()},
                            "AP_target": _group(per_class, TARGET), "AP_negative": _group(per_class, NEGATIVE)})
            _write("eval_epochs.json", history)
        return result

    detector.evaluate_acc = timed_evaluate

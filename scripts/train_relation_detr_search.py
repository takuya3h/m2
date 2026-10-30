"""Observe the existing detector training loop; leave its updates and recipe intact."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "third_party/Relation-DETR"))

import main as detector  # noqa: E402
import torch  # noqa: E402
from tower_search_common import (  # noqa: E402
    TASK,
    OfflineTracker,
    check_detector_groups,
    load_point,
    optimizer_groups,
    runtime_state,
    write_json,
)


def install_observers(point, work, tracker):
    train_epoch = detector.train_one_epoch_acc
    evaluate = detector.evaluate_acc
    load_state = detector.load_state_dict
    rank = int(os.environ.get("RANK", "0"))
    history = []

    class ControlComplete(Exception):
        pass

    class LimitedBatches:
        def __init__(self, loader, count):
            self.loader, self.count = loader, min(len(loader), count)

        def __len__(self):
            return self.count

        def __iter__(self):
            return itertools.islice(self.loader, self.count)

    def loaded(model, checkpoint):
        result = load_state(model, checkpoint)
        state = model.state_dict()
        checked = [k for k, v in checkpoint.items() if k in state and state[k].shape == v.shape]
        if not checked or any(not torch.equal(state[k].cpu(), checkpoint[k].cpu()) for k in checked):
            raise RuntimeError("COCO initialization did not reach the detector")
        write_json(work / f"initialization_rank{rank}.json", {
            "source": os.environ["RELDETR_COCO_CKPT"], "matching_tensors": len(checked),
            "source_sha256": hashlib.sha256(Path(os.environ["RELDETR_COCO_CKPT"]).read_bytes()).hexdigest(),
            "matched": True, "runtime": runtime_state()})
        return result

    def train(**kwargs):
        accelerator, optimizer = kwargs["accelerator"], kwargs["optimizer"]
        epoch = kwargs["epoch"]
        groups = optimizer_groups(optimizer)
        if epoch == 0:
            check_detector_groups(groups, point)
            norms = [float(sum(p.detach().double().square().sum().cpu().item()
                               for p in g["params"]) ** .5) for g in optimizer.param_groups]
            write_json(work / f"optimizer_rank{rank}.json", {
                "point": point, "groups": groups, "initial_weight_norms": norms,
                "parameter_names": [[name for name, p in accelerator.unwrap_model(kwargs["model"]).named_parameters()
                                     if id(p) in {id(q) for q in g["params"]}]
                                    for g in optimizer.param_groups],
                "max_norm": kwargs["max_grad_norm"], "runtime": runtime_state(),
                "autocast": accelerator.mixed_precision})
        if os.environ.get("TOWER_SEARCH_CONTROL_STEPS"):
            kwargs["data_loader"] = LimitedBatches(kwargs["data_loader"],
                                                    int(os.environ["TOWER_SEARCH_CONTROL_STEPS"]))
        clip = accelerator.clip_grad_norm_
        gradient_file = work / f"gradients_rank{rank}.jsonl"
        with gradient_file.open("a", buffering=1) as handle:
            def clipped(parameters, max_norm, *args, **kw):
                norm = clip(parameters, max_norm, *args, **kw)
                value = float(norm)
                handle.write(json.dumps({"epoch": epoch, "norm": value,
                                         "clipped": value > max_norm,
                                         "max_norm": max_norm}) + "\n")
                return norm
            accelerator.clip_grad_norm_ = clipped
            started = time.monotonic()
            torch.cuda.reset_peak_memory_stats(accelerator.device)
            try:
                result = train_epoch(**kwargs)
            finally:
                accelerator.clip_grad_norm_ = clip
        record = {"epoch": epoch, "seconds": time.monotonic() - started,
                  "peak_memory_bytes": torch.cuda.max_memory_allocated(accelerator.device),
                  "groups": groups}
        write_json(work / f"train_epoch_{epoch:03d}_rank{rank}.json", record)
        if os.environ.get("TOWER_SEARCH_CONTROL_STEPS"):
            write_json(work / f"control_complete_rank{rank}.json", {
                "steps": len(kwargs["data_loader"]), "point": point,
                "groups_after_warmup": optimizer_groups(optimizer),
                "successful_optimizer_steps": max((int(s["step"]) for s in optimizer.state.values()
                                                    if "step" in s), default=0),
                "final_weight_norms": [float(sum(p.detach().double().square().sum().cpu().item()
                                                 for p in g["params"]) ** .5)
                                       for g in optimizer.param_groups]})
            raise ControlComplete()
        return result

    def evaluated(model, data_loader, epoch, accelerator=None):
        result = evaluate(model, data_loader, epoch, accelerator)
        if accelerator.is_main_process:
            stats = [float(v) for v in result.coco_eval["bbox"].stats]
            history.append({"epoch": epoch, "val_mAP": stats[0], "stats": stats})
            write_json(work / "search_history.json", history)
            tracker.log({"val/mAP": stats[0], "val/AP50": stats[1]}, epoch)
        return result

    detector.load_state_dict = loaded
    detector.train_one_epoch_acc = train
    detector.evaluate_acc = evaluated
    return ControlComplete


def main():
    point = load_point(int(os.environ["TOWER_SEARCH_POINT"]))
    work = Path(os.environ["RELDETR_OUTPUT_DIR"])
    work.mkdir(parents=True, exist_ok=True)
    is_main = int(os.environ.get("RANK", "0")) == 0
    tracker = (OfflineTracker(f"detector_point{point['point']:02d}",
                              {"task_id": TASK, "point": point, "fold": "A", "seed": 42},
                              work / "wandb") if is_main else None)
    control_complete = install_observers(point, work, tracker)
    try:
        detector.train()
    except control_complete:
        print("CONTROL_COMPLETE (no evaluation; excluded from search)", flush=True)
    finally:
        if tracker is not None:
            tracker.finish()


if __name__ == "__main__":
    main()

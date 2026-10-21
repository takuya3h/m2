"""Post-training measurements from actual checkpoints; never fills missing metrics."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import stage1_ptower as base
import stage1_ptower_r3 as r3
import torch
from omegaconf import OmegaConf
from tower_search_common import ROOT, write_json

TARGET = ("Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory")
NEGATIVE = ("Gauze", "Mouth Gag", "Suction Cannula", "Tweezers")


def weight_norm(parameters):
    return float(sum(p.detach().double().square().sum().cpu().item() for p in parameters) ** .5)


def slope(history, field):
    if len(history) < 4:
        return None
    return float(np.polyfit([r["epoch"] for r in history[-4:]],
                            [r[field] for r in history[-4:]], 1)[0])


def phase(work, action):
    pointer = json.loads((work / f"{action}_last_run.json").read_text())
    run = Path(pointer["path"])
    cfg = OmegaConf.load(run / "config.yaml")
    metrics = json.loads((run / "metrics.json").read_text())
    if not metrics:
        raise RuntimeError("Phase run has no measured metrics")
    if action == "extract":
        return run, {"features": json.loads((run / "feature_audit.json").read_text())}
    base.deterministic(cfg.seed)
    checkpoint = torch.load(run / "checkpoints/best.pth", map_location="cpu", weights_only=True)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    if action == "finetune":
        from torch.utils.data import DataLoader
        model, _, _ = r3.build_backbone(len(names), cfg.device, cfg.init)
        model.load_state_dict(checkpoint["model"])
        clips = base.manifests(cfg)
        train = r3.FoldFrames(clips, base.folds()[cfg.fold]["train"], train=False)
        if cfg.get("control_frames", 0):
            train.frames = train.frames[:int(cfg.control_frames)]
        loader = DataLoader(train, batch_size=cfg.ft_batch_size, shuffle=False,
                            num_workers=cfg.workers)
        pred, labels, ids = r3.frame_predictions(model, loader, cfg.device)
        measured = r3.frame_accuracy(pred, labels, ids, names)
        metrics["train_accuracy"] = measured["phase_accuracy"]
        metrics["train_val_accuracy_gap"] = measured["phase_accuracy"] - metrics["phase_accuracy"]
        history = json.loads((run / "finetune_history.json").read_text())["history"]
        extra = {"last_val_accuracy": history[-1]["val_accuracy"],
                 "last_four_val_slope": slope(history, "val_accuracy") if metrics["reached_epoch_cap"] else None}
    else:
        _, data = base.load_fold(cfg)
        model = base.build_model(cfg, len(names)).to(cfg.device)
        model.load_state_dict(checkpoint["model"])
        measured = base.evaluate(model, data["train"], cfg.device, names)
        metrics["train_jaccard"] = measured["phase_jaccard"]
        metrics["train_val_jaccard_gap"] = measured["phase_jaccard"] - metrics["phase_jaccard"]
        history = json.loads((run / "search_epoch_history.json").read_text())
        extra = {"last_val_jaccard": history[-1]["metrics"]["val/jaccard"],
                 "last_val_accuracy": history[-1]["metrics"]["val/accuracy"],
                 "reached_head_epoch_cap": metrics["epochs_completed"] == cfg.epochs}
    initial = json.loads((work / f"{action}_optimizer_rank0.json").read_text())
    norms = [weight_norm(p for p in model.parameters() if p.requires_grad)]
    record = {"checkpoint_epoch": int(checkpoint["epoch"]), "optimizer": initial,
              "final_weight_norms": norms,
              "weight_norm_changes": [v - u for u, v in zip(initial["initial_weight_norms"], norms, strict=True)],
              "epoch_timing_and_memory": json.loads((run / "search_epoch_history.json").read_text()),
              **extra}
    write_json(run / "optimizer_record.json", initial)
    write_json(run / "metrics.json", metrics)
    return run, record


def group_ap(per_class, classes):
    present = [per_class[name] for name in classes if math.isfinite(per_class[name])]
    if not present:
        raise RuntimeError("No measured class in detection group")
    return float(np.mean(present))


def detector(work):
    val = json.loads((work / "eval_val.json").read_text())
    train = json.loads((work / "eval_train.json").read_text())
    if not math.isfinite(val["AP"]) or val["AP"] <= 0:
        raise RuntimeError("Val AP is zero or non-finite; stop and ask")
    history = json.loads((work / "search_history.json").read_text())
    best = max(history, key=lambda r: (r["val_mAP"], r["epoch"]))
    convergence = json.loads((work / "convergence.json").read_text())
    initial = json.loads((work / "optimizer_rank0.json").read_text())
    state = torch.load(work / "best_ap.pth", map_location="cpu", weights_only=True)
    norms = [weight_norm(state[name] for name in names) for names in initial["parameter_names"]]
    gradients = [json.loads(line) for line in (work / "gradients_rank0.jsonl").read_text().splitlines()]
    finite = [r["norm"] for r in gradients if math.isfinite(r["norm"])]
    quantiles = np.quantile(finite, [.05, .5, .95]).tolist() if finite else None
    cap = len(history) == 36
    metrics = {"mAP": val["AP"], "AP_target": group_ap(val["per_class_ap"], TARGET),
               "AP_negative": group_ap(val["per_class_ap"], NEGATIVE), "train_mAP": train["AP"],
               "train_val_mAP_gap": train["AP"] - val["AP"], "best_epoch": best["epoch"],
               "epochs_completed": len(history), "reached_epoch_cap": cap}
    record = {"metrics": metrics, "convergence": convergence,
              "last_val_mAP": history[-1]["val_mAP"], "optimizer": initial,
              "final_weight_norms": norms, "weight_norm_changes": [v - u for u, v in zip(initial["initial_weight_norms"], norms, strict=True)],
              "gradient_norm_quantiles_5_50_95": quantiles,
              "gradient_nonfinite_steps": sum(not math.isfinite(r["norm"]) for r in gradients),
              "clipping_fraction": sum(r["clipped"] for r in gradients) / len(gradients),
              "last_four_val_slope": slope(history, "val_mAP") if cap else None,
              "per_rank_epochs": [json.loads(p.read_text()) for p in sorted(work.glob("train_epoch_*_rank*.json"))]}
    write_json(work / "search_metrics.json", metrics)
    return work, record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("phase", "detector"))
    parser.add_argument("work", type=Path)
    parser.add_argument("--action", choices=("finetune", "extract", "train"))
    args = parser.parse_args()
    run, record = (phase(args.work, args.action) if args.kind == "phase" else detector(args.work))
    write_json(run / "posthoc_records.json", record)
    print(f"RECORDS_COMPLETE {run}", flush=True)


if __name__ == "__main__":
    main()

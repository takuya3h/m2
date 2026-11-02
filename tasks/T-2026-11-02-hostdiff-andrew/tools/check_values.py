"""完了判定 d: values.json に SPEC §6.1 の全キーがあり、値か理由つきの UNKNOWN が入っているか（読むだけ）。

    python3 tasks/T-2026-11-02-hostdiff-andrew/tools/check_values.py <values.json> [--self-test]

``--self-test`` はキーを一つ消した写しを検査にかけ、欠けとして出ることを確かめる。
"""
from __future__ import annotations

import argparse
import copy
import json
import sys

TOP = ["host", "task_id", "code_commit", "env", "determinism_check", "phase", "detector"]
ENV = ["phase_venv", "detector_venv", "driver", "power_limit_W", "NCCL_P2P_DISABLE", "phase_determinism",
       "detector_autocast", "tf32"]
VENV = ["torch", "torch_cuda_runtime", "cudnn", "nccl", "torchvision", "accelerate", "image_decoder"]
PHASE = ["J_heads", "J_mean", "J_max", "backbone_val_frame_acc", "lr_drop_epoch", "stop_epoch",
         "checkpoint_epoch", "cap_reached", "coco_loaded", "timing", "gpu", "foreign_gpu_use"]
DET = ["mAP", "AP_signature", "AP_negative", "AP50", "lr_drop_epoch", "stop_epoch", "checkpoint_epoch",
       "cap_reached", "coco_loaded", "timing", "gpu", "foreign_gpu_use"]
TIMING_P = ["wall_s", "train_s_per_epoch", "s_per_step_median", "eval_s", "features_s", "heads_s"]
TIMING_D = ["wall_s", "train_s_per_epoch", "s_per_step_median", "eval_s"]


def missing(values):
    out = []

    def need(obj, keys, where):
        if isinstance(obj, dict) and set(obj) == {"UNKNOWN"} and obj["UNKNOWN"]:
            return False
        for key in keys:
            if not isinstance(obj, dict) or key not in obj:
                out.append(f"{where}.{key}")
        return isinstance(obj, dict)

    need(values, TOP, "")
    if need(values.get("env"), ENV, "env"):
        for v in ("phase_venv", "detector_venv"):
            need(values["env"].get(v), VENV, f"env.{v}")
    need(values.get("determinism_check"), ["identical", "loss_sequence_sha256", "optimizer_steps"], "determinism_check")
    for seed in ("seed42", "seed123"):
        run = values.get("phase", {}).get(seed)
        if need(run, PHASE, f"phase.{seed}") and "timing" in run:
            if need(run["timing"], TIMING_P, f"phase.{seed}.timing") and "s_per_step_median" in run["timing"]:
                need(run["timing"]["s_per_step_median"], ["micro_step", "optimizer_step"],
                     f"phase.{seed}.timing.s_per_step_median")
    for name in ("seed42a", "seed42b", "seed123"):
        run = values.get("detector", {}).get(name)
        if need(run, DET, f"detector.{name}") and "timing" in run:
            need(run["timing"], TIMING_D, f"detector.{name}.timing")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    values = json.load(open(args.path))
    if args.self_test:
        broken = copy.deepcopy(values)
        del broken["detector"]["seed123"]["AP_signature"]
        print(json.dumps({"self_test_missing": missing(broken)}, ensure_ascii=False))
        return
    gaps = missing(values)
    print(json.dumps({"missing": gaps, "ok": not gaps}, ensure_ascii=False))
    sys.exit(1 if gaps else 0)


if __name__ == "__main__":
    main()

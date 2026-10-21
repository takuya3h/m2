"""A few real updates through each tower, excluded from the search runs."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from tower_search_common import SCRATCH, load_point  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("detector", "phase"))
    parser.add_argument("point", type=int)
    parser.add_argument("--gpus", choices=("1,2", "3,4"), required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    point = load_point(args.point)
    work = SCRATCH / "controls" / f"{args.kind}_point{args.point:02d}{args.tag}"
    work.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": args.gpus, "WANDB_MODE": "offline",
           "WANDB_DIR": str(work), "PYTHONPATH": str(ROOT / "src") + ":" + str(ROOT / "scripts")}
    if args.kind == "detector":
        env.update(EGO_ROOT=str(ROOT / "data/raw/ego"),
                   EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
                   RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"),
                   RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
                   DTOWER_LR=str(point["lr"]), DTOWER_WEIGHT_DECAY=str(point["detector_weight_decay"]),
                   DTOWER_MAX_NORM=str(point["max_norm"]), TOWER_SEARCH_POINT=str(args.point),
                   TOWER_SEARCH_CONTROL_STEPS=str(args.steps), CUDA_HOME="/usr/local/cuda")
        cmd = [str(ROOT / ".venv-relation-detr/bin/accelerate"), "launch", "--multi_gpu",
               "--num_processes", "2", "--main_process_port", str(args.port),
               str(ROOT / "scripts/train_relation_detr_search.py"), "--config-file",
               str(ROOT / "configs/detector_relation_detr/train_search.py"), "--seed", "42",
               "--mixed-precision", "fp16", "--convergence-schedule", "--max-epochs", "1"]
        cwd = ROOT / "third_party/Relation-DETR"
    else:
        cmd = [sys.executable, "-m", "torch.distributed.run", "--nproc_per_node=2",
               f"--master_port={args.port}", "scripts/run_ptower_search.py",
               f"+point_id={args.point}", f"+artifact_root={work}", "+control_frames=32",
               "ft_epochs=1", "workers=2", "manifest_dir=data/processed/phase_manifest_all_phase"]
        cwd = ROOT
    (work / "command.json").write_text(json.dumps({"cmd": cmd, "gpus": args.gpus, "point": point}, indent=2))
    with (work / "train.log").open("w") as output:
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
    print(f"{args.kind} point={args.point} exit={result.returncode} work={work}", flush=True)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

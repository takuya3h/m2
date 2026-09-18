"""Run the second round's grids with two subprocess workers and stop gates.

Three stages share the resume logic: FT fine-tunes one backbone per (fold, seed,
learning rate), EX extracts that backbone's features, and HEAD replays the first
round's ten temporal heads on each of those feature sets. Every stage skips work
that already carries evidence, so an interrupted run continues where it stopped.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASK = "T-2026-09-19-stage1-phase-tower-r2"
SCRIPT = "scripts/stage1_ptower_r2.py"
LEARNING_RATES = (0.0001, 0.000033333333333333335)
FOLD_SEEDS = [(f, s) for f in "ABCDE" for s in ((42, 123, 456) if f == "A" else (42,))]


def backbones():
    return [dict(ft_lr=lr, fold=f, seed=s) for lr in LEARNING_RATES for f, s in FOLD_SEEDS]


def heads():
    """The first round's ten recipes, values unchanged."""
    recipes = [dict(candidate="A", layers=layers, smoothing_weight=0.0, history=30)
               for layers in (6, 8)]
    for layers in (6, 8):
        recipes += [dict(candidate="B", layers=layers, smoothing_weight=0.0, history=h)
                    for h in (30, 60)]
        recipes += [dict(candidate="C", layers=layers, smoothing_weight=w, history=30)
                    for w in (0.15, 0.30)]
    return recipes


def cache_of(params):
    return f"data/processed/stage1_features/r2_ft_lr{params['ft_lr']}_fold{params['fold']}_seed{params['seed']}/all_gap.npz"


def checkpoint_of(params):
    done = evidence_for(dict(params, action="finetune"))
    if done is None:
        raise RuntimeError(f"Fine-tune missing for {params}")
    return str((done[0] / "checkpoints/best.pth").relative_to(ROOT))


def grid(stage):
    if stage == "FT":
        return [dict(b, action="finetune") for b in backbones()]
    if stage == "EX":
        return [dict(b, action="extract") for b in backbones()]
    return [dict(b, action="train", **r) for b in backbones() for r in heads()]


# Keys that identify a run; the rest of the config is evidence, not identity.
IDENTITY = ("action", "ft_lr", "fold", "seed", "candidate", "layers",
            "smoothing_weight", "history")


def evidence_for(params, task=TASK):
    found = []
    wanted = {k: v for k, v in params.items() if k in IDENTITY}
    for path in (ROOT / "experiments/phase1").glob("stage1_ptower_r2_*/config.yaml"):
        cfg = yaml.safe_load(path.read_text())
        if cfg.get("task_id") != task:
            continue
        if not all(cfg.get(k) == v for k, v in wanted.items()):
            continue
        metrics = json.loads(path.with_name("metrics.json").read_text())
        if metrics and path.with_name("wandb_run.json").exists():
            found.append((path.parent, metrics))
    if len(found) > 1:
        raise RuntimeError(f"Duplicate completed setting: {wanted}")
    return found[0] if found else None


def arguments(params, device, verify):
    args = [f"{k}={v}" for k, v in params.items()]
    args.append(f"device=cuda:{device}")
    args.append(f"cache={cache_of(params)}")
    if params["action"] == "extract":
        args.append(f"checkpoint={checkpoint_of(params)}")
        args.append(f"verify_determinism={str(verify).lower()}")
    if params["action"] == "train":
        args.append(f"backbone_tag=imagenet_r50_v1_ft_lr{params['ft_lr']}")
        args.append(f"desc_suffix=_lr{params['ft_lr']}")
    return args


def run(params, device, verify=False):
    done = evidence_for(params)
    if done is None:
        name = "_".join(f"{k}-{v}" for k, v in params.items())
        log = ROOT / "tasks" / TASK / f"grid_{name}.log"
        cmd = [str(ROOT / ".venv/bin/python"), "-u", SCRIPT] + arguments(params, device, verify)
        with log.open("xb") as output:
            subprocess.run(cmd, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                           check=True, timeout=3700)
        done = evidence_for(params)
        if done is None:
            raise RuntimeError(f"No evidence for {params}")
    path, metrics = done
    if metrics.get("elapsed_seconds", 0) > 3600:
        raise RuntimeError(f"One-hour stop condition: {path}")
    score = metrics.get("phase_jaccard", metrics.get("phase_accuracy"))
    print(f"COMPLETE {path.name} score={score}", flush=True)
    return {"params": params, "path": str(path.relative_to(ROOT)), "metrics": metrics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["FT", "EX", "HEAD"])
    parser.add_argument("--verify-first", action="store_true",
                        help="check determinism on the first extraction only")
    args = parser.parse_args()
    items = grid(args.stage)
    results = []
    # Submit one pair at a time: a failed pair cannot start subsequent runs.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i in range(0, len(items), 2):
            futures = [pool.submit(run, p, device, args.verify_first and i == 0 and device == 0)
                       for device, p in enumerate(items[i:i + 2])]
            for future in as_completed(futures):
                results.append(future.result())
    path = ROOT / "tasks" / TASK / f"grid_{args.stage}_results.json"
    path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"GRID_COMPLETE {args.stage} runs={len(results)}", flush=True)


if __name__ == "__main__":
    main()

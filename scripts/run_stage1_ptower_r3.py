"""Run the third round's grids with two subprocess workers and resume on evidence.

Three stages share the resume logic: FT fine-tunes one backbone per (init chain,
learning rate, fold, seed), EX extracts that backbone's features at short side 800,
and HEAD replays the first round's ten temporal heads on each of those feature sets.
Every stage skips work that already carries evidence, so an interrupted run continues
where it stopped.

The second round capped a run at one hour. Here the whole frame at short side 800 is
about 22 times the pixels of its 224 centre crop, and the epoch budget is 36 instead
of 12, so a run is measured in hours; the user accepted that the three-hour figure in
the contract is exceeded (Task B measured it). The hard timeout only catches a run
that has stopped making progress.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASK = "T-2026-09-19-stage1-phase-tower-r3"
SCRIPT = "scripts/stage1_ptower_r3.py"
INITS = ("coco", "imagenet")
LEARNING_RATES = (0.0001, 0.0003)
FOLD_SEEDS = [(f, s) for f in "ABCDE" for s in ((42, 123, 456) if f == "A" else (42,))]
LOG_DIR = ROOT / "experiments/phase1/stage1_ptower_r3/logs"
# Task B measured about 4.8 hours at the 36-epoch cap. Eight hours leaves headroom
# for the slowest fold while still catching a run that has hung.
RUN_TIMEOUT_SECONDS = 8 * 3600
# The contract's gate G2. Exceeding it is reported, not fatal: the user was asked.
GATE_SECONDS = 3 * 3600


def backbones():
    return [dict(init=i, ft_lr=lr, fold=f, seed=s)
            for i in INITS for lr in LEARNING_RATES for f, s in FOLD_SEEDS]


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
    return (f"data/processed/stage1_features/r3_{params['init']}_lr{params['ft_lr']}"
            f"_fold{params['fold']}_seed{params['seed']}/all_gap.npz")


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
IDENTITY = ("action", "init", "ft_lr", "fold", "seed", "candidate", "layers",
            "smoothing_weight", "history")


def evidence_for(params, task=TASK):
    found = []
    wanted = {k: v for k, v in params.items() if k in IDENTITY}
    for path in (ROOT / "experiments/phase1").glob("stage1_ptower_r3_*/config.yaml"):
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
        args.append(f"backbone_tag={params['init']}_r50_ft800_lr{params['ft_lr']}")
        args.append(f"desc_suffix=_{params['init']}_lr{params['ft_lr']}")
    return args


def run(params, device, verify=False):
    done = evidence_for(params)
    if done is None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        name = "_".join(f"{k}-{v}" for k, v in params.items())
        log = LOG_DIR / f"grid_{name}.log"
        cmd = [str(ROOT / ".venv/bin/python"), "-u", SCRIPT] + arguments(params, device, verify)
        with log.open("xb") as output:
            subprocess.run(cmd, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                           check=True, timeout=RUN_TIMEOUT_SECONDS)
        done = evidence_for(params)
        if done is None:
            raise RuntimeError(f"No evidence for {params}")
    path, metrics = done
    elapsed = metrics.get("elapsed_seconds", 0)
    gate = "OVER_GATE" if elapsed > GATE_SECONDS else "within_gate"
    score = metrics.get("phase_jaccard", metrics.get("phase_accuracy"))
    print(f"COMPLETE {path.name} score={score} elapsed={elapsed:.0f}s {gate}", flush=True)
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
    path = LOG_DIR / f"grid_{args.stage}_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"GRID_COMPLETE {args.stage} runs={len(results)}", flush=True)


if __name__ == "__main__":
    main()

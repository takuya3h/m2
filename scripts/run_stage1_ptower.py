"""Run preregistered Stage 1 grids with two subprocess workers and stop gates."""
from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASK = "T-2026-09-18-stage1-phase-tower"


def grid(stage):
    recipes = []
    for layers in (6, 8):
        if stage == "A":
            recipes.append(dict(candidate="A", layers=layers, smoothing_weight=0.0, history=30))
        else:
            recipes.extend(dict(candidate="B", layers=layers, smoothing_weight=0.0, history=h)
                           for h in (30, 60))
            recipes.extend(dict(candidate="C", layers=layers, smoothing_weight=w, history=30)
                           for w in (0.15, 0.30))
    return [dict(r, fold=f, seed=s) for r in recipes for f in "ABCDE"
            for s in ((42, 123, 456) if f == "A" else (42,))]


def completed(params):
    found = []
    for p in (ROOT / "experiments/phase1").glob("stage1_ptower_*/config.yaml"):
        cfg = yaml.safe_load(p.read_text())
        if cfg.get("task_id") != TASK or cfg.get("action") != "train":
            continue
        if not all(cfg.get(k) == v for k, v in params.items()):
            continue
        m = json.loads(p.with_name("metrics.json").read_text())
        if "epochs_completed" in m and p.with_name("wandb_run.json").exists():
            found.append((p.parent, m))
    if len(found) > 1:
        raise RuntimeError(f"Duplicate completed setting: {params}")
    return found[0] if found else None


def run(params, device):
    done = completed(params)
    if done is None:
        name = "_".join(f"{k}-{v}" for k, v in params.items())
        log = ROOT / "tasks" / TASK / f"grid_{name}.log"
        cmd = [str(ROOT / ".venv/bin/python"), "-u", "scripts/stage1_ptower.py", "action=train",
               f"device=cuda:{device}"] + [f"{k}={v}" for k, v in params.items()]
        with log.open("xb") as output:
            subprocess.run(cmd, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                           check=True, timeout=3700)
        done = completed(params)
        if done is None:
            raise RuntimeError(f"No evidence for {params}")
    path, metrics = done
    if metrics["elapsed_seconds"] > 3600:
        raise RuntimeError(f"One-hour stop condition: {path}")
    print(f"COMPLETE {path.name} J={metrics['phase_jaccard']}", flush=True)
    return {"params": params, "path": str(path.relative_to(ROOT)), "metrics": metrics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["A", "D"])
    args = parser.parse_args()
    items = grid(args.stage)
    results = []
    # Submit one pair at a time: a failed pair cannot start subsequent runs.
    with ThreadPoolExecutor(max_workers=2) as pool:
        for i in range(0, len(items), 2):
            futures = [pool.submit(run, p, device) for device, p in enumerate(items[i:i+2])]
            for future in as_completed(futures):
                results.append(future.result())
    path = ROOT / "tasks" / TASK / f"grid_{args.stage}_results.json"
    path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"GRID_COMPLETE {args.stage} runs={len(results)}", flush=True)


if __name__ == "__main__":
    main()

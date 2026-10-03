"""Run P*-20's grids with two subprocess workers and resume on evidence.

The third round's runner, reduced to what this contract trains: one learning rate
(the confirmed 1e-4), the confirmed temporal head per init chain, and the extra
videos in train. CTRL is the host-difference control -- P*-15, COCO chain, fold A,
seed 42, fine-tune then features then head -- run before anything else. FT, EX and
HEAD then build P*-20 for both chains over 5 folds (fold A with 3 seeds).

The contract asks the user once a single fine-tune passes eight hours. That is a
report, not a kill: the hard timeout only catches a run that has stopped.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASK = "T-2026-09-27-stage1-ptower-20"
SCRIPT = "scripts/stage1_ptower_20.py"
INITS = ("coco", "imagenet")
FT_LR = 0.0001
FOLD_SEEDS = [(f, s) for f in "ABCDE" for s in ((42, 123, 456) if f == "A" else (42,))]
CONTROL = dict(data_setting="P15", init="coco", ft_lr=FT_LR, fold="A", seed=42)
SELECTION = ROOT / "experiments/phase1/stage1_ptower_r3/selection.json"
P15_MANIFEST = "data/processed/phase_manifest"
LOG_DIR = ROOT / "experiments/phase1/stage1_ptower_20/logs"
RUN_TIMEOUT_SECONDS = 24 * 3600
ASK_SECONDS = 8 * 3600
HEAD_KEYS = ("candidate", "layers", "smoothing_weight", "history")


def head_of(init):
    """The third round's confirmed temporal head for an init chain."""
    recipe = json.loads(SELECTION.read_text())["chains"][init]["recipe"]
    assert recipe["ft_lr"] == FT_LR, recipe
    return {k: recipe[k] for k in HEAD_KEYS}


def backbones():
    return [dict(data_setting="P20", init=i, ft_lr=FT_LR, fold=f, seed=s)
            for i in INITS for f, s in FOLD_SEEDS]


def stages(b):
    return {"FT": dict(b, action="finetune"), "EX": dict(b, action="extract"),
            "HEAD": dict(b, action="train", **head_of(b["init"]))}


def grid(stage):
    if stage == "CTRL":
        return list(stages(CONTROL).values())
    return [stages(b)[stage] for b in backbones()]


# Keys that identify a run; the rest of the config is evidence, not identity.
IDENTITY = ("action", "data_setting", "init", "ft_lr", "fold", "seed", *HEAD_KEYS)


def evidence_for(params, task=TASK):
    found = []
    wanted = {k: v for k, v in params.items() if k in IDENTITY}
    for path in (ROOT / "experiments/phase1").glob("stage1_ptower_20_*/config.yaml"):
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


def cache_of(params):
    tag = "p20" if params["data_setting"] == "P20" else "p15ctl"
    return (f"data/processed/stage1_features/{tag}_{params['init']}_lr{params['ft_lr']}"
            f"_fold{params['fold']}_seed{params['seed']}/all_gap.npz")


def checkpoint_of(params):
    done = evidence_for(dict(params, action="finetune"))
    if done is None:
        raise RuntimeError(f"Fine-tune missing for {params}")
    return str((done[0] / "checkpoints/best.pth").relative_to(ROOT))


def arguments(params, device, verify):
    args = [f"{k}={v}" for k, v in params.items()]
    args.append(f"device=cuda:{device}")
    args.append(f"cache={cache_of(params)}")
    if params["data_setting"] == "P15":
        args.append(f"manifest_dir={P15_MANIFEST}")
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
    flag = "OVER_8H_ASK_USER" if elapsed > ASK_SECONDS else "within_8h"
    score = metrics.get("phase_jaccard", metrics.get("phase_accuracy"))
    print(f"COMPLETE {path.name} score={score} elapsed={elapsed:.0f}s {flag}", flush=True)
    return {"params": params, "path": str(path.relative_to(ROOT)), "metrics": metrics}


def running_elsewhere(params):
    """A run with exactly these settings is already in progress outside this runner."""
    marker = " ".join(f"{k}={v}" for k, v in params.items())
    return subprocess.run(["pgrep", "-f", f"{SCRIPT} {marker}"],
                          capture_output=True).returncode == 0


def gpu_busy(device):
    """Any compute process on the device (the contract stops if another user is on it)."""
    query = ["nvidia-smi", "--format=csv,noheader"]
    buses = subprocess.run(query + ["--query-gpu=pci.bus_id"], capture_output=True,
                           text=True, check=True).stdout.split()
    apps = subprocess.run(query + ["--query-compute-apps=gpu_bus_id"], capture_output=True,
                          text=True, check=True).stdout.split()
    return buses[device] in apps


def worker(device, queue, lock, first, verify_first):
    """Take the next setting whenever this device is free. A fine-tune of P*-20 runs
    for seven to ten hours and they differ by hours, so pairing would idle a GPU."""
    results = []
    while True:
        while gpu_busy(device):
            time.sleep(60)
        with lock:
            if not queue:
                return results
            params = queue.pop(0)
        if evidence_for(params) is None and running_elsewhere(params):
            print(f"SKIP_RUNNING_ELSEWHERE {params}", flush=True)
            continue
        results.append(run(params, device, verify_first and params == first))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["CTRL", "FT", "EX", "HEAD"])
    parser.add_argument("--verify-first", action="store_true",
                        help="check determinism on the first extraction only")
    args = parser.parse_args()
    items = grid(args.stage)
    results = []
    if args.stage == "CTRL":
        # Each step needs the previous one's evidence, so the control runs in order.
        for params in items:
            results.append(run(params, 0, args.verify_first and params["action"] == "extract"))
    else:
        queue, lock = list(items), threading.Lock()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker, device, queue, lock, items[0], args.verify_first)
                       for device in (0, 1)]
            for future in as_completed(futures):
                results.extend(future.result())
    missing = [p for p in items if evidence_for(p) is None]
    if missing:
        print(f"MISSING_EVIDENCE {len(missing)} {missing}", flush=True)
    path = LOG_DIR / f"grid_{args.stage}_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2) + "\n")
    print(f"GRID_COMPLETE {args.stage} runs={len(results)}", flush=True)


if __name__ == "__main__":
    main()

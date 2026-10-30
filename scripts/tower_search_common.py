"""Evidence helpers for the preregistered dlsta tower search; no training rules."""
from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = "T-2026-10-22-tower-reselect-search-dlsta"
SCRATCH = Path.home() / "m2-scratch" / TASK
ANALYSIS = ROOT / "experiments/analysis/tower_reselect_search_dlsta"
POINTS = ANALYSIS / "points.csv"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def points_from_prereg(text):
    """Copy the published rounded values; never regenerate Sobol coordinates."""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 8 or not cells[0].isdigit():
            continue
        point, lr, ps, pwd, accum, ds, dwd, norm = cells
        rows.append(dict(point=int(point), lr=float(lr), phase_S=float(ps),
                         phase_weight_decay=float(pwd), accum=int(accum.split("（")[0]),
                         detector_S=float(ds), detector_weight_decay=float(dwd),
                         max_norm=float(norm)))
    if [r["point"] for r in rows] != list(range(20)):
        raise ValueError("prereg must contain exactly points 0..19")
    return rows


def load_point(number):
    with POINTS.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = rows[int(number)]
    result = {k: (int(v) if k in ("point", "accum") else float(v)) for k, v in row.items()}
    if result["point"] != int(number):
        raise ValueError("point number does not match row")
    return result


def optimizer_groups(optimizer):
    return [{"group": i, "lr": float(g["lr"]), "weight_decay": float(g["weight_decay"]),
             "parameters": sum(p.numel() for p in g["params"])}
            for i, g in enumerate(optimizer.param_groups)]


def check_detector_groups(groups, point):
    expected_lr = [point["lr"] * f for f in (1, .1, .1, .1, .1, 1)]
    expected_wd = [point["detector_weight_decay"] * f for f in (1, 1, 0, 1, 0, 0)]
    if len(groups) != 6 or any(abs(g["lr"] - lr) > 1e-15 or
                               abs(g["weight_decay"] - wd) > 1e-15
                               for g, lr, wd in zip(groups, expected_lr, expected_wd)):
        raise ValueError("detector optimizer groups differ from the preregistered point")


def runtime_state():
    import torch
    return {"tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
            "tf32_cudnn": torch.backends.cudnn.allow_tf32,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}


class OfflineTracker:
    """Use the existing body venv without installing wandb into the detector venv."""

    def __init__(self, name, config, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "WANDB_MODE": "offline", "WANDB_DIR": str(directory),
               "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(ROOT / "src")}
        self.process = subprocess.Popen(
            [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/tower_search_track.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
        self.send({"init": True, "name": name, "config": config, "directory": str(directory)})
        if self.process.stdout.readline().strip() != "TRACKING_READY":
            raise RuntimeError("offline W&B tracker did not start")

    def send(self, record):
        self.process.stdin.write(json.dumps(record, allow_nan=False) + "\n")
        self.process.stdin.flush()

    def log(self, metrics, step):
        self.send({"metrics": metrics, "step": step})

    def finish(self):
        self.send({"finish": True})
        self.process.stdin.close()
        if self.process.wait(timeout=60):
            raise RuntimeError("offline W&B tracker failed")

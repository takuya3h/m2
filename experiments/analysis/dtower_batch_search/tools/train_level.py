"""Run scripts/train_relation_detr_search.py with the level's point (T-2026-11-06-dtower-batch-search).

The search script takes the learning rate, weight decay and max_norm from ``DTOWER_*`` and, at
epoch 0, checks the optimizer groups against the point it loads from the dlsta ``points.csv``
(``load_point``). That file holds point 12 with weight decay 3.37e-4, so the batch 4 and 6 levels
(6.7428e-4 and 1.01058e-3, prereg §2.1) would stop there although their value reached the
optimizer. This wrapper imports the search script unchanged and gives it the level's point from
``DTOWER_LEVEL_POINT`` (a JSON file the runner writes from the prereg table) in place of the
``points.csv`` row. Everything else, including the epoch-0 group check, runs as written; the check
now compares the optimizer groups with the prereg values of the level, so a ``DTOWER_*`` value that
differs from the prereg table still stops the run.

    accelerate launch ... train_level.py --config-file ... (the search script's own arguments)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))

import train_relation_detr_search as search  # noqa: E402

KEYS = ("point", "lr", "detector_weight_decay", "max_norm")


def level_point(number):
    point = json.loads(Path(os.environ["DTOWER_LEVEL_POINT"]).read_text())
    if int(point["point"]) != int(number) or any(k not in point for k in KEYS):
        raise ValueError("level point file does not describe the requested point")
    return point


search.load_point = level_point

if __name__ == "__main__":
    search.main()

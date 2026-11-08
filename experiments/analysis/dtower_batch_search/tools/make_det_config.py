"""Write the detector config copy outside the repo with the per-GPU batch and the worker count
from the environment (T-2026-11-06-dtower-batch-search).

``configs/detector_relation_detr/train_search.py`` fixes ``batch_size = 2`` and
``num_workers = 4`` and has no per-point input for either. The copy differs from the original
in those two lines only; the script refuses to write it otherwise and prints the diff.

    python make_det_config.py <out.py>
"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "configs/detector_relation_detr/train_search.py"
CHANGES = {
    "batch_size = 2\n": 'batch_size = int(os.environ["PROBE_BATCH_SIZE"])\n',
    "num_workers = 4\n": 'num_workers = int(os.environ["PROBE_NUM_WORKERS"])\n',
}


def main():
    out = Path(sys.argv[1]).resolve()
    if ROOT in out.parents:
        raise SystemExit("the copy must live outside the repo")
    lines = SOURCE.read_text().splitlines(keepends=True)
    if any(lines.count(old) != 1 for old in CHANGES) or "import os\n" not in lines:
        raise SystemExit("the original no longer has exactly one batch_size and one num_workers line")
    copied = [CHANGES.get(line, line) for line in lines]
    changed = sum(a != b for a, b in zip(lines, copied))
    if changed != len(CHANGES) or len(copied) != len(lines):
        raise SystemExit(f"expected {len(CHANGES)} changed lines, got {changed}")
    out.write_text("".join(copied))
    sys.stdout.writelines(difflib.unified_diff(lines, copied, str(SOURCE), str(out)))


if __name__ == "__main__":
    main()

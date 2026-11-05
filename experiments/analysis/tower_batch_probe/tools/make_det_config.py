"""Write the detector config copy outside the repo with the per-GPU batch from the environment.

``configs/detector_relation_detr/train_search.py`` fixes ``batch_size = 2`` and has no
per-point input for it (SPEC §3.3: without one, a copy lives outside the repo). The copy
differs from the original in that one line only; the script refuses to write it otherwise
and prints the diff.

    python make_det_config.py <out.py>
"""
from __future__ import annotations

import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "configs/detector_relation_detr/train_search.py"
OLD = "batch_size = 2\n"
NEW = 'batch_size = int(os.environ["PROBE_BATCH_SIZE"])\n'


def main():
    out = Path(sys.argv[1]).resolve()
    if ROOT in out.parents:
        raise SystemExit("the copy must live outside the repo")
    lines = SOURCE.read_text().splitlines(keepends=True)
    if lines.count(OLD) != 1 or "import os\n" not in lines:
        raise SystemExit("the original no longer has exactly one batch_size line")
    copied = [NEW if line == OLD else line for line in lines]
    out.write_text("".join(copied))
    sys.stdout.writelines(difflib.unified_diff(lines, copied, str(SOURCE), str(out)))


if __name__ == "__main__":
    main()

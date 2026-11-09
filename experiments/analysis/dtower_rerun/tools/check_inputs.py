"""G1 (Task A-6): inputs and tools exist and their sha256 matches the recorded values.

    python check_inputs.py [--override PATH=FILE]   # exit 0 when every entry exists and matches

The recorded COCO checkpoint value is the one the detector's initialization record writes
(``initialization_rank*.json`` ``source_sha256``, PR 290 / PR 292). The fold-A annotations and
the training images are summarised by digests.py (content walk); here the annotation files
and tools are pinned by their own sha256 taken at the start of this contract.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXPECTED = {
    "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth":
        "2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff",
}


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pin", help="JSON of {path: sha256} to check in addition")
    ap.add_argument("--override", action="append", default=[], help="PATH=FILE: read FILE in place of PATH")
    args = ap.parse_args()
    expected = dict(EXPECTED)
    if args.pin:
        expected.update(json.loads(Path(args.pin).read_text()))
    overrides = dict(o.split("=", 1) for o in args.override)
    rows, bad = [], 0
    for rel, want in expected.items():
        path = Path(overrides.get(rel, ROOT / rel))
        got = sha(path) if path.is_file() else None
        ok = got == want
        bad += not ok
        rows.append({"path": rel, "read": str(path), "exists": path.is_file(), "sha256": got, "expected": want, "match": ok})
    print(json.dumps({"entries": len(rows), "mismatches": bad, "rows": rows}, indent=1))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

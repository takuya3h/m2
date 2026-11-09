"""Task A-5 / B-3 (T-2026-11-07-dtower-rerun): the videos each fold's datasets serve equal the
conventions#folds table.

For every fold the detector config the runs use is loaded the way ``main.py`` loads it (Relation-DETR
``Config`` with ``EGO_ANN_DIR`` of the fold), and the evaluation script's test dataset is built the way
``scripts/eval_relation_detr_map.py --split test`` builds it. The served image ids (after the
training filter of images without boxes) are mapped to video ids and compared with the table.
The per-rank DataLoader length expected for 2 processes and the per-GPU batch is printed as well;
the measured length comes from the Task B controls.

    .venv-relation-detr/bin/python check_folds.py --config <config copy> --out <json> [--inject-test FOLD]
    exit 0 when every set matches, 1 otherwise. --inject-test adds the fold's first test video to its
    val set (a positive control: the check must fail).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPO = ROOT / "third_party/Relation-DETR"
# conventions#folds (正本 docs/stage0/A1_fold_table.md). train is the other 10 of 01..15.
TABLE = {"A": {"test": ["04", "05", "07"], "val": ["09", "10"]},
         "B": {"test": ["01", "03", "14"], "val": ["02", "08"]},
         "C": {"test": ["02", "08", "11"], "val": ["06", "12"]},
         "D": {"test": ["06", "13", "15"], "val": ["04", "05"]},
         "E": {"test": ["09", "10", "12"], "val": ["07", "15"]}}
ALL = [f"{i:02d}" for i in range(1, 16)]


def served(dataset):
    ids = [dataset.ids[i] for i in dataset.indices] if hasattr(dataset, "indices") else list(dataset.ids)
    return ids, sorted({Path(str(dataset.coco.imgs[i]["file_name"])).name[:2] for i in ids})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--inject-test")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    from datasets.coco import CocoDetection
    from util.lazy_load import Config

    os.environ.setdefault("EGO_ROOT", str(ROOT / "data/raw/ego"))
    os.environ.update(DTOWER_LR="1e-4", DTOWER_WEIGHT_DECAY="1e-4", DTOWER_MAX_NORM="0.1",
                      RELDETR_OUTPUT_DIR="/nonexistent-not-written", PROBE_BATCH_SIZE=str(args.batch),
                      PROBE_NUM_WORKERS="4",
                      RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"))
    os.environ.pop("DTOWER_EVAL_SPLIT", None)
    rows, bad = [], 0
    for fold, sets in TABLE.items():
        ann = ROOT / "data/annotations/egosurgery_tool_folds" / fold
        os.environ["EGO_ANN_DIR"] = str(ann)
        cfg = Config(args.config, partials=("lr_scheduler", "optimizer", "param_dicts"))
        test = CocoDetection(img_folder=os.environ["EGO_ROOT"], ann_file=f"{ann}/instances_test.json", transforms=None)
        expected = {"test": sets["test"], "val": sets["val"],
                    "train": sorted(set(ALL) - set(sets["test"]) - set(sets["val"]))}
        found = {}
        counts = {}
        for split, dataset in (("train", cfg.train_dataset), ("val", cfg.test_dataset), ("test", test)):
            ids, videos = served(dataset)
            found[split], counts[split] = videos, len(ids)
        if args.inject_test == fold:
            found["val"] = sorted(set(found["val"]) | {sets["test"][0]})
        match = {split: found[split] == expected[split] for split in expected}
        disjoint = not (set(found["train"]) & set(found["val"]) or set(found["train"]) & set(found["test"])
                        or set(found["val"]) & set(found["test"]))
        ok = all(match.values()) and disjoint
        bad += not ok
        per_rank = math.ceil(counts["train"] / 2)
        rows.append({"fold": fold, "found": found, "expected": expected, "match": match, "disjoint": disjoint,
                     "served_frames": counts, "batch_cfg": cfg.batch_size,
                     "expected_loader_length_per_rank": math.ceil(per_rank / args.batch)})
    Path(args.out).write_text(json.dumps({"folds": rows, "mismatches": bad, "inject_test": args.inject_test},
                                         indent=1) + "\n")
    print(f"check_folds mismatches={bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

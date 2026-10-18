"""Task E-3: 検出の交差適合用の塔の注釈を作る（非公式 T-2026-10-18-stage2-pilot-folda）。

折り A の instances_train.json を動画単位で H1 だけ（または H2 だけ）に絞った instances_train.json と、
折り A の instances_val.json の写しを、版管理の外（STORE/ann_cf/<半分>/）に置く。test の注釈は置かない。
既存の注釈は読むだけで変えない。--smoke は H1 の先頭 n 枚だけの試走用。

    python scripts/stage2pilot/make_cf_annotations.py --split <split.json> [--smoke 40]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402


def subset(blob, videos, limit=None):
    imgs = [im for im in blob["images"] if Path(im["file_name"]).parent.name in videos]
    if limit:
        imgs = imgs[:limit]
    keep = {im["id"] for im in imgs}
    out = {k: v for k, v in blob.items() if k not in ("images", "annotations")}
    out["images"] = imgs
    out["annotations"] = [a for a in blob["annotations"] if a["image_id"] in keep]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--smoke", type=int, default=0)
    a = ap.parse_args()
    split = json.loads(Path(a.split).read_text())["chosen"]
    blob = json.loads((C.DET_ANN_A / "instances_train.json").read_text())
    rec = {"task_id": C.TASK_ID, "source": str(C.DET_ANN_A / "instances_train.json"),
           "source_sha256": C.sha256(C.DET_ANN_A / "instances_train.json"), "halves": {}}
    halves = {"H1smoke": split["H1"]} if a.smoke else {"H1": split["H1"], "H2": split["H2"]}
    for name, videos in halves.items():
        C.assert_no_test(videos, "make_cf_annotations")
        out_dir = C.STORE / "ann_cf" / name
        out_dir.mkdir(parents=True, exist_ok=True)
        sub = subset(blob, set(videos), a.smoke or None)
        (out_dir / "instances_train.json").write_text(json.dumps(sub))
        shutil.copyfile(C.DET_ANN_A / "instances_val.json", out_dir / "instances_val.json")
        got = sorted({Path(im["file_name"]).parent.name for im in sub["images"]})
        rec["halves"][name] = {"videos": got, "images": len(sub["images"]), "annotations": len(sub["annotations"]),
                               "dir": str(out_dir), "train_sha256": C.sha256(out_dir / "instances_train.json"),
                               "val_sha256": C.sha256(out_dir / "instances_val.json"),
                               "test_file_present": (out_dir / "instances_test.json").exists()}
        assert a.smoke or got == sorted(videos)
    out = C.ANALYSIS / "crossfit" / ("annotations_smoke.json" if a.smoke else "annotations.json")
    C.write_json(out, rec)
    print(json.dumps(rec["halves"], ensure_ascii=False))


if __name__ == "__main__":
    main()

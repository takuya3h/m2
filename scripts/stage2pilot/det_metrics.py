"""検出の指標（非公式 T-2026-10-18-stage2-pilot-folda）。両方の venv で動く（numpy と pycocotools だけ）。

COCO の検出結果（image_id, category_id, bbox=[x, y, w, h], score）から、
overall mAP（AP@[.5:.95]）、クラス別 AP（area all、maxDets 100。eval_relation_detr_map.py と同じ取り方）、
標的群 AP と陰性対照群 AP（conventions#det_groups の表から読む。評価集合に出現しないクラスは除いて記録）、
動画ごとの mAP を出す。
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import re
from pathlib import Path

import numpy as np
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval as CocoEvalAlias

ROOT = Path(__file__).resolve().parents[2]
GROUP_KEYS = {"標的群": "target", "陰性対照群": "control"}


def read_groups() -> dict[str, list[str]]:
    text = (ROOT / "context/conventions.md").read_text()
    m = re.search(r'<a id="det_groups"></a>\n(.*?)(?=<a id="|\Z)', text, re.S)
    groups = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] in GROUP_KEYS:
            groups[GROUP_KEYS[cells[0]]] = [c.strip() for c in cells[1].split("、")]
    assert set(groups) == set(GROUP_KEYS.values()), groups
    return groups


def _eval(gt: COCO, results: list, img_ids) -> CocoEvalAlias:
    with contextlib.redirect_stdout(io.StringIO()):
        dt = gt.loadRes(results) if results else COCO()
        ev = CocoEvalAlias(gt, dt, "bbox")
        ev.params.imgIds = sorted(img_ids)
        ev.evaluate()
        ev.accumulate()
        ev.summarize()
    return ev


def summary(ann_file, results: list, img_ids=None) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        gt = COCO(str(ann_file))
    ids = sorted(img_ids) if img_ids is not None else sorted(gt.getImgIds())
    ev = _eval(gt, results, ids)
    prec = ev.eval["precision"]
    names = {c["id"]: c["name"] for c in gt.loadCats(gt.getCatIds())}
    per_class = {}
    for k, cid in enumerate(ev.params.catIds):
        p = prec[:, :, k, 0, -1]
        p = p[p > -1]
        per_class[names[cid]] = float(p.mean()) if p.size else float("nan")
    out = {"AP": float(ev.stats[0]), "AP50": float(ev.stats[1]), "per_class_ap": per_class, "n_images": len(ids)}
    for g, classes in read_groups().items():
        used = [per_class[c] for c in classes if not math.isnan(per_class[c])]
        out[f"{g}_AP"] = float(np.mean(used)) if used else None
        out[f"{g}_missing"] = [c for c in classes if math.isnan(per_class[c])]
    by_video = {}
    for i in ids:
        by_video.setdefault(Path(gt.imgs[i]["file_name"]).stem.split("_")[0], []).append(i)
    out["per_video_AP"] = {v: float(_eval(gt, [r for r in results if r["image_id"] in set(vi)], vi).stats[0])
                           for v, vi in sorted(by_video.items())}
    return out


def load_results(path) -> list:
    import gzip
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        return json.load(f)


def max_output_diff(a: list, b: list) -> dict:
    """二つの検出結果の、画像ごとの順位をそろえた score と bbox の差の最大値。件数が違えば None。"""
    def by_img(rs):
        d = {}
        for r in rs:
            d.setdefault(r["image_id"], []).append(r)
        return {k: sorted(v, key=lambda r: -r["score"]) for k, v in d.items()}
    A, B = by_img(a), by_img(b)
    if set(A) != set(B) or any(len(A[k]) != len(B[k]) for k in A):
        return {"comparable": False}
    ds, db, dl = 0.0, 0.0, 0
    for k in A:
        sa = np.array([r["score"] for r in A[k]])
        sb = np.array([r["score"] for r in B[k]])
        ds = max(ds, float(np.abs(sa - sb).max()))
        db = max(db, float(np.abs(np.array([r["bbox"] for r in A[k]]) - np.array([r["bbox"] for r in B[k]])).max()))
        dl += int(sum(ra["category_id"] != rb["category_id"] for ra, rb in zip(A[k], B[k])))
    return {"comparable": True, "max_abs_score_diff": ds, "max_abs_bbox_diff_px": db, "label_mismatch": dl}

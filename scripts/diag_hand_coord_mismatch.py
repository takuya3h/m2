#!/usr/bin/env python
"""raw02 vs hand4 手 bbox 座標系不一致の診断（読み取り専用・GPU 不要）。

仮説検定（ユーザ指定）:
  raw02 と hand4 の手 bbox に大域的な相似変換（per-axis スケール＋オフセット）を最小二乗で
  当てはめ、変換後の best-IoU 分布を再計算する。
  - 変換後 IoU median > 0.9 → 座標規約の違い。写像だけで欠落動画を復活できる。
  - 跳ねない          → 別世代の独立アノテーション。全 downstream の再導出が必要。

対応付け: 同一フレーム・カテゴリ対応（raw02 cat = hand4 cat + 1）で 1:1 の組のみ採用
  （多重時は中心最近傍でも組むが、fit は 1:1 純度の高い組だけで頑健化）。
出力: experiments/analysis/hts_raw_provenance_2026-07-29/hand_coord_mismatch.json
"""
from __future__ import annotations
import json
import glob
import os
import collections
import statistics as st
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/OpenSurgery_Dataset/02_hand/json_per_video"
HAND4 = ROOT / "data/annotations/egosurgery_hand4"
OUT = ROOT / "experiments/analysis/hts_raw_provenance_2026-07-29/hand_coord_mismatch.json"

# hand4 cat -> raw02 cat（Own/Other × L/R が +1 でずれる）
CAT_MAP = {0: 1, 1: 2, 2: 3, 3: 4}


def base(fn):
    return os.path.basename(fn)


def to_xyxy(b):
    x, y, w, h = b
    return [x, y, x + w, y + h]


def iou_xyxy(a, b):
    ix, iy = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix) * max(0, iy2 - iy)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def quant(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return {"min": round(v[0], 4), "q1": round(v[n // 4], 4), "median": round(v[n // 2], 4),
            "q3": round(v[3 * n // 4], 4), "max": round(v[-1], 4), "mean": round(st.mean(v), 4), "n": n}


def load_raw():
    boxes = collections.defaultdict(list)
    for f in glob.glob(str(RAW / "*/*.json")):
        d = json.load(open(f))
        m = {im["id"]: base(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            boxes[m[a["image_id"]]].append((a["category_id"], to_xyxy(a["bbox"])))
    return boxes


def load_hand4():
    boxes = collections.defaultdict(list)
    for sp in ("train", "val", "test"):
        d = json.load(open(HAND4 / f"instances_{sp}.json"))
        m = {im["id"]: base(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            boxes[m[a["image_id"]]].append((a["category_id"], to_xyxy(a["bbox"])))
    return boxes


def main():
    raw = load_raw()
    h4 = load_hand4()
    common = sorted(set(raw) & set(h4))

    # 1:1 純対応（各フレームで cat がユニークな組のみ）で fit 用点を集める
    src_pts, dst_pts = [], []  # hand4 corner -> raw02 corner
    for fn in common:
        rcat = collections.defaultdict(list)
        for c, b in raw[fn]:
            rcat[c].append(b)
        hcat = collections.defaultdict(list)
        for c, b in h4[fn]:
            hcat[c].append(b)
        for hc, hb_list in hcat.items():
            rc = CAT_MAP.get(hc)
            if rc is None or len(hb_list) != 1 or len(rcat.get(rc, [])) != 1:
                continue
            hb, rb = hb_list[0], rcat[rc][0]
            src_pts += [(hb[0], hb[1]), (hb[2], hb[3])]
            dst_pts += [(rb[0], rb[1]), (rb[2], rb[3])]

    src = np.array(src_pts, float)
    dst = np.array(dst_pts, float)
    # per-axis: raw_x = ax*h_x + bx ; raw_y = ay*h_y + by（最小二乗）
    ax, bx = np.polyfit(src[:, 0], dst[:, 0], 1)
    ay, by = np.polyfit(src[:, 1], dst[:, 1], 1)

    def apply(b):  # xyxy
        return [ax * b[0] + bx, ay * b[1] + by, ax * b[2] + bx, ay * b[3] + by]

    # 変換前後の best-IoU（hand4 box -> 同フレーム raw02 の最良、cat 対応内で）
    iou_before, iou_after = [], []
    for fn in common:
        rcat = collections.defaultdict(list)
        for c, b in raw[fn]:
            rcat[c].append(b)
        for hc, hb in h4[fn]:
            rc = CAT_MAP.get(hc)
            cands = rcat.get(rc, []) or [b for _, b in raw[fn]]
            if not cands:
                continue
            iou_before.append(max(iou_xyxy(hb, rb) for rb in cands))
            hb2 = apply(hb)
            iou_after.append(max(iou_xyxy(hb2, rb) for rb in cands))

    # 手数の一致（同フレームで手インスタンス数が一致するか）
    count_match = sum(1 for fn in common if len(raw[fn]) == len(h4[fn]))
    res = {
        "coordinate_ranges": {"raw02": "[0,0,1920,1080] img 1920x1080",
                              "hand4": "[0,0,1920,1080] img 1920x1080", "same_pixel_space": True},
        "fit_pairs": len(src_pts) // 2,
        "similarity_transform_hand4_to_raw02": {"scale_x": round(ax, 5), "offset_x": round(bx, 3),
                                                "scale_y": round(ay, 5), "offset_y": round(by, 3)},
        "iou_before_transform": quant(iou_before),
        "iou_after_transform": quant(iou_after),
        "frames_common": len(common),
        "frames_hand_count_equal": count_match,
        "frames_hand_count_equal_pct": round(count_match / len(common) * 100, 1) if common else None,
    }
    med_after = res["iou_after_transform"]["median"] if res["iou_after_transform"] else 0
    res["verdict"] = (
        "座標規約の違い（写像で復活可）" if med_after and med_after > 0.9
        else "別世代の独立アノテーション（全 downstream 再導出が必要）")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res


if __name__ == "__main__":
    main()

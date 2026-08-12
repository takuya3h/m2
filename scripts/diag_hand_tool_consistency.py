#!/usr/bin/env python
"""raw02 vs hand4：どちらの手アノテが tool と物理的に整合するか（読み取り専用・GPU 不要）。

L2 は手の局在を注入する。手が tool とズレていれば陰性が出るが、それは「局在は効かない」でなく
アノテーションのズレの帰結（撤退ラインの誤強化）。物理事前分布「手は術具を握っている」で判定する。

同一 tool box 集合（egosurgery_tool_hand の tool IDs=EDA と同一）に対し、手を hand4 と raw02 で
入れ替えて接触統計を再現比較する。既知 EDA 値（hand4 世代で算出）:
  frac_tool_overlap_hand_iou>0.1 = 0.561 / frac_near_dist<0.15diag = 0.596 / active-phase contact ≈0.959
接触統計をより良く（より高く=手が tool により重なる）再現する方が正本。完全性より整合性を優先。

時刻ずれ検査: 同一 basename の raw02 箱を hand4 の frame ±1/±2/±5/±10 と照合し IoU ピーク位置を見る。
IoU median 0.52 は独立アノテにしては低く（通常0.75-0.85）時刻ずれの兆候。

出力: experiments/analysis/hts_raw_provenance_2026-07-29/hand_tool_consistency.json
"""
from __future__ import annotations
import json
import glob
import os
import csv
import math
import statistics as st
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data/annotations"
RAW = ROOT / "data/raw/OpenSurgery_Dataset/02_hand/json_per_video"
OUT = ROOT / "experiments/analysis/hts_raw_provenance_2026-07-29/hand_tool_consistency.json"

DIAG = math.hypot(1920, 1080)  # 2203.6
NEAR = 0.15 * DIAG
# 能動工程（術具を握っている想定）
ACTIVE_PHASES = {"incision", "dissection", "hemostasis", "closure"}
CAT_MAP_H4_TO_RAW = {0: 1, 1: 2, 2: 3, 3: 4}


def load(p):
    return json.load(open(p))


def bn(fn):
    return os.path.splitext(os.path.basename(fn))[0]


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix, iy = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, ix2 - ix) * max(0, iy2 - iy)
    ua = aw * ah + bw * bh - inter
    return inter / ua if ua > 0 else 0.0


def center(b):
    return (b[0] + b[2] / 2, b[1] + b[3] / 2)


def load_phase():
    ph = {}
    for f in glob.glob(str(ANN / "egosurgery_phase/*.csv")):
        for row in csv.DictReader(open(f)):
            k = row.get("Frame") or row.get("frame")
            v = row.get("Phase") or row.get("phase")
            if k:
                ph[k] = v
    return ph


def load_tool_and_hand4():
    """egosurgery_tool_hand から tool boxes と hand4 手 boxes を分離（EDA と同一入力）。"""
    tool = defaultdict(list)
    hand = defaultdict(list)
    for sp in ("train", "val", "test"):
        d = load(ANN / f"egosurgery_tool_hand/instances_{sp}.json")
        cats = {c["id"]: c["name"] for c in d["categories"]}
        m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            name = cats[a["category_id"]].lower()
            (hand if "hand" in name else tool)[m[a["image_id"]]].append(a["bbox"])
    return tool, hand


def load_raw02_hands():
    hand = defaultdict(list)
    for f in glob.glob(str(RAW / "*/*.json")):
        d = load(f)
        m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            hand[m[a["image_id"]]].append(a["bbox"])
    return hand


def contact_stats(tool_by_frame, hand_by_frame, phase):
    """EDA と同一定義で tool 側から見た手接触統計を算出。"""
    max_ious, min_dists = [], []
    n_tool = overlap = near = 0
    frames_contact = 0
    by_phase_num, by_phase_den = Counter(), Counter()
    for fr, tools in tool_by_frame.items():
        hands = hand_by_frame.get(fr, [])
        has_contact = False
        for tb in tools:
            n_tool += 1
            if not hands:
                max_ious.append(0.0)
                continue
            tcx, tcy = center(tb)
            mi = max(iou(tb, hb) for hb in hands)
            md = min(math.hypot(tcx - center(hb)[0], tcy - center(hb)[1]) for hb in hands)
            max_ious.append(mi)
            min_dists.append(md)
            if mi > 0.1:
                overlap += 1
                has_contact = True
            if md < NEAR:
                near += 1
        ph = phase.get(fr)
        if ph:
            by_phase_den[ph] += 1
            if has_contact:
                by_phase_num[ph] += 1
        if has_contact:
            frames_contact += 1
    active_num = sum(by_phase_num[p] for p in ACTIVE_PHASES)
    active_den = sum(by_phase_den[p] for p in ACTIVE_PHASES)
    return {
        "n_tool_boxes": n_tool,
        "frac_overlap_iou>0.1": round(overlap / n_tool, 3) if n_tool else None,
        "frac_near_dist<0.15diag": round(near / n_tool, 3) if n_tool else None,
        "mean_max_iou_tool_hand": round(st.mean(max_ious), 3) if max_ious else None,
        "median_min_center_dist_px": round(st.median(min_dists), 1) if min_dists else None,
        "frames_with_contact": frames_contact,
        "active_phase_contact_rate": round(active_num / active_den, 3) if active_den else None,
        "contact_rate_by_phase": {p: round(by_phase_num[p] / by_phase_den[p], 3)
                                  for p in sorted(by_phase_den) if by_phase_den[p]},
    }


def frame_num(k):
    parts = k.split("_")
    try:
        return int(parts[-1])
    except ValueError:
        return None


def timeshift_check(raw_hand, hand4_by_cat):
    """raw02 箱を hand4 の frame±offset と照合（cat 対応）。offset 別 median IoU。"""
    # video -> {framenum -> {rawcat -> [boxes]}}
    def index(hand_by_frame_cat):
        idx = defaultdict(dict)
        for fr, catboxes in hand_by_frame_cat.items():
            n = frame_num(fr)
            vid = "_".join(fr.split("_")[:2])
            if n is not None:
                idx[vid][n] = catboxes
        return idx
    ridx = index(raw_hand)
    hidx = index(hand4_by_cat)
    offsets = [0, 1, -1, 2, -2, 5, -5, 10, -10]
    res = {}
    for off in offsets:
        ious = []
        for vid, frames in ridx.items():
            hv = hidx.get(vid, {})
            for n, rcats in frames.items():
                hcats = hv.get(n + off)
                if not hcats:
                    continue
                for rc, rboxes in rcats.items():
                    hboxes = hcats.get(rc, [])
                    for rb in rboxes:
                        if hboxes:
                            ious.append(max(iou(rb, hb) for hb in hboxes))
        res[off] = {"n": len(ious), "median_iou": round(st.median(ious), 4) if ious else None}
    return res


def main():
    phase = load_phase()
    tool, hand4 = load_tool_and_hand4()
    raw02 = load_raw02_hands()

    stats_hand4 = contact_stats(tool, hand4, phase)
    stats_raw02 = contact_stats(tool, raw02, phase)

    # 時刻ずれ用に cat 別 index（raw02 cat1-4 / hand4 は raw cat へ写像）
    raw_by_cat = defaultdict(lambda: defaultdict(list))
    for f in glob.glob(str(RAW / "*/*.json")):
        d = load(f)
        m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            raw_by_cat[m[a["image_id"]]][a["category_id"]].append(a["bbox"])
    h4_by_cat = defaultdict(lambda: defaultdict(list))
    for sp in ("train", "val", "test"):
        d = load(ANN / f"egosurgery_hand4/instances_{sp}.json")
        m = {im["id"]: bn(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            h4_by_cat[m[a["image_id"]]][CAT_MAP_H4_TO_RAW[a["category_id"]]].append(a["bbox"])
    shift = timeshift_check({k: dict(v) for k, v in raw_by_cat.items()},
                            {k: dict(v) for k, v in h4_by_cat.items()})

    ref = {"frac_overlap_iou>0.1": 0.561, "frac_near_dist<0.15diag": 0.596,
           "active_phase_contact": 0.959, "source": "hand4 世代(egosurgery_tool_hand)で算出=stats_extra.json"}
    # 判定: overlap/near/contact が高い方が tool と整合（物理事前分布）
    def score(s):
        return (s["frac_overlap_iou>0.1"] or 0) + (s["frac_near_dist<0.15diag"] or 0) + (s["active_phase_contact_rate"] or 0)
    winner = "raw02" if score(stats_raw02) > score(stats_hand4) else "hand4"
    peak_off = max(shift, key=lambda o: (shift[o]["median_iou"] or 0))

    res = {
        "reference_EDA": ref,
        "tool_boxes_source": "egosurgery_tool_hand tool IDs（EDA と同一）",
        "contact_stats_hand4": stats_hand4,
        "contact_stats_raw02": stats_raw02,
        "timeshift_iou_by_offset": shift,
        "timeshift_peak_offset": peak_off,
        "verdict_canonical": winner,
        "note": "接触統計が高い方=手が tool により整合=正本。時刻ずれは peak_offset≠0 なら該当。",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(json.dumps({k: v for k, v in res.items() if k != "timeshift_iou_by_offset"}, indent=2, ensure_ascii=False))
    print("\n--- timeshift median IoU by offset ---")
    for o in [0, 1, -1, 2, -2, 5, -5, 10, -10]:
        print(f"  offset {o:+d}: median_iou={shift[o]['median_iou']} (n={shift[o]['n']})")
    return res


if __name__ == "__main__":
    main()

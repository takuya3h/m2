#!/usr/bin/env python3
"""T2: SAM 指紋検査 — HTS のマスクが tool bbox から機械生成されたものかを判定する。

§1.4-i の説明「既存 bbox を条件に SAM で生成し、その後人手で確認・修正した」の真偽を測る。
マスクが bbox 条件付き生成なら mask は bbox にほぼ完全に内包され、
IoU / 内包率が特定値に鋭く集中する。前バンドル (偽物) の指紋は 内包率 mean≈0.879 / IoU median≈0.927。

重要: マスク側 JSON の ann['bbox'] は mask の外接矩形から導出されており (実測で差が常に 1px = w/h 規約差)、
独立な検出 box ではない。したがって照合相手は必ず外部の canonical tool/hand bbox を使う。

この検査は G-2 / G-3 のみをゲートする。G-1 は mask ではなく関係ラベルを使うため対象外。

Usage:
    python3 scripts/analysis/hts_sam_fingerprint.py --out $OUT
    python3 scripts/analysis/hts_sam_fingerprint.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import defaultdict

import numpy as np
from pycocotools import mask as mu

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTS = os.path.join(REPO, "data/raw/OpenSurgery_Dataset/05_egosurgery_hts")
HANDS_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/hands")
SPLITS = ["train", "val", "test"]

# 前バンドル (2026-07-10 入手・偽物) の SAM 指紋 (§1.5)
REF_INCLUSION_MEAN = 0.879
REF_IOU_MEDIAN = 0.927

SIGNATURE_TOOLS = ["Bipolar Forceps", "Scalpel", "Needle Holders"]
HT_TOOL_CATS = {3, 4, 5}   # Left Hand Tool / Right Hand Tool / Two Hands Tool
HT_HAND_CATS = {1, 2}      # First Person's Left/Right Hand


# --------------------------------------------------------------------------- #
def rle_of(seg, h, w):
    """segmentation を RLE に正規化する。"""
    if isinstance(seg, list):                      # polygon
        return mu.merge(mu.frPyObjects(seg, h, w))
    if isinstance(seg, dict) and isinstance(seg.get("counts"), list):
        return mu.frPyObjects(seg, h, w)           # uncompressed RLE
    if isinstance(seg, dict):
        c = seg["counts"]
        return {"size": seg["size"], "counts": c.encode() if isinstance(c, str) else c}
    raise TypeError(f"unsupported segmentation: {type(seg)}")


def mask_rect_and_area(seg, h, w):
    """mask の外接矩形 [x,y,w,h] と画素面積を返す (decode せず高速に)。"""
    rle = rle_of(seg, h, w)
    bb = mu.toBbox(rle).astype(float)      # [x, y, w, h]
    area = float(mu.area(rle))
    return bb, area


def rect_iou(a, b):
    """[x,y,w,h] 同士の IoU。"""
    ax0, ay0, aw, ah = a; bx0, by0, bw, bh = b
    ax1, ay1 = ax0 + aw, ay0 + ah
    bx1, by1 = bx0 + bw, by0 + bh
    ix = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    iy = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def rect_inter_area(a, b):
    ax0, ay0, aw, ah = a; bx0, by0, bw, bh = b
    ix = max(0.0, min(ax0 + aw, bx0 + bw) - max(ax0, bx0))
    iy = max(0.0, min(ay0 + ah, by0 + bh) - max(ay0, by0))
    return ix * iy


def greedy_match(masks, boxes):
    """同一画像内で mask外接矩形 と bbox を IoU 最大で貪欲マッチング。

    masks: [(idx, rect, area, cat)], boxes: [(idx, rect, cat)]
    returns (pairs, n_unmatched_mask, n_unmatched_box)
    """
    cand = []
    for mi, (m_i, m_rect, m_area, m_cat) in enumerate(masks):
        for bi, (b_i, b_rect, b_cat) in enumerate(boxes):
            iou = rect_iou(m_rect, b_rect)
            if iou > 0:
                cand.append((iou, mi, bi))
    cand.sort(key=lambda x: -x[0])
    used_m, used_b, pairs = set(), set(), []
    for iou, mi, bi in cand:
        if mi in used_m or bi in used_b:
            continue
        used_m.add(mi); used_b.add(bi)
        pairs.append((mi, bi, iou))
    return pairs, len(masks) - len(used_m), len(boxes) - len(used_b)


def stats(v):
    a = np.asarray(v, dtype=float)
    if a.size == 0:
        return {k: None for k in
                ["n", "min", "q1", "median", "q3", "max", "mean", "std", "iqr"]}
    q1, med, q3 = np.percentile(a, [25, 50, 75])
    return {"n": int(a.size), "min": float(a.min()), "q1": float(q1),
            "median": float(med), "q3": float(q3), "max": float(a.max()),
            "mean": float(a.mean()), "std": float(a.std()), "iqr": float(q3 - q1)}


def histogram(v, width=0.02, lo=0.0, hi=1.0):
    a = np.asarray(v, dtype=float)
    nb = int(round((hi - lo) / width))
    edges = np.linspace(lo, hi, nb + 1)
    cnt, _ = np.histogram(np.clip(a, lo, hi), bins=edges)
    return [{"bin_lo": round(float(edges[i]), 4), "bin_hi": round(float(edges[i + 1]), 4),
             "count": int(cnt[i])} for i in range(nb)]


# --------------------------------------------------------------------------- #
def load_boxes_by_basename(paths, cat_filter=None):
    """COCO 群から {basename: [(ann_idx, [x,y,w,h], category_name)]} と画像サイズを作る。"""
    out = defaultdict(list)
    sizes = {}
    catmap = {}
    for p in paths:
        with open(p) as f:
            d = json.load(f)
        cats = {c["id"]: c["name"] for c in d.get("categories", [])}
        catmap.update(cats)
        id2b = {}
        for im in d["images"]:
            b = os.path.basename(im["file_name"])
            id2b[im["id"]] = b
            sizes[b] = (im["height"], im["width"])
        for i, a in enumerate(d["annotations"]):
            if a["image_id"] not in id2b:
                continue
            if cat_filter and a["category_id"] not in cat_filter:
                continue
            out[id2b[a["image_id"]]].append((i, [float(x) for x in a["bbox"]],
                                             cats.get(a["category_id"], str(a["category_id"]))))
    return out, sizes, catmap


def load_masks_by_basename(paths, cat_filter=None):
    """COCO 群から {basename: [(ann_idx, segmentation, category_name)]} を作る。"""
    out = defaultdict(list)
    sizes = {}
    for p in paths:
        with open(p) as f:
            d = json.load(f)
        cats = {c["id"]: c["name"] for c in d.get("categories", [])}
        id2b = {}
        for im in d["images"]:
            b = os.path.basename(im["file_name"])
            id2b[im["id"]] = b
            sizes[b] = (im["height"], im["width"])
        for i, a in enumerate(d["annotations"]):
            if a["image_id"] not in id2b or not a.get("segmentation"):
                continue
            if cat_filter and a["category_id"] not in cat_filter:
                continue
            out[id2b[a["image_id"]]].append((i, a["segmentation"],
                                             cats.get(a["category_id"], str(a["category_id"]))))
    return out, sizes


def run_track(mask_src, box_src, label, mask_cat_filter=None, box_cat_filter=None,
              class_from="box"):
    """1 トラック分の照合を実行し、指標を集める。"""
    masks, msizes = load_masks_by_basename(mask_src, mask_cat_filter)
    boxes, bsizes, _ = load_boxes_by_basename(box_src, box_cat_filter)

    common = sorted(set(masks) & set(boxes))
    rec = {"iou": [], "inclusion": [], "fill": [], "cls": []}
    n_um, n_ub, n_pairs, size_mismatch = 0, 0, 0, 0

    for b in common:
        h, w = msizes.get(b, bsizes.get(b, (None, None)))
        if h is None:
            continue
        # 座標系一致の確認 (mask 側 RLE の size と bbox 側の画像サイズ)
        if b in bsizes and b in msizes and msizes[b] != bsizes[b]:
            size_mismatch += 1
            continue
        mlist = []
        for i, seg, cname in masks[b]:
            try:
                rect, area = mask_rect_and_area(seg, h, w)
            except Exception:
                continue
            if rect[2] <= 0 or rect[3] <= 0:
                continue
            mlist.append((i, rect, area, cname))
        blist = [(i, r, c) for i, r, c in boxes[b] if r[2] > 0 and r[3] > 0]
        if not mlist or not blist:
            n_um += len(mlist); n_ub += len(blist)
            continue
        pairs, um, ub = greedy_match(mlist, blist)
        n_um += um; n_ub += ub
        for mi, bi, iou in pairs:
            _, m_rect, m_area, m_cls = mlist[mi]
            _, b_rect, b_cls = blist[bi]
            m_rect_area = m_rect[2] * m_rect[3]
            inter = rect_inter_area(m_rect, b_rect)
            incl = inter / m_rect_area if m_rect_area > 0 else 0.0
            b_area = b_rect[2] * b_rect[3]
            fill = m_area / b_area if b_area > 0 else 0.0
            rec["iou"].append(iou); rec["inclusion"].append(incl); rec["fill"].append(fill)
            rec["cls"].append(b_cls if class_from == "box" else m_cls)
            n_pairs += 1

    overall = {k: stats(rec[k]) for k in ("iou", "inclusion", "fill")}
    per_class = {}
    cls_arr = np.array(rec["cls"])
    for c in sorted(set(rec["cls"])):
        m = cls_arr == c
        per_class[c] = {k: stats(np.asarray(rec[k])[m]) for k in ("iou", "inclusion", "fill")}

    return {
        "label": label,
        "n_common_images": len(common),
        "n_pairs": n_pairs,
        "n_unmatched_mask": n_um,
        "n_unmatched_box": n_ub,
        "n_size_mismatch_images": size_mismatch,
        "overall": overall,
        "per_class": per_class,
        "_raw": rec,
    }


def judge(overall):
    """Step 2-3 の判定。"""
    incl_mean = overall["inclusion"]["mean"]
    iou_med = overall["iou"]["median"]
    iou_iqr = overall["iou"]["iqr"]
    incl_lo = overall["inclusion"]  # for tail check we use q1
    if incl_mean is None:
        return "SKIP", "照合ペアが 0 件"
    sam_like = (0.86 <= incl_mean <= 0.90) and (0.91 <= iou_med <= 0.94) and (iou_iqr < 0.10)
    human_like = (iou_iqr >= 0.15) and (incl_lo["q1"] < 0.95)
    if sam_like:
        return "FAIL", ("SAM 由来の指紋と一致 (内包率 mean 0.86-0.90 かつ IoU median 0.91-0.94 に "
                        f"IQR<0.10 で集中: incl_mean={incl_mean:.4f}, iou_med={iou_med:.4f}, "
                        f"iou_iqr={iou_iqr:.4f})。G-2 / G-3 は中止")
    if human_like:
        return "PASS", (f"分布が広く bbox からはみ出す例が有意に存在 (iou_iqr={iou_iqr:.4f}>=0.15, "
                        f"inclusion_q1={incl_lo['q1']:.4f}<0.95)。人手アノテーションとして扱える")
    return "WARN", (f"どちらの条件にも当てはまらない (incl_mean={incl_mean:.4f}, "
                    f"iou_med={iou_med:.4f}, iou_iqr={iou_iqr:.4f})。ヒストグラムを添えて判断を仰ぐ")


# --------------------------------------------------------------------------- #
def self_test() -> int:
    """検出できることを確認する:
       (1) mask が bbox に完全内包される合成ケースで 内包率≈1 / 高 IoU を検出できるか
       (2) mask が bbox からはみ出す合成ケースで 内包率<1 を検出できるか
       (3) toBbox/area ベースの計測が decode ベースと一致するか (高速化の妥当性)
    """
    ok = True
    H = W = 64

    def mk(y0, y1, x0, x1):
        m = np.zeros((H, W), dtype=np.uint8, order="F")
        m[y0:y1, x0:x1] = 1
        return mu.encode(m)

    # (1) mask ⊂ bbox
    rle = mk(10, 30, 10, 30)
    rect, area = mask_rect_and_area(rle, H, W)
    box = [8.0, 8.0, 24.0, 24.0]          # mask を包む大きめの box
    incl = rect_inter_area(rect, box) / (rect[2] * rect[3])
    if not (abs(incl - 1.0) < 1e-9):
        print(f"  [FAIL] 完全内包ケースで内包率 {incl}"); ok = False
    else:
        print("  [OK]   mask ⊂ bbox のとき内包率 1.0 を検出")

    # (2) はみ出し
    box2 = [20.0, 20.0, 10.0, 10.0]        # mask の一部しか覆わない
    incl2 = rect_inter_area(rect, box2) / (rect[2] * rect[3])
    if not (incl2 < 0.5):
        print(f"  [FAIL] はみ出しケースで内包率 {incl2}"); ok = False
    else:
        print(f"  [OK]   mask ⊄ bbox のとき内包率 {incl2:.3f} (<0.5) を検出")

    # (3) decode ベースとの一致
    m = mu.decode(rle)
    ys, xs = np.nonzero(m)
    ref_rect = [float(xs.min()), float(ys.min()),
                float(xs.max() - xs.min() + 1), float(ys.max() - ys.min() + 1)]
    ref_area = float(m.sum())
    # toBbox は w = xmax-xmin+1 と同義 (連結矩形の場合)
    if not (abs(area - ref_area) < 1e-9 and max(abs(np.array(rect) - np.array(ref_rect))) < 1e-9):
        print(f"  [FAIL] toBbox/area が decode と不一致: {rect}/{area} vs {ref_rect}/{ref_area}")
        ok = False
    else:
        print("  [OK]   toBbox/area ベースの計測が decode ベースと一致")

    # (4) 貪欲マッチが 1 対 1 を守るか
    masks = [(0, [0, 0, 10, 10], 50.0, "m"), (1, [100, 100, 10, 10], 50.0, "m")]
    bxs = [(0, [0, 0, 10, 10], "A"), (1, [1, 1, 10, 10], "B")]
    pairs, um, ub = greedy_match(masks, bxs)
    if len({p[0] for p in pairs}) != len(pairs) or len({p[1] for p in pairs}) != len(pairs):
        print("  [FAIL] 貪欲マッチが 1 対 1 を破った"); ok = False
    else:
        print(f"  [OK]   貪欲マッチが 1 対 1 を維持 (pairs={len(pairs)}, 未マッチ mask={um}, box={ub})")

    # (5) SAM 指紋の判定関数が参照値で FAIL を返すか
    fake = {"inclusion": {"mean": REF_INCLUSION_MEAN, "q1": 0.87},
            "iou": {"median": REF_IOU_MEDIAN, "iqr": 0.05}}
    v, _ = judge(fake)
    if v != "FAIL":
        print(f"  [FAIL] 前バンドル指紋を FAIL と判定できない (={v})"); ok = False
    else:
        print("  [OK]   前バンドル指紋 (incl 0.879 / IoU 0.927 / IQR 0.05) を FAIL と判定")

    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test のどちらかが必要")

    out = args.out
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    canonical_tool = [os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{sp}.json")
                      for sp in SPLITS]
    hands_by_video = [os.path.join(HANDS_BY_VIDEO, v, "annotations.json")
                      for v in sorted(os.listdir(HANDS_BY_VIDEO))
                      if os.path.exists(os.path.join(HANDS_BY_VIDEO, v, "annotations.json"))]
    tool_seg = [os.path.join(HTS, "tool_seg_noskewer", s, f"{s}.json")
                for s in sorted(os.listdir(os.path.join(HTS, "tool_seg_noskewer")))
                if os.path.exists(os.path.join(HTS, "tool_seg_noskewer", s, f"{s}.json"))]
    merged = [os.path.join(HTS, "fusion/merged_annotations.json")]

    tracks = []
    print("track B: tool_seg 31cls masks vs canonical tool bbox ...", flush=True)
    tracks.append(run_track(tool_seg, canonical_tool, "toolseg31_vs_canonical_toolbbox",
                            class_from="box"))
    print("track A1: HT tool masks (cat 3,4,5) vs canonical tool bbox ...", flush=True)
    tracks.append(run_track(merged, canonical_tool, "HTtool_vs_canonical_toolbbox",
                            mask_cat_filter=HT_TOOL_CATS, class_from="box"))
    print("track A2: HT hand masks (cat 1,2) vs hand bbox ...", flush=True)
    tracks.append(run_track(merged, hands_by_video, "HThand_vs_handbbox",
                            mask_cat_filter=HT_HAND_CATS, class_from="box"))

    results = {"task": "T2_sam_fingerprint",
               "reference_fingerprint": {"inclusion_mean": REF_INCLUSION_MEAN,
                                         "iou_median": REF_IOU_MEDIAN},
               "note": ("マスク JSON の ann['bbox'] は mask 外接矩形由来 (実測: 差が常に 1px の w/h 規約差) "
                        "のため、照合相手は外部 canonical bbox を使用した。"),
               "tracks": []}

    hist_rows, cls_rows = [], []
    for t in tracks:
        v, reason = judge(t["overall"])
        raw = t.pop("_raw")
        t["verdict"], t["verdict_reason"] = v, reason
        results["tracks"].append(t)
        for metric in ("iou", "inclusion", "fill"):
            for h in histogram(raw[metric]):
                hist_rows.append({"track": t["label"], "metric": metric, **h})
        for c, s in t["per_class"].items():
            cls_rows.append({
                "track": t["label"], "class": c,
                "n": s["iou"]["n"],
                "iou_median": s["iou"]["median"], "iou_iqr": s["iou"]["iqr"],
                "incl_mean": s["inclusion"]["mean"], "incl_q1": s["inclusion"]["q1"],
                "fill_median": s["fill"]["median"], "fill_q1": s["fill"]["q1"],
                "fill_q3": s["fill"]["q3"],
            })

    # Step 2-4: signature 3 術具の充填率
    sig = {}
    for t in results["tracks"]:
        if t["label"] != "toolseg31_vs_canonical_toolbbox":
            continue
        for name in SIGNATURE_TOOLS:
            if name in t["per_class"]:
                f = t["per_class"][name]["fill"]
                sig[name] = {"n": f["n"], "fill_median": f["median"],
                             "fill_q1": f["q1"], "fill_q3": f["q3"]}
            else:
                sig[name] = "NOT_FOUND"
    results["signature_tool_fill_ratio"] = sig
    # 総合判定 (最も保守的なもの: FAIL があれば FAIL)
    vs = [t["verdict"] for t in results["tracks"]]
    results["overall_verdict"] = "FAIL" if "FAIL" in vs else ("WARN" if "WARN" in vs else "PASS")

    with open(os.path.join(out, "json", "t2_fingerprint.json"), "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "csv", "t2_iou_incl_by_class.csv"), "w") as f:
        cols = ["track", "class", "n", "iou_median", "iou_iqr", "incl_mean", "incl_q1",
                "fill_median", "fill_q1", "fill_q3"]
        f.write(",".join(cols) + "\n")
        for r in cls_rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    with open(os.path.join(out, "csv", "t2_fill_ratio_by_class.csv"), "w") as f:
        f.write("track,metric,bin_lo,bin_hi,count\n")
        for r in hist_rows:
            f.write(f"{r['track']},{r['metric']},{r['bin_lo']},{r['bin_hi']},{r['count']}\n")

    print("\n=== T2 results ===")
    for t in results["tracks"]:
        o = t["overall"]
        print(f"\n[{t['label']}] pairs={t['n_pairs']} imgs={t['n_common_images']} "
              f"unmatched(mask/box)={t['n_unmatched_mask']}/{t['n_unmatched_box']} "
              f"size_mismatch_imgs={t['n_size_mismatch_images']}")
        for m in ("iou", "inclusion", "fill"):
            s = o[m]
            if s["n"]:
                print(f"   {m:9s} median={s['median']:.4f} mean={s['mean']:.4f} "
                      f"q1={s['q1']:.4f} q3={s['q3']:.4f} IQR={s['iqr']:.4f}")
        print(f"   VERDICT: {t['verdict']} — {t['verdict_reason']}")
    print(f"\n=== signature tools fill ratio ===\n   {json.dumps(sig, ensure_ascii=False)}")
    print(f"\n=== T2 OVERALL VERDICT: {results['overall_verdict']} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

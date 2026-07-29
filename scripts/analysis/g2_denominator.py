#!/usr/bin/env python3
"""M1: tool mask のフレーム水準被覆率 — G-2 の分母確定。

G-2 が使うのは tool mask であって Hand-Tool ではない。
tool mask のフレーム水準被覆率が高ければ G-2 は I1 を破らず T1a (+0.0497) と直接比較できる。

設計 (D1-2): taxonomy は VBS (15 クラス) で固定し、mask を幾何マッチで VBS box に貼り付ける。
mask 側 (tool_seg_noskewer) は Mouth Gag / Skewer の実データを持たないため、
その分は原理的に埋まらない。これを cov_ann と cov_ann_maskable で分離する。

3 つの被覆率 (混同すると結論が変わるため必ず 3 つとも出す):
  cov_frame          mask を 1 件以上持つフレーム数 / canonical フレーム数   ← 主指標
  cov_ann            mask とマッチした VBS box 数 / VBS box 総数
  cov_ann_maskable   同上 (Mouth Gag / Skewer を除外した分母で再計算)

join は必ず os.path.basename 適用後の文字列で行う (§1.5)。

Usage:
    python3 scripts/analysis/g2_denominator.py --out $OUT
    python3 scripts/analysis/g2_denominator.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict

import numpy as np
from pycocotools import mask as mu

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts/analysis"))
from assert_class_system import assert_known_system  # noqa: E402

HTS = os.path.join(REPO, "data/raw/OpenSurgery_Dataset/05_egosurgery_hts")
TOOL_SEG = os.path.join(HTS, "tool_seg_noskewer")
SPLITS = ["train", "val", "test"]
THRESHOLDS = [0.3, 0.5, 0.7, 0.9]
PRIMARY_THR = 0.5

# mask 側に実データが無いクラス (T3 実測: tool_seg_noskewer の declared_but_empty)
NO_MASK_CLASSES = {"Mouth Gag", "Skewer"}

FRAME_RE = re.compile(r"^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)\.(?:jpg|png)$")


def parse_frame(b):
    m = FRAME_RE.match(b)
    return (m.group("video"), f"{m.group('video')}_{m.group('segidx')}", m.group("frame")) if m else None


def rle_of(seg, h, w):
    if isinstance(seg, list):
        return mu.merge(mu.frPyObjects(seg, h, w))
    if isinstance(seg, dict) and isinstance(seg.get("counts"), list):
        return mu.frPyObjects(seg, h, w)
    if isinstance(seg, dict):
        c = seg["counts"]
        return {"size": seg["size"], "counts": c.encode() if isinstance(c, str) else c}
    raise TypeError(f"unsupported segmentation: {type(seg)}")


def rect_iou(a, b):
    ax0, ay0, aw, ah = a; bx0, by0, bw, bh = b
    ix = max(0.0, min(ax0 + aw, bx0 + bw) - max(ax0, bx0))
    iy = max(0.0, min(ay0 + ah, by0 + bh) - max(ay0, by0))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


def greedy_from_pairs(cands, thr):
    """cands: [(iou, mi, bi)] を降順で貪欲マッチ。thr 以上のみ採用。"""
    used_m, used_b, out = set(), set(), []
    for v, mi, bi in cands:
        if v < thr or mi in used_m or bi in used_b:
            continue
        used_m.add(mi); used_b.add(bi); out.append((mi, bi, v))
    return out


def load_vbs():
    """canonical VBS box を {split: {basename: [(bbox, class)]}} で返す。"""
    out = {}
    for sp in SPLITS:
        p = os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{sp}.json")
        assert_known_system(p, "by_split_15cls")
        with open(p) as f:
            d = json.load(f)
        cm = {c["id"]: c["name"] for c in d["categories"]}
        id2b = {im["id"]: os.path.basename(im["file_name"]) for im in d["images"]}
        per = defaultdict(list)
        for im in d["images"]:
            per.setdefault(os.path.basename(im["file_name"]), [])
        for a in d["annotations"]:
            if a["image_id"] in id2b:
                per[id2b[a["image_id"]]].append(([float(x) for x in a["bbox"]],
                                                 cm[a["category_id"]]))
        out[sp] = dict(per)
    return out


def load_masks():
    """tool mask を {basename: [(rect, area, class)]} で返す (外接矩形は toBbox で高速取得)。"""
    out = defaultdict(list)
    n_ann = 0
    for seg in sorted(os.listdir(TOOL_SEG)):
        p = os.path.join(TOOL_SEG, seg, f"{seg}.json")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            d = json.load(f)
        cm = {c["id"]: c["name"] for c in d["categories"]}
        id2 = {im["id"]: (os.path.basename(im["file_name"]), im["height"], im["width"])
               for im in d["images"]}
        for a in d["annotations"]:
            if a["image_id"] not in id2 or not a.get("segmentation"):
                continue
            b, h, w = id2[a["image_id"]]
            try:
                rle = rle_of(a["segmentation"], h, w)
                rect = mu.toBbox(rle).astype(float)
                area = float(mu.area(rle))
            except Exception:
                continue
            if rect[2] <= 0 or rect[3] <= 0:
                continue
            out[b].append((rect, area, cm[a["category_id"]]))
            n_ann += 1
    return dict(out), n_ann


def self_test() -> int:
    """検出できることを確認する:
       1) mask はあるが対応する VBS box が無いフレーム
       2) クラスが食い違うマッチ
       3) mask が 1 件も無いフレーム
    """
    ok = True
    H = W = 64

    def mk_rle(y0, y1, x0, x1):
        m = np.zeros((H, W), dtype=np.uint8, order="F")
        m[y0:y1, x0:x1] = 1
        rle = mu.encode(m)
        return mu.toBbox(rle).astype(float), float(mu.area(rle))

    # frame1: mask あり / VBS box 無し
    r1, a1 = mk_rle(10, 30, 10, 30)
    # frame2: mask と box が重なるがクラスが違う
    r2, a2 = mk_rle(10, 30, 10, 30)
    # frame3: mask 無し / box あり
    masks = {"01_1_0001.jpg": [(r1, a1, "Tweezers")],
             "01_1_0002.jpg": [(r2, a2, "Forceps")]}
    vbs = {"01_1_0001.jpg": [],
           "01_1_0002.jpg": [([10.0, 10.0, 20.0, 20.0], "Tweezers")],
           "01_1_0003.jpg": [([0.0, 0.0, 5.0, 5.0], "Gauze")]}

    frames_with_mask = {b for b, v in masks.items() if v}
    # 1) mask あり box 無し
    mask_no_box = {b for b in frames_with_mask if not vbs.get(b)}
    if mask_no_box != {"01_1_0001.jpg"}:
        print(f"  [FAIL] mask あり VBS box 無しフレームの検出: {mask_no_box}"); ok = False
    else:
        print("  [OK]   mask はあるが VBS box が無いフレームを検出")

    # 2) クラス食い違い
    cands = [(rect_iou(masks["01_1_0002.jpg"][0][0], vbs["01_1_0002.jpg"][0][0]), 0, 0)]
    pairs = greedy_from_pairs(sorted(cands, key=lambda x: -x[0]), 0.5)
    mism = sum(1 for mi, bi, _ in pairs
               if masks["01_1_0002.jpg"][mi][2] != vbs["01_1_0002.jpg"][bi][1])
    if len(pairs) != 1 or mism != 1:
        print(f"  [FAIL] クラス食い違い検出: pairs={pairs} mism={mism}"); ok = False
    else:
        print("  [OK]   クラスが食い違うマッチを検出 (Forceps mask vs Tweezers box)")

    # 3) mask が 1 件も無いフレーム
    no_mask = {b for b in vbs if b not in frames_with_mask}
    if no_mask != {"01_1_0003.jpg"}:
        print(f"  [FAIL] mask 無しフレーム検出: {no_mask}"); ok = False
    else:
        print("  [OK]   mask が 1 件も無いフレームを検出")

    # 4) cov_frame が images 配列長ではなく ann>=1 基準であること
    #    frame3 は VBS に存在するが mask 0 件 -> 分子に入ってはいけない
    cov = len(frames_with_mask & set(vbs)) / len(vbs)
    if abs(cov - 2 / 3) > 1e-9:
        print(f"  [FAIL] cov_frame が ann>=1 基準でない: {cov}"); ok = False
    else:
        print("  [OK]   cov_frame を ann>=1 基準で計算 (2/3)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


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
    for sub in ("json", "csv", "subsets"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    vbs = load_vbs()
    masks, n_mask_ann = load_masks()
    print(f"VBS frames: {sum(len(v) for v in vbs.values())} / "
          f"mask frames: {len(masks)} (mask ann {n_mask_ann})")

    # ---- 1 回だけ IoU 候補を計算し、4 閾値で使い回す ---------------------- #
    per_frame_cands = {}
    for sp in SPLITS:
        for b, boxes in vbs[sp].items():
            ml = masks.get(b, [])
            if not ml or not boxes:
                continue
            c = []
            for mi, (mrect, marea, mcls) in enumerate(ml):
                for bi, (brect, bcls) in enumerate(boxes):
                    v = rect_iou(mrect, brect)
                    if v > 0:
                        c.append((v, mi, bi))
            c.sort(key=lambda x: -x[0])
            per_frame_cands[b] = c

    results_by_thr = {}
    for thr in THRESHOLDS:
        per_split = {}
        tot = Counter()
        unmatched_cls = Counter()
        mismatch_cls = Counter()
        matched_cls = Counter()
        unmatched_by_seg = Counter()
        frames_matched = {sp: set() for sp in SPLITS}
        for sp in SPLITS:
            n_frames = len(vbs[sp])
            n_frames_with_mask = sum(1 for b in vbs[sp] if masks.get(b))
            n_box = sum(len(v) for v in vbs[sp].values())
            n_box_maskable = sum(1 for v in vbs[sp].values() for _, c in v
                                 if c not in NO_MASK_CLASSES)
            n_matched = 0
            n_matched_maskable = 0   # VBS box 側が mask を持ちうるクラスのマッチのみ
            n_mismatch = 0
            for b, boxes in vbs[sp].items():
                ml = masks.get(b, [])
                if not ml or not boxes:
                    for _, c in boxes:
                        unmatched_cls[c] += 1
                        if (pf := parse_frame(b)):
                            unmatched_by_seg[pf[1]] += 1
                    continue
                pairs = greedy_from_pairs(per_frame_cands.get(b, []), thr)
                if pairs:
                    frames_matched[sp].add(b)
                used_b = {bi for _, bi, _ in pairs}
                n_matched += len(pairs)
                for mi, bi, v in pairs:
                    mcls = ml[mi][2]; bcls = boxes[bi][1]
                    matched_cls[bcls] += 1
                    if bcls not in NO_MASK_CLASSES:
                        n_matched_maskable += 1
                    if mcls != bcls:
                        n_mismatch += 1
                        mismatch_cls[f"{bcls}<-{mcls}"] += 1
                for bi, (_, c) in enumerate(boxes):
                    if bi not in used_b:
                        unmatched_cls[c] += 1
                        if (pf := parse_frame(b)):
                            unmatched_by_seg[pf[1]] += 1
            r = {
                "n_canonical_frames": n_frames,
                "n_frames_with_mask": n_frames_with_mask,
                "n_frames_with_matched_mask": len(frames_matched[sp]),
                "cov_frame": n_frames_with_mask / n_frames if n_frames else 0.0,
                "cov_frame_matched": len(frames_matched[sp]) / n_frames if n_frames else 0.0,
                "n_vbs_box": n_box,
                "n_vbs_box_maskable": n_box_maskable,
                "n_matched": n_matched,
                "n_matched_maskable": n_matched_maskable,
                "cov_ann": n_matched / n_box if n_box else 0.0,
                # 分子・分母とも mask を持ちうるクラスに揃える (揃えないと 1 を超えうる)
                "cov_ann_maskable": n_matched_maskable / n_box_maskable if n_box_maskable else 0.0,
                "n_class_mismatch": n_mismatch,
                "class_mismatch_rate": n_mismatch / n_matched if n_matched else 0.0,
            }
            per_split[sp] = r
            for k, v in r.items():
                if isinstance(v, int):
                    tot[k] += v
        totals = {
            "n_canonical_frames": tot["n_canonical_frames"],
            "n_frames_with_mask": tot["n_frames_with_mask"],
            "n_frames_with_matched_mask": tot["n_frames_with_matched_mask"],
            "cov_frame": tot["n_frames_with_mask"] / tot["n_canonical_frames"],
            "cov_frame_matched": tot["n_frames_with_matched_mask"] / tot["n_canonical_frames"],
            "n_vbs_box": tot["n_vbs_box"],
            "n_vbs_box_maskable": tot["n_vbs_box_maskable"],
            "n_matched": tot["n_matched"],
            "n_matched_maskable": tot["n_matched_maskable"],
            "cov_ann": tot["n_matched"] / tot["n_vbs_box"],
            "cov_ann_maskable": tot["n_matched_maskable"] / tot["n_vbs_box_maskable"],
            "n_class_mismatch": tot["n_class_mismatch"],
            "class_mismatch_rate": tot["n_class_mismatch"] / max(1, tot["n_matched"]),
        }
        # 被覆率が 1 を超えたら定義の不整合 (分子と分母の母集団がずれている)。黙って通さない。
        for k in ("cov_frame", "cov_frame_matched", "cov_ann", "cov_ann_maskable"):
            assert 0.0 <= totals[k] <= 1.0, (
                f"coverage out of range: thr={thr} {k}={totals[k]} — 分子/分母の母集団を確認せよ")
        results_by_thr[str(thr)] = {
            "per_split": per_split, "totals": totals,
            "unmatched_by_class": dict(unmatched_cls.most_common()),
            "matched_by_class": dict(matched_cls.most_common()),
            "class_mismatch_pairs": dict(mismatch_cls.most_common(20)),
            "unmatched_by_segment": dict(unmatched_by_seg.most_common()),
        }
        print(f"  thr={thr}: cov_frame={totals['cov_frame']:.4f} "
              f"cov_frame_matched={totals['cov_frame_matched']:.4f} "
              f"cov_ann={totals['cov_ann']:.4f} "
              f"cov_ann_maskable={totals['cov_ann_maskable']:.4f} "
              f"mismatch={totals['class_mismatch_rate']:.4f}")

    prim = results_by_thr[str(PRIMARY_THR)]

    # ---- Step M1-4: 未マッチ内訳 ------------------------------------------ #
    um = prim["unmatched_by_class"]
    um_nomask = {c: n for c, n in um.items() if c in NO_MASK_CLASSES}
    um_other = {c: n for c, n in um.items() if c not in NO_MASK_CLASSES}
    seg_conc = prim["unmatched_by_segment"]

    # ---- Step M1-5: subset 出力 (mask を 1 件以上持つ canonical フレーム) -- #
    subset_sizes = {}
    for sp in SPLITS:
        usable = sorted(b for b in vbs[sp] if masks.get(b))
        subset_sizes[sp] = len(usable)
        with open(os.path.join(out, "subsets", f"subset_toolmask_{sp}.txt"), "w") as f:
            f.write("\n".join(usable) + ("\n" if usable else ""))

    # ---- Step M1-7: 判定 -------------------------------------------------- #
    cf = prim["totals"]["cov_frame"]
    if cf >= 0.95:
        verdict, design = "PASS", "分母は canonical 15,437。T1a (+0.0497) と直接比較可能。I1 を破らない"
    elif cf >= 0.80:
        verdict, design = "WARN", "分母は canonical のまま、mask 無しフレームは bbox フォールバック。被覆率を論文に明記"
    else:
        verdict, design = "FAIL", "分母を subset_toolmask に縮約し、T1a を含む対照を同一分母上で再計算する必要あり"

    # 閾値によって判定が変わるか
    verdict_by_thr = {}
    for t, r in results_by_thr.items():
        c = r["totals"]["cov_frame"]
        verdict_by_thr[t] = "PASS" if c >= 0.95 else ("WARN" if c >= 0.80 else "FAIL")
    verdict_stable = len(set(verdict_by_thr.values())) == 1

    result = {
        "task": "M1_tool_mask_coverage",
        "mask_source": TOOL_SEG,
        "mask_source_note": ("tool_seg_noskewer。宣言 31 categories / 実データ 29 クラス。"
                             "Mouth Gag と Skewer は annotation 0 件のため原理的にマッチしない。"),
        "taxonomy": "VBS (15cls, data/annotations/egosurgery_tool) に固定し mask を貼り付ける (D1-2)",
        "primary_iou_threshold": PRIMARY_THR,
        "coverage_definitions": {
            "cov_frame": "mask を 1 件以上持つ canonical フレーム数 / canonical フレーム数 (主指標)",
            "cov_frame_matched": "VBS box とマッチした mask を 1 件以上持つフレーム数 / canonical フレーム数",
            "cov_ann": "マッチした VBS box 数 / VBS box 総数",
            "cov_ann_maskable": "マッチした VBS box 数 / (VBS box 総数 - Mouth Gag - Skewer)",
        },
        "by_threshold": results_by_thr,
        "unmatched_breakdown": {
            "no_mask_classes": um_nomask,
            "no_mask_classes_total": sum(um_nomask.values()),
            "other_classes": um_other,
            "other_classes_total": sum(um_other.values()),
            "unmatched_by_segment_top": dict(list(seg_conc.items())[:15]),
        },
        "subset_sizes": subset_sizes,
        "verdict": verdict,
        "design": design,
        "verdict_by_threshold": verdict_by_thr,
        "verdict_stable_across_thresholds": verdict_stable,
    }
    with open(os.path.join(out, "json", "m1_tool_mask_coverage.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    cols = ["iou_thr", "split", "n_canonical_frames", "n_frames_with_mask",
            "n_frames_with_matched_mask", "cov_frame", "cov_frame_matched",
            "n_vbs_box", "n_vbs_box_maskable", "n_matched", "cov_ann",
            "cov_ann_maskable", "n_class_mismatch", "class_mismatch_rate"]
    with open(os.path.join(out, "csv", "m1_coverage_by_split.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for t, r in results_by_thr.items():
            for sp in SPLITS:
                row = {"iou_thr": t, "split": sp, **r["per_split"][sp]}
                f.write(",".join(str(row[c]) for c in cols) + "\n")
            row = {"iou_thr": t, "split": "TOTAL", **r["totals"]}
            f.write(",".join(str(row[c]) for c in cols) + "\n")

    # 動画別 (primary threshold)
    with open(os.path.join(out, "csv", "m1_coverage_by_video.csv"), "w") as f:
        f.write("split,video,n_canonical_frames,n_frames_with_mask,cov_frame\n")
        for sp in SPLITS:
            per_v = defaultdict(lambda: [0, 0])
            for b in vbs[sp]:
                pf = parse_frame(b)
                if not pf:
                    continue
                per_v[pf[0]][0] += 1
                if masks.get(b):
                    per_v[pf[0]][1] += 1
            for v in sorted(per_v):
                n, m = per_v[v]
                f.write(f"{sp},{v},{n},{m},{m/n if n else 0:.6f}\n")

    with open(os.path.join(out, "csv", "m1_unmatched_by_class.csv"), "w") as f:
        f.write("class,n_unmatched,n_matched,has_mask_data\n")
        mc = prim["matched_by_class"]
        for c in sorted(set(um) | set(mc)):
            f.write(f"\"{c}\",{um.get(c,0)},{mc.get(c,0)},"
                    f"{'no' if c in NO_MASK_CLASSES else 'yes'}\n")

    print(f"\n=== M1 (thr={PRIMARY_THR}) ===")
    for sp in SPLITS:
        r = prim["per_split"][sp]
        print(f"  {sp:5s} frames={r['n_canonical_frames']:5d} with_mask={r['n_frames_with_mask']:5d} "
              f"cov_frame={r['cov_frame']:.4f} cov_ann={r['cov_ann']:.4f} "
              f"cov_ann_maskable={r['cov_ann_maskable']:.4f} mismatch={r['class_mismatch_rate']:.4f}")
    t = prim["totals"]
    print(f"  TOTAL cov_frame={t['cov_frame']:.4f} cov_frame_matched={t['cov_frame_matched']:.4f} "
          f"cov_ann={t['cov_ann']:.4f} cov_ann_maskable={t['cov_ann_maskable']:.4f}")
    print(f"  class_mismatch_rate={t['class_mismatch_rate']:.4f} "
          f"({t['n_class_mismatch']}/{t['n_matched']})")
    print(f"\n  未マッチ: mask無しクラス={sum(um_nomask.values())} {um_nomask}")
    print(f"           その他={sum(um_other.values())} 上位={dict(list(um_other.items())[:6])}")
    print(f"\n  判定安定性 (閾値別): {verdict_by_thr} stable={verdict_stable}")
    print(f"\n=== M1 VERDICT: {verdict} ===\n  {design}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

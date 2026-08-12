#!/usr/bin/env python3
"""S4-1: 手 mask のフレーム水準被覆率と、手 bbox との幾何マッチ / クラス食い違いを測る。

術具のときと同じ手続き（`ann >= 1` 基準の cov_frame、IoU>=0.5 の幾何マッチ、
クラス食い違い率）で測る。GPU 不要。

join は **basename** で行う（COCO の file_name をそのまま使うと出所間で交差 0 になる）。

データ:
  canonical : data/annotations/egosurgery_tool/instances_{split}.json（15,437 フレーム）
  手 mask   : data/annotations/egosurgery_hts/handtool_seg_5cls/by_split/
              {split}_toolhand_withmask.json の category 1,2（First Person's Left/Right Hand）
              ※ README の警告に従い merged_annotations.json は使わない
  手 bbox   : data/annotations/egosurgery_hts/hand_bbox/by_split/{split}.json（4 クラス）

Usage:
    python scripts/analysis/s4_hand_coverage.py --out experiments/g2_followup_2026-07-29
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
HTS = PROJ / "data/annotations/egosurgery_hts"
SPLITS = ["train", "val", "test"]
IOU_THR = 0.5

# 手 mask の手クラス（5cls のうち 1,2 のみが手。3,4,5 は術具）
MASK_HAND_IDS = {1: "First Person's Left Hand", 2: "First Person's Right Hand"}
# 手 bbox の 4 クラス
BBOX_HAND_IDS = {1: "Own hands left", 2: "Own hands right",
                 3: "Other hands left", 4: "Other hands right"}
# mask -> bbox の対応（"Other hands" に対応する mask は存在しない）
MASK_TO_BBOX = {1: 1, 2: 2}


def stem(fn: str) -> str:
    return Path(fn).stem


def rect_iou(a, b) -> float:
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


def load_canonical(split: str) -> set[str]:
    d = json.loads((PROJ / f"data/annotations/egosurgery_tool/instances_{split}.json").read_text())
    return {stem(im["file_name"]) for im in d["images"]}


def load_mask_hands(split: str):
    """{stem: [(bbox, cat_id)]} 手クラスのみ。あわせて全体の統計も返す。"""
    p = HTS / f"handtool_seg_5cls/by_split/{split}_toolhand_withmask.json"
    d = json.loads(p.read_text())
    id2 = {im["id"]: stem(im["file_name"]) for im in d["images"]}
    out = defaultdict(list)
    n_ann_all = len(d["annotations"])
    n_hand = 0
    n_no_seg = 0
    cat_count = Counter()
    for a in d["annotations"]:
        cat_count[a["category_id"]] += 1
        if a["category_id"] not in MASK_HAND_IDS:
            continue
        if a["image_id"] not in id2:
            continue
        if not a.get("segmentation"):
            n_no_seg += 1
            continue
        n_hand += 1
        out[id2[a["image_id"]]].append(([float(x) for x in a["bbox"]], a["category_id"]))
    return dict(out), {
        "json": str(p), "n_images_in_json": len(d["images"]),
        "n_ann_all_5cls": n_ann_all, "n_hand_ann_with_seg": n_hand,
        "n_hand_ann_without_seg": n_no_seg,
        "ann_count_by_category": {f"{k}:{MASK_HAND_IDS.get(k, '(tool)')}" : v
                                  for k, v in sorted(cat_count.items())},
    }


def load_bbox_hands(split: str):
    p = HTS / f"hand_bbox/by_split/{split}.json"
    d = json.loads(p.read_text())
    id2 = {im["id"]: stem(im["file_name"]) for im in d["images"]}
    out = defaultdict(list)
    for a in d["annotations"]:
        if a["image_id"] in id2:
            out[id2[a["image_id"]]].append(([float(x) for x in a["bbox"]], a["category_id"]))
    return dict(out), {"json": str(p), "n_images_in_json": len(d["images"]),
                       "n_ann": len(d["annotations"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "json").mkdir(parents=True, exist_ok=True)
    (out / "csv").mkdir(parents=True, exist_ok=True)

    rep: dict = {
        "denominator_definition": (
            "cov_frame の分母 = canonical (egosurgery_tool/instances_{split}.json) の画像数。"
            "分子 = そのフレームに手クラス(mask cat 1,2)の segmentation 付き annotation が "
            "**1 件以上**あるフレーム数（ann>=1 基準）。"),
        "class_system_note": (
            "手 mask は 2 クラス（First Person's Left/Right Hand）しか無い。手 bbox は 4 クラス "
            "（Own/Other × Left/Right）。すなわち mask 側に 'Other hands' が存在しない。"
            "指示書 §1.5 の『手 bbox 4 クラス』は bbox 側の記述としては正しいが、"
            "mask 側を 4 クラスで作ることはできない。"),
        "splits": {}, "total": {},
    }
    rows = []
    tot = Counter()
    for split in SPLITS:
        canon = load_canonical(split)
        mh, mstat = load_mask_hands(split)
        bh, bstat = load_bbox_hands(split)

        n_canon = len(canon)
        frames_with_mask = {s for s in mh if s in canon}
        frames_with_bbox = {s for s in bh if s in canon}
        # mask json に載っているが canonical に無いフレーム（join の健全性確認）
        mask_outside = {s for s in mh if s not in canon}
        bbox_outside = {s for s in bh if s not in canon}

        # --- 幾何マッチ（canonical に載るフレームのみ）---
        n_mask_ann = n_matched = n_cls_mismatch = 0
        mismatch_pairs = Counter()
        unmatched_by_cls = Counter()
        for s in sorted(frames_with_mask):
            blist = list(bh.get(s, []))
            used = set()
            for mbox, mcat in mh[s]:
                n_mask_ann += 1
                best, bi = 0.0, -1
                for j, (bbox, _bc) in enumerate(blist):
                    if j in used:
                        continue
                    v = rect_iou(bbox, mbox)
                    if v > best:
                        best, bi = v, j
                if bi >= 0 and best >= IOU_THR:
                    used.add(bi)
                    n_matched += 1
                    bcat = blist[bi][1]
                    if MASK_TO_BBOX.get(mcat) != bcat:
                        n_cls_mismatch += 1
                        mismatch_pairs[f"mask{mcat}({MASK_HAND_IDS[mcat]})->bbox{bcat}"
                                       f"({BBOX_HAND_IDS.get(bcat,'?')})"] += 1
                else:
                    unmatched_by_cls[f"mask{mcat}({MASK_HAND_IDS[mcat]})"] += 1

        sp = {
            "n_canonical_frames": n_canon,
            "n_frames_with_hand_mask_ann_ge1": len(frames_with_mask),
            "cov_frame_hand_mask": len(frames_with_mask) / n_canon,
            "n_frames_with_hand_bbox_ann_ge1": len(frames_with_bbox),
            "cov_frame_hand_bbox": len(frames_with_bbox) / n_canon,
            "n_mask_frames_outside_canonical": len(mask_outside),
            "n_bbox_frames_outside_canonical": len(bbox_outside),
            "mask_source": mstat, "bbox_source": bstat,
            "geometric_match": {
                "iou_threshold": IOU_THR,
                "denominator": "canonical に載るフレーム上の手 mask annotation 数",
                "n_mask_ann": n_mask_ann, "n_matched": n_matched,
                "match_rate": (n_matched / n_mask_ann) if n_mask_ann else None,
                "n_class_mismatch": n_cls_mismatch,
                "class_mismatch_rate_of_matched": (n_cls_mismatch / n_matched) if n_matched else None,
                "mismatch_pairs": dict(mismatch_pairs),
                "unmatched_by_mask_class": dict(unmatched_by_cls),
            },
        }
        rep["splits"][split] = sp
        tot["canon"] += n_canon
        tot["mask_frames"] += len(frames_with_mask)
        tot["bbox_frames"] += len(frames_with_bbox)
        tot["mask_ann"] += n_mask_ann
        tot["matched"] += n_matched
        tot["mismatch"] += n_cls_mismatch
        rows.append({
            "split": split, "n_canonical": n_canon,
            "n_frames_hand_mask_ge1": len(frames_with_mask),
            "cov_frame_hand_mask": round(len(frames_with_mask) / n_canon, 6),
            "n_frames_hand_bbox_ge1": len(frames_with_bbox),
            "cov_frame_hand_bbox": round(len(frames_with_bbox) / n_canon, 6),
            "n_mask_ann": n_mask_ann, "n_matched": n_matched,
            "match_rate": round(n_matched / n_mask_ann, 6) if n_mask_ann else None,
            "n_class_mismatch": n_cls_mismatch,
            "class_mismatch_rate": round(n_cls_mismatch / n_matched, 6) if n_matched else None,
        })
        print(f"[{split}] canonical={n_canon}  手mask ann>=1 のフレーム={len(frames_with_mask)} "
              f"(cov_frame={len(frames_with_mask)/n_canon:.4f})  "
              f"手bbox ann>=1={len(frames_with_bbox)} (cov_frame={len(frames_with_bbox)/n_canon:.4f})")
        print(f"        幾何マッチ: mask ann={n_mask_ann} matched={n_matched} "
              f"({n_matched/n_mask_ann:.4f} @IoU>={IOU_THR})  "
              f"クラス食い違い={n_cls_mismatch} ({n_cls_mismatch/max(n_matched,1):.4f} of matched)")
        if mismatch_pairs:
            print(f"        食い違い内訳: {dict(mismatch_pairs)}")

    rep["total"] = {
        "n_canonical_frames": tot["canon"],
        "n_frames_with_hand_mask_ann_ge1": tot["mask_frames"],
        "cov_frame_hand_mask": tot["mask_frames"] / tot["canon"],
        "n_frames_with_hand_bbox_ann_ge1": tot["bbox_frames"],
        "cov_frame_hand_bbox": tot["bbox_frames"] / tot["canon"],
        "n_mask_ann": tot["mask_ann"], "n_matched": tot["matched"],
        "match_rate": tot["matched"] / tot["mask_ann"] if tot["mask_ann"] else None,
        "n_class_mismatch": tot["mismatch"],
        "class_mismatch_rate_of_matched": tot["mismatch"] / tot["matched"] if tot["matched"] else None,
    }
    t = rep["total"]
    print("\n=== 合計（分母 = canonical 15,437 フレーム）===")
    print(f"  手 mask のフレーム水準被覆率 cov_frame = {t['n_frames_with_hand_mask_ann_ge1']}/"
          f"{t['n_canonical_frames']} = {t['cov_frame_hand_mask']:.4f}")
    print(f"  手 bbox のフレーム水準被覆率 cov_frame = {t['n_frames_with_hand_bbox_ann_ge1']}/"
          f"{t['n_canonical_frames']} = {t['cov_frame_hand_bbox']:.4f}")
    print(f"  幾何マッチ率 = {t['n_matched']}/{t['n_mask_ann']} = {t['match_rate']:.4f} (IoU>=0.5)")
    print(f"  クラス食い違い率 = {t['n_class_mismatch']}/{t['n_matched']} = "
          f"{t['class_mismatch_rate_of_matched']:.4f}（分母 = matched）")

    (out / "json" / "s4_hand_coverage.json").write_text(
        json.dumps(rep, indent=2, ensure_ascii=False))
    with open(out / "csv" / "s4_hand_coverage.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"\n-> {out/'json'/'s4_hand_coverage.json'}")
    print(f"-> {out/'csv'/'s4_hand_coverage.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

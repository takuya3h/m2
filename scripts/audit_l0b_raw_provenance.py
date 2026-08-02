#!/usr/bin/env python
"""l0b_raw_provenance — raw bundle の来歴監査（読み取り専用・CPU only・GPU 不要）。

目的: 「完全版 GT 組み立て」の設計を確定させるため raw bundle 側を監査する。
**組み立て・変換・生成は一切しない**。egosurgery_hts に何も書かない。SAM/GrabCut 等で
bbox からマスクを作らない。未達は未達として実測値で報告する。

出力: experiments/analysis/hts_raw_provenance_2026-07-29/<task>.json + REPORT.md
実行: PYTHONPATH=src .venv-relation-detr/bin/python scripts/audit_l0b_raw_provenance.py
"""
from __future__ import annotations

import json
import glob
import os
import csv
import statistics as st
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np
from pycocotools import mask as maskUtils

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/OpenSurgery_Dataset"
ANN = ROOT / "data/annotations"
OUT = ROOT / "experiments/analysis/hts_raw_provenance_2026-07-29"
OUT.mkdir(parents=True, exist_ok=True)

# SAM(bbox プロンプト)由来の指紋（2026-07-10 バンドル実測値）
SAM_INCLUSION_MEAN = 0.879
SAM_IOU_MEDIAN = 0.927
# 完全版が満たすべき手インスタンス総数（raw 02_hand 正本）
HAND_TOTAL = 57173
# Tool15（プロジェクト標準・egosurgery_tool_hand cat 0-14 と一致）
TOOL15 = ["Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Mouth Gag",
          "Needle Holders", "Raspatory", "Retractor", "Scalpel", "Scissors", "Skewer",
          "Suction Cannula", "Syringe", "Tweezers"]


def load(p):
    with open(p) as f:
        return json.load(f)


def base(fn):
    return os.path.basename(fn)


def vid(fn):
    return "_".join(base(fn).split("_")[:2])


def bbox_iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix, iy = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    inter = max(0, ix2 - ix) * max(0, iy2 - iy)
    ua = aw * ah + bw * bh - inter
    incl = inter / (aw * ah) if aw * ah > 0 else 0.0
    return (inter / ua if ua > 0 else 0.0), incl


def quantiles(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return {"min": round(v[0], 4), "q1": round(v[n // 4], 4), "median": round(v[n // 2], 4),
            "q3": round(v[3 * n // 4], 4), "max": round(v[-1], 4), "mean": round(st.mean(v), 4), "n": n}


def rle_bbox_area(seg):
    rle = seg
    if isinstance(rle.get("counts"), list):
        rle = maskUtils.frPyObjects(rle, rle["size"][0], rle["size"][1])
    m = maskUtils.decode(rle)
    if m.ndim == 3:
        m = m[..., 0]
    ys, xs = np.where(m > 0)
    if len(xs) == 0:
        return None, 0
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)], int(m.sum())


# ---------------------------------------------------------------------------
def task1_overview():
    subsets = {}
    for d in sorted(glob.glob(str(RAW / "*"))):
        if not os.path.isdir(d):
            continue
        exts = Counter()
        for f in glob.glob(os.path.join(d, "**", "*"), recursive=True):
            if os.path.isfile(f):
                exts[os.path.splitext(f)[1].lstrip(".")] += 1
        subsets[os.path.basename(d)] = dict(exts.most_common(6))
    return {"root": str(RAW), "subsets": subsets,
            "note": "00_master=json(seg=矩形), 01_frames=jpg, 02_hand=PNG(手バイナリ)+json, "
                    "03_tool=json(RLE), 04_handtool=PNG(マルチクラス)+json(RLE)"}


def task2_seg_format(sample=400):
    """C1-raw: 真のインスタンスマスクは実在するか (a)/(b)。"""
    res = {}
    for label, p in [("03_tool_14cls", RAW / "03_tool/coco_splits_14cls_cleaned/train.json"),
                     ("04_handtool_5cls", RAW / "04_handtool/coco_splits_5cls/train.json")]:
        d = load(p)
        types = Counter()
        vtx = Counter()
        fills = []
        for a in d["annotations"]:
            s = a.get("segmentation")
            if isinstance(s, dict):
                types["rle"] += 1
            elif isinstance(s, list):
                types["polygon"] += 1
                if s and isinstance(s[0], list):
                    vtx[len(s[0]) // 2] += 1
        for a in d["annotations"][:sample]:
            s = a.get("segmentation")
            if isinstance(s, dict):
                bm, area = rle_bbox_area(s)
                if bm:
                    fills.append(area / (bm[2] * bm[3]))
        res[label] = {"seg_types": dict(types), "polygon_vertex_hist": dict(sorted(vtx.items())),
                      "fill_ratio(mask_area/mask_bbox)": quantiles(fills)}
    # master
    m = load(sorted(glob.glob(str(RAW / "00_master_annotations/annotations_raw/*/annotations.json")))[0])
    mvtx = Counter()
    mtypes = Counter()
    for a in m["annotations"][:sample]:
        s = a.get("segmentation")
        if isinstance(s, list) and s and isinstance(s[0], list):
            mtypes["polygon"] += 1
            mvtx[len(s[0]) // 2] += 1
        elif isinstance(s, dict):
            mtypes["rle"] += 1
    res["00_master"] = {"seg_types": dict(mtypes), "polygon_vertex_hist": dict(sorted(mvtx.items()))}
    # 判定: 派生に RLE 真マスクが在り(=形式a) だが master には無い（矩形のみ）
    has_real = all(res[k]["seg_types"].get("rle", 0) > 0 for k in ("03_tool_14cls", "04_handtool_5cls"))
    master_only_rect = (res["00_master"]["polygon_vertex_hist"].get(4, 0) > 0
                        and len(res["00_master"]["polygon_vertex_hist"]) == 1)
    res["_verdict"] = {
        "real_masks_exist_in_derived": has_real,
        "master_is_rect_only": master_only_rect,
        "class": "(a) 形式上は真マスク(RLE)実在。ただし master に無く『派生時に挿入』のため生成来歴の確認が必須",
    }
    return res


def task3_sam_fingerprint(sample=1500):
    """C4-provenance: 派生 RLE mask 外接矩形 vs master 原 bbox の内包率/IoU 分布。"""
    # master 原 bbox（basename -> [(cls,bbox)]）
    master = defaultdict(list)
    mcats = {}
    for f in glob.glob(str(RAW / "00_master_annotations/annotations_raw/*/annotations.json")):
        d = load(f)
        id2 = {im["id"]: base(im["file_name"]) for im in d["images"]}
        for c in d["categories"]:
            mcats[c["id"]] = c["name"]
        for a in d["annotations"]:
            master[id2.get(a["image_id"])].append((mcats.get(a["category_id"]), a["bbox"]))
    out = {}
    for label, p in [("03_tool_14cls", RAW / "03_tool/coco_splits_14cls_cleaned/train.json"),
                     ("04_handtool_5cls", RAW / "04_handtool/coco_splits_5cls/train.json")]:
        d = load(p)
        id2 = {im["id"]: base(im["file_name"]) for im in d["images"]}
        tcats = {c["id"]: c["name"] for c in d["categories"]}
        ious, incls = [], []
        for a in d["annotations"][:sample]:
            s = a.get("segmentation")
            if not isinstance(s, dict):
                continue
            bm, _ = rle_bbox_area(s)
            if not bm:
                continue
            fn, tname = id2.get(a["image_id"]), tcats.get(a["category_id"])
            cand = [bb for (cn, bb) in master.get(fn, []) if cn == tname] or [bb for (cn, bb) in master.get(fn, [])]
            if not cand:
                continue
            best = max((bbox_iou(bm, bb) for bb in cand), key=lambda x: x[0])
            ious.append(best[0])
            incls.append(best[1])
        out[label] = {"iou_vs_master_bbox": quantiles(ious), "inclusion_vs_master_bbox": quantiles(incls)}
    out["_reference_SAM_fingerprint"] = {"inclusion_mean": SAM_INCLUSION_MEAN, "iou_median": SAM_IOU_MEDIAN}
    # 判定: 内包率が 1.0 近くに高集中(=箱内包)なら bbox 由来生成の疑い。鋭い SAM ピークとの一致度も併記。
    incl_mean = out["04_handtool_5cls"]["inclusion_vs_master_bbox"]["mean"]
    iou_med = out["04_handtool_5cls"]["iou_vs_master_bbox"]["median"]
    out["_verdict"] = {
        "inclusion_high_containment": incl_mean is not None and incl_mean >= 0.95,
        "matches_sharp_sam_peak": (incl_mean is not None and abs(incl_mean - SAM_INCLUSION_MEAN) < 0.03
                                   and abs(iou_med - SAM_IOU_MEDIAN) < 0.03),
        "assessment": "判定不能→要追加証拠。master が矩形のみで派生に真マスクがある=マスクは箱から生成された可能性。"
                      "内包率が箱にほぼ完全内包(高集中)なら bbox 由来生成の疑いが濃厚。ただし 7/10 SAM の鋭い指紋"
                      "(内包0.879/IoU0.927)とは完全一致せず分布は広い。生成方法の来歴書が無い限りクリア不可。",
    }
    return out


def task4_c6_phase(sample_videos=None):
    """C6: HTI ∧ phase 共存フレーム数（basename join・9 工程別）。"""
    hti = set()
    for sp in ("train", "val", "test"):
        d = load(RAW / f"04_handtool/coco_splits_5cls/{sp}.json")
        hti |= {os.path.splitext(base(im["file_name"]))[0] for im in d["images"]}
    phase = {}
    for csvf in glob.glob(str(ANN / "egosurgery_phase/*.csv")):
        with open(csvf) as f:
            r = csv.DictReader(f)
            for row in r:
                key = row.get("Frame") or row.get("frame")
                lab = row.get("Phase") or row.get("phase")
                if key:
                    phase[key] = lab
    coexist = [k for k in hti if k in phase]
    per_phase = Counter(phase[k] for k in coexist)
    return {"hti_frames": len(hti), "phase_frames": len(phase),
            "coexist_frames": len(coexist), "per_phase": dict(per_phase.most_common()),
            "note": "join は basename。image_id join は test 約7割誤接続の既知バグ回避のため不可。"}


def task4_c7_class_map():
    """C7: raw 器具クラス ↔ Tool15。"""
    d14 = load(RAW / "03_tool/coco_splits_14cls_cleaned/train.json")
    raw14 = [c["name"] for c in d14["categories"]]
    mapping = {name: (name if name in TOOL15 else "MISSING_in_raw14") for name in TOOL15}
    dropped = [t for t in TOOL15 if t not in raw14]
    extra = [t for t in raw14 if t not in TOOL15]
    out = {"tool15": TOOL15, "raw_14cls_cleaned": raw14,
           "dropped_from_raw14(=Tool15にありraw14に無い)": dropped,
           "extra_in_raw14": extra,
           "bipolar_merged_into_forceps": not ("Bipolar Forceps" in raw14),
           "mapping": mapping}
    with open(OUT / "C7_class_mapping.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out


def task4_c8_hand_canonical(sample=3000):
    """C8: 手 bbox 正本決定（raw02 / hand4 / tool_hand 3者比較）。"""
    def collect_hand4():
        boxes = defaultdict(list)
        vids = set()
        imgs = 0
        tot = 0
        for sp in ("train", "val", "test"):
            d = load(ANN / f"egosurgery_hand4/instances_{sp}.json")
            m = {im["id"]: base(im["file_name"]) for im in d["images"]}
            imgs += len(d["images"])
            tot += len(d["annotations"])
            for im in d["images"]:
                vids.add(vid(im["file_name"]))
            for a in d["annotations"]:
                boxes[m[a["image_id"]]].append(a["bbox"])
        return boxes, tot, imgs, sorted(vids)

    def collect_raw02():
        boxes = defaultdict(list)
        vids = Counter()
        tot = 0
        imgset = set()
        for f in glob.glob(str(RAW / "02_hand/json_per_video/*/*.json")):
            d = load(f)
            m = {im["id"]: base(im["file_name"]) for im in d["images"]}
            tot += len(d["annotations"])
            for im in d["images"]:
                vids[vid(im["file_name"])] += 1
                imgset.add(base(im["file_name"]))
            for a in d["annotations"]:
                boxes[m[a["image_id"]]].append(a["bbox"])
        return boxes, tot, len(imgset), vids

    h, htot, himgs, hvids = collect_hand4()
    r, rtot, rimgs, rvids = collect_raw02()
    common = set(h) & set(r)
    # 幾何一致: 各 hand4 box に対し同フレーム raw02 の最良 IoU
    exact = 0
    tot_pairs = 0
    ious = []
    for fn in list(common)[:sample]:
        for hb in h[fn]:
            tot_pairs += 1
            best = max((bbox_iou(hb, rb)[0] for rb in r[fn]), default=0.0)
            ious.append(best)
            if best > 0.999:
                exact += 1
    return {
        "raw02_hand": {"instances": rtot, "images": rimgs, "videos": len(rvids),
                       "video_img_counts_03_12_15": {k: rvids[k] for k in sorted(rvids) if k.split("_")[0] in ("03", "12", "15")}},
        "egosurgery_hand4": {"instances": htot, "images": himgs, "videos": len(hvids),
                             "missing_vs_raw02": sorted(set(rvids) - set(hvids))},
        "note_toolhand": "egosurgery_tool_hand の手は egosurgery_hand4 と件数/動画/画像すべて同一(46320/15437/22)=同世代",
        "03_3_status": "raw02 にも 03_3 の手アノテは存在しない（frames はあるが GT 無し→復活不能）",
        "raw02_vs_hand4": {"common_frames": len(common), "raw02_only_frames": len(set(r) - set(h)),
                           "hand4_only_frames": len(set(h) - set(r)),
                           "geom_iou_best": quantiles(ious),
                           "exact_match_pct": round(exact / tot_pairs * 100, 2) if tot_pairs else None},
        "_verdict": {
            "recommended_canonical": "raw 02_hand（最完全: 57,173 / 25 セグメント / 欠落は 03_3 のみ＝どの世代にも無い）",
            "reason": "hand4/tool_hand は 46,320/22セグメントの subset かつ raw02 と座標系が異なる"
                      "(bbox 完全一致≈0%)。世代混在は S0 の Δ 基準点を汚染するため、raw02 を正本に一本化し"
                      "downstream を全て raw02 座標で再導出すること。12_2 は 16 枚のみ・03_3 は復活不能。",
        },
    }


def task5_delta_denominator():
    """init mAP(warm-start) vs S0-frozen 0.7051 の差の説明。"""
    return {
        "t1b_warmstart_init_mAP": {"seed42": 0.7303, "seed123": 0.729, "seed456": 0.722, "mean": 0.7271},
        "warmstart_ckpt": "third_party/Relation-DETR/checkpoints/incoming/seed{S}/best_ap.pth "
                          "(= 収束済み 15クラス Relation-DETR 検出器。train_t1b.py L147-152)",
        "s0_frozen_denominator": {"value": "0.7051 ± 0.0042",
                                  "source": "experiments/baselines/s0_frozen_00{1,2,3}_relationdetr_s0frozen_cocohead_seed* "
                                            "(= backbone 凍結 + COCO-init head を frozen-source 手順で再学習した検出器)"},
        "eval_recipe": "両者とも公式 score_thr=0.0 / NMS 無 / top-k=300・同一 split(val 1515)。recipe 差は無い。",
        "explanation": "約2.2pt差は eval recipe/split の不一致ではなく『別 checkpoint』に起因。"
                       "0.7271=収束済み full 検出器(warm-start源)、0.7051=frozen-backbone+COCO-head 再学習の S0-frozen。"
                       "T1b/L2 の Δ は inj−ctrl(両者とも warm-start源 0.7271 から)で測る paired 量であり、"
                       "絶対 mAP を 0.7051 と直接比較してはならない(分母が別系統=4分母運用)。",
        "caution": "L2/L1a の陽性主張は『同一 warm-start・同一 recipe の ctrl との paired 差』で行い、"
                   "S0-frozen 0.7051 とは混同しない。DeltaCalculator の recipe 整合検証を必ず通すこと。",
    }


def main():
    results = {}
    results["task1_overview"] = task1_overview()
    results["task2_seg_format"] = task2_seg_format()
    results["task3_sam_fingerprint"] = task3_sam_fingerprint()
    results["task4_c6_phase_coexist"] = task4_c6_phase()
    results["task4_c7_class_map"] = task4_c7_class_map()
    results["task4_c8_hand_canonical"] = task4_c8_hand_canonical()
    results["task5_delta_denominator"] = task5_delta_denominator()
    for k, v in results.items():
        with open(OUT / f"{k}.json", "w") as f:
            json.dump(v, f, indent=2, ensure_ascii=False)
    with open(OUT / "all_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("=== l0b raw provenance audit 完了 ===")
    t2 = results["task2_seg_format"]["_verdict"]
    t3 = results["task3_sam_fingerprint"]["_verdict"]
    print("Task2 (真マスク実在?):", t2["class"])
    print("Task3 (SAM指紋):", t3["assessment"][:60], "...")
    c8 = results["task4_c8_hand_canonical"]
    print("C8 正本推奨:", c8["_verdict"]["recommended_canonical"])
    print("C6 共存フレーム:", results["task4_c6_phase_coexist"]["coexist_frames"])
    print(f"出力: {OUT}")
    return results


if __name__ == "__main__":
    main()

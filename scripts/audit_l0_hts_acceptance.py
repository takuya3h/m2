#!/usr/bin/env python
"""l0_hts_acceptance — HTS（Hand-Tool-Seg）公式 GT「完全版」受入検査（C1–C8）。

台帳 Run `l0_hts_acceptance_2026-07-28`（S1/must）の受入基準を機械判定する。
**学習・評価を伴わないデータ検査**（CPU only）。研究インテグリティ: 合否は実測のみ。
未達は「未達」と明記し取り繕わない。

対象（"HTS 完全版 候補" の実体マッピング。正本が未組立なら候補=現行派生を検査し不足を可視化）:
  - 手 GT          : data/annotations/egosurgery_hand4/instances_{split}.json（4クラス手）
  - 把持関係 GT    : data/annotations/egosurgery_tool_hand/instances_{split}.json（tool⊕hand）
  - 参照(正本源)   : data/raw/OpenSurgery_Dataset/02_hand/json_per_video/*（手 57,173 の正本）
                     data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls/*（Two Hands Tool=値5 を持つ）
                     data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/*/annotations.json

受入基準（台帳 Primary Metric より）: 主判定量 = C1/C2/C3/C4 の 4 項目すべて合格。
  C1 ポリゴン点数分布       : HTS の seg が真マスク（RLE / 多頂点 polygon）か。master の 4 頂点矩形は不可。
  C2 Hand-Tool ラベルに値5   : 把持関係 GT に "Two Hands Tool"(=5) が出現するか。
  C3 手インスタンス 57,173   : 欠落4動画(03_1/03_3/12_2/15_2)を復活し 26 セグメント総手数 = 57,173 か。
  C4 リーク指紋の不在        : train/val/test が frame・video を共有しない（データリーク無し）。
  C5 公式 split 整合         : images 数が公式 9657/1515/4265 に一致。
  C6 phase 共存フレーム数    : phase アノテーションと HTS が共存するフレーム数（報告値）。
  C7 クラス対応表            : カテゴリ id↔名 の対応表（報告）。
  C8 手 bbox 正本決定        : 手 bbox の正本ソース（報告・決定）。

出力: experiments/audit/l0_hts_acceptance/acceptance_report.json（+ 標準出力に要約）
使い方: .venv-relation-detr/bin/python scripts/audit_l0_hts_acceptance.py
        （stdlib のみ。pycocotools 不要）
"""
from __future__ import annotations

import json
import os
import glob
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data/annotations"
RAW = ROOT / "data/raw/OpenSurgery_Dataset"

HAND4 = ANN / "egosurgery_hand4"           # instances_{split}.json（4クラス手）
TOOLHAND = ANN / "egosurgery_tool_hand"    # instances_{split}.json（tool⊕hand）
RAW_HAND_PV = RAW / "02_hand/json_per_video"           # 手 正本（57,173）
RAW_HT_5CLS = RAW / "04_handtool/coco_splits_5cls"     # 値5=Two Hands Tool を持つ
RAW_MASTER = RAW / "00_master_annotations/annotations_raw"

OFFICIAL_SPLIT = {"train": 9657, "val": 1515, "test": 4265}
HAND_TOTAL_TARGET = 57173
MISSING_VIDEO_TARGET = {"03_1", "03_3", "12_2", "15_2"}  # 完全版で復活すべき


def _load(p: Path) -> dict:
    with open(p) as f:
        return json.load(f)


def _vid_of(file_name: str) -> str:
    """frame filename -> video segment id（例: '03_3_000123.jpg' -> '03_3'）。"""
    b = os.path.basename(file_name)
    return "_".join(b.split("_")[:2])


def _splits(dirpath: Path, prefix: str = "instances_"):
    out = {}
    for sp in ("train", "val", "test"):
        p = dirpath / f"{prefix}{sp}.json"
        if p.exists():
            out[sp] = _load(p)
    return out


# ---------------------------------------------------------------------------
# C1 ポリゴン点数分布: HTS seg が真マスクか（master の 4 頂点矩形は不可）
# ---------------------------------------------------------------------------
def check_c1_polygon_points() -> dict:
    def seg_profile(anns, n=3000):
        types = Counter()
        vtx = Counter()
        for a in anns[:n]:
            s = a.get("segmentation")
            if isinstance(s, dict):
                types["rle"] += 1
            elif isinstance(s, list):
                types["polygon"] += 1
                if s and isinstance(s[0], list):
                    vtx[len(s[0]) // 2] += 1
        return dict(types), dict(sorted(vtx.items()))

    # 把持関係 GT（HTS 本体）の seg 形式
    ht = _splits(TOOLHAND)
    ht_types, ht_vtx = ({}, {})
    if "train" in ht:
        ht_types, ht_vtx = seg_profile(ht["train"]["annotations"])
    # raw 04_handtool（RLE 真マスクの正本）
    raw_ht = _load(RAW_HT_5CLS / "train.json")
    raw_types, raw_vtx = seg_profile(raw_ht["annotations"])
    # master（4 頂点矩形 = 不可）
    m = _load(next(iter(sorted(glob.glob(str(RAW_MASTER / "*/annotations.json"))))))
    m_types, m_vtx = seg_profile(m["annotations"])

    # 真マスク = RLE 主体 or polygon の頂点数 > 4 が主。master 相当（全4頂点）は不可。
    def is_real(types, vtx):
        if types.get("rle", 0) > 0:
            return True
        non4 = sum(c for k, c in vtx.items() if k > 4)
        return non4 > 0 and (vtx.get(4, 0) == 0 or non4 >= vtx.get(4, 0))

    ht_real = is_real(ht_types, ht_vtx) if ht_types else None
    passed = bool(ht_real) and is_real(raw_types, raw_vtx)
    return {
        "pass": passed,
        "toolhand_seg_types": ht_types, "toolhand_vertex_hist": ht_vtx,
        "raw04_seg_types": raw_types,
        "master_seg_types": m_types, "master_vertex_hist": m_vtx,
        "note": "master は 100% 4 頂点矩形(bbox 相当)=真マスク不可。HTS は RLE/多頂点でなければ FAIL。",
    }


# ---------------------------------------------------------------------------
# C2 Hand-Tool ラベルに値5(Two Hands Tool) が出現するか
# ---------------------------------------------------------------------------
def check_c2_value5() -> dict:
    def cat_map_and_counts(d):
        cats = {c["id"]: c["name"] for c in d["categories"]}
        cnt = Counter(a["category_id"] for a in d["annotations"])
        return cats, cnt

    ht = _splits(TOOLHAND)
    res = {"pass": False}
    has5 = False
    if "train" in ht:
        cats, cnt = cat_map_and_counts(ht["train"])
        name5 = cats.get(5)
        res["toolhand_cat5_name"] = name5
        res["toolhand_cat5_count"] = cnt.get(5, 0)
        has5 = (name5 is not None and "two hands" in str(name5).lower() and cnt.get(5, 0) > 0)
    # 正本源(raw 04_handtool 5cls) の値5
    raw = _load(RAW_HT_5CLS / "train.json")
    rcats = {c["id"]: c["name"] for c in raw["categories"]}
    rcnt = Counter(a["category_id"] for a in raw["annotations"])
    res["raw04_cat5_name"] = rcats.get(5)
    res["raw04_cat5_count"] = rcnt.get(5, 0)
    res["pass"] = bool(has5)
    res["note"] = ("HTS 把持関係 GT に Two Hands Tool(=5) が必要。"
                   "現行 egosurgery_tool_hand が 19クラス(手混在)で値5=Mouth Gag なら不合格。"
                   "正本源 raw 04_handtool 5cls は値5=Two Hands Tool を保持。")
    return res


# ---------------------------------------------------------------------------
# C3 手インスタンス 57,173・欠落4動画の復活
# ---------------------------------------------------------------------------
def check_c3_hand_total() -> dict:
    hand = _splits(HAND4)
    total = sum(len(d["annotations"]) for d in hand.values())
    present = set()
    for d in hand.values():
        present |= {_vid_of(im["file_name"]) for im in d["images"]}
    raw_vids = {os.path.basename(p) for p in glob.glob(str(RAW_HAND_PV / "*"))}
    missing = sorted(raw_vids - present)
    # 参照: raw 02_hand per_video 総手数
    raw_total = 0
    for f in glob.glob(str(RAW_HAND_PV / "*/*.json")):
        raw_total += len(_load(Path(f))["annotations"])
    passed = (total == HAND_TOTAL_TARGET) and (len(missing) == 0)
    return {
        "pass": passed,
        "hand_instances_current": total,
        "hand_instances_target": HAND_TOTAL_TARGET,
        "raw02_hand_total": raw_total,
        "segments_present": len(present),
        "segments_raw": len(raw_vids),
        "missing_videos": missing,
        "missing_videos_expected": sorted(MISSING_VIDEO_TARGET),
        "note": "完全版は欠落4動画(03_1/03_3/12_2/15_2)を復活し 26 セグメント総手数=57,173 が要件。",
    }


# ---------------------------------------------------------------------------
# C4 リーク指紋の不在: train/val/test が frame/video を共有しない
# ---------------------------------------------------------------------------
def check_c4_leakage() -> dict:
    hand = _splits(HAND4)
    frames = {sp: {im["file_name"] for im in d["images"]} for sp, d in hand.items()}
    vids = {sp: {_vid_of(fn) for fn in fs} for sp, fs in frames.items()}
    pairs = [("train", "val"), ("train", "test"), ("val", "test")]
    frame_overlap = {f"{a}∩{b}": len(frames[a] & frames[b]) for a, b in pairs if a in frames and b in frames}
    video_overlap = {f"{a}∩{b}": sorted(vids[a] & vids[b]) for a, b in pairs if a in vids and b in vids}
    passed = all(v == 0 for v in frame_overlap.values()) and all(len(v) == 0 for v in video_overlap.values())
    return {
        "pass": passed,
        "frame_overlap": frame_overlap,
        "video_overlap": video_overlap,
        "note": "同一 frame も同一 video も split 跨ぎで共有しないこと（動画単位リークの封じ）。",
    }


# ---------------------------------------------------------------------------
# C5 公式 split 整合 / C6 phase 共存 / C7 クラス対応表 / C8 手 bbox 正本
# ---------------------------------------------------------------------------
def check_c5_split() -> dict:
    hand = _splits(HAND4)
    counts = {sp: len(d["images"]) for sp, d in hand.items()}
    passed = all(counts.get(sp) == n for sp, n in OFFICIAL_SPLIT.items())
    return {"pass": passed, "image_counts": counts, "official": OFFICIAL_SPLIT}


def check_c6_phase_coexist() -> dict:
    # phase アノテーション(CSV)が在るフレーム集合と HTS(手GT)の共存フレーム数を報告。
    phase_dir = ANN / "egosurgery_phase"
    phase_frames = set()
    for csv in glob.glob(str(phase_dir / "*.csv")):
        vid = os.path.basename(csv).replace(".csv", "")
        phase_frames.add(vid)  # video 粒度（frame 粒度 CSV の詳細解析は scope 外）
    hand = _splits(HAND4)
    hts_vids = set()
    for d in hand.values():
        hts_vids |= {_vid_of(im["file_name"]) for im in d["images"]}
    return {"pass": None, "phase_video_segments": len(phase_frames),
            "hts_video_segments": len(hts_vids),
            "coexist_video_segments": len(phase_frames & hts_vids),
            "note": "報告値（合否対象外）。frame 粒度の共存数は完全版組立時に再算出。"}


def check_c7_class_map() -> dict:
    out = {"pass": None}
    hand = _splits(HAND4)
    if "train" in hand:
        out["hand4_categories"] = {c["id"]: c["name"] for c in hand["train"]["categories"]}
    ht = _splits(TOOLHAND)
    if "train" in ht:
        out["toolhand_categories"] = {c["id"]: c["name"] for c in ht["train"]["categories"]}
    raw = _load(RAW_HT_5CLS / "train.json")
    out["raw04_5cls_categories"] = {c["id"]: c["name"] for c in raw["categories"]}
    out["note"] = "報告（合否対象外）。完全版のクラス対応表の正本化に用いる。"
    return out


def check_c8_hand_bbox_source() -> dict:
    # 手 bbox の正本候補を列挙して報告。決定は完全版組立時に確定。
    return {"pass": None,
            "candidates": {
                "egosurgery_hand4": "4クラス手・現行派生（22セグメント・46,320）",
                "raw_02_hand_json_per_video": "手 正本 57,173（26セグメント・欠落なし）",
                "master_38cls": "seg=4頂点矩形(bbox相当)・手id 10/11/21/22",
            },
            "recommended_canonical": "raw_02_hand_json_per_video（完全性・欠落なし）",
            "note": "報告/決定（合否対象外）。"}


def main() -> int:
    checks = {
        "C1_polygon_points": check_c1_polygon_points(),
        "C2_value5_two_hands_tool": check_c2_value5(),
        "C3_hand_total_57173": check_c3_hand_total(),
        "C4_leakage_fingerprint": check_c4_leakage(),
        "C5_official_split": check_c5_split(),
        "C6_phase_coexist": check_c6_phase_coexist(),
        "C7_class_map": check_c7_class_map(),
        "C8_hand_bbox_source": check_c8_hand_bbox_source(),
    }
    main_keys = ["C1_polygon_points", "C2_value5_two_hands_tool",
                 "C3_hand_total_57173", "C4_leakage_fingerprint"]
    main_pass = all(bool(checks[k]["pass"]) for k in main_keys)

    report = {
        "run": "l0_hts_acceptance_2026-07-28",
        "target": "HTS(Hand-Tool-Seg)公式GT完全版 候補=現行 data/annotations 派生",
        "main_criteria": main_keys,
        "main_pass": main_pass,
        "checks": checks,
        "verdict": ("ACCEPTED" if main_pass else "NOT ACCEPTED (完全版 未達)"),
    }
    out_dir = ROOT / "experiments/audit/l0_hts_acceptance"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "acceptance_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print(f"l0 HTS 受入検査 — 主判定(C1/C2/C3/C4): "
          f"{'ALL PASS ✓' if main_pass else 'FAIL ✗ (完全版 未達)'}")
    print("=" * 70)
    for k, v in checks.items():
        p = v.get("pass")
        mark = "✓" if p is True else ("✗" if p is False else "·(報告)")
        print(f"  {mark} {k}")
    print(f"\n  C3: 手 {checks['C3_hand_total_57173']['hand_instances_current']} / "
          f"目標 {HAND_TOTAL_TARGET} / 欠落動画 {checks['C3_hand_total_57173']['missing_videos']}")
    print(f"  C2: toolhand cat5 = {checks['C2_value5_two_hands_tool'].get('toolhand_cat5_name')} "
          f"/ raw04 cat5 = {checks['C2_value5_two_hands_tool'].get('raw04_cat5_name')}")
    print(f"\n  → verdict: {report['verdict']}")
    print(f"  出力: {out_dir / 'acceptance_report.json'}")
    return 0 if main_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

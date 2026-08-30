#!/usr/bin/env python
"""Phase C — candidates.csv / criteria_matrix.csv を生成し、組み合わせを評価する。"""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "experiments/analysis/hts_candidate_acceptance"

rows = json.load(open(D / "candidates_raw.json"))
crit = json.load(open(D / "criteria_raw.json"))

# --- candidates.csv -------------------------------------------------------
FIELDS = ["scope", "path", "is_symlink", "symlink_target", "format", "bytes",
          "n_images", "n_annotations", "n_categories", "categories",
          "seg_types", "vertex_hist", "n_videos", "videos",
          "n_hand_annotations", "is_candidate", "provenance"]

PROV = {
    "_deprecated/egosurgery_hand4": "旧 canonical。2026-07-31 の HTS 再構成に伴い _deprecated へ退避（DEPRECATED.md は不在）",
    "egosurgery_hts/hand_seg": "README §5: build_hts_split_aligned.py --src raw/02_hand/json_per_video",
    "egosurgery_hts/tool_seg": "README §5: build_hts_split_aligned.py --src raw/03_tool/json_per_video",
    "egosurgery_hts/hand_tool_seg": "README §5: build_hand_tool_seg_5cls.py --src raw/04_handtool/json_per_video",
    "egosurgery_tool_hand": "手 bbox 4cls および 術具+手 19cls。生成元の記載を README で確認できず",
    "egosurgery_tool/hand": "symlink -> egosurgery_tool_hand",
    "egosurgery_tool/instances": "術具 bbox 15cls（公式 split の基準）",
    "02_hand/json_per_video": "参照先: 手注釈の正本（57,173）",
    "04_handtool/coco_splits_5cls": "参照先: 把持関係 5cls の正本（値5=Two Hands Tool）",
    "00_master_annotations": "参照先: master 38cls。seg は全件 4 頂点矩形",
}


def prov(p):
    for k, v in PROV.items():
        if k in p:
            return v
    return ""


with open(D / "candidates.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        r = dict(r)
        for k in ("categories", "seg_types", "vertex_hist"):
            if k in r:
                r[k] = json.dumps(r[k], ensure_ascii=False)
        if "videos" in r:
            r["videos"] = " ".join(r["videos"])
        r["provenance"] = prov(r["path"])
        w.writerow(r)

# --- criteria_matrix.csv --------------------------------------------------
CF = ["candidate", "desc", "criterion", "verdict", "counted", "threshold"]
with open(D / "criteria_matrix.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=CF)
    w.writeheader()
    for c in crit:
        if not c.get("readable"):
            for k in ("C1", "C2", "C3", "C4", "C5"):
                w.writerow({"candidate": c["key"], "desc": c["desc"], "criterion": k,
                            "verdict": "UNKNOWN", "counted": "読めない/不在",
                            "threshold": ""})
            continue
        for k in ("C1", "C2", "C3", "C4", "C5"):
            w.writerow({"candidate": c["key"], "desc": c["desc"], "criterion": k,
                        "verdict": "PASS" if c[k]["pass"] else "FAIL",
                        "counted": json.dumps(c[k]["counted"], ensure_ascii=False),
                        "threshold": c[k]["threshold"]})

# --- 組み合わせ評価（Step 2-4）--------------------------------------------
combo = {}
for k in ("C1", "C2", "C3", "C4", "C5"):
    sat = [c["key"] for c in crit if c.get("readable") and c[k]["pass"]]
    combo[k] = sat
main_keys = ["C1", "C2", "C3", "C4"]
all_main_have = all(combo[k] for k in main_keys)
json.dump({"satisfying_candidates_per_criterion": combo,
           "main_criteria": main_keys,
           "every_main_criterion_has_a_candidate": all_main_have},
          open(D / "combination.json", "w"), ensure_ascii=False, indent=1)

print("candidates.csv 行数:", len(rows))
print("criteria_matrix.csv 行数:", sum(5 for _ in crit))
for k, v in combo.items():
    print(f"  {k}: 満たす候補 {len(v)} 件 {v}")
print("主判定 C1-C4 すべてに満たす候補があるか:", all_main_have)

#!/usr/bin/env python
"""Step 2-3 — 手の件数: 既存記録(46,320)の再現と、候補合算の集合件数。

重複は「同一フレーム・同一 box」を鍵に集合で除く（SPEC §3 Task2 Step2-3）。
単純加算と集合件数を必ず並べる。**読み取りのみ。**
"""
from __future__ import annotations
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANN = ROOT / "data/annotations"
RAW = ROOT / "data/raw/OpenSurgery_Dataset"


def is_true_hand(n): 
    n = n.lower(); return "hand" in n and "tool" not in n


def hand_anns(paths):
    """(file_name, bbox) の集合と、単純加算件数を返す。"""
    keys, total = set(), 0
    keys_wcat = set()
    for p in paths:
        d = json.load(open(p))
        cats = {c["id"]: c["name"] for c in d.get("categories", [])}
        hids = {i for i, n in cats.items() if is_true_hand(n)}
        imgs = {im["id"]: im["file_name"] for im in d["images"]}
        for a in d["annotations"]:
            if a.get("category_id") not in hids:
                continue
            total += 1
            fn = os.path.basename(imgs.get(a["image_id"], f"?{a['image_id']}"))
            bb = tuple(round(float(x), 2) for x in a.get("bbox", []))
            keys.add((fn, bb))
            keys_wcat.add((fn, bb, a["category_id"]))
    return total, keys, keys_wcat


SETS = {
    "hand4_deprecated": [ANN/f"_deprecated/egosurgery_hand4/instances_{s}.json" for s in ("train","val","test")],
    "hts_hand_seg_splits": [ANN/f"egosurgery_hts/hand_seg/{s}.json" for s in ("train","val","test")],
    "hts_hand_seg_extra": [ANN/"egosurgery_hts/hand_seg/extra.json"],
    "tool_hand_4cls": [ANN/f"egosurgery_tool_hand/{s}.json" for s in ("train","val","test")],
    "tool_hand_19cls": [ANN/f"egosurgery_tool_hand/instances_{s}.json" for s in ("train","val","test")],
    "raw02_hand_source": sorted(RAW.glob("02_hand/json_per_video/*/*.json")),
}

res = {}
for k, ps in SETS.items():
    t, ks, kc = hand_anns(ps)
    res[k] = {"simple_sum": t, "set_by_frame_bbox": len(ks), "set_by_frame_bbox_cat": len(kc)}
    print(f'{k:<22} 単純加算={t:>7}  集合(frame,bbox)={len(ks):>7}  集合(frame,bbox,cat)={len(kc):>7}')

print()
print("=== 既存記録の再現 ===")
print(f'  hand4_deprecated 単純加算 = {res["hand4_deprecated"]["simple_sum"]}  / 既存記録 46320  '
      f'→ 再現 {res["hand4_deprecated"]["simple_sum"]==46320}')
print(f'  raw02_hand_source 単純加算 = {res["raw02_hand_source"]["simple_sum"]}  / 完全版 57173  '
      f'→ 一致 {res["raw02_hand_source"]["simple_sum"]==57173}')

print()
print("=== 候補の合算（重複除去つき）===")
combos = {
    "hand_seg(split)+hand_seg(extra)": ["hts_hand_seg_splits", "hts_hand_seg_extra"],
    "hand_seg(全)+hand4(退避)": ["hts_hand_seg_splits", "hts_hand_seg_extra", "hand4_deprecated"],
    "hand4(退避)+tool_hand_4cls": ["hand4_deprecated", "tool_hand_4cls"],
    "hand_seg(全)+hand4+tool_hand_4cls+19cls": ["hts_hand_seg_splits","hts_hand_seg_extra",
                                                "hand4_deprecated","tool_hand_4cls","tool_hand_19cls"],
}
for name, keys in combos.items():
    paths = [p for k in keys for p in SETS[k]]
    t, ks, kc = hand_anns(paths)
    naive = sum(res[k]["simple_sum"] for k in keys)
    print(f'  {name}')
    print(f'      単純加算={naive:>7}  集合(frame,bbox)={len(ks):>7}  差={naive-len(ks):>7}  '
          f'目標 57173 到達={len(ks)==57173}')

json.dump({"per_set": res}, open(ROOT/"experiments/analysis/hts_candidate_acceptance/hand_count.json","w"),
          ensure_ascii=False, indent=1)

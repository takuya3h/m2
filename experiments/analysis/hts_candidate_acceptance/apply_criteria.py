#!/usr/bin/env python
"""T-2026-08-30-hts-candidate-acceptance / Phase B — 受け入れ基準の当てはめ。

基準 C1-C5 の定義は scripts/audit_l0_hts_acceptance.py の実装を正とする。
本スクリプトは同じ判定関数（is_real / cat5 / 手件数 / リーク / split 整合）を
候補ごとに適用し、数えた値と閾値を併記した行列を作る。**読み取りのみ。**
"""
from __future__ import annotations
import json, os, glob, itertools
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANN = ROOT / "data/annotations"
RAW = ROOT / "data/raw/OpenSurgery_Dataset"
RAW_HAND_PV = RAW / "02_hand/json_per_video"

OFFICIAL_SPLIT = {"train": 9657, "val": 1515, "test": 4265}
HAND_TOTAL_TARGET = 57173


def load(p): return json.load(open(p))
def vid_of(fn): return "_".join(os.path.basename(fn).split("_")[:2])


def is_true_hand(name: str) -> bool:
    n = name.lower()
    return "hand" in n and "tool" not in n


# --- 検査器と同一の判定（実装から写す。改変しない） -------------------------
def is_real_mask(types: dict, vtx: dict) -> bool:
    if types.get("rle", 0) > 0:
        return True
    non4 = sum(c for k, c in vtx.items() if k > 4)
    return non4 > 0 and (vtx.get(4, 0) == 0 or non4 >= vtx.get(4, 0))


# --- 候補集合の定義 ---------------------------------------------------------
CANDIDATES = [
    ("hand4_deprecated",   "手 bbox 4cls（退避先）",
     {sp: ANN/f"_deprecated/egosurgery_hand4/instances_{sp}.json" for sp in ("train","val","test")}, []),
    ("hts_hand_seg",       "手 seg 4cls（HTS 再構成）",
     {sp: ANN/f"egosurgery_hts/hand_seg/{sp}.json" for sp in ("train","val","test")},
     [ANN/"egosurgery_hts/hand_seg/extra.json"]),
    ("hts_hand_tool_seg",  "把持関係 seg 5cls（HTS 再構成）",
     {sp: ANN/f"egosurgery_hts/hand_tool_seg/{sp}.json" for sp in ("train","val","test")},
     [ANN/"egosurgery_hts/hand_tool_seg/extra.json"]),
    ("hts_tool_seg",       "術具 seg 31cls（HTS 再構成）",
     {sp: ANN/f"egosurgery_hts/tool_seg/{sp}.json" for sp in ("train","val","test")},
     [ANN/"egosurgery_hts/tool_seg/extra.json"]),
    ("tool_bbox",          "術具 bbox 15cls",
     {sp: ANN/f"egosurgery_tool/instances_{sp}.json" for sp in ("train","val","test")}, []),
    ("tool_hand_19cls",    "術具+手 bbox 19cls（検査器が見る現行派生）",
     {sp: ANN/f"egosurgery_tool_hand/instances_{sp}.json" for sp in ("train","val","test")}, []),
    ("tool_hand_4cls",     "手 bbox 4cls（egosurgery_tool_hand 直下）",
     {sp: ANN/f"egosurgery_tool_hand/{sp}.json" for sp in ("train","val","test")}, []),
    ("tool_hand_4cls_link","手 bbox 4cls（symlink: egosurgery_tool/hand）",
     {sp: ANN/f"egosurgery_tool/hand/{sp}.json" for sp in ("train","val","test")}, []),
    ("raw04_5cls",         "参照先: raw 04_handtool 5cls",
     {sp: RAW/f"04_handtool/coco_splits_5cls/{sp}.json" for sp in ("train","val","test")}, []),
]


def eval_candidate(key, desc, splits, extras):
    docs = {sp: load(p) for sp, p in splits.items() if p.exists()}
    extra_docs = [load(p) for p in extras if p.exists()]
    r = {"key": key, "desc": desc,
         "paths": {sp: str(p.relative_to(ROOT)) for sp, p in splits.items()},
         "extras": [str(p.relative_to(ROOT)) for p in extras],
         "splits_found": sorted(docs)}
    all_docs = list(docs.values()) + extra_docs
    if not all_docs:
        r["readable"] = False
        return r
    r["readable"] = True

    cats = {c["id"]: c["name"] for c in all_docs[0].get("categories", [])}
    r["categories"] = {str(k): v for k, v in sorted(cats.items())}
    hand_ids = {i for i, n in cats.items() if is_true_hand(n)}
    r["true_hand_category_ids"] = sorted(hand_ids)

    # --- C1 マスクが真か -----------------------------------------------
    types, vtx = Counter(), Counter()
    for d in all_docs:
        for a in d["annotations"]:
            s = a.get("segmentation")
            if isinstance(s, dict): types["rle"] += 1
            elif isinstance(s, list) and s and isinstance(s[0], list):
                types["polygon"] += 1; vtx[len(s[0]) // 2] += 1
            elif isinstance(s, list) and s:
                types["polygon"] += 1; vtx[len(s) // 2] += 1
            else: types["none"] += 1
    r["C1"] = {"pass": is_real_mask(dict(types), dict(vtx)),
               "counted": {"seg_types": dict(types),
                           "vertex_hist": {str(k): v for k, v in sorted(vtx.items())}},
               "threshold": "RLE>0 か、頂点数>4 の polygon が 4 頂点以上に多いこと"}

    # --- C2 値5 = Two Hands Tool ----------------------------------------
    cnt5 = sum(1 for d in all_docs for a in d["annotations"] if a.get("category_id") == 5)
    name5 = cats.get(5)
    r["C2"] = {"pass": bool(name5 is not None and "two hands" in str(name5).lower() and cnt5 > 0),
               "counted": {"cat5_name": name5, "cat5_count": cnt5},
               "threshold": "id=5 の名が 'Two Hands' を含み、件数>0"}

    # --- C3 手の件数 ------------------------------------------------------
    hand_total = sum(1 for d in all_docs for a in d["annotations"] if a.get("category_id") in hand_ids)
    present = set()
    for d in all_docs:
        present |= {vid_of(im["file_name"]) for im in d["images"]}
    raw_dirs = {os.path.basename(p) for p in glob.glob(str(RAW_HAND_PV / "*"))}
    missing = sorted(raw_dirs - present)
    r["C3"] = {"pass": (hand_total == HAND_TOTAL_TARGET and not missing),
               "counted": {"hand_annotations": hand_total,
                           "segments_present": len(present),
                           "segments_raw_dirs": len(raw_dirs),
                           "missing_videos": missing},
               "threshold": f"手注釈 == {HAND_TOTAL_TARGET} かつ 欠落動画 0"}

    # --- C4 リーク --------------------------------------------------------
    frames = {sp: {im["file_name"] for im in d["images"]} for sp, d in docs.items()}
    vids = {sp: {vid_of(f) for f in fs} for sp, fs in frames.items()}
    pairs = [("train","val"),("train","test"),("val","test")]
    fo = {f"{a}^{b}": len(frames[a] & frames[b]) for a,b in pairs if a in frames and b in frames}
    vo = {f"{a}^{b}": sorted(vids[a] & vids[b]) for a,b in pairs if a in vids and b in vids}
    r["C4"] = {"pass": bool(fo) and all(v==0 for v in fo.values()) and all(not v for v in vo.values()),
               "counted": {"frame_overlap": fo, "video_overlap": vo},
               "threshold": "frame も video も split 跨ぎで共有 0（比較対が存在すること）"}

    # --- C5 公式 split ----------------------------------------------------
    counts = {sp: len(d["images"]) for sp, d in docs.items()}
    r["C5"] = {"pass": all(counts.get(sp)==n for sp,n in OFFICIAL_SPLIT.items()),
               "counted": {"image_counts": counts},
               "threshold": f"images 数 == {OFFICIAL_SPLIT}"}
    return r


def main():
    res = [eval_candidate(*c) for c in CANDIDATES]
    out = ROOT/"experiments/analysis/hts_candidate_acceptance/criteria_raw.json"
    json.dump(res, open(out,"w"), ensure_ascii=False, indent=1)
    hdr = f'{"候補":<22}{"C1":>6}{"C2":>6}{"C3":>6}{"C4":>6}{"C5":>6}   手件数'
    print(hdr); print("-"*len(hdr))
    for r in res:
        if not r["readable"]:
            print(f'{r["key"]:<22}  読めない'); continue
        m = lambda k: "PASS" if r[k]["pass"] else "FAIL"
        print(f'{r["key"]:<22}{m("C1"):>6}{m("C2"):>6}{m("C3"):>6}{m("C4"):>6}{m("C5"):>6}   {r["C3"]["counted"]["hand_annotations"]}')
    print(f"\n-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

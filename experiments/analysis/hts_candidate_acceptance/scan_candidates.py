#!/usr/bin/env python
"""T-2026-08-30-hts-candidate-acceptance / Phase A Step 1-2 — 候補の棚卸し。

data/annotations 配下の全ファイルと、文書・検査器が指す配下外の参照先を読み、
候補ごとに 経路 / 実体か symlink か / 形式 / 画像数 / 注釈数 / カテゴリ /
マスクの型 / 動画の被覆 / 来歴 を実測して JSON に落とす。**読み取りのみ。**
"""
from __future__ import annotations
import json, os, sys, glob
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ANN = ROOT / "data/annotations"
RAW = ROOT / "data/raw/OpenSurgery_Dataset"

HAND_WORDS = ("hand",)
GRASP_WORDS = ("tool hand", "hand tool", "two hands")


def vid_of(fn: str) -> str:
    b = os.path.basename(fn)
    return "_".join(b.split("_")[:2])


def profile_coco(path: Path) -> dict:
    """COCO 形式なら実測値を返す。読めなければ理由を返す。"""
    out = {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size}
    out["is_symlink"] = path.is_symlink()
    if path.is_symlink():
        out["symlink_target"] = os.readlink(path)
    try:
        with open(path) as f:
            d = json.load(f)
    except Exception as e:  # 読めない形式
        out["format"] = "unreadable"
        out["error"] = f"{type(e).__name__}: {e}"
        return out
    if not (isinstance(d, dict) and "annotations" in d and "images" in d):
        out["format"] = "json-not-coco"
        out["top_keys"] = list(d.keys()) if isinstance(d, dict) else type(d).__name__
        return out
    out["format"] = "coco-json"
    imgs, anns = d["images"], d["annotations"]
    out["n_images"] = len(imgs)
    out["n_annotations"] = len(anns)
    cats = {c["id"]: c["name"] for c in d.get("categories", [])}
    out["categories"] = {str(k): v for k, v in sorted(cats.items())}
    out["n_categories"] = len(cats)
    # マスクの型（全件走査。標本ではない）
    types, vtx = Counter(), Counter()
    for a in anns:
        s = a.get("segmentation")
        if isinstance(s, dict):
            types["rle"] += 1
        elif isinstance(s, list):
            if not s:
                types["polygon_empty"] += 1
            elif isinstance(s[0], list):
                types["polygon"] += 1
                vtx[len(s[0]) // 2] += 1
            else:
                types["polygon_flat"] += 1
                vtx[len(s) // 2] += 1
        elif s is None:
            types["none"] += 1
        else:
            types["other"] += 1
    out["seg_types"] = dict(types)
    out["vertex_hist"] = {str(k): v for k, v in sorted(vtx.items())}
    # 動画の被覆
    vids = sorted({vid_of(im["file_name"]) for im in imgs})
    out["videos"] = vids
    out["n_videos"] = len(vids)
    # 候補条件: 手 / 把持 / マスクのいずれかを含むか
    names = " ".join(cats.values()).lower()
    out["has_hand_cat"] = any(w in names for w in HAND_WORDS)
    out["has_grasp_cat"] = any(w in names for w in GRASP_WORDS)
    out["has_mask"] = (types.get("rle", 0) + types.get("polygon", 0) + types.get("polygon_flat", 0)) > 0
    out["is_candidate"] = bool(out["has_hand_cat"] or out["has_grasp_cat"] or out["has_mask"])
    # 手カテゴリの注釈数
    hand_ids = {i for i, n in cats.items() if "hand" in n.lower()}
    out["hand_category_ids"] = sorted(hand_ids)
    out["n_hand_annotations"] = sum(1 for a in anns if a.get("category_id") in hand_ids)
    return out


def main() -> int:
    targets: list[Path] = []
    for p in sorted(ANN.rglob("*")):
        if p.is_file() or p.is_symlink():
            targets.append(p)
    # 参照先（配下外）。走査の起点は data/annotations だが棚卸しには含める。
    ref_targets = []
    ref_targets += sorted(RAW.glob("02_hand/json_per_video/*/*.json"))
    ref_targets += sorted(RAW.glob("04_handtool/coco_splits_5cls/*.json"))
    ref_targets += sorted(RAW.glob("00_master_annotations/annotations_raw/*/annotations.json"))

    rows = []
    for p in targets:
        if p.suffix.lower() == ".json" or p.is_symlink():
            rows.append({"scope": "under_annotations", **profile_coco(p)})
        else:
            rows.append({"scope": "under_annotations",
                         "path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size,
                         "is_symlink": False,
                         "format": {".md": "markdown", ".csv": "csv", ".txt": "text"}.get(p.suffix.lower(), "other"),
                         "is_candidate": False})
    for p in ref_targets:
        rows.append({"scope": "referenced_outside", **profile_coco(p)})

    out = ROOT / "experiments/analysis/hts_candidate_acceptance/candidates_raw.json"
    with open(out, "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    n_cand = sum(1 for r in rows if r.get("is_candidate"))
    print(f"走査 {len(rows)} 件 / 候補 {n_cand} 件 -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

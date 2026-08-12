"""19 クラス統合 COCO から手 4 クラスだけを抽出し、独立 4 クラス COCO を生成する。

系統①の非-oracle 経路（S2-hand 独立検出器 → pred 手特徴）の前提となる
「tool 検出器から完全に独立した手 4 クラス検出器」を学習するためのアノテーションを作る。
既存の 19 クラス統合 COCO
``data/annotations/egosurgery_tool_hand/instances_{train,val,test}.json``
（tool 0-14 / hand 15-18）から **手 4 クラス（category_id 15,16,17,18）だけ**を取り出し、
0-3 に remap して ``data/annotations/egosurgery_hand4/instances_{split}.json`` を書く。

    remap（19 クラス統合 id → 独立 4 クラス id）:
        15 Own hands left   -> 0 (own_L)
        16 Own hands right  -> 1 (own_R)
        17 Other hands left -> 2 (other_L)
        18 Other hands right-> 3 (other_R)

方針:
    - images は **全画像を保持**（手が無いフレームも negative として残す）。
    - annotations は **手のみ**（tool は完全に捨てる。19 クラス統合を一切引き継がない）。
    - **bbox only**（segmentation は落とす。手検出器は矩形のみ学習する）。
    - categories は id 0-3・descriptive name・supercategory="hand" を付す。

実行:
    python scripts/build_hand_coco.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from egosurgery.datasets.constants import HAND_CLASSES  # noqa: E402

SRC_DIR = PROJECT_DIR / "data" / "annotations" / "egosurgery_tool_hand"
OUT_DIR = PROJECT_DIR / "data" / "annotations" / "egosurgery_hand4"

# 19 クラス統合 id (15..18) -> 独立 4 クラス id (0..3)。HAND_CLASSES は id 昇順で
# own_L, own_R, other_L, other_R の順に並ぶため enumerate がそのまま 0..3 になる。
SRC_TO_HAND4: dict[int, int] = {c["id"]: new_id for new_id, c in enumerate(HAND_CLASSES)}

# 独立 4 クラス COCO の categories（id 0-3・手のみ）。
HAND4_CATEGORIES: list[dict] = [
    {"id": new_id, "name": c["name"], "supercategory": "hand"}
    for new_id, c in enumerate(HAND_CLASSES)
]
# 短縮タグ（own_other 特徴やログ用の参考。COCO name とは別に注記）。
HAND4_SHORT = {0: "own_L", 1: "own_R", 2: "other_L", 3: "other_R"}


def build_split(split: str) -> dict:
    """1 split を 19 クラス統合 COCO から手 4 クラス独立 COCO へ変換する。"""
    src_path = SRC_DIR / f"instances_{split}.json"
    if not src_path.exists():
        raise FileNotFoundError(f"missing merged COCO: {src_path}（build_tool_hand_coco.py を実行したか）")

    src = json.loads(src_path.read_text(encoding="utf-8"))

    # 画像は全保持（手の無いフレームも negative として残す）。
    images = list(src["images"])

    # annotations は手のみ抽出・bbox only・category_id を 0-3 へ remap・id は 1.. に振り直す。
    annotations: list[dict] = []
    per_class: Counter = Counter()
    next_ann_id = 1
    for ann in src["annotations"]:
        cid = ann["category_id"]
        if cid not in SRC_TO_HAND4:
            continue  # tool（0-14）は捨てる
        new_cid = SRC_TO_HAND4[cid]
        bbox = [float(v) for v in ann["bbox"]]
        area = float(ann.get("area", bbox[2] * bbox[3]))
        annotations.append({
            "id": next_ann_id,
            "image_id": ann["image_id"],
            "category_id": new_cid,
            "bbox": bbox,
            "area": area,
            "iscrowd": int(ann.get("iscrowd", 0)),
        })
        per_class[new_cid] += 1
        next_ann_id += 1

    out = {
        "info": src.get("info", {"description": "EgoSurgery Hand-4 (independent hand detector)"}),
        "licenses": src.get("licenses", []),
        "images": images,
        "annotations": annotations,
        "categories": HAND4_CATEGORIES,
    }
    counts = " ".join(f"{HAND4_SHORT[k]}={per_class[k]}" for k in range(len(HAND4_CATEGORIES)))
    print(
        f"  [{split}] images={len(images)} hand_annotations={len(annotations)}  ({counts})"
    )
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"output: {OUT_DIR}")
    print(f"remap (19-class -> hand4): {SRC_TO_HAND4}")
    for split in ("train", "val", "test"):
        out = build_split(split)
        out_path = OUT_DIR / f"instances_{split}.json"
        out_path.write_text(
            json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        print(f"  wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

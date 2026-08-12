"""tool (15 クラス) と hand (4 クラス) の COCO を 19 クラス統合 COCO に結合する。

S2 (手検出追加) で mmdet の検出ヘッドを 19 クラスで学習させるため、
``data/annotations/egosurgery_tool/instances_{train,val,test}.json`` と
``data/annotations/egosurgery_tool/hand/{train,val,test}.json`` を画像 ID で
マージし、新しい annotation ファイル
``data/annotations/egosurgery_tool_hand/instances_{train,val,test}.json`` を生成する。

カテゴリ ID の割当:
    - tool:  0-14（変更なし、constants.TOOL_CLASSES に一致）
    - hand: 15-18（hand JSON の元 id 1-4 を +14 シフト、HAND_CLASSES に一致）

実行:
    python scripts/build_tool_hand_coco.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from egosurgery.datasets.constants import (  # noqa: E402
    HAND_CLASSES,
    TOOL_CLASSES,
    coco_categories,
)

TOOL_DIR = PROJECT_DIR / "data" / "annotations" / "egosurgery_tool"
HAND_DIR = TOOL_DIR / "hand"
OUT_DIR = PROJECT_DIR / "data" / "annotations" / "egosurgery_tool_hand"


def _hand_cat_shift(orig_id: int) -> int:
    """hand JSON の category_id (1-4) を統合後 id (15-18) に対応させる。"""
    # hand JSON は category_id を 1..4 で持つので 1->15, 2->16, 3->17, 4->18。
    return int(orig_id) + 14


def _normalize_hand_file_name(file_name: str, split: str) -> str:
    """hand JSON の素の file_name (例: ``14_1_0250.jpg``) を tool 形式
    （``train/14/14_1_0250.jpg``）へ正規化する。

    file_name は ``<vidid>_<sess>_<frame>.jpg`` 形式を想定し、先頭の vidid を
    取り出してサブディレクトリを付ける。既にスラッシュを含む場合はそのまま返す。
    """
    if "/" in file_name:
        return file_name
    head = file_name.split("_", 1)[0]
    return f"{split}/{head}/{file_name}"


def merge_split(split: str) -> dict:
    """1 split を tool + hand から 1 つの COCO 辞書へマージする。"""
    tool_path = TOOL_DIR / f"instances_{split}.json"
    hand_path = HAND_DIR / f"{split}.json"
    if not tool_path.exists() or not hand_path.exists():
        raise FileNotFoundError(f"missing: {tool_path} or {hand_path}")

    tool = json.loads(tool_path.read_text(encoding="utf-8"))
    hand = json.loads(hand_path.read_text(encoding="utf-8"))

    # tool 側の file_name を真として保持。hand 側は短縮形式 (例: 14_1_0250.jpg)
    # を tool 形式 (train/14/14_1_0250.jpg) へ正規化する。
    tool_imgs = {img["id"]: img for img in tool["images"]}
    hand_imgs: dict = {}
    for img in hand["images"]:
        img2 = dict(img)
        img2["file_name"] = _normalize_hand_file_name(img2["file_name"], split)
        hand_imgs[img2["id"]] = img2

    only_tool = set(tool_imgs) - set(hand_imgs)
    only_hand = set(hand_imgs) - set(tool_imgs)
    if only_tool or only_hand:
        print(
            f"  WARN [{split}]: only_tool={len(only_tool)} only_hand={len(only_hand)} "
            f"images (tool={len(tool_imgs)} hand={len(hand_imgs)})"
        )

    # 画像は tool 側を真とし、hand 側固有のものは正規化後のものを採用。
    images = list(tool["images"])
    for img_id in only_hand:
        images.append(hand_imgs[img_id])

    # annotations を結合: tool は id をそのまま、hand は category_id をシフト。
    next_ann_id = max((a["id"] for a in tool["annotations"]), default=0) + 1
    annotations = list(tool["annotations"])
    for ann in hand["annotations"]:
        ann2 = dict(ann)
        ann2["category_id"] = _hand_cat_shift(ann["category_id"])
        ann2["id"] = next_ann_id
        next_ann_id += 1
        annotations.append(ann2)

    # categories は constants から正規生成（順序を安定化）。
    categories = coco_categories(include_hand=True)
    assert len(categories) == len(TOOL_CLASSES) + len(HAND_CLASSES) == 19

    merged = {
        "info": tool.get("info", {"description": "EgoSurgery Tool+Hand merged"}),
        "licenses": tool.get("licenses", []),
        "images": images,
        "annotations": annotations,
        "categories": categories,
    }
    print(
        f"  [{split}] images={len(images)} annotations={len(annotations)} "
        f"(tool ann={len(tool['annotations'])} + hand ann={len(hand['annotations'])})"
    )
    return merged


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"output: {OUT_DIR}")
    for split in ("train", "val", "test"):
        merged = merge_split(split)
        out_path = OUT_DIR / f"instances_{split}.json"
        out_path.write_text(
            json.dumps(merged, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        print(f"  wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()

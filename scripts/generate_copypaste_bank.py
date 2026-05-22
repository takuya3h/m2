"""Copy-Paste 用の crop バンクを生成する。

学習画像から稀少クラスの術具を bbox で切り出し、
``{output_dir}/{class_name}/{video}_{ann_id}.jpg`` として保存する。
生成された crop は :class:`BBoxCopyPaste` が読み込む。

使い方:
    python scripts/generate_copypaste_bank.py \\
        --ann_file data/annotations/egosurgery_tool/instances_train.json \\
        --img_dir data/raw/ego/train/ \\
        --output_dir data/processed/copypaste_bank/ \\
        --rare_classes Skewer Syringe Forceps
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

# scripts/ から実行されても egosurgery パッケージを import 可能にする。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from egosurgery.datasets.constants import RARE_CLASSES, TOOL_NAME_TO_ID  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """コマンドライン引数を解釈する。"""
    parser = argparse.ArgumentParser(
        description="稀少クラスの術具を crop して Copy-Paste バンクを生成する",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ann_file", required=True, type=Path,
        help="COCO 形式アノテーション JSON",
    )
    parser.add_argument(
        "--img_dir", required=True, type=Path,
        help="画像ディレクトリ",
    )
    parser.add_argument(
        "--output_dir", type=Path, default=Path("data/processed/copypaste_bank"),
        help="crop バンクの出力先",
    )
    parser.add_argument(
        "--rare_classes", nargs="+", default=list(RARE_CLASSES),
        help="crop 対象とする稀少クラス名",
    )
    parser.add_argument(
        "--min_size", type=int, default=16,
        help="この一辺（px）未満の bbox は crop しない",
    )
    parser.add_argument(
        "--padding", type=float, default=0.05,
        help="bbox の周囲に付与する余白の割合",
    )
    return parser.parse_args(argv)


def generate_bank(args: argparse.Namespace) -> dict[str, int]:
    """crop バンクを生成し、クラスごとの crop 枚数を返す。"""
    from pycocotools.coco import COCO

    target_ids = {
        TOOL_NAME_TO_ID[name]: name
        for name in args.rare_classes
        if name in TOOL_NAME_TO_ID
    }
    if not target_ids:
        print("[警告] 有効な稀少クラスが指定されていません。")
        return {}

    coco = COCO(str(args.ann_file))
    counts: dict[str, int] = {name: 0 for name in target_ids.values()}

    for cat_id, class_name in target_ids.items():
        class_dir = args.output_dir / class_name
        class_dir.mkdir(parents=True, exist_ok=True)

        for ann_id in coco.getAnnIds(catIds=[cat_id]):
            ann = coco.loadAnns(ann_id)[0]
            img_info = coco.loadImgs(ann["image_id"])[0]
            image = cv2.imread(str(args.img_dir / img_info["file_name"]))
            if image is None:
                continue

            crop = _crop_bbox(image, ann["bbox"], args.padding, args.min_size)
            if crop is None:
                continue
            out_path = class_dir / f"{img_info['id']}_{ann_id}.jpg"
            cv2.imwrite(str(out_path), crop)
            counts[class_name] += 1

    return counts


def _crop_bbox(image, bbox, padding: float, min_size: int):
    """COCO の xywh bbox を余白付きで crop する（小さすぎる場合は ``None``）。"""
    x, y, w, h = bbox
    if w < min_size or h < min_size:
        return None
    height, width = image.shape[:2]
    pad_x, pad_y = w * padding, h * padding
    x1 = max(0, int(x - pad_x))
    y1 = max(0, int(y - pad_y))
    x2 = min(width, int(x + w + pad_x))
    y2 = min(height, int(y + h + pad_y))
    if x2 <= x1 or y2 <= y1:
        return None
    return image[y1:y2, x1:x2]


def main(argv: list[str] | None = None) -> None:
    """crop バンク生成のエントリーポイント。"""
    args = parse_args(argv)
    print(f"Copy-Paste バンク生成: {args.ann_file} -> {args.output_dir}")
    counts = generate_bank(args)
    print("\n=== 生成結果 ===")
    for class_name, count in counts.items():
        print(f"  {class_name:18s} {count:5d} crops")
    print(f"\n合計 {sum(counts.values())} crops を生成しました。")


if __name__ == "__main__":
    main()

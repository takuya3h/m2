"""EgoSurgery-Tool / EgoSurgery-Phase のデータをプロジェクト構造へ配置する。

EgoSurgery のフレーム画像をプロジェクトの ``data/raw/ego/{split}/`` に
配置し、bbox アノテーションを COCO 形式 JSON へ、工程ラベルを
``phases_{split}.json`` へ変換する。最後にクラス分布の統計を出力する。

使い方:
    python scripts/preprocess_ego.py \\
        --ego_root /path/to/EgoSurgery \\
        --output_dir data/

処理内容:
1. data/splits/ の ego_{train,val,test}.txt（動画 ID リスト）を読み込む
2. 各動画のフレーム画像を data/raw/ego/{split}/ に配置（symlink / copy）
3. bbox アノテーションを COCO 形式へ変換し
   data/annotations/egosurgery_tool/instances_{split}.json に保存
4. 工程ラベルを data/annotations/egosurgery_phase/phases_{split}.json に保存
5. 15 クラスの出現頻度・不均衡比率を標準出力に表示

注意: EgoSurgery 公式データのアノテーション仕様に合わせ、入力側の
読み取り（_load_source_annotations）は実データ確認のうえ調整すること。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

# scripts/ から実行されても egosurgery パッケージを import 可能にする。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from egosurgery.datasets.constants import (  # noqa: E402
    TOOL_ID_TO_NAME,
    coco_categories,
)

SPLITS = ("train", "val", "test")
_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


# --------------------------------------------------------------------- #
# 引数
# --------------------------------------------------------------------- #
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """コマンドライン引数を解釈する。"""
    parser = argparse.ArgumentParser(
        description="EgoSurgery データをプロジェクト構造へ前処理する",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ego_root", required=True, type=Path,
        help="EgoSurgery データセットのルートディレクトリ",
    )
    parser.add_argument(
        "--output_dir", type=Path, default=Path("data"),
        help="出力先（data/ ディレクトリ）",
    )
    parser.add_argument(
        "--splits_dir", type=Path, default=None,
        help="ego_{train,val,test}.txt の場所（既定: {output_dir}/splits）",
    )
    parser.add_argument(
        "--link_mode", choices=["symlink", "copy"], default="symlink",
        help="フレーム画像の配置方式",
    )
    parser.add_argument(
        "--include_hand", action="store_true",
        help="手 4 クラスも COCO categories に含める",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------- #
# 各処理ステップ
# --------------------------------------------------------------------- #
def load_split_ids(splits_dir: Path) -> dict[str, list[str]]:
    """ego_{split}.txt から動画 ID のリストを読み込む。"""
    split_ids: dict[str, list[str]] = {}
    for split in SPLITS:
        path = splits_dir / f"ego_{split}.txt"
        if path.exists():
            ids = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            ids = []
            print(f"  [警告] split ファイルがありません: {path}")
        split_ids[split] = ids
    return split_ids


def place_frames(
    ego_root: Path, video_ids: list[str], split: str,
    output_dir: Path, link_mode: str,
) -> int:
    """各動画のフレーム画像を data/raw/ego/{split}/ に配置する。"""
    dest_root = output_dir / "raw" / "ego" / split
    dest_root.mkdir(parents=True, exist_ok=True)
    placed = 0
    for video_id in video_ids:
        src_dir = ego_root / "images" / video_id
        if not src_dir.is_dir():
            src_dir = ego_root / video_id
        if not src_dir.is_dir():
            print(f"  [警告] 動画フォルダが見つかりません: {video_id}")
            continue
        dest_dir = dest_root / video_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        for frame in sorted(src_dir.iterdir()):
            if frame.suffix.lower() not in _IMAGE_SUFFIXES:
                continue
            dest = dest_dir / frame.name
            if dest.exists():
                continue
            if link_mode == "symlink":
                dest.symlink_to(frame.resolve())
            else:
                shutil.copy2(frame, dest)
            placed += 1
    return placed


def load_source_annotations(ego_root: Path, split: str) -> dict:
    """EgoSurgery 側の bbox アノテーションを読み込む（COCO 形式想定）。

    公式データが既に COCO 形式ならそれを返す。形式が異なる場合は
    本関数を実データ仕様に合わせて調整すること。見つからなければ
    空の COCO 構造を返す。
    """
    for candidate in (
        ego_root / "annotations" / f"instances_{split}.json",
        ego_root / "annotations" / f"egosurgery_tool_{split}.json",
        ego_root / f"{split}.json",
    ):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    print(f"  [警告] {split} の bbox アノテーションが見つかりません。空で出力します。")
    return {"images": [], "annotations": []}


def build_coco_json(
    source: dict, include_hand: bool,
) -> dict:
    """読み込んだアノテーションを COCO 形式 JSON へ整形する。"""
    return {
        "info": {"description": "EgoSurgery-Tool (converted)"},
        "categories": coco_categories(include_hand=include_hand),
        "images": source.get("images", []),
        "annotations": source.get("annotations", []),
    }


def build_phase_json(ego_root: Path, video_ids: list[str], split: str) -> list[dict]:
    """工程ラベルを {"video_id", "frames":[{"frame_id","phase"}]} 形式へ変換する。"""
    records: list[dict] = []
    for video_id in video_ids:
        for candidate in (
            ego_root / "phase" / f"{video_id}.json",
            ego_root / "annotations" / "phase" / f"{video_id}.json",
        ):
            if candidate.exists():
                data = json.loads(candidate.read_text(encoding="utf-8"))
                records.append(
                    {"video_id": video_id, "frames": data.get("frames", data)}
                )
                break
    return records


def class_distribution(coco: dict) -> dict[str, int]:
    """COCO アノテーションから 15 クラスの出現頻度を集計する。"""
    counter: Counter = Counter()
    for ann in coco.get("annotations", []):
        name = TOOL_ID_TO_NAME.get(ann.get("category_id"))
        if name is not None:
            counter[name] += 1
    return dict(counter)


def report_distribution(name: str, distribution: dict[str, int]) -> None:
    """クラス分布と不均衡比率（最多 / 最少）を表示する。"""
    print(f"\n=== クラス分布: {name} ===")
    if not distribution:
        print("  （アノテーションなし）")
        return
    counts = sorted(distribution.items(), key=lambda kv: kv[1], reverse=True)
    total = sum(distribution.values())
    for class_name, count in counts:
        ratio = 100.0 * count / total if total else 0.0
        print(f"  {class_name:18s} {count:7d}  ({ratio:5.2f}%)")
    max_count = counts[0][1]
    min_count = counts[-1][1]
    imbalance = max_count / max(min_count, 1)
    print(f"  不均衡比率（最多/最少）: {imbalance:.1f}x")


# --------------------------------------------------------------------- #
# メイン
# --------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    """前処理パイプライン全体を実行する。"""
    args = parse_args(argv)
    splits_dir = args.splits_dir or (args.output_dir / "splits")

    print(f"EgoSurgery 前処理を開始: ego_root={args.ego_root}")
    split_ids = load_split_ids(splits_dir)

    ann_dir = args.output_dir / "annotations"
    (ann_dir / "egosurgery_tool").mkdir(parents=True, exist_ok=True)
    (ann_dir / "egosurgery_phase").mkdir(parents=True, exist_ok=True)

    for split in SPLITS:
        video_ids = split_ids.get(split, [])
        print(f"\n[{split}] 動画数: {len(video_ids)}")

        placed = place_frames(
            args.ego_root, video_ids, split, args.output_dir, args.link_mode
        )
        print(f"  フレーム配置: {placed} 枚")

        source = load_source_annotations(args.ego_root, split)
        coco = build_coco_json(source, include_hand=args.include_hand)
        coco_path = ann_dir / "egosurgery_tool" / f"instances_{split}.json"
        coco_path.write_text(json.dumps(coco, ensure_ascii=False), encoding="utf-8")
        print(f"  COCO JSON 出力: {coco_path} "
              f"(images={len(coco['images'])}, anns={len(coco['annotations'])})")

        phases = build_phase_json(args.ego_root, video_ids, split)
        phase_path = ann_dir / "egosurgery_phase" / f"phases_{split}.json"
        phase_path.write_text(json.dumps(phases, ensure_ascii=False), encoding="utf-8")
        print(f"  工程 JSON 出力: {phase_path} (videos={len(phases)})")

        report_distribution(split, class_distribution(coco))

    print("\n前処理が完了しました。")


if __name__ == "__main__":
    main()

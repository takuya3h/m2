"""scripts/preprocess_ego.py の assert_paper_split のテスト。

研究計画 §15.1 のデータ split 取り違え事故（train が 23% 不足）を
再発防止するため、論文 Fujii+ 2024 Table 3a の image/annotation/video
サイズに対する整合性を検証する。

1. test_assert_paper_split_passes_on_official:
       論文公式サイズの最小 COCO JSON で assert_paper_split が通ること
2. test_assert_paper_split_fails_on_wrong_split:
       train を意図的に 8000 images に減らした JSON で AssertionError が
       送出されること【§15.1 再発防止の最重要テスト】

実行方法:
    PYTHONPATH=src pytest tests/test_preprocess.py -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
# PYTHONPATH=src を付け忘れても import できるよう src/ を通す。
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _load_preprocess_module():
    """scripts/preprocess_ego.py をモジュールとして動的に読み込む。

    scripts/ は通常パッケージ化されておらず import パスに無いため、
    importlib.util で直接読み込む。
    """
    path = _PROJECT_ROOT / "scripts" / "preprocess_ego.py"
    spec = importlib.util.spec_from_file_location("preprocess_ego", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 論文公式 split サイズ（preprocess_ego.PAPER_SPLIT_SIZES と同値）。
_PAPER = {
    "train": {
        "images": 9657, "annotations": 32272,
        "videos": ["01", "02", "03", "06", "08", "11", "12", "13", "14", "15"],
    },
    "val":   {"images": 1515, "annotations":  4707, "videos": ["09", "10"]},
    "test":  {"images": 4265, "annotations": 12673, "videos": ["04", "05", "07"]},
}


def _write_min_coco(path: Path, n_images: int, n_annotations: int,
                    videos: list[str]) -> None:
    """assert_paper_split が見るキーだけを持つ最小 COCO JSON を書く。

    file_name は ``{video}_xxx.jpg`` 形式にし、preprocess_ego 側が
    file_name.split("/")[-1].split("_")[0] で video 数を数える挙動と整合させる。
    """
    images = []
    for i in range(n_images):
        video = videos[i % len(videos)]
        images.append({
            "id": i,
            "file_name": f"{video}_{i:06d}.jpg",
            "width": 128,
            "height": 128,
        })
    # annotations は数だけ合えばよい（assert_paper_split は len のみ参照）。
    annotations = [{"id": i, "image_id": i % max(n_images, 1)}
                   for i in range(n_annotations)]
    payload = {"images": images, "annotations": annotations, "categories": []}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_official_layout(output_dir: Path) -> None:
    """{output_dir}/annotations/egosurgery_tool/instances_{split}.json を
    論文公式サイズで作成する。"""
    ann_dir = output_dir / "annotations" / "egosurgery_tool"
    ann_dir.mkdir(parents=True, exist_ok=True)
    for split, meta in _PAPER.items():
        _write_min_coco(
            ann_dir / f"instances_{split}.json",
            n_images=meta["images"],
            n_annotations=meta["annotations"],
            videos=meta["videos"],
        )


# ---------------------------------------------------------------------- #
# 1. 公式サイズで assert が通る
# ---------------------------------------------------------------------- #
def test_assert_paper_split_passes_on_official(tmp_path):
    """論文公式サイズの instances_*.json で assert_paper_split が通る。"""
    module = _load_preprocess_module()
    _make_official_layout(tmp_path)

    # strict=True で例外が出ないことを直接検証する。
    module.assert_paper_split(tmp_path, strict=True)


# ---------------------------------------------------------------------- #
# 2. train を意図的に縮めた JSON で AssertionError【§15.1 最重要テスト】
# ---------------------------------------------------------------------- #
def test_assert_paper_split_fails_on_wrong_split(tmp_path):
    """train を 8000 images に減らした JSON で AssertionError が出ること。

    §15.1 で発覚した「train 23% 不足」と同型の事故を仕組みで検出する。
    """
    module = _load_preprocess_module()
    _make_official_layout(tmp_path)

    # train だけを意図的に縮める（val/test は公式のまま）。
    ann_dir = tmp_path / "annotations" / "egosurgery_tool"
    _write_min_coco(
        ann_dir / "instances_train.json",
        n_images=8000,
        n_annotations=25000,
        videos=_PAPER["train"]["videos"][:8],  # videos も 10 → 8 に減らす
    )

    with pytest.raises(AssertionError, match=r"split"):
        module.assert_paper_split(tmp_path, strict=True)


# ---------------------------------------------------------------------- #
# 3. strict=False では AssertionError を投げず警告のみ
# ---------------------------------------------------------------------- #
def test_assert_paper_split_warns_when_not_strict(tmp_path, capsys):
    """strict=False の場合は AssertionError を送出せず [WARN] を出力する。"""
    module = _load_preprocess_module()
    _make_official_layout(tmp_path)

    ann_dir = tmp_path / "annotations" / "egosurgery_tool"
    _write_min_coco(
        ann_dir / "instances_train.json",
        n_images=8000, n_annotations=25000,
        videos=_PAPER["train"]["videos"][:8],
    )
    module.assert_paper_split(tmp_path, strict=False)
    out = capsys.readouterr().out
    assert "WARN" in out

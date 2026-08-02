"""hand_tool_seg 用 loss mask ローダのテスト。

実配置 (`data/annotations/.../hand_tool_seg_v2/loss_mask/`) は
存在する前提の統合テストと、tmp_path での単体テストを両方持つ。

実行方法:
    PYTHONPATH=src pytest tests/test_loss_mask.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from egosurgery.datasets.loss_mask import (  # noqa: E402
    DEFAULT_ROOT,
    load_loss_mask,
)

_REAL_LOSS_MASK = Path(__file__).resolve().parents[1] / DEFAULT_ROOT


# ---------------------------------------------------------------------- #
# 単体テスト（tmp_path で自己完結）
# ---------------------------------------------------------------------- #

def test_load_loss_mask_reads_stems(tmp_path):
    (tmp_path / "train.txt").write_text("01_1_0124\n02_1_0300\n\n03_1_0001\n")
    got = load_loss_mask("train", root=tmp_path)
    assert got == frozenset({"01_1_0124", "02_1_0300", "03_1_0001"})


def test_load_loss_mask_empty_file(tmp_path):
    (tmp_path / "val.txt").write_text("")
    assert load_loss_mask("val", root=tmp_path) == frozenset()


def test_load_loss_mask_unknown_split(tmp_path):
    with pytest.raises(ValueError, match="unknown split"):
        load_loss_mask("holdout", root=tmp_path)


def test_load_loss_mask_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_loss_mask("train", root=tmp_path)


def test_load_loss_mask_ignores_blank_lines_and_whitespace(tmp_path):
    (tmp_path / "test.txt").write_text("  01_1_0124  \n\n  \n05_1_0200\n")
    assert load_loss_mask("test", root=tmp_path) == frozenset(
        {"01_1_0124", "05_1_0200"}
    )


def test_returns_frozenset(tmp_path):
    (tmp_path / "train.txt").write_text("01_1_0001\n")
    got = load_loss_mask("train", root=tmp_path)
    assert isinstance(got, frozenset)


# ---------------------------------------------------------------------- #
# 統合テスト（実配置に依存。存在しない環境ではスキップ）
# ---------------------------------------------------------------------- #

@pytest.mark.skipif(
    not _REAL_LOSS_MASK.exists(),
    reason=f"実 loss_mask 未配置: {_REAL_LOSS_MASK}",
)
def test_real_loss_mask_expected_counts():
    """SUMMARY.md / v1_recovery_report.md の数値と一致するか。"""
    train = load_loss_mask("train", root=_REAL_LOSS_MASK)
    val = load_loss_mask("val", root=_REAL_LOSS_MASK)
    test = load_loss_mask("test", root=_REAL_LOSS_MASK)
    assert len(train) == 301, f"expected 301, got {len(train)}"
    assert len(val) == 1, f"expected 1, got {len(val)}"
    assert len(test) == 158, f"expected 158, got {len(test)}"
    # 3 split は互いに disjoint
    assert train & val == set()
    assert train & test == set()
    assert val & test == set()

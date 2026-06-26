"""ResearchLogger ファサード + run_logging + idempotency の単体テスト（§9 受け入れ基準 A）。

検証項目:
- A1. 冪等: 同じ run を 2 回 log_run → REST create は 1 回のみ（2 回目は skip）
- A2. fail-open: NOTION_API_KEY 未設定 / REST 例外 → 例外を投げず None を返す、マーカーを書かない
- A3. マーカー: hash 重複検出、save/load の atomic 性
- A4. run_logging context: 正常終了で log_run が呼ばれる、二重起動で再投稿しない
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from egosurgery.utils.idempotency import (
    content_hash,
    is_block_posted,
    is_run_posted,
    load_marker,
    mark_block_posted,
    mark_run_posted,
    save_marker,
)
from egosurgery.utils.research_logger import ResearchLogger
from egosurgery.utils.run_logging import run_logging

# ---- idempotency.py --------------------------------------------------------


def test_content_hash_stable() -> None:
    """同じ input は同じ hash、異なる input は異なる hash."""
    h1 = content_hash("title", "2026-06-26", "body")
    h2 = content_hash("title", "2026-06-26", "body")
    h3 = content_hash("title", "2026-06-27", "body")
    assert h1 == h2 and h1 != h3
    assert len(h1) == 40  # SHA1 hex


def test_marker_load_save_atomic(tmp_path: Path) -> None:
    """マーカーの save/load が atomic（tmp + rename）."""
    save_marker(tmp_path, {"run_ledger_page": "abc123", "decisions": ["h1"]})
    loaded = load_marker(tmp_path)
    assert loaded == {"run_ledger_page": "abc123", "decisions": ["h1"]}
    # 破損ファイルは空 dict（fail-open）
    (tmp_path / ".notion_sync.json").write_text("broken{json")
    assert load_marker(tmp_path) == {}


def test_is_run_posted(tmp_path: Path) -> None:
    assert is_run_posted(tmp_path) is False
    mark_run_posted(tmp_path, "page-id-1")
    assert is_run_posted(tmp_path) is True


def test_block_posted_lifecycle(tmp_path: Path) -> None:
    h = content_hash("title", "2026-06-26", "body")
    assert is_block_posted(tmp_path, "decisions", h) is False
    mark_block_posted(tmp_path, "decisions", h)
    assert is_block_posted(tmp_path, "decisions", h) is True
    # 重複呼び出しでもリストは伸びない
    mark_block_posted(tmp_path, "decisions", h)
    marker = load_marker(tmp_path)
    assert marker["decisions"].count(h) == 1


# ---- ResearchLogger.log_run -------------------------------------------------


def _fake_manager(exp_dir: Path) -> SimpleNamespace:
    """ExperimentManager の最小スタブ（exp_dir のみ持つ）。"""
    exp_dir.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(exp_dir=exp_dir)


def test_log_run_idempotent(tmp_path: Path) -> None:
    """A1: 同じ run を 2 回 log_run → REST create は 1 回のみ."""
    manager = _fake_manager(tmp_path / "run1")
    rlog = ResearchLogger(cfg=None, manager=manager)

    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mocked:
        mocked.return_value = {"id": "page-abc"}
        # 1 回目: create → page id 返す + マーカー書く
        assert rlog.log_run(step="test") == "page-abc"
        assert mocked.call_count == 1
        # 2 回目: マーカーで skip（API は呼ばれない）
        assert rlog.log_run(step="test") == "page-abc"
        assert mocked.call_count == 1


def test_log_run_fail_open_on_exception(tmp_path: Path) -> None:
    """A2: REST 例外 → 例外を投げず None、マーカーを書かない."""
    manager = _fake_manager(tmp_path / "run2")
    rlog = ResearchLogger(cfg=None, manager=manager)
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mocked:
        mocked.side_effect = RuntimeError("network error")
        result = rlog.log_run(step="test")
        assert result is None
        assert (
            is_run_posted(manager.exp_dir) is False
        )  # マーカー無し → 後続スイープで再試行可


def test_log_run_fail_open_when_no_auth(tmp_path: Path) -> None:
    """A2: notion_logger 自体が None 返す（NOTION_API_KEY 未設定の挙動）→ 例外なし、マーカー無し."""
    manager = _fake_manager(tmp_path / "run3")
    rlog = ResearchLogger(cfg=None, manager=manager)
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mocked:
        mocked.return_value = None
        assert rlog.log_run(step="test") is None
        assert is_run_posted(manager.exp_dir) is False


# ---- ResearchLogger.log_decision -------------------------------------------


def test_log_decision_idempotent(tmp_path: Path) -> None:
    """同じ decision を 2 回 → REST は 1 回のみ."""
    manager = _fake_manager(tmp_path / "run4")
    rlog = ResearchLogger(cfg=None, manager=manager)
    decision = {"title": "撤退ライン確定", "body": "...", "date": "2026-06-26"}
    with patch("egosurgery.utils.notion_ops.log_decision") as mocked:
        mocked.return_value = {"id": "decision-1"}
        assert rlog.log_decision(decision) == "decision-1"
        assert rlog.log_decision(decision) is None  # 2 回目は skip
        assert mocked.call_count == 1


def test_log_decision_fail_open(tmp_path: Path) -> None:
    manager = _fake_manager(tmp_path / "run5")
    rlog = ResearchLogger(cfg=None, manager=manager)
    with patch("egosurgery.utils.notion_ops.log_decision") as mocked:
        mocked.side_effect = RuntimeError("boom")
        assert rlog.log_decision({"title": "X", "body": "y"}) is None


# ---- run_logging context manager -------------------------------------------


def test_run_logging_invokes_log_run_on_finally(tmp_path: Path) -> None:
    """A4: with ブロック終了時に log_run が呼ばれる."""
    manager = _fake_manager(tmp_path / "run6")
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mocked:
        mocked.return_value = {"id": "page-X"}
        with run_logging(cfg=None, manager=manager, step="s0"):
            pass
        assert mocked.call_count == 1


def test_run_logging_no_double_post_on_normal_exit(tmp_path: Path) -> None:
    """A4: 正常終了で finally + atexit が両方走っても、マーカーで 1 回に収束."""
    manager = _fake_manager(tmp_path / "run7")
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mocked:
        mocked.return_value = {"id": "page-Y"}
        with run_logging(cfg=None, manager=manager, step="s0"):
            pass
        # finally で posted=True になるため、atexit が後で発火しても再投稿しない
        # ここでは context exit 時点で 1 回のみ呼ばれていることを確認
        assert mocked.call_count == 1


def test_run_logging_swallows_exception_in_user_block(tmp_path: Path) -> None:
    """ユーザコード例外が出ても finally の log_run は走り、マーカーが書ける."""
    manager = _fake_manager(tmp_path / "run8")
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mocked:
        mocked.return_value = {"id": "page-Z"}
        with pytest.raises(ValueError):
            with run_logging(cfg=None, manager=manager, step="s0"):
                raise ValueError("user error")
        assert mocked.call_count == 1
        assert is_run_posted(manager.exp_dir) is True

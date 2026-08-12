"""sync_experiments_to_notion.py のスイープテスト（§9 受け入れ基準 B 統合）。

検証項目:
- dry-run: 未投稿 run/notes を「正確に」列挙し、API は呼ばない
- 冪等: 投稿後マーカーで二重実行が skip される
- fail-open: NOTION_API_KEY 未設定でも例外なく完走
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ / "scripts"))

from sync_experiments_to_notion import sync_run  # noqa: E402


def _make_run_dir(tmp_path: Path, name: str, with_notes: bool = False) -> Path:
    d = tmp_path / "experiments" / "transfer" / name
    d.mkdir(parents=True, exist_ok=True)
    # 最小 metrics.json と config.yaml
    (d / "metrics.json").write_text(json.dumps({"mAP": 0.5, "phase_accuracy": 0.9}))
    (d / "server.txt").write_text("lecun")
    (d / "git_commit.txt").write_text("abc1234567890def")
    if with_notes:
        (d / "notes.md").write_text("""```decision
title: dry-run テスト用 decision
status: 撤退
body: |
  this is a test decision.
```

```lesson
title: dry-run テスト用 lesson
recurrence_guard: do not retry without exponential backoff
body: |
  hit a rate limit during sync.
```
""")
    return d


def test_sync_run_dry_run_lists_unposted(tmp_path: Path) -> None:
    """dry-run でも API を呼ばず、未投稿の run + 2 ブロックを正確に列挙."""
    run_dir = _make_run_dir(tmp_path, "t1b_test_001", with_notes=True)
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mock_run:
        with patch("egosurgery.utils.notion_ops.log_decision") as mock_dec:
            with patch("egosurgery.utils.notion_ops.log_lesson") as mock_les:
                counts = sync_run(run_dir, dry_run=True)
                # dry-run なので API は 0 回
                mock_run.assert_not_called()
                mock_dec.assert_not_called()
                mock_les.assert_not_called()
                # 列挙は正確
                assert counts["run"] == 1
                assert counts["decision"] == 1
                assert counts["lesson"] == 1


def test_sync_run_real_post_then_idempotent(tmp_path: Path) -> None:
    """実投稿: 1 回目で run+decision+lesson が posted、2 回目はマーカーで skip."""
    run_dir = _make_run_dir(tmp_path, "t1b_test_002", with_notes=True)
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mock_run:
        with patch("egosurgery.utils.notion_ops.log_decision") as mock_dec:
            with patch("egosurgery.utils.notion_ops.log_lesson") as mock_les:
                mock_run.return_value = {"id": "run-page"}
                mock_dec.return_value = {"id": "dec-page"}
                mock_les.return_value = {"id": "les-page"}

                # 1 回目: 全部投稿
                c1 = sync_run(run_dir, dry_run=False)
                assert c1["run"] == 1
                assert c1["decision"] == 1
                assert c1["lesson"] == 1
                assert mock_run.call_count == 1
                assert mock_dec.call_count == 1
                assert mock_les.call_count == 1

                # 2 回目: マーカーで skip → API は増えない
                c2 = sync_run(run_dir, dry_run=False)
                assert c2["run"] == 0
                assert c2["decision"] == 0
                assert c2["lesson"] == 0
                assert mock_run.call_count == 1  # 増えない
                assert mock_dec.call_count == 1
                assert mock_les.call_count == 1


def test_sync_run_no_notes_only_run(tmp_path: Path) -> None:
    """notes.md 無しなら run だけ投稿される（fail-open: 何もしないと判定はしない）."""
    run_dir = _make_run_dir(tmp_path, "t1b_test_003", with_notes=False)
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mock_run:
        mock_run.return_value = {"id": "run-only"}
        c = sync_run(run_dir, dry_run=False)
        assert c["run"] == 1
        assert c["decision"] == 0
        assert c["lesson"] == 0


def test_sync_run_fail_open_on_api_error(tmp_path: Path) -> None:
    """API 例外でも例外を再投げせず、カウント 0 で完了."""
    run_dir = _make_run_dir(tmp_path, "t1b_test_004", with_notes=True)
    with patch("egosurgery.utils.notion_logger.log_experiment_to_notion") as mock_run:
        with patch("egosurgery.utils.notion_ops.log_decision") as mock_dec:
            mock_run.side_effect = RuntimeError("rate limit")
            mock_dec.side_effect = RuntimeError("rate limit")
            # 例外を投げず完了
            c = sync_run(run_dir, dry_run=False)
            assert c["run"] == 0
            assert c["decision"] == 0
            assert c["skipped"] >= 2  # run + 2 notes が skip 扱い

#!/usr/bin/env python3
"""Claude Code Stop/PostToolUse hook: 学習・評価コマンド完了後に Notion スイープを実行。

設計（auto_logging_implementation.md §5.5）:
- フック発火条件: Stop または「学習/評価コマンド」検知の PostToolUse
- 実行内容: `python scripts/sync_experiments_to_notion.py`（timeout + fail-open）
- **REST 経由**で投稿（MCP は対話承認が要るので無人不可）
- 失敗しても Claude Code を絶対に止めない（exit 0 で常に返す）

ログ: $CLAUDE_PROJECT_DIR/.claude/hooks/auto_notion_sync.log に追記。
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

PROJ = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
LOG = PROJ / ".claude" / "hooks" / "auto_notion_sync.log"
TIMEOUT_SEC = 60  # スイープが長引いたら諦める（fail-open）

# 学習/評価コマンドの marker（PostToolUse の場合はこれらが含まれていれば発火）
TRAINING_MARKERS = (
    "scripts/train_",
    "scripts/run_s",
    "scripts/run_t1b",
    "scripts/run_b1",
    "scripts/run_t1a",
    "scripts/run_hc",
    "scripts/postprocess_",
    "scripts/eval_",
    "scripts/audit_",
    "egosurgery.train",
)


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat()
    LOG.open("a", encoding="utf-8").write(f"[{ts}] {msg}\n")


def _should_fire_post_tool_use(payload: dict) -> bool:
    """PostToolUse hook の payload を見て学習/評価コマンドかを判定。"""
    tool_input = payload.get("tool_input", {}) or {}
    cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    return any(m in cmd for m in TRAINING_MARKERS)


def _sweep() -> int:
    """sync_experiments_to_notion.py を timeout 付きで実行。例外も握り潰す（fail-open）。"""
    try:
        # .env を source した上で sweep を呼ぶ。
        # python は .venv/bin/python があればそれ、無ければ python3/python に fallback
        # （efros 等 venv 無しホストで sweep が黙って死ぬのを防ぐ。sync スクリプトは
        #  自前で sys.path に src を追加するため PYTHONPATH は不要）。
        cmd = (
            "if [ -f .env ]; then set -a; source .env; set +a; fi; "
            "PY=$([ -x .venv/bin/python ] && echo .venv/bin/python "
            "|| command -v python3 || command -v python); "
            '"$PY" scripts/sync_experiments_to_notion.py 2>&1 || true'
        )
        result = subprocess.run(
            ["bash", "-c", cmd],
            cwd=PROJ,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC,
        )
        _log(
            f"sweep exit={result.returncode} stdout_tail={result.stdout[-300:]!r} "
            f"stderr_tail={result.stderr[-200:]!r}"
        )
    except subprocess.TimeoutExpired:
        _log(f"sweep TIMEOUT after {TIMEOUT_SEC}s → fail-open")
    except Exception as exc:  # noqa: BLE001
        _log(f"sweep exception {exc!r} → fail-open")
    return 0  # 常に成功扱い


def main() -> int:
    # Claude Code hook の payload は stdin から JSON で来る（Stop/PostToolUse 共通）
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:  # noqa: BLE001
        payload = {}

    event = payload.get("hook_event_name", "Stop")
    if event == "PostToolUse" and not _should_fire_post_tool_use(payload):
        # 学習/評価以外の PostToolUse では発火しない（ノイズ防止）
        return 0

    _log(f"hook fired (event={event})")
    return _sweep()


if __name__ == "__main__":
    sys.exit(main())

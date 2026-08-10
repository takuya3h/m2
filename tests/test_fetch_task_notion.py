"""配布台帳からの取り込み経路の検査。

**外部サービスへは接続しない。** HTTP を担う 1 箇所だけを差し替え、
経路（行の特定・要約値の照合・失敗の理由・頁送り）を検査する。
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fetch_task  # noqa: E402

DB_ID = "00000000-0000-0000-0000-000000000000"
PAGE_ID = "11111111-1111-1111-1111-111111111111"


def _page(sha: str) -> dict:
    return {
        "id": PAGE_ID,
        "properties": {
            "task_id": {"type": "title", "title": [{"plain_text": "T-2026-01-01-probe"}]},
            "sha256": {"type": "rich_text", "rich_text": [{"plain_text": sha}]},
        },
    }


def _blocks(chunks: list[str], has_more: bool = False, cursor: str | None = None) -> dict:
    return {
        "results": [
            {"type": "code", "code": {"rich_text": [{"plain_text": c} for c in chunks]}}
        ],
        "has_more": has_more,
        "next_cursor": cursor,
    }


@pytest.fixture(autouse=True)
def _registry(monkeypatch):
    """登録簿の読み取りを固定する。実ファイルへは依存しない。"""
    monkeypatch.setattr(fetch_task, "_notion_database_id", lambda: DB_ID)
    monkeypatch.setenv("NOTION_API_KEY", "dummy-not-a-real-key")


def _install_fake(monkeypatch, *, rows, chunks, has_more_first=False):
    """query と blocks の応答を差し替える。呼ばれた URL も記録する。"""
    calls: list[str] = []
    state = {"page": 0}

    def fake(url: str, body=None):
        calls.append(url)
        if "/query" in url:
            return {"results": rows}
        if "/children" in url:
            if has_more_first and state["page"] == 0:
                state["page"] = 1
                return _blocks(chunks[:1], has_more=True, cursor="CUR")
            return _blocks(chunks[1:] if has_more_first else chunks)
        raise AssertionError(f"想定外の URL: {url}")

    monkeypatch.setattr(fetch_task, "_notion_call", fake)
    return calls


def test_task_id_locates_the_row(monkeypatch):
    text = "#!TASK-BUNDLE v1 delim=X\n"
    sha = hashlib.sha256(text.encode()).hexdigest()
    calls = _install_fake(monkeypatch, rows=[_page(sha)], chunks=[text])
    assert fetch_task.read_notion_bundle("T-2026-01-01-probe") == text
    assert any("/query" in c for c in calls)


def test_unknown_task_id_fails_with_reason(monkeypatch):
    _install_fake(monkeypatch, rows=[], chunks=[])
    with pytest.raises(fetch_task.BundleError) as exc:
        fetch_task.read_notion_bundle("T-2099-01-01-no-such-task")
    assert "T-2099-01-01-no-such-task" in str(exc.value)


def test_sha256_mismatch_is_rejected(monkeypatch):
    text = "本文が改変された場合\n"
    wrong = hashlib.sha256(b"different").hexdigest()
    _install_fake(monkeypatch, rows=[_page(wrong)], chunks=[text])
    with pytest.raises(fetch_task.BundleError) as exc:
        fetch_task.read_notion_bundle("T-2026-01-01-probe")
    assert "要約値" in str(exc.value)


def test_missing_credential_fails_with_reason(monkeypatch):
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    with pytest.raises(fetch_task.BundleError) as exc:
        fetch_task.read_notion_bundle("T-2026-01-01-probe")
    assert "NOTION_API_KEY" in str(exc.value)


def test_paginated_blocks_are_concatenated(monkeypatch):
    part_a, part_b = "前半\n", "後半\n"
    text = part_a + part_b
    sha = hashlib.sha256(text.encode()).hexdigest()
    _install_fake(monkeypatch, rows=[_page(sha)], chunks=[part_a, part_b], has_more_first=True)
    assert fetch_task.read_notion_bundle("T-2026-01-01-probe") == text


def test_read_source_routes_to_the_shared_intake(monkeypatch):
    """取得方法だけが分かれ、取り込みの流れは複製しない。"""
    text = "#!TASK-BUNDLE v1 delim=Y\n"
    sha = hashlib.sha256(text.encode()).hexdigest()
    _install_fake(monkeypatch, rows=[_page(sha)], chunks=[text])
    assert fetch_task.read_source("notion:T-2026-01-01-probe") == text


def test_credential_is_not_included_in_the_error(monkeypatch):
    """失敗の理由に資格情報そのものを混ぜない。"""
    monkeypatch.setenv("NOTION_API_KEY", "SECRET-VALUE-MUST-NOT-LEAK")
    _install_fake(monkeypatch, rows=[], chunks=[])
    with pytest.raises(fetch_task.BundleError) as exc:
        fetch_task.read_notion_bundle("T-2099-01-01-no-such-task")
    assert "SECRET-VALUE-MUST-NOT-LEAK" not in str(exc.value)

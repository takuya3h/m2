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


# --------------------------------------------------------------------------- #
# 添付からの取り込み
#
# 実測（2026-08-10・配布台帳）にもとづく形。添付は行の列ではなく**ページの子の
# file ブロック**として置かれる。台帳の列に files 型は存在しない。
# 参照先は署名つきで**取得のたびに変わり、期限は 60 分**である。
# --------------------------------------------------------------------------- #

ATTACH_URL = "https://example.invalid/probe_bundle.txt?signature=REDACTED"


def _file_block(url: str = ATTACH_URL, expiry: str = "2026-08-10T21:00:00.000Z") -> dict:
    return {
        "type": "file",
        "file": {"type": "file", "file": {"url": url, "expiry_time": expiry}},
    }


def _mixed_blocks(*blocks: dict, has_more: bool = False, cursor: str | None = None) -> dict:
    return {"results": list(blocks), "has_more": has_more, "next_cursor": cursor}


def _install_blocks(monkeypatch, *, rows, children):
    """query と children の応答を差し替える。children は呼ばれるたびに 1 つ取り出す。"""
    seen: list[str] = []
    remaining = list(children)

    def fake(url: str, body=None):
        seen.append(url)
        if "/query" in url:
            return {"results": rows}
        if "/children" in url:
            return remaining.pop(0) if len(remaining) > 1 else remaining[0]
        raise AssertionError(f"想定外の URL: {url}")

    monkeypatch.setattr(fetch_task, "_notion_call", fake)
    return seen


def test_attachment_is_preferred_over_body(monkeypatch):
    """添付と本文の両方がある行では、添付から読む。"""
    attached = "#!TASK-BUNDLE v1 delim=A\n添付の本文\n"
    sha = hashlib.sha256(attached.encode()).hexdigest()
    body_block = {"type": "code", "code": {"rich_text": [{"plain_text": "本文の側\n"}]}}
    _install_blocks(
        monkeypatch,
        rows=[_page(sha)],
        children=[_mixed_blocks(_file_block(), body_block)],
    )
    monkeypatch.setattr(fetch_task, "_download_attachment", lambda url: attached)
    assert fetch_task.read_notion_bundle("T-2026-01-01-probe") == attached


def test_body_path_is_unchanged_without_attachment(monkeypatch):
    """添付が無い行は従来どおり本文から集める。既存の行の挙動を変えない。"""
    text = "#!TASK-BUNDLE v1 delim=B\n"
    sha = hashlib.sha256(text.encode()).hexdigest()
    code_block = {"type": "code", "code": {"rich_text": [{"plain_text": text}]}}
    _install_blocks(monkeypatch, rows=[_page(sha)], children=[_mixed_blocks(code_block)])
    assert fetch_task.read_notion_bundle("T-2026-01-01-probe") == text


def test_attachment_sha256_mismatch_is_rejected(monkeypatch):
    """添付でも要約値が一致しなければ受け付けない。"""
    _install_blocks(
        monkeypatch,
        rows=[_page(hashlib.sha256(b"declared-something-else").hexdigest())],
        children=[_mixed_blocks(_file_block())],
    )
    monkeypatch.setattr(fetch_task, "_download_attachment", lambda url: "取得した別の本文\n")
    with pytest.raises(fetch_task.BundleError) as exc:
        fetch_task.read_notion_bundle("T-2026-01-01-probe")
    assert "要約値" in str(exc.value)


def test_attachment_download_failure_fails_with_reason(monkeypatch):
    """取得に失敗したら、理由の分かる失敗にする。黙って本文へ落ちない。"""
    _install_blocks(
        monkeypatch,
        rows=[_page("0" * 64)],
        children=[_mixed_blocks(_file_block())],
    )

    def boom(url):
        raise fetch_task.BundleError("添付を取得できません: HTTP 500")

    monkeypatch.setattr(fetch_task, "_download_attachment", boom)
    with pytest.raises(fetch_task.BundleError) as exc:
        fetch_task.read_notion_bundle("T-2026-01-01-probe")
    assert "添付" in str(exc.value)


def test_expired_attachment_url_is_refetched_and_retried(monkeypatch):
    """参照先が期限切れなら、ブロックから取り直して再試行する。

    実測: 参照先は取得のたびに変わる。期限切れは取り直しで回復する。
    """
    fresh = "https://example.invalid/probe_bundle.txt?signature=FRESH"
    attached = "#!TASK-BUNDLE v1 delim=C\n再試行で取れた本文\n"
    sha = hashlib.sha256(attached.encode()).hexdigest()
    _install_blocks(
        monkeypatch,
        rows=[_page(sha)],
        children=[
            _mixed_blocks(_file_block(ATTACH_URL)),   # 1 回目: 期限切れの参照先
            _mixed_blocks(_file_block(fresh)),        # 取り直し: 新しい参照先
        ],
    )
    tried: list[str] = []

    def flaky(url):
        tried.append(url)
        if url == ATTACH_URL:
            raise fetch_task.AttachmentExpired("参照先の期限が切れています")
        return attached

    monkeypatch.setattr(fetch_task, "_download_attachment", flaky)
    assert fetch_task.read_notion_bundle("T-2026-01-01-probe") == attached
    assert tried == [ATTACH_URL, fresh], "取り直した参照先で再試行していない"


def test_attachment_download_does_not_send_credentials(monkeypatch):
    """署名つきの参照先へ資格情報を送らない。送れば外部へ漏れる。"""
    monkeypatch.setenv("NOTION_API_KEY", "SECRET-VALUE-MUST-NOT-LEAK")
    captured: dict = {}

    class FakeResponse:
        def read(self):
            return b"#!TASK-BUNDLE v1 delim=D\n"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(request, timeout=None):
        captured["headers"] = dict(getattr(request, "headers", {}) or {})
        return FakeResponse()

    monkeypatch.setattr(fetch_task.urllib.request, "urlopen", fake_urlopen)
    fetch_task._download_attachment(ATTACH_URL)
    joined = " ".join(f"{k}:{v}" for k, v in captured["headers"].items())
    assert "SECRET-VALUE-MUST-NOT-LEAK" not in joined
    assert not any(k.lower() == "authorization" for k in captured["headers"])

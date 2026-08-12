"""完了報告の送り返しの検査。

**外部サービスへは接続しない。** 応答を差し替えて経路だけを見る。
送信は取り消せないため、拒む側の検査を先に固める。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fetch_task as F  # noqa: E402
import report_task as R  # noqa: E402

TASK_ID = "T-2026-01-01-example"

PAIR = {
    "result_version": 2,
    "task_id": TASK_ID,
    "status": "pass",
    "host": "lecun",
    "branch": "feat/example",
    "gates": [{"id": "G1", "verdict": "pass", "note": "測った"}],
    "tests": {"before_failed": 5, "after_failed": 5, "after_passed": 10},
    "deviations": [{"type": "judgement", "note": "判断した"}],
    "issuer_defects": [{"type": "self_contradiction", "note": "あ" * 80}],
    "followups": [],
    "unknowns": [],
    "commits": ["abc1234"],
}


def _make_task(tmp_path, *, body="# 報告\n\n普通の本文\n", with_pair=True, task_id=TASK_ID):
    tasks = tmp_path / "tasks"
    d = tasks / task_id
    d.mkdir(parents=True)
    (d / "RESULT.md").write_text(body, encoding="utf-8")
    if with_pair:
        pair = dict(PAIR, task_id=task_id)
        (d / "result.yaml").write_text(yaml.safe_dump(pair, allow_unicode=True), encoding="utf-8")
    return tasks


# --- 秘匿の検査 -------------------------------------------------------------


def test_env_credential_in_body_is_detected():
    """最も確実な照合。環境にある値そのものが本文に現れるかを直接見る。"""
    env = {"NOTION_API_KEY": "ntn_" + "z" * 30}
    found = R.scan_secrets(f"設定は {env['NOTION_API_KEY']} です", env=env)
    assert found and any("NOTION_API_KEY" in f for f in found)


def test_secret_value_is_never_echoed():
    """**何に一致したかは出すが、値は出さない。**"""
    secret = "ntn_" + "q" * 30
    found = R.scan_secrets(f"key={secret}", env={"NOTION_API_KEY": secret})
    assert found
    assert all(secret not in f for f in found)


def test_known_prefix_is_detected_without_the_env():
    """手元に値が無くても、形で気付ける。"""
    assert R.scan_secrets("token: secret_" + "a" * 32, env={})


def test_plain_identifier_is_not_a_secret():
    """設定値は対象外。平易な識別子で偽陽性を出すと送れなくなる。"""
    text = "WANDB_PROJECT=egosurgery_multitask\nDATA_ROOT=/path/to/data\n"
    assert R.scan_secrets(text, env={"WANDB_API_KEY": "0123456789abcdef" * 2 + "01234567"}) == []


def test_short_env_value_is_not_matched():
    """短い値は偶然一致する。照合の対象にしない。"""
    assert R.scan_secrets("status は pass です", env={"NOTION_API_KEY": "pass"}) == []


@pytest.mark.parametrize(
    ("name", "text", "should_stop"),
    [
        ("hex40_should_pass", "commit " + "0123456789abcdef" * 2 + "01234567 を参照", False),
        ("plain_should_pass", "これは普通の文章である", False),
        ("dash_should_stop", "api-key: " + "z" * 40, True),
        ("lower_password_stop", "password=" + "q" * 20, True),
        ("notion_should_stop", "NOTION_API_KEY=" + "x" * 40, True),
        ("wandb_should_stop", "WANDB_API_KEY=" + "y" * 40, True),
        ("report_like", "九台すべてが Permission denied (publickey,password) を返した。", False),
    ],
)
def test_secret_scan_regression_controls(name, text, should_stop):
    """履歴識別子と報告文を通し、資格情報の代入だけを止める。"""
    assert bool(R.scan_secrets(text, env={})) is should_stop, name


def test_send_refuses_when_secret_present(tmp_path, monkeypatch):
    body = "# 報告\n\nkey: secret_" + "b" * 32 + "\n"
    tasks = _make_task(tmp_path, body=body)
    monkeypatch.setattr(F, "_notion_call_method", lambda *a, **k: pytest.fail("送ってはならない"))
    with pytest.raises(R.ReportError) as exc:
        R.send_report(TASK_ID, tasks, dry_run=True)
    assert "送信しません" in str(exc.value)


def test_send_allows_clean_body(tmp_path):
    tasks = _make_task(tmp_path)
    out = R.send_report(TASK_ID, tasks, dry_run=True)
    assert out["verdict"] == "pass" and out["n_issuer_defects"] == 1
    assert out["report_bytes"] > 0 and len(out["report_sha256"]) == 64


# --- 材料の読み取り ---------------------------------------------------------


def test_missing_pair_is_refused(tmp_path):
    tasks = _make_task(tmp_path, with_pair=False)
    with pytest.raises(R.ReportError) as exc:
        R.send_report(TASK_ID, tasks, dry_run=True)
    assert "構造化された対" in str(exc.value)


def test_missing_report_is_refused(tmp_path):
    tasks = tmp_path / "tasks"
    (tasks / TASK_ID).mkdir(parents=True)
    with pytest.raises(R.ReportError):
        R.send_report(TASK_ID, tasks, dry_run=True)


def test_verdict_comes_from_the_pair_not_the_prose(tmp_path):
    """散文から抽出しない。対に書かれた値だけを使う。"""
    tasks = _make_task(tmp_path, body="# 報告\n\n状態は stopped だと本文に書いてある\n")
    assert R.send_report(TASK_ID, tasks, dry_run=True)["verdict"] == "pass"


# --- 台帳への書き込み（応答を差し替える） -----------------------------------


class _Ledger:
    """台帳の最小の模型。呼び出しの順序と本文を覚える。"""

    def __init__(self, blocks=None, rows=1):
        self.blocks = list(blocks or [])
        self.rows = rows
        self.calls: list[tuple[str, str]] = []
        self.props: dict = {}

    def query(self, url, body=None):
        if "/databases/" in url and body is not None:
            return {"results": [{"id": "page-1", "properties": {}} for _ in range(self.rows)]}
        if "/blocks/" in url and "/children" in url:
            return {"results": self.blocks, "has_more": False}
        return {}

    def method(self, verb, url, body=None):
        self.calls.append((verb, url))
        if verb == "DELETE":
            self.blocks = [b for b in self.blocks if b["id"] not in url]
        elif verb == "PATCH" and "/children" in url:
            self.blocks.extend(body["children"])
        elif verb == "PATCH" and "/pages/" in url:
            self.props = body["properties"]
        return {}


def _wire(monkeypatch, ledger):
    monkeypatch.setattr(F, "_notion_call", ledger.query)
    monkeypatch.setattr(F, "_notion_call_method", ledger.method)
    monkeypatch.setattr(F, "_notion_database_id", lambda: "db-1")
    monkeypatch.setenv("NOTION_API_KEY", "x" * 40)


def _report_block(text):
    return {
        "id": "blk-old",
        "type": "code",
        "code": {"rich_text": [{"plain_text": R.REPORT_SENTINEL + "\n" + text}]},
    }


def test_second_send_replaces_instead_of_appending(tmp_path, monkeypatch):
    """**二度送っても行が壊れない。** 追記を繰り返すと読めなくなる。"""
    tasks = _make_task(tmp_path)
    ledger = _Ledger(blocks=[_report_block("古い報告")])
    _wire(monkeypatch, ledger)

    out = R.send_report(TASK_ID, tasks)
    assert out["replaced_blocks"] == 1
    reports = [b for b in ledger.blocks if b.get("type") == "code"]
    assert len(reports) == 1
    assert "DELETE" in [verb for verb, _ in ledger.calls]


def test_contract_block_is_left_alone(tmp_path, monkeypatch):
    """契約本文のブロックには触れない。目印の無い code は消さない。"""
    contract = {"id": "blk-contract", "type": "code",
                "code": {"rich_text": [{"plain_text": "#!TASK-BUNDLE v1 ..."}]}}
    tasks = _make_task(tmp_path)
    ledger = _Ledger(blocks=[contract])
    _wire(monkeypatch, ledger)
    R.send_report(TASK_ID, tasks)
    assert contract in ledger.blocks


def test_status_columns_are_written(tmp_path, monkeypatch):
    tasks = _make_task(tmp_path)
    ledger = _Ledger()
    _wire(monkeypatch, ledger)
    R.send_report(TASK_ID, tasks)
    assert ledger.props["status"]["select"]["name"] == "done"
    assert ledger.props["verdict"]["select"]["name"] == "pass"
    assert ledger.props["n_issuer_defects"]["number"] == 1
    assert len(ledger.props["report_sha256"]["rich_text"][0]["text"]["content"]) == 64


def test_missing_row_is_refused(tmp_path, monkeypatch):
    tasks = _make_task(tmp_path)
    ledger = _Ledger(rows=0)
    _wire(monkeypatch, ledger)
    with pytest.raises(F.BundleError) as exc:
        R.send_report(TASK_ID, tasks)
    assert "見つかりません" in str(exc.value)


def test_body_is_split_but_rejoins(tmp_path, monkeypatch):
    """上限ごとに切って送るが、取得時は連結されて返る。境界は覚えない。"""
    body = "あ" * 4500
    tasks = _make_task(tmp_path, body=body)
    ledger = _Ledger()
    _wire(monkeypatch, ledger)
    R.send_report(TASK_ID, tasks)
    items = ledger.blocks[0]["code"]["rich_text"]
    assert len(items) == 3
    assert all(len(i["text"]["content"]) <= R.RICH_TEXT_LIMIT for i in items)
    joined = "".join(i["text"]["content"] for i in items)
    assert joined == R.REPORT_SENTINEL + "\n" + body


@pytest.mark.parametrize(
    "body",
    [
        "\U0001f534" * 1001,
        "あ" * 1999 + "\U0001f534" + "い",
        "あ" * 4501,
    ],
)
def test_rich_text_uses_utf16_units_and_rejoins(body):
    """受け側の UTF-16 単位上限を守り、文字を壊さず元へ戻せる。"""
    items = R._rich_text(body)
    chunks = [item["text"]["content"] for item in items]
    assert all(len(chunk.encode("utf-16-le")) // 2 <= R.RICH_TEXT_LIMIT for chunk in chunks)
    assert "".join(chunks) == body


def test_report_block_is_not_read_as_contract_body():
    """送り返した報告を、取り込み側が契約本文として拾わないこと。"""
    blocks = [
        {"type": "code", "code": {"rich_text": [{"plain_text": "契約の本文"}]}},
        {"type": "code", "code": {"rich_text": [{"plain_text": R.REPORT_SENTINEL + "\n報告"}]}},
    ]
    original = F._iter_child_blocks
    F._iter_child_blocks = lambda page_id: iter(blocks)  # noqa: E731
    try:
        url, body = F._scan_children("page-1")
    finally:
        F._iter_child_blocks = original
    assert url is None
    assert body == "契約の本文"

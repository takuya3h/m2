import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_context import _parse_backlog_entries  # noqa: E402

SAMPLE_BACKLOG = """# backlog

| id | # | 事項 | 分かっていること | 着手の前提 |
|---|---|---|---|---|
| BL-example-one | B-1 | 通常の事項 | 詳細 | 前提 |
| BL-example-two | B-2 | 🔴 **重大な事項** | 詳細 | 前提 |
| ~~BL-example-three~~ | ~~B-3~~ | ~~解決済みの事項~~ | 解決済み | — |
"""


def test_parses_open_entries_only_excludes_resolved():
    entries, skipped = _parse_backlog_entries(SAMPLE_BACKLOG)
    slugs = [e["slug"] for e in entries]
    assert "BL-example-one" in slugs
    assert "BL-example-two" in slugs
    assert "BL-example-three" not in [e["slug"] for e in entries if not e["resolved"]]
    assert skipped == 0


def test_resolved_entry_flagged_true():
    entries, _ = _parse_backlog_entries(SAMPLE_BACKLOG)
    resolved = [e for e in entries if e["slug"] == "BL-example-three"]
    assert len(resolved) == 1
    assert resolved[0]["resolved"] is True


def test_critical_marker_detected():
    entries, _ = _parse_backlog_entries(SAMPLE_BACKLOG)
    flagged = {e["slug"]: e["flagged"] for e in entries}
    assert flagged["BL-example-one"] is False
    assert flagged["BL-example-two"] is True


def test_heading_strips_emoji_and_bold_markup():
    entries, _ = _parse_backlog_entries(SAMPLE_BACKLOG)
    heading = next(e["heading"] for e in entries if e["slug"] == "BL-example-two")
    assert "🔴" not in heading
    assert "**" not in heading
    assert heading == "重大な事項"


def test_pipe_in_heading_is_escaped():
    text = "| BL-pipe-case | B-9 | a " + chr(124) + " b の比較 | 詳細 | 前提 |\n"
    entries, skipped = _parse_backlog_entries(text)
    assert skipped == 1
    assert entries == []


def test_malformed_row_is_skipped_not_fabricated():
    text = "| BL-broken | B-10 |\n"
    entries, skipped = _parse_backlog_entries(text)
    assert entries == []
    assert skipped == 1


def test_no_entries_when_backlog_empty():
    entries, skipped = _parse_backlog_entries("")
    assert entries == []
    assert skipped == 0

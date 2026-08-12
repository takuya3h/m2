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


def test_stamp_names_runindex_as_its_source():
    """生成元は runindex/ である。**値は commit ではなく内容の要約値。**

    かつては runindex/ の最終更新 commit を刻んでいたが、索引と投影を同じ commit へ
    入れるとその commit 自身が最終更新になり、再生成した値が記録済みの値と食い違って
    検査が常に 1 つ遅れた。内容から作れば記録したかどうかに左右されない。
    """
    from build_context import resolve_stamp_source

    source = resolve_stamp_source()
    assert source["path"] == "runindex/"
    assert source["digest"]
    assert "commit" not in source and "date" not in source


def test_stamp_is_stable_when_only_head_moves():
    """runindex が変わらない限り、スタンプは変化しない。"""
    from build_context import resolve_stamp_source

    first = resolve_stamp_source()
    second = resolve_stamp_source()
    assert first == second


# --- 来歴のスタンプ ---------------------------------------------------------
#
# 索引に触れた最後の commit をスタンプすると、**索引を記録した瞬間に古くなる。**
# 生成 → 索引と投影を commit → 検査、の順で必ず 1 つ遅れ、検査が落ちる。
# 内容そのものから作れば commit の順序に依存しない。

import hashlib  # noqa: E402

import build_context  # noqa: E402


def _fake_runindex(tmp_path, index_body="a\n1\n"):
    d = tmp_path / "runindex"
    d.mkdir(parents=True)
    (d / "index.csv").write_text(index_body, encoding="utf-8")
    (d / "experiments.csv").write_text("b\n2\n", encoding="utf-8")
    (d / "verdicts.csv").write_text("c\n3\n", encoding="utf-8")
    return d


def test_stamp_is_derived_from_content(tmp_path, monkeypatch):
    d = _fake_runindex(tmp_path)
    monkeypatch.setattr(build_context, "RUNINDEX_DIR", d)
    source = build_context.resolve_stamp_source()
    assert "digest" in source
    assert source["digest"] != "UNKNOWN"


def test_stamp_changes_when_content_changes(tmp_path, monkeypatch):
    d = _fake_runindex(tmp_path)
    monkeypatch.setattr(build_context, "RUNINDEX_DIR", d)
    before = build_context.resolve_stamp_source()["digest"]
    (d / "index.csv").write_text("a\n1\n2\n", encoding="utf-8")
    after = build_context.resolve_stamp_source()["digest"]
    assert before != after


def test_stamp_is_stable_for_identical_content(tmp_path, monkeypatch):
    """同じ内容なら同じ値。commit したかどうかに左右されない。"""
    d1 = _fake_runindex(tmp_path / "one")
    d2 = _fake_runindex(tmp_path / "two")
    monkeypatch.setattr(build_context, "RUNINDEX_DIR", d1)
    a = build_context.resolve_stamp_source()["digest"]
    monkeypatch.setattr(build_context, "RUNINDEX_DIR", d2)
    b = build_context.resolve_stamp_source()["digest"]
    assert a == b


def test_stamp_does_not_use_git(tmp_path, monkeypatch):
    """git を呼ばない。呼ぶと作業ツリーの記録状態に依存して遅れが戻る。"""
    d = _fake_runindex(tmp_path)
    monkeypatch.setattr(build_context, "RUNINDEX_DIR", d)

    def _boom(*args, **kwargs):
        raise AssertionError("スタンプの算出で git を呼んではならない")

    monkeypatch.setattr(build_context, "_run_git", _boom)
    assert build_context.resolve_stamp_source()["digest"]


def test_stamp_is_sha256_of_the_three_sources(tmp_path, monkeypatch):
    d = _fake_runindex(tmp_path)
    monkeypatch.setattr(build_context, "RUNINDEX_DIR", d)
    expect = hashlib.sha256()
    for name in ("index.csv", "experiments.csv", "verdicts.csv"):
        expect.update((d / name).read_bytes())
    assert build_context.resolve_stamp_source()["digest"] == expect.hexdigest()[:12]

"""notes.md fenced block parser のテスト（§9 受け入れ基準 B）。

検証項目:
- 正常: decision / lesson / prompt の単独・複数・混在ブロック
- 壊れた YAML / 未知キー / title 欠落 / ブロック無し
- 日本語 status の正規化（採用→active, 撤退→superseded, 保留→needs review）
"""

from __future__ import annotations

from pathlib import Path

from egosurgery.utils.notes_schema import (
    DECISION_STATUS_MAP,
    parse_notes,
    parse_notes_file,
    valid_blocks,
)


def test_parse_empty_notes() -> None:
    """ブロック無しは空 list."""
    assert parse_notes("") == []
    assert parse_notes("just text\nno blocks here") == []


def test_parse_single_decision() -> None:
    text = """```decision
title: 撤退ライン確定
status: 撤退
affects: §17.1
body: |
  CA/FiLM/rescore すべてで改善せず。
  方向非対称が確定。
```"""
    blocks = parse_notes(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert b.type == "decision"
    assert b.data["title"] == "撤退ライン確定"
    assert b.data["status"] == "superseded"  # 撤退 → superseded
    assert b.data["affects"] == "§17.1"
    assert "CA/FiLM/rescore" in b.data["body"]
    assert b.warnings == []


def test_parse_single_lesson() -> None:
    text = """```lesson
title: NpzFile OOM
recurrence_guard: _index_npz で一括展開
body: |
  per-key ループが exit137 の原因。
```"""
    blocks = parse_notes(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert b.type == "lesson"
    assert b.data["title"] == "NpzFile OOM"
    assert b.data["recurrence_guard"] == "_index_npz で一括展開"


def test_parse_multiple_blocks() -> None:
    text = """前置きテキスト

```decision
title: 採用案
status: 採用
body: |
  X を試す。
```

中間テキスト

```lesson
title: バグ
recurrence_guard: テスト追加
body: |
  Y のせい。
```
"""
    blocks = parse_notes(text)
    assert len(blocks) == 2
    assert blocks[0].type == "decision"
    assert blocks[0].data["status"] == "active"  # 採用 → active
    assert blocks[1].type == "lesson"


def test_parse_unknown_key_is_warned_not_failed() -> None:
    """未知キーは警告だが解析は続行（前方互換）."""
    text = """```decision
title: X
unknown_field: foo
body: ok
```"""
    blocks = parse_notes(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert b.data["title"] == "X"
    assert any("unknown_field" in w for w in b.warnings)


def test_parse_missing_title_marks_invalid() -> None:
    """title 欠落は warnings に出るが parse 自体は壊さない."""
    text = """```decision
status: 採用
body: title 無し
```"""
    blocks = parse_notes(text)
    assert len(blocks) == 1
    b = blocks[0]
    assert "title" in b.warnings[-1]
    # valid_blocks では除外される
    assert valid_blocks(blocks) == []


def test_decision_status_map_complete() -> None:
    """日本語 status enum がすべて map されている."""
    for ja in ("採用", "撤退", "保留"):
        assert ja in DECISION_STATUS_MAP
    assert DECISION_STATUS_MAP["採用"] == "active"
    assert DECISION_STATUS_MAP["撤退"] == "superseded"


def test_parse_notes_file_missing(tmp_path: Path) -> None:
    """ファイル不在は空 list（fail-open）."""
    assert parse_notes_file(tmp_path / "absent.md") == []


def test_parse_notes_file_present(tmp_path: Path) -> None:
    notes = tmp_path / "notes.md"
    notes.write_text("""```lesson
title: T1
recurrence_guard: guard
body: |
  body text
```
""")
    blocks = parse_notes_file(notes)
    assert len(blocks) == 1
    assert blocks[0].data["title"] == "T1"


def test_valid_blocks_filters_invalid() -> None:
    text = """```decision
title: A
body: ok
```

```decision
status: 採用
body: title なし
```
"""
    blocks = parse_notes(text)
    valid = valid_blocks(blocks)
    assert len(valid) == 1
    assert valid[0].data["title"] == "A"


def test_prompt_block_parses() -> None:
    text = """```prompt
title: T1b-CA runbook
target: Claude Code CLI
body: |
  ステップ手順。
```"""
    blocks = parse_notes(text)
    assert len(blocks) == 1
    assert blocks[0].type == "prompt"
    assert blocks[0].data["target"] == "Claude Code CLI"

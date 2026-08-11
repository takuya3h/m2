"""tools/check_docs.py の試験。

通る例と通らない例の双方を置く。**検出できないものを検出したことにしない**ため、
偽陽性として除外する範囲にも試験を置く。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from check_docs import (  # noqa: E402
    check_text,
    extract_make_names,
    extract_paths,
    parse_audit_targets,
)

TARGETS = {"context", "context-check", "taskindex", "test"}
BRANCHES = {"docs/plan-rewrite-2026-06", "exp/lecun"}


def _exists(path: str) -> bool:
    return path in {
        "tools/build_context.py",
        "context/conventions.md",
        "scripts/sync/keeper.sh",
    }


def _check(text: str, doc: str = "sample.md"):
    return check_text(doc, text, targets=TARGETS, exists=_exists, branches=BRANCHES)


# --- 通る例 -----------------------------------------------------------------


def test_existing_make_and_path_pass():
    text = "再生成は `make context` を使う。実装は `tools/build_context.py`。\n"
    assert _check(text) == []


def test_command_line_in_code_block_passes():
    text = "```bash\nmake taskindex\n```\n"
    assert _check(text) == []


# --- 通らない例 -------------------------------------------------------------


def test_unknown_make_is_rejected():
    text = "実験は `make s0` で起動する。\n"
    problems = _check(text)
    assert len(problems) == 1
    assert "make s0" in problems[0]


def test_missing_path_is_rejected():
    text = "詳細は `context/plan_mirror.md` を参照。\n"
    problems = _check(text)
    assert len(problems) == 1
    assert "context/plan_mirror.md" in problems[0]


def test_line_number_is_reported():
    text = "一行目\n二行目\n`make nope` は無い\n"
    problems = _check(text)
    assert len(problems) == 1
    assert ":3" in problems[0]


# --- 偽陽性として除外する範囲 -----------------------------------------------


def test_variable_lines_are_skipped():
    text = "起動は `scripts/run_s${N}.sh`。設定は `configs/<name>.yaml`。\n"
    assert _check(text) == []


def test_prose_make_is_not_a_target():
    text = "If none exist and you are about to make a non-trivial change, ask.\n"
    assert extract_make_names(text) == []
    assert _check(text) == []


def test_branch_name_is_not_a_path():
    text = "歴史的記録の分岐は `docs/plan-rewrite-2026-06` である。\n"
    assert _check(text) == []


def test_ignore_line_marker():
    text = "候補は `docs/incidents.md` である。 <!-- docs-check: ignore-line -->\n"
    assert _check(text) == []


def test_ignore_file_marker():
    text = "<!-- docs-check: ignore-file -->\n`make s0` も `docs/nope.md` も見ない。\n"
    assert _check(text) == []


def test_out_of_scope_prefixes_are_skipped():
    text = "`data/annotations/x.json` と `experiments/baselines/s0_001/` は対象外。\n"
    assert extract_paths(text) == []


# --- 対象の一覧の解析 -------------------------------------------------------


def test_parse_audit_targets_takes_only_current():
    audit = (
        "| 文書 | 分類 | 根拠 |\n"
        "|---|---|---|\n"
        "| README.md | 現行手順 | 実行方法 |\n"
        "| docs/old.md | 記録 | 過去 |\n"
        "| experiments/ 配下 633 件 | 記録 | 証跡 |\n"
    )
    assert parse_audit_targets(audit) == ["README.md"]


def test_parse_audit_targets_accepts_dot_directories():
    """先頭がドットの経路を落とさない。落とすと .claude/ 配下が静かに未検査になる。"""
    audit = (
        "| 文書 | 分類 | 根拠 |\n"
        "|---|---|---|\n"
        "| .claude/skills/task/SKILL.md | 現行手順 | 手順書 |\n"
    )
    assert parse_audit_targets(audit) == [".claude/skills/task/SKILL.md"]


def test_parse_audit_targets_ignores_non_path_rows():
    audit = (
        "| 文書 | 分類 | 根拠 |\n"
        "|---|---|---|\n"
        "| 現行手順の全 42 件 | 現行手順 | 集約行であって経路ではない |\n"
    )
    assert parse_audit_targets(audit) == []


# --- 落ちないこと -----------------------------------------------------------


def test_missing_document_is_reported_not_raised(tmp_path):
    from check_docs import check_documents

    problems = check_documents(
        [str(tmp_path / "does_not_exist.md")],
        targets=TARGETS,
        exists=_exists,
        branches=BRANCHES,
    )
    assert len(problems) == 1
    assert "does_not_exist.md" in problems[0]


def test_no_documents_is_not_an_error():
    from check_docs import check_documents

    assert check_documents([], targets=TARGETS, exists=_exists, branches=BRANCHES) == []

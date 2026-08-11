"""tools/check_agent_docs.py の試験。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from check_agent_docs import check_text, main  # noqa: E402


def test_separate_source_and_operation_is_rejected():
    text = "source scripts/load_env.sh\nmake task-notion TASK=x\n"
    violations = check_text("bad.md", text)
    assert len(violations) == 1
    assert violations[0].line == 1
    assert violations[0].next_line == 2


def test_same_line_source_and_operation_passes():
    text = "    source scripts/load_env.sh && make task-notion TASK=x\n"
    assert check_text("good.md", text) == []


def test_inline_quote_and_standalone_source_are_not_rejected():
    text = (
        "説明では `source scripts/load_env.sh` と書く。\n"
        "\n"
        "    source ~/.zshrc\n"
    )
    assert check_text("notes.md", text) == []


def test_makefile_comment_example_is_checked():
    text = (
        "#   source .venv/bin/activate && source scripts/load_env.sh\n"
        "#   make task-start TASK=x\n"
    )
    assert len(check_text("Makefile", text)) == 1


def test_explicit_empty_targets_fail(capsys):
    assert main(["--path"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail"
    assert payload["targets"] == 0
    assert payload["errors"] == ["検査対象が 0 件"]

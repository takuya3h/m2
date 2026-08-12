"""tools/check_agent_docs.py の試験。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from check_agent_docs import check_pager_text, check_text, main  # noqa: E402


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


def test_fenced_commands_are_checked_across_comments_and_blank_lines():
    text = (
        "```bash\n"
        "source ~/.nvm/nvm.sh\n"
        "\n"
        "# 後続操作\n"
        "node --version\n"
        "```\n"
    )
    violations = check_text("setup.md", text)
    assert len(violations) == 1
    assert violations[0].next_line == 5


def test_explicit_empty_targets_fail(capsys):
    assert main(["--path"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail"
    assert payload["targets"] == 0
    assert payload["errors"] == ["検査対象が 0 件"]


def test_history_read_without_pager_avoidance_is_rejected():
    """頁送りが無いホストで失敗する命令を、文書の側で止める。"""
    violations = check_pager_text("bad.md", "git log -1 --format=%h\n")
    assert len(violations) == 1
    assert violations[0].subcommand == "log"
    assert violations[0].line == 1


def test_history_read_with_pager_avoidance_passes():
    """陰性対照。回避があれば通す。"""
    assert check_pager_text("good.md", "git --no-pager log -1 --format=%h\n") == []


def test_short_pager_avoidance_flag_passes():
    """``-P`` は ``--no-pager`` と同義である。"""
    assert check_pager_text("good.md", "git -P show HEAD\n") == []


def test_non_pager_subcommand_is_not_rejected():
    """頁送りへ流さない下位命令は対象外。**除外しすぎていないことの対。**"""
    assert check_pager_text("good.md", "git status --porcelain\n") == []
    assert check_pager_text("good.md", "git rev-parse HEAD\n") == []


def test_command_substitution_is_not_rejected():
    """置換の内側は端末でないため頁送りへ流れない。誤検出させない。"""
    text = "    BEHIND=$(git log --oneline -1)\n"
    assert check_pager_text("good.md", text) == []


def test_prose_mention_is_not_rejected():
    """散文の中の言及は命令ではない。"""
    text = "説明では `git log` と書く。\n"
    assert check_pager_text("notes.md", text) == []


def test_fenced_history_read_is_checked():
    text = "```bash\ngit diff --cached docs/\n```\n"
    violations = check_pager_text("setup.md", text)
    assert len(violations) == 1
    assert violations[0].subcommand == "diff"


def test_main_reports_pager_violations(tmp_path, capsys):
    doc = tmp_path / "bad.md"
    doc.write_text("git blame README.md\n", encoding="utf-8")
    assert main(["--path", str(doc)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail"
    assert len(payload["pager_violations"]) == 1
    assert payload["violations"] == []

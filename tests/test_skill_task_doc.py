"""手順書 .claude/skills/task/SKILL.md の構造を縛る。

- 始める段（0）が読む段（1）より前にあり、既存の 1〜7 の見出しが変わっていない
- 終える段（8）の状態の一覧が、scripts/task_release.py の状態の一覧と両方向で一致する
- 抑止の目印を手で置く・外す命令は、条件つきの箇所にしか無い

出所: T-2026-10-07-skill-task-start-and-release
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = Path(os.environ.get("SKILL_MD_UNDER_TEST", REPO_ROOT / ".claude" / "skills" / "task" / "SKILL.md"))
TOOL = REPO_ROOT / "scripts" / "task_release.py"

# 既存の段の見出し。過去の報告と文書が番号で参照しているため、付け替えない。
EXISTING_STEPS = [
    "### 1. 読む",
    "### 2. 検証する（L1 + L2）",
    "### 3. 参照を解決する",
    "### 4. L3 プリフライト（実行直前）",
    "### 5. 実行する",
    "### 6. 報告する",
    "### 7. 禁止事項",
]

_MANUAL_MARKER = re.compile(r"(touch|rm -f|mv)\s+\.sync-pause\b|>\s*\.sync-pause\b")


def _lines() -> list[str]:
    return SKILL.read_text(encoding="utf-8").splitlines()


def _section(lines: list[str], heading: str) -> list[str]:
    start = lines.index(heading)
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^#{1,3} ", lines[i])), len(lines))
    return lines[start:end]


def _tool_states() -> set[str]:
    spec = importlib.util.spec_from_file_location("task_release_for_doc", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["task_release_for_doc"] = module
    spec.loader.exec_module(module)
    return set(module.EXIT)


def test_start_step_precedes_read_and_existing_steps_are_unchanged() -> None:
    lines = _lines()
    assert "### 0. 始める" in lines
    assert lines.index("### 0. 始める") < lines.index("### 1. 読む")
    positions = [lines.index(h) for h in EXISTING_STEPS]
    assert positions == sorted(positions)
    assert "### 8. 終える" in lines
    assert lines.index("### 8. 終える") > lines.index("### 7. 禁止事項")


def test_end_step_states_match_the_tool_both_ways() -> None:
    section = _section(_lines(), "### 8. 終える")
    documented = {m.group(1) for line in section if (m := re.match(r"^\| `([A-Z_]+)` \|", line))}
    tool = _tool_states()
    assert documented - tool == set(), "手順書にだけある状態"
    assert tool - documented == set(), "道具にだけある状態"


def test_manual_marker_commands_only_in_conditional_places() -> None:
    heading = ""
    offenders = []
    for number, line in enumerate(_lines(), start=1):
        if re.match(r"^#{2,3} ", line):
            heading = line
        if not _MANUAL_MARKER.search(line):
            continue
        conditional = (
            (heading == "### 5. 実行する" and "task-start を経ない場合だけ" in line)
            or (heading == "### 8. 終える" and re.match(r"^\s+(rm -f|mv) \.sync-pause", line))
        )
        if not conditional:
            offenders.append(f"{number}: {line.strip()}")
    assert offenders == [], offenders

#!/usr/bin/env python3
"""エージェント向け文書のシェル命令が単独で完結することを検査する。"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

DOC_PATTERNS = (
    ".claude/skills/task/SKILL.md",
    "tasks/README.md",
    "CLAUDE.md",
    "Makefile",
    "docs/*.md",
)
PLAIN_COMMAND_PREFIXES = (
    "source ",
    "make ",
    "python ",
    "git ",
    "export ",
    "curl ",
)


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    next_line: int
    command: str
    next_command: str


def discover_documents() -> list[Path]:
    """Task 3 と同じ git ls-files の集合を返す。"""
    proc = subprocess.run(
        ["git", "ls-files", *DOC_PATTERNS],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return []
    return [Path(line) for line in proc.stdout.splitlines() if line]


def _command(line: str, *, in_fence: bool) -> str | None:
    if in_fence:
        command = line.strip()
        return command or None
    if line.startswith("    "):
        return line.strip() or None
    stripped = line.lstrip()
    if stripped.startswith("#   "):
        return stripped[1:].strip() or None
    if line.startswith(PLAIN_COMMAND_PREFIXES):
        return line.strip()
    return None


def _ends_with_source(command: str) -> bool:
    if "source " not in command:
        return False
    tail = command.split("&&")[-1].strip()
    return tail.startswith("source ")


def check_text(path: str, text: str) -> list[Violation]:
    """分離された source と直後の操作を検出する。"""
    lines = text.splitlines()
    in_fence = False
    commands: list[str | None] = []
    fence_states: list[bool] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            commands.append(None)
            fence_states.append(in_fence)
            in_fence = not in_fence
            continue
        commands.append(_command(line, in_fence=in_fence))
        fence_states.append(in_fence)

    violations = []
    for index, command in enumerate(commands[:-1]):
        if command is None or not _ends_with_source(command):
            continue
        next_index = index + 1
        if fence_states[index]:
            while next_index < len(lines):
                if lines[next_index].lstrip().startswith("```"):
                    next_index = len(lines)
                    break
                candidate = commands[next_index]
                if candidate is not None and not candidate.startswith("#"):
                    break
                next_index += 1
        if next_index >= len(lines):
            continue
        next_command = commands[next_index]
        if next_command is None or next_command.startswith("#"):
            continue
        violations.append(
            Violation(
                path=path,
                line=index + 1,
                next_line=next_index + 1,
                command=command,
                next_command=next_command,
            )
        )
    return violations


def check_documents(paths: list[Path]) -> tuple[list[Violation], list[str]]:
    violations = []
    errors = []
    for path in paths:
        if not path.is_file():
            errors.append(f"対象の文書が存在しない: {path}")
            continue
        violations.extend(check_text(str(path), path.read_text(encoding="utf-8")))
    return violations, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        nargs="*",
        help="指定した文書だけを検査する。引数なしの --path は空集合の検査に使う。",
    )
    args = parser.parse_args(argv)

    paths = discover_documents() if args.path is None else [Path(p) for p in args.path]
    violations, errors = check_documents(paths)
    if not paths:
        errors.append("検査対象が 0 件")

    payload = {
        "status": "fail" if violations or errors else "pass",
        "targets": len(paths),
        "violations": [asdict(item) for item in violations],
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if violations or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

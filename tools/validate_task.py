#!/usr/bin/env python3
"""TASK 契約 (tasks/<task_id>/spec.yaml) の検証。

L1: 静的検証（repo 状態に非依存）
L2: 参照解決（runindex に依存）

L3（実行直前）は /task skill 側で行う。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "tasks" / "_schema" / "spec.schema.json"
TASKS_DIR = REPO_ROOT / "tasks"

_NUMBER_RE = re.compile(r"(?<![\w.-])(\d+\.\d+|\d{4,})(?![\w.-])")
_ALLOW_NUMBER_PATHS = {
    "meta.created_at",
    "meta.created_from.runindex_commit",
    "meta.created_from.counts.index",
    "meta.created_from.counts.experiments",
    "meta.created_from.counts.verdicts",
    "contract.conventions_rev",
}
_NUMBER_SCAN_PATHS = ("intent.", "inputs.denominator.", "prereg.")


@dataclass(frozen=True)
class Finding:
    check: str
    path: str
    message: str

    def __str__(self) -> str:
        return f"[{self.check}] {self.path}: {self.message}"


def _walk_strings(node: Any, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_strings(value, f"{prefix}{key}.")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk_strings(value, f"{prefix}{i}.")
    elif isinstance(node, str):
        yield prefix.rstrip("."), node


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_l1(spec: dict, dir_name: str) -> list[Finding]:
    findings: list[Finding] = []

    try:
        from jsonschema import Draft202012Validator
    except ImportError:  # pragma: no cover
        raise SystemExit("jsonschema が必要です: pip install 'jsonschema>=4'")
    validator = Draft202012Validator(_load_schema())
    for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "(root)"
        findings.append(Finding("L1-1", path, err.message))

    task_id = spec.get("meta", {}).get("task_id")
    if task_id != dir_name:
        findings.append(
            Finding("L1-2", "meta.task_id", f"ディレクトリ名 {dir_name} と一致しません")
        )

    for path, value in _walk_strings(spec):
        if "|" in value:
            findings.append(
                Finding("L1-3", path, "半角パイプを含みます。列挙は YAML の配列で書いてください")
            )

    denom = spec.get("inputs", {}).get("denominator")
    if isinstance(denom, dict):
        ref = denom.get("ref", "")
        if not re.fullmatch(r"exp:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", ref):
            findings.append(
                Finding("L1-4", "inputs.denominator.ref", "exp:<group>/<experiment_id> の形式が必要です")
            )
    frozen = spec.get("inputs", {}).get("frozen_source")
    if isinstance(frozen, dict):
        ref = frozen.get("ref", "")
        if not re.fullmatch(r"run:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", ref):
            findings.append(
                Finding("L1-4", "inputs.frozen_source.ref", "run:<group>/<run_name> の形式が必要です")
            )

    if spec.get("contract", {}).get("verbatim_forbidden") is True:
        for path, value in _walk_strings(spec):
            if path in _ALLOW_NUMBER_PATHS or not path.startswith(_NUMBER_SCAN_PATHS):
                continue
            hit = _NUMBER_RE.search(value)
            if hit:
                findings.append(
                    Finding(
                        "L1-5",
                        path,
                        f"数値リテラル {hit.group(0)} が直書きされています。参照で書いてください",
                    )
                )
    return findings


def _iter_task_dirs(only: str | None) -> list[Path]:
    dirs = [d for d in sorted(TASKS_DIR.iterdir()) if d.is_dir() and not d.name.startswith("_")]
    if only:
        dirs = [d for d in dirs if d.name == only]
        if not dirs:
            raise SystemExit(f"task が見つかりません: {only}")
    return dirs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default=None)
    parser.add_argument("--level", choices=["l1", "l2"], default="l2")
    args = parser.parse_args()

    total = 0
    failed = 0
    for task_dir in _iter_task_dirs(args.task):
        spec_path = task_dir / "spec.yaml"
        if not spec_path.exists():
            print(f"SKIP {task_dir.name}: spec.yaml なし")
            continue
        total += 1
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        findings = validate_l1(spec, dir_name=task_dir.name)
        if args.level == "l2" and not findings:
            findings += validate_l2(spec)  # noqa: F821
        if findings:
            failed += 1
            print(f"FAIL {task_dir.name}")
            for finding in findings:
                print(f"  {finding}")
        else:
            print(f"OK   {task_dir.name}")

    print(f"\n{total} task(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

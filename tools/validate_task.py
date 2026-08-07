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
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "tasks" / "_schema" / "spec.schema.json"
TASKS_DIR = REPO_ROOT / "tasks"
EXPERIMENTS_CSV = REPO_ROOT / "runindex" / "experiments.csv"
CONVENTIONS_PATH = REPO_ROOT / "context" / "conventions.md"
COL_EXPERIMENT_ID = "experiment_id"
COL_GROUP = "group"
COL_N_SEEDS = "n_seeds"
COL_SIGMA_SOURCE = "sigma_source"
COL_DELTA_SIGMA_SOURCE = "delta_sigma_source"
_ANCHOR_RE = re.compile(r'<a id="([a-z0-9_]+)"></a>')
_SIGMA_DEFAULT_RE = re.compile(
    r"series:\s*(\w+).*?sigma_source:\s*(\w+).*?delta_sigma_source:\s*(\w+)", re.S
)

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
# 🔴 終端は $ ではなく \Z を使い、照合は fullmatch で行う。
#    Python の $ は**文字列末尾の改行の直前にも一致する**ため、$ と match の組み合わせは
#    改行を含む値を通してしまう（fetch_task.py で実際に悪用可能な欠陥として見つかった形）。
#    ここは内部の経路文字列を見る箇所だが、書き方を検証系全体で揃える。
_PIPE_STRICT_PATHS = (
    re.compile(r"meta\.title\Z"),
    re.compile(r"intent\.(question|decision_at_stake|hypothesis)\Z"),
    re.compile(r"plan\.phases\.\d+\.name\Z"),
    re.compile(r"plan\.gates\.\d+\.check\Z"),
    re.compile(r"outputs\.acceptance\.\d+\Z"),
)
_WARN_CHECKS = {"L1-3W"}


def _is_pipe_strict(path: str) -> bool:
    return any(pattern.fullmatch(path) for pattern in _PIPE_STRICT_PATHS)


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
        if chr(124) not in value:
            continue
        if _is_pipe_strict(path):
            findings.append(
                Finding("L1-3", path, "表へ流れるフィールドに区切り文字を含みます")
            )
        else:
            findings.append(
                Finding("L1-3W", path, "区切り文字を含みます。表へ引用する際は注意してください")
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


def conventions_anchors() -> set[str]:
    if not CONVENTIONS_PATH.exists():
        return set()
    return set(_ANCHOR_RE.findall(CONVENTIONS_PATH.read_text(encoding="utf-8")))


def conventions_sigma_defaults() -> dict[str, str]:
    """conventions.md#sigma の既定値ブロックを読む。"""
    if not CONVENTIONS_PATH.exists():
        return {}
    match = _SIGMA_DEFAULT_RE.search(CONVENTIONS_PATH.read_text(encoding="utf-8"))
    if not match:
        return {}
    return {"series": match.group(1), "sigma_source": match.group(2), "delta_sigma_source": match.group(3)}


def resolve_sigma_policy(spec: dict, defaults: dict[str, str]) -> dict[str, str]:
    """明示指定をconventionsの既定より優先し、完全なdictを返す。"""
    explicit = spec.get("inputs", {}).get("sigma_policy") or {}
    resolved = dict(defaults)
    resolved.update({key: value for key, value in explicit.items() if value is not None})
    return resolved


def _origin_refs() -> list[str]:
    """refs/remotes/origin 配下の ref 名を返す。origin/HEAD は除く。"""
    out = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    ).stdout
    refs = [line.strip() for line in out.splitlines() if line.strip()]
    return [ref for ref in refs if not ref.endswith("/HEAD")]


def task_identity_on_refs(task_id: str) -> dict[str, list[str]]:
    """task_id を含む ref を meta.created_at 別に集める。

    戻り値は created_at をキー、その値を持つ ref のリストを値とする dict。
    ref に spec.yaml が無い場合と、解析できない場合はその ref を無視する。
    """
    spec_path = f"tasks/{task_id}/spec.yaml"
    identities: dict[str, list[str]] = {}
    for ref in _origin_refs():
        shown = subprocess.run(
            ["git", "show", f"{ref}:{spec_path}"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        if shown.returncode != 0:
            continue
        try:
            data = yaml.safe_load(shown.stdout) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        created_at = str(data.get("meta", {}).get("created_at", "") or "")
        if created_at:
            identities.setdefault(created_at, []).append(ref)
    return identities


def task_id_conflicts(task_id: str, identities: dict[str, list[str]]) -> list[str]:
    """同じ task_id が異なる meta.created_at で複数 ref に存在すれば衝突とみなす。

    squash merge や rebase merge で同一 task が複数 ref に現れるのは正常なので、
    created_at が一致する限り衝突としない。
    """
    if len(identities) <= 1:
        return []
    return [
        f"{created_at} <- {', '.join(sorted(refs))}"
        for created_at, refs in sorted(identities.items())
    ]


def _csv_rows(path: Path) -> list[dict[str, str]]:
    import csv
    with path.open(newline="", encoding="utf-8") as file_handle:
        return list(csv.DictReader(file_handle))


def validate_l2(spec: dict) -> list[Finding]:
    findings: list[Finding] = []
    task_id = spec.get("meta", {}).get("task_id", "")
    conflicts = task_id_conflicts(task_id, task_identity_on_refs(task_id))
    if conflicts:
        findings.append(
            Finding(
                "L2-1",
                "meta.task_id",
                "同じ task_id が異なる created_at で複数の ref に存在します: "
                + "; ".join(conflicts),
            )
        )

    anchors = conventions_anchors()
    if not anchors:
        findings.append(Finding("L2-5", "contract.inject_verbatim", "context/conventions.md が読めません"))
    for ref in spec.get("contract", {}).get("inject_verbatim", []):
        anchor = ref.split("#", 1)[1]
        if anchors and anchor not in anchors:
            findings.append(Finding("L2-5", "contract.inject_verbatim", f"アンカー {anchor} が存在しません"))

    for key, paths in (
        ("inputs.data.split_files", spec.get("inputs", {}).get("data", {}).get("split_files", [])),
        ("inputs.code.entrypoints", spec.get("inputs", {}).get("code", {}).get("entrypoints", [])),
        ("inputs.caches", spec.get("inputs", {}).get("caches", []) or []),
    ):
        for path in paths:
            if not (REPO_ROOT / path).exists():
                findings.append(Finding("L2-7", key, f"存在しません: {path}"))

    denominator = spec.get("inputs", {}).get("denominator")
    if denominator and EXPERIMENTS_CSV.exists() and COL_EXPERIMENT_ID != "UNKNOWN":
        rows = _csv_rows(EXPERIMENTS_CSV)
        group, experiment_id = denominator["ref"].split(":", 1)[1].split("/", 1)
        matches = [row for row in rows if row.get(COL_EXPERIMENT_ID) == experiment_id and row.get(COL_GROUP) == group]
        if not matches:
            findings.append(Finding("L2-2", "inputs.denominator.ref", f"experiments.csv に {group}/{experiment_id} がありません"))
        else:
            row = matches[0]
            needed = denominator.get("require", {}).get("n_seeds")
            if needed and COL_N_SEEDS != "UNKNOWN":
                try:
                    actual = int(float(row.get(COL_N_SEEDS, "0") or 0))
                except ValueError:
                    actual = 0
                bound = int(needed.lstrip(">=< "))
                if actual < bound:
                    findings.append(Finding("L2-3", "inputs.denominator.require.n_seeds", f"実測 {actual} が要求 {needed} を満たしません"))
            resolved = resolve_sigma_policy(spec, conventions_sigma_defaults())
            for policy_key, column in (("sigma_source", COL_SIGMA_SOURCE), ("delta_sigma_source", COL_DELTA_SIGMA_SOURCE)):
                actual_value = row.get(column)
                resolved_value = resolved.get(policy_key)
                if actual_value and resolved_value and actual_value != resolved_value:
                    findings.append(Finding("L2-4", f"inputs.sigma_policy.{policy_key}", f"分母の実値 {actual_value} と解決値 {resolved_value} が不一致"))
    _warn_conventions_rev(spec)
    _warn_population_drift(spec)
    return findings


def _warn_conventions_rev(spec: dict) -> None:
    revision = spec.get("contract", {}).get("conventions_rev")
    if not revision:
        return
    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{revision}..HEAD", "--", "context/conventions.md"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    ).stdout.strip()
    if changed:
        print(f"WARN [L2-6] conventions.md が {revision} 以降に変更されています。差分を確認してください", file=sys.stderr)


def _warn_population_drift(spec: dict) -> None:
    counts = spec.get("meta", {}).get("created_from", {}).get("counts", {})
    for name, key in (("index.csv", "index"), ("experiments.csv", "experiments"), ("verdicts.csv", "verdicts")):
        path = REPO_ROOT / "runindex" / name
        if not path.exists():
            continue
        actual = sum(1 for _ in path.open(encoding="utf-8")) - 1
        expected = counts.get(key)
        if expected is not None and actual != expected:
            print(f"WARN [L2-8] {name}: 起票時 {expected} → 現在 {actual}（分母が動いています）", file=sys.stderr)


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
        if args.level == "l2" and not [f for f in findings if f.check not in _WARN_CHECKS]:
            findings += validate_l2(spec)
        hard = [f for f in findings if f.check not in _WARN_CHECKS]
        warn = [f for f in findings if f.check in _WARN_CHECKS]
        for f in warn:
            print(f"WARN {task_dir.name}: {f}", file=sys.stderr)
        if hard:
            failed += 1
            print(f"FAIL {task_dir.name}")
            for f in hard:
                print(f"  {f}")
        else:
            print(f"OK   {task_dir.name}")

    print(f"\n{total} task(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

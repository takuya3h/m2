#!/usr/bin/env python3
"""TASK 契約の実行直前検査。

L1 と L2 は tools/validate_task.py が担う。ここは実行環境に依存する検査のみを行う。
出力は実装系をまたいで比較できるよう、固定書式とする。

この検査器を `.venv/bin/python` で起動してはならない。activate していなくても
sys.prefix が一致して P1 が通ってしまう（実測済み）。PATH 上の python で起動し、
現在の環境をそのまま検査対象にすること。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "tasks"
CONVENTIONS_PATH = REPO_ROOT / "context" / "conventions.md"
STATUSES = ("PASS", "SKIP", "FAIL")

CHECK_NAMES = {
    "P1": "venv_active",
    "P2": "cuda_ext_loaded",
    "P3": "deterministic_flags",
    "P4": "prereg_committed",
    "P5": "frozen_source_hash",
    "P6": "decisions_answered",
    "P7": "destination_writable",
    "P8": "contract_valid",
}
ALWAYS = {"P1", "P6", "P7", "P8"}
EXP_ONLY = {"P4", "P5"}
LISTED_ONLY = {"P2": "cuda_ext_loaded", "P3": "deterministic_flags"}

# 検出系の CUDA 拡張は トップレベル module ではない。実測（Task 1 Step 3）で確認した
# 唯一の import 経路は scripts/run_hc_seeds_lecun.sh の warmup と同じ次の手順。
#   sys.path.insert(0, "third_party/Relation-DETR"); os.chdir(...); import models.bricks.relation_transformer
# chdir を伴うため検査器本体では行わず、必ず子プロセスで実行する。
CUDA_EXT_DIR = "third_party/Relation-DETR"
CUDA_EXT_MODULE = "models.bricks.relation_transformer"
CUDA_EXT_TIMEOUT_SEC = 600

# P3 の判定基準が実測で定まらなかった理由（Task 1 Step 4）。
# seed_everything() は cudnn.deterministic / benchmark / PYTHONHASHSEED を
# **実行プロセス内で**設定するため、別プロセスである検査器からは観測できない。
# use_deterministic_algorithms と CUBLAS_WORKSPACE_CONFIG はコードにも環境にも無く、
# 何をもって合格とするかは backlog B-20 が未解決のまま残している。
P3_UNKNOWN_REASON = (
    "UNKNOWN 判定基準が未確定。決定性設定は実行プロセス内で行われ外部から観測できない。backlog B-20 が未解決"
)


@dataclass(frozen=True)
class Check:
    check_id: str
    name: str
    status: str
    detail: str


def decide_applicability(spec: dict) -> dict[str, bool]:
    """各検査を実行するかどうかを契約から決める。環境には触らない純関数。"""
    kind = spec.get("meta", {}).get("kind", "")
    listed = set(spec.get("plan", {}).get("env", {}).get("preflight", []) or [])
    applicable: dict[str, bool] = {}
    for cid in CHECK_NAMES:
        if cid in ALWAYS:
            applicable[cid] = True
        elif cid in EXP_ONLY:
            applicable[cid] = kind == "exp"
        else:
            applicable[cid] = LISTED_ONLY[cid] in listed
    return applicable


def summarize(checks: list[Check]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for check in checks:
        counts[check.status] += 1
    return counts


def format_report(checks: list[Check]) -> str:
    lines = [
        f"{c.check_id} {c.name:<22} {c.status:<4} {c.detail}".rstrip() for c in checks
    ]
    counts = summarize(checks)
    lines.append("")
    lines.append(
        f"RESULT: {counts['PASS']} PASS / {counts['SKIP']} SKIP / {counts['FAIL']} FAIL"
    )
    return "\n".join(lines)


def _frozen_source_from_conventions() -> tuple[str | None, str | None]:
    """conventions.md の frozen_source 節から (正本 SHA-256, ckpt パス) を読む。

    節の切り出しは `<a id="frozen_source"></a>` から次の `<a id=` まで。
    """
    if not CONVENTIONS_PATH.exists():
        return None, None
    text = CONVENTIONS_PATH.read_text(encoding="utf-8")
    match = re.search(r'<a id="frozen_source"></a>(.*?)(?=<a id="|\Z)', text, re.S)
    if not match:
        return None, None
    section = match.group(1)
    sha_match = re.search(r"\b([0-9a-f]{64})\b", section)
    path_match = re.search(r"`([^`]*\.pth)`", section)
    return (
        sha_match.group(1) if sha_match else None,
        path_match.group(1) if path_match else None,
    )


def check_venv(spec: dict) -> Check:
    """P1. $VIRTUAL_ENV と sys.prefix の両方を見て、片方でも一致すれば PASS。

    実測（Task 1 Step 2）: activate せず .venv/bin/python を直叩きすると
    VIRTUAL_ENV は空だが sys.prefix は一致する。逆に activate 済みなら両方一致する。
    片方でも一致すれば PASS とするのは安全側の判断である。
    """
    declared = spec.get("plan", {}).get("env", {}).get("venv", "")
    if not declared:
        return Check("P1", CHECK_NAMES["P1"], "SKIP", "契約に plan.env.venv の記載なし")
    expected = (REPO_ROOT / declared).resolve()
    env_venv = os.environ.get("VIRTUAL_ENV", "")
    env_match = bool(env_venv) and Path(env_venv).resolve() == expected
    prefix_match = Path(sys.prefix).resolve() == expected
    detail = f"expected={expected} VIRTUAL_ENV={env_venv or '(未設定)'} sys.prefix={sys.prefix}"
    if env_match or prefix_match:
        return Check("P1", CHECK_NAMES["P1"], "PASS", detail)
    return Check("P1", CHECK_NAMES["P1"], "FAIL", detail)


def check_cuda_ext() -> Check:
    """P2. 拡張を実 import して成功するかを子プロセスで確かめる。

    chdir と JIT ビルドを伴うため検査器本体では実行しない。
    import できなければ FAIL とする（無言で CPU へ落ちる事故を防ぐのが目的であり、
    読み込めない環境で実行を許すと目的を達しない）。
    """
    ext_dir = REPO_ROOT / CUDA_EXT_DIR
    code = (
        f"import sys, os; sys.path.insert(0, {str(ext_dir)!r}); "
        f"os.chdir({str(ext_dir)!r}); import {CUDA_EXT_MODULE}; print('ok')"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=CUDA_EXT_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return Check(
            "P2",
            CHECK_NAMES["P2"],
            "FAIL",
            f"{CUDA_EXT_MODULE} の import が {CUDA_EXT_TIMEOUT_SEC}s でタイムアウト",
        )
    if proc.returncode == 0:
        return Check("P2", CHECK_NAMES["P2"], "PASS", f"{CUDA_EXT_MODULE} を import できた")
    last = (proc.stderr or "").strip().splitlines()
    reason = last[-1] if last else f"exit={proc.returncode}"
    return Check("P2", CHECK_NAMES["P2"], "FAIL", f"{CUDA_EXT_MODULE} を import できない: {reason}")


def check_deterministic_flags() -> Check:
    """P3. 判定基準が実測で定まらないため常に SKIP とする。理由を明示する。"""
    return Check("P3", CHECK_NAMES["P3"], "SKIP", P3_UNKNOWN_REASON)


def check_prereg(spec: dict) -> Check:
    """P4. prereg.commit が存在し、その commit 時刻が現在より前であることを確かめる。"""
    commit = (spec.get("prereg") or {}).get("commit")
    if not commit:
        return Check("P4", CHECK_NAMES["P4"], "FAIL", "prereg.commit が未記入")
    proc = subprocess.run(
        ["git", "show", "-s", "--format=%cI", str(commit)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return Check("P4", CHECK_NAMES["P4"], "FAIL", f"commit {commit} が存在しない")
    stamp = proc.stdout.strip()
    try:
        committed_at = datetime.fromisoformat(stamp)
    except ValueError:
        return Check("P4", CHECK_NAMES["P4"], "FAIL", f"commit 時刻を解釈できない: {stamp}")
    if committed_at > datetime.now(timezone.utc):
        return Check("P4", CHECK_NAMES["P4"], "FAIL", f"commit 時刻が未来: {stamp}")
    return Check("P4", CHECK_NAMES["P4"], "PASS", f"{commit} committed_at={stamp}")


def check_frozen_source() -> Check:
    """P5. ckpt の SHA-256 が conventions の正本と一致することを確かめる。

    conventions#frozen_source は「skip する経路は設けない」と定めている。
    したがってこの検査が適用される限り、読めない・一致しないは全て FAIL とする。
    """
    expected_sha, rel_path = _frozen_source_from_conventions()
    if not expected_sha or not rel_path:
        return Check(
            "P5", CHECK_NAMES["P5"], "FAIL", "conventions.md の frozen_source 節から正本を読めない"
        )
    ckpt = REPO_ROOT / rel_path
    if not ckpt.exists():
        return Check("P5", CHECK_NAMES["P5"], "FAIL", f"凍結源が存在しない: {rel_path}")
    digest = hashlib.sha256()
    with ckpt.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual == expected_sha:
        return Check("P5", CHECK_NAMES["P5"], "PASS", f"{rel_path} sha256={actual}")
    return Check(
        "P5",
        CHECK_NAMES["P5"],
        "FAIL",
        f"{rel_path} sha256 が不一致 expected={expected_sha} actual={actual}",
    )


def check_decisions(spec: dict) -> Check:
    """P6. governance.decisions_required が空であることを確かめる。

    非空なら FAIL とし、項目をそのまま detail に出す（人へ提示するため）。
    """
    pending = spec.get("governance", {}).get("decisions_required") or []
    if not pending:
        return Check("P6", CHECK_NAMES["P6"], "PASS", "decisions_required は空")
    items = "; ".join(str(item) for item in pending)
    return Check("P6", CHECK_NAMES["P6"], "FAIL", f"未回答 {len(pending)} 件: {items}")


def _probe_writable(directory: Path) -> str | None:
    """実際に書いて消せるかを確かめる。駄目な場合だけ理由を返す。"""
    try:
        handle, name = tempfile.mkstemp(dir=directory, prefix=".preflight_probe_")
        os.close(handle)
        probe = Path(name)
        probe.unlink()
        if probe.exists():
            return "probe を削除できない"
    except OSError as exc:
        return str(exc)
    return None


def check_destination(spec: dict) -> Check:
    """P7. outputs.destination へ書き込めることを確かめる。

    出力先がまだ存在しない場合もある。新しい出力領域を作る契約では、
    destination はその契約自身の成果物であり実行前には存在しない。
    存在しないことだけを理由に FAIL とすると、そうした契約すべてで偽陽性になる。
    そこで**最も近い既存の祖先**へ probe し、作成できるかどうかで判定する。
    **検査が実体を作ってはならない**（実行前検査は環境を変えない）。
    """
    dest_rel = spec.get("outputs", {}).get("destination", "")
    if not dest_rel:
        return Check("P7", CHECK_NAMES["P7"], "SKIP", "契約に outputs.destination の記載なし")
    dest = REPO_ROOT / dest_rel

    if dest.is_dir():
        reason = _probe_writable(dest)
        if reason:
            return Check("P7", CHECK_NAMES["P7"], "FAIL", f"{dest_rel} へ書き込めない: {reason}")
        return Check("P7", CHECK_NAMES["P7"], "PASS", f"{dest_rel} へ書き込みと削除ができた")

    if dest.exists():
        return Check("P7", CHECK_NAMES["P7"], "FAIL", f"ディレクトリではありません: {dest_rel}")

    ancestor = dest.parent
    while not ancestor.is_dir() and ancestor != ancestor.parent:
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        return Check("P7", CHECK_NAMES["P7"], "FAIL", f"既存の親が見つかりません: {dest_rel}")
    reason = _probe_writable(ancestor)
    if reason:
        return Check(
            "P7",
            CHECK_NAMES["P7"],
            "FAIL",
            f"{dest_rel} を作成できない（{ancestor.relative_to(REPO_ROOT)} へ書き込めない: {reason}）",
        )
    return Check(
        "P7",
        CHECK_NAMES["P7"],
        "PASS",
        f"{dest_rel} は未作成だが作成可能（{ancestor.relative_to(REPO_ROOT)} へ書き込みと削除ができた）",
    )


def check_contract(task_id: str) -> Check:
    """P8. L1 と L2 を validate_task.py へ委譲する。判定を複製しない。"""
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "validate_task.py"),
         "--task", task_id, "--level", "l2"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return Check("P8", CHECK_NAMES["P8"], "PASS", "validate_task.py --level l2 が exit 0")
    return Check(
        "P8",
        CHECK_NAMES["P8"],
        "FAIL",
        f"validate_task.py が exit {proc.returncode}",
    )


def run_checks(task_id: str, spec: dict) -> list[Check]:
    applicable = decide_applicability(spec)
    checks: list[Check] = []
    for cid in sorted(CHECK_NAMES):
        if not applicable[cid]:
            checks.append(Check(cid, CHECK_NAMES[cid], "SKIP", _skip_reason(cid, spec)))
            continue
        if cid == "P1":
            checks.append(check_venv(spec))
        elif cid == "P2":
            checks.append(check_cuda_ext())
        elif cid == "P3":
            checks.append(check_deterministic_flags())
        elif cid == "P4":
            checks.append(check_prereg(spec))
        elif cid == "P5":
            checks.append(check_frozen_source())
        elif cid == "P6":
            checks.append(check_decisions(spec))
        elif cid == "P7":
            checks.append(check_destination(spec))
        elif cid == "P8":
            checks.append(check_contract(task_id))
    return checks


def _skip_reason(check_id: str, spec: dict) -> str:
    if check_id in EXP_ONLY:
        kind = spec.get("meta", {}).get("kind", "")
        return f"kind={kind} のため対象外（exp のみ）"
    if check_id in LISTED_ONLY:
        return f"plan.env.preflight に {LISTED_ONLY[check_id]} の記載なし"
    return "対象外"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="検査する task_id")
    args = parser.parse_args()

    spec_path = TASKS_DIR / args.task / "spec.yaml"
    if not spec_path.exists():
        print(f"spec.yaml が見つかりません: {spec_path}", file=sys.stderr)
        return 1
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}

    checks = run_checks(args.task, spec)
    print(format_report(checks))
    return 1 if summarize(checks)["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

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
# P14 が tools/check_proposal.py を使う。**起動の仕方に依らず解決できるようにする。**
_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
CONVENTIONS_PATH = REPO_ROOT / "context" / "conventions.md"
# WARN は「合格でも失敗でもない」第 4 の状態である。SKIP と PASS を区別しているのと
# 同じ理由で、警告と合格も区別する。**WARN は終了コードを変えない**（判定は FAIL の数のみ）。
STATUSES = ("PASS", "WARN", "SKIP", "FAIL")

CHECK_NAMES = {
    "P1": "venv_active",
    "P2": "cuda_ext_loaded",
    "P3": "deterministic_flags",
    "P4": "prereg_committed",
    "P5": "frozen_source_hash",
    "P6": "decisions_answered",
    "P7": "destination_writable",
    "P8": "contract_valid",
    "P9": "spec_lint",
    "P10": "preflight_names_known",
    "P11": "gpu_free",
    "P12": "refs_resolved",
    "P13": "symmetry_table_complete",
    "P14": "proposal_card_checked",
}
ALWAYS = {"P1", "P6", "P7", "P8", "P9", "P10", "P12"}
EXP_ONLY = {"P4", "P5", "P13", "P14"}
LISTED_ONLY = {
    "P2": "cuda_ext_loaded",
    "P3": "deterministic_flags",
    "P11": "gpu_free",
}

# plan.env.preflight に書いてよい名前。**schema の enum と同じ集合でなければならない。**
# 片方だけを増やすと、一方が通して他方が落とす食い違いが起きる。整合は試験で縛る。
KNOWN_PREFLIGHT_NAMES = frozenset({"venv_active", *LISTED_ONLY.values()})

# 実行者が索引で解決する前提の参照の書き方。**取り込みでは落とさず、実行直前で止める。**
UNRESOLVED_PREFIX = "unresolved:"
RESOLVED_FILE = "resolved.yaml"

# P13 symmetry_table_complete。conventions#symmetry が定めた対称性の表を prereg から探す。
# **表の同定は列名の完全一致で行う。** 部分一致にすると「判定規約」「条件の理由」のような
# 別の表を拾い、無関係な表で合否が決まる（issuer_cautions #13 と同型）。
PREREG_FILE = "prereg.md"
# **完了済みの契約は P13 の対象外とする**（利用者の決定 2026-09-19）。関門はこれから
# 起票する契約に効かせるものであり、過去の契約の再現や追試を妨げる意図は無い。
# 判定は `result.yaml` の実在と verdict の有無**だけ**で行う。名前の部分一致・日付・
# 台帳は使わない。部分一致は無関係な契約を完了済みと誤認する（issuer_cautions #13 と同型）。
# **`verdict` は最上位の項目ではない。** 様式が持つのは `gates[].verdict` であり、
# 最上位は `status` である（result.schema.json を実測して確かめた）。
RESULT_FILE = "result.yaml"
SYMMETRY_CONDITION_HEADER = "条件"
SYMMETRY_VERDICT_HEADER = "判定"
SYMMETRY_REASON_HEADER = "理由"
SYMMETRY_ARM_RE = re.compile(r"^腕\d+$")
SYMMETRY_MIN_ARMS = 2
SYMMETRY_ALIGN = "揃える"
SYMMETRY_INTENDED = "意図的に変える"
SYMMETRY_UNKNOWN = "UNKNOWN"
SYMMETRY_VERDICTS = (SYMMETRY_ALIGN, SYMMETRY_INTENDED, SYMMETRY_UNKNOWN)

# P14 proposal_card_checked。conventions#proposal_gate の「置き場と参照」が定めた
# 提案カードを spec から辿り、実在と静的検査の通過を確かめる。
# **関門は在ったのに使われなかった。** 規約・手順・検査器は 2026-09-16 から在ったが、
# Stage 1 の二周目と三周目はカードを repo に置かず prereg を直接書いた。関門を作った
# 起票者自身が飛ばした。**文言による自制は働かないので機械にする**（docs/issuer-defects.md）。
PROPOSAL_CARD_FIELD = "proposal_card"
# 導入前に配布済みの契約。**照合は task_id の完全一致で行う。**
# 部分一致にすると `-r2` を含む別の契約や後続の周回まで免除する
# （issuer_cautions #13 と同型。P13 の完了済み判定と同じ理由）。
# **三件目を足すときは規約の改訂が要る**（conventions#proposal_gate「置き場と参照」）。
PRE_GATE_EXEMPT_TASKS = frozenset({
    "T-2026-09-19-stage1-detector-towers-r2",
    "T-2026-09-19-stage1-phase-tower-r3",
})
PRE_GATE_EXEMPT_REASON = "導入前の契約"

# P11 gpu_free。**空きの判定は「compute プロセスが 0 件」で行う。**
# 使用量の閾値は機種と用途で変わるため置かない。占有しているプロセスの有無だけを見る。
NVIDIA_SMI_TIMEOUT_SEC = 30

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
        f"RESULT: {counts['PASS']} PASS / {counts['WARN']} WARN / "
        f"{counts['SKIP']} SKIP / {counts['FAIL']} FAIL"
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


def check_spec_lint(task_id: str) -> Check:
    """P9. 層 1 の検査を実行直前でも回す（二重の網）。

    **失敗させない。警告として出す。** 起票者が層 1 を回し忘れた分をここで拾う。
    判定は `tools/check_spec.py` へ委譲する。**規則をここに複製しない。**

    該当があっても終了コードは変わらない。契約の誤りは実行者の責任ではなく、
    実行を止める根拠にもならない。**気付かせることだけが目的である。**
    """
    tools_dir = str(REPO_ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import check_spec
    except ImportError as exc:  # pragma: no cover - 実装が欠けた場合のみ
        return Check("P9", CHECK_NAMES["P9"], "SKIP", f"check_spec.py を読み込めない: {exc}")

    payload = check_spec.check([check_spec.load_contract(task_id)])
    if payload["errors"]:
        return Check("P9", CHECK_NAMES["P9"], "SKIP", "; ".join(payload["errors"]))
    if not payload["findings"]:
        return Check(
            "P9",
            CHECK_NAMES["P9"],
            "PASS",
            f"規則 {payload['rules_checked']} 件を検査し該当なし",
        )
    where = ", ".join(
        f"{f['rule']}@{f['file']}:{f['line']}" for f in payload["findings"][:5]
    )
    more = "" if len(payload["findings"]) <= 5 else f" ほか {len(payload['findings']) - 5} 件"
    return Check(
        "P9",
        CHECK_NAMES["P9"],
        "WARN",
        f"規則 {payload['rules_checked']} 件のうち {payload['hits']} 件が該当: {where}{more}"
        "（終了コードは変わらない）",
    )


def unknown_preflight_names(spec: dict) -> list[str]:
    """契約が書いた preflight の名前のうち、検査器が実装していないものを返す。"""
    listed = (spec.get("plan", {}).get("env", {}) or {}).get("preflight") or []
    return [str(n) for n in listed if str(n) not in KNOWN_PREFLIGHT_NAMES]


def check_preflight_names(spec: dict) -> Check:
    """P10. 未知の名前を **FAIL** にする。

    以前は未知の名前が黙って無視され、契約が宣言した検査が一つも動かないまま
    PASS になっていた（実測: `gpu_free` が 1 契約で無視されていた）。
    **黙って通すより落ちるほうがよい。**
    """
    unknown = unknown_preflight_names(spec)
    known = ", ".join(sorted(KNOWN_PREFLIGHT_NAMES))
    if not unknown:
        listed = (spec.get("plan", {}).get("env", {}) or {}).get("preflight") or []
        return Check("P10", CHECK_NAMES["P10"], "PASS",
                     f"宣言 {len(listed)} 件はすべて実装済み（既知: {known}）")
    return Check("P10", CHECK_NAMES["P10"], "FAIL",
                 f"実装されていない名前: {', '.join(unknown)}（既知: {known}）")


def check_gpu_free() -> Check:
    """P11. GPU を占有している compute プロセスが無いことを確かめる。

    使用量の閾値は置かない。**占有しているプロセスの有無だけを見る。**
    観測できない場合は FAIL とする。契約が「空いていること」を前提に宣言した以上、
    確かめられないまま実行を許すと宣言の意味が無い。
    """
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader"],
            capture_output=True, text=True, check=False, timeout=NVIDIA_SMI_TIMEOUT_SEC,
        )
    except FileNotFoundError:
        return Check("P11", CHECK_NAMES["P11"], "FAIL", "nvidia-smi が無く GPU の空きを観測できない")
    except subprocess.TimeoutExpired:
        return Check("P11", CHECK_NAMES["P11"], "FAIL",
                     f"nvidia-smi が {NVIDIA_SMI_TIMEOUT_SEC}s でタイムアウト")
    if proc.returncode != 0:
        reason = (proc.stderr or "").strip().splitlines()
        return Check("P11", CHECK_NAMES["P11"], "FAIL",
                     f"nvidia-smi が失敗: {reason[-1] if reason else proc.returncode}")
    busy = [line for line in proc.stdout.splitlines() if line.strip()]
    if busy:
        return Check("P11", CHECK_NAMES["P11"], "FAIL",
                     f"GPU を占有する compute プロセスが {len(busy)} 件: {'; '.join(busy)}")
    return Check("P11", CHECK_NAMES["P11"], "PASS", "GPU を占有する compute プロセスは 0 件")


def unresolved_refs(spec: dict) -> list[str]:
    """`unresolved:` で始まる参照の位置を返す（`inputs.denominator.ref` のような点区切り）。"""
    found: list[str] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}.{i}")
        elif isinstance(node, str) and node.startswith(UNRESOLVED_PREFIX):
            found.append(path)

    walk(spec, "")
    return sorted(found)


def check_refs_resolved(task_id: str, spec: dict) -> Check:
    """P12. 実行者が解決する前提の参照が、実行前に解決済みであることを確かめる。

    起票者は `unresolved:<何を索引で引くか>` と書いて契約を設置できる（取り込みで
    落ちない）。実行者は `tasks/<task_id>/resolved.yaml` に解決結果を書く。
    **解決が済んでいなければここで止まる。**
    """
    pending = unresolved_refs(spec)
    if not pending:
        return Check("P12", CHECK_NAMES["P12"], "SKIP", "解決前提の参照は無い")

    path = TASKS_DIR / task_id / RESOLVED_FILE
    if not path.exists():
        return Check("P12", CHECK_NAMES["P12"], "FAIL",
                     f"解決前提の参照 {len(pending)} 件（{', '.join(pending)}）に対し {RESOLVED_FILE} が無い")
    try:
        resolved = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return Check("P12", CHECK_NAMES["P12"], "FAIL", f"{RESOLVED_FILE} を読めない: {exc}")
    if not isinstance(resolved, dict):
        return Check("P12", CHECK_NAMES["P12"], "FAIL", f"{RESOLVED_FILE} が対応表ではない")

    missing = [
        key for key in pending
        if not str(((resolved.get(key) or {}) if isinstance(resolved.get(key), dict)
                    else {}).get("resolved_to") or "").strip()
    ]
    if missing:
        return Check("P12", CHECK_NAMES["P12"], "FAIL",
                     f"{RESOLVED_FILE} に resolved_to が無い: {', '.join(missing)}")
    still = [key for key in pending
             if str(resolved[key]["resolved_to"]).startswith(UNRESOLVED_PREFIX)]
    if still:
        return Check("P12", CHECK_NAMES["P12"], "FAIL",
                     f"解決先がまだ未解決のまま: {', '.join(still)}")
    return Check("P12", CHECK_NAMES["P12"], "PASS",
                 f"解決前提の参照 {len(pending)} 件がすべて {RESOLVED_FILE} で解決済み")


def _table_cells(line: str) -> list[str]:
    """markdown の表の行をセルへ割る。両端の縦線と強調の印は落とす。"""
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [cell.strip().strip("*").strip() for cell in inner.split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:|-]+\|?", line.strip())) and "-" in line


def symmetry_tables(text: str) -> list[tuple[dict[str, int], list[list[str]]]]:
    """対称性の表を全て返す。列名の**完全一致**で同定する。

    Returns:
        (列名 -> 添字, 本体の行) の一覧。様式に合う表が無ければ空。
    """
    lines = text.split("\n")
    tables: list[tuple[dict[str, int], list[list[str]]]] = []
    i = 0
    while i < len(lines) - 1:
        if not lines[i].strip().startswith("|") or not _is_separator(lines[i + 1]):
            i += 1
            continue
        header = _table_cells(lines[i])
        body: list[list[str]] = []
        j = i + 2
        while j < len(lines) and lines[j].strip().startswith("|"):
            body.append(_table_cells(lines[j]))
            j += 1
        arms = sum(1 for cell in header if SYMMETRY_ARM_RE.fullmatch(cell))
        matched = (
            header
            and header[0] == SYMMETRY_CONDITION_HEADER
            and SYMMETRY_VERDICT_HEADER in header
            and SYMMETRY_REASON_HEADER in header
            and arms >= SYMMETRY_MIN_ARMS
        )
        if matched:
            index = {
                SYMMETRY_CONDITION_HEADER: 0,
                SYMMETRY_VERDICT_HEADER: header.index(SYMMETRY_VERDICT_HEADER),
                SYMMETRY_REASON_HEADER: header.index(SYMMETRY_REASON_HEADER),
            }
            tables.append((index, body))
        i = j if body else i + 1
    return tables


def completed_verdicts(task_id: str) -> list[str]:
    """完了済みの印を返す。`result.yaml` の `gates[].verdict` のうち空でない値。

    読めない・様式に合わない場合は空を返して「完了済みでない」と扱う。
    **推測で補わない。** 印が無いなら未完了として従来どおり検査する。
    """
    path = TASKS_DIR / task_id / RESULT_FILE
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    if not isinstance(data, dict):
        return []
    gates = data.get("gates")
    if not isinstance(gates, list):
        return []
    return [
        str(gate["verdict"]).strip()
        for gate in gates
        if isinstance(gate, dict) and str(gate.get("verdict") or "").strip()
    ]


def check_symmetry_table(task_id: str) -> Check:
    """P13. prereg の対称性の表が埋まっていることを確かめる。

    正本は `conventions#symmetry`。表が無い、UNKNOWN が残る、
    「意図的に変える」に理由が無い、判定が三値のいずれでもない、のいずれも FAIL とする。
    **判定の空欄を通さない。** 空欄を許すと、埋めないまま起票できてしまう。

    **完了済みの契約は SKIP とする。** 判定は `completed_verdicts` だけに委ねる。
    """
    verdicts = completed_verdicts(task_id)
    if verdicts:
        return Check(
            "P13", CHECK_NAMES["P13"], "SKIP",
            f"完了済み（{RESULT_FILE} に verdict あり: {len(verdicts)} 件）のため対象外",
        )
    path = TASKS_DIR / task_id / PREREG_FILE
    if not path.exists():
        return Check("P13", CHECK_NAMES["P13"], "FAIL", f"{PREREG_FILE} が無い")
    tables = symmetry_tables(path.read_text(encoding="utf-8"))
    if not tables:
        return Check(
            "P13", CHECK_NAMES["P13"], "FAIL",
            f"{PREREG_FILE} に conventions#symmetry の対称性の表が無い"
            f"（列名 {SYMMETRY_CONDITION_HEADER}／腕1／腕2／"
            f"{SYMMETRY_VERDICT_HEADER}／{SYMMETRY_REASON_HEADER} で探す）",
        )
    rows = sum(len(body) for _, body in tables)
    if not rows:
        return Check("P13", CHECK_NAMES["P13"], "FAIL", "対称性の表に行が無い")

    unknown: list[str] = []
    no_reason: list[str] = []
    bad_verdict: list[str] = []
    for index, body in tables:
        for cells in body:
            if len(cells) <= max(index.values()):
                bad_verdict.append(f"{cells[0] if cells else '(空行)'}（列が足りない）")
                continue
            condition = cells[index[SYMMETRY_CONDITION_HEADER]] or "(条件が空)"
            verdict = cells[index[SYMMETRY_VERDICT_HEADER]]
            reason = cells[index[SYMMETRY_REASON_HEADER]]
            if verdict == SYMMETRY_UNKNOWN:
                unknown.append(condition)
            elif verdict == SYMMETRY_INTENDED and not reason:
                no_reason.append(condition)
            elif verdict not in SYMMETRY_VERDICTS:
                bad_verdict.append(f"{condition}（判定が「{verdict or '空欄'}」）")

    problems: list[str] = []
    if unknown:
        problems.append(f"UNKNOWN {len(unknown)} 行: {', '.join(unknown)}")
    if no_reason:
        problems.append(f"「{SYMMETRY_INTENDED}」に理由が無い {len(no_reason)} 行: {', '.join(no_reason)}")
    if bad_verdict:
        problems.append(f"判定が三値でない {len(bad_verdict)} 行: {', '.join(bad_verdict)}")
    if problems:
        return Check("P13", CHECK_NAMES["P13"], "FAIL", f"{rows} 行を検査。" + "／".join(problems))
    return Check(
        "P13", CHECK_NAMES["P13"], "PASS",
        f"対称性の表 {len(tables)} 個 / {rows} 行に UNKNOWN と理由欠落は無い",
    )


def check_proposal_card(task_id: str, spec: dict) -> Check:
    """P14. exp 契約が、検査を通った提案カードを参照していることを確かめる。

    正本は `conventions#proposal_gate` の「置き場と参照」。判定は次の順で行う。

    1. 完了済み（`result.yaml` に `gates[].verdict` がある）→ SKIP。P13 と同じ判定に委ねる
    2. 導入前に配布済みの契約（`PRE_GATE_EXEMPT_TASKS` の完全一致）→ SKIP
    3. `intent.proposal_card` が無い → FAIL
    4. 経路のファイルが無い → FAIL
    5. `check_proposal.py` に検出がある → FAIL（検出の内容を出す）

    **カードの中身の妥当性は見ない。** 形の検査は `check_proposal.py` に委ね、
    価値の判断は批判会話が持つ（`docs/proposal-gate.md` B.6）。
    """
    verdicts = completed_verdicts(task_id)
    if verdicts:
        return Check(
            "P14", CHECK_NAMES["P14"], "SKIP",
            f"完了済み（{RESULT_FILE} に verdict あり: {len(verdicts)} 件）のため対象外",
        )
    if task_id in PRE_GATE_EXEMPT_TASKS:
        return Check(
            "P14", CHECK_NAMES["P14"], "SKIP",
            f"{PRE_GATE_EXEMPT_REASON}のため対象外（conventions#proposal_gate の置き場と参照）",
        )

    card = (spec.get("intent") or {}).get(PROPOSAL_CARD_FIELD)
    if not isinstance(card, str) or not card.strip():
        return Check(
            "P14", CHECK_NAMES["P14"], "FAIL",
            f"intent.{PROPOSAL_CARD_FIELD} が無い。"
            "提案カードを docs/proposals/ に置き、経路を書くこと",
        )
    card = card.strip()
    path = REPO_ROOT / card
    if not path.is_file():
        return Check("P14", CHECK_NAMES["P14"], "FAIL", f"提案カードが無い: {card}")

    try:
        import check_proposal
    except ImportError as exc:  # pragma: no cover - 検査器の欠落を隠さない
        return Check("P14", CHECK_NAMES["P14"], "FAIL", f"check_proposal を読めない: {exc}")
    report = check_proposal.check(path)
    if report["errors"]:
        return Check(
            "P14", CHECK_NAMES["P14"], "FAIL",
            f"{card} の検査が成立しない: " + "／".join(report["errors"]),
        )
    if report["findings"]:
        detail = "／".join(
            f"{f['kind']}:{f['detail']}" for f in report["findings"][:5]
        )
        more = "" if report["hits"] <= 5 else f"（ほか {report['hits'] - 5} 件）"
        return Check(
            "P14", CHECK_NAMES["P14"], "FAIL",
            f"{card} が check_proposal.py を通らない（検出 {report['hits']} 件）: {detail}{more}",
        )
    return Check(
        "P14", CHECK_NAMES["P14"], "PASS",
        f"{card} は検出 0 件（カード {report['card_items']} 件 / 禁止語 {report['words_checked']} 語を検査）",
    )


def run_checks(task_id: str, spec: dict) -> list[Check]:
    applicable = decide_applicability(spec)
    checks: list[Check] = []
    for cid in sorted(CHECK_NAMES, key=lambda c: int(c[1:])):
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
        elif cid == "P9":
            checks.append(check_spec_lint(task_id))
        elif cid == "P10":
            checks.append(check_preflight_names(spec))
        elif cid == "P11":
            checks.append(check_gpu_free())
        elif cid == "P12":
            checks.append(check_refs_resolved(task_id, spec))
        elif cid == "P13":
            checks.append(check_symmetry_table(task_id))
        elif cid == "P14":
            checks.append(check_proposal_card(task_id, spec))
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

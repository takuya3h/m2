#!/usr/bin/env python3
"""契約の本文を走査し、起票者の既知の誤りを検出する（層 1）。

**規則は思いつきで足さない。** 各規則は `tasks/*/result.yaml` の `issuer_defects` に
実際に記録された誤りを裏付けとして持つ。教師データが正本であり、対応表は
`tests/test_check_spec.py` の `TEACHER` が持つ。裏付けの無い規則を足すと検出率が
測れなくなる（分母を後から動かすことになる）。

対象は `syntactic` と `structural` に分類した誤りだけである。`semantic` に分類した
誤りは構文でも構造でも捕まらない。**捕まらないことを明示するのが分類の目的である。**
分類とその理由は `tasks/T-2026-08-11-issuer-defect-detector/defects.md` にある。

命令の取り出しは `tools/check_agent_docs.py` の実装を再利用する。SPEC.md は
fenced block と 4 字下げの両方を命令に使うため、取り出しを自作すると片方を落とす。
**取りこぼしそのものが本道具が捕まえようとしている誤りの型である。**

生成物の場所は `tools/check_forbidden.py` が生成器の実装から解決したものを使う。
手で書いた一覧を持つと生成物が増えたときに古くなる。**二重管理を作らない。**

使い方:

    python tools/check_spec.py                       # 全契約
    python tools/check_spec.py --task T-YYYY-MM-DD-slug
    python tools/check_spec.py --path <SPEC.md> --spec <spec.yaml>   # 陽性対照用
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "tasks"

_TOOLS_DIR = str(REPO_ROOT / "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

# 命令の取り出しと置換の除去は既存の実装を使う。**同じ取り方にする。**
from check_agent_docs import _command, check_text  # noqa: E402
from check_forbidden import generated_locations  # noqa: E402

# 一覧・件数を作る命令。ここへ切り詰めが混ざると記録が縮む。
_LISTING = re.compile(r"(?<![\w./-])(grep|rg|ls|find|git\s+ls-files|git\s+[^|]*\blog\b)")
# 件数を指定しない切り詰めだけを対象にする。`head -30` は書き手が上限を選んでいるが、
# 素の `head` は既定の 10 行で**黙って**落ちる。絞り込みの実測は 102 件 -> 6 件。
_TRUNCATE = re.compile(r"\|\s*(head|tail)(?:\s+(?!-)|\s*$|\s*\|\|)")
_FULL_COUNT = re.compile(r"(?<![\w./-])wc\s+-l")

# zsh は `--opt=*.md` の語全体をグロブとして展開しようとし、一致しなければ失敗する。
_UNQUOTED_OPT_GLOB = re.compile(r"(?<!\S)--?[A-Za-z][\w-]*=[^\s'\"]*\*")
_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")

_HOST_DECL = re.compile(r"\*\*実行ホスト:?\*\*[^`\n]*`([^`]+)`")
_BACKTICKED = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
_TABLE_ROW = re.compile(r"^\s*\|(.+)\|\s*$")

# 「差分が空」を求める判定。生成物を除外する道具を指していれば誤りではない。
_EMPTY_DIFF = re.compile(r"無変更|差分が空|差分なし|出力なし")
_EXCLUDING_TOOL = "forbidden-check"

_INTEGRATION = re.compile(r"統合")
_PAUSE_MARK = ".sync-pause"
# 抑止の**手順**を書いている契約は該当としない。目印の文字列を書かず
# 「抑止を置く／解除する」と日本語で述べるだけの起票が二契約続けて偽陽性になった
# （T-2026-08-31 の二本と T-2026-09-01 の一本。教師データの陰性例に追加した）。
# **語だけでは足りない。** 設置と解除の双方に触れる記述だけを抑止の手順とみなす。
# 陽性の教師例（抑止を探すこと自体が課題の契約）はこの形を持たない。
_PAUSE_SET = re.compile(r"抑止[^。\n]{0,20}(置く|設置|作成|付ける)")
_PAUSE_RELEASE = re.compile(r"抑止[^。\n]{0,20}(解除|外す|移動で解|消せば)")


def _has_pause_procedure(text: str) -> bool:
    """抑止の手順があるか。目印の文字列か、設置と解除の双方の記述で判定する。"""
    if _PAUSE_MARK in text:
        return True
    return bool(_PAUSE_SET.search(text) and _PAUSE_RELEASE.search(text))

# 報告を「書く／転記する／投影する」ことを求めるゲート。語だけでは足りない
# （多くのゲートが報告に言及する）。**動作を伴う言及だけを対象にする。**
_REPORT_WORDS = re.compile(r"報告[^。]*(書|転記|投影|対)|(書|作)[^。]*報告|RESULT\.md|result\.yaml")
_MEASURE_WORDS = re.compile(r"数える|実数|内訳|確かめ|測る|測定|集計")
_REVERIFY = re.compile(r"再検証しない")

RULE_CLASSES = {
    "truncation_in_measurement": "syntactic",
    "unquoted_glob": "syntactic",
    "separated_source": "syntactic",
    "forbidden_vs_output": "structural",
    "host_mismatch": "structural",
    "integration_prohibited_without_pause": "structural",
    "gate_requires_report_before_end": "structural",
    "reverify_contradiction": "structural",
}


def _rel(path: Path) -> str:
    """repo 相対で表す。repo の外（陽性対照の一時ファイル）はそのまま返す。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class Finding:
    task: str
    rule: str
    rule_class: str
    file: str
    line: int
    detail: str


@dataclass(frozen=True)
class Contract:
    task: str
    md_path: Path
    md_text: str
    spec_path: Path
    spec: dict


def iter_commands(text: str):
    """(行番号, 命令) を返す。行番号は 1 始まり。"""
    in_fence = False
    for index, line in enumerate(text.splitlines()):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        command = _command(line, in_fence=in_fence)
        if command is None or command.startswith("#"):
            continue
        yield index + 1, command


def _tables(text: str) -> list[tuple[int, list[str]]]:
    """(行番号, セルの一覧) を返す。区切り行は落とす。"""
    rows = []
    for index, line in enumerate(text.splitlines()):
        match = _TABLE_ROW.match(line)
        if not match:
            continue
        cells = [c.strip() for c in match.group(1).split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append((index + 1, cells))
    return rows


def _prohibition_rows(text: str) -> list[tuple[int, str]]:
    """禁止事項の表の行を返す。表の見出しに「禁止」を含むものだけを対象にする。"""
    rows = _tables(text)
    result = []
    active = False
    for line, cells in rows:
        joined = " ".join(cells)
        if any("禁止" in c for c in cells) and len(cells) <= 3 and len(joined) < 40:
            active = True
            continue
        if active:
            if not cells or not cells[0].strip():
                active = False
                continue
            if re.fullmatch(r"\d+", cells[0].strip()):
                result.append((line, joined))
            else:
                active = False
    return result


# ---------------------------------------------------------------- syntactic

def rule_truncation_in_measurement(c: Contract) -> list[Finding]:
    """一覧・件数を作る命令に表示用の切り詰めが混ざっている。

    裏付け: T-2026-08-17-report-projection-and-friction#2、
            T-2026-08-11-hts-comparability-audit#3（同じ行が両方に該当する）。
    件数を別に出している（`wc -l`）場合は記録が縮まないため対象にしない。
    """
    found = []
    for line, command in iter_commands(c.md_text):
        if not _TRUNCATE.search(command):
            continue
        if not _LISTING.search(command):
            continue
        if _FULL_COUNT.search(command):
            continue
        found.append(
            Finding(
                c.task,
                "truncation_in_measurement",
                "syntactic",
                _rel(c.md_path),
                line,
                f"一覧を作る命令に切り詰めが混ざる（件数の出力が無い）: {command}",
            )
        )
    return found


def rule_unquoted_glob(c: Contract) -> list[Finding]:
    """引用符の外にグロブを含む選択肢。zsh では語全体の展開に失敗して命令が落ちる。

    裏付け: T-2026-08-11-hts-comparability-audit#3。
    """
    found = []
    for line, command in iter_commands(c.md_text):
        bare = _QUOTED.sub(" ", command)
        for match in _UNQUOTED_OPT_GLOB.finditer(bare):
            found.append(
                Finding(
                    c.task,
                    "unquoted_glob",
                    "syntactic",
                    _rel(c.md_path),
                    line,
                    f"引用されていないグロブ {match.group(0)} は zsh で展開に失敗する: {command}",
                )
            )
    return found


def rule_separated_source(c: Contract) -> list[Finding]:
    """読み込み（`source`）が単独の命令で終わり、直後の命令がそれを前提にしている。

    裏付け: T-2026-08-11-codex-parity#1。命令ごとに新しいシェルが起きる実装系では
    前の命令で読み込んだ環境が引き継がれない。**読み込みは同じ命令の中に入れる。**

    判定は `tools/check_agent_docs.py` の `check_text` へ委譲する。**判定を複製しない。**
    同じ規則を 2 か所に書くと、片方だけが直されて食い違う。既存の実装は手順書側を
    見ており、ここは契約側を見る。**対象が違うだけで規則は 1 つである。**

    次の命令もまた読み込みである場合は対象にしない。**後の読み込みは前の読み込みに
    依存しない**ため、そこは誤りではない。鎖の実際の切れ目（最後の読み込みと、それを
    使う命令の境目）は別の該当として出る。実測では該当 18 件のうち 8 件がこれだった。
    """
    return [
        Finding(
            c.task,
            "separated_source",
            "syntactic",
            _rel(c.md_path),
            v.line,
            f"読み込みが単独の命令で終わり、次の命令（{v.next_line} 行）へ引き継がれない: "
            f"{v.command} -> {v.next_command}",
        )
        for v in check_text(_rel(c.md_path), c.md_text)
        if not v.next_command.startswith("source ")
    ]


# --------------------------------------------------------------- structural

def rule_forbidden_vs_output(c: Contract) -> list[Finding]:
    """禁止領域と生成物の交差が空でないのに、差分が空であることを求めている。

    裏付け: T-2026-08-13-implementation-history-index#1、
            T-2026-08-15-template-leak-and-autosync-conflict#1 と #3、
            T-2026-08-11-codex-parity#4。
    生成物を除外する道具（`forbidden-check`）を指している判定は誤りではない。
    **素朴に「差分が空」を求めると、指示どおり実行すると必ず判定を破る。**
    """
    directories, files = generated_locations()
    forbidden = _prohibition_rows(c.md_text)
    overlapping = []
    for line, body in forbidden:
        for raw in _BACKTICKED.findall(body):
            path = raw.rstrip("*").rstrip("/")
            if not path:
                continue
            prefix = f"{path}/"
            if any(d.startswith(prefix) or prefix.startswith(d) for d in directories) or any(
                f.startswith(prefix) for f in files
            ):
                overlapping.append((line, raw))
    if not overlapping:
        return []

    found = []
    for line, cells in _tables(c.md_text):
        joined = " ".join(cells)
        if "禁止領域" not in joined or not _EMPTY_DIFF.search(joined):
            continue
        if _EXCLUDING_TOOL in joined:
            continue
        crossing = ", ".join(sorted({raw for _, raw in overlapping}))
        found.append(
            Finding(
                c.task,
                "forbidden_vs_output",
                "structural",
                _rel(c.md_path),
                line,
                f"禁止領域 {crossing} は生成物の場所と交差するが、判定は差分が空であることを"
                f"求め、生成物を除外する道具（{_EXCLUDING_TOOL}）を指していない: {joined}",
            )
        )
    return found


def rule_host_mismatch(c: Contract) -> list[Finding]:
    """本文が宣言した実行ホストと、実際の実行環境が異なる。

    裏付け: T-2026-08-14-bundle-attachment-transport#3、
            T-2026-08-16-docs-reconciliation#3。

    **この規則は実行対象の契約に対してのみ意味を持つ。** 完了した契約は別のホストで
    実行されたのだから、いま別のホストから走らせれば当然一致しない。全契約へ回すと
    過去の契約に無意味な該当が出る（実測 5 件のうち 1 件がこれ）。
    `--task` で実行対象を指定して使うこと。
    """
    actual = socket.gethostname()
    found = []
    for index, line in enumerate(c.md_text.splitlines(), 1):
        match = _HOST_DECL.search(line)
        if not match:
            continue
        declared = match.group(1).strip()
        if declared.casefold() != actual.casefold():
            found.append(
                Finding(
                    c.task,
                    "host_mismatch",
                    "structural",
                    _rel(c.md_path),
                    index,
                    f"宣言された実行ホスト {declared} と実行環境 {actual} が異なる",
                )
            )
    return found


def rule_integration_prohibited_without_pause(c: Contract) -> list[Finding]:
    """統合を禁止しながら、常駐処理を止める手順を持たない。

    裏付け: T-2026-08-14-bundle-attachment-transport#5、
            T-2026-08-15-template-leak-and-autosync-conflict#2。
    常駐処理は実行者の操作なしに統合する。**文言だけでは守れない。**
    """
    if _has_pause_procedure(c.md_text):
        return []
    found = []
    for line, body in _prohibition_rows(c.md_text):
        if _INTEGRATION.search(body):
            found.append(
                Finding(
                    c.task,
                    "integration_prohibited_without_pause",
                    "structural",
                    _rel(c.md_path),
                    line,
                    f"統合を禁止しているが {_PAUSE_MARK} による抑止の手順が本文に無い: {body}",
                )
            )
    return found


def rule_gate_requires_report_before_end(c: Contract) -> list[Finding]:
    """完了報告を求めるゲートが、最終フェーズより前に置かれている。

    裏付け: T-2026-08-17-report-projection-and-friction#1。指示どおり評価しようと
    すると、まだ測っていない値を書くことになり「未測定の値を書かない」と衝突する。
    """
    plan = c.spec.get("plan") or {}
    phases = [str(p.get("id")) for p in (plan.get("phases") or []) if p.get("id")]
    if not phases:
        return []
    last = phases[-1]
    spec_lines = c.spec_path.read_text(encoding="utf-8").splitlines()

    found = []
    for gate in plan.get("gates") or []:
        after = str(gate.get("after", ""))
        check = str(gate.get("check", ""))
        if after == last or not _REPORT_WORDS.search(check):
            continue
        gate_id = str(gate.get("id", ""))
        line = next(
            (i for i, text in enumerate(spec_lines, 1) if f"id: {gate_id}" in text),
            0,
        )
        found.append(
            Finding(
                c.task,
                "gate_requires_report_before_end",
                "structural",
                _rel(c.spec_path),
                line,
                f"ゲート {gate_id} は after={after}（最終フェーズは {last}）で完了報告を"
                f"求めている。未測定の値を書くことになる: {check}",
            )
        )
    return found


def rule_reverify_contradiction(c: Contract) -> list[Finding]:
    """再検証しないと宣言した対象について、後段が測ることを求めている。

    裏付け: T-2026-08-11-hts-comparability-audit#2。前者に従えば測らず後者に従えば
    測る。**同じ事実について両方を書くと、どちらに従っても契約を破る。**
    """
    lines = c.md_text.splitlines()
    declared_at = [i for i, text in enumerate(lines, 1) if _REVERIFY.search(text)]
    if not declared_at:
        return []
    scope_end = max(declared_at)
    scope = "\n".join(lines[:scope_end])

    terms = set()
    for span in _BOLD.findall(scope) + _BACKTICKED.findall(scope):
        for word in re.findall(r"[A-Z][a-z]{3,}", span):
            terms.add(word)
    if not terms:
        return []

    found = []
    for index, line in enumerate(lines[scope_end:], scope_end + 1):
        if not _MEASURE_WORDS.search(line):
            continue
        hit = sorted(t for t in terms if t in line)
        if not hit:
            continue
        found.append(
            Finding(
                c.task,
                "reverify_contradiction",
                "structural",
                _rel(c.md_path),
                index,
                f"再検証しないと宣言した対象 {', '.join(hit)} について測ることを求めている: "
                f"{line.strip()}",
            )
        )
        break
    return found


RULES = (
    rule_truncation_in_measurement,
    rule_unquoted_glob,
    rule_separated_source,
    rule_forbidden_vs_output,
    rule_host_mismatch,
    rule_integration_prohibited_without_pause,
    rule_gate_requires_report_before_end,
    rule_reverify_contradiction,
)


def load_contract(task: str) -> Contract:
    md_path = TASKS_DIR / task / "SPEC.md"
    spec_path = TASKS_DIR / task / "spec.yaml"
    return Contract(
        task=task,
        md_path=md_path,
        md_text=md_path.read_text(encoding="utf-8") if md_path.exists() else "",
        spec_path=spec_path,
        spec=(yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {})
        if spec_path.exists()
        else {},
    )


def discover_contracts() -> list[str]:
    return sorted(
        p.name for p in TASKS_DIR.glob("T-*") if p.is_dir() and (p / "SPEC.md").exists()
    )


def check(contracts: list[Contract]) -> dict:
    findings: list[Finding] = []
    errors: list[str] = []
    for contract in contracts:
        if not contract.md_text:
            errors.append(f"SPEC.md が無い、または空: {contract.task}")
            continue
        for rule in RULES:
            try:
                findings.extend(rule(contract))
            except Exception as exc:  # pragma: no cover - 規則の不具合を隠さない
                errors.append(f"{contract.task} の {rule.__name__} が失敗: {exc}")

    by_rule: dict[str, int] = {name: 0 for name in RULE_CLASSES}
    for finding in findings:
        by_rule[finding.rule] += 1

    return {
        "status": "fail" if findings or errors else "pass",
        "rules_checked": len(RULES),
        "targets": len(contracts),
        "hits": len(findings),
        "hits_by_rule": by_rule,
        "findings": [asdict(f) for f in findings],
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="契約の本文から既知の誤りを検出する。")
    parser.add_argument("--task", help="契約の識別子。省略時は全契約。")
    parser.add_argument("--path", help="SPEC.md を直接指定する（陽性対照用）。")
    parser.add_argument("--spec", help="spec.yaml を直接指定する（--path と併用）。")
    args = parser.parse_args(argv)

    if args.path:
        md_path = Path(args.path)
        spec_path = Path(args.spec) if args.spec else md_path.with_name("spec.yaml")
        contracts = [
            Contract(
                task=args.task or md_path.parent.name,
                md_path=md_path,
                md_text=md_path.read_text(encoding="utf-8") if md_path.exists() else "",
                spec_path=spec_path,
                spec=(yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {})
                if spec_path.exists()
                else {},
            )
        ]
    else:
        tasks = [args.task] if args.task else discover_contracts()
        contracts = [load_contract(t) for t in tasks]

    payload = check(contracts)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

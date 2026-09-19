#!/usr/bin/env python3
"""提案文書を走査し、提案関門の機械で見える部分だけを検査する。

規約の正本は `context/conventions.md` の `proposal_gate` 節、手順は
`docs/proposal-gate.md` にある。

**一覧は規約から読む。検査器の中に持たない。** 禁止語もカードの項目も、
写しを持つと規約を直したときに検査だけが古くなる。読めなかった場合は黙って
通さず `errors` に入れて非零で終わる（**空の一覧で全件合格にしない**）。

検査は二つ。

1. 禁止語の完全一致。正規化も語幹処理もせず、書かれたままの並びを探す
2. 提案カードの充足。見出しの有無と、規約が数値を求める項目に数字があるか。件数は
   規約の表から読む（`EXPECTED_CARD_ITEMS` は読めているかの健全性検査にだけ使う）

**内容の妥当性は見ない。** 効果量の値が妥当か、引用が実在するか、順位が正しいかは
批判会話が見る（`docs/proposal-gate.md` の B.6）。ここで見るのは形だけである。

`tools/check_spec.py` には足していない。あちらの規則は `tasks/*/result.yaml` の
`issuer_defects` を裏付けに持つ設計で、裏付けの無い規則を足すと検出率の分母が動く。

使い方:

    python tools/check_proposal.py <proposal.md>
    python tools/check_proposal.py <proposal.md> --only forbidden
    python tools/check_proposal.py <proposal.md> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVENTIONS_PATH = REPO_ROOT / "context" / "conventions.md"

# アンカーの形は tools/validate_task.py の _ANCHOR_RE と同じにする。
# 節は次のアンカーまで。proposal_gate は末尾に置かれるため \Z も終端に取る。
_SECTION_RE = re.compile(
    r'<a id="proposal_gate"></a>\n(.*?)(?=\n<a id="[a-z0-9_]+"></a>|\Z)', re.S
)
_FORBIDDEN_HEADING = re.compile(r"^### 禁止語.*$", re.M)
_CARD_HEADING = re.compile(r"^### 提案カード.*$", re.M)
_NEXT_SUBHEADING = re.compile(r"^### ", re.M)
_CARD_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", re.M)
# 「#5 #6 #10 は数値で書く。」だけを取る。同じ段落の「#10 は #14 の掃引集合全体で
# 見積もる。」を巻き込まないため、文単位（句点区切り）で当てる。
_NUMERIC_SENTENCE = re.compile(r"[^。\n]*数値で書く[^。\n]*。")
_CARD_REF = re.compile(r"#(\d+)")

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_DIGIT = re.compile(r"[0-9０-９]")

# 規約は「未踏」「空白」の禁止を解かないが、空白である理由の仮説を添えた本文は
# 形の検査では通し、境界の判断を批判会話に委ねる
# （SPEC Task D-5 / docs/proposal-gate.md B.6）。この二語と条件だけは実装側に置く。
# 規約に該当の文言が在ることは tests/test_check_proposal.py が確かめる。
_EXEMPT_WORDS = ("未踏", "空白")
_EXEMPT_CONDITION = "空白である理由の仮説"

# 規約の表から読めた件数がこの数と違えば、読み取りが壊れたとみなして非零で終わる。
# **一覧そのものは規約から読む。** ここに持つのは件数だけで、写しではない。
# 規約が増えたらこの数も直す（試験 test_expected_card_items_matches_conventions が縛る）。
EXPECTED_CARD_ITEMS = 16


@dataclass
class Finding:
    kind: str
    line: int
    detail: str


def section_text() -> str:
    """規約の proposal_gate 節の本文。読めなければ空文字を返す。"""
    if not CONVENTIONS_PATH.exists():
        return ""
    found = _SECTION_RE.search(CONVENTIONS_PATH.read_text(encoding="utf-8"))
    return found.group(1) if found else ""


def forbidden_words(section: str | None = None) -> list[str]:
    """禁止語の一覧。見出しの直後の段落を全角の／で割る。"""
    text = section_text() if section is None else section
    found = _FORBIDDEN_HEADING.search(text)
    if not found:
        return []
    collected: list[str] = []
    for line in text[found.end():].split("\n"):
        stripped = line.strip()
        if not stripped:
            if collected:
                break
            continue
        collected.append(stripped)
    return [w for w in ("".join(collected).split("／")) if w.strip()]


def card_items(section: str | None = None) -> dict[int, str]:
    """提案カードの項目。番号 -> 項目名。"""
    text = section_text() if section is None else section
    found = _CARD_HEADING.search(text)
    if not found:
        return {}
    rest = text[found.end():]
    nxt = _NEXT_SUBHEADING.search(rest)
    if nxt:
        rest = rest[: nxt.start()]
    return {int(num): name for num, name in _CARD_ROW.findall(rest)}


def numeric_items(section: str | None = None) -> set[int]:
    """数値で書くことを規約が求めている項目の番号。"""
    text = section_text() if section is None else section
    numbers: set[int] = set()
    for sentence in _NUMERIC_SENTENCE.findall(text):
        numbers.update(int(n) for n in _CARD_REF.findall(sentence))
    return numbers


def _heading_number(title: str) -> int | None:
    """見出しからカード番号を取る。`#5 ...` と `5. ...` の両方を認める。"""
    ref = _CARD_REF.search(title)
    if ref:
        return int(ref.group(1))
    lead = re.match(r"(\d+)\s*[.．、)）]", title)
    return int(lead.group(1)) if lead else None


def _bodies_by_number(text: str) -> dict[int, tuple[int, list[str]]]:
    """カード番号 -> (見出しの行番号, 次の見出しまでの本文)。"""
    bodies: dict[int, tuple[int, list[str]]] = {}
    current: int | None = None
    for lineno, line in enumerate(text.split("\n"), 1):
        heading = _MD_HEADING.match(line)
        if heading:
            current = _heading_number(heading.group(2))
            if current is not None and current not in bodies:
                bodies[current] = (lineno, [])
            continue
        if current is not None and current in bodies:
            bodies[current][1].append(line)
    return bodies


def check_forbidden(text: str, words: list[str]) -> list[Finding]:
    """禁止語を出現ごとに 1 件として拾う。行番号を付けて返す。"""
    exempt = _EXEMPT_CONDITION in text
    findings: list[Finding] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for word in words:
            if exempt and word in _EXEMPT_WORDS:
                continue
            start = 0
            while True:
                at = line.find(word, start)
                if at < 0:
                    break
                findings.append(Finding("forbidden_word", lineno, f"禁止語「{word}」"))
                start = at + len(word)
    return findings


def check_card(text: str, items: dict[int, str], numeric: set[int]) -> list[Finding]:
    """見出しの欠落と、数値を求める項目に数字が無いことを拾う。"""
    bodies = _bodies_by_number(text)
    findings: list[Finding] = []
    for num in sorted(items):
        name = items[num].split("。")[0]
        if num not in bodies:
            findings.append(
                Finding("missing_heading", 0, f"カード #{num}（{name}）の見出しが無い")
            )
            continue
        lineno, body = bodies[num]
        if num in numeric and not _DIGIT.search("\n".join(body)):
            findings.append(
                Finding("missing_number", lineno, f"カード #{num}（{name}）の本文に数字が無い")
            )
    return findings


def check(path: Path, only: str = "both") -> dict:
    text = path.read_text(encoding="utf-8")
    section = section_text()
    errors: list[str] = []
    words = forbidden_words(section)
    items = card_items(section)
    numeric = numeric_items(section)

    if not section:
        errors.append("context/conventions.md の proposal_gate 節を読めません")
    else:
        if not words:
            errors.append("規約から禁止語の一覧を読めません")
        if len(items) != EXPECTED_CARD_ITEMS:
            errors.append(
                f"規約の提案カードが {EXPECTED_CARD_ITEMS} 件ではありません: {len(items)} 件"
            )
        if not numeric:
            errors.append("規約から数値を求める項目を読めません")

    findings: list[Finding] = []
    if only in ("both", "forbidden"):
        findings.extend(check_forbidden(text, words))
    if only in ("both", "card"):
        findings.extend(check_card(text, items, numeric))

    by_kind: dict[str, int] = {"forbidden_word": 0, "missing_heading": 0, "missing_number": 0}
    for finding in findings:
        by_kind[finding.kind] += 1

    return {
        "status": "fail" if findings or errors else "pass",
        "path": str(path),
        "only": only,
        "words_checked": len(words),
        "card_items": len(items),
        "numeric_items": sorted(numeric),
        "hits": len(findings),
        "hits_by_kind": by_kind,
        "findings": [asdict(f) for f in findings],
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="提案文書を提案関門の形で検査する。")
    parser.add_argument("path", help="検査する markdown ファイル。")
    parser.add_argument(
        "--only", choices=["both", "forbidden", "card"], default="both",
        help="片方だけを回す（対照を測るときに使う）。",
    )
    parser.add_argument("--json", action="store_true", help="結果を JSON で出す。")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR 見つかりません: {path}", file=sys.stderr)
        return 2

    report = check(path, args.only)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for error in report["errors"]:
            print(f"ERROR {error}", file=sys.stderr)
        for finding in report["findings"]:
            where = f"{path}:{finding['line']}" if finding["line"] else str(path)
            print(f"{finding['kind']:16s} {where}  {finding['detail']}")
        print(
            f"\n規約から読んだ禁止語 {report['words_checked']} 語 / "
            f"カード {report['card_items']} 件（数値必須 {report['numeric_items']}）"
        )
        print(
            f"検出 {report['hits']} 件"
            f"（禁止語 {report['hits_by_kind']['forbidden_word']} / "
            f"見出し欠落 {report['hits_by_kind']['missing_heading']} / "
            f"数字欠落 {report['hits_by_kind']['missing_number']}）"
        )
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

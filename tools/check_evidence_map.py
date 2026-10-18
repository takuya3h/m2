#!/usr/bin/env python3
"""証拠地図の様式を検査する。

対象は docs/evidence/ の Markdown のうち、見出しの前の欄に `**種類:**` を持つもの。
雛形（docs/evidence/_template.md）の「検査が見る項目」と同じ項目を見る。雛形と本器の
項目が食い違わないことは tests/test_check_evidence_map.py が縛る。

    python tools/check_evidence_map.py                 # docs/evidence/ の地図すべて
    python tools/check_evidence_map.py <地図>.md ...   # 指定した地図だけ
    make evidence-check

見る項目:

1. 見出しの前の五つの欄（版・種類・状態・元の報告・検索日）と、種類の値
2. 種類ごとの必須の節（見出しの語で探す。番号は問わない）
3. citation の印の残骸（報告の参照記号）と私用領域の文字
4. BMP 外の文字
5. 禁止語。**規約（context/conventions.md の proposal_gate）から読む。写しを持たない**
6. `**元の報告:**` に書いた sha256 が docs/evidence/reports/ の実在のファイルの要約値と一致する

**内容の正しさは見ない。** 書誌の実在は tools/verify_evidence_ids.py が見る。

終了コード: 0 違反なし / 1 違反あり / 2 読めない（地図・規約の禁止語）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from check_proposal import check_forbidden, forbidden_words  # noqa: E402

EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence"
REPORTS_DIR = EVIDENCE_DIR / "reports"

HEADER_FIELDS = ("版", "種類", "状態", "元の報告", "検索日")
REQUIRED_SECTIONS = {
    "探索の地図": (
        "系統表", "行の一覧", "近さ", "手法の位置", "証拠の質", "効果", "実装",
        "本研究との関係", "見つからなかったもの", "未検証の組み合わせ", "検索記録",
    ),
    "新規性の照合": ("照合表", "見つからない理由の証拠", "見つからなかったもの", "検索記録"),
}
# 本文の全体に当てる検査の種類。雛形の「本文の全体」の四項目に対応する（試験が縛る）。
BODY_CHECKS = ("citation_residue", "private_use", "non_bmp", "forbidden_word", "report_sha256")

_FIELD_RE = re.compile(r"^\*\*(?P<name>[^*:]+):\*\*\s*(?P<value>.*)$")
_HEADING_RE = re.compile(r"^#{2,6}\s+(?P<text>.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
# 報告の参照記号の残骸。deep research の報告は私用領域の文字で囲んだ cite・turn1view1 の形で書く。
_CITATION_RES = (
    re.compile(r"turn\d+[a-z]{3,10}\d+"),
    re.compile(r"【\d+[^】]*†[^】]*】"),
    re.compile(r"filecite"),
)
_SHA_TOKEN_RE = re.compile(r"sha256[\s:：=]*(?P<token>[^\s、。，,）)（(]+)")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")


@dataclass
class Finding:
    kind: str
    line: int
    detail: str


def header_lines(text: str) -> list[tuple[int, str]]:
    """最初の `## ` 見出しより前の行（行番号つき）。"""
    out = []
    for lineno, line in enumerate(text.split("\n"), 1):
        if line.startswith("## "):
            break
        out.append((lineno, line))
    return out


def header_fields(text: str) -> dict[str, tuple[int, str]]:
    fields: dict[str, tuple[int, str]] = {}
    for lineno, line in header_lines(text):
        m = _FIELD_RE.match(line)
        if m and m["name"] not in fields:
            fields[m["name"]] = (lineno, m["value"].strip())
    return fields


def is_target(text: str) -> bool:
    return "種類" in header_fields(text)


def headings(text: str) -> list[tuple[int, str]]:
    out, fenced = [], False
    for lineno, line in enumerate(text.split("\n"), 1):
        if _FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            m = _HEADING_RE.match(line)
            if m:
                out.append((lineno, m["text"]))
    return out


def report_block(text: str) -> list[tuple[int, str]]:
    """`**元の報告:**` の欄。次の欄・区切り線・見出しの手前まで。"""
    block: list[tuple[int, str]] = []
    inside = False
    for lineno, line in header_lines(text):
        m = _FIELD_RE.match(line)
        if m:
            if inside:
                break
            inside = m["name"] == "元の報告"
        elif inside and line.strip() == "---":
            break
        if inside:
            block.append((lineno, line))
    return block


def report_digests(reports_dir: Path) -> dict[str, str]:
    """reports/ の各ファイルの sha256 -> ファイル名。"""
    if not reports_dir.is_dir():
        return {}
    return {
        hashlib.sha256(p.read_bytes()).hexdigest(): p.name
        for p in sorted(reports_dir.iterdir())
        if p.is_file()
    }


def check_header(text: str) -> list[Finding]:
    fields = header_fields(text)
    findings = [
        Finding("header_field", 0, f"見出しの前に **{name}:** の欄が無い")
        for name in HEADER_FIELDS
        if name not in fields
    ]
    if "種類" in fields:
        lineno, value = fields["種類"]
        if value not in REQUIRED_SECTIONS:
            findings.append(
                Finding("header_kind", lineno, f"**種類:** の値が {' / '.join(REQUIRED_SECTIONS)} のどれでもない: {value!r}")
            )
    return findings


def check_sections(text: str) -> list[Finding]:
    fields = header_fields(text)
    kind = fields.get("種類", (0, ""))[1]
    titles = [t for _l, t in headings(text)]
    return [
        Finding("missing_section", 0, f"種類「{kind}」の必須の節「{word}」の見出しが無い")
        for word in REQUIRED_SECTIONS.get(kind, ())
        if not any(word in t for t in titles)
    ]


def check_characters(text: str) -> list[Finding]:
    findings = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for pattern in _CITATION_RES:
            for m in pattern.finditer(line):
                findings.append(Finding("citation_residue", lineno, f"citation の印の残骸「{m.group(0)}」"))
        for ch in line:
            code = ord(ch)
            if 0xE000 <= code <= 0xF8FF:
                findings.append(Finding("private_use", lineno, f"私用領域の文字 U+{code:04X}"))
            elif code > 0xFFFF:
                findings.append(Finding("non_bmp", lineno, f"BMP 外の文字 U+{code:X}"))
    return findings


def check_report_sha256(text: str, digests: dict[str, str]) -> list[Finding]:
    block = report_block(text)
    tokens = [(lineno, m["token"]) for lineno, line in block for m in _SHA_TOKEN_RE.finditer(line)]
    if not tokens:
        lineno = block[0][0] if block else 0
        return [Finding("report_sha256", lineno, "**元の報告:** に sha256 が無い")]
    findings = []
    for lineno, token in tokens:
        if not _HEX64_RE.match(token):
            findings.append(Finding("report_sha256", lineno, f"sha256 の値が 64 桁の小文字十六進でない: {token!r}"))
        elif token not in digests:
            findings.append(Finding("report_sha256", lineno, f"sha256 {token} に一致するファイルが reports/ に無い"))
    return findings


def check_text(text: str, words: list[str], digests: dict[str, str]) -> list[Finding]:
    findings = check_header(text) + check_sections(text) + check_characters(text)
    findings += [Finding(f.kind, f.line, f.detail) for f in check_forbidden(text, words)]
    findings += check_report_sha256(text, digests)
    return findings


def default_paths() -> list[Path]:
    return sorted(EVIDENCE_DIR.rglob("*.md"))


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def run(paths: list[Path], reports_dir: Path = REPORTS_DIR) -> dict:
    words = forbidden_words()
    errors = [] if words else ["context/conventions.md の proposal_gate から禁止語の一覧を読めない"]
    digests = report_digests(reports_dir)
    checked, skipped = [], []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"読めない: {_display(path)}: {exc}")
            continue
        if not is_target(text):
            skipped.append(_display(path))
            continue
        findings = check_text(text, words, digests)
        checked.append({"path": _display(path), "violations": len(findings), "findings": [asdict(f) for f in findings]})
    return {
        "status": "error" if errors else ("fail" if any(c["violations"] for c in checked) else "pass"),
        "words_checked": len(words),
        "reports": sorted(digests.values()),
        "checked": checked,
        "skipped": skipped,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="証拠地図の様式を検査する。")
    parser.add_argument("paths", nargs="*", help="検査する地図。省略すると docs/evidence/ の Markdown すべて")
    parser.add_argument("--reports-dir", default=str(REPORTS_DIR), help="元の報告の置き場（既定 docs/evidence/reports）")
    parser.add_argument("--json", action="store_true", help="結果を JSON で出す")
    args = parser.parse_args(argv)

    paths = [Path(p) for p in args.paths] if args.paths else default_paths()
    report = run(paths, Path(args.reports_dir))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for error in report["errors"]:
            print(f"ERROR {error}", file=sys.stderr)
        for item in report["checked"]:
            for f in item["findings"]:
                where = f"{item['path']}:{f['line']}" if f["line"] else item["path"]
                print(f"{f['kind']:16s} {where}  {f['detail']}")
            print(f"検査 {item['path']}: 違反 {item['violations']} 件")
        for path in report["skipped"]:
            print(f"対象外 {path}（見出しの前に **種類:** が無い）")
        print(f"\n規約から読んだ禁止語 {report['words_checked']} 語 / reports/ のファイル {len(report['reports'])} 件")
    if report["status"] == "error":
        return 2
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())

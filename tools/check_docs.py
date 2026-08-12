#!/usr/bin/env python3
"""現行手順の文書に書かれた操作と経路が実在することを機械で確かめる。

**確かめるのは実在だけである。** 手順の順序・前提条件・説明の正しさは対象外で、
人が読んで判断するしかない。何を確かめ、何を確かめないかは `docs/docs_audit.md`
の末尾に書いてある。

対象の一覧は `docs/docs_audit.md` の「対象の分類」表から取る。分類が `現行手順`
の行だけを見る。記録として分類された文書は対象外である。**過去の記述が現在と
食い違うのは当然であり、それを誤りとして数えない。**

走査するのは**コードとして書かれた箇所だけ**である。行内のバッククォートと
コードブロックの中だけを見る。散文は見ない。英文の "make a decision" のような
動詞の make を操作名と誤読するためである（実測で偽陽性が出た）。
この設計上、バッククォートを付けずに散文へ書かれた操作名や経路は**検出できない。**
検出漏れは残るが、誤検出よりましである。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

IGNORE_LINE = "<!-- docs-check: ignore-line -->"
IGNORE_FILE = "<!-- docs-check: ignore-file -->"

# 書き手が置いた変数・グロブ・省略を含む記述は対象外。実在を約束していない。
VAR_MARKS = ("$", "<", "{", "*", "...")

# 追跡下に置かれる領域だけを見る。
IN_PREFIXES = (
    "tools/", "scripts/", "tasks/", "context/", "configs/", "src/", "tests/",
    "docs/", ".claude/", "paper/", "notebooks/", "evidence/", "runindex/",
)
# ホスト依存のデータと、実行時に採番・生成される証跡は対象外。
OUT_PREFIXES = ("data/", "experiments/", "third_party/", "third_party_snapshot/")

INLINE_CODE = re.compile(r"`([^`]+)`")
FENCE = re.compile(r"^\s*```")
MAKE = re.compile(r"(?:^|[;&|]\s*|\$\s*)make\s+([a-z][a-z0-9-]*)")
PATH = re.compile(r"(?<![\w./-])([\w.][\w./-]*/[\w./-]+)")
AUDIT_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*現行手順\s*\|")
# 先頭のドットを許すこと。`.claude/` 配下の 17 文書が静かに対象から落ちる。
# 2026-08-11 に実際に落ちた（対象が 42 ではなく 25 と表示されて気付いた）。
PATHLIKE = re.compile(r"^[\w.][\w./-]*\.md$")


def _code_fragments(text: str):
    """(行番号, コードとして書かれた文字列) を返す。散文は返さない。"""
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if IGNORE_LINE in line:
            continue
        if in_fence:
            yield lineno, line
        else:
            for span in INLINE_CODE.findall(line):
                yield lineno, span
            # 字下げされたコマンド行もコードとして扱う。
            if line.startswith("    ") and line.strip():
                yield lineno, line.strip()


def extract_make_names(text: str) -> list[tuple[int, str]]:
    """コードとして書かれた `make <名前>` を抜く。"""
    out = []
    for lineno, frag in _code_fragments(text):
        if any(m in frag for m in VAR_MARKS):
            continue
        for name in MAKE.findall(frag):
            if (lineno, name) not in out:
                out.append((lineno, name))
    return out


def extract_paths(text: str) -> list[tuple[int, str]]:
    """コードとして書かれた経路のうち、追跡下の領域のものだけを抜く。"""
    out = []
    for lineno, frag in _code_fragments(text):
        if any(m in frag for m in VAR_MARKS):
            continue
        for path in PATH.findall(frag):
            path = path.rstrip(".,)）。、")
            if path.startswith(OUT_PREFIXES):
                continue
            if not path.startswith(IN_PREFIXES):
                continue
            if (lineno, path) not in out:
                out.append((lineno, path))
    return out


def check_text(doc, text, *, targets, exists, branches) -> list[str]:
    """1 つの文書を検査し、問題を人が読める行で返す。"""
    if IGNORE_FILE in text:
        return []
    problems = []
    for lineno, name in extract_make_names(text):
        if name not in targets:
            problems.append(f"{doc}:{lineno} 実在しない操作 make {name}")
    for lineno, path in extract_paths(text):
        if path in branches:
            continue  # 分岐名であって経路ではない
        if not exists(path):
            problems.append(f"{doc}:{lineno} 実在しない経路 {path}")
    return problems


def check_documents(docs, *, targets, exists, branches) -> list[str]:
    """対象が無くても、対象の文書が存在しなくても落ちない。"""
    problems = []
    for doc in docs:
        p = Path(doc)
        if not p.is_file():
            problems.append(f"{doc} 対象の文書が存在しない")
            continue
        problems.extend(
            check_text(doc, p.read_text(encoding="utf-8"),
                       targets=targets, exists=exists, branches=branches)
        )
    return problems


def parse_audit_targets(audit_text: str) -> list[str]:
    """分類表から現行手順の行だけを取る。集約行（空白を含む説明）は経路ではない。"""
    out = []
    for line in audit_text.splitlines():
        m = AUDIT_ROW.match(line)
        if not m:
            continue
        cell = m.group(1).strip().strip("`")
        if PATHLIKE.match(cell):
            out.append(cell)
    return out


def load_make_targets(makefile: Path) -> set[str]:
    return {
        line.split(":", 1)[0]
        for line in makefile.read_text(encoding="utf-8").splitlines()
        if re.match(r"^[a-z][a-z0-9-]*:", line)
    }


def load_branches() -> set[str]:
    r = subprocess.run(["git", "branch", "-r", "--format=%(refname:short)"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return set()
    return {b.split("/", 1)[1] for b in r.stdout.split() if "/" in b}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", default="docs/docs_audit.md")
    ap.add_argument("--makefile", default="Makefile")
    args = ap.parse_args()

    audit = Path(args.audit)
    if not audit.is_file():
        print(f"[docs-check] 対象の一覧が無い: {audit}", file=sys.stderr)
        return 1

    docs = parse_audit_targets(audit.read_text(encoding="utf-8"))
    targets = load_make_targets(Path(args.makefile))
    branches = load_branches()
    problems = check_documents(
        docs, targets=targets, exists=lambda p: Path(p).exists(), branches=branches
    )

    print(f"[docs-check] 対象 {len(docs)} 文書 / Makefile のターゲット {len(targets)} 件")
    for line in problems:
        print(f"  {line}")
    if problems:
        print(f"[docs-check] {len(problems)} 件の食い違い", file=sys.stderr)
        return 1
    print("[docs-check] 食い違いなし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

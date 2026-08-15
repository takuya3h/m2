#!/usr/bin/env python
"""実装側の集合を、異質な二つの方法で集める。

方法 1（構文木）: `ast` で解析し、設定らしき根から伸びる属性・添字の連なりを集める。
方法 2（字面）: 生の文字列を正規表現で走査する。構文木を使わないため、
              文字列引数の中に現れる経路（OmegaConf.select など）も拾う。

どちらも「根がどの物体か」までは決められない。判定は実行時の追跡に委ねる。
本スクリプトは候補と出所（ファイル:行・囲みの関数）を記録するだけである。

出力: audit/impl_reads.json
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

PROJ = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "impl_reads.json"

ROOT_NAMES = {"cfg", "config", "conf"}
TARGET_DIRS = ("src/egosurgery", "scripts")


def iter_py() -> list[Path]:
    files: list[Path] = []
    for d in TARGET_DIRS:
        files.extend(sorted((PROJ / d).rglob("*.py")))
    return files


# ----------------------------------------------------------------- 方法 1
class Collector(ast.NodeVisitor):
    def __init__(self, rel: str) -> None:
        self.rel = rel
        self.hits: list[dict] = []
        self.stack: list[str] = []

    def _scope(self) -> str:
        return ".".join(self.stack) or "<module>"

    def visit_FunctionDef(self, node: ast.FunctionDef):  # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef):  # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    @staticmethod
    def _root_of(node: ast.AST) -> tuple[str, list[str]] | None:
        """属性・添字の連なりを (根, 経路) に分解する。根でなければ None。"""
        parts: list[str] = []
        cur = node
        while True:
            if isinstance(cur, ast.Attribute):
                # `self.cfg` / `self.config` は根である。これを属性として
                # 食い潰すと根の判定に到達しない。ここで止める。
                if (
                    isinstance(cur.value, ast.Name)
                    and cur.value.id == "self"
                    and cur.attr in ROOT_NAMES
                ):
                    parts.reverse()
                    return f"self.{cur.attr}", parts
                parts.append(cur.attr)
                cur = cur.value
            elif isinstance(cur, ast.Subscript):
                sl = cur.slice
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                    parts.append(sl.value)
                else:
                    parts.append("<dynamic>")
                cur = cur.value
            else:
                break
        parts.reverse()
        if isinstance(cur, ast.Name) and cur.id in ROOT_NAMES:
            return cur.id, parts
        if (
            isinstance(cur, ast.Attribute)
            and isinstance(cur.value, ast.Name)
            and cur.value.id == "self"
            and cur.attr in ROOT_NAMES
        ):
            return f"self.{cur.attr}", parts
        return None

    def _record(self, node: ast.AST, kind: str, extra: list[str] | None = None) -> None:
        found = self._root_of(node)
        if not found:
            return
        root, parts = found
        parts = parts + (extra or [])
        if not parts:
            path = ""
        else:
            path = ".".join(parts)
        self.hits.append(
            {
                "file": self.rel,
                "line": getattr(node, "lineno", -1),
                "scope": self._scope(),
                "root": root,
                "path": path,
                "kind": kind,
            }
        )

    def visit_Attribute(self, node: ast.Attribute):  # noqa: N802
        self._record(node, "attr")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):  # noqa: N802
        self._record(node, "item")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):  # noqa: N802
        func = node.func
        # cfg.get("x", default) / cfg.a.b.get("x")
        if isinstance(func, ast.Attribute) and func.attr == "get" and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                self._record(func.value, "get", extra=[first.value])
        # OmegaConf.select(cfg, "a.b") / OmegaConf.to_container(cfg.x)
        if isinstance(func, ast.Attribute) and func.attr == "select" and len(node.args) >= 2:
            second = node.args[1]
            if isinstance(second, ast.Constant) and isinstance(second.value, str):
                self._record(node.args[0], "select", extra=second.value.split("."))
        if isinstance(func, ast.Attribute) and func.attr == "to_container" and node.args:
            self._record(node.args[0], "to_container")
        self.generic_visit(node)


def method_ast() -> list[dict]:
    hits: list[dict] = []
    errors: list[dict] = []
    for path in iter_py():
        rel = str(path.relative_to(PROJ))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append({"file": rel, "error": f"SyntaxError: {exc}"})
            continue
        col = Collector(rel)
        col.visit(tree)
        hits.extend(col.hits)
    method_ast.errors = errors  # type: ignore[attr-defined]
    return hits


# ----------------------------------------------------------------- 方法 2
ATTR_RE = re.compile(
    r"(?<![\w.])(self\.cfg|self\.config|cfg|config|conf)((?:\.[A-Za-z_]\w*)+)"
)
ITEM_RE = re.compile(
    r"(?<![\w.])(self\.cfg|self\.config|cfg|config|conf)((?:\[[\"'][^\"']+[\"']\])+)"
)
GET_RE = re.compile(
    r"(?<![\w.])(self\.cfg|self\.config|cfg|config|conf)((?:\.[A-Za-z_]\w*)*)\.get\(\s*[\"']([^\"']+)[\"']"
)
SELECT_RE = re.compile(r"OmegaConf\.select\(\s*[^,]+,\s*[\"']([^\"']+)[\"']")


def code_only_lines(path: Path) -> dict[int, str]:
    """コメントと三重引用の文字列だけを空白で潰した行を返す。

    構文木は使わず字句の位置だけを見る。説明文に書かれた `cfg.xxx` を
    読み取りと誤認しないために要る。`"img_size"` のような通常の
    文字列は残す。`.get("...")` の鍵がそこにあるためである。
    """
    import io
    import tokenize

    text = path.read_text(encoding="utf-8")
    raw = text.splitlines()
    grid = [list(line) for line in raw]
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return {i: line for i, line in enumerate(raw, start=1)}

    def blank(srow: int, scol: int, erow: int, ecol: int) -> None:
        for row in range(srow, erow + 1):
            if row - 1 >= len(grid):
                break
            line = grid[row - 1]
            start = scol if row == srow else 0
            end = ecol if row == erow else len(line)
            for col in range(start, min(end, len(line))):
                line[col] = " "

    for tok in toks:
        is_comment = tok.type == tokenize.COMMENT
        is_docstr = tok.type == tokenize.STRING and (
            tok.string.startswith('"""')
            or tok.string.startswith("'''")
            or tok.string.startswith('r"""')
            or tok.string.startswith("r'''")
        )
        if is_comment or is_docstr:
            blank(tok.start[0], tok.start[1], tok.end[0], tok.end[1])
    return {i: "".join(chars) for i, chars in enumerate(grid, start=1)}


def method_regex() -> list[dict]:
    hits: list[dict] = []
    for path in iter_py():
        rel = str(path.relative_to(PROJ))
        for lineno, line in sorted(code_only_lines(path).items()):
            for m in ATTR_RE.finditer(line):
                hits.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "root": m.group(1),
                        "path": m.group(2).lstrip("."),
                        "kind": "attr",
                    }
                )
            for m in ITEM_RE.finditer(line):
                keys = re.findall(r"[\"']([^\"']+)[\"']", m.group(2))
                hits.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "root": m.group(1),
                        "path": ".".join(keys),
                        "kind": "item",
                    }
                )
            for m in GET_RE.finditer(line):
                base = m.group(2).lstrip(".")
                path_ = f"{base}.{m.group(3)}" if base else m.group(3)
                hits.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "root": m.group(1),
                        "path": path_,
                        "kind": "get",
                    }
                )
            for m in SELECT_RE.finditer(line):
                hits.append(
                    {
                        "file": rel,
                        "line": lineno,
                        "root": "OmegaConf.select",
                        "path": m.group(1),
                        "kind": "select",
                    }
                )
    return hits


def main() -> None:
    ast_hits = method_ast()
    rx_hits = method_regex()
    ast_paths = {h["path"] for h in ast_hits if h["path"]}
    rx_paths = {h["path"] for h in rx_hits if h["path"]}
    payload = {
        "files_scanned": len(iter_py()),
        "ast": {"hits": ast_hits, "n_hits": len(ast_hits), "n_paths": len(ast_paths)},
        "regex": {"hits": rx_hits, "n_hits": len(rx_hits), "n_paths": len(rx_paths)},
        "ast_errors": getattr(method_ast, "errors", []),
        "only_in_ast": sorted(ast_paths - rx_paths),
        "only_in_regex": sorted(rx_paths - ast_paths),
        "in_both": sorted(ast_paths & rx_paths),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"files scanned          : {payload['files_scanned']}")
    print(f"ast   hits/paths       : {len(ast_hits)} / {len(ast_paths)}")
    print(f"regex hits/paths       : {len(rx_hits)} / {len(rx_paths)}")
    print(f"only in ast            : {len(payload['only_in_ast'])}")
    print(f"only in regex          : {len(payload['only_in_regex'])}")
    print(f"in both                : {len(payload['in_both'])}")
    print(f"ast parse errors       : {len(payload['ast_errors'])}")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()

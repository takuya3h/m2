#!/usr/bin/env python3
"""task_start_classify.py — 契約の開始の前に、作業ツリーの汚れを起点（`origin/phase0`）と比べて分類する。

    python3 scripts/task_start_classify.py                     # 読み取りだけ。分類を表示する
    python3 scripts/task_start_classify.py --adopt-list FILE   # task_start.sh が使う。通す経路を FILE に書く

**分類はここ一か所で行う。** `scripts/task_start.sh` も task スキルの「0. 始める」もこれを呼ぶ。
作業ツリー・索引・`.git/info/exclude` を変えない（`--adopt-list` の FILE だけを書く）。取得（fetch）もしない。
呼ぶ側が先に `git fetch origin` を済ませる。

「同じ経路」は、起点の木がその経路のファイルを追跡していることをいう。

    | 手元のファイル         | 起点の同じ経路     | 扱い                                       |
    |------------------------|--------------------|--------------------------------------------|
    | 追跡下の変更           | 問わない           | 止める                                     |
    | 無視されていない未追跡 | 在り、中身が同じ   | 汚れに数えない（通す）                     |
    | 無視されていない未追跡 | 在り、中身が違う   | 止める。経路を一覧にする                   |
    | 無視されていない未追跡 | 無い               | 止める。経路を一覧にする                   |
    | 無視された未追跡       | 在り、中身が同じ   | 通す                                       |
    | 無視された未追跡       | 在り、中身が違う   | 止める。経路を一覧にする（黙った上書きを防ぐ） |
    | 無視された未追跡       | 無い               | 触れない（数えない）                       |

無視されたファイルは数が多い（仮想環境など）ため全数を列挙しない。起点の木の経路から索引の経路を引き、
手元に在るものだけを中身で比べる。**「無視された未追跡・起点に無い」は列挙しないので件数を出さない。**

中身は、git が切り替えで書く内容と比べる。通常のファイルは `git cat-file --filters <起点>:<経路>`
（属性による変換を経た内容）、シンボリックリンクはリンク先の文字列。手元がディレクトリなどで比べられないものは
「違う」に数える（黙って上書きされうる側へ倒さない）。

出所: 契約 T-2026-10-21-ops-taskstart-resume-folds-val（SPEC §5.1）

終了コード:
    0  通す（最後の行が `[task-start] 分類: 通す`）
    3  止める（最後の行が `[task-start] 分類: 止める`。task_start.sh の 3 と同じく前提の不足）
    4  git の照会に失敗した
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

DEFAULT_BASE = "origin/phase0"
PREFIX = "[task-start]"

# 表示の順と名前。止める分類は経路を一覧にする。
TRACKED = "追跡下の変更"
UNTRACKED_SAME = "未追跡・起点に在り中身が同じ"
UNTRACKED_DIFF = "未追跡・起点に在り中身が違う"
UNTRACKED_ABSENT = "未追跡・起点に無い"
IGNORED_SAME = "無視・起点に在り中身が同じ"
IGNORED_DIFF = "無視・起点に在り中身が違う"
IGNORED_ABSENT = "無視・起点に無い"
STOP_CLASSES = (TRACKED, UNTRACKED_DIFF, UNTRACKED_ABSENT, IGNORED_DIFF)
PASS_CLASSES = (UNTRACKED_SAME, IGNORED_SAME)


class GitError(RuntimeError):
    pass


def _git(*args: str, input_bytes: bytes | None = None) -> bytes:
    proc = subprocess.run(["git", *args], input=input_bytes, capture_output=True)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout


def _nul_split(raw: bytes) -> list[str]:
    return [p for p in raw.decode("utf-8", "surrogateescape").split("\0") if p]


def base_tree(base: str) -> dict[str, str]:
    """起点の木の {経路: mode}。"""
    tree: dict[str, str] = {}
    for entry in _nul_split(_git("ls-tree", "-r", "-z", "--full-tree", base)):
        meta, path = entry.split("\t", 1)
        tree[path] = meta.split(" ", 1)[0]
    return tree


def same_content(base: str, path: str, mode: str) -> bool:
    """手元の `path` が、切り替えで git が書く内容と同じか。"""
    if os.path.islink(path):
        if mode != "120000":
            return False
        target = os.fsencode(os.readlink(path))
        return target == _git("cat-file", "blob", f"{base}:{path}")
    if not os.path.isfile(path) or mode not in ("100644", "100755"):
        return False
    with open(path, "rb") as f:
        local = f.read()
    return local == _git("cat-file", "--filters", f"{base}:{path}")


def classify(base: str) -> dict[str, list[str]]:
    """分類ごとの経路の一覧を返す。**作業ツリー・索引を変えない。**"""
    tree = base_tree(base)
    result: dict[str, list[str]] = {name: [] for name in (*STOP_CLASSES, *PASS_CLASSES)}

    result[TRACKED] = [
        line for line in _git("status", "--porcelain", "--untracked-files=no").decode("utf-8", "replace").splitlines()
        if line.strip()
    ]

    untracked = _nul_split(_git("ls-files", "-z", "--others", "--exclude-standard"))
    for path in untracked:
        if path not in tree:
            result[UNTRACKED_ABSENT].append(path)
        elif same_content(base, path, tree[path]):
            result[UNTRACKED_SAME].append(path)
        else:
            result[UNTRACKED_DIFF].append(path)

    # 無視されたものは列挙しない。起点の木 − 索引 − 無視されていない未追跡 のうち手元に在るものだけ。
    index = set(_nul_split(_git("ls-files", "-z")))
    seen = set(untracked)
    for path in sorted(p for p in tree if p not in index and p not in seen and os.path.lexists(p)):
        if same_content(base, path, tree[path]):
            result[IGNORED_SAME].append(path)
        else:
            result[IGNORED_DIFF].append(path)
    return result


def report(base: str, result: dict[str, list[str]]) -> bool:
    """分類を表示し、通すなら True。経路は出すが中身は出さない。"""
    head = _git("rev-parse", "--short", base).decode().strip()
    stop = any(result[name] for name in STOP_CLASSES)
    print(f"{PREFIX} 分類（比較先 {base} {head}）")
    for name in (TRACKED, UNTRACKED_SAME, UNTRACKED_DIFF, UNTRACKED_ABSENT, IGNORED_SAME, IGNORED_DIFF):
        note = "（通す）" if name in PASS_CLASSES else ""
        print(f"{PREFIX}   {name}: {len(result[name])} 件{note}")
    print(f"{PREFIX}   {IGNORED_ABSENT}: 数えない（触れない）")
    if not stop:
        print(f"{PREFIX} 分類: 通す")
        return True
    for name in STOP_CLASSES:
        for path in result[name]:
            print(f"{PREFIX}   止めた理由 [{name}] {path}")
    print(f"{PREFIX} 起点に無いと分類で確かめた経路は、無視の一覧（.git/info/exclude）に足せば切り替えで触れられない。"
          "起点に在る経路は無視の一覧で隠さない（中身が違うと切り替えで黙って上書きされる）")
    print(f"{PREFIX} 分類: 止める")
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="契約の開始の前に作業ツリーの汚れを起点と比べて分類する（読み取りだけ）")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"比べる起点（既定 {DEFAULT_BASE}）")
    parser.add_argument("--adopt-list", help="通す経路（中身が同じ未追跡と無視されたもの）を NUL 区切りで書くファイル")
    args = parser.parse_args(argv)
    try:
        os.chdir(_git("rev-parse", "--show-toplevel").decode().strip())
        result = classify(args.base)
        passed = report(args.base, result)
    except GitError as exc:
        print(f"{PREFIX} 分類のための git の照会に失敗しました: {exc}", file=sys.stderr)
        return 4
    if passed and args.adopt_list:
        adopt = result[UNTRACKED_SAME] + result[IGNORED_SAME]
        with open(args.adopt_list, "wb") as f:
            f.write(b"".join(os.fsencode(p) + b"\0" for p in adopt))
    return 0 if passed else 3


if __name__ == "__main__":
    sys.exit(main())

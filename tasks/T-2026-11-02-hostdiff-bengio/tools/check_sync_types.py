"""Task F-2: 本契約が repo に書いたファイルに、同期の型（.stglobalignore で `!` の規則に当たるもの）が無いことを確かめる（完了判定 f）。

規則は Syncthing の読み方で当てる: 先に当たった行が勝つ。`!` で始まる行は同期する、それ以外の行は同期しない。
`/` を含まない型は任意の階層の名前に当たる。`**` は任意の階層、`*` は一つの階層の中。ディレクトリに当たった型はその中身にも当たる。
対象は phase0 との差に現れる経路（`git diff --name-only origin/phase0 HEAD`）と、本契約の置き場の未追跡のファイル。
--selftest: `experiments/x/foo.npy` が「同期する」に当たり、`experiments/x/foo.json` が当たらないことを示す。

    python check_sync_types.py <out.json> [--selftest]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIRS = ["experiments/phase1/stage1_ptower_hostdiff_bengio", "experiments/baselines/stage1_dtower_hostdiff_bengio",
        "experiments/analysis/hostdiff_andrew_bengio/bengio", "tasks/T-2026-11-02-hostdiff-bengio"]


def compile_rule(line):
    include = line.startswith("!")
    pat = line[1:] if include else line
    anchored = "/" in pat
    rx = ""
    i = 0
    while i < len(pat):
        if pat.startswith("**/", i):
            rx, i = rx + "(?:.*/)?", i + 3
        elif pat.startswith("**", i):
            rx, i = rx + ".*", i + 2
        elif pat[i] == "*":
            rx, i = rx + "[^/]*", i + 1
        elif pat[i] == "?":
            rx, i = rx + "[^/]", i + 1
        elif pat[i] == "[":
            j = pat.index("]", i)
            rx, i = rx + pat[i:j + 1], j + 1
        else:
            rx, i = rx + re.escape(pat[i]), i + 1
    rx = ("^" if anchored else "^(?:.*/)?") + rx + "(?:/.*)?$"
    return line, include, re.compile(rx)


def rules():
    lines = [ln.strip() for ln in (ROOT / ".stglobalignore").read_text().splitlines()]
    return [compile_rule(ln) for ln in lines if ln and not ln.startswith("//")]


def synced(path, rs):
    for line, include, rx in rs:
        if rx.match(path):
            return include, line
    return False, None


def targets():
    diff = subprocess.run(["git", "-C", str(ROOT), "--no-pager", "diff", "--name-only", "origin/phase0", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard", "--", *DIRS],
                               capture_output=True, text=True, check=True).stdout.split()
    return sorted(set(diff) | set(untracked))


def main():
    rs = rules()
    if "--selftest" in sys.argv:
        print(json.dumps({p: synced(p, rs) for p in ["experiments/x/foo.npy", "experiments/x/foo.json"]}))
        return
    paths = targets()
    hits = [{"path": p, "rule": r} for p in paths for s, r in [synced(p, rs)] if s]
    res = {"n_paths": len(paths), "n_sync_type": len(hits), "sync_type": hits}
    Path(sys.argv[1]).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: res[k] for k in ("n_paths", "n_sync_type")}), hits[:5])


if __name__ == "__main__":
    main()

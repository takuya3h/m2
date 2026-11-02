"""前後比較用の木の要約値（T-2026-11-02-bengio-andrew-env-survey、Task A-6 と G-1）。

読むだけ。記号リンクはたどらない（リンクそのものの先を記録する）。各項目について
(相対経路, 種類, バイト数, mtime_ns, リンク先) を並べた列の sha256 を出す。中身の sha256 は取らない
（中身の照合は Task D の道具と reldetr_digest.py が行う）。

    python3 -B stat_tree.py <名前>=<経路> ... [--exclude <相対経路の先頭>]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys


def walk(root: str, excludes: list[str]):
    rows = []
    if not os.path.lexists(root):
        return None
    if os.path.islink(root) or not os.path.isdir(root):
        st = os.lstat(root)
        link = os.readlink(root) if os.path.islink(root) else ""
        return [(".", "l" if link else "f", st.st_size, st.st_mtime_ns, link)]
    for dp, dns, fns in os.walk(root, followlinks=False):
        rel_dp = os.path.relpath(dp, root)
        dns[:] = sorted(d for d in dns if not any(os.path.normpath(os.path.join(rel_dp, d)).startswith(e) for e in excludes))
        for n in sorted(dns + fns):
            p = os.path.join(dp, n)
            r = os.path.normpath(os.path.join(rel_dp, n))
            if any(r.startswith(e) for e in excludes):
                continue
            st = os.lstat(p)
            if os.path.islink(p):
                rows.append((r, "l", st.st_size, st.st_mtime_ns, os.readlink(p)))
            elif os.path.isdir(p):
                rows.append((r, "d", 0, st.st_mtime_ns, ""))
            else:
                rows.append((r, "f", st.st_size, st.st_mtime_ns, ""))
    return rows


def main():
    args = sys.argv[1:]
    excludes = []
    if "--exclude" in args:
        i = args.index("--exclude")
        excludes = args[i + 1].split(",")
        args = args[:i] + args[i + 2:]
    out = {}
    for a in args:
        name, path = a.split("=", 1)
        rows = walk(path, excludes)
        if rows is None:
            out[name] = {"path": path, "exists": False}
            continue
        files = [r for r in rows if r[1] == "f"]
        out[name] = {"path": path, "exists": True, "entries": len(rows), "files": len(files),
                     "bytes": sum(r[2] for r in files),
                     "stat_tree_sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest()}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

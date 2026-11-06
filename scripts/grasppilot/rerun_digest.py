"""禁止の場所の要約値の取得と開始時・終了時の比べ（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task A-7・E-1）。

読むだけ。全ファイルの内容の sha256 を取り、根ごとに「相対経路・大きさ・sha256」の表と木の要約値を残す。
シンボリックリンクは辿らず、リンク先の文字列を記録する。

    python scripts/grasppilot/rerun_digest.py snapshot --out DIR --root 名前=経路 [--root ...] [--skip-dir 名前 ...]
    python scripts/grasppilot/rerun_digest.py compare --a DIR_開始 --b DIR_終了 [--allow-added 名前:接頭辞 ...] [--out FILE]

compare は、開始の表に在るファイルの内容が変わった・消えたものを違反とし、終了にだけ在るファイルは
``--allow-added`` の接頭辞（名前:根からの相対）に当たるものだけ許す。許さないもの（想定外の追加）も数える。
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def walk(root: Path, skip_dirs: set[str]):
    for dp, dns, fns in os.walk(root, followlinks=False):
        dns[:] = sorted(d for d in dns if d not in skip_dirs)
        for d in list(dns):  # ディレクトリのリンクは辿らず、リンクとして記録する
            if os.path.islink(os.path.join(dp, d)):
                dns.remove(d)
                yield os.path.join(dp, d), True
        for fn in sorted(fns):
            yield os.path.join(dp, fn), os.path.islink(os.path.join(dp, fn))


def snapshot_root(name: str, root: Path, skip_dirs: set[str], workers: int) -> dict:
    entries = list(walk(root, skip_dirs))
    rows: dict[str, tuple[str, str]] = {}

    def one(item):
        p, is_link = item
        rel = os.path.relpath(p, root)
        try:
            if is_link:
                return rel, ("L", "->" + os.readlink(p))
            st = os.stat(p)
            return rel, (str(st.st_size), file_sha256(p))
        except OSError as e:  # 読めないものは握りつぶさず、その旨を行に残す
            return rel, ("ERR", type(e).__name__)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for rel, val in ex.map(one, entries):
            rows[rel] = val
    lines = [f"{rel}\t{rows[rel][0]}\t{rows[rel][1]}" for rel in sorted(rows)]
    tree = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    return {"name": name, "root": str(root), "n_files": len(lines), "n_err": sum(1 for r in rows.values() if r[0] == "ERR"),
            "tree_sha256": tree, "lines": lines}


def cmd_snapshot(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for spec in a.root:
        name, _, path = spec.partition("=")
        r = snapshot_root(name, Path(path), set(a.skip_dir or []), a.workers)
        with gzip.open(out / f"{name}.tsv.gz", "wt") as f:
            f.write("\n".join(r.pop("lines")) + "\n")
        summary[name] = r
        print(json.dumps(r), flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))


def load(d: Path, name: str) -> dict[str, tuple[str, str]]:
    rows = {}
    with gzip.open(d / f"{name}.tsv.gz", "rt") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln:
                continue
            rel, size, sha = ln.split("\t")
            rows[rel] = (size, sha)
    return rows


def compare_rows(ra: dict, rb: dict, allow_prefixes: list[str]) -> dict:
    changed = sorted(k for k in ra if k in rb and ra[k] != rb[k])
    removed = sorted(k for k in ra if k not in rb)
    added = sorted(k for k in rb if k not in ra)
    allowed = [k for k in added if any(k == p or k.startswith(p.rstrip("/") + "/") for p in allow_prefixes)]
    unexpected = [k for k in added if k not in set(allowed)]
    return {"n_a": len(ra), "n_b": len(rb), "changed": len(changed), "removed": len(removed), "added": len(added),
            "added_allowed": len(allowed), "added_unexpected": len(unexpected),
            "examples": {"changed": changed[:10], "removed": removed[:10], "added_unexpected": unexpected[:10]}}


def cmd_compare(a):
    da, db = Path(a.a), Path(a.b)
    sa = json.loads((da / "summary.json").read_text())
    allow: dict[str, list[str]] = {}
    for s in a.allow_added or []:
        n, _, pre = s.partition(":")
        allow.setdefault(n, []).append(pre)
    res = {}
    for name in sa:
        res[name] = compare_rows(load(da, name), load(db, name), allow.get(name, []))
    viol = sum(v["changed"] + v["removed"] + v["added_unexpected"] for v in res.values())
    res = {"roots": res, "violations": viol}
    txt = json.dumps(res, indent=1, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(txt)
    print(txt)
    return 0 if viol == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--out", required=True)
    s.add_argument("--root", action="append", required=True)
    s.add_argument("--skip-dir", action="append")
    s.add_argument("--workers", type=int, default=16)
    c = sub.add_parser("compare")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--allow-added", action="append")
    c.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "snapshot":
        cmd_snapshot(a)
        return 0
    return cmd_compare(a)


if __name__ == "__main__":
    sys.exit(main())

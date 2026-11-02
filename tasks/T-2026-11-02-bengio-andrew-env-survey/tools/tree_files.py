"""Relation-DETR の作業場所のファイル単位の表（T-2026-11-02-bengio-andrew-env-survey、Task B）。

読むだけ。結果は標準出力（JSON）。andrew では ``ssh andrew 'python3 -B -I - <root>' < この台本`` で回し、何も書かない。
除外の規則は ``scripts/grasppilot/reldetr_digest.py`` と同じ（最上位の SKIP_TOP と、``__pycache__`` を含む経路）。

- ``included``: 除外に当たらない全ファイル（相対経路 → [バイト数, sha256, mtime]）
- ``excluded``: 除外に当たるファイルを最上位（または ``__pycache__``）ごとに集計（件数・バイト数）。
  ``--hash-top`` に挙げた最上位だけはファイルごとの [バイト数, sha256, mtime] も出す
記号リンクはたどらない（リンクは ``links`` に先を書く）。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

SKIP_TOP = {"experiments", "third_party", "checkpoints", "per_class_coco_map", "data", "outputs", "work_dirs", ".git"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    root = sys.argv[1]
    hash_top = set(sys.argv[sys.argv.index("--hash-top") + 1].split(",")) if "--hash-top" in sys.argv else set()
    included, excluded, hashed, links = {}, {}, {}, {}
    for dp, dns, fns in os.walk(root, followlinks=False):
        dns.sort()
        for n in sorted(fns + [d for d in dns if os.path.islink(os.path.join(dp, d))]):
            p = os.path.join(dp, n)
            r = os.path.relpath(p, root)
            parts = r.split(os.sep)
            if os.path.islink(p):
                links[r] = os.readlink(p)
                continue
            st = os.lstat(p)
            if parts[0] in SKIP_TOP or "__pycache__" in parts:
                key = parts[0] if parts[0] in SKIP_TOP else "__pycache__"
                e = excluded.setdefault(key, [0, 0])
                e[0] += 1
                e[1] += st.st_size
                if key in hash_top:
                    hashed[r] = [st.st_size, sha256(p), int(st.st_mtime)]
                continue
            included[r] = [st.st_size, sha256(p), int(st.st_mtime)]
    print(json.dumps({"root": root, "included": included, "excluded": excluded, "hashed_excluded": hashed,
                      "links": links}, ensure_ascii=False))


if __name__ == "__main__":
    main()

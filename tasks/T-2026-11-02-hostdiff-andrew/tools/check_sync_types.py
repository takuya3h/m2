"""Task F-2: 本契約が書いた場所に、同期の型（``.stignore`` の ``!experiments/**/<X>``）に当たるファイルが無いかを数える（読むだけ）。

照合: ``experiments/`` より下の経路の各段（ディレクトリ名とファイル名）のどれかが ``<X>`` に
fnmatch で当たれば「当たる」。数える対象は、本契約の三つの置き場の下の全ファイル（追跡・未追跡を問わない）と、
``origin/phase0`` から本分岐で増えた・変わった全ファイル。

``--self-test`` は ``experiments/x/foo.npy`` と ``experiments/x/a.json`` を照合し、前者だけが当たることを確かめる。

    python3 tasks/T-2026-11-02-hostdiff-andrew/tools/check_sync_types.py [--self-test]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLACES = ["experiments/phase1/stage1_ptower_hostdiff_andrew", "experiments/baselines/stage1_dtower_hostdiff_andrew",
          "experiments/analysis/hostdiff_andrew_bengio/andrew"]


def patterns():
    out = []
    for line in (ROOT / ".stignore").read_text().splitlines():
        if line.startswith("!experiments/**/"):
            out.append(line[len("!experiments/**/"):])
    return out


def hits(path, pats):
    parts = Path(path).parts
    if not parts or parts[0] != "experiments":
        return []
    return [p for p in pats if any(fnmatch.fnmatchcase(c, p) for c in parts[1:])]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    pats = patterns()
    if args.self_test:
        print(json.dumps({"patterns": pats, "experiments/x/foo.npy": hits("experiments/x/foo.npy", pats),
                          "experiments/x/a.json": hits("experiments/x/a.json", pats)}, ensure_ascii=False))
        return
    files = {str(p.relative_to(ROOT)) for place in PLACES for p in (ROOT / place).rglob("*") if p.is_file()}
    changed = subprocess.check_output(["git", "diff", "--name-only", "origin/phase0...HEAD"], cwd=ROOT, text=True).split()
    files |= set(changed)
    found = {f: hits(f, pats) for f in sorted(files) if hits(f, pats)}
    print(json.dumps({"patterns": pats, "files_checked": len(files), "hits": found, "hit_count": len(found)},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

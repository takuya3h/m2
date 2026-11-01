"""Relation-DETR の作業場所の中身の要約値（非公式 T-2026-11-01-grasp-pilot-d、Task A-5）。

読むだけ。結果は標準出力（JSON）に出す。andrew では ``ssh andrew python3 - --root <dir> < この台本`` の形で回し、
andrew に何も書かない。

- ``source_tree_sha256``: ``scripts/stage2pilot/input_digest.py`` と同じ規則（.py .cu .cuh .cpp .h、
  experiments・入れ子の third_party・checkpoints などを除く）。前回の記録の値と比べられる
- ``all_tree_sha256``: 同じ除外で、拡張子を問わない全ファイル
- ``--venv``: その仮想環境の python で ``importlib.metadata`` から「名前（小文字）==版」を名前の順に並べた列の sha256

    python3 scripts/grasppilot/reldetr_digest.py --root <Relation-DETR> [--venv <venv>] [--files]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

SRC_SUFFIX = {".py", ".cu", ".cuh", ".cpp", ".h"}
SKIP_TOP = {"experiments", "third_party", "checkpoints", "per_class_coco_map", "data", "outputs", "work_dirs", ".git"}
PKG_CMD = ("import importlib.metadata as m; "
           "print('\\n'.join(sorted({d.metadata['Name'].lower() + '==' + d.version for d in m.distributions()})))")


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tree(root: Path, suffixes):
    files = {}
    for f in sorted(root.rglob("*")):
        r = f.relative_to(root)
        if r.parts[0] in SKIP_TOP or "__pycache__" in r.parts or not f.is_file():
            continue
        if suffixes is not None and f.suffix not in suffixes:
            continue
        files[str(r)] = sha256(f)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--venv", default=None)
    ap.add_argument("--files", action="store_true", help="ファイルごとの sha256 も出す")
    a = ap.parse_args()
    root = Path(a.root)
    src = tree(root, SRC_SUFFIX)
    every = tree(root, None)
    res = {"root": str(root),
           "source_files": len(src),
           "source_tree_sha256": hashlib.sha256(json.dumps(src, sort_keys=True).encode()).hexdigest(),
           "all_files": len(every),
           "all_tree_sha256": hashlib.sha256(json.dumps(every, sort_keys=True).encode()).hexdigest()}
    if a.files:
        res["all_file_sha256"] = every
    if a.venv:
        py = Path(a.venv) / "bin" / "python"
        out = subprocess.run([str(py), "-c", PKG_CMD], capture_output=True, text=True)
        lines = out.stdout.strip()
        ver = subprocess.run([str(py), "-c", "import sys; print(sys.version.split()[0])"], capture_output=True, text=True)
        res["venv"] = {"path": a.venv, "python_link": str(py.resolve()), "python_version": ver.stdout.strip(),
                       "returncode": out.returncode, "packages": len(lines.splitlines()) if lines else 0,
                       "packages_sha256": hashlib.sha256(lines.encode()).hexdigest()}
        if a.files:
            res["venv"]["package_list"] = lines.splitlines()
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

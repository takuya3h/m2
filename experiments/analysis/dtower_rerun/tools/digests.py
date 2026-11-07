"""Summary values of the places T-2026-11-07-dtower-rerun must leave unchanged (SPEC §6 の 2・3・4).

Copied from T-2026-11-06-dtower-batch-search; only the list of roots differs. A root may be an
absolute path (the earlier contract's store outside the repo).

Every file under each root is hashed by content (sha256), then the sorted list of
(relative path, size, content sha256) is hashed again. A changed, added or removed file
changes the root's value. The two virtual environments are summarised by the sorted
``uv pip freeze`` list and by the same content walk of their site-packages.

    python digests.py --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ROOTS = [
    "third_party",
    "data/raw/ego",
    "data/raw/OpenSurgery_Dataset/01_frames/initial_videos",
    "data/external",
    "data/annotations/egosurgery_tool_folds",
    "data/splits",
    "data/processed/phase_manifest_all_phase",
    "scripts",
    "configs",
    "experiments/analysis/tower_reselect_search_dlsta",
    "experiments/analysis/tower_batch_probe",
    "experiments/analysis/dtower_step_profile",
    "experiments/analysis/dtower_batch_search",
    "experiments/baselines/stage1_dtower_search",
    "experiments/baselines/stage1_dtower_batch",
    "experiments/baselines/stage1_dtower_r2",
    "tasks/T-2026-11-06-dtower-batch-search",
    "tasks/T-2026-10-22-tower-reselect-search-dlsta",
    "tasks/T-2026-11-06-tower-batch-probe",
    "tasks/T-2026-11-06-dtower-step-profile",
    "/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-batch-search",
]
FROZEN = "third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth"
VENVS = [".venv", ".venv-relation-detr"]


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def walk(path):
    path = Path(path)
    if path.is_file():
        return [(path.name, path.stat().st_size, file_sha(path))]
    rows = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()
        for name in sorted(filenames):
            full = Path(dirpath) / name
            if full.is_symlink():
                rows.append((str(full.relative_to(path)), -1, "symlink:" + os.readlink(full)))
            elif full.is_file():
                rows.append((str(full.relative_to(path)), full.stat().st_size, file_sha(full)))
    return rows


def summary(rows):
    return {"files": len(rows), "bytes": sum(r[1] for r in rows if r[1] > 0),
            "sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    result = {"roots": {}, "venvs": {}}
    for rel in ROOTS:
        result["roots"][rel] = summary(walk(Path(rel) if rel.startswith("/") else ROOT / rel))
    result["frozen_source"] = {"path": FROZEN, "sha256": file_sha(ROOT / FROZEN),
                               "bytes": (ROOT / FROZEN).stat().st_size}
    for venv in VENVS:
        freeze = subprocess.run(["uv", "pip", "freeze", "--python", str(ROOT / venv / "bin/python")],
                                capture_output=True, text=True, check=True).stdout
        lines = sorted(line for line in freeze.splitlines() if line.strip())
        site = next((ROOT / venv / "lib").glob("python*/site-packages"))
        result["venvs"][venv] = {"freeze_lines": len(lines),
                                 "freeze_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest(),
                                 "site_packages": summary(walk(site))}
    Path(args.out).write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()

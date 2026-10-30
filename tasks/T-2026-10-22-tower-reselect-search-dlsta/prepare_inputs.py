"""Lock the user-approved existing-plus-supplement images, without copying images."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "experiments/analysis/tower_reselect_search_dlsta"
MANIFEST = ROOT / "data/processed/phase_manifest_all_phase"
LOCK = ANALYSIS / "image_input_lock.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actual(row):
    return {key: sha(ROOT / row[key]) for key in ("selected", "counterpart") if row.get(key)}


def verify(path):
    if path.resolve() == LOCK.resolve():
        summary = json.loads((ANALYSIS / "manifest_summary.json").read_text())
        if sha(path) != summary["input_lock_sha256"]:
            raise RuntimeError("Input lock itself changed")
        if {p.name: sha(p) for p in MANIFEST.glob("*.json")} != summary["manifest_sha256"]:
            raise RuntimeError("Search manifest changed")
    rows = json.loads(path.read_text())
    with ThreadPoolExecutor(max_workers=12) as pool:
        failed = [row["frame"] for row, hashes in zip(rows, pool.map(actual, rows), strict=True)
                  if hashes != row["sha256"]]
    if failed:
        raise RuntimeError(f"Locked image changed: {failed[:5]} ({len(failed)} total)")
    print(f"INPUT_LOCK_PASS frames={len(rows)}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
        return
    if LOCK.exists():
        raise FileExistsError("Input lock already exists; verify it instead")
    old = {p.name: sha(p) for p in (ROOT / "data/processed/phase_manifest").glob("*.json")}
    subprocess.run([sys.executable, str(ROOT / "scripts/build_phase_manifest.py"),
                    "--fallback-root", str(ROOT / "data/raw/OpenSurgery_Dataset/01_frames/initial_videos"),
                    "--out-dir", str(MANIFEST)], check=True)
    previous = {r["raw"]: r for r in json.loads((ANALYSIS / "image_overlap.json").read_text())["mismatches"]}
    rows, counts, video_counts = [], {}, Counter()
    for split in ("train", "val", "test"):
        manifest = json.loads((MANIFEST / f"{split}.json").read_text())
        counts[split] = manifest["num_frames"]
        for clip in manifest["clips"]:
            for frame in clip["frames"]:
                selected = frame["image_path"]
                counterpart = None
                if selected.startswith("data/raw/ego/"):
                    counterpart = str(Path("data/raw/OpenSurgery_Dataset/01_frames/initial_videos")
                                      / frame["frame"].rsplit("_", 1)[0] / (frame["frame"] + ".jpg"))
                rows.append({"frame": frame["frame"], "selected": selected,
                             "counterpart": counterpart})
                video_counts[clip["video"]] += 1
    with ThreadPoolExecutor(max_workers=12) as pool:
        for row, hashes in zip(rows, pool.map(actual, rows), strict=True):
            row["sha256"] = hashes
            if row["counterpart"]:
                known = previous.get(row["selected"])
                if known:
                    if hashes != {"selected": known["raw_sha256"], "counterpart": known["distributed_sha256"]}:
                        raise RuntimeError("Known image mismatch changed")
                elif hashes["selected"] != hashes["counterpart"]:
                    raise RuntimeError("New image mismatch")
    supplement = sum(r["counterpart"] is None for r in rows)
    if len(rows) != 17233 or len({r["frame"] for r in rows}) != 17233 or supplement != 1796:
        raise RuntimeError(f"Unexpected frame set: {len(rows)=}, {supplement=}")
    if counts["train"] % 16 == 1:
        raise RuntimeError("Train remainder cannot start the two-GPU path")
    if old != {p.name: sha(p) for p in (ROOT / "data/processed/phase_manifest").glob("*.json")}:
        raise RuntimeError("Original manifest changed")
    LOCK.write_text(json.dumps(rows, ensure_ascii=False) + "\n")
    summary = {"total": len(rows), "raw": len(rows) - supplement, "supplement": supplement,
               "counts": counts, "train_remainder_16": counts["train"] % 16,
               "video_counts": dict(video_counts), "original_manifest_sha256": old,
               "manifest_sha256": {p.name: sha(p) for p in MANIFEST.glob("*.json")},
               "input_lock_sha256": sha(LOCK)}
    (ANALYSIS / "manifest_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()

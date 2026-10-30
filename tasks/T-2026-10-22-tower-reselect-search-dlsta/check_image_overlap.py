"""Reproduce the contract's byte-identity check without changing either image set."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/analysis/tower_reselect_search_dlsta/image_overlap.json"


def compare(raw):
    distributed = (ROOT / "data/raw/OpenSurgery_Dataset/01_frames/initial_videos"
                   / raw.stem.rsplit("_", 1)[0] / raw.name)
    raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    distributed_hash = (hashlib.sha256(distributed.read_bytes()).hexdigest()
                        if distributed.is_file() else None)
    return {"raw": str(raw.relative_to(ROOT)),
            "distributed": str(distributed.relative_to(ROOT)),
            "exists": distributed.is_file(), "same": raw_hash == distributed_hash,
            "raw_sha256": raw_hash, "distributed_sha256": distributed_hash}


def main():
    videos = {f"{i:02d}" for i in range(1, 16)}
    paths = sorted(p for p in (ROOT / "data/raw/ego").rglob("*.jpg")
                   if p.name[:2] in videos and "other" not in p.parts[-3])
    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(compare, paths))
    report = {"count": len(rows), "missing": sum(not r["exists"] for r in rows),
              "different": sum(not r["same"] for r in rows),
              "mismatches": [r for r in rows if not r["same"]]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("count", "missing", "different")}))
    return int(report["count"] != 15437 or report["different"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())

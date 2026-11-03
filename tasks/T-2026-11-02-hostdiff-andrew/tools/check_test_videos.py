"""Task F-1: 学習と評価に通した動画の集合と、折り A の test 動画（04・05・07）の共通を数える（読むだけ）。

- 検出塔: 学習は ``instances_train.json``、評価は ``DTOWER_EVAL_SPLIT`` の ``instances_<split>.json``
  （各 run の command.sh から読む）。動画は注釈の ``file_name`` の 2 段目
- 工程塔: fine-tune と評価は config.yaml の ``data.videos`` の train・val。特徴は
  ``feature_audit.json`` の ``video_counts``（ヘッドはこの特徴だけを読む）

``--self-test`` は検出塔の集合に 04 を足し、共通が 1 になることを確かめる。

    python3 tasks/T-2026-11-02-hostdiff-andrew/tools/check_test_videos.py [--self-test]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRATCH = Path.home() / "m2-scratch/T-2026-11-02-hostdiff-andrew"
ANN = ROOT / "data/annotations/egosurgery_tool_folds/A"
PHASE = ROOT / "experiments/phase1/stage1_ptower_hostdiff_andrew"
TEST = {"04", "05", "07"}


def ann_videos(split):
    images = json.loads((ANN / f"instances_{split}.json").read_text())["images"]
    return {img["file_name"].split("/")[1] for img in images}


def detector_sets():
    out = {}
    for run in ("seed42a", "seed42b", "seed123"):
        work = SCRATCH / "detector" / run
        splits = {"train"}  # 学習の集合
        for cmd in ["train", "eval_val", "eval_train"]:
            text = (work / f"{cmd}.command.sh").read_text()
            m = re.search(r"DTOWER_EVAL_SPLIT=(\w+)", text)
            splits.add(m.group(1) if m else "val")  # 設定の既定は val
        out[run] = {"splits": sorted(splits), "videos": sorted(set().union(*(ann_videos(s) for s in splits)))}
    return out


def phase_sets():
    import yaml
    out = {}
    for run in sorted(PHASE.iterdir()):
        cfg = yaml.safe_load((run / "config.yaml").read_text())
        vids = set()
        videos = (cfg.get("data") or {}).get("videos")
        if videos:
            vids |= set(videos["train"]) | set(videos["val"])
        audit = run / "feature_audit.json"
        if audit.exists():
            vids |= set(json.loads(audit.read_text())["video_counts"])
        if vids:
            out[run.name] = sorted(vids)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    det, ph = detector_sets(), phase_sets()
    if args.self_test:
        det["seed42a"]["videos"] = sorted(set(det["seed42a"]["videos"]) | {"04"})
    common = {f"detector.{k}": sorted(TEST & set(v["videos"])) for k, v in det.items()}
    common.update({f"phase.{k}": sorted(TEST & set(v)) for k, v in ph.items()})
    total = sum(len(v) for v in common.values())
    print(json.dumps({"test_videos": sorted(TEST), "detector": det, "phase_runs_checked": len(ph),
                      "phase_videos": sorted(set().union(*map(set, ph.values()))),
                      "common_nonzero": {k: v for k, v in common.items() if v}, "common_total": total,
                      "self_test": args.self_test}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

"""Task D-8 / 完了判定 n: test の動画を、信号の作成・学習・評価に通していないことを示す（非公式 T-2026-10-18-stage2-pilot-folda）。

各段で実際に通した動画の集合を、記録ではなく実体（信号ファイルの frame_ids、評価と学習に渡した注釈の画像、
DP の run の config に残る動画）から集め、{04, 05, 07} との共通の件数を数える。
--inject 04 を渡すと、各段の集合に 04 を混ぜた入力で同じ検査を行う（共通が 1 件になることの確認）。

    python scripts/stage2pilot/test_audit.py --out <json> [--inject 04]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402


def videos_of_npz(path):
    with np.load(path) as d:
        return {C.video_of(str(f)) for f in d["frame_ids"]}


def videos_of_ann(path):
    blob = json.loads(Path(path).read_text())
    return {Path(im["file_name"]).parent.name for im in blob["images"]}


def collect():
    stages = {}
    for p in sorted(glob.glob(str(C.STORE / "signals/**/*.npz"), recursive=True)):
        stages.setdefault("信号の作成（STORE/signals）", set()).update(videos_of_npz(p))
    for p in sorted(glob.glob(str(C.STORE / "arms/**/*.npz"), recursive=True)):
        stages.setdefault("腕の信号（STORE/arms）", set()).update(videos_of_npz(p))
    for p in ("instances_train.json", "instances_val.json"):
        stages.setdefault("PD の学習と評価の注釈（折り A の train と val）", set()).update(videos_of_ann(C.DET_ANN_A / p))
    for p in sorted(glob.glob(str(C.STORE / "ann_cf/*/instances_*.json"))):
        stages.setdefault("検出の交差適合用の塔の注釈", set()).update(videos_of_ann(p))
    for p in sorted(glob.glob(str(C.STORE / "cf_ptower/*/all_gap.npz"))):
        stages.setdefault("工程の交差適合用の塔の特徴", set()).update(videos_of_npz(p))
    for p in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_dp_*/config.yaml")):
        cfg = yaml.safe_load(p.read_text())
        v = cfg.get("videos", {})
        stages.setdefault("DP の学習と評価（run の config）", set()).update(v.get("train", []) + v.get("val", []))
    for p in sorted((C.ANALYSIS / "identity").glob("*.json")):
        d = json.loads(p.read_text())
        if "videos" in d:
            stages.setdefault("恒等性と陽性対照の評価", set()).update(d["videos"])
    for p in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_cf_ptower_*/config.yaml")):
        cfg = yaml.safe_load(p.read_text())
        stages.setdefault("工程の交差適合用の塔の学習（run の config）", set()).update(
            cfg.get("crossfit", {}).get("train_videos", []))
    return stages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--inject", default=None)
    a = ap.parse_args()
    stages = collect()
    if a.inject:
        stages = {k: v | {a.inject} for k, v in stages.items()}
    rows = {k: {"videos": sorted(v), "common_with_test": sorted(v & C.TEST_VIDEOS)} for k, v in stages.items()}
    union = set().union(*stages.values()) if stages else set()
    res = {"task_id": C.TASK_ID, "inject": a.inject, "test_videos": sorted(C.TEST_VIDEOS), "stages": rows,
           "union": sorted(union), "common_total": len(union & C.TEST_VIDEOS)}
    C.write_json(a.out, res)
    for k, r in rows.items():
        print(f"{k}: {len(r['videos'])} 本 共通 {len(r['common_with_test'])}")
    print(f"全体の共通 {res['common_total']} 件 {sorted(union & C.TEST_VIDEOS)}")


if __name__ == "__main__":
    main()

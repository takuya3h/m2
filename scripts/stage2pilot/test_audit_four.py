"""完了判定 l / G3: test の動画を、信号の作成・学習・評価に通していないことを示す（非公式 T-2026-10-19-stage2-pilot-four-new-types）。

本契約の各段で実際に通した動画の集合を、実体（run が読んだ信号ファイルの frame_ids、学習と評価に渡した注釈の画像、
DP と K3 の run の config に残る動画、見落としの集合と D* の train の出力の記録、恒等性・再現・殺し実験の評価の記録）から集め、
{04, 05, 07} との共通の件数を数える。--inject 04 を渡すと、各段の集合に 04 を混ぜた入力で同じ検査を行う（共通が 1 件になることの確認）。

    python scripts/stage2pilot/test_audit_four.py --out <json> [--inject 04]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot.test_audit import videos_of_ann, videos_of_npz  # noqa: E402

TASK_ID = "T-2026-10-19-stage2-pilot-four-new-types"
PHASE1 = C.ROOT / "experiments/phase1"
ANA = C.ROOT / "experiments/analysis/stage2_pilot_four"
FOUR = C.STORE.parent / TASK_ID


def collect():
    stages = {}

    def add(name, videos):
        stages.setdefault(name, set()).update(videos)

    for d in sorted(PHASE1.glob("stage2four_dp_*")):
        cfg = yaml.safe_load((d / "config.yaml").read_text())
        add("DP の学習と評価（run の config の動画）", cfg["videos"]["train"] + cfg["videos"]["val"])
        for f in cfg.get("signals_train", []) + cfg.get("signals_val", []):
            add("DP の run が読んだ信号ファイル", videos_of_npz(f["path"]))
    for d in sorted(PHASE1.glob("stage2four_k3_*")):
        cfg = yaml.safe_load((d / "config.yaml").read_text())
        add("K3 の GRU の学習と評価（run の config の動画）", cfg["videos"]["train"] + cfg["videos"]["val"])
        for f in cfg["signals"].values():
            add("K3 の GRU が読んだ信号ファイル", videos_of_npz(f["path"]))
    for d in sorted(PHASE1.glob("stage2four_pd_*")):
        sp = yaml.safe_load((d / "config.yaml").read_text())["stage2pilot"]
        for f in (sp["signal_train"], sp["signal_val"]):
            add("PD の run が読んだ信号ファイル", videos_of_npz(f))
        for part in ("train", "val"):
            add("PD の学習と評価の注釈（run の config の ann_dir）", videos_of_ann(Path(sp["ann_dir"]) / f"instances_{part}.json"))
        if sp.get("missed_set"):
            add("extra-queries の見落としの集合（run が読んだもの）", json.loads(Path(sp["missed_set"]).read_text())["videos"])
    for p in sorted(glob.glob(str(FOUR / "xq/*.meta.json"))):
        add("D* の train の出力（見落としの集合の元）", json.loads(Path(p).read_text())["videos"])
    for sub in ("identity", "repro", "xq", "kill"):
        for p in sorted((ANA / sub).glob("*.json")):
            d = json.loads(p.read_text())
            if isinstance(d.get("videos"), list):
                add(f"評価の記録（{sub}）", d["videos"])
            for arm in d.values() if isinstance(d, dict) else []:
                if isinstance(arm, dict) and isinstance(arm.get("signal_files"), list):
                    for f in arm["signal_files"]:
                        add(f"評価の記録が読んだ信号ファイル（{sub}）", videos_of_npz(f["path"]))
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
    res = {"task_id": TASK_ID, "inject": a.inject, "test_videos": sorted(C.TEST_VIDEOS), "stages": rows,
           "union": sorted(union), "common_total": len(union & C.TEST_VIDEOS)}
    C.write_json(a.out, res)
    for k, r in rows.items():
        print(f"{k}: {len(r['videos'])} 本 共通 {len(r['common_with_test'])}")
    print(f"全体の共通 {res['common_total']} 件 {sorted(union & C.TEST_VIDEOS)}")


if __name__ == "__main__":
    main()

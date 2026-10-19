"""完了判定 l / G3: test の動画を、信号の作成・学習・評価に通していないことを示す（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。

本契約の各段で実際に通した動画の集合を、記録ではなく実体（入れ替えた信号と対応表、run が読んだ信号ファイルの frame_ids、
評価と学習に渡した注釈の画像、DP の run の config に残る動画、恒等性と再現の評価の記録）から集め、{04, 05, 07} との共通の件数を数える。
--inject 04 を渡すと、各段の集合に 04 を混ぜた入力で同じ検査を行う（共通が 1 件になることの確認）。

    python scripts/stage2pilot/test_audit_fix.py --out <json> [--inject 04]
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

PHASE1 = C.ROOT / "experiments/phase1"
REMOTE_DIGEST = C.FIX_ANALYSIS / "bengio/input_digest_bengio.json"


def same_as_remote(path: Path) -> Path:
    """別ホスト（bengio）の run の注釈は andrew に無い。bengio の入力の照合の記録の sha256 が、andrew の同じ名前の注釈と
    一致するときだけ andrew の写しを返す。一致しなければ止まる（数えずに通さない）。"""
    remote = json.loads(REMOTE_DIGEST.read_text())["annotations"][path.name]
    local = C.DET_ANN_A / path.name
    if C.sha256(local) != remote:
        raise SystemExit(f"別ホストの注釈 {path} の sha256 が andrew の {local} と一致しない")
    return local


def collect():
    stages = {}

    def add(name, videos):
        stages.setdefault(name, set()).update(videos)

    for p in sorted(glob.glob(str(C.FIX_STORE / "signals/shuffle/*.npz"))):
        add("入れ替えた信号（FIX/signals/shuffle）", videos_of_npz(p))
    for p in sorted(glob.glob(str(C.FIX_STORE / "signals/shuffle/mapping_*.json"))):
        m = json.loads(Path(p).read_text())["mapping"]
        add("入れ替えの対応表（元と入れ替え先の両方）", {C.video_of(f) for f in list(m) + list(m.values())})
    for d in sorted(PHASE1.glob("stage2fix_dp_*")):
        cfg = yaml.safe_load((d / "config.yaml").read_text())
        add("DP の学習と評価（run の config の動画）", cfg["videos"]["train"] + cfg["videos"]["val"])
        for f in cfg.get("signals_train", []) + cfg.get("signals_val", []):
            add("DP の run が読んだ信号ファイル", videos_of_npz(f["path"]))
    for d in sorted(PHASE1.glob("stage2fix_pd_*")):
        sp = yaml.safe_load((d / "config.yaml").read_text())["stage2pilot"]
        for f in (sp["signal_train"], sp["signal_val"]):
            add("PD の run が読んだ信号ファイル", videos_of_npz(f))
        for part in ("train", "val"):
            ann = Path(sp["ann_dir"]) / f"instances_{part}.json"
            if ann.exists():
                add("PD の学習と評価の注釈（run の config の ann_dir）", videos_of_ann(ann))
            else:
                add("PD の学習と評価の注釈（別ホストの run。sha256 が同じ andrew の写しで数えた）", videos_of_ann(same_as_remote(ann)))
    for p in sorted((C.FIX_ANALYSIS / "identity").glob("*.json")) + sorted((C.FIX_ANALYSIS / "repro").glob("ptower_*.json")):
        d = json.loads(p.read_text())
        if "videos" in d:
            add("恒等性・陽性対照・塔単独の再現の評価", d["videos"])
    for part in ("val",):
        add("検出塔単独の再現の注釈（折り A の val）", videos_of_ann(C.DET_ANN_A / f"instances_{part}.json"))
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
    res = {"task_id": C.FIX_TASK_ID, "inject": a.inject, "test_videos": sorted(C.TEST_VIDEOS), "stages": rows,
           "union": sorted(union), "common_total": len(union & C.TEST_VIDEOS)}
    C.write_json(a.out, res)
    for k, r in rows.items():
        print(f"{k}: {len(r['videos'])} 本 共通 {len(r['common_with_test'])}")
    print(f"全体の共通 {res['common_total']} 件 {sorted(union & C.TEST_VIDEOS)}")


if __name__ == "__main__":
    main()

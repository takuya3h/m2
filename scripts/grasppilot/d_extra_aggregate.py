"""追加の測定の集計（非公式 T-2026-11-01-grasp-pilot-d、利用者の指示 2026-11-01。meta.amendments の 1 件目）。.venv で回す。

一本目の正解の腕を別の seed（123・456）と長い学習（案 B seed 42 の 12 epoch）で回した値を、bengio の塔単独との差（Δ塔）で並べる。
seed 42 の 4 epoch の値は一本目（andrew）の run を読む。ホストが違う値の差を処置の差として読まない。

    python scripts/grasppilot/d_extra_aggregate.py --out experiments/analysis/grasp_pilot_d/extra/report.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

M = Path("/home/ubuntu/slocal2/m2")
P = M / "experiments/phase1"
sys.path.insert(0, str(M / "scripts"))
from stage2pilot import det_metrics as DM  # noqa: E402

TEST_VIDEOS = {"04", "05", "07"}
REPRO = M / "experiments/analysis/grasp_pilot_d/repro/dtower_val_seed42.json"
PTOWER = M / "experiments/analysis/grasp_pilot_d/extra/ptower_val_bengio.json"
B_RUNS = {42: "grasppilot_pd_B_gt_ep4_seed42", 123: "grasppilot3x_pd_B_gt_ep4_seed123", 456: "grasppilot3x_pd_B_gt_ep4_seed456"}
A_RUNS = {42: "grasppilot_dp_002_GA_gt_ep4_seed42", 123: "grasppilot3x_dp_001_GA_gt_ep4_seed123",
          456: "grasppilot3x_dp_002_GA_gt_ep4_seed456"}
B_LONG = "grasppilot3x_pd_B_gt_ep12_seed42"


def read(path):
    return json.loads(Path(path).read_text())


def host(run):
    return (P / run / "server.txt").read_text().strip()


def group_ap(per_class: dict, names: list[str]):
    v = [per_class[c] for c in names if c in per_class and per_class[c] == per_class[c] and per_class[c] >= 0]
    return float(np.mean(v)) if v else None


def caseB_row(run, tower):
    m = read(P / run / "grasppilot_metrics.json")
    t = read(P / run / "t1b_result.json")
    st, en = (P / run / "start.txt").read_text().strip(), (P / run / "end.txt").read_text().strip()
    return {"run": run, "host": host(run), "seed": t["seed"], "epochs": t["epochs"], "result_epoch": m["result_epoch"],
            "mAP": m["AP"], "target_AP": m["target_AP"], "control_AP": m["control_AP"],
            "d_tower": {"mAP": m["AP"] - tower["mAP"], "target_AP": m["target_AP"] - tower["target_AP"],
                        "control_AP": m["control_AP"] - tower["control_AP"]},
            "init": m["init"], "init_equals_tower": abs(m["init"] - tower["mAP"]) < 1e-12,
            "per_video_AP": m["per_video_AP"], "per_class_AP": m["per_class_ap"], "per_epoch_mAP": m["per_epoch_mAP"],
            "iface_weight_by_epoch": m["iface_weight_by_epoch"], "frozen_unchanged": m["frozen_unchanged"],
            "start": st, "end": en, "code_sha256": (P / run / "code_sha256.txt").read_text().splitlines()}


def caseA_row(run, tower):
    m = read(P / run / "metrics.json")
    ck = m.get("iface_ckpt")
    l2 = None
    if ck and Path(ck).exists():
        st = torch.load(ck, map_location="cpu")["iface"]  # dp_train.py の保存形 {"iface": {"weight": ...}, ...}
        w = [v for v in st.values() if hasattr(v, "float")]
        l2 = float(math.sqrt(sum(float((x.float() ** 2).sum()) for x in w))) if w else None
    side = M / "experiments/analysis/grasp_pilot_d/extra/caseA_seed42_iface_andrew.json"  # andrew にだけ在る重みを読んで測った値
    if l2 is None and side.exists() and read(side)["sha256"] == m.get("iface_ckpt_sha256"):
        l2 = read(side)["iface_l2"]
    cfg = (P / run / "config.yaml").read_text()
    seed = int([ln.split(":")[1] for ln in cfg.splitlines() if ln.strip().startswith("seed:")][0])
    return {"run": run, "host": host(run), "seed": seed, "result_epoch": m["result_epoch"],
            "jaccard": m["phase_jaccard"], "accuracy": m["phase_accuracy"],
            "d_tower": {"jaccard": m["phase_jaccard"] - tower["jaccard"], "accuracy": m["phase_accuracy"] - tower["accuracy"]},
            "init_jaccard": m["init_phase_jaccard"], "init_equals_tower": abs(m["init_phase_jaccard"] - tower["jaccard"]) < 1e-12,
            "per_video": m["per_video"], "per_class": read(P / run / "per_class_ap.json"),
            "iface_l2": l2, "iface_ckpt": ck, "elapsed_seconds": m.get("elapsed_seconds"),
            "receiver_unchanged": m.get("receiver_unchanged")}


def minmax(rows, key, sub=None):
    vals = [(r[sub][key] if sub else r[key]) for r in rows]
    return {"min": min(vals), "max": max(vals), "n": len(vals)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rp = read(REPRO)["metrics"]
    tb = {"mAP": rp["AP"], "target_AP": rp["target_AP"], "control_AP": rp["control_AP"], "host": "bengio",
          "src": str(REPRO)}
    pt = read(PTOWER)
    ta = {"jaccard": pt["phase_jaccard"], "accuracy": pt["phase_accuracy"], "host": "bengio", "src": str(PTOWER)}
    res = {"task_id": "T-2026-11-01-grasp-pilot-d", "unofficial": True, "amendment": "meta.amendments[0]（利用者の指示 2026-11-01）",
           "tower_bengio": {"B": tb, "A": ta}, "caseB": [], "caseA": [], "caseB_long": None}
    for sd, run in B_RUNS.items():
        if (P / run / "grasppilot_metrics.json").exists():
            res["caseB"].append(caseB_row(run, tb))
    for sd, run in A_RUNS.items():
        if (P / run / "metrics.json").exists():
            res["caseA"].append(caseA_row(run, ta))
    res["caseB_minmax"] = {k: minmax(res["caseB"], k, "d_tower") for k in ("mAP", "target_AP", "control_AP")}
    res["caseA_minmax"] = {k: minmax(res["caseA"], k, "d_tower") for k in ("jaccard", "accuracy")}
    groups = DM.read_groups()
    lp = P / B_LONG
    if (lp / "t1b_result.json").exists() or (lp / "logs/val_metrics_by_epoch.json").exists():
        rows = []
        src = lp / "t1b_result.json"
        if src.exists():
            pe = read(src)["per_epoch_eval"]
            for e in pe:
                pc = e["per_class_coco_map"]
                rows.append({"epoch": e["epoch"], "epoch_1based": e["epoch"] + 1, "mAP": e["mAP"],
                             "target_AP": group_ap(pc, groups["target"]), "control_AP": group_ap(pc, groups["control"]),
                             "d_tower_mAP": e["mAP"] - tb["mAP"]})
        final = caseB_row(B_LONG, tb) if (lp / "grasppilot_metrics.json").exists() else None
        res["caseB_long"] = {"run": B_LONG, "host": host(B_LONG), "per_epoch": rows,
                             "at_4_8_12": [r for r in rows if r["epoch_1based"] in (4, 8, 12)], "final": final,
                             "completed": final is not None}
    vids = set()
    for r in res["caseB"] + ([res["caseB_long"]["final"]] if res["caseB_long"] and res["caseB_long"]["final"] else []):
        vids |= set(r["per_video_AP"])
    for r in res["caseA"]:
        vids |= set(r["per_video"])
    res["val_videos_evaluated"] = sorted(vids)
    res["train_videos"] = sorted({Path(im["file_name"]).stem.split("_")[0] for im in read(
        Path("/home/ubuntu/slocal2/s2fix-bengio-body/data/annotations/egosurgery_tool_folds/A/instances_train.json"))["images"]})
    res["test_overlap"] = sorted((vids | set(res["train_videos"])) & TEST_VIDEOS)
    res["test_overlap_control_with_04"] = sorted((vids | set(res["train_videos"]) | {"04"}) & TEST_VIDEOS)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    show = {"B": [(r["seed"], r["host"], round(r["mAP"], 7), round(r["d_tower"]["mAP"], 7), round(r["d_tower"]["target_AP"], 7))
                  for r in res["caseB"]],
            "A": [(r["seed"], r["host"], round(r["jaccard"], 7), round(r["d_tower"]["jaccard"], 7)) for r in res["caseA"]],
            "B_minmax": res["caseB_minmax"], "A_minmax": res["caseA_minmax"], "test_overlap": res["test_overlap"],
            "long": res["caseB_long"]["at_4_8_12"] if res["caseB_long"] else None}
    print(json.dumps(show, ensure_ascii=False))


if __name__ == "__main__":
    main()

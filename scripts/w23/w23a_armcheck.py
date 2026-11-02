"""Task C-1・SPEC §3.2: 台本の腕と信号の対応が、その型の W1 の run の記録と同じか（非公式 T-2026-11-01-stage2-w23-andrew）。

run_pd_w23_andrew.sh の dryrun が表示する引数を、W1 の run の config.yaml（信号・評価の信号・零の信号・界面の設定の名前・
地図の種類と見取り・学習率・数値精度・長さ・seed・検出塔・注釈）と突き合わせる。読むだけ。

    python scripts/w23/w23a_armcheck.py --out <json> [--swap gt,pred_noCF]   # --swap は陽性対照（台本の二つの腕を入れ替えて照合）
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path

import yaml

M = Path(__file__).resolve().parents[2]
P1 = M / "experiments/phase1"
ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
W1_RUNS = {
    "P1": {"empty": "stage2fix_pd_P1-W1_empty_ep4_seed42", "pred_noCF": "stage2fix_pd_P1-W1_pred_noCF_ep4_seed42",
           "gt": "stage2pilot_pd_P1-W1_gt_seed42", "pred_CF": "stage2pilot_pd_P1-W1_pred_CF_seed42",
           "gtpred_CF": "stage2pilot_pd_P1-W1_gtpred_CF_seed42", "shuffle": "stage2fix_pd_P1-W1_shuffle_ep4_seed42"},
    "DX": {a: f"stage2four_pd_DX_{a}_ep4_seed42" for a in ARMS},
    "B": {a: f"grasppilot2_B_{a}_ep4_seed42" for a in ARMS},
}
COMMON = {"lr": 0.0001, "film_lr": 0.0005, "amp": "bf16", "seed": 42, "inject": "film"}


def dryrun(typ: str, w: str, arm: str) -> dict:
    out = subprocess.run(["bash", str(M / "scripts/w23/run_pd_w23_andrew.sh"), typ, w, arm, "dryrun"],
                         capture_output=True, text=True, check=True).stdout
    kv = dict(line.split("=", 1) for line in out.splitlines())
    toks = shlex.split(kv["train_in"])
    d = {"cfg_name": Path(kv["cfg"]).name, "zero_ctx": "--zero-ctx" in toks, "trainable": kv["trainable"], "run": kv["run"]}
    for flag in ("--signal-train", "--signal-val", "--grasp-map", "--grasp-pred-train", "--grasp-pred-val"):
        d[flag.lstrip("-").replace("-", "_")] = toks[toks.index(flag) + 1] if flag in toks else None
    return d


def recorded(run: str) -> dict:
    c = yaml.safe_load((P1 / run / "config.yaml").read_text())
    s = c.get("stage2pilot", {})
    return {"cfg_name": Path(c["model_cfg"]).name, "zero_ctx": bool(c["zero_ctx"]), "signal_train": s.get("signal_train"),
            "signal_val": s.get("signal_val"), "grasp_map": s.get("grasp_map"), "grasp_pred_train": s.get("grasp_pred_train"),
            "grasp_pred_val": s.get("grasp_pred_val"), "trainable": c["trainable"],
            "common": {k: c[k] for k in COMMON}, "epochs": c["epochs"], "det_ckpt": s.get("det_ckpt"),
            "ann_dir": s.get("ann_dir"), "fixed_epochs": s.get("fixed_epochs")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--swap", default=None)
    a = ap.parse_args()
    swap = dict(zip(a.swap.split(","), reversed(a.swap.split(",")))) if a.swap else {}
    rows, all_ok = [], True
    keys = ("cfg_name", "zero_ctx", "signal_train", "signal_val", "grasp_map", "grasp_pred_train", "grasp_pred_val")
    for typ, runs in W1_RUNS.items():
        for arm in ARMS:
            rec = recorded(runs[arm])
            for w in ("W2", "W3"):
                got = dryrun(typ, w, swap.get(arm, arm))
                diff = {k: (got[k], rec[k]) for k in keys if got[k] != rec[k]}
                ok = not diff and rec["common"] == COMMON and rec["epochs"] in (4, 6) and rec["trainable"] == "film"
                all_ok &= ok
                rows.append({"type": typ, "w": w, "arm": arm, "w1_run": runs[arm], "run": got["run"], "trainable": got["trainable"],
                             "match": ok, "diff": diff, "w1_common": rec["common"], "w1_epochs": rec["epochs"],
                             "w1_fixed_epochs": rec["fixed_epochs"], "w1_det_ckpt": rec["det_ckpt"], "w1_ann_dir": rec["ann_dir"]})
    res = {"task_id": "T-2026-11-01-stage2-w23-andrew", "swap": a.swap, "n": len(rows),
           "n_match": sum(r["match"] for r in rows), "all_match": all_ok, "rows": rows}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    for r in rows:
        if not r["match"]:
            print("MISMATCH", r["type"], r["w"], r["arm"], r["diff"], r["w1_common"], r["w1_epochs"])
    print({k: res[k] for k in ("swap", "n", "n_match", "all_match")})


if __name__ == "__main__":
    main()

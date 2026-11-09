"""腕と信号の対応の照合（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew、Task B）。

台本 run_w3lra.sh の dryrun が解決する引数（設定・学習と評価の信号・零の信号・学ぶ範囲）を、前回の W3 の run の config.yaml
（P1・P2L・P3 は bengio の experiments/phase1/w23b_pd_<型>-W3_<腕>_ep4_seed42、DX は andrew の w23a_pd_DX_W3_<腕>_ep4_seed42）と突き合わせる。
受け取り手の学習率だけは前回 1e-4・本契約 1e-5 で違うはずであり、違うことを別に記録する（ほかの項目は一致するはず）。
陽性対照: --swap a,b で二つの腕の前回の run を入れ替えて照合すると一致が外れる。

    python w3lra_armcheck.py --out <json> [--swap gt,pred_noCF]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml

M = Path(__file__).resolve().parents[4]
RUNNER = Path(__file__).resolve().parent / "run_w3lra.sh"
TYPES = ("P1", "P2L", "P3", "DX")
ARMS = ("empty", "pred_noCF", "gt", "shuffle")


def prev_run(typ: str, arm: str) -> Path:
    if typ == "DX":
        return M / f"experiments/phase1/w23a_pd_DX_W3_{arm}_ep4_seed42"
    return M / f"experiments/phase1/w23b_pd_{typ}-W3_{arm}_ep4_seed42"


def dryrun(typ: str, arm: str) -> dict:
    out = subprocess.run(["bash", str(RUNNER), typ, arm, "dryrun"], capture_output=True, text=True, check=True).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--swap", default=None)
    a = ap.parse_args()
    swap = tuple(a.swap.split(",")) if a.swap else None
    rows = []
    for typ in TYPES:
        for arm in ARMS:
            parm = arm
            if swap and arm in swap:
                parm = swap[1] if arm == swap[0] else swap[0]
            d = dryrun(typ, arm)
            cfg = yaml.safe_load((prev_run(typ, parm) / "config.yaml").read_text())
            sp = cfg["stage2pilot"]
            same = {
                "model_cfg": Path(d["cfg"]).name == Path(cfg["model_cfg"]).name,
                "signal_train": d["signal_train"] == sp["signal_train"],
                "signal_val": d["signal_val"] == sp["signal_val"],
                "zero_ctx": (d["zero"] == "--zero-ctx") == bool(cfg["zero_ctx"]),
                "trainable": d["trainable"] == cfg["trainable"],
                "film_lr": float(d["film_lr"]) == float(cfg["film_lr"]),
                "amp_seed_epochs_fixed": (cfg["amp"], cfg["seed"], cfg["epochs"], sp["fixed_epochs"]) == ("bf16", 42, 4, True),
            }
            rows.append({"type": typ, "arm": arm, "prev_run": prev_run(typ, parm).name, "match": all(same.values()),
                         "fields": same, "lr_now": float(d["lr"]), "lr_prev": float(cfg["lr"])})
    out = {"swap": a.swap, "n": len(rows), "n_match": sum(r["match"] for r in rows),
           "all_match": all(r["match"] for r in rows),
           "lr_now_all": sorted({r["lr_now"] for r in rows}), "lr_prev_all": sorted({r["lr_prev"] for r in rows}), "rows": rows}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: out[k] for k in ("swap", "n", "n_match", "all_match", "lr_now_all", "lr_prev_all")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

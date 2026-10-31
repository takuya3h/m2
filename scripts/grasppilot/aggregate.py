"""案 A・案 B の腕の表（非公式 T-2026-10-31-grasp-pilot-probe、SPEC §6.1・§6.2、Task D-7・acceptance j）。本体の .venv。

各 run の記録（案 A: metrics.json・per_class_ap.json・predictions/val_probs_best.npz・logs/history.json、
案 B: grasppilot_metrics.json）から、4 epoch 目の値、空の腕との差 Δ空、塔単独との差 Δ塔、動画ごとの Δ空 を計算し直す。
案 A は工程注釈のある全フレームと、注釈のあるフレーム（g の旗 1）の両方で出す。塔単独の値は時間ヘッドをその場で当てて出す。

    .venv/bin/python scripts/grasppilot/aggregate.py --signals <dir> --out <json> [--with-b]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402

P1 = C.ROOT / "experiments/phase1"
A_RUNS = {"empty": "grasppilot_dp_001_GA_empty_ep4_seed42", "gt": "grasppilot_dp_002_GA_gt_ep4_seed42"}
B_RUNS = {"empty": "grasppilot_pd_B_empty_ep4_seed42", "gt": "grasppilot_pd_B_gt_ep4_seed42"}
DET_TOWER = C.ROOT / "experiments/analysis/grasp_pilot_probe/repro/dtower_val_seed42.json"


def metrics(probs, seqs, names, keep=None):
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    per = {}
    for v, frames, lab in seqs:
        pred = probs[v].argmax(1)
        m = np.ones(len(frames), bool) if keep is None else np.array([f in keep for f in frames])
        ev.update(pred[m], lab[m], video_id=v)
        one = PhaseEvaluator(num_classes=len(names), class_names=names)
        one.update(pred[m], lab[m], video_id=v)
        r = one.compute()
        per[v] = {"jaccard": r["phase_jaccard"], "accuracy": r["phase_accuracy"], "n": int(m.sum())}
    r = ev.compute()
    return {"jaccard": r["phase_jaccard"], "accuracy": r["phase_accuracy"], "per_class_jaccard": r["phase_per_class_jaccard"],
            "per_video": per, "n": int(sum(p["n"] for p in per.values()))}


def tower_probs(seqs):
    feats = C.load_features()
    head = C.load_ptower_head()
    out = {}
    with torch.no_grad():
        for v, frames, _ in seqs:
            x = torch.from_numpy(np.stack([feats[f] for f in frames])).T[None].cuda()
            out[v] = torch.softmax(head(x)[-1][0], 0).T.cpu().numpy()
    return out


def case_a(signals):
    names = C.phase_names()
    seqs = C.phase_sequences(C.fold_a()["val"])
    with np.load(Path(signals) / "g_val.npz") as d:
        keep = {str(f) for f, k in zip(d["frame_ids"], d["flag"]) if k > 0}
    rows = {"tower": {"all": metrics(tower_probs(seqs), seqs, names), "annotated": metrics(tower_probs(seqs), seqs, names, keep)}}
    for arm, run in A_RUNS.items():
        d = P1 / run
        with np.load(d / "predictions/val_probs_best.npz") as z:
            probs = {k: z[k] for k in z.files}
        m = json.loads((d / "metrics.json").read_text())
        rows[arm] = {"run": run, "all": metrics(probs, seqs, names), "annotated": metrics(probs, seqs, names, keep),
                     "recorded_jaccard": m["phase_jaccard"], "recorded_accuracy": m["phase_accuracy"],
                     "result_epoch": m.get("result_epoch"), "elapsed_seconds": m["elapsed_seconds"],
                     "history": json.loads((d / "logs/history.json").read_text())}
        rows[arm]["recompute_matches_record"] = (rows[arm]["all"]["jaccard"] == m["phase_jaccard"]
                                                 and rows[arm]["all"]["accuracy"] == m["phase_accuracy"])
    for arm in A_RUNS:
        for fs in ("all", "annotated"):
            r, e, t = rows[arm][fs], rows["empty"][fs], rows["tower"][fs]
            r["d_empty"] = {"jaccard": r["jaccard"] - e["jaccard"], "accuracy": r["accuracy"] - e["accuracy"]}
            r["d_tower"] = {"jaccard": r["jaccard"] - t["jaccard"], "accuracy": r["accuracy"] - t["accuracy"]}
            r["d_empty_per_video"] = {v: {"jaccard": r["per_video"][v]["jaccard"] - e["per_video"][v]["jaccard"],
                                          "accuracy": r["per_video"][v]["accuracy"] - e["per_video"][v]["accuracy"]}
                                      for v in r["per_video"]}
    return rows


def case_b():
    tower = json.loads(DET_TOWER.read_text())["metrics"]
    rows = {"tower": {k: tower[k] for k in ("AP", "target_AP", "control_AP", "per_video_AP")}}
    for arm, run in B_RUNS.items():
        p = P1 / run / "grasppilot_metrics.json"
        if not p.exists():
            rows[arm] = None
            continue
        m = json.loads(p.read_text())
        st, en = ((P1 / run / f).read_text().strip() for f in ("start.txt", "end.txt"))
        rows[arm] = {"run": run, **{k: m[k] for k in ("AP", "target_AP", "control_AP", "per_video_AP", "per_class_ap",
                                                     "result_epoch", "init", "per_epoch_mAP", "iface_weight_by_epoch",
                                                     "frozen_unchanged")}, "start_utc": st, "end_utc": en}
    if rows.get("empty"):
        for arm in B_RUNS:
            r = rows[arm]
            if r is None:
                continue
            e, t = rows["empty"], rows["tower"]
            r["d_empty"] = {k: r[k] - e[k] for k in ("AP", "target_AP", "control_AP")}
            r["d_tower"] = {k: r[k] - t[k] for k in ("AP", "target_AP", "control_AP")}
            r["d_empty_per_video"] = {v: r["per_video_AP"][v] - e["per_video_AP"][v] for v in r["per_video_AP"]}
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signals", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--with-b", action="store_true")
    a = ap.parse_args()
    out = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True, "case_A": case_a(a.signals)}
    if a.with_b:
        out["case_B"] = case_b()
    C.write_json(a.out, out)
    for arm in ("tower", "empty", "gt"):
        r = out["case_A"][arm]
        print("A", arm, {fs: (round(r[fs]["jaccard"], 7), round(r[fs]["accuracy"], 7), r[fs].get("d_empty"), r[fs]["n"])
                         for fs in ("all", "annotated")}, r.get("recompute_matches_record"))
    if a.with_b:
        for arm, r in out["case_B"].items():
            print("B", arm, r and {k: r.get(k) for k in ("AP", "target_AP", "control_AP", "d_empty", "d_tower")})


if __name__ == "__main__":
    main()

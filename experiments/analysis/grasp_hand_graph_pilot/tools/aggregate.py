"""集計と検証（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task E、SPEC §3.3・§7）。本体の .venv。GPU を使わない。

塔: 7 本の run の記録（epoch ごとの val の mask mAP とクラス別 AP、止まった回、選んだ回、所要）。G3 の器具 3 クラスと G5r の器具 3 クラスの並べ、
bengio の G の値（11-05 の RESULT §3、参考の別欄）、目標 0.80 との差、H4 の自分の手と他者の手。
腕: 96 本の run の記録を読み、val の確率（最良と最後の回）から指標を測り直して記録と突き合わせる（ずれ 0 を求める。1e-6 ずらした写しを検出する）。
差（SPEC §7。同じ W・同じ設定の中だけ）: 6 工程の Jaccard（val に現れる 7 工程から dressing を除いた平均）、frame accuracy、7 工程の Jaccard、
工程別、動画ごと、二つの腕の argmax の一致の割合、指標がちょうど同じか。W1 だけ塔単独との差。±0.015 の中の差は「読めない」。

    .venv/bin/python experiments/analysis/grasp_hand_graph_pilot/tools/aggregate.py --out <S>/grasp_hand_graph/e/summary.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402

TASK = "T-2026-11-20-grasp-hand-graph-pilot"
PH1 = ROOT / "experiments/phase1"
SETTINGS = [("s1", 10, 1), ("s2", 10, 2), ("s3", 30, 1), ("s4", 30, 2)]
SCOPES = ("W1", "W2", "W3")
ARMS = ("empty", "D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")
LABEL = {"empty": "A0"}
DIFFS = [("DGH", "empty", "グラフ全体の効果"), ("D", "empty", "検出塔の情報だけ"), ("DG", "D", "把持の上乗せ"),
         ("DH", "D", "自分の手の位置の上乗せ"), ("DGH", "DG", "把持に手の節と辺を足した上乗せ"),
         ("DGH", "DGH-U", "どの手かの情報"), ("DGH", "DGH-noCF", "交差適合の有無"), ("DGH-GT", "empty", "正解のグラフでの余地")]
BAND = 0.015
TOWERS = [("G3", "all"), ("G3", "H1"), ("G3", "H2"), ("H4", "all"), ("H4", "H1"), ("H4", "H2"), ("G5r", "all")]
TOOL3 = ["Left Hand Tool", "Right Hand Tool", "Two Hands Tool"]
BENGIO_G = {"segm_mAP": 0.6460, "First Person's Left Hand": 0.7116, "First Person's Right Hand": 0.8245,
            "Left Hand Tool": 0.5306, "Right Hand Tool": 0.6338, "Two Hands Tool": 0.5296,
            "source": "tasks/T-2026-11-05-grasp-tower-rebuild/RESULT.md §3（bengio、確定、epoch 3）"}


def six(per_class, present):
    return float(np.mean([per_class[n] for n in present if n != "dressing"]))


def seven(per_class, present):
    return float(np.mean([per_class[n] for n in present]))


class Ctx:
    def __init__(self):
        self.names = C.phase_names()
        self.seqs = C.phase_sequences(C.fold_a()["val"])
        self.present = [self.names[c] for c in sorted(set(np.concatenate([y for _, _, y in self.seqs]).tolist()))]


def from_probs(ctx, path):
    probs = np.load(path)
    ev = PhaseEvaluator(num_classes=len(ctx.names), class_names=ctx.names)
    per_video, argmax = {}, {}
    for video, _, y in ctx.seqs:
        pred = probs[video].argmax(1)
        argmax[video] = pred
        ev.update(pred, y, video_id=video)
        one = PhaseEvaluator(num_classes=len(ctx.names), class_names=ctx.names)
        one.update(pred, y, video_id=video)
        r1 = one.compute()
        per_video[video] = {"phase_jaccard": r1["phase_jaccard"], "phase_accuracy": r1["phase_accuracy"],
                            "six_phase_mean": six(r1["phase_per_class_jaccard"], ctx.present)}
    r = ev.compute()
    return {"phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
            "per_class_jaccard": r["phase_per_class_jaccard"], "six_phase_mean": six(r["phase_per_class_jaccard"], ctx.present),
            "seven_phase_mean": seven(r["phase_per_class_jaccard"], ctx.present), "per_video": per_video}, argmax


def find_run(scope, n, layers, arm):
    hits = [h for h in sorted(PH1.glob(f"grasp_hand_graph_arm_*_GR-{scope}-N{n}-L{layers}_{arm}_conv_seed42"))
            if (h / "logs/history.json").exists()]
    return hits


def towers():
    out = {}
    for t, v in TOWERS:
        d = PH1 / f"grasp_hand_graph_tower_{t}_{v}_seed42"
        if not (d / "metrics.json").exists() or not json.loads((d / "metrics.json").read_text()):
            out[f"{t}_{v}"] = None
            continue
        m = json.loads((d / "metrics.json").read_text())
        cfg = json.loads((d / "config.json").read_text())
        h = json.loads((d / "logs/history.json").read_text())
        out[f"{t}_{v}"] = {"run": d.name, "train_videos": cfg["train_videos"], "train_frames": cfg["train_frames"],
                           "val_frames": cfg["val_frames"], "best_epoch": m["best_epoch"], "stopped_epoch": m["early_stopped_epoch"],
                           "reached_cap": m["reached_epoch_cap"], "best_segm_mAP": m["best_segm_mAP"], "pre_segm_mAP": m["pre_segm_mAP"],
                           "elapsed_seconds": m["elapsed_seconds"], "peak_alloc_bytes": m["peak_alloc_bytes"],
                           "best_per_class_ap": m["best_per_class_ap"], "ckpt_sha256": m["best_ckpt_sha256"],
                           "epochs": [{"epoch": r["epoch"], "segm_mAP": r["segm_mAP"], "per_class_ap": r["per_class_ap"],
                                       "train_seconds": r.get("train_seconds"), "train_loss": r.get("train_loss")} for r in h]}
    cmp = None
    if out.get("G3_all") and out.get("G5r_all"):
        g3, g5 = out["G3_all"]["best_per_class_ap"], out["G5r_all"]["best_per_class_ap"]
        rows = [{"class": c, "G3": g3[c], "G5r": g5[c], "G3_minus_G5r": g3[c] - g5[c], "bengio_G_reference": BENGIO_G[c]} for c in TOOL3]
        m3, m5 = float(np.mean([g3[c] for c in TOOL3])), float(np.mean([g5[c] for c in TOOL3]))
        cmp = {"rows": rows, "G3_tool3_mean": m3, "G5r_tool3_mean": m5, "diff_mean": m3 - m5,
               "G3_segm_mAP": out["G3_all"]["best_segm_mAP"], "G5r_segm_mAP_5cls": out["G5r_all"]["best_segm_mAP"],
               "G5r_tool3_mean_differs_from_5cls_mAP": m5 != out["G5r_all"]["best_segm_mAP"],
               "target_0p80_gap_G3_tool3_mean": m3 - 0.80, "bengio_G": BENGIO_G}
    hand = None
    if out.get("H4_all"):
        p = out["H4_all"]["best_per_class_ap"]
        own = [p["First Person's Left Hand"], p["First Person's Right Hand"]]
        oth = [p["Other Person's Left Hand"], p["Other Person's Right Hand"]]
        hand = {"own_mean": float(np.mean(own)), "other_mean": float(np.mean(oth)), "own": own, "other": oth}
    return out, cmp, hand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ctx = Ctx()
    tw, cmp, hand = towers()
    alone = json.loads((Path(a.out).parent / "tower_alone.json").read_text())
    runs, missing, checks, argm = {}, [], [], {}
    for sc in SCOPES:
        for s, n, layers in SETTINGS:
            for arm in ARMS:
                hits = find_run(sc, n, layers, arm)
                key = f"{sc}|{s}|{arm}"
                if len(hits) != 1:
                    missing.append({"key": key, "found": [h.name for h in hits]})
                    continue
                d = hits[0]
                m = json.loads((d / "metrics.json").read_text())
                last = json.loads((d / "metrics_last.json").read_text())
                pc = json.loads((d / "per_class_ap.json").read_text())
                hist = json.loads((d / "logs/history.json").read_text())
                rb, am = from_probs(ctx, d / "predictions/val_probs_best.npz")
                rl, _ = from_probs(ctx, d / "predictions/val_probs_last.npz")
                argm[key] = am
                dev = max(abs(rb["phase_jaccard"] - m["phase_jaccard"]), abs(rb["phase_accuracy"] - m["phase_accuracy"]),
                          max(abs(rb["per_class_jaccard"][k] - pc[k]) for k in pc),
                          abs(rl["phase_jaccard"] - last["phase_jaccard"]), abs(rl["phase_accuracy"] - last["phase_accuracy"]))
                ctrl = abs((rb["phase_jaccard"] + 1e-6) - m["phase_jaccard"]) > 0
                checks.append({"key": key, "max_dev": dev, "control_shift_detected": ctrl,
                               "j7_equals_phase_jaccard": abs(rb["seven_phase_mean"] - rb["phase_jaccard"]) < 1e-12})
                runs[key] = {"run": d.name, "best": rb, "last": rl, "best_epoch": m["best_epoch"], "epochs_run": m["epochs_run"],
                             "lr_drop_epoch": m.get("lr_drop_epoch"), "reached_cap": m["reached_epoch_cap"],
                             "early_stopped_epoch": m["early_stopped_epoch"], "elapsed_seconds": m["elapsed_seconds"],
                             "init_phase_jaccard": m["init_phase_jaccard"], "receiver_unchanged": m.get("receiver_unchanged"),
                             "norms": m.get("norms"), "negative_control": m.get("negative_control"),
                             "iface_params": m["iface_params"], "history_val_jaccard": [h["val_jaccard"] for h in hist]}
    diffs = []
    for sc in SCOPES:
        for s, n, layers in SETTINGS:
            for a1, a2, what in DIFFS:
                k1, k2 = f"{sc}|{s}|{a1}", f"{sc}|{s}|{a2}"
                if k1 not in runs or k2 not in runs:
                    continue
                for state in ("best", "last"):
                    r1, r2 = runs[k1][state], runs[k2][state]
                    row = {"scope": sc, "setting": s, "N": n, "L": layers, "arm1": LABEL.get(a1, a1), "arm2": LABEL.get(a2, a2),
                           "reads": what, "state": state,
                           "six": r1["six_phase_mean"] - r2["six_phase_mean"], "acc": r1["phase_accuracy"] - r2["phase_accuracy"],
                           "j7": r1["phase_jaccard"] - r2["phase_jaccard"],
                           "per_phase": {p: r1["per_class_jaccard"][p] - r2["per_class_jaccard"][p] for p in ctx.present},
                           "per_video": {v: {kk: r1["per_video"][v][kk] - r2["per_video"][v][kk] for kk in r1["per_video"][v]}
                                         for v in r1["per_video"]},
                           "metrics_identical": r1["phase_jaccard"] == r2["phase_jaccard"] and r1["phase_accuracy"] == r2["phase_accuracy"]}
                    if state == "best":
                        am1, am2 = argm[k1], argm[k2]
                        tot = sum(len(v) for v in am1.values())
                        row["argmax_agree"] = sum(int((am1[v] == am2[v]).sum()) for v in am1) / tot
                    row["readable"] = abs(row["six"]) > BAND
                    diffs.append(row)
    w1_alone = []
    for s, n, layers in SETTINGS:
        for arm in ARMS:
            k = f"W1|{s}|{arm}"
            if k in runs:
                r = runs[k]["best"]
                w1_alone.append({"setting": s, "arm": LABEL.get(arm, arm), "six": r["six_phase_mean"] - alone["six_phase_mean"],
                                 "acc": r["phase_accuracy"] - alone["phase_accuracy"], "j7": r["phase_jaccard"] - alone["phase_jaccard"]})
    best_rows = [d for d in diffs if d["state"] == "best"]
    pred = {"p1_gt_ge_dgh": [], "p2_w1_dg_minus_d_in_band": []}
    for sc in SCOPES:
        for s, _, _ in SETTINGS:
            g = next((d for d in best_rows if d["scope"] == sc and d["setting"] == s and d["arm1"] == "DGH-GT" and d["arm2"] == "A0"), None)
            h = next((d for d in best_rows if d["scope"] == sc and d["setting"] == s and d["arm1"] == "DGH" and d["arm2"] == "A0"), None)
            if g and h:
                pred["p1_gt_ge_dgh"].append({"scope": sc, "setting": s, "gt_minus_a0": g["six"], "dgh_minus_a0": h["six"], "hit": g["six"] >= h["six"]})
            if sc == "W1":
                dg = next((d for d in best_rows if d["scope"] == sc and d["setting"] == s and d["arm1"] == "DG" and d["arm2"] == "D"), None)
                if dg:
                    pred["p2_w1_dg_minus_d_in_band"].append({"setting": s, "six": dg["six"], "hit": abs(dg["six"]) <= BAND})
    if cmp:
        pred["p3_g3_vs_g5r_tool3_within_0p03"] = {"diff": cmp["diff_mean"], "hit": abs(cmp["diff_mean"]) <= 0.03}
    if hand:
        pred["p4_h4_own_gt_other"] = {"own": hand["own_mean"], "other": hand["other_mean"], "hit": hand["own_mean"] > hand["other_mean"]}
    summary = {"task_id": TASK, "unofficial": True, "present_phases": ctx.present, "towers": tw, "tower_compare": cmp, "hands": hand,
               "tower_alone": alone, "runs": runs, "n_runs": len(runs), "missing": missing, "recompute_checks": checks,
               "recompute_max_dev": max((c["max_dev"] for c in checks), default=None),
               "recompute_control_all_detected": all(c["control_shift_detected"] for c in checks),
               "j7_equals_phase_jaccard_all": all(c["j7_equals_phase_jaccard"] for c in checks),
               "diffs": diffs, "w1_vs_tower_alone": w1_alone, "predictions": pred, "band": BAND,
               "n_diffs_best": len(best_rows), "n_metrics_identical_best": sum(d["metrics_identical"] for d in best_rows),
               "n_unreadable_best": sum(not d["readable"] for d in best_rows)}
    C.write_json(a.out, summary)
    print(json.dumps({k: summary[k] for k in ("n_runs", "recompute_max_dev", "recompute_control_all_detected", "j7_equals_phase_jaccard_all",
                                              "n_diffs_best", "n_metrics_identical_best", "n_unreadable_best")}, ensure_ascii=False))
    print("missing", len(missing), missing[:3])


if __name__ == "__main__":
    main()

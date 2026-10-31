"""二本目の腕の表（非公式 T-2026-11-01-grasp-pilot-g、SPEC §6.1・§6.2、Task G・acceptance g）。本体の .venv。

各 run の記録から値を計算し直す（表に手で写さない）:
    G     experiments/phase1/grasppilot2_G_{all,H1,H2}_seed42/{metrics.json, logs/history.json}
    案 A  experiments/phase1/grasppilot2_dp_*_GA_<腕>_ep4_seed42/（predictions/val_probs_best.npz から指標を計算し直す）
    案 B  experiments/phase1/grasppilot2_B_<腕>_ep4_seed42/grasppilot_metrics.json
    案 C  experiments/phase1/grasppilot2_C_<腕>_seed42/{metrics_head.json, logs/history.json, aux_val.json}
差: Δ空 = 腕 − 空、Δ入替 = 腕 − 入れ替え、Δ塔 = 腕 − 塔単独、予測-noCF − 正解。案 C は Δ教師・Δ入替・教師 − 入れ替え。

    .venv/bin/python scripts/grasppilot/aggregate2.py --out experiments/analysis/grasp_pilot_g/report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import aggregate as A1  # noqa: E402
from stage2pilot import common as C  # noqa: E402

P1 = C.ROOT / "experiments/phase1"
ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
C_ARMS = ("noaux", "teacher", "shuffled")
PROBE_SIG = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/signals")


def read(p):
    return json.loads(Path(p).read_text())


def g_tower():
    out = {}
    for g in ("all", "H1", "H2"):
        d = P1 / f"grasppilot2_G_{g}_seed42"
        if not (d / "metrics.json").exists():
            out[g] = None
            continue
        m, h = read(d / "metrics.json"), read(d / "logs/history.json")
        out[g] = {**m, "history": [{k: r.get(k) for k in ("epoch", "lr", "train_loss", "segm_mAP", "grasp5_mAP", "action",
                                                         "train_seconds", "infer_seconds", "eval_seconds")} for r in h],
                  "per_class_ap_best": read(d / "per_class_ap.json"), "config": read(d / "config.json")}
    return out


def diffs(rows, keys, tower):
    e, s = rows.get("empty"), rows.get("shuffle")
    for arm, r in rows.items():
        if r is None or arm == "tower":
            continue
        r["d_empty"] = {k: r[k] - e[k] for k in keys} if e else None
        r["d_shuffle"] = {k: r[k] - s[k] for k in keys} if s else None
        r["d_tower"] = {k: r[k] - tower[k] for k in keys}
        if rows.get("gt"):
            r["d_gt"] = {k: r[k] - rows["gt"][k] for k in keys}


def case_a():
    names = C.phase_names()
    seqs = C.phase_sequences(C.fold_a()["val"])
    with np.load(PROBE_SIG / "g_val.npz") as d:
        keep = {str(f) for f, k in zip(d["frame_ids"], d["flag"]) if k > 0}
    tp = A1.tower_probs(seqs)
    rows = {"tower": {"all": A1.metrics(tp, seqs, names), "annotated": A1.metrics(tp, seqs, names, keep)}}
    for arm in ARMS:
        hits = sorted(P1.glob(f"grasppilot2_dp_*_GA_{arm}_ep4_seed42"))
        if not hits:
            rows[arm] = None
            continue
        d = hits[-1]
        with np.load(d / "predictions/val_probs_best.npz") as z:
            probs = {k: z[k] for k in z.files}
        m = read(d / "metrics.json")
        rows[arm] = {"run": d.name, "all": A1.metrics(probs, seqs, names), "annotated": A1.metrics(probs, seqs, names, keep),
                     "recorded_jaccard": m["phase_jaccard"], "recorded_accuracy": m["phase_accuracy"],
                     "elapsed_seconds": m.get("elapsed_seconds"), "history": read(d / "logs/history.json")}
        rows[arm]["recompute_matches_record"] = (rows[arm]["all"]["jaccard"] == m["phase_jaccard"]
                                                 and rows[arm]["all"]["accuracy"] == m["phase_accuracy"])
    for fs in ("all", "annotated"):
        flat = {arm: ({"jaccard": r[fs]["jaccard"], "accuracy": r[fs]["accuracy"]} if r else None)
                for arm, r in rows.items() if arm != "tower"}
        diffs(flat, ("jaccard", "accuracy"), rows["tower"][fs])
        for arm, r in flat.items():
            if r is None:
                continue
            for k in ("d_empty", "d_shuffle", "d_tower", "d_gt"):
                rows[arm][fs][k] = r.get(k)
            e = rows.get("empty")
            if e:
                rows[arm][fs]["d_empty_per_video"] = {
                    v: {m: rows[arm][fs]["per_video"][v][m] - e[fs]["per_video"][v][m] for m in ("jaccard", "accuracy")}
                    for v in rows[arm][fs]["per_video"]}
    return rows


def case_b():
    tower = read(A1.DET_TOWER)["metrics"]
    rows = {"tower": {k: tower[k] for k in ("AP", "target_AP", "control_AP", "per_video_AP")}}
    for arm in ARMS:
        d = P1 / f"grasppilot2_B_{arm}_ep4_seed42"
        if not (d / "grasppilot_metrics.json").exists():
            rows[arm] = None
            continue
        m = read(d / "grasppilot_metrics.json")
        st, en = ((d / f).read_text().strip() for f in ("start.txt", "end.txt"))
        rows[arm] = {"run": d.name, **{k: m[k] for k in ("AP", "target_AP", "control_AP", "per_video_AP", "per_class_ap",
                                                         "result_epoch", "per_epoch_mAP", "iface_weight_by_epoch",
                                                         "frozen_unchanged")},
                     "start_utc": st, "end_utc": en, "code_sha256": (d / "code_sha256.txt").read_text()}
    keys = ("AP", "target_AP", "control_AP")
    diffs({a: r for a, r in rows.items() if a != "tower"}, keys, rows["tower"])
    e = rows.get("empty")
    for arm, r in rows.items():
        if arm != "tower" and r and e:
            r["d_empty_per_video"] = {v: r["per_video_AP"][v] - e["per_video_AP"][v] for v in r["per_video_AP"]}
    shas = {a: r["code_sha256"] for a, r in rows.items() if a != "tower" and r}
    rows["code_identical_across_arms"] = len(set(shas.values())) == 1 if shas else None
    return rows


def case_c():
    rows = {}
    for arm in C_ARMS:
        d = P1 / f"grasppilot2_C_{arm}_seed42"
        if not (d / "metrics_head.json").exists():
            rows[arm] = None
            continue
        h = read(d / "metrics_head.json")
        rows[arm] = {"run": d.name, "jaccard": h["phase_jaccard"], "accuracy": h["phase_accuracy"],
                     "per_class_jaccard": h["per_class_jaccard"], "per_video": h["per_video"],
                     "head_history": h["history"], "finetune_history": read(d / "logs/history.json"),
                     "finetune": read(d / "metrics_finetune.json"),
                     "aux_val": read(d / "aux_val.json") if (d / "aux_val.json").exists() else None}
    n, t, s = (rows.get(a) for a in C_ARMS)
    out = {"arms": rows}
    for name, (x, y) in {"teacher_minus_noaux": (t, n), "shuffled_minus_noaux": (s, n), "teacher_minus_shuffled": (t, s)}.items():
        if x and y:
            out[name] = {"jaccard": x["jaccard"] - y["jaccard"], "accuracy": x["accuracy"] - y["accuracy"],
                         "per_video": {v: {m: x["per_video"][v][m] - y["per_video"][v][m] for m in ("jaccard", "accuracy")}
                                       for v in x["per_video"]},
                         "per_class_jaccard": {c: x["per_class_jaccard"][c] - y["per_class_jaccard"][c]
                                               for c in x["per_class_jaccard"]}}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {"task_id": "T-2026-11-01-grasp-pilot-g", "unofficial": True, "G": g_tower(), "case_A": case_a(),
           "case_B": case_b(), "case_C": case_c()}
    C.write_json(a.out, out)
    for arm in ARMS:
        r = out["case_A"].get(arm)
        print("A", arm, r and (round(r["all"]["jaccard"], 7), r["all"].get("d_empty"), r.get("recompute_matches_record")))
    for arm in ARMS:
        r = out["case_B"].get(arm)
        print("B", arm, r and (round(r["target_AP"], 7), r.get("d_empty")))
    print("C", {k: v for k, v in out["case_C"].items() if k != "arms"})


if __name__ == "__main__":
    main()

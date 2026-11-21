"""集計と検証（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、Task E、SPEC §3.4・§5.3・§6・§7）。本体の .venv。GPU を使わない。

    .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/aggregate.py --out <T>/e/summary.json

- 腕の run（グラフ 129 本・T→P 36 本。4 epoch で止めた確かめ 6 本は c_checks の ep4）の epoch 4・8・12・16 の val の確率から指標を測り直し、
  metrics_ep<E>.json と突き合わせる（ずれ 0 を求める。1e-6 ずらした写しを検出する）
- 省いた run（SPEC §5.3）: A0 は W ごとに s1 の値を 4 設定に、辺の無い腕（D・DG・DH の 9 腕）は s1 の値を s2 に、s3 の値を s4 に使う（出所を記録）
- 差（SPEC §7）: 同じ W・同じ設定・同じ epoch の中だけ。6 工程の Jaccard（val に現れる 7 工程から dressing を除いた平均）、frame accuracy、
  7 工程の Jaccard、工程別、動画ごと、argmax の一致の割合、指標がちょうど同じか。±0.015 の中は「読めない」
- 参考の列: 前回の T→P の記録（W1 は andrew の stage2fix、W2・W3 は bengio の w23b。クラス別の値から同じ指標を出す）と、
  前回のグラフの最良の回（収束規則。腕の名前の対応: A0 = empty、X-CF = X、DGH-noCF、DGH-GT）
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-graph-t2p-match"
T = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p")
PH = ROOT / "experiments/phase1"
SCOPES = ("W1", "W2", "W3")
SETTINGS = [("s1", 10, 1), ("s2", 10, 2), ("s3", 30, 1), ("s4", 30, 2)]
EPOCHS = (4, 8, 12, 16)
CORES = ("D", "DG", "DH", "DGH", "DGH-U")
GR_ARMS = ["A0"] + [f"{c}-{s}" for c in CORES for s in ("noCF", "CF", "S")] + ["DGH-GT"]
EDGELESS = {f"{c}-{s}" for c in ("D", "DG", "DH") for s in ("noCF", "CF", "S")}
TP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L2")
TP_ARMS = ("empty", "pred_noCF", "shuffle")
TP_PREV = {"W1": "stage2fix_dp", "W2": "w23b_dp_W2", "W3": "w23b_dp_W3"}
BAND = 0.015
DIFFS = ([(f"{c}-noCF", f"{c}-S", "フレームに対応した信号の中身（主）") for c in CORES]
         + [(f"{c}-S", "A0", "信号の値の分布だけ") for c in CORES]
         + [(f"{c}-noCF", "A0", "グラフを入れたことの全体") for c in CORES]
         + [(f"{c}-CF", f"{c}-noCF", "学習時の信号の質") for c in CORES]
         + [("DG-noCF", "D-noCF", "把持の上乗せ"), ("DH-noCF", "D-noCF", "自分の手の位置の上乗せ"),
            ("DGH-noCF", "DG-noCF", "把持に手の節と辺を足した上乗せ"), ("DGH-noCF", "DGH-U-noCF", "どの手かの情報"),
            ("DGH-GT", "A0", "正解のグラフでの余地"), ("DGH-GT", "DGH-noCF", "送り手の誤りの分")])
PREV_GR = {"A0": "empty", **{f"{c}-CF": c for c in CORES}, "DGH-noCF": "DGH-noCF", "DGH-GT": "DGH-GT"}


def six(per_class, present):
    return float(np.mean([per_class[n] for n in present if n != "dressing"]))


class Ctx:
    def __init__(self):
        self.names = C.phase_names()
        self.seqs = C.phase_sequences(C.fold_a()["val"])
        self.present = [self.names[c] for c in sorted(set(np.concatenate([y for _, _, y in self.seqs]).tolist()))]
        C.assert_no_test([v for v, _, _ in self.seqs], "aggregate/val")


def evaluate(ctx, probs):
    ev = PhaseEvaluator(num_classes=len(ctx.names), class_names=ctx.names)
    per_video, argmax = {}, {}
    for video, _, y in ctx.seqs:
        pred = probs[video].argmax(1)
        argmax[video] = pred
        ev.update(pred, y, video_id=video)
        one = PhaseEvaluator(num_classes=len(ctx.names), class_names=ctx.names)
        one.update(pred, y, video_id=video)
        r1 = one.compute()
        per_video[video] = {"j7": r1["phase_jaccard"], "acc": r1["phase_accuracy"], "six": six(r1["phase_per_class_jaccard"], ctx.present)}
    r = ev.compute()
    return {"j7": r["phase_jaccard"], "acc": r["phase_accuracy"], "six": six(r["phase_per_class_jaccard"], ctx.present),
            "per_class": r["phase_per_class_jaccard"], "per_video": per_video}, argmax


def load_probs(path):
    with np.load(path) as d:
        return {k: d[k] for k in d.files}


def one(pattern):
    hits = sorted(glob.glob(str(PH / pattern)))
    return Path(hits[0]) if len(hits) == 1 else (None if not hits else hits)


def read_run(ctx, run, checks):
    out, am = {}, {}
    for e in EPOCHS:
        m = json.loads((run / f"metrics_ep{e}.json").read_text())
        r, a = evaluate(ctx, load_probs(run / f"predictions/val_probs_ep{e}.npz"))
        dev = max(abs(r["j7"] - m["phase_jaccard"]), abs(r["acc"] - m["phase_accuracy"]),
                  max(abs(r["per_class"][k] - m["phase_per_class_jaccard"][k]) for k in m["phase_per_class_jaccard"]),
                  max(abs(r["per_video"][v]["j7"] - m["per_video"][v]["phase_jaccard"]) for v in m["per_video"]))
        checks.append({"run": run.name, "epoch": e, "max_dev": dev, "control_shift_detected": (r["j7"] + 1e-6) != m["phase_jaccard"]})
        out[e] = {**r, "iface_last": m["iface_last"], "optim_lr": m["optim_lr"]}
        am[e] = a
    met = json.loads((run / "metrics.json").read_text())
    return {"run": run.name, "epochs": out, "elapsed_seconds": met["elapsed_seconds"], "epochs_run": met["epochs_run"],
            "result_epoch": met.get("result_epoch"), "init_phase_jaccard": met["init_phase_jaccard"],
            "receiver_unchanged": met.get("receiver_unchanged"), "negative_control": met.get("negative_control"),
            "steps_without_grad": met.get("steps_without_grad"),
            "receiver_trained_changed": met.get("receiver_trained_changed"),
            "receiver_outside_scope_unchanged": met.get("receiver_outside_scope_unchanged")}, am


def diff_row(r1, r2, a1, a2):
    row = {"six": r1["six"] - r2["six"], "acc": r1["acc"] - r2["acc"], "j7": r1["j7"] - r2["j7"],
           "per_phase": {p: r1["per_class"][p] - r2["per_class"][p] for p in r1["per_class"]},
           "per_video": {v: {k: r1["per_video"][v][k] - r2["per_video"][v][k] for k in r1["per_video"][v]} for v in r1["per_video"]},
           "metrics_identical": r1["j7"] == r2["j7"] and r1["acc"] == r2["acc"] and r1["per_class"] == r2["per_class"]}
    tot = sum(len(v) for v in a1.values())
    row["argmax_agree"] = sum(int((a1[v] == a2[v]).sum()) for v in a1) / tot
    row["readable"] = abs(row["six"]) > BAND
    return row


def record_values(ctx, run):
    """前回の記録（クラス別の値）から同じ指標を出す。"""
    m = json.loads((run / "metrics.json").read_text())
    pc = json.loads((run / "per_class_ap.json").read_text())
    pv = m.get("per_video", {})
    return {"run": run.name, "host": (run / "server.txt").read_text().strip() if (run / "server.txt").exists() else None,
            "six": six(pc, ctx.present), "acc": m["phase_accuracy"], "j7": m["phase_jaccard"], "epoch": m.get("best_epoch"),
            "per_video": {v: {"j7": x["phase_jaccard"], "acc": x["phase_accuracy"]} for v, x in pv.items()}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ctx = Ctx()
    alone = json.loads((T / "b/tower_alone.json").read_text())
    checks, missing, runs, argm = [], [], {}, {}
    # グラフの腕（回した run）
    for sc in SCOPES:
        for s, n, ell in SETTINGS:
            for arm in GR_ARMS:
                name = "empty" if arm == "A0" else arm
                run = one(f"grasp_hand_graph_t2p_gr_[0-9][0-9][0-9]_GR-{sc}-N{n}-L{ell}_{name}_ep16_seed42")
                if run is None:
                    continue
                if not isinstance(run, Path) or not (run / "metrics_ep16.json").exists():
                    missing.append({"key": f"{sc}|{s}|{arm}", "found": str(run)})
                    continue
                r, am = read_run(ctx, run, checks)
                runs[f"GR|{sc}|{s}|{arm}"], argm[f"GR|{sc}|{s}|{arm}"] = r, am
        for t in TP_TYPES:
            for arm in TP_ARMS:
                run = one(f"grasp_hand_graph_t2p_tp_{sc}_[0-9][0-9][0-9]_{t}_{arm}_ep16_seed42")
                if not isinstance(run, Path) or not (run / "metrics_ep16.json").exists():
                    missing.append({"key": f"TP|{sc}|{t}|{arm}", "found": str(run)})
                    continue
                r, am = read_run(ctx, run, checks)
                runs[f"TP|{sc}|{t}|{arm}"], argm[f"TP|{sc}|{t}|{arm}"] = r, am
    # 表の値（省いた run は出所の run の値）
    table, source = {}, {}
    for sc in SCOPES:
        for s, n, ell in SETTINGS:
            for arm in GR_ARMS:
                if arm == "A0":
                    src = "s1"
                elif arm in EDGELESS:
                    src = {"s1": "s1", "s2": "s1", "s3": "s3", "s4": "s3"}[s]
                else:
                    src = s
                k = f"GR|{sc}|{src}|{arm}"
                if k in runs:
                    table[f"{sc}|{s}|{arm}"] = k
                    source[f"{sc}|{s}|{arm}"] = {"run": runs[k]["run"], "omitted": src != s}
                else:
                    missing.append({"key": f"table {sc}|{s}|{arm}", "found": []})
    # 差
    diffs = []
    for sc in SCOPES:
        for s, n, ell in SETTINGS:
            for a1, a2, what in DIFFS:
                k1, k2 = table.get(f"{sc}|{s}|{a1}"), table.get(f"{sc}|{s}|{a2}")
                if not (k1 and k2):
                    continue
                for e in EPOCHS:
                    row = diff_row(runs[k1]["epochs"][e], runs[k2]["epochs"][e], argm[k1][e], argm[k2][e])
                    diffs.append({"group": "graph", "scope": sc, "setting": s, "N": n, "L": ell, "epoch": e, "arm1": a1, "arm2": a2,
                                  "reads": what, **row})
        for t in TP_TYPES:
            for a1, a2, what in (("pred_noCF", "shuffle", "T→P の信号の中身"), ("pred_noCF", "empty", "T→P の信号を入れたことの全体")):
                k1, k2 = f"TP|{sc}|{t}|{a1}", f"TP|{sc}|{t}|{a2}"
                if k1 not in runs or k2 not in runs:
                    continue
                for e in EPOCHS:
                    row = diff_row(runs[k1]["epochs"][e], runs[k2]["epochs"][e], argm[k1][e], argm[k2][e])
                    diffs.append({"group": "tp", "scope": sc, "type": t, "epoch": e, "arm1": a1, "arm2": a2, "reads": what, **row})
    # W1 だけ塔単独との差
    w1_alone = []
    for key, k in table.items():
        sc, s, arm = key.split("|")
        if sc == "W1":
            for e in EPOCHS:
                r = runs[k]["epochs"][e]
                w1_alone.append({"group": "graph", "setting": s, "arm": arm, "epoch": e, "six": r["six"] - alone["six_phase_mean"],
                                 "acc": r["acc"] - alone["phase_accuracy"], "j7": r["j7"] - alone["phase_jaccard"]})
    for t in TP_TYPES:
        for arm in TP_ARMS:
            k = f"TP|W1|{t}|{arm}"
            if k in runs:
                for e in EPOCHS:
                    r = runs[k]["epochs"][e]
                    w1_alone.append({"group": "tp", "type": t, "arm": arm, "epoch": e, "six": r["six"] - alone["six_phase_mean"],
                                     "acc": r["acc"] - alone["phase_accuracy"], "j7": r["j7"] - alone["phase_jaccard"]})
    # 参考の列: 前回の T→P の記録と、本契約の回し直しの 4 epoch 目との差
    tp_prev = []
    for sc in SCOPES:
        for t in TP_TYPES:
            for arm in TP_ARMS:
                old = one(f"{TP_PREV[sc]}_[0-9][0-9][0-9]_{t}_{arm}_ep4_seed42")
                k = f"TP|{sc}|{t}|{arm}"
                if not isinstance(old, Path) or k not in runs:
                    missing.append({"key": f"tp_prev {sc}|{t}|{arm}", "found": str(old)})
                    continue
                rv = record_values(ctx, old)
                new = runs[k]["epochs"][4]
                po = load_probs(old / "predictions/val_probs_best.npz")
                pn = load_probs(PH / runs[k]["run"] / "predictions/val_probs_ep4.npz")
                tp_prev.append({"scope": sc, "type": t, "arm": arm, "prev": rv, "new_ep4": {kk: new[kk] for kk in ("six", "acc", "j7")},
                                "new_minus_prev": {kk: new[kk] - rv[kk] for kk in ("six", "acc", "j7")},
                                "probs_equal": all(np.array_equal(po[v], pn[v]) for v in po),
                                "probs_max_abs_diff": max(float(np.abs(po[v] - pn[v]).max()) for v in po)})
    # 参考の列: 前回のグラフの最良の回
    gr_prev = []
    for sc in SCOPES:
        for s, n, ell in SETTINGS:
            for arm, old_arm in PREV_GR.items():
                old = one(f"grasp_hand_graph_arm_[0-9][0-9][0-9]_GR-{sc}-N{n}-L{ell}_{old_arm}_conv_seed42")
                if isinstance(old, Path):
                    gr_prev.append({"scope": sc, "setting": s, "arm": arm, **record_values(ctx, old)})
    # 指標がちょうど同じになった差の数と argmax の一致（W と epoch ごと）
    ident = {}
    for sc in SCOPES:
        for e in EPOCHS:
            rows = [d for d in diffs if d["scope"] == sc and d["epoch"] == e]
            ident[f"{sc}|{e}"] = {"graph_diffs": sum(d["group"] == "graph" for d in rows),
                                  "graph_identical": sum(d["metrics_identical"] for d in rows if d["group"] == "graph"),
                                  "tp_diffs": sum(d["group"] == "tp" for d in rows),
                                  "tp_identical": sum(d["metrics_identical"] for d in rows if d["group"] == "tp"),
                                  "unreadable": sum(not d["readable"] for d in rows),
                                  "argmax_agree_min": min((d["argmax_agree"] for d in rows), default=None),
                                  "argmax_agree_median": statistics.median([d["argmax_agree"] for d in rows]) if rows else None}
    # 零初期化の層の大きさ
    norms = {}
    for k, r in runs.items():
        g, sc = k.split("|")[0], k.split("|")[1]
        for e in EPOCHS:
            norms.setdefault(f"{g}|{sc}|{e}", []).append(r["epochs"][e]["iface_last"]["last_weight_l2"])
    norms = {k: {"n": len(v), "min": min(v), "median": statistics.median(v), "max": max(v)} for k, v in norms.items()}
    # 予測（SPEC §7.1）
    def d4(**kw):
        return next((d for d in diffs if d["epoch"] == 4 and all(d.get(k) == v for k, v in kw.items())), None)
    pred = {"p1": [], "p2": [], "p3": None, "p4": []}
    for sc in SCOPES:
        for s, _, _ in SETTINGS:
            g, h = d4(scope=sc, setting=s, arm1="DGH-GT", arm2="A0"), d4(scope=sc, setting=s, arm1="DGH-noCF", arm2="A0")
            if g and h:
                pred["p1"].append({"scope": sc, "setting": s, "gt_minus_a0": g["six"], "dgh_minus_a0": h["six"], "hit": g["six"] >= h["six"]})
            dg = d4(scope=sc, setting=s, arm1="DG-noCF", arm2="D-noCF")
            if dg:
                pred["p4"].append({"scope": sc, "setting": s, "six": dg["six"], "hit": abs(dg["six"]) <= BAND})
    for s in ("s1", "s3"):
        x = d4(scope="W1", setting=s, arm1="D-noCF", arm2="D-S")
        if x:
            pred["p2"].append({"setting": s, "six": x["six"], "hit": abs(x["six"]) <= BAND})
    gw2 = [d4(scope="W2", setting=s, arm1="DGH-noCF", arm2="DGH-S") for s, _, _ in SETTINGS]
    tw2 = d4(scope="W2", group="tp", type="D1-L2", arm1="pred_noCF", arm2="shuffle")
    if all(gw2) and tw2:
        mx = max(d["six"] for d in gw2)
        pred["p3"] = {"graph_max": mx, "graph_by_setting": [d["six"] for d in gw2], "d1l2": tw2["six"], "hit": mx < tw2["six"]}
    # 終わりの数え上げ
    import yaml
    all_runs = sorted(p.name for p in PH.glob("grasp_hand_graph_t2p_*") if "_repro_" not in p.name)

    def complete(r):
        d = PH / r
        if not (d / "metrics.json").exists() or not json.loads((d / "metrics.json").read_text() or "{}"):
            return False                                   # ExperimentManager は始めに空の metrics.json を置く
        rec = yaml.safe_load((d / "config.yaml").read_text())["record_epochs"]
        return all((d / f"metrics_ep{e}.json").exists() and (d / f"predictions/val_probs_ep{e}.npz").exists() for e in rec)
    end = {"expected": 189, "found": len(all_runs), "complete": sum(complete(r) for r in all_runs),
           "nonexistent_name_hits": len(glob.glob(str(PH / "grasp_hand_graph_t2p_gr_[0-9][0-9][0-9]_GR-W1-N10-L1_NO_SUCH_ARM_ep16_seed42"))),
           "known_name_hits": len(glob.glob(str(PH / "grasp_hand_graph_t2p_gr_[0-9][0-9][0-9]_GR-W1-N10-L1_DGH-noCF_ep16_seed42"))),
           "by_prefix": {}}
    for r in all_runs:
        pfx = re.sub(r"_[0-9]{3}_.*", "", r)
        end["by_prefix"][pfx] = end["by_prefix"].get(pfx, 0) + 1
    videos = sorted({v for r in all_runs for p in ("train", "val")
                     for v in yaml.safe_load((PH / r / "config.yaml").read_text())["videos"][p]})
    summary = {"task_id": TASK, "unofficial": True, "present_phases": ctx.present, "tower_alone": alone, "band": BAND,
               "runs": runs, "n_runs": len(runs), "table_source": source, "missing": missing, "end_check": end,
               "recompute_n": len(checks), "recompute_max_dev": max((c["max_dev"] for c in checks), default=None),
               "recompute_control_all_detected": all(c["control_shift_detected"] for c in checks),
               "diffs": diffs, "w1_vs_tower_alone": w1_alone, "tp_prev": tp_prev, "graph_prev": gr_prev,
               "identical_by_scope_epoch": ident, "iface_last_norms": norms, "predictions": pred,
               "videos_in_runs": {"videos": videos, "test_overlap": sorted(set(videos) & set(C.TEST_VIDEOS))},
               "videos_control_04": {"test_overlap": sorted((set(videos) | {"04"}) & set(C.TEST_VIDEOS))},
               "elapsed_seconds_total": sum(r["elapsed_seconds"] for r in runs.values())}
    C.write_json(a.out, summary)
    print(json.dumps({k: summary[k] for k in ("n_runs", "recompute_n", "recompute_max_dev", "recompute_control_all_detected",
                                              "end_check", "videos_in_runs")}, ensure_ascii=False))
    print("missing", len(missing), missing[:5])
    print("pred", json.dumps({k: (v if k == "p3" else [x["hit"] for x in v]) for k, v in pred.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()

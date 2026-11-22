"""集計と検証（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、Task E、SPEC §5.2・§7）。本体の .venv。GPU を使わない。読むだけ。書くのは --out だけ。

    .venv/bin/python experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/aggregate.py --out <T>/e/summary.json

腕: 本契約の run（型 IRN・HiCE・HTT）と前回のグラフの型の 96 本の記録を読み、val の確率（最良と最後の回）から指標を測り直して記録と突き合わせる
（ずれ 0 を求める。1e-6 ずらした写しを検出する）。
省いた組み合わせ（SPEC §5.2）は、確かめ（d/chk_compare.json）が一致したときだけ流用先の値を使う。一致しなかった組み合わせに run が在れば
（jobs.py fill、利用者の回答 (3)）その run を使い、無ければ欠けとして数える。
  A0 の s2〜s4 ← 同じ型・同じ W の A0 の s1（確かめ: 各型の A0 の s4 と s1、W1）
  HiCE の D ← HiCE の同じ W・同じ設定の A0（確かめ: HiCE の D と A0、s1・W1）
  HiCE の DH の s3・s4 ← s1・s2（確かめ: HiCE の DH の s3 と s1、W1）
差（SPEC §7。同じ型・同じ W・同じ設定の中だけ）: 6 工程の Jaccard（val に現れる 7 工程から dressing を除いた平均）、frame accuracy、
7 工程の Jaccard、工程別、動画ごと、二つの腕の argmax の一致の割合、指標がちょうど同じか。W1 だけ塔単独との差。±0.015 の中の差は「読めない」。
型の間: 同じ W・同じ設定で、グラフの型（前回の記録）・IRN・HiCE・HTT の差を並べ、同じ腕どうしの型の差を出す。
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jobs as J  # noqa: E402
from stage2pilot import common as C  # noqa: E402

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-irn-hice-htt-pilot"
T = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt")
PH1 = ROOT / "experiments/phase1"
SETTINGS = [("s1", 10, 1), ("s2", 10, 2), ("s3", 30, 1), ("s4", 30, 2)]
SN = {s: (n, ell) for s, n, ell in SETTINGS}
SCOPES = ("W1", "W2", "W3")
TYPES = ("GR", "IRN", "HiCE", "HTT")
NEW = ("IRN", "HiCE", "HTT")
ARMS = ("empty", "D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")
LABEL = {"empty": "A0"}
DIFFS = [("DGH", "empty", "渡し方の全体の効果"), ("D", "empty", "検出塔の情報だけ"), ("DG", "D", "把持の上乗せ"),
         ("DH", "D", "自分の手の位置の上乗せ"), ("DGH", "DG", "把持に手のトークンを足した上乗せ"),
         ("DGH", "DGH-U", "どの手かの情報"), ("DGH", "DGH-noCF", "交差適合の有無"), ("DGH-GT", "empty", "正解の信号での余地")]
CROSS = [("DGH", "empty"), ("DGH-GT", "empty"), ("DG", "D"), ("DGH", "DGH-U")]
BAND = 0.015


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


def run_dirs(t, sc, s, arm):
    n, ell = SN[s]
    pfx = ["grasp_hand_graph_arm"] if t == "GR" else [J.MAIN, J.CHK]
    return [h for p in pfx for h in sorted(PH1.glob(f"{p}_[0-9][0-9][0-9]_{t}-{sc}-N{n}-L{ell}_{arm}_conv_seed42"))
            if (h / "logs/history.json").exists() and (h / "metrics_last.json").exists()]


def borrow_source(t, sc, s, arm, chk_ok):
    """省いた組み合わせの流用先 (型, W, 設定, 腕, 確かめの名前)。省いていなければ None。"""
    if t == "GR":
        return None
    if arm == "empty" and s != "s1":
        return (t, sc, "s1", "empty", f"{t} A0 s4 vs s1 (W1)")
    if t == "HiCE" and arm == "D" and not (sc == "W1" and s == "s1"):
        return (t, sc, s, "empty", "HiCE D vs A0 (s1, W1)")
    if t == "HiCE" and arm == "DH" and s in ("s3", "s4"):
        return (t, sc, {"s3": "s1", "s4": "s2"}[s], "DH", "HiCE DH s3 vs s1 (W1)")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ctx = Ctx()
    alone = json.loads((T / "b/tower_alone.json").read_text())
    chk = {p["name"]: p for p in json.loads((T / "d/chk_compare.json").read_text())["pairs"]}
    # HiCE の D の s1・W1 は確かめの run そのもの（接頭辞 chk）。腕の値として使う
    runs, missing, checks, argm, borrowed = {}, [], [], {}, []
    keys = [(t, sc, s, arm) for t in TYPES for sc in SCOPES for s, _, _ in SETTINGS for arm in ARMS]
    for t, sc, s, arm in keys:
        key = f"{t}|{sc}|{s}|{arm}"
        hits = run_dirs(t, sc, s, arm)
        if t != "GR":
            hits = [h for h in hits if h.name.startswith(J.MAIN)] or [h for h in hits if (t, s, arm, sc) == ("HiCE", "s1", "D", "W1")]
        if len(hits) != 1:
            if not hits and borrow_source(t, sc, s, arm, chk):
                continue
            missing.append({"key": key, "found": [h.name for h in hits]})
            continue
        d = hits[0]
        m = json.loads((d / "metrics.json").read_text())
        last = json.loads((d / "metrics_last.json").read_text())
        pc = json.loads((d / "per_class_ap.json").read_text())
        hist = json.loads((d / "logs/history.json").read_text())
        rb, am = from_probs(ctx, d / "predictions/val_probs_best.npz")
        rl, aml = from_probs(ctx, d / "predictions/val_probs_last.npz")
        argm[key] = {"best": am, "last": aml}
        dev = max(abs(rb["phase_jaccard"] - m["phase_jaccard"]), abs(rb["phase_accuracy"] - m["phase_accuracy"]),
                  max(abs(rb["per_class_jaccard"][k] - pc[k]) for k in pc),
                  abs(rl["phase_jaccard"] - last["phase_jaccard"]), abs(rl["phase_accuracy"] - last["phase_accuracy"]))
        checks.append({"key": key, "max_dev": dev, "control_shift_detected": abs((rb["phase_jaccard"] + 1e-6) - m["phase_jaccard"]) > 0,
                       "j7_equals_phase_jaccard": abs(rb["seven_phase_mean"] - rb["phase_jaccard"]) < 1e-12})
        runs[key] = {"run": d.name, "best": rb, "last": rl, "best_epoch": m["best_epoch"], "epochs_run": m["epochs_run"],
                     "lr_drop_epoch": m.get("lr_drop_epoch"), "reached_cap": m["reached_epoch_cap"],
                     "early_stopped_epoch": m["early_stopped_epoch"], "elapsed_seconds": m["elapsed_seconds"],
                     "init_phase_jaccard": m["init_phase_jaccard"], "iface_params": m["iface_params"],
                     "negative_control": m.get("negative_control"), "history_val_jaccard": [h["val_jaccard"] for h in hist],
                     "borrowed_from": None}
    for t, sc, s, arm in keys:
        key = f"{t}|{sc}|{s}|{arm}"
        if key in runs or any(x["key"] == key for x in missing):
            continue
        src = borrow_source(t, sc, s, arm, chk)
        ok = chk.get(src[4], {}).get("equal", False)
        # 流用先が自分も流用（HiCE の D ← A0 ← A0 の s1）のときは先へ辿る
        s_key = f"{src[0]}|{src[1]}|{src[2]}|{src[3]}"
        while s_key not in runs and borrow_source(*s_key.split("|"), chk):
            nxt = borrow_source(*s_key.split("|"), chk)
            ok = ok and chk.get(nxt[4], {}).get("equal", False)
            s_key = f"{nxt[0]}|{nxt[1]}|{nxt[2]}|{nxt[3]}"
        if not ok or s_key not in runs:
            missing.append({"key": key, "found": [], "borrow_refused": src[4], "check_equal": ok})
            continue
        runs[key] = {**runs[s_key], "borrowed_from": s_key, "check": src[4]}
        argm[key] = argm[s_key]
        borrowed.append({"key": key, "from": s_key, "check": src[4]})
    diffs = []
    for t in TYPES:
        for sc in SCOPES:
            for s, n, ell in SETTINGS:
                for a1, a2, what in DIFFS:
                    k1, k2 = f"{t}|{sc}|{s}|{a1}", f"{t}|{sc}|{s}|{a2}"
                    if k1 not in runs or k2 not in runs:
                        continue
                    for state in ("best", "last"):
                        diffs.append(diff_row(ctx, runs, argm, k1, k2, state, kind="within", type_=t, scope=sc, setting=s,
                                              arm1=LABEL.get(a1, a1), arm2=LABEL.get(a2, a2), reads=what))
    cross = []
    for sc in SCOPES:
        for s, _, _ in SETTINGS:
            for arm in ARMS:
                for t1, t2 in itertools.combinations(TYPES, 2):
                    k1, k2 = f"{t2}|{sc}|{s}|{arm}", f"{t1}|{sc}|{s}|{arm}"
                    if k1 not in runs or k2 not in runs:
                        continue
                    for state in ("best", "last"):
                        cross.append(diff_row(ctx, runs, argm, k1, k2, state, kind="cross", type_=f"{t2}−{t1}", scope=sc,
                                              setting=s, arm1=f"{t2} {LABEL.get(arm, arm)}", arm2=f"{t1} {LABEL.get(arm, arm)}",
                                              reads="同じ腕どうしの型の差"))
    w1_alone = []
    for t in TYPES:
        for s, _, _ in SETTINGS:
            for arm in ARMS:
                k = f"{t}|W1|{s}|{arm}"
                if k in runs:
                    for state in ("best", "last"):
                        r = runs[k][state]
                        w1_alone.append({"type": t, "setting": s, "arm": LABEL.get(arm, arm), "state": state,
                                         "six": r["six_phase_mean"] - alone["six_phase_mean"],
                                         "acc": r["phase_accuracy"] - alone["phase_accuracy"], "j7": r["phase_jaccard"] - alone["phase_jaccard"]})
    sign_flip = []
    for kind_rows in (diffs, cross):
        best = {(d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"]): d for d in kind_rows if d["state"] == "best"}
        for d in kind_rows:
            if d["state"] != "last":
                continue
            b = best[(d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"])]
            sign_flip.append({"kind": d["kind"], "type": d["type"], "scope": d["scope"], "setting": d["setting"], "arm1": d["arm1"],
                              "arm2": d["arm2"], "best": b["six"], "last": d["six"], "flip": bool(np.sign(b["six"]) != np.sign(d["six"]))})
    pred = predictions(diffs, cross)
    a0_vs_graph = [{"name": n, "equal": p["equal"], "best_max_abs_diff": p["best"].get("max_abs_diff"),
                    "last_max_abs_diff": p["last"].get("max_abs_diff")} for n, p in chk.items() if "graph A0" in n]
    stats = {}
    for t in TYPES:
        own = [r for k, r in runs.items() if k.startswith(f"{t}|") and r["borrowed_from"] is None]
        stats[t] = {"runs": len(own), "best_epoch_median": float(np.median([r["best_epoch"] for r in own])),
                    "epochs_run_range": [min(r["epochs_run"] for r in own), max(r["epochs_run"] for r in own)],
                    "reached_cap": sum(bool(r["reached_cap"]) for r in own),
                    "elapsed_range": [min(r["elapsed_seconds"] for r in own), max(r["elapsed_seconds"] for r in own)],
                    "params_by_setting": {s: sorted({r["iface_params"] for k, r in runs.items() if k.startswith(f"{t}|")
                                                     and k.split("|")[2] == s and r["borrowed_from"] is None}) for s, _, _ in SETTINGS},
                    "by_scope": {sc: {"best_epoch_median": float(np.median([r["best_epoch"] for k, r in runs.items()
                                                                             if k.startswith(f"{t}|{sc}|") and r["borrowed_from"] is None])),
                                      "last_minus_best_six_median": float(np.median([r["last"]["six_phase_mean"] - r["best"]["six_phase_mean"]
                                                                                      for k, r in runs.items()
                                                                                      if k.startswith(f"{t}|{sc}|") and r["borrowed_from"] is None]))}
                                 for sc in SCOPES}}
    within_best = [d for d in diffs if d["state"] == "best"]
    summary = {"task_id": TASK, "unofficial": True, "present_phases": ctx.present, "tower_alone": alone, "band": BAND,
               "runs": runs, "n_runs": len(runs), "n_borrowed": len(borrowed), "borrowed": borrowed, "missing": missing,
               "recompute_checks": checks, "recompute_max_dev": max((c["max_dev"] for c in checks), default=None),
               "recompute_control_all_detected": all(c["control_shift_detected"] for c in checks),
               "j7_equals_phase_jaccard_all": all(c["j7_equals_phase_jaccard"] for c in checks), "n_recomputed": len(checks),
               "diffs": diffs, "cross": cross, "w1_vs_tower_alone": w1_alone, "sign_flip": sign_flip, "predictions": pred,
               "a0_vs_graph": a0_vs_graph, "stats": stats,
               "counts": {t: {"n_diffs_best": sum(d["type"] == t for d in within_best),
                              "n_unreadable_best": sum(d["type"] == t and not d["readable"] for d in within_best),
                              "n_metrics_identical_best": sum(d["type"] == t and d["metrics_identical"] for d in within_best),
                              "n_sign_flip": sum(f["kind"] == "within" and f["type"] == t and bool(f["flip"]) for f in sign_flip)}
                          for t in TYPES}}
    C.write_json(a.out, summary)
    print(json.dumps({k: summary[k] for k in ("n_runs", "n_borrowed", "recompute_max_dev", "recompute_control_all_detected",
                                              "j7_equals_phase_jaccard_all", "n_recomputed", "counts")}, ensure_ascii=False, default=str))
    print("missing", len(missing), missing[:5])


def diff_row(ctx, runs, argm, k1, k2, state, **meta):
    r1, r2 = runs[k1][state], runs[k2][state]
    am1, am2 = argm[k1][state], argm[k2][state]
    tot = sum(len(v) for v in am1.values())
    t = meta.pop("type_")
    row = {**meta, "type": t, "state": state, "key1": k1, "key2": k2,
           "six": r1["six_phase_mean"] - r2["six_phase_mean"], "acc": r1["phase_accuracy"] - r2["phase_accuracy"],
           "j7": r1["phase_jaccard"] - r2["phase_jaccard"],
           "per_phase": {p: r1["per_class_jaccard"][p] - r2["per_class_jaccard"][p] for p in ctx.present},
           "per_video": {v: {kk: r1["per_video"][v][kk] - r2["per_video"][v][kk] for kk in r1["per_video"][v]} for v in r1["per_video"]},
           "metrics_identical": r1["phase_jaccard"] == r2["phase_jaccard"] and r1["phase_accuracy"] == r2["phase_accuracy"],
           "argmax_agree": sum(int((am1[v] == am2[v]).sum()) for v in am1) / tot,
           "borrowed": [k for k in (k1, k2) if runs[k]["borrowed_from"]]}
    row["readable"] = abs(row["six"]) > BAND
    return row


def predictions(diffs, cross):
    """SPEC §7.1 の予測 1・3・4・5（最良の回、6 工程）。予測 2 は d/chk_compare.json の A0 とグラフの型の A0。"""
    best = {(d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"]): d["six"] for d in diffs if d["state"] == "best"}
    cb = {(d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"]): d["six"] for d in cross if d["state"] == "best"}
    out = {"p1": [], "p3": {}, "p4": {}, "p5": []}
    for t in NEW:
        for sc in SCOPES:
            vals = []
            for s, _, _ in SETTINGS:
                g, h = best.get((t, sc, s, "DGH-GT", "A0")), best.get((t, sc, s, "DGH", "A0"))
                if g is not None and h is not None:
                    out["p1"].append({"type": t, "scope": sc, "setting": s, "gt_minus_a0": g, "dgh_minus_a0": h, "hit": g >= h})
                vals.append(h)
            if sc == "W1":
                n_in = sum(abs(v) <= BAND for v in vals if v is not None)
                out["p3"][t] = {"values": vals, "n_in_band": n_in, "hit": n_in >= 3}
            if sc == "W2":
                n_up = sum(v > BAND for v in vals if v is not None)
                out["p4"][t] = {"values": vals, "n_above": n_up, "hit": n_up >= 2}
        for s, _, _ in SETTINGS:
            v = cb.get((f"{t}−GR", "W1", s, f"{t} DGH", "GR DGH"))
            if v is not None:
                out["p5"].append({"type": t, "setting": s, "six": v, "hit": abs(v) <= BAND})
    out["p1_hit"] = all(x["hit"] for x in out["p1"])
    out["p1_n"] = [sum(x["hit"] for x in out["p1"]), len(out["p1"])]
    out["p5_hit"] = {t: all(x["hit"] for x in out["p5"] if x["type"] == t) for t in NEW}
    return out


if __name__ == "__main__":
    main()

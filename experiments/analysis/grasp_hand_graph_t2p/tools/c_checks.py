"""確かめの集計（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、完了判定 c・f・g・h・k）。読むだけ。書くのは --out だけ。

    python c_checks.py identity --out <T>/c/identity_summary.json   恒等性と陽性対照、学ぶ範囲の定義、W ごとの受け取り手の側の名前の集合
    python c_checks.py repro    --out <T>/c/repro_compare.json      既定の挙動: 回し直した 2 本と記録の比べ（値と val の確率）。対照つき
    python c_checks.py ep4      --out <T>/d/ep4_compare.json        4 epoch で止めた run と続けた run の 4 epoch 目の val の確率。対照つき
    python c_checks.py omitted  --out <T>/d/omitted_compare.json    省いた run（A0 の N、辺の無い腕の L）の確かめ。対照つき
    python c_checks.py optim    --out <T>/d/optim_check.json        optimizer の群ごとの学習率・weight decay が写した値と一致するか。対照つき
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

T = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p")
PH = ROOT / "experiments/phase1"
COPIED = {"iface": {"lr": 5e-4, "weight_decay": 0.01}, "receiver": {"lr": 5e-4, "weight_decay": 0.01}}   # audit B-3


def one(pattern):
    hits = sorted(glob.glob(str(PH / pattern)))
    if len(hits) != 1:
        raise SystemExit(f"run が一つに決まらない: {pattern} {hits}")
    return Path(hits[0])


def probs(path):
    with np.load(path) as d:
        return {k: d[k] for k in d.files}


def probs_diff(a, b):
    if sorted(a) != sorted(b):
        return {"same_keys": False}
    m = max(float(np.abs(a[k] - b[k]).max()) for k in a)
    return {"same_keys": True, "max_abs_diff": m, "equal": all(np.array_equal(a[k], b[k]) for k in a),
            "argmax_agree": float(np.mean(np.concatenate([a[k].argmax(1) == b[k].argmax(1) for k in a])))}


def cmd_identity(a):
    rows, bad, recv = [], [], {}
    for p in sorted((T / "identity").glob("*.json")):
        d = json.loads(p.read_text())
        kind, sc = p.stem.split("_")[0], p.stem.split("_")[1]
        for arm, v in d.items():
            if not isinstance(v, dict) or "identity_max_abs_logit_diff" not in v:
                continue
            ok = v["identity_max_abs_logit_diff"] == 0.0 and v["jaccard_equals_taskB"] and v["positive_max_abs_logit_diff"] > 0
            s = v.get("scope_check")
            if s:
                ok = ok and s["equal"] and not s["equal_with_one_outside_mixed"]
                recv.setdefault(sc, {}).setdefault(kind, set()).add(
                    json.dumps(sorted(n for n in s["trainable_names"] if n.startswith("head."))))
            rows.append({"file": p.stem, "arm": arm, "identity_max_abs_logit_diff": v["identity_max_abs_logit_diff"],
                         "identity_jaccard": v["identity_jaccard"], "positive_max_abs_logit_diff": v["positive_max_abs_logit_diff"],
                         "positive_jaccard": v["positive_jaccard"], "perturbed": v.get("perturbed_params"), "ok": ok})
            if not ok:
                bad.append((p.stem, arm))
    same = {sc: {"GR_sets": len(k.get("GR", ())), "TP_sets": len(k.get("TP", ())),
                 "equal": k.get("GR") == k.get("TP") and len(k.get("GR", ())) == 1,
                 "n_names": len(json.loads(next(iter(k["GR"])))) if k.get("GR") else None} for sc, k in recv.items()}
    out = {"n": len(rows), "n_ok": sum(r["ok"] for r in rows), "bad": bad,
           "identity_max": max(r["identity_max_abs_logit_diff"] for r in rows),
           "positive_min": min(r["positive_max_abs_logit_diff"] for r in rows),
           "positive_max": max(r["positive_max_abs_logit_diff"] for r in rows),
           "receiver_names_GR_vs_TP": same, "rows": rows}
    C.write_json(a.out, out)
    print(json.dumps({k: out[k] for k in ("n", "n_ok", "bad", "identity_max", "positive_min", "positive_max", "receiver_names_GR_vs_TP")}))


def compare_run(new, old, keys, probs_files):
    mn, mo = json.loads((new / "metrics.json").read_text()), json.loads((old / "metrics.json").read_text())
    vals = {k: {"new": mn.get(k), "old": mo.get(k), "equal": mn.get(k) == mo.get(k)} for k in keys}
    pr = {f: probs_diff(probs(new / f"predictions/{f}"), probs(old / f"predictions/{f}")) for f in probs_files}
    extra = {}
    if (old / "metrics_last.json").exists():
        ln, lo = json.loads((new / "metrics_last.json").read_text()), json.loads((old / "metrics_last.json").read_text())
        extra["metrics_last_equal"] = ln == lo
    return {"new": new.name, "old": old.name, "values": vals, "probs": pr, **extra,
            "all_equal": all(v["equal"] for v in vals.values()) and all(p.get("equal") for p in pr.values())
            and extra.get("metrics_last_equal", True)}


def cmd_repro(a):
    keys = ["phase_jaccard", "phase_accuracy", "phase_macro_f1", "best_epoch", "per_video", "epochs_run", "init_phase_jaccard"]
    gr = compare_run(one("grasp_hand_graph_t2p_repro_gr_*_GR-W1-N10-L1_DGH-noCF_conv_seed42"),
                     PH / "grasp_hand_graph_arm_009_GR-W1-N10-L1_DGH-noCF_conv_seed42", keys,
                     ["val_probs_best.npz", "val_probs_last.npz"])
    tp = compare_run(one("grasp_hand_graph_t2p_repro_tp_*_D1-L1_pred_noCF_ep4_seed42"),
                     PH / "stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42", keys, ["val_probs_best.npz"])
    # 陽性対照: 比べる側の val の確率を 1 か所 1e-6 ずらした写し、記録の値を 1e-6 ずらした写しで、比べが違いを拾うか
    new = one("grasp_hand_graph_t2p_repro_tp_*_D1-L1_pred_noCF_ep4_seed42")
    pa = probs(new / "predictions/val_probs_best.npz")
    pb = {k: v.copy() for k, v in pa.items()}
    k0 = sorted(pb)[0]
    pb[k0][0, 0] += 1e-6
    ctrl_p = probs_diff(pa, pb)
    mo = json.loads(((PH / "stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42") / "metrics.json").read_text())
    ctrl_v = json.loads((new / "metrics.json").read_text())["phase_jaccard"] == mo["phase_jaccard"] + 1e-6
    out = {"graph": gr, "tp": tp, "controls": {"probs_one_value_shifted_1e-6": ctrl_p, "jaccard_shifted_1e-6_equal": ctrl_v}}
    C.write_json(a.out, out)
    print(json.dumps({"graph_all_equal": gr["all_equal"], "tp_all_equal": tp["all_equal"],
                      "ctrl_probs_equal": ctrl_p["equal"], "ctrl_probs_diff": ctrl_p["max_abs_diff"], "ctrl_value_equal": ctrl_v}))


def cmd_ep4(a):
    rows = []
    for sc in ("W1", "W2", "W3"):
        for kind, short, long_ in (
                ("GR DGH-noCF s1", f"grasp_hand_graph_t2p_ep4chk_[0-9]*_GR-{sc}-N10-L1_DGH-noCF_ep4_seed42",
                 f"grasp_hand_graph_t2p_gr_[0-9]*_GR-{sc}-N10-L1_DGH-noCF_ep16_seed42"),
                ("D1-L1 pred_noCF", f"grasp_hand_graph_t2p_ep4chk_tp_{sc}_[0-9]*_D1-L1_pred_noCF_ep4_seed42",
                 f"grasp_hand_graph_t2p_tp_{sc}_[0-9]*_D1-L1_pred_noCF_ep16_seed42")):
            s, lg = one(short), one(long_)
            d = probs_diff(probs(s / "predictions/val_probs_ep4.npz"), probs(lg / "predictions/val_probs_ep4.npz"))
            ms, ml = json.loads((s / "metrics_ep4.json").read_text()), json.loads((lg / "metrics_ep4.json").read_text())
            ctrl = probs_diff(probs(lg / "predictions/val_probs_ep4.npz"), probs(lg / "predictions/val_probs_ep8.npz"))
            rows.append({"scope": sc, "kind": kind, "short": s.name, "long": lg.name, "probs": d,
                         "jaccard_equal": ms["phase_jaccard"] == ml["phase_jaccard"],
                         "iface_last_equal": ms["iface_last"] == ml["iface_last"],
                         "short_result_is_ep4": json.loads((s / "metrics.json").read_text())["result_epoch"] == 4,
                         "control_ep4_vs_ep8": ctrl})
    out = {"rows": rows, "all_equal": all(r["probs"]["equal"] and r["jaccard_equal"] for r in rows),
           "controls_detect": all(not r["control_ep4_vs_ep8"]["equal"] for r in rows)}
    C.write_json(a.out, out)
    print(json.dumps({"all_equal": out["all_equal"], "controls_detect": out["controls_detect"],
                      "rows": [(r["scope"], r["kind"], r["probs"].get("max_abs_diff"), r["control_ep4_vs_ep8"].get("max_abs_diff"))
                               for r in rows]}))


def cmd_omitted(a):
    rows = []
    for sc in ("W1", "W2", "W3"):
        for label, x, y in (("A0 s4 vs s1", f"GR-{sc}-N30-L2_empty", f"GR-{sc}-N10-L1_empty"),
                            ("D-noCF s2 vs s1", f"GR-{sc}-N10-L2_D-noCF", f"GR-{sc}-N10-L1_D-noCF"),
                            ("control D-noCF vs DG-noCF s1", f"GR-{sc}-N10-L1_D-noCF", f"GR-{sc}-N10-L1_DG-noCF")):
            rx, ry = one(f"grasp_hand_graph_t2p_gr_[0-9]*_{x}_ep16_seed42"), one(f"grasp_hand_graph_t2p_gr_[0-9]*_{y}_ep16_seed42")
            per = {e: probs_diff(probs(rx / f"predictions/val_probs_ep{e}.npz"), probs(ry / f"predictions/val_probs_ep{e}.npz"))
                   for e in (4, 8, 12, 16)}
            rows.append({"scope": sc, "label": label, "x": rx.name, "y": ry.name, "per_epoch": per,
                         "equal_all_epochs": all(v["equal"] for v in per.values())})
    checks = [r for r in rows if not r["label"].startswith("control")]
    ctrls = [r for r in rows if r["label"].startswith("control")]
    out = {"rows": rows, "checks_all_equal": all(r["equal_all_epochs"] for r in checks),
           "controls_detect": all(not r["equal_all_epochs"] for r in ctrls),
           "by_scope": {sc: all(r["equal_all_epochs"] for r in checks if r["scope"] == sc) for sc in ("W1", "W2", "W3")}}
    C.write_json(a.out, out)
    print(json.dumps({k: out[k] for k in ("checks_all_equal", "controls_detect", "by_scope")}))


def optim_ok(sc, groups, epoch_logs):
    """群ごとの学習率と weight decay が写した値（audit B-3）と一致し、群の中身が界面・受け取り手で、学習の間も変わらないか。"""
    want = [COPIED["iface"]] + ([COPIED["receiver"]] if sc != "W1" else [])
    got = [{"lr": g["lr"], "weight_decay": g["weight_decay"]} for g in groups]
    iface_ok = all(n.startswith("iface.") for n in groups[0]["names"])
    recv_ok = sc == "W1" or (len(groups) == 2 and all(n.startswith("head.") for n in groups[1]["names"]))
    logs_ok = all(m["optim_lr"] == [x["lr"] for x in want] and m["optim_weight_decay"] == [x["weight_decay"] for x in want]
                  for m in epoch_logs)
    return got == want and iface_ok and recv_ok and logs_ok, got


def cmd_optim(a):
    import copy

    import yaml
    rows, bad, recv = [], [], {}
    ctrl_src = None
    for p in sorted(glob.glob(str(PH / "grasp_hand_graph_t2p_*"))):
        run = Path(p)
        if "_repro_" in run.name:
            continue
        cfg = yaml.safe_load((run / "config.yaml").read_text())
        groups = cfg.get("optim_groups")
        if groups is None:
            bad.append((run.name, "no optim_groups"))
            continue
        sc = cfg.get("scope", "W1")
        logs = [json.loads((run / f"metrics_ep{e}.json").read_text()) for e in cfg.get("record_epochs", [])]
        ok, got = optim_ok(sc, groups, logs)
        kind = "GR" if cfg["type"] == "GR" else "TP"
        if sc != "W1":
            recv.setdefault(sc, {}).setdefault(kind, set()).add(json.dumps(groups[1]["names"]))
            if ctrl_src is None:
                ctrl_src = (sc, groups, logs, run.name)
        rows.append({"run": run.name, "scope": sc, "kind": kind, "got": got, "ok": ok,
                     "recv_tensors": groups[1]["n_tensors"] if sc != "W1" else 0})
        if not ok:
            bad.append((run.name, got))
    # 対照: 実際の run の群の受け取り手の学習率だけを 5e-5 に変えた写しを同じ検査にかける
    sc, groups, logs, name = ctrl_src
    g2 = copy.deepcopy(groups)
    g2[1]["lr"] = 5e-5
    ctrl_ok, _ = optim_ok(sc, g2, logs)
    same = {sc: {"GR_sets": len(k.get("GR", ())), "TP_sets": len(k.get("TP", ())),
                 "equal": k.get("GR") == k.get("TP") and len(k.get("GR", ())) == 1} for sc, k in recv.items()}
    out = {"n": len(rows), "n_ok": sum(r["ok"] for r in rows), "bad": bad,
           "control": {"run": name, "change": "receiver lr 5e-4 -> 5e-5", "check_passes": ctrl_ok},
           "receiver_names_GR_vs_TP": same, "rows": rows}
    C.write_json(a.out, out)
    print(json.dumps({k: out[k] for k in ("n", "n_ok", "bad", "control", "receiver_names_GR_vs_TP")})[:2000])


def cmd_unchanged(a):
    """完了判定 k: 開始時の一覧（$T/start/k_listing_start.json。大きさと mtime_ns）と今の同じ根の一覧を比べる。
    本契約の新しい run（grasp_hand_graph_t2p_*）は experiments/phase1/grasp_hand_graph_* の根から除く。対照: 本契約の新しいファイルを
    一つ加えた一覧で、追加として拾うこと。"""
    import os
    start = json.loads((T / "start/k_listing_start.json").read_text())
    now = {}
    tops = set()
    for k in start:
        parts = k.split("/")
        if k.startswith("experiments/phase1/"):
            tops.add("/".join(parts[:3]))
        elif k.startswith("experiments/analysis/"):
            tops.add("/".join(parts[:3]))
        elif k.startswith("/home/ubuntu/slocal2/stage2pilot_store/"):
            tops.add("/".join(parts[:6]))
        else:
            tops.add("/".join(parts[:2]) if k.startswith("data/") else parts[0])
    for r in sorted(tops):
        for dp, dn, fn in os.walk(r):
            for f_ in fn:
                q = os.path.join(dp, f_)
                try:
                    st = os.lstat(q)
                except FileNotFoundError:
                    continue
                now[q] = [st.st_size, st.st_mtime_ns]
    changed = sorted(k for k in start if k in now and now[k] != start[k])
    removed = sorted(k for k in start if k not in now)
    added = sorted(k for k in now if k not in start)
    ctrl_now = dict(now)
    ctrl_now["experiments/analysis/grasp_hand_graph_pilot/__control_new_file__"] = [1, 1]
    ctrl_added = sorted(k for k in ctrl_now if k not in start)
    out = {"roots": sorted(tops), "n_start": len(start), "n_now": len(now), "changed": changed[:50], "n_changed": len(changed),
           "removed": removed[:50], "n_removed": len(removed), "added": added[:50], "n_added": len(added),
           "control_added": len(ctrl_added) - len(added)}
    C.write_json(a.out, out)
    print(json.dumps({k: out[k] for k in ("n_start", "n_now", "n_changed", "n_removed", "n_added", "added", "control_added")})[:3000])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("identity", "repro", "ep4", "omitted", "optim", "unchanged"):
        sub.add_parser(n).add_argument("--out", required=True)
    a = ap.parse_args()
    {"identity": cmd_identity, "repro": cmd_repro, "ep4": cmd_ep4, "omitted": cmd_omitted, "optim": cmd_optim,
     "unchanged": cmd_unchanged}[a.cmd](a)


if __name__ == "__main__":
    main()

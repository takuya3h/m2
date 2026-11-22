"""確かめの集計（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、完了判定 d・e・f・g）。読むだけ。書くのは --out だけ。

    python c_checks.py identity --out <T>/c/identity_summary.json   学習前の一致と陽性対照、学ぶ範囲の定義（288 組み合わせ）
    python c_checks.py repro    --out <T>/c/repro_compare.json      回し直した 2 本と前回の記録の比べ（値と val の確率）。対照つき
    python c_checks.py ends     --out <T>/d/ends.json               SPEC §5.2 の表の全本が収束規則で終わり、最良と最後の val の確率があるか。
                                                                    存在しない名前で 0 件・在る名前で 1 件
    python c_checks.py chk      --out <T>/d/chk_compare.json        確かめの run の一致・不一致と最大の差（A0 の s4 と s1、HiCE の D と A0、
                                                                    HiCE の DH の s3 と s1、各型の A0 とグラフの型の A0）。対照つき
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jobs as J  # noqa: E402
from stage2pilot import common as C  # noqa: E402

T = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt")
PH = ROOT / "experiments/phase1"
COPIED = {"iface": {"lr": 5e-4, "weight_decay": 0.01}, "receiver": {"lr": 5e-4, "weight_decay": 0.01}}   # 前回の RESULT §3


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
        return {"same_keys": False, "equal": False}
    return {"same_keys": True, "max_abs_diff": max(float(np.abs(a[k] - b[k]).max()) for k in a),
            "equal": all(np.array_equal(a[k], b[k]) for k in a),
            "argmax_agree": float(np.mean(np.concatenate([a[k].argmax(1) == b[k].argmax(1) for k in a])))}


def shifted(p):
    q = {k: v.copy() for k, v in p.items()}
    k0 = sorted(q)[0]
    q[k0][0, 0] += 1e-6
    return q


def cmd_identity(a):
    rows, bad = [], []
    for p in sorted((T / "identity").glob("*.json")):
        d = json.loads(p.read_text())
        t, sc, n, ell = p.stem.split("_")
        for arm, v in d.items():
            if not isinstance(v, dict) or "identity_max_abs_logit_diff" not in v:
                continue
            ok = v["identity_max_abs_logit_diff"] == 0.0 and v["jaccard_equals_taskB"] and v["positive_max_abs_logit_diff"] > 0
            s = v.get("scope_check")
            if s:
                ok = ok and s["equal"] and not s["equal_with_one_outside_mixed"]
            row = {"type": t, "scope": sc, "N": int(n[1:]), "L": int(ell[1:]), "arm": arm, "ok": ok,
                   "identity_max_abs_logit_diff": v["identity_max_abs_logit_diff"], "identity_jaccard": v["identity_jaccard"],
                   "positive_max_abs_logit_diff": v["positive_max_abs_logit_diff"], "iface_params": v["iface_params"],
                   "perturbed_params": v.get("perturbed_params"),
                   "scope_equal": None if not s else s["equal"], "n_receiver_trainable": None if not s else s["n_receiver_trainable"]}
            rows.append(row)
            if not ok:
                bad.append(row)
    pos = [r["positive_max_abs_logit_diff"] for r in rows]
    out = {"n": len(rows), "n_ok": sum(r["ok"] for r in rows), "bad": bad,
           "identity_diff_max": max(r["identity_max_abs_logit_diff"] for r in rows),
           "identity_jaccard": sorted({r["identity_jaccard"] for r in rows}), "positive_range": [min(pos), max(pos)],
           "positive_changed": sum(p > 0 for p in pos), "perturbed_params": sorted({tuple(r["perturbed_params"]) for r in rows}),
           "n_receiver_trainable": sorted({(r["scope"], r["n_receiver_trainable"]) for r in rows if r["n_receiver_trainable"] is not None}),
           "rows": rows}
    C.write_json(a.out, out)
    print(json.dumps({k: out[k] for k in ("n", "n_ok", "identity_diff_max", "identity_jaccard", "positive_range",
                                          "positive_changed", "perturbed_params", "n_receiver_trainable")}, ensure_ascii=False))


def compare_run(new, old, extra_probs=()):
    mn, mo = json.loads((new / "metrics.json").read_text()), json.loads((old / "metrics.json").read_text())
    keys = ("phase_jaccard", "phase_accuracy", "best_epoch", "epochs_run", "early_stopped_epoch")
    vals = {k: {"new": mn.get(k), "old": mo.get(k), "equal": mn.get(k) == mo.get(k)} for k in keys}
    pr = {"best": probs_diff(probs(new / "predictions/val_probs_best.npz"), probs(old / "predictions/val_probs_best.npz"))}
    for e in extra_probs:
        pr[e] = probs_diff(probs(new / f"predictions/val_probs_{e}.npz"), probs(old / f"predictions/val_probs_{e}.npz"))
    ctrl_p = probs_diff(shifted(probs(new / "predictions/val_probs_best.npz")), probs(old / "predictions/val_probs_best.npz"))
    ctrl_v = (mn["phase_jaccard"] + 1e-6) == mo["phase_jaccard"]
    cn, co = yaml.safe_load((new / "config.yaml").read_text()), yaml.safe_load((old / "config.yaml").read_text())
    same_inputs = ([f["sha256"] for f in cn["signals_train"] + cn["signals_val"]]
                   == [f["sha256"] for f in co["signals_train"] + co["signals_val"]]
                   and cn["receiver"]["head_sha256"] == co["receiver"]["head_sha256"])
    return {"new": new.name, "old": old.name, "host_new": (new / "server.txt").read_text().strip(),
            "host_old": (old / "server.txt").read_text().strip(), "same_inputs": same_inputs, "values": vals, "probs": pr,
            "all_equal": all(v["equal"] for v in vals.values()) and all(p["equal"] for p in pr.values()),
            "control_probs_shift_1e-6_equal": ctrl_p["equal"], "control_jaccard_shift_1e-6_equal": ctrl_v}


def cmd_repro(a):
    out = {"gr": compare_run(one("grasp_hand_irn_hice_htt_repro_gr_*_GR-W3-N30-L2_DGH_conv_seed42"),
                             one("grasp_hand_graph_arm_093_GR-W3-N30-L2_DGH_conv_seed42"), extra_probs=("last",)),
           "tp": compare_run(one("grasp_hand_irn_hice_htt_repro_tp_*_D1-L1_pred_noCF_ep4_seed42"),
                             one("stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42"))}
    C.write_json(a.out, out)
    print(json.dumps({k: {x: v[x] for x in ("all_equal", "same_inputs", "host_new", "host_old", "control_probs_shift_1e-6_equal",
                                            "control_jaccard_shift_1e-6_equal")} for k, v in out.items()}, ensure_ascii=False))


def runs_of(group):
    for line in J.chk_jobs() + J.main_jobs() if group == "all" else J.fill_jobs(group):
        desc, pfx, _ = line.split("|")
        yield desc, pfx


def run_dir(pfx, desc):
    hits = sorted(glob.glob(str(PH / f"{pfx}_[0-9][0-9][0-9]_{desc}_seed42")))
    return hits


def end_state(d):
    m = json.loads((d / "metrics.json").read_text()) if (d / "metrics.json").exists() and (d / "metrics.json").stat().st_size else {}
    cfg = yaml.safe_load((d / "config.yaml").read_text())
    groups = [(cfg["stop_rule"]["lr"], cfg["stop_rule"]["weight_decay"])]
    if cfg.get("receiver_optim"):
        groups.append((cfg["receiver_optim"]["lr"], cfg["receiver_optim"]["weight_decay"]))
    return {"run": d.name, "complete": bool(m) and (d / "predictions/val_probs_best.npz").exists()
            and (d / "predictions/val_probs_last.npz").exists() and (d / "metrics_last.json").exists(),
            "converge": cfg["stop_rule"].get("converge") is not None, "stopped": m.get("early_stopped_epoch"),
            "cap": m.get("reached_epoch_cap"), "epochs_run": m.get("epochs_run"), "best_epoch": m.get("best_epoch"),
            "elapsed": m.get("elapsed_seconds"), "lr_ok": groups == [(COPIED["iface"]["lr"], COPIED["iface"]["weight_decay"])]
            + ([(COPIED["receiver"]["lr"], COPIED["receiver"]["weight_decay"])] if len(groups) > 1 else []),
            "host": (d / "server.txt").read_text().strip(), "test_overlap": sorted(set(cfg["videos"]["train"] + cfg["videos"]["val"])
                                                                                    & set(C.TEST_VIDEOS))}


def cmd_ends(a):
    rows, missing = [], []
    groups = ["all"] + list(a.fill or [])
    for g in groups:
        for desc, pfx in runs_of(g):
            hits = run_dir(pfx, desc)
            if len(hits) != 1:
                missing.append((pfx, desc, len(hits)))
                continue
            rows.append({"group": g, "desc": desc, **end_state(Path(hits[0]))})
    el = [r["elapsed"] for r in rows if r["elapsed"]]
    out = {"n": len(rows), "missing": missing, "n_complete": sum(r["complete"] for r in rows),
           "n_converge": sum(r["converge"] for r in rows), "n_stopped_by_rule": sum(r["stopped"] is not None for r in rows),
           "n_cap": sum(bool(r["cap"]) for r in rows), "n_lr_ok": sum(r["lr_ok"] for r in rows),
           "hosts": sorted({r["host"] for r in rows}), "test_overlap": sorted({v for r in rows for v in r["test_overlap"]}),
           "elapsed_range": [min(el), max(el)] if el else None,
           "control_nonexistent_name": len(run_dir(J.MAIN, "IRN-W1-N10-L1_NO_SUCH_ARM_conv")),
           "control_existing_name": len(run_dir(J.MAIN, "IRN-W1-N10-L1_DGH_conv")), "rows": rows}
    C.write_json(a.out, out)
    print(json.dumps({k: out[k] for k in out if k != "rows"}, ensure_ascii=False))


def val_probs(pfx, desc, which):
    return probs(Path(run_dir(pfx, desc)[0]) / f"predictions/val_probs_{which}.npz")


def pair(name, a_, b_):
    out = {"name": name, "a": a_[0] + "/" + a_[1], "b": b_[0] + "/" + b_[1]}
    for which in ("best", "last"):
        pa, pb = val_probs(*a_, which), val_probs(*b_, which)
        out[which] = probs_diff(pa, pb)
        out[f"{which}_control_shift_1e-6_equal"] = probs_diff(shifted(pa), pb)["equal"]
    out["equal"] = out["best"]["equal"] and out["last"]["equal"]
    return out


def cmd_chk(a):
    M, K = J.MAIN, J.CHK
    out = []
    for t in ("IRN", "HiCE", "HTT"):
        out.append(pair(f"{t} A0 s4 vs s1 (W1)", (K, f"{t}-W1-N30-L2_empty_conv"), (M, f"{t}-W1-N10-L1_empty_conv")))
    out.append(pair("HiCE D vs A0 (s1, W1)", (K, "HiCE-W1-N10-L1_D_conv"), (M, "HiCE-W1-N10-L1_empty_conv")))
    out.append(pair("HiCE DH s3 vs s1 (W1)", (K, "HiCE-W1-N30-L1_DH_conv"), (M, "HiCE-W1-N10-L1_DH_conv")))
    for t in ("IRN", "HiCE", "HTT"):
        for sc in ("W1", "W2", "W3"):
            out.append(pair(f"{t} A0 vs graph A0 ({sc}, s1)", (M, f"{t}-{sc}-N10-L1_empty_conv"),
                            ("grasp_hand_graph_arm", f"GR-{sc}-N10-L1_empty_conv")))
    C.write_json(a.out, {"pairs": out})
    for p in out:
        print(p["name"], p["equal"], p["best"].get("max_abs_diff"), p["last"].get("max_abs_diff"),
              p["best_control_shift_1e-6_equal"], flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("identity", "repro", "ends", "chk"):
        s = sub.add_parser(n)
        s.add_argument("--out", required=True)
        if n == "ends":
            s.add_argument("--fill", nargs="*", default=None, help="回した fill の群（a0・hice_d・hice_dh）")
    a = ap.parse_args()
    {"identity": cmd_identity, "repro": cmd_repro, "ends": cmd_ends, "chk": cmd_chk}[a.cmd](a)


if __name__ == "__main__":
    main()

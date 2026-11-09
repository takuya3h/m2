"""Task D 集計と検証（T-2026-11-09-grasp-pilot-converge）。本体の .venv。GPU を使わない。

本契約の 127 本（収束規則、grasprc_*）と、同じ腕・設定の前の処方の run（4 epoch 固定。案 3・5 は前の予備 grasprt_*、
案 A は四本目 grasparms_dp_*）を同じ規則で読み、同じ差を並べる。前の予備の f_aggregate.py の部品（from_probs・six）を使う。

差（SPEC §5.1）:
    案 3（設定ごと）: TG − T0、TG − TRand、TG − TGeo、TG − TU、参照段 正解 − T0、参照段 正解 ⊕ 予測 − T0（参照段は把持の注釈のある 1,514 行）
    案 5（同じ W の中だけ）: S_W − S_0、S_W − S_1、S_W − S_W-perm、S_W − S_W-R、S_W − S_W-U。W1 だけ S_W − P 単独
    案 A: 予測-noCF − 空、予測-noCF − 入れ替え
各差に: J・acc・6 工程の平均・クラス別・動画ごと、二つの run の val の argmax が一致したフレームの割合、指標（J と acc）がちょうど同じか。
前の処方と本契約で 6 工程の平均の差の符号が変わったか。

各 run に: 総 epoch、学習率を落とした epoch、最良（checkpoint）の epoch、上限に届いたか、epoch ごとの val、
出力射影の重みの最大の絶対値と L2（学習前・最良・最終）、TW の相対時刻の埋め込みの標準偏差。前の処方の run の同じ量は
その run の界面の重み（checkpoint）から読む。

    .venv/bin/python d_aggregate.py --out <S>/d/summary.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "experiments/analysis/grasp_roitoken_transition_pilot/tools"))
from f_aggregate import C, from_probs, six  # noqa: E402

PRIOR = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot")
KEYS = ("phase_jaccard", "phase_accuracy", "six_phase_mean")
RT_SETTINGS = [f"{ly}-{c}-K{k}" for ly in ("layer4", "layer3") for c in ("roi_geo", "roi") for k in (16, 64)]
RT_ARMS = {"empty": "T0", "pred_CF": "TG", "geo": "TGeo", "union": "TU", "shuffle": "TRand", "gt": "REF_GT", "gtpred_CF": "REF_GTP"}
RT_DIFFS = [("TG", "T0"), ("TG", "TRand"), ("TG", "TGeo"), ("TG", "TU"), ("REF_GT", "T0"), ("REF_GTP", "T0")]
TW_ARMS = {"pred_CF": "S_W", "perm": "S_W-perm", "union": "S_W-U", "shuffle": "S_W-R"}
TW_DIFFS = [("S_W", "S_0"), ("S_W", "S_1"), ("S_W", "S_W-perm"), ("S_W", "S_W-R"), ("S_W", "S_W-U")]


class Ctx:
    def __init__(self):
        self.names = C.phase_names()
        self.seqs = C.phase_sequences(C.fold_a()["val"])
        self.present = [self.names[c] for c in sorted(set(np.concatenate([y for _, _, y in self.seqs]).tolist()))]
        has = np.load(PRIOR / "b4/has_gt_val.npy")
        self.keep, k = {}, 0
        for video, fs, _ in self.seqs:
            self.keep[video] = has[k:k + len(fs)]
            k += len(fs)
        tower = json.loads((PRIOR / "b/b12.json").read_text())["tower_alone_val"]
        self.p_alone = {"phase_jaccard": tower["phase_jaccard"], "phase_accuracy": tower["phase_accuracy"],
                        "six_phase_mean": six(tower["per_class_jaccard"], self.present)}
        self.missing, self.seen = [], {"train": set(), "val": set()}


def find(pattern):
    return sorted((ROOT / "experiments/phase1").glob(pattern))


def norms_from_ckpt(path, kind):
    st = torch.load(path, map_location="cpu")["iface"]
    w = st["out.weight"] if "out.weight" in st else st["weight"]
    out = {"out_w_max_abs": float(w.abs().max()), "out_w_l2": float(w.norm())}
    if "rel" in st:
        out["rel_std"] = float(st["rel"].std())
    return out


def load(ctx, pattern, ref=False, kind=None):
    hits = [h for h in find(pattern) if (h / "logs/history.json").exists()]   # 走っている途中の run は数えない
    if len(hits) != 1:
        ctx.missing.append({"pattern": pattern, "found": [h.name for h in hits]})
        return None
    d = hits[0]
    m = json.loads((d / "metrics.json").read_text())
    pc = json.loads((d / "per_class_ap.json").read_text())
    hist = json.loads((d / "logs/history.json").read_text())
    cfg = yaml.safe_load((d / "config.yaml").read_text())
    for part in ("train", "val"):
        ctx.seen[part] |= set(cfg["videos"][part])
    probs = np.load(d / "predictions/val_probs_best.npz")
    arg = {v: probs[v].argmax(1) for v in probs}
    rec = {"run": d.name, "phase_jaccard": m["phase_jaccard"], "phase_accuracy": m["phase_accuracy"], "per_class_jaccard": pc,
           "six_phase_mean": six(pc, ctx.present), "per_video": m["per_video"], "epochs_run": m["epochs_run"],
           "best_epoch": m["best_epoch"], "lr_drop_epoch": m.get("lr_drop_epoch"), "stopped_epoch": m.get("early_stopped_epoch"),
           "reached_cap": m.get("reached_epoch_cap"), "history_val_jaccard": [h["val_jaccard"] for h in hist],
           "history_lr": [h.get("lr") for h in hist], "norms": m.get("norms"), "scope": cfg.get("scope", "W1"),
           "receiver_unchanged": m.get("receiver_unchanged"), "receiver_trained_changed": m.get("receiver_trained_changed"),
           "receiver_outside_scope_unchanged": m.get("receiver_outside_scope_unchanged"), "elapsed_seconds": m["elapsed_seconds"],
           "ckpt_norms": norms_from_ckpt(m["iface_ckpt"], kind), "result_selection": m.get("result_selection")}
    p2 = from_probs(d / "predictions/val_probs_best.npz", ctx.seqs, ctx.names, ctx.keep if ref else None)
    p2["six_phase_mean"] = six(p2["per_class_jaccard"], ctx.present)
    rec["path2"] = p2
    on = from_probs(d / "predictions/val_probs_best.npz", ctx.seqs, ctx.names, ctx.keep)
    on["six_phase_mean"] = six(on["per_class_jaccard"], ctx.present)
    rec["on_ref_rows"] = on
    rec["_arg"] = arg
    return rec


def dd(ctx, x, y, ref=False):
    a = x
    b = y["on_ref_rows"] if ref else y
    out = {k: a[k] - b[k] for k in KEYS}
    out["path2"] = {k: x["path2"][k] - (y["on_ref_rows"][k] if ref else y["path2"][k]) for k in KEYS}
    out["per_class"] = {n: a["per_class_jaccard"][n] - b["per_class_jaccard"][n] for n in ctx.present}
    out["per_video"] = {v: {k: a["per_video"][v][k] - b["per_video"][v][k] for k in ("phase_jaccard", "phase_accuracy")} for v in a["per_video"]}
    same = tot = 0
    for v in x["_arg"]:
        sel = ctx.keep[v] if ref else np.ones(len(x["_arg"][v]), bool)
        same += int((x["_arg"][v][sel] == y["_arg"][v][sel]).sum())
        tot += int(sel.sum())
    out["argmax_agree"] = same / tot
    out["identical_metrics"] = x["phase_jaccard"] == b["phase_jaccard"] and x["phase_accuracy"] == b["phase_accuracy"]
    return out


def block(ctx, runs, diffs, ref_labels=()):
    row = {"arms": {k: (v["run"] if v else None) for k, v in runs.items()}, "diffs": {}}
    for x, y in diffs:
        if runs.get(x) and runs.get(y):
            row["diffs"][f"{x} - {y}"] = dd(ctx, runs[x], runs[y], ref=x in ref_labels)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ctx = Ctx()
    out = {"task_id": "T-2026-11-09-grasp-pilot-converge", "p_alone": ctx.p_alone, "six_phases": [n for n in ctx.present if n != "dressing"],
           "runs": {"conv": {}, "prior": {}}, "case3": {}, "case5": {}, "caseA": {}}
    for regime, pre, suf in (("conv", "grasprc", "conv"), ("prior", "grasprt", "ep4")):
        for s in RT_SETTINGS:
            runs = {}
            for arm, lab in RT_ARMS.items():
                runs[lab] = load(ctx, f"{pre}_rt_*_RT-{s}_{arm}_{suf}_seed42", ref=lab.startswith("REF"), kind="rt")
                if runs[lab]:
                    out["runs"][regime][runs[lab]["run"]] = runs[lab]
            out["case3"].setdefault(s, {})[regime] = block(ctx, runs, RT_DIFFS, ("REF_GT", "REF_GTP"))
        for sc in ("W1", "W2", "W3"):
            for f in ("a", "b"):
                s0 = load(ctx, f"{pre}_tw_*_TW-{sc}-{f}-K64_empty_{suf}_seed42", kind="tw")
                s1 = load(ctx, f"{pre}_tw_*_TW-{sc}-{f}-K64_t1_{suf}_seed42", kind="tw")
                for r in (s0, s1):
                    if r:
                        out["runs"][regime][r["run"]] = r
                for L in (8, 32):
                    runs = {"S_0": s0, "S_1": s1}
                    for arm, lab in TW_ARMS.items():
                        runs[lab] = load(ctx, f"{pre}_tw_*_TW-{sc}-{f}-L{L}-K64_{arm}_{suf}_seed42", kind="tw")
                        if runs[lab]:
                            out["runs"][regime][runs[lab]["run"]] = runs[lab]
                    row = block(ctx, runs, TW_DIFFS)
                    if sc == "W1" and runs["S_W"]:
                        row["diffs"]["S_W - P 単独"] = {k: runs["S_W"][k] - ctx.p_alone[k] for k in KEYS}
                    if sc == "W1":
                        for arm, lab in (("gt", "REF_GT"), ("gtpred_CF", "REF_GTP")):
                            r = load(ctx, f"{pre}_tw_*_TW-W1-{f}-L{L}-K64_{arm}_{suf}_seed42", ref=True, kind="tw")
                            if r:
                                out["runs"][regime][r["run"]] = r
                                if s0:
                                    row["diffs"][f"{lab} - S_0"] = dd(ctx, r, s0, ref=True)
                    out["case5"].setdefault(f"{sc}-{f}-L{L}", {})[regime] = row
        gpre, gsuf = ("grasprc_ga_*", "conv") if regime == "conv" else ("grasparms_dp_*", "ep4")
        runs = {lab: load(ctx, f"{gpre}_GA-noflag_{arm}_{gsuf}_seed42", kind="ga")
                for arm, lab in (("empty", "空"), ("pred_noCF", "予測-noCF"), ("shuffle", "入れ替え"))}
        for r in runs.values():
            if r:
                out["runs"][regime][r["run"]] = r
        out["caseA"][regime] = block(ctx, runs, [("予測-noCF", "空"), ("予測-noCF", "入れ替え")])
    # 処方で符号が変わった差
    flips = {"case3": [], "case5": [], "caseA": []}
    for case in ("case3", "case5"):
        for s, r in out[case].items():
            for n, d in r["conv"]["diffs"].items():
                p = r["prior"]["diffs"].get(n)
                if p and "six_phase_mean" in d and np.sign(d["six_phase_mean"]) != np.sign(p["six_phase_mean"]):
                    flips[case].append(f"{s} {n}")
    for n, d in out["caseA"]["conv"]["diffs"].items():
        p = out["caseA"]["prior"]["diffs"].get(n)
        if p and np.sign(d["six_phase_mean"]) != np.sign(p["six_phase_mean"]):
            flips["caseA"].append(n)
    out["sign_flips"] = flips
    # 検証
    recheck, ident = [], {"conv": [0, 0], "prior": [0, 0]}
    for case in ("case3", "case5"):
        for r in out[case].values():
            for regime in ("conv", "prior"):
                for d in r[regime]["diffs"].values():
                    if "path2" in d:
                        recheck += [abs(d[k] - d["path2"][k]) for k in KEYS]
                        ident[regime][0] += int(d["identical_metrics"])
                        ident[regime][1] += 1
    for regime in ("conv", "prior"):
        for d in out["caseA"][regime]["diffs"].values():
            recheck += [abs(d[k] - d["path2"][k]) for k in KEYS]
            ident[regime][0] += int(d["identical_metrics"])
            ident[regime][1] += 1
    first = out["case3"][RT_SETTINGS[0]]["conv"]["diffs"]["TG - T0"]
    bad = copy.deepcopy(first)
    bad["phase_jaccard"] += 1e-6
    conv = out["runs"]["conv"]
    w23 = [r for r in conv.values() if r["scope"] in ("W2", "W3")]
    vids = sorted(ctx.seen["train"] | ctx.seen["val"])
    out["checks"] = {
        "f_conv_runs": len(conv), "f_expected": 127, "f_prior_runs": len(out["runs"]["prior"]), "missing": ctx.missing,
        "f_all_converge": all(r["result_selection"] == "best_val_jaccard" for r in conv.values()),
        "f_bogus_found": [len(find("grasprc_rt_*_RT-layer9-roi-K7_empty_conv_seed42")), len(find("grasprc_tw_*_no_such_arm_conv_seed42"))],
        "g_recheck_n": len(recheck), "g_recheck_max_abs_diff": max(recheck) if recheck else None,
        "g_shifted_copy_detected": abs(bad["phase_jaccard"] - bad["path2"]["phase_jaccard"]) > 1e-9,
        "g_identical_metrics_pairs": {k: {"identical": v[0], "pairs": v[1]} for k, v in ident.items()},
        "h_videos": vids, "h_common_with_test": sorted(set(vids) & C.TEST_VIDEOS),
        "h_control_with_04": sorted(set(vids + ["04"]) & C.TEST_VIDEOS),
        "w1_receiver_unchanged": all(r["receiver_unchanged"] for r in conv.values() if r["scope"] == "W1"),
        "w23_trained_changed": all(r["receiver_trained_changed"] for r in w23),
        "w23_outside_unchanged": all(r["receiver_outside_scope_unchanged"] for r in w23),
        "e_out_w_max_abs_over_prior_max_0.021": sum(r["ckpt_norms"]["out_w_max_abs"] > 0.021 for r in conv.values()),
        "e_not_over": sorted(r["run"] for r in conv.values() if r["ckpt_norms"]["out_w_max_abs"] <= 0.021),
    }
    for regime in ("conv", "prior"):
        for r in out["runs"][regime].values():
            r.pop("_arg", None)
    for case in ("case3", "case5"):
        for r in out[case].values():
            for regime in ("conv", "prior"):
                r[regime]["arms"] = {k: v for k, v in r[regime]["arms"].items()}
    out["videos_seen"] = {p: sorted(v) for p, v in ctx.seen.items()}
    C.write_json(a.out, out)
    print(json.dumps(out["checks"], ensure_ascii=False, indent=1))
    print(json.dumps(out["sign_flips"], ensure_ascii=False))


if __name__ == "__main__":
    main()

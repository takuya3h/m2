"""案 5 の集計と検証（T-2026-11-09-grasp-roitoken-transition-pilot、利用者の依頼で追加）。本体の .venv。GPU を使わない。

f_aggregate.py（案 3）と同じ経路 1（metrics・per_class_ap・history・config）と経路 2（val の確率の argmax を測り直す）。
差（SPEC §5.1 の 3）は**同じ W の中でだけ**: S_W − S_0、S_W − S_1、S_W − S_W-perm、S_W − S_W-R、S_W − S_W-U（形 × L ごと）。
W1 だけ S_W − P 単独。W2・W3 では塔単独との差を書かない、W の間の差も取らない。
参照段（W1）: 正解 − S_0・正解 ⊕ 予測 − S_0 と、正解 − S_W・正解 ⊕ 予測 − S_W（S_0・S_W は把持の注釈のある val 1,514 行に絞って測り直す）。

    .venv/bin/python f_aggregate5.py --rt-dir <S> --out <S>/f/summary5.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).parent))
import f_aggregate as F  # noqa: E402
from f_aggregate import KEYS, ROOT, C, from_probs, six  # noqa: E402

SCOPES, FORMS, LS = ("W1", "W2", "W3"), ("a", "b"), (8, 32)
WIN_ARMS = {"pred_CF": "S_W", "perm": "S_W-perm", "union": "S_W-U", "shuffle": "S_W-R"}
DIFFS = [("S_W", "S_0"), ("S_W", "S_1"), ("S_W", "S_W-perm"), ("S_W", "S_W-R"), ("S_W", "S_W-U")]


def find(name):
    return sorted((ROOT / "experiments/phase1").glob(f"grasprt_tw_*_{name}_ep4_seed42"))


def record(d, seqs, names, present, keep, ref):
    m = json.loads((d / "metrics.json").read_text())
    pc = json.loads((d / "per_class_ap.json").read_text())
    hist = json.loads((d / "logs/history.json").read_text())
    cfg = yaml.safe_load((d / "config.yaml").read_text())
    rec = {"run": d.name, "phase_jaccard": m["phase_jaccard"], "phase_accuracy": m["phase_accuracy"],
           "per_class_jaccard": pc, "six_phase_mean": six(pc, present), "per_video": m["per_video"],
           "epochs": [h["epoch"] for h in hist], "history": hist, "result_epoch": m.get("result_epoch"),
           "receiver_unchanged": m["receiver_unchanged"], "receiver_trained_changed": m.get("receiver_trained_changed"),
           "receiver_outside_scope_unchanged": m.get("receiver_outside_scope_unchanged"),
           "elapsed_seconds": m["elapsed_seconds"], "iface_params": m["iface_params"], "videos": cfg["videos"],
           "scope": cfg.get("scope")}
    p2 = from_probs(d / "predictions/val_probs_best.npz", seqs, names, keep if ref else None)
    p2["six_phase_mean"] = six(p2["per_class_jaccard"], present)
    rec["path2"] = p2
    on = from_probs(d / "predictions/val_probs_best.npz", seqs, names, keep)
    on["six_phase_mean"] = six(on["per_class_jaccard"], present)
    rec["on_ref_rows"] = on
    return rec


def dd(x, y, present, xkey=None, ykey=None):
    a = x if xkey is None else x[xkey]
    b = y if ykey is None else y[ykey]
    out = {k: a[k] - b[k] for k in KEYS}
    out["per_class"] = {n: a["per_class_jaccard"][n] - b["per_class_jaccard"][n] for n in present}
    out["per_video"] = {v: {k: a["per_video"][v][k] - b["per_video"][v][k] for k in ("phase_jaccard", "phase_accuracy")}
                        for v in a["per_video"]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rt-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names = C.phase_names()
    split = C.fold_a()
    seqs = C.phase_sequences(split["val"])
    present = [names[c] for c in sorted(set(np.concatenate([y for _, _, y in seqs]).tolist()))]
    has = np.load(Path(a.rt_dir) / "b4/has_gt_val.npy")
    keep, k = {}, 0
    for video, fs, _ in seqs:
        keep[video] = has[k:k + len(fs)]
        k += len(fs)
    tower = json.loads((Path(a.rt_dir) / "b/b12.json").read_text())["tower_alone_val"]
    p_alone = {"phase_jaccard": tower["phase_jaccard"], "phase_accuracy": tower["phase_accuracy"],
               "six_phase_mean": six(tower["per_class_jaccard"], present), "per_class_jaccard": tower["per_class_jaccard"],
               "per_video": None}
    out = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "case": 5, "six_phases": [n for n in present if n != "dressing"],
           "p_alone": p_alone, "runs": {}, "settings": {}, "reference": {}, "missing": []}
    seen = {"train": set(), "val": set()}
    recheck = []

    def get(name, ref=False):
        hits = find(name)
        if len(hits) != 1:
            out["missing"].append({"name": name, "found": [h.name for h in hits]})
            return None
        r = record(hits[0], seqs, names, present, keep, ref)
        for part in ("train", "val"):
            seen[part] |= set(r["videos"][part])
        out["runs"][name] = r
        return r
    for sc in SCOPES:
        for f in FORMS:
            s0 = get(f"TW-{sc}-{f}-K64_empty")
            s1 = get(f"TW-{sc}-{f}-K64_t1")
            for L in LS:
                arms = {"S_0": s0, "S_1": s1}
                for arm, lab in WIN_ARMS.items():
                    arms[lab] = get(f"TW-{sc}-{f}-L{L}-K64_{arm}")
                row = {"arms": {lab: (r["run"] if r else None) for lab, r in arms.items()}, "diffs": {}, "diffs_path2": {}}
                for x, y in DIFFS:
                    if arms[x] and arms[y]:
                        row["diffs"][f"{x} - {y}"] = dd(arms[x], arms[y], present)
                        row["diffs_path2"][f"{x} - {y}"] = {kk: arms[x]["path2"][kk] - arms[y]["path2"][kk] for kk in KEYS}
                if sc == "W1" and arms["S_W"]:
                    row["diffs"]["S_W - P 単独"] = {kk: arms["S_W"][kk] - p_alone[kk] for kk in KEYS}
                    row["diffs_path2"]["S_W - P 単独"] = {kk: arms["S_W"]["path2"][kk] - p_alone[kk] for kk in KEYS}
                for name, d in row["diffs_path2"].items():
                    for kk in KEYS:
                        recheck.append(abs(row["diffs"][name][kk] - d[kk]))
                out["settings"][f"{sc}-{f}-L{L}"] = row
    for f in FORMS:
        for L in LS:
            s0 = out["runs"].get(f"TW-W1-{f}-K64_empty")
            sw = out["runs"].get(f"TW-W1-{f}-L{L}-K64_pred_CF")
            row = {"diffs": {}, "arms": {}}
            for arm, lab in (("gt", "正解"), ("gtpred_CF", "正解 ⊕ 予測")):
                r = get(f"TW-W1-{f}-L{L}-K64_{arm}", ref=True)
                if r is None:
                    continue
                row["arms"][lab] = r["run"]
                if s0:
                    row["diffs"][f"{lab} - S_0"] = dd(r, s0, present, ykey="on_ref_rows")
                    recheck += [abs(row["diffs"][f"{lab} - S_0"][kk] - (r["path2"][kk] - s0["on_ref_rows"][kk])) for kk in KEYS]
                if sw:
                    row["diffs"][f"{lab} - S_W"] = dd(r, sw, present, ykey="on_ref_rows")
            out["reference"][f"W1-{f}-L{L}"] = row
    runs = out["runs"]
    test = sorted(C.TEST_VIDEOS)
    first = next(iter(out["settings"].values()))
    bad = copy.deepcopy(first["diffs"]["S_W - S_0"])
    bad["phase_jaccard"] += 1e-6
    out["videos_seen"] = {p: sorted(v) for p, v in seen.items()}
    vids = out["videos_seen"]["train"] + out["videos_seen"]["val"]
    w23 = [r for r in runs.values() if r["scope"] in ("W2", "W3")]
    out["checks"] = {
        "g_runs": len(runs), "g_expected": 68, "g_missing": len(out["missing"]),
        "g_all_4_epochs_final_state": all(r["epochs"] == [1, 2, 3, 4] and r["result_epoch"] == 4 for r in runs.values()),
        "g_bogus_names_found": [len(find("TW-W9-a-L8-K64_pred_CF")), len(find("TW-W1-a-L8-K64_no_such_arm"))],
        "h_recheck_n": len(recheck), "h_recheck_max_abs_diff": max(recheck) if recheck else None,
        "h_shifted_copy_detected": abs(bad["phase_jaccard"] - first["diffs_path2"]["S_W - S_0"]["phase_jaccard"]) > 1e-9,
        "i_common_with_test": sorted(set(vids) & set(test)), "i_control_with_04": sorted(set(vids + ["04"]) & set(test)),
        "w1_receiver_unchanged": all(r["receiver_unchanged"] for r in runs.values() if r["scope"] in (None, "W1")),
        "w23_receiver_trained_changed": all(r["receiver_trained_changed"] for r in w23),
        "w23_receiver_outside_scope_unchanged": all(r["receiver_outside_scope_unchanged"] for r in w23),
        "n_w23": len(w23),
    }
    C.write_json(a.out, out)
    print(json.dumps(out["checks"], ensure_ascii=False, indent=1))
    print(json.dumps(out["missing"], ensure_ascii=False))
    for s, r in out["settings"].items():
        print(s, {k2: [round(v[k3], 4) for k3 in KEYS] for k2, v in r["diffs"].items()})
    for s, r in out["reference"].items():
        print(s, {k2: [round(v[k3], 4) for k3 in KEYS] for k2, v in r["diffs"].items()})


if __name__ == "__main__":
    _ = F
    main()

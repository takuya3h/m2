"""Task F 集計と検証（T-2026-11-09-grasp-roitoken-transition-pilot、案 3 だけ）。本体の .venv。GPU を使わない。

各 run の metrics.json・per_class_ap.json・logs/history.json・config.yaml から表を作る（経路 1）。差（§5.1 の 2）:
TG − T0、TG − TRand、TG − TGeo、TG − TU（主の行 1,515）、参照段 − T0（把持の注釈のある val 1,514 行。T0 はその run の
val の確率の argmax をその行に絞って測り直す）。指標は macro Jaccard・accuracy・dressing を除く 6 工程の平均・クラス別・動画ごと。

検証（§7 の g・h・i）:
  g  56 本の存在、各 run の history が 4 epoch、epoch ごとの val の値。存在しない run の名前 2 つで 0 件
  h  差を各 run の val の確率（predictions/val_probs_best.npz）の argmax から PhaseEvaluator で測り直した値（経路 2）で計算し直して一致。
     1e-6 ずらした写しで不一致
  i  各 run の config の videos（train・val）と {04, 05, 07} の共通 0 件。04 を混ぜた入力で共通 1 件

    .venv/bin/python f_aggregate.py --rt-dir <S> --out <S>/f/summary.json
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402

LAYERS, CONTENTS, KS = ("layer4", "layer3"), ("roi_geo", "roi"), (16, 64)
ARMS = {"empty": "T0", "pred_CF": "TG", "geo": "TGeo", "union": "TU", "shuffle": "TRand", "gt": "REF_GT", "gtpred_CF": "REF_GTP"}
DIFFS = [("TG", "T0"), ("TG", "TRand"), ("TG", "TGeo"), ("TG", "TU")]
KEYS = ("phase_jaccard", "phase_accuracy", "six_phase_mean")


def run_dir(setting, arm):
    hits = sorted((ROOT / "experiments/phase1").glob(f"grasprt_rt_*_RT-{setting}_{arm}_ep4_seed42"))
    return hits


def six(per_class, present):
    return float(np.mean([per_class[n] for n in present if n != "dressing"]))


def from_probs(path, seqs, names, keep=None):
    """経路 2: val の確率の argmax を PhaseEvaluator で測る。keep は動画 → 行の印（参照段の行）。"""
    probs = np.load(path)
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    per_video = {}
    for video, _, y in seqs:
        pred = probs[video].argmax(1)
        yy = y
        if keep is not None:
            pred, yy = pred[keep[video]], y[keep[video]]
        ev.update(pred, yy, video_id=video)
        one = PhaseEvaluator(num_classes=len(names), class_names=names)
        one.update(pred, yy, video_id=video)
        r1 = one.compute()
        per_video[video] = {"phase_jaccard": r1["phase_jaccard"], "phase_accuracy": r1["phase_accuracy"]}
    r = ev.compute()
    return {"phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
            "per_class_jaccard": r["phase_per_class_jaccard"], "per_video": per_video}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rt-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    names = C.phase_names()
    split = C.fold_a()
    seqs = C.phase_sequences(split["val"])
    present = [names[c] for c in sorted(set(np.concatenate([y for _, _, y in seqs]).tolist()))]
    frames = [f for _, fs, _ in seqs for f in fs]
    has = np.load(Path(a.rt_dir) / "b4/has_gt_val.npy")
    assert [str(f) for f in np.load(Path(a.rt_dir) / "b4/frame_ids_val.npy")] == frames
    keep, k = {}, 0
    for video, fs, _ in seqs:
        keep[video] = has[k:k + len(fs)]
        k += len(fs)
    tower = json.loads((Path(a.rt_dir) / "b/b12.json").read_text())["tower_alone_val"]
    p_alone = {"phase_jaccard": tower["phase_jaccard"], "phase_accuracy": tower["phase_accuracy"],
               "six_phase_mean": six(tower["per_class_jaccard"], present), "per_class_jaccard": tower["per_class_jaccard"]}
    out = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "six_phases": [n for n in present if n != "dressing"],
           "p_alone": p_alone, "settings": {}, "missing": [], "videos_seen": {"train": set(), "val": set()}}
    recheck = []
    for layer in LAYERS:
        for content in CONTENTS:
            for kk in KS:
                setting = f"{layer}-{content}-K{kk}"
                row = {"arms": {}, "diffs": {}, "diffs_path2": {}}
                for arm, label in ARMS.items():
                    hits = run_dir(setting, arm)
                    if len(hits) != 1:
                        out["missing"].append({"setting": setting, "arm": arm, "found": [h.name for h in hits]})
                        continue
                    d = hits[0]
                    m = json.loads((d / "metrics.json").read_text())
                    pc = json.loads((d / "per_class_ap.json").read_text())
                    pc = pc.get("per_class", pc) if isinstance(pc, dict) else pc
                    hist = json.loads((d / "logs/history.json").read_text())
                    cfg = yaml.safe_load((d / "config.yaml").read_text())
                    for part in ("train", "val"):
                        out["videos_seen"][part] |= set(cfg["videos"][part])
                    rec = {"run": d.name, "phase_jaccard": m["phase_jaccard"], "phase_accuracy": m["phase_accuracy"],
                           "per_class_jaccard": pc, "six_phase_mean": six(pc, present), "per_video": m["per_video"],
                           "epochs": [h["epoch"] for h in hist], "history": hist, "result_epoch": m.get("result_epoch"),
                           "init_phase_jaccard": m["init_phase_jaccard"], "receiver_unchanged": m["receiver_unchanged"],
                           "elapsed_seconds": m["elapsed_seconds"], "iface_params": m["iface_params"],
                           "rowmask_rows": cfg.get("rowmask_rows")}
                    p2 = from_probs(d / "predictions/val_probs_best.npz", seqs, names,
                                    keep if arm in ("gt", "gtpred_CF") else None)
                    p2["six_phase_mean"] = six(p2["per_class_jaccard"], present)
                    rec["path2"] = p2
                    if arm == "empty":
                        t0r = from_probs(d / "predictions/val_probs_best.npz", seqs, names, keep)
                        t0r["six_phase_mean"] = six(t0r["per_class_jaccard"], present)
                        rec["on_ref_rows"] = t0r
                    row["arms"][label] = rec
                arms = row["arms"]
                for x, y in DIFFS:
                    if x in arms and y in arms:
                        row["diffs"][f"{x}-{y}"] = {k2: arms[x][k2] - arms[y][k2] for k2 in KEYS}
                        row["diffs"][f"{x}-{y}"]["per_class"] = {n: arms[x]["per_class_jaccard"][n] - arms[y]["per_class_jaccard"][n]
                                                                for n in present}
                        row["diffs"][f"{x}-{y}"]["per_video"] = {v: {k2: arms[x]["per_video"][v][k2] - arms[y]["per_video"][v][k2]
                                                                     for k2 in ("phase_jaccard", "phase_accuracy")}
                                                                 for v in arms[x]["per_video"]}
                        row["diffs_path2"][f"{x}-{y}"] = {k2: arms[x]["path2"][k2] - arms[y]["path2"][k2] for k2 in KEYS}
                for ref in ("REF_GT", "REF_GTP"):
                    if ref in arms and "T0" in arms:
                        t0 = arms["T0"]["on_ref_rows"]
                        row["diffs"][f"{ref}-T0"] = {k2: arms[ref][k2] - t0[k2] for k2 in KEYS}
                        row["diffs"][f"{ref}-T0"]["per_class"] = {n: arms[ref]["per_class_jaccard"][n] - t0["per_class_jaccard"][n]
                                                                  for n in present}
                        row["diffs"][f"{ref}-T0"]["per_video"] = {v: {k2: arms[ref]["per_video"][v][k2] - t0["per_video"][v][k2]
                                                                      for k2 in ("phase_jaccard", "phase_accuracy")}
                                                                  for v in arms[ref]["per_video"]}
                        row["diffs_path2"][f"{ref}-T0"] = {k2: arms[ref]["path2"][k2] - t0[k2] for k2 in KEYS}
                for name, dd in row["diffs"].items():
                    for k2 in KEYS:
                        recheck.append(abs(dd[k2] - row["diffs_path2"][name][k2]))
                out["settings"][setting] = row
    n_runs = sum(len(r["arms"]) for r in out["settings"].values())
    epochs_ok = all(rec["epochs"] == [1, 2, 3, 4] and rec["result_epoch"] == 4
                    for r in out["settings"].values() for rec in r["arms"].values())
    bogus = [len(run_dir("layer9-roi-K7", "empty")), len(run_dir("layer4-roi_geo-K16", "no_such_arm"))]
    # h の陽性対照: 1e-6 ずらした写し
    first = next(iter(out["settings"].values()))
    bad = copy.deepcopy(first["diffs"]["TG-T0"])
    bad["phase_jaccard"] += 1e-6
    shifted_detect = abs(bad["phase_jaccard"] - first["diffs_path2"]["TG-T0"]["phase_jaccard"]) > 1e-9
    seen = {p: sorted(v) for p, v in out["videos_seen"].items()}
    test = sorted(C.TEST_VIDEOS)
    out["videos_seen"] = seen
    out["checks"] = {
        "g_runs": n_runs, "g_expected": 56, "g_all_4_epochs_final_state": epochs_ok, "g_bogus_names_found": bogus,
        "h_recheck_max_abs_diff": max(recheck) if recheck else None, "h_recheck_n": len(recheck),
        "h_recheck_equal_1e-9": bool(recheck) and max(recheck) <= 1e-9, "h_shifted_copy_detected": shifted_detect,
        "i_common_with_test": sorted(set(seen["train"] + seen["val"]) & set(test)),
        "i_control_with_04": sorted(set(seen["train"] + seen["val"] + ["04"]) & set(test)),
        "receiver_unchanged_all": all(rec["receiver_unchanged"] for r in out["settings"].values() for rec in r["arms"].values()),
    }
    C.write_json(a.out, out)
    print(json.dumps(out["checks"], ensure_ascii=False, indent=1))
    print(json.dumps(out["missing"], ensure_ascii=False))
    for s, r in out["settings"].items():
        print(s, {k2: [round(v[k3], 4) for k3 in KEYS] for k2, v in r["diffs"].items()})


if __name__ == "__main__":
    main()

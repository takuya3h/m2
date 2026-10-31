"""読み出しの検査（非公式 T-2026-10-31-grasp-pilot-probe、Task C-3・C-5）。本体の .venv（sklearn）で動かす。

    phase   工程塔の凍結特徴（PT_CACHE の注釈のあるフレーム）から g を読む（C-3）
    det     検出塔の decoder の最終層の出力（正解の枠に対応づけた query）から s（τ = 0.1、4 クラス）を読む（C-5）

正則化の強さは測る前に一つに決めた（REG）。val の値で選び直さない。特徴は train で標準化する。
陰性対照: train の標的を並べ替えたもの（seed 42・123・456）、同じ形の乱数の特徴（seed 42）。
§8-e の空振りの確認: 標的そのものを特徴に足すと val の値がほぼ完全になること。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    r2_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402

REG = {"logistic_C": 1.0, "ridge_alpha": 1.0, "max_iter": 3000}
SEEDS = (42, 123, 456)


def std(xtr, xva):
    sc = StandardScaler().fit(xtr)
    return sc.transform(xtr), sc.transform(xva)


def binary(xtr, ytr, xva, yva):
    if len(set(ytr)) < 2:
        return {"auc": None, "ap": None, "note": "train に一つのクラスしか無い"}
    m = LogisticRegression(C=REG["logistic_C"], max_iter=REG["max_iter"]).fit(xtr, ytr)
    p = m.predict_proba(xva)[:, 1]
    ok = len(set(yva)) == 2
    return {"auc": float(roc_auc_score(yva, p)) if ok else None, "ap": float(average_precision_score(yva, p)) if ok else None,
            "val_pos_rate": float(np.mean(yva)), "n_train": int(len(ytr)), "n_val": int(len(yva))}


def ridge(xtr, ytr, xva, yva):
    m = Ridge(alpha=REG["ridge_alpha"]).fit(xtr, ytr)
    return {"r2": float(r2_score(yva, m.predict(xva))), "n_train": int(len(ytr)), "n_val": int(len(yva))}


def multiclass(xtr, ytr, xva, yva, labels):
    m = LogisticRegression(C=REG["logistic_C"], max_iter=REG["max_iter"]).fit(xtr, ytr)
    p = m.predict(xva)
    return {"balanced_accuracy": float(balanced_accuracy_score(yva, p)),
            "macro_f1": float(f1_score(yva, p, labels=labels, average="macro", zero_division=0)),
            "confusion": confusion_matrix(yva, p, labels=labels).tolist(), "labels": [int(x) for x in labels],
            "n_train": int(len(ytr)), "n_val": int(len(yva))}


def g_targets(g):
    """g（N, 14）→ 標的ごとの (値, 測るフレームの印)。重心は対象が在るフレームだけ。"""
    out = {}
    for i in G.G_BINARY:
        out[G.G_NAMES[i]] = ("bin", (g[:, i] > 0).astype(int), np.ones(len(g), bool))
    present = {"L": g[:, 1] > 0, "R": g[:, 6] > 0, "B": g[:, 10] > 0}
    for i, n in enumerate(G.G_NAMES):
        if i in G.G_BINARY:
            continue
        side = n[0]
        mask = present[side] if n.endswith(("cx", "cy")) else np.ones(len(g), bool)
        out[n] = ("cont", g[:, i], mask)
    return out


def run_targets(feats_tr, feats_va, targets_tr, targets_va, perm_seed=None):
    res = {}
    for name, (kind, ytr, mtr) in targets_tr.items():
        _, yva, mva = targets_va[name]
        y = ytr[mtr]
        if perm_seed is not None:
            y = np.random.default_rng(perm_seed).permutation(y)
        xtr, xva = feats_tr[mtr], feats_va[mva]
        res[name] = binary(xtr, y, xva, yva[mva]) if kind == "bin" else ridge(xtr, y, xva, yva[mva])
    return res


def cmd_phase(a):
    fold = C.fold_a()
    feats = C.load_features()
    seqs = {v: (fr, lab) for v, fr, lab in C.phase_sequences(fold["train"] + fold["val"])}
    data = {}
    for part in ("train", "val"):
        with np.load(Path(a.signals) / f"g_{part}.npz") as d:
            ids, g, flag = [str(x) for x in d["frame_ids"]], d["x"], d["flag"]
        keep = flag > 0
        frames = [f for f, k in zip(ids, keep) if k]
        lab = {f: l for v in fold[part] for f, l in zip(*seqs[v])}
        data[part] = {"frames": frames, "g": g[keep], "x": np.stack([feats[f] for f in frames]),
                      "phase": np.eye(9)[[lab[f] for f in frames]],
                      "videos": C.assert_no_test(frames, f"probe_phase/{part}")}
    # 陽性対照: 術具の正解の在否（15 クラス）。train と val の両方で正例と負例があるクラスだけ
    tool = {}
    for part in ("train", "val"):
        raw = json.loads((C.DET_ANN_A / f"instances_{part}.json").read_text())
        imgs = {im["id"]: Path(im["file_name"]).stem for im in raw["images"]}
        y = {f: np.zeros(15, int) for f in data[part]["frames"]}
        for an in raw["annotations"]:
            f = imgs[an["image_id"]]
            if f in y:
                y[f][an["category_id"]] = 1
        tool[part] = np.stack([y[f] for f in data[part]["frames"]])
        names = {c["id"]: c["name"] for c in raw["categories"]}
    rates = {names[c]: {"train": float(tool["train"][:, c].mean()), "val": float(tool["val"][:, c].mean())} for c in range(15)}
    usable = [c for c in range(15) if 0 < tool["train"][:, c].mean() < 1 and 0 < tool["val"][:, c].mean() < 1]
    tt, tv = g_targets(data["train"]["g"]), g_targets(data["val"]["g"])
    xtr, xva = std(data["train"]["x"], data["val"]["x"])
    res = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True, "reg": REG,
           "videos": {p: data[p]["videos"] for p in data}, "n": {p: len(data[p]["frames"]) for p in data},
           "features": str(C.PT_CACHE), "features_sha256": C.sha256(C.PT_CACHE),
           "main": run_targets(xtr, xva, tt, tv)}
    res["positive_control_tool_presence"] = {
        "class_rates": rates, "used_classes": [names[c] for c in usable],
        "results": {names[c]: binary(xtr, tool["train"][:, c], xva, tool["val"][:, c]) for c in usable}}
    res["negative_permuted"] = {str(s): run_targets(xtr, xva, tt, tv, perm_seed=s) for s in SEEDS}
    rng = np.random.default_rng(42)
    rtr, rva = rng.standard_normal(xtr.shape), rng.standard_normal(xva.shape)
    res["negative_random_features"] = run_targets(rtr, rva, tt, tv)
    ptr, pva = data["train"]["phase"], data["val"]["phase"]
    res["baseline_phase_onehot"] = run_targets(ptr, pva, tt, tv)
    # §8-e: 標的そのものを特徴に足す（二値の 5 個だけ）
    leak = {}
    for name in [G.G_NAMES[i] for i in G.G_BINARY]:
        _, ytr, _ = tt[name]
        _, yva, _ = tv[name]
        leak[name] = binary(np.c_[xtr, ytr * 10.0], ytr, np.c_[xva, yva * 10.0], yva)
    res["check_target_appended"] = leak
    C.write_json(a.out, res)
    short = {k: {n: (v.get("auc") if "auc" in v else v.get("r2")) for n, v in res[k].items()}
             for k in ("main", "negative_random_features", "baseline_phase_onehot")}
    short["perm42"] = {n: (v.get("auc") if "auc" in v else v.get("r2")) for n, v in res["negative_permuted"]["42"].items()}
    short["leak"] = {n: v["auc"] for n, v in leak.items()}
    short["tool_pc"] = {n: v["auc"] for n, v in res["positive_control_tool_presence"]["results"].items()}
    print(json.dumps(short, ensure_ascii=False, indent=1))


def cmd_det(a):
    data = {}
    for p in ("train", "val"):
        parts = [dict(np.load(f)) for f in sorted(Path(a.feats).glob(f"decfeat_{p}_*.npz"))]
        data[p] = {k: np.concatenate([q[k] for q in parts]) for k in ("ann_ids", "cats", "stems", "matched", "feat")}
    out = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True, "reg": REG, "tau": 0.1}
    xs, ys, cs = {}, {}, {}
    for p, d in data.items():
        bs = np.load(Path(a.signals) / f"boxstate_{p}.npz")
        r_by = {int(i): r for i, r in zip(bs["ann_ids"], bs["r"])}
        ann_by = {int(i): bool(v) for i, v in zip(bs["ann_ids"], bs["annotated"])}
        d["annotated"] = np.array([ann_by[int(i)] for i in d["ann_ids"]])
        keep = d["matched"] & d["annotated"]
        r = np.array([r_by[int(i)] for i in d["ann_ids"][keep]])
        _, s, _ = G.box_state(r, 0.1)
        xs[p], ys[p], cs[p] = d["feat"][keep].astype(np.float64), s, d["cats"][keep]
        out[f"{p}_counts"] = {"boxes": int(len(d["ann_ids"])), "unmatched": int((~d["matched"]).sum()),
                              "no_annotation": int((~d["annotated"]).sum()), "used": int(keep.sum()),
                              "state_counts": {G.STATE_NAMES[k]: int((s == k).sum()) for k in range(4)}}
        out[f"{p}_videos"] = C.assert_no_test([str(x) for x in d["stems"]], f"probe_det/{p}")
    labels = [0, 1, 2, 3]
    xtr, xva = std(xs["train"], xs["val"])
    oh = np.eye(15)
    out["main"] = multiclass(xtr, ys["train"], xva, ys["val"], labels)
    maj = np.bincount(ys["train"], minlength=4).argmax()
    pm = np.full(len(ys["val"]), maj)
    out["baseline_majority"] = {"class": int(maj), "balanced_accuracy": float(balanced_accuracy_score(ys["val"], pm)),
                                "macro_f1": float(f1_score(ys["val"], pm, labels=labels, average="macro", zero_division=0))}
    out["baseline_class_onehot"] = multiclass(oh[cs["train"]], ys["train"], oh[cs["val"]], ys["val"], labels)
    out["baseline_feat_and_class"] = multiclass(np.c_[xtr, oh[cs["train"]]], ys["train"], np.c_[xva, oh[cs["val"]]],
                                                ys["val"], labels)
    present = sorted(set(cs["train"]) & set(cs["val"]))
    out["positive_control_class"] = multiclass(xtr, cs["train"], xva, cs["val"], present)
    out["negative_permuted"] = {str(sd): multiclass(xtr, np.random.default_rng(sd).permutation(ys["train"]), xva,
                                                    ys["val"], labels) for sd in SEEDS}
    rng = np.random.default_rng(42)
    out["negative_random_features"] = multiclass(rng.standard_normal(xtr.shape), ys["train"],
                                                 rng.standard_normal(xva.shape), ys["val"], labels)
    out["check_target_appended"] = multiclass(np.c_[xtr, np.eye(4)[ys["train"]] * 10], ys["train"],
                                              np.c_[xva, np.eye(4)[ys["val"]] * 10], ys["val"], labels)
    C.write_json(a.out, out)
    print(json.dumps({k: (v.get("balanced_accuracy"), v.get("macro_f1")) for k, v in out.items()
                      if isinstance(v, dict) and "balanced_accuracy" in v}, indent=1))
    print({k: out[k] for k in ("train_counts", "val_counts")})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("phase")
    p.add_argument("--signals", required=True)
    p.add_argument("--out", required=True)
    d = sub.add_parser("det")
    d.add_argument("--signals", required=True)
    d.add_argument("--feats", required=True)
    d.add_argument("--out", required=True)
    a = ap.parse_args()
    {"phase": cmd_phase, "det": cmd_det}[a.cmd](a)


if __name__ == "__main__":
    main()

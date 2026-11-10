"""Task B-3 の診断（T-2026-11-09-grasp-pilot-converge）。候補を足すのではなく、試した 2 つの処方の陽性対照の中身を見る。

各候補（C = 1.0・0.1）の陽性対照（P の特徴 2048 ＋ 正解の工程の one-hot 9）について、train の正解率、重みの L2 のうち
one-hot の 9 列が占める割合、val の macro Jaccard を出す。経路の確かめとして one-hot だけ（9 次元）の層の val も出す。

    .venv/bin/python b3_diag.py --out <S>/b/b3_diag.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "experiments/analysis/grasp_roitoken_transition_pilot/tools"))
import c_kill as K  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from sklearn.linear_model import LogisticRegression
    names = K.C.phase_names()
    feats = K.C.load_features()
    d = {}
    for part in ("train", "val"):
        fr, y = K.labels_frames(part)
        g = np.stack([feats[f] for f in fr])
        d[part] = (g, np.eye(len(names), dtype=np.float32)[y], y, fr)
    (gt_, ot, yt, _), (gv, ov, yv, fv) = d["train"], d["val"]
    out = {"task_id": "T-2026-11-09-grasp-pilot-converge", "cases": {}}
    for name, xt, xv, C in (("onehot_only_C1", ot, ov, 1.0), ("feat+onehot_C1", np.c_[gt_, ot], np.c_[gv, ov], 1.0),
                            ("feat+onehot_C0.1", np.c_[gt_, ot], np.c_[gv, ov], 0.1)):
        mu, sd = xt.mean(0), xt.std(0)
        sd[sd < 1e-6] = 1.0
        clf = LogisticRegression(C=C, max_iter=3000, class_weight="balanced").fit((xt - mu) / sd, yt)
        w = clf.coef_
        share = float(np.linalg.norm(w[:, -9:]) / np.linalg.norm(w))
        r = K.metrics(clf.predict((xv - mu) / sd), yv, fv, names)
        out["cases"][name] = {"train_accuracy": float((clf.predict((xt - mu) / sd) == yt).mean()),
                              "val_jaccard": r["phase_jaccard"], "val_accuracy": r["phase_accuracy"],
                              "onehot_weight_share_of_l2": share, "n_iter": int(np.max(clf.n_iter_)),
                              "train_classes_present": sorted(set(yt.tolist())), "val_classes_present": sorted(set(yv.tolist()))}
        print(name, json.dumps(out["cases"][name]), flush=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()

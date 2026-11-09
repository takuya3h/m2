"""Task B-3 殺し実験の処方の直し（T-2026-11-09-grasp-pilot-converge、SPEC §3.2）。本体の .venv。

前の予備の道具 `experiments/analysis/grasp_roitoken_transition_pilot/tools/c_kill.py` を読み込み、線形の層の当て方
（`fit_eval`）だけを本契約の候補に差し替える。行・特徴・殺す条件・事象の率の計算は前の予備のまま、材料は前の予備の保存先を読むだけ。

前の予備の処方（Adam、lr 1e-3、wd 1e-4、100 epoch）は、陽性対照（正解の工程の one-hot）で J +0.016 しか出なかった。
train を P の特徴だけで分け切ると、Adam は足した列を重く使わない（実行者の見立て）。L2 の正則化を最適まで解けば、
小さなノルムで分けられる one-hot が勝つはずなので、候補は L2 つきの多項ロジスティック回帰を L-BFGS で解く形にする。

    候補 1: sklearn LogisticRegression（lbfgs、L2、C = 1.0、max_iter 3000、class_weight balanced）、train の平均・標準偏差で標準化
    候補 2: 同じで C = 0.1（候補 1 が陽性対照で J 0.9 に届かないときだけ）
    候補 3・4: 同じで C = 1e-3・1e-4（利用者の決定 2026-11-09「1のあと、学習にすすんで」で追加。候補 1・2 が届かず、
               診断 b3_diag.py で train の正解率 1.0・one-hot の重みの割合 22〜26% と出たため、正則化を強める向き）。
               --only で選ぶ。1 回目（候補 1・2）の記録は b3_kill.json、2 回目は b3_kill_round2.json

手順: 陽性対照（P の全体の特徴 ＋ 正解の工程の one-hot）で val の macro Jaccard ≥ 0.9 に届く最初の候補を採る（最大 2 つ）。
採った処方で、陰性対照（P の特徴 ＋ 乱数の特徴 10,245 次元〔案 3 の足す次元と同じ〕、seed 42）の差が 0.1 pt 未満かを測り、
案 3（正解の枠・G の枠の ROI の平均）と案 5（窓 8 秒・32 秒の遷移の特徴）の殺し実験を測り直す。殺す条件に当たっても止めない。

    .venv/bin/python b3_kill.py --out <S>/b/b3_kill.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
PRIOR_TOOLS = ROOT / "experiments/analysis/grasp_roitoken_transition_pilot/tools"
PRIOR = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot")
sys.path.insert(0, str(PRIOR_TOOLS))
import c_kill as K  # noqa: E402

CANDIDATES = [{"name": "lbfgs_C1", "C": 1.0, "max_iter": 3000}, {"name": "lbfgs_C0.1", "C": 0.1, "max_iter": 3000},
              {"name": "lbfgs_C1e-3", "C": 1e-3, "max_iter": 3000}, {"name": "lbfgs_C1e-4", "C": 1e-4, "max_iter": 3000}]
TARGET = 0.9
RECIPE = {}


def fit_lbfgs(xtr, ytr, xva, yva, fva, names):
    from sklearn.linear_model import LogisticRegression
    mu, sd = xtr.mean(0), xtr.std(0)
    sd[sd < 1e-6] = 1.0
    clf = LogisticRegression(C=RECIPE["C"], max_iter=RECIPE["max_iter"], class_weight="balanced")
    t0 = time.monotonic()
    clf.fit((xtr - mu) / sd, ytr)
    pred = clf.predict((xva - mu) / sd)
    r = K.metrics(pred, yva, fva, names)
    r["fit"] = {"n_iter": int(np.max(clf.n_iter_)), "converged": bool(np.max(clf.n_iter_) < RECIPE["max_iter"]),
                "seconds": time.monotonic() - t0}
    return r


def negative_control(names, feats):
    rng = np.random.default_rng(42)
    data = {}
    for part in ("train", "val"):
        frames, y = K.labels_frames(part)
        g = np.stack([feats[f] for f in frames])
        noise = rng.standard_normal((len(frames), 10245)).astype(np.float32)
        data[part] = (g, np.concatenate([g, noise], 1), y, frames)
    (btr, ptr, ytr, _), (bva, pva, yva, fva) = data["train"], data["val"]
    b = K.fit_eval(btr, ytr, bva, yva, fva, names)
    p = K.fit_eval(ptr, ytr, pva, yva, fva, names)
    d = K.diff(p, b)
    return {"dims": {"base": btr.shape[1], "plus": ptr.shape[1]}, "base": {k: b[k] for k in ("phase_jaccard", "phase_accuracy", "six_phase_mean")},
            "plus_noise": {k: p[k] for k in ("phase_jaccard", "phase_accuracy", "six_phase_mean")}, "diff": d,
            "below_0.1pt_both": K.killed(d)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="+", default=None, help="試す候補の名前（既定は候補 1・2）")
    a = ap.parse_args()
    cands = [c for c in CANDIDATES if c["name"] in (a.only or ["lbfgs_C1", "lbfgs_C0.1"])]
    import stage1_ptower as base
    base.deterministic(42)
    names = K.C.phase_names()
    feats = K.C.load_features()
    K.fit_eval = fit_lbfgs
    out = {"task_id": "T-2026-11-09-grasp-pilot-converge", "prior_tools": str(PRIOR_TOOLS), "prior_store": str(PRIOR),
           "candidates": cands, "target_positive_jaccard": TARGET, "kill_threshold": K.KILL, "tried": []}
    chosen = None
    for cand in cands:
        RECIPE.clear()
        RECIPE.update(cand)
        pc = K.positive_control(names, feats, str(PRIOR / "b4"))
        ok = pc["plus_gt_onehot"]["phase_jaccard"] >= TARGET
        out["tried"].append({"candidate": cand, "positive_control": pc, "reaches_target": ok})
        print("positive", cand["name"], json.dumps(pc["plus_gt_onehot"]), ok, flush=True)
        if ok:
            chosen = cand
            break
    out["chosen"] = chosen
    if chosen is None:
        Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
        print("NO_CANDIDATE_REACHED_TARGET", flush=True)
        return
    out["negative_control"] = negative_control(names, feats)
    print("negative", json.dumps(out["negative_control"]["diff"]), flush=True)
    args = argparse.Namespace(box_dir=str(PRIOR / "b4"), tok_dir=str(PRIOR / "tok"), seq_dir=str(PRIOR / "seq"))
    out["case3_gt"] = K.case3(args, names, feats, "gt")
    out["case3_pred"] = K.case3(args, names, feats, "pred")
    print("case3", json.dumps(out["case3_gt"]["diff"]), json.dumps(out["case3_pred"]["diff"]), flush=True)
    out["case5"] = K.case5(args, names, feats)
    for L, v in out["case5"]["linear"].items():
        print("case5", L, json.dumps(v["diff"]), v["kill"], flush=True)
    out["videos"] = {p: K.C.assert_no_test(K.labels_frames(p)[0], "b3_kill") for p in ("train", "val")}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    main()

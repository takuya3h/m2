"""殺し実験（記述だけ。非公式 T-2026-10-19-stage2-pilot-four-new-types、SPEC §3.6、Task D）。本体の .venv で動かす。

    k1       extra-queries の神託。val の見落とし（xq_missed.py missed の出力）を、正しいクラスと位置・確信度 1 で D* の val の
             出力に足し、画像ごとに上位 300 を取って評価する。塔単独との差（overall mAP、群 AP）
    k2       logit-correction。val の 2 本で、片方で多項ロジスティック回帰を当てはめ、もう片方で測る（両方向）。
             特徴 (i) softmax(ℓ0)、(ii) (i) と D0、(iii) (ii) と D-GT
    k3-train tool-history。D0 の系列だけから工程を当てる GRU（1 層、64、線形で 9 工程）を学ぶ（run の表の 1 本。
             ExperimentManager の実験フォルダ）。train は交差適合版の D0、val は確定塔の D0
    k3-eval  (2) K2 と同じ形で (i) と (i)+GRU の事後確率を比べる。(3) val の D0 を動画の中で時間の順だけ無作為に入れ替えた系列
             （seed 42）で事後確率を作り直し、(2) を繰り返す

設定は測る前に一つに固定する（K2・K3 の回帰: sklearn LogisticRegression、多項、L2、C=1.0、lbfgs、max_iter 5000、特徴の標準化なし。
K3 の GRU: 検出から工程と同じ学習率 5e-4 一定・weight decay 0.01・1 歩 = train の動画 1 本・4 epoch・seed 42・損失は
クラスの重みつき交差エントロピーと平滑化の重み 0.3）。測った動画の値で選び直さない。
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stage2pilot import common as C  # noqa: E402

TASK_ID = "T-2026-10-19-stage2-pilot-four-new-types"
FOUR = C.STORE.parent / TASK_ID
FINAL = C.STORE / "signals/final"
CF = C.STORE / "signals/cf"
LR_SETTING = {"model": "sklearn.linear_model.LogisticRegression", "multi_class": "multinomial（lbfgs の既定）",
              "penalty": "l2", "C": 1.0, "solver": "lbfgs", "max_iter": 5000, "standardize": False}
GRU_SETTING = {"layers": 1, "hidden": 64, "head": "linear → 9", "lr": 5e-4, "weight_decay": 0.01, "epochs": 4,
               "step": "train の動画 1 本", "seed": 42, "loss": "クラスの重みつき交差エントロピー + 平滑化 0.3（DP と同じ）",
               "train_signal": "交差適合版の D0（signals/cf/D0_train.npz）", "val_signal": "確定塔の D0（signals/final/D0_val.npz）"}


# ------------------------------------------------------------------ K1
def cmd_k1(a):
    from stage2pilot import det_metrics as M
    preds = M.load_results(a.preds)
    miss = json.loads(Path(a.missed).read_text())
    ann = json.loads(Path(a.ann).read_text())
    by_id = {x["id"]: x for x in ann["annotations"]}
    added = [{"image_id": by_id[i]["image_id"], "category_id": by_id[i]["category_id"], "bbox": by_id[i]["bbox"],
              "score": 1.0} for i in (miss["missed_ann_ids"] if not a.empty_missed else [])]
    per_img = {}
    for r in preds + added:
        per_img.setdefault(r["image_id"], []).append(r)
    oracle = [r for rs in per_img.values() for r in sorted(rs, key=lambda r: -r["score"])[:300]]
    base = M.summary(a.ann, preds)
    orc = M.summary(a.ann, oracle)
    keys = ("AP", "target_AP", "control_AP")
    res = {"task_id": TASK_ID, "missed_file": a.missed, "n_missed_added": len(added), "empty_missed": a.empty_missed,
           "preds": a.preds, "tower": {k: base[k] for k in keys} | {"per_class_ap": base["per_class_ap"]},
           "oracle": {k: orc[k] for k in keys} | {"per_class_ap": orc["per_class_ap"]},
           "diff": {k: orc[k] - base[k] for k in keys},
           "diff_per_class": {c: orc["per_class_ap"][c] - base["per_class_ap"][c] for c in base["per_class_ap"]},
           "per_video_AP": {"tower": base["per_video_AP"], "oracle": orc["per_video_AP"]}}
    C.write_json(a.out, res)
    print(json.dumps({"n_added": len(added), "diff": res["diff"]}, ensure_ascii=False))


# ------------------------------------------------------------------ K2・K3 共通
def val_sequences():
    split = C.fold_a()
    return C.phase_sequences(C.assert_no_test(split["val"], "kill_four/val"))


def tower_probs(seqs):
    """工程塔単独の最後の段の softmax（動画ごと、(T, 9)）。repro_ptower.predict と同じ。"""
    import stage1_ptower as base
    from stage2pilot.repro_ptower import predict
    base.deterministic(42)
    feats = C.load_features()
    head = C.load_ptower_head()
    return {v: p.astype(np.float64) for v, p in predict(head, feats, seqs).items()}


def frame_rows(path, frames):
    sig = C.load_signal(path)
    return np.stack([sig[f] for f in frames]).astype(np.float64)


def lr_measure(feats_by_video, labels_by_video, names):
    """片方で当てはめ、もう片方で測る（両方向）。値: 測った動画の macro Jaccard、frame accuracy、平均の負の対数尤度。"""
    from sklearn.linear_model import LogisticRegression

    from egosurgery.metrics.phase import PhaseEvaluator
    vids = sorted(feats_by_video)
    out = {}
    for fit, test in ((vids[0], vids[1]), (vids[1], vids[0])):
        clf = LogisticRegression(C=LR_SETTING["C"], max_iter=LR_SETTING["max_iter"], solver="lbfgs")
        clf.fit(feats_by_video[fit], labels_by_video[fit])
        proba = clf.predict_proba(feats_by_video[test])
        full = np.zeros((len(proba), len(names)))
        full[:, clf.classes_] = proba
        pred = full.argmax(1)
        y = labels_by_video[test]
        ev = PhaseEvaluator(num_classes=len(names), class_names=names)
        ev.update(pred, y, video_id=test)
        r = ev.compute()
        p_true = full[np.arange(len(y)), y]
        unseen = sorted(set(y.tolist()) - set(clf.classes_.tolist()))
        out[f"fit{fit}_test{test}"] = {
            "phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
            "mean_nll": float(-np.log(np.clip(p_true, 1e-12, None)).mean()),
            "mean_nll_seen_only": float(-np.log(np.clip(p_true[np.isin(y, clf.classes_)], 1e-12, None)).mean()),
            "phases_in_fit": [names[c] for c in clf.classes_],
            "phases_in_test_not_in_fit": [names[c] for c in unseen],
            "frames_test_label_unseen": int((~np.isin(y, clf.classes_)).sum()), "n_frames_test": int(len(y))}
    return out


def diffs(res, base_key, keys):
    """(x)−(i) を方向ごとと 2 方向の平均で。"""
    out = {}
    for k in keys:
        per_dir = {d: {m: res[k][d][m] - res[base_key][d][m] for m in ("phase_jaccard", "phase_accuracy", "mean_nll")}
                   for d in res[base_key]}
        out[f"{k}-{base_key}"] = {"per_direction": per_dir,
                                  "mean_over_directions": {m: float(np.mean([v[m] for v in per_dir.values()]))
                                                           for m in ("phase_jaccard", "phase_accuracy", "mean_nll")}}
    return out


def cmd_k2(a):
    seqs = val_sequences()
    names = C.phase_names()
    probs = tower_probs(seqs)
    labels = {v: y for v, _, y in seqs}
    d0 = {v: frame_rows(FINAL / "D0_val.npz", fr) for v, fr, _ in seqs}
    dgt = {v: frame_rows(FINAL / "D-GT_val.npz", fr) for v, fr, _ in seqs}
    feats = {"i": probs, "ii": {v: np.hstack([probs[v], d0[v]]) for v in probs},
             "iii": {v: np.hstack([probs[v], d0[v], dgt[v]]) for v in probs}}
    if a.control_onehot:
        # 陽性対照: (ii) の D0 の代わりに正解の工程の one-hot を入れる
        feats["ii"] = {v: np.hstack([probs[v], np.eye(len(names))[labels[v]]]) for v in probs}
    res = {k: lr_measure(f, labels, names) for k, f in feats.items()}
    out = {"task_id": TASK_ID, "setting": LR_SETTING, "control_onehot": a.control_onehot,
           "videos": sorted(probs), "features": {"i": "softmax(ℓ0)（工程塔単独）", "ii": "(i) と D0（確定塔、15）",
                                                  "iii": "(ii) と D-GT（15）"} | (
               {"ii": "(i) と正解の工程の one-hot（陽性対照）"} if a.control_onehot else {}),
           "values": res, "diffs": diffs(res, "i", ("ii", "iii"))}
    C.write_json(a.out, out)
    print(json.dumps(out["diffs"], ensure_ascii=False)[:1500])


# ------------------------------------------------------------------ K3
def gru_model(torch):
    from torch import nn

    class GRUPhase(nn.Module):
        def __init__(self, in_dim=15, hidden=64, n=9):
            super().__init__()
            self.gru = nn.GRU(in_dim, hidden, num_layers=1, batch_first=True)
            self.head = nn.Linear(hidden, n)

        def forward(self, x):                     # (T, 15) → (1, 9, T)、最終状態 (64,)
            h, last = self.gru(x[None])
            return self.head(h[0]).T[None], last[0, 0]

    return GRUPhase()


def cmd_k3_train(a):
    import torch
    import torch.nn.functional as F
    from torch import nn

    import stage1_ptower as base
    from egosurgery.metrics.phase import PhaseEvaluator
    from egosurgery.utils import tracking
    from egosurgery.utils.experiment_manager import ExperimentManager
    from stage2pilot.dp_train import STOP, class_weights
    base.deterministic(42)
    random.seed(GRU_SETTING["seed"])
    np.random.seed(GRU_SETTING["seed"])
    torch.manual_seed(GRU_SETTING["seed"])
    names = C.phase_names()
    split = C.fold_a()
    tr_v = C.assert_no_test(split["train"], "k3/train")
    va_v = C.assert_no_test(split["val"], "k3/val")
    tr_sig, va_sig = CF / "D0_train.npz", FINAL / "D0_val.npz"
    tr = [(v, torch.from_numpy(frame_rows(tr_sig, fr)).float().cuda(), torch.from_numpy(y).cuda())
          for v, fr, y in C.phase_sequences(tr_v)]
    va = [(v, torch.from_numpy(frame_rows(va_sig, fr)).float().cuda(), torch.from_numpy(y).cuda())
          for v, fr, y in C.phase_sequences(va_v)]
    model = gru_model(torch).cuda()
    weights, counts = class_weights([(None, None, None, None, y) for _, _, y in tr], len(names))
    ce = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device="cuda"))
    opt = torch.optim.AdamW(model.parameters(), lr=GRU_SETTING["lr"], weight_decay=GRU_SETTING["weight_decay"])
    cfg = {"task_id": TASK_ID, "unofficial": f"非公式（{TASK_ID}）", "kill_experiment": "K3 (1)", **GRU_SETTING,
           "signals": {"train": {"path": str(tr_sig), "sha256": C.sha256(tr_sig)},
                       "val": {"path": str(va_sig), "sha256": C.sha256(va_sig)}},
           "videos": {"train": tr_v, "val": va_v}, "class_counts": counts.tolist(), "class_weights": weights.tolist(),
           "params": int(sum(p.numel() for p in model.parameters())), "smoke": bool(a.smoke)}
    epochs = 1 if a.smoke else GRU_SETTING["epochs"]
    manager = ExperimentManager(C.ROOT / "experiments", "phase1", "stage2four_k3", f"gru_D0only_ep{epochs}"
                                + ("_smoke" if a.smoke else ""), GRU_SETTING["seed"])
    manager.setup(cfg)
    run = tracking.init(manager.exp_id, config=cfg, group=TASK_ID, job_type="stage2four_k3", exp_dir=manager.exp_dir)
    if run is None:
        raise RuntimeError("W&B tracking could not start; no experiment executed")
    started = time.monotonic()
    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        order = list(range(len(tr)))
        random.shuffle(order)
        total = 0.0
        for i in order:
            _, x, y = tr[i]
            o, _ = model(x)
            logp = F.log_softmax(o, dim=1)
            loss = ce(o[0].T, y) + STOP["smoothing_weight"] * F.mse_loss(
                logp[:, :, 1:], logp[:, :, :-1].detach(), reduction="none").clamp(max=16).mean()
            if not torch.isfinite(loss):
                raise RuntimeError(f"非数の損失 epoch {epoch}")
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            total += float(loss)
        res, _ = k3_eval_videos(model, va, names, torch, PhaseEvaluator)
        history.append({"epoch": epoch, "train_loss": total / len(order), "val_jaccard": res["phase_jaccard"],
                        "val_accuracy": res["phase_accuracy"]})
        tracking.log({"train/loss": total / len(order), "val/jaccard": res["phase_jaccard"]}, step=epoch)
    res, probs = k3_eval_videos(model, va, names, torch, PhaseEvaluator)
    ckpt = FOUR / "k3" / f"{manager.exp_id}.pth"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "epoch": epochs, "setting": GRU_SETTING}, ckpt)
    np.savez(manager.exp_dir / "predictions/val_probs_final.npz", **{v: p for v, p in probs.items()})
    metrics = {"phase_jaccard": res["phase_jaccard"], "phase_accuracy": res["phase_accuracy"],
               "per_video": res["per_video"], "result_selection": "final_epoch", "result_epoch": epochs,
               "elapsed_seconds": time.monotonic() - started, "ckpt": str(ckpt), "ckpt_sha256": C.sha256(ckpt)}
    manager.log_metrics(metrics)
    manager.log_per_class_ap(res["phase_per_class_jaccard"])
    manager.log_eval_recipe({"test_cfg": {"task": "phase", "inference_protocol": "online_causal",
                                          "jaccard_mode": "strict", "split": "val"}})
    C.write_json(manager.exp_dir / "logs/history.json", history)
    (manager.exp_dir / "notes.md").write_text(
        f"# 非公式（{TASK_ID}） K3 (1) D0 の系列だけの GRU seed 42\n\n"
        f"殺し実験（記述だけ）。{epochs} epoch 学習し、最後の epoch の状態を結果にする。val だけで評価した。test は通していない。\n"
        f"val macro Jaccard {res['phase_jaccard']} / accuracy {res['phase_accuracy']}\n")
    tracking.finish()
    print(f"K3_RUN_COMPLETE {manager.exp_dir} jaccard={res['phase_jaccard']:.6f}", flush=True)


def k3_eval_videos(model, va, names, torch, PhaseEvaluator):
    model.eval()
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    probs, per_video = {}, {}
    with torch.no_grad():
        for v, x, y in va:
            o, _ = model(x)
            pred = o[0].argmax(0).cpu().numpy()
            ev.update(pred, y.cpu().numpy(), video_id=v)
            one = PhaseEvaluator(num_classes=len(names), class_names=names)
            one.update(pred, y.cpu().numpy(), video_id=v)
            r = one.compute()
            per_video[v] = {"phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"]}
            probs[v] = torch.softmax(o[0], 0).T.cpu().numpy()
    res = ev.compute()
    res["per_video"] = per_video
    return res, probs


def cmd_k3_eval(a):
    import torch

    from egosurgery.metrics.phase import PhaseEvaluator
    seqs = val_sequences()
    names = C.phase_names()
    probs = tower_probs(seqs)
    labels = {v: y for v, _, y in seqs}
    model = gru_model(torch).cuda()
    model.load_state_dict(torch.load(a.ckpt, map_location="cuda")["model"])
    va = [(v, torch.from_numpy(frame_rows(FINAL / "D0_val.npz", fr)).float().cuda(), torch.from_numpy(y).cuda())
          for v, fr, y in seqs]
    gru_res, gru_probs = k3_eval_videos(model, va, names, torch, PhaseEvaluator)
    # (3) 動画の中で時間の順だけ無作為に入れ替える（seed 42、動画ごとに一つの並べ替え）
    rng = np.random.default_rng(42)
    perms = {v: rng.permutation(len(fr)) for v, fr, _ in seqs}
    va_sh = [(v, x[torch.from_numpy(perms[v]).cuda()], y) for v, x, y in va]
    sh_res, sh_probs = k3_eval_videos(model, va_sh, names, torch, PhaseEvaluator)
    f2 = {"i": probs, "i+gru": {v: np.hstack([probs[v], gru_probs[v]]) for v in probs}}
    f3 = {"i": probs, "i+gru_shuffled": {v: np.hstack([probs[v], sh_probs[v]]) for v in probs}}
    r2 = {k: lr_measure(f, labels, names) for k, f in f2.items()}
    r3 = {k: lr_measure(f, labels, names) for k, f in f3.items()}
    d2 = diffs(r2, "i", ("i+gru",))
    d3 = diffs(r3, "i", ("i+gru_shuffled",))
    out = {"task_id": TASK_ID, "setting": LR_SETTING, "gru_setting": GRU_SETTING, "ckpt": a.ckpt,
           "ckpt_sha256": C.sha256(a.ckpt), "videos": sorted(probs),
           "gru_alone_val": {"phase_jaccard": gru_res["phase_jaccard"], "phase_accuracy": gru_res["phase_accuracy"],
                             "per_video": gru_res["per_video"]},
           "gru_alone_val_shuffled": {"phase_jaccard": sh_res["phase_jaccard"],
                                      "phase_accuracy": sh_res["phase_accuracy"], "per_video": sh_res["per_video"]},
           "shuffle": {"seed": 42, "kind": "動画の中で時間の順だけ（フレームの集合は同じ）",
                       "fixed_points": {v: int((p == np.arange(len(p))).sum()) for v, p in perms.items()}},
           "k3_2": {"values": r2, "diffs": d2}, "k3_3": {"values": r3, "diffs": d3},
           "k3_3_minus_k3_2": {m: d3["i+gru_shuffled-i"]["mean_over_directions"][m]
                               - d2["i+gru-i"]["mean_over_directions"][m]
                               for m in ("phase_jaccard", "phase_accuracy", "mean_nll")},
           "surgery_type_accuracy": "UNKNOWN（動画ごとの術式の対応が repo に無い。context/auto/results_recent.md の 194・204 行）"}
    C.write_json(a.out, out)
    print(json.dumps({"k3_2": d2, "k3_3": d3}, ensure_ascii=False)[:1500])


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    k1 = sub.add_parser("k1")
    k1.add_argument("--preds", required=True)
    k1.add_argument("--missed", required=True)
    k1.add_argument("--ann", required=True)
    k1.add_argument("--empty-missed", action="store_true", help="陽性対照: 見落としを 0 件にした写し（差が 0 になるはず）")
    k1.add_argument("--out", required=True)
    k2 = sub.add_parser("k2")
    k2.add_argument("--control-onehot", action="store_true", help="陽性対照: (ii) の D0 を正解の工程の one-hot に替える")
    k2.add_argument("--out", required=True)
    k3t = sub.add_parser("k3-train")
    k3t.add_argument("--smoke", action="store_true")
    k3e = sub.add_parser("k3-eval")
    k3e.add_argument("--ckpt", required=True)
    k3e.add_argument("--out", required=True)
    a = ap.parse_args()
    {"k1": cmd_k1, "k2": cmd_k2, "k3-train": cmd_k3_train, "k3-eval": cmd_k3_eval}[a.cmd](a)


if __name__ == "__main__":
    main()

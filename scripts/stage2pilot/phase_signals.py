"""Task C（工程側）/ E-5: 工程塔の信号、送り手の差、較正、P2F の表（非公式 T-2026-10-18-stage2-pilot-folda）。

    P0    工程塔の時間ヘッドの出力の softmax（online causal。列は工程塔の学習と同じ。動画ごとに全フレーム）  (9)
    P-GT  工程の正解の one-hot                                                                       (9)

サブコマンド:
    signals    --head --cache --videos --part --out-dir   P0 と P-GT を保存し、その動画での Jaccard と accuracy を記録
    calib      --signals-dir                              train と val の ECE（温度 1 と val で当てた温度）と温度
    p2f        --out                                      折り A の train の正解だけから B[工程, 術具] を作る
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stage2pilot import common as C  # noqa: E402
from stage2pilot.repro_ptower import per_video, phase_metrics, predict  # noqa: E402

ECE_BINS = 15


def cmd_signals(a):
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    videos = sorted(a.videos.split(","))
    seqs = C.phase_sequences(videos)
    feats = C.load_features(a.cache)
    head = C.load_ptower_head(a.head)
    probs = predict(head, feats, seqs)
    out = Path(a.out_dir)
    ids = [f for _, frames, _ in seqs for f in frames]
    p0 = np.concatenate([probs[v] for v, _, _ in seqs]).astype(np.float32)
    gt = np.eye(len(names), dtype=np.float32)[np.concatenate([y for _, _, y in seqs])]
    m = phase_metrics(probs, seqs, names)
    rec = {"task_id": C.TASK_ID, "head": a.head, "head_sha256": C.sha256(a.head), "cache": str(a.cache),
           "cache_sha256": C.sha256(a.cache), "part": a.part,
           "videos": C.assert_no_test(ids, "phase_signals"), "frames": len(ids), "class_order": names,
           "phase_jaccard": m["phase_jaccard"], "phase_accuracy": m["phase_accuracy"],
           "per_video": per_video(probs, seqs, names),
           "files": {"P0": {"path": str(out / f"P0_{a.part}.npz"), "shape": list(p0.shape),
                            "sha256": C.save_signal(out / f"P0_{a.part}.npz", ids, p0)},
                     "P-GT": {"path": str(out / f"P-GT_{a.part}.npz"), "shape": list(gt.shape),
                              "sha256": C.save_signal(out / f"P-GT_{a.part}.npz", ids, gt)}}}
    C.write_json(out / f"record_phase_{a.part}.json", rec)
    print(json.dumps({k: v for k, v in rec.items() if k not in ("files", "per_video")}, ensure_ascii=False))


def ece(probs: np.ndarray, labels: np.ndarray, bins: int = ECE_BINS) -> float:
    """最大確率の等幅区間による expected calibration error。"""
    conf = probs.max(1)
    correct = (probs.argmax(1) == labels).astype(np.float64)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(total)


def tempered(probs: np.ndarray, t: float) -> np.ndarray:
    logit = np.log(np.clip(probs, 1e-12, 1.0)) / t
    logit -= logit.max(1, keepdims=True)
    e = np.exp(logit)
    return e / e.sum(1, keepdims=True)


def fit_temperature(probs: np.ndarray, labels: np.ndarray) -> float:
    """val の負の対数尤度を最小にする温度（log t の格子探索 → 黄金分割）。"""
    def nll(t):
        p = tempered(probs, t)
        return float(-np.log(np.clip(p[np.arange(len(labels)), labels], 1e-12, 1.0)).mean())
    grid = np.exp(np.linspace(np.log(0.05), np.log(20.0), 400))
    t0 = grid[int(np.argmin([nll(t) for t in grid]))]
    lo, hi = t0 / 1.1, t0 * 1.1
    g = (np.sqrt(5) - 1) / 2
    for _ in range(80):
        c, d = hi - g * (hi - lo), lo + g * (hi - lo)
        if nll(c) < nll(d):
            hi = d
        else:
            lo = c
    return float((lo + hi) / 2)


def cmd_calib(a):
    d = Path(a.signals_dir)
    res = {"task_id": C.TASK_ID, "ece_bins": ECE_BINS, "binning": "等幅（最大確率）"}
    data = {}
    for part in ("train", "val"):
        p0, gt = C.load_signal(d / f"P0_{part}.npz"), C.load_signal(d / f"P-GT_{part}.npz")
        ids = sorted(p0)
        assert ids == sorted(gt)
        data[part] = (np.stack([p0[i] for i in ids]), np.stack([gt[i] for i in ids]).argmax(1))
    t = fit_temperature(*data["val"])
    res["temperature_fit_on"] = "val"
    res["temperature"] = t
    for part, (p, y) in data.items():
        res[f"ece_{part}_t1"] = ece(p, y)
        res[f"ece_{part}_tfit"] = ece(tempered(p, t), y)
        res[f"nll_{part}_t1"] = float(-np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)).mean())
    C.write_json(Path(a.out), res)
    print(res)


@torch.no_grad()
def cmd_construct_check(a):
    """P0 の時刻を作り方から確かめる（time_check の一致率とは異質な方法）。

    各動画から等間隔に n 個のフレーム t を選び、特徴の先頭から t までだけを時間ヘッドに通した最終段の softmax
    （t より後の特徴を使わない）が、保存した P0[名前 t] と一致するかを見る。さらに名前を一つ先へ付け替えた写し
    （名前 t の行が t-1 の情報）では、一致が t ではなく t-1 で成り立つことを示す（陽性対照）。
    """
    import stage1_ptower as base
    base.deterministic(42)
    feats = C.load_features(a.cache)
    head = C.load_ptower_head(a.head)
    p0 = C.load_signal(Path(a.signals_dir) / f"P0_{a.part}.npz")
    videos = sorted({C.video_of(f) for f in p0})
    res = {"task_id": C.TASK_ID, "part": a.part, "videos": C.assert_no_test(videos, "construct_check"),
           "per_video": {}, "tolerance": a.tol}
    worst, worst_shift_t, worst_shift_tm1, n = 0.0, np.inf, 0.0, 0
    for video, frames, _ in C.phase_sequences(videos):
        x = torch.from_numpy(np.stack([feats[f] for f in frames])).cuda()
        picks = np.linspace(1, len(frames) - 1, a.n).astype(int)
        diffs, sh_t, sh_tm1 = [], [], []
        for t in picks:
            prefix = torch.softmax(head(x[: t + 1].T[None])[-1][0], 0)[:, -1].cpu().numpy()
            prev = torch.softmax(head(x[:t].T[None])[-1][0], 0)[:, -1].cpu().numpy()
            diffs.append(float(np.abs(prefix - p0[frames[t]]).max()))
            shifted_row = p0[frames[t - 1]]               # 名前 t に付け替えた写しの行（t-1 の情報）
            sh_t.append(float(np.abs(prefix - shifted_row).max()))
            sh_tm1.append(float(np.abs(prev - shifted_row).max()))
        res["per_video"][video] = {"picks": len(picks), "max_abs_diff_at_t": max(diffs),
                                   "shifted_min_diff_at_t": min(sh_t), "shifted_max_diff_at_t_minus_1": max(sh_tm1)}
        worst = max(worst, max(diffs))
        worst_shift_t = min(worst_shift_t, min(sh_t))
        worst_shift_tm1 = max(worst_shift_tm1, max(sh_tm1))
        n += len(picks)
    res.update({"frames_checked": n, "max_abs_diff_at_t": worst, "unshifted_same_time": worst <= a.tol,
                "shifted_min_diff_at_t": worst_shift_t, "shifted_max_diff_at_t_minus_1": worst_shift_tm1,
                "shifted_detected_as_minus_1": worst_shift_tm1 <= a.tol < worst_shift_t})
    C.write_json(a.out, res)
    print(json.dumps({k: v for k, v in res.items() if k != "per_video"}, ensure_ascii=False))


def cmd_p2f(a):
    """B[工程, 術具] = log((工程で術具が在るフレーム数 + 1) / (工程のフレーム数 + 2))。折り A の train の正解だけ。"""
    split = C.fold_a()
    names = C.phase_names()
    phase_of = {}
    for _, frames, labels in C.phase_sequences(split["train"]):
        phase_of.update(zip(frames, labels.tolist()))
    ann = json.loads((C.DET_ANN_A / "instances_train.json").read_text())
    cats = sorted(ann["categories"], key=lambda c: c["id"])
    present = {}
    for x in ann["annotations"]:
        present.setdefault(x["image_id"], set()).add(x["category_id"])
    n_phase = np.zeros(len(names))
    n_both = np.zeros((len(names), len(cats)))
    stems = []
    for im in ann["images"]:
        stem = Path(im["file_name"]).stem
        stems.append(stem)
        p = phase_of[stem]
        n_phase[p] += 1
        for c in present.get(im["id"], ()):
            n_both[p, c] += 1
    table = np.log((n_both + 1.0) / (n_phase[:, None] + 2.0))
    res = {"task_id": C.TASK_ID, "videos": C.assert_no_test(stems, "p2f"), "frames": len(stems),
           "phase_order": names, "tool_order": [c["name"] for c in cats],
           "smoothing": "在る数に 1、工程の数に 2", "n_phase": n_phase.tolist(), "n_present": n_both.tolist(),
           "B": table.tolist()}
    C.write_json(Path(a.out), res)
    print(json.dumps({k: res[k] for k in ("videos", "frames", "n_phase")}))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("signals")
    s.add_argument("--head", default=str(C.PT_HEAD_CKPT))
    s.add_argument("--cache", default=str(C.PT_CACHE))
    s.add_argument("--videos", required=True)
    s.add_argument("--part", required=True)
    s.add_argument("--out-dir", required=True)
    c = sub.add_parser("calib")
    c.add_argument("--signals-dir", required=True)
    c.add_argument("--out", required=True)
    p = sub.add_parser("p2f")
    p.add_argument("--out", required=True)
    k = sub.add_parser("construct-check")
    k.add_argument("--head", default=str(C.PT_HEAD_CKPT))
    k.add_argument("--cache", default=str(C.PT_CACHE))
    k.add_argument("--signals-dir", required=True)
    k.add_argument("--part", required=True)
    k.add_argument("--n", type=int, default=40)
    k.add_argument("--tol", type=float, default=1e-5)
    k.add_argument("--out", required=True)
    a = ap.parse_args()
    {"signals": cmd_signals, "calib": cmd_calib, "p2f": cmd_p2f, "construct-check": cmd_construct_check}[a.cmd](a)


if __name__ == "__main__":
    main()

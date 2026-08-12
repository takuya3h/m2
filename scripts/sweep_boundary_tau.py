#!/usr/bin/env python
"""T1a-Boundary の sticky decode しきい値 τ を **再学習なし**で掃引し、edit-score↔accuracy の
operating-point 曲線を出す。

boundary-gated sticky decode は τ が高いほど工程遷移を厳しく抑制する:
  τ→0 : ほぼ全遷移を受理 = plain（高 acc・低 edit）
  τ→1 : ほぼ全遷移を抑制 = 過度に sticky（高 edit だが誤phase に固着 → acc 崩壊）
初期 τ=0.5 は acc を大きく落としたため、val 上で **acc を base 近傍に保ちつつ edit を最大化**する
τ* を探索する。checkpoint（best_tecno_boundary.pth）の logits/boundary_prob を一度だけ前計算し、
τ ごとに decode のみやり直すので高速。

実行: python scripts/sweep_boundary_tau.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))
sys.path.insert(0, str(PROJ / "scripts"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from train_t1a_boundary import (  # noqa: E402
    CLASS_NAMES,
    GAP_DIM,
    REGION_DIM,
    TeCNOBoundary,
    load_clips,
    sticky_decode,
)

TR = PROJ / "experiments" / "transfer"
SEEDS = (42, 123, 456)
TAUS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]


def _boundary_dir(seed: int) -> Path | None:
    ds = sorted(TR.glob(f"t1a_boundary_*seed{seed}"))
    ds = [d for d in ds if (d / "checkpoints" / "best_tecno_boundary.pth").exists()]
    return ds[-1] if ds else None


def _base_metric(seed: int, key: str):
    ds = sorted(TR.glob(f"t1a_base_env_*seed{seed}"))
    for d in reversed(ds):
        f = d / "metrics.json"
        if f.exists():
            return json.load(open(f)).get(key)
    return None


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    val_clips = load_clips("val", region_only=False)

    # base（同env）の val 指標
    base_acc = [_base_metric(s, "phase_accuracy") for s in SEEDS]
    base_edit = [_base_metric(s, "phase_edit_score") for s in SEEDS]
    base_acc_m = float(np.mean([a for a in base_acc if a is not None]))
    base_edit_m = float(np.mean([e for e in base_edit if e is not None]))

    # 各 seed: checkpoint を読み logits/boundary_prob を前計算
    per_seed_cache = {}
    for s in SEEDS:
        d = _boundary_dir(s)
        if d is None:
            print(f"[sweep] seed{s} boundary checkpoint 不在 — skip")
            continue
        ck = torch.load(d / "checkpoints" / "best_tecno_boundary.pth", map_location=device)
        model = TeCNOBoundary(2, 8, 64, GAP_DIM + REGION_DIM, len(CLASS_NAMES)).to(device)
        model.load_state_dict(ck["model"])
        model.eval()
        cache = []
        with torch.no_grad():
            for clip_id, feats, labels in val_clips:
                x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
                phase_outs, b_logit = model(x)
                lg = phase_outs[-1][0].cpu().numpy()
                bp = torch.sigmoid(b_logit[0, 0]).cpu().numpy()
                cache.append((clip_id, lg, bp, labels))
        per_seed_cache[s] = cache
        print(f"[sweep] seed{s} <- {d.name} (epoch {ck.get('epoch')})")

    # τ 掃引（seed 平均）
    print(f"\nbase(同env val): acc={base_acc_m:.4f}  edit={base_edit_m:.2f}\n")
    header = f"{'tau':>5} | {'acc':>7} {'macroF1':>7} {'edit':>7} {'segF1@50':>8} | {'Δacc':>7} {'Δedit':>7}"
    print(header)
    print("-" * len(header))
    rows = []
    for tau in TAUS:
        accs, f1s, edits, segs = [], [], [], []
        for s, cache in per_seed_cache.items():
            ev = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
            for clip_id, lg, bp, labels in cache:
                preds = lg.argmax(0) if tau <= 0.0 else sticky_decode(lg, bp, tau)
                ev.update(preds, labels, video_id=clip_id)
            m = ev.compute()
            accs.append(m["phase_accuracy"]); f1s.append(m["phase_macro_f1"])
            edits.append(m["phase_edit_score"]); segs.append(m["phase_seg_f1_50"])
        am, fm, em, sm = np.mean(accs), np.mean(f1s), np.mean(edits), np.mean(segs)
        rows.append((tau, am, fm, em, sm))
        print(f"{tau:5.2f} | {am:7.4f} {fm:7.4f} {em:7.2f} {sm:8.3f} | "
              f"{(am-base_acc_m)*100:+7.2f} {em-base_edit_m:+7.2f}")

    # τ* = acc を base の 0.5pp 以内に保ちつつ edit 最大
    tol = 0.005
    feasible = [r for r in rows if r[1] >= base_acc_m - tol]
    if feasible:
        star = max(feasible, key=lambda r: r[3])
        print(f"\n[sweep] τ* (acc≥base−{tol*100:.1f}pp で edit 最大) = {star[0]:.2f}: "
              f"acc={star[1]:.4f} (Δ{(star[1]-base_acc_m)*100:+.2f}pp) edit={star[3]:.2f} (Δ{star[3]-base_edit_m:+.2f})")
    else:
        print(f"\n[sweep] acc を base−{tol*100:.1f}pp 以内に保つ τ は無し → acc↔edit は本質的トレードオフ")


if __name__ == "__main__":
    main()

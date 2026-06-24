#!/usr/bin/env python
"""test split での det→phase 工程評価（per-phase F1・§3.1 を本番データで確証）。

phase head（TeCNO）は元実験で ckpt 未保存のため、**同一 seed・同一ハイパーで再学習**し、val で
best を選んで（再現確認）→ **test** で per-phase F1 を評価する。S4 base / B2a(presence) / T1a(region)
の3系統 × 3seed。特徴は全てキャッシュ（train_t1a と同じ作法）。

system 別 入力:
  s4  : GAP(2048)
  b2a : GAP(2048) ⊕ tool-presence(15) = 2063
  t1a : GAP(2048) ⊕ region-token(3840) = 5888

実行（本体 .venv・CPU 既定で GPU 評価に非干渉）:
  .venv/bin/python scripts/eval_det2phase_test.py --device cpu --seeds 42,123,456
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "scripts"))
# train_t1a から再利用（TeCNO/評価/定数）。import 時に src を path 追加する。
from train_t1a import (  # noqa: E402
    CLASS_NAMES,
    GAP_DIR,
    MANIFEST_DIR,
    TeCNO,
    evaluate,
    smoothing_loss,
)

PRES_DIR = PROJ / "data/processed/b2a_detsignal/relation_detr_seed42"
REG_DIR = PROJ / "data/processed/t1a_regiontoken/relation_detr_seed42"
OUT = PROJ / "experiments/analysis/step_c_coupling_analysis"
IN_DIM = {"s4": 2048, "b2a": 2063, "t1a": 5888}


def _index_npz(path, key):
    """npz の配列を **一度だけ** メモリ展開して {frame_id: row} を返す。
    `z[key][i]` をループ毎に評価すると NpzFile が毎回 zip 展開し、速度・メモリが破綻する
    （元実装の OOM 原因）。配列を一度だけ取り出して in-memory 添字に切替える。"""
    z = np.load(path)
    arr = z[key]
    fids = [str(f) for f in z["frame_ids"]]
    z.close()
    return {fid: arr[i] for i, fid in enumerate(fids)}


def load_clips(split: str, system: str):
    gap_by = _index_npz(GAP_DIR / f"{split}_gap.npz", "features")
    extra_by = None
    if system == "b2a":
        extra_by = _index_npz(PRES_DIR / f"{split}_toolpresence.npz", "signal")
    elif system == "t1a":
        extra_by = _index_npz(REG_DIR / f"{split}_regiontoken.npz", "region")
    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        rows = []
        for fr in clip["frames"]:
            gp = gap_by[fr["frame"]]
            rows.append(gp if extra_by is None else np.concatenate([gp, extra_by[fr["frame"]]]))
        feats = np.stack(rows).astype(np.float32)
        labels = np.asarray([fr["label"] for fr in clip["frames"]], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


def train_eval(system: str, seed: int, device, epochs: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    tr = load_clips("train", system)
    va = load_clips("val", system)
    te = load_clips("test", system)
    model = TeCNO(num_stages=2, num_layers=8, num_f_maps=64,
                  in_dim=IN_DIM[system], num_classes=len(CLASS_NAMES)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.01)
    ce = nn.CrossEntropyLoss()
    best = {"phase_accuracy": -1.0}
    best_state = None
    for _ in range(epochs):
        model.train()
        random.shuffle(tr)
        for _cid, feats, labels in tr:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
            y = torch.from_numpy(labels).to(device)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad()
            loss.backward()
            opt.step()
        val = evaluate(model, va, device)
        if val["phase_accuracy"] > best["phase_accuracy"]:
            best = val
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    test = evaluate(model, te, device)
    return best, test


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="42,123,456")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--epochs", type=int, default=50)
    args = ap.parse_args()
    device = torch.device(args.device)
    seeds = [int(s) for s in args.seeds.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for system in ["s4", "b2a", "t1a"]:
        results[system] = {}
        for seed in seeds:
            best, test = train_eval(system, seed, device, args.epochs)
            results[system][seed] = {
                "val": {k: v for k, v in best.items() if isinstance(v, (int, float))},
                "val_per_phase_f1": best.get("phase_per_class_f1", {}),
                "test": {k: v for k, v in test.items() if isinstance(v, (int, float))},
                "test_per_phase_f1": test.get("phase_per_class_f1", {}),
            }
            print(f"[det2phase-test] {system} seed{seed}: "
                  f"val acc={best['phase_accuracy']:.4f} mF1={best['phase_macro_f1']:.4f} | "
                  f"test acc={test['phase_accuracy']:.4f} mF1={test['phase_macro_f1']:.4f} "
                  f"hemo(val→test)={best.get('phase_per_class_f1',{}).get('hemostasis',float('nan')):.3f}"
                  f"→{test.get('phase_per_class_f1',{}).get('hemostasis',float('nan')):.3f}", flush=True)
    (OUT / "test_eval_det2phase.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"[det2phase-test] saved -> {OUT/'test_eval_det2phase.json'}")


if __name__ == "__main__":
    main()

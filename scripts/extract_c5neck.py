#!/usr/bin/env python
"""検出で学習した C5 線形 neck を Relation-DETR ckpt から抽出する（②系統の転移結合）。

`RelationDETRC5Neck` は `self.c5_neck = C5LinearNeck`（key `c5_neck.weight`/`c5_neck.bias`）。
これを工程側 `train_s4_tecno.py --neck-from` が読める純テンソル dict `{weight, bias}` に整形して保存。

入力 ckpt は `_classes_`（非テンソル）を含むため weights_only=False で読むが、
出力は純テンソルのみ → 工程側は weights_only=True（安全側）で読める。

実行: .venv/bin/python scripts/extract_c5neck.py \
        --ckpt /tmp/reldetr_work_..._seed456_*/best_ap.pth --seed 456
出力: data/processed/c5neck/c5neck_seed{SEED}.pth
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[1]
OUT_DIR = PROJ / "data/processed/c5neck"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True, help="Relation-DETR(neck版) の best_ap.pth")
    ap.add_argument("--seed", required=True, type=int)
    args = ap.parse_args()

    # 検出器 ckpt は _classes_ を含むため weights_only=False（信頼できる自前成果物）。
    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    sd = ck["model"] if isinstance(ck, dict) and "model" in ck else ck

    w, b = sd.get("c5_neck.weight"), sd.get("c5_neck.bias")
    if w is None or b is None:
        raise SystemExit(f"c5_neck.weight/bias が見つかりません: {args.ckpt}")

    # zero-init からの学習で恒等(norm 0)を脱しているか＝検出が neck を実際に使った証拠。
    wn, bn = w.float().norm().item(), b.float().norm().item()
    if wn < 1e-3:
        raise SystemExit(f"c5_neck.weight が恒等(norm={wn:.2e})に近い → 抽出を中止（neck 未学習の疑い）")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"c5neck_seed{args.seed}.pth"
    # 純テンソル dict（既存 c5neck_seed42/123.pth と同一フォーマット）。
    torch.save({"weight": w.detach().clone(), "bias": b.detach().clone()}, out)
    print(f"[extract] seed{args.seed}: weight norm={wn:.4f} / bias norm={bn:.4f}")
    print(f"[extract] saved -> {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

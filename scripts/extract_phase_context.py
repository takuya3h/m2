#!/usr/bin/env python
"""T1b 用: 凍結 S4 工程モデルの per-frame 事後分布（phase context）を抽出する。

MT4MTL-KD-style Phase→Det（§4.6 双方向の Phase→Det 半分）で、**凍結 S4 工程モデル**を
phase teacher とし、その per-frame 事後分布（9-d, causal）を検出器への FiLM 条件入力にする。
S4 は TeCNO（causal）なので frame t の事後は ≤t 情報のみ＝未来非参照（注入に leak なし）。

入力: data/processed/stage1_features/relation_detr_seed42/{split}_gap.npz（GAP 2048, S4 と同一資産）
      data/processed/phase_manifest/{split}.json（clip 時系列順）
      凍結 S4 ckpt（既定 s4_phase_baseline seed42 best_tecno.pth）
出力: data/processed/phase_context/relation_detr_seed42/{split}_phasectx.npz（frame_ids, ctx=(N,9) softmax）

本体 .venv（Relation-DETR 非依存・キャッシュのみ）:
  .venv/bin/python scripts/extract_phase_context.py --subset train
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402

CACHE_DIR = PROJ / "data/processed/stage1_features/relation_detr_seed42"
MANIFEST_DIR = PROJ / "data/processed/phase_manifest"
OUT_DIR = PROJ / "data/processed/phase_context/relation_detr_seed42"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
NUM_PHASES = len(VOCAB)
DEFAULT_CKPT = (PROJ / "experiments/phase1/s4_phase_baseline_001_frozen_tecno_phase_baseline_seed42"
                / "checkpoints/best_tecno.pth")


def load_clips(split: str):
    d = np.load(CACHE_DIR / f"{split}_gap.npz")
    feats_all = d["features"]
    feat_by_frame = {str(fid): feats_all[i] for i, fid in enumerate(d["frame_ids"])}
    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    for clip in man["clips"]:
        frames = clip["frames"]
        feats = np.stack([feat_by_frame[fr["frame"]] for fr in frames]).astype(np.float32)
        ids = [fr["frame"] for fr in frames]
        yield clip["clip_id"], ids, feats


def load_teacher(ckpt_path: Path, device) -> TeCNO:
    """凍結 S4 base（素 TeCNO・neck 無）。ckpt は {"tecno": state_dict, ...}。"""
    model = TeCNO(num_stages=2, num_layers=8, num_f_maps=64, in_dim=2048, num_classes=NUM_PHASES)
    # S4 TeCNO ckpt は {"tecno": state_dict, "epoch", "val"} の単純構造（検出器 ckpt と違い
    # _classes_ を含まない）→ 規約通り weights_only=True。
    sd = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    sd = sd["tecno"] if isinstance(sd, dict) and "tecno" in sd else sd
    model.load_state_dict(sd)
    model.eval().to(device)
    for p in model.parameters():
        p.requires_grad_(False)
    return model


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser(description="Frozen S4 phase teacher → per-frame posterior (phase context).")
    ap.add_argument("--subset", required=True, choices=["train", "val", "test"])
    ap.add_argument("--ckpt", default=str(DEFAULT_CKPT))
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    teacher = load_teacher(Path(args.ckpt), device)
    ids, ctxs = [], []
    for _clip_id, frame_ids, feats in load_clips(args.subset):
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)   # (1, 2048, T)
        logits = teacher(x)[-1]                                  # 最終ステージ (1, 9, T)
        post = F.softmax(logits[0], dim=0).T.cpu().numpy()       # (T, 9) causal posterior
        ctxs.append(post.astype(np.float32))
        ids.extend(frame_ids)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.subset}_phasectx.npz"
    ctx_arr = np.concatenate(ctxs, axis=0)
    np.savez(out, frame_ids=np.asarray(ids), ctx=ctx_arr)
    print(f"[phasectx] saved {ctx_arr.shape[0]} x {ctx_arr.shape[1]} -> {out} "
          f"(mean max-prob={ctx_arr.max(1).mean():.3f})")


if __name__ == "__main__":
    main()

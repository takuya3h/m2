#!/usr/bin/env python
"""T1a 用: 凍結検出器の region-token（object-query 埋め込み）抽出（TAPIS/GraSP 型・②系統）。

凍結 Relation-DETR seed42（= 三角形の源, mAP 0.7303）を**フル forward** し、デコーダ最終層の
**object-query 埋め込み**（= `class_head[-1]` への入力 = `norm(query)`, (Q,256)）と、その
**per-query クラス logits**（= `class_head[-1]` の出力, (Q,15)）を 1 つの forward hook で捕捉する。

region 表現（ユーザー確定: クラス別 256-d 埋め込み）:
    scores = sigmoid(logits)                      # (Q,15) Relation-DETR は focal/sigmoid 採点
    各器具クラス c=0..14:
      q* = argmax_q scores[q,c]
      region[c] = scores[q*,c] · embedding[q*]    # 256-d（score でソフトに存在ゲート）
    region = concat_c region[c]  → 15×256 = 3840-d

これを工程枝で GAP(2048) に連結 → TeCNO（in_dim=5888）が T1a。Δ_phase=(T1a − S4 base)。
B2a の 15-d tool-presence（クラス別最大スコアの**スカラ**）に対し、T1a は同じクラス軸で
**256-d 埋め込み**（物体特徴）を渡す——埋め込み vs スカラで明確に差別化される。

GAP/frame_id を揃えるため phase manifest を走査（frame_id = fr["frame"]）。
低メモリ（走行中ジョブを邪魔しない）: batch=1 / fp16 autocast / no_grad。

実行（必ず .venv-relation-detr を activate: ninja を PATH に載せ MS-Deform-Attn を JIT）:
  source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda-11.8
  CUDA_VISIBLE_DEVICES=0 python scripts/extract_t1a_regiontoken.py --subset val --limit 8   # スモーク
  CUDA_VISIBLE_DEVICES=0 python scripts/extract_t1a_regiontoken.py --subset train --limit 0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torchvision.io import ImageReadMode, read_image

PROJ = Path(__file__).resolve().parents[1]
_REPO = PROJ / "third_party" / "Relation-DETR"
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from util.lazy_load import Config  # noqa: E402
from util.utils import load_checkpoint, load_state_dict  # noqa: E402

MANIFEST_DIR = PROJ / "data/processed/phase_manifest"
NUM_TOOLS = 15
EMBED_DIM = 256
REGION_DIM = NUM_TOOLS * EMBED_DIM  # 3840
import os  # noqa: E402  再抽出の env 上書き用

MODEL_CFG = str(_REPO / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
# 改善検出器での再抽出: env で ckpt / frozen タグを上書き（既定=凍結源 seed42・後方互換）
_FROZEN_TAG = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
CKPT = os.environ.get("RELDETR_EXTRACT_CKPT", str(_REPO / "checkpoints/incoming/seed42/best_ap.pth"))
OUT_DIR = PROJ / f"data/processed/t1a_regiontoken/{_FROZEN_TAG}"


class _DecoderCapture:
    """decoder.class_head[-1] の forward hook。最終層の (region token, logits) を捕捉する。

    class_head は per-layer ModuleList（len=num_layers）。[-1] は最終層のみで 1 回発火するが、
    共有実装でも「最後の発火＝最終層」を採るため毎回上書きで保持する（堅牢化）。
    """

    def __init__(self) -> None:
        self.tokens = None   # (Q, 256)
        self.logits = None   # (Q, 15)

    def __call__(self, module, inputs, output):
        self.tokens = inputs[0].detach()[0]   # (B,Q,256) -> (Q,256), B=1
        self.logits = output.detach()[0]      # (B,Q,15)  -> (Q,15)

    def reset(self):
        self.tokens = self.logits = None


def region_vector(cap: _DecoderCapture) -> np.ndarray:
    """捕捉した (tokens, logits) → クラス別 256-d 埋め込み連結（3840-d）。"""
    scores = torch.sigmoid(cap.logits.float())          # (Q,15)
    tokens = cap.tokens.float()                          # (Q,256)
    region = torch.zeros(NUM_TOOLS, EMBED_DIM, dtype=torch.float32)
    qstar = scores.argmax(dim=0)                         # (15,) 各クラス最高スコアの query idx
    for c in range(NUM_TOOLS):
        q = int(qstar[c])
        region[c] = scores[q, c] * tokens[q]             # score でソフトゲート
    return region.reshape(-1).cpu().numpy()              # (3840,)


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser(description="T1a frozen-detector region-token extractor (per-class 256-d).")
    ap.add_argument("--subset", required=True, choices=["train", "val", "test"])
    ap.add_argument("--limit", type=int, default=0, help="先頭 N 件のみ（0=全件, スモーク用）")
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    model = Config(MODEL_CFG).model.eval()
    ckpt = load_checkpoint(CKPT)
    if isinstance(ckpt, dict) and "model" in ckpt:
        ckpt = ckpt["model"]
    load_state_dict(model, ckpt)
    model.to(device)
    for p in model.parameters():
        p.requires_grad_(False)

    # region-token を捕捉する hook を最終層 class head に登録（Fail Loud: パス検証）。
    head = model.transformer.decoder.class_head[-1]
    assert getattr(head, "in_features", None) == EMBED_DIM, f"class_head[-1] in={getattr(head,'in_features',None)}"
    assert getattr(head, "out_features", None) == NUM_TOOLS, f"class_head[-1] out={getattr(head,'out_features',None)}"
    cap = _DecoderCapture()
    handle = head.register_forward_hook(cap)

    manifest = json.loads((MANIFEST_DIR / f"{args.subset}.json").read_text())
    ids, regs = [], []
    i = 0
    for clip in manifest["clips"]:
        for fr in clip["frames"]:
            if args.limit and i >= args.limit:
                break
            try:
                img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
            except Exception as exc:  # noqa: BLE001
                print(f"[t1a][skip] 読込失敗 {fr['frame']}: {exc}")
                continue
            cap.reset()
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                _ = model([img.to(device)])  # eval forward → hook が最終層 (tokens, logits) を捕捉
            if cap.tokens is None or cap.logits is None:
                raise RuntimeError(f"hook 未発火: region-token を捕捉できません ({fr['frame']})")
            regs.append(region_vector(cap))
            ids.append(fr["frame"])
            i += 1
            if i % 500 == 0:
                print(f"[t1a] {i} frames done", flush=True)
        if args.limit and i >= args.limit:
            break

    handle.remove()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.subset}_regiontoken.npz"
    reg_arr = np.stack(regs).astype(np.float32)
    np.savez(out, frame_ids=np.asarray(ids), region=reg_arr)
    nz = (np.abs(reg_arr) > 1e-6).mean()
    print(f"[t1a] saved {reg_arr.shape[0]} x {reg_arr.shape[1]} -> {out} "
          f"(nonzero frac={nz:.3f} absmax={np.abs(reg_arr).max():.3f})")


if __name__ == "__main__":
    main()

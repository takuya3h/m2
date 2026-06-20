#!/usr/bin/env python
"""B2a 用: 凍結検出 tool-presence 信号の抽出（片方向 検出→工程・Tier-0）。

凍結 Relation-DETR seed42（= 三角形の源, mAP 0.7303）を**フル forward** し、各フレームの
予測から **15-d tool-presence ベクトル**（クラス別の最大予測スコア ∈[0,1]）を作る。これを
工程枝の入力 GAP(2048) に連結して TeCNO を学習するのが B2a（Δ_phase = B2a − S4）。

GAP キャッシュと frame_id を揃えるため **phase manifest を走査**（frame_id = fr["frame"]）。
出力: npz（frame_ids: (N,), signal: (N, 15) float32, max score/class）。

低メモリ運用（走行中 B1 を邪魔しない）: batch=1 / fp16 autocast / no_grad（検出器推論のみ ~5-8GB）。

実行（.venv-relation-detr, cwd=third_party/Relation-DETR で ninja を PATH に）:
  source ../../.venv-relation-detr/bin/activate
  CUDA_VISIBLE_DEVICES=0 python ../../scripts/extract_b2a_detsignal.py --subset train --limit 0
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
MODEL_CFG = str(_REPO / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
CKPT = str(_REPO / "checkpoints/incoming/seed42/best_ap.pth")
OUT_DIR = PROJ / "data/processed/b2a_detsignal/relation_detr_seed42"


def tool_presence(pred: dict) -> np.ndarray:
    """予測 dict（scores/labels）→ 15-d クラス別最大スコア（無ければ 0）。"""
    sig = np.zeros(NUM_TOOLS, dtype=np.float32)
    scores = pred["scores"].detach().cpu().numpy()
    labels = pred["labels"].detach().cpu().numpy().astype(int)
    for c in range(NUM_TOOLS):
        m = labels == c
        if m.any():
            sig[c] = float(scores[m].max())
    return sig


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser(description="B2a frozen-detector tool-presence extractor (15-d).")
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

    manifest = json.loads((MANIFEST_DIR / f"{args.subset}.json").read_text())
    ids, sigs = [], []
    i = 0
    for clip in manifest["clips"]:
        for fr in clip["frames"]:
            if args.limit and i >= args.limit:
                break
            try:
                img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
            except Exception as exc:  # noqa: BLE001
                print(f"[b2a][skip] 読込失敗 {fr['frame']}: {exc}")
                continue
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                preds = model([img.to(device)])  # eval forward → [ {scores,labels,boxes} ]
            sigs.append(tool_presence(preds[0]))
            ids.append(fr["frame"])
            i += 1
            if i % 500 == 0:
                print(f"[b2a] {i} frames done", flush=True)
        if args.limit and i >= args.limit:
            break

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{args.subset}_toolpresence.npz"
    sig_arr = np.stack(sigs).astype(np.float32)
    np.savez(out, frame_ids=np.asarray(ids), signal=sig_arr)
    nz = (sig_arr > 0).mean()
    print(f"[b2a] saved {sig_arr.shape[0]} x {sig_arr.shape[1]} -> {out} "
          f"(nonzero frac={nz:.3f} max={sig_arr.max():.3f})")


if __name__ == "__main__":
    main()

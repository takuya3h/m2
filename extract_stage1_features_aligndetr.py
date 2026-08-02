#!/usr/bin/env python
"""AlignDETR 版: Stage1 frozen backbone GAP 特徴抽出 (2048-d)。

Relation-DETR 版 (`extract_stage1_features.py`) と等価の出力 (npz: frame_ids, features=(N,2048))
を、AlignDETR (detrex/detectron2 系) から取得する。

台帳 Run「凍結源の下流有用性比較：Relation-DETR vs AlignDETR」用。
同じ TeCNO で det→phase Δ を測るため、両検出器の GAP を同一形式・同一 phase manifest で保存する。

前提:
  - phase manifest が `data/processed/phase_manifest/{train,val,test}.json` に存在。
  - AlignDETR-S0-frozen 学習済み ckpt が `--checkpoint` で指定される (S0-frozen 12ep 完走 後)。
  - .venv-detectron2 で実行。third_party/detrex を sys.path に載せる。

実行例:
  source .venv-detectron2/bin/activate
  python scripts/extract_stage1_features_aligndetr.py \\
    --subset val --limit 8 \\
    --config-file third_party/detrex/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py \\
    --checkpoint /tmp/aligndetr_s0frozen_seed42_XXXX/model_final.pth \\
    --out data/processed/stage1_features/aligndetr_s0frozen_seed42/val_gap.npz
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
_DETREX = PROJ / "third_party" / "detrex"
if str(_DETREX) not in sys.path:
    sys.path.insert(0, str(_DETREX))

# detectron2 / detrex 環境で実行される前提 (.venv-detectron2)
from detectron2.config import LazyConfig, instantiate  # noqa: E402
from detectron2.checkpoint import DetectionCheckpointer  # noqa: E402

MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"


def parse_args():
    p = argparse.ArgumentParser(description="AlignDETR frozen-backbone GAP extractor.")
    p.add_argument("--subset", required=True, choices=["train", "val", "test"])
    p.add_argument("--config-file", required=True, help="LazyConfig path (S0-frozen)")
    p.add_argument("--checkpoint", required=True, help="AlignDETR-S0-frozen 学習済 ckpt (.pth)")
    p.add_argument("--out", required=True, help="出力 npz path")
    p.add_argument("--limit", type=int, default=0, help="先頭 N 件のみ (0=全件)")
    p.add_argument("--device", default="cuda")
    return p.parse_args()


class C5Capture:
    """backbone forward hook で res5 (C5, 2048ch) を捕捉。"""

    def __init__(self):
        self.c5 = None

    def __call__(self, module, inputs, output):
        # detectron2 の ResNet は dict {"res3": ..., "res4": ..., "res5": ...} を返す
        assert isinstance(output, dict), f"backbone output type: {type(output)}"
        assert "res5" in output, f"backbone keys: {list(output.keys())}"
        self.c5 = output["res5"].detach()

    def reset(self):
        self.c5 = None


@torch.no_grad()
def main():
    args = parse_args()
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    # モデル構築 + 学習済 ckpt をロード
    cfg = LazyConfig.load(args.config_file)
    model = instantiate(cfg.model).to(device).eval()
    DetectionCheckpointer(model).load(args.checkpoint)
    for p in model.parameters():
        p.requires_grad_(False)

    trainable = sum(p.requires_grad for p in model.backbone.parameters())
    assert trainable == 0, f"backbone に学習可能パラメータが残っています: {trainable}"

    # backbone forward hook
    cap = C5Capture()
    handle = model.backbone.register_forward_hook(cap)

    manifest = json.loads((MANIFEST_DIR / f"{args.subset}.json").read_text(encoding="utf-8"))
    ids: list[str] = []
    feats: list[np.ndarray] = []
    feat_dim = None
    i = 0
    for clip in manifest["clips"]:
        for fr in clip["frames"]:
            if args.limit and i >= args.limit:
                break
            try:
                img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
            except Exception as exc:  # noqa: BLE001
                print(f"[stage1-align][skip] 読込失敗 {fr['frame']}: {exc}")
                continue
            cap.reset()
            # detectron2 標準の入力形式: [{"image": (C,H,W) uint8/float, "height": H, "width": W}]
            batched_inputs = [{
                "image": img.to(device).float(),
                "height": img.shape[1],
                "width": img.shape[2],
            }]
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                _ = model(batched_inputs)
            if cap.c5 is None:
                raise RuntimeError(f"backbone hook 未発火: C5 を捕捉できません ({fr['frame']})")
            # GAP: 単純 mean (padding なし想定, detectron2 は image を全域 resize)
            gap = cap.c5.mean(dim=(2, 3)).squeeze(0).float().cpu().numpy()  # (2048,)
            if feat_dim is None:
                feat_dim = gap.shape[0]
                print(f"[stage1-align] C5 shape={tuple(cap.c5.shape)}  GAP dim={feat_dim}  device={device}")
            ids.append(fr["frame"])
            feats.append(gap)
            i += 1
            if i % 200 == 0:
                print(f"[stage1-align] {i} frames done", flush=True)
        if args.limit and i >= args.limit:
            break

    handle.remove()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.stack(feats).astype(np.float32)
    np.savez(out_path, frame_ids=np.asarray(ids), features=arr)
    print(f"[stage1-align] saved {arr.shape[0]} x {arr.shape[1]} -> {out_path}")


if __name__ == "__main__":
    main()

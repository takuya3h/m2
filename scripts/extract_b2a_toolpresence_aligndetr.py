#!/usr/bin/env python
"""AlignDETR 版: tool-presence 信号抽出（15-d, class-wise max sigmoid score）。

Relation-DETR 版 (`extract_b2a_detsignal.py`) と等価の出力 (npz: frame_ids, signal=(N,15)) を、
AlignDETR (detrex) の class_embed[-1] hook から取得する。

抽出ロジック:
    scores = sigmoid(logits)           # (Q, 15)
    presence[c] = max_q scores[q, c]   # (15,)  クラス別最大 query score

region-token 版と同じ decoder hook を使うため、同一 config/checkpoint 前提。
台帳 Run「AlignDETR 凍結特徴抽出（region-token/tool-presence, val+train）」用。

実行例:
  source .venv-detectron2/bin/activate
  python scripts/extract_b2a_toolpresence_aligndetr.py \\
    --subset val \\
    --config-file third_party/detrex/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py \\
    --checkpoint /tmp/aligndetr_s0frozen_seed42/model_final.pth \\
    --out data/processed/b2a_detsignal/aligndetr_s0frozen_seed42/val_toolpresence.npz
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

from detectron2.config import LazyConfig, instantiate  # noqa: E402
from detectron2.checkpoint import DetectionCheckpointer  # noqa: E402

MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
NUM_TOOLS = 15
EMBED_DIM = 256


class DecoderCapture:
    """AlignDETR の class_embed[-1] logits を forward hook で捕捉。"""

    def __init__(self):
        self.logits = None  # (Q, 15)

    def __call__(self, module, inputs, output):
        assert output.dim() == 3, f"logits shape unexpected: {output.shape}"
        self.logits = output.detach()[0]  # (Q, 15)

    def reset(self):
        self.logits = None


def tool_presence(cap: DecoderCapture) -> np.ndarray:
    """15-d tool-presence: クラス別に query 最大の sigmoid スコア。"""
    scores = torch.sigmoid(cap.logits.float())  # (Q, 15)
    return scores.max(dim=0).values.cpu().numpy()  # (15,)


def parse_args():
    p = argparse.ArgumentParser(description="AlignDETR tool-presence extractor (15-d).")
    p.add_argument("--subset", required=True, choices=["train", "val", "test"])
    p.add_argument("--config-file", required=True, help="LazyConfig path")
    p.add_argument("--checkpoint", required=True, help="AlignDETR-S0-frozen 学習済 ckpt")
    p.add_argument("--out", required=True, help="出力 npz path")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--device", default="cuda")
    return p.parse_args()


@torch.no_grad()
def main():
    args = parse_args()
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    cfg = LazyConfig.load(args.config_file)
    model = instantiate(cfg.model).to(device).eval()
    DetectionCheckpointer(model).load(args.checkpoint)
    for p in model.parameters():
        p.requires_grad_(False)

    head = model.class_embed[-1]
    assert getattr(head, "in_features", None) == EMBED_DIM
    assert getattr(head, "out_features", None) == NUM_TOOLS

    cap = DecoderCapture()
    handle = head.register_forward_hook(cap)

    manifest = json.loads((MANIFEST_DIR / f"{args.subset}.json").read_text(encoding="utf-8"))
    ids: list[str] = []
    sigs: list[np.ndarray] = []
    i = 0
    for clip in manifest["clips"]:
        for fr in clip["frames"]:
            if args.limit and i >= args.limit:
                break
            try:
                img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
            except Exception as exc:  # noqa: BLE001
                print(f"[b2a-align][skip] 読込失敗 {fr['frame']}: {exc}")
                continue
            cap.reset()
            batched_inputs = [{
                "image": img.to(device).float(),
                "height": img.shape[1],
                "width": img.shape[2],
            }]
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                _ = model(batched_inputs)
            if cap.logits is None:
                raise RuntimeError(f"decoder hook 未発火: logits を捕捉できません ({fr['frame']})")
            sigs.append(tool_presence(cap))
            ids.append(fr["frame"])
            i += 1
            if i % 500 == 0:
                print(f"[b2a-align] {i} frames done", flush=True)
        if args.limit and i >= args.limit:
            break

    handle.remove()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.stack(sigs).astype(np.float32)
    np.savez(out_path, frame_ids=np.asarray(ids), signal=arr)
    print(f"[b2a-align] saved {arr.shape[0]} x {arr.shape[1]} -> {out_path} "
          f"(mean={arr.mean():.3f} max={arr.max():.3f})")


if __name__ == "__main__":
    main()

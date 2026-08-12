#!/usr/bin/env python
"""AlignDETR 版: region-token (object-query 埋め込み) 抽出 (3840-d = 15×256)。

Relation-DETR 版 (`extract_t1a_regiontoken.py`) と等価の出力 (npz: frame_ids, region=(N,3840))
を、AlignDETR (detrex) の decoder 最終層 class_embed[-1] hook から取得する。

抽出ロジック (Relation-DETR 版と完全一致):
    scores = sigmoid(logits)                      # (Q,15)
    for each class c:
      q* = argmax_q scores[q,c]
      region[c] = scores[q*,c] · embedding[q*]    # 256-d (score でソフトゲート)
    region = concat_c region[c]                   # 3840-d

AlignDETR は self.class_embed = nn.ModuleList([Linear(256,15) x (dec_layers+1)])。
最終層 = self.class_embed[-1] を forward hook で捕捉 (inputs[0] = tokens, output = logits)。

実行例:
  source .venv-detectron2/bin/activate
  python scripts/extract_t1a_regiontoken_aligndetr.py \\
    --subset val --limit 8 \\
    --config-file third_party/detrex/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py \\
    --checkpoint /tmp/aligndetr_s0frozen_seed42_XXXX/model_final.pth \\
    --out data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42/val_regiontoken.npz
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
REGION_DIM = NUM_TOOLS * EMBED_DIM  # 3840


class DecoderCapture:
    """AlignDETR の class_embed[-1] (Linear(256,15)) を forward hook で捕捉。

    AlignDETR.forward 内で `outputs_class = self.class_embed[lvl](inter_states[lvl])`
    が per-layer 呼ばれる。最終層 self.class_embed[-1] の (inputs[0]=tokens, output=logits) を上書き保持。
    """

    def __init__(self):
        self.tokens = None  # (Q, 256)
        self.logits = None  # (Q, 15)

    def __call__(self, module, inputs, output):
        assert inputs[0].dim() == 3, f"tokens shape unexpected: {inputs[0].shape}"
        assert output.dim() == 3, f"logits shape unexpected: {output.shape}"
        # batch=1 前提 (推論)
        self.tokens = inputs[0].detach()[0]   # (Q, 256)
        self.logits = output.detach()[0]      # (Q, 15)

    def reset(self):
        self.tokens = self.logits = None


def region_vector(cap: DecoderCapture) -> np.ndarray:
    """Relation-DETR 版と完全一致の region 表現生成。"""
    scores = torch.sigmoid(cap.logits.float())          # (Q, 15)
    tokens = cap.tokens.float()                         # (Q, 256)
    region = torch.zeros(NUM_TOOLS, EMBED_DIM, dtype=torch.float32)
    qstar = scores.argmax(dim=0)                        # (15,)
    for c in range(NUM_TOOLS):
        q = int(qstar[c])
        region[c] = scores[q, c] * tokens[q]            # score でソフトゲート
    return region.reshape(-1).cpu().numpy()             # (3840,)


def parse_args():
    p = argparse.ArgumentParser(description="AlignDETR region-token extractor (per-class 256-d).")
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

    # 最終層 class_embed[-1] は Linear(256, 15) のはず
    head = model.class_embed[-1]
    assert getattr(head, "in_features", None) == EMBED_DIM, \
        f"class_embed[-1] in={getattr(head, 'in_features', None)}"
    assert getattr(head, "out_features", None) == NUM_TOOLS, \
        f"class_embed[-1] out={getattr(head, 'out_features', None)}"

    cap = DecoderCapture()
    handle = head.register_forward_hook(cap)

    manifest = json.loads((MANIFEST_DIR / f"{args.subset}.json").read_text(encoding="utf-8"))
    ids: list[str] = []
    regs: list[np.ndarray] = []
    i = 0
    for clip in manifest["clips"]:
        for fr in clip["frames"]:
            if args.limit and i >= args.limit:
                break
            try:
                img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
            except Exception as exc:  # noqa: BLE001
                print(f"[t1a-align][skip] 読込失敗 {fr['frame']}: {exc}")
                continue
            cap.reset()
            batched_inputs = [{
                "image": img.to(device).float(),
                "height": img.shape[1],
                "width": img.shape[2],
            }]
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(device.type == "cuda")):
                _ = model(batched_inputs)
            if cap.tokens is None or cap.logits is None:
                raise RuntimeError(f"decoder hook 未発火: region-token を捕捉できません ({fr['frame']})")
            regs.append(region_vector(cap))
            ids.append(fr["frame"])
            i += 1
            if i % 500 == 0:
                print(f"[t1a-align] {i} frames done", flush=True)
        if args.limit and i >= args.limit:
            break

    handle.remove()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.stack(regs).astype(np.float32)
    np.savez(out_path, frame_ids=np.asarray(ids), region=arr)
    nz = (np.abs(arr) > 1e-6).mean()
    print(f"[t1a-align] saved {arr.shape[0]} x {arr.shape[1]} -> {out_path} "
          f"(nonzero frac={nz:.3f} absmax={np.abs(arr).max():.3f})")


if __name__ == "__main__":
    main()

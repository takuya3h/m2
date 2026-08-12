#!/usr/bin/env python
"""Stage1 特徴抽出（2段方式 / 研究ピボット §5.3・STEP A）。

凍結した Relation-DETR の ResNet-50 backbone で各フレームの空間特徴を抽出し、
工程認識（S4 / TeCNO）の入力となる **GAP 2048-d ベクトル**をキャッシュする。

設計上の要点:
  - 凍結源は STEP 0-2 で確定した Relation-DETR seed42 完走 ckpt（再 eval で mAP 0.7303 再現）。
  - 抽出経路は検出器の forward と同一: ``model.preprocess`` → ``model.backbone(images.tensors)``。
    eval_transform（resize 800/1333 + 正規化）も検出と完全一致するため特徴が忠実。
  - phase 入力は backbone の **C5（2048ch）を valid 領域で GAP** した 2048-d。neck（ChannelMapper）は
    検出専用なので使わない。
  - 検出側 S0-frozen は多階層マップが巨大（全フレームで TB 級）でキャッシュ非現実的なため、
    凍結 backbone を学習時オンザフライ forward する想定。本スクリプトのキャッシュは **phase 用**。

実行（必ず .venv-relation-detr を activate: ninja を PATH に載せ MS-Deform-Attn を JIT）:
  cd third_party/Relation-DETR
  source ../../.venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda
  python ../../scripts/extract_stage1_features.py \
    --coco-path ../../data/eval_staging/egosurgery_val --subset val \
    --model-config configs/relation_detr/relation_detr_resnet50_egosurgery.py \
    --checkpoint checkpoints/incoming/seed42/best_ap.pth \
    --out ../../data/processed/stage1_features/relation_detr_seed42/val_gap.npz \
    --limit 8            # スモーク。本番は --limit 0（全件）

出力: npz（image_ids: (N,), features: (N, 2048) float32）。image_id でキーづけして読む。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils import data
from torchvision.io import ImageReadMode, read_image

# プロジェクトルートと Relation-DETR repo（datasets/util/models）を import 可能にする。
# 絶対パス起動でも cwd 非依存で解決する。
PROJ = Path(__file__).resolve().parents[1]
_REPO = PROJ / "third_party" / "Relation-DETR"
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

# 以下は sys.path 設定後に import する必要があるため E402 を抑制する。
from datasets.coco import CocoDetection  # noqa: E402
from util.collate_fn import collate_fn  # noqa: E402
from util.lazy_load import Config  # noqa: E402
from util.utils import load_checkpoint, load_state_dict  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Stage1 frozen-backbone feature extractor (GAP 2048-d).")
    # 入力は (a) phase manifest（推奨, build_phase_manifest.py の出力）か (b) COCO-2017 レイアウト。
    p.add_argument("--manifest", type=str, default=None,
                   help="phase manifest json（指定時はこちらを優先。画像をパス直読みで処理）")
    p.add_argument("--coco-path", type=str, default=None, help="COCO-2017 レイアウトのルート（--manifest 未指定時）")
    p.add_argument("--subset", type=str, default="val")
    p.add_argument("--model-config", type=str, required=True)
    p.add_argument("--checkpoint", type=str, required=True)
    p.add_argument("--out", type=str, required=True, help="出力 npz パス")
    p.add_argument("--limit", type=int, default=0, help="先頭 N 件のみ（0=全件, スモーク用）")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--device", type=str, default="cuda")
    return p.parse_args()


def masked_gap(feat: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """padding を除いた valid 領域で GAP する。

    Args:
        feat: (B, C, h, w) backbone の C5 特徴。
        mask: (B, H, W) construct_mask 由来（1=pad, 0=valid）。
    Returns:
        (B, C) の GAP ベクトル。
    """
    m = F.interpolate(mask[None].float(), size=feat.shape[-2:])[0]  # (B, h, w)
    valid = (m < 0.5).float().unsqueeze(1)                          # (B, 1, h, w)
    summed = (feat * valid).sum(dim=(2, 3))
    count = valid.sum(dim=(2, 3)).clamp(min=1.0)
    return summed / count


def _iter_manifest(args):
    """phase manifest を時系列順に走査し (frame_id, uint8 RGB テンソル) を yield する。"""
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    for clip in manifest["clips"]:
        for fr in clip["frames"]:
            # 防御: 破損/空 jpg（0バイト等）で read_image が落ちても全体を止めず skip+記録する。
            try:
                img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
            except Exception as exc:  # noqa: BLE001  (画像読込の全失敗を skip 対象にする)
                print(f"[stage1][skip] 読込失敗 {fr['frame']}: {exc}")
                continue
            yield fr["frame"], img


def _iter_coco(args):
    """COCO-2017 レイアウトを走査し (str(image_id), uint8 RGB テンソル) を yield する。"""
    dataset = CocoDetection(
        img_folder=f"{args.coco_path}/{args.subset}2017",
        ann_file=f"{args.coco_path}/annotations/instances_{args.subset}2017.json",
        transforms=None,  # eval_transform はモデル内蔵
        train=False,
    )
    loader = data.DataLoader(
        dataset, batch_size=1, shuffle=False, num_workers=args.workers, collate_fn=collate_fn,
    )
    for images, targets in loader:
        yield str(int(targets[0]["image_id"])), images[0]


@torch.no_grad()
def main():
    args = parse_args()
    if not args.manifest and not args.coco_path:
        raise SystemExit("--manifest か --coco-path のどちらかを指定してください。")
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    # モデル構築 + 凍結重みロード（test.py と同一経路）
    model = Config(args.model_config).model.eval()
    checkpoint = load_checkpoint(args.checkpoint)
    if isinstance(checkpoint, dict) and "model" in checkpoint:
        checkpoint = checkpoint["model"]
    load_state_dict(model, checkpoint)
    model.to(device)
    for prm in model.parameters():
        prm.requires_grad_(False)

    # backbone が確実に凍結・eval であることを確認（FrozenBN + freeze_indices に加え二重ガード）
    trainable = sum(p.requires_grad for p in model.backbone.parameters())
    assert trainable == 0, f"backbone に学習可能パラメータが残っています: {trainable}"

    source = _iter_manifest(args) if args.manifest else _iter_coco(args)

    ids: list[str] = []
    feats: list[np.ndarray] = []
    feat_dim = None
    for i, (frame_id, image) in enumerate(source):
        if args.limit and i >= args.limit:
            break
        # 検出器と同一の前処理 → backbone（OrderedDict layer2/3/4）→ C5 を valid GAP
        images_il, _, mask = model.preprocess([image.to(device)], None)
        multi_level_feats = model.backbone(images_il.tensors)
        if isinstance(multi_level_feats, dict):
            c5 = list(multi_level_feats.values())[-1]
        else:
            c5 = multi_level_feats[-1]
        gap = masked_gap(c5, mask).squeeze(0).float().cpu().numpy()  # (2048,)
        if feat_dim is None:
            feat_dim = gap.shape[0]
            print(f"[stage1] C5 shape={tuple(c5.shape)}  GAP dim={feat_dim}  device={device}")
        ids.append(frame_id)
        feats.append(gap)
        if (i + 1) % 200 == 0:
            print(f"[stage1] {i + 1} frames done")

    # frame_ids は manifest の frame 文字列（例 "09_1_0213"）/ coco モードは str(image_id)。
    ids_arr = np.asarray(ids)
    feats_arr = np.stack(feats).astype(np.float32)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_path, frame_ids=ids_arr, features=feats_arr)
    print(
        f"[stage1] saved {feats_arr.shape[0]} x {feats_arr.shape[1]} features -> {out_path} "
        f"(min={feats_arr.min():.3f} max={feats_arr.max():.3f} mean={feats_arr.mean():.3f})"
    )


if __name__ == "__main__":
    main()

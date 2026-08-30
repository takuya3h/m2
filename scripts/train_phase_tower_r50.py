#!/usr/bin/env python
"""強い工程塔（暫定）: ImageNet-R50 を工程ラベルで微調整し、GAP 特徴を書き出す。

契約 T-2026-08-29-lecun-detector-env-pd の Phase C（B4）で要る。既存実装に
「画像から工程を学ぶ経路」が無かったため新設した（凍結検出器の特徴を使う
train_s4_tecno.py / train_b2a.py とは別系統）。

**学習に使う動画は train の 10 本のみ。** val・test の動画には触れない
（前契約 SPEC の「十五動画」は val 2・test 3 を含み分割違反であり、本契約で訂正された）。

出力する特徴は既存の GAP キャッシュと同じ形式にする:
    data/processed/stage1_features/<tag>/{train,val}_gap.npz  （frame_ids, features=2048d）
これにより train_s4_tecno.py / train_b2a.py が `RELDETR_FROZEN_TAG=<tag>` でそのまま読める。

    python scripts/train_phase_tower_r50.py --epochs 3 --tag imagenet_r50_phasetower_seed42
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils import data
from torchvision import transforms
from torchvision.models import ResNet50_Weights, resnet50

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402

MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
GAP_DIM = 2048

# ImageNet の標準前処理。学習側だけ軽い水平反転を入れる（検出器側の aug とは独立）。
NORM = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
TF_TRAIN = transforms.Compose([
    transforms.Resize((224, 224)), transforms.RandomHorizontalFlip(), transforms.ToTensor(), NORM,
])
TF_EVAL = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), NORM])


class FrameDataset(data.Dataset):
    """manifest の frame を 1 枚ずつ返す。順序は manifest のまま保つ（特徴の整列に要る）。"""

    def __init__(self, split: str, train: bool) -> None:
        man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
        self.items = [
            (fr["frame"], PROJ / fr["image_path"], int(fr["label"]))
            for clip in man["clips"] for fr in clip["frames"]
        ]
        self.tf = TF_TRAIN if train else TF_EVAL

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int):
        fid, path, label = self.items[i]
        with Image.open(path) as im:
            x = self.tf(im.convert("RGB"))
        return x, label, fid


def build_model(device) -> nn.Module:
    """ImageNet 事前学習 R50。fc を 9 クラスへ差し替える。"""
    m = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    m.fc = nn.Linear(m.fc.in_features, len(CLASS_NAMES))
    return m.to(device)


@torch.no_grad()
def extract(model: nn.Module, split: str, device, batch: int, workers: int):
    """GAP 特徴（fc の直前 2048-d）を manifest 順に取り出す。"""
    model.eval()
    ds = FrameDataset(split, train=False)
    loader = data.DataLoader(ds, batch_size=batch, shuffle=False, num_workers=workers, pin_memory=True)
    feats, fids, labels, preds = [], [], [], []
    backbone = nn.Sequential(*list(model.children())[:-1])  # fc を外す
    for x, y, fid in loader:
        x = x.to(device, non_blocking=True)
        g = backbone(x).flatten(1)                 # (B, 2048)
        logit = model.fc(g)
        feats.append(g.cpu().numpy().astype(np.float32))
        preds.append(logit.argmax(1).cpu().numpy())
        labels.append(y.numpy())
        fids.extend(fid)
    return (np.concatenate(feats), np.asarray(fids, dtype="<U9"),
            np.concatenate(labels), np.concatenate(preds))


def main() -> None:
    ap = argparse.ArgumentParser(description="強い工程塔（ImageNet-R50 微調整）")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--num-workers", type=int, default=8)
    ap.add_argument("--tag", type=str, default="imagenet_r50_phasetower_seed42",
                    help="特徴キャッシュのタグ。stage1_features/<tag>/ へ書く")
    ap.add_argument("--out-json", type=str, default=None, help="塔単体の指標を書き出す json")
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tr = FrameDataset("train", train=True)
    videos = sorted({f.split("_")[0] for f, _, _ in tr.items})
    print(f"[tower] train frames={len(tr)} videos={videos} (val/test は使わない)", flush=True)

    loader = data.DataLoader(tr, batch_size=args.batch_size, shuffle=True,
                             num_workers=args.num_workers, pin_memory=True, drop_last=False)
    model = build_model(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        tot, n, correct = 0.0, 0, 0
        for x, y, _ in loader:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            logit = model(x)
            loss = ce(logit, y)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            tot += float(loss) * y.numel()
            n += y.numel()
            correct += int((logit.argmax(1) == y).sum())
        print(f"[tower][ep{ep}] loss={tot/n:.4f} train_acc={correct/n:.4f} "
              f"({time.time()-t0:.0f}s)", flush=True)
    train_seconds = time.time() - t0

    # --- 塔単体の val 性能（フレーム単位。時系列ヘッド無し）---
    _, _, y_va, p_va = extract(model, "val", device, args.batch_size, args.num_workers)
    ev = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    ev.update(p_va, y_va, video_id="val")
    tower = ev.compute()
    print(f"[tower] val accuracy={tower['phase_accuracy']:.4f} "
          f"macro_f1={tower['phase_macro_f1']:.4f}", flush=True)

    # --- 特徴を既存形式で書き出す ---
    out_dir = PROJ / "data" / "processed" / "stage1_features" / args.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    for split in ("train", "val"):
        f, fid, _, _ = extract(model, split, device, args.batch_size, args.num_workers)
        np.savez(out_dir / f"{split}_gap.npz", frame_ids=fid, features=f)
        print(f"[tower] wrote {out_dir/f'{split}_gap.npz'} {f.shape}", flush=True)

    if args.out_json:
        Path(args.out_json).write_text(json.dumps({
            "tag": args.tag, "seed": args.seed, "epochs": args.epochs,
            "train_videos": videos, "train_frames": len(tr),
            "train_seconds": train_seconds,
            "tower_val": {k: v for k, v in tower.items() if not isinstance(v, dict)},
            "tower_val_per_class_f1": tower.get("phase_per_class_f1", {}),
        }, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

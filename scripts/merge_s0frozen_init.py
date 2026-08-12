#!/usr/bin/env python
"""S0-frozen の初期化重みを合成する（研究ピボット §2.2 Step2a）。

S0-frozen = 凍結 backbone（= seed42 完走 ckpt の ResNet-50）+ 学習する検出ヘッド。
検出ヘッドの init は §6（三角形で検出ヘッド init を共有）と s0_016 の前例（COCO 1x init→
fine-tune）に合わせ **COCO-init**。よって初期化重み = 「COCO 1x 重み」の backbone.* のみを
「seed42 backbone.*」で置換したもの。これを resume_from_checkpoint に渡し、backbone を凍結する。

出力: data/external/weights/relation_detr_s0frozen_init_seed42.pth
（class head は egosurgery 15 クラスと形状不一致のため load 時に reinit される＝s0_016 と同条件）

実行: .venv/bin/python scripts/merge_s0frozen_init.py
"""
from __future__ import annotations

from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[1]
COCO = PROJ / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"
SEED42 = PROJ / "third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth"
OUT = PROJ / "data/external/weights/relation_detr_s0frozen_init_seed42.pth"


def _state(d):
    return d["model"] if isinstance(d, dict) and "model" in d else d


def main() -> None:
    # weights_only=True: 純粋な state_dict（テンソルのみ）なので安全側で読む。
    coco = _state(torch.load(COCO, map_location="cpu", weights_only=True))
    seed = _state(torch.load(SEED42, map_location="cpu", weights_only=True))

    merged = dict(coco)
    replaced = 0
    for k, v in seed.items():
        if k.startswith("backbone"):
            merged[k] = v
            replaced += 1

    # 検証: backbone は seed42 と一致、非 backbone は COCO のまま
    bb_ok = all(
        torch.equal(merged[k], seed[k]) for k in seed if k.startswith("backbone")
    )
    head_keys = [k for k in coco if not k.startswith("backbone")]
    head_ok = all(torch.equal(merged[k], coco[k]) for k in head_keys)
    assert bb_ok, "backbone が seed42 と一致しません"
    assert head_ok, "非 backbone が COCO と一致しません"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    torch.save(merged, OUT)
    print(f"[merge] backbone replaced={replaced} (seed42) / head kept={len(head_keys)} (COCO)")
    print(f"[merge] saved -> {OUT}  ({OUT.stat().st_size // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()

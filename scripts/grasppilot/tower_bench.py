"""学び直しの費用の材料: andrew での塔の学習の一歩の時間（非公式 T-2026-10-31-grasp-pilot-probe、Task E-3）。

既定の置き場（experiments/、checkpoint）に何も書かない。測った値だけを --out に書く。重みは保存しない。

    ptower  工程塔の fine-tune の段（stage1_ptower_r3.finetune と同じ: R50、COCO の初期化、stem 凍結、短辺 800、反転、
            batch 16、AdamW lr 1e-4・wd 1e-4、単精度）。一歩 = batch 16 の順伝播と逆伝播（4 歩ごとに更新）。本体の .venv
    dtower  検出塔（D*-COCO の構成、presets.detr、batch 2、fp16 の自動混合精度、学習範囲は全体で backbone の freeze_indices は凍結）。
            記録の処方は 2 GPU（accelerate）。ここでは 1 GPU で測る。.venv-relation-detr

    python scripts/grasppilot/tower_bench.py ptower|dtower --out <json> [--warmup 10 --steps 60]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]


def ptower(a):
    sys.path.insert(0, str(PROJ / "scripts"))
    sys.path.insert(0, str(PROJ / "src"))
    import stage1_ptower_r3 as r3
    import torch
    from torch import nn
    from torch.utils.data import DataLoader
    clips = []
    for part in ("train",):
        clips += json.loads((PROJ / f"data/processed/phase_manifest/{part}.json").read_text())["clips"]
    train_videos = sorted({c["video"] for c in clips})
    assert not set(train_videos) & {"04", "05", "07"}
    ds = r3.FoldFrames(clips, train_videos, train=True)
    torch.manual_seed(42)
    loader = DataLoader(ds, batch_size=16, shuffle=True, num_workers=4, pin_memory=True)  # nosemgrep
    model, source, digest = r3.build_backbone(9, "cuda", "coco")
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4, weight_decay=1e-4)
    ce = nn.CrossEntropyLoss()
    model.train()
    r3.stem_eval(model)
    torch.cuda.reset_peak_memory_stats()
    times, shapes = [], []
    it = iter(loader)
    for step in range(1, a.warmup + a.steps + 1):
        images, y, _ = next(it)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        loss = ce(model(images.cuda(non_blocking=True)), y.cuda(non_blocking=True))
        (loss / 4).backward()
        if step % 4 == 0:
            opt.step()
            opt.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        if step > a.warmup:
            times.append(time.perf_counter() - t0)
            shapes.append(tuple(images.shape))
    return {"tower": "ptower fine-tune", "train_frames": len(ds), "batch": 16, "accum": 4, "steps_per_epoch": len(loader),
            "input_shapes": sorted(set(shapes)), "init": source, "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()),
            "times": times, "note": "一歩の時間はデータの読み込みの待ちを含まない（GPU の計算だけ）"}


def dtower(a):
    sys.path.insert(0, str(PROJ / "scripts"))
    import torch
    import train_t1b as t1b
    from stage2pilot import common as C
    torch.manual_seed(42)
    loader = t1b.build_det_loader(train=True)
    cfg = str(t1b.RELDETR / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
    model = t1b.build_model(torch.device("cuda"), 42, cfg, ckpt_override=str(C.DET_CKPT))
    t1b.register_classes(model, loader)
    model.set_phase_context = lambda ctx: None
    from optimizer import param_dict
    groups = param_dict.finetune_backbone_and_linear_projection(model, lr=1e-4)
    opt = torch.optim.AdamW(groups, lr=1e-4, weight_decay=1e-4)
    scaler = torch.cuda.amp.GradScaler()
    model.train()
    from util.collate_fn import DataPrefetcher
    pf = DataPrefetcher(loader, torch.device("cuda"))
    torch.cuda.reset_peak_memory_stats()
    times = []
    for step in range(a.warmup + a.steps):
        images, targets = pf.next()
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.autocast("cuda", dtype=torch.float16):
            loss = sum(model(images, targets).values())
        opt.zero_grad()
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1)
        scaler.step(opt)
        scaler.update()
        torch.cuda.synchronize()
        if step >= a.warmup:
            times.append(time.perf_counter() - t0)
    return {"tower": "dtower full", "batch": 2, "steps_per_epoch_1gpu": len(loader), "precision": "fp16 autocast",
            "trainable": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
            "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()), "times": times,
            "note": "記録の処方は 2 GPU・GPU ごとに batch 2。ここは 1 GPU・batch 2。データの読み込みの待ちを含まない"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=("ptower", "dtower"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--shared", action="store_true")
    a = ap.parse_args()
    import numpy as np
    import torch
    res = ptower(a) if a.which == "ptower" else dtower(a)
    t = res.pop("times")
    res.update(warmup=a.warmup, steps=a.steps, step_seconds_mean=float(np.mean(t)), step_seconds_median=float(np.median(t)),
               gpu=torch.cuda.get_device_name(0), gpu_shared_with_other_runs=a.shared,
               task_id="T-2026-10-31-grasp-pilot-probe")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str) + "\n")
    print(json.dumps(res, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()

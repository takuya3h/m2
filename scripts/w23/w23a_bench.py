"""利用者の指示（2026-11-02）(3): W3 の試走で 1 本の所要と記憶を測る（非公式 T-2026-11-01-stage2-w23-andrew）。

train_t1b.py の --smoke は 6 step で打ち切るため速度を測れない。そこで学習の経路と同じ関数（build_model・register_classes・
set_trainable・finetune_t1b・AdamW・bf16 の自動混合精度・勾配の刈り込み 0.1）で train を --steps 回まわし、
--warmup 以降の 1 step の秒数と記憶の山を測る。重みは保存しない。評価もしない（評価の所要は Task B-2 の実測を使う）。

    python scripts/w23/w23a_bench.py --type DX|B --w W1|W2|W3 --arm gt --out <json> [--steps 130 --warmup 30]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402

from stage2pilot import common as C  # noqa: E402

TRAINABLE = {"W1": "film", "W2": "w2", "W3": "all"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=("P1", "DX", "B"))
    ap.add_argument("--w", required=True, choices=tuple(TRAINABLE))
    ap.add_argument("--arm", default="gt")
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--signal-train", default=None)
    ap.add_argument("--grasp-map", default=None)
    ap.add_argument("--steps", type=int, default=130)
    ap.add_argument("--warmup", type=int, default=30)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device("cuda")
    torch.manual_seed(42)
    if a.grasp_map:
        from grasppilot import grasp_signals as G
        from grasppilot.pd_grasp import build_grasp_loader
        loader = build_grasp_loader(t1b.EGO_ROOT, t1b.ANN_DIR, True, a.grasp_map, G.HTSIndex(("train", "val")))
        ctx, dim = {}, 1
    else:
        loader = t1b.build_det_loader(train=True)
        sig = t1b.load_signal_npz(a.signal_train)
        dim = next(iter(sig.values())).shape[0]
        ctx, _ = t1b.build_imgid_to_ctx(loader.dataset.coco, sig, dim)
    model = t1b.build_model(device, 42, a.cfg, ckpt_override=str(C.DET_CKPT))
    t1b.register_classes(model, loader)
    t1b.set_trainable(model, TRAINABLE[a.w])
    from optimizer import param_dict
    opt = torch.optim.AdamW(param_dict.finetune_t1b(model, lr=1e-4, film_lr=5e-4), lr=1e-4, weight_decay=1e-4)
    from util.collate_fn import DataPrefetcher
    model.train()
    pf = DataPrefetcher(loader, device)
    torch.cuda.reset_peak_memory_stats()
    times = []
    for step in range(a.steps):
        t0 = time.perf_counter()
        images, targets = pf.next()
        model.set_phase_context(t1b.ctx_for_targets(targets, ctx, device, False, dim))
        if a.grasp_map:
            model.set_grasp_maps([t["grasp_map"] for t in targets])
        with torch.autocast("cuda", dtype=torch.bfloat16):
            loss = sum(model(images, targets).values())
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 0.1)
        opt.step()
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    meas = times[a.warmup:]
    res = {"task_id": "T-2026-11-01-stage2-w23-andrew", "type": a.type, "w": a.w, "arm": a.arm, "steps": a.steps,
           "warmup": a.warmup, "sec_per_step_mean": sum(meas) / len(meas), "sec_per_step_sorted_mid": sorted(meas)[len(meas) // 2],
           "steps_per_epoch": len(loader), "max_memory_allocated_MiB": torch.cuda.max_memory_allocated() / 2**20,
           "max_memory_reserved_MiB": torch.cuda.max_memory_reserved() / 2**20,
           "n_trainable": int(sum(p.numel() for p in model.parameters() if p.requires_grad)), "last_loss": float(loss)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()

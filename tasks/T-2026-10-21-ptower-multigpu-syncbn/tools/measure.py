"""Task E: memory and time of the third round's recipe on two GPUs.

    CUDA_VISIBLE_DEVICES=1,2 torchrun --nproc_per_node=2 --master_port=<p> measure.py --out <json>

The recipe unchanged: ft_batch_size 16 (8 per GPU), accumulation 4, whole frame at short side
800 (800x1422), fp32, the determinism switches on, fold A's train set with the flip,
``workers`` from the config. Uses ``stage1_ptower_r3_dist``'s own ``setup``, ``wrap``,
``ShardedBatches`` and ``micro_step``, as its ``finetune`` does; no val, no evidence.

Time per micro-step is taken two ways, both after ``torch.cuda.synchronize``:
``wall`` from the end of the previous micro-step (includes waiting for the loader; this is
REPORT §3's measure) and ``compute`` from the moment the batch arrived. The mean drops the
first ``--warmup`` micro-steps. An out-of-memory error is a result: the micro-step, the phase
and the memory at that moment are recorded and the run stops (the batch is never changed).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.distributed as dist
from omegaconf import OmegaConf
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402
import stage1_ptower_r3_dist as dp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=68)
    ap.add_argument("--warmup", type=int, default=8)
    args = ap.parse_args()
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_r3.yaml")
    base.deterministic(cfg.seed)
    rank, world, device = dp.setup()
    per_gpu = dp.per_rank_batch(int(cfg.ft_batch_size), world)
    split = base.folds()[cfg.fold]
    clips = base.manifests(cfg)
    names = json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text())
    train_set = r3.FoldFrames(clips, split["train"], train=True)
    model, _, digest = r3.build_backbone(len(names), device, cfg.init)
    ddp = dp.wrap(model, device)
    torch.manual_seed(dp.rank_seed(cfg.seed, rank))
    determinism = dp.determinism_state()
    sampler = dp.ShardedBatches(len(train_set), int(cfg.ft_batch_size), rank, world, cfg.seed)
    sampler.set_epoch(1)
    loader = DataLoader(train_set, batch_sampler=sampler, num_workers=cfg.workers,
                        pin_memory=cfg.get("pin_memory", True))  # nosemgrep
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=cfg.ft_lr, weight_decay=cfg.ft_weight_decay)
    accum = int(cfg.ft_accum_steps)
    steps = len(sampler)
    torch.cuda.reset_peak_memory_stats(device)
    ddp.train()
    r3.stem_eval(model)
    optimizer.zero_grad(set_to_none=True)
    walls, computes, shape, phase, step = [], [], None, "load", 0
    result = {"oom": False}
    torch.cuda.synchronize(device)
    t_prev = time.perf_counter()
    try:
        for step, (images, y, _) in enumerate(loader, start=1):
            t0 = time.perf_counter()
            images = images.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            shape = shape or list(images.shape)
            phase = "forward/backward"
            boundary = step % accum == 0 or step == steps
            dp.micro_step(ddp, images, y, sampler.count(step), world, accum, boundary)
            phase = "optimizer"
            if boundary:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            torch.cuda.synchronize(device)
            now = time.perf_counter()
            walls.append(now - t_prev)
            computes.append(now - t0)
            t_prev = now
            phase = "load"
            if step >= args.steps:
                break
    except torch.cuda.OutOfMemoryError as exc:
        result.update(oom=True, oom_step=step, oom_phase=phase,
                      oom_message=str(exc).splitlines()[0],
                      memory_allocated_at_oom=int(torch.cuda.memory_allocated(device)))
    warm_wall, warm_compute = walls[args.warmup:], computes[args.warmup:]
    result.update({
        "rank": rank, "world_size": world, "device_index_visible": device.index,
        "per_gpu_batch": per_gpu, "ft_batch_size": int(cfg.ft_batch_size), "accum": accum,
        "input_shape": shape, "dtype": "float32", "backbone_init_sha256": digest,
        "determinism": determinism, "train_frames": len(train_set),
        "micro_steps_per_epoch": steps, "steps_done": len(walls), "warmup_excluded": args.warmup,
        "micro_step_wall_seconds_mean": float(np.mean(warm_wall)) if warm_wall else None,
        "micro_step_wall_seconds_median": float(np.median(warm_wall)) if warm_wall else None,
        "micro_step_compute_seconds_mean": float(np.mean(warm_compute)) if warm_compute else None,
        "micro_step_wall_seconds_all": [round(t, 4) for t in walls],
        "max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
        "max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
        "device_total_bytes": int(torch.cuda.get_device_properties(device).total_memory),
        "gpu_name": torch.cuda.get_device_name(device)})
    results = dp.gather(result)
    if rank == 0:
        Path(args.out).write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps([{k: v for k, v in r.items() if not k.endswith("_all")} for r in results]))
    dist.destroy_process_group()


if __name__ == "__main__":
    main()

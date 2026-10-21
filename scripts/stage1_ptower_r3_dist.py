"""Stage 1 third round on several GPUs: the same fine-tune as ``stage1_ptower_r3.finetune``.

Only a torchrun launch (``WORLD_SIZE`` > 1) comes here; a plain launch keeps the one-GPU
path untouched. The recipe stays the one-GPU recipe:

- ``ft_batch_size`` is still the physical batch over all ranks; each rank takes an equal
  share and the run refuses to start when it does not divide.
- layer1-4's BatchNorm becomes SyncBatchNorm, so every batch is normalised and the running
  statistics updated with all ranks' frames. The frozen stem's ``bn1`` stays a plain
  BatchNorm2d in eval, its running statistics untouched.
- Gradients are averaged across ranks only at the accumulation boundary (``no_sync``
  elsewhere), the same boundary as the one-GPU loop.
- Every rank walks the same shuffled global batches, cut like the one-GPU loader (the tail
  is kept), and keeps its own shard. The loss is scaled so the averaged gradient equals the
  mean over the global batch even when the tail's shards differ in size.
- Each rank's augmentation draws from its own seed, so flips do not repeat across ranks.
- Val, the checkpoint, the evidence and W&B are rank 0's alone; the plateau decision is
  broadcast so every rank lowers the rate and stops at the same epoch.

    CUDA_VISIBLE_DEVICES=1,2 torchrun --nproc_per_node=2 --master_port=29501 \
        scripts/stage1_ptower_r3.py action=finetune
"""
from __future__ import annotations

import datetime
import json
import os
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import stage1_ptower as base
import stage1_ptower_r3 as r3
import torch
import torch.distributed as dist
import torch.nn.functional as F
from torch import nn
from torch.nn.parallel import DistributedDataParallel
from torch.utils.data import DataLoader, Sampler

from egosurgery.utils import tracking

ROOT = Path(__file__).resolve().parents[1]

# The other ranks wait in a broadcast while rank 0 evaluates val alone.
TIMEOUT = datetime.timedelta(hours=2)
SYNCED = ("layer1", "layer2", "layer3", "layer4")


def requested():
    return int(os.environ.get("WORLD_SIZE", "1")) > 1


def setup():
    local = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local)
    dist.init_process_group("nccl", timeout=TIMEOUT)
    return dist.get_rank(), dist.get_world_size(), torch.device("cuda", local)


def per_rank_batch(batch, world):
    if batch % world:
        raise ValueError(f"ft_batch_size={batch} does not split evenly over {world} GPUs")
    return batch // world


def rank_seed(seed, rank):
    """Seed of one rank's augmentation; a pure function, so a rerun draws the same flips."""
    return int(seed) * 1000 + int(rank)


def shard(batch, rank, world):
    """This rank's part of one global batch; part sizes differ by at most one."""
    return [int(i) for i in np.array_split(np.asarray(batch, dtype=np.int64), world)[rank]]


class ShardedBatches(Sampler):
    """Every rank walks the same shuffled global batches and keeps its own shard.

    The global batches are cut as the one-GPU loader cuts them (the tail is kept), so each
    epoch uses every frame once. The order depends on the seed and the epoch only.
    """

    def __init__(self, size, batch, rank, world, seed):
        tail = size % batch
        if 0 < tail < world:
            raise ValueError(f"the last batch of {tail} frames leaves a rank of {world} empty")
        self.size, self.batch, self.rank, self.world, self.seed = size, batch, rank, world, seed
        self.epoch = 0

    def set_epoch(self, epoch):
        self.epoch = epoch

    def global_batches(self):
        generator = torch.Generator()
        generator.manual_seed(int(self.seed) * 100003 + int(self.epoch))
        order = torch.randperm(self.size, generator=generator).tolist()
        return [order[i:i + self.batch] for i in range(0, self.size, self.batch)]

    def count(self, step):
        """Frames in the global batch of a 1-based step."""
        return min(self.batch, self.size - (step - 1) * self.batch)

    def __iter__(self):
        for batch in self.global_batches():
            yield shard(batch, self.rank, self.world)

    def __len__(self):
        return -(-self.size // self.batch)


def sync_batchnorm(model):
    """layer1-4's BatchNorm becomes SyncBatchNorm; the stem's bn1 is left as it is."""
    for name in SYNCED:
        setattr(model, name, nn.SyncBatchNorm.convert_sync_batchnorm(getattr(model, name)))
    return model


def wrap(model, device, sync_bn=True):
    """``sync_bn=False`` exists only as the equivalence check's breaking control."""
    if sync_bn:
        sync_batchnorm(model)
    return DistributedDataParallel(model, device_ids=[device.index])


def scaled_loss(logits, y, count, world):
    """This rank's summed loss, scaled so DDP's mean over ranks is the mean over ``count``."""
    return F.cross_entropy(logits, y, reduction="sum") * world / count


def micro_step(ddp, images, y, count, world, accum, boundary):
    """One micro-step; gradients cross ranks only on the accumulation boundary.

    Returns this rank's summed loss, for the epoch's mean.
    """
    with nullcontext() if boundary else ddp.no_sync():
        loss = scaled_loss(ddp(images), y, count, world)
        if not torch.isfinite(loss):
            raise RuntimeError("Non-finite loss")
        (loss / accum).backward()
    return loss.detach() * count / world


def determinism_state():
    return {"deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
            "cudnn_tf32": torch.backends.cudnn.allow_tf32,
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}


def gather(value):
    values = [None] * dist.get_world_size()
    dist.all_gather_object(values, value)
    return values


def finetune(cfg):
    rank, world, device = setup()
    main_rank = rank == 0
    per_gpu = per_rank_batch(int(cfg.ft_batch_size), world)
    split = base.folds()[cfg.fold]
    clips = base.manifests(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    train_set = r3.FoldFrames(clips, split["train"], train=True)
    val_set = r3.FoldFrames(clips, split["val"], train=False)
    assert len(train_set) and len(val_set)
    model, source, digest = r3.build_backbone(len(names), device, cfg.init)
    trainable = r3.freeze_report(model)
    assert trainable["stem"] == 0 and all(trainable[k] for k in
                                          ("layer1", "layer2", "layer3", "layer4", "fc"))
    ddp = wrap(model, device)
    torch.manual_seed(rank_seed(cfg.seed, rank))
    determinism = gather(determinism_state())
    print(f"rank={rank} device={device} determinism={determinism[rank]}", flush=True)
    cfg = base.enrich(cfg, {
        "data": {"videos": split, "train_frames": len(train_set), "val_frames": len(val_set)},
        "weights": source, "backbone_init_sha256": digest,
        "transform_train": str(train_set.transform), "transform_eval": str(r3.EVAL_TRANSFORM),
        "short_side": r3.SHORT_SIDE, "crop": "none", "frame_kept_fraction": 1.0,
        "effective_batch_size": int(cfg.ft_batch_size) * int(cfg.ft_accum_steps),
        "world_size": world, "per_gpu_batch_size": per_gpu,
        "sync_batchnorm": "layer1-4 (stem bn1 stays BatchNorm2d in eval)",
        "freeze": "stem (conv1, bn1); layer1-4 and fc trained",
        "selection_metric": "phase_accuracy", "data_setting": cfg.get("data_setting", "P15")})
    manager = base.evidence(cfg, f"ft_{cfg.init}_lr{cfg.ft_lr}_fold{cfg.fold}") if main_rank else None
    sampler = ShardedBatches(len(train_set), int(cfg.ft_batch_size), rank, world, cfg.seed)
    train_loader = DataLoader(train_set, batch_sampler=sampler, num_workers=cfg.workers,
                              pin_memory=cfg.get("pin_memory", True))  # nosemgrep
    val_loader = (DataLoader(val_set, batch_size=cfg.ft_batch_size, shuffle=False,
                             num_workers=cfg.workers, pin_memory=cfg.get("pin_memory", True))  # nosemgrep
                  if main_rank else None)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=cfg.ft_lr, weight_decay=cfg.ft_weight_decay)
    accum = int(cfg.ft_accum_steps)
    best, best_score, history = None, -1.0, []
    stale, lowered, lowered_at, stopped_at = 0, False, None, None
    torch.cuda.reset_peak_memory_stats(device)
    started = time.monotonic()
    for epoch in range(1, cfg.ft_epochs + 1):
        sampler.set_epoch(epoch)
        ddp.train()
        r3.stem_eval(model)
        total = torch.zeros(2, dtype=torch.float64, device=device)
        optimizer.zero_grad(set_to_none=True)
        steps = len(sampler)
        for step, (images, y, _) in enumerate(train_loader, start=1):
            images = images.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            boundary = step % accum == 0 or step == steps
            total[0] += micro_step(ddp, images, y, sampler.count(step), world, accum, boundary)
            total[1] += y.numel()
            if boundary:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
        dist.all_reduce(total)
        train_loss = float(total[0] / total[1])
        decision = [None]
        if main_rank:
            # The unwrapped model: DDP's forward may talk to ranks that are not evaluating.
            preds, labels, ids = r3.frame_predictions(model, val_loader, device)
            val = r3.frame_accuracy(preds, labels, ids, names)
            score = val["phase_accuracy"]
            current_lr = optimizer.param_groups[0]["lr"]
            history.append({"epoch": epoch, "train_loss": train_loss, "lr": current_lr,
                            "val_accuracy": score, "val_macro_f1": val["phase_macro_f1"]})
            tracking.log({"train/loss": train_loss, "val/accuracy": score,
                          "val/macro_f1": val["phase_macro_f1"], "lr": current_lr}, step=epoch)
            print(f"epoch={epoch} lr={current_lr:g} loss={train_loss:.6f} "
                  f"val_accuracy={score:.6f}", flush=True)
            improved = score > best_score
            if improved:
                best_score = score
                best = {**val, "epoch": epoch}
                torch.save({"model": model.state_dict(), "epoch": epoch},
                           manager.exp_dir / "checkpoints/best.pth")
            decision[0], stale, lowered = r3.plateau_action(improved, stale, lowered,
                                                            cfg.ft_patience)
        dist.broadcast_object_list(decision, src=0)
        if decision[0] == "lower":
            for group in optimizer.param_groups:
                group["lr"] *= cfg.ft_lr_decay
            lowered_at = epoch
            print(f"rank={rank} lr lowered at epoch={epoch} to "
                  f"{optimizer.param_groups[0]['lr']:g}", flush=True)
        elif decision[0] == "stop":
            stopped_at = epoch
            print(f"rank={rank} early stop at epoch={epoch}", flush=True)
            break
    peaks = gather({"device": str(device),
                    "peak_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
                    "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device))})
    if main_rank:
        best["elapsed_seconds"] = time.monotonic() - started
        best["epochs_completed"] = epoch
        best["trainable_params"] = trainable
        best["peak_memory_bytes"] = max(p["peak_memory_bytes"] for p in peaks)
        best["peak_reserved_bytes"] = max(p["peak_reserved_bytes"] for p in peaks)
        best["lr_lowered_epoch"] = lowered_at
        best["early_stopped_epoch"] = stopped_at
        best["reached_epoch_cap"] = stopped_at is None and epoch == cfg.ft_epochs
        best["world_size"] = world
        best["per_gpu_batch_size"] = per_gpu
        manager.log_metrics({k: v for k, v in best.items()
                             if isinstance(v, (int, float)) or v is None})
        manager.log_per_class_ap(best["phase_per_class_f1"])
        manager.log_eval_recipe({"test_cfg": {"task": "phase", "backbone": cfg.backbone_tag,
                                              "inference_protocol": "frame", "jaccard_mode": "strict"}})
        base.write_json(manager.exp_dir / "finetune_history.json",
                        {"task_id": cfg.task_id, "fold": cfg.fold, "seed": cfg.seed,
                         "init": cfg.init, "ft_lr": cfg.ft_lr, "trainable_params": trainable,
                         "backbone_init_sha256": digest, "weights": source,
                         "effective_batch_size": int(cfg.ft_batch_size) * accum,
                         "world_size": world, "per_gpu_batch_size": per_gpu,
                         "history": history, "best_epoch": best["epoch"],
                         "best_val_accuracy": best_score,
                         "lr_lowered_epoch": lowered_at, "early_stopped_epoch": stopped_at,
                         "peak_memory_per_rank": peaks, "determinism_per_rank": determinism,
                         "checkpoint_sha256": base.sha256(manager.exp_dir / "checkpoints/best.pth")})
        (manager.exp_dir / "notes.md").write_text(
            f"# Stage 1 r3 fine-tune {cfg.init} fold {cfg.fold} lr {cfg.ft_lr}\n\n"
            f"Short side {r3.SHORT_SIDE}, whole frame (no crop). Stem frozen; val picks the "
            f"epoch; test unread.\n{world} GPUs x {per_gpu} frames, SyncBatchNorm in layer1-4.\n"
            f"Backbone init sha256: {digest}\n"
            f"Best epoch: {best['epoch']}\nVal frame accuracy: {best_score}\n"
            f"Epochs completed: {epoch} (lr lowered at {lowered_at}, stopped at {stopped_at})\n"
            f"Peak memory bytes per rank: {[p['peak_memory_bytes'] for p in peaks]}\n"
            f"Elapsed seconds: {best['elapsed_seconds']}\n")
        tracking.finish()
        print(f"FINETUNE_COMPLETE {manager.exp_dir} acc={best_score}", flush=True)
    dist.destroy_process_group()

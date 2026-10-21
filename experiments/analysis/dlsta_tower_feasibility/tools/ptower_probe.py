"""Task E (T-2026-10-19-dlsta-tower-feasibility): memory and time of the phase tower on one GPU.

Calls the third round's own functions (``scripts/stage1_ptower_r3.py``) and changes none of
them. Nothing is written under the repo: ``base.evidence`` would create an experiment
folder under ``experiments/phase1`` and require W&B, so the actions below either avoid it
(finetune, extract) or replace it for this process only with a stub whose folder lives in
the scratch directory (head).

    python ptower_probe.py finetune --batch 16 --steps 40 --out <json>
    python ptower_probe.py extract  --checkpoint <best.pth> --cache <npz outside repo> --out <json>
    python ptower_probe.py head     --cache <npz> --workdir <dir outside repo> --out <json>

finetune repeats the inner loop of ``stage1_ptower_r3.finetune`` (lines 208-226) for
``--steps`` micro-batches: same dataset class, transform, backbone, frozen stem,
``stem_eval``, AdamW, loss, accumulation. An out-of-memory error is a result, recorded
with the micro-step and the phase (forward / backward / optimizer) where it happened.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf
from torch import nn
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402

GIB = 1024 ** 3


def config(**overrides):
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_r3.yaml")
    cfg.pop("hydra", None)
    cfg.device = "cuda:0"
    for key, value in overrides.items():
        cfg[key] = value
    return cfg


def memory(device):
    return {"max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
            "device_total_bytes": int(torch.cuda.get_device_properties(device).total_memory)}


def finetune(args):
    cfg = config(ft_batch_size=args.batch, ft_accum_steps=args.accum, ft_lr=args.lr)
    base.deterministic(cfg.seed)
    split = base.folds()[cfg.fold]
    clips = base.manifests(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    train_set = r3.FoldFrames(clips, split["train"], train=True)
    model, _, digest = r3.build_backbone(len(names), cfg.device, cfg.init)
    loader = DataLoader(train_set, batch_size=cfg.ft_batch_size, shuffle=True,
                        num_workers=cfg.workers, pin_memory=cfg.get("pin_memory", True))  # nosemgrep
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=cfg.ft_lr, weight_decay=cfg.ft_weight_decay)
    ce = nn.CrossEntropyLoss()
    accum = int(cfg.ft_accum_steps)
    torch.cuda.reset_peak_memory_stats(cfg.device)
    r3.stem_eval(model)
    optimizer.zero_grad(set_to_none=True)
    steps = len(loader)
    times, walls, phase, step, result = [], [], "load", 0, {"oom": False}
    first_shape = None
    t_prev = time.perf_counter()
    try:
        for step, (images, y, _) in enumerate(loader, start=1):
            torch.cuda.synchronize(cfg.device)
            t0 = time.perf_counter()
            images = images.to(cfg.device, non_blocking=True)
            y = y.to(cfg.device, non_blocking=True)
            first_shape = first_shape or list(images.shape)
            phase = "forward"
            loss = ce(model(images), y)
            phase = "backward"
            (loss / accum).backward()
            phase = "optimizer"
            if step % accum == 0 or step == steps:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            torch.cuda.synchronize(cfg.device)
            now = time.perf_counter()
            times.append(now - t0)
            walls.append(now - t_prev)
            t_prev = now
            phase = "load"
            if step >= args.steps:
                break
    except torch.cuda.OutOfMemoryError as exc:
        result.update(oom=True, oom_step=step, oom_phase=phase, oom_message=str(exc).splitlines()[0])
    warm = times[args.warmup:]
    warm_wall = walls[args.warmup:]
    result.update({
        "micro_step_wall_seconds_mean": float(np.mean(warm_wall)) if warm_wall else None,
        "micro_step_wall_seconds_all": [round(t, 4) for t in walls],
        "action": "finetune", "batch": args.batch, "accum": accum, "effective_batch": args.batch * accum,
        "steps_done": len(times), "input_shape": first_shape, "backbone_init_sha256": digest,
        "train_frames": len(train_set), "micro_steps_per_epoch": steps,
        "warmup_excluded": args.warmup,
        "micro_step_seconds_mean": float(np.mean(warm)) if warm else None,
        "micro_step_seconds_median": float(np.median(warm)) if warm else None,
        "micro_step_seconds_all": [round(t, 4) for t in times],
        "alloc_conf": __import__("os").environ.get("PYTORCH_CUDA_ALLOC_CONF"),
        **memory(cfg.device)})
    return result


def extract(args):
    cfg = config(batch_size=args.batch)
    base.deterministic(cfg.seed)
    clips = base.manifests(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    every = r3.FoldFrames(clips, sorted({c["video"] for c in clips}), train=False)
    loader = DataLoader(every, batch_size=cfg.batch_size, shuffle=False,
                        num_workers=cfg.workers, pin_memory=cfg.get("pin_memory", True))  # nosemgrep
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    model, _, _ = r3.build_backbone(len(names), cfg.device, cfg.init)
    model.load_state_dict(state["model"])
    model.fc = nn.Identity()
    model.eval().requires_grad_(False)
    torch.cuda.reset_peak_memory_stats(cfg.device)
    before = time.monotonic()
    features, frame_ids = r3._features(model, loader, cfg.device)
    elapsed = time.monotonic() - before
    out = Path(args.cache)
    assert ROOT not in out.resolve().parents, "cache must live outside the repo"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, frame_ids=np.asarray(frame_ids), features=features)
    report = {"action": "extract", "batch": args.batch, "frames": len(every),
              "feature_shape": list(features.shape), "elapsed_seconds": elapsed,
              "feature_sha256": hashlib.sha256(features.tobytes()).hexdigest(),
              "checkpoint_sha256": base.sha256(args.checkpoint), "best_epoch": int(state["epoch"]),
              "cache_sha256": base.sha256(out), "cache_bytes": out.stat().st_size,
              **memory(cfg.device)}
    # load_fold() checks the cache against this audit file, as the real extract writes it.
    base.write_json(out.with_suffix(".json"), report)
    return report


class _StubManager:
    """Stands in for ExperimentManager in this process only; writes nowhere in the repo."""

    def __init__(self, workdir):
        self.exp_dir = Path(workdir)
        (self.exp_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        self.metrics = None

    def log_metrics(self, metrics):
        self.metrics = metrics

    def log_per_class_ap(self, _):
        pass

    def log_eval_recipe(self, _):
        pass


def head(args):
    workdir = Path(args.workdir)
    assert ROOT not in workdir.resolve().parents, "workdir must live outside the repo"
    cfg = config(action="train", cache=str(Path(args.cache).resolve()))
    base.deterministic(cfg.seed)
    stub = _StubManager(workdir)
    base.evidence = lambda _cfg, _desc: stub
    torch.cuda.init()
    torch.cuda.reset_peak_memory_stats(cfg.device)
    before = time.monotonic()
    base.train(cfg)
    elapsed = time.monotonic() - before
    metrics = stub.metrics or {}
    return {"action": "head", "candidate": cfg.candidate, "layers": cfg.layers,
            "elapsed_seconds_wall": elapsed,
            "elapsed_seconds_train": metrics.get("elapsed_seconds"),
            "epochs_completed": metrics.get("epochs_completed"), **memory(cfg.device)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["finetune", "extract", "head"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--lr", type=float, default=0.0001)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--warmup", type=int, default=8)
    ap.add_argument("--checkpoint")
    ap.add_argument("--cache")
    ap.add_argument("--workdir")
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    result = {"finetune": finetune, "extract": extract, "head": head}[args.action](args)
    result["gpu"] = torch.cuda.get_device_name(0)
    for key in ("max_memory_allocated_bytes", "max_memory_reserved_bytes"):
        if key in result:
            result[key.replace("_bytes", "_gib")] = result[key] / GIB
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if not k.endswith("_all")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""Task D: the several-GPU fine-tune end to end, and the one-GPU read of its checkpoint.

    cd <dir outside the repo>
    torchrun --nproc_per_node=2 --master_port=<p> flow.py finetune [--lr 0] [--patience 1] [--epochs 10] [--seed 42]
    python flow.py extract --checkpoint <best.pth>

Runs the real ``stage1_ptower_r3.main`` (``action=finetune`` or ``extract``; the config file is
read and handed to it). Replaced for this process only:

- finetune: ``FoldFrames`` keeps a fixed subset (38 train, 8 val frames) and its flip records
  each draw (same ``torch.rand(1)`` as ``RandomHorizontalFlip``) to ``flips/rank<r>_<pid>.tsv``.
- extract: every clip keeps its first frame (22 frames), since extract checks its output
  against every clip of the manifest.
- ``ExperimentManager`` is the real class with its root moved to ``./experiments`` here, so
  evidence goes through ``base.evidence`` unchanged but nothing lands in the repo.
- ``base.evidence``, ``torch.save`` and ``tracking.init/log/finish`` are wrapped to append each
  call, with the rank, to ``calls/rank<r>.jsonl``.

W&B runs offline (``WANDB_MODE=offline``, ``WANDB_DIR`` here): nothing is sent.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch
import torchvision.transforms.functional as TF
from omegaconf import OmegaConf
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402

from egosurgery.utils import tracking  # noqa: E402

N_TRAIN, N_VAL = 38, 8
HERE = Path.cwd()
RANK = int(os.environ.get("RANK", "0"))


class RecordingFlip(transforms.RandomHorizontalFlip):
    def forward(self, img):
        self.last = bool(torch.rand(1) < self.p)
        return TF.hflip(img) if self.last else img


class Subset(r3.FoldFrames):
    def __init__(self, clips, videos, train):
        super().__init__(clips, videos, train)
        n = N_TRAIN if train else N_VAL
        self.frames = self.frames[::len(self.frames) // n][:n]
        self.flip = RecordingFlip() if train else None
        if train:
            self.transform = transforms.Compose([self.flip, r3.EVAL_TRANSFORM])

    def __getitem__(self, index):
        item = super().__getitem__(index)
        if self.flip is not None:
            out = HERE / "flips" / f"rank{RANK}_{os.getpid()}.tsv"
            with out.open("a") as handle:
                handle.write(f"{item[2]}\t{int(self.flip.last)}\n")
        return item


def record(name, fn):
    def wrapped(*args, **kwargs):
        with (HERE / "calls" / f"rank{RANK}.jsonl").open("a") as handle:
            handle.write(json.dumps({"rank": RANK, "call": name}) + "\n")
        return fn(*args, **kwargs)
    return wrapped


def first_frame_of_each_clip(manifests):
    def trimmed(cfg):
        return [{**c, "frames": c["frames"][:1]} for c in manifests(cfg)]
    return trimmed


def patch(action):
    assert ROOT not in HERE.resolve().parents and HERE != ROOT, "run outside the repo"
    for sub in ("flips", "calls"):
        (HERE / sub).mkdir(exist_ok=True)
    if action == "finetune":
        r3.FoldFrames = Subset
    else:
        # extract checks its output against every clip, so trim the clips instead.
        base.manifests = first_frame_of_each_clip(base.manifests)
    real = base.ExperimentManager
    base.ExperimentManager = lambda _root, *a, **k: real(HERE / "experiments", *a, **k)
    base.evidence = record("base.evidence", base.evidence)
    torch.save = record("torch.save", torch.save)
    for name in ("init", "log", "finish"):
        setattr(tracking, name, record(f"tracking.{name}", getattr(tracking, name)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["finetune", "extract"])
    ap.add_argument("--lr", default="0.0003")
    ap.add_argument("--patience", default="4")
    ap.add_argument("--epochs", default="1")
    ap.add_argument("--seed", default="42")
    ap.add_argument("--checkpoint")
    args = ap.parse_args()
    patch(args.action)
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_r3.yaml")
    cfg.pop("hydra")
    cfg.merge_with_dotlist([
        f"action={args.action}", "task_id=T-2026-10-21-ptower-multigpu-syncbn",
        "ft_batch_size=4", "ft_accum_steps=4", f"ft_epochs={args.epochs}", "workers=2",
        f"ft_lr={args.lr}", f"ft_patience={args.patience}", f"seed={args.seed}",
        "device=cuda:0", "batch_size=4", "verify_determinism=true",
        f"cache={HERE / 'features' / 'all_gap.npz'}",
        f"checkpoint={args.checkpoint}" if args.checkpoint else "checkpoint=null"])
    r3.main(cfg)


if __name__ == "__main__":
    main()

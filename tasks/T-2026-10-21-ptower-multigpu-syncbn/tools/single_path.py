"""Task A.7 / B.3: summary of the one-GPU path's weights, before and after the change.

    cd <dir outside the repo> && python single_path.py --out <json> [--lr 0.0003]

Runs the real ``stage1_ptower_r3.main`` (``action=finetune``; the config file is read and
handed to it, which Hydra passes straight through) in this process, so it goes through
whatever dispatch ``main`` has. Only three things are replaced, for this
process only:

- ``FoldFrames`` keeps a fixed, evenly spaced subset of each split (38 train, 8 val
  frames), so one epoch is 10 micro-steps of 4 frames with a 2-frame tail and a
  2-step accumulation tail.
- ``base.evidence`` returns a stub whose folder lives in the current directory (outside
  the repo); nothing is written under ``experiments/`` and W&B is not called.

One epoch, so ``checkpoints/best.pth`` holds the final weights. The summary covers every
entry of the saved state dict, running statistics included.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch
from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402

N_TRAIN, N_VAL = 38, 8


class Subset(r3.FoldFrames):
    def __init__(self, clips, videos, train):
        super().__init__(clips, videos, train)
        n = N_TRAIN if train else N_VAL
        stride = len(self.frames) // n
        self.frames = self.frames[::stride][:n]


class Stub:
    def __init__(self, workdir):
        self.exp_dir = Path(workdir)
        (self.exp_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

    def log_metrics(self, metrics):
        (self.exp_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    def log_per_class_ap(self, _):
        pass

    def log_eval_recipe(self, _):
        pass


def state_digest(state):
    digest = hashlib.sha256()
    for name, tensor in sorted(state.items()):
        digest.update(name.encode())
        digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return digest.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--lr", default="0.0003")
    args = ap.parse_args()
    workdir = Path.cwd() / "stub"
    assert ROOT not in workdir.resolve().parents, "run outside the repo"
    r3.FoldFrames = Subset
    base.evidence = lambda _cfg, _desc: Stub(workdir)
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_r3.yaml")
    cfg.pop("hydra")
    cfg.merge_with_dotlist(["action=finetune", "ft_batch_size=4", "ft_accum_steps=4",
                            "ft_epochs=1", "workers=2", f"ft_lr={args.lr}", "device=cuda:0"])
    # hydra.main calls the task function directly when handed a config.
    r3.main(cfg)
    state = torch.load(workdir / "checkpoints/best.pth", map_location="cpu", weights_only=True)
    history = json.loads((workdir / "finetune_history.json").read_text())
    result = {"state_sha256": state_digest(state["model"]), "keys": len(state["model"]),
              "train_loss": history["history"][0]["train_loss"], "lr": args.lr,
              "train_frames": N_TRAIN, "val_frames": N_VAL,
              "checkpoint_file_sha256": history["checkpoint_sha256"]}
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()

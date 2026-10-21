"""Task F (T-2026-10-19-dlsta-tower-feasibility): evaluate a third-round phase tower on a fold's val.

Uses the third round's own functions unchanged: ``FoldFrames`` (val, eval transform),
``build_backbone``, ``frame_predictions`` and ``frame_accuracy`` -- the evaluation that
``stage1_ptower_r3.finetune`` ran at its best epoch and wrote to ``metrics.json``.
No experiment folder and no W&B run are created.

    python ptower_eval.py --run <experiments/phase1/... run dir> --fold A --out <json>
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402

KEYS = ("phase_accuracy", "phase_macro_f1", "phase_jaccard", "phase_edit_score",
        "phase_seg_f1_10", "phase_seg_f1_25", "phase_seg_f1_50")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--fold", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    run = ROOT / args.run
    recorded_cfg = OmegaConf.load(run / "config.yaml")
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_r3.yaml")
    cfg.pop("hydra", None)
    cfg.device = "cuda:0"
    cfg.seed = int(recorded_cfg.seed)
    base.deterministic(cfg.seed)
    split = base.folds()[args.fold]
    clips = base.manifests(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    val_set = r3.FoldFrames(clips, split["val"], train=False)
    loader = DataLoader(val_set, batch_size=int(recorded_cfg.ft_batch_size), shuffle=False,
                        num_workers=cfg.workers, pin_memory=True)  # nosemgrep
    model, _, _ = r3.build_backbone(len(names), cfg.device, str(recorded_cfg.init))
    state = torch.load(run / "checkpoints/best.pth", map_location="cpu", weights_only=True)
    model.load_state_dict(state["model"])
    preds, labels, ids = r3.frame_predictions(model, loader, cfg.device)
    val = r3.frame_accuracy(preds, labels, ids, names)
    recorded = json.loads((run / "metrics.json").read_text())
    rows = {k: {"dlsta": val[k], "recorded": recorded.get(k),
                "diff": (val[k] - recorded[k]) if k in recorded else None,
                "exact": val[k] == recorded.get(k)} for k in KEYS}
    out = {"run": args.run, "eval_fold": args.fold, "train_fold": str(recorded_cfg.fold),
           "checkpoint_sha256": base.sha256(run / "checkpoints/best.pth"),
           "best_epoch": int(state["epoch"]), "recorded_epoch": recorded.get("epoch"),
           "val_frames": len(val_set), "batch_size": int(recorded_cfg.ft_batch_size),
           "recorded_server": (run / "server.txt").read_text().strip(), "metrics": rows}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

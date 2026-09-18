"""Stage 1 second round: fine-tune the backbone per fold, then extract its features.

The first round froze ImageNet-1K R50. Here the backbone is trained on the fold's
own phase labels with the stem frozen, matching the detector tower's
``freeze_indices=(0,)``. Only the fold's train videos are used; val picks the best
epoch and test is never read. Feature extraction reuses the first round's
preprocessing so the only difference against it is the backbone's weights.

Temporal-head training reuses ``stage1_ptower.train`` unchanged through the cache.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import hydra
import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import ResNet50_Weights, resnet50

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.utils import tracking  # noqa: E402

# The first round's preprocessing, so a feature difference means a weight difference.
EVAL_TRANSFORM = ResNet50_Weights.IMAGENET1K_V1.transforms()


class FoldFrames(Dataset):
    """Frames of the given videos, in manifest order. Train adds the flip only."""

    def __init__(self, clips, videos, train):
        self.frames = [f for c in clips if c["video"] in set(videos) for f in c["frames"]]
        self.transform = (transforms.Compose([transforms.RandomHorizontalFlip(), EVAL_TRANSFORM])
                          if train else EVAL_TRANSFORM)

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, index):
        f = self.frames[index]
        with Image.open(ROOT / f["image_path"]) as im:
            return self.transform(im.convert("RGB")), int(f["label"]), f["frame"]


def build_backbone(classes, device):
    """ImageNet-1K R50 with a phase head; the stem is frozen like the detector tower."""
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, classes)
    for module in (model.conv1, model.bn1):
        module.requires_grad_(False)
    return model.to(device)


def freeze_report(model):
    """Count trainable parameters per group; the stem must be zero."""
    groups = {"stem": [model.conv1, model.bn1], "layer1": [model.layer1],
              "layer2": [model.layer2], "layer3": [model.layer3],
              "layer4": [model.layer4], "fc": [model.fc]}
    return {name: sum(p.numel() for m in mods for p in m.parameters() if p.requires_grad)
            for name, mods in groups.items()}


def stem_eval(model):
    """Keep the frozen stem's batch statistics fixed while the rest trains."""
    model.train()
    model.conv1.eval()
    model.bn1.eval()


@torch.no_grad()
def frame_predictions(model, loader, device):
    model.eval()
    preds, labels, ids = [], [], []
    for images, y, fid in loader:
        logits = model(images.to(device, non_blocking=True))
        preds.append(logits.argmax(1).cpu().numpy())
        labels.append(y.numpy())
        ids.extend(fid)
    return np.concatenate(preds), np.concatenate(labels), ids


def frame_accuracy(preds, labels, ids, names):
    """Same evaluator as the temporal heads, grouped per video."""
    evaluator = PhaseEvaluator(num_classes=len(names), class_names=names)
    order = {}
    for i, fid in enumerate(ids):
        order.setdefault(fid.split("_")[0], []).append(i)
    for video, index in order.items():
        evaluator.update(preds[index], labels[index], video_id=video)
    return evaluator.compute()


def finetune(cfg):
    split = base.folds()[cfg.fold]
    clips = base.manifests(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    train_set = FoldFrames(clips, split["train"], train=True)
    val_set = FoldFrames(clips, split["val"], train=False)
    assert len(train_set) and len(val_set)
    cfg = base.enrich(cfg, {
        "data": {"videos": split, "train_frames": len(train_set), "val_frames": len(val_set)},
        "weights": str(ResNet50_Weights.IMAGENET1K_V1),
        "transform_train": str(train_set.transform), "transform_eval": str(EVAL_TRANSFORM),
        "freeze": "stem (conv1, bn1); layer1-4 and fc trained",
        "selection_metric": "phase_accuracy", "data_setting": "P15"})
    manager = base.evidence(cfg, f"ft_lr{cfg.ft_lr}_fold{cfg.fold}")
    model = build_backbone(len(names), cfg.device)
    trainable = freeze_report(model)
    assert trainable["stem"] == 0 and all(trainable[k] for k in
                                          ("layer1", "layer2", "layer3", "layer4", "fc"))
    loaders = {
        "train": DataLoader(train_set, batch_size=cfg.ft_batch_size, shuffle=True,
                            num_workers=cfg.workers, pin_memory=True),  # nosemgrep
        "val": DataLoader(val_set, batch_size=cfg.ft_batch_size, shuffle=False,
                          num_workers=cfg.workers, pin_memory=True),  # nosemgrep
    }
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=cfg.ft_lr, weight_decay=cfg.ft_weight_decay)
    ce = nn.CrossEntropyLoss()
    best, best_score, history = None, -1.0, []
    started = time.monotonic()
    for epoch in range(1, cfg.ft_epochs + 1):
        stem_eval(model)
        total, seen = 0.0, 0
        for images, y, _ in loaders["train"]:
            images = images.to(cfg.device, non_blocking=True)
            y = y.to(cfg.device, non_blocking=True)
            loss = ce(model(images), y)
            if not torch.isfinite(loss):
                raise RuntimeError(f"Non-finite loss at epoch {epoch}")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += float(loss) * y.numel()
            seen += y.numel()
        preds, labels, ids = frame_predictions(model, loaders["val"], cfg.device)
        val = frame_accuracy(preds, labels, ids, names)
        score = val["phase_accuracy"]
        history.append({"epoch": epoch, "train_loss": total / seen,
                        "val_accuracy": score, "val_macro_f1": val["phase_macro_f1"]})
        tracking.log({"train/loss": total / seen, "val/accuracy": score,
                      "val/macro_f1": val["phase_macro_f1"]}, step=epoch)
        print(f"epoch={epoch} loss={total/seen:.6f} val_accuracy={score:.6f}", flush=True)
        if score > best_score:
            best_score = score
            best = {**val, "epoch": epoch}
            torch.save({"model": model.state_dict(), "epoch": epoch},
                       manager.exp_dir / "checkpoints/best.pth")
    best["elapsed_seconds"] = time.monotonic() - started
    best["epochs_completed"] = epoch
    best["trainable_params"] = trainable
    manager.log_metrics({k: v for k, v in best.items() if isinstance(v, (int, float))})
    manager.log_per_class_ap(best["phase_per_class_f1"])
    manager.log_eval_recipe({"test_cfg": {"task": "phase", "backbone": cfg.backbone_tag,
                                          "inference_protocol": "frame", "jaccard_mode": "strict"}})
    base.write_json(manager.exp_dir / "finetune_history.json",
                    {"task_id": cfg.task_id, "fold": cfg.fold, "seed": cfg.seed,
                     "ft_lr": cfg.ft_lr, "trainable_params": trainable, "history": history,
                     "best_epoch": best["epoch"], "best_val_accuracy": best_score,
                     "checkpoint_sha256": base.sha256(manager.exp_dir / "checkpoints/best.pth")})
    (manager.exp_dir / "notes.md").write_text(
        f"# Stage 1 r2 fine-tune fold {cfg.fold} lr {cfg.ft_lr}\n\n"
        f"Stem frozen; val picks the epoch; test unread.\nBest epoch: {best['epoch']}\n"
        f"Val frame accuracy: {best_score}\nElapsed seconds: {best['elapsed_seconds']}\n")
    tracking.finish()
    print(f"FINETUNE_COMPLETE {manager.exp_dir} acc={best_score}", flush=True)


@torch.no_grad()
def _features(model, loader, device):
    arrays, frame_ids = [], []
    for images, _, ids in loader:
        arrays.append(model(images.to(device, non_blocking=True)).cpu().numpy())
        frame_ids.extend(ids)
    return np.concatenate(arrays), frame_ids


def extract(cfg):
    """Write the fold's features from its own fine-tuned backbone."""
    out = ROOT / cfg.cache
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite features: {out}")
    clips = base.manifests(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    every = FoldFrames(clips, sorted({c["video"] for c in clips}), train=False)
    loader = DataLoader(every, batch_size=cfg.batch_size, shuffle=False,
                        num_workers=cfg.workers, pin_memory=True)  # nosemgrep
    checkpoint = ROOT / cfg.checkpoint
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model = build_backbone(len(names), cfg.device)
    model.load_state_dict(state["model"])
    model.fc = nn.Identity()
    model.eval().requires_grad_(False)
    cfg = base.enrich(cfg, {"weights": str(ResNet50_Weights.IMAGENET1K_V1),
                            "transform": str(EVAL_TRANSFORM), "feature_dim": 2048,
                            "data_setting": "P15", "best_epoch": int(state["epoch"]),
                            "checkpoint_sha256": base.sha256(checkpoint)})
    manager = base.evidence(cfg, f"features_lr{cfg.ft_lr}_fold{cfg.fold}")
    before = time.monotonic()
    features, frame_ids = _features(model, loader, cfg.device)
    first_hash = hashlib.sha256(features.tobytes()).hexdigest()
    report = {"task_id": cfg.task_id, "fold": cfg.fold, "seed": cfg.seed, "ft_lr": cfg.ft_lr,
              "feature_sha256": first_hash, "checkpoint_sha256": cfg.checkpoint_sha256,
              "best_epoch": int(state["epoch"])}
    if cfg.verify_determinism:
        second, second_ids = _features(model, loader, cfg.device)
        assert second_ids == frame_ids
        report["second_feature_sha256"] = hashlib.sha256(second.tobytes()).hexdigest()
        # Breaking control: a changed weight must change the summary.
        saved = model.conv1.weight.clone()
        model.conv1.weight.zero_()
        changed, _ = _features(model, loader, cfg.device)
        model.conv1.weight.copy_(saved)
        report["weight_change_detected"] = not np.array_equal(changed, features)
        assert report["second_feature_sha256"] == first_hash
        assert report["weight_change_detected"]
    expected = Counter(c["video"] for c in clips for _ in c["frames"])
    actual = Counter(fid.split("_")[0] for fid in frame_ids)
    assert actual == expected and features.shape == (len(every), 2048)
    assert np.isfinite(features).all()
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, frame_ids=np.asarray(frame_ids), features=features)
    report.update(cache_sha256=base.sha256(out), cache_bytes=out.stat().st_size,
                  video_counts=dict(actual), elapsed_seconds=time.monotonic() - before)
    base.write_json(out.with_suffix(".json"), report)
    base.write_json(manager.exp_dir / "feature_audit.json", report)
    manager.log_metrics({"frames": len(every), "elapsed_seconds": report["elapsed_seconds"]})
    (manager.exp_dir / "notes.md").write_text(
        f"# Stage 1 r2 features fold {cfg.fold} lr {cfg.ft_lr}\n\n"
        f"Fine-tuned backbone, first round's preprocessing.\n"
        f"Best epoch: {state['epoch']}\nBytes: {report['cache_bytes']}\n")
    tracking.log({"frames": len(every), "cache_bytes": report["cache_bytes"]})
    tracking.finish()
    print(f"EXTRACT_COMPLETE {out} sha={first_hash}", flush=True)


@hydra.main(version_base=None, config_path="../configs", config_name="stage1_ptower_r2")
def main(cfg):
    base.deterministic(cfg.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required by task")
    if cfg.action == "finetune":
        finetune(cfg)
    elif cfg.action == "extract":
        extract(cfg)
    elif cfg.action == "train":
        base.train(cfg)
    else:
        raise ValueError(cfg.action)


if __name__ == "__main__":
    main()

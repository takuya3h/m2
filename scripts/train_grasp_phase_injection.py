#!/usr/bin/env python
"""Train causal phase recognition with an internal grasp-inference signal.

The control and injected arms share the same model, optimizer, auxiliary loss,
and population.  Only the signal concatenated to the phase input differs:
zeros for ``ctrl`` and detached grasp predictions for ``inj``.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from omegaconf import OmegaConf
from torch import nn

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.datasets.grasp_targets import (  # noqa: E402
    GRASP_LABEL_NAMES,
    load_grasp_target_index,
)
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.models.build import build_grasp_phase_injection  # noqa: E402
from egosurgery.models.temporal.grasp_inference_injection import (  # noqa: E402
    grasp_accuracy_per_class,
    masked_grasp_bce,
)
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.grasp_phase_recipe import build_grasp_phase_recipe  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJ / path


def load_clips(split: str, cfg) -> list[tuple]:
    """Load frozen features, phase labels, grasp targets, and validity flags."""
    cache_dir = _path(str(cfg.data.feature_cache))
    manifest_dir = _path(str(cfg.data.phase_manifest))
    target_root = _path(str(cfg.grasp_inference.annotation_root))

    with np.load(cache_dir / f"{split}_gap.npz") as data:
        features_all = data["features"]
        frame_ids = data["frame_ids"]
    features_by_frame = {
        str(frame_id): features_all[index] for index, frame_id in enumerate(frame_ids)
    }
    manifest = json.loads((manifest_dir / f"{split}.json").read_text(encoding="utf-8"))
    grasp_index = load_grasp_target_index(split, target_root)

    manifest_frames = [
        str(frame["frame"]) for clip in manifest["clips"] for frame in clip["frames"]
    ]
    expected = int(cfg.data.population[split])
    if len(manifest_frames) != expected:
        raise ValueError(
            f"{split} phase population changed: {len(manifest_frames)} != {expected}"
        )
    target_population = set(grasp_index.labels) | set(grasp_index.masked_frames)
    missing_targets = set(manifest_frames) - target_population
    extra_targets = target_population - set(manifest_frames)
    if missing_targets or extra_targets:
        raise ValueError(
            f"{split} grasp population mismatch: missing={len(missing_targets)} "
            f"extra={len(extra_targets)}"
        )

    clips = []
    for clip in manifest["clips"]:
        frames = clip["frames"]
        stems = [str(frame["frame"]) for frame in frames]
        missing_features = [stem for stem in stems if stem not in features_by_frame]
        if missing_features:
            raise KeyError(f"frozen feature missing: {missing_features[:3]}")
        targets_and_flags = [grasp_index.target_for(stem) for stem in stems]
        clips.append(
            (
                str(clip["clip_id"]),
                np.stack([features_by_frame[stem] for stem in stems]).astype(
                    np.float32
                ),
                np.asarray([frame["label"] for frame in frames], dtype=np.int64),
                np.stack([target for target, _ in targets_and_flags]).astype(
                    np.float32
                ),
                np.asarray([valid for _, valid in targets_and_flags], dtype=np.bool_),
            )
        )
    return clips


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    """TeCNO temporal smoothing loss with causal model outputs."""
    if logits.shape[-1] < 2:
        return logits.sum() * 0.0
    log_probs = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(log_probs[:, :, 1:], log_probs[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


def build_component_cfg(cfg) -> dict:
    """Resolve the model-only config while keeping arm settings explicit."""
    return {
        "enabled": bool(cfg.grasp_inference.enabled),
        "arm": str(cfg.grasp_inference.arm),
        "input_dim": int(cfg.model.input_dim),
        "hidden_dim": int(cfg.grasp_inference.hidden_dim),
        "num_grasp_classes": int(cfg.grasp_inference.num_classes),
        "num_phases": int(cfg.model.num_phases),
        "temporal": OmegaConf.to_container(cfg.model.temporal, resolve=True),
    }


def _batch(clip: tuple, device: torch.device) -> tuple:
    _, features, phase_labels, grasp_targets, grasp_valid = clip
    x = torch.from_numpy(features).T.unsqueeze(0).to(device)
    phase_y = torch.from_numpy(phase_labels).to(device)
    grasp_y = torch.from_numpy(grasp_targets).T.unsqueeze(0).to(device)
    grasp_mask = torch.from_numpy(grasp_valid).unsqueeze(0).to(device)
    return x, phase_y, grasp_y, grasp_mask


def _phase_loss(
    outputs: list[torch.Tensor], labels: torch.Tensor, weight: float
) -> torch.Tensor:
    ce = nn.CrossEntropyLoss()
    return sum(
        ce(output[0].T, labels) + weight * smoothing_loss(output) for output in outputs
    )


@torch.no_grad()
def evaluate(model: nn.Module, clips: list[tuple], device: torch.device) -> dict:
    """Evaluate phase metrics and all five grasp-dimension accuracies."""
    model.train(False)
    phase_metrics = PhaseEvaluator(num_classes=9)
    grasp_correct = np.zeros(len(GRASP_LABEL_NAMES), dtype=np.float64)
    grasp_count = 0
    for clip in clips:
        clip_id = clip[0]
        x, phase_y, grasp_y, grasp_mask = _batch(clip, device)
        outputs = model(x)
        phase_logits = outputs["phase_logits"][-1]
        predictions = phase_logits[0].argmax(dim=0).cpu().numpy()
        phase_metrics.update(predictions, phase_y.cpu().numpy(), video_id=clip_id)

        valid_count = int(grasp_mask.sum().item())
        accuracies = grasp_accuracy_per_class(
            outputs["grasp_logits"], grasp_y, grasp_mask
        )
        if valid_count:
            grasp_correct += np.asarray(accuracies) * valid_count
            grasp_count += valid_count

    result = phase_metrics.compute()
    for index, name in enumerate(GRASP_LABEL_NAMES):
        result[f"grasp_accuracy_{name}"] = (
            float(grasp_correct[index] / grasp_count) if grasp_count else float("nan")
        )
    return result


def train(cfg, output_dir: Path | None = None, smoke: bool = False) -> dict:
    """Train one control or injected arm and return measured run facts."""
    seed = int(cfg.seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device_name = str(cfg.get("device", "auto"))
    device = torch.device(
        "cuda"
        if device_name == "auto" and torch.cuda.is_available()
        else "cpu"
        if device_name == "auto"
        else device_name
    )

    train_clips = load_clips("train", cfg)
    val_clips = load_clips("val", cfg)
    if smoke:
        train_clips = train_clips[: int(cfg.get("smoke_train_clips", 1))]
        val_clips = val_clips[: int(cfg.get("smoke_val_clips", 1))]

    model = build_grasp_phase_injection(build_component_cfg(cfg)).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg.train.lr),
        weight_decay=float(cfg.train.weight_decay),
    )
    epochs = int(cfg.train.epochs)
    if smoke and epochs > 2:
        raise ValueError(f"smoke epochs must be <= 2, got {epochs}")

    server_name = resolve_server_name(None)
    manager = None
    run_dir = output_dir
    if smoke:
        if run_dir is None:
            raise ValueError("smoke requires an explicit output directory")
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"),
            category=str(cfg.experiment.category),
            step=str(cfg.experiment.step),
            description=str(cfg.experiment.description),
            seed=seed,
        )
        manager.setup(OmegaConf.to_container(cfg, resolve=True))
        run_dir = manager.exp_dir

    from egosurgery.utils import tracking

    arm = str(cfg.grasp_inference.arm)
    tracking.init(
        f"{cfg.experiment.description}_seed{seed}",
        group="S4-grasp-injection",
        job_type=arm,
        config=OmegaConf.to_container(cfg, resolve=True),
    )
    started = time.perf_counter()
    best = {"phase_accuracy": -1.0}
    last_train = {}
    try:
        for epoch in range(epochs):
            model.train()
            random.shuffle(train_clips)
            phase_total = 0.0
            grasp_total = 0.0
            for clip in train_clips:
                x, phase_y, grasp_y, grasp_mask = _batch(clip, device)
                outputs = model(x)
                phase_loss = _phase_loss(
                    outputs["phase_logits"],
                    phase_y,
                    float(cfg.train.smoothing_weight),
                )
                grasp_loss = masked_grasp_bce(
                    outputs["grasp_logits"], grasp_y, grasp_mask
                )
                loss = phase_loss + float(cfg.train.grasp_loss_weight) * grasp_loss
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()
                phase_total += float(phase_loss.detach())
                grasp_total += float(grasp_loss.detach())

            denom = max(len(train_clips), 1)
            last_train = {
                "train/phase_loss": phase_total / denom,
                "train/grasp_loss": grasp_total / denom,
            }
            val = evaluate(model, val_clips, device)
            record = {**last_train, **val, "epoch": epoch + 1}
            tracking.log(record, step=epoch)
            print(
                f"[grasp-phase][{arm}][{epoch + 1}/{epochs}] "
                f"phase_loss={last_train['train/phase_loss']:.6f} "
                f"grasp_loss={last_train['train/grasp_loss']:.6f} "
                f"val_acc={val['phase_accuracy']:.6f}",
                flush=True,
            )
            if val["phase_accuracy"] > best["phase_accuracy"]:
                best = record
                if not smoke and run_dir is not None:
                    torch.save(
                        {"model": model.state_dict(), "epoch": epoch + 1},
                        run_dir / "checkpoints" / "best_grasp_phase.pth",
                    )
    finally:
        tracking.finish()

    elapsed = time.perf_counter() - started
    result = {
        "task_id": str(cfg.task_id),
        "arm": arm,
        "completed": len(best) > 1,
        "epochs": epochs,
        "device": str(device),
        "train_clips": len(train_clips),
        "val_clips": len(val_clips),
        "elapsed_seconds": elapsed,
        **last_train,
        **{
            key: value for key, value in best.items() if isinstance(value, (int, float))
        },
    }
    assert run_dir is not None
    if smoke:
        (run_dir / "smoke_metrics.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    else:
        assert manager is not None
        manager.log_eval_recipe(build_grasp_phase_recipe(cfg, server_name))
        manager.log_metrics(result)
        manager.log_per_class_ap(
            {name: best.get(f"grasp_accuracy_{name}") for name in GRASP_LABEL_NAMES}
        )
        manager.finalize(metric=("phase_accuracy", float(best["phase_accuracy"])))
        from egosurgery.utils.notion_logger import log_experiment_to_notion

        log_experiment_to_notion(
            run_dir,
            status="completed",
            step="S4-grasp-injection",
            tier="must",
            primary_metric="phase + five grasp-presence accuracies",
            extra_result_text=f"grasp inference arm={arm}",
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--max-train-clips", type=int, default=1)
    parser.add_argument("--max-val-clips", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = OmegaConf.load(_path(args.config))
    if args.epochs is not None:
        cfg.train.epochs = args.epochs
    if args.seed is not None:
        cfg.seed = args.seed
    cfg.device = args.device
    cfg.smoke_train_clips = args.max_train_clips
    cfg.smoke_val_clips = args.max_val_clips
    output_dir = _path(args.output_dir) if args.output_dir else None
    result = train(cfg, output_dir=output_dir, smoke=args.smoke)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Train grasp-phase injection arms whose signal shape is selectable.

Thin variant driver over ``train_grasp_phase_injection``.  That script's
``build_component_cfg`` passes a fixed key set to the model, so the ``signal``
selector never reaches it; this driver forwards the signal keys, feeds grasp
targets to the forward pass (required by ``oracle_upper_bound_only``), and adds
the two-stage schedule.  The original script and its configs behave exactly as
before -- new behaviour exists only through this entry point.

Two-stage schedule (``grasp_inference.staged: true``): the grasp head is
trained alone first (grasp BCE only), then frozen; the phase head trains
afterwards against a signal that no longer moves.  After freezing, the grasp
loss is not computed at all.  The parameter *count* of the model is identical
to the joint schedule -- only the order of training differs.

``oracle_upper_bound_only`` feeds ground-truth targets into the phase input.
UPPER-BOUND MEASUREMENT ONLY -- MUST NEVER BE REPORTED AS A RESULT.
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
from omegaconf import OmegaConf

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))
sys.path.insert(0, str(PROJ / "scripts"))

from train_grasp_phase_injection import (  # noqa: E402
    _batch,
    _path,
    _phase_loss,
    build_component_cfg,
    load_clips,
)

from egosurgery.datasets.grasp_targets import GRASP_LABEL_NAMES  # noqa: E402
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.models.build import build_grasp_phase_injection  # noqa: E402
from egosurgery.models.temporal.grasp_inference_injection import (  # noqa: E402
    grasp_accuracy_per_class,
    masked_grasp_bce,
)
from egosurgery.utils.determinism import enable_determinism  # noqa: E402
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.grasp_phase_recipe import build_grasp_phase_recipe  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

# Signal keys forwarded to the model on top of build_component_cfg's set.
# The signal name deliberately never enters the eval recipe: arms must stay
# comparable under recipes_match, exactly like arm ctrl/inj already does.
SIGNAL_CFG_KEYS = (
    "signal",
    "signal_center",
    "signal_scale",
    "oracle_upper_bound_acknowledged",
    "oracle_missing_fill",
)


def build_component_cfg_variants(cfg) -> dict:
    """Original component cfg plus the signal-shape keys, verbatim."""
    component = build_component_cfg(cfg)
    grasp_cfg = OmegaConf.to_container(cfg.grasp_inference, resolve=True)
    for key in SIGNAL_CFG_KEYS:
        if key in grasp_cfg:
            component[key] = grasp_cfg[key]
    return component


def evaluate(model, clips, device) -> dict:
    """Mirror of the original evaluate, passing targets to the forward.

    The original calls ``model(x)`` without targets, which the oracle signal
    rejects by design.  Same metrics, same reduction.
    """
    model.train(False)
    phase_metrics = PhaseEvaluator(num_classes=9)
    grasp_correct = np.zeros(len(GRASP_LABEL_NAMES), dtype=np.float64)
    grasp_count = 0
    with torch.no_grad():
        for clip in clips:
            clip_id = clip[0]
            x, phase_y, grasp_y, grasp_mask = _batch(clip, device)
            outputs = model(x, grasp_targets=grasp_y, grasp_valid=grasp_mask)
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


def _stage_epochs(model, clips, optimizer, cfg, device, *, epochs, grasp_on, phase_on):
    """Run one schedule stage; returns the last epoch's mean losses."""
    last = {"train/phase_loss": float("nan"), "train/grasp_loss": float("nan")}
    for _ in range(epochs):
        model.train()
        random.shuffle(clips)
        phase_total, grasp_total = 0.0, 0.0
        for clip in clips:
            x, phase_y, grasp_y, grasp_mask = _batch(clip, device)
            outputs = model(x, grasp_targets=grasp_y, grasp_valid=grasp_mask)
            loss = x.new_zeros(())
            if phase_on:
                phase_loss = _phase_loss(
                    outputs["phase_logits"], phase_y, float(cfg.train.smoothing_weight)
                )
                loss = loss + phase_loss
                phase_total += float(phase_loss.detach())
            if grasp_on:
                grasp_loss = masked_grasp_bce(
                    outputs["grasp_logits"], grasp_y, grasp_mask
                )
                loss = loss + float(cfg.train.grasp_loss_weight) * grasp_loss
                grasp_total += float(grasp_loss.detach())
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
        denom = max(len(clips), 1)
        last = {
            "train/phase_loss": phase_total / denom if phase_on else float("nan"),
            "train/grasp_loss": grasp_total / denom if grasp_on else float("nan"),
        }
    return last


def train(
    cfg,
    output_dir: Path | None = None,
    smoke: bool = False,
    audit: bool = False,
) -> dict:
    """Train one arm with a selectable signal shape; returns measured facts.

    ``audit=True`` is measurement plumbing for the determinism contract: like
    smoke it writes to an explicit directory and never touches
    ``experiments/`` or the index, but it runs the full epoch count and full
    data. Training behaviour is identical to the normal path.
    """
    seed = int(cfg.seed)
    determinism_record = None
    if bool(cfg.train.get("deterministic", False)):
        # Opt-in only (禁止 13): the default path stays byte-identical.
        determinism_record = enable_determinism(seed)
    else:
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

    model = build_grasp_phase_injection(build_component_cfg_variants(cfg)).to(device)
    staged = bool(cfg.grasp_inference.get("staged", False))
    epochs = int(cfg.train.epochs)
    if smoke and epochs > 2:
        raise ValueError(f"smoke epochs must be <= 2, got {epochs}")

    server_name = resolve_server_name(None)
    manager = None
    run_dir = output_dir
    if smoke or audit:
        if run_dir is None:
            raise ValueError("smoke/audit requires an explicit output directory")
        run_dir.mkdir(parents=True, exist_ok=True)
        if audit:
            # 重みの一致まで比べられるよう、audit では checkpoint も保存する。
            (run_dir / "checkpoints").mkdir(exist_ok=True)
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
    signal = str(cfg.grasp_inference.get("signal", "predicted_sigmoid"))
    tracking.init(
        f"{cfg.experiment.description}_seed{seed}",
        group="S4-grasp-injection-variants",
        job_type=f"{arm}:{signal}{':staged' if staged else ''}",
        config=OmegaConf.to_container(cfg, resolve=True),
    )
    started = time.perf_counter()
    best = {"phase_accuracy": -1.0}
    last_train = {}
    stage1_seconds = None
    try:
        if staged:
            # Stage 1: grasp head alone.  The phase head sees nothing yet.
            stage1_epochs = int(cfg.train.epochs_stage1)
            if smoke and stage1_epochs > 2:
                raise ValueError(
                    f"smoke stage-1 epochs must be <= 2, got {stage1_epochs}"
                )
            assert model.grasp_head is not None
            stage1_optimizer = torch.optim.AdamW(
                model.grasp_head.parameters(),
                lr=float(cfg.train.lr),
                weight_decay=float(cfg.train.weight_decay),
            )
            stage1_start = time.perf_counter()
            _stage_epochs(
                model, train_clips, stage1_optimizer, cfg, device,
                epochs=stage1_epochs, grasp_on=True, phase_on=False,
            )
            stage1_seconds = time.perf_counter() - stage1_start
            # Freeze: from here on the signal cannot move and the grasp loss
            # is not computed at all.
            model.grasp_head.requires_grad_(False)
            trained_params = [p for p in model.parameters() if p.requires_grad]
        else:
            trained_params = list(model.parameters())

        optimizer = torch.optim.AdamW(
            trained_params,
            lr=float(cfg.train.lr),
            weight_decay=float(cfg.train.weight_decay),
        )
        for epoch in range(epochs):
            last_train = _stage_epochs(
                model, train_clips, optimizer, cfg, device,
                epochs=1, grasp_on=not staged, phase_on=True,
            )
            val = evaluate(model, val_clips, device)
            record = {**last_train, **val, "epoch": epoch + 1}
            tracking.log(record, step=epoch)
            print(
                f"[grasp-phase-variants][{arm}:{signal}][{epoch + 1}/{epochs}] "
                f"phase_loss={last_train['train/phase_loss']:.6f} "
                f"val_acc={val['phase_accuracy']:.6f}",
                flush=True,
            )
            if val["phase_accuracy"] > best["phase_accuracy"]:
                best = record
                if (not smoke) and run_dir is not None:
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
        "signal": signal,
        "staged": staged,
        "oracle_upper_bound_only_do_not_report": signal == "oracle_upper_bound_only",
        "completed": len(best) > 1,
        "epochs": epochs,
        "device": str(device),
        "train_clips": len(train_clips),
        "val_clips": len(val_clips),
        "elapsed_seconds": elapsed,
        **({"determinism": determinism_record} if determinism_record else {}),
        **({"stage1_epochs": int(cfg.train.epochs_stage1), "stage1_seconds": stage1_seconds} if staged else {}),
        **last_train,
        **{
            key: value for key, value in best.items() if isinstance(value, (int, float))
        },
    }
    assert run_dir is not None
    if smoke or audit:
        name = "audit_metrics.json" if audit else "smoke_metrics.json"
        (run_dir / name).write_text(
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
            step="S4-grasp-injection-variants",
            tier="must",
            primary_metric="phase + five grasp-presence accuracies",
            extra_result_text=f"grasp inference arm={arm} signal={signal} staged={staged}",
        )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--stage1-epochs", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--audit-dir",
        help="決定性の測定用。experiments/ を汚さずに全世代を走らせ、ここへ書く",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="決定的にする（cfg の train.deterministic: true と同じ。既定は現状のまま）",
    )
    parser.add_argument("--output-dir")
    parser.add_argument("--max-train-clips", type=int, default=1)
    parser.add_argument("--max-val-clips", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg = OmegaConf.load(_path(args.config))
    if args.epochs is not None:
        cfg.train.epochs = args.epochs
    if args.stage1_epochs is not None:
        cfg.train.epochs_stage1 = args.stage1_epochs
    if args.seed is not None:
        cfg.seed = args.seed
    cfg.device = args.device
    cfg.smoke_train_clips = args.max_train_clips
    cfg.smoke_val_clips = args.max_val_clips
    if args.deterministic:
        cfg.train.deterministic = True
    if args.audit_dir:
        result = train(cfg, output_dir=_path(args.audit_dir), audit=True)
    else:
        output_dir = _path(args.output_dir) if args.output_dir else None
        result = train(cfg, output_dir=output_dir, smoke=args.smoke)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

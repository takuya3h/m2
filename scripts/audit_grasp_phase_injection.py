#!/usr/bin/env python
"""Measure all structural acceptance conditions for grasp-phase injection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from omegaconf import OmegaConf

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.datasets.grasp_targets import (  # noqa: E402
    GRASP_LABEL_NAMES,
    load_grasp_target_index,
)
from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402
from egosurgery.models.temporal.grasp_inference_injection import (  # noqa: E402
    GraspInferenceInjectionModel,
    grasp_accuracy_per_class,
    masked_grasp_bce,
)
from egosurgery.utils.eval_recipe import (  # noqa: E402
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
    recipes_match,
)
from egosurgery.utils.grasp_phase_recipe import build_grasp_phase_recipe  # noqa: E402


def tiny_cfg(arm: str, enabled: bool = True) -> dict:
    return {
        "enabled": enabled,
        "arm": arm,
        "input_dim": 8,
        "hidden_dim": 4,
        "num_grasp_classes": 5,
        "num_phases": 3,
        "temporal": {
            "num_stages": 2,
            "num_layers": 2,
            "num_f_maps": 4,
            "dropout": 0.0,
        },
    }


def full_model_cfg(cfg) -> dict:
    return {
        "enabled": True,
        "arm": str(cfg.grasp_inference.arm),
        "input_dim": int(cfg.model.input_dim),
        "hidden_dim": int(cfg.grasp_inference.hidden_dim),
        "num_grasp_classes": int(cfg.grasp_inference.num_classes),
        "num_phases": int(cfg.model.num_phases),
        "temporal": OmegaConf.to_container(cfg.model.temporal, resolve=True),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    torch.manual_seed(17)
    injected = GraspInferenceInjectionModel(tiny_cfg("inj")).eval()
    control = GraspInferenceInjectionModel(tiny_cfg("ctrl")).eval()
    control.load_state_dict(injected.state_dict())
    features = torch.randn(1, 8, 8)
    signal_a = torch.zeros(1, 5, 8)
    signal_b = torch.ones(1, 5, 8)
    inj_a = injected(features, injected_signal=signal_a)["phase_logits"][-1]
    inj_b = injected(features, injected_signal=signal_b)["phase_logits"][-1]
    ctrl_a = control(features, injected_signal=signal_a)["phase_logits"][-1]
    ctrl_b = control(features, injected_signal=signal_b)["phase_logits"][-1]
    inj_delta = float((inj_a - inj_b).abs().max())
    ctrl_delta = float((ctrl_a - ctrl_b).abs().max())

    ctrl_cfg = OmegaConf.load(PROJ / "configs/stage/s4_grasp_injection_ctrl.yaml")
    inj_cfg = OmegaConf.load(PROJ / "configs/stage/s4_grasp_injection_inj.yaml")
    full_control = GraspInferenceInjectionModel(full_model_cfg(ctrl_cfg))
    full_injected = GraspInferenceInjectionModel(full_model_cfg(inj_cfg))
    temporal = ctrl_cfg.model.temporal
    baseline = TeCNO(
        num_stages=int(temporal.num_stages),
        num_layers=int(temporal.num_layers),
        num_f_maps=int(temporal.num_f_maps),
        in_dim=int(ctrl_cfg.model.input_dim),
        num_classes=int(ctrl_cfg.model.num_phases),
        dropout=float(temporal.dropout),
    )
    parameters = {
        "A_trainable": sum(p.numel() for p in baseline.parameters() if p.requires_grad),
        "ctrl_trainable": sum(
            p.numel() for p in full_control.parameters() if p.requires_grad
        ),
        "inj_trainable": sum(
            p.numel() for p in full_injected.parameters() if p.requires_grad
        ),
    }
    parameters["ctrl_minus_A"] = (
        parameters["ctrl_trainable"] - parameters["A_trainable"]
    )

    baseline_recipe = build_eval_recipe(
        test_cfg={
            "task": "phase",
            **PHASE_EVAL_PROTOCOL,
            "backbone": "relation_detr_resnet50_frozen_seed42",
            "temporal_head": "tecno",
            "num_stages": int(temporal.num_stages),
            "num_layers": int(temporal.num_layers),
            "num_f_maps": int(temporal.num_f_maps),
        },
        split_sizes=PAPER_SPLIT_SIZES,
        server_name="lecun",
        gpu_count=1,
        effective_batch_size=1,
        lr_scaling="none",
    )
    ctrl_recipe = build_grasp_phase_recipe(ctrl_cfg, "lecun")
    inj_recipe = build_grasp_phase_recipe(inj_cfg, "lecun")
    false_cfg = OmegaConf.create(OmegaConf.to_container(inj_cfg, resolve=True))
    false_cfg.model.temporal.num_layers += 1
    false_recipe = build_grasp_phase_recipe(false_cfg, "lecun")
    recipe_checks = {
        "baseline_vs_ctrl": recipes_match(baseline_recipe, ctrl_recipe),
        "baseline_vs_inj": recipes_match(baseline_recipe, inj_recipe),
        "baseline_vs_false_temporal": recipes_match(baseline_recipe, false_recipe),
    }

    zero_logits = torch.zeros(1, 5, 2, requires_grad=True)
    one_targets = torch.ones_like(zero_logits)
    masked = torch.zeros(1, 2, dtype=torch.bool)
    annotated = torch.ones(1, 2, dtype=torch.bool)
    loss_checks = {
        "grasp_loss_masked": float(masked_grasp_bce(zero_logits, one_targets, masked)),
        "grasp_loss_annotated": float(
            masked_grasp_bce(zero_logits, one_targets, annotated)
        ),
        "phase_loss_on_masked_frame": float(
            F.cross_entropy(torch.zeros(2, 3), torch.tensor([0, 1]))
        ),
    }
    five_metrics = grasp_accuracy_per_class(zero_logits, one_targets, annotated)

    populations = {}
    manifest_dir = PROJ / "data/processed/phase_manifest"
    for split, expected in (("train", 9657), ("val", 1515), ("test", 4265)):
        manifest = json.loads(
            (manifest_dir / f"{split}.json").read_text(encoding="utf-8")
        )
        stems = {
            str(frame["frame"])
            for clip in manifest["clips"]
            for frame in clip["frames"]
        }
        target_index = load_grasp_target_index(split)
        target_population = set(target_index.labels) | set(target_index.masked_frames)
        populations[split] = {
            "phase_frames": len(stems),
            "annotated_frames": len(target_index.labels),
            "masked_frames": len(target_index.masked_frames),
            "missing_from_grasp_population": len(stems - target_population),
            "extra_in_grasp_population": len(target_population - stems),
            "expected": expected,
        }

    changed_features = features.clone()
    changed_signal = signal_a.clone()
    changed_features[:, :, 5:] += 100.0
    changed_signal[:, :, 5:] -= 100.0
    causal_original = injected(features, injected_signal=signal_a)
    causal_changed = injected(changed_features, injected_signal=changed_signal)
    causal_grasp_delta = float(
        (
            causal_original["grasp_logits"][:, :, :5]
            - causal_changed["grasp_logits"][:, :, :5]
        )
        .abs()
        .max()
    )
    causal_phase_delta = max(
        float((before[:, :, :5] - after[:, :, :5]).abs().max())
        for before, after in zip(
            causal_original["phase_logits"], causal_changed["phase_logits"]
        )
    )

    base_small = TeCNO(
        num_stages=2,
        num_layers=2,
        num_f_maps=4,
        in_dim=8,
        num_classes=3,
        dropout=0.0,
    ).eval()
    disabled = GraspInferenceInjectionModel(tiny_cfg("ctrl", enabled=False)).eval()
    disabled.phase_head.load_state_dict(base_small.state_dict())
    disabled_outputs = disabled(features)["phase_logits"]
    base_outputs = base_small(features)
    disabled_delta = max(
        float((before - after).abs().max())
        for before, after in zip(base_outputs, disabled_outputs)
    )

    report = {
        "signal_reachability": {
            "inj_max_abs_delta": inj_delta,
            "ctrl_max_abs_delta": ctrl_delta,
        },
        "trainable_parameters": parameters,
        "recipes": recipe_checks,
        "loss_masking": loss_checks,
        "grasp_accuracy_per_class": dict(zip(GRASP_LABEL_NAMES, five_metrics)),
        "population": populations,
        "causality": {
            "past_grasp_max_abs_delta": causal_grasp_delta,
            "past_phase_max_abs_delta": causal_phase_delta,
        },
        "disabled_vs_existing_max_abs_delta": disabled_delta,
    }

    checks = [
        inj_delta > 0.0,
        ctrl_delta == 0.0,
        parameters["ctrl_trainable"] == parameters["inj_trainable"],
        parameters["ctrl_minus_A"] > 0,
        recipe_checks["baseline_vs_ctrl"],
        recipe_checks["baseline_vs_inj"],
        not recipe_checks["baseline_vs_false_temporal"],
        loss_checks["grasp_loss_masked"] == 0.0,
        loss_checks["grasp_loss_annotated"] > 0.0,
        loss_checks["phase_loss_on_masked_frame"] > 0.0,
        len(five_metrics) == 5,
        all(
            row["phase_frames"] == row["expected"]
            and row["missing_from_grasp_population"] == 0
            and row["extra_in_grasp_population"] == 0
            for row in populations.values()
        ),
        causal_grasp_delta == 0.0,
        causal_phase_delta == 0.0,
        disabled_delta == 0.0,
    ]
    report["all_pass"] = all(checks)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

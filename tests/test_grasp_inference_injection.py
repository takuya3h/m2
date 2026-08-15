from __future__ import annotations

import json

import numpy as np
import torch
import torch.nn.functional as F
from omegaconf import OmegaConf

from egosurgery.datasets.grasp_targets import load_grasp_target_index
from egosurgery.models.build import build_grasp_phase_injection
from egosurgery.models.heads.tecno_head import TeCNO
from egosurgery.models.temporal.grasp_inference_injection import (
    GraspInferenceInjectionModel,
    grasp_accuracy_per_class,
    masked_grasp_bce,
)
from egosurgery.utils.eval_recipe import recipes_match
from egosurgery.utils.grasp_phase_recipe import build_grasp_phase_recipe


def _cfg(arm: str = "inj", enabled: bool = True) -> dict:
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


def test_grasp_model_shapes_and_five_metrics() -> None:
    model = GraspInferenceInjectionModel(_cfg()).eval()
    features = torch.randn(2, 8, 7)
    outputs = model(features)
    assert outputs["grasp_logits"].shape == (2, 5, 7)
    assert outputs["phase_input_signal"].shape == (2, 5, 7)
    assert [item.shape for item in outputs["phase_logits"]] == [(2, 3, 7), (2, 3, 7)]

    targets = torch.zeros(2, 5, 7)
    valid = torch.ones(2, 7, dtype=torch.bool)
    metrics = grasp_accuracy_per_class(outputs["grasp_logits"], targets, valid)
    assert len(metrics) == 5
    assert all(0.0 <= value <= 1.0 for value in metrics)


def test_signal_reaches_injected_arm_but_not_control() -> None:
    torch.manual_seed(7)
    injected = GraspInferenceInjectionModel(_cfg("inj")).eval()
    control = GraspInferenceInjectionModel(_cfg("ctrl")).eval()
    control.load_state_dict(injected.state_dict())

    features = torch.randn(1, 8, 6)
    signal_a = torch.zeros(1, 5, 6)
    signal_b = torch.ones(1, 5, 6)
    inj_a = injected(features, injected_signal=signal_a)["phase_logits"][-1]
    inj_b = injected(features, injected_signal=signal_b)["phase_logits"][-1]
    ctrl_a = control(features, injected_signal=signal_a)["phase_logits"][-1]
    ctrl_b = control(features, injected_signal=signal_b)["phase_logits"][-1]

    assert float((inj_a - inj_b).abs().max()) > 0.0
    torch.testing.assert_close(ctrl_a, ctrl_b, rtol=0.0, atol=0.0)


def test_control_and_injection_parameter_counts_match() -> None:
    control = GraspInferenceInjectionModel(_cfg("ctrl"))
    injected = GraspInferenceInjectionModel(_cfg("inj"))
    baseline = TeCNO(
        num_stages=2,
        num_layers=2,
        num_f_maps=4,
        in_dim=8,
        num_classes=3,
        dropout=0.0,
    )
    n_control = sum(parameter.numel() for parameter in control.parameters())
    n_injected = sum(parameter.numel() for parameter in injected.parameters())
    n_baseline = sum(parameter.numel() for parameter in baseline.parameters())
    assert n_control == n_injected
    assert n_control > n_baseline


def test_mask_only_disables_grasp_loss() -> None:
    logits = torch.zeros(1, 5, 2, requires_grad=True)
    targets = torch.ones_like(logits)
    masked = torch.zeros(1, 2, dtype=torch.bool)
    annotated = torch.ones(1, 2, dtype=torch.bool)

    assert float(masked_grasp_bce(logits, targets, masked)) == 0.0
    assert float(masked_grasp_bce(logits, targets, annotated)) > 0.0
    phase_loss = F.cross_entropy(torch.zeros(2, 3), torch.tensor([0, 1]))
    assert float(phase_loss) > 0.0


def test_grasp_injection_is_causal() -> None:
    torch.manual_seed(11)
    model = GraspInferenceInjectionModel(_cfg("inj")).eval()
    features = torch.randn(1, 8, 8)
    signal = torch.randn(1, 5, 8)
    changed_features = features.clone()
    changed_features[:, :, 5:] += 100.0
    changed_signal = signal.clone()
    changed_signal[:, :, 5:] -= 100.0

    original = model(features, injected_signal=signal)
    changed = model(changed_features, injected_signal=changed_signal)
    torch.testing.assert_close(
        original["grasp_logits"][:, :, :5], changed["grasp_logits"][:, :, :5]
    )
    for original_stage, changed_stage in zip(
        original["phase_logits"], changed["phase_logits"]
    ):
        torch.testing.assert_close(original_stage[:, :, :5], changed_stage[:, :, :5])


def test_disabled_component_matches_existing_tecno() -> None:
    baseline = TeCNO(
        num_stages=2,
        num_layers=2,
        num_f_maps=4,
        in_dim=8,
        num_classes=3,
        dropout=0.0,
    ).eval()
    disabled = GraspInferenceInjectionModel(_cfg(enabled=False)).eval()
    disabled.phase_head.load_state_dict(baseline.state_dict())
    features = torch.randn(1, 8, 6)
    expected = baseline(features)
    actual = disabled(features)["phase_logits"]
    for expected_stage, actual_stage in zip(expected, actual):
        torch.testing.assert_close(expected_stage, actual_stage, rtol=0.0, atol=0.0)


def test_recipe_ignores_arm_but_detects_temporal_change() -> None:
    base = {
        "model": {"temporal": {"num_stages": 2, "num_layers": 8, "num_f_maps": 64}},
        "grasp_inference": {"arm": "ctrl"},
    }
    injected = OmegaConf.create(base)
    injected.grasp_inference.arm = "inj"
    changed = OmegaConf.create(base)
    changed.model.temporal.num_layers = 7

    ctrl_recipe = build_grasp_phase_recipe(OmegaConf.create(base), "lecun")
    inj_recipe = build_grasp_phase_recipe(injected, "lecun")
    changed_recipe = build_grasp_phase_recipe(changed, "lecun")
    assert recipes_match(ctrl_recipe, inj_recipe)
    assert not recipes_match(ctrl_recipe, changed_recipe)


def test_grasp_target_index_preserves_masked_frame(tmp_path) -> None:
    (tmp_path / "loss_mask").mkdir()
    (tmp_path / "loss_mask" / "train.txt").write_text("frame_b\n", encoding="utf-8")
    data = {
        "images": [
            {"id": 1, "file_name": "frame_a.jpg"},
        ],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 3},
        ],
        "categories": [
            {"id": index, "name": f"class-{index}"} for index in range(1, 6)
        ],
    }
    (tmp_path / "train.json").write_text(json.dumps(data), encoding="utf-8")

    index = load_grasp_target_index("train", tmp_path)
    target, valid = index.target_for("frame_a")
    masked_target, masked_valid = index.target_for("frame_b")
    np.testing.assert_array_equal(target, np.asarray([0, 0, 1, 0, 0]))
    np.testing.assert_array_equal(masked_target, np.zeros(5))
    assert valid is True
    assert masked_valid is False


def test_factory_resolves_new_component_config() -> None:
    model = build_grasp_phase_injection("grasp_phase_injection")
    assert isinstance(model, GraspInferenceInjectionModel)
    assert model.enabled is False

"""Signal-shape variants: reachability, parity, distinctness, causality.

通ることだけを確かめない。破れるべきときに破れること（未知の値・承認なしの
oracle・定数なしの standardized・教師なしの oracle forward）も対で確かめる。
"""

from __future__ import annotations

import pytest
import torch

from egosurgery.models.heads.tecno_head import TeCNO
from egosurgery.models.temporal.grasp_inference_injection import (
    SIGNAL_MODES,
    GraspInferenceInjectionModel,
)

CENTER = [0.925502, 0.896323, 0.761971, 0.766994, 0.101753]
SCALE = [0.262579, 0.304841, 0.425877, 0.422746, 0.302323]
FILL = [0.925502, 0.896323, 0.761971, 0.766994, 0.101753]

FORM_EXTRAS = {
    "predicted_sigmoid": {},
    "raw_logits": {},
    "standardized": {"signal_center": CENTER, "signal_scale": SCALE},
    "oracle_upper_bound_only": {
        "oracle_upper_bound_acknowledged": True,
        "oracle_missing_fill": FILL,
    },
}
FOUR_FORMS = tuple(FORM_EXTRAS)


def _cfg(arm: str = "inj", signal: str | None = None, **extra) -> dict:
    cfg = {
        "enabled": True,
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
    if signal is not None:
        cfg["signal"] = signal
        cfg.update(FORM_EXTRAS.get(signal, {}))
    cfg.update(extra)
    return cfg


def _batchlike(t: int = 6):
    torch.manual_seed(3)
    features = torch.randn(1, 8, t)
    targets = torch.randint(0, 2, (1, 5, t)).float()
    valid = torch.ones(1, t)
    return features, targets, valid


# ---------------------------------------------------------------- ガード --


def test_unknown_signal_fails_loudly() -> None:
    """未知の値は落ちる。黙って既定にならない。今回直した欠陥そのもの。"""
    with pytest.raises(ValueError, match="unknown grasp injection signal"):
        GraspInferenceInjectionModel(_cfg(signal="predicted_sigmoi"))


def test_oracle_refuses_without_acknowledgement() -> None:
    """上限測定専用の形は、明示の承認なしでは構築できない。"""
    with pytest.raises(ValueError, match="never be reported"):
        GraspInferenceInjectionModel(
            _cfg(signal="oracle_upper_bound_only", oracle_upper_bound_acknowledged=None)
        )


def test_standardized_requires_constants() -> None:
    cfg = _cfg(signal="standardized")
    cfg.pop("signal_center")
    with pytest.raises(ValueError, match="signal_center"):
        GraspInferenceInjectionModel(cfg)


def test_oracle_forward_requires_targets() -> None:
    model = GraspInferenceInjectionModel(_cfg(signal="oracle_upper_bound_only")).eval()
    features, _, _ = _batchlike()
    with pytest.raises(ValueError, match="grasp_targets"):
        model(features)


# ------------------------------------------------------- G2: 信号の到達 --


@pytest.mark.parametrize("signal", FOUR_FORMS)
def test_signal_reaches_phase_head_in_each_form(signal: str) -> None:
    """四つの形すべてで、渡す信号を変えると工程側の出力が変わる。"""
    torch.manual_seed(7)
    model = GraspInferenceInjectionModel(_cfg("inj", signal)).eval()
    features, targets, valid = _batchlike()
    kwargs = {"grasp_targets": targets, "grasp_valid": valid}
    out_a = model(features, injected_signal=torch.zeros(1, 5, 6), **kwargs)
    out_b = model(features, injected_signal=torch.ones(1, 5, 6), **kwargs)
    delta = float(
        (out_a["phase_logits"][-1] - out_b["phase_logits"][-1]).abs().max()
    )
    assert delta > 0.0, f"signal={signal} で信号が工程側へ届いていない"


@pytest.mark.parametrize("signal", FOUR_FORMS)
def test_uninformative_arm_blocks_signal_in_each_form(signal: str) -> None:
    """無情報な腕（ctrl）では、どの形でも信号が届かない。対照。"""
    torch.manual_seed(7)
    model = GraspInferenceInjectionModel(_cfg("ctrl", signal)).eval()
    features, targets, valid = _batchlike()
    kwargs = {"grasp_targets": targets, "grasp_valid": valid}
    out_a = model(features, injected_signal=torch.zeros(1, 5, 6), **kwargs)
    out_b = model(features, injected_signal=torch.ones(1, 5, 6), **kwargs)
    torch.testing.assert_close(
        out_a["phase_logits"][-1], out_b["phase_logits"][-1], rtol=0.0, atol=0.0
    )


# --------------------------------------------------- G3: 重みの総数一致 --


def _fullsize_cfg(arm: str, signal: str) -> dict:
    return _cfg(
        arm,
        signal,
        input_dim=2048,
        hidden_dim=64,
        num_phases=9,
        temporal={"num_stages": 2, "num_layers": 8, "num_f_maps": 64, "dropout": 0.5},
    )


def test_all_five_arms_share_parameter_count() -> None:
    """五つの腕（四つの形 + 無情報）の学習可能な重みの総数が完全に一致する。

    実寸で数える。前の実験の実測 528919、基準点 397138、差 131781 と照合する。
    """
    counts = {}
    for signal in FOUR_FORMS:
        model = GraspInferenceInjectionModel(_fullsize_cfg("inj", signal))
        counts[signal] = sum(p.numel() for p in model.parameters() if p.requires_grad)
    ctrl = GraspInferenceInjectionModel(_fullsize_cfg("ctrl", "zeros"))
    counts["ctrl:zeros"] = sum(p.numel() for p in ctrl.parameters() if p.requires_grad)

    assert len(set(counts.values())) == 1, counts
    assert next(iter(counts.values())) == 528919, counts

    baseline = TeCNO(
        num_stages=2, num_layers=8, num_f_maps=64, in_dim=2048, num_classes=9, dropout=0.5
    )
    n_baseline = sum(p.numel() for p in baseline.parameters())
    assert n_baseline == 397138
    assert next(iter(counts.values())) - n_baseline == 131781


# ----------------------------------------------- 形ごとに渡す値が違う --


def test_forms_pass_distinct_values() -> None:
    """同じ入力・同じ重みで、四つの形が実際に違う値を渡している。"""
    torch.manual_seed(5)
    features, targets, valid = _batchlike()
    reference = GraspInferenceInjectionModel(_cfg("inj", "predicted_sigmoid")).eval()

    signals = {}
    for signal in FOUR_FORMS:
        model = GraspInferenceInjectionModel(_cfg("inj", signal)).eval()
        model.load_state_dict(reference.state_dict(), strict=False)
        out = model(features, grasp_targets=targets, grasp_valid=valid)
        signals[signal] = out["phase_input_signal"]

    sigmoid = signals["predicted_sigmoid"]
    logits = signals["raw_logits"]
    standardized = signals["standardized"]
    oracle = signals["oracle_upper_bound_only"]

    # 押しつぶす前: 零から一に収まらない（sigmoid の逆像なので必ずはみ出す）。
    assert float(logits.min()) < 0.0 or float(logits.max()) > 1.0
    torch.testing.assert_close(torch.sigmoid(logits), sigmoid)

    # 揃えた値: 記録した定数どおりの affine 変換になっている。
    center = torch.tensor(CENTER).view(1, 5, 1)
    scale = torch.tensor(SCALE).view(1, 5, 1)
    torch.testing.assert_close(standardized, (sigmoid - center) / scale)

    # 正解: 教師ありのフレームでは値が零か一のみで、教師と完全に一致する。
    assert set(torch.unique(oracle).tolist()) <= {0.0, 1.0}
    torch.testing.assert_close(oracle, targets)

    # 四つが互いに異なる値を渡している。
    tensors = list(signals.values())
    for i in range(len(tensors)):
        for j in range(i + 1, len(tensors)):
            assert float((tensors[i] - tensors[j]).abs().max()) > 0.0


def test_oracle_missing_frames_receive_recorded_fill() -> None:
    """教師の無いフレームには記録済みの埋め値（学習側の正例率）が渡る。"""
    model = GraspInferenceInjectionModel(_cfg("inj", "oracle_upper_bound_only")).eval()
    features, targets, valid = _batchlike()
    valid[0, 2] = 0.0  # 1 フレームだけ教師を消す
    out = model(features, grasp_targets=targets, grasp_valid=valid)
    signal = out["phase_input_signal"]
    torch.testing.assert_close(signal[0, :, 2], torch.tensor(FILL))
    # 埋め値は 0/1 でないため、教師の有無は下流から区別できる（漏れは残る）。
    assert not set(signal[0, :, 2].tolist()) <= {0.0, 1.0}


def test_staged_freeze_keeps_signal_fixed() -> None:
    """段階を分ける形: 固定した後は、工程側を学習しても信号が動かない。"""
    torch.manual_seed(9)
    model = GraspInferenceInjectionModel(_cfg("inj", "predicted_sigmoid"))
    features, targets, valid = _batchlike()

    model.grasp_head.requires_grad_(False)
    frozen = [p for p in model.parameters() if p.requires_grad]
    assert sum(p.numel() for p in model.parameters()) == sum(
        p.numel() for p in GraspInferenceInjectionModel(_cfg("inj")).parameters()
    ), "固定は重みの総数を変えない（学習の順序が違うだけ）"

    before = model(features)["phase_input_signal"].clone()
    optimizer = torch.optim.SGD(frozen, lr=0.5)
    out = model(features)
    loss = out["phase_logits"][-1].sum()
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    after = model(features)["phase_input_signal"]
    torch.testing.assert_close(before, after, rtol=0.0, atol=0.0)


# ------------------------------------------------------ 既定と因果性 --


def test_default_behaviour_unchanged_without_signal_key() -> None:
    """signal を書かない設定は predicted_sigmoid と同一の出力になる。"""
    torch.manual_seed(4)
    implicit = GraspInferenceInjectionModel(_cfg("inj")).eval()
    explicit = GraspInferenceInjectionModel(_cfg("inj", "predicted_sigmoid")).eval()
    explicit.load_state_dict(implicit.state_dict())
    features, _, _ = _batchlike()
    torch.testing.assert_close(
        implicit(features)["phase_logits"][-1],
        explicit(features)["phase_logits"][-1],
        rtol=0.0,
        atol=0.0,
    )
    assert implicit.signal == "predicted_sigmoid"
    assert set(SIGNAL_MODES) >= set(FOUR_FORMS)


@pytest.mark.parametrize("signal", FOUR_FORMS)
def test_each_form_is_causal(signal: str) -> None:
    """未来のフレームを差し替えても過去の出力が変わらない。四つの形すべて。"""
    torch.manual_seed(11)
    model = GraspInferenceInjectionModel(_cfg("inj", signal)).eval()
    t = 8
    features = torch.randn(1, 8, t)
    targets = torch.randint(0, 2, (1, 5, t)).float()
    valid = torch.ones(1, t)

    changed_features = features.clone()
    changed_features[:, :, 5:] += 100.0
    changed_targets = targets.clone()
    changed_targets[:, :, 5:] = 1.0 - changed_targets[:, :, 5:]

    original = model(features, grasp_targets=targets, grasp_valid=valid)
    changed = model(
        changed_features, grasp_targets=changed_targets, grasp_valid=valid
    )
    for original_stage, changed_stage in zip(
        original["phase_logits"], changed["phase_logits"]
    ):
        torch.testing.assert_close(original_stage[:, :, :5], changed_stage[:, :, :5])

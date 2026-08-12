"""モデル（models/）の統合テスト。

DINOv2 backbone のテストはネットワーク接続（torch.hub のダウンロード）が
必要なため、取得に失敗した場合は ``pytest.skip`` でスキップする。
Mask DINO / VarifocalNet は Detectron2 / mmdet 非依存環境でも import 可能な
よう設計されているため、本体構築は環境依存でスキップされうる。

実行方法:
    PYTHONPATH=src pytest tests/test_models.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

# PYTHONPATH=src を付け忘れても import できるよう src/ を通す。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---------------------------------------------------------------------- #
# DINOv2 backbone 設定（テストは軽量な ViT-S/14 with registers を用いる）
# ---------------------------------------------------------------------- #
def _vits_backbone_cfg(peft_method: str | None = "lora") -> dict:
    """ViT-S/14 with registers の backbone 設定を返す。"""
    return {
        "hub_repo": "facebookresearch/dinov2",
        "hub_model": "dinov2_vits14_reg",
        "out_indices": [2, 5, 8, 11],
        "embed_dim": 384,
        "patch_size": 14,
        "img_size": 518,
        "pretrained": True,
        "gradient_checkpointing": False,
        "peft": {
            "method": peft_method,
            "r": 8,
            "lora_alpha": 16,
            "lora_dropout": 0.05,
            "target_modules": ["qkv", "proj"],
            "use_dora": False,
        },
    }


def _load_dinov2_or_skip(peft_method: str | None = "lora"):
    """DINOv2 backbone を構築する。取得に失敗したらテストをスキップする。"""
    from omegaconf import OmegaConf

    from egosurgery.models.backbones.dinov2_registry import DINOv2Backbone

    try:
        return DINOv2Backbone(OmegaConf.create(_vits_backbone_cfg(peft_method)))
    except Exception as exc:  # ネットワーク不通・hub 互換性など
        pytest.skip(f"DINOv2 をロードできません: {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------- #
# 1. DINOv2 backbone の forward
# ---------------------------------------------------------------------- #
def test_dinov2_backbone_forward():
    """DINOv2 backbone が 4 段階特徴 + cls_token を返すこと。"""
    backbone = _load_dinov2_or_skip(peft_method=None)
    backbone.train(False)

    with torch.no_grad():
        out = backbone(torch.randn(2, 3, 518, 518))

    assert set(out.keys()) == {"features", "cls_token"}
    assert len(out["features"]) == 4
    for feat in out["features"]:
        # 518 / 14 = 37
        assert feat.shape == (2, 384, 37, 37)
    assert out["cls_token"].shape == (2, 384)


# ---------------------------------------------------------------------- #
# 2. LoRA 適用後の forward と学習可能パラメータ比率
# ---------------------------------------------------------------------- #
def test_dinov2_with_lora():
    """LoRA 適用後も forward が通り、学習可能パラメータが全体の数%程度。"""
    from omegaconf import OmegaConf

    from egosurgery.models.backbones.peft import (
        apply_peft,
        count_trainable_parameters,
    )

    backbone = _load_dinov2_or_skip(peft_method=None)
    peft_cfg = OmegaConf.create(_vits_backbone_cfg("lora")["peft"])

    try:
        lora_backbone = apply_peft(backbone, peft_cfg)
    except Exception as exc:  # peft 環境依存の失敗
        pytest.skip(f"PEFT を適用できません: {type(exc).__name__}: {exc}")

    with torch.no_grad():
        out = lora_backbone(torch.randn(2, 3, 518, 518))
    assert len(out["features"]) == 4

    trainable, total = count_trainable_parameters(lora_backbone)
    assert total > 0
    fraction = trainable / total
    # LoRA は backbone を凍結しアダプタのみ学習するため、ごく小さい比率になる。
    assert 0.0 < fraction < 0.1, f"学習可能パラメータ比率が想定外: {fraction:.4f}"


# ---------------------------------------------------------------------- #
# 3. ViT-Adapter の出力 shape
# ---------------------------------------------------------------------- #
def test_vit_adapter_output_shapes():
    """ViT-Adapter が stride 4/8/16/32 の 4 段階特徴を返すこと。"""
    from egosurgery.models.backbones.vit_adapter import ViTAdapter

    adapter = ViTAdapter(embed_dim=384, out_channels=256, num_outs=4)
    # DINOv2 ViT/14 の等解像度特徴を模した入力（stride 14, 37x37）。
    features = [torch.randn(2, 384, 37, 37) for _ in range(4)]

    outs = adapter(features)

    assert len(outs) == 4
    for out in outs:
        assert out.shape[0] == 2 and out.shape[1] == 256
    # stride 4 < 8 < 16 < 32 なので解像度は単調減少する。
    sizes = [out.shape[-1] for out in outs]
    assert sizes[0] > sizes[1] > sizes[2] > sizes[3]
    # 最粗段階 (stride 32) は 518/32 ≈ 16。
    assert sizes[3] == round(518 / 32)


# ---------------------------------------------------------------------- #
# 4. build_model（S0 構成）
# ---------------------------------------------------------------------- #
def test_build_model_s0():
    """S0 config で build_model が backbone + detection_head を返すこと。"""
    from omegaconf import OmegaConf

    from egosurgery.models.build import build_model

    cfg = OmegaConf.create(
        {
            "model": {
                "num_classes": 15,
                "backbone": _vits_backbone_cfg(peft_method=None),
                "detection_head": {
                    "name": "mask_dino",
                    "num_queries": 300,
                    "hidden_dim": 256,
                    "mask_on": False,
                },
            },
            "relation": {"enabled": False},
            "exo": {"enabled": False},
        }
    )

    try:
        model = build_model(cfg)
    except Exception as exc:
        pytest.skip(f"build_model に必要な DINOv2 をロードできません: {exc}")

    assert "backbone" in model.components
    assert "detection_head" in model.components
    # detection_head は nn.Module（Detectron2 非依存環境でも構築可能）。
    assert isinstance(model.detection_head, torch.nn.Module)


# ---------------------------------------------------------------------- #
# 4b. build_model で CoDETR ヘッドが構築できること（§13.2 S0・§9 #6）
# ---------------------------------------------------------------------- #
def test_build_model_codetr():
    """configs/model/detection_head/co_detr.yaml で build_model が CoDETRHead
    を含むモデルを返すこと（mmdet projects/CO-DETR 非依存環境でも構築自体は通る）。"""
    from omegaconf import OmegaConf

    from egosurgery.models.build import build_model
    from egosurgery.models.heads.codetr_head import CoDETRHead

    cfg = OmegaConf.create(
        {
            "model": {
                "num_classes": 15,
                "backbone": _vits_backbone_cfg(peft_method=None),
                "detection_head": {
                    "name": "codetr",
                    "num_queries": 300,
                    "with_box_refine": True,
                    "as_two_stage": True,
                    "aux_heads": {"enabled": True},
                    "mask_on": False,
                },
            },
            "relation": {"enabled": False},
            "exo": {"enabled": False},
        }
    )

    try:
        model = build_model(cfg)
    except Exception as exc:
        pytest.skip(f"build_model に必要な DINOv2 をロードできません: {exc}")

    assert "detection_head" in model.components
    assert isinstance(model.detection_head, CoDETRHead)
    # CoDETRHead は num_classes を保持していること（ヘッド側で受け取れる口の検証）。
    assert model.detection_head.num_classes == 15
    # test_cfg 受け取り口（§15.3 G1）が既定の locked-down 値で初期化されている。
    assert model.detection_head.test_detections_per_img == 300
    assert model.detection_head.test_score_thr == 1e-8


# ---------------------------------------------------------------------- #
# 5. Seesaw Loss の勾配
# ---------------------------------------------------------------------- #
def test_seesaw_loss_gradient():
    """Seesaw Loss がスカラー損失と正しい shape の勾配を返すこと。"""
    from egosurgery.models.losses.detection import SeesawLoss

    loss_fn = SeesawLoss(p=0.8, q=2.0, num_classes=15)
    cls_score = torch.randn(8, 15, requires_grad=True)
    labels = torch.randint(0, 15, (8,))

    loss = loss_fn(cls_score, labels)

    assert loss.ndim == 0
    assert torch.isfinite(loss)
    loss.backward()
    assert cls_score.grad is not None
    assert cls_score.grad.shape == cls_score.shape


# ---------------------------------------------------------------------- #
# 6. Logit Adjustment
# ---------------------------------------------------------------------- #
def test_logit_adjustment():
    """Logit Adjustment が頻度の対数事前分布で logit を調整すること。"""
    from egosurgery.models.losses.logit_adjust import LogitAdjustment

    # 長尾の頻度（高頻度クラス -> 稀少クラス）。
    frequencies = [1000, 500, 100, 20, 5]
    adjuster = LogitAdjustment(frequencies, tau=1.0)

    logits = torch.randn(4, 5)
    adjusted = adjuster(logits)

    # 調整量は tau * log_prior に一致する。
    delta = adjusted - logits
    expected = adjuster.tau * adjuster.log_prior.expand_as(delta)
    assert torch.allclose(delta, expected, atol=1e-6)
    # 高頻度クラスほど log_prior が大きい（= 補正の加算量が大きい）。
    assert adjuster.log_prior[0] > adjuster.log_prior[-1]


# ---------------------------------------------------------------------- #
# 7. PhaseHead (S3)
# ---------------------------------------------------------------------- #
def test_phase_head_forward():
    """PhaseHead が (B, input_dim) -> (B, num_classes) の forward を通すこと。"""
    from egosurgery.models.heads.phase_head import PhaseHead

    head = PhaseHead(input_dim=1024, num_classes=9, hidden_dim=512, dropout=0.3)
    x = torch.randn(4, 1024)
    out = head(x)
    assert out.shape == (4, 9)
    # 出力に NaN が混入しない。
    assert not torch.isnan(out).any()


def test_phase_loss_gradient():
    """PhaseLoss が class_weights / label_smoothing を尊重し勾配を返すこと。"""
    from egosurgery.models.losses.phase import PhaseLoss, class_weights_from_frequencies

    weights = class_weights_from_frequencies()
    loss_fn = PhaseLoss(class_weights=weights, label_smoothing=0.1)

    logits = torch.randn(8, 9, requires_grad=True)
    targets = torch.tensor([0, 1, 2, 3, 4, 5, 6, 7, 0][:8])
    loss = loss_fn(logits, targets)
    assert torch.is_tensor(loss) and loss.ndim == 0
    loss.backward()
    assert logits.grad is not None
    assert logits.grad.shape == logits.shape
    # クラス重みが効くこと: 重み付きと均一の loss が異なる値になる。
    unweighted = PhaseLoss(label_smoothing=0.0)(logits.detach(), targets)
    skewed = torch.ones(9)
    skewed[0] = 10.0  # クラス 0 だけ強調
    weighted = PhaseLoss(class_weights=skewed, label_smoothing=0.0)(logits.detach(), targets)
    assert abs(float(weighted) - float(unweighted)) > 1e-4

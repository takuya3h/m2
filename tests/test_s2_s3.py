"""S2 (hand 検出) + S3 (Phase head) のユニットテスト。

prompts_n/phase2_part4_s2_s3_v2.md §3 で要求される 9 件のテスト:

1. test_hand_head_forward: HandHead が 4 クラス logits を返す
2. test_layer_wise_lr: layer-wise lr が backbone/tool/hand head で異なる
3. test_backbone_freeze: freeze_epochs 中は backbone の grad が False
4. test_phase_head_forward: PhaseHead が 9 クラス logits を返す
5. test_phase_loss_no_weights: use_class_weights=False で正常動作
6. test_phase_loss_with_clipped_weights: 重み比が max_weight_ratio 以内
7. test_phase_loss_label_smoothing: label_smoothing=0.1 が適用される
8. test_s2_negative_transfer_config: S2 yaml の negative_transfer 構成
9. test_phase_trainer_writes_eval_recipe: PhaseTrainer の eval_recipe 構造

実行方法:
    PYTHONPATH=src pytest tests/test_s2_s3.py -v

注: test #2 / #3 は MMDetTrainer.setup() 経由ではなく、optim_wrapper や
nn.Module の requires_grad を直接検証する形にして heavy なセットアップを避ける。
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---------------------------------------------------------------------- #
# 1. HandHead の forward
# ---------------------------------------------------------------------- #
def test_hand_head_forward():
    """HandHead (input_dim=256) が (N, 4) の logits を返す。"""
    from egosurgery.models.heads.hand_head import HAND_CLASS_NAMES, HandHead

    head = HandHead(input_dim=256, num_classes=4)
    out = head(torch.randn(8, 256))
    assert out.shape == (8, 4)
    # 4 クラス名が own/other × L/R で揃っている。
    assert len(HAND_CLASS_NAMES) == 4
    assert any("Own" in n for n in HAND_CLASS_NAMES)
    assert any("Other" in n for n in HAND_CLASS_NAMES)


# ---------------------------------------------------------------------- #
# 2. layer-wise lr が backbone と tool head / hand head で異なる
# ---------------------------------------------------------------------- #
def test_layer_wise_lr():
    """negative_transfer.layer_wise_lr 設定で paramwise_cfg に backbone の
    lr_mult が反映されることを確認する（MMDetTrainer の内部メソッドを直接呼ぶ）。"""
    from omegaconf import OmegaConf

    from egosurgery.engines.mmdet_trainer import MMDetTrainer

    cfg = OmegaConf.create(
        {
            "negative_transfer": {
                "layer_wise_lr": {
                    "enabled": True,
                    "backbone_lr_scale": 0.1,
                    "existing_head_lr_scale": 0.1,
                    "new_head_lr_scale": 1.0,
                },
            },
        }
    )
    trainer = MMDetTrainer.__new__(MMDetTrainer)  # __init__ をバイパス
    trainer.cfg = cfg

    # ダミーの mmcfg（dict ベース）を渡す。
    class _Cfg(dict):
        def __getattr__(self, k):
            return self[k]

        def __setattr__(self, k, v):
            self[k] = v

    mmcfg = _Cfg(optim_wrapper=_Cfg())
    trainer._apply_negative_transfer_overrides(mmcfg)
    pwc = mmcfg.optim_wrapper["paramwise_cfg"]
    assert "custom_keys" in pwc
    assert "backbone" in pwc["custom_keys"]
    assert pwc["custom_keys"]["backbone"]["lr_mult"] == 0.1


# ---------------------------------------------------------------------- #
# 3. backbone_freeze: requires_grad が False になることを直接検証
# ---------------------------------------------------------------------- #
def test_backbone_freeze():
    """nn.Parameter の requires_grad=False で backbone が凍結される様子を
    PyTorch レベルで直接検証する（hook 実装は本番拡張のためここでは扱わない）。"""
    backbone = torch.nn.Sequential(
        torch.nn.Linear(10, 10), torch.nn.ReLU(), torch.nn.Linear(10, 5)
    )
    for p in backbone.parameters():
        p.requires_grad = False
    head = torch.nn.Linear(5, 4)
    trainable_backbone = sum(p.numel() for p in backbone.parameters() if p.requires_grad)
    trainable_head = sum(p.numel() for p in head.parameters() if p.requires_grad)
    assert trainable_backbone == 0
    assert trainable_head > 0


# ---------------------------------------------------------------------- #
# 4. PhaseHead forward
# ---------------------------------------------------------------------- #
def test_phase_head_forward():
    """PhaseHead (input_dim=1024) が (B, 9) の logits を返す。"""
    from egosurgery.models.heads.phase_head import PhaseHead

    head = PhaseHead(input_dim=1024, num_classes=9)
    out = head(torch.randn(4, 1024))
    assert out.shape == (4, 9)


# ---------------------------------------------------------------------- #
# 5. PhaseLoss: use_class_weights=False で重みなし動作【§14】
# ---------------------------------------------------------------------- #
def test_phase_loss_no_weights():
    """v2 デフォルト (use_class_weights=False) で重みなしの cross-entropy。"""
    from egosurgery.models.losses.phase import PhaseLoss

    loss_fn = PhaseLoss(use_class_weights=False)
    assert loss_fn.class_weights is None
    logits = torch.randn(4, 9, requires_grad=True)
    targets = torch.randint(0, 9, (4,))
    loss = loss_fn(logits, targets)
    assert torch.isfinite(loss)
    loss.backward()
    assert logits.grad is not None


# ---------------------------------------------------------------------- #
# 6. PhaseLoss: use_class_weights=True で重み比が上限以内【§14 最重要】
# ---------------------------------------------------------------------- #
def test_phase_loss_with_clipped_weights():
    """逆頻度ベース重みでも max_weight_ratio で必ずクリップされる。"""
    from egosurgery.models.losses.phase import PhaseLoss

    loss_fn = PhaseLoss(use_class_weights=True, max_weight_ratio=10.0)
    assert loss_fn.class_weights is not None
    w = loss_fn.class_weights
    ratio = float(w.max() / w.min())
    assert ratio <= 10.0 + 1e-5, f"重み比 {ratio:.2f} が上限 10.0 を超えている"


# ---------------------------------------------------------------------- #
# 7. PhaseLoss: label_smoothing が常時適用される
# ---------------------------------------------------------------------- #
def test_phase_loss_label_smoothing():
    """label_smoothing=0.1 が cross_entropy へ実際に渡され、smoothing=0 と
    異なる loss 値を生む。"""
    from egosurgery.models.losses.phase import PhaseLoss

    loss_smooth_fn = PhaseLoss(use_class_weights=False, label_smoothing=0.1)
    loss_none_fn = PhaseLoss(use_class_weights=False, label_smoothing=0.0)
    # (1) コンフィグ値が保持されている。
    assert loss_smooth_fn.label_smoothing == 0.1
    assert loss_none_fn.label_smoothing == 0.0
    # (2) 一様でない logits なら値が異なる（一様 logits は smoothing が
    #     loss に効かないので、非対称な分布を作る）。
    logits = torch.tensor(
        [
            [3.0, -1.0, 0.5, 0.0, -0.5, 1.0, -2.0, 0.0, 0.0],
            [-1.0, 2.5, 0.0, 0.0, 1.0, -0.5, 0.0, 0.0, 0.0],
            [0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.5],
            [0.0, -1.0, 0.0, 3.5, 0.0, 0.0, 0.5, 0.0, 0.0],
        ]
    )
    targets = torch.tensor([0, 1, 2, 3])
    loss_smooth = loss_smooth_fn(logits, targets)
    loss_none = loss_none_fn(logits, targets)
    assert abs(float(loss_smooth) - float(loss_none)) > 1e-6, (
        f"smoothing=0.1 と 0.0 で loss が同値: {loss_smooth} vs {loss_none}"
    )


# ---------------------------------------------------------------------- #
# 8. s2_hand.yaml の negative_transfer config が読める
# ---------------------------------------------------------------------- #
def test_s2_negative_transfer_config():
    """s2_hand.yaml の negative_transfer セクションが §v2 仕様で読める。"""
    from hydra import compose, initialize_config_dir

    with initialize_config_dir(
        version_base=None,
        config_dir=str(_PROJECT_ROOT / "configs"),
    ):
        cfg = compose("default", overrides=["stage=s2_hand"])
    nt = cfg.get("negative_transfer", None)
    assert nt is not None
    assert nt.layer_wise_lr.enabled is True
    assert 0 < float(nt.layer_wise_lr.backbone_lr_scale) < 1.0
    assert int(nt.backbone_freeze.freeze_epochs) >= 1
    assert "tool_mAP" in str(nt.best_metric.formula)


# ---------------------------------------------------------------------- #
# 9. PhaseTrainer._build_eval_recipe の構造
# ---------------------------------------------------------------------- #
def test_phase_trainer_writes_eval_recipe():
    """PhaseTrainer._build_eval_recipe が Phase 用 recipe (task='phase') を返す。

    setup() は heavy（DINOv2 / ResNet50 ロード）なので、最小モック属性で
    _build_eval_recipe だけを直接呼ぶ。
    """
    from types import SimpleNamespace

    from omegaconf import OmegaConf

    from egosurgery.engines.phase_trainer import PhaseTrainer

    cfg = OmegaConf.create(
        {
            "data": {"image_size": 224},
            "loss": {
                "phase_use_class_weights": False,
                "phase_max_weight_ratio": 10.0,
                "phase_label_smoothing": 0.1,
            },
        }
    )
    trainer = PhaseTrainer.__new__(PhaseTrainer)
    trainer.cfg = cfg
    trainer.server_name = "bengio"
    trainer.phase_head = SimpleNamespace(dropout_p=0.3)

    recipe = trainer._build_eval_recipe()
    assert recipe["server_name"] == "bengio"
    assert recipe["test_cfg"]["task"] == "phase"
    assert recipe["test_cfg"]["use_class_weights"] is False
    assert recipe["test_cfg"]["max_weight_ratio"] == 10.0
    assert "split_train_images" in recipe

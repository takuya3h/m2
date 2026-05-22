"""Config からモデルを構築するファクトリ。

config のフラグに応じて各コンポーネント（backbone / detection_head /
phase_head ...）の有効・無効を切り替え、``nn.ModuleDict`` で束ねたモデルを
返す。S0 では backbone + detection_head のみ。

使い方:
    model = build_model(cfg)
    # S0: backbone + detection_head
    # S3 以降: + phase_head（Part 4 で実装）
    outputs = model(images, targets)

ステージ別のコンポーネント:
    - cfg.feedback.phase_to_det / det_to_phase : フィードバック経路（フェーズ III）
    - cfg.relation.enabled                     : 関係モジュール（フェーズ IV）
    - cfg.exo.enabled                          : Exo 経路（フェーズ IV）
"""

from __future__ import annotations

import warnings

import torch
from omegaconf import OmegaConf
from torch import nn

from egosurgery.models.backbones.dinov2_registry import DINOv2Backbone
from egosurgery.models.backbones.peft import apply_peft
from egosurgery.models.backbones.vit_adapter import ViTAdapter
from egosurgery.models.heads.mask_dino_head import MaskDINOHead
from egosurgery.models.heads.varifocanet_head import VarifocalNetHead


class BackboneWithAdapter(nn.Module):
    """DINOv2 backbone と ViT-Adapter を束ねた特徴抽出モジュール。"""

    def __init__(self, backbone: nn.Module, adapter: ViTAdapter) -> None:
        super().__init__()
        self.backbone = backbone
        self.adapter = adapter

    def forward(self, images: torch.Tensor) -> dict:
        """画像から マルチスケール特徴 と CLS token を返す。"""
        out = self.backbone(images)
        features = out["features"] if isinstance(out, dict) else out
        cls_token = out.get("cls_token") if isinstance(out, dict) else None
        return {"features": self.adapter(features), "cls_token": cls_token}


class EgoSurgeryModel(nn.Module):
    """backbone / detection_head 等を束ねたマルチタスクモデル。"""

    def __init__(self, components: dict) -> None:
        """
        Args:
            components: ``{"backbone": ..., "detection_head": ..., ...}``。
                値が ``None`` の要素は登録しない。
        """
        super().__init__()
        self.components = nn.ModuleDict(
            {k: v for k, v in components.items() if v is not None}
        )

    @property
    def backbone(self) -> nn.Module:
        """backbone コンポーネント。"""
        return self.components["backbone"]

    @property
    def detection_head(self) -> nn.Module | None:
        """detection_head コンポーネント（無ければ ``None``）。"""
        return self.components["detection_head"] if (
            "detection_head" in self.components
        ) else None

    def forward(self, images: torch.Tensor, targets=None) -> dict:
        """各コンポーネントを順に呼び、losses を集約して返す。

        Args:
            images: 入力画像 ``(B, 3, H, W)``。
            targets: 学習時の target（推論時は ``None``）。

        Returns:
            ``{"features", "cls_token", "losses", "detection"}``。
        """
        backbone_out = self.backbone(images)
        features = backbone_out["features"]

        losses: dict = {}
        detection = None
        head = self.detection_head
        if head is not None:
            detection = head(features, targets)
            if isinstance(detection, dict):
                losses.update(detection)

        return {
            "features": features,
            "cls_token": backbone_out.get("cls_token"),
            "losses": losses,
            "detection": detection,
        }


# --------------------------------------------------------------------- #
# コンポーネント単位のビルダ
# --------------------------------------------------------------------- #
def _resolve_component_cfg(value, group: str):
    """コンポーネント設定を解決する。

    ``value`` が文字列なら ``configs/model/{group}/{value}.yaml`` を読み込む
    （Hydra の defaults 合成を介さず ``model.backbone=name`` 形式で部品を
    指定できるようにする）。dict / DictConfig ならそのまま返す。
    """
    if isinstance(value, str):
        from pathlib import Path

        cfg_path = (
            Path(__file__).resolve().parents[3]
            / "configs" / "model" / group / f"{value}.yaml"
        )
        return OmegaConf.load(cfg_path)
    return value


def build_backbone(cfg) -> BackboneWithAdapter:
    """DINOv2 backbone + ViT-Adapter（+ PEFT）を構築する。"""
    backbone_cfg = _resolve_component_cfg(cfg.model.backbone, "backbone")
    dinov2 = DINOv2Backbone(backbone_cfg)
    # PEFT（LoRA / DoRA）を DINOv2 本体へ適用する。
    dinov2 = apply_peft(dinov2, backbone_cfg.get("peft", None))

    embed_dim = int(backbone_cfg.get("embed_dim", 1024))
    adapter = ViTAdapter(embed_dim=embed_dim, out_channels=256, num_outs=4)
    return BackboneWithAdapter(dinov2, adapter)


def build_detection_head(cfg) -> nn.Module:
    """config に応じて Mask DINO / VarifocalNet の検出ヘッドを構築する。"""
    head_cfg = _resolve_component_cfg(cfg.model.detection_head, "detection_head")
    # num_classes はモデル全体設定から注入する（tool=15 / tool+hand=19）。
    num_classes = int(cfg.model.get("num_classes", 15))
    head_cfg = OmegaConf.merge(
        OmegaConf.create(head_cfg), {"num_classes": num_classes}
    )

    name = str(head_cfg.get("name", "mask_dino")).lower()
    if name in ("varifocanet", "varifocalnet", "vfnet"):
        return VarifocalNetHead(head_cfg)
    return MaskDINOHead(head_cfg)


def build_phase_head(cfg):
    """Phase head を構築する（Part 4 で実装。現状は常に ``None``）。"""
    # phase_head 本体は Part 4 のスコープ。S0 では構築しない。
    return None


# --------------------------------------------------------------------- #
# モデル全体のビルダ
# --------------------------------------------------------------------- #
def build_model(cfg) -> EgoSurgeryModel:
    """Hydra config からマルチタスクモデルを構築する。

    Args:
        cfg: ``cfg.model.*`` を含む設定。

    Returns:
        :class:`EgoSurgeryModel`。S0 では backbone + detection_head を持つ。
    """
    backbone = build_backbone(cfg)

    detection_head = build_detection_head(cfg)
    # 検出ヘッドへ backbone 特徴の仕様を渡す（本体構築のトリガ）。
    detection_head.setup(backbone)

    components = {"backbone": backbone, "detection_head": detection_head}

    phase_head = build_phase_head(cfg)
    if phase_head is not None:
        components["phase_head"] = phase_head

    # フェーズ III / IV のコンポーネントは該当フラグが立った段階で追加する。
    if bool(cfg.get("relation", {}).get("enabled", False)):
        warnings.warn("relation モジュールは未実装です（フェーズ IV）。", RuntimeWarning)
    if bool(cfg.get("exo", {}).get("enabled", False)):
        warnings.warn("exo 経路は未実装です（フェーズ IV）。", RuntimeWarning)

    return EgoSurgeryModel(components)

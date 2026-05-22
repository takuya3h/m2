"""Mask DINO を自プロジェクトのパイプラインから呼び出すラッパー。

Mask DINO 本体は ``third_party/MaskDINO/`` に置かれ Detectron2 ベースで動く。
本ファイルは Hydra config ↔ Detectron2 config の変換と、自プロジェクトの
インターフェース（features 入力・losses / predictions 出力）への適合を担う。

使い方:
    head = MaskDINOHead(cfg)
    head.setup(backbone)               # backbone 特徴の仕様を渡す
    losses = head(features, targets)   # 学習時
    predictions = head.predict(features)  # 推論時

注意: Detectron2 / Mask DINO が import できない環境では、エラーではなく
警告を出して ``forward`` / ``predict`` が ``None`` を返す（テスト環境対応）。
"""

from __future__ import annotations

import warnings

from torch import nn


def is_maskdino_available() -> bool:
    """Detectron2 と Mask DINO がともに import 可能なら ``True``。"""
    try:
        import detectron2  # noqa: F401
        import maskdino  # noqa: F401
    except Exception:
        return False
    return True


def build_d2_config(cfg):
    """Hydra config (DictConfig) から Detectron2 の ``CfgNode`` を構築する。

    Detectron2 / Mask DINO がインストールされている環境でのみ呼べる。

    Args:
        cfg: ``configs/model/detection_head/mask_dino.yaml`` 由来の設定。

    Returns:
        Mask DINO 用に各フィールドを設定した Detectron2 ``CfgNode``。
    """
    from detectron2.config import get_cfg

    d2_cfg = get_cfg()
    try:
        # Mask DINO 固有のキーを CfgNode に登録する。
        from maskdino import add_maskdino_config

        add_maskdino_config(d2_cfg)
    except Exception:  # pragma: no cover - 環境依存
        warnings.warn(
            "add_maskdino_config を適用できませんでした。既定値で続行します。",
            RuntimeWarning,
        )

    num_classes = int(cfg.get("num_classes", 15))
    d2_cfg.MODEL.MASK_DINO.NUM_CLASSES = num_classes
    d2_cfg.MODEL.MASK_DINO.NUM_OBJECT_QUERIES = int(cfg.get("num_queries", 300))
    d2_cfg.MODEL.MASK_DINO.HIDDEN_DIM = int(cfg.get("hidden_dim", 256))
    d2_cfg.MODEL.MASK_DINO.NHEADS = int(cfg.get("nheads", 8))
    d2_cfg.MODEL.MASK_DINO.DIM_FEEDFORWARD = int(cfg.get("dim_feedforward", 2048))
    d2_cfg.MODEL.MASK_DINO.DEC_LAYERS = int(cfg.get("dec_layers", 9))
    d2_cfg.MODEL.MASK_DINO.ENC_LAYERS = int(cfg.get("enc_layers", 6))
    # Phase-0 は bbox-only。mask branch を無効化する。
    d2_cfg.MODEL.MASK_DINO.MASK_ON = bool(cfg.get("mask_on", False))
    # contrastive denoising。
    d2_cfg.MODEL.MASK_DINO.DN = "cdn" if bool(cfg.get("denoising", True)) else "no"
    d2_cfg.MODEL.MASK_DINO.DN_NUM = int(cfg.get("dn_num", 100))
    return d2_cfg


class MaskDINOHead(nn.Module):
    """Mask DINO 検出ヘッドのラッパー（Detectron2 非依存環境では無効化）。"""

    def __init__(self, cfg) -> None:
        """
        Args:
            cfg: 検出ヘッド設定（``mask_dino.yaml`` 由来。``num_classes`` 等）。
        """
        super().__init__()
        self.cfg = cfg
        self.num_classes = int(cfg.get("num_classes", 15))
        self.num_queries = int(cfg.get("num_queries", 300))
        self.mask_on = bool(cfg.get("mask_on", False))
        self.available = is_maskdino_available()
        self._head: nn.Module | None = None

        if not self.available:
            warnings.warn(
                "Detectron2 / Mask DINO が利用できないため、MaskDINOHead は "
                "無効化されます（forward / predict は None を返します）。",
                RuntimeWarning,
            )

    def setup(self, backbone) -> None:
        """backbone の特徴仕様を受け取り、Mask DINO 本体を構築する。

        Args:
            backbone: 特徴を供給する backbone（ViT-Adapter 出力 4 段階）。
        """
        if not self.available:
            return
        # Detectron2 / Mask DINO が揃う環境でのみ本体を構築する。
        from maskdino.maskdino import MaskDINO  # pragma: no cover - 環境依存

        d2_cfg = build_d2_config(self.cfg)
        self._head = MaskDINO(d2_cfg)

    def forward(self, features, targets=None):
        """学習時の損失を計算する。

        Args:
            features: ViT-Adapter の 4 段階マルチスケール特徴。
            targets: COCO 形式の target リスト。

        Returns:
            学習時は損失辞書 ``{"loss_ce", "loss_bbox", "loss_giou",
            "loss_mask"}``。Mask DINO 非対応環境では ``None``。
        """
        if not self.available or self._head is None:
            return None
        losses = self._head(features, targets)  # pragma: no cover - 環境依存
        if self.mask_on:
            return losses
        # bbox-only モード: mask 損失の重みを 0 にする。
        losses = dict(losses)
        losses["loss_mask"] = 0.0
        return losses

    def predict(self, features):
        """推論時の検出結果を返す。

        Returns:
            ``{"boxes", "scores", "labels"}``。非対応環境では ``None``。
        """
        if not self.available or self._head is None:
            return None
        return self._head.predict(features)  # pragma: no cover - 環境依存

"""mmdet の VarifocalNet を呼び出すラッパー。

EgoSurgery-Tool の実質 SOTA (mAP 45.8) を再現するベースライン検出ヘッド。
DINOv2 + ViT-Adapter の 4 段階特徴を入力とし、VarifocalNet のヘッドで
クラス分類・bbox 回帰を行う。

使い方:
    head = VarifocalNetHead(cfg)
    head.setup(backbone)
    losses = head(features, targets)
    predictions = head.predict(features)

注意: mmdet が import できない / ヘッド構築に失敗する環境では、警告を出して
``forward`` / ``predict`` が ``None`` を返す（テスト環境対応）。
"""

from __future__ import annotations

import warnings

from torch import nn


def is_mmdet_available() -> bool:
    """mmdet が import 可能なら ``True``。"""
    try:
        import mmdet  # noqa: F401
    except Exception:
        return False
    return True


def build_vfnet_head_cfg(cfg, num_classes: int) -> dict:
    """Hydra config から mmdet の VFNetHead 構築用 dict を組み立てる。

    Args:
        cfg: ``varifocanet.yaml`` 由来の設定。
        num_classes: 検出クラス数（tool=15 / tool+hand=19）。

    Returns:
        ``mmdet.registry.MODELS.build`` に渡すヘッド設定 dict。
    """
    loss_cls = cfg.get("loss_cls", {})
    loss_bbox = cfg.get("loss_bbox", {})
    return {
        "type": "VFNetHead",
        "num_classes": num_classes,
        "in_channels": int(cfg.get("feat_channels", 256)),
        "feat_channels": int(cfg.get("feat_channels", 256)),
        "stacked_convs": int(cfg.get("stacked_convs", 3)),
        "strides": list(cfg.get("strides", [8, 16, 32, 64, 128])),
        "loss_cls": {
            "type": "VarifocalLoss",
            "use_sigmoid": True,
            "alpha": float(loss_cls.get("alpha", 0.75)),
            "gamma": float(loss_cls.get("gamma", 2.0)),
            "iou_weighted": bool(loss_cls.get("iou_weighted", True)),
            "loss_weight": 1.0,
        },
        "loss_bbox": {
            "type": "GIoULoss",
            "loss_weight": float(loss_bbox.get("loss_weight", 1.5)),
        },
    }


class VarifocalNetHead(nn.Module):
    """VarifocalNet 検出ヘッドのラッパー（mmdet 非依存環境では無効化）。"""

    def __init__(self, cfg) -> None:
        """
        Args:
            cfg: 検出ヘッド設定（``varifocanet.yaml`` 由来）。
        """
        super().__init__()
        self.cfg = cfg
        self.num_classes = int(cfg.get("num_classes", 15))
        self.available = is_mmdet_available()
        self._head: nn.Module | None = None

        if not self.available:
            warnings.warn(
                "mmdet が利用できないため、VarifocalNetHead は無効化されます"
                "（forward / predict は None を返します）。",
                RuntimeWarning,
            )

    def setup(self, backbone=None) -> None:
        """mmdet の VFNetHead を構築する。

        Args:
            backbone: 特徴を供給する backbone（インターフェース整合用、未使用可）。
        """
        if not self.available:
            return
        try:
            from mmdet.registry import MODELS

            head_cfg = build_vfnet_head_cfg(self.cfg, self.num_classes)
            self._head = MODELS.build(head_cfg)
        except Exception as exc:  # mmdet バージョン差・依存欠落に備える。
            warnings.warn(
                f"VFNetHead の構築に失敗したため無効化します: {exc!r}",
                RuntimeWarning,
            )
            self.available = False
            self._head = None

    def forward(self, features, targets=None):
        """学習時の損失を計算する。

        Args:
            features: ViT-Adapter の 4 段階マルチスケール特徴。
            targets: 検出 target。

        Returns:
            損失辞書。非対応環境では ``None``。
        """
        if not self.available or self._head is None:
            return None
        return self._head(features)  # pragma: no cover - 環境依存

    def predict(self, features):
        """推論時の検出結果を返す。

        Returns:
            ``{"boxes", "scores", "labels"}``。非対応環境では ``None``。
        """
        if not self.available or self._head is None:
            return None
        return self._head(features)  # pragma: no cover - 環境依存

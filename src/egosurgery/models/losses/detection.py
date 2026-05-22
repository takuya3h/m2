"""検出用損失関数: Seesaw Loss + Focal Loss + GIoU Loss。

Seesaw Loss は mmdetection の実装から核心部分を抽出・再実装したもの。

# Adapted from: https://github.com/open-mmlab/mmdetection
# License: Apache 2.0

Seesaw Loss（Wang et al., CVPR 2021）は長尾分布の分類バイアスを 2 つの
係数で緩和する:
  - Mitigation factor : 出現頻度差に基づき、稀少クラスへの過罰を緩和する。
  - Compensation factor: 誤分類しやすいクラス対（形状類似ペア）への罰を強める。
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

_EPS = 1e-2


class SeesawLoss(nn.Module):
    """Seesaw Loss（mitigation + compensation による長尾補正 CE）。"""

    def __init__(
        self,
        p: float = 0.8,
        q: float = 2.0,
        num_classes: int = 15,
        eps: float = _EPS,
    ) -> None:
        """
        Args:
            p: mitigation factor の指数（頻度差の緩和強度）。
            q: compensation factor の指数（誤分類ペアへの罰強度）。
            num_classes: クラス数。
            eps: 数値安定化用の下限値。
        """
        super().__init__()
        self.p = float(p)
        self.q = float(q)
        self.num_classes = int(num_classes)
        self.eps = float(eps)
        # クラスごとの累積出現サンプル数（学習の進行に応じて更新）。
        self.register_buffer("cum_samples", torch.zeros(self.num_classes))

    def forward(self, cls_score: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """Seesaw 補正済みクロスエントロピーを計算する。

        Args:
            cls_score: ``(N, num_classes)`` のクラスロジット。
            labels: ``(N,)`` の正解ラベル（``0..num_classes-1``）。

        Returns:
            スカラー損失。
        """
        if cls_score.size(-1) != self.num_classes:
            raise ValueError(
                f"cls_score の最終次元 ({cls_score.size(-1)}) が "
                f"num_classes ({self.num_classes}) と一致しません。"
            )

        onehot = F.one_hot(labels, self.num_classes).to(cls_score.dtype)
        # 累積サンプル数を更新（勾配は流さない）。
        self.cum_samples = self.cum_samples + onehot.sum(dim=0).detach()

        seesaw_weights = cls_score.new_ones(cls_score.size())

        # --- Mitigation factor: 頻度差に基づく緩和 ---------------------- #
        if self.p > 0:
            sample_target = self.cum_samples[labels].clamp(min=1.0)  # (N,)
            ratio = self.cum_samples[None, :] / sample_target[:, None]  # (N, C)
            less = (ratio < 1.0).to(cls_score.dtype)
            mitigation = ratio.clamp(min=self.eps) ** self.p
            seesaw_weights = seesaw_weights * (mitigation * less + (1.0 - less))

        # --- Compensation factor: 誤分類ペアへの罰 --------------------- #
        if self.q > 0:
            scores = F.softmax(cls_score.detach(), dim=-1)
            self_score = scores.gather(1, labels[:, None]).clamp(min=self.eps)
            score_ratio = scores / self_score  # (N, C)
            greater = (score_ratio > 1.0).to(cls_score.dtype)
            compensation = score_ratio ** self.q
            seesaw_weights = seesaw_weights * (
                compensation * greater + (1.0 - greater)
            )

        # 正解クラス以外のロジットを seesaw 重みの log で調整。
        adjusted = cls_score + seesaw_weights.clamp(min=self.eps).log() * (
            1.0 - onehot
        )
        return F.cross_entropy(adjusted, labels)


class FocalLoss(nn.Module):
    """多クラス Focal Loss（Seesaw との比較用ベースライン）。"""

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0) -> None:
        """
        Args:
            alpha: 易/難サンプルのバランス係数。
            gamma: 易サンプルの寄与を抑える集中係数。
        """
        super().__init__()
        self.alpha = float(alpha)
        self.gamma = float(gamma)

    def forward(self, cls_score: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """Focal Loss を計算する。"""
        ce = F.cross_entropy(cls_score, labels, reduction="none")
        pt = torch.exp(-ce)
        loss = self.alpha * (1.0 - pt) ** self.gamma * ce
        return loss.mean()


class GIoULoss(nn.Module):
    """Generalized IoU Loss（bbox 回帰用、xyxy 形式）。"""

    def __init__(self, loss_weight: float = 1.0, eps: float = 1e-7) -> None:
        """
        Args:
            loss_weight: 損失の重み係数。
            eps: ゼロ除算回避用の微小値。
        """
        super().__init__()
        self.loss_weight = float(loss_weight)
        self.eps = float(eps)

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """要素ごとの GIoU 損失 ``mean(1 - GIoU)`` を計算する。

        Args:
            pred: ``(N, 4)`` 予測 bbox（xyxy）。
            target: ``(N, 4)`` 正解 bbox（xyxy）。
        """
        giou = _generalized_iou(pred, target, self.eps)
        return ((1.0 - giou).mean()) * self.loss_weight


def _generalized_iou(
    pred: torch.Tensor, target: torch.Tensor, eps: float
) -> torch.Tensor:
    """要素ごとの GIoU を返す（``pred``/``target`` ともに ``(N,4)`` xyxy）。"""
    # 交差領域。
    inter_x1 = torch.max(pred[:, 0], target[:, 0])
    inter_y1 = torch.max(pred[:, 1], target[:, 1])
    inter_x2 = torch.min(pred[:, 2], target[:, 2])
    inter_y2 = torch.min(pred[:, 3], target[:, 3])
    inter = (inter_x2 - inter_x1).clamp(min=0) * (inter_y2 - inter_y1).clamp(min=0)

    area_pred = (pred[:, 2] - pred[:, 0]).clamp(min=0) * (
        pred[:, 3] - pred[:, 1]
    ).clamp(min=0)
    area_target = (target[:, 2] - target[:, 0]).clamp(min=0) * (
        target[:, 3] - target[:, 1]
    ).clamp(min=0)
    union = area_pred + area_target - inter + eps
    iou = inter / union

    # 最小包含矩形。
    enclose_x1 = torch.min(pred[:, 0], target[:, 0])
    enclose_y1 = torch.min(pred[:, 1], target[:, 1])
    enclose_x2 = torch.max(pred[:, 2], target[:, 2])
    enclose_y2 = torch.max(pred[:, 3], target[:, 3])
    enclose = (enclose_x2 - enclose_x1).clamp(min=0) * (
        enclose_y2 - enclose_y1
    ).clamp(min=0) + eps

    return iou - (enclose - union) / enclose


class DetectionLoss(nn.Module):
    """分類損失 + bbox 回帰損失を統合する検出用損失。"""

    def __init__(self, cfg=None) -> None:
        """
        Args:
            cfg: 損失設定。``num_classes`` / ``cls_loss``（``"seesaw"`` または
                ``"focal"``）/ ``lambda_*`` を参照する（すべて任意）。
        """
        super().__init__()
        cfg = cfg or {}
        self.num_classes = int(cfg.get("num_classes", 15))
        cls_loss = str(cfg.get("cls_loss", "seesaw")).lower()
        if cls_loss == "focal":
            self.cls_loss = FocalLoss()
        else:
            self.cls_loss = SeesawLoss(num_classes=self.num_classes)
        self.giou_loss = GIoULoss()

        self.lambda_cls = float(cfg.get("lambda_cls", 1.0))
        self.lambda_bbox = float(cfg.get("lambda_bbox", 5.0))
        self.lambda_giou = float(cfg.get("lambda_giou", 2.0))

    def forward(self, predictions: dict, targets: dict) -> dict:
        """各損失と合計を辞書で返す。

        Args:
            predictions: ``{"cls_score": (N,C), "bbox_pred": (N,4)}``。
            targets: ``{"labels": (N,), "boxes": (N,4)}``。

        Returns:
            ``{"loss_cls", "loss_bbox", "loss_giou", "loss_total"}``。
        """
        loss_cls = self.cls_loss(predictions["cls_score"], targets["labels"])
        loss_bbox = F.l1_loss(predictions["bbox_pred"], targets["boxes"])
        loss_giou = self.giou_loss(predictions["bbox_pred"], targets["boxes"])
        loss_total = (
            self.lambda_cls * loss_cls
            + self.lambda_bbox * loss_bbox
            + self.lambda_giou * loss_giou
        )
        return {
            "loss_cls": loss_cls,
            "loss_bbox": loss_bbox,
            "loss_giou": loss_giou,
            "loss_total": loss_total,
        }

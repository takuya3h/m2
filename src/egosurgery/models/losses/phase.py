"""手術工程（phase）認識用の損失関数。

クラス不均衡対策（Dissection 44.1% / Closure 34.3% が支配的）と
過信抑制（label smoothing）を施した cross-entropy。

【§14 再発防止 / v2】class weights が不適切だと学習が崩壊する
（過去に val_acc 0.5% に崩壊した事故あり）。本実装の方針:

- ``use_class_weights=False`` をデフォルトとする（崩壊しない構成）
- 有効化時は weight の最大/最小比を ``max_weight_ratio`` で上限クリップ
- label smoothing は常に 0.1 を既定とする

使い方（推奨・v2）:
    loss_fn = PhaseLoss(num_classes=9, use_class_weights=False)
    loss = loss_fn(logits, targets)   # logits: (B, C), targets: (B,)

旧 API（v1・後方互換）:
    loss_fn = PhaseLoss(class_weights=torch.tensor([...9...]))
"""

from __future__ import annotations

import torch
from torch import nn

# 研究計画 §7 に基づく phase 頻度（学習データ上の頻度はデータから再計算するが、
# 初期値として参考に用意。`class_weights_from_frequencies` の引数として渡せる）。
# 順序は constants.PHASE_CLASSES（alphabetical）に対応:
#   0:anesthesia 1:closure 2:design 3:disinfection 4:dissection 5:dressing
#   6:hemostasis 7:incision 8:irrigation
DEFAULT_PHASE_FREQUENCIES: tuple[float, ...] = (
    0.02, 0.343, 0.02, 0.03, 0.441, 0.02, 0.05, 0.02, 0.07,
)


def _clip_weight_ratio(weights: torch.Tensor, max_ratio: float) -> torch.Tensor:
    """重みの max/min 比が ``max_ratio`` を超えないようクリップする（§14 再発防止）。

    過去に逆頻度から計算された極端な重み（最大/最小比 ~20 以上）で学習が
    崩壊した。本関数は最小値を持ち上げて比を上限に抑え、平均が 1 になるよう
    再正規化する（cross_entropy weight の慣行）。
    """
    w = weights.float().clone()
    w_min = float(w.min().item())
    w_max = float(w.max().item())
    if w_min <= 0 or w_max / w_min <= max_ratio:
        return w
    target_min = w_max / float(max_ratio)
    w = torch.clamp(w, min=target_min)
    return w * (len(w) / w.sum())


class PhaseLoss(nn.Module):
    """クラス重み付き cross-entropy + label smoothing。

    Args:
        class_weights: 9 クラスの重み（``torch.Tensor`` または ``None``）。
            旧 API: 直接重みテンソルを渡す。``use_class_weights`` より優先。
        num_classes: クラス数（既定 9）。
        class_frequencies: クラス頻度（``use_class_weights=True`` 時に
            逆頻度重みを計算する入力）。``None`` のときは
            :data:`DEFAULT_PHASE_FREQUENCIES` を使う。
        use_class_weights: ``True`` のとき逆頻度重みを内部計算する。
            **既定 False**（§14 再発防止: 不適切な weight で学習崩壊した
            事故を防ぐ）。
        max_weight_ratio: 計算された重みの最大値/最小値の比の上限。
            ``use_class_weights=True`` 時のみ適用。既定 10.0。
        label_smoothing: ラベル平滑化係数（既定 0.1、§14 で常時推奨）。
        reduction: 損失集約方法（``"mean"`` / ``"sum"`` / ``"none"``）。
    """

    def __init__(
        self,
        class_weights: torch.Tensor | None = None,
        num_classes: int = 9,
        class_frequencies: list[float] | tuple[float, ...] | None = None,
        use_class_weights: bool = False,
        max_weight_ratio: float = 10.0,
        label_smoothing: float = 0.1,
        reduction: str = "mean",
    ) -> None:
        super().__init__()
        self.num_classes = int(num_classes)
        self.use_class_weights = bool(use_class_weights)
        self.max_weight_ratio = float(max_weight_ratio)
        self.label_smoothing = float(label_smoothing)
        self.reduction = str(reduction)

        # 重みの解決順序: 旧 API（直接渡し）優先 → v2 (use_class_weights + frequencies) → なし。
        resolved: torch.Tensor | None = None
        if class_weights is not None:
            resolved = class_weights.float()
        elif self.use_class_weights:
            freqs = class_frequencies or DEFAULT_PHASE_FREQUENCIES
            resolved = class_weights_from_frequencies(freqs)
            resolved = _clip_weight_ratio(resolved, self.max_weight_ratio)

        if resolved is not None:
            # buffer として登録すると ``.to(device)`` で自動移動する。
            self.register_buffer("class_weights", resolved)
        else:
            self.class_weights = None  # type: ignore[assignment]

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """logits と target ラベルから損失を計算する。

        Args:
            logits: ``(B, C)`` の生 logits。
            targets: ``(B,)`` の整数クラスラベル（0 ≤ id < C）。

        Returns:
            スカラー損失（``reduction="mean"`` 時）または ``(B,)`` テンソル。
        """
        weight = self.class_weights if isinstance(self.class_weights, torch.Tensor) else None
        return nn.functional.cross_entropy(
            logits,
            targets,
            weight=weight,
            reduction=self.reduction,
            label_smoothing=self.label_smoothing,
        )


def class_weights_from_frequencies(
    frequencies: list[float] | tuple[float, ...] = DEFAULT_PHASE_FREQUENCIES,
    eps: float = 1e-6,
) -> torch.Tensor:
    """クラス頻度の逆数を正規化した重みテンソルを返す。

    Args:
        frequencies: 各クラスの頻度（必ずしも和が 1 で無くてもよい）。
        eps: ゼロ除算回避用の微小値。

    Returns:
        平均が 1 になるよう正規化された重み ``(C,)``。
    """
    f = torch.tensor(frequencies, dtype=torch.float32)
    inv = 1.0 / (f + eps)
    return inv * (len(f) / inv.sum())

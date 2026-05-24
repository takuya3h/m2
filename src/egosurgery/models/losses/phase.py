"""手術工程（phase）認識用の損失関数。

クラス不均衡対策（Dissection / Closure が支配的）と過信抑制（label smoothing）を
施した cross-entropy。実頻度を ``class_weights`` に渡せば逆頻度正規化された
重みでクラスバランスを取れる。

使い方:
    loss_fn = PhaseLoss(class_weights=torch.tensor([...9...]), label_smoothing=0.1)
    loss = loss_fn(logits, targets)   # logits: (B, C), targets: (B,)
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


class PhaseLoss(nn.Module):
    """クラス重み付き cross-entropy + label smoothing。

    Args:
        class_weights: 9 クラスの重み（``torch.Tensor`` または ``None``）。
            ``None`` のときは均一重み。
        label_smoothing: ラベル平滑化係数（既定 0.1）。
        reduction: 損失集約方法（``"mean"`` / ``"sum"`` / ``"none"``）。
    """

    def __init__(
        self,
        class_weights: torch.Tensor | None = None,
        label_smoothing: float = 0.1,
        reduction: str = "mean",
    ) -> None:
        super().__init__()
        self.label_smoothing = float(label_smoothing)
        self.reduction = str(reduction)
        if class_weights is not None:
            # buffer として登録すると ``.to(device)`` で自動移動する。
            self.register_buffer("class_weights", class_weights.float())
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

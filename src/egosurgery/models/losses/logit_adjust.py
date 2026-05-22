"""Post-hoc Logit Adjustment（長尾分類の補正）。

参考: Menon et al., ICLR 2021,
      "Long-tail learning via logit adjustment".

クラス頻度の対数事前分布を logit に加算することで、頻度バイアスを補正する。
学習時に損失へ組み込む使い方も、推論時に logit へ後付けする
（post-hoc）使い方も可能。

使い方:
    adjuster = LogitAdjustment(class_frequencies, tau=1.0)
    adjusted_logits = adjuster(logits)
"""

from __future__ import annotations

import torch
from torch import nn

_EPS = 1e-12


class LogitAdjustment(nn.Module):
    """クラス頻度に基づく logit 補正モジュール。"""

    def __init__(self, class_frequencies, tau: float = 1.0) -> None:
        """
        Args:
            class_frequencies: クラスごとの出現頻度（件数でも割合でも可。
                内部で正規化する）。長さ = クラス数。
            tau: 補正の強さ。``0`` で無補正。
        """
        super().__init__()
        freq = torch.as_tensor(list(class_frequencies), dtype=torch.float32)
        freq = freq.clamp(min=_EPS)
        freq = freq / freq.sum()
        self.tau = float(tau)
        # log 事前分布をバッファに保持（state_dict に含まれ device 追従する）。
        self.register_buffer("log_prior", torch.log(freq))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        """logit に ``tau * log(prior)`` を加算して返す。

        Args:
            logits: ``(..., num_classes)`` の生 logit。

        Returns:
            補正後の logit（入力と同 shape）。
        """
        return logits + self.tau * self.log_prior

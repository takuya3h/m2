"""Frame-by-frame の手術工程（phase）分類ヘッド。

入力は backbone のグローバル特徴（[CLS] token もしくは GAP ベクトル、(B, D)）。
出力は 9 クラス（``PHASE_CLASSES``）の logits ``(B, num_classes)``。

S3 では弱接続（``feedback.det_to_phase=false``）の単純ベースラインとして使用し、
S4 で時系列モデル（TCN / Transformer）へ、S5 以降で object token 入力へ
段階的に拡張する比較基準となる。

使い方:
    head = PhaseHead(input_dim=1024, num_classes=9)
    logits = head(global_feat)   # (B, 1024) -> (B, 9)
"""

from __future__ import annotations

import torch
from torch import nn


class PhaseHead(nn.Module):
    """グローバル特徴から phase logits を出す軽量 MLP ヘッド。

    構造: ``Linear(input_dim, hidden_dim) -> ReLU -> Dropout -> Linear(hidden_dim, num_classes)``

    Args:
        input_dim: 入力特徴の次元（例: DINOv2 ViT-L の [CLS] token = 1024）。
        num_classes: 出力クラス数（既定 9）。
        hidden_dim: 中間層の次元（既定 512）。
        dropout: Dropout 率（既定 0.3）。
    """

    def __init__(
        self,
        input_dim: int = 1024,
        num_classes: int = 9,
        hidden_dim: int = 512,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.input_dim = int(input_dim)
        self.num_classes = int(num_classes)
        self.hidden_dim = int(hidden_dim)
        self.dropout_p = float(dropout)

        self.fc1 = nn.Linear(self.input_dim, self.hidden_dim)
        self.act = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(self.dropout_p)
        self.fc2 = nn.Linear(self.hidden_dim, self.num_classes)

        self._init_weights()

    def _init_weights(self) -> None:
        """重みを Kaiming / 出力層を小さい分散の正規で初期化する。"""
        nn.init.kaiming_normal_(self.fc1.weight, nonlinearity="relu")
        nn.init.zeros_(self.fc1.bias)
        nn.init.normal_(self.fc2.weight, std=0.01)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """グローバル特徴 ``(B, input_dim)`` から logits ``(B, num_classes)`` を返す。

        Args:
            x: 入力テンソル ``(B, input_dim)``。3 次元以上で渡された場合は
                先頭以外の空間次元を平均プーリングして 2 次元へ整える。

        Returns:
            ``(B, num_classes)`` の生 logits（softmax 前）。
        """
        if x.dim() > 2:
            # (B, D, H, W) や (B, T, D) を (B, D) へ落とす。
            x = x.flatten(2).mean(dim=-1) if x.dim() == 4 else x.mean(dim=1)
        h = self.act(self.fc1(x))
        h = self.dropout(h)
        return self.fc2(h)

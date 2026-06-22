"""TeCNO 時系列ヘッド（causal MS-TCN）— S4 工程認識の分母（研究ピボット §4.2）。

Czempiel et al., "TeCNO: Surgical Phase Recognition with Multi-Stage Temporal
Convolutional Networks" (MICCAI 2020) の多段 TCN を、**online/causal**（未来フレーム
不使用）で実装する。入力は Stage1 で抽出した凍結 backbone 由来のフレーム特徴列。

因果性（causality）の要点:
    標準 MS-TCN の dilated conv は対称 padding で未来フレームを参照する（acausal）。
    本実装は **左側のみ padding**（``F.pad(x, (2*dilation, 0))``）し、出力時刻 t が
    入力時刻 ≤ t のみに依存するようにする。これにより §4.2「eval も未来フレーム不使用」
    と §6「online/offline を混ぜない」を**構造的に**満たす。

入出力:
    forward(x): x = (B, in_dim, T) のフレーム特徴列 →
        各ステージのロジット列のリスト [(B, num_classes, T), ...]（長さ num_stages）。
    学習時は各ステージの CE（+ 平滑化損失）を合算するのが TeCNO の標準。推論は最終
    ステージの argmax を使う。
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn


class CausalDilatedResidualLayer(nn.Module):
    """因果的 dilated 残差層（kernel=3）。出力時刻 t は入力 ≤ t のみに依存する。"""

    def __init__(self, dilation: int, n_channels: int, dropout: float = 0.5) -> None:
        super().__init__()
        self.dilation = dilation
        self.conv_dilated = nn.Conv1d(n_channels, n_channels, kernel_size=3, dilation=dilation)
        self.conv_1x1 = nn.Conv1d(n_channels, n_channels, kernel_size=1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 左に 2*dilation だけ pad（右は 0）→ kernel=3 で出力長は T のまま、出力 t は入力 ≤ t に依存
        out = F.pad(x, (2 * self.dilation, 0))
        out = F.relu(self.conv_dilated(out))
        out = self.conv_1x1(out)
        out = self.dropout(out)
        return x + out


class SingleStageTCN(nn.Module):
    """1 ステージ分の因果 TCN。dilation を 2^l で指数増加させる。"""

    def __init__(self, num_layers: int, n_channels: int, in_dim: int, num_classes: int,
                 dropout: float = 0.5) -> None:
        super().__init__()
        self.conv_in = nn.Conv1d(in_dim, n_channels, kernel_size=1)
        self.layers = nn.ModuleList(
            [CausalDilatedResidualLayer(2 ** i, n_channels, dropout) for i in range(num_layers)]
        )
        self.conv_out = nn.Conv1d(n_channels, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv_in(x)
        for layer in self.layers:
            out = layer(out)
        return self.conv_out(out)


class TeCNO(nn.Module):
    """Causal Multi-Stage TCN（TeCNO）。online 工程認識の分母。

    Args:
        num_stages: 段数（各段が前段の予測を精緻化）。
        num_layers: 1 段あたりの dilated 層数（dilation = 1,2,4,...,2^(num_layers-1)）。
        num_f_maps: 中間チャネル数。
        in_dim: 入力特徴次元（Stage1 GAP = 2048）。
        num_classes: 工程クラス数（EgoSurgery-Phase = 9）。
    """

    def __init__(self, num_stages: int = 2, num_layers: int = 8, num_f_maps: int = 64,
                 in_dim: int = 2048, num_classes: int = 9, dropout: float = 0.5) -> None:
        super().__init__()
        self.num_stages = num_stages
        self.num_classes = num_classes
        self.stage1 = SingleStageTCN(num_layers, num_f_maps, in_dim, num_classes, dropout)
        # 2 段目以降は前段の softmax 確率（num_classes 次元）を入力に取る
        self.refine_stages = nn.ModuleList(
            [SingleStageTCN(num_layers, num_f_maps, num_classes, num_classes, dropout)
             for _ in range(num_stages - 1)]
        )

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        """x: (B, in_dim, T) → 各ステージのロジット [(B, num_classes, T), ...]。"""
        out = self.stage1(x)
        outputs = [out]
        for stage in self.refine_stages:
            out = stage(F.softmax(out, dim=1))
            outputs.append(out)
        return outputs

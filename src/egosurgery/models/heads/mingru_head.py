"""minGRU 時系列ヘッド（系統② 核 T-5）— TeCNO と同一契約の drop-in 差し替え核。

Feng et al., "Were RNNs All We Need?" (arXiv:2410.01201) の **minGRU** を、TeCNO
（``tecno_head.py``）と同一の multi-stage シェルに載せた online/causal 工程認識ヘッド。
公平比較（§8.1: 同一特徴・同一 seed で「核だけ」差し替え）のため、シェル構造・引数名・
forward 契約は TeCNO と完全に一致させ、**dilated causal TCN stack の部分だけ**を minGRU の
線形再帰に置き換える。

minGRU（arXiv:2410.01201 §3.2）:
    標準 GRU から (i) 隠れ状態依存の gate/candidate を排し入力のみに依存させ、
    (ii) reset gate を削除、(iii) candidate の tanh を除いた最小 GRU。
        z_t   = σ(Linear_z(x_t))                      # update gate（入力のみ依存）
        h̃_t  = Linear_h(x_t)                          # candidate（入力のみ依存）
        h_t   = (1 − z_t) ⊙ h_{t−1} + z_t ⊙ h̃_t      # 線形再帰
    gate/candidate が入力のみに依存するため系列全体を一括前計算でき、逐次スキャンは
    上式の線形再帰のみ（O(1)/step, O(T) 全体）。本実装は正しさ優先で左→右の逐次
    再帰（sequential）で実装する。
    （並列化する場合、論文は log-space parallel scan のため candidate を正に保つ連続関数
    g(·) を導入するが、逐次形では不要なので用いない。）

因果性（causality）の要点:
    h_t は入力 x_{≤t} のみに依存する厳密 causal な再帰であり、シェルの conv_in / conv_out
    は kernel=1（時間方向に混ざらない）。したがって出力時刻 t は入力 ≤ t のみに依存し、
    §4.2「eval も未来フレーム不使用」/ §6「online/offline を混ぜない」を構造的に満たす。

入出力（TeCNO と同一）:
    forward(x): x = (B, in_dim, T) のフレーム特徴列 →
        各ステージのロジット列のリスト [(B, num_classes, T), ...]（長さ num_stages）。
    学習時は各ステージの CE（+ 平滑化損失）を合算、推論は最終ステージの argmax。
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn


class MinGRULayer(nn.Module):
    """causal minGRU 層（arXiv:2410.01201 §3.2）。残差接続は TeCNO 流儀に合わせる。

    update gate z と candidate h̃ は入力のみに依存するため系列全体を一括で前計算し、
    逐次ループは線形再帰 ``h_t = (1−z_t)⊙h_{t−1} + z_t⊙h̃_t`` のみを回す（O(1)/step）。
    出力時刻 t は入力 ≤ t だけに依存する（strict causal）。
    """

    def __init__(self, n_channels: int, dropout: float = 0.5) -> None:
        super().__init__()
        self.to_z = nn.Linear(n_channels, n_channels)
        self.to_h = nn.Linear(n_channels, n_channels)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, C)。gate / candidate は入力のみ依存なので一括前計算
        z = torch.sigmoid(self.to_z(x))          # (B, T, C) update gate ∈ (0, 1)
        h_tilde = self.to_h(x)                    # (B, T, C) candidate
        b, t, c = x.shape
        h = x.new_zeros(b, c)                     # h_0 = 0
        outs: list[torch.Tensor] = []
        for step in range(t):                     # 左→右の逐次再帰（未来非参照）
            h = (1.0 - z[:, step]) * h + z[:, step] * h_tilde[:, step]
            outs.append(h)
        out = torch.stack(outs, dim=1)            # (B, T, C)
        out = self.dropout(out)
        return x + out                            # 残差（TeCNO の residual layer に対応）


class _SingleStageMinGRU(nn.Module):
    """1 ステージ分の causal minGRU（TeCNO の ``SingleStageTCN`` に対応）。

    conv_in(in_dim→n_channels, k=1) → minGRU core（num_layers 層）→ conv_out(n_channels→num_classes, k=1)。
    再帰は時間軸を最後から 2 番目に置く (B, T, C) で行うため、内部で transpose する。
    """

    def __init__(self, num_layers: int, n_channels: int, in_dim: int, num_classes: int,
                 dropout: float = 0.5) -> None:
        super().__init__()
        self.conv_in = nn.Conv1d(in_dim, n_channels, kernel_size=1)
        self.layers = nn.ModuleList(
            [MinGRULayer(n_channels, dropout) for _ in range(num_layers)]
        )
        self.conv_out = nn.Conv1d(n_channels, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, in_dim, T)
        out = self.conv_in(x)              # (B, n_channels, T)
        out = out.transpose(1, 2)          # (B, T, n_channels) — 再帰の時間軸へ
        for layer in self.layers:
            out = layer(out)
        out = out.transpose(1, 2)          # (B, n_channels, T)
        return self.conv_out(out)          # (B, num_classes, T)


class MinGRUHead(nn.Module):
    """Multi-stage causal minGRU ヘッド（系統② 核 T-5）。TeCNO と drop-in 互換。

    シェル・引数名・forward 契約は ``tecno_head.TeCNO`` と同一。核（時系列演算）のみが
    dilated causal TCN → minGRU 線形再帰に置き換わる。

    Args:
        num_stages: 段数（各段が前段の予測を精緻化）。
        num_layers: 1 段あたりの minGRU 層数（core の層数）。
        num_f_maps: 中間チャネル数。
        in_dim: 入力特徴次元（Stage1 GAP = 2048 等）。
        num_classes: 工程クラス数（EgoSurgery-Phase = 9）。
        dropout: 各 minGRU 層の dropout。
    """

    def __init__(self, num_stages: int = 2, num_layers: int = 8, num_f_maps: int = 64,
                 in_dim: int = 2048, num_classes: int = 9, dropout: float = 0.5) -> None:
        super().__init__()
        self.num_stages = num_stages
        self.num_classes = num_classes
        self.stage1 = _SingleStageMinGRU(num_layers, num_f_maps, in_dim, num_classes, dropout)
        # 2 段目以降は前段の softmax 確率（num_classes 次元）を入力に取る（TeCNO と同一）
        self.refine_stages = nn.ModuleList(
            [_SingleStageMinGRU(num_layers, num_f_maps, num_classes, num_classes, dropout)
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

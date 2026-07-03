"""Mamba 時系列ヘッド（系統② 核 T-6）— TeCNO と同一契約の drop-in 差し替え核。

Gu & Dao, "Mamba: Linear-Time Sequence Modeling with Selective State Spaces"
(arXiv:2312.00752) の選択的状態空間モデル（selective SSM, SR-Mamba 系）を、TeCNO
（``tecno_head.py``）と同一の multi-stage シェルに載せた online/causal 工程認識ヘッド。
公平比較（§8.1: 同一特徴・同一 seed で「核だけ」差し替え）のため、シェル構造・引数名・
forward 契約は TeCNO と完全に一致させ、**dilated causal TCN stack の部分だけ**を Mamba
ブロックに置き換える。

因果性（causality）の要点:
    Mamba の選択的スキャンは左→右の再帰（h_t が入力 ≤ t のみに依存）であり、内部の
    depthwise 短 conv も causal（左 padding）である。したがって Mamba ブロックは構造的に
    strict causal。シェルの conv_in / conv_out は kernel=1（時間方向に混ざらない）ため、
    出力時刻 t は入力 ≤ t のみに依存し、§4.2 / §6 の online 制約を満たす。

依存: `mamba-ssm` / `causal-conv1d`（lecun 検証構成: mamba-ssm 2.2.2 / causal-conv1d 1.4.0）。
    未導入環境ではコンストラクタで明瞭な ImportError を送出する（研究フローを止めない）。

入出力（TeCNO と同一）:
    forward(x): x = (B, in_dim, T) のフレーム特徴列 →
        各ステージのロジット列のリスト [(B, num_classes, T), ...]（長さ num_stages）。
    学習時は各ステージの CE（+ 平滑化損失）を合算、推論は最終ステージの argmax。
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn


def _import_mamba() -> type:
    """mamba-ssm の Mamba クラスを取得。未導入なら導入手順を促す ImportError。"""
    try:
        from mamba_ssm import Mamba
    except ImportError as e:  # noqa: F841 — 元例外は from で連結
        raise ImportError(
            "MambaHead は mamba-ssm / causal-conv1d を必要とします。"
            "`pip install mamba-ssm causal-conv1d` で導入してください"
            "（lecun 検証構成: mamba-ssm 2.2.2 / causal-conv1d 1.4.0, CUDA 必須）。"
        ) from e
    return Mamba


class _MambaResidualLayer(nn.Module):
    """pre-norm 残差 Mamba 層（causal SSM）。TeCNO の残差層に対応する。

    ``x + Dropout(Mamba(LayerNorm(x)))``。Mamba は選択的スキャンで strict causal。
    """

    def __init__(self, mamba_cls: type, n_channels: int, dropout: float,
                 d_state: int, d_conv: int, expand: int) -> None:
        super().__init__()
        self.norm = nn.LayerNorm(n_channels)
        self.mamba = mamba_cls(d_model=n_channels, d_state=d_state, d_conv=d_conv, expand=expand)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, C) — Mamba は (batch, length, dim) 契約
        return x + self.dropout(self.mamba(self.norm(x)))


class _SingleStageMamba(nn.Module):
    """1 ステージ分の causal Mamba（TeCNO の ``SingleStageTCN`` に対応）。

    conv_in(in_dim→n_channels, k=1) → Mamba core（num_layers 層）→ conv_out(n_channels→num_classes, k=1)。
    Mamba は時間軸を最後から 2 番目に置く (B, T, C) で行うため、内部で transpose する。
    """

    def __init__(self, mamba_cls: type, num_layers: int, n_channels: int, in_dim: int,
                 num_classes: int, dropout: float, d_state: int, d_conv: int, expand: int) -> None:
        super().__init__()
        self.conv_in = nn.Conv1d(in_dim, n_channels, kernel_size=1)
        self.layers = nn.ModuleList(
            [_MambaResidualLayer(mamba_cls, n_channels, dropout, d_state, d_conv, expand)
             for _ in range(num_layers)]
        )
        self.conv_out = nn.Conv1d(n_channels, num_classes, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, in_dim, T)
        out = self.conv_in(x)              # (B, n_channels, T)
        out = out.transpose(1, 2)          # (B, T, n_channels) — Mamba の時間軸へ
        for layer in self.layers:
            out = layer(out)
        out = out.transpose(1, 2)          # (B, n_channels, T)
        return self.conv_out(out)          # (B, num_classes, T)


class MambaHead(nn.Module):
    """Multi-stage causal Mamba ヘッド（系統② 核 T-6）。TeCNO と drop-in 互換。

    シェル・引数名・forward 契約は ``tecno_head.TeCNO`` と同一。核（時系列演算）のみが
    dilated causal TCN → 選択的 SSM（Mamba）に置き換わる。mamba-ssm 未導入環境では
    本コンストラクタで ImportError を送出する。

    Args:
        num_stages: 段数（各段が前段の予測を精緻化）。
        num_layers: 1 段あたりの Mamba 層数（core の層数）。
        num_f_maps: 中間チャネル数（Mamba の d_model）。
        in_dim: 入力特徴次元（Stage1 GAP = 2048 等）。
        num_classes: 工程クラス数（EgoSurgery-Phase = 9）。
        dropout: 各 Mamba 層の dropout。
        d_state: Mamba SSM の状態次元（既定 16）。
        d_conv: Mamba 内 causal depthwise conv の kernel（既定 4）。
        expand: Mamba の内部拡張率（既定 2）。
    """

    def __init__(self, num_stages: int = 2, num_layers: int = 8, num_f_maps: int = 64,
                 in_dim: int = 2048, num_classes: int = 9, dropout: float = 0.5,
                 d_state: int = 16, d_conv: int = 4, expand: int = 2) -> None:
        super().__init__()
        mamba_cls = _import_mamba()  # 未導入ならここで ImportError（明瞭なメッセージ）
        self.num_stages = num_stages
        self.num_classes = num_classes
        self.stage1 = _SingleStageMamba(
            mamba_cls, num_layers, num_f_maps, in_dim, num_classes, dropout, d_state, d_conv, expand
        )
        # 2 段目以降は前段の softmax 確率（num_classes 次元）を入力に取る（TeCNO と同一）
        self.refine_stages = nn.ModuleList(
            [_SingleStageMamba(mamba_cls, num_layers, num_f_maps, num_classes, num_classes,
                               dropout, d_state, d_conv, expand)
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

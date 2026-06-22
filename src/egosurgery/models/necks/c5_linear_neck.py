"""C5 共有線形 neck（STEP B / B0-2・②特徴レベル系統の結合チャネル）。

確定事項（2026-06-18）:
    - 共有 trainable neck は **C5 のみ**に置く（(a)案）。
    - 形は **1×1 線形 neck**（norm/act 無し・2048→2048・残差・zero-init）。

なぜ 1×1 線形か（masked-GAP との可換性）:
    1×1 conv は点ごと線形なので、valid 領域の GAP（空間平均）と**交換**する::

        GAP_valid(N(C5)) == N(GAP_valid(C5))         （bias・mask 込みで厳密成立）

    よって工程枝は **既存 GAP キャッシュ（2048-d）に neck を当てるだけ**で済み、オンザフライ
    backbone forward が不要 → S4′ / B1 の工程側が S4 と同じ計算量で回る。検出枝のみ C5 spatial
    に neck を適用する（検出は元々オンザフライ forward）。spatial 適用と vector 適用で**同一の
    重み（weight/bias）を共有**するため、両経路の neck は定義上一致する。

zero-init 残差:
    weight=0 / bias=0 で初期化 → 初期は恒等（``N(x)=x``）。S0-frozen′/S4′ は学習開始時に
    neck 無し（S0-frozen/S4）と一致し、neck は残差として学習される。比較の三角形の
    「1軸（neck の有無/共有）」を初期状態で汚さない。

使い方::

    neck = C5LinearNeck(dim=2048)
    c5p = neck(c5_spatial)          # (B, 2048, H, W) -> 検出 ChannelMapper へ
    gapp = neck(cached_gap)         # (T, 2048)       -> TeCNO へ（キャッシュ流用）
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn


class C5LinearNeck(nn.Module):
    """C5 に作用する 1×1 線形 neck（spatial / vector 両適用・重み共有・残差）。

    Args:
        dim: 入出力チャネル数（C5=2048）。入出力同次元で残差を取る。
        residual: ``True`` なら ``x + Wx + b``、``False`` なら ``Wx + b``。
        zero_init: ``True`` なら weight/bias を 0 初期化（初期は恒等写像）。
    """

    def __init__(self, dim: int = 2048, residual: bool = True, zero_init: bool = True) -> None:
        super().__init__()
        self.dim = int(dim)
        self.residual = bool(residual)
        self.weight = nn.Parameter(torch.empty(self.dim, self.dim))
        self.bias = nn.Parameter(torch.empty(self.dim))
        if zero_init:
            nn.init.zeros_(self.weight)
            nn.init.zeros_(self.bias)
        else:
            nn.init.kaiming_uniform_(self.weight, a=5 ** 0.5)
            nn.init.zeros_(self.bias)

    def forward_vector(self, v: torch.Tensor) -> torch.Tensor:
        """post-GAP ベクトルに適用: ``v`` shape ``(..., dim)``（工程枝・キャッシュ流用）。"""
        out = F.linear(v, self.weight, self.bias)
        return v + out if self.residual else out

    def forward_spatial(self, x: torch.Tensor) -> torch.Tensor:
        """C5 spatial に適用: ``x`` shape ``(B, dim, H, W)``（検出枝）。"""
        w = self.weight.unsqueeze(-1).unsqueeze(-1)  # (dim, dim, 1, 1)
        out = F.conv2d(x, w, self.bias)
        return x + out if self.residual else out

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """次元数で自動振り分け: 4D=spatial / それ以外=vector。"""
        if x.dim() == 4:
            return self.forward_spatial(x)
        return self.forward_vector(x)

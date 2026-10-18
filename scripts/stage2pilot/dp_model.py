"""検出から工程（DP）の界面つき工程塔（非公式 T-2026-10-18-stage2-pilot-folda、SPEC §3）。

受け取り手は確定塔の時間ヘッド（TeCNO、candidate C、8 層）。凍結し、学習中も eval（dropout なし）で使う。
界面の重みはすべて ``iface`` の下にある。全型で最後の層を零初期化し、学習前の出力が塔単独と一致する。

    D1 concat  時間ヘッドの最初の層 stage1.conv_in（1×1 の畳み込み = 入力の線形写像）に、
               信号の次元の分の入力を零で足す（Conv1d(S, maps, 1, bias=False)、零初期化）。足した分だけを学ぶ
    D2 film    P1 と同じ式・隠れ幅・初期化の MLP（S → 64 → 2 × 2048、最後の層を零初期化）で、
               フレームごとの 2048 次元の特徴を (1 + γ) × x + β に変調する
    D3 attn    術具ごとのトークンの集合を key と value、特徴を射影したものを query にした多頭注意で一つにまとめ、
               零初期化の出力射影（d → 2048）を通して特徴に足す。トークンが 0 個のフレームは零
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

TYPES = ("concat", "film", "attn")


class FiLM(nn.Module):
    """relation_detr_phasefilm.PhaseFiLM と同じ形（隠れ幅 64、最後の層を零初期化）を 2048 次元の特徴に当てる。"""

    def __init__(self, sig_dim: int, dim: int = 2048, hidden: int = 64):
        super().__init__()
        self.dim = dim
        self.mlp = nn.Sequential(nn.Linear(sig_dim, hidden), nn.ReLU(inplace=True), nn.Linear(hidden, 2 * dim))
        nn.init.zeros_(self.mlp[-1].weight)
        nn.init.zeros_(self.mlp[-1].bias)

    def forward(self, x, s):                      # x (T, 2048), s (T, S)
        gb = self.mlp(s)
        return (1.0 + gb[:, :self.dim]) * x + gb[:, self.dim:]


class SetAttention(nn.Module):
    def __init__(self, tok_dim: int, dim: int = 2048, d: int = 64, heads: int = 4):
        super().__init__()
        self.h, self.dh = heads, d // heads
        self.q = nn.Linear(dim, d)
        self.k = nn.Linear(tok_dim, d)
        self.v = nn.Linear(tok_dim, d)
        self.out = nn.Linear(d, dim)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x, tok, mask):              # x (T, 2048), tok (T, K, D), mask (T, K) bool
        t, k = tok.shape[0], tok.shape[1]
        if k == 0:
            return x
        q = self.q(x).view(t, self.h, self.dh)
        kk = self.k(tok).view(t, k, self.h, self.dh)
        vv = self.v(tok).view(t, k, self.h, self.dh)
        att = torch.einsum("thd,tkhd->thk", q, kk) / self.dh ** 0.5
        att = att.masked_fill(~mask[:, None, :], float("-inf"))
        any_tok = mask.any(1)
        att = torch.where(any_tok[:, None, None], att, torch.zeros_like(att))
        w = torch.softmax(att, dim=-1) * any_tok[:, None, None]
        o = torch.einsum("thk,tkhd->thd", w, vv).reshape(t, -1)
        return x + self.out(o) * any_tok[:, None]


class DPReceiver(nn.Module):
    def __init__(self, head, iface_type: str, sig_dim: int, d: int = 64, heads: int = 4, hidden: int = 64):
        super().__init__()
        if iface_type not in TYPES:
            raise ValueError(iface_type)
        self.head = head
        for p in self.head.parameters():
            p.requires_grad_(False)
        self.iface_type = iface_type
        maps = head.stage1.conv_in.out_channels
        assert isinstance(head.stage1.conv_in, nn.Conv1d) and head.stage1.conv_in.kernel_size == (1,)
        if iface_type == "concat":
            self.iface = nn.Conv1d(sig_dim, maps, 1, bias=False)
            nn.init.zeros_(self.iface.weight)
        elif iface_type == "film":
            self.iface = FiLM(sig_dim, head.stage1.conv_in.in_channels, hidden)
        else:
            self.iface = SetAttention(sig_dim, head.stage1.conv_in.in_channels, d, heads)

    def train(self, mode: bool = True):
        super().train(mode)
        self.head.eval()                          # 受け取り手は凍結、dropout も切る
        return self

    def forward(self, x, s=None, mask=None):
        """x (T, 2048) の特徴列、s は (T, S) か (T, K, D)。戻り値は各段のロジット [(1, 9, T), ...]。"""
        if self.iface_type == "film" and s is not None:
            x = self.iface(x, s)
        elif self.iface_type == "attn" and s is not None:
            x = self.iface(x, s, mask)
        st = self.head.stage1
        out = st.conv_in(x.T[None])
        if self.iface_type == "concat" and s is not None:
            out = out + self.iface(s.T[None])
        for layer in st.layers:
            out = layer(out)
        out = st.conv_out(out)
        outputs = [out]
        for stage in self.head.refine_stages:
            out = stage(F.softmax(out, dim=1))
            outputs.append(out)
        return outputs

    def iface_last_params(self):
        if self.iface_type == "concat":
            return [self.iface.weight]
        if self.iface_type == "film":
            return [self.iface.mlp[-1].weight, self.iface.mlp[-1].bias]
        return [self.iface.out.weight, self.iface.out.bias]

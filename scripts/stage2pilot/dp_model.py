"""検出から工程（DP）の界面つき工程塔（非公式 T-2026-10-18-stage2-pilot-folda、SPEC §3）。

受け取り手は確定塔の時間ヘッド（TeCNO、candidate C、8 層）。凍結し、学習中も eval（dropout なし）で使う。
界面の重みはすべて ``iface`` の下にある。全型で最後の層を零初期化し、学習前の出力が塔単独と一致する。

    D1 concat  時間ヘッドの最初の層 stage1.conv_in（1×1 の畳み込み = 入力の線形写像）に、
               信号の次元の分の入力を零で足す（Conv1d(S, maps, 1, bias=False)、零初期化）。足した分だけを学ぶ
    D2 film    P1 と同じ式・隠れ幅・初期化の MLP（S → 64 → 2 × 2048、最後の層を零初期化）で、
               フレームごとの 2048 次元の特徴を (1 + γ) × x + β に変調する
    D3 attn    術具ごとのトークンの集合を key と value、特徴を射影したものを query にした多頭注意で一つにまとめ、
               零初期化の出力射影（d → 2048）を通して特徴に足す。トークンが 0 個のフレームは零

契約 T-2026-10-19-stage2-pilot-four-new-types（SPEC §3.3〜3.5）で足した型。どれも時間ヘッドの最後の段だけを変える:
    logit_corr        ℓ1 = ℓ0 + W_out GELU(W_in x + W_p softmax(ℓ0) + b)（W_out は零初期化。ℓ0 は最後の段の出力）
    tool_hist         z′ = z + tanh(α) W_o h、h = GRU(W_in x + b_in) を動画の先頭から因果的に流す（α は 0 から）。
                      z は最後の段の conv_out に入る特徴
    tool_hist_nogate  z′ = z + W_o h（W_o を零初期化。ゲートを置かない版）
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

TYPES = ("concat", "film", "attn", "logit_corr", "tool_hist", "tool_hist_nogate")
LAST_STAGE_TYPES = ("logit_corr", "tool_hist", "tool_hist_nogate")


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


class LogitCorrection(nn.Module):
    """SPEC §3.3。u = GELU(W_in x + W_p softmax(ℓ0) + b) ∈ ℝ^32、Δℓ = W_out u（W_out と bias を零初期化）。"""

    def __init__(self, sig_dim: int, num_classes: int = 9, hidden: int = 32):
        super().__init__()
        self.w_in = nn.Linear(sig_dim, hidden)                       # W_in x + b（b はここに一つだけ置く）
        self.w_p = nn.Linear(num_classes, hidden, bias=False)
        self.w_out = nn.Linear(hidden, num_classes)
        nn.init.zeros_(self.w_out.weight)
        nn.init.zeros_(self.w_out.bias)

    def forward(self, s, logits):                 # s (T, S), logits (1, 9, T)
        u = F.gelu(self.w_in(s) + self.w_p(torch.softmax(logits[0].T, dim=-1)))
        return logits + self.w_out(u).T[None]


class ToolHistory(nn.Module):
    """SPEC §3.4・3.5。h(t) = GRU(W_in x(t) + b_in, h(t−1))（1 層、64、動画の先頭で h = 0）、出力は W_o h を最後の段の z に足す分。

    gated=True はカードどおり（tanh(α)、α は 0 から、W_o は線形層の既定の初期化）。gated=False はゲートなし版（W_o と bias を零初期化）。
    """

    def __init__(self, sig_dim: int, z_dim: int = 64, hidden: int = 64, gated: bool = True):
        super().__init__()
        self.gated = gated
        self.w_in = nn.Linear(sig_dim, hidden)
        self.gru = nn.GRU(hidden, hidden, num_layers=1, batch_first=True)
        self.w_o = nn.Linear(hidden, z_dim)
        if gated:
            self.alpha = nn.Parameter(torch.zeros(()))
        else:
            nn.init.zeros_(self.w_o.weight)
            nn.init.zeros_(self.w_o.bias)

    def forward(self, s):                         # s (T, S) → (1, z_dim, T)
        h, _ = self.gru(self.w_in(s)[None])       # 打ち切らずに動画の全体を因果的に流す
        d = self.w_o(h[0])
        if self.gated:
            d = torch.tanh(self.alpha) * d
        return d.T[None]


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
        if iface_type in LAST_STAGE_TYPES:
            # SPEC §3.4 の停止条件: 最後の段（続きの段の最後）が「層の列 → conv_out（1×1）」の形で、z が一つに決まること
            assert len(head.refine_stages) > 0
            last = self.last_stage()
            assert isinstance(last.conv_out, nn.Conv1d) and last.conv_out.kernel_size == (1,), last
            assert len(last.layers) > 0, last
        if iface_type == "concat":
            self.iface = nn.Conv1d(sig_dim, maps, 1, bias=False)
            nn.init.zeros_(self.iface.weight)
        elif iface_type == "film":
            self.iface = FiLM(sig_dim, head.stage1.conv_in.in_channels, hidden)
        elif iface_type == "attn":
            self.iface = SetAttention(sig_dim, head.stage1.conv_in.in_channels, d, heads)
        elif iface_type == "logit_corr":
            self.iface = LogitCorrection(sig_dim, self.last_stage().conv_out.out_channels, 32)
        else:
            self.iface = ToolHistory(sig_dim, self.last_stage().conv_out.in_channels, 64,
                                     gated=iface_type == "tool_hist")

    def last_stage(self):
        return self.head.refine_stages[-1]

    def gate_values(self):
        """ゲートを持つ型（tool_hist）の tanh(α)。持たない型は None。"""
        if self.iface_type == "tool_hist":
            return {"tanh_alpha": float(torch.tanh(self.iface.alpha.detach()))}
        return None

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
        for i, stage in enumerate(self.head.refine_stages):
            if (self.iface_type in ("tool_hist", "tool_hist_nogate") and s is not None
                    and i == len(self.head.refine_stages) - 1):
                z = stage.conv_in(F.softmax(out, dim=1))
                for layer in stage.layers:
                    z = layer(z)
                out = stage.conv_out(z + self.iface(s))           # z(t) は最後の段の conv_out に入る特徴
            else:
                out = stage(F.softmax(out, dim=1))
            outputs.append(out)
        if self.iface_type == "logit_corr" and s is not None:
            outputs[-1] = self.iface(s, outputs[-1])               # 最後の段の出力のロジットだけを変える
        return outputs

    def iface_last_params(self):
        if self.iface_type == "concat":
            return [self.iface.weight]
        if self.iface_type == "film":
            return [self.iface.mlp[-1].weight, self.iface.mlp[-1].bias]
        if self.iface_type == "logit_corr":
            return [self.iface.w_out.weight, self.iface.w_out.bias]
        if self.iface_type == "tool_hist":
            return [self.iface.alpha]                               # 陽性対照はゲート α を零でない値にする
        if self.iface_type == "tool_hist_nogate":
            return [self.iface.w_o.weight, self.iface.w_o.bias]
        return [self.iface.out.weight, self.iface.out.bias]

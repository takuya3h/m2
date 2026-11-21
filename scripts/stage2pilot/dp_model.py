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

契約 T-2026-11-09-grasp-roitoken-transition-pilot（SPEC §3.2、案 3）で足した型:
    roitoken  把持領域トークン。各フレームの J 個（5、正解 ⊕ 予測は 10）のトークン = 枠位置の埋め込み ＋
              （枠が在れば ROI の平均の線形写像 ＋ 幾何 6 の線形写像（幾何を使う設定だけ）、無ければ学ぶ空トークン）。
              特徴 x(t)（2048）を問い合わせにした 1 層の多頭注意（4 head、K 次元）で束ね、零初期化の出力射影（K → 2048）で特徴に足す
    transwin  遷移の符号化（SPEC §3.3、案 5）。窓の k 個の時点の入力［特徴 D｜有無 1］を時点ごとの小さな MLP（D + 1 → K → K）
              ＋ 相対時刻の埋め込みで K 次元にし、x(t) を問い合わせにした 1 層の多頭注意（4 head）で束ね、零初期化の出力射影
              （K → 2048）で特徴に足す。無い時点は 0 と印 0 のまま入れる（隠さない）。k = 1 でも同じ界面

契約 T-2026-11-20-grasp-hand-graph-pilot（SPEC §4）で足した型:
    graph     術具と自分の手のグラフ（ToolHandGraph）。s (T, N + 2, 27) の行 0..N−1 が術具の節［有無 1｜特徴 23｜辺の重み 3］、
              行 N・N + 1 が自分の左手・右手の節［有無 1｜特徴 8｜0］。節の種類ごとの MLP（→ K → K）で K 次元に写し、
              辺の種類（左・右・両手）ごとに別の重みで L 段伝播し、種類ごとの平均と最大で読み出した 4K 次元を、
              零初期化の線形層（4K → 2048）で特徴に足す。節の無いフレームは読み出しが 0

契約 T-2026-11-21-grasp-hand-irn-hice-htt-pilot（SPEC §4）で足した型。入力は graph と同じ s (T, N + 2, 27)（辺の重みの 3 列は使わない）。
どれも時刻 t の 1 本のベクトル r_t（K = 64）を作り、零初期化の線形層 out（K → 2048、bias つき）で特徴に足す。入力の無いフレームは r_t = 0。
注意は 4 head。値と注意の出力の射影は bias なし（学ぶ定数を値と r_t に入れない、SPEC §4.1）。段ごとに問い合わせへ注意の出力を足し（残差）、
r_t（IRN は z_s）は各段の注意の出力の和。正規化の層は置かない。
    irn   手が問い合わせ、術具が鍵（SPEC §4.2）。q_s = e_s ＋ 手のトークン s の埋め込み、術具のトークンの埋め込みを鍵と値に L 段、
          z_s = 各段の出力の和。g_t（線形で K 次元）を問い合わせ、{z_左, z_右} を鍵と値に 1 段の出力を r_t とする
    hice  フレームが問い合わせ、手が鍵（SPEC §4.3）。ω_s = Σ_i w_is m(術具 i)（w_is = 持ち手の側 s ＋ 両手、正規化しない）、
          値 v_s = 手のトークン s の埋め込み ＋ W_ω ω_s（W_ω は bias なし）、鍵 k_s = e_s ＋ v_s。側 s の鍵は手のトークン s が在るか
          Σ_i w_is > 0 のときだけ置く。g_t を問い合わせに L 段、r_t = 各段の出力の和
    htt   フレームごとの一つのトークン（SPEC §4.4）。x_t（76）= ［術具の在否 15｜左手 8｜右手 8｜持つ器具のクラス 左・右・両手 各 15］を、
          隠れ層 L 段・幅 K の MLP（最後に K → K の線形）で写して r_t。術具のトークンも手のトークンも無いフレームは r_t = 0
"""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

TYPES = ("concat", "film", "attn", "logit_corr", "tool_hist", "tool_hist_nogate", "roitoken", "transwin", "graph",
         "irn", "hice", "htt")
TOKEN_TYPES = ("irn", "hice", "htt")                     # 契約 T-2026-11-21-grasp-hand-irn-hice-htt-pilot の型（入力は graph と同じ）
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


class RoiTokens(nn.Module):
    """SPEC §3.2。s (T, J, C + 7) = ［ROI の平均 C｜幾何 6｜有無 1］。無いトークンは学ぶ空トークン（枠位置ごと）。"""

    def __init__(self, tok_dim: int, slots: int, use_geo: bool, dim: int = 2048, k: int = 64, heads: int = 4):
        super().__init__()
        self.c, self.h, self.dh = tok_dim, heads, k // heads
        self.content = nn.Linear(tok_dim, k)
        self.geo = nn.Linear(6, k) if use_geo else None
        self.slot = nn.Parameter(torch.randn(slots, k) * 0.02)
        self.empty = nn.Parameter(torch.randn(slots, k) * 0.02)
        self.q = nn.Linear(dim, k)
        self.k = nn.Linear(k, k)
        self.v = nn.Linear(k, k)
        self.out = nn.Linear(k, dim)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x, s):                      # x (T, 2048), s (T, J, C + 7)
        t, j = s.shape[0], s.shape[1]
        e = self.content(s[..., :self.c])
        if self.geo is not None:
            e = e + self.geo(s[..., self.c:self.c + 6])
        present = s[..., self.c + 6:self.c + 7] > 0.5
        tok = torch.where(present, e, self.empty[None]) + self.slot[None]
        q = self.q(x).view(t, self.h, self.dh)
        kk = self.k(tok).view(t, j, self.h, self.dh)
        vv = self.v(tok).view(t, j, self.h, self.dh)
        w = torch.softmax(torch.einsum("thd,tjhd->thj", q, kk) / self.dh ** 0.5, dim=-1)
        o = torch.einsum("thj,tjhd->thd", w, vv).reshape(t, -1)
        return x + self.out(o)


class TransWindow(nn.Module):
    """SPEC §3.3。s (T, k, D + 1) = 窓の各時点の［特徴 D｜有無 1］（時点 0 が t、1 が t − Δ、…）。"""

    def __init__(self, in_dim: int, slots: int, dim: int = 2048, k: int = 64, heads: int = 4):
        super().__init__()
        self.h, self.dh = heads, k // heads
        self.mlp = nn.Sequential(nn.Linear(in_dim, k), nn.ReLU(inplace=True), nn.Linear(k, k))
        self.rel = nn.Parameter(torch.randn(slots, k) * 0.02)
        self.q = nn.Linear(dim, k)
        self.k = nn.Linear(k, k)
        self.v = nn.Linear(k, k)
        self.out = nn.Linear(k, dim)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def forward(self, x, s):                      # x (T, 2048), s (T, k, D + 1)
        t, j = s.shape[0], s.shape[1]
        tok = self.mlp(s) + self.rel[None]
        q = self.q(x).view(t, self.h, self.dh)
        kk = self.k(tok).view(t, j, self.h, self.dh)
        vv = self.v(tok).view(t, j, self.h, self.dh)
        w = torch.softmax(torch.einsum("thd,tjhd->thj", q, kk) / self.dh ** 0.5, dim=-1)
        o = torch.einsum("thj,tjhd->thd", w, vv).reshape(t, -1)
        return x + self.out(o)


class ToolHandGraph(nn.Module):
    """SPEC §4.3（契約 T-2026-11-20-grasp-hand-graph-pilot）。s (T, N + 2, 27)。

    術具の行 = ［有無 1｜クラス 15・得点 1・枠 4・持ち手 3｜辺の重み 3（左・右・両手の種類）］、手の行 = ［有無 1｜側 2・得点 1・枠 4・面積 1｜0］。
    辺の種類 e の隣接 A_e (T, N, 2): 左は術具 → 左手、右は術具 → 右手、両手は術具 → 左手と右手の両方。手の無い側の辺は 0。
    伝播（L 段）: h_t ← (h_t + ReLU(Σ_e A_e W^{ht}_e h_h))、h_h ← (h_h + ReLU(Σ_e A_eᵀ W^{th}_e h_t))、無い節は 0 のまま。
    読み出し: 術具・手それぞれの在る節の平均と最大（無ければ 0）を並べた 4K。出力射影（4K → 2048）は零初期化。
    """

    TOOL_F, HAND_F, EDGE_T = 23, 8, 3

    def __init__(self, n_tools: int, layers: int, dim: int = 2048, k: int = 64):
        super().__init__()
        self.n, self.layers, self.k = n_tools, layers, k
        self.enc_t = nn.Sequential(nn.Linear(self.TOOL_F, k), nn.ReLU(inplace=True), nn.Linear(k, k))
        self.enc_h = nn.Sequential(nn.Linear(self.HAND_F, k), nn.ReLU(inplace=True), nn.Linear(k, k))
        self.ht = nn.ModuleList([nn.ModuleList([nn.Linear(k, k) for _ in range(self.EDGE_T)]) for _ in range(layers)])
        self.th = nn.ModuleList([nn.ModuleList([nn.Linear(k, k) for _ in range(self.EDGE_T)]) for _ in range(layers)])
        self.out = nn.Linear(4 * k, dim)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    @staticmethod
    def _readout(h, present):                     # h (T, M, K)、present (T, M) bool → (T, 2K)
        p = present[..., None].to(h.dtype)
        cnt = p.sum(1).clamp_min(1.0)
        mean = (h * p).sum(1) / cnt
        mx = torch.where(present[..., None], h, torch.full_like(h, float("-inf"))).amax(1)
        mx = torch.where(present.any(1)[:, None], mx, torch.zeros_like(mx))
        return torch.cat([mean, mx], -1)

    def adjacency(self, s):
        """辺の種類ごとの隣接 (T, 3, N, 2)。術具・手の有無で切る。"""
        n = self.n
        tp, hp = s[:, :n, 0] > 0.5, s[:, n:n + 2, 0] > 0.5
        e = s[:, :n, 1 + self.TOOL_F:1 + self.TOOL_F + self.EDGE_T] * tp[..., None].to(s.dtype)     # (T, N, 3)
        z = torch.zeros_like(e[..., :1])
        a = torch.stack([torch.cat([e[..., 0:1], z], -1), torch.cat([z, e[..., 1:2]], -1),
                         torch.cat([e[..., 2:3], e[..., 2:3]], -1)], 1)                             # (T, 3, N, 2)
        return a * hp[:, None, None, :].to(s.dtype), tp, hp

    def forward(self, x, s):                      # x (T, 2048)、s (T, N + 2, 27)
        n = self.n
        a, tp, hp = self.adjacency(s)
        ht = self.enc_t(s[:, :n, 1:1 + self.TOOL_F]) * tp[..., None].to(x.dtype)
        hh = self.enc_h(s[:, n:n + 2, 1:1 + self.HAND_F]) * hp[..., None].to(x.dtype)
        for layer in range(self.layers):
            mt = sum(torch.einsum("tns,tsk->tnk", a[:, e], self.ht[layer][e](hh)) for e in range(self.EDGE_T))
            mh = sum(torch.einsum("tns,tnk->tsk", a[:, e], self.th[layer][e](ht)) for e in range(self.EDGE_T))
            ht = (ht + F.relu(mt)) * tp[..., None].to(x.dtype)
            hh = (hh + F.relu(mh)) * hp[..., None].to(x.dtype)
        r = torch.cat([self._readout(ht, tp), self._readout(hh, hp)], -1)
        return x + self.out(r)


def masked_attention(q, k, v, mask, heads):
    """多頭の注意の重みつきの和。q (T, Q, K)、k・v (T, M, K)、mask (T, M) bool → (T, Q, K)。鍵の無いフレームは 0（非数を出さない）。"""
    t, nq, kd = q.shape
    m = k.shape[1]
    if m == 0:
        return q.new_zeros(t, nq, kd)
    dh = kd // heads
    att = torch.einsum("tqhd,tmhd->tqhm", q.view(t, nq, heads, dh), k.view(t, m, heads, dh)) / dh ** 0.5
    att = att.masked_fill(~mask[:, None, None, :], float("-inf"))
    any_k = mask.any(1)[:, None, None, None]
    att = torch.where(any_k, att, torch.zeros_like(att))
    w = torch.softmax(att, dim=-1) * any_k.to(q.dtype)
    return torch.einsum("tqhm,tmhd->tqhd", w, v.view(t, m, heads, dh)).reshape(t, nq, kd)


class CrossAttention(nn.Module):
    """cross attention 1 段。値と出力の射影は bias なし（SPEC §4.1: 学ぶ定数を注意の値と r_t に入れない）。"""

    def __init__(self, k: int, heads: int):
        super().__init__()
        self.heads = heads
        self.q = nn.Linear(k, k)
        self.k = nn.Linear(k, k)
        self.v = nn.Linear(k, k, bias=False)
        self.o = nn.Linear(k, k, bias=False)

    def forward(self, q, key, value, mask):
        return self.o(masked_attention(self.q(q), self.k(key), self.v(value), mask, self.heads))


def _mlp(i, k):
    return nn.Sequential(nn.Linear(i, k), nn.ReLU(inplace=True), nn.Linear(k, k))


class _TokenIface(nn.Module):
    """irn・hice・htt の共通部分。s (T, N + 2, 27) の列: 術具の行 ［有無 0｜クラス 1..15・得点 16・枠 17..20・持ち手 21..23（左・右・両手）｜辺 24..26］、
    手の行 ［有無 0｜側 1..2・得点 3・枠 4..7・面積 8｜0］。出力射影 out（K → 2048）は零初期化。"""

    TOOL_F, HAND_F = 23, 8

    def __init__(self, n_tools: int, dim: int, k: int):
        super().__init__()
        self.n, self.k = n_tools, k
        self.out = nn.Linear(k, dim)
        nn.init.zeros_(self.out.weight)
        nn.init.zeros_(self.out.bias)

    def parts(self, s):
        n = self.n
        tp, hp = s[:, :n, 0] > 0.5, s[:, n:n + 2, 0] > 0.5
        return tp, hp, s[:, :n, 1:1 + self.TOOL_F], s[:, n:n + 2, 1:1 + self.HAND_F]

    def forward(self, x, s):                      # x (T, 2048)、s (T, N + 2, 27)
        return x + self.out(self.readout(x, s))


class IRNIface(_TokenIface):
    """SPEC §4.2（手が問い合わせ、術具が鍵）。"""

    def __init__(self, n_tools: int, layers: int, dim: int = 2048, k: int = 64, heads: int = 4):
        super().__init__(n_tools, dim, k)
        self.enc_t = _mlp(self.TOOL_F, k)
        self.enc_h = _mlp(self.HAND_F, k)
        self.side = nn.Parameter(torch.randn(2, k) * 0.02)          # e_s（左・右）
        self.inter = nn.ModuleList([CrossAttention(k, heads) for _ in range(layers)])
        self.g = nn.Linear(dim, k)
        self.agg = CrossAttention(k, heads)

    def counts(self, s):
        tp, _, _, _ = self.parts(s)
        return {"queries": torch.full_like(tp[:, 0], 2, dtype=torch.long), "keys": tp.sum(1),
                "agg_queries": torch.ones_like(tp[:, 0], dtype=torch.long), "agg_keys": 2 * tp.any(1).long()}

    def readout(self, x, s):
        tp, hp, tf, hf = self.parts(s)
        ht = self.enc_t(tf) * tp[..., None].to(x.dtype)
        q = self.side[None] + self.enc_h(hf) * hp[..., None].to(x.dtype)            # (T, 2, K)
        z = torch.zeros_like(q)
        for blk in self.inter:
            a = blk(q, ht, ht, tp)                                                  # 術具が無いフレームは 0
            q, z = q + a, z + a
        zmask = tp.any(1)[:, None].expand(-1, 2)
        return self.agg(self.g(x)[:, None], z, z, zmask)[:, 0]


class HiCEIface(_TokenIface):
    """SPEC §4.3（フレームが問い合わせ、手が鍵）。"""

    def __init__(self, n_tools: int, layers: int, dim: int = 2048, k: int = 64, heads: int = 4):
        super().__init__(n_tools, dim, k)
        self.m = _mlp(self.TOOL_F - 3, k)                           # 持ち手を除いた術具のトークン（クラス・得点・枠）
        self.enc_h = _mlp(self.HAND_F, k)
        self.w_omega = nn.Linear(k, k, bias=False)                  # ω_s の埋め込み（ω = 0 なら 0）
        self.side = nn.Parameter(torch.randn(2, k) * 0.02)          # e_s（左・右）
        self.g = nn.Linear(dim, k)
        self.blocks = nn.ModuleList([CrossAttention(k, heads) for _ in range(layers)])

    def keys(self, s):
        """側の値 v_s (T, 2, K) と鍵の在否 (T, 2)。"""
        tp, hp, tf, hf = self.parts(s)
        hold = tf[..., 20:23] * tp[..., None].to(s.dtype)
        w = torch.stack([hold[..., 0] + hold[..., 2], hold[..., 1] + hold[..., 2]], -1)     # (T, N, 2)
        omega = torch.einsum("tns,tnk->tsk", w, self.m(tf[..., :20]) * tp[..., None].to(s.dtype))
        value = self.enc_h(hf) * hp[..., None].to(s.dtype) + self.w_omega(omega)
        return value, hp | (w.sum(1) > 0)

    def counts(self, s):
        _, kp = self.keys(s)
        return {"queries": torch.ones_like(kp[:, 0], dtype=torch.long), "keys": kp.sum(1)}

    def readout(self, x, s):
        value, kp = self.keys(s)
        key = self.side[None] + value
        u = self.g(x)[:, None]
        r = torch.zeros_like(u)
        for blk in self.blocks:
            a = blk(u, key, value, kp)
            u, r = u + a, r + a
        return r[:, 0]


class HTTIface(_TokenIface):
    """SPEC §4.4（フレームごとの一つのトークン）。"""

    IN = 76

    def __init__(self, n_tools: int, layers: int, dim: int = 2048, k: int = 64):
        super().__init__(n_tools, dim, k)
        mods, i = [], self.IN
        for _ in range(layers):
            mods += [nn.Linear(i, k), nn.ReLU(inplace=True)]
            i = k
        self.mlp = nn.Sequential(*mods, nn.Linear(k, k))

    def vector(self, s):
        """x_t (T, 76) と入力の在否 (T,)。"""
        tp, hp, tf, hf = self.parts(s)
        onehot = tf[..., :15] * tp[..., None].to(s.dtype)
        p = (onehot * tf[..., 15:16]).amax(1)                                       # クラスごとの得点の最大
        c = (onehot[..., None] * tf[:, :, None, 20:23]).amax(1)                     # (T, 15, 3) クラスごとの持ち手の側 s の最大
        hands = (hf * hp[..., None].to(s.dtype)).reshape(len(s), -1)                # 左 8・右 8
        return torch.cat([p, hands, c[..., 0], c[..., 1], c[..., 2]], -1), tp.any(1) | hp.any(1)

    def counts(self, s):
        v, present = self.vector(s)
        return {"dim": torch.full_like(present, v.shape[1], dtype=torch.long), "present": present.long()}

    def readout(self, x, s):
        v, present = self.vector(s)
        return self.mlp(v) * present[:, None].to(x.dtype)


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
    def __init__(self, head, iface_type: str, sig_dim: int, d: int = 64, heads: int = 4, hidden: int = 64, rt=None, tw=None,
                 gr=None):
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
        elif iface_type == "roitoken":
            self.iface = RoiTokens(rt["tok_dim"], rt["slots"], rt["use_geo"], head.stage1.conv_in.in_channels,
                                   rt["k"], heads)
        elif iface_type == "transwin":
            self.iface = TransWindow(sig_dim, tw["slots"], head.stage1.conv_in.in_channels, tw["k"], heads)
        elif iface_type == "graph":
            self.iface = ToolHandGraph(gr["n_tools"], gr["layers"], head.stage1.conv_in.in_channels, gr["k"])
        elif iface_type in ("irn", "hice"):
            cls = IRNIface if iface_type == "irn" else HiCEIface
            self.iface = cls(gr["n_tools"], gr["layers"], head.stage1.conv_in.in_channels, gr["k"], heads)
        elif iface_type == "htt":
            self.iface = HTTIface(gr["n_tools"], gr["layers"], head.stage1.conv_in.in_channels, gr["k"])
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
        elif self.iface_type in ("roitoken", "transwin", "graph") + TOKEN_TYPES and s is not None:
            x = self.iface(x, s)                  # mask は行の印（参照段の学ぶ・測る行）で、界面は使わない
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

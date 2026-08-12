"""C5LinearNeck の検証（STEP B / B0-2）。

核心は **GAP 可換性**: 工程枝（vector 適用）と検出枝（spatial 適用→GAP）が同一 neck で
一致すること。これが成り立つから「工程枝は GAP キャッシュ流用、検出枝は C5 spatial」を
同じ重みで両立でき、② 系統の neck が単一定義になる。
"""
from __future__ import annotations

import torch

from egosurgery.models.necks import C5LinearNeck


def test_zero_init_is_identity():
    neck = C5LinearNeck(dim=16, zero_init=True)
    x = torch.randn(2, 16, 5, 7)
    assert torch.allclose(neck.forward_spatial(x), x)
    v = torch.randn(4, 16)
    assert torch.allclose(neck.forward_vector(v), v)


def test_forward_dispatch_by_ndim():
    neck = C5LinearNeck(dim=16, zero_init=True)
    assert neck(torch.randn(2, 16, 5, 7)).dim() == 4   # spatial
    assert neck(torch.randn(4, 16)).dim() == 2          # vector


def test_gap_commutation_with_nonzero_weights():
    """GAP_valid(N(C5)) == N(GAP_valid(C5))（full-valid GAP = 空間平均）。"""
    torch.manual_seed(0)
    neck = C5LinearNeck(dim=32, residual=True)
    # 非自明な重みを入れて可換性を実証（zero-init では自明に通るため）。
    with torch.no_grad():
        neck.weight.copy_(torch.randn(32, 32) * 0.1)
        neck.bias.copy_(torch.randn(32) * 0.1)
    c5 = torch.randn(3, 32, 6, 9)
    gap_then_neck = neck.forward_vector(c5.mean(dim=(2, 3)))     # N(GAP(C5))
    neck_then_gap = neck.forward_spatial(c5).mean(dim=(2, 3))    # GAP(N(C5))
    assert torch.allclose(gap_then_neck, neck_then_gap, atol=1e-5)


def test_residual_flag():
    neck = C5LinearNeck(dim=8, residual=False)
    with torch.no_grad():
        neck.weight.zero_()
        neck.bias.copy_(torch.ones(8))
    v = torch.randn(2, 8)
    # residual=False かつ weight=0,bias=1 -> 出力は全要素 1（入力非依存）
    assert torch.allclose(neck.forward_vector(v), torch.ones(2, 8))


def test_param_count_and_grad():
    neck = C5LinearNeck(dim=64)
    n_params = sum(p.numel() for p in neck.parameters())
    assert n_params == 64 * 64 + 64                      # weight + bias
    out = neck.forward_spatial(torch.randn(1, 64, 4, 4)).sum()
    out.backward()
    assert neck.weight.grad is not None

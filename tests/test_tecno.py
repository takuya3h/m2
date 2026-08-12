"""TeCNO（causal MS-TCN）時系列ヘッドのテスト。

最重要は **causality（因果性）**: online/causal 工程認識（研究ピボット §4.2）では
出力時刻 t が入力 ≤ t のみに依存しなければならない。未来フレームを変えても過去の
出力が変わらないことを検証する（acausal な実装ならここで落ちる）。

実行: PYTHONPATH=src pytest tests/test_tecno.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_tecno_output_shapes():
    """forward は num_stages 個の (B, num_classes, T) ロジットを返す。"""
    from egosurgery.models.heads.tecno_head import TeCNO

    model = TeCNO(num_stages=2, num_layers=6, num_f_maps=32, in_dim=2048, num_classes=9).eval()
    x = torch.randn(2, 2048, 40)
    with torch.no_grad():
        outs = model(x)
    assert isinstance(outs, list) and len(outs) == 2
    for o in outs:
        assert o.shape == (2, 9, 40)
        assert not torch.isnan(o).any()


def test_tecno_is_causal():
    """未来フレームの変更が過去の出力に影響しない（online/causal の構造的保証）。"""
    from egosurgery.models.heads.tecno_head import TeCNO

    torch.manual_seed(0)
    model = TeCNO(num_stages=2, num_layers=6, num_f_maps=32, in_dim=2048, num_classes=9).eval()
    T, t_cut = 60, 35
    x = torch.randn(1, 2048, T)
    with torch.no_grad():
        out_a = model(x)
        x2 = x.clone()
        x2[..., t_cut:] = torch.randn(1, 2048, T - t_cut)  # 未来だけ差し替え
        out_b = model(x2)

    for s in range(len(out_a)):
        # t_cut より前: 未来入力の変更に対して不変であるべき
        assert torch.allclose(out_a[s][..., :t_cut], out_b[s][..., :t_cut], atol=1e-5), (
            f"stage {s}: 過去出力が未来入力に依存している（acausal）"
        )
        # t_cut 以降: 入力が変わったので出力も変わるはず（テストの健全性チェック）
        assert not torch.allclose(out_a[s][..., t_cut:], out_b[s][..., t_cut:], atol=1e-5)


def test_tecno_variable_length():
    """可変長シーケンス（動画ごとにフレーム数が異なる）を扱える。"""
    from egosurgery.models.heads.tecno_head import TeCNO

    model = TeCNO(num_stages=2, num_layers=4, num_f_maps=16, in_dim=2048, num_classes=9).eval()
    with torch.no_grad():
        for length in (1, 7, 123):
            out = model(torch.randn(1, 2048, length))
            assert out[-1].shape == (1, 9, length)

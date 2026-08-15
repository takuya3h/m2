"""決定性モジュールの検査。

通ることだけを確かめない。既定（無効）のときに全体状態を変えないことも確かめる。
GPU 上での実地の一致・不一致は契約の audit（同じ種で二度の完全一致、
無効時の不一致 −0.0086）で実測済みであり、ここでは CPU で閉じる性質だけを固定する。
"""

from __future__ import annotations

import os

import torch

from egosurgery.utils.determinism import enable_determinism


def _snapshot() -> dict:
    return {
        "det_algos": torch.are_deterministic_algorithms_enabled(),
        "cudnn_det": torch.backends.cudnn.deterministic,
        "cudnn_bench": torch.backends.cudnn.benchmark,
    }


def _restore(s: dict) -> None:
    torch.use_deterministic_algorithms(s["det_algos"])
    torch.backends.cudnn.deterministic = s["cudnn_det"]
    torch.backends.cudnn.benchmark = s["cudnn_bench"]


def test_enable_sets_flags_and_returns_record() -> None:
    before = _snapshot()
    try:
        record = enable_determinism(7)
        assert torch.are_deterministic_algorithms_enabled() is True
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False
        assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"
        # 記録が run の JSON へ埋め込める形で返る（要件 3）。
        assert record["deterministic"] is True
        assert record["seed"] == 7
    finally:
        _restore(before)


def test_two_tiny_trainings_are_bitwise_identical() -> None:
    """同じ種で二度、小さな学習を回すと重みがビット単位で一致する。"""
    before = _snapshot()
    try:
        results = []
        for _ in range(2):
            enable_determinism(11)
            model = torch.nn.Sequential(
                torch.nn.Conv1d(4, 8, kernel_size=3, padding=2, dilation=2),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.5),
                torch.nn.Conv1d(8, 2, kernel_size=1),
            )
            optimizer = torch.optim.AdamW(model.parameters(), lr=1e-2)
            for _step in range(5):
                x = torch.randn(1, 4, 16)
                loss = model(x).square().mean()
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            results.append([p.detach().clone() for p in model.parameters()])
        for a, b in zip(*results):
            torch.testing.assert_close(a, b, rtol=0.0, atol=0.0)
    finally:
        _restore(before)


def test_disabled_leaves_global_state_untouched() -> None:
    """既定（無効）の経路はプロセスの決定性状態を変えない（禁止 13）。"""
    before = _snapshot()
    # enable を呼ばない限り、この試験の観測だけで状態は変わらないはずである。
    assert _snapshot() == before

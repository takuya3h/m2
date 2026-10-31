"""把持の信号の関数の試験（非公式 T-2026-10-31-grasp-pilot-probe、Task C-2）。答えを手で決めた人工のマスクを当てる。"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from grasppilot import grasp_signals as G  # noqa: E402


def _rect(h, w, y0, y1, x0, x1, v=1.0):
    m = np.zeros((h, w), np.float32)
    m[y0:y1, x0:x1] = v
    return m


def test_g_rectangles_known_values():
    h, w = 10, 20
    ch = {"hand_L": _rect(h, w, 0, 1, 0, 1), "tool_L": _rect(h, w, 2, 4, 4, 8),     # 2×4 = 8 画素、中心 (6, 3)
          "tool_B": _rect(h, w, 0, 10, 10, 20)}                                        # 右半分 100 画素
    g = G.summary_g(ch)
    assert g.shape == (14,)
    np.testing.assert_allclose(g[:5], [1, 1, 8 / 200, 6 / 20, 3 / 10], atol=1e-6)
    np.testing.assert_allclose(g[5:10], [0, 0, 0, 0, 0])                               # 右手は何も無い
    np.testing.assert_allclose(g[10:], [1, 0.5, 15 / 20, 5 / 10], atol=1e-6)


def test_g_probability_matches_definition():
    h, w = 4, 4
    p = np.zeros((h, w), np.float32)
    p[0, 0], p[3, 3] = 0.2, 0.6
    g = G.summary_g({"tool_R": p})
    assert abs(g[6] - 0.6) < 1e-6                                                      # 存在 = 最大
    assert abs(g[7] - 0.8 / 16) < 1e-6                                                 # 面積 = 和 ÷ 画素数
    assert abs(g[8] - (0.2 * 0.5 + 0.6 * 3.5) / 0.8 / 4) < 1e-6                        # 重み付きの重心


def test_empty_masks_give_zero():
    assert not G.summary_g({}).any()
    assert not G.summary_g({"tool_L": np.zeros((5, 5), np.float32)}).any()


def test_box_ratios_and_state():
    h, w = 10, 10
    ch = {"tool_L": _rect(h, w, 0, 10, 0, 5), "tool_R": _rect(h, w, 0, 10, 5, 10)}
    boxes = [[0, 0, 10, 10], [0, 0, 4, 4], [6, 6, 2, 2], [0, 0, 5.5, 2]]
    r = G.box_ratios(ch, boxes, h, w)
    np.testing.assert_allclose(r[0], [0.5, 0.5, 0])
    np.testing.assert_allclose(r[1], [1, 0, 0])
    np.testing.assert_allclose(r[2], [0, 1, 0])
    np.testing.assert_allclose(r[3], [10 / 12, 2 / 12, 0])                             # 端の画素を含めて 6 列 × 2 行
    q, s, over = G.box_state(r, 0.1)
    np.testing.assert_allclose(q[:, 3], [0, 0, 0, 0])
    assert list(s[1:]) == [0, 1, 0] and over == 0
    q, s, _ = G.box_state(np.array([[0.04, 0.0, 0.0], [0.6, 0.0, 0.7]]), 0.05)
    assert list(s) == [3, 2]
    np.testing.assert_allclose(q[1], [0.6, 0, 0.7, 0])                                 # Σ が 1 を超えたら 1 で切る
    assert G.box_state(np.array([[0.6, 0.0, 0.7]]), 0.1)[2] == 1


def test_empty_box_state_is_none():
    r = G.box_ratios({}, [[0, 0, 3, 3]], 5, 5)
    q, s, _ = G.box_state(r, 0.1)
    assert not r.any() and s[0] == 3 and q[0, 3] == 1

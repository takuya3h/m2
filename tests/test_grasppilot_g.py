"""非公式 T-2026-11-01-grasp-pilot-g の G の注釈と教師の標的の関数（人工の入力）。"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from grasppilot import g38_build as B  # noqa: E402

torch = pytest.importorskip("torch")
from grasppilot import g_signals as S  # noqa: E402


def test_g38_class_table_has_38_unique_classes():
    assert len(B.SOURCES) == 38 and len(set(B.CLASS_OF.values())) == 38
    assert B.CLASS_OF[("hand_tool_seg", 1)] == 1 and B.CLASS_OF[("hand_seg", 3)] == 6 and B.CLASS_OF[("tool_seg", 31)] == 38
    assert ("hand_seg", 1) not in B.CLASS_OF and ("hand_seg", 2) not in B.CLASS_OF   # 自分の手は把持関係の 1・2 で一度だけ


def test_g38_restore_inverts_mapping():
    anns = [{"category_id": B.CLASS_OF[k], "segmentation": f"seg{i}"} for i, k in enumerate(B.SOURCES)]
    assert sorted(B.restore(anns, "tool_seg")) == [(c, f"seg{7 + c - 1}") for c in range(1, 32)]
    # hand_seg は 1・2 を把持関係の 1・2 から、3・4 を他者の手から戻す
    assert sorted(B.restore(anns, "hand_seg")) == [(1, "seg0"), (2, "seg1"), (3, "seg5"), (4, "seg6")]
    assert sorted(B.restore(anns, "hand_tool_seg")) == [(c, f"seg{c - 1}") for c in range(1, 6)]


def _names():
    tools = ["BiClamp", "Bipolar Forceps"] + [f"T{i}" for i in range(29)]
    return ["grasp:a"] * 5 + ["hand:b"] * 2 + [f"tool:{n}" for n in tools]


def test_t_target_splits_mass_by_overlap_and_sums_to_one():
    P = torch.zeros((5, 4, 4))
    P[2, :2, :] = 0.8                         # 左手の器具（max 0.8）
    masks = torch.zeros((2, 4, 4))
    masks[0, 0, :] = 1.0                      # Bipolar Forceps（14 種）: 重なり 4 × 0.8
    masks[1, 1, :2] = 1.0                     # BiClamp（その他）: 重なり 2 × 0.8
    t = S.t_target(P, masks, np.array([8, 7]), torch.tensor([1.0, 1.0]), _names()).reshape(3, 16)
    assert np.allclose(t.sum(1), 1.0)
    assert t[0, -1] == pytest.approx(0.2)     # なし = 1 − 0.8
    assert t[0, S.SPECIES.index("Bipolar Forceps")] == pytest.approx(0.8 * 4 / 6)
    assert t[0, 14] == pytest.approx(0.8 * 2 / 6)   # その他
    assert t[1, -1] == pytest.approx(1.0) and t[2, -1] == pytest.approx(1.0)


def test_t_target_without_overlap_puts_mass_on_other():
    P = torch.zeros((5, 4, 4))
    P[3, 3, 3] = 0.5                          # 右手の器具だけ
    t = S.t_target(P, torch.zeros((0, 4, 4)), np.zeros(0, int), torch.zeros(0), _names()).reshape(3, 16)
    assert t[1, 14] == pytest.approx(0.5) and t[1, -1] == pytest.approx(0.5)
    assert np.allclose(t.sum(1), 1.0)

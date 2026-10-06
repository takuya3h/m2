"""Pure parts of scripts/ptower_attribution.py (no GPU, no data)."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ptower_attribution", ROOT / "scripts/ptower_attribution.py")
pa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa)

TOOL = {"id": 1, "category": "Scalpel", "kind": "tool", "x": 100, "y": 100, "w": 200, "h": 100}
HAND = {"id": 2, "category": "Own hands left", "kind": "hand", "x": 200, "y": 150, "w": 300, "h": 200}
GAUZE = {"id": 3, "category": "Gauze", "kind": "tool", "x": 1500, "y": 800, "w": 100, "h": 100}


def test_targets_reject_official_test():
    assert pa.check_targets(["09", "02"], test={"04", "05", "07"}) == ["02", "09"]
    with pytest.raises(ValueError):
        pa.check_targets(["09", "04"], test={"04", "05", "07"})


def test_reads_outside_catches_foreign_video_and_tower():
    plan = {"09": "A", "10": "A", "02": "B"}
    rows = [{"kind": "run", "fold": "A", "chain": "coco", "videos": ["09", "10"]},
            {"kind": "control_b", "fold": "B", "chain": "coco", "videos": ["09", "10"]}]
    assert pa.reads_outside(rows, set(plan), plan) == []
    rows.append({"kind": "run", "fold": "A", "chain": "coco", "videos": ["04"]})
    rows.append({"kind": "run", "fold": "A", "chain": "coco", "videos": ["02"]})
    assert len(pa.reads_outside(rows, set(plan), plan)) == 2


def test_four_regions_are_disjoint_and_sum_to_one():
    masks = pa.region_masks([TOOL, HAND, GAUZE])
    four = [masks[k] for k in ("tool_only", "hand_only", "both", "outside")]
    assert (sum(m.astype(int) for m in four) == 1).all()
    field = np.random.default_rng(0).random((pa.HEIGHT, pa.WIDTH))
    s = pa.shares(field, dict(zip("abcd", four)))
    assert abs(sum(s.values()) - 1) < 1e-12
    assert masks["target_tools"].sum() == 200 * 100 and masks["negative_tools"].sum() == 100 * 100


def test_synthetic_maps_give_one_inside_zero_outside():
    union = pa.box_mask([TOOL, HAND])
    inside, outside = union.astype(float), (~union).astype(float)
    assert pa.shares(inside, {"u": union})["u"] == 1.0
    assert pa.shares(outside, {"u": union})["u"] == 0.0


def test_rolled_control_keeps_area_and_avoids_boxes():
    masks = pa.region_masks([TOOL, HAND])
    union = ~masks["outside"]
    control, overlap, _ = pa.rolled_control(masks["tool_only"], union, 7)
    assert control.sum() == masks["tool_only"].sum()
    assert overlap == 0.0
    # Breaking control for 完了判定 g: a half-area control fails the equality.
    half = control.copy()
    rows, cols = np.nonzero(half)
    half[rows[: len(rows) // 2], cols[: len(cols) // 2]] = False
    assert half.sum() != masks["tool_only"].sum()
    assert np.isnan(pa.rolled_control(np.zeros_like(union), union, 1)[1])


def test_input_grid_matches_resize():
    small = pa.to_input_grid(np.ones((pa.HEIGHT, pa.WIDTH), dtype=bool))
    assert small.shape == (800, 1422)


def test_cache_rows_reads_only_requested_rows(tmp_path):
    ids = np.array([f"{v}_1_{i:04d}" for v in ("04", "09") for i in range(5)])
    feats = np.arange(10 * 4, dtype=np.float32).reshape(10, 4)
    path = tmp_path / "all_gap.npz"
    np.savez(path, frame_ids=ids, features=feats)
    got = pa.cache_rows(path, ["09_1_0003", "09_1_0001"])
    assert np.array_equal(got, feats[[8, 6]])


def test_positional_selection_rule():
    g = np.zeros(300, dtype=np.float32)
    g[[150, 120, 199]] = [3.0, 2.0, 1.0]  # lags 50, 80, 1 at t=200
    chosen = pa.positional_selection(g, 200, 1021)
    assert chosen == {1: ["fixed", "top"], 5: ["fixed"], 15: ["fixed"], 30: ["fixed"],
                      50: ["top"], 60: ["fixed"], 80: ["top"]}
    # Lags outside the receptive field are never chosen.
    tops = [lag for lag, tags in pa.positional_selection(g, 200, 40).items() if "top" in tags]
    assert tops == [1, 2, 3]

"""tools/estimate_tier_cost.py の試験。

**判定が通ったことは、その判定が働いていることを意味しない。** 出所の検査と
対応表の検査には、壊した入力を与えて 1 件を返すことまで確かめる（陽性対照）。
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import estimate_tier_cost as etc  # noqa: E402

ALL_TIERS = ("stage1", "tier1", "tier2", "tier3")


def _base() -> etc.Assumptions:
    return etc.Assumptions(k=3, devices=2, hours_per_day=24.0)


def _totals(a: etc.Assumptions) -> dict[str, float]:
    return etc.cumulative_totals(etc.compute(a), ALL_TIERS)


# ---------------------------------------------------------------- 出所
def test_every_run_type_has_a_source():
    n, bad = etc.check_sources()
    assert n == 0, bad


def test_removing_one_source_is_detected(monkeypatch):
    """陽性対照。出所を一件消すと検査が 1 件を返す。"""
    key = next(iter(etc.RUN_TYPES))
    broken = dict(etc.RUN_TYPES)
    broken[key] = dataclasses.replace(etc.RUN_TYPES[key], source="")
    monkeypatch.setattr(etc, "RUN_TYPES", broken)
    n, bad = etc.check_sources()
    assert n == 1
    assert bad == [key]


# ---------------------------------------------------------------- 対応表
def test_every_m_item_is_covered():
    n, missing = etc.check_coverage(_base())
    assert n == 0, missing


def test_removing_one_coverage_is_detected(monkeypatch):
    """陽性対照。対応表から一項目を消すと検査が 1 件を返す。"""
    target = "t1.pd_w2"
    original = etc.build_rows

    def stripped(k, search_trials, two_stage_selection):
        rows = original(k, search_trials, two_stage_selection)
        return [
            dataclasses.replace(r, covers=tuple(c for c in r.covers if c != target))
            for r in rows
        ]

    monkeypatch.setattr(etc, "build_rows", stripped)
    n, missing = etc.check_coverage(_base())
    assert n == 1
    assert missing == [target]


# ---------------------------------------------------------------- 対照
def test_doubling_durations_doubles_gpu_hours():
    base = _totals(_base())
    twice = _totals(dataclasses.replace(_base(), duration_scale=2.0))
    assert twice["gpu_low"] == pytest.approx(2.0 * base["gpu_low"])
    assert twice["gpu_high"] == pytest.approx(2.0 * base["gpu_high"])


def test_doubling_devices_at_most_halves_wall_clock():
    base = _totals(_base())
    twice = _totals(dataclasses.replace(_base(), devices=4))
    assert twice["wall_low"] <= 0.5 * base["wall_low"] + 1e-9
    assert twice["wall_high"] <= 0.5 * base["wall_high"] + 1e-9


def test_wall_clock_never_below_the_longest_single_run():
    """1 本の run は装置をまたげない。台数を増やしても最長の 1 run より短くならない。"""
    a = dataclasses.replace(_base(), devices=100000)
    res = etc.compute(a)
    total = etc.cumulative_totals(res, ALL_TIERS)
    assert total["wall_low"] == pytest.approx(res["longest_run_hours"])


# ---------------------------------------------------------------- 縮退
def test_degrade_step_count_matches_the_master_order():
    """縮退表の段数が M の縮退順の項目数と一致する。"""
    assert len(etc.DEGRADE_STEPS) == 4
    assert len(etc.DEGRADE_STEPS_SPLIT) == 5


def test_degrade_is_monotonically_non_increasing():
    prev = None
    for i in range(len(etc.DEGRADE_STEPS) + 1):
        t = _totals(etc.apply_degrade(_base(), etc.DEGRADE_STEPS, i))
        if prev is not None:
            assert t["gpu_high"] <= prev + 1e-9
        prev = t["gpu_high"]


def test_degrade_never_drops_the_pd_arms():
    """M は「P→D の W1・W2・専用探索は最後まで削らない」と定める。"""
    protected = {"t1_pd_w1", "t1_pd_w2", "t1_pd_search"}
    a = etc.apply_degrade(_base(), etc.DEGRADE_STEPS, len(etc.DEGRADE_STEPS))
    assert protected.isdisjoint(set(a.dropped_rows))
    keys = {c.row.key for c in etc.compute(a)["costs"]}
    assert protected <= keys


# ---------------------------------------------------------------- K
def test_larger_k_costs_more_in_stage1():
    small = etc.compute(dataclasses.replace(_base(), k=2))["by_tier"]["stage1"]
    large = etc.compute(dataclasses.replace(_base(), k=4))["by_tier"]["stage1"]
    assert large["gpu_high"] > small["gpu_high"]


def test_tier1_does_not_depend_on_k():
    small = etc.compute(dataclasses.replace(_base(), k=2))["by_tier"]["tier1"]
    large = etc.compute(dataclasses.replace(_base(), k=4))["by_tier"]["tier1"]
    assert small["gpu_high"] == pytest.approx(large["gpu_high"])


# ---------------------------------------------------------------- 設計変更
def test_redesign_has_a_non_empty_breakdown():
    r = etc.redesign_cost(_base())
    assert len(r["rows"]) > 0
    assert r["total"]["gpu_high"] > 0
    keys = {c.row.key for c in r["rows"]}
    assert "s1_det_coco" in keys
    assert "t1_pd_w1" in keys


def test_redesign_costs_less_than_the_whole_plan():
    whole = _totals(_base())
    r = etc.redesign_cost(_base())
    assert r["total"]["gpu_high"] < whole["gpu_high"]


# ---------------------------------------------------------------- 文書
def test_check_doc_reports_a_difference_when_a_number_is_changed(tmp_path):
    """陽性対照。文書の数値を一つ書き換えると差が非零になる。"""
    a = _base()
    body = etc.section_base(a)
    key = "base"
    doc = tmp_path / "doc.md"

    def write(text: str) -> None:
        doc.write_text(
            f"{etc.BLOCK_BEGIN.format(key=key)}\n{text}\n{etc.BLOCK_END.format(key=key)}\n",
            encoding="utf-8",
        )

    write(body)
    n, diffs = etc.check_doc(doc, a, split_last=False)
    # 他の節が無いので差は出るが、base 節については差が無いことを確かめる
    assert not any(d.startswith("base 行") for d in diffs), diffs

    write(body.replace("| 2 | Stage 1 |", "| 2 | Stage 1 x |", 1))
    n2, diffs2 = etc.check_doc(doc, a, split_last=False)
    assert any(d.startswith("base 行") for d in diffs2), diffs2
    assert n2 > n

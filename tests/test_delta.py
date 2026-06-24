"""DeltaCalculator の eval_recipe 整合性検証テスト。

研究計画 §15.4 B / §15.6 に対応する整合性検証の振る舞いを検証する:

1. test_eval_recipe_match_same:
       同一 recipe 同士で _recipes_match が True を返す
2. test_eval_recipe_mismatch_score_thr:
       test_cfg.score_thr が異なる recipe で False
3. test_eval_recipe_mismatch_split:
       split_train_images が異なる recipe で False
4. test_compute_delta_raises_on_inconsistent_recipe:
       不一致 recipe で compute_delta が InconsistentRecipeError を送出する
       【§15.6 の最重要テスト】
5. test_compute_delta_warns_on_missing_recipe:
       一方に recipe が無い場合、例外ではなく警告で計算続行する
6. test_server_name_mismatch_warns_not_raises:
       server_name 違いは警告のみで例外にしない（§15.6 は同一サーバー測定を
       推奨するが必須化はしていない）

実行方法:
    PYTHONPATH=src pytest tests/test_delta.py -v
"""

from __future__ import annotations

import json
import logging
import sys
from copy import deepcopy
from pathlib import Path

import pytest

# PYTHONPATH=src を付け忘れても import できるよう src/ を通す。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---------------------------------------------------------------------- #
# テスト用ヘルパ
# ---------------------------------------------------------------------- #
def _make_recipe(**overrides) -> dict:
    """論文公式 split + locked-down test_cfg をベースとした recipe を作る。

    v2（§8.0 反映）では DDP フィールド（gpu_count / effective_batch_size /
    lr_scaling）が必須化されたため、既定で単一 GPU（gpu_count=1,
    effective_batch_size=4, lr_scaling="none"）の recipe を生成する。
    DDP 比較テストでは override で gpu_count=2 等を指定する。
    """
    from egosurgery.utils.eval_recipe import (
        LOCKED_DOWN_TEST_CFG,
        PAPER_SPLIT_SIZES,
        build_eval_recipe,
    )

    recipe = build_eval_recipe(
        test_cfg=LOCKED_DOWN_TEST_CFG,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name="bengio",
        gpu_count=1,
        effective_batch_size=4,
        lr_scaling="none",
    )
    # overrides は top-level または test_cfg.* を上書きできる。
    for key, value in overrides.items():
        if key.startswith("test_cfg."):
            sub = key.split(".", 1)[1]
            recipe["test_cfg"][sub] = value
        else:
            recipe[key] = value
    return recipe


def _seed_baseline(baselines_dir: Path, recipe: dict, map_values=None) -> None:
    """baselines_dir に 3 つの s0_NNN_*_seed42 フォルダを作り、各 metrics.json
    に同一 recipe と mAP を埋めて Δ 計算の素地を作る。"""
    if map_values is None:
        map_values = [0.45, 0.46, 0.47]
    for seq, value in enumerate(map_values, start=1):
        run_dir = baselines_dir / f"s0_{seq:03d}_tool_seed42"
        run_dir.mkdir(parents=True)
        (run_dir / "metrics.json").write_text(
            json.dumps({"mAP": value, "eval_recipe": recipe}),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------- #
# 1. recipe match: 同一 recipe で True
# ---------------------------------------------------------------------- #
def test_eval_recipe_match_same():
    """同一 recipe 同士は _recipes_match が True。"""
    from egosurgery.metrics.delta import DeltaCalculator

    recipe = _make_recipe()
    assert DeltaCalculator._recipes_match(recipe, deepcopy(recipe)) is True


# ---------------------------------------------------------------------- #
# 2. test_cfg.score_thr が異なる → False
# ---------------------------------------------------------------------- #
def test_eval_recipe_mismatch_score_thr():
    """test_cfg.score_thr の不一致は recipe を不一致と判定する。"""
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_recipe()
    diff = _make_recipe(**{"test_cfg.score_thr": 0.05})  # mmdet default
    assert DeltaCalculator._recipes_match(base, diff) is False


# ---------------------------------------------------------------------- #
# 3. split_train_images が異なる → False
# ---------------------------------------------------------------------- #
def test_eval_recipe_mismatch_split():
    """split_train_images の不一致は recipe を不一致と判定する（§15.1 事故対応）。"""
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_recipe()
    diff = _make_recipe(split_train_images=7427)  # 過去の事故時の値
    assert DeltaCalculator._recipes_match(base, diff) is False


# ---------------------------------------------------------------------- #
# 4. 不一致 recipe で InconsistentRecipeError を送出【§15.6 最重要テスト】
# ---------------------------------------------------------------------- #
def test_compute_delta_raises_on_inconsistent_recipe(tmp_path):
    """異なる test_cfg の実験で compute_delta が例外を送出することを確認する。"""
    from egosurgery.metrics.delta import DeltaCalculator, InconsistentRecipeError

    baselines_dir = tmp_path / "baselines"
    baseline_recipe = _make_recipe()
    _seed_baseline(baselines_dir, baseline_recipe)
    calculator = DeltaCalculator(baselines_dir)

    experiment_recipe = _make_recipe(**{"test_cfg.score_thr": 0.05})
    with pytest.raises(InconsistentRecipeError, match=r"§15\.4 B"):
        calculator.compute_delta(
            baseline_step="s0",
            experiment_metrics={"mAP": 0.50},
            metric="mAP",
            experiment_recipe=experiment_recipe,
            baseline_recipe=baseline_recipe,
        )


# ---------------------------------------------------------------------- #
# 5. recipe 欠落: 警告のみで計算続行
# ---------------------------------------------------------------------- #
def test_compute_delta_warns_on_missing_recipe(tmp_path, caplog):
    """recipe の片方が None なら警告のみで Δ 計算は続行する（後方互換）。"""
    from egosurgery.metrics.delta import DeltaCalculator

    baselines_dir = tmp_path / "baselines"
    recipe = _make_recipe()
    _seed_baseline(baselines_dir, recipe)
    calculator = DeltaCalculator(baselines_dir)

    with caplog.at_level(logging.WARNING, logger="egosurgery.metrics.delta"):
        result = calculator.compute_delta(
            baseline_step="s0",
            experiment_metrics={"mAP": 0.50},
            metric="mAP",
            experiment_recipe=recipe,
            baseline_recipe=None,  # 旧実験を想定
        )
    assert result["delta"] == pytest.approx(0.04)
    assert any("eval_recipe" in r.message for r in caplog.records)


# ---------------------------------------------------------------------- #
# 6. server_name 違いは警告のみで例外にしない（§15.6）
# ---------------------------------------------------------------------- #
def test_server_name_mismatch_warns_not_raises(tmp_path, caplog):
    """server_name の不一致は警告のみで InconsistentRecipeError を送出しない。"""
    from egosurgery.metrics.delta import DeltaCalculator

    baselines_dir = tmp_path / "baselines"
    baseline_recipe = _make_recipe(server_name="bengio")
    _seed_baseline(baselines_dir, baseline_recipe)
    calculator = DeltaCalculator(baselines_dir)

    experiment_recipe = _make_recipe(server_name="philip")
    with caplog.at_level(logging.WARNING, logger="egosurgery.metrics.delta"):
        result = calculator.compute_delta(
            baseline_step="s0",
            experiment_metrics={"mAP": 0.50},
            metric="mAP",
            experiment_recipe=experiment_recipe,
            baseline_recipe=baseline_recipe,
        )
    assert result["delta"] == pytest.approx(0.04)
    assert any("server_name" in r.message for r in caplog.records)


# ---------------------------------------------------------------------- #
# 7. gpu_count が異なる → False（§8.0 条件 (4)）
# ---------------------------------------------------------------------- #
def test_eval_recipe_mismatch_gpu_count():
    """gpu_count の不一致（単一 GPU vs DDP 2 GPU）は recipe 不一致と判定する。"""
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_recipe(gpu_count=1, effective_batch_size=4)
    diff = _make_recipe(gpu_count=2, effective_batch_size=4)
    assert DeltaCalculator._recipes_match(base, diff) is False


# ---------------------------------------------------------------------- #
# 8. effective_batch_size が異なる → False（§8.0 条件 (5)）
# ---------------------------------------------------------------------- #
def test_eval_recipe_mismatch_effective_batch_size():
    """effective_batch_size の不一致は recipe 不一致と判定する。"""
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_recipe(gpu_count=2, effective_batch_size=4)
    diff = _make_recipe(gpu_count=2, effective_batch_size=8)
    assert DeltaCalculator._recipes_match(base, diff) is False


# ---------------------------------------------------------------------- #
# 9. gpu_count 不一致で compute_delta が例外を送出（§8.0 条件 (4)）
# ---------------------------------------------------------------------- #
def test_compute_delta_raises_on_gpu_count_mismatch(tmp_path):
    """単一 GPU 基準点と DDP 実験を比較しようとすると InconsistentRecipeError。"""
    from egosurgery.metrics.delta import DeltaCalculator, InconsistentRecipeError

    baselines_dir = tmp_path / "baselines"
    baseline_recipe = _make_recipe(gpu_count=1, effective_batch_size=4)
    _seed_baseline(baselines_dir, baseline_recipe)
    calculator = DeltaCalculator(baselines_dir)

    experiment_recipe = _make_recipe(
        gpu_count=2, effective_batch_size=4, lr_scaling="linear_x2",
    )
    with pytest.raises(InconsistentRecipeError, match=r"§8\.0"):
        calculator.compute_delta(
            baseline_step="s0",
            experiment_metrics={"mAP": 0.50},
            metric="mAP",
            experiment_recipe=experiment_recipe,
            baseline_recipe=baseline_recipe,
        )


# ---------------------------------------------------------------------- #
# 10. build_eval_recipe が DDP フィールドを含む dict を返す（§8.0 条件 (5)(6)）
# ---------------------------------------------------------------------- #
def test_build_eval_recipe_ddp_fields():
    """build_eval_recipe の戻り値に gpu_count / effective_batch_size /
    lr_scaling が含まれる。"""
    from egosurgery.utils.eval_recipe import (
        LOCKED_DOWN_TEST_CFG,
        PAPER_SPLIT_SIZES,
        build_eval_recipe,
    )

    recipe = build_eval_recipe(
        test_cfg=LOCKED_DOWN_TEST_CFG,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name="bengio",
        gpu_count=2,
        effective_batch_size=4,
        lr_scaling="linear_x2",
    )
    assert recipe["gpu_count"] == 2
    assert recipe["effective_batch_size"] == 4
    assert recipe["lr_scaling"] == "linear_x2"
    # 既存フィールドも一緒に確認（v1 互換キーの維持）。
    assert recipe["test_cfg"]["score_thr"] == 1e-8
    assert recipe["split_train_images"] == 9657
    assert recipe["server_name"] == "bengio"


# ---------------------------------------------------------------------- #
# phase 側 recipe 保護（イ-2 / 2026-06-15）
# ---------------------------------------------------------------------- #
def _make_phase_recipe(**test_cfg_overrides) -> dict:
    """task='phase' の eval_recipe を作る（phase_trainer._build_eval_recipe と同形式）。

    test_cfg のキーを override して構成差を作れる。split / DDP は既定で
    _make_recipe と一致させ、test_cfg の差だけが _recipes_match を動かすようにする。
    """
    from egosurgery.utils.eval_recipe import PAPER_SPLIT_SIZES, build_eval_recipe

    test_cfg = {
        "task": "phase",
        "backbone": "torchvision_resnet50_frozen_imagenet",
        "phase_head_dropout": 0.5,
        "image_size": 224,
        "use_class_weights": False,
        "max_weight_ratio": 10.0,
        "label_smoothing": 0.1,
    }
    test_cfg.update(test_cfg_overrides)
    return build_eval_recipe(
        test_cfg=test_cfg,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name="bengio",
        gpu_count=1,
        effective_batch_size=4,
        lr_scaling="none",
    )


def test_phase_recipe_match_same():
    """同一 phase recipe 同士は _recipes_match が True。"""
    from egosurgery.metrics.delta import DeltaCalculator

    recipe = _make_phase_recipe()
    assert DeltaCalculator._recipes_match(recipe, deepcopy(recipe)) is True


def test_phase_recipe_mismatch_param():
    """phase test_cfg の構成差（image_size）を不一致として検出する【イ-2 の主目的】。

    旧実装は固定の検出キー (score_thr 等) のみ比較したため、phase recipe の
    差は全キー None 同士で素通りしていた。本テストはその穴が塞がれたことを保証する。
    """
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_phase_recipe()
    diff = _make_phase_recipe(image_size=336)
    assert DeltaCalculator._recipes_match(base, diff) is False


def test_phase_recipe_mismatch_label_smoothing():
    """phase の label_smoothing 差も不整合として検出する。"""
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_phase_recipe()
    diff = _make_phase_recipe(label_smoothing=0.0)
    assert DeltaCalculator._recipes_match(base, diff) is False


def test_detection_vs_phase_recipe_mismatch():
    """検出 recipe と phase recipe（task 不一致）は不一致と判定する。"""
    from egosurgery.metrics.delta import DeltaCalculator

    det = _make_recipe()
    phase = _make_phase_recipe()
    assert DeltaCalculator._recipes_match(det, phase) is False


def test_descriptive_note_ignored():
    """記述用 test_cfg.note の差は recipe 一致判定に影響しない（DESCRIPTIVE_TEST_CFG_KEYS）。

    検出器ごとに異なる note（自由文）で s0 ベンチ比較が誤不一致にならないことを保証する。
    """
    from egosurgery.metrics.delta import DeltaCalculator

    base = _make_recipe(**{"test_cfg.note": "Relation-DETR topk (NMS-free)"})
    diff = _make_recipe(**{"test_cfg.note": "VFNet locked-down NMS"})
    assert DeltaCalculator._recipes_match(base, diff) is True


def test_phase_recipe_protocol_lock():
    """工程 recipe ロック: online_causal / Jaccard strict の差を不整合として検出する（注249）。"""
    from egosurgery.metrics.delta import DeltaCalculator
    from egosurgery.utils.eval_recipe import PHASE_EVAL_PROTOCOL

    base = _make_phase_recipe(**PHASE_EVAL_PROTOCOL)
    same = _make_phase_recipe(**PHASE_EVAL_PROTOCOL)
    offline = _make_phase_recipe(**{**PHASE_EVAL_PROTOCOL, "inference_protocol": "offline"})
    relaxed = _make_phase_recipe(**{**PHASE_EVAL_PROTOCOL, "jaccard_mode": "relaxed"})
    assert DeltaCalculator._recipes_match(base, same) is True
    assert DeltaCalculator._recipes_match(base, offline) is False  # offline 混在禁止（§6）
    assert DeltaCalculator._recipes_match(base, relaxed) is False  # relaxed 混在禁止（§6）

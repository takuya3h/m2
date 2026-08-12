"""評価条件（eval recipe）の locked-down 定数と構築ユーティリティ。

研究計画 §15.3 G1（locked-down test_cfg）および §15.4 B（Δ は同一 eval
recipe 同士でのみ意味を持つ）に対応する。本モジュールは metrics.json に
書き込む ``eval_recipe`` dict の単一情報源として機能する。

v2（2026/05/25 §8.0・§13.2 反映）:
    DDP 2 GPU 運用に伴い、``gpu_count`` / ``effective_batch_size`` /
    ``lr_scaling`` を recipe に追加する。単一 GPU と DDP 2 GPU の混在は
    effective batch size・NCCL allreduce 非決定性・BN/LN 挙動差により
    Δ の意味が崩壊するため、これらの不一致は :func:`recipes_match` が
    False を返す（``DeltaCalculator`` 側で
    :class:`InconsistentRecipeError` を送出）。

使い方:
    from egosurgery.utils.eval_recipe import (
        LOCKED_DOWN_TEST_CFG, PAPER_SPLIT_SIZES, build_eval_recipe,
    )
    recipe = build_eval_recipe(
        test_cfg=LOCKED_DOWN_TEST_CFG,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name="bengio",
        gpu_count=2,
        effective_batch_size=4,
        lr_scaling="linear_x2",
    )
    experiment_manager.log_eval_recipe(recipe)
"""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)


# 研究計画 §15.3 G1: 全 detector・全 stage で強制する locked-down test_cfg。
# §15.2 で発覚した「score_thr が mmdet default 0.05 で論文 1e-8 と乖離」の
# 再発防止策として、評価時の検出後処理を 1 箇所で一元定義する。
LOCKED_DOWN_TEST_CFG: dict = {
    "score_thr": 1e-8,
    "max_per_img": 300,
    "nms_pre": 3000,
    "nms_iou": 0.6,
}

# 研究ピボット「分析ファースト」STEP 0-1（2026-06-15）の決定。比較の三角形
# （凍結源 = Relation-DETR 単一 backbone）および DETR-family（NMS-free）検出ヘッドの
# 公式 eval recipe。Relation-DETR を両 recipe で実測した結果、locked-down の NMS@0.6 を
# NMS-free モデルに適用すると -4.5pt mAP（PostProcess の class-agnostic NMS が手術シーンの
# 異クラス重なり箱を誤除去）と判明した。三角形の検出ヘッドには NMS を適用しないこと
# （Δ_detection 汚染防止）。score_thr は 0.0 と 1e-8 で完全同値（予測の最小スコア ≫ 1e-8）。
# 証跡: experiments/analysis/step0_recipe/notes.md / docs/experiment_log.md(2026-06-15 STEP 0-1)。
NMS_FREE_TEST_CFG: dict = {
    "score_thr": 0.0,
    "max_per_img": 300,
    "nms_pre": None,
    "nms_iou": None,
}

# 研究計画 §4.2 / §6 / 注249（ピボット 2026-06-15）: 「工程 recipe」のロック。
# 検出 recipe（NMS_FREE_TEST_CFG / LOCKED_DOWN_TEST_CFG）とは別軸で、工程認識
# （S4 時系列・結合手法）の評価 protocol を一元定義する。online/causal（未来フレーム
# 不使用）と Jaccard strict を固定し、offline / relaxed との混在を recipes_match が
# 不整合として検出できるようにする（§6 公正比較の鉄則: 推論 protocol・指標の混在禁止）。
# S4 / 結合手法の eval_recipe.test_cfg に **マージして** 記録すること
# （task='phase' と併記。例: {"task": "phase", **PHASE_EVAL_PROTOCOL, ...}）。
# 指標セット（accuracy / macro-P,R,F1 / Jaccard+edit / seg-F1@{10,25,50}）は metrics.json
# 本体に記録するが、Δ 比較の「土台」を縛るのは下記 protocol（online + strict）である。
PHASE_EVAL_PROTOCOL: dict = {
    "inference_protocol": "online_causal",  # 未来フレーム不使用（§4.2）
    "jaccard_mode": "strict",               # relaxed と混ぜない（§6 交絡の禁止）
}

# eval_recipe.test_cfg のうち「記述用」で Δ の一致判定から除外するキー。検出器ごとに
# 異なる自由文（例: ``note``）は実効パラメータではないため recipe 一致判定に影響させない。
# これにより検出（score_thr/nms 等）も phase（task='phase' + backbone/image_size 等）も
# 「実効キーを全比較」する単一の仕組みで保護できる（recipes_match 参照）。
DESCRIPTIVE_TEST_CFG_KEYS: tuple = ("note", "description")

# 研究計画 §15.1: 論文公式 split サイズ。§15.1 では train 8 videos / 7427
# images で学習していた事故が発覚した。Δ 基準点を汚染させないため、
# 期待値を定数で明示する。
PAPER_SPLIT_SIZES: dict = {
    "train": {"images": 9657, "annotations": 32272},
    "val":   {"images": 1515, "annotations": 4707},
    "test":  {"images": 4265, "annotations": 12673},
}

# 論文公式 split の動画割り当て（§15.1）。preprocess の検証用。
PAPER_SPLIT_VIDEOS: dict = {
    "train": ["01", "02", "03", "06", "08", "11", "12", "13", "14", "15"],
    "val":   ["09", "10"],
    "test":  ["04", "05", "07"],
}


def build_eval_recipe(
    test_cfg: dict,
    split_sizes: dict,
    server_name: str,
    gpu_count: int = 1,
    effective_batch_size: int | None = None,
    lr_scaling: str = "none",
) -> dict:
    """``metrics.json`` に書き込む ``eval_recipe`` dict を構築する。

    Args:
        test_cfg: 評価時の検出後処理設定（``score_thr`` 等）。通常は
            :data:`LOCKED_DOWN_TEST_CFG` を渡す。Phase 認識など検出と異なる
            タスクでは ``{"task": "phase", ...}`` のような自由 dict でもよい。
        split_sizes: ``{"train": {"images": int, "annotations": int}, ...}``
            形式の split サイズ辞書。通常は :data:`PAPER_SPLIT_SIZES` を渡す。
        server_name: 実行サーバー名（``resolve_server_name()`` の戻り値）。
        gpu_count: 学習に使った GPU 枚数。単一 GPU=1、DDP 2 GPU=2（§8.0 条件 (5)）。
        effective_batch_size: ``gpu_count × per-GPU batch size``。明示しない
            場合は ``None``（後方互換のための既定）（§8.0 条件 (5)）。
        lr_scaling: lr 線形スケーリングの適用状況（§8.0 条件 (6)）。
            ``"none"``（単一 GPU）/ ``"linear_x2"``（DDP 2 GPU で lr×2）/
            ``"per_gpu_bs_adjusted"`` 等。

    Returns:
        :func:`recipes_match` の比較対象キーをすべて含む dict。
    """
    return {
        "test_cfg": dict(test_cfg),
        "split_train_images": split_sizes["train"]["images"],
        "split_train_annotations": split_sizes["train"]["annotations"],
        "split_val_images": split_sizes["val"]["images"],
        "split_val_annotations": split_sizes["val"]["annotations"],
        "split_test_images": split_sizes["test"]["images"],
        "split_test_annotations": split_sizes["test"]["annotations"],
        "server_name": server_name,
        # === DDP / GPU 構成（§8.0 条件 (4)(5)(6)） ===
        "gpu_count": int(gpu_count),
        "effective_batch_size": (
            int(effective_batch_size) if effective_batch_size is not None else None
        ),
        "lr_scaling": str(lr_scaling),
    }


# recipes_match が比較する split サイズキー（§15.4 A）。
_SPLIT_KEYS = (
    "split_train_images",
    "split_val_images",
    "split_test_images",
)

# DDP 構成の比較キー（§8.0 条件 (4)(5)）。
_DDP_KEYS = ("gpu_count", "effective_batch_size")


def recipes_match(recipe_a: dict, recipe_b: dict) -> bool:
    """2 つの ``eval_recipe`` が Δ 計算に互換かを判定する。

    比較対象:
        - ``test_cfg`` の実効項目（:data:`DESCRIPTIVE_TEST_CFG_KEYS` を除く全キー）。
          検出 recipe（score_thr/nms_* 等）も phase recipe（task='phase' +
          backbone/image_size 等）も同一の仕組みで比較される。
        - split サイズ（train/val/test images）
        - GPU 構成（``gpu_count``、``effective_batch_size``）— §8.0 条件 (4)

    ``server_name`` の不一致は警告のみで True/False には影響しない
    （§15.6: 同一サーバー測定は推奨だが必須化はしていない）。

    Args:
        recipe_a: 片方の eval_recipe。
        recipe_b: もう一方の eval_recipe。

    Returns:
        test_cfg / split / GPU 構成が全て一致する場合に True。
    """
    # test_cfg の実効項目をすべて比較する（記述用キーは除外）。検出（score_thr/nms_*）も
    # phase（task='phase' + backbone/image_size 等）も同一の仕組みで保護する。task キーが
    # 異なれば（検出 vs phase、または phase 同士の構成差）ここで不一致になる。
    test_a = recipe_a.get("test_cfg") or {}
    test_b = recipe_b.get("test_cfg") or {}
    compared_keys = (set(test_a) | set(test_b)) - set(DESCRIPTIVE_TEST_CFG_KEYS)
    for key in compared_keys:
        if test_a.get(key) != test_b.get(key):
            return False

    # split サイズを比較（§15.1）
    for key in _SPLIT_KEYS:
        if recipe_a.get(key) != recipe_b.get(key):
            return False

    # GPU 構成を比較（§8.0 条件 (4)：単一 GPU と DDP の混在禁止）
    for key in _DDP_KEYS:
        if recipe_a.get(key) != recipe_b.get(key):
            return False

    # server_name は不一致でも match と判定する。警告のみ出す。
    server_a = recipe_a.get("server_name")
    server_b = recipe_b.get("server_name")
    if server_a and server_b and server_a != server_b:
        _logger.warning(
            "eval_recipe.server_name が異なります "
            "(%r vs %r). 同一サーバー測定が推奨されますが、recipes_match は True を返します。",
            server_a, server_b,
        )
    return True

"""評価条件（eval recipe）の locked-down 定数と構築ユーティリティ。

研究計画 §15.3 G1（locked-down test_cfg）および §15.4 B（Δ は同一 eval
recipe 同士でのみ意味を持つ）に対応する。本モジュールは metrics.json に
書き込む ``eval_recipe`` dict の単一情報源として機能する。

使い方:
    from egosurgery.utils.eval_recipe import (
        LOCKED_DOWN_TEST_CFG, PAPER_SPLIT_SIZES, build_eval_recipe,
    )
    recipe = build_eval_recipe(PAPER_SPLIT_SIZES, server_name="bengio")
    experiment_manager.log_eval_recipe(recipe)
"""

from __future__ import annotations

# 研究計画 §15.3 G1: 全 detector・全 stage で強制する locked-down test_cfg。
# §15.2 で発覚した「score_thr が mmdet default 0.05 で論文 1e-8 と乖離」の
# 再発防止策として、評価時の検出後処理を 1 箇所で一元定義する。
LOCKED_DOWN_TEST_CFG: dict = {
    "score_thr": 1e-8,
    "max_per_img": 300,
    "nms_pre": 3000,
    "nms_iou": 0.6,
}

# 研究計画 §15.1: 論文公式 split サイズ。§15.1 では train 8 videos / 7427
# images で学習していた事故が発覚した。Δ 基準点を汚染させないため、
# 期待値を定数で明示する。
PAPER_SPLIT_SIZES: dict = {
    "train": {"images": 9657, "annotations": 32272},
    "val":   {"images": 1515, "annotations": 4707},
    "test":  {"images": 4265, "annotations": 12673},
}


def build_eval_recipe(
    split_sizes: dict,
    server_name: str,
    test_cfg: dict | None = None,
) -> dict:
    """``metrics.json`` に書き込む ``eval_recipe`` dict を構築する。

    Args:
        split_sizes: ``{"train": {"images": int, "annotations": int}, ...}``
            形式の split サイズ辞書。通常は :data:`PAPER_SPLIT_SIZES` を渡す。
        server_name: 実行サーバー名（``resolve_server_name()`` の戻り値）。
        test_cfg: 評価時の検出後処理設定。省略時は :data:`LOCKED_DOWN_TEST_CFG`
            のコピーを使う。

    Returns:
        ``DeltaCalculator._recipes_match`` の比較対象キーをすべて含む dict。
    """
    return {
        "split_train_images": split_sizes["train"]["images"],
        "split_val_images": split_sizes["val"]["images"],
        "split_test_images": split_sizes["test"]["images"],
        "split_train_annotations": split_sizes["train"]["annotations"],
        "test_cfg": dict(test_cfg) if test_cfg is not None else dict(LOCKED_DOWN_TEST_CFG),
        "server_name": server_name,
    }

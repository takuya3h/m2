"""Δ 指標の自動計算ユーティリティ。

研究計画 §7.1 で定義された相互改善幅（Δ）を計算する。Δ は

    Δ = (実験の指標値) - (基準ステップの 3-seed 平均)

として定義し、その有意性は基準点の標準偏差（σ）を用いて判定する。
§10.1「Δ が 1σ 以内なら改善と主張しない」に従い、``abs(Δ) > σ`` を
満たすときのみ ``significant=True`` を返す。

使い方:
    calculator = DeltaCalculator(baselines_dir="experiments/baselines")

    # S0 の基準点（同一 step の全 seed フォルダの平均±標準偏差）
    baseline = calculator.get_baseline("s0", metric="mAP")
    # -> {"mean": 0.458, "std": 0.012, "values": [...], "n": 3}

    # Δ を計算
    delta = calculator.compute_delta(
        baseline_step="s0",
        experiment_metrics={"mAP": 0.49},
        metric="mAP",
    )
    # -> {"delta": 0.032, "baseline_mean": 0.458, "baseline_std": 0.012,
    #     "significant": True, ...}

    # 実験フォルダの metrics.json 内の全指標について一括計算
    deltas = calculator.compute_all_deltas("experiments/.../s6_001_.../", "s0")
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

_logger = logging.getLogger(__name__)

# 研究計画 §15.4 B / §15.6: eval recipe の不一致は Δ の意味を破壊するため、
# 不一致が検出された場合は計算自体を拒否する。
_RECIPE_REQUIRED_KEYS = (
    "split_train_images",
    "split_val_images",
    "split_test_images",
)
_TEST_CFG_KEYS = ("score_thr", "max_per_img", "nms_pre", "nms_iou")
# §8.0 条件 (4)(5): 単一 GPU と DDP 2 GPU の混在は Δ の意味を崩壊させるため、
# gpu_count / effective_batch_size の不一致も致命的不整合として扱う。
_DDP_REQUIRED_KEYS = ("gpu_count", "effective_batch_size")


class InconsistentRecipeError(Exception):
    """2 つの実験の eval_recipe が一致しないときに送出される。

    研究計画 §15.4 B / §15.6 に対応: Δ は同一の評価条件で測定された
    値同士でのみ意味を持つため、不一致時は計算を続行せず例外で停止する。
    """


class DeltaCalculator:
    """基準ステップに対する Δ（相互改善幅）を計算するクラス。"""

    def __init__(self, baselines_dir: str | Path) -> None:
        """
        Args:
            baselines_dir: ``{step}_NNN_..._seedXX/`` 形式の実験フォルダが
                並ぶディレクトリ（通常 ``experiments/baselines``）。
        """
        self.baselines_dir = Path(baselines_dir)

    # ------------------------------------------------------------------ #
    # 基準点の集約
    # ------------------------------------------------------------------ #
    def _iter_step_metrics(self, step: str):
        """``{step}_*`` フォルダの ``metrics.json`` を順に読み出す。

        Yields:
            (フォルダ名, metrics 辞書) のタプル。
        """
        if not self.baselines_dir.exists():
            return
        prefix = f"{step}_"
        for child in sorted(self.baselines_dir.iterdir()):
            if not child.is_dir() or not child.name.startswith(prefix):
                continue
            metrics_path = child / "metrics.json"
            if not metrics_path.exists():
                continue
            try:
                data = json.loads(metrics_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(data, dict):
                yield child.name, data

    def get_baseline(self, step: str, metric: str) -> dict:
        """基準ステップの指定指標について平均・標準偏差・生値を返す。

        Args:
            step: 基準ステップ識別子（例: ``s0``）。
            metric: 集約対象の指標名（例: ``mAP``）。

        Returns:
            ``{"mean": float, "std": float, "values": list, "n": int}``。
            標準偏差は不偏標準偏差（ddof=1）。サンプルが 1 個以下なら 0.0。

        Raises:
            ValueError: 該当する指標値が 1 つも見つからない場合。
        """
        values: list[float] = []
        for _name, data in self._iter_step_metrics(step):
            value = data.get(metric)
            if isinstance(value, bool):  # bool は数値扱いしない
                continue
            if isinstance(value, (int, float)):
                values.append(float(value))

        if not values:
            raise ValueError(
                f"基準点となる指標が見つかりません: "
                f"step={step!r}, metric={metric!r}, dir={self.baselines_dir}"
            )

        arr = np.asarray(values, dtype=float)
        std = float(arr.std(ddof=1)) if arr.size >= 2 else 0.0
        return {
            "mean": float(arr.mean()),
            "std": std,
            "values": values,
            "n": int(arr.size),
        }

    # ------------------------------------------------------------------ #
    # eval recipe の整合性検証（§15.4 B / §15.6）
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_eval_recipe(metrics_path: str | Path) -> dict | None:
        """``metrics.json`` から ``eval_recipe`` を読む。無ければ ``None``。

        Args:
            metrics_path: ``metrics.json`` のパス。

        Returns:
            eval_recipe dict、または存在しない場合 ``None``。
        """
        path = Path(metrics_path)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        recipe = data.get("eval_recipe") if isinstance(data, dict) else None
        return recipe if isinstance(recipe, dict) else None

    @staticmethod
    def _recipes_match(recipe_a: dict, recipe_b: dict) -> bool:
        """2 つの ``eval_recipe`` が一致するか判定する。

        比較対象:
            - split の image/annotation 数
            - ``test_cfg`` の全項目
            - GPU 構成（``gpu_count`` / ``effective_batch_size``）— §8.0 条件 (4)(5)。
              単一 GPU と DDP 2 GPU の混在は effective batch size・NCCL allreduce
              非決定性・BN/LN 挙動差により Δ の意味が崩壊するため、recipe 不一致
              とみなし False を返す。

        ``server_name`` の不一致は警告のみで True/False には影響しない
        （§15.6: 同一サーバー測定は推奨だが必須化はしていない）。

        Args:
            recipe_a: 片方の eval_recipe。
            recipe_b: もう一方の eval_recipe。

        Returns:
            split / test_cfg / GPU 構成が全て一致する場合に True。
        """
        for key in _RECIPE_REQUIRED_KEYS:
            if recipe_a.get(key) != recipe_b.get(key):
                return False

        test_a = recipe_a.get("test_cfg") or {}
        test_b = recipe_b.get("test_cfg") or {}
        for key in _TEST_CFG_KEYS:
            if test_a.get(key) != test_b.get(key):
                return False

        # §8.0 条件 (4)(5): GPU 構成（gpu_count / effective_batch_size）の比較。
        # 旧 metrics.json（v1 時代）にはこのキーが無いため、両側に存在する場合のみ
        # 厳格比較する。一方に欠落していたら（=v1 互換）警告だけ出して通す。
        for key in _DDP_REQUIRED_KEYS:
            val_a = recipe_a.get(key)
            val_b = recipe_b.get(key)
            if val_a is None or val_b is None:
                # v1 互換のため、欠落側を不整合扱いせず警告に留める。
                if val_a != val_b:
                    _logger.warning(
                        "eval_recipe.%s が片側のみ存在します (%r vs %r). "
                        "v1 時代の metrics.json と推測されるため Δ 計算は続行します。",
                        key, val_a, val_b,
                    )
                continue
            if val_a != val_b:
                return False

        # server_name は不一致でも match と判定する。警告のみ出す。
        server_a = recipe_a.get("server_name")
        server_b = recipe_b.get("server_name")
        if server_a and server_b and server_a != server_b:
            _logger.warning(
                "eval_recipe.server_name が異なります "
                "(%r vs %r). 同一サーバー測定が推奨されますが、Δ 計算は続行します。",
                server_a, server_b,
            )
        return True

    # ------------------------------------------------------------------ #
    # Δ の計算
    # ------------------------------------------------------------------ #
    def compute_delta(
        self,
        baseline_step: str,
        experiment_metrics: dict,
        metric: str,
        experiment_recipe: dict | None = None,
        baseline_recipe: dict | None = None,
    ) -> dict:
        """単一指標について基準点との Δ を計算する。

        Args:
            baseline_step: 基準ステップ識別子（例: ``s0``）。
            experiment_metrics: 比較対象実験の metrics 辞書。
            metric: 対象の指標名。
            experiment_recipe: 実験側の ``eval_recipe`` dict（省略可）。
            baseline_recipe: 基準点側の ``eval_recipe`` dict（省略可）。

        Returns:
            Δ・基準統計・有意性を含む辞書。``significant`` は
            ``abs(delta) > baseline_std``（§10.1: 1σ 基準）で判定する。

        Raises:
            KeyError: ``experiment_metrics`` に ``metric`` が無い場合。
            ValueError: 基準点が取得できない場合（:meth:`get_baseline` 経由）。
            InconsistentRecipeError: ``experiment_recipe`` と ``baseline_recipe``
                が両方与えられて split / test_cfg / GPU 構成のいずれかが一致しない
                場合（§15.4 B / §15.6 / §8.0 条件 (4)(5)）。

        Notes:
            recipe がどちらか一方でも ``None`` の場合は後方互換のため警告を
            出して計算を続行する（旧実験の metrics.json には eval_recipe が
            無いため）。
        """
        if metric not in experiment_metrics:
            raise KeyError(f"experiment_metrics に指標 {metric!r} がありません。")

        if experiment_recipe is not None and baseline_recipe is not None:
            if not self._recipes_match(experiment_recipe, baseline_recipe):
                raise InconsistentRecipeError(
                    "eval_recipe の不一致により Δ 計算を停止します "
                    "（§15.4 B / §15.6 / §8.0 条件 (4)(5)）。実験と基準点で "
                    "split サイズ・test_cfg・GPU 構成（gpu_count / "
                    "effective_batch_size）のいずれかが異なります: "
                    f"exp={experiment_recipe!r}, base={baseline_recipe!r}"
                )
        elif experiment_recipe is None or baseline_recipe is None:
            _logger.warning(
                "eval_recipe の片方または両方が None です。"
                "後方互換のため Δ 計算を続行しますが、結果の比較可能性は保証されません "
                "(§15.4 B)。"
            )

        baseline = self.get_baseline(baseline_step, metric)
        exp_value = float(experiment_metrics[metric])
        delta = exp_value - baseline["mean"]
        significant = abs(delta) > baseline["std"]

        return {
            "metric": metric,
            "delta": delta,
            "experiment_value": exp_value,
            "baseline_step": baseline_step,
            "baseline_mean": baseline["mean"],
            "baseline_std": baseline["std"],
            "baseline_n": baseline["n"],
            "significant": bool(significant),
        }

    def compute_all_deltas(
        self,
        experiment_dir: str | Path,
        baseline_step: str,
    ) -> dict:
        """実験フォルダの ``metrics.json`` 内の全数値指標について Δ を一括計算する。

        基準点側に存在しない指標は黙ってスキップする。

        Args:
            experiment_dir: ``metrics.json`` を含む実験フォルダ。
            baseline_step: 基準ステップ識別子。

        Returns:
            ``{指標名: compute_delta の戻り値}`` の辞書。

        Raises:
            FileNotFoundError: ``metrics.json`` が存在しない場合。
        """
        metrics_path = Path(experiment_dir) / "metrics.json"
        if not metrics_path.exists():
            raise FileNotFoundError(f"metrics.json が見つかりません: {metrics_path}")

        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        results: dict = {}
        for metric, value in metrics.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            try:
                results[metric] = self.compute_delta(baseline_step, metrics, metric)
            except ValueError:
                # 基準点側に当該指標が無い -> スキップ
                continue
        return results

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
from pathlib import Path

import numpy as np


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
    # Δ の計算
    # ------------------------------------------------------------------ #
    def compute_delta(
        self,
        baseline_step: str,
        experiment_metrics: dict,
        metric: str,
    ) -> dict:
        """単一指標について基準点との Δ を計算する。

        Args:
            baseline_step: 基準ステップ識別子（例: ``s0``）。
            experiment_metrics: 比較対象実験の metrics 辞書。
            metric: 対象の指標名。

        Returns:
            Δ・基準統計・有意性を含む辞書。``significant`` は
            ``abs(delta) > baseline_std``（§10.1: 1σ 基準）で判定する。

        Raises:
            KeyError: ``experiment_metrics`` に ``metric`` が無い場合。
            ValueError: 基準点が取得できない場合（:meth:`get_baseline` 経由）。
        """
        if metric not in experiment_metrics:
            raise KeyError(f"experiment_metrics に指標 {metric!r} がありません。")

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

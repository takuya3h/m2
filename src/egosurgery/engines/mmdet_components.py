"""mmdet Runner に差し込む EgoSurgery 専用コンポーネント。

S0（術具検出ベースライン）を実検出器（VarifocalNet / DINO）で完走させる際、
mmdet の標準パイプラインへ以下を注入する:

- :class:`EgoCocoMetric`: COCO mAP に加え、研究計画 §7 の長尾分析が要求する
  ``AP_rare`` / ``AP_common`` と 15 クラス per-class AP を評価結果へ追加する。
  ``prefix='val'`` で記録されるため W&B キーは ``val/mAP`` ``val/AP_rare`` 等。
- :class:`EgoWandbHook`: 学習ロス（``train/loss``）と各 epoch の検証指標を
  W&B へ転送し、検証指標を ``logs/val_metrics.jsonl`` へも追記する。

両者は import 時に mmdet のレジストリへ登録される。
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from mmdet.evaluation.metrics import CocoMetric
from mmdet.registry import HOOKS, METRICS
from mmengine.hooks import Hook

from egosurgery.datasets.constants import RARE_CLASSES

# 研究計画 §7 の稀少クラス（Copy-Paste / RFS 優先対象と一致）。
# 【2026/05/24 v2 訂正】Forceps (12.21%) は稀少ではないため、
# constants.RARE_CLASSES（Skewer / Syringe の 2 クラス）を単一情報源とする。
_DEFAULT_RARE = tuple(RARE_CLASSES)
# S2 (hand 追加) のクラスグループ集計用デフォルト。
_DEFAULT_TOOL_GROUP = (
    "Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook",
    "Mouth Gag", "Needle Holders", "Raspatory", "Retractor", "Scalpel",
    "Scissors", "Skewer", "Suction Cannula", "Syringe", "Tweezers",
)
_DEFAULT_HAND_GROUP = (
    "Own hands left", "Own hands right", "Other hands left", "Other hands right",
)
_PRECISION_SUFFIX = "_precision"


@METRICS.register_module()
class EgoCocoMetric(CocoMetric):
    """COCO mAP に AP_rare / AP_common / per-class AP を加える評価指標。

    mmdet の :class:`CocoMetric` を ``classwise=True`` で動かし、得られた
    ``{クラス名}_precision`` から稀少クラスと頻出クラスの平均 AP を導出する。
    返り値の辞書は ``prefix`` 付き（既定 ``val``）でロガーへ渡る。
    """

    def __init__(
        self,
        *args,
        rare_classes=None,
        tool_classes=None,
        hand_classes=None,
        **kwargs,
    ) -> None:
        """
        Args:
            rare_classes: 稀少クラス名のリスト（既定 Skewer/Syringe/Forceps）。
            tool_classes: tool グループとして集計するクラス名のリスト
                （S2 で tool_mAP を計算するため。``None`` ではデフォルトの 15 クラス）。
            hand_classes: hand グループとして集計するクラス名のリスト
                （S2 で hand_mAP を計算するため。``None`` ではデフォルトの 4 クラス）。
            *args, **kwargs: :class:`CocoMetric` へ素通し。``classwise`` は
                未指定なら ``True`` を補う。
        """
        kwargs.setdefault("classwise", True)
        super().__init__(*args, **kwargs)
        self._rare = tuple(rare_classes) if rare_classes else _DEFAULT_RARE
        self._tool = tuple(tool_classes) if tool_classes else _DEFAULT_TOOL_GROUP
        self._hand = tuple(hand_classes) if hand_classes else _DEFAULT_HAND_GROUP

    def compute_metrics(self, results) -> dict:
        """COCO 指標を計算し、長尾指標と per-class AP を補って返す。"""
        eval_results = super().compute_metrics(results)

        # CocoMetric(classwise=True) は {クラス名}_precision を入れてくる。
        per_class: dict[str, float] = {}
        for key, value in list(eval_results.items()):
            if key.endswith(_PRECISION_SUFFIX):
                name = key[: -len(_PRECISION_SUFFIX)]
                # GT 不在クラスは NaN になり得るため 0.0 に倒す。
                per_class[name] = 0.0 if value is None or math.isnan(value) else float(value)

        if per_class:
            rare = [per_class[c] for c in self._rare if c in per_class]
            common = [v for c, v in per_class.items() if c not in self._rare]
            eval_results["AP_rare"] = float(np.mean(rare)) if rare else 0.0
            eval_results["AP_common"] = float(np.mean(common)) if common else 0.0
            # tool / hand のクラスグループ別 mAP（S2 判定 #2 用）。
            tool_vals = [per_class[c] for c in self._tool if c in per_class]
            hand_vals = [per_class[c] for c in self._hand if c in per_class]
            if tool_vals:
                eval_results["tool_mAP"] = float(np.mean(tool_vals))
            if hand_vals:
                eval_results["hand_mAP"] = float(np.mean(hand_vals))

        # 'bbox_mAP' を素の 'mAP' / 'mAP_50' / 'mAP_75' でも参照可能にする。
        if "bbox_mAP" in eval_results:
            eval_results["mAP"] = eval_results["bbox_mAP"]
            eval_results["mAP_50"] = eval_results.get("bbox_mAP_50", 0.0)
            eval_results["mAP_75"] = eval_results.get("bbox_mAP_75", 0.0)
        return eval_results


@HOOKS.register_module()
class EgoWandbHook(Hook):
    """学習ロスと検証指標を W&B / JSONL へ転送する mmengine フック。

    - ``after_train_iter``: ``interval`` ごとに ``train/*`` ロスを W&B へ。
    - ``after_val_epoch``: 検証指標を W&B へ送り、``logs/val_metrics.jsonl``
      へ 1 行追記する（学習後に最良 epoch を選ぶための証跡）。
    """

    priority = "BELOW_NORMAL"

    def __init__(self, interval: int = 50) -> None:
        """
        Args:
            interval: 学習ロスを W&B へ送る iteration 間隔。
        """
        self.interval = int(interval)

    @staticmethod
    def _wandb():
        """アクティブな W&B run があれば ``wandb`` モジュールを返す。"""
        try:
            import wandb
        except ImportError:
            return None
        return wandb if wandb.run is not None else None

    def after_train_iter(
        self, runner, batch_idx: int, data_batch=None, outputs=None
    ) -> None:
        """学習ロスを W&B へ記録する。"""
        if outputs is None or not self.every_n_train_iters(runner, self.interval):
            return
        wandb = self._wandb()
        if wandb is None:
            return
        log: dict[str, float] = {}
        for key, value in outputs.items():
            scalar = self._to_scalar(value)
            if scalar is not None:
                log[f"train/{key}"] = scalar
        try:
            log["train/lr"] = float(runner.optim_wrapper.get_lr()["lr"][0])
        except Exception:  # optim_wrapper の実装差に備える。
            pass
        log["epoch"] = runner.epoch + 1
        wandb.log(log, step=runner.iter)

    def after_val_epoch(self, runner, metrics=None) -> None:
        """検証指標を W&B へ記録し、JSONL へ追記する。

        W&B では監視しやすいよう名前空間を分離する:
        ``val/*`` にコア指標（mAP / AP_rare / AP_common / mAP_50 / mAP_75）、
        ``val_per_class/{クラス名}`` に 15 クラスの per-class AP。
        JSONL は学習後の最良 epoch 選定（``_collect_best_metrics``）が
        ``val/{クラス名}_precision`` キーに依存するため、変換せず素のまま残す。
        """
        if not metrics:
            return
        record = {"epoch": runner.epoch, "iter": runner.iter}
        for key, value in metrics.items():
            scalar = self._to_scalar(value)
            if scalar is not None:
                record[key] = scalar

        log_path = Path(runner.work_dir) / "logs" / "val_metrics.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

        wandb = self._wandb()
        if wandb is None:
            return
        payload: dict[str, float] = {}
        for key, value in record.items():
            if key == "iter":
                continue
            if key.startswith("val/") and key.endswith(_PRECISION_SUFFIX):
                # per-class AP は専用名前空間へ（W&B ダッシュボードで分離表示）。
                cls = key[len("val/") : -len(_PRECISION_SUFFIX)]
                payload[f"val_per_class/{cls}"] = value
            else:
                payload[key] = value
        wandb.log(payload, step=runner.iter)

    @staticmethod
    def _to_scalar(value):
        """tensor / np / python 数値を ``float`` へ。数値でなければ ``None``。"""
        if isinstance(value, (int, float)):
            return float(value)
        if hasattr(value, "item"):
            try:
                return float(value.item())
            except Exception:
                return None
        return None

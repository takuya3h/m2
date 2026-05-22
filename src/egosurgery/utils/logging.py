"""W&B + ローカルファイルの二重ロギングユーティリティ。

学習中の指標を W&B（オンライン or オフライン）と実験フォルダ内の
ローカルファイルへ同時に記録する。W&B が利用できない環境でも
ローカルロギングだけは必ず成功するようフォールバックする。

設計方針:
    - ``enabled=True``  -> W&B をオンラインモードで使用
    - ``enabled=False`` -> W&B をオフラインモードで使用（ネット不要）
    - ``wandb`` 未インストール、または ``wandb.init`` 失敗時
      -> W&B を無効化し、ローカルロギングのみ継続

使い方:
    logger = ExperimentLogger(
        experiment_manager=manager,
        wandb_project="egosurgery_multitask",
        wandb_entity=None,
        tags=["s0", "baseline"],
        enabled=True,
        config=resolved_cfg_dict,
    )
    logger.init()                              # W&B run を開始
    logger.log({"train/loss": 0.5}, step=100)  # W&B + ローカルへ記録
    logger.log_metrics({"mAP": 0.45})          # metrics.json へ保存
    logger.finish()                            # W&B run を終了
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # 型注釈専用
    from egosurgery.utils.experiment_manager import ExperimentManager


class ExperimentLogger:
    """W&B とローカルファイルへ二重に記録するロガー。"""

    def __init__(
        self,
        experiment_manager: "ExperimentManager",
        wandb_project: str,
        wandb_entity: str | None = None,
        tags: list[str] | None = None,
        enabled: bool = True,
        config: dict | None = None,
        run_name: str | None = None,
    ) -> None:
        """
        Args:
            experiment_manager: ``setup()`` 済みの :class:`ExperimentManager`。
            wandb_project: W&B プロジェクト名。
            wandb_entity: W&B エンティティ（個人/チーム）。``None`` 可。
            tags: W&B run に付与するタグ。
            enabled: ``True`` でオンライン、``False`` でオフライン記録。
            config: W&B run に保存する設定辞書（resolved config 等）。
            run_name: W&B run 名。``None`` なら W&B 既定の自動命名。
        """
        self.experiment_manager = experiment_manager
        self.wandb_project = wandb_project
        self.wandb_entity = wandb_entity
        self.tags = list(tags) if tags else []
        self.enabled = bool(enabled)
        self.config = config
        self.run_name = run_name

        self._wandb = None          # import 済みの wandb モジュール
        self._run = None            # 生成された wandb run
        self._log_path: Path | None = None  # ローカル JSONL ログのパス

    # ------------------------------------------------------------------ #
    # ライフサイクル
    # ------------------------------------------------------------------ #
    def init(self) -> "ExperimentLogger":
        """ローカルログファイルを準備し、W&B run を開始する。

        W&B の import / init に失敗しても例外は送出せず、
        ローカルロギングのみで継続する。
        """
        exp_dir = Path(self.experiment_manager.exp_dir)
        self._log_path = exp_dir / "logs" / "metrics_log.jsonl"
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_path.touch(exist_ok=True)

        try:
            import wandb
        except ImportError:
            # wandb 未導入 -> 無効化してローカルのみ
            self.enabled = False
            self._wandb = None
            return self

        os.environ.setdefault("WANDB_SILENT", "true")
        try:
            self._run = wandb.init(
                project=self.wandb_project,
                entity=self.wandb_entity,
                name=self.run_name,
                config=self.config,
                tags=self.tags,
                dir=str(exp_dir),
                mode="online" if self.enabled else "offline",
                reinit=True,
            )
            self._wandb = wandb
        except Exception:
            # init 失敗（認証・ネットワーク等） -> ローカルのみで継続
            self._run = None
            self._wandb = None
        return self

    def log(self, data: dict, step: int | None = None) -> None:
        """指標を W&B とローカル JSONL の双方へ記録する。

        Args:
            data: 記録する指標辞書（例: ``{"train/loss": 0.5}``）。
            step: グローバルステップ。``None`` なら省略。
        """
        record = dict(data)
        if step is not None:
            record["_step"] = step

        if self._log_path is not None:
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        if self._wandb is not None and self._run is not None:
            try:
                self._wandb.log(data, step=step)
            except Exception:
                pass  # W&B 側の失敗はローカル記録を妨げない

    def log_metrics(self, metrics: dict) -> None:
        """最終指標を ``metrics.json``（と W&B summary）へ保存する。

        Args:
            metrics: 保存する指標辞書。
        """
        self.experiment_manager.log_metrics(metrics)
        if self._run is not None:
            try:
                self._run.summary.update(dict(metrics))
            except Exception:
                pass

    def finish(self) -> None:
        """W&B run を終了する。W&B 未使用時は何もしない。"""
        if self._wandb is not None and self._run is not None:
            try:
                self._wandb.finish()
            except Exception:
                pass
        self._run = None

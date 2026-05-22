"""学習のエントリーポイント（Hydra アプリケーション）。

``cfg.experiment.step`` に応じてトレーナーを選択する:
    - s0 / s1 / s2  -> StageATrainer（検出ベースライン、Stage A0）
    - それ以外      -> Trainer（ダミートレーナー、フォールバック）

使い方:
    python -m egosurgery.train stage=s0_tool_baseline seed=42
    python -m egosurgery.train stage=s0_tool_baseline model.detection_head=varifocanet \\
        seed=123 logging.wandb_enabled=true

`config_path` は本ファイル（``src/egosurgery/train.py``）から見た
``configs/`` への相対パス。``src/egosurgery/`` -> ``../../configs``。
"""

from __future__ import annotations

import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="../../configs", config_name="default")
def main(cfg: DictConfig) -> None:
    """Hydra が合成した config で、ステージに応じたトレーナーを起動する。"""
    step = str(cfg.experiment.step)
    if step.startswith(("s0", "s1", "s2")):
        from egosurgery.engines.stage_a_trainer import StageATrainer

        trainer = StageATrainer(cfg)
    else:
        # S3 以降の専用トレーナー実装までのフォールバック（ダミートレーナー）。
        from egosurgery.engines.trainer import Trainer

        trainer = Trainer(cfg)

    trainer.setup()
    trainer.run()


if __name__ == "__main__":
    main()

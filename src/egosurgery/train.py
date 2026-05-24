"""学習のエントリーポイント（Hydra アプリケーション）。

``cfg.experiment.step`` と ``cfg.train.real_detector`` に応じてトレーナーを選ぶ:
    - s0/s1/s2 かつ real_detector=true -> MMDetTrainer
      （mmdet で実 VarifocalNet/DINO を COCO 重みから fine-tune。S0 基準点用）
    - s0/s1/s2 かつ real_detector=false -> StageATrainer
      （内蔵 SimpleDetectionHead。スモーク・パイプライン検証用）
    - それ以外 -> Trainer（ダミートレーナー、フォールバック）

使い方:
    python -m egosurgery.train stage=s0_tool_baseline seed=42
    python -m egosurgery.train stage=s0_tool_baseline model.detection_head=varifocanet \\
        seed=123 logging.wandb_enabled=true
    # スモーク（内蔵ヘッド）:
    python -m egosurgery.train stage=s0_tool_baseline train.real_detector=false ...

`config_path` は本ファイル（``src/egosurgery/train.py``）から見た
``configs/`` への相対パス。``src/egosurgery/`` -> ``../../configs``。
"""

from __future__ import annotations

import hydra
from omegaconf import DictConfig


def _select_trainer(cfg: DictConfig):
    """config からトレーナーを選択して構築する。"""
    step = str(cfg.experiment.step)
    is_stage_a = step.startswith(("s0", "s1", "s2"))
    use_real = bool(cfg.get("train", {}).get("real_detector", False))

    if is_stage_a and use_real:
        from egosurgery.engines.mmdet_trainer import MMDetTrainer

        return MMDetTrainer(cfg)
    if is_stage_a:
        from egosurgery.engines.stage_a_trainer import StageATrainer

        return StageATrainer(cfg)

    # S3: 工程認識（弱接続・frozen backbone + PhaseHead）。
    if step.startswith("s3"):
        from egosurgery.engines.phase_trainer import PhaseTrainer

        return PhaseTrainer(cfg)

    # S4 以降の専用トレーナー実装までのフォールバック（ダミートレーナー）。
    from egosurgery.engines.trainer import Trainer

    return Trainer(cfg)


@hydra.main(version_base=None, config_path="../../configs", config_name="default")
def main(cfg: DictConfig) -> None:
    """Hydra が合成した config で、ステージに応じたトレーナーを起動する。"""
    trainer = _select_trainer(cfg)
    trainer.setup()
    trainer.run()


if __name__ == "__main__":
    main()

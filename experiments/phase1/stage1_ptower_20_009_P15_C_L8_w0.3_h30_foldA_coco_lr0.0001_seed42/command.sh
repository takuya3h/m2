#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-03T01:16:02+00:00
python scripts/stage1_ptower_20.py data_setting=P15 init=coco ft_lr=0.0001 fold=A seed=42 action=train candidate=C layers=8 smoothing_weight=0.3 history=30 device=cuda:0 cache=data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz manifest_dir=data/processed/phase_manifest backbone_tag=coco_r50_ft800_lr0.0001 desc_suffix=_coco_lr0.0001

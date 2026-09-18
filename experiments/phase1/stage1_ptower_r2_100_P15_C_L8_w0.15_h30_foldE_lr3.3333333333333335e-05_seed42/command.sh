#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T06:15:16+00:00
python scripts/stage1_ptower_r2.py ft_lr=3.3333333333333335e-05 fold=E seed=42 action=train candidate=C layers=8 smoothing_weight=0.15 history=30 device=cuda:0 cache=data/processed/stage1_features/r2_ft_lr3.3333333333333335e-05_foldE_seed42/all_gap.npz backbone_tag=imagenet_r50_v1_ft_lr3.3333333333333335e-05 desc_suffix=_lr3.3333333333333335e-05

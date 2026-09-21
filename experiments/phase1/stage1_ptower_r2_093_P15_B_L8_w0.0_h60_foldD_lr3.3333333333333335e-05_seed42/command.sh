#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T06:14:14+00:00
python scripts/stage1_ptower_r2.py ft_lr=3.3333333333333335e-05 fold=D seed=42 action=train candidate=B layers=8 smoothing_weight=0.0 history=60 device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr3.3333333333333335e-05_foldD_seed42/all_gap.npz backbone_tag=imagenet_r50_v1_ft_lr3.3333333333333335e-05 desc_suffix=_lr3.3333333333333335e-05

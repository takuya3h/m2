#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T06:12:06+00:00
python scripts/stage1_ptower_r2.py ft_lr=3.3333333333333335e-05 fold=B seed=42 action=train candidate=A layers=8 smoothing_weight=0.0 history=30 device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr3.3333333333333335e-05_foldB_seed42/all_gap.npz backbone_tag=imagenet_r50_v1_ft_lr3.3333333333333335e-05 desc_suffix=_lr3.3333333333333335e-05

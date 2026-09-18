#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T06:05:09+00:00
python scripts/stage1_ptower_r2.py ft_lr=0.0001 fold=A seed=123 action=train candidate=A layers=8 smoothing_weight=0.0 history=30 device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr0.0001_foldA_seed123/all_gap.npz backbone_tag=imagenet_r50_v1_ft_lr0.0001 desc_suffix=_lr0.0001

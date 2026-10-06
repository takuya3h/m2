#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-05T02:40:23+00:00
python scripts/stage1_ptower_20.py data_setting=P20 init=imagenet ft_lr=0.0001 fold=E seed=42 action=train candidate=B layers=8 smoothing_weight=0.0 history=30 device=cuda:1 cache=data/processed/stage1_features/p20_imagenet_lr0.0001_foldE_seed42/all_gap.npz backbone_tag=imagenet_r50_ft800_lr0.0001 desc_suffix=_imagenet_lr0.0001

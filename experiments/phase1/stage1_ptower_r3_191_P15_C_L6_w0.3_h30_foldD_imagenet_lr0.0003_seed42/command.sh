#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T15:01:20+00:00
python scripts/stage1_ptower_r3.py init=imagenet ft_lr=0.0003 fold=D seed=42 action=train candidate=C layers=6 smoothing_weight=0.3 history=30 device=cuda:1 cache=data/processed/stage1_features/r3_imagenet_lr0.0003_foldD_seed42/all_gap.npz backbone_tag=imagenet_r50_ft800_lr0.0003 desc_suffix=_imagenet_lr0.0003

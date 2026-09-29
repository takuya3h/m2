#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T14:58:57+00:00
python scripts/stage1_ptower_r3.py init=imagenet ft_lr=0.0003 fold=B seed=42 action=train candidate=A layers=8 smoothing_weight=0.0 history=30 device=cuda:1 cache=data/processed/stage1_features/r3_imagenet_lr0.0003_foldB_seed42/all_gap.npz backbone_tag=imagenet_r50_ft800_lr0.0003 desc_suffix=_imagenet_lr0.0003

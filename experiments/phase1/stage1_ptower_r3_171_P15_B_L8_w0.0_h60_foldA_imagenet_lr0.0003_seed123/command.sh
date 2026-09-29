#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T14:57:42+00:00
python scripts/stage1_ptower_r3.py init=imagenet ft_lr=0.0003 fold=A seed=123 action=train candidate=B layers=8 smoothing_weight=0.0 history=60 device=cuda:1 cache=data/processed/stage1_features/r3_imagenet_lr0.0003_foldA_seed123/all_gap.npz backbone_tag=imagenet_r50_ft800_lr0.0003 desc_suffix=_imagenet_lr0.0003

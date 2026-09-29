#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T01:58:40+00:00
python scripts/stage1_ptower_r3.py init=imagenet ft_lr=0.0003 fold=A seed=42 action=finetune device=cuda:1 cache=data/processed/stage1_features/r3_imagenet_lr0.0003_foldA_seed42/all_gap.npz

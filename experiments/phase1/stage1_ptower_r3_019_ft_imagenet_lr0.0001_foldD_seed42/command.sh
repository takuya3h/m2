#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-24T22:16:46+00:00
python scripts/stage1_ptower_r3.py init=imagenet ft_lr=0.0001 fold=D seed=42 action=finetune device=cuda:1 cache=data/processed/stage1_features/r3_imagenet_lr0.0001_foldD_seed42/all_gap.npz

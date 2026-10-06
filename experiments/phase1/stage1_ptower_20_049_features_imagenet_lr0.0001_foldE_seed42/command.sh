#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-05T02:29:57+00:00
python scripts/stage1_ptower_20.py data_setting=P20 init=imagenet ft_lr=0.0001 fold=E seed=42 action=extract device=cuda:0 cache=data/processed/stage1_features/p20_imagenet_lr0.0001_foldE_seed42/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_20_022_ft_imagenet_lr0.0001_foldE_seed42/checkpoints/best.pth verify_determinism=false

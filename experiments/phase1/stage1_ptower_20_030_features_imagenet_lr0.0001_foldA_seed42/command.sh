#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-04T20:31:58+00:00
python scripts/stage1_ptower_20.py data_setting=P20 init=imagenet ft_lr=0.0001 fold=A seed=42 action=extract device=cuda:0 cache=data/processed/stage1_features/p20_imagenet_lr0.0001_foldA_seed42/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_20_016_ft_imagenet_lr0.0001_foldA_seed42/checkpoints/best.pth verify_determinism=false

#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T05:55:19+00:00
python scripts/stage1_ptower_r2.py ft_lr=0.0001 fold=A seed=123 action=extract device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr0.0001_foldA_seed123/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_r2_002_ft_lr0.0001_foldA_seed123/checkpoints/best.pth verify_determinism=false

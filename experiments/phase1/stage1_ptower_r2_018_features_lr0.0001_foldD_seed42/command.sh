#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T05:58:57+00:00
python scripts/stage1_ptower_r2.py ft_lr=0.0001 fold=D seed=42 action=extract device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr0.0001_foldD_seed42/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_r2_005_ft_lr0.0001_foldD_seed42/checkpoints/best.pth verify_determinism=false

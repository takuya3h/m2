#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T06:02:15+00:00
python scripts/stage1_ptower_r2.py ft_lr=3.3333333333333335e-05 fold=C seed=42 action=extract device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr3.3333333333333335e-05_foldC_seed42/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_r2_011_ft_lr3.3333333333333335e-05_foldC_seed42/checkpoints/best.pth verify_determinism=false

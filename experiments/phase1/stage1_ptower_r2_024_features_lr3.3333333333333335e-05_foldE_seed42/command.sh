#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T06:03:22+00:00
python scripts/stage1_ptower_r2.py ft_lr=3.3333333333333335e-05 fold=E seed=42 action=extract device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr3.3333333333333335e-05_foldE_seed42/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_r2_013_ft_lr3.3333333333333335e-05_foldE_seed42/checkpoints/best.pth verify_determinism=false

#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T05:02:34+00:00
python scripts/stage1_ptower_r2.py ft_lr=0.0001 fold=C seed=42 action=finetune device=cuda:0 cache=data/processed/stage1_features/r2_ft_lr0.0001_foldC_seed42/all_gap.npz

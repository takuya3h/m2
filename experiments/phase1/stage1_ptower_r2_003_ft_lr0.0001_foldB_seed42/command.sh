#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-18T04:52:39+00:00
python scripts/stage1_ptower_r2.py ft_lr=0.0001 fold=B seed=42 action=finetune device=cuda:1 cache=data/processed/stage1_features/r2_ft_lr0.0001_foldB_seed42/all_gap.npz

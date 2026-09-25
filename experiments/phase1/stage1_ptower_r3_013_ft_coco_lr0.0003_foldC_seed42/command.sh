#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-24T05:31:16+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0003 fold=C seed=42 action=finetune device=cuda:1 cache=data/processed/stage1_features/r3_coco_lr0.0003_foldC_seed42/all_gap.npz

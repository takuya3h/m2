#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T13:34:06+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0001 fold=B seed=42 action=extract device=cuda:1 cache=data/processed/stage1_features/r3_coco_lr0.0001_foldB_seed42/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_r3_008_ft_coco_lr0.0001_foldB_seed42/checkpoints/best.pth verify_determinism=false

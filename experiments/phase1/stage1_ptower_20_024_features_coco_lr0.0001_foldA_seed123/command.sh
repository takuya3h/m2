#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-04T19:29:18+00:00
python scripts/stage1_ptower_20.py data_setting=P20 init=coco ft_lr=0.0001 fold=A seed=123 action=extract device=cuda:0 cache=data/processed/stage1_features/p20_coco_lr0.0001_foldA_seed123/all_gap.npz checkpoint=experiments/phase1/stage1_ptower_20_011_ft_coco_lr0.0001_foldA_seed123/checkpoints/best.pth verify_determinism=false

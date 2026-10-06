#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-03T01:09:48+00:00
python scripts/stage1_ptower_20.py data_setting=P15 init=coco ft_lr=0.0001 fold=A seed=42 action=extract device=cuda:0 cache=data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz manifest_dir=data/processed/phase_manifest checkpoint=experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth verify_determinism=false

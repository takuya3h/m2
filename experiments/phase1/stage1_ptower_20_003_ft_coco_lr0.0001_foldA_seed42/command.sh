#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-02T18:30:37+00:00
python scripts/stage1_ptower_20.py data_setting=P15 init=coco ft_lr=0.0001 fold=A seed=42 action=finetune device=cuda:0 cache=data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz manifest_dir=data/processed/phase_manifest

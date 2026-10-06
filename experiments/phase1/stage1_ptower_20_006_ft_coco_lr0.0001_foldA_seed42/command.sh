#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-02T21:17:46+00:00
python scripts/stage1_ptower_20.py data_setting=P20 init=coco ft_lr=0.0001 fold=A seed=42 action=finetune device=cuda:1 cache=data/processed/stage1_features/p20_coco_lr0.0001_foldA_seed42/all_gap.npz

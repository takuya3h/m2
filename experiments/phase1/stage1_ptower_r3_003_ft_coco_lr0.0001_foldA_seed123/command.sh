#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-23T13:32:23+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0001 fold=A seed=123 action=finetune device=cuda:1 cache=data/processed/stage1_features/r3_coco_lr0.0001_foldA_seed123/all_gap.npz

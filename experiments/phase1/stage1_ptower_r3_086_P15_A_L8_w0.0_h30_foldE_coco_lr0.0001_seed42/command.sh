#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T14:43:19+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0001 fold=E seed=42 action=train candidate=A layers=8 smoothing_weight=0.0 history=30 device=cuda:1 cache=data/processed/stage1_features/r3_coco_lr0.0001_foldE_seed42/all_gap.npz backbone_tag=coco_r50_ft800_lr0.0001 desc_suffix=_coco_lr0.0001

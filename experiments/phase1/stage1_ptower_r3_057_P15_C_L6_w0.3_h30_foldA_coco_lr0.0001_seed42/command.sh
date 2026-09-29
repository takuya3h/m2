#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T14:38:33+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0001 fold=A seed=42 action=train candidate=C layers=6 smoothing_weight=0.3 history=30 device=cuda:1 cache=data/processed/stage1_features/r3_coco_lr0.0001_foldA_seed42/all_gap.npz backbone_tag=coco_r50_ft800_lr0.0001 desc_suffix=_coco_lr0.0001

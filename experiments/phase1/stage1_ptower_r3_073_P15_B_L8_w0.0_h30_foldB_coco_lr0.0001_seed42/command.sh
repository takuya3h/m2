#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T14:41:13+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0001 fold=B seed=42 action=train candidate=B layers=8 smoothing_weight=0.0 history=30 device=cuda:0 cache=data/processed/stage1_features/r3_coco_lr0.0001_foldB_seed42/all_gap.npz backbone_tag=coco_r50_ft800_lr0.0001 desc_suffix=_coco_lr0.0001

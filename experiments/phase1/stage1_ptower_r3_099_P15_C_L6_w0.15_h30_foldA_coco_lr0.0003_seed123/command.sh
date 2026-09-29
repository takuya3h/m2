#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-25T14:45:13+00:00
python scripts/stage1_ptower_r3.py init=coco ft_lr=0.0003 fold=A seed=123 action=train candidate=C layers=6 smoothing_weight=0.15 history=30 device=cuda:0 cache=data/processed/stage1_features/r3_coco_lr0.0003_foldA_seed123/all_gap.npz backbone_tag=coco_r50_ft800_lr0.0003 desc_suffix=_coco_lr0.0003

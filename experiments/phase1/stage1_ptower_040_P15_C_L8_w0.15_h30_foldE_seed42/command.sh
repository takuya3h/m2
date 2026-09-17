#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-17T16:06:36+00:00
python scripts/stage1_ptower.py action=train device=cuda:0 candidate=C layers=8 smoothing_weight=0.15 history=30 fold=E seed=42

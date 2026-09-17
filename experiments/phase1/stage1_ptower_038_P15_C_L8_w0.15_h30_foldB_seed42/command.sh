#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-09-17T16:06:13+00:00
python scripts/stage1_ptower.py action=train device=cuda:1 candidate=C layers=8 smoothing_weight=0.15 history=30 fold=B seed=42

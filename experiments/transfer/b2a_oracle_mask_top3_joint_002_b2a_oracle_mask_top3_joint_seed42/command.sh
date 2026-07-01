#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-06-29T06:32:23+00:00
python scripts/train_b2a.py --seed 42 --epochs 50 --tool-source oracle --mask-tool-dims 0,6,9 --description-override b2a_oracle_mask_top3_joint

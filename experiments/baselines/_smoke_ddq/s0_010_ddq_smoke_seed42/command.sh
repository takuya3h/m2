#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-05-28T08:12:10+00:00
python /home/ubuntu/slocal2/m2/src/egosurgery/train.py stage=s0_tool_baseline model.detection_head=ddq seed=42 experiment.description=ddq_smoke train.real_detector=true train.epochs=1 train.batch_size=2 train.num_workers=2 train.lr_scaling_mode=linear data.limit=20 logging.wandb_enabled=false

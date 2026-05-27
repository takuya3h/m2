#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-05-26T02:21:45+00:00
python /home/ubuntu/slocal2/m2/src/egosurgery/train.py stage=s0_tool_baseline model.detection_head=varifocanet seed=456 experiment.description=varifocanet_bbox train.real_detector=true train.epochs=12 train.batch_size=2 train.lr_scaling_mode=linear logging.wandb_enabled=true

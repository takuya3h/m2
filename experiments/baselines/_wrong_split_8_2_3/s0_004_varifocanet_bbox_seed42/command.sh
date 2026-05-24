#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-05-22T22:44:41+00:00
python /home/ubuntu/slocal2/egosurgery_multitask/src/egosurgery/train.py stage=s0_tool_baseline model.detection_head=varifocanet seed=42 experiment.description=varifocanet_bbox train.real_detector=true logging.wandb_enabled=true

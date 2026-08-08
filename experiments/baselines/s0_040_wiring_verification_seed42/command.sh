#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-08-07T21:17:04+00:00
python /home/ubuntu/slocal2/m2/src/egosurgery/train.py stage=s0_tool_baseline +task_id=T-2026-08-09-run-wiring-verification experiment.description=wiring_verification train.real_detector=false model.backbone=dinov2_vits14_reg data.limit=16 data.img_size=224 train.epochs=1 train.freeze_backbone=true data.num_workers=0 logging.wandb_enabled=false seed=42

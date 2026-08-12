#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-05-22T05:53:35+00:00
python /home/ubuntu/slocal2/egosurgery_multitask/src/egosurgery/train.py stage=s0_tool_baseline model.detection_head=mask_dino seed=123 experiment.description=maskdino_bbox logging.wandb_enabled=true model.backbone=dinov2_vits14_reg data.img_size=392 data.batch_size=8 train.epochs=8 train.freeze_backbone=true optimizer.lr=0.001 logging.wandb_enabled=false

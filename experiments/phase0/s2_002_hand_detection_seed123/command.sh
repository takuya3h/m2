#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-05-23T07:39:46+00:00
python /home/ubuntu/slocal2/egosurgery_multitask/src/egosurgery/train.py stage=s2_hand model.detection_head=mask_dino seed=123 experiment.description=hand_detection train.real_detector=true train.load_from=experiments/baselines/s0_001_maskdino_bbox_seed42/best_val_mAP_epoch_5.pth logging.wandb_enabled=true

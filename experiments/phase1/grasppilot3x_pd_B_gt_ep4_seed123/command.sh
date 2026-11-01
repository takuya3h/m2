#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 生成日時: 2026-10-31T17:20:16+00:00
python scripts/train_t1b.py --seed 123 --trainable film --task-id T-2026-11-01-grasp-pilot-d --run-name grasppilot3x_pd_B_gt_ep4_seed123 --det-ckpt /home/ubuntu/slocal2/s2fix-bengio-body/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth --grasp-map gt --epochs 4 --fixed-epochs --amp bf16 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/extra/pd_ckpt/grasppilot3x_pd_B_gt_ep4_seed123 --save-trainable-only --print-freq 500

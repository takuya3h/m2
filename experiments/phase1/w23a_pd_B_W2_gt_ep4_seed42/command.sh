#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 生成日時: 2026-11-01T22:20:35+00:00
python scripts/train_t1b.py --seed 42 --trainable w2 --task-id T-2026-11-01-stage2-w23-andrew --run-name w23a_pd_B_W2_gt_ep4_seed42 --det-ckpt /home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth --grasp-map gt --epochs 4 --fixed-epochs --amp bf16 --save-predictions-all --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-andrew/pd_ckpt/w23a_pd_B_W2_gt_ep4_seed42 --save-trainable-only --print-freq 500

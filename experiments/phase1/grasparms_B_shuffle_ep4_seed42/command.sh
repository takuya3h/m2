#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 生成日時: 2026-11-06T07:25:13+00:00
python scripts/train_t1b.py --seed 42 --trainable film --task-id T-2026-11-06-grasp-pilot-arms --run-name grasparms_B_shuffle_ep4_seed42 --det-ckpt /home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth --grasp-map pred --grasp-pred-train /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/views/B_shuffle_train.json --grasp-pred-val /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/views/B_shuffle_val.json --epochs 4 --fixed-epochs --amp bf16 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-grasp-pilot-arms/pd_ckpt/grasparms_B_shuffle_ep4_seed42 --save-trainable-only --print-freq 500

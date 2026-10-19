#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 生成日時: 2026-10-19T01:36:12+00:00
python scripts/train_t1b.py --seed 42 --trainable w2 --task-id T-2026-10-18-stage2-pilot-folda --run-name stage2pilot_pd_P1-W2_pred_CF_seed42 --det-ckpt /home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth --signal-train /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/cf/P0_train.npz --signal-val /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P0_val.npz --patience 2 --epochs 4 --best-excludes-init --amp bf16 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/pd_ckpt/stage2pilot_pd_P1-W2_pred_CF_seed42 --save-trainable-only --print-freq 500

#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 生成日時: 2026-10-19T17:44:09+00:00
python scripts/train_t1b.py --seed 42 --trainable film --task-id T-2026-10-19-stage2-pilot-four-new-types --run-name stage2four_pd_DX_pred_noCF_ep4_seed42 --det-ckpt /home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth --signal-train /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P0_train.npz --signal-val /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P0_val.npz --epochs 4 --fixed-epochs --amp bf16 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/pd_ckpt/stage2four_pd_DX_pred_noCF_ep4_seed42 --save-trainable-only --print-freq 500

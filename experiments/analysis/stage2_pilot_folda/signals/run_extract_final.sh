#!/usr/bin/env bash
# Task C: 確定塔の検出側の信号（非公式 T-2026-10-18-stage2-pilot-folda）。train は GPU 0、val は GPU 1。
set -uo pipefail
BODY=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final
L=$BODY/experiments/analysis/stage2_pilot_folda/signals
cd "$BODY"
source .venv-relation-detr/bin/activate
export CUDA_HOME=/usr/local/cuda
CK=experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth
ANN=data/annotations/egosurgery_tool_folds/A
CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/extract_det_signals.py --ckpt $CK --ann-dir $ANN --part train \
  --videos 01,02,03,06,08,11,12,13,14,15 --out-dir $S --k 11 > $L/extract_det_train.log 2>&1 &
P1=$!
CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/extract_det_signals.py --ckpt $CK --ann-dir $ANN --part val \
  --videos 09,10 --out-dir $S --k 11 --check-map > $L/extract_det_val.log 2>&1 &
P2=$!
wait $P1; R1=$?
wait $P2; R2=$?
echo "train rc=$R1 val rc=$R2"

#!/usr/bin/env bash
# Task C-4: 凍結した D* の train の出力（上位 300、確信度の下限なし）を GPU 2 枚に半分ずつ作る（非公式 T-2026-10-19-stage2-pilot-four-new-types）。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
OV=/home/ubuntu/slocal2/s2fix-bengio-body
FOUR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types
cd "$WT"
# shellcheck disable=SC1091
source "$OV/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A PYTHONUTF8=1
for i in 0 1; do
  CUDA_VISIBLE_DEVICES=$i python scripts/stage2pilot/xq_missed.py predict --split train --shard $i/2 \
    --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --out "$FOUR/xq/dstar_train_top300_shard$i.json.gz" > "$WT/experiments/analysis/stage2_pilot_four/xq/predict_train_shard$i.log" 2>&1 &
done
wait
echo "done"

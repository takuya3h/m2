#!/usr/bin/env bash
# 利用者の指示 (3) の計測（非公式 T-2026-11-01-stage2-w23-andrew）。GPU 0 に DX の W1・W2・W3、GPU 1 に案 B の W1・W2・W3 を
# 同時に 3 本ずつ置き（W1 の実績と同じ 1 枚 3 本）、1 step の秒数と記憶の山を測る。腕は正解。nvidia-smi で GPU の使用量も 5 秒ごとに残す。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
R=$M/experiments/analysis/stage2_w23_andrew/bench
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
F=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final
nvidia-smi --query-gpu=timestamp,index,memory.used,utilization.gpu,power.draw --format=csv -l 5 > "$R/nvsmi.csv" &
SMI=$!
for W in W1 W2 W3; do
  CUDA_VISIBLE_DEVICES=0 python scripts/w23/w23a_bench.py --type DX --w $W --cfg $M/configs/stage2pilot/pd_dec_xattn_d9.py \
    --signal-train $F/P-GT_train.npz --out "$R/DX_$W.json" > "$R/DX_$W.log" 2>&1 &
  CUDA_VISIBLE_DEVICES=1 python scripts/w23/w23a_bench.py --type B --w $W --cfg $M/configs/stage2pilot/pd_graspmap_d5.py \
    --grasp-map gt --out "$R/B_$W.json" > "$R/B_$W.log" 2>&1 &
done
wait %2 %3 %4 %5 %6 %7
kill $SMI

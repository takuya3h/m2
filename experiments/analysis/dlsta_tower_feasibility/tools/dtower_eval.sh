#!/usr/bin/env bash
# Task F (T-2026-10-19-dlsta-tower-feasibility): evaluate a detector-tower checkpoint on fold A's val
# with the existing tool, as scripts/eval_stage1_dtower.sh does (2 processes, same config), but
# writing outside the repo so the recorded eval_val.json is left untouched.
#
#   dtower_eval.sh <gpus e.g. 0,1> <port> <checkpoint> <out.json>
set -uo pipefail
GPUS="$1"; PORT="$2"; CKPT="$3"; OUT="$4"
BODY="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$BODY"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_VISIBLE_DEVICES="$GPUS"
export CUDA_HOME=/usr/local/cuda
export EGO_ROOT="$BODY/data/raw/ego"
export EGO_ANN_DIR="$BODY/data/annotations/egosurgery_tool_folds/A"
mkdir -p "$(dirname "$OUT")"
accelerate launch --num_processes 2 --main_process_port "$PORT" \
    "$BODY/scripts/eval_relation_detr_map.py" \
    --config configs/train_config_egosurgery_seed42.py --checkpoint "$CKPT" --split val --out "$OUT" \
    > "${OUT%.json}.log" 2>&1
echo "rc=$? $OUT"

#!/usr/bin/env bash
# B1 素朴MTL 起動ラッパ（②特徴レベル結合・最初の結合手法）。
#
# 単GPU・.venv-relation-detr（ninja を PATH に載せるため venv 有効化）。1 run = 1 seed × 1 weighting。
# 使い方:
#   scripts/run_b1.sh <weighting:fixed|uncertainty> <seed> <gpu_index>
# 例（2 GPU 並列）:
#   scripts/run_b1.sh fixed 42 0
#   scripts/run_b1.sh fixed 123 1
set -euo pipefail
WEIGHTING="${1:?weighting=fixed|uncertainty}"
SEED="${2:?seed}"
GPU="${3:-0}"

# BODY はスクリプト位置から解決する（特定ホストの絶対パス固定は別サーバーで壊れる）。
BODY="${EGO_BODY:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG_DIR="$BODY/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/b1_${WEIGHTING}_seed${SEED}.log"
WORK="$BODY/experiments/transfer/b1_work_${WEIGHTING}_seed${SEED}"

# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"   # ninja を PATH に
echo "[run_b1] weighting=$WEIGHTING seed=$SEED gpu=$GPU work=$WORK log=$LOG"
CUDA_VISIBLE_DEVICES="$GPU" B1_WORK_DIR="$WORK" \
  python "$BODY/scripts/train_b1_mtl.py" \
    --weighting "$WEIGHTING" --seed "$SEED" --epochs 12 \
    > "$LOG" 2>&1
echo "[run_b1] DONE -> $WORK"

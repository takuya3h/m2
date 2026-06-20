#!/usr/bin/env bash
# T1b Phase→Det 起動ラッパ（MT4MTL-KD-style §4.6・①予測相互作用・server B 本走）。
#
# .venv-relation-detr（ninja を PATH に・MS-Deform-Attn JIT）。warm-start init=s0_016。
# 前提: scripts/extract_phase_context.py で phase context を抽出済み。
#
# 使い方:
#   scripts/run_t1b.sh <seed> <gpu> [extra args...]
# 例（注入本体 + §4.6 対照）:
#   scripts/run_t1b.sh 42 0                 # phase 注入 fine-tune
#   scripts/run_t1b.sh 42 1 --zero-ctx      # 対照（注入効果の分離）
set -euo pipefail
SEED="${1:?seed}"
GPU="${2:-0}"
shift $(( $# >= 2 ? 2 : 1 )) || true

BODY=/home/ubuntu/slocal2/m2
LOG_DIR="$BODY/logs"; mkdir -p "$LOG_DIR"
TAG="t1b_seed${SEED}"
for a in "$@"; do [ "$a" = "--zero-ctx" ] && TAG="t1b_zeroctx_seed${SEED}"; done
LOG="$LOG_DIR/${TAG}.log"

# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
echo "[run_t1b] seed=$SEED gpu=$GPU tag=$TAG log=$LOG extra=$*"
CUDA_VISIBLE_DEVICES="$GPU" T1B_WORK_DIR="/tmp/${TAG}" \
  python "$BODY/scripts/train_t1b.py" --seed "$SEED" --epochs 6 "$@" \
    > "$LOG" 2>&1
echo "[run_t1b] DONE seed=$SEED tag=$TAG"

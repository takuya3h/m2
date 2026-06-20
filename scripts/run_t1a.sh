#!/usr/bin/env bash
# T1a region-token→工程 起動ラッパ（Tier-1 主力⭐ TAPIS/GraSP 型・②系統）。
#
# 本体 .venv（キャッシュのみ読む）。region-token は事前抽出済みである必要がある:
#   data/processed/t1a_regiontoken/relation_detr_seed42/{train,val,test}_regiontoken.npz
#   （未抽出なら: source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda-11.8
#     && python scripts/extract_t1a_regiontoken.py --subset <split> --limit 0）
#
# 使い方:
#   scripts/run_t1a.sh <seed> <gpu_index> [extra args...]
# 例（3-seed・GPU 空き次第）:
#   scripts/run_t1a.sh 42 0
#   scripts/run_t1a.sh 123 0
#   scripts/run_t1a.sh 456 0
set -euo pipefail
SEED="${1:?seed}"
GPU="${2:-0}"
shift $(( $# >= 2 ? 2 : 1 )) || true

BODY=/home/ubuntu/slocal2/m2
LOG_DIR="$BODY/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/t1a_seed${SEED}.log"

echo "[run_t1a] seed=$SEED gpu=$GPU log=$LOG extra=$*"
CUDA_VISIBLE_DEVICES="$GPU" \
  "$BODY/.venv/bin/python" "$BODY/scripts/train_t1a.py" \
    --seed "$SEED" --epochs 50 "$@" \
    > "$LOG" 2>&1
echo "[run_t1a] DONE seed=$SEED"

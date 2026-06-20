#!/usr/bin/env bash
# B2a 片方向結合 検出→工程 起動ラッパ（Tier-0 必須・①信号レベル）。
#
# 本体 .venv（キャッシュのみ読む・Relation-DETR 非依存）。tool-presence 信号は
# scripts/extract_b2a_detsignal.py で事前抽出済みである必要がある:
#   data/processed/b2a_detsignal/relation_detr_seed42/{train,val,test}_toolpresence.npz
#
# 使い方:
#   scripts/run_b2a.sh <seed> <gpu_index>
# 例（3-seed・GPU 空き次第）:
#   scripts/run_b2a.sh 42 1
#   scripts/run_b2a.sh 123 1
#   scripts/run_b2a.sh 456 1
set -euo pipefail
SEED="${1:?seed}"
GPU="${2:-0}"

BODY=/home/ubuntu/slocal2/m2
LOG_DIR="$BODY/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/b2a_seed${SEED}.log"

echo "[run_b2a] seed=$SEED gpu=$GPU log=$LOG"
CUDA_VISIBLE_DEVICES="$GPU" \
  "$BODY/.venv/bin/python" "$BODY/scripts/train_b2a.py" \
    --seed "$SEED" --epochs 50 \
    > "$LOG" 2>&1
echo "[run_b2a] DONE seed=$SEED"

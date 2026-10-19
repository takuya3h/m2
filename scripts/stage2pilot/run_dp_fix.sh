#!/usr/bin/env bash
# DP（検出から工程）の固定の長さの腕をまとめて回す（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle、SPEC §4 Task E）。
#
#   scripts/stage2pilot/run_dp_fix.sh <型:腕> [<型:腕> ...]
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。既に在る run（同じ型・腕、試走でない）は飛ばす。
#
# 4 epoch 学習し、途中で止めず、4 epoch 目の状態を結果にする（dp_train.py --fixed-epochs 4）。それ以外の設定
# （受け取り手、界面の型と容量、学習率一定、重み減衰、平滑化、seed）は前回の run_dp_batch.sh と同じ。D3 の型は
# 前回と同じく重複しない query の上位 K（--inst-variant uq）。run は experiments/phase1/stage2fix_dp_*、界面の重みは本契約の置き場。
set -uo pipefail
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
LOGS=/home/ubuntu/slocal2/stage2pilot_store/$TASK/queues
SEED=42
mkdir -p "$LOGS"
cd "$BODY"
# shellcheck disable=SC1091
source .venv/bin/activate
# shellcheck disable=SC1091
source scripts/load_env.sh > /dev/null 2>&1
export PYTHONPATH=src:scripts
for spec in "$@"; do
  TYPE=${spec%%:*}; ARM=${spec#*:}
  if grep -l '"phase_jaccard"' experiments/phase1/stage2fix_dp_*_"${TYPE}_${ARM}_ep4_seed${SEED}"/metrics.json > /dev/null 2>&1; then
    echo "[dp_fix] 済み $TYPE $ARM"; continue
  fi
  EXTRA=()
  case "$TYPE" in D3-*) EXTRA=(--inst-variant uq) ;; esac
  LOG="$LOGS/dp_${TYPE}_${ARM}_${SEED}.log"
  python scripts/stage2pilot/dp_train.py train --type "$TYPE" --arm "$ARM" --seed "$SEED" "${EXTRA[@]}" \
    --fixed-epochs 4 --task-id "$TASK" --exp-prefix stage2fix_dp > "$LOG" 2>&1
  echo "[dp_fix] $TYPE $ARM rc=$? $(grep -E 'DP_RUN_COMPLETE|Error' "$LOG" | tail -1)"
done

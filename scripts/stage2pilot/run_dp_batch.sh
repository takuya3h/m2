#!/usr/bin/env bash
# DP の腕をまとめて回す（非公式 T-2026-10-18-stage2-pilot-folda）。
#
#   scripts/stage2pilot/run_dp_batch.sh <inst_variant|-> <型:腕> [<型:腕> ...]
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 123 456。既に在る run（同じ型・腕・seed）は飛ばす。
set -uo pipefail
VARIANT="$1"; shift
BODY=/home/ubuntu/slocal2/m2
cd "$BODY"
# shellcheck disable=SC1091
source .venv/bin/activate
# shellcheck disable=SC1091
source scripts/load_env.sh > /dev/null 2>&1
export PYTHONPATH=src:scripts
for spec in "$@"; do
  TYPE=${spec%%:*}; ARM=${spec#*:}
  for SEED in 42 123 456; do
    if ls -d experiments/phase1/stage2pilot_dp_*_"${TYPE}_${ARM}_seed${SEED}" > /dev/null 2>&1; then
      echo "[dp_batch] 済み $TYPE $ARM $SEED"; continue
    fi
    EXTRA=()
    [ "$VARIANT" != "-" ] && EXTRA=(--inst-variant "$VARIANT")
    python scripts/stage2pilot/dp_train.py train --type "$TYPE" --arm "$ARM" --seed "$SEED" "${EXTRA[@]}" \
      > "/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/queues/dp_${TYPE}_${ARM}_${SEED}.log" 2>&1
    echo "[dp_batch] $TYPE $ARM $SEED rc=$? $(grep -E 'DP_RUN_COMPLETE|Error' "/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/queues/dp_${TYPE}_${ARM}_${SEED}.log" | tail -1)"
  done
done

#!/usr/bin/env bash
# B2a-RegionOnly: GAP 削除して tool-pres 15d のみ (pred + oracle) × 3-seed = 6 run
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_pred() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap \
    --description-override b2a_regiononly_pred \
    > "logs/b2a_regiononly_pred_seed${seed}.log" 2>&1
}
run_oracle() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --tool-source oracle \
    --description-override b2a_regiononly_oracle \
    > "logs/b2a_regiononly_oracle_seed${seed}.log" 2>&1
}

for S in 42 123 456; do
  echo "[seed $S] pred(GPU0) + oracle(GPU1) ..."
  run_pred "$S" 0 & pa=$!
  run_oracle "$S" 1 & pb=$!
  wait "$pa"; wait "$pb"
done
echo "================ 完了 ================"
for variant in pred oracle; do
  for S in 42 123 456; do
    echo "-- b2a_regiononly_${variant} seed${S} --"
    tail -1 "logs/b2a_regiononly_${variant}_seed${S}.log"
  done
done

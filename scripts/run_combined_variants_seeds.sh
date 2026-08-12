#!/usr/bin/env bash
# 2 つの追加 combined 変種 × 3-seed = 6 run
#   variant A: T1a-combined-oracle (GAP+region+oracle tool-pres)
#   variant B: T1a-Shuffle + oracle tool-pres (region shuffle で破壊 + oracle 復活試験)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_combined_oracle() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --add-toolpresence --toolpresence-source oracle \
    --description t1a_combined_oracle \
    > "logs/combined_oracle_seed${seed}.log" 2>&1
}

run_shuffle_oracle() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --region-shuffle \
    --add-toolpresence --toolpresence-source oracle \
    --description t1a_shuffle_oracle \
    > "logs/shuffle_oracle_seed${seed}.log" 2>&1
}

# 6 run を 2 GPU 並列で 3 wave
for S in 42 123 456; do
  echo "[seed $S] combined-oracle(GPU0) + shuffle-oracle(GPU1) ..."
  run_combined_oracle "$S" 0 & pa=$!
  run_shuffle_oracle "$S" 1 & pb=$!
  wait "$pa"; wait "$pb"
done
echo "================ 完了 ================"
for variant in combined_oracle shuffle_oracle; do
  for S in 42 123 456; do
    echo "-- ${variant} seed${S} --"
    tail -1 "logs/${variant}_seed${S}.log"
  done
done

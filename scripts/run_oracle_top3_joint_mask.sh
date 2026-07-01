#!/usr/bin/env bash
# Top3 (Bipolar/NH/Scalpel) を同時 mask した B2a-oracle 3-seed
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_one() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --tool-source oracle --mask-tool-dims 0,6,9 \
    --description-override b2a_oracle_mask_top3_joint \
    > "logs/oracle_top3_joint_seed${seed}.log" 2>&1
}

echo "[wave 1] seed42(GPU0) + seed123(GPU1) ..."
run_one 42 0 & pa=$!
run_one 123 1 & pb=$!
wait "$pa"; wait "$pb"
echo "[wave 2] seed456(GPU0) ..."
run_one 456 0

for S in 42 123 456; do
  echo "-- seed$S --"
  tail -1 "logs/oracle_top3_joint_seed${S}.log"
done

#!/usr/bin/env bash
# B2a-RegionOnly-oracle で Top3 (0,6,9) 同時 mask × 3-seed = 3 run
# +0.0680 のうち Top3 が支配するか最終検証
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_one() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --tool-source oracle \
    --mask-tool-dims 0,6,9 \
    --description-override b2a_regiononly_oracle_mask_top3 \
    > "logs/b2a_ro_oracle_top3_seed${seed}.log" 2>&1
}

echo "[wave 1] seed42(GPU0) + seed123(GPU1) ..."
run_one 42 0 & pa=$!
run_one 123 1 & pb=$!
wait "$pa"; wait "$pb"
echo "[wave 2] seed456(GPU0) ..."
run_one 456 0
echo "================ 完了 ================"
for S in 42 123 456; do
  echo "-- seed$S --"
  tail -1 "logs/b2a_ro_oracle_top3_seed${S}.log"
done

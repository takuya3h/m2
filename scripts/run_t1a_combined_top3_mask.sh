#!/usr/bin/env bash
# T1a-Combined (GAP+region+tool-pres) で region-token と tool-pres 両方の Top3 を同時 mask
# region-token slot 0,6,9 mask + train_b2a.py の tool-presence の dim 0,6,9 は手動で
# (train_t1a.py は --add-toolpresence で B2a の tool-pres も使う、これも mask したい)
# シンプル化: region-token のみ Top3 mask、tool-pres は素通し → combined vs combined+region-Top3 mask
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_one() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --add-toolpresence \
    --mask-region-tool-dims 0,6,9 \
    --description t1a_combined_region_top3_mask \
    > "logs/t1a_combined_top3_seed${seed}.log" 2>&1
}

echo "[wave 1] seed42(GPU1) + seed123(GPU0) 並列..."
run_one 42  1 & pa=$!
run_one 123 0 & pb=$!
wait "$pa"; wait "$pb"
echo "[wave 2] seed456(GPU1)..."
run_one 456 1
for S in 42 123 456; do
  echo "-- seed$S --"
  tail -1 "logs/t1a_combined_top3_seed${S}.log"
done

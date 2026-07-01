#!/usr/bin/env bash
# ============================================================================
# B2a + T1a combined（GAP + region-token + tool-presence = 5903d）3-seed 実行
# B2a base (+0.0383) と T1a base (+0.0497) の相補効果を測定。
# 軽量実験で L1-2 と GPU 共存可。
# ============================================================================
set -euo pipefail

DESC="t1a_b2a_combined"
EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

echo "================ B2a+T1a combined 3-seed (in_dim=5903) ================"
echo " 比較: B2a base (+0.0383) と T1a base (+0.0497) の相補/累積効果"
echo "======================================================================="

run_one() {
  local seed="$1" gpu="$2" log="$3"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs "$EPOCHS" --add-toolpresence \
    --description "$DESC" > "$log" 2>&1
}

echo "[wave 1] seed42(GPU0) + seed123(GPU1) 並列 ..."
run_one 42  0 "logs/combined_seed42.log"  &
pa=$!
run_one 123 1 "logs/combined_seed123.log" &
pb=$!
wait "$pa"; wait "$pb"

echo "[wave 2] seed456(GPU0) ..."
run_one 456 0 "logs/combined_seed456.log"

echo ""
echo "================ 完了 ================"
for S in "${SEEDS[@]}"; do
  echo "-- seed$S --"
  tail -2 "logs/combined_seed${S}.log"
done

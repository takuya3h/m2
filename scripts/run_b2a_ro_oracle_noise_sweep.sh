#!/usr/bin/env bash
# 検出器精度 → phase acc transfer function 推定:
# B2a-RegionOnly-oracle (15d only) の tool-pres を確率 p で flip。
# p ∈ {0.05, 0.10, 0.20, 0.30} × 3-seed = 12 run。
# 実効精度 (1-p) → mean acc の曲線で「検出器を p pt 改善すれば phase が何 pt 上がるか」が定量化。
# L1-2 と GPU 共存（GPU1 のみ使用、TeCNO 軽量）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

NOISE_RATES=(0.05 0.10 0.20 0.30)
SEEDS=(42 123 456)
GPU=1  # L1-2 が GPU0 占有中なので GPU1 のみ

run_one() {
  local seed="$1" rate="$2"
  local tag; tag=$(printf "%03d" "$(echo "$rate * 100 / 1" | bc)")
  local desc="b2a_ro_oracle_noise${tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --tool-source oracle \
    --tool-noise-rate "$rate" --description-override "$desc" \
    > "logs/b2a_ro_noise_${tag}_seed${seed}.log" 2>&1
}

for rate in "${NOISE_RATES[@]}"; do
  for S in "${SEEDS[@]}"; do
    echo "[noise=${rate}, seed=${S}] GPU=${GPU} ..."
    run_one "$S" "$rate"
  done
done
echo "================ 完了 ================"
for rate in "${NOISE_RATES[@]}"; do
  tag=$(printf "%03d" "$(echo "$rate * 100 / 1" | bc)")
  for S in "${SEEDS[@]}"; do
    echo "-- noise=${rate} seed${S} --"
    tail -1 "logs/b2a_ro_noise_${tag}_seed${S}.log"
  done
done

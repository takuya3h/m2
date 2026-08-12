#!/usr/bin/env bash
# Top3 (Bipolar/Scalpel/NH = dim 0,6,9) 限定 noise injection。
# 「Top3 だけ検出器強化で同等の改善が得られるか」を直接検証。
# noise rate p ∈ {0.10, 0.20, 0.30} × 3-seed = 9 run、GPU1 sequential ~45min。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

NOISE_RATES=(0.10 0.20 0.30)
SEEDS=(42 123 456)
GPU=1

run_one() {
  local seed="$1" rate="$2" rate_tag="$3"
  local desc="b2a_ro_oracle_top3noise_p${rate_tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --tool-source oracle \
    --tool-noise-rate "$rate" --tool-noise-dims "0,6,9" \
    --description-override "$desc" \
    > "logs/b2a_ro_top3noise_p${rate_tag}_seed${seed}.log" 2>&1
}

# rate_tag を bc に依存せず手動で対応付け
declare -A RATE_TAGS=( [0.10]="010" [0.20]="020" [0.30]="030" )

for rate in "${NOISE_RATES[@]}"; do
  tag="${RATE_TAGS[$rate]}"
  for S in "${SEEDS[@]}"; do
    echo "[noise=${rate} (dim 0,6,9), seed=${S}] GPU=${GPU} ..."
    run_one "$S" "$rate" "$tag"
  done
done
echo "================ 完了 ================"
for rate in "${NOISE_RATES[@]}"; do
  tag="${RATE_TAGS[$rate]}"
  for S in "${SEEDS[@]}"; do
    echo "-- noise=${rate}(Top3) seed${S} --"
    tail -1 "logs/b2a_ro_top3noise_p${tag}_seed${S}.log"
  done
done

#!/usr/bin/env bash
# NH (dim 6) 単独 + Bipolar+Scalpel (dim 0,9) 同時の noise sweep
# 9 + 9 = 18 run、GPU1 sequential ~1.5h
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

GPU=1
declare -A RATE_TAGS=( [0.10]="010" [0.20]="020" [0.30]="030" )

run_one() {
  local seed="$1" rate="$2" tag="$3" dims="$4" name="$5"
  local desc="b2a_ro_oracle_${name}noise_p${tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --tool-source oracle \
    --tool-noise-rate "$rate" --tool-noise-dims "$dims" \
    --description-override "$desc" \
    > "logs/b2a_ro_${name}noise_p${tag}_seed${seed}.log" 2>&1
}

# NH (dim 6) 単独
for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[NH noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag" "6" "nh"
  done
done

# Bipolar+Scalpel (dim 0,9) 同時 (NH なし)
for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[Bipolar+Scalpel noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag" "0,9" "bs"
  done
done
echo "================ 完了 ================"

#!/usr/bin/env bash
# 単一 dim noise sweep: Bipolar (dim 0) と Scalpel (dim 9) を別々に noise 適用
# 各 dim の精度向上が phase に与える独立効果を測定 (NH は既に L2-4 oracle で「同等」確定)
# 2 dim × 3 noise × 3 seed = 18 run、GPU1 sequential ~1.5h
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

GPU=1
declare -A RATE_TAGS=( [0.10]="010" [0.20]="020" [0.30]="030" )

run_one() {
  local seed="$1" rate="$2" tag="$3" dim="$4" name="$5"
  local desc="b2a_ro_oracle_${name}noise_p${tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --tool-source oracle \
    --tool-noise-rate "$rate" --tool-noise-dims "$dim" \
    --description-override "$desc" \
    > "logs/b2a_ro_${name}noise_p${tag}_seed${seed}.log" 2>&1
}

# Bipolar (dim 0)
for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[Bipolar noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag" "0" "bipolar"
  done
done

# Scalpel (dim 9)
for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[Scalpel noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag" "9" "scalpel"
  done
done
echo "================ 完了 ================"

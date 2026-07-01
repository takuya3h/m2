#!/usr/bin/env bash
# T1a-Combined-Oracle (region+GAP+oracle tool-pres) で同じ noise sweep
# - region-token は素のまま、oracle tool-pres にのみ noise
# - 「region-token が tool noise を補填できるか」を測定
# 全dim noise × 3 rate × 3 seed = 9 run、GPU1 sequential ~45min
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

GPU=1
declare -A RATE_TAGS=( [0.10]="010" [0.20]="020" [0.30]="030" )

run_one() {
  local seed="$1" rate="$2" tag="$3"
  local desc="t1a_combined_oracle_noise_p${tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 \
    --add-toolpresence --toolpresence-source oracle \
    --tool-noise-rate "$rate" \
    --description "$desc" \
    > "logs/t1a_combined_oracle_noise_p${tag}_seed${seed}.log" 2>&1
}

for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[T1a-Combined noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag"
  done
done
echo "================ 完了 ================"

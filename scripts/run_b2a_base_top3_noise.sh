#!/usr/bin/env bash
# B2a-base (GAP+tool 2063d) で Top3 限定 noise
# GAP は全dim noise を部分補填する → Top3 限定 noise も補填できるか？
# 3 rate × 3 seed = 9 run
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

GPU=0
declare -A RATE_TAGS=( [0.10]="010" [0.20]="020" [0.30]="030" )

run_one() {
  local seed="$1" rate="$2" tag="$3"
  local desc="b2a_base_oracle_top3noise_p${tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --tool-source oracle \
    --tool-noise-rate "$rate" --tool-noise-dims "0,6,9" \
    --description-override "$desc" \
    > "logs/b2a_base_top3noise_p${tag}_seed${seed}.log" 2>&1
}

for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[B2a-base Top3 noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag"
  done
done
echo "================ 完了 ================"

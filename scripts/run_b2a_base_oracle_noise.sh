#!/usr/bin/env bash
# B2a-base (GAP 2048 + tool-pres 15d, drop-gap なし) で noise injection
# 補填主役切り分け: GAP 単独で tool noise を補えるか？
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
  local desc="b2a_base_oracle_noise_p${tag}"
  CUDA_VISIBLE_DEVICES="$GPU" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --tool-source oracle \
    --tool-noise-rate "$rate" \
    --description-override "$desc" \
    > "logs/b2a_base_noise_p${tag}_seed${seed}.log" 2>&1
}

for rate in 0.10 0.20 0.30; do
  tag="${RATE_TAGS[$rate]}"
  for S in 42 123 456; do
    echo "[B2a-base noise=${rate}, seed=${S}]"
    run_one "$S" "$rate" "$tag"
  done
done
echo "================ 完了 ================"

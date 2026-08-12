#!/usr/bin/env bash
# T1a per-tool slot ablation: region-token (15, 256) の各 tool slot を 0 mask (45 run)
set -euo pipefail
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_one() {
  local seed="$1" gpu="$2" dim="$3"
  local desc; desc="t1a_region_mask_$(printf '%02d' "$dim")"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --mask-region-tool-dim "$dim" \
    --description "$desc" > "logs/t1a_region_mask_${desc}_seed${seed}.log" 2>&1
}

for ((dim_a=0; dim_a<15; dim_a+=2)); do
  dim_b=$((dim_a + 1))
  for S in "${SEEDS[@]}"; do
    echo "[dim ${dim_a}+${dim_b}, seed $S]"
    run_one "$S" 0 "$dim_a" & pa=$!
    if [ "$dim_b" -lt 15 ]; then
      run_one "$S" 1 "$dim_b" & pb=$!
      wait "$pa"; wait "$pb"
    else
      wait "$pa"
    fi
  done
done
echo "================ 完了 ================"

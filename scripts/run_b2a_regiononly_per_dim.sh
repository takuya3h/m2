#!/usr/bin/env bash
# B2a-RegionOnly per-dim ablation: 15d only で各 dim を 0 mask して per-dim 寄与（45 run）
# pred + Top3 既存比較対象として B2a-RegionOnly-pred ベースで実行
set -euo pipefail
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_one() {
  local seed="$1" gpu="$2" dim="$3"
  local desc; desc="b2a_regiononly_mask_$(printf '%02d' "$dim")"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --drop-gap --mask-tool-dim "$dim" \
    --description-override "$desc" \
    > "logs/b2a_ro_mask_${desc}_seed${seed}.log" 2>&1
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

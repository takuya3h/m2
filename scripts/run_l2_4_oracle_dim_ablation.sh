#!/usr/bin/env bash
# L2-4 oracle 版: B2a-oracle の各 dim を 0 mask して per-dim 寄与を測定（45 run, 2GPU 並列）
# pred 版との対比で「検出器誤差が per-dim 寄与をどう変えるか」を完全マップ。
set -euo pipefail

SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_one() {
  local seed="$1" gpu="$2" dim="$3"
  local desc; desc="b2a_oracle_mask_$(printf '%02d' "$dim")"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --tool-source oracle \
    --mask-tool-dim "$dim" --description-override "$desc" \
    > "logs/l2_4_oracle_${desc}_seed${seed}.log" 2>&1
}

# dim 0..14 を 2 並列、ただし Top3 (0/6/9) は既に oracle mask 完了済みなので skip
for ((dim_a=0; dim_a<15; dim_a+=2)); do
  dim_b=$((dim_a + 1))
  for S in "${SEEDS[@]}"; do
    echo "[dim ${dim_a}+${dim_b}, seed $S] ..."
    skip_a=0; skip_b=0
    case "$dim_a" in 0|6|9) skip_a=1;; esac
    case "$dim_b" in 0|6|9) skip_b=1;; esac
    if [ "$skip_a" -eq 0 ]; then
      run_one "$S" 0 "$dim_a" & pa=$!
    else
      echo "  (skip dim $dim_a — Top3 既実施)"
      pa=
    fi
    if [ "$dim_b" -lt 15 ] && [ "$skip_b" -eq 0 ]; then
      run_one "$S" 1 "$dim_b" & pb=$!
    else
      [ "$skip_b" -eq 1 ] && echo "  (skip dim $dim_b — Top3 既実施)"
      pb=
    fi
    [ -n "$pa" ] && wait "$pa"
    [ -n "$pb" ] && wait "$pb"
  done
done
echo "================ L2-4 oracle 完走 ================"
for ((dim=0; dim<15; dim++)); do
  case "$dim" in 0|6|9) continue;; esac
  desc="b2a_oracle_mask_$(printf '%02d' "$dim")"
  echo "-- $desc --"
  for S in "${SEEDS[@]}"; do
    log="logs/l2_4_oracle_${desc}_seed${S}.log"
    [ -f "$log" ] && tail -1 "$log"
  done
done

#!/usr/bin/env bash
# ============================================================================
# B2a-oracle で Top3 工程特異 dim (Bipolar/NH/Scalpel) を mask（9 run, 2GPU）
#
# L2-4 で発見した寄与 Top3: dim 9 (Scalpel) -0.0095, dim 0 (Bipolar) -0.0086,
# dim 6 (Needle Holders) -0.0058。これらを oracle で mask して、L2-3 で発見した
# 上限差分 +0.0214 のうち Top3 への依存度を定量化。
#
# 仮説:
#   - oracle Top3 mask で +0.0214 → +0.0050 程度に縮小（Top3 が大半を支配）
#   - その場合「検出器強化は Top3 の per-class AP に集中」が最適戦略を確定
# ============================================================================
set -euo pipefail

DIMS=(0 6 9)        # Bipolar / Needle Holders / Scalpel
SEEDS=(42 123 456)
EPOCHS=50
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

echo "================ B2a-oracle Top3 mask (9 run, 2GPU 並列) ================"
echo " 対象 dim: 0 Bipolar, 6 Needle Holders, 9 Scalpel（L2-4 Top3 寄与）"
echo " 比較: B2a oracle 5-seed mean 0.9583 から、各 dim mask で どれだけ落ちるか"
echo "=========================================================================="

run_one() {
  local seed="$1" gpu="$2" dim="$3"
  local desc
  desc="b2a_oracle_mask_$(printf '%02d' "$dim")"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs "$EPOCHS" --tool-source oracle \
    --mask-tool-dim "$dim" --description-override "$desc" \
    > "logs/oracle_mask_${desc}_seed${seed}.log" 2>&1
}

# 3 dim × 3 seed = 9 run、2 GPU 並列
# wave: (dim0,seed42 GPU0) + (dim6,seed42 GPU1), then dim9 seed42, ...
for S in "${SEEDS[@]}"; do
  echo "[seed $S] wave 1: dim 0(GPU0) + dim 6(GPU1) ..."
  run_one "$S" 0 0 &
  pa=$!
  run_one "$S" 1 6 &
  pb=$!
  wait "$pa"; wait "$pb"

  echo "[seed $S] wave 2: dim 9(GPU0) ..."
  run_one "$S" 0 9
done

echo ""
echo "================ 完了 ================"
for dim in "${DIMS[@]}"; do
  desc="b2a_oracle_mask_$(printf '%02d' "$dim")"
  echo "-- $desc --"
  for S in "${SEEDS[@]}"; do
    log="logs/oracle_mask_${desc}_seed${S}.log"
    [ -f "$log" ] && tail -1 "$log"
  done
done

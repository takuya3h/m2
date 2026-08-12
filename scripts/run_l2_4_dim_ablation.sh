#!/usr/bin/env bash
# ============================================================================
# §18.4 L2-4 15-d ablation（B2a tool-presence の各 dim 寄与を測定）
#
# B2a 入力 = GAP(2048) ⊕ tool-presence(15) のうち、tool-presence の 1 dim を
# 0 mask して 3-seed × 15 dim = 45 run。dim 別の phase acc 低下から、各術具クラスの
# 寄与度を測定（EDA §11 の MI 上位術具と一致するか実験的検証）。
#
# 15 dim × 3 seed = 45 run、2 GPU 並列で約 12h（軽量 0.14 GB / process なので
# L1-2 oracle-phase + L3 と GPU 共存可）。
# ============================================================================
set -euo pipefail

SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

echo "================ §18.4 L2-4 15-d ablation (45 run, 2GPU 並列) ================"
echo " 各 dim を 0 mask して B2a を 50 epoch 学習、phase acc 低下から寄与度を測定"
echo " 比較: B2a base 3-seed (mean phase acc 0.9369) と paired-σ"
echo "==============================================================================="

run_one() {
  local seed="$1" gpu="$2" dim="$3"
  local desc
  desc="b2a_mask_dim_$(printf '%02d' "$dim")"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --mask-tool-dim "$dim" --description-override "$desc" \
    > "logs/l2_4_${desc}_seed${seed}.log" 2>&1
}

# dim 0..14 を 2 並列、各 dim ペアで 3 seed sequence
for ((dim_a=0; dim_a<15; dim_a+=2)); do
  dim_b=$((dim_a + 1))
  for S in "${SEEDS[@]}"; do
    echo "[dim ${dim_a}+${dim_b}, seed $S] GPU0+1 並列起動 ..."
    run_one "$S" 0 "$dim_a" &
    pa=$!
    if [ "$dim_b" -lt 15 ]; then
      run_one "$S" 1 "$dim_b" &
      pb=$!
      wait "$pa"; wait "$pb"
    else
      wait "$pa"
    fi
  done
done

echo ""
echo "================ L2-4 全 45 run 完走 ================"
for ((dim=0; dim<15; dim++)); do
  desc="b2a_mask_dim_$(printf '%02d' "$dim")"
  echo "-- $desc --"
  for S in "${SEEDS[@]}"; do
    log="logs/l2_4_${desc}_seed${S}.log"
    [ -f "$log" ] && tail -1 "$log"
  done
done
echo "次: experiments/transfer/b2a_mask_dim_*/metrics.json を集計し、tool クラス別寄与度を可視化。"

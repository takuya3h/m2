#!/usr/bin/env bash
# ============================================================================
# §18.4 L3 seed 拡張（既存 3-seed → 5-seed 化、paired-σ 強化）
#
# 既存実験の追加 seed (789, 1000) を実行。軽量（特徴キャッシュ + TeCNO のみ、
# GPU memory ~0.14 GB / process）なので、L1-2 oracle-phase (detection 学習,
# GPU memory ~17 GB) と GPU を共存して並列起動できる。
#
# 12 run × 30 min ≈ 3h（2 GPU 並列）:
#   T1a base (789, 1000)
#   T1a-Deep (789, 1000)
#   T1a-RegionOnly (789, 1000)
#   T1a-Shuffle (789, 1000)
#   B2a base (789, 1000)
#   B2a oracle (789, 1000)
#
# 完走後の集計で paired-σ を 5-seed に拡張（Holm-Bonferroni 対応で多重比較補正可）。
# ============================================================================
set -euo pipefail

SEEDS=(789 1000)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

echo "================ §18.4 L3 seed 拡張（5-seed paired-σ 強化）================"
echo " 対象: T1a (base/Deep/RegionOnly/Shuffle) + B2a (base/oracle) × seed 789, 1000"
echo " 軽量実験のため L1-2 oracle-phase と GPU 共存（detection 17GB / TeCNO 0.14GB）"
echo "==========================================================================="

t1a_base() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --description t1a_regiontoken \
    > "logs/l3_t1a_base_seed${seed}.log" 2>&1
}
t1a_deep() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --num-stages 3 --num-layers 10 --num-f-maps 96 \
    --description t1a_deep_3s10l96f \
    > "logs/l3_t1a_deep_seed${seed}.log" 2>&1
}
t1a_region_only() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --region-only --description t1a_region_only \
    > "logs/l3_t1a_region_only_seed${seed}.log" 2>&1
}
t1a_shuffle() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --region-shuffle --description t1a_shuffle \
    > "logs/l3_t1a_shuffle_seed${seed}.log" 2>&1
}
b2a_base() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 \
    > "logs/l3_b2a_base_seed${seed}.log" 2>&1
}
b2a_oracle() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs 50 --tool-source oracle \
    > "logs/l3_b2a_oracle_seed${seed}.log" 2>&1
}

for S in "${SEEDS[@]}"; do
  echo ""
  echo "[seed $S] wave 1: T1a-base(GPU0) + B2a-base(GPU1) ..."
  t1a_base "$S" 0 &
  pa=$!
  b2a_base "$S" 1 &
  pb=$!
  wait "$pa"; wait "$pb"

  echo "[seed $S] wave 2: T1a-Deep(GPU0) + B2a-oracle(GPU1) ..."
  t1a_deep "$S" 0 &
  pa=$!
  b2a_oracle "$S" 1 &
  pb=$!
  wait "$pa"; wait "$pb"

  echo "[seed $S] wave 3: T1a-RegionOnly(GPU0) + T1a-Shuffle(GPU1) ..."
  t1a_region_only "$S" 0 &
  pa=$!
  t1a_shuffle "$S" 1 &
  pb=$!
  wait "$pa"; wait "$pb"
done

echo ""
echo "================ L3 全 12 run 完走 ================"
for variant in t1a_base t1a_deep t1a_region_only t1a_shuffle b2a_base b2a_oracle; do
  for S in "${SEEDS[@]}"; do
    log="logs/l3_${variant}_seed${S}.log"
    [ -f "$log" ] && echo "-- $variant seed$S --" && tail -2 "$log"
  done
done
echo "次: experiments/transfer/ から 5-seed 集計し paired-σ + Holm-Bonferroni で多重比較補正。"

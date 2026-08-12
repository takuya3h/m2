#!/usr/bin/env bash
# ============================================================================
# T1a-RegionOnly（GAP を捨てて region-token のみ入力, T1a の 1 点 ablation）
# 3-seed 実行（lecun GPU 0/1 並列）。
#
# 既存 T1a base との 1 点ablation:
#   T1a base       : in_dim = GAP(2048) + region(3840) = 5888d
#   T1a-RegionOnly : in_dim = region(3840)d           （GAP を捨てる）
#
# 仮説:
#   - もし T1a-RegionOnly ≈ T1a base なら GAP は冗長で region のみで十分（T1a の最小構成確定）
#   - もし T1a-RegionOnly < T1a base なら GAP は補完情報（両方必要を実証）
#
# 入力・学習率・loss・eval recipe・分母（S4 base 0.8986±0.0034）はすべて T1a base と同一。
# 軽量実験（特徴キャッシュ利用・50 epoch ≈ 30 分 / seed）。
#
# 使い方:
#   bash scripts/run_t1a_region_only_seeds.sh
# ============================================================================
set -euo pipefail

DESC="t1a_region_only"
EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }

# .env を source（NOTION_API_KEY/NOTION_DB_ID をロード・自動投稿のため）
if [ -f "$ROOT/.env" ]; then
  set -a; source "$ROOT/.env"; set +a
fi

[ -f "data/processed/t1a_regiontoken/relation_detr_seed42/train_regiontoken.npz" ] || \
  { echo "[ERR] T1a region-token キャッシュが無い"; exit 1; }

echo "================ T1a-RegionOnly 3-seed (GAP 削除 ablation) ================"
echo " DESC=$DESC epochs=$EPOCHS region_only=True"
echo " in_dim = 3840 (region のみ・GAP 2048 削除)"
echo " 比較: T1a base 3-seed (in_dim=5888) との 1 点 ablation"
echo " 分母: S4 base 0.8986±0.0034 (T1a base mean 0.9483, Δ=+0.0497)"
echo "============================================================================"

run_one() {
  local seed="$1" gpu="$2" log="$3"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs "$EPOCHS" --region-only \
    --description "$DESC" \
    > "$log" 2>&1
}

# wave 1: seed42(GPU0) + seed123(GPU1)
echo "[wave 1] seed42(GPU0) + seed123(GPU1) 並列起動 ..."
run_one 42  0 "logs/t1a_region_only_seed42.log"  &
pa=$!
run_one 123 1 "logs/t1a_region_only_seed123.log" &
pb=$!
wait "$pa"; wait "$pb"
echo "[wave 1] 完了"

# wave 2: seed456(GPU0)
echo "[wave 2] seed456(GPU0) 単独 ..."
run_one 456 0 "logs/t1a_region_only_seed456.log"
echo "[wave 2] 完了"

echo "================ 完了・サマリ ================"
for S in "${SEEDS[@]}"; do
  echo "-- seed$S --"
  tail -3 "logs/t1a_region_only_seed${S}.log"
done
echo "次: experiments/transfer/t1a_region_only_*/metrics.json を集計し、T1a base 3-seed と paired-σ で Δ 判定。"

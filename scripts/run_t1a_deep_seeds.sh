#!/usr/bin/env bash
# ============================================================================
# T1a-Deep（時系列容量・受容野拡張版）3-seed 実行（lecun GPU 0/1 並列）。
#
# 既存 T1a base（num_stages=2 / num_layers=8 / num_f_maps=64, val phase acc +0.0497, hemostasis F1 +0.36〜+0.45）
# との **1 点 ablation**（時系列モデル容量のみ差し替え）:
#
#   T1a base : num_stages=2, num_layers=8,  num_f_maps=64
#              → receptive field dilation 2^(num_layers-1) = 2^7 = 128 frames（約 4.3 秒 @ 30fps）
#   T1a-Deep : num_stages=3, num_layers=10, num_f_maps=96
#              → receptive field 2^9 = 512 frames（約 17 秒、混同工程の境界を覆う）
#
# 入力・学習率・loss・eval recipe・分母（S4 base 0.8986±0.0034）はすべて T1a base と同一。
# 比較: Δ_phase(T1a-Deep) vs Δ_phase(T1a base) で paired-σ 判定。
#
# 軽量実験: 工程枝のみ・特徴キャッシュ利用・各 seed 50 epoch ≈ 30 分（lecun A6000）。
# GPU 並列: seed42(GPU0) + seed123(GPU1) → seed456(GPU0) 単独。
#
# 使い方:
#   bash scripts/run_t1a_deep_seeds.sh
# ============================================================================
set -euo pipefail

DESC="t1a_deep_3s10l96f"
EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }

# .env を source して NOTION_API_KEY/NOTION_DB_ID をロード（自動投稿のため・未設定でも no-op）
if [ -f "$ROOT/.env" ]; then
  set -a; source "$ROOT/.env"; set +a
fi

# 凍結検出器の region-token キャッシュ存在確認
[ -f "data/processed/t1a_regiontoken/relation_detr_seed42/train_regiontoken.npz" ] || \
  { echo "[ERR] T1a region-token キャッシュが無い"; exit 1; }

echo "================ T1a-Deep 3-seed（lecun・固定設定）================"
echo " DESC=$DESC epochs=$EPOCHS"
echo " 機構: num_stages=3 num_layers=10 num_f_maps=96 (T1a base 比 +1 stage / +2 layers / +32 maps)"
echo " 分母: S4 base 0.8986±0.0034 (T1a base mean 0.9483, Δ=+0.0497 既存)"
echo " 期待: T1a-Deep > T1a base なら時系列容量拡張で混同工程の境界 frame を更に救う"
echo "===================================================================="

run_one() {
  local seed="$1" gpu="$2" log="$3"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs "$EPOCHS" \
    --num-stages 3 --num-layers 10 --num-f-maps 96 \
    --description "$DESC" \
    > "$log" 2>&1
}

# wave 1: seed42(GPU0) + seed123(GPU1) 並列
echo "[wave 1] seed42(GPU0) + seed123(GPU1) 並列起動 ..."
run_one 42  0 "logs/t1a_deep_seed42.log"  &
pa=$!
run_one 123 1 "logs/t1a_deep_seed123.log" &
pb=$!
wait "$pa"; wait "$pb"
echo "[wave 1] 完了"

# wave 2: seed456(GPU0) 単独
echo "[wave 2] seed456(GPU0) 単独 ..."
run_one 456 0 "logs/t1a_deep_seed456.log"
echo "[wave 2] 完了"

echo "================ 完了・サマリ ================"
for S in "${SEEDS[@]}"; do
  echo "-- seed$S --"
  tail -3 "logs/t1a_deep_seed${S}.log"
done
echo "次: experiments/transfer/t1a_deep_3s10l96f_*/metrics.json を集計し、T1a base 3-seed と paired-σ で Δ 判定。"

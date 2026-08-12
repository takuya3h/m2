#!/usr/bin/env bash
# ============================================================================
# §18.4 L2-2 shuffle control（T1a の region-token を shuffle して Δ_phase 消失検証）
# 3-seed 実行（lecun GPU 0/1 並列）。
#
# 既存 T1a base との 1 点 ablation:
#   T1a base    : 真の region-token（frame 対応保持）→ phase acc +0.0497 / macroF1 +0.164
#   T1a-Shuffle : region-token の frame 対応を破壊 → Δ_phase が消えるはず（消えれば真の寄与の positive control 反証）
#
# 仮説:
#   - Δ_phase が消える（≈ S4 base 水準）→ T1a の改善は region-phase の真の相関に依存（強い反証）
#   - Δ_phase が残る → region の表現力（容量）だけで効いている疑い（弱い positive result）
#
# 軽量実験（特徴キャッシュ利用・50 epoch ≈ 30 分/seed）。
# ============================================================================
set -euo pipefail

DESC="t1a_shuffle"
EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

echo "================ §18.4 L2-2 T1a-Shuffle 3-seed ================"
echo " DESC=$DESC epochs=$EPOCHS region_shuffle=True"
echo " 比較: T1a base 3-seed (mean acc 0.9483) との 1 点 ablation"
echo " 分母: S4 base 0.8986±0.0034 (T1a base Δ=+0.0497 既存)"
echo "==============================================================="

run_one() {
  local seed="$1" gpu="$2" log="$3"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs "$EPOCHS" --region-shuffle \
    --description "$DESC" > "$log" 2>&1
}

echo "[wave 1] seed42(GPU0) + seed123(GPU1) 並列起動 ..."
run_one 42  0 "logs/t1a_shuffle_seed42.log"  &
pa=$!
run_one 123 1 "logs/t1a_shuffle_seed123.log" &
pb=$!
wait "$pa"; wait "$pb"
echo "[wave 1] 完了"

echo "[wave 2] seed456(GPU0) 単独 ..."
run_one 456 0 "logs/t1a_shuffle_seed456.log"
echo "[wave 2] 完了"

echo "================ 完了・サマリ ================"
for S in "${SEEDS[@]}"; do
  echo "-- seed$S --"
  tail -3 "logs/t1a_shuffle_seed${S}.log"
done
echo "次: T1a base 3-seed と paired-σ で Δ_acc/macroF1 の消失を判定。"

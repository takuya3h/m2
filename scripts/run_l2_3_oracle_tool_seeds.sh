#!/usr/bin/env bash
# ============================================================================
# §18.4 L2-3 oracle-tool-presence（B2a の上限を測定）
# B2a 入力の tool-presence を「凍結検出器の予測」→「GT bbox の one-hot」に置換し、
# 3-seed × 50 epoch で実行（軽量・特徴キャッシュ利用）。
#
# 比較: B2a base 3-seed (mean phase acc 0.9369, Δ +0.0383) との 1 点 ablation
#
# 仮説:
#   - oracle で大幅改善（例 +0.10）→ 検出器の精度がボトルネック（改善余地）
#   - oracle で微改善（例 +0.04 維持）→ B2a は既に info 上限近くで効いている
#   - oracle で悪化 → GT 分布のシフトが原因
# ============================================================================
set -euo pipefail

DESC="b2a_det2phase_oracletool"
EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

# oracle データ存在確認
for split in train val test; do
  f="data/processed/oracle_toolpresence/${split}_oracletool.npz"
  [ -f "$f" ] || { echo "[ERR] $f が無い。先に scripts/build_oracle_toolpresence.py を実行"; exit 1; }
done

echo "================ §18.4 L2-3 B2a-oracle-tool 3-seed ================"
echo " 比較: B2a base (mean phase acc 0.9369, Δ +0.0383) との 1 点 ablation"
echo " 差分: tool-presence ソース pred→oracle のみ。他は全て B2a base と同一"
echo "==================================================================="

run_one() {
  local seed="$1" gpu="$2" log="$3"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_b2a.py \
    --seed "$seed" --epochs "$EPOCHS" --tool-source oracle > "$log" 2>&1
}

# wave 1: seed42(GPU0) + seed123(GPU1) 並列
echo "[wave 1] seed42(GPU0) + seed123(GPU1) 並列起動 ..."
run_one 42  0 "logs/b2a_oracle_seed42.log"  &
pa=$!
run_one 123 1 "logs/b2a_oracle_seed123.log" &
pb=$!
wait "$pa"; wait "$pb"
echo "[wave 1] 完了"

echo "[wave 2] seed456(GPU0) 単独 ..."
run_one 456 0 "logs/b2a_oracle_seed456.log"
echo "[wave 2] 完了"

echo "================ 完了・サマリ ================"
for S in "${SEEDS[@]}"; do
  echo "-- seed$S --"
  tail -3 "logs/b2a_oracle_seed${S}.log"
done
echo "次: B2a base 3-seed と paired-σ で Δ_acc/macroF1 を比較。"

#!/usr/bin/env bash
# ============================================================================
# STEP D-aux 系統② 時間文脈 Problem B: 温度ヘッド比較（temporal-feature=none 固定）
# 入力側の時間特徴を off（none）に固定し、**温度カーネル（時間ヘッド）そのもの**だけを
# 変える 1 軸 ablation。素 GAP → 各カーネルで工程認識の Δ_phase を比較する。
#   --temporal-feature none 固定 × --temporal-kernel {tecno, mingru, mamba} 各 3-seed
# 呼ぶのは scripts/train_taux.py。特徴キャッシュ利用で軽量。
#
# 使い方:
#   bash scripts/run_taux_problemB.sh
# ============================================================================
set -euo pipefail

FEATURE=none
KERNELS=(tecno mingru mamba)
EPOCHS=50
SEEDS=(42 123 456)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
if [ -f "$ROOT/.env" ]; then set -a; source "$ROOT/.env"; set +a; fi

[ -f "$ROOT/scripts/train_taux.py" ] || \
  { echo "[ERR] scripts/train_taux.py が無い（系統② temporal トレーナ未実装）"; exit 1; }

GAP_DIR="data/processed/stage1_features/relation_detr_seed42"
for split in train val test; do
  [ -f "$GAP_DIR/${split}_gap.npz" ] || \
    { echo "[ERR] GAP キャッシュ不在: $GAP_DIR/${split}_gap.npz（先に stage1 特徴抽出を実行）"; exit 1; }
done

echo "================ 系統② Problem B: 温度カーネル比較（feature=$FEATURE 固定）================"
echo " 呼: scripts/train_taux.py --temporal-feature $FEATURE --temporal-kernel {${KERNELS[*]}} epochs=$EPOCHS"
echo " 分母: S4 base phase acc 0.8986±0.0028 / macro-F1 0.709（tecno は素 TeCNO = 実質 base 再現）"
echo " seeds=${SEEDS[*]}"
echo "======================================================================================"

run_taux() {
  local seed="$1" gpu="$2" log="$3"; shift 3
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_taux.py \
    --seed "$seed" --epochs "$EPOCHS" "$@" > "$log" 2>&1
}

run_3seed() {
  local tag="$1"; shift
  echo "[$tag] wave 1: seed42(GPU0) + seed123(GPU1) 並列起動 ..."
  run_taux 42  0 "logs/taux_${tag}_seed42.log"  "$@" &
  local pa=$!
  run_taux 123 1 "logs/taux_${tag}_seed123.log" "$@" &
  local pb=$!
  wait "$pa"; wait "$pb"
  echo "[$tag] wave 2: seed456(GPU0) 単独 ..."
  run_taux 456 0 "logs/taux_${tag}_seed456.log" "$@"
  echo "[$tag] 完了"
}

# mamba/mingru カーネルは順次（tecno→mingru→mamba）に回す。mamba-ssm は導入済（JIT ビルド不要）。
for k in "${KERNELS[@]}"; do
  echo ""
  echo "==== temporal-kernel=$k (feature=$FEATURE) ===="
  run_3seed "feat${FEATURE}_kernel${k}" --temporal-feature "$FEATURE" --temporal-kernel "$k"
done

echo ""
echo "================ 完了・サマリ ================"
for k in "${KERNELS[@]}"; do
  for S in "${SEEDS[@]}"; do
    log="logs/taux_feat${FEATURE}_kernel${k}_seed${S}.log"
    [ -f "$log" ] && echo "-- feat=$FEATURE kernel=$k seed$S --" && tail -3 "$log"
  done
done
echo ""
echo "次: experiments/transfer/ から各 kernel を 3-seed 集計し、S4 base 0.8986±0.0028 と"
echo "    §10.1 paired-σ 判定（per-seed Δ → mean, pstdev, |mean|/pstdev, 全seed同符号 → |mean|>pstdev かつ同符号で ✓）。"

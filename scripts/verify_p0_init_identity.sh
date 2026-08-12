#!/usr/bin/env bash
# ============================================================================
# verify_p0_init_identity.sh — p0 判定量(4) の証拠生成（フル学習なし・read-only 評価のみ）
#
# 目的: zero-init 恒等ガード「inj==ctrl@init」を seed 42/123/456 すべてで実測する。
#   注入層は zero-init（残差 0）なので init 時点で inj（通常 ctx）と ctrl（--zero-ctx）は
#   完全に同一予測を出すはず。これが破れると Δ を注入効果と解釈できない（§4.6 比較前提）。
#
# 既存の run_t1b_clsbias_3seed_efros.sh の preflight+identity 部だけを抽出したもの。
# 各 seed で train_t1b.py を --epochs 0（init 評価のみ・学習ループに入らない）で
# inj / ctrl の 2 本走らせ、init 予測を保存 → run_artifacts.py --verify-init-identity で
# bit-exact 一致（SHA-256）を判定。学習・loss・optimizer・eval recipe には一切触れない。
#
# 使い方:  bash scripts/verify_p0_init_identity.sh
# 出力:    experiments/transfer/_p0_identity_{inj,ctrl}_seed{S}/  （init 予測・result）
#          logs/p0_init_identity_seed{S}.json                    （一致判定）
#          logs/p0_measure_{inj,ctrl}_seed{S}.log                （実行ログ）
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

INJECT="clsbias"      # zero-ctx 対照を持つ注入機構（smoke で seed42 一致を実測済）
TRAINABLE="film"
SEEDS=(42 123 456)
GPU="${P0_GPU:-0}"

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い"; exit 1; }

for S in "${SEEDS[@]}"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done

echo "[warmup] MSDeformAttn CUDA 拡張を事前ビルド ..."
CUDA_VISIBLE_DEVICES="$GPU" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] ready')"

run_one() {  # $1=seed $2=workdir $3=log  $4..=extra
  local seed="$1" work="$2" log="$3"; shift 3
  CUDA_VISIBLE_DEVICES="$GPU" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$seed" --inject "$INJECT" --trainable "$TRAINABLE" \
      --epochs 0 "$@" > "$log" 2>&1
}

overall=0
for S in "${SEEDS[@]}"; do
  echo "############### seed$S (init-only) ###############"
  INJ="$ROOT/experiments/transfer/_p0_identity_inj_seed${S}"
  CTRL="$ROOT/experiments/transfer/_p0_identity_ctrl_seed${S}"
  run_one "$S" "$INJ"  "logs/p0_measure_inj_seed${S}.log"
  run_one "$S" "$CTRL" "logs/p0_measure_ctrl_seed${S}.log" --zero-ctx
  if "$VENV" scripts/run_artifacts.py --verify-init-identity "$INJ" "$CTRL" \
        > "logs/p0_init_identity_seed${S}.json"; then
    echo "[seed$S] init identity ✓ (inj==ctrl@init)"
  else
    echo "[seed$S] init identity ✗ 不一致（恒等性の破れ）"; overall=1
  fi
done

echo "======== p0 init-identity 判定: $([ $overall -eq 0 ] && echo 'ALL PASS ✓' || echo 'FAIL ✗') ========"
exit "$overall"

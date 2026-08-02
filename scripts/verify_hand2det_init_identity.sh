#!/usr/bin/env bash
# ============================================================================
# verify_hand2det_init_identity.sh — zero-init 恒等ガードの証拠生成（学習なし・init 評価のみ）
#
# 目的: Hand-mask→Det 注入の zero-init 恒等「inj==ctrl@init」を seed 42/123/456 で実測する。
#   注入層(hand_prior)は bias 無し zero-init 1x1 conv なので、init 時点で残差=0。よって
#   inj（合成手 mask 注入）と ctrl（--zero-ctx=注入テンソル0）は完全に同一予測を出すはず。
#   これが破れると「Δ を注入効果と解釈する」前提が崩れる。
#
#   各 seed で train_hand2det.py を --epochs 0（init 評価のみ）で inj / ctrl の 2 本走らせ、
#   init 予測を保存 → run_artifacts.py --verify-init-identity で bit-exact 一致(SHA-256)を判定。
#   学習・loss・optimizer・eval recipe には一切触れない。
#
# 使い方:  bash scripts/verify_hand2det_init_identity.sh          # 既定 4ch(L2)
#          HAND2DET_CH=5 bash scripts/verify_hand2det_init_identity.sh  # 5ch(L1a)
# 出力:    experiments/hand2det_dev/_identity_{inj,ctrl}_{CH}ch_seed{S}/  （init 予測・result）
#          logs/hand2det_identity_{CH}ch_seed{S}.json                    （一致判定）
#          logs/hand2det_measure_{inj,ctrl}_{CH}ch_seed{S}.log           （実行ログ）
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CH="${HAND2DET_CH:-4}"           # 4=L2 / 5=L1a
SRC="${HAND2DET_SOURCE:-synth}"  # synth=合成 / real=raw02 手 bbox（L2 実データ配線検証）
TRAINABLE="film"
SEEDS=(42 123 456)
GPU="${HAND2DET_GPU:-0}"

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い"; exit 1; }

for S in "${SEEDS[@]}"; do
  CK="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${S}/best_ap.pth"
  [ -f "$CK" ] || { echo "[ERR] warm-start ckpt が無い: $CK"; exit 1; }
done
mkdir -p "$ROOT/logs"

echo "[warmup] MSDeformAttn CUDA 拡張を事前ビルド ..."
CUDA_VISIBLE_DEVICES="$GPU" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] ready')"

run_one() {  # $1=seed $2=workdir $3=log  $4..=extra
  local seed="$1" work="$2" log="$3"; shift 3
  CUDA_VISIBLE_DEVICES="$GPU" HAND2DET_WORK_DIR="$work" \
    "$VENV" scripts/train_hand2det.py \
      --seed "$seed" --hand-channels "$CH" --trainable "$TRAINABLE" \
      --hand-source "$SRC" --epochs 0 "$@" > "$log" 2>&1
}

overall=0
for S in "${SEEDS[@]}"; do
  echo "############### ${CH}ch/${SRC} seed$S (init-only) ###############"
  INJ="$ROOT/experiments/hand2det_dev/_identity_inj_${CH}ch_${SRC}_seed${S}"
  CTRL="$ROOT/experiments/hand2det_dev/_identity_ctrl_${CH}ch_${SRC}_seed${S}"
  run_one "$S" "$INJ"  "logs/hand2det_measure_inj_${CH}ch_${SRC}_seed${S}.log"
  run_one "$S" "$CTRL" "logs/hand2det_measure_ctrl_${CH}ch_${SRC}_seed${S}.log" --zero-ctx
  if "$VENV" scripts/run_artifacts.py --verify-init-identity "$INJ" "$CTRL" \
        > "logs/hand2det_identity_${CH}ch_${SRC}_seed${S}.json"; then
    echo "[${CH}ch/${SRC} seed$S] init identity OK (inj==ctrl@init)"
  else
    echo "[${CH}ch/${SRC} seed$S] init identity FAIL 不一致（恒等性の破れ）"; overall=1
  fi
done

echo "======== hand2det init-identity 判定(${CH}ch): $([ $overall -eq 0 ] && echo 'ALL PASS' || echo 'FAIL') ========"
exit "$overall"

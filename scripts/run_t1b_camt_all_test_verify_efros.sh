#!/usr/bin/env bash
# ============================================================================
# ① camt-all の **test 追認**（checkpoint 消失 → 再学習して保全 → test 評価）
#   1. run_t1b_camt_all_3seed_efros.sh を TAG=camt_all_reverify で再走
#      （INJECT=camt/TRAINABLE=all/EPOCHS=6 は元と完全一致・seed 固定＝val 再現。
#        別 TAG なので committed evidence transfer/t1b_camt_all_* は上書きしない）。
#   2. best_t1b.pth（inj+ctrl×3seed）を artifacts/ にも複製（現在は experiments/transfer/
#      <run>/checkpoints/ が正本。学習出力自体が永続化されたので本 step は二重化のみ）。
#   3. eval_t1b_test.py --inject camt で整合ゲート(reload→val 再現)→test 評価。
# 出力: experiments/analysis/t1b_camt_all_test/test_eval.json
# 所要: trainable=all で ~50min/ep × 6ep × 3seed ≈ 15h（overnight, background 運用）。
# ============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"; mkdir -p logs
VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV 無い"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
command -v ninja >/dev/null || { echo "[ERR] ninja が PATH に無い"; exit 1; }

RTAG="camt_all_reverify"
CKROOT="$ROOT/artifacts/t1b_camt_all_ckpt"; mkdir -p "$CKROOT"
SEEDS=(42 123 456)

echo "================ ① camt-all test 追認 orchestrator ================"
echo " step1: 再学習 (TAG=$RTAG, inject=camt trainable=all epochs=6)"
echo "================================================================="

# --- step1: 再学習（val 再現・committed evidence 非上書き）---
TAG="$RTAG" bash scripts/run_t1b_camt_all_3seed_efros.sh

# --- step2: checkpoint 保全（best + 存在すれば final）---
echo "[step2] checkpoint を $CKROOT へ保全"
for S in "${SEEDS[@]}"; do
  for sub in "_seed${S}" "_zeroctx_seed${S}"; do
    src="$ROOT/experiments/transfer/t1b_${RTAG}${sub}/checkpoints/best_t1b.pth"
    if [ -f "$src" ]; then
      cp -f "$src" "$CKROOT/t1b_${RTAG}${sub}_best.pth"
      echo "  保全: $src -> $CKROOT/t1b_${RTAG}${sub}_best.pth"
    else
      echo "  [WARN] best_t1b.pth 欠損: $src"
    fi
  done
done

# --- step3: test 追認 eval（整合ゲート→test）---
echo "[step3] test 追認 eval（--inject camt --tag $RTAG）"
CUDA_VISIBLE_DEVICES="${GPU_EVAL:-0}" PYTHONPATH=src \
  "$VENV" scripts/eval_t1b_test.py \
    --inject camt --tag "$RTAG" --ckpt-root "$ROOT/experiments/transfer" --ckpt-name best_t1b.pth \
    --seeds "$(IFS=,; echo "${SEEDS[*]}")" \
    --out experiments/analysis/t1b_camt_all_test/test_eval.json

echo "[ALLDONE] ① camt-all test 追認 完了（再学習→保全→test 評価）"

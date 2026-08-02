#!/usr/bin/env bash
# ============================================================================
# T1b-CA（cross-attention phase→det / §4.6 primary）を任意 seed で実行する。
# run_t1b_ca_seed42_bengio.sh の **引数化版**（seed42/123/456 対応）。
#
# 【設定ドリフト根絶】inject=ca / trainable=film / epochs=6 は固定。seed と、それに
#   対応する preflight init mAP（= 各 seed の S0-frozen 水準）だけを per-seed 表から
#   自動選択する。bengio で打つのは seed のみ。assert 値は表からの自動引き＝取り違え防止。
#
# phase_context は **検出器 seed 非依存**（凍結 S4 の per-frame 事後を frame_id で突合・
#   train_t1b.py:48）。ゆえ relation_detr_seed42 キャッシュを全 seed 共有する。seed 汚染
#   ではない（S4 は単一モデル / 検出器 seed と無関係）。
#
# 使い方（bengio・tmux/screen 推奨）:
#   bash scripts/run_t1b_ca_bengio.sh 123            # 単一 seed（注入+対照を並列）
#   GPU_INJ=0 GPU_CTRL=1 bash scripts/run_t1b_ca_bengio.sh 456
#   SEQUENTIAL=1 GPU_INJ=0 bash scripts/run_t1b_ca_bengio.sh 123   # 単一GPUで逐次
# ============================================================================
set -euo pipefail

SEED="${1:-${SEED:-}}"
[ -n "$SEED" ] || { echo "[ERR] seed を引数で指定せよ（例: bash $0 123）"; exit 1; }

# --- per-seed S0-frozen init mAP（preflight・取り違え/捏造防止のハードコード表）---
#   warm-start+zero-init 恒等なので init mAP は各 seed の S0-frozen と一致するはず。
#   出典: docs/experiment_log.md（seed42 0.7303 / seed123 0.7292 / seed456 0.7217）。
case "$SEED" in
  42)  ASSERT_INIT_MAP=0.7303 ;;
  123) ASSERT_INIT_MAP=0.7292 ;;
  456) ASSERT_INIT_MAP=0.7217 ;;
  *) echo "[ERR] 未知の seed=$SEED（42/123/456 のみ assert 値を持つ。追加時は表を更新）"; exit 1 ;;
esac

# --- 固定設定（変更不可・ドリフト防止の核）---
INJECT=ca
TRAINABLE=film
EPOCHS=6
ASSERT_INIT_TOL=0.02

GPU_INJ="${GPU_INJ:-0}"
GPU_CTRL="${GPU_CTRL:-1}"
SEQUENTIAL="${SEQUENTIAL:-0}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

VENV="$ROOT/.venv-relation-detr/bin/python"
[ -x "$VENV" ] || { echo "[ERR] $VENV が無い。先に scripts/setup_env.sh で .venv-relation-detr を構築せよ"; exit 1; }
export CUDA_HOME="${CUDA_HOME:-/usr/local/cuda-11.8}"

CKPT="$ROOT/third_party/Relation-DETR/checkpoints/incoming/seed${SEED}/best_ap.pth"
[ -f "$CKPT" ] || { echo "[ERR] warm-start ckpt が無い: $CKPT（transfer_to_bengio.sh で受領せよ）"; exit 1; }

echo "================ T1b-CA seed${SEED}（引数化版・固定設定）================"
echo " inject=$INJECT trainable=$TRAINABLE epochs=$EPOCHS seed=$SEED"
echo " preflight: init mAP == $ASSERT_INIT_MAP ± $ASSERT_INIT_TOL（外れたら中断）"
echo " GPU_INJ=$GPU_INJ GPU_CTRL=$GPU_CTRL SEQUENTIAL=$SEQUENTIAL"
echo "======================================================================="

run() {  # $1=gpu $2=workdir $3=logfile $4(optional)=--zero-ctx
  local gpu="$1" work="$2" log="$3" extra="${4:-}"
  CUDA_VISIBLE_DEVICES="$gpu" T1B_WORK_DIR="$work" \
    "$VENV" scripts/train_t1b.py \
      --seed "$SEED" --inject "$INJECT" --trainable "$TRAINABLE" --epochs "$EPOCHS" \
      --assert-init-map "$ASSERT_INIT_MAP" --assert-init-tol "$ASSERT_INIT_TOL" $extra \
      > "$log" 2>&1
}

INJ_WORK=/tmp/t1b_ca_seed${SEED}
CTRL_WORK=/tmp/t1b_ca_zeroctx_seed${SEED}
INJ_LOG="logs/t1b_ca_seed${SEED}.log"
CTRL_LOG="logs/t1b_ca_zeroctx_seed${SEED}.log"

# MSDeformAttn CUDA 拡張を単一プロセスで事前 JIT ビルド（並列起動時のビルド競合 crash を防ぐ）。
echo "[warmup] MultiScaleDeformableAttention CUDA 拡張を事前ビルド中 ..."
CUDA_VISIBLE_DEVICES="$GPU_INJ" "$VENV" -c \
  "import sys, os; sys.path.insert(0, 'third_party/Relation-DETR'); os.chdir('third_party/Relation-DETR'); import models.bricks.relation_transformer; print('[warmup] MSDeformAttn ext ready')" \
  || { echo '[ERR] MSDeformAttn 拡張の事前ビルドに失敗。ログを確認せよ'; exit 1; }

if [ "$SEQUENTIAL" = "1" ]; then
  echo "[run] 逐次: 注入 → 対照（同一GPU $GPU_INJ）"
  run "$GPU_INJ" "$INJ_WORK"  "$INJ_LOG"
  run "$GPU_INJ" "$CTRL_WORK" "$CTRL_LOG" --zero-ctx
else
  echo "[run] 並列: 注入(GPU $GPU_INJ) + 対照(GPU $GPU_CTRL)"
  run "$GPU_INJ"  "$INJ_WORK"  "$INJ_LOG" &
  pid_inj=$!
  run "$GPU_CTRL" "$CTRL_WORK" "$CTRL_LOG" --zero-ctx &
  pid_ctrl=$!
  wait "$pid_inj"; wait "$pid_ctrl"
fi

echo "================ seed${SEED} 完了・回収用サマリ ================"
for tag in "$INJ_WORK" "$CTRL_WORK"; do
  if [ -f "$tag/t1b_result.json" ]; then
    echo "-- $tag/t1b_result.json --"; cat "$tag/t1b_result.json"
  else
    echo "[WARN] $tag/t1b_result.json が無い（preflight 中断 or 失敗。ログ確認: logs/）"
  fi
done
echo "次: この2 work dir（logs/t1b_ca_*seed${SEED}.log + *_result.json）を lecun へ回収せよ。"

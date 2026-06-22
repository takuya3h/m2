#!/usr/bin/env bash
# ============================================================================
# T1b-CA（cross-attention phase→det / §4.6 primary）seed42 を bengio で実行する。
#
# 【設定ドリフト根絶】このスクリプトは全フラグをハードコードする。bengio では引数を打たない。
#   - inject=ca / trainable=film / epochs=6 / seed=42 を固定（前回 seed42 が all 化した事故の再発防止）。
#   - --assert-init-map 0.7303 で warm-start+zero-init 恒等を preflight 検査し、外れたら即中断
#     （warm-start ckpt 取り違え・恒等破れ・捏造を物理的に弾く）。
#   - result.json に inject/trainable/epochs を必ず記録（事後検証可能）。
#
# 前提（bengio）: git pull 済み + lecun から transfer_to_bengio.sh で資産受領済み +
#   .venv-relation-detr を lock から再構築済み（scripts/setup_env.sh）。
#
# 使い方（bengio・tmux/screen 推奨。SSH 切断で死なないよう）:
#   bash scripts/run_t1b_ca_seed42_bengio.sh
#   # GPU を変える場合のみ:  GPU_INJ=0 GPU_CTRL=1 bash scripts/run_t1b_ca_seed42_bengio.sh
#   # 単一GPUで逐次実行:     SEQUENTIAL=1 GPU_INJ=0 bash scripts/run_t1b_ca_seed42_bengio.sh
# ============================================================================
set -euo pipefail

# --- 固定設定（変更不可・これがドリフト防止の核） ---
SEED=42
INJECT=ca
TRAINABLE=film
EPOCHS=6
ASSERT_INIT_MAP=0.7303          # seed42 の S0-frozen 水準（= warm-start+zero-init 恒等の期待値）
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

echo "================ T1b-CA seed${SEED}（固定設定）================"
echo " inject=$INJECT trainable=$TRAINABLE epochs=$EPOCHS seed=$SEED"
echo " preflight: init mAP == $ASSERT_INIT_MAP ± $ASSERT_INIT_TOL（外れたら中断）"
echo " GPU_INJ=$GPU_INJ GPU_CTRL=$GPU_CTRL SEQUENTIAL=$SEQUENTIAL"
echo "=============================================================="

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

echo "================ 完了・回収用サマリ ================"
for tag in "$INJ_WORK" "$CTRL_WORK"; do
  if [ -f "$tag/t1b_result.json" ]; then
    echo "-- $tag/t1b_result.json --"; cat "$tag/t1b_result.json"
  else
    echo "[WARN] $tag/t1b_result.json が無い（preflight 中断 or 失敗。ログ確認: logs/）"
  fi
done
echo "次: この2 work dir（または logs/t1b_ca_*seed${SEED}.log + *_result.json）を lecun へ回収せよ。"

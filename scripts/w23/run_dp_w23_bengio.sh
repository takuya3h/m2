#!/usr/bin/env bash
# DP（検出から工程）と案 A（把持から工程）の W2・W3 の腕をまとめて回す（非公式 T-2026-11-01-stage2-w23-bengio、SPEC §3.1・§4・Task D）。
#
#   scripts/w23/run_dp_w23_bengio.sh <型:腕:W> [<型:腕:W> ...]
#     型: D1-L1 D1-L2 D2 D3-L1 D3-L2 LC TH TH-NG GA、腕: empty pred_noCF gt pred_CF gtpred_CF shuffle、W: W2 W3
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。既に在る run（同じ型・腕・W）は飛ばす。
#
# 設定は W1 の台本（scripts/stage2pilot/run_dp_fix.sh・run_dp_four.sh、案 A は二本目）と同じ（4 epoch を止めずに学んで
# 4 epoch 目の状態を結果にする、学習率一定 5e-4、重み減衰 0.01、平滑化 0.3、1 歩 = train の動画 1 本、seed 42、
# D3 は --inst-variant uq）。変えるのは学習範囲だけ（dp_train.py --scope W2・W3）。
# 案 A の信号は andrew から本契約の置き場へ写したもの（audit.md の Task B-1。要約値は記録と一致）。
# run は experiments/phase1/w23b_dp_<W>_*、界面と受け取り手の重みは stage2pilot_store/<本契約>/dp_ckpt。
set -uo pipefail
CODE=/home/ubuntu/slocal2/m2
TASK=T-2026-11-01-stage2-w23-bengio
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
LOGS=$S/queues
SEED=42
mkdir -p "$LOGS"
cd "$CODE"
# shellcheck disable=SC1091
source .venv/bin/activate
# W&B は手元だけに記録する（契約 §7.10 は外部への送信を task-report に限る。利用者の決定 2026-11-02、三本目と同じ形）。
# 資格情報は読み込まない。WANDB_API_KEY は tracking の有効化の判定だけに使う仮の値（offline では送らない）
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
mkdir -p "$WANDB_DIR"
export PYTHONPATH=src:scripts PYTHONUTF8=1
for spec in "$@"; do
  IFS=: read -r TYPE ARM W <<< "$spec"
  case "$W" in W2|W3) ;; *) echo "[dp_w23] W が不明: $spec" >&2; continue ;; esac
  if grep -l '"phase_jaccard"' experiments/phase1/w23b_dp_"${W}"_*_"${TYPE}_${ARM}_ep4_seed${SEED}"/metrics.json > /dev/null 2>&1; then
    echo "[dp_w23] 済み $TYPE $ARM $W"; continue
  fi
  EXTRA=()
  case "$TYPE" in D3-*) EXTRA=(--inst-variant uq) ;; esac
  [ "$TYPE" = GA ] && EXTRA=(--grasp-signal-dir "$S/copied/grasp-pilot-probe/signals" --grasp-pred-dir "$S/copied/grasp-pilot-g/signals/A")
  LOG="$LOGS/dp_${TYPE}_${ARM}_${W}_${SEED}.log"
  python scripts/stage2pilot/dp_train.py train --type "$TYPE" --arm "$ARM" --seed "$SEED" "${EXTRA[@]}" \
    --fixed-epochs 4 --scope "$W" --task-id "$TASK" --exp-prefix "w23b_dp_${W}" > "$LOG" 2>&1
  RC=$?
  DIR=$(grep -o 'DP_RUN_COMPLETE [^ ]*' "$LOG" | tail -1 | cut -d' ' -f2)
  if [ "$RC" = 0 ] && [ -n "$DIR" ]; then
    sha256sum scripts/w23/run_dp_w23_bengio.sh scripts/stage2pilot/dp_train.py scripts/stage2pilot/dp_model.py \
      scripts/stage2pilot/common.py > "$DIR/code_sha256.txt"
  fi
  echo "[dp_w23] $TYPE $ARM $W rc=$RC $(grep -E 'DP_RUN_COMPLETE|Error' "$LOG" | tail -1)"
done

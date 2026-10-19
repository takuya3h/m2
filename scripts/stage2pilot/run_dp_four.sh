#!/usr/bin/env bash
# DP（検出から工程）の新しい型の固定の長さの腕をまとめて回す（非公式 T-2026-10-19-stage2-pilot-four-new-types、SPEC §4 Task E）。
#
#   scripts/stage2pilot/run_dp_four.sh <型:腕> [<型:腕> ...]          型: LC TH TH-NG、腕: empty pred_noCF gt pred_CF gtpred_CF shuffle
#   scripts/stage2pilot/run_dp_four.sh smoke <型> [<型> ...]          1 epoch の試走（腕ではない。名前に _ep1_smoke、腕は pred_noCF）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。既に在る run（同じ型・腕、試走でない）は飛ばす。
#
# 設定は直しの契約の run_dp_fix.sh と同じ（受け取り手、学習率一定 5e-4、重み減衰 0.01、平滑化 0.3、1 歩 = train の動画 1 本、
# 4 epoch を止めずに学んで 4 epoch 目の状態を結果にする、seed 42）。変えるのは界面の型と x(t)（32 次元）だけ。
# 台本・run の置き場は S2FOUR_CODE（既定はこの台本の repo）。直しの run_dp_fix.sh は main の作業場所に cd するので、worktree からはこちらを使う。
set -uo pipefail
CODE=${S2FOUR_CODE:-$(cd "$(dirname "$0")/../.." && pwd)}
VENV=${S2FOUR_VENV:-/home/ubuntu/slocal2/m2/.venv}
TASK=T-2026-10-19-stage2-pilot-four-new-types
LOGS=/home/ubuntu/slocal2/stage2pilot_store/$TASK/queues
SEED=42
mkdir -p "$LOGS"
cd "$CODE"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
# shellcheck disable=SC1091
source scripts/load_env.sh > /dev/null 2>&1
export PYTHONPATH=src:scripts PYTHONUTF8=1
EXTRA=(--fixed-epochs 4)
if [ "${1:-}" = smoke ]; then
  shift
  EXTRA=(--fixed-epochs 1 --smoke)
  set -- "${@/%/:pred_noCF}"
fi
for spec in "$@"; do
  TYPE=${spec%%:*}; ARM=${spec#*:}
  if [ "${EXTRA[*]}" = "--fixed-epochs 4" ] && \
     grep -l '"phase_jaccard"' experiments/phase1/stage2four_dp_*_"${TYPE}_${ARM}_ep4_seed${SEED}"/metrics.json > /dev/null 2>&1; then
    echo "[dp_four] 済み $TYPE $ARM"; continue
  fi
  LOG="$LOGS/dp_${TYPE}_${ARM}_${SEED}${EXTRA[2]:+_smoke}.log"
  python scripts/stage2pilot/dp_train.py train --type "$TYPE" --arm "$ARM" --seed "$SEED" \
    "${EXTRA[@]}" --task-id "$TASK" --exp-prefix stage2four_dp > "$LOG" 2>&1
  echo "[dp_four] $TYPE $ARM rc=$? $(grep -E 'DP_RUN_COMPLETE|Error' "$LOG" | tail -1)"
done

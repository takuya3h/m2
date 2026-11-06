#!/usr/bin/env bash
# 案 A の六腕（非公式 T-2026-11-06-grasp-pilot-arms、SPEC §3.1・§4・Task D）。二本目の run_caseA.sh と同じ処方
# （D1 concat の界面、W1、seed 42、4 epoch の固定の長さ、学習率一定 5e-4）に --grasp-no-flag（旗なし 28 次元）を足した。
# run は experiments/phase1/grasparms_dp_<番号>_GA-noflag_<腕>_ep4_seed42、界面の重みは stage2pilot_store/<本契約>/dp_ckpt
#   bash run_caseA.sh <GPU>
set -uo pipefail
GPU=${1:-0}
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-arms
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
R=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild
GT=$R/inputs/probe_signals
PRED=$R/signals/A
OUT=$M/experiments/analysis/grasp_pilot_arms/taskD/caseA
mkdir -p "$OUT"
cd "$M"
# shellcheck disable=SC1091
source .venv/bin/activate
# W&B は手元だけ（SPEC §7-10）。資格情報は読み込まない。WANDB_API_KEY は tracking の有効化の判定だけに使う仮の値
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
mkdir -p "$WANDB_DIR"
export PYTHONPATH=src:scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
for ARM in empty gt pred_noCF pred_CF gtpred_CF shuffle; do
  if grep -l '"phase_jaccard"' experiments/phase1/grasparms_dp_*_GA-noflag_"${ARM}"_ep4_seed42/metrics.json > /dev/null 2>&1; then
    echo "[caseA] 済み $ARM"; continue
  fi
  LOG=$OUT/train_$ARM.log
  python scripts/stage2pilot/dp_train.py train --type GA --arm "$ARM" --seed 42 --fixed-epochs 4 --grasp-no-flag \
    --grasp-signal-dir "$GT" --grasp-pred-dir "$PRED" --task-id "$TASK" --exp-prefix grasparms_dp > "$LOG" 2>&1
  RC=$?
  DIR=$(grep -o 'DP_RUN_COMPLETE [^ ]*' "$LOG" | tail -1 | cut -d' ' -f2)
  if [ "$RC" = 0 ] && [ -n "$DIR" ]; then
    sha256sum experiments/analysis/grasp_pilot_arms/taskD/run_caseA.sh scripts/stage2pilot/dp_train.py scripts/stage2pilot/dp_model.py \
      scripts/stage2pilot/common.py > "$DIR/code_sha256.txt"
    hostname > "$DIR/host.txt"
  fi
  echo "[caseA] $ARM rc=$RC $(grep -E 'DP_RUN_COMPLETE|Error' "$LOG" | tail -1)"
done

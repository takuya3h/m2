#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、Task C-2・C-3（DP と案 A）。型と W ごとに全腕で、学習前の出力が塔単独と一致するか、
# 界面の最後の層を N(0, 0.05²) にすると変わるか（dp_train.py identity --scope W --arms <W1 の腕>）。学ぶ集合も腕ごとに記録する。
#
#   bash run_dp_identity.sh <GPU>
set -uo pipefail
GPU=$1
CODE=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio
OUT=$CODE/experiments/analysis/stage2_w23_bengio/taskC/dp_identity
TASK=T-2026-11-01-stage2-w23-bengio
mkdir -p "$OUT"
cd "$CODE"
# shellcheck disable=SC1091
source .venv/bin/activate
export PYTHONPATH=src:scripts PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=$GPU
ALL6="empty pred_noCF gt pred_CF gtpred_CF shuffle"
NOGT="empty pred_noCF pred_CF shuffle"
for W in W2 W3; do
  for T in D1-L1 D1-L2 D2 D3-L1 D3-L2 LC TH TH-NG GA; do
    NAME=dp_${T}_${W}
    [ -f "$OUT/$NAME.json" ] && { echo "[dp_identity] 済み $NAME"; continue; }
    ARMS=$ALL6; EXTRA=()
    case $T in D1-L2|D3-L2) ARMS=$NOGT ;; esac
    case $T in D3-*) EXTRA=(--inst-variant uq) ;; esac
    [ "$T" = GA ] && EXTRA=(--grasp-signal-dir "$S/copied/grasp-pilot-probe/signals" --grasp-pred-dir "$S/copied/grasp-pilot-g/signals/A")
    # shellcheck disable=SC2086
    python scripts/stage2pilot/dp_train.py identity --type "$T" --scope "$W" --arms $ARMS "${EXTRA[@]}" \
      --task-id "$TASK" --out "$OUT/$NAME.json" > "$OUT/$NAME.log" 2>&1
    echo "[dp_identity] $NAME rc=$?"
  done
done

#!/usr/bin/env bash
# 案 A の恒等性（非公式 T-2026-11-06-grasp-pilot-arms、Task C-1・C-2）。旗なし 28 次元の 6 腕で、学習前（界面の重み 0）のロジットが
# 塔単独と一致するか、界面の重みを N(0, 0.05²) にすると出力が変わるか（dp_train.py identity、二本目の run_caseA.sh と同じ形に --grasp-no-flag）。
#   bash run_caseA_identity.sh <GPU>
set -uo pipefail
GPU=${1:-0}
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-arms
R=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild
GT=$R/inputs/probe_signals
PRED=$R/signals/A
OUT=$M/experiments/analysis/grasp_pilot_arms/taskC/caseA
mkdir -p "$OUT"
cd "$M"
export PYTHONPATH=src:scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
for ARM in empty gt pred_noCF pred_CF gtpred_CF shuffle; do
  .venv/bin/python scripts/stage2pilot/dp_train.py identity --type GA --arm "$ARM" --grasp-no-flag --task-id "$TASK" \
    --grasp-signal-dir "$GT" --grasp-pred-dir "$PRED" --out "$OUT/identity_$ARM.json" > "$OUT/identity_$ARM.log" 2>&1
  echo "[caseA identity] $ARM rc=$?"
done

#!/usr/bin/env bash
# 案 A の六腕（非公式 T-2026-11-01-grasp-pilot-g、SPEC §3.4・Task E）。恒等性（学習前の出力が塔単独と一致、重み N(0,0.05²) で変わる）の後に、
# 一本目と同じ処方（D1 concat 30 次元、W1、seed 42、4 epoch の固定の長さ）で 6 本を回す。界面の重みは stage2pilot_store/<本契約>/dp_ckpt
set -uo pipefail
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
GT=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/signals
PRED=$S/signals/A
R=$M/experiments/analysis/grasp_pilot_g/caseA
cd "$M"
source scripts/load_env.sh >/dev/null 2>&1 || true
export PYTHONPATH=src
for ARM in empty pred_noCF gt pred_CF gtpred_CF shuffle; do
  .venv/bin/python scripts/stage2pilot/dp_train.py identity --type GA --arm "$ARM" --task-id "$TASK" \
    --grasp-signal-dir "$GT" --grasp-pred-dir "$PRED" --out "$R/identity_$ARM.json" > "$R/identity_$ARM.log" 2>&1
  echo "identity $ARM rc=$?"
done
for ARM in empty pred_noCF gt pred_CF gtpred_CF shuffle; do
  .venv/bin/python scripts/stage2pilot/dp_train.py train --type GA --arm "$ARM" --seed 42 --fixed-epochs 4 --task-id "$TASK" \
    --exp-prefix grasppilot2_dp --grasp-signal-dir "$GT" --grasp-pred-dir "$PRED" > "$R/train_$ARM.log" 2>&1
  echo "train $ARM rc=$?"
done

#!/usr/bin/env bash
# Task C-5（DP）: 検出から工程の三つの型（LC、TH、TH-NG）の全 6 腕で、学習前の出力が塔単独と一致するか、
# 零から始めた部分（LC の W_out、TH の α、TH-NG の W_o）を零でない値にすると出力が変わるかを val で調べる
# （非公式 T-2026-10-19-stage2-pilot-four-new-types）。本体の .venv、GPU は CUDA_VISIBLE_DEVICES で渡す。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
OUT=$WT/experiments/analysis/stage2_pilot_four/identity
cd "$WT"
# shellcheck disable=SC1091
source /home/ubuntu/slocal2/m2/.venv/bin/activate
export PYTHONPATH=src:scripts PYTHONUTF8=1
for TYPE in LC TH TH-NG; do
  for ARM in empty pred_noCF gt pred_CF gtpred_CF shuffle; do
    python scripts/stage2pilot/dp_train.py identity --type "$TYPE" --arm "$ARM" \
      --task-id T-2026-10-19-stage2-pilot-four-new-types --out "$OUT/dp_${TYPE}_${ARM}.json" > "$OUT/dp_${TYPE}_${ARM}.log" 2>&1
    echo "[dp_identity] $TYPE $ARM rc=$?"
  done
done

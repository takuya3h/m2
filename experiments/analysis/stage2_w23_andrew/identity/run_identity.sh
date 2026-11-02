#!/usr/bin/env bash
# Task C-2〜C-4（非公式 T-2026-11-01-stage2-w23-andrew）: 型 × W × 腕ごとに、学ぶ集合と学習前の恒等性を
# scripts/w23/run_pd_w23_andrew.sh の identity・perturb・setcheck で調べる。陽性対照（perturb）は型 × W ごとに正解の腕。
# W1 は setcheck だけ（学ぶ集合が W1 の集合と一致するか。評価しない、CPU）。GPU は 2 枚、同時 6 本（1 枚 3 本）。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
cd "$M"
JOBS=$M/experiments/analysis/stage2_w23_andrew/identity/jobs.txt
: > "$JOBS"
i=0
for T in P1 DX B; do
  for W in W2 W3; do
    for A in empty pred_noCF gt pred_CF gtpred_CF shuffle; do echo "$T $W $A identity $((i % 2))" >> "$JOBS"; i=$((i+1)); done
    echo "$T $W gt perturb $((i % 2))" >> "$JOBS"; i=$((i+1))
  done
  for A in empty pred_noCF gt pred_CF gtpred_CF shuffle; do echo "$T W1 $A setcheck none" >> "$JOBS"; done
done
xargs -P 6 -L 1 bash -c 'if [ "$4" = none ]; then export CUDA_VISIBLE_DEVICES=""; else export CUDA_VISIBLE_DEVICES=$4; fi; bash scripts/w23/run_pd_w23_andrew.sh "$0" "$1" "$2" "$3"' < "$JOBS"

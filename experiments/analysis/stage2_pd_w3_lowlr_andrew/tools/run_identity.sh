#!/usr/bin/env bash
# Task B-4・B-5（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew）: 4 型 × 4 腕の学習前の恒等性と学ぶ集合、型ごとの陽性対照（正解の腕）。
# GPU ごとに 3 並列（xargs -P 3）。各件は run_w3lra.sh <型> <腕> identity|perturb。val だけ。
set -uo pipefail
T=$(cd "$(dirname "$0")" && pwd)
JOBS=()
for t in P1 P2L P3 DX; do for a in empty pred_noCF gt shuffle; do JOBS+=("$t $a identity"); done; JOBS+=("$t gt perturb"); done
: > "$T/../identity/jobs_gpu0.txt"; : > "$T/../identity/jobs_gpu1.txt"
for k in "${!JOBS[@]}"; do echo "${JOBS[$k]}" >> "$T/../identity/jobs_gpu$((k % 2)).txt"; done
for g in 0 1; do
  ( xargs -P 3 -L 1 sh -c 'CUDA_VISIBLE_DEVICES='"$g"' bash '"$T"'/run_w3lra.sh "$0" "$1" "$2"' < "$T/../identity/jobs_gpu$g.txt" ) &
done
wait

#!/usr/bin/env bash
# Task C-1（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew）: §4 の 16 本を GPU 2 枚・1 枚 3 本（xargs -P 3）で回す。
# 列は型 × 腕の 16 組を交互に GPU 0・1 へ割る（各 GPU に各型の 2 腕）。各本は run_w3lra.sh <型> <腕>（学習のモード）。
# 出力は queue/gpu<g>.out。1 枚に載せる本数（3）は前回の andrew の計測（W3 の記憶の山 12.6 GB、3 本で 48 GB に収まる）と B の試走で決めた。
set -uo pipefail
T=$(cd "$(dirname "$0")" && pwd)
Q=$T/../queue
mkdir -p "$Q"
: > "$Q/gpu0.txt"; : > "$Q/gpu1.txt"
k=0
for t in P1 P2L P3 DX; do for a in empty pred_noCF gt shuffle; do echo "$t $a" >> "$Q/gpu$((k % 2)).txt"; k=$((k + 1)); done; done
for g in 0 1; do
  ( xargs -P 3 -L 1 sh -c 'CUDA_VISIBLE_DEVICES='"$g"' bash '"$T"'/run_w3lra.sh "$0" "$1"' < "$Q/gpu$g.txt" > "$Q/gpu$g.out" 2>&1 ) &
done
wait

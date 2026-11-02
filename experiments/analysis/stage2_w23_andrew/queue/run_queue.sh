#!/usr/bin/env bash
# Task D（非公式 T-2026-11-01-stage2-w23-andrew）: SPEC §4 の 36 本を GPU 2 枚で回す待ち行列。
#   run_queue.sh <GPU> <同時本数> <列のファイル>
# 列のファイルは 1 行 1 本（"<型> <W> <腕>"）。GPU ごとに別の列を渡し、その GPU の中で <同時本数> 本ずつ並べる。
# 既に作業フォルダが在る run は台本が exit 4 で飛ばす（上書きしない）。各 run の終了コードは run の exit_code.txt と本ファイルの出力に残る。
set -uo pipefail
GPU=$1; K=$2; LIST=$3
M=/home/ubuntu/slocal2/m2
cd "$M"
export CUDA_VISIBLE_DEVICES=$GPU
xargs -P "$K" -L 1 bash -c 'echo "[queue] $(TZ=Asia/Tokyo date "+%m-%d %H:%M:%S") start $0 $1 $2 gpu=$CUDA_VISIBLE_DEVICES"; bash scripts/w23/run_pd_w23_andrew.sh "$0" "$1" "$2"; echo "[queue] $(TZ=Asia/Tokyo date "+%m-%d %H:%M:%S") end $0 $1 $2 rc=$?"' < "$LIST"

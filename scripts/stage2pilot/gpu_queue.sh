#!/usr/bin/env bash
# 一つの GPU でキューの命令を順に流す（非公式 T-2026-10-18-stage2-pilot-folda）。
#
#   scripts/stage2pilot/gpu_queue.sh <GPU 番号> <キューのファイル>
#
# キューは 1 行 1 命令（repo 直下で bash -c に渡す）。先頭の行を flock の下で取り出して実行する。
# キューが空なら 60 秒ごとに見直し、<キュー>.stop が在り空なら終わる。結果は <キュー>.done に 1 行ずつ足す。
set -uo pipefail
GPU="$1"; Q="$2"
BODY=/home/ubuntu/slocal2/m2
LOCK="$Q.lock"
touch "$Q" "$Q.done"
cd "$BODY"
while true; do
  CMD=$(flock "$LOCK" bash -c 'line=$(head -n 1 "$0"); [ -n "$line" ] && sed -i 1d "$0"; printf "%s" "$line"' "$Q")
  if [ -z "$CMD" ]; then
    [ -e "$Q.stop" ] && break
    sleep 60
    continue
  fi
  START=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
  CUDA_VISIBLE_DEVICES="$GPU" bash -c "$CMD"
  RC=$?
  echo "$START $(date -u '+%Y-%m-%dT%H:%M:%SZ') gpu=$GPU rc=$RC $CMD" >> "$Q.done"
done
echo "[gpu_queue] gpu=$GPU 終了"

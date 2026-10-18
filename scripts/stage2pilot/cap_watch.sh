#!/usr/bin/env bash
# PD の上限を 4 epoch にした後（spec の amendments の 4 件目）、上限 8 で起動済みの run を 5 epoch 目の始まりで止め、
# cap_finalize.py で結果を書く（非公式 T-2026-10-18-stage2-pilot-folda）。
#
#   scripts/stage2pilot/cap_watch.sh <run 名>
#
# 止めるのは、その run 名を命令行に持つ train_t1b.py の親プロセスだけ（命令行を確かめてから kill）。
# run が 4 epoch 目までに止め方の規則で自分で終われば、何もしない。
set -uo pipefail
RUN="$1"
BODY=/home/ubuntu/slocal2/m2
W=$BODY/experiments/phase1/$RUN
while :; do
  if [ -f "$W/exit_code.txt" ]; then
    echo "[cap_watch] $RUN は自分で終わった rc=$(cat "$W/exit_code.txt")"; exit 0
  fi
  grep -q '\[t1b\]\[ep4 0/' "$W/train.log" && break
  sleep 20
done
PID=$(pgrep -o -f -- "--run-name $RUN --det-ckpt")
if [ -z "$PID" ] || ! tr '\0' ' ' < "/proc/$PID/cmdline" | grep -q "train_t1b.py .*--run-name $RUN "; then
  echo "[cap_watch] $RUN の train_t1b.py が見つからない" >&2; exit 2
fi
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$W/cap_stop.txt"
echo "pid=$PID 5 epoch 目の始まりで止めた（上限 4 epoch。spec の amendments の 4 件目）" >> "$W/cap_stop.txt"
kill -TERM "$PID"
until [ -f "$W/exit_code.txt" ]; do sleep 5; done
cd "$BODY" && PYTHONPATH=src:scripts .venv/bin/python scripts/stage2pilot/cap_finalize.py "$W"
echo "[cap_watch] $RUN 止めた rc=$(cat "$W/exit_code.txt")"

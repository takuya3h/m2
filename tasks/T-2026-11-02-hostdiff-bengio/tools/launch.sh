#!/usr/bin/env bash
# 本契約の run を順に起こす（T-2026-11-02-hostdiff-bengio）。手本と同じく load_env を読んでから起こす。
set -uo pipefail
cd /home/ubuntu/slocal2/m2
source scripts/load_env.sh > /dev/null 2>&1
LOG=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/launch.log
mkdir -p "$(dirname "$LOG")"
for run in "$@"; do
  echo "$(date -Is) START $run" >> "$LOG"
  .venv/bin/python -B tasks/T-2026-11-02-hostdiff-bengio/tools/run_hostdiff.py "$run" >> "$LOG" 2>&1
  rc=$?
  echo "$(date -Is) END $run rc=$rc" >> "$LOG"
  [ $rc -ne 0 ] && exit $rc
done
echo "$(date -Is) ALL_DONE $*" >> "$LOG"

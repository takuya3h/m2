#!/usr/bin/env bash
# 案 B の 4 腕と術具だけの 2 腕（非公式 T-2026-11-06-grasp-pilot-arms、SPEC §4・Task D）。GPU 2 枚に 3 本ずつ並行で起こす
# （1 本 約 <試走で測った値> GiB。記憶の確保は audit.md の Task D に記録）。各 run は scripts/grasppilot/run_pd_grasparms.sh。
# 外の使用の見張り: 60 秒ごとに nvidia-smi の全体の使用量と compute の一覧を $S/logs/gpu_watch.csv へ（差は一覧の外の使用）
#   bash run_caseB.sh
set -uo pipefail
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-arms
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
L=$S/logs
mkdir -p "$L"
cd "$M"
( while true; do
    T=$(date -u '+%F %T')
    nvidia-smi --query-gpu=index,memory.used,utilization.gpu,power.draw --format=csv,noheader | sed "s/^/$T,gpu,/"
    nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | sed "s/^/$T,app,/"
    sleep 60
  done ) >> "$L/gpu_watch.csv" 2>&1 &
WATCH=$!
lane() { GPU=$1; ARM=$2
  echo "[caseB] start $ARM GPU $GPU $(date -u '+%F %T UTC')"
  CUDA_VISIBLE_DEVICES=$GPU bash scripts/grasppilot/run_pd_grasparms.sh "$ARM" > "$L/d_B_$ARM.log" 2>&1
  echo "[caseB] end $ARM GPU $GPU rc=$? $(date -u '+%F %T UTC')"; }
lane 0 pred_noCF & sleep 30
lane 0 pred_CF & sleep 30
lane 0 gtpred_CF & sleep 30
lane 1 shuffle & sleep 30
lane 1 toolonly_pred_noCF & sleep 30
lane 1 toolonly_shuffle &
wait $(jobs -p | grep -v "^$WATCH$")
kill "$WATCH"
echo "[caseB] all done $(date -u '+%F %T UTC')"

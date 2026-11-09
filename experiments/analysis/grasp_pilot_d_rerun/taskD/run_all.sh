#!/usr/bin/env bash
# 非公式 T-2026-11-06-grasp-pilot-d-rerun、Task D。4 本（案 D の G を教師・入れ替えた教師、案 B の空・正解）を起こす。
#   bash run_all.sh <D gteach の GPU> <D shuf の GPU> <B empty の GPU> <B gt の GPU>
# 載せ方は Task C の記憶の実測で決めて、引数で渡す（audit に理由を書く）。起動は 30 秒ずつずらす。
# 各 run は setsid nohup で切り離す。終了コードは各 run の exit_code.txt に残る。
set -uo pipefail
GD=${1:?GPU for D gteach}; SD=${2:?GPU for D shuf}; BE=${3:?GPU for B empty}; BG=${4:?GPU for B gt}
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-d-rerun
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
mkdir -p "$S/logs"
cd "$M"
export PYTHONDONTWRITEBYTECODE=1
{ date '+%F %T %Z'; TZ=Asia/Tokyo date '+%F %T JST'; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | wc -l; } > "$S/logs/d_start_gpu.txt" 2>&1
CUDA_VISIBLE_DEVICES=$GD setsid nohup bash scripts/grasppilot/run_d_arm_rerun.sh gteach 29811 > "$S/logs/d_gteach.out" 2>&1 &
sleep 30
CUDA_VISIBLE_DEVICES=$SD setsid nohup bash scripts/grasppilot/run_d_arm_rerun.sh shuf 29812 > "$S/logs/d_shuf.out" 2>&1 &
sleep 30
CUDA_VISIBLE_DEVICES=$BE setsid nohup bash scripts/grasppilot/run_pd_grasparms_rerun.sh empty > "$S/logs/b_empty.out" 2>&1 &
sleep 30
CUDA_VISIBLE_DEVICES=$BG setsid nohup bash scripts/grasppilot/run_pd_grasparms_rerun.sh gt > "$S/logs/b_gt.out" 2>&1 &
echo "started 4 runs: D gteach GPU$GD, D shuf GPU$SD, B empty GPU$BE, B gt GPU$BG"

#!/usr/bin/env bash
# 塔 7 本（G3・H4 の確定と交差適合の半分 H1・H2、G5r の確定）を GPU 2 枚の待ち行列で学ぶ（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task B）。
# 1 枚に 1 本ずつ（1 本の最大確保 25.6 GB、RTX A6000 49 GB）。並びは信号に要る G3・H4 を先、対照の G5r を最後。
#   bash experiments/analysis/grasp_hand_graph_pilot/tools/run_towers.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
Q=$O/queues/towers
mkdir -p "$Q" "$O/logs" "$O/wandb"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$O/wandb WANDB_SILENT=true
JOBS="G3:all H4:all G3:H1 G3:H2 H4:H1 H4:H2 G5r:all"
: > "$Q/next"
for j in $JOBS; do echo "$j" >> "$Q/next"; done

pop() {   # 待ち行列の先頭を一つ取り出す（flock で 2 本の取り合いを防ぐ）
  flock "$Q/lock" bash -c 'h=$(head -1 "$1"); [ -n "$h" ] && sed -i 1d "$1"; echo "$h"' _ "$Q/next"
}

worker() {
  local gpu=$1
  while :; do
    local job; job=$(pop)
    [ -z "$job" ] && break
    local t=${job%%:*} v=${job##*:}
    local name=grasp_hand_graph_tower_${t}_${v}_seed42
    echo "$(date '+%F %T %Z') gpu$gpu start $name" >> "$Q/events.log"
    CUDA_VISIBLE_DEVICES=$gpu python scripts/grasppilot/ghg_tower.py train --tower "$t" --videos "$v" \
      --run-dir "experiments/phase1/$name" --ckpt-dir "$O/ckpt/${t}_${v}" --ann-dir "$O/ann" \
      > "$O/logs/${t}_${v}.log" 2>&1
    local rc=$?
    echo "$(date '+%F %T %Z') gpu$gpu end $name rc=$rc" >> "$Q/events.log"
  done
}

worker 0 &
sleep 30
worker 1 &
wait
echo "$(date '+%F %T %Z') all done" >> "$Q/events.log"

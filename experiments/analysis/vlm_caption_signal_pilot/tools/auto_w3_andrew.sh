#!/usr/bin/env bash
# andrew 上で W2 の全 14 本が起動済みになった後、空き GPU スロットへ W3 の担当 4 本を自動投入する。
set -euo pipefail
M=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot
LOG=$S/task_f/andrew_W3.log
SCRIPT=$M/experiments/analysis/vlm_caption_signal_pilot/tools/run_v2t_one_andrew.sh
mkdir -p "$S/task_f"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%d %H:%M:%S UTC')" "$*" | tee -a "$LOG"; }

log "Waiting until all 14 W2 runs on andrew have started (train.log present)..."
while true; do
  STARTED=$(ls "$M"/experiments/phase1/vlm_caption_signal_pilot_pd_*_W2_*/train.log 2>/dev/null | wc -l)
  if [ "$STARTED" -ge 14 ]; then
    log "All 14 W2 runs started (count=$STARTED). Proceeding to schedule 4 W3 runs into free slots."
    break
  fi
  sleep 60
done

# 担当 4 本（GPU 0 に 2 本、GPU 1 に 2 本。run_v2t_one_andrew.sh が各 GPU <2 本になるまで待機）
# 各 GPU 内で直列 2 本ずつ起動することで、空きスロットが 1 つ開いた瞬間から即投入される
(
  log "GPU 0 slot queue: P1 W3 vlm_ko_shuf -> P1 W3 vlm_hei_shuf"
  CUDA_VISIBLE_DEVICES=0 bash "$SCRIPT" P1 W3 vlm_ko_shuf 16 >> "$LOG" 2>&1
  CUDA_VISIBLE_DEVICES=0 bash "$SCRIPT" P1 W3 vlm_hei_shuf 16 >> "$LOG" 2>&1
) &
P0=$!
sleep 5
(
  log "GPU 1 slot queue: P1 W3 vlm_otsu_shuf -> P2L W3 empty"
  CUDA_VISIBLE_DEVICES=1 bash "$SCRIPT" P1 W3 vlm_otsu_shuf 16 >> "$LOG" 2>&1
  CUDA_VISIBLE_DEVICES=1 bash "$SCRIPT" P2L W3 empty 16 >> "$LOG" 2>&1
) &
P1=$!

wait "$P0"
wait "$P1"
log "ALL 4 ANDREW W3 RUNS COMPLETED!"

#!/usr/bin/env bash
# jobs.py の一覧を GPU 2 枚 × NW/2 本並行で回す（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、Task D）。
# 実験フォルダが在る run は飛ばす。記録は $T/logs/<群>/events.log と run ごとの log。
#   bash experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/run_jobs.sh <群> [fill の先]   （NW 既定 8）
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
GROUP=$1
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt
TASK=T-2026-11-21-grasp-hand-irn-hice-htt-pilot
LOG=$T/logs/$GROUP${2:+_$2}
mkdir -p "$LOG" "$T/dp_ckpt" "$T/wandb"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$T/wandb WANDB_SILENT=true
NW=${NW:-8}
mapfile -t JOBS < <(python3 experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/jobs.py "$GROUP" ${2:-})
echo "[jobs] $GROUP${2:+ $2} jobs ${#JOBS[@]} workers $NW start $(date -u +%FT%TZ)" >> "$LOG/events.log"
worker() {
  local w=$1 gpu=$(( $1 % 2 )) i=0
  for J in "${JOBS[@]}"; do
    if [ $((i % NW)) -eq "$w" ]; then
      IFS='|' read -r DESC PFX ARGS <<< "$J"
      if ls -d experiments/phase1/${PFX}_[0-9][0-9][0-9]_${DESC}_seed42 >/dev/null 2>&1; then
        echo "[jobs] skip $PFX $DESC" >> "$LOG/events.log"
      else
        start=$(date -u +%FT%TZ)
        # shellcheck disable=SC2086
        CUDA_VISIBLE_DEVICES=$gpu python scripts/stage2pilot/dp_train.py train $ARGS --seed 42 --task-id "$TASK" \
          --exp-prefix "$PFX" --ckpt-dir "$T/dp_ckpt" > "$LOG/${PFX}__${DESC}.log" 2>&1
        rc=$?
        echo "[jobs] $PFX $DESC gpu=$gpu w=$w start=$start end=$(date -u +%FT%TZ) rc=$rc $(grep DP_RUN_COMPLETE "$LOG/${PFX}__${DESC}.log")" >> "$LOG/events.log"
      fi
    fi
    i=$((i + 1))
  done
}
for w in $(seq 0 $((NW - 1))); do worker "$w" & sleep 3; done
wait
echo "[jobs] $GROUP${2:+ $2} all done $(date -u +%FT%TZ)" >> "$LOG/events.log"

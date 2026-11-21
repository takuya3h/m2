#!/usr/bin/env bash
# jobs.py の一覧を GPU 2 枚 × NW/2 本並行で回す（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、Task D）。
# 実験フォルダが在る run は飛ばす。記録は $T/logs/<群>/events.log と run ごとの log。
#   bash experiments/analysis/grasp_hand_graph_t2p/tools/run_jobs.sh <群>        （NW 既定 8）
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
GROUP=$1
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p
TASK=T-2026-11-21-grasp-hand-graph-t2p-match
LOG=$T/logs/$GROUP
mkdir -p "$LOG" "$T/dp_ckpt" "$T/wandb"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$T/wandb WANDB_SILENT=true
NW=${NW:-8}
mapfile -t JOBS < <(python3 experiments/analysis/grasp_hand_graph_t2p/tools/jobs.py "$GROUP")
echo "[jobs] $GROUP jobs ${#JOBS[@]} workers $NW start $(date -u +%FT%TZ)" >> "$LOG/events.log"
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
echo "[jobs] $GROUP all done $(date -u +%FT%TZ)" >> "$LOG/events.log"

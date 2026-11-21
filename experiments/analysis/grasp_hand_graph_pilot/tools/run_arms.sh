#!/usr/bin/env bash
# 腕 96 本（8 腕 × 4 設定 × W1・W2・W3）を収束規則で回す（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task D、SPEC §5・§6）。
# GPU 2 枚 × 4 本並行（NW = 8）。実験フォルダが在る腕は飛ばす。最良と最後の回の val の確率を保存する（--save-last-probs）。
#   bash experiments/analysis/grasp_hand_graph_pilot/tools/run_arms.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
TASK=T-2026-11-20-grasp-hand-graph-pilot
PFX=grasp_hand_graph_arm
LOG=$O/logs/arms
mkdir -p "$LOG" "$O/dp_ckpt"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$O/wandb WANDB_SILENT=true
NW=${NW:-8}
JOBS=()
for SC in W1 W2 W3; do
  for ST in "s1 10 1" "s2 10 2" "s3 30 1" "s4 30 2"; do
    read -r S N L <<< "$ST"
    for ARM in empty D DG DH DGH DGH-U DGH-noCF DGH-GT; do
      JOBS+=("GR-$SC-N$N-L$L|$ARM|--type GR --gr-dir $O --gr-N $N --gr-L $L --scope $SC --arm $ARM")
    done
  done
done
echo "[d] jobs ${#JOBS[@]} workers $NW" >> "$LOG/events.log"
worker() {
  local w=$1 gpu=$(( $1 % 2 )) i=0
  for J in "${JOBS[@]}"; do
    if [ $((i % NW)) -eq "$w" ]; then
      IFS='|' read -r DESC ARM ARGS <<< "$J"
      NAME=${DESC}_${ARM}
      if ls -d experiments/phase1/${PFX}_*_${NAME}_conv_seed42 >/dev/null 2>&1; then
        echo "[d] skip $NAME" >> "$LOG/events.log"
      else
        start=$(date -u +%FT%TZ)
        # shellcheck disable=SC2086
        CUDA_VISIBLE_DEVICES=$gpu python scripts/stage2pilot/dp_train.py train $ARGS --seed 42 --converge --task-id "$TASK" \
          --exp-prefix "$PFX" --ckpt-dir "$O/dp_ckpt" --save-last-probs > "$LOG/$NAME.log" 2>&1
        rc=$?
        echo "[d] $NAME gpu=$gpu w=$w start=$start end=$(date -u +%FT%TZ) rc=$rc $(grep DP_RUN_COMPLETE "$LOG/$NAME.log")" >> "$LOG/events.log"
      fi
    fi
    i=$((i + 1))
  done
}
for w in $(seq 0 $((NW - 1))); do worker "$w" & sleep 3; done
wait
echo "[d] all done $(date -u +%FT%TZ)" >> "$LOG/events.log"

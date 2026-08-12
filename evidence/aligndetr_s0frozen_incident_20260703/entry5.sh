#!/bin/bash
# entry5.sh — Entry 5: AlignDETR frozen source TeCNO training queue.
# 手順: (1) 特徴抽出 x 3 subset (2) TeCNO 訓練 x 3 seed。GPU 空き 30GB 待機。
# 対比: 既存 s4_001-003 (Rel-DETR frozen) vs 新規 (AlignDETR frozen)

set -o pipefail
REPO=/home/ubuntu/slocal2/m2
DETREX_ROOT=$REPO/third_party/detrex
DETREX_VENV=$REPO/.venv-detectron2/bin/python
MAIN_VENV=$REPO/.venv/bin/python
ALIGN_CFG=$DETREX_ROOT/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery.py
CKPT=/tmp/aligndetr_work_seed42/model_final.pth
FEAT_ROOT=$REPO/data/processed/stage1_features/aligndetr_seed42
TECNO_SCRIPT=/tmp/queue_runner/train_s4_tecno_aligndetr.py
THRESH_MB=30000

mkdir -p $FEAT_ROOT

echo "$(date '+%H:%M:%S') entry5 queue armed. threshold=${THRESH_MB}MB."

# ---- Wait for GPU free ----
GPU=""
while [ -z "$GPU" ]; do
  free0=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0 2>/dev/null | tr -d ' ')
  free1=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 1 2>/dev/null | tr -d ' ')
  if [ -n "$free0" ] && [ "$free0" -gt "$THRESH_MB" ]; then
    GPU=0
  elif [ -n "$free1" ] && [ "$free1" -gt "$THRESH_MB" ]; then
    GPU=1
  else
    sleep 60
  fi
done
echo "$(date '+%H:%M:%S') GPU $GPU freed. entry5 starts."

# ---- Phase 1: feature extraction x 3 subsets ----
for SUBSET in val test train; do
  OUT=$FEAT_ROOT/${SUBSET}_gap.npz
  LOG=$FEAT_ROOT/${SUBSET}_extract.log
  if [ -f "$OUT" ]; then
    echo "$(date '+%H:%M:%S') SKIP extract $SUBSET (already exists)"
    continue
  fi
  echo "$(date '+%H:%M:%S') START extract $SUBSET on GPU $GPU"
  cd $REPO || exit 1
  CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=$DETREX_ROOT PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    $DETREX_VENV scripts/extract_stage1_features_aligndetr.py \
      --subset $SUBSET \
      --config-file $ALIGN_CFG \
      --checkpoint $CKPT \
      --out $OUT \
      > $LOG 2>&1
  RC=$?
  if [ $RC -eq 0 ] && [ -f "$OUT" ]; then
    SIZE=$(stat -c '%s' "$OUT")
    echo "$(date '+%H:%M:%S') DONE extract $SUBSET rc=$RC size=$((SIZE/1024/1024))MB"
  else
    TAIL=$(grep -E "Traceback|Error|OOM|Killed" "$LOG" | tail -1)
    echo "$(date '+%H:%M:%S') FAIL extract $SUBSET rc=$RC $TAIL"
    exit 2
  fi
done

# ---- Phase 2: TeCNO training x 3 seeds ----
for SEED in 42 123 456; do
  MARKER=/tmp/queue_runner/entry5_tecno_seed${SEED}.marker
  LOG=/tmp/queue_runner/entry5_tecno_seed${SEED}.log
  if [ -f "$MARKER" ]; then
    echo "$(date '+%H:%M:%S') SKIP TeCNO seed=$SEED (marker exists)"
    continue
  fi
  echo "$(date '+%H:%M:%S') START TeCNO seed=$SEED (AlignDETR frozen)"
  cd $REPO || exit 1
  CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=$REPO/src PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    $MAIN_VENV $TECNO_SCRIPT --seed $SEED --epochs 50 \
    > $LOG 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then
    ACC=$(grep -E "best.*accuracy|accuracy.*=" $LOG | tail -3)
    echo "$(date '+%H:%M:%S') DONE TeCNO seed=$SEED rc=$RC"
    echo "  $ACC"
    touch $MARKER
  else
    TAIL=$(grep -E "Traceback|Error|OOM|Killed" "$LOG" | tail -3)
    echo "$(date '+%H:%M:%S') FAIL TeCNO seed=$SEED rc=$RC"
    echo "  $TAIL"
  fi
done

echo "$(date '+%H:%M:%S') ENTRY5 QUEUE COMPLETE."

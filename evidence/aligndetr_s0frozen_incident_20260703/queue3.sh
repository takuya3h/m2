#!/bin/bash
# queue3.sh — Entry 6: Rel-DETR × 3 seed + AlignDETR × 3 seed test-split re-eval.
# recipe: score_thr=0.0系 NMS-free (両検出器とも DETR set-based prediction = NMS-free by design)
# データ: /tmp/coco_ego/{test2017, annotations/instances_test2017.json}

REPO=/home/ubuntu/slocal2/m2
RD_ROOT=$REPO/third_party/Relation-DETR
DETREX_ROOT=$REPO/third_party/detrex
COCO_PATH=/tmp/coco_ego
RD_VENV=$REPO/.venv-relation-detr/bin/python
DETREX_VENV=$REPO/.venv-detectron2/bin/python
RD_MODEL_CFG=$RD_ROOT/configs/relation_detr/relation_detr_resnet50_egosurgery.py
ALIGN_CFG=$REPO/third_party/detrex/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery.py
THRESH_MB=30000

echo "$(date '+%H:%M:%S') queue3 armed. entries=6 (Rel-DETR × 3 + AlignDETR × 3). threshold=${THRESH_MB}MB."

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
echo "$(date '+%H:%M:%S') GPU $GPU freed. queue3 starts."

success=0; crash=0

# ---- Rel-DETR × 3 seed ----
for SEED in 42 123 456; do
  LABEL=reldetr_seed$SEED
  CKPT=/tmp/reldetr_work_seed$SEED/best_ap.pth
  OUT=/tmp/queue_runner/$LABEL
  mkdir -p $OUT
  LOG=$OUT/eval.log

  if [ -f "$OUT/completed.marker" ]; then
    echo "$(date '+%H:%M:%S') SKIP $LABEL (already completed)"
    success=$((success+1)); continue
  fi
  if [ ! -f "$CKPT" ]; then
    echo "$(date '+%H:%M:%S') MISSING $LABEL ckpt=$CKPT. SKIP."; continue
  fi

  echo "$(date '+%H:%M:%S') START $LABEL on GPU $GPU (Rel-DETR test.py)."
  cd $RD_ROOT || exit 1
  CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=$RD_ROOT PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    $RD_VENV test.py \
      --coco-path $COCO_PATH \
      --subset test \
      --model-config $RD_MODEL_CFG \
      --checkpoint $CKPT \
      --seed $SEED \
      > $LOG 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then
    MAP=$(grep -E "Average Precision.*IoU=0.50:0.95.*area=   all.*maxDets=100" $LOG | tail -1 | awk '{print $NF}')
    echo "$(date '+%H:%M:%S') DONE  $LABEL rc=$RC mAP=$MAP"
    touch $OUT/completed.marker
    success=$((success+1))
  else
    TAIL=$(grep -E "Traceback|Error|OOM|CUDA out of memory|Killed" $LOG 2>/dev/null | tail -1)
    echo "$(date '+%H:%M:%S') FAIL  $LABEL rc=$RC $TAIL"
    crash=$((crash+1))
  fi
done

# ---- AlignDETR × 3 seed ----
for SEED in 42 123 456; do
  LABEL=aligndetr_seed$SEED
  CKPT=/tmp/aligndetr_work_seed$SEED/model_final.pth
  OUT=/tmp/queue_runner/$LABEL
  mkdir -p $OUT
  LOG=$OUT/eval.log

  if [ -f "$OUT/completed.marker" ]; then
    echo "$(date '+%H:%M:%S') SKIP $LABEL (already completed)"
    success=$((success+1)); continue
  fi
  if [ ! -f "$CKPT" ]; then
    echo "$(date '+%H:%M:%S') MISSING $LABEL ckpt=$CKPT. SKIP."; continue
  fi

  echo "$(date '+%H:%M:%S') START $LABEL on GPU $GPU (detrex --eval-only, egosurgery_test)."
  cd $DETREX_ROOT || exit 1
  CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=$DETREX_ROOT PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    $DETREX_VENV tools/train_net_egosurgery.py \
      --config-file $ALIGN_CFG \
      --num-gpus 1 \
      --eval-only \
      train.init_checkpoint=$CKPT \
      dataloader.test.dataset.names=egosurgery_test \
      > $LOG 2>&1
  RC=$?
  if [ $RC -eq 0 ]; then
    MAP=$(grep -E "AP\s*[:\s]|bbox/AP\b" $LOG | tail -3)
    echo "$(date '+%H:%M:%S') DONE  $LABEL rc=$RC"
    echo "  $MAP"
    touch $OUT/completed.marker
    success=$((success+1))
  else
    TAIL=$(grep -E "Traceback|Error|OOM|CUDA out of memory|Killed" $LOG 2>/dev/null | tail -1)
    echo "$(date '+%H:%M:%S') FAIL  $LABEL rc=$RC $TAIL"
    crash=$((crash+1))
  fi
done

echo "$(date '+%H:%M:%S') QUEUE3 COMPLETE. success=$success crash=$crash total=6"

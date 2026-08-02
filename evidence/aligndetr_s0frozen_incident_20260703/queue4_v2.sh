#!/bin/bash
# queue4_v2.sh — AlignDETR S0-frozen seed42 訓練 (2 GPU DDP)。他 AlignDETR (s0_028) と GPU 数を揃える。
# 訓練だけを担当。抽出は queue4_parallel_extract.sh が model_final.pth 出現で自動発火。
#
# 前提: GPU 0 と GPU 1 の両方に >= THRESH_MB 空き。

set -o pipefail
REPO=/home/ubuntu/slocal2/m2
DETREX_ROOT=$REPO/third_party/detrex
DETREX_VENV=$REPO/.venv-detectron2/bin/python
S0FROZEN_CFG=$DETREX_ROOT/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py
TRAIN_OUT=/tmp/aligndetr_s0frozen_seed42_v2
THRESH_MB=30000

mkdir -p $TRAIN_OUT

echo "$(date '+%H:%M:%S') queue4_v2 armed (2 GPU DDP). threshold=${THRESH_MB}MB per GPU."

# ---- Wait for BOTH GPUs free ----
while true; do
  free0=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 0 2>/dev/null | tr -d ' ')
  free1=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits -i 1 2>/dev/null | tr -d ' ')
  if [ -n "$free0" ] && [ -n "$free1" ] && [ "$free0" -gt "$THRESH_MB" ] && [ "$free1" -gt "$THRESH_MB" ]; then
    break
  fi
  sleep 60
done
echo "$(date '+%H:%M:%S') both GPUs freed (0=${free0}MB, 1=${free1}MB). Training starts."

# ---- Train S0-frozen with 2 GPUs (matches s0_028 recipe) ----
cd $DETREX_ROOT || exit 1
CUDA_VISIBLE_DEVICES=0,1 PYTHONPATH=$DETREX_ROOT PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  WANDB_MODE=disabled \
  NCCL_P2P_DISABLE=1 NCCL_IB_DISABLE=1 NCCL_DEBUG=WARN \
  $DETREX_VENV tools/train_net_egosurgery.py \
    --config-file $S0FROZEN_CFG \
    --num-gpus 2 \
    train.seed=42 \
    train.output_dir=$TRAIN_OUT \
    > $TRAIN_OUT/train.log 2>&1
RC=$?
TRAIN_CKPT=$TRAIN_OUT/model_final.pth
if [ $RC -eq 0 ] && [ -f "$TRAIN_CKPT" ]; then
  echo "$(date '+%H:%M:%S') DONE train S0-frozen (2 GPU). ckpt=$TRAIN_CKPT"
else
  TAIL=$(grep -E "Traceback|OOM|CUDA out of memory|Killed|RuntimeError" $TRAIN_OUT/train.log 2>/dev/null | tail -1)
  echo "$(date '+%H:%M:%S') FAIL train S0-frozen rc=$RC $TAIL"
  exit 2
fi

echo "$(date '+%H:%M:%S') queue4_v2 COMPLETE (extractions delegated to queue4_parallel_extract watchdog)."

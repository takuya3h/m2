#!/bin/bash
# queue4.sh — 台帳 planned: AlignDETR 凍結特徴抽出 (region-token/tool-presence, val+train)
#
# 手順:
#   Phase 1: AlignDETR-S0-frozen seed42 訓練 (12ep, backbone freeze) → ~1.5-2h
#   Phase 2: region-token val 抽出
#   Phase 3: region-token train 抽出
#   Phase 4: tool-presence val 抽出
#   Phase 5: tool-presence train 抽出
#
# 前提: 他コンテナの GPU プロセス終了待ち (>= 30GB 空き)。単 GPU で完結。

set -o pipefail
REPO=/home/ubuntu/slocal2/m2
DETREX_ROOT=$REPO/third_party/detrex
DETREX_VENV=$REPO/.venv-detectron2/bin/python
S0FROZEN_CFG=$DETREX_ROOT/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py
TRAIN_OUT=/tmp/aligndetr_s0frozen_seed42_v2
TRAIN_CKPT=$TRAIN_OUT/model_final.pth
RT_ROOT=$REPO/data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42
TP_ROOT=$REPO/data/processed/b2a_detsignal/aligndetr_s0frozen_seed42
THRESH_MB=30000

mkdir -p $RT_ROOT $TP_ROOT $TRAIN_OUT

echo "$(date '+%H:%M:%S') queue4 armed. threshold=${THRESH_MB}MB, seed=42."

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
echo "$(date '+%H:%M:%S') GPU $GPU freed. queue4 starts."

# ---- Phase 1: Train S0-frozen ----
if [ ! -f "$TRAIN_CKPT" ]; then
  echo "$(date '+%H:%M:%S') START train S0-frozen aligndetr seed42 on GPU $GPU (~1.5-2h)"
  cd $DETREX_ROOT || exit 1
  CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=$DETREX_ROOT PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    WANDB_MODE=disabled \
    $DETREX_VENV tools/train_net_egosurgery.py \
      --config-file $S0FROZEN_CFG \
      --num-gpus 1 \
      train.seed=42 \
      train.output_dir=$TRAIN_OUT \
      > $TRAIN_OUT/train.log 2>&1
  RC=$?
  if [ $RC -ne 0 ] || [ ! -f "$TRAIN_CKPT" ]; then
    TAIL=$(grep -E "Traceback|OOM|CUDA out of memory|Killed|RuntimeError" $TRAIN_OUT/train.log 2>/dev/null | tail -1)
    echo "$(date '+%H:%M:%S') FAIL train S0-frozen rc=$RC $TAIL"
    exit 2
  fi
  echo "$(date '+%H:%M:%S') DONE train S0-frozen. ckpt=$TRAIN_CKPT"
else
  echo "$(date '+%H:%M:%S') SKIP train (ckpt exists)"
fi

# ---- Phase 2-5: 4 extractions ----
run_extract() {
  local NAME=$1 SCRIPT=$2 SUBSET=$3 OUT=$4
  if [ -f "$OUT" ]; then
    echo "$(date '+%H:%M:%S') SKIP $NAME (already exists)"
    return 0
  fi
  echo "$(date '+%H:%M:%S') START $NAME on GPU $GPU"
  cd $REPO || return 1
  CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=$DETREX_ROOT PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    $DETREX_VENV $SCRIPT \
      --subset $SUBSET \
      --config-file $S0FROZEN_CFG \
      --checkpoint $TRAIN_CKPT \
      --out $OUT \
      > "${OUT%.npz}.log" 2>&1
  RC=$?
  if [ $RC -eq 0 ] && [ -f "$OUT" ]; then
    SIZE=$(stat -c '%s' "$OUT")
    echo "$(date '+%H:%M:%S') DONE  $NAME rc=$RC size=$((SIZE/1024/1024))MB"
  else
    TAIL=$(grep -E "Traceback|OOM|Killed" "${OUT%.npz}.log" 2>/dev/null | tail -1)
    echo "$(date '+%H:%M:%S') FAIL  $NAME rc=$RC $TAIL"
    return 1
  fi
}

run_extract "region-token val"    scripts/extract_t1a_regiontoken_aligndetr.py    val   $RT_ROOT/val_regiontoken.npz
run_extract "region-token train"  scripts/extract_t1a_regiontoken_aligndetr.py    train $RT_ROOT/train_regiontoken.npz
run_extract "tool-presence val"   scripts/extract_b2a_toolpresence_aligndetr.py   val   $TP_ROOT/val_toolpresence.npz
run_extract "tool-presence train" scripts/extract_b2a_toolpresence_aligndetr.py   train $TP_ROOT/train_toolpresence.npz

echo "$(date '+%H:%M:%S') QUEUE4 COMPLETE."

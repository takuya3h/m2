#!/bin/bash
# queue4_parallel_extract.sh — 訓練完了を watch し、model_final.pth が出た瞬間に
# 両 GPU (0=val 系, 1=train 系) で 4 抽出を並列実行。
# 既存 queue4.sh は完了後にこれらの npz を見つけて自動 skip する。

set -o pipefail
REPO=/home/ubuntu/slocal2/m2
DETREX_ROOT=$REPO/third_party/detrex
DETREX_VENV=$REPO/.venv-detectron2/bin/python
S0FROZEN_CFG=$DETREX_ROOT/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py
TRAIN_CKPT=/tmp/aligndetr_s0frozen_seed42_v2/model_final.pth
RT_ROOT=$REPO/data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42
TP_ROOT=$REPO/data/processed/b2a_detsignal/aligndetr_s0frozen_seed42

mkdir -p $RT_ROOT $TP_ROOT

echo "$(date '+%H:%M:%S') parallel-extract watchdog armed. waiting for $TRAIN_CKPT ..."
until [ -f "$TRAIN_CKPT" ]; do sleep 60; done
echo "$(date '+%H:%M:%S') model_final.pth found. launching 4 parallel extractions."

# 実装方針: GPU 0=val 系, GPU 1=train 系 の 2×2 分割で並列。
# val (1515 frames) は train (9657 frames) の 1/6 のため、val 完了後に同 GPU で余った train 系タスクは無い。
# 4 タスクを 2 GPU に均等配分: GPU 0=rt-val + tp-val, GPU 1=rt-train + tp-train
run_extract_on_gpu() {
  local GPU=$1 NAME=$2 SCRIPT=$3 SUBSET=$4 OUT=$5
  if [ -f "$OUT" ]; then
    echo "$(date '+%H:%M:%S') [GPU$GPU] SKIP $NAME (already exists)"
    return 0
  fi
  echo "$(date '+%H:%M:%S') [GPU$GPU] START $NAME"
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
    echo "$(date '+%H:%M:%S') [GPU$GPU] DONE  $NAME rc=$RC size=$((SIZE/1024/1024))MB"
  else
    TAIL=$(grep -E "Traceback|OOM|Killed" "${OUT%.npz}.log" 2>/dev/null | tail -1)
    echo "$(date '+%H:%M:%S') [GPU$GPU] FAIL  $NAME rc=$RC $TAIL"
  fi
}

# GPU 0 で val 系 2 本を直列
(
  run_extract_on_gpu 0 "region-token val"  scripts/extract_t1a_regiontoken_aligndetr.py val $RT_ROOT/val_regiontoken.npz
  run_extract_on_gpu 0 "tool-presence val" scripts/extract_b2a_toolpresence_aligndetr.py val $TP_ROOT/val_toolpresence.npz
) &
PID_GPU0=$!

# GPU 1 で train 系 2 本を直列
(
  run_extract_on_gpu 1 "region-token train"  scripts/extract_t1a_regiontoken_aligndetr.py train $RT_ROOT/train_regiontoken.npz
  run_extract_on_gpu 1 "tool-presence train" scripts/extract_b2a_toolpresence_aligndetr.py train $TP_ROOT/train_toolpresence.npz
) &
PID_GPU1=$!

echo "$(date '+%H:%M:%S') parallel launched: GPU0-pid=$PID_GPU0 GPU1-pid=$PID_GPU1"
wait $PID_GPU0
echo "$(date '+%H:%M:%S') GPU 0 val-pair complete."
wait $PID_GPU1
echo "$(date '+%H:%M:%S') GPU 1 train-pair complete."

echo "$(date '+%H:%M:%S') PARALLEL EXTRACT COMPLETE."

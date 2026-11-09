#!/usr/bin/env bash
# 非公式 T-2026-11-09-grasp-roitoken-transition-pilot、Task E（案 3、型 RT、W1）。利用者の決定で案 5 は回さない。
# 8 設定（中身 {roi_geo, roi} × 層 {layer4, layer3} × K {16, 64}）× 7 腕（T0 empty・TG pred_CF・TGeo geo・TU union・TRand shuffle・
# 参照段 正解 gt・正解 ⊕ 予測 gtpred_CF）= 56 本を学ぶ。P 単独は学ばない（塔の値）。処方は四本目と同じ（学習率 5e-4、4 epoch 固定、
# 最後の状態、seed 42）。run は experiments/phase1/grasprt_rt_<番号>_RT-<層>-<中身>-K<K>_<腕>_ep4_seed42。
#   bash run_e.sh <GPU> <worker> <workers>   全 56 本の並びのうち (i mod workers) == worker の本だけを順に回す
set -uo pipefail
GPU=$1
W=$2
NW=$3
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-grasp-roitoken-transition-pilot
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
LOG=$S/e
mkdir -p "$LOG"
cd "$M"
# shellcheck disable=SC1091
source .venv/bin/activate
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
export PYTHONPATH=$M/src:$M/scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
i=0
for L in layer4 layer3; do for CT in roi_geo roi; do for K in 16 64; do
  for ARM in empty pred_CF geo union shuffle gt gtpred_CF; do
    if [ $((i % NW)) -eq "$W" ]; then
      NAME=RT-$L-$CT-K${K}_$ARM
      if ls -d experiments/phase1/grasprt_rt_*_${NAME}_ep4_seed42 >/dev/null 2>&1; then
        echo "[e] skip $NAME（実験フォルダが在る）"
      else
        start=$(date -u +%FT%TZ)
        python scripts/stage2pilot/dp_train.py train --type RT --rt-dir "$S" --rt-layer $L --rt-content $CT --rt-k $K \
          --arm $ARM --seed 42 --fixed-epochs 4 --task-id "$TASK" --exp-prefix grasprt_rt > "$LOG/$NAME.log" 2>&1
        rc=$?
        echo "[e] $NAME gpu=$GPU start=$start end=$(date -u +%FT%TZ) rc=$rc $(grep DP_RUN_COMPLETE "$LOG/$NAME.log")"
      fi
    fi
    i=$((i + 1))
  done
done; done; done
echo "[e] worker $W/$NW done"

#!/usr/bin/env bash
# 非公式 T-2026-11-09-grasp-roitoken-transition-pilot、案 5 の追加（利用者の依頼 2026-11-09「案5、追加でやって」）の Task E（型 TW）。
# SPEC §3.3 の run の表: W 3 × 形 2 の 6 設定で S_0（empty）・S_1（t1）、W 3 × L 2 × 形 2 の 12 設定で S_W（pred_CF）・
# S_W-perm（perm）・S_W-U（union）・S_W-R（shuffle）、W1 × L 2 × 形 2 の 4 設定で参照段 正解（gt）・正解 ⊕ 予測（gtpred_CF）= 68 本。
# K = 64。処方は四本目（W1）と T-2026-11-01-stage2-w23-bengio（W2・W3、受け取り手の学習率 5e-4）と同じ、4 epoch 固定・最後の状態・seed 42。
# run は experiments/phase1/grasprt_tw_<番号>_TW-<W>-<形>[-L<L>]-K64_<腕>_ep4_seed42。
#   bash run_e5.sh <GPU> <worker> <workers>
set -uo pipefail
GPU=$1
W_=$2
NW=$3
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-grasp-roitoken-transition-pilot
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
LOG=$S/e5
mkdir -p "$LOG"
cd "$M"
# shellcheck disable=SC1091
source .venv/bin/activate
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
export PYTHONPATH=$M/src:$M/scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
JOBS=()
for SC in W1 W2 W3; do for F in a b; do
  JOBS+=("$SC $F 0 empty" "$SC $F 0 t1")
  for L in 8 32; do for ARM in pred_CF perm union shuffle; do JOBS+=("$SC $F $L $ARM"); done; done
done; done
for F in a b; do for L in 8 32; do for ARM in gt gtpred_CF; do JOBS+=("W1 $F $L $ARM"); done; done; done
[ "$W_" -eq 0 ] && echo "[e5] jobs ${#JOBS[@]}"
i=0
for J in "${JOBS[@]}"; do
  if [ $((i % NW)) -eq "$W_" ]; then
    read -r SC F L ARM <<< "$J"
    LARG=()
    NAME=TW-$SC-$F-K64_$ARM
    if [ "$L" != 0 ]; then LARG=(--tw-L "$L"); NAME=TW-$SC-$F-L$L-K64_$ARM; fi
    if ls -d experiments/phase1/grasprt_tw_*_${NAME}_ep4_seed42 >/dev/null 2>&1; then
      echo "[e5] skip $NAME（実験フォルダが在る）"
    else
      start=$(date -u +%FT%TZ)
      python scripts/stage2pilot/dp_train.py train --type TW --tw-dir "$S" --tw-form "$F" "${LARG[@]}" --tw-k 64 --scope "$SC" \
        --arm "$ARM" --seed 42 --fixed-epochs 4 --task-id "$TASK" --exp-prefix grasprt_tw > "$LOG/$NAME.log" 2>&1
      rc=$?
      echo "[e5] $NAME gpu=$GPU start=$start end=$(date -u +%FT%TZ) rc=$rc $(grep DP_RUN_COMPLETE "$LOG/$NAME.log")"
    fi
  fi
  i=$((i + 1))
done
echo "[e5] worker $W_/$NW done"

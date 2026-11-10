#!/usr/bin/env bash
# 非公式 T-2026-11-09-grasp-pilot-converge、Task C。SPEC §3.3 の 127 本を収束規則（--converge）で学ぶ。
# 腕・設定は前の予備（T-2026-11-09-grasp-roitoken-transition-pilot）と四本目（T-2026-11-06-grasp-pilot-arms）と同じで、処方だけが違う。
#   案 3 RT W1: 8 設定 × 7 腕 = 56     run は experiments/phase1/grasprc_rt_<番号>_RT-<層>-<中身>-K<K>_<腕>_conv_seed42
#   案 5 TW:   12 設定 × 4 腕 ＋ 6 設定 × 2 腕 ＋ 参照段 8 = 68   grasprc_tw_<番号>_TW-<W>-<形>[-L<L>]-K64_<腕>_conv_seed42
#   案 A GA W1 旗なし: 空・予測-noCF・入れ替え = 3                  grasprc_ga_<番号>_GA-noflag_<腕>_conv_seed42
# トークン・列は前の予備の保存先、案 A の信号は T-2026-11-05 の保存先を読むだけ。
#   bash run_c.sh <GPU> <worker> <workers>
set -uo pipefail
GPU=$1
W_=$2
NW=$3
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-grasp-pilot-converge
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
P=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot
GT=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals
PRED=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/A
LOG=$S/c
mkdir -p "$LOG"
cd "$M"
# shellcheck disable=SC1091
source .venv/bin/activate
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
export PYTHONPATH=$M/src:$M/scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
JOBS=()
for L in layer4 layer3; do for CT in roi_geo roi; do for K in 16 64; do for ARM in empty pred_CF geo union shuffle gt gtpred_CF; do
  JOBS+=("RT|grasprc_rt|RT-$L-$CT-K${K}_$ARM|--type RT --rt-dir $P --rt-layer $L --rt-content $CT --rt-k $K --arm $ARM")
done; done; done; done
for SC in W1 W2 W3; do for F in a b; do
  for ARM in empty t1; do JOBS+=("TW|grasprc_tw|TW-$SC-$F-K64_$ARM|--type TW --tw-dir $P --tw-form $F --tw-k 64 --scope $SC --arm $ARM"); done
  for L in 8 32; do for ARM in pred_CF perm union shuffle; do
    JOBS+=("TW|grasprc_tw|TW-$SC-$F-L$L-K64_$ARM|--type TW --tw-dir $P --tw-form $F --tw-L $L --tw-k 64 --scope $SC --arm $ARM")
  done; done
done; done
for F in a b; do for L in 8 32; do for ARM in gt gtpred_CF; do
  JOBS+=("TW|grasprc_tw|TW-W1-$F-L$L-K64_$ARM|--type TW --tw-dir $P --tw-form $F --tw-L $L --tw-k 64 --scope W1 --arm $ARM")
done; done; done
for ARM in empty pred_noCF shuffle; do
  JOBS+=("GA|grasprc_ga|GA-noflag_$ARM|--type GA --grasp-signal-dir $GT --grasp-pred-dir $PRED --grasp-no-flag --arm $ARM")
done
[ "$W_" -eq 0 ] && echo "[c] jobs ${#JOBS[@]}"
i=0
for J in "${JOBS[@]}"; do
  if [ $((i % NW)) -eq "$W_" ]; then
    IFS='|' read -r _ PFX NAME ARGS <<< "$J"
    if ls -d experiments/phase1/${PFX}_*_${NAME}_conv_seed42 >/dev/null 2>&1; then
      echo "[c] skip $NAME（実験フォルダが在る）"
    else
      start=$(date -u +%FT%TZ)
      # shellcheck disable=SC2086
      python scripts/stage2pilot/dp_train.py train $ARGS --seed 42 --converge --task-id "$TASK" --exp-prefix "$PFX" \
        > "$LOG/$NAME.log" 2>&1
      rc=$?
      echo "[c] $NAME gpu=$GPU start=$start end=$(date -u +%FT%TZ) rc=$rc $(grep DP_RUN_COMPLETE "$LOG/$NAME.log")"
    fi
  fi
  i=$((i + 1))
done
echo "[c] worker $W_/$NW done"

#!/usr/bin/env bash
# Task F（SPEC §3.2 の記録）: 学習後の extra-queries の寄与（非公式 T-2026-10-19-stage2-pilot-four-new-types）。
# 各腕の 4 epoch 目の界面（$FOUR/pd_ckpt/<run>/best_t1b.pth）で val を評価し、最終の検出（和集合の上位 300）と元の出力だけの検出の両方の指標、
# 上位 300 に入った追加の出力の数、照合した見落としの数（xq_missed.py contrib）を出す。
#   run_xq_contrib.sh <GPU> <腕> [<腕> ...]
set -uo pipefail
GPU=$1; shift
WT=/home/ubuntu/slocal2/m2-four
OV=/home/ubuntu/slocal2/s2fix-bengio-body
FOUR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
SH=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle
F=$OLD/signals/final
OUT=$WT/experiments/analysis/stage2_pilot_four/xq_contrib
ANN=$OV/data/annotations/egosurgery_tool_folds/A
mkdir -p "$OUT" "$FOUR/xq_contrib"
cd "$WT"
for ARM in "$@"; do
  DIM=9; EXTRA=()
  case "$ARM" in
    empty) SIG=$F/P0_val.npz; EXTRA=(--zero-ctx) ;;
    pred_noCF|pred_CF) SIG=$F/P0_val.npz ;;
    gt) SIG=$F/P-GT_val.npz ;;
    gtpred_CF) SIG=$OLD/arms/PD/gtpred_noCF_val.npz; DIM=18 ;;
    shuffle) SIG=$SH/P0_val.npz ;;
  esac
  RUN=stage2four_pd_EQ_${ARM}_ep4_seed42
  (
    # shellcheck disable=SC1091
    source "$OV/.venv-relation-detr/bin/activate"
    export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$ANN PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=$GPU
    python scripts/stage2pilot/pd_four_eval.py --cfg "configs/stage2pilot/pd_extra_q_d${DIM}.py" \
      --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
      --iface-state "$FOUR/pd_ckpt/$RUN/best_t1b.pth" --signal-val "$SIG" "${EXTRA[@]}" \
      --ref-preds "$FOUR/identity/plain_val_preds.json.gz" --save-preds "$FOUR/xq_contrib/${ARM}_final.json.gz" \
      --out "$OUT/pd_EQ_${ARM}_trained.json" > "$OUT/pd_EQ_${ARM}_trained.log" 2>&1
    echo "[xq_contrib] eval $ARM rc=$?"
  )
  /home/ubuntu/slocal2/m2/.venv/bin/python scripts/stage2pilot/xq_missed.py contrib --ann "$ANN/instances_val.json" \
    --preds "$FOUR/xq_contrib/${ARM}_final.json.gz" --from-extra "$FOUR/xq_contrib/${ARM}_final_from_extra.json.gz" \
    --missed "$FOUR/xq/missed_val.json" --out "$OUT/pd_EQ_${ARM}_contrib.json" > "$OUT/pd_EQ_${ARM}_contrib.log" 2>&1
  echo "[xq_contrib] contrib $ARM rc=$?"
done

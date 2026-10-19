#!/usr/bin/env bash
# Task C-5・C-6（PD）: 工程から検出の二つの型（DX decoder-xattn、EQ extra-queries）の全 6 腕で、学習前の出力が塔単独と一致するか（val 全 1,515 枚、
# 基準は Task B-2 の塔単独の予測）と、陽性対照・extra-queries の追加の検査を回す（非公式 T-2026-10-19-stage2-pilot-four-new-types）。
#   run_pd_identity.sh <レーンの数> <このレーンの番号>    GPU はレーンの番号の偶奇で 0 と 1 に分ける
set -uo pipefail
LANES=$1; LANE=$2
WT=/home/ubuntu/slocal2/m2-four
OV=/home/ubuntu/slocal2/s2fix-bengio-body
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
SH=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle
REF=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/identity/plain_val_preds.json.gz
OUT=$WT/experiments/analysis/stage2_pilot_four/identity
F=$OLD/signals/final
cd "$WT"
# shellcheck disable=SC1091
source "$OV/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A PYTHONUTF8=1
export CUDA_VISIBLE_DEVICES=$((LANE % 2))
JOBS=()
for T in DX EQ; do
  I=$([ $T = DX ] && echo dec_xattn || echo extra_q)
  JOBS+=("$T empty $I 9 $F/P0_val.npz --zero-ctx")
  JOBS+=("$T pred_noCF $I 9 $F/P0_val.npz")
  JOBS+=("$T gt $I 9 $F/P-GT_val.npz")
  JOBS+=("$T pred_CF $I 9 $F/P0_val.npz")
  JOBS+=("$T gtpred_CF $I 18 $OLD/arms/PD/gtpred_noCF_val.npz")
  JOBS+=("$T shuffle $I 9 $SH/P0_val.npz")
done
JOBS+=("DX positive_gate dec_xattn 9 $F/P0_val.npz --perturb gate")
JOBS+=("EQ positive_score0 extra_q 9 $F/P0_val.npz --perturb score0")
JOBS+=("EQ random_weights extra_q 9 $F/P0_val.npz --perturb random")
JOBS+=("EQ positive_unmask extra_q 9 $F/P0_val.npz --perturb unmask")
for k in "${!JOBS[@]}"; do
  [ $((k % LANES)) = "$LANE" ] || continue
  read -r T ARM I DIM SIG EXTRA <<< "${JOBS[$k]}"
  NAME=pd_${T}_${ARM}
  [ -f "$OUT/$NAME.json" ] && { echo "[pd_identity] 済み $NAME"; continue; }
  # shellcheck disable=SC2086
  python scripts/stage2pilot/pd_four_eval.py --cfg "configs/stage2pilot/pd_${I}_d${DIM}.py" \
    --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --signal-val "$SIG" --ref-preds "$REF" $EXTRA --out "$OUT/$NAME.json" > "$OUT/$NAME.log" 2>&1
  echo "[pd_identity] $NAME rc=$? $(tail -1 "$OUT/$NAME.log" | cut -c1-200)"
done

#!/usr/bin/env bash
# Task C-5・C-6（PD）: 新しい型の全 6 腕で学習前の出力が塔単独と一致するか（val 全 1,515 枚）と陽性対照を回す
# （非公式 T-2026-10-19-stage2-pilot-four-new-types）。ホストに依らない形（bengio の記録は
# experiments/analysis/stage2_pilot_four/identity/run_pd_identity.sh、andrew は handoff_andrew.md でこれを使う）。
#
#   run_pd_four_identity.sh <レーンの数> <このレーンの番号>     GPU はレーンの番号の偶奇で 0 と 1
#   S2FIX_BODY   データ・仮想環境・Relation-DETR・検出塔の重みの場所（既定 /home/ubuntu/slocal2/m2）
#   S2FOUR_REF   基準の予測（塔単独。pd_eval.py --cfg plain --save-preds の出力）
#   S2FOUR_OUT   出力の置き場（新しいフォルダ）
#   S2FOUR_TYPES 回す型（既定 "DX EQ"）
set -uo pipefail
LANES=$1; LANE=$2
CODE=$(cd "$(dirname "$0")/../.." && pwd)
BODY=${S2FIX_BODY:-/home/ubuntu/slocal2/m2}
REF=${S2FOUR_REF:?基準の予測 S2FOUR_REF を渡す}
OUT=${S2FOUR_OUT:?出力の置き場 S2FOUR_OUT を渡す}
TYPES=${S2FOUR_TYPES:-DX EQ}
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
SH=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle
F=$OLD/signals/final
mkdir -p "$OUT"
cd "$CODE"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$BODY EGO_ROOT=$BODY/data/raw/ego EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/A
export PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=$((LANE % 2))
JOBS=()
for T in $TYPES; do
  I=$([ "$T" = DX ] && echo dec_xattn || echo extra_q)
  JOBS+=("$T empty $I 9 $F/P0_val.npz --zero-ctx")
  JOBS+=("$T pred_noCF $I 9 $F/P0_val.npz")
  JOBS+=("$T gt $I 9 $F/P-GT_val.npz")
  JOBS+=("$T pred_CF $I 9 $F/P0_val.npz")
  JOBS+=("$T gtpred_CF $I 18 $OLD/arms/PD/gtpred_noCF_val.npz")
  JOBS+=("$T shuffle $I 9 $SH/P0_val.npz")
  if [ "$T" = DX ]; then
    JOBS+=("DX positive_gate dec_xattn 9 $F/P0_val.npz --perturb gate")
  else
    JOBS+=("EQ positive_score0 extra_q 9 $F/P0_val.npz --perturb score0")
    JOBS+=("EQ random_weights extra_q 9 $F/P0_val.npz --perturb random")
    JOBS+=("EQ positive_unmask extra_q 9 $F/P0_val.npz --perturb unmask")
  fi
done
for k in "${!JOBS[@]}"; do
  [ $((k % LANES)) = "$LANE" ] || continue
  read -r T ARM I DIM SIG EXTRA <<< "${JOBS[$k]}"
  NAME=pd_${T}_${ARM}
  [ -f "$OUT/$NAME.json" ] && { echo "[pd_four_identity] 済み $NAME"; continue; }
  # shellcheck disable=SC2086
  python scripts/stage2pilot/pd_four_eval.py --cfg "configs/stage2pilot/pd_${I}_d${DIM}.py" \
    --det-ckpt "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --signal-val "$SIG" --ref-preds "$REF" $EXTRA --out "$OUT/$NAME.json" > "$OUT/$NAME.log" 2>&1
  echo "[pd_four_identity] $NAME rc=$? $(tail -1 "$OUT/$NAME.log" | cut -c1-200)"
done

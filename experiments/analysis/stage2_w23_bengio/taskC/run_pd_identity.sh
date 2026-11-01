#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、Task C-3（PD）。学習前の出力が塔単独と一致するか、界面を零でない値にすると変わるか。
#
#   bash run_pd_identity.sh <レーンの数> <レーン>      GPU はレーンの番号の偶奇で選ぶ
#
# 型ごとに全腕（W1 の台本の腕と信号の対応）を、界面を零初期化のまま評価し、塔単独の予測（Task B-2 の
# $S/b/plain_val_preds_seed42.json.gz）との出力の差の最大を記録する。W は学ぶ集合（requires_grad）だけを変え、
# 学習前の順伝播を変えないので、型と腕ごとの一回の評価が W2・W3 の両方の学習前に当たる（各 run の学習前の
# 予測と塔単独の差は pd_w23_finalize.py が run ごとにも記録する）。
# 陽性対照: P2L・P3 は pd_eval.py --perturb（界面の最後の層を N(0, 0.05²)）、EQ は四本目と同じ pd_four_eval.py の
# score0・random・unmask。val だけ。test は評価しない。
set -uo pipefail
LANES=$1; LANE=$2
CODE=/home/ubuntu/slocal2/m2
BODY=/home/ubuntu/slocal2/s2fix-bengio-body
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio
REF=$S/b/plain_val_preds_seed42.json.gz
OUT=$CODE/experiments/analysis/stage2_w23_bengio/taskC/pd_identity
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
for T in ${PD_TYPES:-P2L P3 EQ}; do
  case $T in P2L) I=clsbias_lin ;; P3) I=query ;; EQ) I=extra_q ;; P1) I=film ;; esac
  JOBS+=("$T empty $I 9 $F/P0_val.npz --zero-ctx")
  JOBS+=("$T pred_noCF $I 9 $F/P0_val.npz")
  JOBS+=("$T gt $I 9 $F/P-GT_val.npz")
  JOBS+=("$T pred_CF $I 9 $F/P0_val.npz")
  JOBS+=("$T gtpred_CF $I 18 $OLD/arms/PD/gtpred_noCF_val.npz")
  JOBS+=("$T shuffle $I 9 $SH/P0_val.npz")
  if [ "$T" = EQ ]; then
    JOBS+=("EQ positive_score0 extra_q 9 $F/P-GT_val.npz --perturb score0")
    JOBS+=("EQ random_weights extra_q 9 $F/P-GT_val.npz --perturb random")
    JOBS+=("EQ positive_unmask extra_q 9 $F/P-GT_val.npz --perturb unmask")
  else
    JOBS+=("$T positive $I 9 $F/P-GT_val.npz --perturb")
  fi
done
for k in "${!JOBS[@]}"; do
  [ $((k % LANES)) = "$LANE" ] || continue
  read -r T ARM I DIM SIG EXTRA <<< "${JOBS[$k]}"
  # PD_ARMS で腕を絞る（利用者の決定 2026-11-02: PD の W2・W3 は空・予測-noCF・正解・入れ替えの四腕と陽性対照だけ）
  if [ -n "${PD_ARMS:-}" ] && [[ " $PD_ARMS " != *" $ARM "* ]]; then continue; fi
  NAME=pd_${T}_${ARM}
  [ -f "$OUT/$NAME.json" ] && { echo "[pd_identity] 済み $NAME"; continue; }
  TOOL=scripts/stage2pilot/pd_eval.py
  [ "$T" = EQ ] && TOOL=scripts/stage2pilot/pd_four_eval.py
  # shellcheck disable=SC2086
  python "$TOOL" --cfg "configs/stage2pilot/pd_${I}_d${DIM}.py" \
    --det-ckpt "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --signal-val "$SIG" --ref-preds "$REF" $EXTRA --out "$OUT/$NAME.json" > "$OUT/$NAME.log" 2>&1
  echo "[pd_identity] $NAME rc=$? $(tail -1 "$OUT/$NAME.log" | cut -c1-200)"
done

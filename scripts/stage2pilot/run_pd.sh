#!/usr/bin/env bash
# PD（工程から検出）の腕を一本起こす（非公式 T-2026-10-18-stage2-pilot-folda、SPEC §4 Task F）。
#
#   scripts/stage2pilot/run_pd.sh <型> <腕> <seed> [smoke]
#     型: P1-W1 P1-W2 P2L P3 P2F
#     腕: empty pred_noCF gt pred_CF gtpred_CF（P2F は pred と gt。学習しない）
#     smoke を付けると 1 epoch だけ流す試走（D-9。腕ではない。run 名に _smoke）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。
#
# 受け取り手は D*-COCO 折り A seed 42。同じ型の腕は、受け取り手・界面の型と容量（最初の層を除く）・
# 学習範囲・増強・batch・数値精度（fp32）・止め方・seed を同じにする。止め方（PD-W1 と PD-W2 に一つずつ。
# 同じ値）: 学習率一定、val の overall mAP が 2 epoch 改善しなければ止める、上限 8 epoch、
# 最良の時点は学習した epoch から val の overall mAP で選ぶ。
set -euo pipefail
TYPE="$1"; ARM="$2"; SEED="$3"; MODE="${4:-}"
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-18-stage2-pilot-folda
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
F=$S/signals/final
CF=$S/signals/cf
PATIENCE=2
MAX_EPOCHS=8

case "$TYPE" in
  P1-W1) IFACE=film;        TRAINABLE=film ;;
  P1-W2) IFACE=film;        TRAINABLE=w2 ;;
  P2L)   IFACE=clsbias_lin; TRAINABLE=film ;;
  P3)    IFACE=query;       TRAINABLE=w2 ;;
  P2F)   IFACE=clsbias_fix; TRAINABLE=film ;;
  *) echo "型が不明: $TYPE" >&2; exit 2 ;;
esac

DIM=9; ZERO=()
case "$TYPE:$ARM" in
  P2F:pred)       TR=$F/P0_train.npz;   VA=$F/P0_val.npz ;;
  P2F:gt)         TR=$F/P-GT_train.npz; VA=$F/P-GT_val.npz ;;
  P2F:*)          echo "P2F の腕は pred か gt" >&2; exit 2 ;;
  *:empty)        TR=$F/P0_train.npz;   VA=$F/P0_val.npz; ZERO=(--zero-ctx) ;;
  *:pred_noCF)    TR=$F/P0_train.npz;   VA=$F/P0_val.npz ;;
  *:gt)           TR=$F/P-GT_train.npz; VA=$F/P-GT_val.npz ;;
  *:pred_CF)      TR=$CF/P0_train.npz;  VA=$F/P0_val.npz ;;
  *:gtpred_CF)    TR=$S/arms/PD/gtpred_CF_train.npz; VA=$S/arms/PD/gtpred_noCF_val.npz; DIM=18 ;;
  *) echo "腕が不明: $ARM" >&2; exit 2 ;;
esac
for f in "$TR" "$VA"; do [ -f "$f" ] || { echo "信号が無い: $f" >&2; exit 3; }; done

RUN="stage2pilot_pd_${TYPE}_${ARM}_seed${SEED}${MODE:+_$MODE}"
WORK=$BODY/experiments/phase1/$RUN
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
CFG=$BODY/configs/stage2pilot/pd_${IFACE}_d${DIM}.py
EXTRA=(--patience "$PATIENCE" --epochs "$MAX_EPOCHS" --best-excludes-init)
if [ "$TYPE" = P2F ]; then
  EXTRA=(--eval-only --fixed-table "$BODY/experiments/analysis/stage2_pilot_folda/signals/p2f_table.json")
elif [ "$MODE" = smoke ]; then
  EXTRA=(--patience "$PATIENCE" --epochs 1 --best-excludes-init)
fi

cd "$BODY"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda
export EGO_ROOT=$BODY/data/raw/ego
export EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/A
export T1B_MODEL_CFG=$CFG
export T1B_WORK_DIR=$WORK
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
set +e
python scripts/train_t1b.py --seed "$SEED" --trainable "$TRAINABLE" --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  --signal-train "$TR" --signal-val "$VA" "${ZERO[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd] $RUN rc=$RC"
exit $RC

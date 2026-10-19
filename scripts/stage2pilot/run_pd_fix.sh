#!/usr/bin/env bash
# PD（工程から検出）の固定の長さの run を一本起こす（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle、SPEC §4 Task E）。
#
#   scripts/stage2pilot/run_pd_fix.sh <型> <腕> [smoke]
#     型: P1-W1 P1-W2 P2L P3 P2F
#     腕: empty pred_noCF gt pred_CF gtpred_CF shuffle（P2F は shuffle だけ。学習せず評価だけ）
#     smoke を付けると 1 epoch・6 step・val 20 枚の試走（腕ではない。run 名に _smoke）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。
#
# 4 epoch 学習し、途中で止めず、4 epoch 目の状態を結果にする（train_t1b.py --fixed-epochs。学習率は一定）。
# 受け取り手・界面の型と容量・学習範囲・学習率・増強・batch・数値精度（学習の順伝播は bf16 の自動混合精度、評価は単精度）・
# seed は前回の run_pd.sh と同じ。変えるのは止め方と、入れ替えの腕の信号だけ（SPEC Task E-1）。
# 前回の信号は OLD から読むだけ。入れ替えた信号・重み・記録の写しは本契約の置き場（FIX）へ。
set -euo pipefail
TYPE="$1"; ARM="$2"; MODE="${3:-}"
SEED=42
EPOCHS=4
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
FIX=/home/ubuntu/slocal2/stage2pilot_store/$TASK
F=$OLD/signals/final
CF=$OLD/signals/cf
SH=$FIX/signals/shuffle

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
  P2F:shuffle)    TR=$SH/P0_train.npz;  VA=$SH/P0_val.npz ;;
  P2F:*)          echo "P2F の腕は shuffle だけ（予測と正解は前回の評価を使う）" >&2; exit 2 ;;
  *:empty)        TR=$F/P0_train.npz;   VA=$F/P0_val.npz; ZERO=(--zero-ctx) ;;
  *:pred_noCF)    TR=$F/P0_train.npz;   VA=$F/P0_val.npz ;;
  *:gt)           TR=$F/P-GT_train.npz; VA=$F/P-GT_val.npz ;;
  *:pred_CF)      TR=$CF/P0_train.npz;  VA=$F/P0_val.npz ;;
  *:gtpred_CF)    TR=$OLD/arms/PD/gtpred_CF_train.npz; VA=$OLD/arms/PD/gtpred_noCF_val.npz; DIM=18 ;;
  *:shuffle)      TR=$SH/P0_train.npz;  VA=$SH/P0_val.npz ;;
  *) echo "腕が不明: $ARM" >&2; exit 2 ;;
esac
for f in "$TR" "$VA"; do [ -f "$f" ] || { echo "信号が無い: $f" >&2; exit 3; }; done

RUN="stage2fix_pd_${TYPE}_${ARM}_ep${EPOCHS}_seed${SEED}${MODE:+_$MODE}"
WORK=$BODY/experiments/phase1/$RUN
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
CFG=$BODY/configs/stage2pilot/pd_${IFACE}_d${DIM}.py
EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16)
if [ "$TYPE" = P2F ]; then
  EXTRA=(--eval-only --fixed-table "$BODY/experiments/analysis/stage2_pilot_folda/signals/p2f_table.json")
elif [ "$MODE" = smoke ]; then
  EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke)
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
# conventions#env_p0: 拡張の読み込みを記録に残す（読めていなければ ms_deform_attn_ext=False）
(cd third_party/Relation-DETR && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1
python scripts/train_t1b.py --seed "$SEED" --trainable "$TRAINABLE" --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  --signal-train "$TR" --signal-val "$VA" "${ZERO[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$FIX/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ]; then
  PYTHONPATH=src:scripts "$BODY/.venv/bin/python" scripts/stage2pilot/pd_fix_finalize.py "$WORK" "$TYPE" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd_fix] $RUN rc=$RC"
exit $RC

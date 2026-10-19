#!/usr/bin/env bash
# PD（工程から検出）の新しい型の固定の長さの run を一本起こす（非公式 T-2026-10-19-stage2-pilot-four-new-types、SPEC §4 Task E）。
#
#   scripts/stage2pilot/run_pd_four.sh <型> <腕> [smoke]
#     型: DX（decoder-xattn、SPEC §3.1）EQ（extra-queries、SPEC §3.2）
#     腕: empty pred_noCF gt pred_CF gtpred_CF shuffle
#     smoke を付けると 1 epoch・6 step・val 20 枚の試走（腕ではない。run 名に _smoke）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。
#
# 直しの契約の run_pd_fix.sh と同じ処方: 4 epoch 学習し途中で止めず 4 epoch 目の状態を結果にする（--fixed-epochs、学習率一定）、
# 学習の順伝播は bf16 の自動混合精度（評価は単精度）、W1（--trainable film = 名前に phase を含む界面のパラメータだけ）、
# 受け取り手 D*-COCO 折り A seed 42、増強・batch・seed も同じ。腕と信号の対応も同じ（前回の信号を読むだけ、入れ替えは直しの契約の信号）。
# extra-queries は train の見落としの集合（$FOUR/xq/missed_train.json）を渡す。
#
#   S2FIX_BODY  データ・仮想環境・third_party/Relation-DETR・検出塔の重みを読む場所（既定 /home/ubuntu/slocal2/m2。bengio では重ねの BODY）
#   S2FIX_CODE  台本・構成・run の置き場（experiments/phase1/<run>）の repo。既定は S2FIX_BODY と同じ
set -euo pipefail
TYPE="$1"; ARM="$2"; MODE="${3:-}"
SEED=42
EPOCHS=4
BODY=${S2FIX_BODY:-/home/ubuntu/slocal2/m2}
CODE=${S2FIX_CODE:-$BODY}
TASK=T-2026-10-19-stage2-pilot-four-new-types
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
FIX=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
FOUR=/home/ubuntu/slocal2/stage2pilot_store/$TASK
F=$OLD/signals/final
CF=$OLD/signals/cf
SH=$FIX/signals/shuffle

MISSED=()
case "$TYPE" in
  DX) IFACE=dec_xattn ;;
  EQ) IFACE=extra_q; MISSED=(--missed-set "$FOUR/xq/missed_train.json") ;;
  *) echo "型が不明: $TYPE" >&2; exit 2 ;;
esac

DIM=9; ZERO=()
case "$ARM" in
  empty)        TR=$F/P0_train.npz;   VA=$F/P0_val.npz; ZERO=(--zero-ctx) ;;
  pred_noCF)    TR=$F/P0_train.npz;   VA=$F/P0_val.npz ;;
  gt)           TR=$F/P-GT_train.npz; VA=$F/P-GT_val.npz ;;
  pred_CF)      TR=$CF/P0_train.npz;  VA=$F/P0_val.npz ;;
  gtpred_CF)    TR=$OLD/arms/PD/gtpred_CF_train.npz; VA=$OLD/arms/PD/gtpred_noCF_val.npz; DIM=18 ;;
  shuffle)      TR=$SH/P0_train.npz;  VA=$SH/P0_val.npz ;;
  *) echo "腕が不明: $ARM" >&2; exit 2 ;;
esac
for f in "$TR" "$VA" "${MISSED[@]:1}"; do [ -f "$f" ] || { echo "入力が無い: $f" >&2; exit 3; }; done

RUN="stage2four_pd_${TYPE}_${ARM}_ep${EPOCHS}_seed${SEED}${MODE:+_$MODE}"
WORK=$CODE/experiments/phase1/$RUN
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
CFG=$CODE/configs/stage2pilot/pd_${IFACE}_d${DIM}.py
EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16)
if [ "$MODE" = smoke ]; then
  EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke)
fi

cd "$CODE"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda
export EGO_BODY=$BODY      # train_t1b.py が third_party/Relation-DETR を BODY から引く
export EGO_ROOT=$BODY/data/raw/ego
export EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/A
export T1B_MODEL_CFG=$CFG
export T1B_WORK_DIR=$WORK
export PYTHONUTF8=1
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
set +e
# conventions#env_p0: 拡張の読み込みを記録に残す（読めていなければ ms_deform_attn_ext=False）
(cd "$BODY/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1
python scripts/train_t1b.py --seed "$SEED" --trainable film --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  --signal-train "$TR" --signal-val "$VA" "${ZERO[@]}" "${MISSED[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$FOUR/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ]; then
  PYTHONPATH=src:scripts "$BODY/.venv/bin/python" scripts/stage2pilot/pd_four_finalize.py "$WORK" "$TYPE" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd_four] $RUN rc=$RC"
exit $RC

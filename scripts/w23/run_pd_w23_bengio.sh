#!/usr/bin/env bash
# PD（工程から検出）の W2・W3 の run を一本起こす（非公式 T-2026-11-01-stage2-w23-bengio、SPEC §3.1・§4・Task C-1・D）。
#
#   scripts/w23/run_pd_w23_bengio.sh <型> <腕> <W> [smoke]
#     型: P2L P3 P1（decoder-xattn と案 B は並行する andrew の契約が回す）。EQ（extra-queries）は台本に残すが回さない
#     腕: empty pred_noCF gt shuffle（pred_CF gtpred_CF も台本に残すが回さない）
#     W:  W2（界面 ＋ --trainable w2）、W3（界面 ＋ --trainable all）
#   回す組は利用者の決定（2026-11-02、spec.yaml の meta.amendments）に限る: P2L の W2・W3、P3 の W3、P1 の W3 の各 4 腕。
#   P3 の W2 は W1 と同じ集合（P3 の W1 が既に --trainable w2）、P1 の W1・W2 は andrew の値を参考に置く
#     smoke を付けると 1 epoch・6 step・val 20 枚の試走（腕ではない。run 名に _smoke）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。
#
# 腕と信号の対応は W1 の台本（P1・P2L・P3 は scripts/stage2pilot/run_pd_fix.sh、EQ は scripts/stage2pilot/run_pd_four.sh）を写した。
# 処方も W1 と同じ（4 epoch を止めずに学び 4 epoch 目の状態を結果にする、学習率一定、batch と増強は train_t1b.py の既定、
# 学習の順伝播は bf16 の自動混合精度・評価は単精度、seed 42）。変えるのは学習範囲だけ。受け取り手の学習率 1e-4 と
# 界面の学習率 5e-4 は train_t1b.py の既定の値で、記録のため明示して渡す。
# データ・仮想環境・third_party/Relation-DETR は重ねの BODY（andrew と同じ中身。audit.md の A-6）から読む。
# run の置き場は本 repo の experiments/phase1/w23b_pd_*。予測（1 本 25MB 前後）は確定の後に版管理と同期の外（S）へ移し、
# 経路と sha256 を run の predictions_moved.json に残す。
set -euo pipefail
TYPE="$1"; ARM="$2"; W="$3"; MODE="${4:-}"
SEED=42
EPOCHS=4
BODY=/home/ubuntu/slocal2/s2fix-bengio-body
CODE=/home/ubuntu/slocal2/m2
TASK=T-2026-11-01-stage2-w23-bengio
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
FIX=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
FOUR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types
F=$OLD/signals/final
CF=$OLD/signals/cf
SH=$FIX/signals/shuffle

MISSED=()
case "$TYPE" in
  P2L) IFACE=clsbias_lin ;;
  P3)  IFACE=query ;;
  P1)  IFACE=film ;;
  EQ)  IFACE=extra_q; MISSED=(--missed-set "$FOUR/xq/missed_train.json") ;;
  *) echo "型が不明: $TYPE" >&2; exit 2 ;;
esac
case "$W" in
  W2) TRAINABLE=w2 ;;
  W3) TRAINABLE=all ;;
  *) echo "W が不明: $W" >&2; exit 2 ;;
esac
case "$TYPE:$W" in
  P2L:W2|P2L:W3|P3:W3|P1:W3) ;;
  *) echo "回さない組: $TYPE $W（利用者の決定 2026-11-02、spec.yaml の meta.amendments）" >&2; exit 2 ;;
esac
case "$ARM" in
  empty|pred_noCF|gt|shuffle) ;;
  *) [ -n "$MODE" ] || { echo "回さない腕: $ARM（PD の W2・W3 は四腕だけ。利用者の決定 2026-11-02）" >&2; exit 2; } ;;
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

RUN="w23b_pd_${TYPE}-${W}_${ARM}_ep${EPOCHS}_seed${SEED}${MODE:+_$MODE}"
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
# 資格情報は読み込まない（契約 §7.10。train_t1b.py は W&B を使わない）
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
python scripts/train_t1b.py --seed "$SEED" --trainable "$TRAINABLE" --lr 1e-4 --film-lr 5e-4 --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  --signal-train "$TR" --signal-val "$VA" "${ZERO[@]}" "${MISSED[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ]; then
  PYTHONPATH=src:scripts "$CODE/.venv/bin/python" experiments/analysis/stage2_w23_bengio/tools/pd_w23_finalize.py \
    "$WORK" "$TYPE" "$ARM" "$W" "$S/pd_preds/$RUN" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd_w23] $RUN rc=$RC"
exit $RC

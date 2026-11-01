#!/usr/bin/env bash
# 工程から検出（P1・decoder-xattn）と案 B を W2・W3 で回す（非公式 T-2026-11-01-stage2-w23-andrew、SPEC §3・§4・Task C-1）。
#
#   scripts/w23/run_pd_w23_andrew.sh <型> <W> <腕> [モード]
#     型:  P1（FiLM）、DX（decoder-xattn）、B（案 B、把持の地図を C5 に足す型）
#     W:   W2（--trainable w2 = 界面 ＋ decoder の最終層とその層のクラスと box の頭）、
#          W3（--trainable all = 界面 ＋ 設定の凍結以外の検出器の全体）、W1（--trainable film。setcheck と dryrun だけ。学習しない）
#     腕:  empty pred_noCF gt pred_CF gtpred_CF shuffle
#     モード: なし（学習。4 epoch の固定の長さ）、smoke（1 epoch・6 step・val 20 枚の試走。置き場は版管理の外）、
#             identity（学習前の出力を塔単独の予測と比べる）、perturb（陽性対照。界面の重みを N(0, 0.05²)）、
#             setcheck（学ぶ集合だけを調べる。評価しない）、dryrun（解決した引数を表示するだけ）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。
#
# 腕と信号の対応は W1 の台本の写し（P1 は scripts/stage2pilot/run_pd_fix.sh、DX は run_pd_four.sh、案 B は
# scripts/grasppilot/run_pd_grasp2.sh）。受け取り手・界面の型と容量・学習率（受け取り手 1e-4・界面 5e-4 の既定）・増強・batch 2・
# 数値精度（学習は bf16 の自動混合精度、評価は単精度）・長さ（--fixed-epochs、4 epoch）・seed も W1 と同じ。
# W1 と違うのは --trainable と、epoch ごとの val の予測を残すこと（--save-predictions-all。学習には効かない）と、置き場だけ。
# 前の契約の信号は読むだけ。書くのは本契約の置き場（run は experiments/phase1/w23a_*、重みと試走は $S）だけ。
set -euo pipefail
TYPE="$1"; W="$2"; ARM="$3"; MODE="${4:-}"
SEED=42
EPOCHS=4
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-01-stage2-w23-andrew
STORE=/home/ubuntu/slocal2/stage2pilot_store
S=$STORE/$TASK
OLD=$STORE/T-2026-10-18-stage2-pilot-folda
FIX=$STORE/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
GV=$STORE/T-2026-11-01-grasp-pilot-g/signals/views
F=$OLD/signals/final
CF=$OLD/signals/cf
SH=$FIX/signals/shuffle
DETCKPT=$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth
A=$M/experiments/analysis/stage2_w23_andrew

case "$W" in
  W1) TRAINABLE=film ;;
  W2) TRAINABLE=w2 ;;
  W3) TRAINABLE=all ;;
  *) echo "W が不明: $W" >&2; exit 2 ;;
esac
case "$MODE" in
  ""|smoke|identity|perturb|setcheck|dryrun) ;;
  *) echo "モードが不明: $MODE" >&2; exit 2 ;;
esac
if [ "$W" = W1 ] && [ "$MODE" != setcheck ] && [ "$MODE" != dryrun ]; then
  echo "W1 は setcheck と dryrun だけ（本契約は W1 を学習しない。SPEC Task C-4）" >&2; exit 2
fi

case "$TYPE" in
  P1|DX)
    if [ "$TYPE" = P1 ]; then IFACE=film; else IFACE=dec_xattn; fi
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
    CFG=$M/configs/stage2pilot/pd_${IFACE}_d${DIM}.py
    TRAIN_IN=(--signal-train "$TR" --signal-val "$VA" "${ZERO[@]}")
    EVAL_IN=(--signal-val "$VA" "${ZERO[@]}")
    INPUTS=("$TR" "$VA")
    ;;
  B)
    CFG=$M/configs/stage2pilot/pd_graspmap_d5.py
    case "$ARM" in
      empty) GMAP=zero ;;
      gt)    GMAP=gt ;;
      pred_noCF|pred_CF|shuffle) GMAP=pred; CFG=$M/configs/stage2pilot/pd_graspmap_pred5.py ;;
      gtpred_CF) GMAP=gt_pred; CFG=$M/configs/stage2pilot/pd_graspmap_d10.py ;;
      *) echo "腕が不明: $ARM" >&2; exit 2 ;;
    esac
    TRAIN_IN=(--grasp-map "$GMAP"); EVAL_IN=(--grasp-map "$GMAP"); INPUTS=()
    if [ "$GMAP" = pred ] || [ "$GMAP" = gt_pred ]; then
      VARM=$ARM; [ "$ARM" = gtpred_CF ] && VARM=pred_CF
      PTR=$GV/B_${VARM}_train.json; PVA=$GV/B_${VARM}_val.json
      TRAIN_IN+=(--grasp-pred-train "$PTR" --grasp-pred-val "$PVA")
      EVAL_IN+=(--grasp-pred-val "$PVA")
      INPUTS=("$PTR" "$PVA")
    fi
    ;;
  *) echo "型が不明: $TYPE" >&2; exit 2 ;;
esac
for f in "$CFG" "$DETCKPT" "${INPUTS[@]}"; do [ -f "$f" ] || { echo "入力が無い: $f" >&2; exit 3; }; done

RUN="w23a_pd_${TYPE}_${W}_${ARM}_ep${EPOCHS}_seed${SEED}"

if [ "$MODE" = dryrun ]; then
  printf 'run=%s\ntrainable=%s\ncfg=%s\ntrain_in=%s\neval_in=%s\n' "$RUN" "$TRAINABLE" "$CFG" "${TRAIN_IN[*]}" "${EVAL_IN[*]}"
  exit 0
fi

cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1

if [ "$MODE" = identity ] || [ "$MODE" = perturb ] || [ "$MODE" = setcheck ]; then
  OUTD=$A/identity; mkdir -p "$OUTD"
  case "$MODE" in
    identity) OUT=$OUTD/${TYPE}_${W}_${ARM}.json; X=(--ref-preds "$S/identity/plain_val_preds.json.gz") ;;
    perturb)  OUT=$OUTD/${TYPE}_${W}_${ARM}_perturb.json; X=(--perturb --ref-preds "$S/identity/plain_val_preds.json.gz") ;;
    setcheck) OUT=$OUTD/setcheck_${TYPE}_${W}_${ARM}.json; X=(--no-eval) ;;
  esac
  PYTHONPATH=src:scripts python scripts/w23/w23a_identity.py --type "$TYPE" --w "$W" --trainable "$TRAINABLE" --arm "$ARM" \
    --cfg "$CFG" --det-ckpt "$DETCKPT" "${EVAL_IN[@]}" "${X[@]}" --out "$OUT" > "${OUT%.json}.log" 2>&1
  RC=$?
  echo "[run_pd_w23_andrew] $MODE $TYPE $W $ARM rc=$RC $(tail -1 "${OUT%.json}.log")"
  exit $RC
fi

if [ "$MODE" = smoke ]; then
  RUN=${RUN}_smoke; WORK=$S/smoke/$RUN
  EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke)
else
  WORK=$M/experiments/phase1/$RUN
  EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16 --save-predictions-all)
fi
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
export T1B_MODEL_CFG=$CFG T1B_WORK_DIR=$WORK
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
sha256sum scripts/train_t1b.py scripts/stage2pilot/pd_model.py scripts/stage2pilot/pd_four.py scripts/grasppilot/pd_grasp.py \
  scripts/grasppilot/pd_grasp_model.py scripts/grasppilot/grasp_signals.py scripts/w23/run_pd_w23_andrew.sh \
  scripts/w23/w23a_finalize.py "$CFG" > "$WORK/code_sha256.txt"
git rev-parse HEAD > "$WORK/code_commit.txt"
for f in "${INPUTS[@]}"; do sha256sum "$f"; done > "$WORK/input_sha256.txt"
set +e
# conventions#env_p0: 拡張の読み込みを記録に残す（読めていなければ ms_deform_attn_ext=False）
(cd "$M/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1
python scripts/train_t1b.py --seed "$SEED" --trainable "$TRAINABLE" --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$DETCKPT" "${TRAIN_IN[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ] && [ "$MODE" != smoke ]; then
  PYTHONPATH=src:scripts "$M/.venv/bin/python" scripts/w23/w23a_finalize.py "$WORK" "$TYPE" "$W" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd_w23_andrew] $RUN rc=$RC"
exit $RC

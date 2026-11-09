#!/usr/bin/env bash
# 工程から検出の 4 型を W3 で、受け取り手の学習率 1e-5 で回す（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew、SPEC §3・§4・Task B・C）。
#
#   bash experiments/analysis/stage2_pd_w3_lowlr_andrew/tools/run_w3lra.sh <型> <腕> [モード]
#     型:  P1（film）、P2L（clsbias_lin）、P3（query）、DX（dec_xattn）。どれも d9
#     腕:  empty pred_noCF gt shuffle（予測-CF・正解予測-CF・案 B は回さない。SPEC §7-13）
#     モード: なし（学習。4 epoch の固定の長さ）、
#             smoke（1 epoch・6 step・val 20 枚の試走。置き場は $S/smoke。受け取り手 1e-5）、
#             smoke_lr1e-4（B-3 の陽性対照だけ。smoke と同じで受け取り手を 1e-4 にする）、
#             identity（学習前の出力を塔単独の予測と比べる）、perturb（陽性対照。界面の最後の層を N(0, 0.05²)）、
#             setcheck（学ぶ集合だけを調べる。評価しない）、dryrun（解決した引数を表示するだけ）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。
#
# 前回の andrew の台本 scripts/w23/run_pd_w23_andrew.sh（P1・DX）の写し。腕と信号の対応は同じで、P2L・P3 は bengio の台本
# scripts/w23/run_pd_w23_bengio.sh の型と設定の対応（P2L → clsbias_lin、P3 → query）を andrew の保存先と main で読む。
# 前回と違うのは次だけ:
#   - 受け取り手の学習率を 1e-5 にする（--lr 1e-5。界面は --film-lr 5e-4 のまま。どちらも明示して渡す。train_t1b.py の既定は変えない）
#   - 包み w3lra_lrwrap.py を通して optimizer の各群の学習率を記録する（学習の計算は変えない）
#   - 置き場（run は experiments/phase1/w3lra_*、重み・試走・W&B は $S）と、契約の識別子
# 処方（W3 = --trainable all、4 epoch を止めずに学び 4 epoch 目の状態を結果にする、batch と増強は train_t1b.py の既定、
# 学習は bf16 の自動混合精度・評価は単精度、weight decay 1e-4、勾配の刈り込み 0.1、seed 42、epoch ごとの val の予測を残す）は前回と同じ。
set -euo pipefail
TYPE="$1"; ARM="$2"; MODE="${3:-}"
SEED=42
EPOCHS=4
W=W3
TRAINABLE=all
LR=1e-5
FILM_LR=5e-4
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-stage2-pd-w3-lowlr-andrew
STORE=/home/ubuntu/slocal2/stage2pilot_store
S=$STORE/$TASK
OLD=$STORE/T-2026-10-18-stage2-pilot-folda
FIX=$STORE/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
F=$OLD/signals/final
SH=$FIX/signals/shuffle
DETCKPT=$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth
A=$M/experiments/analysis/stage2_pd_w3_lowlr_andrew
T=$A/tools

case "$MODE" in
  ""|smoke|identity|perturb|setcheck|dryrun) ;;
  smoke_lr1e-4) LR=1e-4 ;;     # B-3 の陽性対照だけ（数歩の写し。SPEC §7-13 の例外）
  *) echo "モードが不明: $MODE" >&2; exit 2 ;;
esac
case "$TYPE" in
  P1) IFACE=film ;;
  P2L) IFACE=clsbias_lin ;;
  P3) IFACE=query ;;
  DX) IFACE=dec_xattn ;;
  *) echo "型が不明（回さない型）: $TYPE" >&2; exit 2 ;;
esac
ZERO=()
case "$ARM" in
  empty)     TR=$F/P0_train.npz;   VA=$F/P0_val.npz; ZERO=(--zero-ctx) ;;
  pred_noCF) TR=$F/P0_train.npz;   VA=$F/P0_val.npz ;;
  gt)        TR=$F/P-GT_train.npz; VA=$F/P-GT_val.npz ;;
  shuffle)   TR=$SH/P0_train.npz;  VA=$SH/P0_val.npz ;;
  *) echo "回さない腕: $ARM（本契約は空・予測-noCF・正解・入れ替えの四腕だけ。SPEC §3.2）" >&2; exit 2 ;;
esac
CFG=$M/configs/stage2pilot/pd_${IFACE}_d9.py
for f in "$CFG" "$DETCKPT" "$TR" "$VA"; do [ -f "$f" ] || { echo "入力が無い: $f" >&2; exit 3; }; done

RUN="w3lra_pd_${TYPE}_${W}_${ARM}_ep${EPOCHS}_seed${SEED}"

if [ "$MODE" = dryrun ]; then
  printf 'run=%s\ntrainable=%s\nlr=%s\nfilm_lr=%s\ncfg=%s\nsignal_train=%s\nsignal_val=%s\nzero=%s\n' \
    "$RUN" "$TRAINABLE" "$LR" "$FILM_LR" "$CFG" "$TR" "$VA" "${ZERO[*]}"
  exit 0
fi

cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
# SPEC §7-11: W&B は手元だけ（offline）。外へ送らない（資格情報も読み込まない）
export WANDB_MODE=offline WANDB_DIR=$S/wandb

if [ "$MODE" = identity ] || [ "$MODE" = perturb ] || [ "$MODE" = setcheck ]; then
  OUTD=$A/identity; mkdir -p "$OUTD"
  case "$MODE" in
    identity) OUT=$OUTD/${TYPE}_${W}_${ARM}.json; X=(--ref-preds "$S/identity/plain_val_preds.json.gz") ;;
    perturb)  OUT=$OUTD/${TYPE}_${W}_${ARM}_perturb.json; X=(--perturb --ref-preds "$S/identity/plain_val_preds.json.gz") ;;
    setcheck) OUT=$OUTD/setcheck_${TYPE}_${W}_${ARM}.json; X=(--no-eval) ;;
  esac
  PYTHONPATH=src:scripts python "$T/w3lra_identity.py" --type "$TYPE" --w "$W" --trainable "$TRAINABLE" --arm "$ARM" \
    --cfg "$CFG" --det-ckpt "$DETCKPT" --signal-val "$VA" "${ZERO[@]}" "${X[@]}" --out "$OUT" > "${OUT%.json}.log" 2>&1
  RC=$?
  echo "[run_w3lra] $MODE $TYPE $W $ARM rc=$RC $(tail -1 "${OUT%.json}.log")"
  exit $RC
fi

if [ "$MODE" = smoke ] || [ "$MODE" = smoke_lr1e-4 ]; then
  RUN=${RUN}_${MODE}; WORK=$S/smoke/$RUN
  EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke --save-predictions-all)
else
  WORK=$M/experiments/phase1/$RUN
  EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16 --save-predictions-all)
fi
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
export T1B_MODEL_CFG=$CFG T1B_WORK_DIR=$WORK W3LRA_LR_LOG=$WORK/lr_groups.json
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
sha256sum scripts/train_t1b.py scripts/stage2pilot/pd_model.py "$T/run_w3lra.sh" "$T/w3lra_lrwrap.py" "$T/w3lra_finalize.py" \
  "$CFG" > "$WORK/code_sha256.txt"
git rev-parse HEAD > "$WORK/code_commit.txt"
for f in "$TR" "$VA" "$DETCKPT"; do sha256sum "$f"; done > "$WORK/input_sha256.txt"
set +e
# conventions#env_p0: 拡張の読み込みを記録に残す（読めていなければ ms_deform_attn_ext=False）
(cd "$M/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1
python "$T/w3lra_lrwrap.py" --seed "$SEED" --trainable "$TRAINABLE" --lr "$LR" --film-lr "$FILM_LR" --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$DETCKPT" --signal-train "$TR" --signal-val "$VA" "${ZERO[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ] && [ "$MODE" = "" ]; then
  PYTHONPATH=src:scripts "$M/.venv/bin/python" "$T/w3lra_finalize.py" "$WORK" "$TYPE" "$W" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_w3lra] $RUN rc=$RC"
exit $RC

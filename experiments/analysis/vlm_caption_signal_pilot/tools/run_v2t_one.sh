#!/usr/bin/env bash
# V→T（P1・P2L × W1・W2・W3 × 7 腕）を 1 本実行する（T-2026-11-26-vlm-caption-signal-pilot）
#   run_v2t_one.sh <TYPE P1|P2L> <W W1|W2|W3> <ARM> [EPOCHS=16]
set -euo pipefail
TYPE="$1"; W="$2"; ARM="$3"; EPOCHS="${4:-16}"
SEED=42
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-26-vlm-caption-signal-pilot
S=/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot
SIG=$S/signals
DETCKPT=$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth

case "$TYPE" in
  P1)  CFG=$M/configs/stage2pilot/pd_film_d3128.py ;;
  P2L) CFG=$M/configs/stage2pilot/pd_clsbias_lin_d3128.py ;;
  *) echo "TYPE 不明: $TYPE" >&2; exit 2 ;;
esac

case "$W" in
  W1) TRAINABLE=film; LR=1e-4 ;;
  W2) TRAINABLE=w2;   LR=1e-4 ;;
  W3) TRAINABLE=all;  LR=1e-5 ;;
  *) echo "W 不明: $W" >&2; exit 2 ;;
esac

ZERO=()
case "$ARM" in
  empty)         TR=$SIG/vec_ko_train.npz;          VA=$SIG/vec_ko_val.npz; ZERO=(--zero-ctx) ;;
  vlm_ko)        TR=$SIG/vec_ko_train.npz;          VA=$SIG/vec_ko_val.npz ;;
  vlm_otsu)      TR=$SIG/vec_otsu_train.npz;        VA=$SIG/vec_otsu_val.npz ;;
  vlm_hei)       TR=$SIG/vec_hei_train.npz;         VA=$SIG/vec_hei_val.npz ;;
  vlm_ko_shuf)   TR=$SIG/vec_ko_shuffle_train.npz;  VA=$SIG/vec_ko_shuffle_val.npz ;;
  vlm_otsu_shuf) TR=$SIG/vec_otsu_shuffle_train.npz; VA=$SIG/vec_otsu_shuffle_val.npz ;;
  vlm_hei_shuf)  TR=$SIG/vec_hei_shuffle_train.npz; VA=$SIG/vec_hei_shuffle_val.npz ;;
  *) echo "ARM 不明: $ARM" >&2; exit 2 ;;
esac

for f in "$CFG" "$DETCKPT" "$TR" "$VA"; do
  [ -f "$f" ] || { echo "入力が無い: $f" >&2; exit 3; }
done

RUN="vlm_caption_signal_pilot_pd_${TYPE}_${W}_${ARM}_ep${EPOCHS}_seed${SEED}"
WORK=$M/experiments/phase1/$RUN
mkdir -p "$WORK"
exec 9>"$WORK/.run.lock"
flock 9
if [ -f "$WORK/v2t_metrics.json" ] && [ "$(cat "$WORK/exit_code.txt" 2>/dev/null || echo 1)" = "0" ]; then
  echo "[run_v2t_one] SKIP already completed: $RUN"
  exit 0
fi

# 同一 GPU で v2t_wrap.py が 2 本以上稼働中なら空きを待つ（先発起動との OOM 競合防止）
if [ -n "${CUDA_VISIBLE_DEVICES:-}" ]; then
  while true; do
    N_ON_GPU=$(nvidia-smi -i "$CUDA_VISIBLE_DEVICES" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | sed '/^$/d' | wc -l)
    [ "${N_ON_GPU:-0}" -lt 2 ] && break
    sleep 30
  done
fi

cd "$M"
export PATH="/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/detr-venv/bin:$PATH"
export CUDA_HOME=/usr/local/cuda
export TORCH_EXTENSIONS_DIR=/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime/torch-extensions
export EGO_BODY=$S/inputs
export EGO_ROOT=$M/data/raw/ego
export EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export T1B_MODEL_CFG=$CFG
export T1B_WORK_DIR=$WORK
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
export WANDB_MODE=offline
export WANDB_DIR=$S/wandb
export V2T_RECORD_LOG=$WORK/v2t_wrap.json

mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
sha256sum scripts/train_t1b.py scripts/stage2pilot/pd_model.py \
  experiments/analysis/vlm_caption_signal_pilot/tools/v2t_wrap.py \
  experiments/analysis/vlm_caption_signal_pilot/tools/v2t_finalize.py "$CFG" > "$WORK/code_sha256.txt"
git rev-parse HEAD > "$WORK/code_commit.txt"
sha256sum "$TR" "$VA" > "$WORK/input_sha256.txt"

set +e
(cd "$EGO_BODY/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1

python experiments/analysis/vlm_caption_signal_pilot/tools/v2t_wrap.py \
  --seed "$SEED" --trainable "$TRAINABLE" --lr "$LR" --film-lr 5e-4 \
  --task-id "$TASK" --run-name "$RUN" --det-ckpt "$DETCKPT" \
  --signal-train "$TR" --signal-val "$VA" "${ZERO[@]}" \
  --epochs "$EPOCHS" --fixed-epochs --amp bf16 --save-predictions-all \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 1000 \
  > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ]; then
  PYTHONPATH=src:scripts "$M/.venv/bin/python" experiments/analysis/vlm_caption_signal_pilot/tools/v2t_finalize.py \
    "$WORK" "$TYPE" "$W" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_v2t_one] $RUN rc=$RC"
exit $RC

#!/usr/bin/env bash
# 案 B（把持の地図を C5 に足す型）の固定の長さの run を一本起こす（非公式 T-2026-10-31-grasp-pilot-probe、SPEC §4・Task D-6）。
#
#   scripts/grasppilot/run_pd_grasp.sh <腕> [smoke]
#     腕: empty（地図は全 0）、gt（正解の地図）
#     smoke を付けると 1 epoch・6 step・val 20 枚の試走（腕ではない。run の置き場は版管理の外の $S/smoke）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。seed は 42 だけ。
#
# 受け取り手・学習範囲（W1 = --trainable film、名前に phase を含むパラメータだけ）・学習率（lr 1e-4・film_lr 5e-4 の既定）・
# 増強（presets.detr）・batch 2・数値精度（学習は bf16 の自動混合精度、評価は単精度）・seed は前回の run_pd_fix.sh と同じ。
# 4 epoch 学習し、途中で止めず、4 epoch 目の状態を結果にする（--fixed-epochs）。
set -euo pipefail
ARM="$1"; MODE="${2:-}"
SEED=42
EPOCHS=4
M=/home/ubuntu/slocal2/m2
TASK=T-2026-10-31-grasp-pilot-probe
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
case "$ARM" in
  empty) GMAP=zero ;;
  gt)    GMAP=gt ;;
  *) echo "腕が不明: $ARM" >&2; exit 2 ;;
esac
RUN="grasppilot_pd_B_${ARM}_ep${EPOCHS}_seed${SEED}${MODE:+_$MODE}"
if [ "$MODE" = smoke ]; then WORK=$S/smoke/$RUN; else WORK=$M/experiments/phase1/$RUN; fi
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
CFG=$M/configs/stage2pilot/pd_graspmap_d5.py
EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16)
[ "$MODE" = smoke ] && EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke)
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export T1B_MODEL_CFG=$CFG T1B_WORK_DIR=$WORK PYTHONDONTWRITEBYTECODE=1
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
sha256sum scripts/grasppilot/pd_grasp.py scripts/grasppilot/pd_grasp_model.py scripts/grasppilot/grasp_signals.py \
  scripts/train_t1b.py "$CFG" > "$WORK/code_sha256.txt"
git rev-parse HEAD > "$WORK/code_commit.txt"
set +e
(cd "$M/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1
python scripts/train_t1b.py --seed "$SEED" --trainable film --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  --grasp-map "$GMAP" "${EXTRA[@]}" \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ]; then
  PYTHONPATH=src:scripts "$M/.venv/bin/python" scripts/grasppilot/pd_grasp_finalize.py "$WORK" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd_grasp] $RUN rc=$RC"
exit $RC

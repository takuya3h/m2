#!/usr/bin/env bash
# 案 B の固定の長さの run を一本起こす（非公式 T-2026-11-01-grasp-pilot-g、SPEC §3.4・Task E）。一本目の run_pd_grasp.sh の写しで、
# 本契約の置き場と腕にした（受け取り手・学習範囲・学習率・増強・batch・数値精度・長さ・seed は一本目と同じ）。
#
#   scripts/grasppilot/run_pd_grasp2.sh <腕> [smoke]
#     empty（全 0）、gt（正解）、pred_noCF（確定の G の地図）、pred_CF（train は交差適合、val は確定の G）、
#     gtpred_CF（正解と予測-CF の連結 10 チャネル）、shuffle（並べ替えた予測-noCF）
#   見取りの json は $S/signals/views/B_<腕>_{train,val}.json（g_signals.py assemble が書く）。GPU は CUDA_VISIBLE_DEVICES
set -euo pipefail
ARM="$1"; MODE="${2:-}"
SEED=42
EPOCHS=4
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
V=${V_OVERRIDE:-$S/signals/views}
CFG=$M/configs/stage2pilot/pd_graspmap_d5.py
PRED=()
case "$ARM" in
  empty) GMAP=zero ;;
  gt)    GMAP=gt ;;
  pred_noCF|pred_CF|shuffle) GMAP=pred; CFG=$M/configs/stage2pilot/pd_graspmap_pred5.py ;;
  gtpred_CF) GMAP=gt_pred; CFG=$M/configs/stage2pilot/pd_graspmap_d10.py ;;
  *) echo "腕が不明: $ARM" >&2; exit 2 ;;
esac
if [ "$GMAP" = pred ] || [ "$GMAP" = gt_pred ]; then
  VA=$ARM; [ "$ARM" = gtpred_CF ] && VA=pred_CF
  PRED=(--grasp-pred-train "$V/B_${VA}_train.json" --grasp-pred-val "$V/B_${VA}_val.json")
fi
RUN="grasppilot2_B_${ARM}_ep${EPOCHS}_seed${SEED}${MODE:+_$MODE}"
if [ "$MODE" = smoke ]; then WORK=$S/smoke/$RUN; else WORK=$M/experiments/phase1/$RUN; fi
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16)
[ "$MODE" = smoke ] && EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke)
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
source "$M/scripts/load_env.sh" >/dev/null 2>&1 || true
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export T1B_MODEL_CFG=$CFG T1B_WORK_DIR=$WORK PYTHONDONTWRITEBYTECODE=1 GRASPPILOT_TASK=$TASK
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
sha256sum scripts/grasppilot/pd_grasp.py scripts/grasppilot/pd_grasp_model.py scripts/grasppilot/grasp_signals.py \
  scripts/train_t1b.py configs/stage2pilot/pd_graspmap_d5.py configs/stage2pilot/pd_graspmap_pred5.py \
  configs/stage2pilot/pd_graspmap_d10.py > "$WORK/code_sha256.txt"
git rev-parse HEAD > "$WORK/code_commit.txt"
for f in "${PRED[@]}"; do case "$f" in *.json) sha256sum "$f" >> "$WORK/view_sha256.txt" ;; esac; done
set +e
(cd "$M/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$WORK/env_check.txt" 2>&1
python scripts/train_t1b.py --seed "$SEED" --trainable film --task-id "$TASK" --run-name "$RUN" \
  --det-ckpt "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  --grasp-map "$GMAP" "${PRED[@]}" "${EXTRA[@]}" \
  --ckpt-dir "$S/pd_ckpt/$RUN" --save-trainable-only --print-freq 500 > "$WORK/train.log" 2>&1
RC=$?
if [ "$RC" = 0 ]; then
  PYTHONPATH=src:scripts "$M/.venv/bin/python" scripts/grasppilot/pd_grasp_finalize.py "$WORK" "$ARM" > "$WORK/finalize.log" 2>&1
  RC=$?
fi
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/end.txt"
echo "$RC" > "$WORK/exit_code.txt"
echo "[run_pd_grasp2] $RUN rc=$RC"
exit $RC

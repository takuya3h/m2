#!/usr/bin/env bash
# 案 B と術具だけの対照の固定の長さの run を一本起こす（非公式 T-2026-11-06-grasp-pilot-arms、SPEC §3.2〜§3.4・§4・Task D）。
# 二本目の run_pd_grasp2.sh の写しで、本契約の置き場・信号の置き場・腕・run の名前だけを変えた
# （受け取り手・学習範囲・学習率・増強・batch・数値精度（bf16 の自動混合精度）・長さ・seed は二本目と同じ）。
#
#   scripts/grasppilot/run_pd_grasparms.sh <腕> [smoke]
#     案 B: pred_noCF（確定の G の地図）、pred_CF（train は交差適合、val は確定の G）、gtpred_CF（正解と予測-CF の 10 チャネル）、
#           shuffle（並べ替えた予測-noCF）。見取りは前契約の目録の B_m（$R/signals/views/B_<腕>_{train,val}.json。読むだけ）
#     術具だけ: toolonly_pred_noCF（器具の 3 チャネルの最大を 1 チャネル目、他は零）、toolonly_shuffle（同じ信号を目録と同じ並べ替えで）。
#           見取りは本契約の $S/signals/tool_only/B_<腕>_{train,val}.json（scripts/grasppilot/arms_tool_only.py が書く）
#     empty（全 0）は二本目の空の腕の code_sha256 が本契約の経路と違うときだけ回す（SPEC §3.2）
#   GPU は CUDA_VISIBLE_DEVICES。run は experiments/phase1/grasparms_B_<腕>_ep4_seed42、学ぶ部分の重みは $S/pd_ckpt/
#   W&B: train_t1b.py は追跡を持たない（二本目と同じ）。資格情報は読み込まない（SPEC §7-10）
set -euo pipefail
ARM="$1"; MODE="${2:-}"
SEED=42
EPOCHS=4
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-arms
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
R=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild
VR=$R/signals/views
VT=$S/signals/tool_only
CFG=$M/configs/stage2pilot/pd_graspmap_d5.py
PRED=()
case "$ARM" in
  empty) GMAP=zero ;;
  pred_noCF|pred_CF|shuffle) GMAP=pred; CFG=$M/configs/stage2pilot/pd_graspmap_pred5.py
    PRED=(--grasp-pred-train "$VR/B_${ARM}_train.json" --grasp-pred-val "$VR/B_${ARM}_val.json") ;;
  gtpred_CF) GMAP=gt_pred; CFG=$M/configs/stage2pilot/pd_graspmap_d10.py
    PRED=(--grasp-pred-train "$VR/B_pred_CF_train.json" --grasp-pred-val "$VR/B_pred_CF_val.json") ;;
  toolonly_pred_noCF|toolonly_shuffle) GMAP=pred; CFG=$M/configs/stage2pilot/pd_graspmap_pred5.py
    PRED=(--grasp-pred-train "$VT/B_${ARM}_train.json" --grasp-pred-val "$VT/B_${ARM}_val.json") ;;
  *) echo "腕が不明: $ARM" >&2; exit 2 ;;
esac
RUN="grasparms_B_${ARM}_ep${EPOCHS}_seed${SEED}${MODE:+_$MODE}"
if [ "$MODE" = smoke ]; then WORK=$S/smoke/$RUN; else WORK=$M/experiments/phase1/$RUN; fi
[ -e "$WORK" ] && { echo "既に在る: $WORK" >&2; exit 4; }
EXTRA=(--epochs "$EPOCHS" --fixed-epochs --amp bf16)
[ "$MODE" = smoke ] && EXTRA=(--epochs 1 --fixed-epochs --amp bf16 --smoke)
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export T1B_MODEL_CFG=$CFG T1B_WORK_DIR=$WORK PYTHONDONTWRITEBYTECODE=1 GRASPPILOT_TASK=$TASK
mkdir -p "$WORK"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$WORK/start.txt"
hostname > "$WORK/host.txt"
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv > "$WORK/gpu_at_start.txt"
nvidia-smi --query-gpu=index,uuid,memory.used,power.limit --format=csv >> "$WORK/gpu_at_start.txt"
# 二本目の空の腕の code_sha256.txt と同じ並び（SPEC §3.2 の比べ）。台本そのものは別のファイルに
sha256sum scripts/grasppilot/pd_grasp.py scripts/grasppilot/pd_grasp_model.py scripts/grasppilot/grasp_signals.py \
  scripts/train_t1b.py configs/stage2pilot/pd_graspmap_d5.py configs/stage2pilot/pd_graspmap_pred5.py \
  configs/stage2pilot/pd_graspmap_d10.py > "$WORK/code_sha256.txt"
sha256sum scripts/grasppilot/run_pd_grasparms.sh scripts/grasppilot/pd_grasp_finalize.py > "$WORK/runner_sha256.txt"
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
echo "[run_pd_grasparms] $RUN rc=$RC"
exit $RC

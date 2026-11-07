#!/usr/bin/env bash
# 案 B と術具だけの恒等性（非公式 T-2026-11-06-grasp-pilot-arms、Task C-1・C-2）。学習前（界面の重み 0）の出力が塔単独の予測と一致するか、
# 界面の重みを N(0, 0.05²) にすると出力が変わるか（二本目の run_caseB_identity.sh と同じ道具 pd_grasp_eval.py）。
# 基準の予測は本契約の Task B-2 の塔単独の予測（$S/b/plain_val_preds_seed42.json.gz）。
# 予測-CF の val の見取りは予測-noCF と同じ地図（確定の G）なので、予測-CF の val も別に回して確かめる。
#   bash run_caseB_identity.sh <GPU> [名前 ...]
set -uo pipefail
GPU=${1:-0}; shift || true
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-arms
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
VR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/views
VT=$S/signals/tool_only
OUT=$M/experiments/analysis/grasp_pilot_arms/taskC/caseB
REF=$S/b/plain_val_preds_seed42.json.gz
mkdir -p "$OUT"
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU GRASPPILOT_TASK=$TASK
P5=$M/configs/stage2pilot/pd_graspmap_pred5.py; D10=$M/configs/stage2pilot/pd_graspmap_d10.py
ONLY=" $* "
run() { name=$1; shift; [ "$ONLY" != "  " ] && [[ "$ONLY" != *" $name "* ]] && return; [ -s "$OUT/identity_$name.json" ] && { echo "$name skip（既にある）"; return; }
  python scripts/grasppilot/pd_grasp_eval.py "$@" --ref-preds "$REF" --out "$OUT/identity_$name.json" > "$OUT/identity_$name.log" 2>&1; echo "[caseB identity] $name rc=$?"; }
run pred_noCF          --mode pred    --cfg $P5  --pred-view "$VR/B_pred_noCF_val.json" --trainable-check
run pred_CF            --mode pred    --cfg $P5  --pred-view "$VR/B_pred_CF_val.json"
run shuffle            --mode pred    --cfg $P5  --pred-view "$VR/B_shuffle_val.json"
run gtpred_CF          --mode gt_pred --cfg $D10 --pred-view "$VR/B_pred_CF_val.json" --trainable-check
run toolonly_pred_noCF --mode pred    --cfg $P5  --pred-view "$VT/B_toolonly_pred_noCF_val.json" --trainable-check
run toolonly_shuffle   --mode pred    --cfg $P5  --pred-view "$VT/B_toolonly_shuffle_val.json"
run pos_pred_noCF          --mode pred    --cfg $P5  --pred-view "$VR/B_pred_noCF_val.json" --perturb
run pos_gtpred_CF          --mode gt_pred --cfg $D10 --pred-view "$VR/B_pred_CF_val.json" --perturb
run pos_toolonly_pred_noCF --mode pred    --cfg $P5  --pred-view "$VT/B_toolonly_pred_noCF_val.json" --perturb

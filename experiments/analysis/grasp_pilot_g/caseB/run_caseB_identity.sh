#!/usr/bin/env bash
# 案 B の恒等性（非公式 T-2026-11-01-grasp-pilot-g、Task E-2）。学習前（界面の重み 0）の出力が塔単独の予測と一致するか、
# 界面の重みを N(0, 0.05²) にすると出力が変わるか。基準の予測は一本目の塔単独の予測（読むだけ）。GPU は第 1 引数
set -uo pipefail
GPU=${1:-0}
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
V=$S/signals/views
R=$M/experiments/analysis/grasp_pilot_g/caseB
REF=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/b/plain_val_preds.json.gz
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
D5=configs/stage2pilot/pd_graspmap_d5.py; P5=configs/stage2pilot/pd_graspmap_pred5.py; D10=configs/stage2pilot/pd_graspmap_d10.py
run() { name=$1; shift; python scripts/grasppilot/pd_grasp_eval.py "$@" --ref-preds "$REF" --out "$R/identity_$name.json" > "$R/identity_$name.log" 2>&1; echo "$name rc=$?"; }
run empty        --mode zero --cfg $D5 --trainable-check
run gt           --mode gt   --cfg $D5
run pred_noCF    --mode pred --cfg $P5 --pred-view "$V/B_pred_noCF_val.json" --trainable-check
run shuffle      --mode pred --cfg $P5 --pred-view "$V/B_shuffle_val.json"
run gtpred_CF    --mode gt_pred --cfg $D10 --pred-view "$V/B_pred_CF_val.json" --trainable-check
run pos_pred_noCF  --mode pred --cfg $P5 --pred-view "$V/B_pred_noCF_val.json" --perturb
run pos_gtpred_CF  --mode gt_pred --cfg $D10 --pred-view "$V/B_pred_CF_val.json" --perturb

#!/usr/bin/env bash
# 非公式 T-2026-11-01-grasp-pilot-d（利用者の追加の指示）。案 B の正解の腕の恒等性を bengio で測る（一本目の run_caseB_identity.sh と同じ道具）。
# 基準は Task B-1 の塔単独の予測。重ねの BODY を EGO_BODY に置く。GPU 1 だけ。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d
R=$M/experiments/analysis/grasp_pilot_d/extra/identity
cd "$M"
# shellcheck disable=SC1091
source "$OV/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=1
REF=$S/b/plain_val_preds_seed42.json.gz
python scripts/grasppilot/pd_grasp_eval.py --mode gt --trainable-check --ref-preds "$REF" \
  --out "$R/caseB_identity_gt.json" > "$R/caseB_identity_gt.log" 2>&1; echo "gt rc=$?"
python scripts/grasppilot/pd_grasp_eval.py --mode gt --perturb --ref-preds "$REF" \
  --out "$R/caseB_positive_gt_perturb.json" > "$R/caseB_positive_gt_perturb.log" 2>&1; echo "positive rc=$?"

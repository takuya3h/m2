#!/usr/bin/env bash
# 非公式 T-2026-10-31-grasp-pilot-probe、Task D-4・D-5（案 B）。学習前の出力が塔単独と一致するか、陽性対照で変わるか。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe
R=$M/experiments/analysis/grasp_pilot_probe/identity
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1
REF=$S/b/plain_val_preds.json.gz
( CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/pd_grasp_eval.py --mode zero --trainable-check --ref-preds "$REF" \
    --out "$R/caseB_identity_zero.json" > "$R/caseB_identity_zero.log" 2>&1; echo "zero rc=$?"
  CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/pd_grasp_eval.py --mode gt --perturb --ref-preds "$REF" \
    --out "$R/caseB_positive_gt_perturb.json" > "$R/caseB_positive_gt_perturb.log" 2>&1; echo "positive rc=$?" ) &
( CUDA_VISIBLE_DEVICES=1 python scripts/grasppilot/pd_grasp_eval.py --mode gt --ref-preds "$REF" \
    --out "$R/caseB_identity_gt.json" > "$R/caseB_identity_gt.log" 2>&1; echo "gt rc=$?"
  CUDA_VISIBLE_DEVICES=1 python scripts/grasppilot/pd_grasp_eval.py --mode zero --perturb --ref-preds "$REF" \
    --out "$R/caseB_perturb_zero.json" > "$R/caseB_perturb_zero.log" 2>&1; echo "perturb-zero rc=$?" ) &
wait

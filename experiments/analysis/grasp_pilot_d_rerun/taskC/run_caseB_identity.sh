#!/usr/bin/env bash
# 案 B の恒等性（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task C-2）。空と正解の学習前（界面の重み 0）の出力が塔単独の予測と一致するか。
# 陽性対照: 正解の腕で界面の重みを N(0, 0.05²) にすると出力が変わる。空の腕は入力が零のため変わらない（記録だけ。判定に使わない）。
# 四本目の run_caseB_identity.sh と同じ道具 pd_grasp_eval.py。基準の予測は Task B-2 の塔単独の予測。
#   bash run_caseB_identity.sh <GPU>
set -uo pipefail
GPU=${1:-0}
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-d-rerun
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
OUT=$M/experiments/analysis/grasp_pilot_d_rerun/taskC/caseB
REF=$S/b/plain_val_preds_seed42.json.gz
mkdir -p "$OUT"
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU GRASPPILOT_TASK=$TASK
run() { name=$1; shift; [ -s "$OUT/identity_$name.json" ] && { echo "$name skip（既にある）"; return; }
  python scripts/grasppilot/pd_grasp_eval.py "$@" --ref-preds "$REF" --out "$OUT/identity_$name.json" > "$OUT/identity_$name.log" 2>&1; echo "[caseB identity] $name rc=$?"; }
run empty     --mode zero --trainable-check
run gt        --mode gt   --trainable-check
run pos_gt    --mode gt   --perturb
run pos_empty --mode zero --perturb

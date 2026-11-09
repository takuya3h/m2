#!/usr/bin/env bash
# 案 D の run の後処理（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task D）。最後の状態の重みから補助の頭を除き、pd_eval.py --cfg plain で val を評価して
# metrics.json・per_class_ap.json・notes.md を run の置き場に書く。  bash run_finalize.sh <run の名前> <GPU>
set -uo pipefail
RUN=${1:?run}; GPU=${2:?gpu}
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-grasp-pilot-d-rerun
cd "$M"
export PYTHONDONTWRITEBYTECODE=1
# shellcheck disable=SC1091
source "$OV/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A
python scripts/grasppilot/d_finalize_rerun.py --run "$RUN" --gpu "$GPU" > "$S/logs/finalize_$RUN.log" 2>&1
echo "[finalize] $RUN rc=$?"

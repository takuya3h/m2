#!/usr/bin/env bash
# 案 D の確かめ（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task C-1・G3）。腕に数えない。
#   bash run_caseD_check.sh <GPU>
# 1. d_check.py（目録の q = D_q.CF_train.q）: データ・模型・損失（重み 0 と 0.3）・COCO の読み込み
# 2. run_d_arm_rerun.sh smoke（重み 0.3、train 8 枚・val 4 枚・12 epoch。歩ごとの記録、主経路の特徴のフック、COCO の読み込み）
#    → d_finalize_rerun.py で後処理が通ること
# 3. run_d_arm_rerun.sh smoke_nococo（対照: COCO の経路を存在しない経路にして 1 epoch。読み込みの記録が無くなること）
# 命令ごとに GPU 0 または 1 を渡す。2 と 3 は別の GPU で並行してよい（引数で選ぶ）。
set -uo pipefail
GPU=${1:?GPU}; STEP=${2:-all}
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
TASK=T-2026-11-06-grasp-pilot-d-rerun
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
OUT=$M/experiments/analysis/grasp_pilot_d_rerun/taskC
RB=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/D
mkdir -p "$OUT" "$S/logs"
cd "$M"
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
if [ "$STEP" = all ] || [ "$STEP" = check ]; then
  (
    # shellcheck disable=SC1091
    source "$OV/.venv-relation-detr/bin/activate"
    export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A \
      RELDETR_COCO_CKPT=$OV/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
    python scripts/grasppilot/d_check.py --q "$RB/q_CF_train.npz" --out "$OUT/c1_check.json" > "$OUT/c1_check.log" 2>&1
    echo "[caseD] d_check rc=$?"
  )
fi
if [ "$STEP" = all ] || [ "$STEP" = smoke ]; then
  bash scripts/grasppilot/run_d_arm_rerun.sh smoke "${SMOKE_PORT:-29831}" > "$S/logs/smoke.out" 2>&1; echo "[caseD] smoke rc=$?"
  (
    # shellcheck disable=SC1091
    source "$OV/.venv-relation-detr/bin/activate"
    export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$S/smoke_ann
    python scripts/grasppilot/d_finalize_rerun.py --run graspd2_smoke --gpu "$GPU" > "$OUT/smoke_finalize.log" 2>&1; echo "[caseD] smoke finalize rc=$?"
  )
fi
if [ "$STEP" = all ] || [ "$STEP" = nococo ]; then
  bash scripts/grasppilot/run_d_arm_rerun.sh smoke_nococo "${NOCOCO_PORT:-29832}" > "$S/logs/smoke_nococo.out" 2>&1; echo "[caseD] smoke_nococo rc=$?"
fi

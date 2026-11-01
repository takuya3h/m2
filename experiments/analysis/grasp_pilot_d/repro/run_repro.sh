#!/usr/bin/env bash
# 非公式 T-2026-11-01-grasp-pilot-d、Task B-1。検出塔の塔単独の val を bengio で再現する。
# 重ねの BODY（andrew と同じ Relation-DETR。Task A-5）を EGO_BODY で指す。bengio main の third_party は使わない。
# 対照（§8-b）: 別 seed（123）の検出塔を同じ経路で評価する。val だけ。test は評価しない。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d
R=$M/experiments/analysis/grasp_pilot_d/repro
mkdir -p "$R" "$S/b"
cd "$M"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
# shellcheck disable=SC1091
source "$OV/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A
sha256sum "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
  "$OV"/data/annotations/egosurgery_tool_folds/A/instances_{train,val}.json > "$R/b1_sha256.txt"
(cd "$OV/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") > "$R/env_check_det.txt" 2>&1
( CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --save-preds "$S/b/plain_val_preds_seed42.json.gz" --out "$R/dtower_val_seed42.json" > "$R/dtower_val_seed42.log" 2>&1; echo "dtower rc=$?" ) &
( CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
    --out "$R/dtower_val_control_seed123.json" > "$R/dtower_val_control_seed123.log" 2>&1; echo "dtower control rc=$?" ) &
wait

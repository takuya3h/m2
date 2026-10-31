#!/usr/bin/env bash
# 非公式 T-2026-10-31-grasp-pilot-probe、Task C-5。検出塔の decoder の特徴を train（2 分割）と val で取り出す。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe
R=$M/experiments/analysis/grasp_pilot_probe/taskC
mkdir -p "$S/decfeat"
cd "$M"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1
( CUDA_VISIBLE_DEVICES=0 python scripts/grasppilot/extract_decfeat.py --split train --shard 0/2 --out "$S/decfeat/decfeat_train_0.npz" > "$R/decfeat_train_0.log" 2>&1; echo "train0 rc=$?" ) &
( CUDA_VISIBLE_DEVICES=1 python scripts/grasppilot/extract_decfeat.py --split train --shard 1/2 --out "$S/decfeat/decfeat_train_1.npz" > "$R/decfeat_train_1.log" 2>&1; echo "train1 rc=$?" ) &
( CUDA_VISIBLE_DEVICES=1 python scripts/grasppilot/extract_decfeat.py --split val --shard 0/1 --out "$S/decfeat/decfeat_val_0.npz" > "$R/decfeat_val_0.log" 2>&1; echo "val rc=$?" ) &
wait

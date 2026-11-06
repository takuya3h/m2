#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/slocal2/m2
source scripts/load_env.sh
export CUDA_VISIBLE_DEVICES=0,1
export WANDB_MODE=offline
export WANDB_DIR=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/detector/123
export PYTHONPATH=/home/ubuntu/slocal2/m2/src:/home/ubuntu/slocal2/m2/scripts
export CUDA_HOME=/usr/local/cuda
export EGO_ROOT=/home/ubuntu/slocal2/m2/data/raw/ego
export EGO_ANN_DIR=/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool_folds/A
export RELDETR_COCO_CKPT=/home/ubuntu/slocal2/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
export RELDETR_OUTPUT_DIR=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/detector/123
export RELDETR_EVIDENCE_DIR=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/detector/123
export DTOWER_LR=0.0001
export DTOWER_WEIGHT_DECAY=0.0001
export DTOWER_MAX_NORM=0.1
export TOWER_SEARCH_POINT=0
export NCCL_P2P_DISABLE=1
export TOWER_SEARCH_TASK=T-2026-11-02-hostdiff-bengio
export TOWER_SEARCH_SCRATCH=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio
export TOWER_SEARCH_PHASE_PUBLISH=experiments/phase1/stage1_ptower_hostdiff_bengio
export TOWER_SEARCH_STEP_LOG=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/detector/123/steps
cd /home/ubuntu/slocal2/m2/third_party/Relation-DETR
exec /home/ubuntu/slocal2/m2/.venv-relation-detr/bin/accelerate launch --multi_gpu --num_processes 2 --main_process_port 29801 /home/ubuntu/slocal2/m2/scripts/train_relation_detr_search.py --config-file /home/ubuntu/slocal2/m2/configs/detector_relation_detr/train_search.py --seed 123 --mixed-precision fp16 --convergence-schedule --max-epochs 36

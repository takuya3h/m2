#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/local/m2
source scripts/load_env.sh
export CUDA_VISIBLE_DEVICES=3,4
export WANDB_MODE=offline
export WANDB_DIR=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/detector/point19
export PYTHONPATH=/home/ubuntu/local/m2/src:/home/ubuntu/local/m2/scripts
export CUDA_HOME=/usr/local/cuda
export EGO_ROOT=/home/ubuntu/local/m2/data/raw/ego
export EGO_ANN_DIR=/home/ubuntu/local/m2/data/annotations/egosurgery_tool_folds/A
export RELDETR_COCO_CKPT=/home/ubuntu/local/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
export RELDETR_OUTPUT_DIR=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/detector/point19
export RELDETR_EVIDENCE_DIR=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/detector/point19
export DTOWER_LR=1.53e-05
export DTOWER_WEIGHT_DECAY=0.0635
export DTOWER_MAX_NORM=0.07
export TOWER_SEARCH_POINT=19
cd /home/ubuntu/local/m2/third_party/Relation-DETR
exec /home/ubuntu/local/m2/.venv-relation-detr/bin/accelerate launch --multi_gpu --num_processes 2 --main_process_port 29802 /home/ubuntu/local/m2/scripts/train_relation_detr_search.py --config-file /home/ubuntu/local/m2/configs/detector_relation_detr/train_search.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36

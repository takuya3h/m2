#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 契約 T-2026-09-18-stage1-detector-towers / 塔 coco / 折り C / seed 42
cd third_party/Relation-DETR
export EGO_ANN_DIR=/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool_folds/C
export RELDETR_OUTPUT_DIR=/home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower/dcoco_foldC_seed42/work
export CUDA_HOME=/usr/local/cuda
accelerate launch --num_processes 2 --main_process_port 29561 main.py \
    --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16

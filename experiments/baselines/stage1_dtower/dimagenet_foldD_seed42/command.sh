#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 契約 T-2026-09-18-stage1-detector-towers / 塔 imagenet / 折り D / seed 42
cd third_party/Relation-DETR
export EGO_ANN_DIR=/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool_folds/D
export RELDETR_OUTPUT_DIR=/home/ubuntu/slocal2/m2/experiments/baselines/stage1_dtower/dimagenet_foldD_seed42/work
export CUDA_HOME=/usr/local/cuda
accelerate launch --num_processes 2 --main_process_port 29641 main.py \
    --config-file configs/train_config_egosurgery_stage1_imagenet_seed42.py --seed 42 --mixed-precision fp16

#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録（非公式 T-2026-10-18-stage2-pilot-folda / 半分 H2 / seed 42）
cd third_party/Relation-DETR
export EGO_ANN_DIR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/ann_cf/H2
export RELDETR_OUTPUT_DIR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/cf_dtower/stage2pilot_cf_dcoco_H2_seed42/work
export CUDA_HOME=/usr/local/cuda
export NCCL_P2P_DISABLE=1
accelerate launch --num_processes 2 --main_process_port 29782 main.py \
    --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36

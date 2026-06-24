#!/usr/bin/env bash
# Relation-DETR (accelerate) 実行コマンド
# seed=123
cd /home/ubuntu/slocal2/m2/third_party/Relation-DETR && CUDA_VISIBLE_DEVICES=1 RELDETR_OUTPUT_DIR=/tmp/reldetr_work_s0_frozen_seed123_20260616_204720 RELDETR_EVIDENCE_DIR=/tmp/reldetr_work_s0_frozen_seed123_20260616_204720 RELDETR_S0FROZEN_INIT=/home/ubuntu/slocal2/m2/data/external/weights/relation_detr_s0frozen_init_seed42.pth RELDETR_NUM_EPOCHS=12 RELDETR_BATCH_SIZE=2 RELDETR_NUM_WORKERS=4 RELDETR_LR=1e-4 /home/ubuntu/slocal2/m2/.venv-relation-detr/bin/accelerate launch --num_processes 1 main.py --config-file configs/train_config_egosurgery_s0_frozen.py --seed 123 --mixed-precision fp16

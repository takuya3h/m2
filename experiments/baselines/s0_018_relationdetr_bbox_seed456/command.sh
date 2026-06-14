#!/usr/bin/env bash
# Relation-DETR (accelerate) 実行コマンド
# seed=456
accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed456.py --seed 456 --mixed-precision fp16

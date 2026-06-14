#!/usr/bin/env bash
# Relation-DETR (accelerate) 実行コマンド
# seed=123
accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed123.py --seed 123 --mixed-precision fp16

#!/usr/bin/env bash
# Relation-DETR (accelerate) 実行コマンド
# seed=42
accelerate launch --num_processes 2 main.py --config-file configs/train_config_egosurgery_seed42.py --seed 42 --mixed-precision fp16

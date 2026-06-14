#!/usr/bin/env bash
# Stable-DINO (detrex) 実行コマンド
# seed=42
python train_net_egosurgery.py --config-file /home/ubuntu/slocal2/m2/third_party/DI-MaskDINO/configs/dimaskdino_r50_egosurgery.yaml --num-gpus 2 SEED 42 OUTPUT_DIR /tmp/dimaskdino_work_seed42

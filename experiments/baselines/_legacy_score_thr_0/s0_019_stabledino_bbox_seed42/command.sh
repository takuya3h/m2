#!/usr/bin/env bash
# Stable-DINO (detrex) 実行コマンド
# seed=42
python tools/train_net_egosurgery.py --config-file stabledino_r50_4scale_12ep_egosurgery.py --num-gpus 2 train.seed=42

#!/usr/bin/env bash
# Stable-DINO (detrex) 実行コマンド
# seed=456
tools/train_net_egosurgery.py --config-file /home/ubuntu/slocal2/m2/third_party/detrex/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery.py --num-gpus 2 train.seed=456

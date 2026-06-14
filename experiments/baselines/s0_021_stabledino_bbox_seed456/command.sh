#!/usr/bin/env bash
# Stable-DINO (detrex) 実行コマンド
# seed=456
python tools/train_net_egosurgery.py --config-file /home/ubuntu/slocal2/m2/third_party/Stable-DINO/projects/stabledino/configs/stabledino_r50_4scale_12ep_egosurgery.py --num-gpus 2 train.seed=456 train.output_dir=/tmp/stabledino_work_seed456

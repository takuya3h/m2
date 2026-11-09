#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-09T04:31:53+00:00
python scripts/stage2pilot/dp_train.py train --type RT --rt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot --rt-layer layer4 --rt-content roi --rt-k 64 --arm gtpred_CF --seed 42 --converge --task-id T-2026-11-09-grasp-pilot-converge --exp-prefix grasprc_rt

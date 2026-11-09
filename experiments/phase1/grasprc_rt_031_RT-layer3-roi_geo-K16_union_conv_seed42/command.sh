#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-09T04:32:06+00:00
python scripts/stage2pilot/dp_train.py train --type RT --rt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot --rt-layer layer3 --rt-content roi_geo --rt-k 16 --arm union --seed 42 --converge --task-id T-2026-11-09-grasp-pilot-converge --exp-prefix grasprc_rt

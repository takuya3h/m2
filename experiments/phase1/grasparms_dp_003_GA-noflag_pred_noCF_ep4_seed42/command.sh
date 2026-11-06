#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-06T07:24:32+00:00
python scripts/stage2pilot/dp_train.py train --type GA --arm pred_noCF --seed 42 --fixed-epochs 4 --grasp-no-flag --grasp-signal-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals --grasp-pred-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/A --task-id T-2026-11-06-grasp-pilot-arms --exp-prefix grasparms_dp

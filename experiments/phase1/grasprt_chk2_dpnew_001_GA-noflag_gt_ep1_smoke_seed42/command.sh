#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-09T02:20:31+00:00
python scripts/stage2pilot/dp_train.py train --type GA --arm gt --seed 42 --fixed-epochs 1 --smoke --grasp-signal-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals --grasp-pred-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/A --grasp-no-flag --task-id T-2026-11-09-grasp-roitoken-transition-pilot --exp-prefix grasprt_chk2_dpnew

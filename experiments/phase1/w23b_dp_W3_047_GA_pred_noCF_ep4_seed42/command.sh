#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-01T16:14:29+00:00
python scripts/stage2pilot/dp_train.py train --type GA --arm pred_noCF --seed 42 --grasp-signal-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-probe/signals --grasp-pred-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A --fixed-epochs 4 --scope W3 --task-id T-2026-11-01-stage2-w23-bengio --exp-prefix w23b_dp_W3

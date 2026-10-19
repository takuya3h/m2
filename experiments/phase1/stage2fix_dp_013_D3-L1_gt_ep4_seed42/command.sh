#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-10-19T08:38:17+00:00
python scripts/stage2pilot/dp_train.py train --type D3-L1 --arm gt --seed 42 --inst-variant uq --fixed-epochs 4 --task-id T-2026-10-19-stage2-pilot-fix-epoch4-shuffle --exp-prefix stage2fix_dp

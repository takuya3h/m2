#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-20T06:37:31+00:00
python scripts/stage2pilot/dp_train.py train --type GR --gr-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph/smoke --gr-N 10 --gr-L 1 --arm empty --scope W3 --seed 42 --fixed-epochs 2 --smoke --task-id T-2026-11-20-grasp-hand-graph-pilot --exp-prefix grasp_hand_graph_chk --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph/smoke/dp_ckpt --save-last-probs

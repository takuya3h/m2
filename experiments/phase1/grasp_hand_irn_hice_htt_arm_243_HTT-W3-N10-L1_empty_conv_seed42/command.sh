#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-21T07:04:08+00:00
python scripts/stage2pilot/dp_train.py train --type HTT --gr-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph --gr-N 10 --gr-L 1 --scope W3 --arm empty --converge --save-last-probs --seed 42 --task-id T-2026-11-21-grasp-hand-irn-hice-htt-pilot --exp-prefix grasp_hand_irn_hice_htt_arm --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt/dp_ckpt

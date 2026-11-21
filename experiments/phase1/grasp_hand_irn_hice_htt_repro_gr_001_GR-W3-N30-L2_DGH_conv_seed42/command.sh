#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-21T06:05:40+00:00
python scripts/stage2pilot/dp_train.py train --type GR --gr-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph --gr-N 30 --gr-L 2 --scope W3 --arm DGH --seed 42 --converge --task-id T-2026-11-21-grasp-hand-irn-hice-htt-pilot --exp-prefix grasp_hand_irn_hice_htt_repro_gr --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt/repro/dp_ckpt --save-last-probs

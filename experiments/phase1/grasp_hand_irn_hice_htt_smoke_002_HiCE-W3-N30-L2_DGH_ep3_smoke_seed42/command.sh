#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-21T06:07:31+00:00
python scripts/stage2pilot/dp_train.py train --type HiCE --gr-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph --gr-N 30 --gr-L 2 --scope W3 --arm DGH --seed 42 --fixed-epochs 3 --smoke --task-id T-2026-11-21-grasp-hand-irn-hice-htt-pilot --exp-prefix grasp_hand_irn_hice_htt_smoke --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt/smoke/dp_ckpt

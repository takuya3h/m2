#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-21T01:16:16+00:00
python scripts/stage2pilot/dp_train.py train --type GR --gr-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph --gr-N 10 --gr-L 1 --scope W1 --arm DGH-noCF --seed 42 --converge --task-id T-2026-11-21-grasp-hand-graph-t2p-match --exp-prefix grasp_hand_graph_t2p_repro_gr --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p/repro/dp_ckpt --save-last-probs

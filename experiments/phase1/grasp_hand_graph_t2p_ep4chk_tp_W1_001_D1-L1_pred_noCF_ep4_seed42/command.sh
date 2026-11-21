#!/usr/bin/env bash
# 自動生成: この実験を起動したコマンドの記録
# 生成日時: 2026-11-21T01:18:22+00:00
python scripts/stage2pilot/dp_train.py train --type D1-L1 --arm pred_noCF --scope W1 --fixed-epochs 4 --record-epochs 4 --seed 42 --task-id T-2026-11-21-grasp-hand-graph-t2p-match --exp-prefix grasp_hand_graph_t2p_ep4chk_tp_W1 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p/dp_ckpt

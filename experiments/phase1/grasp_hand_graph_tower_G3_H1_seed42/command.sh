#!/usr/bin/env bash
/home/ubuntu/slocal2/m2/.venv/bin/python scripts/grasppilot/ghg_tower.py train --tower G3 --videos H1 --run-dir experiments/phase1/grasp_hand_graph_tower_G3_H1_seed42 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph/ckpt/G3_H1 --ann-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph/ann

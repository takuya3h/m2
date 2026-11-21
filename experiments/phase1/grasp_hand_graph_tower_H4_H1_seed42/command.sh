#!/usr/bin/env bash
/home/ubuntu/slocal2/m2/.venv/bin/python scripts/grasppilot/ghg_tower.py train --tower H4 --videos H1 --run-dir experiments/phase1/grasp_hand_graph_tower_H4_H1_seed42 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph/ckpt/H4_H1 --ann-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph/ann

#!/usr/bin/env bash
/home/ubuntu/slocal2/m2/.venv/bin/python scripts/grasppilot/g5_train.py --run-dir experiments/phase1/grasptower_G_all_seed42 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/g/ckpt/all --ann-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/g/ann --videos all --batch 8 --amp bf16

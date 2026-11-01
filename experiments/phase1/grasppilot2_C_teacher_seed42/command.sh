#!/usr/bin/env bash
/home/ubuntu/slocal2/m2/.venv/bin/python scripts/grasppilot/ptower_aux.py finetune --arm teacher --targets /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/C/t_teacher_train.npz --run-dir experiments/phase1/grasppilot2_C_teacher_seed42 --ckpt-dir /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/ptower/grasppilot2_C_teacher_seed42

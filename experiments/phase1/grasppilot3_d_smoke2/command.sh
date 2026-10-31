#!/usr/bin/env bash
# 非公式（T-2026-11-01-grasp-pilot-d）。案 D の腕 smoke2。自動生成: この run を起動した命令の記録
cd /home/ubuntu/slocal2/s2fix-bengio-body/third_party/Relation-DETR
export CUDA_VISIBLE_DEVICES=1
export CUDA_HOME=/usr/local/cuda
export EGO_BODY=/home/ubuntu/slocal2/s2fix-bengio-body
export EGO_ROOT=/home/ubuntu/slocal2/s2fix-bengio-body/data/raw/ego
export EGO_ANN_DIR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/smoke_ann
export RELDETR_OUTPUT_DIR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/work/grasppilot3_d_smoke2
export RELDETR_COCO_CKPT=/home/ubuntu/slocal2/s2fix-bengio-body/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
export GRASP_D_CODE=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/code/9b1ecd5fa432ea69
export GRASP_AUX_WEIGHT=0.3
export GRASP_TARGETS=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/targets/trial_q_probe_gt_train.npz
export GRASP_STEPLOG=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/work/grasppilot3_d_smoke2/grasp_steplog.jsonl
export GRASP_SWAP_ON_FLIP=1
accelerate launch --num_processes 1 --main_process_port 29813 main.py --config-file /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/code/9b1ecd5fa432ea69/d_train_config.py --seed 42 --mixed-precision fp16 --accumulate-steps 2 --max-epochs 12

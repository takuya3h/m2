# DRAFT (not for direct training) — Relation-DETR train_config adapted to EgoSurgery.
# Run from inside third_party/Relation-DETR with the .venv-relation-detr venv:
#   CUDA_VISIBLE_DEVICES=0,1 accelerate launch --num_processes 2 main.py \
#       --config-file <this file> --seed 42 --mixed-precision fp16
# Lines marked # <CHANGED> are EgoSurgery-specific.
import os
from torch import optim

from datasets.coco import CocoDetection
from transforms import presets
from optimizer import param_dict

# ---- training schedule (matches S0: 12 epochs, step at 10) ----
num_epochs = 12          # S0 parity
batch_size = 2           # <CHANGED-ish> per-GPU bs; with 2 GPUs -> effective bs = 4 (S0 parity)
num_workers = 4
pin_memory = True
print_freq = 50
starting_epoch = 0
max_norm = 0.1

output_dir = os.environ.get(
    "RELDETR_OUTPUT_DIR",
    "/home/ubuntu/slocal/m2/experiments/detector_improve/augstrong_hires_seed42",
)
find_unused_parameters = False

# ---- EgoSurgery dataset (COCO-format, bbox-only, 15 classes) ----  # <CHANGED block>
# NOTE: instances_*.json file_name fields already include the split prefix
#       e.g. "train/01/01_1_0124.jpg", so img_folder must be the PARENT (data/raw/ego).
EGO_ROOT = os.environ.get("EGO_ROOT", "/home/ubuntu/slocal2/m2/data/raw/ego")
ANN_DIR = os.environ.get(
    "EGO_ANN_DIR", "/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool"
)
train_dataset = CocoDetection(
    img_folder=EGO_ROOT,
    ann_file=f"{ANN_DIR}/instances_train.json",
    transforms=presets.strong_album_1200_2000,  # <CHANGED Method C> 強aug＋高解像度（best-shot）
    train=True,
)
test_dataset = CocoDetection(
    img_folder=EGO_ROOT,
    ann_file=f"{ANN_DIR}/instances_val.json",   # use instances_test.json for final test eval
    transforms=None,
)

# model config to train
model_path = "configs/relation_detr/relation_detr_resnet50_egosurgery.py"  # <CHANGED> drafted above

# ---- COCO-pretrained finetune (S0 load_from parity) ----  # <CHANGED>
# Pointing resume_from_checkpoint at a .pth FILE => finetune. main.py loads it via
# load_state_dict(), and filter_mismatched_weights() auto-drops the 91->15 class-head
# mismatch (backbone + transformer load, class heads reinit). A local copy is preferred
# to avoid network access at train time; download once to data/external/weights/.
resume_from_checkpoint = os.environ.get(
    "RELDETR_COCO_CKPT",
    "/home/ubuntu/slocal2/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth",
)

# ---- optimizer / scheduler (Relation-DETR defaults; 1x schedule) ----
learning_rate = 1e-4     # see report: S0 lr_scaling=linear_x2 maps to doubling base lr for eff bs
optimizer = optim.AdamW(lr=learning_rate, weight_decay=1e-4, betas=(0.9, 0.999))
lr_scheduler = optim.lr_scheduler.MultiStepLR(milestones=[10], gamma=0.1)
param_dicts = param_dict.finetune_backbone_and_linear_projection(lr=learning_rate)

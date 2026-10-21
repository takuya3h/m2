"""Relation-DETR's existing COCO recipe, with the three preregistered search inputs."""
import os

from datasets.coco import CocoDetection
from optimizer import param_dict
from torch import optim
from transforms import presets

num_epochs = 12
batch_size = 2
num_workers = 4
pin_memory = True
print_freq = 50
starting_epoch = 0
find_unused_parameters = False
max_norm = float(os.environ["DTOWER_MAX_NORM"])
learning_rate = float(os.environ["DTOWER_LR"])
weight_decay = float(os.environ["DTOWER_WEIGHT_DECAY"])
output_dir = os.environ["RELDETR_OUTPUT_DIR"]
EGO_ROOT = os.environ["EGO_ROOT"]
ANN_DIR = os.environ["EGO_ANN_DIR"]
evaluation_split = os.environ.get("DTOWER_EVAL_SPLIT", "val")
if evaluation_split not in ("train", "val"):
    raise ValueError("Search never evaluates test")
resume_from_checkpoint = os.environ["RELDETR_COCO_CKPT"]
if not os.path.isfile(resume_from_checkpoint):
    raise FileNotFoundError(resume_from_checkpoint)

train_dataset = CocoDetection(img_folder=EGO_ROOT,
                              ann_file=f"{ANN_DIR}/instances_train.json",
                              transforms=presets.detr, train=True)
test_dataset = CocoDetection(img_folder=EGO_ROOT,
                             ann_file=f"{ANN_DIR}/instances_{evaluation_split}.json", transforms=None)
model_path = "configs/relation_detr/relation_detr_resnet50_egosurgery.py"
optimizer = optim.AdamW(lr=learning_rate, weight_decay=weight_decay, betas=(0.9, 0.999))
lr_scheduler = optim.lr_scheduler.MultiStepLR(milestones=[10], gamma=0.1)
param_dicts = param_dict.finetune_backbone_and_linear_projection(lr=learning_rate)

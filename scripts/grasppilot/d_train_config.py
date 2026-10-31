# 非公式 T-2026-11-01-grasp-pilot-d — 案 D の学習設定（main.py の --config-file）。
# 記録の検出塔の設定 third_party/Relation-DETR/configs/train_config_egosurgery_seed42.py と同じ値。
# 違うのは次の 3 点だけ:
#   1. train_dataset が grasp_aux_d.GraspTargetCoco（枠ごとの q を運ぶ。変換と出力の枠・ラベルは元と同じ）
#   2. model_path が scripts/grasppilot/d_model_config.py（元の模型 + 補助の頭）
#   3. num_epochs = 15（記録の回した epoch 数。起動でも --max-epochs 15 を渡す）。COCO の重みが
#      ファイルでなければ止める（main.py は黙って読み込みを飛ばすため。context/env-facts.md）
# 腕を区別するのは環境変数 GRASP_AUX_WEIGHT と GRASP_TARGETS だけ（grasp_aux_d.env_settings）。
# Config は partial のためにこのファイルを一時の場所へ書き直して読むので、__file__ に頼らず
# GRASP_D_CODE（scripts/grasppilot の絶対経路）から読む。
import os
import sys

from datasets.coco import CocoDetection
from optimizer import param_dict
from torch import optim
from transforms import presets

sys.path.insert(0, os.environ["GRASP_D_CODE"])
import grasp_aux_d  # noqa: E402

# ---- training schedule ----
num_epochs = 15
batch_size = 2
num_workers = 4
pin_memory = True
print_freq = 50
starting_epoch = 0
max_norm = 0.1

output_dir = os.environ["RELDETR_OUTPUT_DIR"]
find_unused_parameters = False

EGO_ROOT = os.environ["EGO_ROOT"]
ANN_DIR = os.environ["EGO_ANN_DIR"]
_s = grasp_aux_d.env_settings()
train_dataset = grasp_aux_d.grasp_dataset_class()(
    img_folder=EGO_ROOT,
    ann_file=f"{ANN_DIR}/instances_train.json",
    transforms=presets.detr,
    train=True,
    q_table=_s["targets"],
    swap_on_flip=_s["swap_on_flip"],
)
test_dataset = CocoDetection(
    img_folder=EGO_ROOT,
    ann_file=f"{ANN_DIR}/instances_val.json",
    transforms=None,
)

model_path = os.path.join(os.environ["GRASP_D_CODE"], "d_model_config.py")

resume_from_checkpoint = os.environ["RELDETR_COCO_CKPT"]
if not os.path.isfile(resume_from_checkpoint) and os.environ.get("GRASP_ALLOW_MISSING_COCO") != "1":
    raise FileNotFoundError(f"COCO の重みがファイルでない: {resume_from_checkpoint}")

# ---- optimizer / scheduler（記録と同じ） ----
learning_rate = 1e-4
optimizer = optim.AdamW(lr=learning_rate, weight_decay=1e-4, betas=(0.9, 0.999))
lr_scheduler = optim.lr_scheduler.MultiStepLR(milestones=[10], gamma=0.1)
param_dicts = param_dict.finetune_backbone_and_linear_projection(lr=learning_rate)

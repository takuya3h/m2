# s0_frozen_002_relationdetr_s0frozen_cocohead_seed123

検出器: Relation-DETR S0-frozen (accelerate, torch 2.1.2+cu118, .venv-relation-detr)
seed: 123

## 結果
mAP=0.6997 / AP_rare=0.7647 / AP_common=0.6889 (best epoch 3)

## per-class AP
COCO mAP(0.50:0.95)。engine.py 改修で precision 全 IoU 平均を出力。
Retractor 等 val 非存在クラスは NaN (AP_rare/common 平均から除外)。

## 初期化
S0-frozen init: Relation-DETR seed42 frozen backbone + COCO-init transformer/head (merged checkpoint: /home/ubuntu/slocal2/m2/data/external/weights/relation_detr_s0frozen_init_seed42.pth). Backbone is frozen with freeze_indices=(0,1,2,3); trainable parts are neck/transformer/detection heads.

## tracking
TensorBoard (train dir/tf_log)。wandb は未使用。

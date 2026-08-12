# s0_frozen_006_relationdetr_s0frozen_neck_cocohead_seed456

検出器: Relation-DETR S0-frozen+neck (accelerate, torch 2.1.2+cu118, .venv-relation-detr)
seed: 456

## 結果
mAP=0.7136 / AP_rare=0.7790 / AP_common=0.7027 (best epoch 12)

## per-class AP
COCO mAP(0.50:0.95)。engine.py 改修で precision 全 IoU 平均を出力。
Retractor 等 val 非存在クラスは NaN (AP_rare/common 平均から除外)。

## 初期化
S0-frozen′ init: Relation-DETR seed42 frozen backbone + COCO-init transformer/head + 共有 C5 線形 neck (trainable, zero-init, 1x1 2048->2048 residual). Backbone frozen freeze_indices=(0,1,2,3); trainable = neck/transformer/heads + c5_neck. trainable_total=29,435,040 (base 25,238,688 + c5_neck 4,196,352). ②特徴レベル系統の Δ_detection 分母。

## tracking
TensorBoard (train dir/tf_log)。wandb は未使用。

# s0_016_relationdetr_bbox_seed42

検出器: Relation-DETR (accelerate, torch 2.1.2+cu118, .venv-relation-detr)
seed: 42

## 結果
mAP=0.7297 / AP_rare=0.7576 / AP_common=0.7251 (best epoch 12)

## per-class AP
COCO mAP(0.50:0.95)。engine.py 改修で precision 全 IoU 平均を出力。
Retractor 等 val 非存在クラスは NaN (AP_rare/common 平均から除外)。

## 初期化
Relation-DETR R50 COCO 1x 重み (backbone+transformer)、class head は 91->15 で再初期化 (他検出器の COCO fine-tune と同条件)。

## tracking
TensorBoard (train dir/tf_log)。wandb は未使用。

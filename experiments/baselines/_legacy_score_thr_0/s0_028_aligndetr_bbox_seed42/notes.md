# s0_028_aligndetr_bbox_seed42

検出器: Align-DETR (detrex, torch 2.1.2+cu118, .venv-detectron2)
seed: 42

## 結果
mAP=0.7191 / AP_rare=0.7969 / AP_common=0.7062 (best eval #12)

## 初期化
DINO R50 COCO 12ep 重み (backbone+transformer)、class_embed は 80->15 で再初期化 (他検出器の COCO fine-tune と同条件)。

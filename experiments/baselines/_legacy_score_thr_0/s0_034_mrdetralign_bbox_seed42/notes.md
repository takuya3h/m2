# s0_034_mrdetralign_bbox_seed42

検出器: Mr.DETR-Align (detrex, torch 2.1.2+cu118, .venv-detectron2)
seed: 42

## 結果
mAP=0.7200 / AP_rare=0.7661 / AP_common=0.7123 (best eval #12)

## 初期化
DINO R50 COCO 12ep 重み (backbone+transformer)、class_embed は 80->15 で再初期化 (他検出器の COCO fine-tune と同条件)。

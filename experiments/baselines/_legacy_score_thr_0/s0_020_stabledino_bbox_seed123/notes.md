# s0_020_stabledino_bbox_seed123

検出器: Stable-DINO (detrex, torch 2.1.2+cu118, .venv-detectron2)
seed: 123

## 結果
mAP=0.7254 / AP_rare=0.7734 / AP_common=0.7174 (best eval #12)

## 初期化
DINO R50 COCO 12ep 重み (backbone+transformer)、class_embed は 80->15 で再初期化 (他検出器の COCO fine-tune と同条件)。

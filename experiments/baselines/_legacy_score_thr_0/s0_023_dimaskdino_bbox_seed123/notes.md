# s0_023_dimaskdino_bbox_seed123

検出器: DI-MaskDINO (detrex, torch 2.1.2+cu118, .venv-detectron2)
seed: 123

## 結果
mAP=0.3936 / AP_rare=0.4253 / AP_common=0.3883 (best eval #9)

## 初期化
DINO R50 COCO 12ep 重み (backbone+transformer)、class_embed は 80->15 で再初期化 (他検出器の COCO fine-tune と同条件)。

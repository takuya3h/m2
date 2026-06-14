# s0_037_dacdetr_bbox_seed42

## 仮説
DAC-DETR (Divide-And-Conquer DETR, NeurIPS 2023) を EgoSurgery-Tool に統一 recipe
で fine-tune する。auxiliary decoder (cross-attention 特化 + one-to-many 割当) により
query の object 集約が改善し、特に小型・希少術具 (Skewer/Syringe) の AP 向上を期待。
評価する構成は dac_cdn_ice = DAC + CDN(対照denoising) + ICE(IoU関連loss / align系)。

## 実験設定
- Detector: DAC-DETR / dac_cdn_ice (ResNet-50, enc6/dec6, num_queries_one2one=900)
- Epochs: 12 / per-GPU batch=2 / seed=42
- DDP: 2 GPU (RTX 6000 Ada, philip) → effective_bs=4
- Optimizer: AdamW lr=0.0002 (backbone 2e-05), wd=0.0001,
  scheduler=StepLR drop@11
- 事前重み: dac_cdn_ice_r50_12ep_coco (official, COCO AP 50.9); class_embed 91->15 reinit, bbox-only
- データ split: EgoSurgery 公式 (train 9657 / val 1515 / test 4265)、評価=val、bbox-only
- 評価: pycocotools COCOeval (test_coco_eval_bbox)。per-class AP は COCOeval.precision
  から IoU0.5:0.95/area=all/maxDet=100 で抽出 (mmdet 系と同定義)

## 結果
- val mAP=0.7165, mAP_50=0.8357, mAP_75=0.7660
- AP_rare=0.7778, AP_common=0.7063 (best epoch=11)

## 解釈
- 他検出器 (judge #6) との Δ 比較は compare_judge6.py で集計。
- val 非存在クラス (Retractor 等) は per-class AP=NaN として rare/common 平均から除外。

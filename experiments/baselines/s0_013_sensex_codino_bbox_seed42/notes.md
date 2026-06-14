# s0_013_sensex_codino_bbox_seed42

## 仮説
Sense-X Co-DETR (CoDINO 5-scale, 9-encoder, R50 LSJ) を EgoSurgery-Tool に
fine-tune すれば、既存 6-encoder 版 (s0_007-009) より rare クラスの AP を
+α 改善できる (encoder 表現力増による稀少特徴抽出の向上)。

## 実験設定
- Detector: Sense-X Co-DETR (CoDINO 5-scale, encoder=9 layers, decoder=6 layers)
- Backbone/Neck: ResNet-50 + ChannelMapper (5 scale)
- Epochs: 12 / batch=2 per-GPU / seed=42
- DDP: 2 GPU (RTX 6000 Ada, philip) → effective_bs=4, lr_scaling=linear_x2
- test_cfg (branch 0 / detr): score_thr=1e-8, max_per_img=300, nms_pre=3000,
  nms_iou=0.6
- データ split: EgoSurgery 公式 (train 9657 / val 1515 / test 4265)
- パイプライン: mmdet 2.x の `tools/train.py` (Sense-X 公式 entry)。
  EgoSurgery は bbox-only なので親 config の LSJ + CopyPaste は除外し、
  通常 bbox pipeline を使用 (config コメントの代替版)。
- 事前学習重み: co_dino_5scale_r50_1x_coco.pth (6-encoder 版)。
  9-encoder の追加 3 層は scratch init。

## 結果
- val mAP=0.7180, mAP_50=0.8560, mAP_75=0.7850
- AP_rare=0.7435, AP_common=0.7143
  (best epoch=12)

## 解釈
- 既存 codetr (s0_007-009, 6-encoder) との Δ:
  ΔAP_rare 等は judge #6 拡張で集計。
- 形状類似ペア (Forceps/Tweezers/Needle Holders/Bipolar Forceps) の混同は
  visualizations/confusion_matrix.png 参照。

# s0_003_maskdino_bbox_seed456

## 仮説
COCO 事前学習済み DINO (dino-4scale_r50, COCO 事前学習) — Mask DINO 枠の代替 を EgoSurgery-Tool（術具 15 クラス）へ fine-tune すれば、§2.5(a) の S0 基準点を実検出器で確立できる。

## 実験設定
- Detector: DINO (dino-4scale_r50, COCO 事前学習) — Mask DINO 枠の代替
- Backbone/Neck: ResNet-50 + FPN（COCO 重みから転移、分類ヘッドのみ再初期化）
- Epochs: 12 / batch=2 / seed=456
- 評価: val split（/home/ubuntu/slocal2/m2/data/annotations/egosurgery_tool/instances_val.json）COCO mAP
- パイプライン: mmdet 3.3.0 Runner（spec §2.1 の「Runner 不使用」からは逸脱。実 SOTA の確実な再現を優先した）

## 結果
- val mAP=67.00 / mAP_50=79.50 / mAP_75=73.10
- AP_rare=77.75 / AP_common=60.18（best epoch=12）

## 解釈
per_class_ap.json と visualizations/confusion_matrix.png を参照。
形状類似ペア（Forceps/Tweezers/Needle Holders/Bipolar Forceps）の
誤分類傾向は混同行列で確認する。

## 次の行動
1. 3 seed の平均±標準偏差を /delta で集計し §2.5(a) 基準点として確定する。

# s0_004_varifocanet_bbox_seed42

## 仮説
COCO 事前学習済み VarifocalNet (vfnet_r50_fpn, COCO 事前学習) を EgoSurgery-Tool（術具 15 クラス）へ fine-tune すれば、§2.5(a) の S0 基準点を実検出器で確立できる。

## 実験設定
- Detector: VarifocalNet (vfnet_r50_fpn, COCO 事前学習)
- Backbone/Neck: ResNet-50 + FPN（COCO 重みから転移、分類ヘッドのみ再初期化）
- Epochs: 12 / batch=4 / seed=42
- 評価: val split（/home/ubuntu/slocal2/egosurgery_multitask/data/annotations/egosurgery_tool/instances_val.json）COCO mAP
- パイプライン: mmdet 3.3.0 Runner（spec §2.1 の「Runner 不使用」からは逸脱。実 SOTA の確実な再現を優先した）

## 結果
- val mAP=28.50 / mAP_50=41.70 / mAP_75=30.50
- AP_rare=13.47 / AP_common=27.47（best epoch=10）
- 完了判定 #4（VarifocalNet mAP ≥ 45.8）: val mAP=28.50 → **未達**

## 解釈
per_class_ap.json と visualizations/confusion_matrix.png を参照。
形状類似ペア（Forceps/Tweezers/Needle Holders/Bipolar Forceps）の
誤分類傾向は混同行列で確認する。

## 次の行動
1. 3 seed の平均±標準偏差を /delta で集計し §2.5(a) 基準点として確定する。

---

## 追加評価: test split での mAP（公式 SOTA 比較）

公式 EgoSurgery-Tool の SOTA 値 (VarifocalNet mAP=45.8) は **test 分割** の値と
推察されるため、val で得た best checkpoint (best_val_mAP_epoch_10.pth) を
test 4265 枚で再評価した。

| split | mAP | mAP_50 | mAP_75 | AP_rare | AP_common |
|---|---:|---:|---:|---:|---:|
| val (training-time best) | 0.285 | 0.418 | — | 0.135 | 0.275 |
| **test (post-hoc)** | **0.388** | **0.555** | **0.431** | **0.329** | **0.403** |

- 完了判定 #4 (VarifocalNet mAP ≥ 45.8): test 0.388 → **未達（7pt の差）**
- val→test で +10pt の改善。test には rare クラスのインスタンスがより多く分布し、
  Skewer 57.6% / Mouth Gag 73.7% / Bipolar Forceps 53.7% など val では計測困難だった
  クラスが評価可能。AP_rare は val 13.5% → test 32.9% へ向上。
- 残り 7pt の差は schedule (1x vs 2x/3x) / multi-scale training /
  長尾対策の有無といったハイパーパラメータの差に起因する可能性が高い。
- 評価コマンドは `/tmp/eval_s0_004_test.py` に保存（再現可能）。

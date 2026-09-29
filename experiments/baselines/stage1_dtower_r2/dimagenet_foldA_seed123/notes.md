# dimagenet_foldA_seed123

契約: T-2026-09-19-stage1-detector-towers-r2
塔: D*-ImageNet / 折り: A / seed: 123

## 結果

- val  mAP=0.6750 / AP_rare=0.7599 / AP_common=0.6609

## 収束

- 最良 epoch: 26（val mAP 0.675274）
- 学習率の低下: epoch 22
- 打ち切り: epoch 30
- 観測した epoch 数: 31

## 処方

凍結源 `s0_016` と**学習の長さの決め方だけ**が違う（fp16・実効バッチ 4・lr 1e-4・`presets.detr` は同一。上限 36、停滞 4 でlr を 0.1 倍、再停滞で打ち切り）。
違うのは折りの注釈と seed と初期化だけである。所要 20:30:51。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

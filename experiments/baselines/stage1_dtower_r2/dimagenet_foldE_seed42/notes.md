# dimagenet_foldE_seed42

契約: T-2026-09-19-stage1-detector-towers-r2
塔: D*-ImageNet / 折り: E / seed: 42

## 結果

- val  mAP=0.4646 / AP_rare=0.6081 / AP_common=0.4385
- test mAP=0.5569 / AP_rare=0.7749 / AP_common=0.5233（**折りごとに一度だけ**評価）

## 収束

- 最良 epoch: 12（val mAP 0.464231）
- 学習率の低下: epoch 10
- 打ち切り: epoch 16
- 観測した epoch 数: 17

## 処方

凍結源 `s0_016` と**学習の長さの決め方だけ**が違う（fp16・実効バッチ 4・lr 1e-4・`presets.detr` は同一。上限 36、停滞 4 でlr を 0.1 倍、再停滞で打ち切り）。
違うのは折りの注釈と seed と初期化だけである。所要 13:08:33。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

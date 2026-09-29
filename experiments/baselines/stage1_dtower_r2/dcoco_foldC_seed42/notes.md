# dcoco_foldC_seed42

契約: T-2026-09-19-stage1-detector-towers-r2
塔: D*-COCO / 折り: C / seed: 42

## 結果

- val  mAP=0.4339 / AP_rare=0.6238 / AP_common=0.4047
- test mAP=0.4803 / AP_rare=0.5955 / AP_common=0.4611（**折りごとに一度だけ**評価）

## 収束

- 最良 epoch: 10（val mAP 0.433927）
- 学習率の低下: epoch 9
- 打ち切り: epoch 14
- 観測した epoch 数: 15

## 処方

凍結源 `s0_016` と**学習の長さの決め方だけ**が違う（fp16・実効バッチ 4・lr 1e-4・`presets.detr` は同一。上限 36、停滞 4 でlr を 0.1 倍、再停滞で打ち切り）。
違うのは折りの注釈と seed と初期化だけである。所要 11:09:37。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

# dcoco_foldA_seed456

契約: T-2026-09-19-stage1-detector-towers-r2
塔: D*-COCO / 折り: A / seed: 456

## 結果

- val  mAP=0.7190 / AP_rare=0.7717 / AP_common=0.7102

## 収束

- 最良 epoch: 12（val mAP 0.719278）
- 学習率の低下: epoch 11
- 打ち切り: epoch 16
- 観測した epoch 数: 17

## 処方

凍結源 `s0_016` と**学習の長さの決め方だけ**が違う（fp16・実効バッチ 4・lr 1e-4・`presets.detr` は同一。上限 36、停滞 4 でlr を 0.1 倍、再停滞で打ち切り）。
違うのは折りの注釈と seed と初期化だけである。所要 11:12:39。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

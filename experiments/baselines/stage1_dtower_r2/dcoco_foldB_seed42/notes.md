# dcoco_foldB_seed42

契約: T-2026-09-19-stage1-detector-towers-r2
塔: D*-COCO / 折り: B / seed: 42

## 結果

- val  mAP=0.4557 / AP_rare=0.5540 / AP_common=0.4378
- test mAP=0.4324 / AP_rare=0.5279 / AP_common=0.4177（**折りごとに一度だけ**評価）

## 収束

- 最良 epoch: 16（val mAP 0.455487）
- 学習率の低下: epoch 11
- 打ち切り: epoch 20
- 観測した epoch 数: 21

## 処方

凍結源 `s0_016` と**学習の長さの決め方だけ**が違う（fp16・実効バッチ 4・lr 1e-4・`presets.detr` は同一。上限 36、停滞 4 でlr を 0.1 倍、再停滞で打ち切り）。
違うのは折りの注釈と seed と初期化だけである。所要 14:06:25。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

# dimagenet_foldB_seed42

契約: T-2026-09-18-stage1-detector-towers
塔: D*-ImageNet / 折り: B / seed: 42

## 結果

- val  mAP=0.4084 / AP_rare=0.5130 / AP_common=0.3894
- test mAP=0.4064 / AP_rare=0.4889 / AP_common=0.3937（**折りごとに一度だけ**評価）

## 処方

凍結源 `s0_016` と**同一**（fp16・12 epoch・実効バッチ 4・lr 1e-4・`presets.detr`）。
違うのは折りの注釈と seed と初期化だけである。所要 8:01:44。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

# dimagenet_foldA_seed123

契約: T-2026-09-18-stage1-detector-towers
塔: D*-ImageNet / 折り: A / seed: 123

## 結果

- val  mAP=0.6774 / AP_rare=0.7411 / AP_common=0.6668

## 処方

凍結源 `s0_016` と**同一**（fp16・12 epoch・実効バッチ 4・lr 1e-4・`presets.detr`）。
違うのは折りの注釈と seed と初期化だけである。所要 7:52:28。

## 評価

NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均
（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。

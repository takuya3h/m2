# S4 phase baseline (frozen Relation-DETR + causal TeCNO)

凍結源: Relation-DETR seed42 完走 ckpt（Stage1 GAP 2048-d をキャッシュ）。
online/causal（未来フレーム不使用）。S4 は結合手法から検出を引いたもの＝単独最適化しない。

## 結果（best @epoch 39）
- accuracy=0.9102 / macro_f1=0.7140
- edit=48.67 / seg_f1@10/25/50=0.57/0.54/0.50

## 構成
- seed=42 epochs=50 lr=0.0005 stages=2 layers=8 f_maps=64
- server=lecun / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)

## 次
- Δ_phase =（結合手法 − この S4）。同一土台（凍結backbone/特徴/recipe/seed）で比較する。

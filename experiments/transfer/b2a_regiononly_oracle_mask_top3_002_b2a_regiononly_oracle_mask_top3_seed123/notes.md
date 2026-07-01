# B2a 片方向結合 検出→工程（Tier-0 必須・①信号レベル）

凍結 Relation-DETR seed42 の tool-presence 信号（15-d）を GAP(2048) に入力連結 → 素 causal TeCNO。
①は勾配を交差させず信号のみ渡す（②B1 と対比）。online/causal（未来不使用）。

## 結果（best @epoch 18）
- accuracy=0.8845 / macro_f1=0.6693
- edit=57.05 / seg_f1@10/25/50=0.67/0.64/0.64

## 構成
- seed=123 epochs=50 lr=0.0005 in_dim=2063(=2048+15) stages=2 layers=8 f_maps=64
- server=lecun / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)

## Δ
- Δ_phase = (B2a − S4 base 0.8986±0.0034)。同一土台（凍結backbone/GAP/recipe/seed・neck無し）。
- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。

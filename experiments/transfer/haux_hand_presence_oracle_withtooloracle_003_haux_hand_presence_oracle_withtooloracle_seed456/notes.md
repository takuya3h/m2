# STEP D-aux 系統① 手情報→工程（det→phase・①信号レベル）

手特徴 `presence`（4-d, source=oracle）を GAP(2048) に入力連結 → 素 causal TeCNO。①は勾配を交差させず信号のみ渡す。online/causal。
H-6: tool-presence 15-d 併用（source=oracle）。

## 結果（best @epoch 48）
- accuracy=0.9584 / macro_f1=0.8254
- edit=55.52 / seg_f1@10/25/50=0.68/0.68/0.64

## 構成
- seed=456 epochs=50 lr=0.0005 in_dim=2067 stages=2 layers=8 f_maps=64
- server=efros / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)

## Δ
- Δ_phase = (H-aux − S4 base 0.8986±0.0028)。同一土台（凍結backbone/GAP/recipe/seed・neck無し）。
- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。

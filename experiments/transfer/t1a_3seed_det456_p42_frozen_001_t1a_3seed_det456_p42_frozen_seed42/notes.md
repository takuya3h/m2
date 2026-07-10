# T1a region-token→工程（Tier-1 主力⭐ TAPIS/GraSP 型・②系統）

凍結 Relation-DETR seed42 の object-query 埋め込み（クラス別 256-d, score 加重）を GAP(2048) に入力 → 素 causal TeCNO。
勾配は交差させず凍結 region token を渡す。online/causal（未来不使用）。

## 結果（best @epoch 25）
- accuracy=0.9518 / macro_f1=0.8104
- edit=34.39 / seg_f1@10/25/50=0.45/0.44/0.38

## 構成
- seed=42 epochs=50 lr=0.0005 in_dim=5888(=2048+3840) stages=2 layers=8 f_maps=64
- server=efros / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)

## Δ
- Δ_phase = (T1a − S4 base 0.8986±0.0034[lecun])。同一土台（凍結backbone/GAP/recipe/seed・neck無）。
- **別サーバー実行時**: 分母は lecun 値流用、サーバー差を §8.0 明文化。
- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。

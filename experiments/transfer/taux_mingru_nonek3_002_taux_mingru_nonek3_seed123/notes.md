# T-aux 系統② region-token→工程 時系列軸スイープ（T-1〜6）

凍結 Relation-DETR seed42 の object-query 埋め込み（クラス別 256-d, score 加重）を主入力に、工程認識の時系列軸のみを振る。GAP(2048) は常に生、時間加工は注入信号（target=region）にのみ適用。online/causal（未来不使用・先頭は複製 pad）。

- temporal_kernel = **mingru**（tecno=causal dilated TCN / mingru=線形再帰 / mamba=選択的 SSM）
- temporal_feature = **none**（k=3; movavg=移動平均 / delta=差分 / window=stack×k / none=生）

## 公平比較（交絡回避・§6 / §8.1）
- 問いB（核比較）: **temporal_feature=none 固定**で kernel だけを変える。
- 問いA（時間加工）: **temporal_kernel=tecno 固定**で temporal_feature だけを変える。
- 両者を同時に動かして「核 × 時間加工」を交絡させない。GAP は常に生・neck 無し。

## 結果（best @epoch 30）
- accuracy=0.9492 / macro_f1=0.7998
- edit=78.00 / seg_f1@10/25/50=0.79/0.79/0.78

## 構成
- seed=123 epochs=50 lr=0.0005 in_dim=5888 stages=2 layers=8 f_maps=64 region_only=False add_toolpresence=False
- server=efros / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)

## Δ
- Δ_phase = (T-aux − S4 base 0.8986±0.0028[lecun])。同一土台（凍結backbone/GAP/recipe/seed・neck無）。
- **別サーバー実行時**: 分母は lecun 値流用、サーバー差を §8.0 明文化。
- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。

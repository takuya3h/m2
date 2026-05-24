# s3_006_phase_frame_seed456

## 仮説
S2 までの検出器とは独立に、frozen ResNet50（ImageNet）特徴を入力とする
PhaseHead で 9 クラス工程認識を学習する。検出器に手を加えないため
判定 #2（tool mAP の劣化 ≈ 0）は構造的に達成される。

## 実験設定
- Backbone（凍結）: torchvision ResNet50 / ImageNet 事前学習
- PhaseHead: 2048 -> 512 -> 9, dropout=0.3
- Loss: class-weighted CE + label smoothing
- Optimizer: AdamW lr=0.0e+00
- Epochs: 5, batch=32, seed=456

## 結果 (val)
- best epoch=5: accuracy=0.6020
- macro F1=0.2980, edit=4.92, seg_F1@10=0.071
- train_loss 推移: e1=1.390, e2=1.120, e3=1.031, e4=0.985, e5=0.969
参照 tool mAP の S2 ファイルが未提供 — S2 完了後に追記する。

## 解釈
phase_loss が epoch とともに減少 → 弱ベースラインとしてパイプライン動作を確認。
上位指標（edit / seg F1）は frame-by-frame の単純設計のため高くないことを許容。
S4 で時系列モデル（TCN / Transformer）へ置き換える際の比較基準として使う。

## 次の行動
1. S4 で frame-level baseline と temporal baseline の Δ を /delta で集計する。

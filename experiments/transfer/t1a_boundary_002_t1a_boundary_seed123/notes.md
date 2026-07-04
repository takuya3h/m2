# T1a-Boundary（region-token→工程 + 因果 boundary head・over-seg / edit-score 改善）

STEP C 改善提案書 §4.1/§8。T1a base の共有 stage-1 trunk から class-agnostic boundary head を分岐し、phase-change 教師（±1）で BCE 監督。online/causal（未来不使用）。

## 結果（best @epoch 30・val）
### plain decode（per-frame argmax = T1a base と同一推論）
- accuracy=0.9452 / macro_f1=0.7980
- edit=33.24 / seg_f1@10/25/50=0.427/0.427/0.396
### sticky decode（因果 boundary-gated・τ=0.5）
- accuracy=0.6449 / macro_f1=0.6124
- edit=49.00 / seg_f1@10/25/50=0.553/0.537/0.471

## 構成
- seed=123 epochs=50 lr=0.0005 in_dim=5888(=2048+3840) stages=2 layers=8 f_maps=64
- boundary: weight=1.0 pos_weight=14.70 dilate=1 tau=0.5
- server=efros / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)

## Δ
- Δ = (T1a-Boundary − T1a base[同env efros])。主指標 edit/seg-F1、維持 acc/macro-F1。
- 3-seed 揃ったら paired-σ(対seed差) §10.1 判定。plain=trunk 正則化 / sticky=+因果 decode。

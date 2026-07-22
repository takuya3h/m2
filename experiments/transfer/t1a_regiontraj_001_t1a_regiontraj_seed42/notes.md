# T1a-RegionTrajectory（Temporal Object-Set Fusion・COUPLING §4.1）

region-token(15×256) を Set encoder（共有MLP+class埋め込み+attention pool）で集約→tool-presence と gated residual→causal temporal attention→TeCNO+boundary head。online/causal。

## 結果（best @epoch 31・val）
### plain decode
- acc=0.9459 / macro_f1=0.8089
- edit=40.41 / seg_f1@10/25/50=0.536/0.528/0.471
### sticky decode（τ=0.5）
- acc=0.9327 / macro_f1=0.7922
- edit=49.85 / seg_f1@10/25/50=0.585/0.573/0.476

## 構成
- seed=42 epochs=50 lr=0.0005 d_model=256 tok_dim=128 pres_dim=64 stages=2 layers=8
- set_encoder=on gated_residual=True temporal_attn=True boundary(w=1.0 pos_w=14.70 tau=0.5)
- server=efros / recipe=online_causal+jaccard_strict

## Δ
- Δ=(RegionTraj − T1a base[同env efros])。主指標 edit/seg-F1、維持 acc/macro-F1。3-seed paired-σ §10.1。

# s0_013_sensex_codino_bbox_seed42 — 環境統一のため中止 (ABORTED)

**ステータス: 中止 (completed ではない)。Δ 基準点・検出器ベンチマークから除外する。**

## 中止の経緯と理由（研究インテグリティのため明記）

- 中止日時: 2026-05-29（aolab/philip サーバー, RTX 6000 Ada ×2）
- 対象: Sense-X 版 Co-DETR（CoDINO 5-scale **9-encoder** LSJ R50）の EgoSurgery 適応学習。
- **中止理由: 実験環境の統一（再現性確保）のため。**
  - 本実験のみ専用 venv `.venv-mmdet2`（**torch 1.13.1+cu117 / mmcv-full 1.7.0 / mmdet 2.25.3 / Python 3.8**）を要し、
    プロジェクト本体 `.venv`（**torch 2.1.2+cu118 / mmdet 3.3.0 / Python 3.11**）と torch/CUDA/Python が異質だった。
  - 原因: Sense-X 9-encoder LSJ の公式実装は mmcv-full 1.x API 前提で、torch 2.1 では CUDA 拡張をビルドできない。
  - 検出器ベンチマーク（S0）は全検出器を可能な限り同一環境で比較すべきという方針（CLAUDE.md / 再現性要件）に基づき、
    本実験（9-encoder 版・異環境）を**中止**し、Co-DETR は **mmdet 3.x 同梱版（s0_007-009、本体 .venv, torch 2.1）で代表**させる。

## 中止時点の途中結果（参考。ベンチマークには使わない）

- 到達: epoch 8 の train 途中（iter 950/2415）で停止。resume(epoch4起点) 込み。epoch8 の val 評価は未実施。
- val bbox_mAP 履歴（評価済み epoch1-7 のみ。実ログ `*.log.json` より）:
  e1=0.590 / e2=0.640 / e3=0.661 / e4=0.686 / e5=0.687 / e6=0.675 / e7=0.696（best）
- これらは **12 epoch 未完・異環境**のため、最終比較値としては採用しない。
- 学習ログ（証跡）: `/tmp/sensex_codino_work_seed42/`（epoch_3/4/5/.. の .pth と .log.json）。

## 影響

- s0_013 / s0_014 / s0_015（Sense-X 9enc 3 seed）は**実施しない**。採番は欠番として残す（後続の採番ずれ防止）。
- Co-DETR の S0 代表は s0_007-009（mmdet 3.x 同梱、torch 2.1、本体 .venv）。
- 他の追加検出器（Stable-DINO / DI-MaskDINO / Relation-DETR）は **torch 2.1.2+cu118 が本体と同一**で、
  framework 隔離のための venv 分離は再現性に影響しないため、現状の venv 分離のまま実施する。

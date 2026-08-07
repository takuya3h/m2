# s0_040_wiring_verification_seed42

作成日時: 2026-08-07T21:17:04+00:00

## この run は何か

**配線の確認を目的とした run である。研究上の測定ではない。**

契約 `T-2026-08-09-run-wiring-verification` に基づき、次の 3 つが動くことを確かめるために
実行した。

1. 学習の完了時に `ExperimentManager.finalize()` から自動同期が発火するか
2. 配備鍵での遠隔操作が成立するか
3. 契約の識別子が生成物へ刻まれ、索引まで到達するか

対応する契約の識別子は `config.yaml` の `task_id` に記録してある。

## この run を何に使ってはならないか

- **性能の主張に使ってはならない。** 学習量が極小である（画像 16 枚・1 epoch・
  backbone 凍結・内蔵 `SimpleDetectionHead`）。下記の指標は配線が通ったことの副産物であり、
  検出性能を表さない。
- **基準点・分母として使ってはならない。** 本 run は対照実験の宣言を持たない
  （`config.yaml` に `delta` の宣言が無く、索引でも `arm=unknown` /
  `control_of` は空 / `pairing_provenance=not_determinable`）。
- **他の S0 系 run と束ねてはならない。** `description` を `wiring_verification` と
  したのは、`experiment_id` を既存の S0 基準点群から分離するためである。

## 実験設定

- Category: baselines
- Step: s0
- Seed: 42
- Config: `config.yaml` を参照
- 起動コマンド: `command.sh` を参照
- 学習量: `data.limit=16` / `train.epochs=1` / `data.img_size=224` /
  `train.freeze_backbone=true` / `model.backbone=dinov2_vits14_reg` /
  `train.real_detector=false`
- 追跡: `logging.wandb_enabled=false`（本 run では追跡を無効にした）

## 実行環境

- 実行ホスト: lecun（`server.txt`）
- 演算装置: 装置 1（NVIDIA RTX A6000, UUID `GPU-8f99ff6b-7241-ba0b-9137-879990b50906`）。
  `CUDA_VISIBLE_DEVICES=1` で固定した。装置 0 は他の利用者が使用中のため使っていない。
- 仮想環境: `.venv`（`torch 2.1.2+cu118` / `cuda_available True` で起動時に記録）
- 所要時間: 2026-08-07 21:17:01 開始 → 21:17:16 終了。**15 秒**

## 結果（`metrics.json` からの転記）

計算し直していない。`metrics.json` の値をそのまま写している。

- `epoch`: 1
- `mAP`: 0.0002771509158176216
- `val/mAP`: 0.0002771509158176216
- `val/mAP_50`: 0.0018654517471083272
- `val/mAP_75`: 7.072135785007073e-05
- `val/AP_rare`: 0.001940056410723351
- `val/AP_common`: 0.0

クラス別（`per_class_ap.json` からの転記）は `Skewer` が 0.003880112821446702 で、
残る 14 クラスはすべて 0.0 である。

配線の確認としての結果は、契約の記録 `tasks/T-2026-08-09-run-wiring-verification/RESULT.md`
に記載してある。自動同期は発火し、この run の証跡は commit `25ea5ef` として自動で
記録・送出された。

## 解釈

**解釈しない。** 上記の指標は配線の確認に伴って生成された値であり、
学習量が極小であるため検出性能を表さない。この run から検出性能に関する結論を
導いてはならない。

## 次の行動

本 run の後始末（索引に残すか、除外規則を足すか）は契約
`T-2026-08-09-wiring-followup-and-integration` で扱う。

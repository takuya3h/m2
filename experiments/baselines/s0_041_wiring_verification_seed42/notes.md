# s0_041_wiring_verification_seed42

作成日時: 2026-08-08T04:40:36+00:00

## この run は何か

**配線の再現確認を目的とした run である。研究上の測定ではない。**

契約 `T-2026-08-10-third-host-verification` に基づき、三台目のホスト bengio で次を確認するために実行した。

1. 最小学習が完走し、契約の識別子を含む成果物が生成されるか
2. 学習完了時に `ExperimentManager.finalize()` から自動同期が発火するか
3. 通常の SSH 鍵経路で自動送出が成立するか

対応する契約の識別子は `config.yaml` の `task_id` に記録してある。

## この run を何に使ってはならないか

- **性能の主張に使ってはならない。** 学習量が極小である（画像16枚・1 epoch・backbone凍結・内蔵 `SimpleDetectionHead`）。下記の指標は配線が通ったことの副産物であり、検出性能を表さない。
- **基準点・分母として使ってはならない。** 本 run は対照実験の宣言を持たない（`config.yaml` に `delta` の宣言が無く、索引上の比較群として扱わない）。
- **他の S0 系 run と束ねてはならない。** `description` を `wiring_verification` とし、既存の S0 基準点群から分離した。

## 実験設定

- Category: baselines
- Step: s0
- Seed: 42
- Config: `config.yaml` を参照
- 起動コマンド: `command.sh` を参照
- 学習量: `data.limit=16` / `train.epochs=1` / `data.img_size=224` / `train.freeze_backbone=true` / `model.backbone=dinov2_vits14_reg` / `train.real_detector=false`
- 追跡: `logging.wandb_enabled=false`（前例と同条件の配線確認用 run）

## 実行環境

- 実行ホスト: bengio（`server.txt`）
- 演算装置: GPU 0（NVIDIA RTX A6000、UUID `GPU-1b153400-9ec9-25fe-d601-7ddc39431aad`）。起動直前は 35 MiB / 49140 MiB、計算プロセス0件。`CUDA_VISIBLE_DEVICES=0` で固定した。
- 仮想環境: `.venv`（`torch 2.1.2+cu118`）
- 所要時間: 2026-08-08 04:40:34Z 開始 → 04:40:46Z 終了。**12秒**

## 結果（`metrics.json` からの転記）

計算し直していない。`metrics.json` の値をそのまま転記した。

- `epoch`: 1
- `mAP`: 4.98194465959574e-05
- `val/mAP`: 4.98194465959574e-05
- `val/mAP_50`: 0.0003802961261577104
- `val/mAP_75`: 5.277713272393338e-06
- `val/AP_rare`: 0.0003487361261717018
- `val/AP_common`: 0.0

`per_class_ap.json` では `Skewer` が 0.0006974722523434036、残る14クラスはすべて 0.0 だった。

自動同期は commit `5f7e255` を生成し、`origin/exp/Bengio-wip-20260703` へ送出された。測定時点の遠隔との差は0、open PRは0件だった。

## 解釈

**性能は解釈しない。** 上記指標は極小の配線確認に伴って生成された値であり、検出性能に関する結論を導いてはならない。

## 次の行動

本 run を含めて索引を再生成し、退避物を含まない正本候補としての性質を契約 `T-2026-08-10-third-host-verification` で検証する。

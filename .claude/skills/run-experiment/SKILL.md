---
name: run-experiment
description: egosurgery_multitask の S0〜S9 ステージ実験を起動・監視・記録する手順。学習を回す、run_sX.sh を実行する、smoke で疎通確認する、長時間 GPU ジョブを管理するときに使う。
---

# ステージ実験の実行手順

egosurgery_multitask の実験を、再現性と研究インテグリティを保って実行する手順。

## 1. 事前確認

- `.venv` を有効化（`source .venv/bin/activate` か `.venv/bin/python` 明示）。
- `torch.cuda.is_available()` が True か確認（`/env-check` コマンドが使える）。
- ステージ config（`configs/stage/sX_*.yaml`）と `configs/default.yaml` を把握。

## 2. まず smoke で疎通確認

未確認の構成は、本実行前に小構成で落ちないことを確認する:

```bash
PYTHONPATH=src .venv/bin/python -m egosurgery.train \
  stage=<stage> seed=42 \
  model.backbone=dinov2_vits14_reg data.img_size=224 data.limit=16 \
  data.batch_size=2 data.num_workers=0 train.epochs=1 \
  train.freeze_backbone=true logging.wandb_enabled=false
```

`scripts/run_sX.sh` は環境変数 `S0_EXTRA_ARGS` で同様の override を一括適用できる。

## 3. 本実行

- 3 seeds（42 / 123 / 456）で回す。Δ 基準点の汚染防止のため optimizer / seed /
  scheduler / augmentation / batch size を S0〜S9 で揃える。
- 画像サイズは patch_size 14 の倍数（224 / 336 / 392 / 518）。
- 長時間ジョブは **`run_in_background: true` で起動**し、Monitor で進捗
  （`[S0][epoch`）と失敗（`Traceback|Error|CUDA out of memory|Killed`）を監視する。

## 4. 完了後

- `experiments/{category}/{step}_{NNN}_{desc}_seed{seed}/` に証拠ファイル
  （config.yaml / command.sh / git_commit.txt / metrics.json / per_class_ap.json /
  notes.md / confusion_matrix.npy）が揃っているか確認。
- `notes.md` に結果・解釈を、`docs/experiment_log.md` に「仮説→実験→結果→解釈→次」を追記。
- 複数 seed が揃ったら `/delta` で Δ と 1σ 有意性を確認。

## 厳守

**mAP 等の数値を捏造しない。** 未収束・失敗・環境制約による未達は、実測値と理由を
そのまま報告する。`StageATrainer` は外部検出器（Mask DINO / VarifocalNet）が
使えない環境では内蔵 `SimpleDetectionHead` にフォールバックする — その旨も明記する。

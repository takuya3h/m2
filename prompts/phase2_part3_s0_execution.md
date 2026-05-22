# フェーズ II — Part 3/5: S0 評価指標 + Stage A トレーナー + 実行スクリプト

前提: Part 1（データパイプライン）と Part 2（backbone + 検出ヘッド + 損失関数）が完了済み。

Part 3 では **S0 の評価指標**、**Stage A トレーナー**、**実行スクリプト** を実装し、S0 を完走させる。
Part 3 の完了 = S0 の完了 = §2.5(a) 基準点の確立。

---

## 1. 評価指標

### 1.1 `src/egosurgery/metrics/detection.py`

```python
"""
COCO mAP ベースの検出評価指標。

使い方:
    evaluator = DetectionEvaluator(
        ann_file="data/annotations/egosurgery_tool/instances_val.json",
        tool_classes=TOOL_CLASSES,
        rare_classes=["Skewer", "Syringe", "Forceps"],
        similar_pairs=["Forceps", "Tweezers", "Needle_Holders", "Bipolar_Forceps"],
    )
    evaluator.update(predictions, image_ids)
    results = evaluator.compute()
    # results: {
    #   "mAP": float,
    #   "mAP_50": float,
    #   "mAP_75": float,
    #   "AP_rare": float,     # Skewer, Syringe, Forceps の平均 AP
    #   "AP_common": float,   # 残り 12 クラスの平均 AP
    #   "per_class_ap": {"Tweezers": float, "Skewer": float, ...},  # 15 クラス全部
    #   "confusion_matrix_similar": np.ndarray,  # (4, 4) 形状類似ペア
    # }
"""
```

実装要件:
- pycocotools の `COCOeval` を使って COCO mAP を計算
- per-class AP: `COCOeval` の `eval["precision"]` から各カテゴリの AP を抽出
- AP_rare / AP_common: `rare_classes` に含まれるクラスとそれ以外を分離して平均
- confusion_matrix_similar: 形状類似ペア (Forceps, Tweezers, Needle_Holders, Bipolar_Forceps) の 4×4 混同行列
  - 各予測について GT とのクラスマッチングを行い、誤分類パターンを集計
  - `numpy.ndarray` で返し、`visualizations/confusion_matrix.npy` に保存可能にする
- 全結果を `dict` で返し、`ExperimentManager.log_metrics()` と `log_per_class_ap()` に直接渡せる形式

### 1.2 `src/egosurgery/metrics/confusion_matrix.py`

```python
"""
形状類似ペアの sub-confusion matrix を計算・可視化。

使い方:
    cm = compute_similar_pair_confusion(predictions, gt_labels, pair_classes)
    save_confusion_matrix(cm, pair_classes, save_path)
    # → visualizations/confusion_matrix.png に保存
"""
```

実装要件:
- 予測ラベルと GT ラベルから、指定クラス群の confusion matrix を計算
- matplotlib で heatmap を生成して保存
- 正規化（行方向 = recall、列方向 = precision）の両バージョンを出力

---

## 2. Stage A トレーナー

### 2.1 `src/egosurgery/engines/stage_a_trainer.py`

```python
"""
Stage A0 専用トレーナー: bbox 検出のみ（Phase-0 主経路）。

使い方:
    trainer = StageATrainer(cfg)
    trainer.setup()
    trainer.run()

内部動作:
    1. setup(): backbone + detection_head + optimizer + scheduler + dataloader を構築
    2. run(): 全 epoch を回し、各 epoch 後に evaluate() → checkpoint 保存 → metrics 記録
    3. evaluate(): COCO mAP + per-class AP + confusion matrix を計算

ExperimentManager / ExperimentLogger / CheckpointManager との統合:
    - setup() で ExperimentManager.setup() を呼び、実験フォルダを自動生成
    - 各 epoch で logger.log() で W&B に記録
    - evaluate() で metrics を experiment_manager.log_metrics() に保存
    - best model は checkpoint_manager.save_best() で保存
"""
```

実装要件:
- `__init__(self, cfg: DictConfig)`: config を受け取る
- `setup()`:
  1. `seed_everything(cfg.seed)`
  2. `ExperimentManager` を作成して `setup()` → 実験フォルダ生成
  3. `ExperimentLogger` を作成して `init()` → W&B 初期化
  4. `CheckpointManager` を作成
  5. `experiment_manager.save_config(cfg)` → config.yaml 保存
  6. `build_model(cfg)` → backbone + detection_head
  7. `EgoSurgeryDataModule(cfg)` → train/val DataLoader
  8. optimizer: AdamW (lr=1e-4, weight_decay=0.05)
  9. scheduler: CosineAnnealingLR with warmup (5 epochs)
  10. AMP: `torch.amp.GradScaler('cuda')` + `autocast(dtype=torch.bfloat16)`

- `train_one_epoch(epoch)`:
  1. model.train()
  2. train_loader を iterate し、forward → loss → backward → step
  3. gradient clipping (max_norm=1.0)
  4. logger.log({"train/loss": ..., "train/loss_ce": ..., "train/loss_bbox": ..., "epoch": epoch})

- `evaluate(epoch) -> dict`:
  1. model.eval()
  2. val_loader を iterate し、predict → 予測結果を蓄積
  3. `DetectionEvaluator.compute()` で全指標を計算
  4. confusion matrix を `visualizations/` に保存
  5. logger.log({"val/mAP": ..., "val/AP_rare": ..., "val/AP_common": ...})
  6. experiment_manager.log_metrics(results)
  7. experiment_manager.log_per_class_ap(results["per_class_ap"])
  8. return results

- `run()`:
  1. epoch ループ: train_one_epoch → evaluate → checkpoint 保存
  2. 最終 epoch 後に best metrics の summary を出力
  3. logger.finish()

- **Mask DINO と VarifocalNet の両方に対応**:
  - Mask DINO: Detectron2 の学習ループをラップ（Detectron2 の DefaultTrainer は使わず、自前ループから呼ぶ）
  - VarifocalNet: mmdet のモデルを自前ループから呼ぶ（mmdet の Runner は使わない）
  - 両方とも `forward(images, targets) -> loss_dict` のインターフェースに統一する

### 2.2 `src/egosurgery/train.py` の更新

既存の Hydra エントリーポイントを更新し、Stage A トレーナーを呼び出すようにする:

```python
@hydra.main(version_base=None, config_path="../../configs", config_name="default")
def main(cfg: DictConfig) -> None:
    # stage config に応じてトレーナーを選択
    if cfg.experiment.step.startswith("s0") or cfg.experiment.step.startswith("s1") or cfg.experiment.step.startswith("s2"):
        from egosurgery.engines.stage_a_trainer import StageATrainer
        trainer = StageATrainer(cfg)
    else:
        from egosurgery.engines.trainer import Trainer
        trainer = Trainer(cfg)  # ダミートレーナー（フォールバック）

    trainer.setup()
    trainer.run()
```

---

## 3. Config ファイル

### 3.1 `configs/stage/s0_tool_baseline.yaml` を更新

```yaml
# S0: 術具検出ベースライン — §2.5(a) 基準点

experiment:
  category: "baselines"
  step: "s0"
  description: "tool_baseline"

model:
  num_classes: 15
  backbone: dinov2_vitl14_reg
  detection_head: mask_dino   # run_s0.sh で varifocanet に切り替えて並走

train:
  epochs: 100
  batch_size: 4
  num_workers: 8
  amp: true
  gradient_checkpoint: true
  grad_clip_norm: 1.0

optimizer:
  name: "adamw"
  lr: 0.0001
  weight_decay: 0.05

scheduler:
  name: "cosine"
  warmup_epochs: 5

# 長尾対策
longtail:
  seesaw_loss: true
  seesaw_p: 0.8
  seesaw_q: 2.0
  rfs: true
  rfs_thresh: 0.001
  copypaste: true
  copypaste_prob: 0.5
  logit_adjustment: true
  logit_adjustment_tau: 1.0

# S0 固有: Phase head なし、双方向なし
feedback:
  phase_to_det: false
  det_to_phase: false

relation:
  enabled: false

exo:
  enabled: false

# データ
data:
  ann_file_train: "data/annotations/egosurgery_tool/instances_train.json"
  ann_file_val: "data/annotations/egosurgery_tool/instances_val.json"
  img_dir_train: "data/raw/ego/train/"
  img_dir_val: "data/raw/ego/val/"
  copypaste_bank: "data/processed/copypaste_bank/"

logging:
  wandb_project: "egosurgery_multitask"
  wandb_enabled: true
  save_top_k: 3

eval:
  num_seeds: 3
```

---

## 4. 実行スクリプト

### 4.1 `scripts/run_s0.sh`

```bash
#!/bin/bash
# S0: 術具検出ベースライン — §2.5(a) 基準点
# 3 seeds × 2 モデル (Mask DINO, VarifocalNet) = 6 実験

set -euo pipefail

SEEDS=(42 123 456)

echo "=== S0: Tool detection baseline ==="
echo "Goal: Establish §2.5(a) baseline. Must beat VarifocalNet SOTA mAP 45.8"

# --- Mask DINO × 3 seeds ---
for SEED in "${SEEDS[@]}"; do
    echo "--- Mask DINO, seed=${SEED} ---"
    PYTHONPATH=src python -m egosurgery.train \
        stage=s0_tool_baseline \
        model.detection_head=mask_dino \
        seed=${SEED} \
        experiment.description="maskdino_bbox" \
        logging.wandb_enabled=true
done

# --- VarifocalNet × 3 seeds ---
for SEED in "${SEEDS[@]}"; do
    echo "--- VarifocalNet, seed=${SEED} ---"
    PYTHONPATH=src python -m egosurgery.train \
        stage=s0_tool_baseline \
        model.detection_head=varifocanet \
        seed=${SEED} \
        experiment.description="varifocanet_bbox" \
        logging.wandb_enabled=true
done

echo "=== S0 completed ==="
echo "Check: experiments/baselines/s0_001_* ~ s0_006_*"
echo "Judgment #6: Compare Mask DINO vs VarifocalNet APr. If diff > 3pt, consider Co-DETR."
```

---

## 5. テスト

`tests/test_metrics.py` に以下を追加:

1. `test_detection_evaluator_basic`: ダミーの predictions と gt で mAP が計算できること
2. `test_per_class_ap_15_classes`: per-class AP が 15 クラス全て含まれること
3. `test_ap_rare_common_split`: AP_rare と AP_common が正しく分離されること
4. `test_confusion_matrix_shape`: confusion_matrix_similar が (4, 4) であること

`tests/test_pipeline.py` に以下を追加:

5. `test_stage_a_trainer_setup`: StageATrainer が setup() でエラーなく初期化されること（ダミーデータ）
6. `test_stage_a_trainer_one_epoch`: 1 epoch の学習が完走すること（小データ）

---

## 6. 完了判定

1. `bash scripts/run_s0.sh` が全 6 実験を完走する
2. `experiments/baselines/` に `s0_001_maskdino_bbox_seed42/` 〜 `s0_006_varifocanet_bbox_seed456/` が存在する
3. 各実験フォルダに config.yaml / metrics.json / per_class_ap.json / notes.md / confusion_matrix.npy が存在する
4. VarifocalNet の mAP ≥ 45.8 (公式 SOTA 再現)
5. Mask DINO の mAP が計測されている
6. 15 クラスの per-class AP が記録されている
7. 3 seeds の平均±標準偏差が算出可能な状態になっている
8. W&B ダッシュボードに train/loss, val/mAP, val/AP_rare が記録されている
9. `pytest tests/ -v` が全テストパスする

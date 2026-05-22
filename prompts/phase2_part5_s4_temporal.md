# フェーズ II — Part 5/5: S4 長距離時系列モデル（§2.5(b) 基準点 + D-B 貢献）

前提: Part 4 まで完了し、S0〜S3 が完走済み。
S0 の基準点 (mAP ≥ 45.8) と S3 の Phase パイプラインが動作する状態。

Part 5 では **S4 の長距離時系列モデル** を実装し、工程認識の基準点を確立する。
これは §2.5(b) の基準点であると同時に、D-B（EgoSurgery-Phase 初の長距離ベンチマーク）の中核。

---

## 1. 概要

S4 は 2 段階で運用する:
- **第1波（本 Part で必須）**: TeCNO + SR-Mamba（causal / bidirectional）
- **第2波（余力があれば着手）**: HID-SSM, SKiT, Surgformer, SPRMamba

Phase head の入力は **画像 global feature**（backbone の [CLS] token）。
object token は S5 で導入するため、ここではまだ使わない。

---

## 2. 特徴量抽出

### 2.1 `scripts/extract_features.py`

```python
"""
S0〜S3 で学習した backbone (DINOv2 + LoRA) を使って
全フレームの [CLS] token 特徴量を抽出・保存する。

使い方:
    python scripts/extract_features.py \
        --checkpoint experiments/baselines/s0_001_.../checkpoints/best.pth \
        --data_dir data/raw/ego/ \
        --output_dir data/processed/features/ \
        --splits data/splits/

出力:
    data/processed/features/
    ├── train/
    │   ├── video_001.pkl    # {"features": ndarray (T, 1024), "frame_ids": list}
    │   ├── video_002.pkl
    │   └── ...
    ├── val/
    └── test/
"""
```

実装要件:
- S0 の best checkpoint から backbone 重み（DINOv2 + LoRA）を読み込む
- 全フレーム画像を forward pass し、[CLS] token (1024 dim) を抽出
- 動画単位で pickle に保存: `{"features": np.ndarray (T, 1024), "frame_ids": List[int]}`
- batch 処理（batch_size=32 程度）で高速化
- GPU メモリ節約: `torch.no_grad()` + `model.eval()`
- bf16 で推論し、保存は float32

---

## 3. 時系列データセット

### 3.1 `src/egosurgery/datasets/temporal_dataset.py`

```python
"""
時系列用データセット: 動画単位で特徴量列と Phase ラベル列を返す。

使い方:
    dataset = TemporalDataset(
        feature_dir="data/processed/features/train/",
        phase_ann_dir="data/annotations/egosurgery_phase/",
        split="train",
        max_seq_len=None,       # None=動画全長, int=サブシーケンスに分割
        overlap=0,              # サブシーケンス間のオーバーラップ
    )

    features, labels, video_id, mask = dataset[i]
    # features: Tensor (T, D) — D=1024 (DINOv2 [CLS] token dim)
    # labels: Tensor (T,) — Phase ラベル (0-8)
    # video_id: str
    # mask: Tensor (T,) — パディング領域は 0、有効領域は 1
"""
```

実装要件:
- `data/processed/features/{split}/{video_id}.pkl` から特徴量を読み込む
- 対応する Phase ラベルを `data/annotations/egosurgery_phase/` から読み込む
- 0.5 fps のため 1 動画あたり T は数千〜数万フレーム
- `max_seq_len` を指定した場合、動画を固定長のサブシーケンスに分割（学習時のメモリ管理）
- バッチ内で長さが異なる場合のパディング + mask を返す
- collate_fn を提供: 可変長テンソルのバッチ化

---

## 4. 時系列モデル

### 4.1 `src/egosurgery/models/temporal/tecno.py`（方式 B: 抽出）

```python
"""
TeCNO: Multi-Stage Temporal Convolutional Network for surgical phase recognition.

公式実装 (https://github.com/tobiascz/TeCNO, MIT License) からモデル定義を抽出。
学習ループは自プロジェクトの engines/ を使う。

参考: Czempiel+ MICCAI 2020
"TeCNO: Surgical Phase Recognition with Multi-Stage Temporal Convolutional Networks"

構成:
    - Stage 1: 1D causal dilated convolution (kernel=15, dilation=1,2,4,8,...,512)
    - Stage 2-4: dilated residual layers で Stage 1 の出力を refinement
    - 各 Stage 後に CE Loss を計算し、合計を返す

入力: (B, T, D) の特徴量列（D=1024, DINOv2 [CLS] token）
出力: List[(B, T, C)] — 各 Stage の予測（C=9, Phase 数）
"""

# =============================================================================
# Adapted from: https://github.com/tobiascz/TeCNO
# Original authors: Tobias Czempiel et al.
# License: MIT
# Modifications:
#   - 入力インターフェースを (B, T, D) に統一（元実装は特徴量 pkl 前提）
#   - config から構成を変更可能に（num_stages, num_layers, kernel_size）
#   - causal / non-causal を config で切り替え可能に
# =============================================================================
```

実装要件:
- `MultiStageTCN(input_dim, num_classes, num_stages=4, num_layers=10, num_features=64, kernel_size=15, causal=True)`
- 各 Stage は `DilatedResidualLayer` の積み重ね
- `DilatedResidualLayer`: Conv1d(causal padding) → ReLU → Conv1d → Residual
- dilation: 1, 2, 4, 8, ..., 2^(num_layers-1)
- causal padding: 入力の左側のみにゼロパディング（未来の情報を使わない）
- `forward(x, mask=None) -> List[Tensor]`: 各 Stage の logits (B, T, C) のリストを返す
- 損失計算は外部（`temporal.py` の `MultiStageLoss`）で行う

### 4.2 `src/egosurgery/models/temporal/sr_mamba.py`（方式 B+C: 抽出 + pip）

```python
"""
SR-Mamba: Surgical Phase Recognition with bidirectional Mamba decoder.

公式実装 (https://github.com/rcao-hk/SR-Mamba) から decoder 部を抽出。
基本 Mamba 層は pip install mamba-ssm で使用。

参考: Cao+ MICCAI 2024
"SR-Mamba: Effective Surgical Phase Recognition with State Space Model"

構成:
    - Spatial encoder は使わない（特徴量は DINOv2 [CLS] token を使用）
    - Bidirectional Mamba decoder:
        - Forward Mamba: 時間方向に順方向 scan
        - Backward Mamba: 時間方向に逆方向 scan
        - Fusion: 両方向の出力を結合 → Linear → Phase logits
    - Single-step training（backbone + decoder の同時最適化を可能にするが、
      S4 では backbone を凍結して decoder だけ学習する）

入力: (B, T, D) の特徴量列（D=1024）
出力: (B, T, C) の Phase logits（C=9）
"""

# =============================================================================
# Adapted from: https://github.com/rcao-hk/SR-Mamba
# Original authors: Rui Cao, Jiangliu Wang, Yun-Hui Liu
# License: MIT
# Modifications:
#   - 空間エンコーダを除去（DINOv2 [CLS] token を直接入力）
#   - config から bidirectional / causal を切り替え可能に
#   - from mamba_ssm import Mamba で基本 Mamba 層を使用
# =============================================================================
```

実装要件:
- `SRMambaDecoder(input_dim, num_classes, d_model=256, d_state=16, d_conv=4, expand=2, num_layers=4, bidirectional=True)`
- 入力射影: `Linear(input_dim, d_model)`
- Forward/Backward Mamba: `Mamba(d_model, d_state, d_conv, expand)` を `num_layers` 個積み重ね
- bidirectional の場合: forward + backward を concat → `Linear(2*d_model, d_model)`
- causal の場合: forward のみ
- 出力射影: `Linear(d_model, num_classes)`
- `forward(x, mask=None) -> Tensor`: (B, T, C) の logits を返す
- Anticipation loss（optional）: 数フレーム先の Phase を予測する補助損失

---

## 5. 損失関数

### 5.1 `src/egosurgery/models/losses/temporal.py`

```python
"""
時系列用損失関数。

- MultiStageLoss: TeCNO の各 Stage の CE loss を集約
- TemporalSmoothingLoss: 隣接フレームの予測一貫性
- TransitionLoss: impossible-transition penalty
"""
```

実装要件:
- `MultiStageLoss(num_stages, weights=None)`:
  - 各 Stage の CE loss に重みを掛けて合計
  - デフォルト重み: 全 Stage 等重み (1/num_stages)
  - `forward(stage_predictions: List[Tensor], targets: Tensor, mask: Tensor) -> Tensor`

- `TemporalSmoothingLoss(lambda_smooth=0.15)`:
  - `|log(p_t) - log(p_{t-1})|^2` の平均
  - MS-TCN の TMSE (Truncated Mean Squared Error) を採用
  - truncation threshold τ=4 で clip

- `TransitionLoss(transition_matrix=None)`:
  - 工程間の遷移確率行列から、ありえない遷移にペナルティ
  - 例: Preparation → Closure は通常ありえない
  - `transition_matrix` は EgoSurgery-Phase の学習データから事前計算
  - `forward(predictions, targets) -> Tensor`

---

## 6. エンジン

### 6.1 `src/egosurgery/engines/trainer.py` を拡張

S4 用の時系列学習ループを追加:

```python
# train.py の stage 分岐に追加
if cfg.experiment.step.startswith("s4"):
    from egosurgery.engines.temporal_trainer import TemporalTrainer
    trainer = TemporalTrainer(cfg)
```

### 6.2 `src/egosurgery/engines/temporal_trainer.py`（★新規追加、空ファイルではない）

```python
"""
時系列モデル用トレーナー。

2フェーズの学習:
    1. 特徴量抽出: backbone (frozen) で全フレームの [CLS] token を抽出
    2. 時系列モデル学習: 抽出済み特徴量 → TeCNO / SR-Mamba → Phase 予測

使い方:
    trainer = TemporalTrainer(cfg)
    trainer.setup()
    trainer.run()
"""
```

実装要件:
- `setup()`:
  1. seed_everything
  2. ExperimentManager.setup()
  3. 特徴量が未抽出なら `scripts/extract_features.py` を呼ぶ（subprocess）
  4. TemporalDataset + DataLoader 構築
  5. 時系列モデル構築 (TeCNO or SRMambaDecoder)
  6. optimizer / scheduler 構築
- `train_one_epoch()`:
  1. 動画単位（またはサブシーケンス単位）で iterate
  2. forward → loss (MultiStageLoss + TemporalSmoothingLoss) → backward
  3. logger.log()
- `evaluate() -> dict`:
  1. 動画単位で推論
  2. PhaseEvaluator で全指標を計算
  3. metrics 記録
- 学習は時系列モデルのみ（backbone は凍結、特徴量は事前抽出済み）

---

## 7. Config ファイル

### 7.1 `configs/stage/s4_temporal.yaml`

```yaml
experiment:
  category: "baselines"    # S4 第1波は §2.5(b) 基準点なので baselines
  step: "s4"
  description: "temporal"

model:
  temporal: tecno      # run_s4.sh で sr_mamba に切り替え
  phase_head:
    input_type: "global_feature"   # S5 で "object_token" に切り替え

data:
  feature_dir: "data/processed/features/"
  phase_ann_dir: "data/annotations/egosurgery_phase/"
  max_seq_len: null                # 動画全長

temporal:
  # TeCNO
  tecno:
    num_stages: 4
    num_layers: 10
    num_features: 64
    kernel_size: 15
    causal: true
  # SR-Mamba
  sr_mamba:
    d_model: 256
    d_state: 16
    d_conv: 4
    expand: 2
    num_layers: 4
    bidirectional: true

loss:
  lambda_phase: 1.0
  lambda_smooth: 0.15
  lambda_transition: 0.1

train:
  epochs: 200      # 時系列モデルは軽いので epoch 数を増やす
  batch_size: 1    # 動画単位（1動画が1バッチ）
  lr: 0.0005       # 時系列モデル用（backbone より大きめ）

feature_extraction:
  checkpoint: "experiments/baselines/s0_001_maskdino_bbox_seed42/checkpoints/best.pth"
  batch_size: 32
```

### 7.2 `configs/model/temporal/tecno.yaml`

```yaml
name: "tecno"
num_stages: 4
num_layers: 10
num_features: 64
kernel_size: 15
input_dim: 1024
num_classes: 9
causal: true
dropout: 0.5
```

### 7.3 `configs/model/temporal/sr_mamba.yaml`

```yaml
name: "sr_mamba"
d_model: 256
d_state: 16
d_conv: 4
expand: 2
num_layers: 4
input_dim: 1024
num_classes: 9
bidirectional: true
dropout: 0.3
```

---

## 8. 実行スクリプト

### 8.1 `scripts/run_s4.sh`

```bash
#!/bin/bash
# S4: 長距離時系列モデル — §2.5(b) 基準点 + D-B 第1波
# TeCNO (causal) × 3 seeds + SR-Mamba (causal/bidirectional) × 3 seeds = 9 実験

set -euo pipefail
SEEDS=(42 123 456)

echo "=== S4 Phase 1: Feature extraction ==="
PYTHONPATH=src python scripts/extract_features.py \
    --checkpoint experiments/baselines/s0_001_maskdino_bbox_seed42/checkpoints/best.pth \
    --data_dir data/raw/ego/ \
    --output_dir data/processed/features/ \
    --splits data/splits/

echo "=== S4 Phase 2: TeCNO (causal, §2.5(b) baseline) ==="
for SEED in "${SEEDS[@]}"; do
    PYTHONPATH=src python -m egosurgery.train \
        stage=s4_temporal \
        model.temporal=tecno \
        temporal.tecno.causal=true \
        seed=${SEED} \
        experiment.description="tecno_causal" \
        experiment.category="baselines"
done

echo "=== S4 Phase 3: SR-Mamba (causal) ==="
for SEED in "${SEEDS[@]}"; do
    PYTHONPATH=src python -m egosurgery.train \
        stage=s4_temporal \
        model.temporal=sr_mamba \
        temporal.sr_mamba.bidirectional=false \
        seed=${SEED} \
        experiment.description="sr_mamba_causal" \
        experiment.category="baselines"
done

echo "=== S4 Phase 4: SR-Mamba (bidirectional) ==="
for SEED in "${SEEDS[@]}"; do
    PYTHONPATH=src python -m egosurgery.train \
        stage=s4_temporal \
        model.temporal=sr_mamba \
        temporal.sr_mamba.bidirectional=true \
        seed=${SEED} \
        experiment.description="sr_mamba_bidirectional" \
        experiment.category="baselines"
done

echo "=== S4 completed ==="
echo "Baselines: experiments/baselines/s4_001_* ~ s4_009_*"
echo "Next: Check TeCNO Jaccard. If < 70%, prioritize Mamba variants."
```

---

## 9. テスト

`tests/test_models.py` に追加:
1. `test_tecno_forward`: TeCNO が (B=2, T=100, D=1024) → List[(B, T, 9)] を返すこと
2. `test_tecno_causal_no_future_leak`: causal モードで未来の情報がリークしないこと（出力の t フレーム目が入力の t+1 以降に依存しないことを勾配で確認）
3. `test_sr_mamba_forward`: SR-Mamba が (B=2, T=100, D=1024) → (B, T, 9) を返すこと
4. `test_sr_mamba_bidirectional_vs_causal`: bidirectional と causal で出力が異なること

`tests/test_losses.py` に追加:
5. `test_multi_stage_loss`: MultiStageLoss が正しい shape の勾配を返すこと
6. `test_temporal_smoothing_loss`: TemporalSmoothingLoss が滑らかな予測に低い損失を与えること

`tests/test_datasets.py` に追加:
7. `test_temporal_dataset_loads`: TemporalDataset が (T, 1024) の特徴量と (T,) のラベルを返すこと
8. `test_temporal_dataset_collate`: バッチ内で長さが異なる動画のパディングが正しいこと

---

## 10. 完了判定（Part 5 / フェーズ II 全体）

### Part 5 の完了判定:
1. `scripts/extract_features.py` が全フレームの特徴量を抽出して `data/processed/features/` に保存する
2. TeCNO (causal) の Phase macro F1 / Edit score / Segmental F1@{10,25,50} が安定取得
3. SR-Mamba (bidirectional) が TeCNO を上回る
4. causal vs bidirectional の差が定量化されている
5. 3 seeds の平均±標準偏差が記録されている
6. `experiments/baselines/` に `s4_001_` 〜 `s4_009_` が正しい構造で存在する

### フェーズ II 全体の完了判定:
7. S0: VarifocalNet mAP ≥ 45.8, Mask DINO mAP が計測済み, per-class AP 15 クラス報告
8. S2: hand mAP > 65, 術具 mAP 劣化なし
9. S3: Phase パイプライン動作, 術具 mAP 劣化なし
10. S4: TeCNO / SR-Mamba の Phase 基準点が確定
11. S0〜S4 の全実験で seed / optimizer / scheduler が完全に統一されている
12. `pytest tests/ -v` が全テストパスする
13. W&B ダッシュボードに全実験の指標が記録されている
14. **S4 終了時点で実験管理パイプラインが完全整備されていることを再確認**（§13.1 I-2 の指示）

# フェーズ II — Part 4/5: S2 手検出追加 + S3 Phase head 接続

前提: Part 3 まで完了し、S0 が完走済み。VarifocalNet mAP ≥ 45.8 を確認済み。
experiments/baselines/ に S0 の 6 実験が保存されている。

Part 4 では **S2（手検出の追加）** と **S3（Phase head の接続）** を実装する。

---

## 1. S2: 手検出の追加

### 1.1 概要
- S0 の術具検出 (15 cls) に手検出 (4 cls: Own_L, Own_R, Other_L, Other_R) を追加
- 術具 mAP が S0 から劣化しないことを確認（negative transfer なし）
- S0 の best checkpoint から fine-tune

### 1.2 実装するファイル

**データ:**
- `src/egosurgery/datasets/ego_dataset.py` を拡張:
  - `include_hand=True` で hand bbox (4 cls) を tool bbox (15 cls) と**別ヘッドとして**返す
  - target に `"hand_boxes"` と `"hand_labels"` を追加（tool と hand を分離管理）
  - あるいは tool (id 1-15) + hand (id 16-19) を統合して 19 クラスで返す方式（検出ヘッドの設計に依存。Mask DINO の場合はクエリを共有するので統合方式が自然）
  - `__getitem__` の返り値:
    ```python
    target = {
        "boxes": Tensor,          # tool + hand の統合 bbox (N, 4)
        "labels": Tensor,         # 統合ラベル (N,) — 1-19
        "image_id": int,
        "is_tool": Tensor,        # (N,) — tool=True, hand=False
        "is_hand": Tensor,        # (N,) — hand=True, tool=False
    }
    ```

- `src/egosurgery/datasets/transforms.py` に追加:
  - `ArtificialGlovesAugmentation`:
    - 手の bbox 領域に色オーバーレイ（ランダムな手袋色: 白/青/ピンク/紫等）
    - 確率 p=0.3 で適用
    - 実装: bbox 内の肌色領域を検出し（HSV 色空間で閾値処理）、色を置換
    - 簡易版: bbox 内全体に半透明の色オーバーレイを重畳
  - `BloodSplatterAugmentation`:
    - 手の bbox 周辺に血液テクスチャを重畳
    - 赤色の小さな不定形パッチをランダム配置
    - 確率 p=0.2 で適用

**Config:**
- `configs/stage/s2_hand.yaml`:
  ```yaml
  experiment:
    category: "phase0"
    step: "s2"
    description: "hand_detection"

  model:
    num_classes: 19  # tool 15 + hand 4
    detection_head: mask_dino

  data:
    include_hand: true
    include_phase: false

  train:
    epochs: 50       # S0 の best checkpoint から fine-tune なので短め
    resume_from: null # S0 の best checkpoint パスを run_s2.sh で指定

  longtail:
    seesaw_loss: true
    rfs: true
    copypaste: true

  augmentation:
    artificial_gloves: true
    blood_splatter: true
  ```

**スクリプト:**
- `scripts/run_s2.sh`:
  ```bash
  #!/bin/bash
  # S2: Tool + Hand detection
  # S0 の best Mask DINO checkpoint から fine-tune

  set -euo pipefail
  SEEDS=(42 123 456)
  S0_BEST="experiments/baselines/s0_001_maskdino_bbox_seed42/checkpoints/best.pth"

  for SEED in "${SEEDS[@]}"; do
      PYTHONPATH=src python -m egosurgery.train \
          stage=s2_hand \
          seed=${SEED} \
          train.resume_from=${S0_BEST} \
          experiment.description="hand_detection"
  done
  ```

### 1.3 S2 の完了判定
- hand mAP > 65
- own/other 区別 accuracy > 90%
- L/R 区別 accuracy > 95%
- 術具 mAP の Δ(S2 - S0) ≈ 0（±1pt 以内）
- 劣化する場合: `train.loss_weight_tool` / `train.loss_weight_hand` を調整

---

## 2. S3: Phase head のパイプライン接続

### 2.1 概要
- S2 の出力に Phase head（frame-by-frame、弱ベースライン）を接続
- Phase 認識精度は評価しない（S4 まで保留）。パイプライン動作確認のみ
- 術具 mAP が S2 から劣化しないことを確認

### 2.2 実装するファイル

**モデル:**
- `src/egosurgery/models/heads/phase_head.py`:
  ```python
  """
  Frame-by-frame Phase 分類ヘッド。

  入力: backbone の [CLS] token (B, 1024) または global average pooling
  出力: 9 クラスの logits (B, 9)

  S4 以降で時系列モデルに置き換えるまでの弱ベースライン。
  S5 で入力を object token に切り替える際の比較対象。
  """

  class PhaseHead(nn.Module):
      def __init__(self, input_dim=1024, num_classes=9, hidden_dim=512, dropout=0.3):
          ...
          # Linear(input_dim, hidden_dim) → ReLU → Dropout → Linear(hidden_dim, num_classes)

      def forward(self, x):
          # x: (B, input_dim) — [CLS] token
          # return: (B, num_classes) — logits
  ```

**損失関数:**
- `src/egosurgery/models/losses/phase.py`:
  ```python
  """
  Phase 認識用損失関数。

  - Class-weighted Cross Entropy (Dissection 44.1%, Closure 34.3% の偏り補正)
  - Label smoothing (0.1)
  - Balanced Softmax (optional)
  """

  class PhaseLoss(nn.Module):
      def __init__(self, class_weights=None, label_smoothing=0.1):
          ...
          # class_weights: 9 クラスの逆頻度重み
          # nn.CrossEntropyLoss(weight=class_weights, label_smoothing=label_smoothing)
  ```

  class_weights の計算:
  ```python
  PHASE_FREQUENCIES = [0.02, 0.01, 0.03, 0.441, 0.05, 0.02, 0.343, 0.02, 0.07]
  # 逆頻度: weight_i = 1.0 / freq_i を正規化
  ```

**データ:**
- `src/egosurgery/datasets/ego_dataset.py` を拡張:
  - `include_phase=True` のとき phase label を target に追加
  - `target["phase"]`: int (0-8)

**評価指標:**
- `src/egosurgery/metrics/phase.py`:
  ```python
  """
  Phase 認識の評価指標。

  - frame-level accuracy
  - macro F1
  - Edit score
  - Segmental F1@{10, 25, 50}
  - per-class F1 (特に Dissection / Closure 内部)
  """

  class PhaseEvaluator:
      def update(self, predictions, gt_labels, video_ids): ...
      def compute(self) -> dict:
          return {
              "phase_accuracy": float,
              "phase_macro_f1": float,
              "phase_edit_score": float,
              "phase_seg_f1_10": float,
              "phase_seg_f1_25": float,
              "phase_seg_f1_50": float,
              "phase_per_class_f1": {class_name: float, ...},
          }
  ```

  Edit score と Segmental F1@k の実装:
  - Edit score: Levenshtein 距離ベースの正規化スコア
  - Segmental F1@k: IoU >= k% のセグメント単位の F1（k=10,25,50）
  - 参考実装: `https://github.com/colincsl/TemporalConvolutionalNetworks`（MS-TCN の評価コード）

**エンジン:**
- `src/egosurgery/engines/stage_a_trainer.py` を拡張:
  - `cfg.data.include_phase=True` のとき phase_head と phase_loss を追加
  - 合計損失: `total_loss = lambda_det * det_loss + lambda_phase * phase_loss`
  - evaluate() で PhaseEvaluator も呼ぶ

**Config:**
- `configs/stage/s3_phase_frame.yaml`:
  ```yaml
  experiment:
    category: "phase0"
    step: "s3"
    description: "phase_frame"

  model:
    num_classes: 19
    detection_head: mask_dino
    phase_head:
      input_dim: 1024
      hidden_dim: 512
      num_classes: 9

  data:
    include_hand: true
    include_phase: true
    phase_ann_dir: "data/annotations/egosurgery_phase/"

  loss:
    lambda_det: 1.0
    lambda_phase: 0.5

  feedback:
    det_to_phase: false   # S3 では弱接続（[CLS] token 入力のみ）
    phase_to_det: false

  train:
    epochs: 50
    resume_from: null     # S2 の best checkpoint
  ```

**スクリプト:**
- `scripts/run_s3.sh`

### 2.3 S3 の完了判定
- パイプラインが動作する（学習・評価が完走）
- 術具 mAP の Δ(S3 - S2) が劣化しない（±1pt 以内）
- Phase 認識指標（accuracy, macro F1）が記録される（精度の判定は S4 まで保留）
- Phase loss が epoch とともに減少傾向であること

---

## 3. テスト

`tests/test_models.py` に追加:
1. `test_phase_head_forward`: PhaseHead が (B, 1024) → (B, 9) の forward を通すこと
2. `test_phase_loss_gradient`: PhaseLoss が正しい勾配を返すこと

`tests/test_metrics.py` に追加:
3. `test_phase_evaluator_basic`: ダミー予測で accuracy / macro F1 が計算できること
4. `test_edit_score`: Edit score が 0〜100 の範囲で返ること
5. `test_segmental_f1`: Segmental F1@k が 0〜1 の範囲で返ること

---

## 4. 完了判定（Part 4 全体）

1. S2 の 3 実験が `experiments/phase0/s2_001_` 〜 `s2_003_` に保存されている
2. hand mAP > 65, 術具 mAP が S0 と同等
3. S3 の 3 実験が `experiments/phase0/s3_001_` 〜 `s3_003_` に保存されている
4. Phase 認識指標が metrics.json に記録されている
5. `pytest tests/ -v` が全テストパスする

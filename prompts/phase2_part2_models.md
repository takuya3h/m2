# フェーズ II — Part 2/5: Backbone + 検出ヘッド + 損失関数

前提: Part 1 が完了し、EgoSurgery データパイプライン（datasets/, transforms, Copy-Paste, RFS）が動作する状態。

Part 2 では **DINOv2 backbone** と **検出ヘッド (Mask DINO / VarifocalNet)** と **長尾対策の損失関数** を実装する。

---

## 1. DINOv2 Backbone

### 1.1 `src/egosurgery/models/backbones/dinov2_registry.py`

```python
"""
DINOv2 ViT-L/14 with registers を読み込み、検出ヘッドに接続するラッパー。

使い方:
    backbone = DINOv2Backbone(cfg.model.backbone)
    outputs = backbone(images)
    # outputs["features"]: List[Tensor] — 4 段階の特徴マップ
    # outputs["cls_token"]: Tensor — [CLS] token (Phase head 入力用, S4 以降)
"""
```

実装要件:
- `torch.hub.load('facebookresearch/dinov2', 'dinov2_vitl14_reg')` で DINOv2 ViT-L/14 with registers を読み込む
- 中間層特徴を取り出す: register_forward_hook で `out_indices=[7, 11, 15, 23]` の出力を capture
- 各中間層出力を reshape して 2D 特徴マップ (B, C, H, W) に変換（ViT は (B, N, C) なので patch_size=14 で reshape）
- `[CLS]` token (B, 1024) も出力に含める
- `forward(x) -> dict`:
  ```python
  return {
      "features": [feat_7, feat_11, feat_15, feat_23],  # List of (B, C, H/14, W/14)
      "cls_token": cls_token,  # (B, 1024)
  }
  ```
- 画像サイズは 518×518 (14 × 37) を推奨。`interpolate_pos_encoding=True` で他サイズにも対応
- bf16 対応: `torch.cuda.amp.autocast` と互換
- gradient checkpointing: `model.set_grad_checkpointing(True)` または手動で `torch.utils.checkpoint`

### 1.2 `src/egosurgery/models/backbones/vit_adapter.py`

```python
"""
ViT-Adapter: DINOv2 の 4 段階特徴マップを FPN 互換のマルチスケール特徴に変換する。
Mask DINO の pixel decoder (MSDeformAttn) に接続するために必要。

使い方:
    adapter = ViTAdapter(embed_dim=1024, out_channels=256, num_outs=4)
    ms_features = adapter(backbone_features)
    # ms_features: List[Tensor] — stride 4, 8, 16, 32 の 4 段階
"""
```

実装要件:
- DINOv2 の 4 段階特徴 (全て stride 14) を、stride 4/8/16/32 の 4 段階に変換
- ConvTranspose + Conv で各スケールを生成（FPN スタイル）
- lateral connection で上位層の情報を下位層に伝播
- 出力チャネルは 256 に統一（Mask DINO のデフォルト）

### 1.3 `src/egosurgery/models/backbones/peft.py`

```python
"""
PEFT (LoRA / DoRA) を DINOv2 backbone に適用するユーティリティ。

使い方:
    backbone = DINOv2Backbone(cfg)
    backbone = apply_peft(backbone, cfg.model.backbone.peft)
"""
```

実装要件:
- `peft` ライブラリの `get_peft_model` を使用
- LoRA 設定: `LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["qkv", "proj"])`
- DoRA 有効化: `use_dora=True` を LoraConfig に渡す（peft >= 0.10.0 で対応）
- QLoRA フォールバック（24GB GPU 用）: `BitsAndBytesConfig(load_in_4bit=True)` で量子化
- config から方式を切り替え: `cfg.model.backbone.peft.method` が `"lora"` / `"dora"` / `"qlora"` / `null`
- `null` の場合は PEFT を適用せず backbone をそのまま返す

---

## 2. 検出ヘッド

### 2.1 `src/egosurgery/models/heads/mask_dino_head.py`

```python
"""
Mask DINO を自プロジェクトのパイプラインから呼び出すラッパー。

Mask DINO 本体は third_party/MaskDINO/ に存在し、Detectron2 ベースで動く。
このファイルは Hydra config ↔ Detectron2 config の変換と、
自プロジェクトの ExperimentManager / metrics との統合を担う。

使い方:
    head = MaskDINOHead(cfg)
    head.setup(backbone)          # backbone の特徴マップを受け取る設定
    losses = head(features, targets)  # 学習時
    predictions = head.predict(features)  # 推論時
"""
```

実装要件:
- Detectron2 の config (CfgNode) を Hydra config (DictConfig) から構築する `build_d2_config(cfg)` 関数
- Mask DINO の Detectron2 モジュールを import して構築
- `num_classes=15` (tool のみ) / `num_classes=19` (tool + hand, S2 以降)
- `num_queries=300`（Mask DINO デフォルト）
- bbox-only モード: `cfg.phase.mask_available=False` のとき mask branch の loss weight を 0 にする
- denoising 有効化: contrastive denoising の noise scale 等はデフォルト値を使用
- 入力は ViT-Adapter の出力（4 段階マルチスケール特徴）
- 出力:
  - 学習時: `{"loss_ce": ..., "loss_bbox": ..., "loss_giou": ..., "loss_mask": 0.0}`
  - 推論時: `{"boxes": Tensor, "scores": Tensor, "labels": Tensor}`
- **注意**: third_party/MaskDINO が import できない環境では、エラーではなく警告を出して `None` を返す（テスト環境対応）

### 2.2 `src/egosurgery/models/heads/varifocanet_head.py`

```python
"""
mmdet の VarifocalNet を呼び出すラッパー。
EgoSurgery-Tool の実質 SOTA (mAP 45.8) の再現ベースライン。

使い方:
    head = VarifocalNetHead(cfg)
    losses = head(features, targets)
    predictions = head.predict(features)
"""
```

実装要件:
- mmdet の `build_detector` を使って VarifocalNet を構築
- backbone は DINOv2 の ViT-Adapter 出力を FPN 経由で接続
- `num_classes=15` (tool) / `num_classes=19` (tool + hand)
- mmdet config をプログラム的に構築（YAML ファイルではなく Python dict から）
- Varifocal Loss を使用（mmdet 内蔵）
- 入力/出力インターフェースは MaskDINOHead と統一
- **注意**: mmdet が import できない環境では警告を出して `None` を返す

### 2.3 `src/egosurgery/models/build.py`

```python
"""
Config からモデルを構築するファクトリ。

使い方:
    model = build_model(cfg)
    # S0: backbone + detection_head のみ
    # S3: + phase_head
    # S5: + object_token + det_to_phase
    # S6: + phase_to_det (双方向)

各コンポーネントは config のフラグに応じて有効/無効を切り替え:
    - cfg.feedback.phase_to_det: False → Phase→Det モジュールを構築しない
    - cfg.relation.enabled: False → 関係モジュールを構築しない
    - cfg.exo.enabled: False → Exo 経路を構築しない
"""
```

実装要件:
- backbone: `build_backbone(cfg)` → DINOv2 + ViT-Adapter + PEFT
- detection_head: `build_detection_head(cfg)` → MaskDINOHead or VarifocalNetHead
- phase_head: `build_phase_head(cfg)` → PhaseHead (S3 以降)
- 各コンポーネントを `nn.ModuleDict` で管理し、config から動的に組み立て
- S0 時点では `model = {"backbone": ..., "detection_head": ...}` のみ
- `forward(images, targets=None)` は各コンポーネントを順に呼び出し、losses の dict を集約して返す

---

## 3. 損失関数

### 3.1 `src/egosurgery/models/losses/detection.py`

```python
"""
検出用損失関数。Seesaw Loss + GIoU Loss。

Seesaw Loss は mmdet の実装から核心部分を抽出。
ファイル冒頭にライセンス表記を記載すること:
# Adapted from: https://github.com/open-mmlab/mmdetection
# License: Apache 2.0
"""
```

実装要件:
- `SeesawLoss(p=0.8, q=2.0, num_classes=15)`:
  - Mitigation factor: 出現頻度に基づく重み緩和
  - Compensation factor: 誤分類されやすいクラス対への罰則（形状類似ペア対策）
  - `forward(cls_score, labels) -> Tensor`
- `FocalLoss(alpha=0.25, gamma=2.0)`: 比較用
- `GIoULoss()`: bbox regression 用
- `DetectionLoss(cfg)`: 上記を統合し、`forward(predictions, targets) -> dict` で各損失と合計を返す

### 3.2 `src/egosurgery/models/losses/logit_adjust.py`

```python
"""
Post-hoc Logit Adjustment。実装 ~10 行。全分類ヘッドに適用。

参考: Menon+ ICLR 2021 "Long-tail learning via logit adjustment"

使い方:
    adjuster = LogitAdjustment(class_frequencies, tau=1.0)
    adjusted_logits = adjuster(logits)
"""
```

実装要件:
- `__init__(class_frequencies: List[float], tau: float = 1.0)`: クラス頻度の log をバッファに保存
- `forward(logits: Tensor) -> Tensor`: `logits + tau * log(frequencies)` を返す
- 学習時ではなく推論時に適用するオプション（post-hoc）も用意

---

## 4. Config ファイル

### 4.1 `configs/model/backbone/dinov2_vitl14_reg.yaml`

```yaml
name: "dinov2_vitl14_reg"
arch: "vitl"
patch_size: 14
embed_dim: 1024
num_heads: 16
depth: 24
num_register_tokens: 4
out_indices: [7, 11, 15, 23]
img_size: 518
pretrained: true
hub_repo: "facebookresearch/dinov2"
hub_model: "dinov2_vitl14_reg"

peft:
  method: "lora"
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: ["qkv", "proj"]
  use_dora: true
  quantization: null

use_bf16: true
gradient_checkpointing: true
```

### 4.2 `configs/model/backbone/dinov2_vitb14_reg.yaml`

```yaml
name: "dinov2_vitb14_reg"
arch: "vitb"
patch_size: 14
embed_dim: 768
num_heads: 12
depth: 12
num_register_tokens: 4
out_indices: [2, 5, 8, 11]
img_size: 518
pretrained: true
hub_repo: "facebookresearch/dinov2"
hub_model: "dinov2_vitb14_reg"

peft:
  method: "lora"
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: ["qkv", "proj"]
  use_dora: true
  quantization: null

use_bf16: true
gradient_checkpointing: false
```

### 4.3 `configs/model/detection_head/mask_dino.yaml`

```yaml
name: "mask_dino"
num_queries: 300
hidden_dim: 256
nheads: 8
dim_feedforward: 2048
dec_layers: 9
enc_layers: 6
mask_on: false     # Phase-0 では bbox-only
denoising: true
dn_num: 100
class_balanced_denoising: false  # 提案手法。S0 で効果を確認後に true にする
```

### 4.4 `configs/model/detection_head/varifocanet.yaml`

```yaml
name: "varifocanet"
# mmdet の VarifocalNet デフォルト設定
stacked_convs: 3
feat_channels: 256
strides: [8, 16, 32, 64, 128]
loss_cls:
  type: "VarifocalLoss"
  alpha: 0.75
  gamma: 2.0
  iou_weighted: true
loss_bbox:
  type: "GIoULoss"
  loss_weight: 1.5
```

---

## 5. テスト

`tests/test_models.py` に以下を実装:

1. `test_dinov2_backbone_forward`: ダミー画像 (B=2, 3, 518, 518) で forward し、features が 4 段階 + cls_token が返ること
2. `test_dinov2_with_lora`: LoRA 適用後もforward が通り、学習可能パラメータ数が全体の ~1% であること
3. `test_vit_adapter_output_shapes`: ViT-Adapter が stride 4/8/16/32 の 4 段階特徴を返すこと
4. `test_build_model_s0`: S0 config で `build_model(cfg)` が backbone + detection_head を含むモデルを返すこと
5. `test_seesaw_loss_gradient`: Seesaw Loss が正しい shape の勾配を返すこと
6. `test_logit_adjustment`: Logit Adjustment が頻度に応じて logit を調整すること

Mask DINO / VarifocalNet のテストは、Detectron2 / mmdet がインストールされていない環境では `pytest.mark.skipif` でスキップする。
DINOv2 のテストも、ネットワーク接続がない環境ではスキップする（`torch.hub` がダウンロードを試みるため）。

---

## 6. 完了判定

1. `from egosurgery.models.backbones.dinov2_registry import DINOv2Backbone` がエラーなく通る
2. `from egosurgery.models.build import build_model` がエラーなく通る
3. `pytest tests/test_models.py -v` が全テストパス（スキップは許容）
4. DINOv2 backbone が (2, 3, 518, 518) の入力で正しい shape の特徴マップを返す
5. Seesaw Loss / Logit Adjustment が正しく動作する

---

## 7. この Part で触らないファイル

- `src/egosurgery/engines/` 配下 → Part 3
- `src/egosurgery/metrics/` 配下 → Part 3
- `scripts/run_s0.sh` → Part 3
- `src/egosurgery/models/heads/phase_head.py` → Part 4
- `src/egosurgery/models/temporal/` 配下 → Part 5
- `src/egosurgery/models/feedback/` 配下 → フェーズ III
- `src/egosurgery/models/relation/` 配下 → フェーズ IV
- `src/egosurgery/models/exo/` 配下 → フェーズ IV

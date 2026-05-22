# フェーズ II — Part 1/5: 環境セットアップ + データパイプライン

あなたは CV 研究プロジェクト `egosurgery_multitask/` のフェーズ II を実装するコーディングエージェントです。
フェーズ I（ディレクトリ構造 + 実験パイプライン）は完了済みで、`ExperimentManager`・Hydra config・W&B 連携・ダミー学習ループが動作する状態です。

Part 1 では **依存関係の整備** と **EgoSurgery データのパイプライン構築** を行います。
モデルの実装は Part 2 以降で行うため、ここでは触りません。

---

## 0. 最重要原則（全 Part 共通）

1. **Δ 基準点の汚染防止**: S0 と S4 第1波は研究全体の Δ の分母。optimizer / seed / scheduler / augmentation / batch size を S0〜S9 で完全に揃える。
2. **Phase-0 主経路**: mask アノテーションは不要。bbox + Phase ラベルだけで動く。
3. **外部手法の取り込み方式**:

| 手法 | 方式 | 取り込み方法 |
|------|------|------------|
| DINOv2 backbone | C (hub) | `torch.hub.load` でラップ |
| mamba-ssm | C (pip) | `pip install mamba-ssm` |
| mmdet (VarifocalNet) | C (pip) | `pip install mmdet mmengine` |
| Mask DINO | D (fork) | fork → `third_party/MaskDINO/` → `pip install -e` |
| TeCNO / SR-Mamba | B (抽出) | 公式リポジトリから核心コードを抽出 → `src/` に統合 |
| Seesaw Loss | B (抽出) | mmdet から損失関数だけ抽出 |
| albumentations, peft | C (pip) | `pip install` |

---

## 1. 依存関係の更新

### 1.1 `requirements.txt` を以下の内容に更新する

```
# === Core ===
torch>=2.2.0
torchvision>=0.17.0
hydra-core>=1.3.0
omegaconf>=2.3.0
wandb>=0.16.0

# === Detection & Segmentation ===
mmdet>=3.3.0
mmengine>=0.10.0
mmcv>=2.1.0
pycocotools>=2.0.7

# === Mamba / SSM ===
mamba-ssm>=2.0.0
causal-conv1d>=1.2.0

# === Backbone ===
timm>=1.0.0

# === PEFT ===
peft>=0.10.0

# === Data & Augmentation ===
albumentations>=1.4.0
opencv-python>=4.9.0

# === Metrics & Analysis ===
scikit-learn>=1.4.0
scipy>=1.12.0
pandas>=2.2.0

# === Visualization ===
matplotlib>=3.8.0
seaborn>=0.13.0

# === Utilities ===
einops>=0.7.0
tqdm>=4.66.0
rich>=13.0.0
```

### 1.2 third_party/ のセットアップ

```bash
# Mask DINO の fork を clone
mkdir -p third_party
git clone https://github.com/IDEA-Research/MaskDINO.git third_party/MaskDINO
# 本番では自分の fork URL に差し替える

# Detectron2 のインストール（Mask DINO の依存）
pip install 'git+https://github.com/facebookresearch/detectron2.git'

# Mask DINO を editable install
cd third_party/MaskDINO && pip install -e . && cd ../..
```

`.gitignore` に `third_party/` を追加する。

### 1.3 `README.md` に以下のセットアップセクションを追記する

```markdown
## セットアップ

### 基本依存
pip install -r requirements.txt

### Mask DINO (third_party)
mkdir -p third_party
git clone https://github.com/IDEA-Research/MaskDINO.git third_party/MaskDINO
pip install 'git+https://github.com/facebookresearch/detectron2.git'
cd third_party/MaskDINO && pip install -e . && cd ../..

### DINOv2 の重みキャッシュ（任意）
python -c "import torch; torch.hub.load('facebookresearch/dinov2', 'dinov2_vitl14_reg')"
```

---

## 2. EgoSurgery データパイプライン

### 2.1 `scripts/preprocess_ego.py` — データ前処理スクリプト

以下の機能を実装する:

```python
"""
EgoSurgery-Tool / EgoSurgery-Phase のデータを
プロジェクトのディレクトリ構造に配置し、COCO 形式の JSON を生成する。

使い方:
    python scripts/preprocess_ego.py \
        --ego_root /path/to/EgoSurgery \
        --output_dir data/

処理内容:
1. data/splits/ の ego_train.txt, ego_val.txt, ego_test.txt を読み込む
   （動画 ID のリスト。Train 10 / Val 2 / Test 3）
2. 各動画のフレーム画像を data/raw/ego/{split}/ にシンボリックリンク or コピー
3. EgoSurgery-Tool の bbox アノテーションを COCO 形式 JSON に変換:
   - data/annotations/egosurgery_tool/instances_train.json
   - data/annotations/egosurgery_tool/instances_val.json
   - data/annotations/egosurgery_tool/instances_test.json
4. EgoSurgery-Phase の工程ラベルを以下に配置:
   - data/annotations/egosurgery_phase/phases_train.json
   - data/annotations/egosurgery_phase/phases_val.json
   - data/annotations/egosurgery_phase/phases_test.json
   フォーマット: {"video_id": str, "frames": [{"frame_id": int, "phase": int}]}
5. クラス分布の統計を出力（15 クラスの出現頻度、不均衡比率）
"""
```

COCO 形式 JSON の categories は以下の 15 クラス:
```python
TOOL_CLASSES = [
    {"id": 1, "name": "Tweezers"},
    {"id": 2, "name": "Needle_Holders"},
    {"id": 3, "name": "Scissors"},
    {"id": 4, "name": "Forceps"},
    {"id": 5, "name": "Bipolar_Forceps"},
    {"id": 6, "name": "Retractors"},
    {"id": 7, "name": "Clip_Applier"},
    {"id": 8, "name": "Suction"},
    {"id": 9, "name": "Scalpel"},
    {"id": 10, "name": "Electrocautery"},
    {"id": 11, "name": "Gauze"},
    {"id": 12, "name": "Needle"},
    {"id": 13, "name": "Thread"},
    {"id": 14, "name": "Skewer"},
    {"id": 15, "name": "Syringe"},
]

HAND_CLASSES = [
    {"id": 16, "name": "Own_Left"},
    {"id": 17, "name": "Own_Right"},
    {"id": 18, "name": "Other_Left"},
    {"id": 19, "name": "Other_Right"},
]

PHASE_CLASSES = [
    {"id": 0, "name": "Preparation"},
    {"id": 1, "name": "Draping"},
    {"id": 2, "name": "Incision"},
    {"id": 3, "name": "Dissection"},
    {"id": 4, "name": "Hemostasis"},
    {"id": 5, "name": "Irrigation"},
    {"id": 6, "name": "Closure"},
    {"id": 7, "name": "Dressing"},
    {"id": 8, "name": "Completion"},
]
```

注意: クラス名とID は EgoSurgery の公式データに合わせて調整すること。上記は推定値であり、実際のデータのアノテーション仕様を確認して正確な値を使うこと。

### 2.2 `src/egosurgery/datasets/ego_dataset.py` — Ego データセット

```python
"""
EgoSurgery-Tool のデータセットクラス。

使い方:
    dataset = EgoSurgeryToolDataset(
        ann_file="data/annotations/egosurgery_tool/instances_train.json",
        img_dir="data/raw/ego/train/",
        transforms=get_train_transforms(),
        include_hand=False,     # S0 では False、S2 で True に
        include_phase=False,    # S0 では False、S3 で True に
        phase_ann_file=None,    # S3 以降で指定
    )

    image, target = dataset[0]
    # image: Tensor (3, H, W)
    # target: {
    #   "boxes": Tensor (N, 4) in xyxy format,
    #   "labels": Tensor (N,),
    #   "image_id": int,
    #   "area": Tensor (N,),
    #   "iscrowd": Tensor (N,),
    #   "phase": int (include_phase=True の場合のみ),
    # }
"""
```

実装要件:
- pycocotools の COCO クラスを使ってアノテーションを読み込む
- `include_hand=True` のとき hand bbox (4 cls) を tool bbox (15 cls) と結合して返す
- `include_phase=True` のとき phase label を target に追加する
- `transforms` は albumentations の Compose を受け取る
- bbox は xyxy 形式に統一

### 2.3 `src/egosurgery/datasets/transforms.py` — Augmentation

```python
"""
学習用 augmentation と評価用 preprocessing。
augmentation と preprocessing を明確に分離する。

使い方:
    train_tfm = get_train_transforms(img_size=518)
    val_tfm = get_val_transforms(img_size=518)
"""
```

実装要件:
- `get_train_transforms(img_size=518)`:
  - RandomResizedCrop(img_size, scale=(0.8, 1.0))
  - HorizontalFlip(p=0.5)
  - ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1) — open surgery の照明変動対策
  - RandomBrightnessContrast(p=0.3) — 無影灯反射対策
  - Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
  - bbox_params=BboxParams(format='pascal_voc', label_fields=['labels'])
- `get_val_transforms(img_size=518)`:
  - Resize(img_size)
  - Normalize のみ
  - bbox_params 同上

### 2.4 `src/egosurgery/datasets/copypaste.py` — Copy-Paste augmentation

```python
"""
bbox-level Simple Copy-Paste（稀少クラス Skewer/Syringe/Forceps を優先）。
mask は使わない（Phase-0）。

使い方:
    cp = BBoxCopyPaste(
        bank_dir="data/processed/copypaste_bank/",
        rare_classes=["Skewer", "Syringe", "Forceps"],
        paste_prob=0.5,
        max_paste_per_image=3,
    )
    image, target = cp(image, target)
"""
```

実装要件:
- `data/processed/copypaste_bank/{class_name}/` から crop 画像を読み込み
- ランダムな位置・スケールで貼り付け
- 既存の bbox と重なりすぎないようチェック（IoU < 0.3）
- 貼り付けた bbox を target に追加

### 2.5 `src/egosurgery/datasets/samplers.py` — Repeat Factor Sampling

```python
"""
Repeat Factor Sampling (RFS)。

使い方:
    sampler = RepeatFactorSampler(dataset, repeat_thresh=0.001)
"""
```

実装要件:
- LVIS の RFS 実装に準拠
- クラス頻度から repeat factor を計算: r_i = max(1, sqrt(t / f_i))
- t=0.001 (Skewer 0.7% → r ≈ 1.2, Tweezers 20.2% → r ≈ 1.0)

### 2.6 `scripts/generate_copypaste_bank.py` — Copy-Paste 用 crop 生成

```python
"""
学習画像から稀少クラスの術具を bbox で crop し保存する。

使い方:
    python scripts/generate_copypaste_bank.py \
        --ann_file data/annotations/egosurgery_tool/instances_train.json \
        --img_dir data/raw/ego/train/ \
        --output_dir data/processed/copypaste_bank/ \
        --rare_classes Skewer Syringe Forceps
"""
```

### 2.7 `src/egosurgery/datasets/datamodule.py` — DataModule

```python
"""
PyTorch DataModule: train/val/test の DataLoader を統合管理。

使い方:
    dm = EgoSurgeryDataModule(cfg)
    dm.setup()
    train_loader = dm.train_dataloader()
    val_loader = dm.val_dataloader()
"""
```

実装要件:
- config から ann_file, img_dir, transforms, sampler を構築
- train_loader: RFS sampler + CopyPaste transform
- val_loader: SequentialSampler + val transforms のみ
- num_workers, batch_size は config から取得

---

## 3. テスト

以下のテストを `tests/test_datasets.py` に実装する:

1. `test_ego_dataset_loads`: データセットが正しく読み込めること（アノテーションが存在する場合）
2. `test_ego_dataset_returns_correct_shape`: `__getitem__` が正しい shape の image と target を返すこと
3. `test_train_transforms_bbox_preserved`: augmentation 後も bbox が画像内に収まること
4. `test_copypaste_adds_instances`: Copy-Paste 後に target の bbox 数が増えること
5. `test_rfs_sampler_oversamples_rare`: RFS で稀少クラスの repeat factor > 1 であること
6. `test_datamodule_creates_loaders`: DataModule が train/val の DataLoader を返すこと

テスト内では小さなダミーデータ（10枚程度の小画像 + ダミー COCO JSON）を `tmp_path` に作成して使うこと。
実際の EgoSurgery データが存在しなくてもテストが通るようにする。

---

## 4. 完了判定

以下をすべて確認して報告すること:

1. `pip install -r requirements.txt` がエラーなく完了する（mamba-ssm は CUDA が必要なので、GPU 環境でのみ確認）
2. `third_party/MaskDINO/` が存在し `import maskdino` がエラーなく通る（Detectron2 環境がある場合）
3. `pytest tests/test_datasets.py -v` が全テストパスする
4. `python scripts/preprocess_ego.py --help` がヘルプを表示する
5. `python scripts/generate_copypaste_bank.py --help` がヘルプを表示する
6. `from egosurgery.datasets.ego_dataset import EgoSurgeryToolDataset` がエラーなく通る
7. `from egosurgery.datasets.transforms import get_train_transforms, get_val_transforms` がエラーなく通る

---

## 5. この Part で触らないファイル

- `src/egosurgery/models/` 配下の全ファイル → Part 2
- `src/egosurgery/engines/` 配下（trainer 更新）→ Part 3
- `src/egosurgery/metrics/` 配下 → Part 3
- `configs/model/` 配下の YAML → Part 2
- `scripts/run_s0.sh` → Part 3
- `src/egosurgery/datasets/temporal_dataset.py` → Part 4

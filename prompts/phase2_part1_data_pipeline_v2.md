# フェーズ II — Part 1/5（改訂版 v2.1）: 環境セットアップ + データパイプライン

> **改訂履歴 v2（2026/05/24 研究計画 §14・§15 反映）**
> - 【重大】データ split を論文公式（train 9657 / val 1515 / test 4265 images）に固定。`assert_paper_split()` を必須化（§15.1）
> - 【重大】公式 tool アノテーションのパスを明記（`tool/{train,val,test}.json`）
> - 【訂正】Forceps は 12.21%（トップ3頻出クラス）。稀少クラスは Skewer 0.7% / Syringe 1.17% の2クラスのみ（2026/05/24 訂正）
> - Copy-Paste のターゲットから Forceps を削除
> - `server_name` 記録機構を追加（§14・§8.0）
>
> **改訂履歴 v2.1（2026/05/25 §8.0 DDP 運用条件・§13.2 DDP 実装要件 反映）**
> - S0 を DDP 2 GPU で実行する方針変更（§14）に伴い、`DataLoader` が `DistributedSampler` を受け入れられる構造であることを明記
> - batch size の用語を「per-GPU batch size」と「effective batch size」に区別

あなたは CV 研究プロジェクト `egosurgery_multitask/` のフェーズ II を実装するコーディングエージェントです。
フェーズ I（ディレクトリ構造 + 実験パイプライン + eval_recipe 整合性検証）は完了済みで、`ExperimentManager`・Hydra config・W&B 連携・ダミー学習ループ・`eval_recipe`・`server_name` が動作する状態です。

Part 1 では **依存関係の整備** と **EgoSurgery データのパイプライン構築** を行います。
モデルの実装は Part 2 以降で行うため、ここでは触りません。

> **監査で判明した現状（2026/05/25 ddp_migration_audit）**
> `src/egosurgery/datasets/` に**データセットクラスと transforms は既に実装済み**である
> （単一 GPU で S0 学習が回っていた実績がある）。したがって本プロンプトの大半は
> **既存実装の確認**であり、新規作成は最小限である。各ファイルについてまず `view` で
> 現状を確認し、(a) RARE_CLASSES が Skewer/Syringe のみか等の §3.3 訂正の反映、
> (b) DataLoader が `DistributedSampler` を外部注入できる構造か、(c) RFS が DDP と
> 二重適用にならないか、の 3 点を中心に**差分を当てる**こと。データセット本体の
> ロジックが正しく動いているなら、それを作り直さない。

---

## 0. 最重要原則（全 Part 共通）

1. **Δ 基準点の汚染防止**: S0 と S4 第1波は研究全体の Δ の分母。optimizer / seed / scheduler / augmentation / batch size を S0〜S9 で完全に揃える。
2. **Phase-0 主経路**: mask アノテーションは不要。bbox + Phase ラベルだけで動く。
3. **外部コードの抽出ルール（方式 B）**: 抽出したファイルの冒頭に必ず原典 URL・著者・ライセンス・変更内容を記載する。
4. **共通設定**: `seed=42`（+ 123, 456 for 3 seeds）、`deterministic=True`、`cudnn.benchmark=False`、optimizer: AdamW lr=1e-4 weight_decay=0.05、scheduler: cosine with warmup（5 epochs）、AMP: bf16、gradient checkpointing: enabled。
5. **データ split は論文公式に完全固定（§15.1）**: train 10動画{01,02,03,06,08,11,12,13,14,15} = 9657 images / val 2動画{09,10} = 1515 images / test 3動画{04,05,07} = 4265 images。これ以外の split を使った実験は Δ 基準点として無効。

---

## 1. 依存関係

`requirements.txt` に以下を追加:

```
# === Core (既存) ===
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

---

## 2. third_party/ のセットアップ

```bash
# 1. Mask DINO の fork を clone
mkdir -p third_party
git clone https://github.com/{your_username}/MaskDINO.git third_party/MaskDINO

# 2. Mask DINO を editable install
pip install -e third_party/MaskDINO

# 3. Detectron2 のインストール（Mask DINO の依存）
pip install 'git+https://github.com/facebookresearch/detectron2.git'

# 4. DINOv2 の重みをダウンロード（torch.hub で自動DLされるが明示キャッシュ）
python -c "import torch; torch.hub.load('facebookresearch/dinov2', 'dinov2_vitl14_reg')"
```

---

## 3. データ split の厳密化（§15.1 最重要）

### 3.1 `data/splits/` の修正

以下のファイルが論文公式と完全に一致すること。**変更禁止・git 管理**。

- `data/splits/ego_train.txt`: 動画 01, 02, 03, 06, 08, 11, 12, 13, 14, 15（10本）
- `data/splits/ego_val.txt`: 動画 09, 10（2本）
- `data/splits/ego_test.txt`: 動画 04, 05, 07（3本）

### 3.2 `scripts/preprocess_ego.py` の修正

`preprocess_ego.py` に以下を追加する:

```python
from egosurgery.utils.eval_recipe import PAPER_SPLIT_SIZES, PAPER_SPLIT_VIDEOS

def assert_paper_split(output_dir: str, strict: bool = True):
    """
    生成された instances_*.json が論文 Table 3a と一致するか検証する。
    strict=True の場合、不一致で AssertionError。
    """
    import json
    for split_name, expected in PAPER_SPLIT_SIZES.items():
        ann_path = os.path.join(output_dir, f"instances_{split_name}.json")
        with open(ann_path) as f:
            data = json.load(f)
        actual_images = len(data["images"])
        actual_anns = len(data["annotations"])
        if strict:
            assert actual_images == expected["images"], \
                f"{split_name}: images {actual_images} != {expected['images']}"
            assert actual_anns == expected["annotations"], \
                f"{split_name}: annotations {actual_anns} != {expected['annotations']}"
```

`main()` の末尾で必ず `assert_paper_split(args.output_dir, strict=True)` を呼ぶ。

### 3.3 公式 tool アノテーション

公式 tool アノテーションは `data/annotations/egosurgery_tool/tool/{train,val,test}.json` に存在する。
これを `instances_train.json` / `instances_val.json` / `instances_test.json` として使用する。
**旧 split（_wrong_split_8_2_3/ に退避済み）は使用禁止。**

---

## 4. EgoSurgery データセットクラス

### `src/egosurgery/datasets/ego_dataset.py`

```python
class EgoSurgeryToolDataset:
    """
    EgoSurgery-Tool データセット（bbox 検出用）。
    COCO フォーマットの instances_*.json を読み込む。

    15 クラスの術具 bbox を返す。
    Phase-0 主経路では mask を使わない。
    """

    # 15 クラス定義（§3.3 のクラス不均衡情報付き）
    TOOL_CLASSES = [
        "Bipolar Forceps",     # 形状類似ペア
        "Cautery",
        "Clip",
        "Cotton",
        "Forceps",             # 12.21%（トップ3頻出、稀少クラスではない）
        "Gauze",
        "Irrigation-suction",
        "Needle",
        "Needle Holders",      # 形状類似ペア
        "Retractor",
        "Scalpel",
        "Skewer",              # 0.7%（稀少クラス）
        "Syringe",             # 1.17%（稀少クラス）
        "Tweezers",            # 形状類似ペア
        "others",
    ]

    # 稀少クラス（§3.3、2026/05/24 訂正: Forceps を削除）
    RARE_CLASSES = ["Skewer", "Syringe"]  # bbox-level Copy-Paste のターゲット

    # 形状類似ペア（混同分析用）
    SHAPE_SIMILAR_CLASSES = ["Forceps", "Tweezers", "Needle Holders", "Bipolar Forceps"]
```

実装要件:
- COCO フォーマット（pycocotools）で読み込み
- `__getitem__` は `(image, target)` を返す。`target` は bbox (xyxy), labels, area, iscrowd を含む dict
- `get_class_frequencies()` メソッドでクラスごとのインスタンス数を返す（RFS / Seesaw Loss / Logit Adjustment に使用）

### `src/egosurgery/datasets/transforms.py`

```python
def get_train_transforms(cfg):
    """
    学習時の augmentation パイプライン。
    albumentations ベース。S0〜S9 で完全に同一であること。
    """
    # 基本 augmentation
    # - RandomResizedCrop (scale 0.5-1.0)
    # - HorizontalFlip (p=0.5)
    # - ColorJitter (brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1)
    # - RandomRotate90 (p=0.3)
    # - Normalize (ImageNet mean/std)
    pass

def get_val_transforms(cfg):
    """検証/テスト時の augmentation。Resize + Normalize のみ。"""
    pass
```

### `src/egosurgery/datasets/copypaste.py`

bbox-level Simple Copy-Paste の実装。**ターゲットは稀少クラスのみ（Skewer / Syringe）**。

```python
class BBoxCopyPaste:
    """
    bbox-level の Simple Copy-Paste（mask 不要の簡易版）。
    §3.3 に準拠。

    対象: RARE_CLASSES = ["Skewer", "Syringe"] のみ。
    ※ Forceps は 12.21% の頻出クラスのため対象外（2026/05/24 訂正）。

    動作:
    1. 稀少クラスの bbox crop をバンクから取得
    2. 学習画像にランダム位置で貼り付け
    3. 重なり処理（既存 bbox との IoU が高すぎる場合はスキップ）
    """
    pass
```

### `src/egosurgery/datasets/rfs.py`

Repeat Factor Sampling (t=0.001) の実装。

```python
class RepeatFactorSampler:
    """
    Repeat Factor Sampling（§3.3, F1 サーベイ）。
    t=0.001 で稀少クラスを含む画像の出現頻度を上げる。

    【DDP 対応・§13.2】DDP 2 GPU 実行時は DistributedSampler と二重適用に
    ならないよう注意する。以下のいずれかで実装する:
    - (推奨) DistributedRepeatFactorSampler として、repeat factor に基づく
      index 複製と DDP の rank 分割を 1 つの sampler 内で両立させる
    - または、repeat factor を Dataset 側の index リスト複製で表現し、
      サンプリング自体は通常の DistributedSampler に委ねる
    単一 GPU 実行時は通常の RepeatFactorSampler として動作する。
    """
    pass
```

### `scripts/generate_copypaste_bank.py`

稀少クラスの bbox crop を事前抽出してバンクとして保存するスクリプト。

```python
"""
稀少クラス（Skewer / Syringe）の bbox crop を train split から抽出し、
data/processed/copypaste_bank/ に保存する。

使い方:
    python scripts/generate_copypaste_bank.py \
        --ann_path data/annotations/egosurgery_tool/instances_train.json \
        --img_dir data/raw/ego/train/ \
        --output_dir data/processed/copypaste_bank/
"""
```

---

## 5. Phase ラベルの読み込み

### `src/egosurgery/datasets/phase_labels.py`

```python
class PhaseLabel:
    """
    EgoSurgery-Phase のラベル（9 クラス、0.5 fps）。
    フレームごとの工程ラベルを返す。

    9 クラス:
    - Dissection (44.1%)
    - Closure (34.3%)
    - その他 7 クラス

    §3.3 注意: Dissection + Closure で約 8 割。工程不均衡が大きい。
    """

    PHASE_CLASSES = [
        "Dissection", "Closure", "Draping", "Marking",
        "Hemostasis", "Irrigation", "Inspection",
        "Preparation", "Others"
    ]
```

---

## 6. Hydra config（データ関連）

### `configs/data/egosurgery_tool.yaml`

```yaml
dataset:
  name: egosurgery_tool
  root: data/raw/ego/
  ann_dir: data/annotations/egosurgery_tool/
  # === 論文公式 split（§15.1、変更禁止）===
  train_ann: instances_train.json   # 9657 images, 32272 annotations
  val_ann: instances_val.json       # 1515 images, 4707 annotations
  test_ann: instances_test.json     # 4265 images, 12673 annotations
  num_classes: 15

augmentation:
  train:
    image_size: 518  # DINOv2 ViT-L/14 入力サイズ
    scale_range: [0.5, 1.0]
    hflip_prob: 0.5
    color_jitter: true
  copypaste:
    enabled: true
    target_classes: ["Skewer", "Syringe"]  # 稀少クラスのみ（Forceps は対象外）
    bank_dir: data/processed/copypaste_bank/
  rfs:
    enabled: true
    t: 0.001

dataloader:
  batch_size: 4   # per-GPU batch size。DDP 2 GPU 時は effective batch size = 2 GPU × 4
  num_workers: 4
  pin_memory: true
```

> **DDP 対応の注記（§13.2 (b)(ii)・§8.0 条件 (5)）**: `dataloader.batch_size` は
> **per-GPU batch size** を表す。S0 を DDP 2 GPU で実行する際、effective batch size は
> `gpu_count × batch_size` となる。データセットクラスと collate 関数は、Part 3 の
> `MMDetTrainer._build_dataloader()` が `DistributedSampler` を差し込めるよう、
> sampler を外部から注入できる素直な `Dataset` インターフェース（`__len__` と
> `__getitem__` のみに依存し、内部で独自サンプリングを行わない）を保つこと。
> RFS（Repeat Factor Sampling）は DDP 下では `DistributedSampler` と二重適用に
> なりうるため、RFS を使う場合は DistributedSampler を兼ねる
> `DistributedRepeatFactorSampler` として実装するか、RFS の重み付けを
> Dataset 側の index 複製で表現して通常の `DistributedSampler` に委ねること。

---

## 7. テスト

`tests/test_datasets.py` に以下を実装:

1. `test_ego_dataset_loads`: EgoSurgeryToolDataset が instances_train.json を読み込み、正しい数の画像・アノテーションを返す
2. `test_ego_dataset_item_shape`: `__getitem__` が正しい shape の image と target を返す
3. `test_ego_dataset_class_count`: 15 クラスが正しく定義されている
4. `test_class_frequencies`: `get_class_frequencies()` が全 15 クラスの頻度を返す
5. `test_rare_classes_correct`: `RARE_CLASSES` が `["Skewer", "Syringe"]` のみ（Forceps を含まない）
6. `test_train_transforms`: 学習 augmentation が正しい shape を返す
7. `test_val_transforms`: 検証 augmentation が正しい shape を返す
8. `test_copypaste_targets_rare_only`: CopyPaste のターゲットが稀少クラスのみ
9. `test_rfs_repeat_factors`: RFS が稀少クラスの repeat factor を上げる
10. `test_paper_split_sizes`: `assert_paper_split()` が公式 split で OK を返す

---

## 8. 完了判定

1. `pip install -r requirements.txt` がエラーなく完了する（mamba-ssm は CUDA 環境でのみ確認）
2. `third_party/MaskDINO/` が存在し `import maskdino` がエラーなく通る（Detectron2 環境がある場合）
3. `pytest tests/test_datasets.py -v` が全テストパスする
4. `python scripts/preprocess_ego.py --help` がヘルプを表示する
5. `python scripts/generate_copypaste_bank.py --help` がヘルプを表示する
6. `from egosurgery.datasets.ego_dataset import EgoSurgeryToolDataset` がエラーなく通る
7. `from egosurgery.datasets.transforms import get_train_transforms, get_val_transforms` がエラーなく通る
8. **`assert_paper_split()` が公式 split で OK を返す**（§15.1 最重要）
9. `EgoSurgeryToolDataset.RARE_CLASSES` が `["Skewer", "Syringe"]` のみ

---

## 9. この Part で触らないファイル

- `src/egosurgery/models/` 配下の全ファイル → Part 2
- `src/egosurgery/engines/` 配下（trainer 更新）→ Part 3
- `src/egosurgery/metrics/` 配下 → Part 3
- `configs/model/` 配下の YAML → Part 2
- `scripts/run_s0.sh` → Part 3
- `src/egosurgery/datasets/temporal_dataset.py` → Part 5

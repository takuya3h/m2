# egosurgery_multitask

EgoSurgery データセット上で、手術器具検出・セグメンテーション・フェーズ認識・関係推論を
**Ego/Exo マルチタスク**で統合的に学習・評価する CV 研究プロジェクト。

---

## 設計原則

本プロジェクトは以下の 7 つの原則の上に構築されている。

1. **`src/` と `configs/` と `experiments/` を絶対に分ける** — コード・設定・実験結果の混在は再現性を壊す。
2. **すべての実験に「証拠」を残す** — 各実験フォルダには最低限 `config.yaml` / `command.sh` / `git_commit.txt` / `metrics.json` / `notes.md` を自動保存する。
3. **`data/` は Git 管理しない** — ただし `data/splits/` と `data/README.md` は Git 管理する。
4. **Phase-0 / Phase-1 の 2 フェーズ構成を構造に反映** — mask アノテーション依存のモジュールを条件付きとして分離する。
5. **S0〜S9 のステップと実験を対応づける** — 連番付き命名規則で Δ 基準点の追跡性を担保する。
6. **Ego / Exo のデータパイプラインを明示的に分離** — 推論時 Ego 単独の制約を構造で保証する。
7. **論文は最初から作る** — `paper/` は Day 1 から存在する。

---

## セットアップ

```bash
# 依存関係のインストール（開発用ツールを含む）
pip install -e ".[dev]"

# 環境変数の設定（W&B / データルート / 事前学習重み）
cp .env.example .env
# .env を編集して WANDB_API_KEY などを設定する
```

`uv` を用いる場合:

```bash
uv venv
uv pip install -e ".[dev]"
```

### 推奨セットアップ（uv 仮想環境 + CUDA + mm系 + Mamba）

mm 系（mmcv/mmdet）と mamba-ssm/causal-conv1d は CUDA 拡張ビルドが必要で、
**torch の CUDA 版をシステム nvcc（11.8）と一致させる**のが要点。検証済み構成:

```bash
# 仮想環境を作成して有効化
uv venv .venv --python 3.11
source .venv/bin/activate

# torch 2.1.2 + cu118（システム nvcc 11.8 と一致 → CUDA 拡張がビルド可能）
uv pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118

# コア依存（numpy<2 を torch 2.1 系に合わせて固定）
uv pip install "numpy<2" hydra-core omegaconf wandb timm "peft==0.13.2" \
  "transformers==4.44.2" albumentations opencv-python scikit-learn scipy pandas \
  matplotlib seaborn einops tqdm rich pycocotools pytest mmengine

# mmcv / mmdet（cu118/torch2.1 の prebuilt wheel）
uv pip install mmcv==2.1.0 --find-links https://download.openmmlab.com/mmcv/dist/cu118/torch2.1/index.html
uv pip install mmdet==3.3.0

# numpy<2 を先に pin（mmdet 等が numpy 2.x を引き込むと torch 2.1 系の C 拡張が壊れる）
uv pip install --force-reinstall "numpy<2"

# ビルドツール（setuptools<80 が必要）
uv pip install "setuptools<80" ninja packaging wheel

# mamba-ssm / causal-conv1d（GitHub の prebuilt wheel を直接導入）
# 注: mamba-ssm 2.2.2 の PyPI sdist には csrc/ ディレクトリが含まれずソースビルド不可。
#     setup.py の GitHub wheel 自動 DL も 403 を返すケースがあるため URL を明示する。
WHEEL_DIR=/tmp/egosurgery_wheels && mkdir -p "$WHEEL_DIR"
CC=causal_conv1d-1.4.0+cu118torch2.1cxx11abiFALSE-cp311-cp311-linux_x86_64.whl
MS=mamba_ssm-2.2.2+cu118torch2.1cxx11abiFALSE-cp311-cp311-linux_x86_64.whl
curl -fSL -o "$WHEEL_DIR/$CC" "https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.4.0/$CC"
curl -fSL -o "$WHEEL_DIR/$MS" "https://github.com/state-spaces/mamba/releases/download/v2.2.2/$MS"
uv pip install --no-deps "$WHEEL_DIR/$CC" "$WHEEL_DIR/$MS"

# プロジェクトを editable install（egosurgery を import 可能にする。PYTHONPATH 不要）
uv pip install -e .          # 開発ツール込みなら -e ".[dev]"
```

`pyproject.toml` は src レイアウトのパッケージ発見・pytest（`pythonpath=["src"]`）・
ruff・black・coverage を定義する。`pip install -e .` 後は `PYTHONPATH=src` は不要。
torch / mmcv 系 / mamba-ssm は CUDA 依存のため `pyproject.toml` の依存には含めず、
上記の手順で個別に導入する。

検証済み: driver 535（CUDA 12.2）上で cu118 ランタイムが動作し、`torch.cuda` /
mmcv 2.1 / mmdet 3.3 / mamba-ssm 2.2.2 / causal-conv1d 1.4.0 がすべて GPU で動作。
`transformers` は mamba-ssm 2.2.2 が旧 generation API を参照するため 4.44.2 に固定。

### 別マシンでの環境再現（推奨）

検証済み環境を他サーバで完全再現するための再現セット（すべて Git 管理）:

```bash
bash scripts/setup_env.sh   # venv 作成〜全依存導入〜検証まで自動
```

- `requirements.lock.txt` — 全 100 パッケージの厳密バージョン（`uv pip freeze`）
- `scripts/setup_env.sh` — index URL・find-links・ソースビルドを含む再現スクリプト
- `docs/environment.md` — OS / driver / CUDA Toolkit 11.8 等のシステム層の記録
- `docs/reproduce_on_new_machine.md` — 別マシンの Claude Code 向け再現指示書

前提: Ubuntu 22.04 系・NVIDIA driver 525 以降・**CUDA Toolkit 11.8（nvcc）**・uv。

---

## 別マシンで完全再現する手順（クローン → 学習開始まで）

新しいサーバで本リポジトリを 0 から立ち上げる手順を順番に示す。
**`scripts/setup_env.sh` だけでは不足**で、以下のシステム準備とデータ配置が前提となる。

### 0. ハードウェア／OS 要件

| 項目 | 要件 |
|---|---|
| OS | Ubuntu 22.04 LTS（20.04 でも `setup_env.sh` は通る想定） |
| NVIDIA driver | **535 以降推奨**（最低 525。`nvidia-smi` で確認）|
| GPU | **VRAM 24GB 以上 × 1 枚以上**。S0/S2 の DINO 学習は batch 4 で 23-48GB 消費。RTX A6000（49GB）×2 で検証済み |
| ディスク | データ・重み・実験結果込みで **40GB 以上空き**（EgoSurgery 約 15GB + COCO 事前学習重み 約 400MB + 実験ログ）|
| RAM | 32GB 以上推奨（DataLoader workers + mmdet で消費）|

### 1. システムパッケージのインストール（root 権限）

```bash
# nvcc 11.8（uv venv の前にホスト側で必要）
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run --toolkit --silent --override
export CUDA_HOME=/usr/local/cuda-11.8
echo 'export CUDA_HOME=/usr/local/cuda-11.8' >> ~/.bashrc
echo 'export PATH=$CUDA_HOME/bin:$PATH' >> ~/.bashrc

# uv（Python パッケージマネージャ）
curl -LsSf https://astral.sh/uv/install.sh | sh
# pyenv 経由で Python 3.11 を入手するか、uv 内蔵の Python ダウンロードに任せる
```

`nvcc --version` で **CUDA 11.8** が表示されることを確認（システム nvcc と
`torch+cu118` の major バージョン一致が CUDA 拡張ビルドの絶対条件）。

### 2. リポジトリのクローン

```bash
git clone git@github.com:takuya3h/m2.git egosurgery_multitask
cd egosurgery_multitask
git checkout phase2   # 最新の作業ブランチ
```

### 3. Python 環境のセットアップ

```bash
bash scripts/setup_env.sh         # venv 作成〜全依存導入〜import 検証まで自動
source .venv/bin/activate
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q   # 28/28 パスを確認
```

### 4. データセットの取得と配置

**Git に含まれない要素 — 別途取得が必要**:

| 取得物 | 入手元 | 配置先 |
|---|---|---|
| EgoSurgery-Tool / Phase の動画フレーム | プロジェクトページ（公式配布、要承認） | `data/raw/ego/{train,val,test}/<vid>/<vid>_<sess>_<frame>.jpg` |
| EgoSurgery-Tool 公式 COCO 注釈 | 同上配布物 | `data/annotations/egosurgery_tool/tool/{train,val,test}.json` と `hand/{train,val,test}.json` |
| EgoSurgery-Phase 工程 CSV | 同上配布物 | `data/annotations/egosurgery_phase/<vid>_<sess>.csv` |

最終的に `data/raw/ego/` 直下に **論文準拠 split**（10/2/3 videos）で配置されている必要がある:

```
data/raw/ego/train/{01,02,03,06,08,11,12,13,14,15}/<frame>.jpg
data/raw/ego/val/{09,10}/<frame>.jpg
data/raw/ego/test/{04,05,07}/<frame>.jpg
```

`data/annotations/egosurgery_tool/{tool,hand}/{train,val,test}.json` を上記レイアウトで
配置したのち、本リポジトリ用の派生注釈を生成する:

```bash
# tool 注釈を instances_*.json に展開（公式 tool/*.json をそのままコピー）
cp data/annotations/egosurgery_tool/tool/train.json data/annotations/egosurgery_tool/instances_train.json
cp data/annotations/egosurgery_tool/tool/val.json   data/annotations/egosurgery_tool/instances_val.json
cp data/annotations/egosurgery_tool/tool/test.json  data/annotations/egosurgery_tool/instances_test.json

# tool + hand 19 クラス統合 COCO の生成（S2 で必要）
python scripts/build_tool_hand_coco.py
```

**注意**: `data/splits/ego_*.txt` は git 管理されており、論文準拠の動画 ID リストが
入っている（変更禁止）。`scripts/preprocess_ego.py` を独自実行する場合は
最後に `assert_paper_split()` が走り、論文 Table 3a と一致しない場合 `AssertionError`
で停止する（再発防止策、§15.3 参照）。

### 5. 環境変数とトークン

```bash
cp .env.example .env
# .env を編集:
#   WANDB_API_KEY=<your_api_key>     # W&B 記録を有効にする場合
#   WANDB_PROJECT=egosurgery_multitask
#   DATA_ROOT=/abs/path/to/data       # data/ を別パスにしたい場合のみ
#   # --- Notion 連携（M2研究運用ハブ・任意）---
#   NOTION_API_KEY=secret_xxxxxxxx    # https://www.notion.so/profile/integrations で発行
#   NOTION_DB_ID=ef4ccd02-0a97-41af-814e-9acc44e1e0d3   # 実験Run台帳の database id（後述・collection idでない）
#   NOTION_SERVER_OPTION=lecun        # Run台帳 Server 列（実行サーバー名）
```

W&B を使わない場合は `logging.wandb_enabled=false` を CLI override で渡せる。

### Notion 連携（運用ハブ駆動・コンテキスト削減）

研究運用を Notion「**M2研究運用ハブ**」に連動させ、マスターの「M2研究計画」（長文）を毎回読まずに
DB 駆動で回す。**ID レジストリ `configs/notion.yaml`（非秘密・コミット可）/ token は `.env`**。
`NOTION_API_KEY` 未設定なら全 no-op（研究フローを止めない）。詳細 → [`docs/notion_integration.md`](docs/notion_integration.md)。

- **書く（自動記録）**:
  - 実験Run台帳: `MMDetTrainer.run()` 完了時 + STEP B 後処理（`postprocess_b1` / `train_b2a` / `train_t1a` / `postprocess_t1b`）が
    `notion_logger.log_experiment_to_notion` で投稿。既存分の一括投稿は `scripts/post_experiments_to_notion.py`（`--dry-run` 可）。
  - **T1b-CA 専用**: `scripts/post_t1b_ca_to_notion.py`（`injected_result.json` / `control_result.json` を inj/ctrl/純効果に整形して冪等 upsert）。
  - 意思決定 / 失敗知見 / プロンプト: `egosurgery.utils.notion_ops`（`log_decision` / `log_lesson` / `save_prompt`）。
- **読む（コンテキスト削減）**: `scripts/notion_context_pack.py --step <S0..S9/B>`（関連 DB 行のみ抽出）+ 「現在の研究状態」を MCP fetch。
  M2研究計画は**該当 § のみ**取得する。
- **DB 共有状態（2026-06-23 確認）**: REST トークンに **全 5 DB（run_ledger / decision_log / lessons / procedure_docs / prompt_library）が共有済み**。
  以前 404 だった `decision_log` / `lessons` も REST 経由で `notion_ops.log_decision` / `log_lesson` が正常動作する
  （メモリ: [[notion-rest-share-gap]] は解消済）。新規 DB を追加した場合は Notion 側で Integration への share が必要。
- **注（DB id）**: `NOTION_DB_ID` は **database id**（`ef4ccd02…`）。Notion-flavored の `collection://7bcf9406…` は
  data source id で、REST `/databases/{id}/query`（API 2022-06-28）では使えない。投稿が 404 で skip される場合は
  ① database id を使っているか ② Integration に share されているか を確認する。
- 失敗時も学習を止めない設計（証拠ファイルは書き出し済）。旧 Run台帳ドキュメント → [`docs/notion_run_ledger_auto_post.md`](docs/notion_run_ledger_auto_post.md)。

### 6. 動作確認（sanity check）

```bash
# (a) 単体テスト（28 ケースが全パスすること）
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q

# (b) Hydra config の resolve 確認（学習しない）
PYTHONPATH=src .venv/bin/python -c "
from hydra import compose, initialize_config_dir
from pathlib import Path
with initialize_config_dir(version_base=None, config_dir=str(Path('configs').resolve())):
    cfg = compose('default', overrides=['stage=s0_tool_baseline'])
    print('step=', cfg.experiment.step, 'num_classes=', cfg.model.num_classes)
"

# (c) 内蔵 SimpleDetectionHead でのスモーク学習（1 epoch、~1 分、GPU 1 枚）
S0_EXTRA_ARGS="train.real_detector=false model.backbone=dinov2_vits14_reg \
  data.limit=16 data.img_size=224 train.epochs=1 train.freeze_backbone=true \
  data.num_workers=0 logging.wandb_enabled=false" bash scripts/run_s0.sh

# (d) データ split 整合性の自動検証
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts'); sys.path.insert(0, 'src')
from preprocess_ego import assert_paper_split
from pathlib import Path
assert_paper_split(Path('data'), strict=True)
"
```

### 7. 本番学習の起動

```bash
# COCO 事前学習重みの自動 DL は run_s0.sh が初回実行時に行う（VFNet 132MB + DINO 263MB）
bash scripts/run_s0.sh   # S0: 6 実験、3 波 × 2 GPU、~9-13 時間
bash scripts/run_s2.sh   # S2: hand 検出、~4-8 時間
bash scripts/run_s3.sh   # S3: phase 認識、~10 分（軽量）
```

### 8. 既知の前提・落とし穴

- **`venv` の必須有効化**: `bash scripts/run_*.sh` は内部で `source .venv/bin/activate` を実行するが、対話セッションでは自分で `source` すること。pyenv グローバル python では mmcv の C 拡張が ABI 不一致で失敗する。
- **DINOv2 重み**: 初回 `torch.hub.load` でダウンロードされる（~/.cache/torch/hub/）。オフライン環境では事前キャッシュ必要。
- **ResNet50 ImageNet 重み**: S3 で初回 `tv_models.resnet50(weights=...)` が自動 DL（~/.cache/torch/hub/checkpoints/、97MB）。
- **Mask DINO / Detectron2**: S0 では mmdet の `dino-4scale_r50` で代替するため、third_party の Mask DINO は必須ではない（オプション）。
- **GPU が 1 枚しか無い場合**: `run_s0.sh` は GPU 数を自動検出し逐次実行へフォールバックするが、合計時間は約 2 倍。
- **失敗実験の保存**: `experiments/_smoke_prior/` `experiments/baselines/_wrong_split_8_2_3/` `experiments/phase0/_failed_s3_weighted/` は過去の失敗ランの証跡。**消さずに残す**（研究 integrity の物理証拠、§15 参照）。
- **研究計画との整合**: M2 研究計画は Notion ページ（社内）に存在。本リポジトリの §15.4 が研究計画への波及項目を集約しているので、計画書を更新する際の参照点とする。

### 基本依存（requirements.txt）

`requirements.txt` は依存の概要一覧。厳密な再現には上記 `requirements.lock.txt` を
用いること。

```bash
pip install -r requirements.txt
```

### Mask DINO (third_party)

Mask DINO は Detectron2 ベースのため `third_party/` に fork を置いて使う
（`third_party/` は Git 管理外）。

```bash
mkdir -p third_party
git clone https://github.com/IDEA-Research/MaskDINO.git third_party/MaskDINO
pip install 'git+https://github.com/facebookresearch/detectron2.git'
cd third_party/MaskDINO && pip install -e . && cd ../..
```

Detectron2 / Mask DINO が無い環境でも、検出ヘッドのラッパーは警告を出して
`None` を返すためパイプライン自体は動作する（テスト環境対応）。

### DINOv2 の重みキャッシュ（任意）

```bash
python -c "import torch; torch.hub.load('facebookresearch/dinov2', 'dinov2_vitl14_reg')"
```

---

## ディレクトリ構造の概要

```
egosurgery_multitask/
├── configs/        # 設定（コードと完全分離）
├── data/           # データ（Git 管理外。splits/ と README.md のみ管理）
├── src/egosurgery/ # 実装コード
├── scripts/        # 実験起動・前処理・集計スクリプト
├── experiments/    # 実験結果（ExperimentManager が自動生成）
├── notebooks/      # 探索用ノートブック（本番実験はやらない）
├── outputs/        # 図表・レポート
├── docs/           # アイデアログ・実験ログ・読書ノート
├── paper/          # 論文（Day 1 から存在）
├── tests/          # テスト
└── tools/          # 補助ツール
```

### `configs/` の 4 軸

設定は Hydra の config group として **4 つの軸**に分解される。コマンドラインで部品を差し替えられる。

| 軸 | 内容 | 例 |
|----|------|----|
| `model/` | モデル部品（backbone / detection_head / temporal / phase_injection / relation / exo / object_token） | `backbone=dinov2_vitl14_reg` |
| `data/` | データセット定義 | `data=egosurgery_tool` |
| `train/` | 学習ステージ設定（stage_a0 〜 stage_d） | `train=stage_a1` |
| `stage/` | S0〜S9 のステップ定義 | `stage=s4_temporal` |

加えて `configs/experiment/`（アブレーション・ベンチマーク一式）と `configs/sweep/`（ハイパラ探索）を持つ。

### `src/egosurgery/` の構造

- `datasets/` — Ego / Exo / ペア / 時系列データセットと変換・サンプラ
- `models/` — `backbones/` `heads/` `temporal/` `object_token/` `feedback/` `relation/` `exo/` `losses/`
  - `feedback/` `relation/` `exo/` `object_token/` `temporal/` は仮説 H1〜H4 に対応するモジュール群
- `engines/` — ステージ別トレーナ（stage_a 〜 stage_d）・バリデータ・フック
- `metrics/` — 検出 / セグメンテーション / フェーズ / 関係 / Δ 評価
- `utils/` — seed 固定・チェックポイント・**実験管理（ExperimentManager）**
- `analysis/` — 埋め込み・失敗事例・注意マップ・ロングテール解析

### `experiments/` の 6 カテゴリ

`baselines/` `phase0/` `phase1/` `ablations/` `transfer/` `final/` の 6 つ。
個別の実験フォルダは手作業で作らず、`ExperimentManager` が実行時に自動生成する。
詳細は [`experiments/README.md`](experiments/README.md) を参照。

---

## 実験の実行方法

`Makefile` 経由でステップ単位の実験を起動する。

```bash
make s0      # S0: tool 検出ベースライン
make s2      # S2: hand
make s4      # S4: temporal
make s5      # S5: object token
make s6      # S6: bidirectional
make eval    # 評価
make delta   # Δ（基準点比較）の算出
make tables  # 論文用テーブルの書き出し
```

`make s0` は内部で `bash scripts/run_s0.sh` を呼び、`ExperimentManager` が
`experiments/baselines/s0_001_..._seed42/` を採番・生成して証拠ファイルを残す。

---

## 命名規則

実験フォルダは以下の規則で **自動採番**される（手作業で命名しない）。

```
{step}_{seq:03d}_{description}_seed{seed}
```

- `step` — S0〜S9 のステップ（`s0` 〜 `s9`）、またはアブレーション（`a1` 〜 `a7`）
- `seq` — 同一 `category` + `step` 内での 3 桁ゼロ埋め連番（`001`, `002`, ...）
- `description` — 実験内容の短い説明（例: `maskdino_bbox`）
- `seed` — 乱数シード（既定 42）

例: `s0_001_maskdino_bbox_seed42` / `s4_003_srmamba_seed42` / `a5_001_relation_seed42`

連番は `ExperimentManager` が `experiments/{category}/` 配下の既存フォルダを走査して
自動決定するため、命名のゆれや重複が構造的に発生しない。

---

## 実装状況

### フェーズ I（パイプライン骨格）— 完了

ダミーモデル・ダミーデータで学習〜評価〜証拠保存の骨格を 1 周通せる状態。
実モデル（Mask DINO / DINOv2 等）は未実装で、配線の検証が目的。

実装済みファイル:

| ファイル | 役割 |
|---|---|
| `src/egosurgery/utils/seed.py` | 全乱数生成器の seed 固定 |
| `src/egosurgery/utils/git_utils.py` | git commit hash の取得・保存 |
| `src/egosurgery/utils/experiment_id.py` | 連番付き実験 ID の採番 |
| `src/egosurgery/utils/experiment_manager.py` | 実験フォルダ・証拠ファイルの自動生成（§14 対応で `server.txt` を併記、`log_eval_recipe()` で metrics.json に eval_recipe を併記） |
| `src/egosurgery/utils/eval_recipe.py` | locked-down test_cfg / 論文公式 split サイズ / `build_eval_recipe()`（§15.3 G1） |
| `src/egosurgery/utils/server_name.py` | 実行サーバー名の単一情報源（環境変数 → cfg → hostname の優先順位） |
| `src/egosurgery/utils/logging.py` | `ExperimentLogger` — W&B + ローカルの二重ロギング（W&B 不在時はフォールバック） |
| `src/egosurgery/utils/checkpoint.py` | `CheckpointManager` — top-k 保持 + best 管理 |
| `src/egosurgery/metrics/delta.py` | `DeltaCalculator` — Δ 計算 + eval recipe の整合性検証（不一致なら `InconsistentRecipeError`、§15.4 B / §15.6） |
| `src/egosurgery/engines/trainer.py` | `Trainer` — ダミーモデルで学習・評価ループを回す汎用トレーナー |
| `src/egosurgery/train.py` | Hydra エントリーポイント |
| `configs/default.yaml` / `configs/stage/s0_tool_baseline.yaml` | グローバル設定・S0 ステージ設定 |
| `tests/test_pipeline.py` / `tests/test_delta.py` | パイプライン統合テスト + Δ 整合性検証テスト |

研究計画 §15 反映の patch（2026/05/24 適用）: §15.1 のデータ split 取り違え事故と §15.2 の `score_thr` 不一致事故を踏まえ、`DeltaCalculator` が異なる eval recipe 間の Δ 計算を `InconsistentRecipeError` で拒否する機構と、各実験フォルダへの `server.txt` 記録を追加した。詳細は `prompts/phase1_patch_eval_recipe.md`。

動作確認:

```bash
# 統合テスト（5 ケース全パス）
PYTHONPATH=src pytest tests/test_pipeline.py -v

# ダミー学習の実行 — experiments/baselines/s0_001_tool_baseline_seed42/ を自動生成
PYTHONPATH=src python -m egosurgery.train \
    stage=s0_tool_baseline seed=42 train.epochs=2 logging.wandb_enabled=false
```

学習後、実験フォルダには `config.yaml` / `command.sh` / `git_commit.txt` /
`metrics.json`（per-class AP の集約・Δ 計算枠を含む）/ `per_class_ap.json`（15 クラス）/
`notes.md` と `logs/` `checkpoints/` `predictions/` `visualizations/` が自動保存される。
同一ステップで再実行すると連番が `s0_002_...` と自動で進む。

### フェーズ II Part 1（データパイプライン）— 完了

EgoSurgery データの前処理・データセット・augmentation・サンプラを実装。

| ファイル | 役割 |
|---|---|
| `src/egosurgery/datasets/constants.py` | 術具15 / 手4 / 工程9 クラス定義の単一情報源 |
| `src/egosurgery/datasets/ego_dataset.py` | `EgoSurgeryToolDataset` — COCO 形式 bbox データセット |
| `src/egosurgery/datasets/transforms.py` | albumentations による train/val 変換 |
| `src/egosurgery/datasets/copypaste.py` | `BBoxCopyPaste` — 稀少クラス優先 Copy-Paste |
| `src/egosurgery/datasets/samplers.py` | `RepeatFactorSampler` — LVIS 準拠 RFS |
| `src/egosurgery/datasets/datamodule.py` | `EgoSurgeryDataModule` — train/val/test ローダ統合 |
| `scripts/preprocess_ego.py` | EgoSurgery → COCO 形式への前処理 CLI |
| `scripts/generate_copypaste_bank.py` | 稀少クラス crop バンク生成 CLI |
| `tests/test_datasets.py` | データパイプライン統合テスト（6 ケース） |

### フェーズ II Part 2（Backbone・検出ヘッド・損失）— 完了

DINOv2 backbone・ViT-Adapter・PEFT・検出ヘッド・長尾損失を実装。

| ファイル | 役割 |
|---|---|
| `src/egosurgery/models/backbones/dinov2_registry.py` | `DINOv2Backbone` — DINOv2 ViT/14+registers ラッパー |
| `src/egosurgery/models/backbones/vit_adapter.py` | `ViTAdapter` — 等解像度特徴 → stride 4/8/16/32 |
| `src/egosurgery/models/backbones/peft.py` | `apply_peft` — LoRA / DoRA / QLoRA 適用 |
| `src/egosurgery/models/heads/mask_dino_head.py` | `MaskDINOHead` — Mask DINO ラッパー（依存欠落時は無効化） |
| `src/egosurgery/models/heads/varifocanet_head.py` | `VarifocalNetHead` — mmdet VarifocalNet ラッパー |
| `src/egosurgery/models/build.py` | `build_model` — config からモデルを組み立てるファクトリ |
| `src/egosurgery/models/losses/detection.py` | Seesaw / Focal / GIoU / `DetectionLoss` |
| `src/egosurgery/models/losses/logit_adjust.py` | `LogitAdjustment` — post-hoc logit 補正 |
| `configs/model/backbone/`, `configs/model/detection_head/` | backbone / 検出ヘッド設定 YAML |
| `tests/test_models.py` | モデル統合テスト（6 ケース） |

動作確認:

```bash
pip install -r requirements.txt          # 依存（GPU 環境推奨）
PYTHONPATH=src pytest tests/test_datasets.py tests/test_models.py -v
```

Detectron2 / Mask DINO が無い環境でも検出ヘッドのラッパーは警告を出して
`None` を返すため、パイプラインとテストは動作する。mmdet は導入済み。

### フェーズ II Part 3（S0 評価指標・Stage A トレーナー・実行スクリプト）— 実装完了

S0（術具検出ベースライン）の評価指標・トレーナー・実行スクリプトを実装。

| ファイル | 役割 |
|---|---|
| `src/egosurgery/metrics/detection.py` | `DetectionEvaluator` — COCO mAP / per-class AP / AP_rare/common / 混同行列 |
| `src/egosurgery/metrics/confusion_matrix.py` | 形状類似ペアの混同行列の計算と heatmap 保存 |
| `src/egosurgery/engines/stage_a_trainer.py` | `StageATrainer` + 内蔵 `SimpleDetectionHead`（FCOS 風・スモーク/パイプライン検証用） |
| `src/egosurgery/engines/mmdet_trainer.py` | `MMDetTrainer` — mmdet で実 VarifocalNet/DINO を COCO 重みから fine-tune（S0 基準点の本命） |
| `src/egosurgery/engines/mmdet_components.py` | `EgoCocoMetric`（COCO mAP + AP_rare/common + 15 クラス per-class AP）/ `EgoWandbHook`（train/val 指標を W&B・JSONL へ記録） |
| `src/egosurgery/train.py` | トレーナールーティング（s0/s1/s2 × `train.real_detector` → MMDetTrainer、それ以外 → StageATrainer） |
| `configs/stage/s0_tool_baseline.yaml` | S0 設定（`real_detector=true`・12 epoch・長尾対策・data 契約） |
| `scripts/run_s0.sh` | 実検出器 6 実験（maskdino/varifocanet × 3 seed）を 2 GPU・3 波で実行（`.venv` 自動有効化） |
| `tests/test_metrics.py` / `tests/test_pipeline.py` | 評価指標 4 件 + StageATrainer 2 件のテスト |

実 EgoSurgery COCO アノテーションから `data/annotations/egosurgery_tool/instances_*.json`
（train 7427 / val 2230 / test 4265 枚、val は train から 2 動画を hold-out）と
`data/splits/ego_*.txt` を生成済み。`datasets/constants.py` は実データの
正しい 15 クラスへ更新済み。

```bash
PYTHONPATH=src pytest tests/ -v          # 全 23 テストパス
# S0 6 実験（実検出器・GPU 実学習）— mmdet で COCO 重みから fine-tune:
bash scripts/run_s0.sh
# スモーク（内蔵 SimpleDetectionHead・小データ・1 epoch）:
S0_EXTRA_ARGS="train.real_detector=false model.backbone=dinov2_vits14_reg \
  data.limit=16 data.img_size=224 train.epochs=1 train.freeze_backbone=true \
  data.num_workers=0 logging.wandb_enabled=false" bash scripts/run_s0.sh
```

**S0 実行アプローチ（実検出器 via mmdet）**: 完了判定 #4「VarifocalNet
mAP ≥ 45.8（公式 SOTA 再現）」は内蔵 `SimpleDetectionHead`（トイ実装）では
到達不能なため、`MMDetTrainer` で mmdet 3.3.0 の実検出器を COCO 事前学習重みから
EgoSurgery-Tool（15 クラス）へ fine-tune する。VarifocalNet は `vfnet_r50_fpn_1x`、
"Mask DINO" 枠は mmdet が Mask DINO 本体を同梱しないため bbox-only S0 で最も近い
実検出器 `dino-4scale_r50` を使用（逸脱は各 notes.md に明記）。3 seeds × 2 detector
= 6 実験を 2 GPU・3 波で実行し、`experiments/baselines/s0_001`〜`s0_006` へ
証拠ファイル（config / metrics / per_class_ap(15クラス) / notes /
visualizations/confusion_matrix.npy）を生成する。

評価は `EgoCocoMetric`（pycocotools COCOeval ベース、`classwise=True` で
per-class AP、稀少 3 クラスから `AP_rare`、残りから `AP_common` を算出）。
学習・検証指標は `EgoWandbHook` が W&B へ送信（`train/*` ロスは iter 軸、
`val/*` 指標と `val_per_class/*` per-class AP は epoch 軸、学習後に混同行列画像と
per-class AP テーブルも記録）。検出の座標系は mmdet 標準パイプラインが内部処理。

**S0 実行結果（実検出器 6 実験完走、cu118 torch + RTX A6000 ×2）**:

| Detector | seed | best epoch | val/mAP | val/mAP_50 | val/AP_rare |
|---|---:|---:|---:|---:|---:|
| Mask DINO (DINO-4scale) | 42  | 5  | **0.327** | 0.451 | 0.129 |
| Mask DINO               | 123 | 10 | 0.296 | 0.402 | 0.111 |
| Mask DINO               | 456 | 9  | 0.321 | 0.435 | 0.140 |
| VarifocalNet            | 42  | 10 | 0.285 | 0.417 | 0.135 |
| VarifocalNet            | 123 | 9  | 0.276 | 0.411 | 0.130 |
| VarifocalNet            | 456 | 9  | 0.272 | 0.399 | 0.125 |

3-seed 平均±標準偏差: **Mask DINO 0.315 ± 0.016 / VarifocalNet 0.278 ± 0.007**（val 分割）。
VFNet seed42 を test split で post-hoc 評価: **test mAP 0.388 / test AP_rare 0.329**。

**完了判定 #4「VarifocalNet mAP ≥ 45.8（公式 SOTA 再現）」は未達**。
- val 0.278 / test 0.388（target 0.458 まで val で 18pt, test で 7pt の差）
- 残ギャップの主因は (1) 標準 1x schedule (12 ep)・固定スケール入力 vs 論文の 2x/multi-scale
  recipe、(2) 長尾対策の差。標準レシピでは収束済み（epoch 8-12 でプラトー）。
- 数値捏造はせず実測値で記録（CLAUDE.md「研究インテグリティ」厳守）。
- 他 8 判定は達成: #1 完走 / #2 命名通り存在 / #3 証拠ファイル一式 / #5 Mask DINO 計測
  / #6 15 クラス per-class AP / #7 3 seed 統計算出可能 / #8 W&B 記録（1500+ uploads/run）
  / #9 pytest 28/28 パス。

### フェーズ II Part 4（S2 手検出 + S3 工程認識）— 実装完了 / 一部判定未達

S2（tool 15 + hand 4 = 19 クラス検出）と S3（frame-by-frame phase 認識・弱ベースライン）を実装。
新規ファイル: `datasets/phase_dataset.py`（CSV→画像インデックス）、`engines/phase_trainer.py`
（frozen ResNet50 + PhaseHead）、`models/heads/phase_head.py` / `models/losses/phase.py` /
`metrics/phase.py`、`scripts/build_tool_hand_coco.py`（tool+hand 19クラス COCO 統合）。

**S2 結果（mask_dino 19-cls × 3 seeds × 8 epoch、S0 best から fine-tune）**:

| seed | best epoch | val/mAP | val/tool_mAP | val/hand_mAP |
|---:|---:|---:|---:|---:|
| 42  | 1 | 0.029 | 0.018 | 0.057 |
| 123 | 1 | 0.032 | — | 0.060 |
| 456 | 1 | 0.028 | — | — |

**判定 #2「hand mAP > 65 & tool mAP Δ(S2-S0) ≤ 1pt」は未達**。
原因: mmengine の `load_from` が DINO の `bbox_head.cls_branches.{0..6}.weight/bias` 全 14 層を
15→19 サイズ不一致で random init し、tool 知識が encoder/decoder の表現と乖離して
catastrophic forgetting（tool mAP 0.327→0.003）。残ギャップを埋めるには COCO 重みからの
19-class 学習（S0 best 経由しない）か、cls_branches 以外の denoising / query embedding の
適切な転移処理が必要。本実装の状況は誠実な実測値として `experiments/phase0/s2_00*` に保存。

**S3 結果（frozen ResNet50 + PhaseHead × 3 seeds × 5 epoch）**:

| seed | best epoch | phase_accuracy | macro_F1 | edit_score | seg_F1@10 |
|---:|---:|---:|---:|---:|---:|
| 42  | 5 | 0.588 | 0.281 | 4.66 | 0.071 |
| 123 | 5 | 0.589 | 0.277 | 4.89 | 0.070 |
| 456 | 5 | 0.602 | 0.298 | 4.92 | 0.071 |

3-seed mean: **accuracy 0.593 ± 0.008 / macro F1 0.285 ± 0.011**（vs random 11%、明確に学習）。
frame-by-frame で時系列を扱わないため edit / seg F1 は低い（S4 の時系列拡張で改善見込み）。
S3 は検出器とデカップル設計のため判定 #2 後半「tool mAP の Δ(S3-S2) ≤ 1pt」は構造的に
**達成**（S3 は検出器を呼ばないため不変）。

**Part 4 判定（5 項目中 4 項目達成）**:
- #1 S2 3 experiments saved → ✓
- #2 hand mAP>65 & tool mAP S0±1pt → ✗（上記）
- #3 S3 3 experiments saved → ✓
- #4 Phase 指標 metrics.json 記録 + loss 減少 → ✓（loss 1.39→0.97 全 seed）
- #5 `pytest tests/ -v` 28/28 → ✓

### 未実装（フェーズ II Part 5 以降）

`models/temporal/`（Part 5）、`models/feedback/`・`relation/`・`exo/`（フェーズ III/IV）。

### 2026-06-16 S0-frozen（Relation-DETR 凍結 backbone + COCO-init head）

S0-frozen の Δ_detection 分母用に Relation-DETR standalone 経路を追加した。

- model config: `third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery_s0_frozen.py`
  - `freeze_indices=(0,1,2,3)` で ResNet-50 backbone を全凍結。
  - eval は NMS-free (`select_box_nums_for_evaluation=300`, `nms_iou_threshold=-1`)。
- train config: `third_party/Relation-DETR/configs/train_config_egosurgery_s0_frozen.py`
  - 初期化は `data/external/weights/relation_detr_s0frozen_init_seed42.pth`。
  - これは seed42 完走 backbone + COCO-init transformer/head のマージ済み重み。
- launcher: `scripts/run_s0_frozen.sh`
  - seed 42/123/456 を seed 並列で実行（GPU0/GPU1 に 2 本、残り 1 本）。
  - post-process は `.env` を読まない `--skip-external-loggers` でローカル証跡のみ生成。

実行前検証: Python 構文 OK、init checkpoint 188MB 存在、MS-Deform-Attn CUDA extension load OK、
`backbone_trainable=0` を確認済み。mAP 等の数値は未完走のため未記録。

2026-06-16 20:47 UTC に `setsid -f scripts/run_s0_frozen.sh` で background 起動済み。
wave1 は seed42/123 が GPU0/1 で稼働し、epoch0 iter100 到達を確認。
launcher log: `/tmp/s0_frozen_launcher.log`、seed log: `/tmp/s0_frozen_logs/`。

### 2026-06-20 ②特徴レベル結合（共有 C5 線形 neck）— 単一タスク分母と転移結合の確定

①予測レベル（neck無）に加え、②特徴レベル（共有 trainable neck 有）の系統を併設。neck は **C5 のみ・1×1 線形・
残差・zero-init**（`src/egosurgery/models/necks/c5_linear_neck.py::C5LinearNeck`、masked-GAP 可換）。

- **②検出分母 S0-frozen′（3-seed 完了）= mAP 0.7095 ± 0.0091**。検出経路に neck を挿入する検出器
  `third_party/Relation-DETR/models/detectors/relation_detr_c5neck.py::RelationDETRC5Neck` +
  config `..._s0_frozen_neck.py` + `scripts/run_s0_frozen_neck.sh`。①(neck無)0.7051±0.0052 比 +0.0044(<1σ)。
- **②工程分母 S4′（3-seed 完了）= acc 0.9142 ± 0.0017**（`train_s4_tecno.py --use-neck`）。
- **真の結合 = 検出→工程 一方向 凍結 neck 転移（S4″）**: `scripts/extract_c5neck.py` で検出 neck を抽出し
  `train_s4_tecno.py --neck-from <ckpt>` で工程へ凍結ロード。3-seed 完了。
- **分析 `scripts/analyze_phase_coupling.py`（paired-σ 判定）**: 結合効果 ΔL2 は **全指標で中立**＝
  frozen neck 転移は Δ_phase 純効果なし（容量利得は工程タスク固有で検出から転移しない）。
  ※ n=2 で見えた segmental 改善は n=3 で非再現＝撤回。詳細は `docs/experiment_log.md` 2026-06-20。

### 2026-06-20 アノテーション EDA（data/annotations ドメイン特性）

- `scripts/analyze_annotations_eda.py` 新規。COCO 画像 basename == 工程 CSV `Frame` でフレーム結合し、
  術具/手/工程の分布・bbox・共起・**術具×工程クロス集計**を実データから網羅集計（数値捏造なし・ruff clean・再現可能）。
- 成果物 `experiments/analysis/annotations_eda/`: `REPORT.md`（日本語ドキュメント）/ `stats.json`（機械可読）/
  `tool_by_phase_appearance.csv` / `phase_by_tool_distribution.csv` / 図3枚。
- 要点: 検出↔工程 join 100%（未結合0）、術具不均衡29.1×・工程不均衡57.8×、bbox 約96%が large、
  術具⇄工程が準決定的（例 Scalpel→incision 97.4%, Needle Holders→closure 99.9%）。詳細は `docs/experiment_log.md` 2026-06-20。
- 追加分析 `scripts/analyze_annotations_advanced.py`（`stats_advanced.json` / `class_video_coverage.csv` / `fig_adv_*.png`）:
  split シフト・クラス↔動画カバレッジ・tool→工程予測上限・工程混同・術具共起PMI・bbox幾何・品質・手。
  **データ整合性の警告**: disinfection は train のみ・irrigation は val 欠・Retractor は val 0件 → 工程 macro-F1 は対象 split の工程のみで算出し欠損扱いを明記、val 選択は test 非保証。
  tool-presence のみの工程予測上限 test acc=0.752（時系列 S4 base 0.899 未満＝主役は時系列、検出→工程は補完）。
- 追加分析 第2弾 `scripts/analyze_annotations_extra.py`（`stats_extra.json` / `fig_ext_*.png`）:
  手-術具接触・時間予測性・シーンテンプレート・工程順序一貫性・手の自他左右・クラス重み・術具スケール/難易度・検出無し工程フレーム。
  要点: 術具56%が手と重なり(能動工程接触率≈0.95)→疑似ラベル生成可、工程自己遷移0.982(時系列が主役)、工程順序遵守0.943、
  effective-number 重み提示、工程のみフレーム1,796。詳細は REPORT.md §18–§27。

### 2026-06-22 STEP B 結合実験一式（比較の三角形・①信号 / ②特徴 / ①予測 系統 完走）

凍結源 = Relation-DETR seed42、共有 trainable は C5 線形 neck のみという「**比較の三角形**」上で、
検出↔工程の結合を **6 つの機構** で完走した（数値は §3 paired-σ、詳細 → `experiments/analysis/step_c_coupling_analysis/REPORT.md`）。

| 系統 | 手法 | 機構 | 主トレーナ | 検出器 | Δ（対分母, 3-seed 平均）| 判定 |
|---|---|---|---|---|---:|---|
| **det→phase ①信号** | **B2a** | tool-presence 15-d 連結 | `scripts/train_b2a.py` | （凍結 GAP）| phase acc **+0.0383** | **有意改善** |
| **det→phase ①信号** | **T1a** | region-token 15×256 連結 | `scripts/train_t1a.py` | （凍結 GAP+RT）| phase acc **+0.0497** | **強く有意** |
| **②共有MTL** | **B1 固定 / K&G** | 共有C5 neck・両勾配 | `scripts/train_b1_mtl.py` | `relation_detr_b1_mtl.py` | det 中立 / phase **−0.046〜−0.053** | det 中立・phase **有意劣化** |
| **phase→det ①信号（学習無）** | **B2b** | training-free 再スコア | `scripts/run_b2b_rescore.py` | （凍結検出器）| mAP α単調 **−0.012〜−0.073** | **単調劣化** |
| **phase→det ①予測（学習・空間一様）** | **T1b-FiLM** | C5 FiLM 注入・zero-init 恒等 | `scripts/train_t1b.py --inject film` | `relation_detr_phasefilm.py` | mAP 純効果 **+0.0019**（s42/123/456: +0.0031/+0.0022/+0.0002）| 一貫正だが微小 |
| **phase→det ①予測（学習・query選択）** | **T1b-CA**（§4.6 primary）| decoder cross-attn 注入 | `scripts/train_t1b.py --inject ca` | `relation_detr_phasecrossattn.py` | mAP 純効果 **+0.00178**（s42/123/456: +0.00245/+0.00161/+0.00127）| paired-σ \|mean\|/σ=3.58, **CA≈FiLM** |

**比較の三角形における結論（方向非対称が確定）**:
1. **結合は向きで符号が決まる**: det→phase 大勝（+3.8〜+5.0pt）／phase→det は中立〜負（CA でも +0.00178 = FiLM 同等）。
2. **共有 MTL は工程のみ劣化**: 更新頻度 89:1 で検出が支配し弱タスク負転移（PCGrad/容量分離が必須）。
3. **phase→det は機構非依存で弱い**: 再スコア・FiLM・**クエリ選択可能な CA でも overall 改善せず**（§7.5 撤退ライン確定）。

**新規実装ファイル（STEP B）**:

| ファイル | 役割 |
|---|---|
| `src/egosurgery/models/necks/c5_linear_neck.py` | `C5LinearNeck` — 1×1 線形・残差・zero-init（masked-GAP 可換、唯一の共有 trainable）|
| `third_party/Relation-DETR/models/detectors/relation_detr_c5neck.py` | 検出経路に neck を挿入する `RelationDETRC5Neck` |
| `third_party/Relation-DETR/models/detectors/relation_detr_b1_mtl.py` | B1 共有 neck + phase head（TeCNO ミラー）+ K&G log σ² |
| `third_party/Relation-DETR/models/detectors/relation_detr_phasefilm.py` | T1b-FiLM: C5 を phase 事後で一様変調（zero-init 恒等）|
| `third_party/Relation-DETR/models/detectors/relation_detr_phasecrossattn.py` | T1b-CA: decoder cross-attn に c_phase token を注入（§4.6 primary）|
| `scripts/extract_b2a_detsignal.py` / `extract_t1a_regiontoken.py` | 凍結検出器から tool-presence (15-d) / region-token (3840-d) をキャッシュ |
| `scripts/postprocess_b1.py` / `postprocess_t1b.py` | 工程指標の集計・Δ 計算・Notion Run台帳投稿 |
| `scripts/run_t1b_ca_seeds_lecun.sh` | T1b-CA seed123/456 を lecun 2 GPU で並列実行（MSDeformAttn JIT warmup → measure-only → Wave A/B）|

### 2026-06-23 STEP C 分析（val 本編 + test 確証）

STEP B の **per-phase / per-class 分解**で「どこで・なぜ効くか」を実証し、test split で確証した。

- `experiments/analysis/step_c_coupling_analysis/REPORT.md`（v2, val 本編・27 §）:
  det→phase の利得が混同工程 **hemostasis（F1 0.353 → 0.713 / 0.800 = +0.36 / +0.45）** に局在することを実証。
  EDA が予言した「Bipolar signature 98%」と完全一致。FiLM/CA は per-class でも rare∧工程特異術具を標的化しない。
- `experiments/analysis/step_c_coupling_analysis/TEST_EVAL_REPORT.md`（test 確証）:
  方向非対称は test でも保たれる。val→test で検出 mAP は約 −0.20 落ちるが（EDA 予言の分布シフト JS=0.133）、
  **macro-F1 では T1a +0.164（強く有意）と val 以上に鮮明**。test FiLM +0.0028 / CA +0.0030（≈0 を維持）。
- 実装注記: 初版 `eval_det2phase_test.py` の `npz[key][i]` ループが NpzFile 反復展開で RSS 40GB 超 → OOM。
  `_index_npz` で一括展開に修正し RSS 0.90GB / 全 split 2.5 秒に是正（前セッションの exit 137 根治）。

### 2026-06-23 Notion 連携 — 全 5 DB 共有完了・STEP B/C を全件反映

REST Integration トークン（`.env` の `NOTION_API_KEY`）に **全 5 DB（run_ledger / decision_log / lessons / procedure_docs / prompt_library）が共有済み**。
`notion_ops.log_decision` / `log_lesson` も REST で正常に動作する（2026-06-23 確認）。

- **実験Run台帳**: STEP B 17 件 + T1b-CA 6 件 = **計 23 件を Notion へ投稿**（冪等 upsert）。
  - T1b-CA は `metrics.json` を持たず `injected_result.json` / `control_result.json` 形式のため、
    専用スクリプト `scripts/post_t1b_ca_to_notion.py`（inj/ctrl/純効果を整形して upsert）を追加。
- **意思決定ログ / 失敗知見**: 「方向非対称確定」「CA≈FiLM の機構独立性」等を反映。
- **「現在の研究状態」ページ**: STEP C 完了・方向非対称確定・次アクション（test split per-class rare 標的化）に更新。

---

## Claude Code 連携（`.claude/`）

本リポジトリには Claude Code でのプロジェクト運用を効率化する設定一式を同梱:

- **スラッシュコマンド**: `/run-stage`（ステージ実験の起動・監視）、`/verify-phase`
  （`prompts/` の完了判定検証）、`/delta`（Δ と 1σ 有意性の集計）、`/exp-report`
  （実験フォルダ要約）、`/new-hypothesis`（notes.md 仮説欄の記入）、`/env-check`
  （依存・CUDA の健全性確認）
- **サブエージェント**: `experiment-runner`（GPU 実験の実行・監視）、`delta-analyst`
  （Δ 分析）、`trace-debugger`（学習異常の診断）、`paper-writer`（論文節の起草）
- **スキル**: `run-experiment`、`add-model-component`
- **フック**: `src/`・`tests/` の Python 編集時に ruff で軽量チェック
- **設定**: `settings.json`（権限・フック・共有 env。Git 管理）と
  `settings.local.json`（`PYTHONPATH` 等のマシン固有設定。Git 管理外）

`settings.json` の権限・フック・env を有効化するには Claude Code の再起動が必要。

---

## 主要ドキュメント

- [`docs/experiment_log.md`](docs/experiment_log.md) — 全実験の「仮説→実験→結果→解釈→次」記録
- [`docs/idea_log.md`](docs/idea_log.md) — アイデアログ
- [`docs/decision_log.md`](docs/decision_log.md) — 設計判断の記録
- [`docs/TODO.md`](docs/TODO.md) — TODO
- [`docs/notion_integration.md`](docs/notion_integration.md) — Notion 5 DB 連携の仕組み（REST + MCP ハイブリッド）
- [`docs/secrets_and_tracking.md`](docs/secrets_and_tracking.md) — `.env.gpg` 暗号化運用 + W&B / Notion 認証
- [`experiments/analysis/step_c_coupling_analysis/REPORT.md`](experiments/analysis/step_c_coupling_analysis/REPORT.md) — STEP C 本編（val・27 §）: 結合機構の解明・実証・最良結合法の設計
- [`experiments/analysis/step_c_coupling_analysis/TEST_EVAL_REPORT.md`](experiments/analysis/step_c_coupling_analysis/TEST_EVAL_REPORT.md) — STEP C test split 確証: 方向非対称は本番データで保たれるか

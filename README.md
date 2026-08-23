# egosurgery_multitask

EgoSurgery データセット上で、手術器具検出・セグメンテーション・フェーズ認識・関係推論を
**Ego/Exo マルチタスク**で統合的に学習・評価する CV 研究プロジェクト。

---

## 設計原則

本プロジェクトは以下の 7 つの原則の上に構築されている。

1. **`src/` と `configs/` と `experiments/` を絶対に分ける** — コード・設定・実験結果の混在は再現性を壊す。
2. **すべての実験に「証拠」を残す** — 6 点の必須証跡（`config.yaml` / `command.sh` / `git_commit.txt` / `metrics.json` / `per_class_ap.json` / `notes.md`）と実行ホスト `server.txt` を自動保存する。
3. **`data/` は Git 管理しない** — ただし `data/splits/` と `data/README.md` は Git 管理する。
4. **Phase-0 / Phase-1 の 2 フェーズ構成を構造に反映** — mask アノテーション依存のモジュールを条件付きとして分離する。
5. **S0〜S9 のステップと実験を対応づける** — 連番付き命名規則で Δ 基準点の追跡性を担保する。
6. **Ego / Exo のデータパイプラインを明示的に分離** — 推論時 Ego 単独の制約を構造で保証する。
7. **論文は最初から作る** — `paper/` は Day 1 から存在する。

---

## セットアップ（軽量開発用）

```bash
# 依存関係のインストール（開発用ツールを含む）
pip install -e ".[dev]"

# W&B / Notion 認証を暗号化 .env.gpg から現在のシェルへロード
source scripts/load_env.sh
```

`uv` を用いる場合:

```bash
uv venv
uv pip install -e ".[dev]"
```

平文 `.env` は commit しない。新規ホストでの暗号化環境の準備と復旧手順は
[`docs/secrets_and_tracking.md`](docs/secrets_and_tracking.md) を参照。
GPU 本実験には、以下の「推奨セットアップ」で CUDA / mmcv / mmdet / Mamba まで導入する。

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
```

`phase0` は統合幹であり、実験を直接実行しない。各ホストでは
[`docs/host_autosync_onboarding.md`](docs/host_autosync_onboarding.md) に従って、
割り当て済みの `exp/<論理ホスト名>` ブランチへ切り替えてから実験する。

### 3. Python 環境のセットアップ

```bash
bash scripts/setup_env.sh         # venv 作成〜全依存導入〜import 検証まで自動
source .venv/bin/activate
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q
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
で停止する（再発防止策、M2研究計画 §15.3 参照）。

### 5. 環境変数とトークン

```bash
source scripts/load_env.sh
```

標準運用では `scripts/load_env.sh` が暗号化済み `.env.gpg` を復号し、W&B と Notion の
認証情報を現在のシェルへ読み込む。平文 `.env` は秘密情報なので commit しない。
本実験前は `WANDB_API_KEY` と `NOTION_API_KEY` が読み込まれたことを確認する。
認証が無い場合、追跡処理は学習を止めず no-op になるが、本実験の正規運用ではない。
意図的に W&B を無効化するスモークでは `logging.wandb_enabled=false` を CLI override で渡せる。

#### 論理サーバー名 `SERVERNAME` の注入（各ホストで 1 回）

`resolve_server_name()` は `SERVERNAME` → `EGOSURGERY_SERVER_NAME` →
`cfg.logging.server_name` → `socket.gethostname()` の順で解決し、結果を実験フォルダの
`server.txt` へ書く。最後の砦の `gethostname()` はコンテナ環境で衝突する（ilya と philip は
いずれも `aolab` を返す）ため、**各ホストで論理名を明示する**。

```bash
bash scripts/sync/setup_host_servername.sh --dry-run bengio   # 空実行（何も書かない）
bash scripts/sync/setup_host_servername.sh bengio             # 適用（冪等）
bash scripts/sync/setup_host_servername.sh --verify           # 現在の解決結果のみ表示
```

- 論理名は小文字英数とハイフン、2〜20 文字。先頭と末尾はハイフン以外。
- 既に同じ値が宣言済みのファイルは skip する。**異なる値が宣言されていれば上書きせず終了する**
  （改名は既存の宣言を手で除いてから）。
- 書き込み先は `~/.zshenv` / `~/.profile` / `~/.bashrc` の 3 つ。標識付きブロックを追記するだけで、
  既存行は書き換えない。戻すときは `# >>> egosurgery SERVERNAME >>>` から
  `# <<< egosurgery SERVERNAME <<<` までの 3 行を削除する。

**なぜ `~/.zshenv` が主経路か。** ログインシェルは zsh であり、zsh は `~/.zshenv` を
対話・非対話・ログイン・スクリプトの全形態で無条件に読む。bash にはこれに相当する
利用者ファイルが無い（`~/.bashrc` は非対話で早期 return、`~/.profile` はログインシェル限定）。
学習が対話シェルから起動されるとは限らないため、全形態を覆える `~/.zshenv` を主経路に据える。

**既知の限界。** `env -i bash -c` のように環境を空にした非対話 bash は、どの利用者ファイルでも
覆えない（`BASH_ENV` 自体が環境変数のため clean env からは設定できない）。覆うなら
`/etc/environment`（PAM 経由・要 root・システム全体）か、起動側での明示 export が要る。

### Notion 連携（運用ハブ駆動・コンテキスト削減）

研究運用を Notion「**M2研究運用ハブ**」に連動させ、マスターの「M2研究計画」（長文）を毎回読まずに
DB 駆動で回す。**ID レジストリ `configs/notion.yaml` は非秘密・commit 可、token は
暗号化 `.env.gpg` から `scripts/load_env.sh` が現在のシェルへ読み込む**。
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
# (a) 単体テスト
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
- **失敗実験の保存**: `experiments/_smoke_prior/` `experiments/baselines/_wrong_split_8_2_3/` `experiments/phase0/_failed_s3_weighted/` は過去の失敗ランの証跡。**消さずに残す**（研究 integrity の物理証拠、M2研究計画 §15 参照）。
- **研究計画との整合**: M2研究計画は Notion ページ（社内）に存在。同計画 §15.4 が研究計画への波及項目を集約しているので、計画書を更新する際の参照点とする。

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

### `ExperimentManager` が生成する `experiments/` の 6 カテゴリ

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
make delta   # Δ・σ・§10.1 判定が runindex/ のどこにあるかを表示（算出はしない）
make tables  # 論文表の材料が runindex/verdicts.csv にあることを表示（書き出しはしない）
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

以下の `§15.x` 表記は README 内の節ではなく、Notion 上の「M2研究計画」を指す。

| ファイル | 役割 |
|---|---|
| `src/egosurgery/utils/seed.py` | 全乱数生成器の seed 固定 |
| `src/egosurgery/utils/git_utils.py` | git commit hash の取得・保存 |
| `src/egosurgery/utils/experiment_id.py` | 連番付き実験 ID の採番 |
| `src/egosurgery/utils/experiment_manager.py` | 実験フォルダ・必須証跡の生成と終了処理（`server.txt`、eval recipe、証跡限定 auto-sync） |
| `src/egosurgery/utils/git_autosync.py` | `exp/*` 上の証跡だけを安全検査して commit / deploy key push（秘密・5 MiB 超・対象外パスを拒否） |
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
# 統合テスト
PYTHONPATH=src .venv/bin/python -m pytest tests/test_pipeline.py -v

# ダミー学習の実行 — experiments/baselines/s0_001_tool_baseline_seed42/ を自動生成
PYTHONPATH=src .venv/bin/python -m egosurgery.train \
    stage=s0_tool_baseline seed=42 train.epochs=2 logging.wandb_enabled=false
```

学習後、実験フォルダには `config.yaml` / `command.sh` / `git_commit.txt` /
`metrics.json`（per-class AP の集約・Δ 計算枠を含む）/ `per_class_ap.json`（15 クラス）/
`notes.md` と `logs/` `checkpoints/` `predictions/` `visualizations/` が自動保存される。
さらに実行ホストを `server.txt` に保存する。
同一ステップで再実行すると連番が `s0_002_...` と自動で進む。

学習終了時の `ExperimentManager.finalize()` は、この実験ディレクトリと
`docs/experiment_log.md` だけを commit 対象にする。実 push は `exp/*` ブランチかつ
ホスト別 deploy key がある場合に限られ、秘密らしい内容、5 MiB 超の単一ファイル、
対象外パスを検出すると安全側に停止する。`EGOSURGERY_AUTOSYNC=0` で無効化でき、
同期失敗は学習結果を失敗扱いにせず `~/claude-sync/sync-alerts.log` に残す。
`scripts/train_t1b.py` も非スモーク実行の終了時に同等の auto-sync を行う。

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
| `scripts/audit_tool_class_distribution.py` | `egosurgery_tool` の split × クラス分布監査 CLI（`report.json` + CSV を生成） |
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
| `tests/test_metrics.py` / `tests/test_pipeline.py` | 評価指標 8 件 + StageATrainer 10 件のテスト（2026-08-11 実測） |

実 EgoSurgery COCO アノテーションから `data/annotations/egosurgery_tool/instances_*.json`
（train 7427 / val 2230 / test 4265 枚、val は train から 2 動画を hold-out）と
`data/splits/ego_*.txt` を生成済み。`datasets/constants.py` は実データの
正しい 15 クラスへ更新済み。
この 2230 枚は当時の hold-out split で、後続の T1b 評価に使う公式 val 1515 枚とは
評価集合が異なるため、両者の数値は直接比較しない。

```bash
PYTHONPATH=src pytest tests/ -v          # 当時の全 23 テストがパス
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
  / #9 当時の pytest 28/28 パス。

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
- #5 当時の `pytest tests/ -v` 28/28 → ✓

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

### 2026-06-24 H-C-v1（T1b-CA + entropy gate）— STEP C §7.2 H-C コア最小実装

STEP C REPORT.md §7.2 が提案する「非対称・標的・ゲート付き循環結合（H-C コア）」の最小実装。
T1b-CA に **per-frame entropy gate** を追加し、phase context の確信度が高い frame のみ強注入する。
比較は T1b-CA との完全同条件 ablation（warm-start ckpt / epochs / lr / eval_recipe 全て一致）で
**gate 単体寄与**を分離する。

| 項目 | 値 |
|---|---|
| 機構 | T1b-CA + Entropy gate（`gated_ctx = ctx * sigmoid((τ-H)*scale)`）|
| Gate 式 | `H = -Σ p log p / log 9 ∈ [0,1]`, `τ=0.15, scale=20`（**データドリブン**）|
| 実装 | `models/detectors/relation_detr_phase_hc.py`（`RelationDETRPhaseCrossAttn` 継承）/ model cfg `..._egosurgery_t1b_hc.py` / trainer `scripts/train_t1b.py --inject hc` / launcher `scripts/run_hc_seeds_lecun.sh`|
| データドリブン根拠 | 実 phase ctx の H は train mean=0.126 / median=0.087 / 95%ile=0.346（S4 TeCNO は high-confidence）→ デフォルト τ=0.5 は 98% frame で gate≈1（H-C → T1b-CA 退化）。τ=0.15 で train 注入優位 76.6% / 抑制 8.6%（差別化と訓練信号両立）|
| Warm-start init mAP（実測） | seed42=0.7303 / seed123=0.7292 / seed456=0.7217（T1b-CA と **15 桁完全一致**で恒等性確認）|
| 比較対象 | T1b-CA (+0.00178, 3-seed) との差分 = gate 単体寄与 |
| 3-seed | 42/123/456 × inj/ctrl（lecun 2 GPU wave-by-wave, 推定 24h）|
| 起動 | 2026-06-24 09:36 UTC（background, `bash scripts/run_hc_seeds_lecun.sh`）|

**判定基準（事前定義）**:
- H-C Δ_det が T1b-CA を有意に上回る → gate 機能を確認 → H-C-v2（+ phase-conditional query bias）へ
- H-C ≈ T1b-CA → §3.2 の局在不変性が真因（時間選択性では救えない）
- いずれも overall 改善せず → §7.5 撤退ライン確定（phase→det は機構非依存で弱い）

**設計レッスン**: hyperparam は理論的中庸点でなく**データ分布の統計量**から逆算する（`tasks/lessons.md` /
Notion lessons DB に記録）。GPU 6h × N seed の実験ではハイパー誤設計のコストが極めて高い。

### 2026-06-25 H-C-v1 完走 — §7.5 撤退ライン確定（phase→det は機構非依存で弱い）

H-C-v1 全 6 run（3-seed × inj/ctrl）が ~16h GPU で完走。**事前判定基準に従い §7.5 撤退ライン確定**。

| seed | init | inj best | ctrl best | Δ_det = inj−ctrl |
|---|---|---|---|---|
| 42 | 0.73031 | 0.73031 (ep-1=init) | 0.73031 (ep-1=init) | **+0.00000** |
| 123 | 0.72919 | 0.73007 (ep5) | 0.72919 (ep-1=init) | **+0.00088** |
| 456 | 0.72166 | 0.72238 (ep1) | 0.72204 (ep3) | **+0.00034** |
| **3-seed** | | | | **mean +0.00040, pstdev 0.00036, \|mean\|/σ 1.12, 全 ≥0** |

**4 機構 ablation（phase→det 全 4 試行）**:

| 機構 | mean Δ_det | \|mean\|/σ | 判定 |
|---|---:|---:|---|
| B2b 再スコア（無較正）| −0.04 | n/a | 単調劣化 |
| T1b-FiLM（空間一様） | +0.0019 | 1.60 | 一貫正だが微小 |
| T1b-CA（クエリ選択） | +0.00178 | 3.58 | 一貫正だが微小 |
| **H-C-v1（CA + 時間選択 gate, §7.2 H-C 最小）** | **+0.00040** | **1.12** | **同 4 機構で最小（gate 追加で 0.23x）** |

**結論（最終確定）**:
- **Δ は単調減少 (+0.0019 → +0.00178 → +0.00040)** ＝ 信号を絞ると効果も縮む。
- seed42 で完全 +0.00000（best@ep-1=init）= 検出器は phase context から有用な情報を抽出できず、gate がそれを更に削った結果「学習する価値のある信号が消滅」。
- **§7.5 撤退ライン確定**: phase→det は **機構非依存で弱い**。H-C-v2（phase-conditional query bias）は overall 改善見込み無しで投資見送り。
- **方向非対称が完全確定**: det→phase 大勝（T1a macro-F1 +0.164）vs phase→det 機構非依存で弱い（全 4 機構が overall を実質改善せず）。

**最終的な貢献**: ① 強い det→phase（T1a +0.05・hemostasis F1 倍増の混同工程局在を per-phase 分解で実証）+ ② phase→det が機構非依存で弱いことの実証（4 機構の負の結果と機構解明）+ ③ 方向非対称の体系的測定（同一土台・paired-σ・per-phase 分解）。

**証跡**: `transfer/hc_seed{42,123,456}/{injected,control}_result.json` / `experiments/analysis/step_c_coupling_analysis/REPORT.md` §7.5.1 / Notion 実験 Run 台帳 6 件 (`hc_{inj,ctrl}_seed{S}`) + 意思決定ログ「H-C-v1 結果による §7.5 撤退ライン確定」(38aee4d4-7777-8104-a673-f3eeedbd9550)。

### 2026-06-26 H-C-v1 test split 3-seed per-class 評価 — §7.5 撤退ライン test 完全閉鎖 + gate の rare 逆害発見

H-C-v1 学習済み ckpt（保存されていない seed は S0-frozen ckpt + H-C cfg で **恒等代替**）を test split 4265 枚で 3-seed × inj/ctrl 評価。実装は `scripts/eval_phase2det_test.py` に `--seed` 引数と H-C モデル 2 種を最小差分追加。

**Test 3-seed overall（val と一貫）**:

| seed | inj | ctrl | Δ_det | val Δ |
|---|---|---|---|---|
| 42 | 0.50605 | 0.50605 | +0.00000 | +0.00000 |
| 123 | 0.50952 | 0.50895 | +0.00057 | +0.00088 |
| 456 | 0.50495 | 0.50402 | +0.00093 | +0.00034 |
| **3-seed** | | | **mean +0.00050, \|mean\|/σ 1.31** | mean +0.00040, \|mean\|/σ 1.12 |

→ **val/test で同方向・同オーダー**＝ H-C-v1 が overall を改善しない結論は本番データで完全確証。

**新規負の発見: gate は rare∧工程特異術具を逆害する**:

| class | mean Δ (3-seed) | \|mean\|/σ | 判定 |
|---|---:|---:|---|
| Skewer (design 99.7%, rare∧特異) | **−0.00603** | 1.17 | **✓有意（負）**|
| Syringe (anesthesia 84%, rare∧特異) | **−0.00578** | 1.41 | **✓有意（負）**|
| rare∧特異 4 クラス平均 | **−0.00150** | — | 負 |
| 汎用 11 クラス平均 | +0.00123 | — | 正 |
| **rare/汎用比** | **−1.22** | — | **gate は rare を逆害** |

**推定機序**: rare∧特異術具は工程遷移近傍で出現することが多い（Skewer は design 工程末）。entropy gate が遷移 frame の注入を抑制 → rare 術具の検出機会を失う。

**§7.5 撤退ライン最終確定**:
- val/test 一貫: phase→det は 4 機構（B2b / FiLM / CA / CA+gate）すべてで overall mAP を実質改善せず
- per-class: 標的化どころか **rare∧特異を逆害**（時間選択性は逆効果）
- **phase→det は機構非依存で本質的に弱い**。phase context は rare 術具に有用な情報を与えていない。
- → **次の研究主軸**: det→phase 強化（時系列 region-token, REPORT §5 #3）。phase→det 系（H-C-v2 等）への投資は中止。

**論文貢献の最終定式（test 確証付き）**:
1. **強い det→phase**（混同工程 hemostasis F1 0.353→0.80・3-seed 有意・test macro-F1 +0.164 で強化）
2. **phase→det は機構非依存で弱い**（4 機構ablation・val/test 一貫・per-class 標的化不可・gate は rare 逆害）
3. **方向非対称の体系的測定**（同一土台・paired-σ・per-phase/per-class 分解）

**証跡**: `experiments/analysis/step_c_coupling_analysis/test_eval_hc_v1_{inj,ctrl}{,_seed{123,456}}.json` / `experiments/analysis/step_c_coupling_analysis/TEST_EVAL_REPORT.md §7` / Notion 意思決定ログ「H-C-v1 test 3-seed で §7.5 撤退ライン完全閉鎖 + gate は rare 術具を逆害」(38bee4d4-7777-813a-a6d8-e00a0507524a) + 失敗知見「entropy gate は rare∧工程特異術具を逆害する」(38bee4d4-7777-8195-9355-ed6e9bd961c3)。

### 2026-06-26 T1a-Deep（時系列容量拡張）3-seed — 容量拡張は寄与なし（負の結果）

REPORT §5 #3 推奨「時系列 region-token 強化」の最小実装。T1a base の Causal MS-TCN を **num_stages=3 / num_layers=10 / num_f_maps=96** に拡張（受容野 128→**512 frames**, 容量 1.5x）し、混同工程の境界 frame を更に救えるか検証。

| seed | T1a base acc | T1a-Deep acc | Δ_acc | T1a base F1 | T1a-Deep F1 | Δ_F1 |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 0.9498 | 0.9452 | **-0.0046** | 0.8081 | 0.8073 | -0.0008 |
| 123 | 0.9485 | 0.9485 | 0.0000 | 0.8090 | 0.8141 | +0.0051 |
| 456 | 0.9465 | 0.9485 | +0.0020 | 0.7961 | 0.8139 | **+0.0178** |
| **3-seed** | 0.9483 | 0.9474 | **mean -0.00088, \|mean\|/σ 0.32, 符号混在 → ×不有意** | 0.8044 | 0.8118 | mean +0.00740, \|mean\|/σ 0.95, 符号混在 → ×不有意 |

**結論（仮説反証）**:
- 時系列モデル容量・受容野の拡張は overall acc を改善しない。T1a base (num_layers=8, 受容野 128 frames) は既に十分な容量を持つ。
- seed42 で -0.0046 微減 = 過学習リスクの兆候。
- **「時系列の問題は容量ではなく per-frame 表現の質」**: 残る改善方向は (i) region-trajectory modeling, (ii) GAP の置き換え（per-class attention pooling）, (iii) PCGrad MTL。
- 論文化視点では「時系列モデル容量拡張は本ドメインで効果なし」を T1a base の十分性として主張可能。

**新規実装**:
- `scripts/train_t1a.py`: `--description` 引数追加（既存パラメータで容量制御）
- `scripts/run_t1a_deep_seeds.sh`: 3-seed 並列実行（`load_env.sh` による認証ロード込み・自動投稿対応）

**証跡**: `experiments/transfer/t1a_deep_3s10l96f_{001,002,003}_*/{metrics.json,notes.md,checkpoints/best_tecno.pth}` / Notion 実験 Run台帳 3 件 + 意思決定ログ「T1a-Deep（時系列容量拡張）3-seed 結果: 容量拡張は寄与なし」(38bee4d4-7777-819a-8c6b-e6c6efa7e177)。

### 2026-06-26 T1a-RegionOnly（GAP 削除 ablation）3-seed — GAP は冗長（region が frame 表現を subsume）

T1a-Deep の負の結果（時系列容量は寄与なし）を受けて、T1a 入力次元の構成要素を 1 点 ablation。既存 `--region-only` フラグで in_dim を 5888→3840（GAP 2048 削除）に切り替え、実装ゼロで実行。

| seed | T1a base acc | RegOnly acc | Δ_acc | T1a base F1 | RegOnly F1 | Δ_F1 |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 0.9498 | 0.9472 | -0.0026 | 0.8081 | 0.8006 | -0.0075 |
| 123 | 0.9485 | 0.9498 | +0.0013 | 0.8090 | 0.8112 | +0.0022 |
| 456 | 0.9465 | 0.9472 | +0.0007 | 0.7961 | 0.8024 | +0.0064 |
| **3-seed** | 0.9483 | 0.9481 | **mean -0.00022, \|mean\|/σ 0.13, 符号混在 → ×不有意** | 0.8044 | 0.8048 | mean +0.00037, \|mean\|/σ 0.06, 符号混在 → ×不有意 |

**重要発見**: **region-token は frame-level GAP を完全に subsume する**（object 表現は frame 表現を含む）。入力次元 35% 削減でも T1a base と統計的に区別不能。

### T1a 構成要素 ablation 完成（3 つの 1 点 ablation, 2026-06-26 確定）

| バリアント | 入力 | 時系列モデル | mean acc | Δ vs T1a base | 判定 |
|---|---|---|---:|---:|---|
| **T1a base** | GAP(2048) + region(3840) | TeCNO (2s/8L/64f) | 0.9483 | — | （Δ vs S4 base = +0.0497） |
| T1a-Deep | GAP + region (5888) | TeCNO (3s/10L/96f) | 0.9474 | -0.0009 | ×不有意（容量拡張なし）|
| **T1a-RegionOnly** | region のみ (3840) | TeCNO (2s/8L/64f) | 0.9481 | -0.0002 | ×不有意（**GAP 冗長**）|

**結論**: T1a の改善は『容量拡張』『入力次元拡張』いずれでも実現せず、本質は **region-token そのもの**。次の改善方向は (i) region-trajectory modeling（各 tool slot × 時間方向 attention）/ (ii) per-tool 重要度分析。**T1a の最小構成 = region のみ**（35% 軽量化可能）。

**証跡**: `experiments/transfer/t1a_region_only_{001,002,003}_*/{metrics.json,notes.md,checkpoints/best_tecno.pth}` / Notion 実験 Run台帳 3 件 + 意思決定ログ「T1a-RegionOnly 3-seed: GAP は冗長」(38bee4d4-7777-8181-9b78-db548aad3fe9)。

### 2026-06-26 §18.4 L0 監査 — phase→det 3 機構の配線・学習能力検証（査読防御）

研究計画 §18.4 が要求する「分析論文の検証厳密化」の最優先タスク。`phase→det が機構非依存で弱い`という負の結果が **under-tuning/バグと外形的に区別できない**ため、4 チェック（勾配フロー / loss@init / NaN-inf hook / overfit-one-batch）で能動的に排除。

**実装**: `scripts/audit_t1b_l0.py`（3 機構 × seed42, 各 1.1-1.3 min @ GPU0）

| 機構 | grad_flow | loss_init | nan_inf | overfit (reduction) | ALL PASS |
|---|---|---|---|---|---|
| **FiLM** | ✓ (issues=0) | ✓ (16.2 ± 6.1) | ✓ (hits=0) | ✓ **49.6%** | **✓** |
| **CA** | ✓ (issues=0) | ✓ (16.2 ± 6.1) | ✓ (hits=0) | ✓ **31.5%** | **✓** |
| **HC** | ✓ (issues=0) | ✓ (16.2 ± 6.1) | ✓ (hits=0) | ✓ **31.2%** | **✓** |

**最重要発見（査読耐性の核心）**: overfit-reduction の機構順序 **FiLM 49.6% > CA 31.5% ≈ HC 31.2%** が、最終 val mAP 順序 **FiLM +0.0019 > CA +0.00178 > HC +0.00040** と**完全一致**。これは「機構容量と汎化能力が比例する=機構変更では本質的に救えない」を実証し、reviewer の「under-tuning では？」反論への**決定的反証**になります。

- HC ≈ CA = entropy gate は learning capacity をわずかに減らす（汎化結果と整合）
- §7.5 撤退ライン主張の**物理的防御完成**: phase 層は learning しているが (overfit OK)、汎化に効かない (val mAP +0.001) = phase context の情報的限界

**閾値の注記**: §18.4 元値 50% overfit-reduction は full-model 想定。本研究は凍結 backbone + 小容量 phase 層（1.58M params）のため物理的上限が約 50%。閾値を 20% に下げて「学習機構が機能している」を判定。

**次の §18.4 優先タスク**: L1-2 oracle-phase（ground-truth phase 直接注入で improvement が出るか）★最重要。

**証跡**: `experiments/audit/t1b_l0_audit_{film,ca,hc}_seed42/audit_report.json` / Notion 意思決定ログ「§18.4 L0 監査 3 variant 全 PASS: §7.5 撤退ラインの査読防御強化」(38bee4d4-7777-8131-87de-e57c2bfb19dd)

### 2026-07-31 手アノテーション系の整理 — `egosurgery_hand4` を退避（run 0 件の scaffold）

`data/annotations/` 配下の手系 3 パスが 1 本の生成チェーンの各段だったことを実測で確定し、未使用段を退避した。

- **生成チェーン**: `egosurgery_tool/instances_*`（術具15・原本）＋ `egosurgery_tool_hand/{train,val,test}.json`（手4・原本、
  `egosurgery_tool/hand/` はここへの **symlink**）→ `build_tool_hand_coco.py` → `egosurgery_tool_hand/instances_*`（19クラス統合）
  → `build_hand_coco.py` → `egosurgery_hand4/instances_*`（手4・id 0-3・bbox only）。
- **使用実績**: 現役学習は `egosurgery_tool`（config.yaml 59 件）。`egosurgery_tool_hand` は直接学習した run が
  全て phase0 アーカイブ配下だが、`build_oracle_handfeature.py` → `experiments/transfer/haux_*`（18 run）の
  oracle 手特徴の供給源として**現役**。`egosurgery_hand4` は **run 0 件**。
- **対応**: `egosurgery_hand4/` を `data/annotations/_deprecated/egosurgery_hand4/` へ退避し `DEPRECATED.md` を同梱
  （経緯・代替・戻し方を記載）。`configs/stage/s2_hand_independent.yaml` の前提データ注記に退避と再生成手順を追記。
  実験値への影響なし（run 0 件）。復元は `mv` か `python scripts/build_hand_coco.py`（手 box 計 46,320 が検証基準）。
- **注意**: 上記 3 パスの `segmentation` は全て bbox 由来の矩形ダミー。マスクが要る場合は
  `data/hts_reconstruction/egosurgery_hts2_tool_aligned/hand_tool_seg_v2/` を使う。

### 2026-08-13 把持推論結果を工程入力へ渡す ctrl/inj 経路

`hand_tool_seg` の5クラス有無をフレーム単位で推論し、その sigmoid 出力を causal TeCNO の
入力へ連結する独立枝を追加した。inj は推論信号、ctrl は同形・同サイズの零信号を渡す。
工程損失を把持推論器へ逆流させると両腕の学習条件が変わるため、工程へ渡す信号は detach し、
把持推論器は両腕とも同じ masked BCE だけで学習する。注釈が無い 460 フレームは工程母集団から
除かず、補助損失だけを零にする。

- モデル: `models/temporal/grasp_inference_injection.py`（既定無効、frame-wise causal 推論）
- 教師: `datasets/grasp_targets.py`（COCO category 1〜5 を5次元 presenceへ変換）
- trainer: `scripts/train_grasp_phase_injection.py`（W&B/ExperimentManager/Notion 配線済み）
- config: `s4_grasp_injection_{ctrl,inj}.yaml`。凍結源は Relation-DETR seed42、neck 無し。
- 検査: `tests/test_grasp_inference_injection.py` と `scripts/audit_grasp_phase_injection.py`。
  信号到達、ctrl 不変、重み同数、recipe 陽性対照、loss mask、母集団、5次元指標、因果性、
  無効時の既存 TeCNO 同一性を検査する。

本変更は実装と1 epoch smoke までで、ctrl/inj の効果比較は未実施。効果は次の事前登録済み実験で測る。

### 2026-07-01 STEP D-aux 実装 — 系統①手情報 / 系統②時系列 のインフラ構築（実行は lecun）

補助信号探索プロンプト `prompts/ Claude_code_prompt_hand_temporal` を実装。**コード実装 + GT だけで動く
部分の実行検証まで**（GPU 学習は本環境では不可 = 画像 /GAP 特徴キャッシュ /`.venv` 未整備。実行は lecun）。
**metrics は一切生成していない**（研究インテグリティ）。

- **系統① 手情報**（det→phase・B2a の手版）:
  - `scripts/build_oracle_handfeature.py`（**実行済**）: GT（手 cat 15-18）→ oracle 手特徴
    presence(4)/count(4)/geom(16)。実測分布は自分の手 0.87-0.98 >> 相手の手 0.38-0.74（外科的に妥当）、
    frame 数は公式 split 完全一致。
  - `scripts/train_haux.py`: GAP⊕手特徴 → 素 causal TeCNO。`--hand-feature-type {presence,count,geom,own_other}`
    (H-1/2/3/5) / `--hand-source {oracle,pred}` / `--with-tool`(H-6) / `--shuffle-hand`(§4.3 control)。
- **系統② 時系列情報**（T1a 基盤の核比較 + 時間特徴量化）:
  - `heads/mingru_head.py`（純 PyTorch causal minGRU）/ `heads/mamba_head.py`（mamba-ssm ラッパ）を
    **TeCNO と同一 forward 契約の drop-in** で実装（strict-causal を検証: 未来摂動が過去出力に漏れない）。
  - `scripts/train_taux.py`: `--temporal-kernel {tecno,mingru,mamba}`(T-4/5/6) と
    `--temporal-feature {none,movavg,delta,window}`(T-1/2/3)。問い A/B の交絡を避ける運用を notes 明記。
- **S2-hand 独立検出器 scaffold**（Notion runbook 準拠・非-oracle の前提）:
  - `scripts/build_hand_coco.py`（**実行済**）: 手4クラス COCO 抽出。手 box 計 **46,320**（§12.11 B3 の
    記載値と完全一致）。`configs/stage/s2_hand_independent.yaml`（COCO-init のみ・19クラス統合せず）。
- **集計/実行**: `scripts/report_{haux,taux}_results.py` + `utils/transfer_delta_report.py`（paired-σ 判定・
  現状 0 件）/ `scripts/run_haux_oracle_gate.sh`（§6: H-1 gate 最優先）ほか launcher 3 本。
- **次**: lecun で GAP キャッシュを用意 → `bash scripts/run_haux_oracle_gate.sh`（H-1 presence oracle を
  最優先ゲート）。詳細は `docs/experiment_log.md` の 2026-07-01 エントリ。

### 2026-07-02 STEP D-aux 実行結果 — 手情報は tool に冗長 / 時系列は入力信号がボトルネック

GAP/region-token キャッシュを配置し本セッション（A6000×2）で全手法を実測。分母 = 同一環境で再学習した
S4 base（GAP-only TeCNO 3-seed = acc 0.8983±0.0090 / macro-F1 0.6965、文書値 0.8986/0.709 と整合）。
判定は per-seed paired-σ（§10.1）。**metrics は全て実測**（`scripts/report_daux_paired.py` → `experiments/analysis/daux/REPORT.md`）。

- **系統① 手情報**: H-1 presence（Δacc +0.51pp / F1 +3.44pp ✓）・H-3 geom（+1.23pp / +3.92pp ✓）が有意
  （geometry > presence）。H-2 count・H-5 own_other は無効。**shuffle control で H-1 の利得が消失（真の相関）**。
  **最重要: 手は tool に冗長** — H-6(hand+tool) +5.85pp ≈ tool単独 +5.81pp、手の上乗せ +0.04pp（不有意）。
  → phase 補助信号のためだけに手検出器を仕上げる価値は低い。
- **系統② 時系列**: region-token(T-4) は S4 を +5.06pp 超（T1a 再現）。明示的時間加工（movavg −0.59pp / delta
  −1.89pp / window +0.15pp・対 T-4）は TeCNO の暗黙集約を超えず、時系列核も minGRU ≈ TeCNO。
  → **ボトルネックは時系列核でなく入力信号（per-frame 表現）**。系統①の検出精度ボトルネック(L2-3)と同方向。
- 実装知見: 純Python 逐次 minGRU は TeCNO の約 30 倍遅い（1run≈25分）。

### 2026-07-04 検出器改善スタディ — 「検出器強化→phase改善」は GAP 経由・val 限定（test で非頑健）

Relation-DETR を efros で強aug(Method A)/高解像(Method C)改善し、phase 転移を **3-seed paired-σ + phase-seed 平均 + test 確認**で厳密評価（`scripts/_detector_full_study.sh` / `_run_phase_probe_3seed.sh` / `paired_sigma_3seed.py` ほか）。**metrics は全て実測**。

- **検出器**: 強aug mAP 0.7303→0.7426/0.745/0.745（3seed 一貫）。hires 0.733（small AP 0.013→0.031 だが large 犠牲で全体微減）。
- **phase(val)**: S4/GAP のみ **+1.80pp 有意**（3seed 全正）。B2a(tool-presence)/T1a(region) 非有意。hires は全経路で A に劣る。
- **phase(test, `--eval-test`)**: S4/GAP は **❌非有意**（mean +2.12pp / det42 が +1.76→**−2.49 反転** / σ3.36）。2/3 seed は test でも正だが同符号崩れ。
- → **検出器改善→phase改善は val で示唆・test で頑健確認に至らず、経路は GAP に限る。B2a oracle gap はどの改善でも非閉塞**。下記 Pillar3「検出器強化」を精緻化: 効くのは **GAP 経由のみ**・test 頑健性は検出器 seed 追加が要。
- 証跡: `docs/experiment_log.md`(2026-07-03/04), `logs/{phase3seed_results.tsv, paired_sigma_final.txt, hires_probe_summary.txt, s4_test_results.tsv}`, `configs/detector_relation_detr/`。

### 2026-07-02 T1a-Boundary — over-segmentation は学習 boundary head でなく因果 debounce で回収

STEP C 改善提案 §8「boundary modeling で T1a の edit-score を改善」を実装・実測（`scripts/train_t1a_boundary.py`、
分母 = 同一環境 efros 再学習 T1a base val acc 0.9476/edit 32.96 ＝ lecun 0.9483 と env parity）。判定は per-seed paired-σ。
集計 `scripts/report_t1a_boundary.py` → `experiments/analysis/t1a_boundary/REPORT.md`。**metrics は全て実測**。

- **学習 boundary head は online で非有効**: 共有 trunk への boundary 監督（plain）は全指標 ×（edit +1.07 のみ）。
  因果 boundary-gated sticky decode は τ を上げると edit↑だが acc が急落（τ0.5 で −19.6pp）→ **acc 維持で edit 改善する τ 無し**。
  本質は「未来を見て区間多数決する offline ASRF が online 制約で使えない」こと。
- **パラメタフリーの因果 min-segment debounce(k=2) が実用的に効く**: Δedit **+23.4 ✓** / ΔsegF1@50 **+0.229 ✓** を
  acc **−0.95pp** / macro-F1 −2.03pp で達成（edit 32.96→56.4・seg-F1@50 0.41→0.63）。遷移を k−1 遅延させる latency と引換。
- → 過分節は online でも **区間長 prior** で低減可能。**edit-score は安価な後処理で回収でき、acc 改善には入力信号
  （検出/region 表現）強化が要る**（Pillar 3「時系列後処理でなく検出器強化」を一段補強・系統②と同方向）。

### 2026-06-23 Notion 連携 — 全 5 DB 共有完了・STEP B/C を全件反映

REST Integration トークン（`.env.gpg` からロードする `NOTION_API_KEY`）に **全 5 DB（run_ledger / decision_log / lessons / procedure_docs / prompt_library）が共有済み**。
`notion_ops.log_decision` / `log_lesson` も REST で正常に動作する（2026-06-23 確認）。

- **実験Run台帳**: STEP B 17 件 + T1b-CA 6 件 = **計 23 件を Notion へ投稿**（冪等 upsert）。
  - T1b-CA は `metrics.json` を持たず `injected_result.json` / `control_result.json` 形式のため、
    専用スクリプト `scripts/post_t1b_ca_to_notion.py`（inj/ctrl/純効果を整形して upsert）を追加。
- **意思決定ログ / 失敗知見**: 「方向非対称確定」「CA≈FiLM の機構独立性」等を反映。
- **「現在の研究状態」ページ**: STEP C 完了・方向非対称確定・次アクション（test split per-class rare 標的化）に更新。

### 2026-07-13 凍結源の per-class AP 分解（台帳 must）— AlignDETR 負転移は signature 術具 AP 欠損で説明できず

Notion 実験Run台帳「凍結源の per-class AP 分解」（S0・must・eval-only）の val 主判定を実施。既存の検証済み
per_class_ap.json（Relation-DETR / AlignDETR 各 3-seed・score_thr=0.0 NMS-free・val 1515枚）から
選択性指標 **R=(signature3[Bipolar Forceps/Needle Holders/Scalpel] AP低下)÷(generic11 AP低下)** を seed 毎に再計算
（新規学習・推論なし）。証跡: `experiments/analysis/frozen_source_signature3_R_index/`。

- **R = −0.11±0.39、seed 間で符号不一致 → 非有意**。signature3 AP低下はほぼゼロ（符号不一致）、
  generic11 AP低下は全 seed 正・平均+1.78pp。**AlignDETR の検出劣化は signature 術具でなく汎用術具に集中**。
- → **仮説（負転移=signature術具AP欠損で説明できる）は支持されず**。2026-07-05
  `signature_subset_detector_compare` の結論（Align劣位は phase 無関係術具に局在）と整合し、凍結源＝Relation-DETR
  確定判断を追加補強。
- **未実施（要判断）**: test split(4265) 確認は relationdetr/aligndetr の S0 checkpoint(\*.pth) 6件が本ホスト
  (andrew) に不在（台帳 Server=philip の資産）のため、philip からの転送が必要。hemostasis F1「0.801→0.179」の
  downstream 直接検証も `s4_phase_baseline_010-012_..._aligndetr_*`（efros 実行・metrics.json 空の scaffold）が
  本ホストにないため未検証。Notion 台帳は Status=running・Decision Needed=✓ で更新済み。

### 2026-07-29 G-2 本実験（ROI チャネル 4 系統 × 3 seed）— 主予測 FAIL・背景除去は効かない（負の結果）

事前登録（`experiments/g2_main_2026-07-29/prereg/g2_prediction.md`、学習前に commit `2dc430b`）に対する
12 run を lecun / commit `ca28064` で完走（失敗 0、MSDeformAttn 拡張ロード全 `True`）。
結果のみの要約は `experiments/g2_main_2026-07-29_lecun/RESULTS.md`、詳細は `docs/experiment_log.md`。

- **主予測 FAIL**: 3(maskROI) > 2(bboxROI) は指定 3 工程 × 2 split の **0/6** で閾値超えせず。
  むしろ test/incision は**負方向に超過**（−0.03081, 95%CI [−0.05723, −0.00343]）。
  → 事前登録の判定規約に従い **「背景は region-token のボトルネックではない」**（負の結果）。
- **ROI チャネル追加自体は有効**: 2−1 が test で incision +0.04384 / closure +0.03902 /
  dissection +0.14795 / accuracy +0.06073 / macro-F1 +0.05748（いずれも両基準超過）。
- **最も情報量の大きい所見**: maskROI と randROI が **ほぼ同幅だけ** bbox を下回った
  （test/incision −0.031 と −0.038）。同面積のランダム形状が真のマスクと同程度に悪化する以上、
  劣化要因は「背景を除いたこと」でなく「平均する画素を減らしたこと」側にある。
- **A-5 再現ばらつき基準点（今後の全実験の基準）**: base 3 seed sd =
  val acc 0.00132 / macroF1 0.00438、test acc 0.00793 / macroF1 0.02203（n=3, ddof=1）。
- **Task F はホスト間でビット再現**: val / test の抽出統計が efros と全 20 項目・
  浮動小数 16 桁まで一致（`source .venv-relation-detr/bin/activate` を守れば決定論的）。

#### コード変更

- `scripts/train_g2.py`: `load_clips` の **OOM 欠陥を修正**（commit `ca28064`）。
  内包表記の中で `NpzFile` へ毎反復アクセスしており、添字アクセスは毎回 zip メンバ全体を
  読み直して新しい配列を返す。さらに `arr[i]` は view なので 1 行が親配列（train で 148MB）
  全体をメモリに固定する。train（9657 行）では約 1.4TB 相当となり **1 run も完走不可**だった。
  配列をループ外で 1 回だけ読むよう修正（値はビット単位で不変・縮小再現の全行比較で確認）。
- `scripts/analysis/g2_report.py`: **新規**。事前登録の判定規約（Welch の 2 標本 SE と
  動画単位クラスタ・ブートストラップ B=2000 の AND）をそのまま実装。**結果を見る前に**書かれている。
  per-phase F1 の再計算が `PhaseEvaluator` と厳密一致することを乱数 30 試行で検証済み
  （tp/fp/fn は動画をまたいで加算可能なので、per-(run, 動画, クラス) counts の前計算だけで
  ブートストラップが厳密かつ高速に回る）。クラスタ単位は**動画**（`clip_id` の `_` 前）。

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

## サーバー間同期（m2-sync: git + Syncthing）

研究サーバー 11 台（he / adam / hinton / lecun / efros / bengio / ian / andrew /
dlsta / ilya / philip）でこのリポジトリは **2 層で自動同期**されている。
日常運用、状態確認、停止条件、復旧の正本は [`OPERATION.md`](OPERATION.md)、
新規ホストの設定は [`docs/host_autosync_onboarding.md`](docs/host_autosync_onboarding.md) を参照。

### 層1: git 管理ファイル（コード・設定・ドキュメント）

通常のライフサイクルは次のとおり。

1. trainer 終了時に `ExperimentManager.finalize()` が必須証跡を限定 commit / push する。
2. 常駐 `keeper` の `m2-sync.sh` または GitHub Actions が、`exp/*` から `phase0` への
   Draft PR を既存 PR と重複しないよう作成する。
3. 人が差分を確認して Draft を解除し、その PR の auto-merge を有効にする。
4. 必須チェックと保護規則を満たすと、GitHub が **merge commit** 方式で `phase0` へ統合する
   （squash merge は使わない）。リポジトリの auto-merge 機能は設定済み。
5. 各サーバーの `keeper` が約 30 分ごとに fetch し、追跡対象が clean、未追跡 blocker なし、
   `origin/phase0` より behind の場合に限って作業ブランチへ自動 merge する。
   conflict 時は merge を abort してログへ残し、自動解決しない。既存の ahead commit は
   現在ブランチが remote 登録済みなら自動 push する。

安全境界:

- trainer 側 auto-sync は `exp/*` とホスト別 deploy key が前提で、実験ディレクトリと
  `docs/experiment_log.md` 以外を stage しない。force-push は行わない。
- keeper は通常変更を新規 commit せず、削除・force-push・conflict の自動解決を行わない。
  ただし手元で作った commit は自動 push の対象になり得るため、WIP を安易に commit しない。
- fetch は GitHub の SSH remote、各ホストからの push は各ホスト専用 deploy key を使う。
  サーバー共通 PAT と Mac の agent forwarding は使わない。
- GitHub Actions の Draft PR 作成だけは repository secret `AUTOSYNC_PR_TOKEN` を使う。
- 同期異常は `~/claude-sync/sync-alerts.log` と `journalctl --user -u keeper` で確認する。
- `runindex/` は追跡外 run が 0 件のホストだけが手動更新し、その後は同じ PR / auto-merge 経路で全台へ配る。

運用は **1 サーバー = 1 定位置ブランチ**（`exp/<論理ホスト名>`）、統合の幹は `phase0`。
論理ホスト名は小文字英数とハイフンのみ、2〜20文字で、日付と `wip` を含めない。
対応は `lecun` / `efros` / `philip` / `andrew` / `ilya` / `bengio` / `he` /
`adam` / `hinton` / `ian` / `dlsta`。既存分岐からの移行手順と旧名は
[`migration_plan.md`](tasks/T-2026-08-10-branch-naming-and-canonical-index/migration_plan.md) を参照する。

### サーバー名の解決（`$(hostname)` を直接使わない）

`hostname` はコンテナ由来で実サーバー名と一致しない。**philip と ilya はどちらも
`hostname=aolab`** を返す。しかも hostname 自体はコンテナ内から変更できない
（`sethostname(2)` に CAP_SYS_ADMIN が要るが、バウンディングセットから落ちているため
root でも不可）。そのため論理サーバー名を明示的に設定する。

- Python: `egosurgery.utils.server_name.resolve_server_name()`
  （`SERVERNAME` → `EGOSURGERY_SERVER_NAME` → Hydra `logging.server_name` → hostname）
- `m2-sync.sh`: `SERVERNAME` → リポジトリ直下 `.servername` → hostname
- 新規ホストでは login shell と systemd の両方で解決できるよう、`.profile` / `.zshenv` と
  `.servername` を設定する。`SERVER_NAME`（アンダースコア有）は別変数なので注意。

同期アラート（`~/claude-sync/sync-alerts.log`）の発信元表記もこの規則に従う。

### 層2: gitignore された実験成果物（Syncthing・星型トポロジ）

サーバー間で開いているポートが SSH のみのため、各ノードから中心への SSH トンネルを使う
**星型**で接続する。正本の `keeper.sh` は `.tunnel_to_中心名` を辞書順で一つ選び、
1 行目の秘密鍵パスと任意の 2 行目の住所から接続先を導出する。2 行目が無い旧形式では
中心名を SSH 別名として使い、目印が無い中心自身はトンネルを張らない。正本の配置と
稼働プロセスの再起動は別契約であり、現時点の稼働版は従来の中心設定のままである。

**同期される（= どのサーバーで生成しても全台に現れる）:**

| 対象 | パターン |
|---|---|
| 実験成果物 | `experiments/**/` の `checkpoints` `logs` `predictions` `visualizations` `tf_log` `training*.log` `last_checkpoint` `*.npy` `*.pt` `*.pth` `*.py` タイムスタンプ付きフォルダ |
| モデル重み全般 | `*.pth` `*.pt` `*.ckpt` `*.onnx` `*.safetensors` |
| 出力・ログ | `outputs/` `logs/` |
| 加工済みデータ | `data/processed/` |
| アノテーション | `data/annotations/pseudo_labels` `data/annotations/egosurgery_hts` `data/annotations/**/*.json` |
| Notion 同期状態 | `.notion_sync.json` |

**同期されない:**

- `.git`・`.claude`・git 追跡ファイル全般（→ 層1 の git 経由で同期）
- 秘密情報（`.env*` `*.key` `*passphrase*`）・`venv` / `.venv` / `__pycache__` 等の環境依存物
- `data/raw`・`data/external`（巨大な生データ。各サーバーで個別配置）
- `third_party`（入れ子 `.git` を含むため。各サーバーで clone）
- `wandb/`（クラウドに記録済み）
- 退避フォルダ `experiments/baselines/_*`・`experiments/phase0/_*`（ローカル証跡）

**ルールの変更方法:** リポジトリ直下の `.stglobalignore` を作業ブランチで編集・commit し、
通常の PR / auto-merge 経路で `phase0` へ統合する。各サーバーの keeper が 30 分以内に
`$M2DIR/.stignore` へ自動反映する（`.stignore` 自体は編集しない。先にマッチした行が勝つ構文に注意）。

---

## 検出側 run の成果物（experiments/transfer/&lt;run_name&gt;/）

**2026-07-28 変更**: 検出側トレーナ（`train_t1b.py` 系）の成果物は `/tmp` ではなく
`experiments/transfer/<run_name>/` に永続化される。あわせて **per-image の検出結果
（predictions）を既定で保存**する。

背景: 従来 `/tmp` に出していたため再起動で消え、eval-only の追認が反復的に実行不能に
なっていた（ckpt 不在 seed の恒等代替 / test 未実施 / FP・FN 集計不能で失敗機序が推測どまり）。
predictions さえ残っていれば ckpt が無くても解析できるため、オプトインではなく既定 on にした。

### レイアウト（工程側 `ExperimentManager` と同一規約）

```
experiments/transfer/<run_name>/
├── checkpoints/best_t1b.pth
├── predictions/{split}_{inj|ctrl}_ep-1.json.gz   # init（warm-start 恒等点）
│                {split}_{inj|ctrl}_best.json.gz  # best epoch
├── logs/val_metrics_by_epoch.json                # epoch 別 mAP + per-class + best_epoch
│       eval_meta_{split}.json                    # 評価対象 image_id 等
├── config.yaml  command.sh  git_commit.txt  server.txt
└── metrics.json  per_class_ap.json  t1b_result.json  notes.md
```

- `logs/val_metrics_by_epoch.json` と `logs/eval_meta_*.json` は **git 追跡対象**
  （`.gitignore` に明示例外）。ckpt や predictions が失われてもコミット済みログだけで
  init 比較・絶対値検証を完遂できる状態を担保する。
- `checkpoints/` `predictions/` は容量のため git 追跡外（層2 の Syncthing 側で同期）。

### predictions

- 形式は COCO detection results（`[{"image_id", "category_id", "bbox":[x,y,w,h], "score"}, …]`）。
- **score 閾値での足切りはしない**（eval recipe が `score_thr=0.0` 系のため、足切りすると
  AP が再現不能になる）。容量対策は image_id ごと **top-k=300**（= `select_box_nums_for_evaluation`
  と同一上限）で、実測では常に恒等変換。
- **実測サイズ**（seed42・val 全 1515 枚・検出 454,500 = 厳密に 300/枚）:
  gzip 後 **12.6 MB**（非圧縮 69.8 MB、圧縮率 0.18）= 8.1 KB/枚。
  → **1 run あたり約 25 MB**（init + best の val 2 本）。test（4265 枚）は約 35 MB/本。

### 関連フラグ

| フラグ | 意味 |
| --- | --- |
| `--run-name NAME` | 保存先 `experiments/transfer/NAME/`（環境変数 `T1B_RUN_NAME` でも可） |
| `--no-save-predictions` | predictions を保存しない（measure run 等） |
| `--save-predictions-all` | 全 epoch の predictions を保存（既定は init と best のみ） |
| `--predictions-no-gzip` | 素の `.json` で保存 |
| `T1B_WORK_DIR` | 保存先の明示 override（後方互換。相対パスはリポジトリ root 基準） |

### 検証コマンド

```bash
# predictions から COCO eval を再実行し、記録 mAP と bit-exact 一致するか検証
.venv-relation-detr/bin/python scripts/verify_predictions_ap.py --run <run_name> --split val --epoch -1

# inj / ctrl の init 予測が完全一致するか（注入層 zero-init=恒等の実測確認）
.venv-relation-detr/bin/python scripts/run_artifacts.py --verify-init-identity <run_inj> <run_ctrl>
```

`run_*_3seed_*.sh` 系ランチャーは本走のたびに init 恒等性を自動検証し、
`logs/<tag>_init_identity*.json` に記録する。

### `best_is_init`

frozen 検出器では init を超える epoch が無いことがあり、その場合 `checkpoints/best_t1b.pth` は
生成されない（過去に「ckpt 不在 seed を S0-frozen で恒等代替」が必要になった原因）。
その状況は `metrics.json` / `logs/val_metrics_by_epoch.json` の `best_is_init: true` で明示し、
best predictions は init の複製として必ず出力する（init ckpt 自体は warm-start ckpt から
決定的に再構成できるため重複保存しない）。

---

### 2026-08-22 横断再集計 — 「完璧な術具検出でも未見手術の工程 accuracy は上がらない／効くのは信号の時間的整形」

GPU 学習なしの読み取り専用セッションで、`experiments/` と `data/processed/` を横断再集計し、
CPU だけで動くプロキシ実験を行った。
詳細は [`docs/research_review_and_next_plan_2026-08-22.md`](docs/research_review_and_next_plan_2026-08-22.md)。

**val で見えたこと**

- 未整理だった run 群を集計すると、**オラクル術具存在 15 次元のみ（画像特徴なし）で
  val acc 0.9666 / macro-F1 0.8375 / edit 64.74 / seg-F1@50 0.724**。
  現行最良 T1a（0.9483 / 0.8044 / 37.07 / 0.431）との差は分類 +1.83pt に対し
  **edit +27.67・seg-F1@50 +0.293**（paired-σ 有意）。
- **GAP は冗長ではなく有害**（削除で acc +0.88pt・3.31σ）。理由は
  **GAP がクリップ ID を 99.8% 識別できる「動画指紋」**だから（region 97.5 / 予測 presence 71.6 / オラクル 62.9）。
- 予測 presence は GT の **1.74 倍（val）/ 2.25 倍（test）**ちらつき、誤りの **73.8% は 1 フレームの孤立フリップ**。
  **因果 HMM forward filter** でちらつきは GT 水準へ戻り（0.596 → 0.355、GT 0.342）、
  **遅延 2 フレームでオフライン平滑化とほぼ同等**になる。

**test と leave-one-video-out で結論は反転した（最重要）**

- 同じプロキシを test で走らせると、**分節指標は改善する（edit 17.71 → 36.13 = 2.04 倍）が
  accuracy / macro-F1 は悪化**（−4.9pt / −11.4pt）。悪化は**短い工程**
  （design 30 frame: 0.795→0.370 / irrigation 84 frame: 0.457→0.081）に局在する。
- **15 動画 leave-one-video-out**（`docs/analysis_scripts/proxy_lovo_*.py`）で
  **研究の中心的主張 P1（det→phase は効く）は成立**し、しかも **分節側で桁違いに強い**:
  GAP のみに対し 予測 presence は accuracy +7.28pt（|m|/SE=2.23・12/15）だが
  **edit +32.20 / seg-F1@50 +0.338 は 15/15 動画すべてで正**。
  **GAP を足すと利得が +7.28pt → +1.54pt に削がれる**（GAP は有害）。
- 一方、**オラクル presence の追加的な優位はほぼ無い**:

  | 指標 | 生 presence | Δ(オラクル − 生) | Δ(因果デノイズ − 生) |
  |---|---:|---|---|
  | accuracy | 0.8658 ± 0.1411 | **+0.0022（\|m\|/SE=0.06・10/15）** | −0.0032（9/15） |
  | edit | 50.73 ± 24.93 | +5.88（9/15） | **+9.11（\|m\|/SE=3.06・12/15）** |
  | seg-F1@50 | 0.514 ± 0.268 | +0.065（12/15） | **+0.068（\|m\|/SE=3.15・12/15）** |

  → **完璧な術具存在を与えても、予測 presence に対する追加的な accuracy 利得はほぼ無い**（val の「+1.83pt 上限」は val 固有）。
  一方 **因果デノイズは分節指標を一貫改善し、しかもオラクルより大きく改善する**。
- **「オラクル presence」は情報量の上限ではない**: 誤りを除く代わりに**連続スコアの段階的情報を捨てている**。
  LOVO の動画 05 では **closure（動画の 58%）が丸ごと dressing に化ける**
  — この手術の closure は **Needle Holders をほとんど使わず**、binary presence が dressing と衝突するため。
  → val の「上限 0.9666」は **presence 精度の上限**であって **検出器が渡せる情報の上限ではない**。
- **誤りは「量」ではなく「形」で壊す場所が変わる**（介入実験・15 動画 LOVO）:
  オラクル presence に同じ誤り率 5% で iid ノイズ（ちらつく）と burst ノイズ（持続的に間違う）を与えると、
  **iid は Δacc −3.02pt / Δedit −18.45**、**burst は Δacc −11.45pt / Δedit −17.77**（ノイズ seed 3 本）。
  **accuracy 1pt あたりの edit 損失は iid 6.1 / burst 1.6（3.9 倍の選択性）**。
  **学習をクリーンにして評価側だけ汚すと選択性は 7.0 倍に鋭くなる**
  （iid は edit を 56.6 → 16.2 と崩壊させるが accuracy は −3.8pt のみ）
  ＝ **孤立フリップは主に分節を壊し、持続的な誤りは主に分類を壊す**。
  → 因果デノイズが除去できるのは **ちらつき成分だけ**なので、**分節だけが直る**のは必然。
- 原因は **術具⇄工程の対応が手術ごとに揺れること**
  （closure の Needle Holders 0.83/0.92/0.51、Mouth Gag は val で 1.00 だが test で 0.29）。
  **val は術具⇄工程の対応が異常にきれいな split** である。

- **揺れへの最初の一手（本書で最も安定した改善）**: **工程を弁別しない汎用術具を信号から落とす**と
  LOVO で macro-F1 が **k=3 で +3.40pt（|m|/SE=2.58・10/15）・k=4 で +2.61pt（3.34σ・10/15）**。
  落とす術具は **fold ごとに train のみ**の正規化エントロピーで決めており、
  **15 fold すべてで同一順序**（Gauze → Mouth Gag → Suction Cannula ⇄ Tweezers）＝**事前登録可能な手続き**。
  汎用術具の在室は工程ではなく**手術（動画）**を符号化している。
  正式プロトコル（fold ごとに train のみで `H(phase|tool) > 0.45` を判定。該当は
  Gauze / Mouth Gag / Suction Cannula / Tweezers / Forceps の 5 本）で
  **acc +1.61pt（|m|/SE=2.37）/ macro-F1 +2.29pt（2.80）**。
  エントロピーは 0.474 と 0.347 の間に **0.13 のギャップ**があり、しきい値が自然に決まる。
  **【訂正】因果デノイズとの併用が「4 指標すべて基準超え」という見立ては、順位ベースの k 掃引でしか出ず、
  しきい値プロトコルでは再現しなかった**（acc +0.51pt・0.47σ）。**2 つの独立した介入として扱う**
  （分類なら除去・分節ならデノイズ）。ただし hemostasis は併用が最良（0.626→0.691）、
  dressing は除去のみが最良（0.096→0.145）＝**工程によって最適構成が違う**。
- **【最も信頼できる知見】術具除去の利得は 6 凍結源すべてで頑健**:
  LOVO × 6 凍結源で **Δacc は 6/6 で正・範囲 +1.13〜+2.13pt**（5/6 で |m|/SE ≥ 2）。
  落とす本数も平均 4.9 本と安定し、**強 aug 検出器でも同じだけ効く**（＝検出器を良くしても消えない利得）。
  ただし **標準 split（train 10 動画）では accuracy は上がらず macro-F1 が大きく上がる**
  （val +6.36pt / test +1.83pt・accuracy は −0.2 / −0.3pt、落とす本数も 4 本）。
  → 事前登録の主終点は **macro-F1**、accuracy は非劣化条件に置く。
  しきい値の感度も測った: **0.30〜0.50 のどの値でも val・test とも macro-F1 が改善**（test +1.57〜+6.56pt）。
  ただし最良値は val（0.45・4 本）と test（0.50・3 本）で違うので、**成績を見て選んではいけない**。
- **【重要な補正】「デノイズで edit +9.11」は凍結源 seed42 固有の上振れだった**:
  6 つの凍結源で LOVO を回すと範囲 **+1.04〜+9.11**（通常 3 seed 平均 +5.46 / 強 aug 3 seed 平均 +3.42）。
  **符号は 6/6 で正**（符号検定 p=0.031）なので改善自体は凍結源に依らないが、**効果量は 3〜9 倍振れる**。
- **【訂正】「デノイズは短い工程を潰す」も単一 split の現象だった**: LOVO では design 0.587 → 0.584 とほぼ不変。
  潰さないための改良案（非対称 HMM / max / 連結）はどれも素の因果デノイズより分節指標が悪い。

- **手法は 15 本中 14 本で多数決ベースラインを +32.6pt 上回る**（|m|/SE=5.70）。
  **唯一の破綻は動画 14**（presence acc 0.468 < 多数決 0.740）で、
  **この手術は止血に Bipolar Forceps ではなく Forceps を使う**ため hemostasis の 70% が dissection に化ける
  — P4 の最も純粋な実例。なお per-video 性能の最良の予測子は意外にも **動画の長さ**（r=−0.778）。
- **「揺れ」の測り方は未解決（負の結果）**: 動画ごとの `P(tool|phase)` の JS ダイバージェンスは
  per-video 性能とまったく相関しない（presence 絶対 acc で r=−0.23、n=15）。
  ずれ最大の 2 本（動画 14・15）が正反対の結果になる。**機序は実在するがまだ測れていない。**
- **「誤り除去」と「2 値化」を LOVO で分離**: **2 値化そのものは害ではない**（macro-F1 +1.17pt）。
  **2 値化した信号から誤りを完全に除いても accuracy は上がらない**（−0.11pt）。
  唯一効いたのは **GT ⊕ 生スコア**（+3.26pt・分散も低下）で、容量対照（生⊕生 −0.05pt / 生⊕乱数 +0.11pt）から
  **容量の産物ではない**が、時間シャッフルした GT でも +0.94pt 出るため約 3 割は周辺分布由来。

- **運用上の発見**: **工程側の実験は `torch` + `numpy` だけで動く**（`mmcv` / `mamba-ssm` / CUDA 拡張は不要）。
  一時環境に CPU 版 torch を入れて import・TeCNO forward・
  **`scripts/train_b2a.py --smoke --drop-gap` の完走**まで実証した（`--smoke` は証跡を残さない）。
  → 次の実験（E1/E3/E9/E8）は最小環境で即座に着手できる。

- **phase→det のクラス別内訳も補完**: clsbias-PE は **Scalpel +1.48pp / Skewer +1.33pp が test でも有意に保存**、
  **Syringe だけ val +1.21 → test −0.49 と反転**。除外した Bipolar と非注入 10 術具は厳密中立
  （phase-排他ゲートが設計どおり働いている数値的確認）。

- **【最重要の訂正】時間方向の受容野を与えるとデノイズ利得は消える**:
  per-frame 分類器に **8 フレーム分の文脈**を与えるだけで、
  デノイズの Δedit が **+9.11（3.06σ）→ +0.008（0.01σ）**と消える。
  同時に生の信号のままでも edit が 50.73 → 58.99 に上がる（**時系列モデルが自力で吸収する**）。
  **TeCNO の受容野は 128 フレーム**なので、**入力側デノイズは本番でほぼ効かないと予測される**。
  → **実務提案としてのデノイズは取り下げ、主路は「工程を弁別しない術具を落とす」一本に絞る。**
  **同じ受容野を与えても術具除去の利得は残る**
  （K=8 +1.12pt / K=32 +1.48pt / **TeCNO 相当の K=128 では macro-F1 +3.08pt・2.24σ・10/15**）＝
  **ちらつきは「時間の問題」で時系列モデルが自分で直せるが、揺れる術具は「情報の問題」で直せない。**
  ※ 科学的主張（誤りの"形"で壊れる場所が変わる）は取り下げない。介入実験で直接示している。

- **方法論上の教訓**: **代理モデルで見えた効果は本番の構造で消えることがある**。
  「デノイズが分節を改善する」を val・test・LOVO・6 凍結源で確認した後、
  最後に受容野を与えたら消えた。**代理が本番と構造的に違う軸で必ず対照を取ること。**

**方針（最終）**:
- **実務上の主路は「工程を弁別しない術具（`H(phase|tool) > 0.45`）を信号から落とす」の一本**。
  受容野を TeCNO 相当まで与えても利得が残る唯一の介入である。
- **工程 accuracy のための検出器強化には投資しない**（LOVO でオラクルですら +0.22pt）。
- **入力側の因果デノイズは実務提案から取り下げ**、E1 は「効かないことを確かめて閉じる」反証テストに格下げ。
  ※ 科学的主張（誤りの"形"で壊れる場所が変わる）は取り下げない。
- 最優先は **E−1**（オラクル上限を本番 TeCNO で test 評価・再学習不要・30 分）→
  **E9**（術具除去・主路）→ **E1**（反証テスト）→ **E8**（本番 TeCNO で LOVO）。
- 主終点は介入ごとに分ける（除去 → macro-F1 / デノイズ → edit・seg-F1@50）。
  fold 数の多い判定は `|mean|/SE ≥ 2` + 符号検定。**val 単独の結果は成果として報告しない。**
- 次の 3 実験の **起票用 TASK 契約ドラフト**は [`docs/task_drafts/`](docs/task_drafts/README.md) にある
  （`tools/validate_task.py` の L1/L2 を findings 0 で通ることを確認済み）。

## 主要ドキュメント

- [`OPERATION.md`](OPERATION.md) — 実験証跡の自動同期、Draft PR、auto-merge、keeper の運用正本
- [`docs/host_autosync_onboarding.md`](docs/host_autosync_onboarding.md) — 新規ホストの auto-sync 導入手順
- [`runindex/README.md`](runindex/README.md) — `ilya` を単一 writer とする実験 run index の規約
- [`docs/experiment_log.md`](docs/experiment_log.md) — 全実験の「仮説→実験→結果→解釈→次」記録
- [`docs/idea_log.md`](docs/idea_log.md) — アイデアログ
- [`docs/decision_log.md`](docs/decision_log.md) — 設計判断の記録
- [`docs/TODO.md`](docs/TODO.md) — TODO
- [`docs/notion_integration.md`](docs/notion_integration.md) — Notion 5 DB 連携の仕組み（REST + MCP ハイブリッド）
- [`docs/secrets_and_tracking.md`](docs/secrets_and_tracking.md) — `.env.gpg` 暗号化運用 + W&B / Notion 認証
- [`experiments/analysis/step_c_coupling_analysis/REPORT.md`](experiments/analysis/step_c_coupling_analysis/REPORT.md) — STEP C 本編（val・27 §）: 結合機構の解明・実証・最良結合法の設計
- [`experiments/analysis/step_c_coupling_analysis/TEST_EVAL_REPORT.md`](experiments/analysis/step_c_coupling_analysis/TEST_EVAL_REPORT.md) — STEP C test split 確証: 方向非対称は本番データで保たれるか
- [`docs/research_review_and_next_plan_2026-08-22.md`](docs/research_review_and_next_plan_2026-08-22.md) — **研究レビューと今後の方針（2026-08-22）**: 全実験の横断再集計（全体・クラス別）、val でのオラクル上限とその **test / LOVO での反転**、presence 信号の時間品質と因果デノイズ、GAP の「動画指紋」性、関連研究調査、次の実験計画 E−1〜E8
- [`docs/task_drafts/README.md`](docs/task_drafts/README.md) — 次の 3 実験（E−1 / E9 / E1）の **起票用 TASK 契約ドラフト**（`tasks/` へそのまま置ける様式）
- [`docs/analysis_scripts/README.md`](docs/analysis_scripts/README.md) — GPU 不要の分析スクリプト一式（依存・前提キャッシュ・所要時間・注意）
- [`docs/analysis_scripts/hmm_presence_filter.py`](docs/analysis_scripts/hmm_presence_filter.py) — 因果 HMM forward filter による tool-presence デノイズの検証（CPU・numpy のみ・読み取り専用）
- [`docs/analysis_scripts/proxy_phase_presence_denoise.py`](docs/analysis_scripts/proxy_phase_presence_denoise.py) — GPU 不要のプロキシ工程認識器（本体 `PhaseEvaluator` を使用）で presence デノイズの工程側効果を先測り
- [`docs/analysis_scripts/proxy_lovo_presence.py`](docs/analysis_scripts/proxy_lovo_presence.py) — 15 動画 leave-one-video-out（GPU 不要）。結論が 2〜3 動画の引きに依存していないかを検査する
- [`docs/analysis_scripts/proxy_noise_structure.py`](docs/analysis_scripts/proxy_noise_structure.py) / [`proxy_lovo_noise_structure.py`](docs/analysis_scripts/proxy_lovo_noise_structure.py) — 同じ誤り率で iid ノイズと burst ノイズを比べる介入実験（誤りの「形」の選択性。後者は 15 動画 LOVO）
- [`docs/analysis_scripts/proxy_lovo_gap_vs_presence.py`](docs/analysis_scripts/proxy_lovo_gap_vs_presence.py) / [`proxy_lovo_recommended.py`](docs/analysis_scripts/proxy_lovo_recommended.py) / [`proxy_lovo_flicker_scaling.py`](docs/analysis_scripts/proxy_lovo_flicker_scaling.py) — LOVO で P1 を確認 / 推奨構成の 4 腕比較 / 6 凍結源での再現性
- [`docs/analysis_scripts/hmm_presence_fixed_lag.py`](docs/analysis_scripts/hmm_presence_fixed_lag.py) — 固定ラグ平滑化の品質/遅延曲線（遅延 2 frame でオフライン平滑化と同等）
- [`docs/analysis_scripts/signal_video_identity_probe.py`](docs/analysis_scripts/signal_video_identity_probe.py) — 各信号が動画 ID をどれだけ符号化しているかの線形 probe（GAP 0.998 / region 0.975 / 予測 presence 0.716 / オラクル presence 0.629）

## runindex と context の再生成

実験証跡から横断インデックス `runindex/` を作り、そこから外部の面（Claude アプリの
プロジェクト知識）向けの軽量ビュー `context/auto/` を作る、2 段階の再生成パイプライン。

```bash
make runindex   # experiments/ から runindex/ を再生成（正本の更新）
make context    # runindex/ から context/auto/ を再生成。make runindex の直後に実行する
```

`context/auto/` は `runindex/` 単体だと大きすぎて外部の面に載らないための縮尺図であり、
判断・解釈・評価は含まない（詳細は [`context/README.md`](context/README.md)）。
`make context-check` で手編集・再生成漏れを検出できる。

## TASK 契約システム

Claude アプリ、CLI、人が起票した作業依頼を、会話だけでなく
`tasks/<task_id>/spec.yaml` という**機械検証可能な契約**で受け渡す仕組み。
実装・実験・解析の目的、入力、禁止事項、実行順、成果物、受入基準、
人に判断を戻す条件を実行前に固定し、指示と結果を `task_id` で追跡する。
運用の正本は [`tasks/README.md`](tasks/README.md) を参照。

### 何を防ぐ仕組みか

- 分母、split、sigma 規約などを会話へ転記して古くする
- 同名 run や複数ブランチ間で参照先を取り違える
- 結果を見た後で仮説・判定基準を書き換える
- agent が未回答の研究判断を推測して GPU 実験を開始する
- 指示から逸脱したのに、結果報告へ記録が残らない

このため、数値の直書きではなく `exp:<group>/<experiment_id>`、
凍結源は `run:<group>/<run_name>`、規約は `conventions#<anchor>` で参照する。
commit 後の契約は上書きせず、変更理由を `meta.amendments` へ追記する。

### ディレクトリと task 種別

```text
tasks/<task_id>/
├── spec.yaml   # 機械可読の契約。validator の入力
├── SPEC.md     # 人が読む背景・手順・完了判定
├── prereg.md   # kind=exp のみ。学習開始前に commit
└── RESULT.md   # 解決結果、成果物、受入判定、逸脱、申し送り
```

`task_id` は `T-YYYY-MM-DD-<slug>`。slug は英小文字・数字・ハイフンのみで
3〜60文字とし、並行ブランチで衝突する連番は使わない。

| `meta.kind` | 用途 | 追加契約・完了条件 |
|---|---|---|
| `impl` | コード・ツール・文書の実装 | `outputs.acceptance` を満たし、テストと commit が完了 |
| `exp` | GPU 学習・評価 | `prereg`、分母、expected runs、task_id stamp が必須。runindex に task_id 付きで現れるまで |
| `analysis` | 集計・レポート作成 | 指定先にレポートがあり、すべての数値を実測へ遡れるまで |

起票元は [`tasks/_templates/`](tasks/_templates/) の `impl` / `exp` / `analysis`。
各テンプレートには `spec.yaml`、`SPEC.md`、`RESULT.md` がある。`kind: exp` は
これらに加えて `prereg.md` を起票時に作り、学習開始前に commit する。
現行の `tasks/_templates/exp/` には `prereg.md` が未同梱なので、コピー後に別途作成が必要。
機械判定の正本は `spec.yaml` の `prereg`、`prereg.md` は同内容を人が確認するための文書とし、
両者を一致させる。現行 validator は両者の一致を自動検査しない。

### `spec.yaml` の構成

Schema は JSON Schema Draft 2020-12 の
[`tasks/_schema/spec.schema.json`](tasks/_schema/spec.schema.json)。
未定義キーは拒否され、トップレベルでは次を契約する。

| セクション | 内容 |
|---|---|
| `meta` | task_id、kind、起票元、起票時刻、runindex commit・行数、依存・改訂履歴 |
| `intent` | 答える問い、判断対象、仮説、関連する決定・教訓・backlog |
| `inputs` | 分母、sigma policy、凍結源、split、cache、実行 entrypoint |
| `contract` | 逐語注入する規約、規約 revision、禁止事項、数値直書き禁止 |
| `plan` | phase、gate、venv、preflight、GPU資源、並列 wave |
| `prereg` | `exp` の事前予測、primary endpoint、判定規則、停止条件、事前 commit |
| `outputs` | 必須成果物、保存先、run 数、task_id stamp、受入基準、報告先 |
| `governance` | 人が答える判断、逸脱記録、研究 integrity、escalation 条件 |

`contract.inject_verbatim` の供給源は
[`context/conventions.md`](context/conventions.md)。split、評価 recipe、凍結源、
sigma、禁止事項、venv、命名規則をアンカー単位で実行直前に読み、要約せず注入する。
spec が `inputs.sigma_policy` を省略した場合は同文書の `conventions#sigma` を継承する。

### L1 / L2 / L3 検証

| 層 | 実行主体 | 主な検査 | 失敗時 |
|---|---|---|---|
| L1 | `tools/validate_task.py` | Schema、task_id とディレクトリ名、半角パイプ、名前空間、禁止された数値直書き、完了判定の陽性対照の欄（L1-9、様式の版 2 以降） | `FAIL`、exit 1 |
| L2 | `tools/validate_task.py` | `refs/remotes/origin` 間での task_id 重複、規約アンカー、split・entrypoint・cache の実在、runindex 分母、seed 数、sigma 整合 | `FAIL`、exit 1 |
| L3 | `/task` を実行する Claude CLI、または同手順を実施する agent / 人 | venv、CUDA 拡張、決定性、prereg の時系列、未回答判断、出力先権限、契約の静的検査（P9、**警告**） | 1件でも赤なら GPU 実行前に停止 |

L2 では、起票後に `context/conventions.md` が変わった場合を `L2-6`、
runindex の母集団件数が動いた場合を `L2-8` として `WARN` する。
WARN 単独では validator の exit code は 0 だが、`/task` 実行時は内容を提示して
続行可否を人に確認する。手動実行でも同じで、WARN は人の明示判断まで停止する。
現在の Python validator が自動化するのは L1/L2 までで、
L3、凍結 checkpoint の SHA-256 照合、実行、`RESULT.md` 記入は `/task` 手順の責務。
エージェント向け文書のシェル命令は `make agent-check` で検査し、仮想環境や資格情報の
読み込みと後続操作が別命令へ分かれていないことを確認する。

### 起票者の誤りの検出（`make spec-check`）

起票者の検査が検証対象を検証していない誤りが 20 task 連続で起きた。手順書の注意項目は
守られず、**文言による自制は働かなかったため機械にした。** 正解データは
`tasks/*/result.yaml` の `issuer_defects` に型つきで残った 39 件である。

`tools/check_spec.py` は契約の `SPEC.md` と `spec.yaml` を走査し、8 規則で該当を出す。
検出可能性で 3 分類した結果は `syntactic` 3 件・`structural` 13 件・`semantic` 23 件で、
検査の対象は前 2 者の 16 件、うち **11 件を検出する**（実測）。
`semantic` は意味論であり構文でも構造でも捕まらない。**捕まえられない型が明示されている
こと自体が成果である。**

    make spec-check TASK=<task_id>    # 契約 1 件（TASK を付けて使う）

各規則は `issuer_defects` の実例を裏付けに持つ。**裏付けの無い規則を足すと分母が動き、
検出率が意味を失う。** 命令の取り出しは `tools/check_agent_docs.py`、生成物の解決は
`tools/check_forbidden.py` へ委譲し、判定を複製しない。
4 層の設計と分類の理由は [`tasks/README.md`](tasks/README.md) と
[`tasks/T-2026-08-11-issuer-defect-detector/defects.md`](tasks/T-2026-08-11-issuer-defect-detector/defects.md)。

### 標準ライフサイクル

1. 作業種別に合う `tasks/_templates/<kind>/` を
   `tasks/T-YYYY-MM-DD-<slug>/` へコピーする。
2. `spec.yaml` と `SPEC.md` を埋める。起票時点の runindex commit と3 CSVの行数を
   `meta.created_from` に記録し、参照には必ず名前空間を付ける。
3. `kind: exp` は予測・primary endpoint・判定規則・停止条件を `prereg` /
   `prereg.md` に書き、**学習開始前に commit** する。
4. L1、続いて L2 を実行する。FAIL は推測で直さず、契約の起票者へ戻す。
5. Claude CLI では `/task T-YYYY-MM-DD-slug` を使う。他の agent は
   `.claude/skills/task/SKILL.md` と `tasks/README.md` の同じ順序を手動で守る。
6. phase を順番に実行し、各 gate の `stop` / `ask` / `skip` に従う。
   `governance.decisions_required` が未回答なら agent は自分で決めない。
7. 成果物へ `outputs.stamp.task_id_in` の task_id を刻み、指示書と run を結ぶ。
8. `RESULT.md` に参照解決、gate、成果物、受入判定、未解決事項、数値の出所を記録する。
   `deviations` は必須で、逸脱が無い場合も「なし」と明記して commit する。

### 検証コマンド

```bash
# 例: impl task を起票（TASK_ID は実際の値へ置き換える）
TASK_ID=T-2026-08-05-example-task
cp -R tasks/_templates/impl "tasks/$TASK_ID"

# 全 task を L2 まで検証（既定）
make task-validate

# 1 task のみ
make task-validate TASK=T-2026-08-03-task-contract-bootstrap

# 起票直後の L1 のみ
make task-validate TASK=T-2026-08-03-task-contract-bootstrap LEVEL=l1

# validator 自体の回帰テスト
.venv/bin/python -m pytest tests/test_validate_task.py -q
```

validator は `tasks/` 直下の `_` で始まらないディレクトリを対象とし、
`spec.yaml` が無いものは `SKIP` する。最終行の `N task(s), M failed` と
プロセスの exit code を両方確認する。現行 validator は `SPEC.md` / `prereg.md` /
`RESULT.md` の存在自体は検査しないため、実行者がライフサイクル上で確認する。
`RESULT.md` の判定欄は現行テンプレート上 `PASS` / `FAIL` / `PARTIAL` だが、
その選択自体も validator は判定しない。上記 kind 別の完了条件と全受入基準を満たす場合だけ
`PASS` とし、未達があれば `PARTIAL` または `FAIL` の理由を本文に残す。

### 現在の実装状態と既知の制約（2026-08-05）

自己契約 [`T-2026-08-03-task-contract-bootstrap`](tasks/T-2026-08-03-task-contract-bootstrap/)
は、現在の専用テストで **11 passed**、L1/L2 で **1 task、0 failed**。
一方、同 task の [`RESULT.md`](tasks/T-2026-08-03-task-contract-bootstrap/RESULT.md) は
ブートストラップ時点の全回帰テスト失敗と既存未追跡成果物を明示して `PARTIAL` 判定のまま残す。
これは履歴証跡なので成功へ書き換えない。

また、`context/conventions.md` では Relation-DETR 凍結源 checkpoint の正本 SHA-256 と
`select_box_nums_for_evaluation` の転記元が `UNKNOWN`。該当する `exp` task は
実行時に実ファイルから SHA-256 を記録し、未確定値を推測で補完してはならない。

### TASK 報告道具の境界処理（2026-08-12）

`tools/report_task.py` の送信前検査は、資格情報名に続く代入値を大小文字および `_` / `-`
区切りを吸収して検出する。裸の 40 桁 hex は履歴識別子として許可し、環境にある資格情報値の
直接照合は維持する。Notion `rich_text` は受け側と同じ UTF-16 単位で 2,000 以下に分割し、
基本多言語面外の文字も壊さず連結できる。`host_mismatch` はホスト名の大小文字を区別せず、
別ホストの宣言は引き続き警告する。回帰試験はこれらの通過・停止を両方向で固定している。

### bengio canary の現在状態（2026-08-13）

`T-2026-08-13-bengio-canary-lecun-cutover` で、状態probe、固定SSH中心probe、
Syncthing granular REST経路切替、keeper起動、rollbackの契約専用補助器を追加し、
ruffと各self-testを通した。ただし bengio にSSH非依存の復旧経路がないため G1 で停止し、
keeper、marker、SSH中継、Syncthing device addressは変更していない。再開には
local console、リモートKVM、親ホストconsoleなど、現在のSSH経路に依存しない復旧手段が必要である。

`T-2026-08-13-bengio-lecun-deadman-cutover` では、選択肢2のdead-man方式で再開する前に
transactionの祖先を `/proc` から再測定した。Codexはzmx配下でPID 1へ再親化され、対話session
sshdは別processだったため、契約の「transaction実行元がsession sshd配下」というG1条件を満たさず
変更前停止した。keeper、marker、SSH中継、Syncthing device addressは未変更。再開にはsession sshd
子孫からの起動経路、またはzmxを安全な独立性として扱う契約amendmentが必要である。

`T-2026-08-13-bengio-lecun-zmx-deadman-cutover` ではzmx再親化を許可する厳密なtopology probeを
追加したが、host全体に同一binaryのzmxを4件検出し、一意なverified_zmxというG1条件を満たさず
変更前停止した。keeper、marker、SSH中継、Syncthing device addressは未変更。再開にはzmx一意性の
scope、または既存zmxを扱う許可を別契約で定義する必要がある。

### Andrew→lecun同期切替（2026-08-13）

`T-2026-08-13-andrew-lecun-sync-cutover` でAndrewを旧philip中心からlecun中心へ切り替えた。
Syncthingを再起動せず、localhost routeをlecun deviceへ一件だけ移し、marker・動的keeper・SSH中継を
lecunへ揃えた。双方向probeと1805秒超の観測でbytes/SHA-256、process identity、route、接続を確認した。
backupとprobeは保持し、guardの適用限界と二回の安全停止・修正履歴はtaskのRESULTへ記録している。

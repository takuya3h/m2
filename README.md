# egosurgery_multitask

EgoSurgery データセット上で、**術具検出と工程認識のあいだの方向性条件付けと相互改善**を測る
CV 研究プロジェクト。設計は**二塔・界面分離型**である。各タスクが自前の最良モデル（**塔**）を
持ち、検出塔は術具ラベルのみ、工程塔は工程ラベルのみで学習して凍結する。結合は塔と塔のあいだの
小さな学習モジュール（**界面**）だけで行い、**比較で変えるのは界面の入力だけ**にする。

相互改善は**定義 A（同時改善）**を主判定に置く。双方向腕で検出と工程の差がともに正で主判定を
満たすことである。達成できない場合は第二段（一方向のみ改善・他方は非劣化。執筆方針を変え改題を
検討）、第三段（両方向とも差が実質零。分析論文と単独の最高性能）へ移る。**各段の論文の形は
先に決めてある。**

論文の主張は先に固定しない。**競合する三つの仮説を事前登録**し、識別実験で残ったものから決める。

- **H1 方向依存** — 転移の符号はどちらの方向かで決まる
- **H2 次元選択則** — 符号と大きさは通す次元の性質で決まり、方向は二次的
- **H3 受け取り手表現依存** — 情報の価値は送り手の質ではなく受け取り手の表現に条件付けられる

**方針の全文の正本は外部の記録場所にある。** 本 README はその要点を実行者向けに写したものである。

---

## 現在の状態（2026-08-28）

**現在地は Stage 0（土台整備）の起票前である。** 段階は Stage 0 から Stage 5（拡張）まで並び、
関門は G0・G1・G1.5・G2・G3・G4 が置かれている。

**投稿先は MICCAI 2027 または IPCAI 2027。どちらを主目標にするかは未決**であり、
G0 の所要時間を実測してから決める。

**保留と未了が二件ある。**

- 中核主張の一つ（凍結源を替えると工程側の差の符号が反転したという記録）の
  **数値の出所照合が未了**である。Stage 0 の調査契約で照合する
- 手術の手アノテーション完全版の組立は**保留**（利用者の判断待ち）。手信号を使う腕はその後

2026-08-28 より前の作業記録は
[`docs/history/README_log_2026-05_to_2026-08.md`](docs/history/README_log_2026-05_to_2026-08.md)
にある。**当時の記録であり、現行方針ではない。**

---

## 設計原則

**中心にあるのは一つである。受け取り手（塔と界面の型・容量・水準・スケジュール・種）を
全腕で同一にし、変えるのは界面の入力だけにする。**

1. **受け取り手を全腕で揃え、界面の入力だけを変える** — 比較したい量以外を動かさない。
2. **塔は自前で最良にしてから凍結する** — 検出塔は術具ラベルのみ、工程塔は工程ラベルのみで学習する。
3. **方向は四腕で測る** — なし・検出から工程・工程から検出・双方向。
4. **参照入力段は四段** — 空・予測・正解・正解と予測の和。**上限として使えるのは最後の段だけである。**
5. **学習範囲は三水準** — 入力適合層のみ（W1）、末端ブロックまで（W2）、受け取り塔全体（W3）。
6. **`src/` と `configs/` と `experiments/` を絶対に分ける** — コード・設定・実験結果の混在は再現性を壊す。
7. **すべての実験に「証拠」を残す** — 6 点の必須証跡（`config.yaml` / `command.sh` / `git_commit.txt` / `metrics.json` / `per_class_ap.json` / `notes.md`）と実行ホスト `server.txt` を自動保存する。
8. **`data/` は Git 管理しない** — ただし `data/splits/` と `data/README.md` は Git 管理する。
9. **論文は最初から作る** — `paper/` は Day 1 から存在する。

**撤回された原則**（全比較対象を同一の凍結 backbone に載せる／工程側の分母を独立に最適化しない／
分母を系統ごとに複数運用する／段階実験の連番による命名とその分母追跡を中核に置く）は
[`docs/history/README_log_2026-05_to_2026-08.md`](docs/history/README_log_2026-05_to_2026-08.md)
にある当時の記録を参照。**現行の設計原則には含めない。**

**将来拡張として残している要素**: セグメンテーション、関係推論、視点外カメラ。

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

### Notion 連携（配布台帳のみ）

**CLI が Notion に触れるのは配布台帳（`task_distribution`）だけである。**
2026-08-31 に記録系を再構成した。ID レジストリ `configs/notion.yaml` は非秘密・commit 可、
token は暗号化 `.env.gpg` から `scripts/load_env.sh` が現在のシェルへ読み込む。
詳細 → [`docs/notion_integration.md`](docs/notion_integration.md)。

- **使う経路**: 契約の取り込み `make task-notion` / `make task-start`（`tools/fetch_task.py`）と、
  完了報告の送り返し `make task-report`（`tools/report_task.py`）。この二つだけ。
- **新しい面**（運用正本・現在地と現行計画・マスター・知見/決定・アーカイブ）は
  **Claude アプリの面であり CLI は読まない**。識別子は登録簿の `claude_app_surfaces` に
  人が引くために載せてあるだけで、コードから解決しない。
- **退役**: 旧データベース群（run 台帳・意思決定ログ・失敗知見・実験手順書・プロンプトライブラリ）と
  旧頁群は凍結した。自動投稿は明示的に止めてあり、呼ばれても投稿せず退役の旨を返す。
  内容は Notion ではなく repo の写しを読む（`docs/archive/notion/db/<KEY>/`）。
  読み取りの道具だった `notion_context_pack.py` は `scripts/retired/` へ移した。

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

実験フォルダは **自動採番**される（手作業で命名しない）。

**命名は方針 v2 の用語に合わせる。腕を区別する軸は、方向・参照入力段・学習範囲の三つである。**

- **方向** — なし / 検出から工程 / 工程から検出 / 双方向
- **参照入力段** — 空 / 予測 / 正解 / 正解と予測の和（**上限として使えるのは最後の段だけ**）
- **学習範囲** — W1（入力適合層のみ）/ W2（末端ブロックまで）/ W3（受け取り塔全体）

**塔と界面は名前の上でも分ける。** 塔は自前で学習して凍結したもの、界面は塔と塔のあいだの
小さな学習モジュールである。**比較で変えるのは界面の入力だけ**なので、名前もその軸で読めるようにする。

連番は `ExperimentManager` が `experiments/{category}/` 配下の既存フォルダを走査して
自動決定するため、命名のゆれや重複が構造的に発生しない。

**旧規則（`{step}_{seq:03d}_{description}_seed{seed}` の S0〜S9 連番と、その分母追跡を
中核に置く枠組み）は撤回されている。** 当時の記録は
[`docs/history/README_log_2026-05_to_2026-08.md`](docs/history/README_log_2026-05_to_2026-08.md)
にある。既存の実験フォルダ名は当時の規則のままである（**過去の記録は書き換えない**）。

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

### 時系列ログ（2026-05 〜 2026-08）

2026-06 から 2026-08 の作業記録は
[`docs/history/README_log_2026-05_to_2026-08.md`](docs/history/README_log_2026-05_to_2026-08.md)
へ移した。**当時の記録であり、現行方針ではない。** そこに書かれた判定規則・分母の運用・
段階実験の枠組みは 2026-08-28 の方針改訂で撤回されている。**現行方針は本 README の冒頭にある。**

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

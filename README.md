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
現行サーバーは **Ubuntu 24.04 / CUDA 12.9 / gcc 13** で、追加のシステム導入は要らない。

### 推奨セットアップ（uv 仮想環境 + CUDA + mm系 + Mamba）

mm 系（mmcv/mmdet）と mamba-ssm/causal-conv1d の CUDA 拡張は、**torch 2.1.2+cu118 に合わせた
prebuilt wheel** で入れる。本体 `.venv` は何もビルドしないので、システムの nvcc の版は問わない。検証済み構成:

```bash
# 仮想環境を作成して有効化
uv venv .venv --python 3.11
source .venv/bin/activate

# torch 2.1.2 + cu118（mmcv / mamba の prebuilt wheel がこの組に合わせてある）
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

検証済み: driver 595 / CUDA 12.9 のホスト（2026-10-13 andrew。旧構成は driver 535）で cu118 ランタイムが
動作し、`torch.cuda` / mmcv 2.1 / mmdet 3.3 / mamba-ssm 2.2.2 / causal-conv1d 1.4.0 がすべて GPU で動作。
`transformers` は mamba-ssm 2.2.2 が旧 generation API を参照するため 4.44.2 に固定。

### 別マシンでの環境再現（推奨）

検証済み環境を他サーバで完全再現するための再現セット（すべて Git 管理）:

```bash
bash scripts/setup_env.sh   # 本体 .venv: 作成〜全依存導入〜検証まで自動

# 検出器（Relation-DETR）側も使うとき
bash scripts/restore_relation_detr_source.sh   # third_party/Relation-DETR に main.py が無いときだけ
bash scripts/setup_env_relation_detr.sh        # .venv-relation-detr + MS-Deform-Attn のビルド検証
```

- `requirements.lock.txt` — 全 100 パッケージの厳密バージョン（`uv pip freeze`）
- `scripts/setup_env.sh` — index URL・find-links・prebuilt wheel の取得を含む再現スクリプト
- `requirements.relation_detr.lock.txt` / `scripts/setup_env_relation_detr.sh` — 検出器 venv の厳密版と構築
- `scripts/restore_relation_detr_source.sh` — 上流 clone + `third_party_snapshot/<host>/` の patch・tarball で
  ソースを復元（既定は efros の版。**どの版を正とするかは研究上の判断**）
- `docs/environment.md` — OS / driver / CUDA Toolkit 11.8 等のシステム層の記録
- `docs/reproduce_on_new_machine.md` — 別マシンの Claude Code 向け再現指示書

前提: NVIDIA driver 525 以降・uv。検出器 venv だけが CUDA Toolkit（nvcc 12.x か 11.8）を使う。
既存の venv を作り直すときは `UV_VENV_CLEAR=1` を付ける。

---

## 別マシンで完全再現する手順（クローン → 学習開始まで）

新しいサーバで本リポジトリを 0 から立ち上げる手順を順番に示す。
**`scripts/setup_env.sh` だけでは不足**で、以下のシステム準備とデータ配置が前提となる。

### 0. ハードウェア／OS 要件

| 項目 | 要件 |
|---|---|
| OS | Ubuntu 24.04 LTS（現行サーバー。旧構成の 22.04 でも通る） |
| NVIDIA driver | **535 以降推奨**（最低 525。現行サーバーは 595。`nvidia-smi` で確認）|
| GPU | **VRAM 24GB 以上 × 1 枚以上**。S0/S2 の DINO 学習は batch 4 で 23-48GB 消費。RTX A6000（49GB）×2 で検証済み |
| ディスク | データ・重み・実験結果込みで **40GB 以上空き**（EgoSurgery 約 15GB + COCO 事前学習重み 約 400MB + 実験ログ）|
| RAM | 32GB 以上推奨（DataLoader workers + mmdet で消費）|

### 1. システムパッケージのインストール（root 権限）

```bash
# uv（Python パッケージマネージャ）
curl -LsSf https://astral.sh/uv/install.sh | sh
# pyenv 経由で Python 3.11 を入手するか、uv 内蔵の Python ダウンロードに任せる
```

CUDA Toolkit は現行コンテナの 12.9（`/usr/local/cuda`）をそのまま使う。**CUDA 11.8 を足す必要はなく、
足さないこと**（nvcc 11.8 は gcc 13 を扱えない。経緯は `docs/environment.md`）。本体 `.venv` は nvcc を
使わず、検出器 venv の MS-Deform-Attn は nvcc 12.9 でビルドして凍結源の出力を bit 一致で再現する。

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

# 検出器（Relation-DETR）側も使うとき
bash scripts/restore_relation_detr_source.sh   # ソースが無いときだけ
bash scripts/setup_env_relation_detr.sh
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
| HTS 整形前バックアップ | `data/annotations/egosurgery_hts_bak/`（`.json.bak` を含む） |
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

**2026-10-07 更新:** HTS の `hand_seg`・`tool_seg`・`hand_tool_seg` の JSON を
内容を変えずに整形し、整形前の12ファイルを `data/annotations/egosurgery_hts_bak/` へ
同じサブフォルダ構成で退避した。退避先は Git 管理から除外し、Syncthing で同期する。
設定配布には `phase0` の取得と keeper の反映が必要で、転送完了は各同期先で別途確認する。

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
`make docs-check` は `.gitignore` で無視される経路（`.claude/settings.local.json` など
ホストの手元にだけ在るファイル）を、在っても無くても対象外にする。結果がホストで変わらず、
追跡下の経路が実在しない場合は従来どおり検出する（2026-10-08、`T-2026-10-08-doc-checks-clean-and-defect-log`。
この時点で二つの検査は手元と新しく取得した作業ツリーの両方で合格）。

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

### Tier 1 の総量の試算器（2026-09-16）

`T-2026-09-17-tier1-cost-estimate` で `tools/estimate_tier_cost.py` と
`tests/test_estimate_tier_cost.py` を追加し、`docs/stage0/B1_tier1_cost_estimate.md` を作った。
Stage 0 の実測した所要時間から Stage 1・Tier 1〜3 の GPU 時間と壁時計時間を積み、
縮退順を一段ずつ当てた総量と、設計変更一回分の費用と、締切への収まりを出す。

所要時間の実測が無い run 型（検出塔のフル学習、検出側 W2 の界面 run）には、利用者の承認を得て
t1b の実測（1 run 約 4 時間 / 6 epoch）を代理に置いた。**いずれも逆伝播の範囲が t1b より
広いため下界である**ことを `RunType.measured` が型として持ち、`--unknown` の一覧に出る。
装置の前提は本ホストの A6000 2 枚（`nvidia-smi` の実測）で、`--devices` で動かせる。

文書の数表はすべて計算器の出力そのものを `<!-- estimate:begin ... -->` で囲って埋めてあり、
`--check-doc` が再計算との差 0 件を確かめる。`--check-sources` は出所の無い所要時間の行を、
`--check-coverage` は run に対応づかない M の項目を数える。**いずれも壊した入力で
1 件を返すことまで試験で確かめている**（陽性対照）。

## Stage 1 工程塔の実行準備（2026-09-18）

`T-2026-09-18-stage1-phase-tower` 用に `scripts/stage1_ptower.py` と
`configs/stage1_ptower.yaml` を追加。Hydra の `action=extract/train` で ImageNet V1
凍結R50のGAP特徴と、折り別のA/C/単フレーム線形対照を実行する。
二度の全特徴抽出の一致・重み変更対照・キャッシュSHA-256照合を行い、
W&B接続失敗時は実験を開始しない。学習はval Jaccardで選択しtestは評価しない。
追加6動画の画像が未発見のため、利用者承認によりP*-15を先行する。
現時点で候補B・全トーナメント・選定後testは未実装/未実施。
進捗と実測は当該タスクのRESULT.md・audit.mdを参照。

## Stage 1 工程塔 P\*-15 の確定（2026-09-18）

`T-2026-09-18-stage1-phase-tower` を完走した。上の「実行準備」の節にある
「候補 B・全トーナメント・選定後 test は未実装/未実施」は解消している。

`scripts/run_stage1_ptower.py`（2 並列で格子を回し、完走済みの設定を証跡から見つけて飛ばす）と
`scripts/select_stage1_ptower.py`（val だけで選定し、確定塔の test を折りごとに一度だけ評価する）を追加。
test は台帳 `experiments/phase1/stage1_ptower/test_access_{A..E}.json` を `open("x")` で先に作るため、
中断しても黙って再評価されない。

**確定した P\*-15 の recipe は、候補 C（truncated MSE の平滑化損失）・8 層（受容野 1021 フレーム）・
平滑化重み 0.30・履歴 30。** 5 折り平均 val macro Jaccard 0.32891、test 0.22472。
選定は 70 run の val だけで行い、最良と次点が同点になったため事前登録 §6.3 に従い諮って決めた。
同点規則「同一候補・同一受容野で残る同点は折り A の seed 間 pstd が小さい方」を `select()` に追加した。

**P\*-21 は UNKNOWN。** 追加 6 動画（17〜22）の注釈は実在するが画像が本ホストに無く、
学習も test も行っていない。Stage 2 の主分母は P\*-21 であるため、画像を使えるようにする別契約が要る。

数値・逸脱・起票者の誤り・陽性対照は当該タスクの `RESULT.md`・`result.yaml`・`audit.md` を参照。

### 凍結検出塔の出力キャッシュの識別実験（2026-09-17）

`T-2026-09-17-frozen-feature-cache-timing` で `scripts/profile_t1b_step.py` と
`scripts/t1b_backbone_cache.py` を追加し、`docs/stage0/C1_frozen_feature_cache_timing.md`
を作った。**P→D 側の界面 run が 1 本約 4 時間かかる原因が「凍結した塔へ毎 epoch 画像を
通し直していること」かを、キャッシュを本実装する前に測って判定する**ための道具である。

- `profile_t1b_step.py` — `train_t1b.py` の構築関数をそのまま再利用して 1 step を
  データ供給・順伝播・backbone・逆伝播・最適化へ分解する。**hook の中で同期するため
  backbone へ過大に帰属する**ことが実測で分かっており、結論には使わない（下記）。
- `t1b_backbone_cache.py` — `build` は決定的な前処理（val）で backbone 出力を保存し、
  塔の識別子と凍結源の要約値を含む鍵と `aggregate_sha256` を記録する。`bench` は
  **同一のバッチ集合**について「塔を計算する経路」と「キャッシュを読む経路」を同一過程内で
  比較する。読み出しは `posix_fadvise(POSIX_FADV_DONTNEED)` で頁キャッシュを落として測る。
  `--swap` で順序を入れ替えられ、`--trainable all` で W2 相当も測れる。

**結果（efros・A6000・実測）**: 凍結 backbone の順伝播は 1 step の 4.63〜7.68% にすぎず、
無料になっても上限は 1.049〜1.083 倍。キャッシュ経路は実測 0.558〜0.661 倍で**遅くなる**
（1 step で読む 91,566,899 bytes を塔の順伝播の時間内に読むには 2.28〜4.58 GB/s が要るが、
実測は 0.367〜0.472 GB/s）。**`configs/stage/s0_frozen.yaml` の `stage1_feature_cache` の
骨組みは P→D の界面学習には使えない。**

`scripts/train_t1b.py` は 1 行も変えていない。キャッシュを読む口は計測用の道具の側にあり、
既存の学習経路は構成上壊れない。

### 数値精度と計算グラフの最適化の実測（2026-09-17）

`T-2026-09-17-amp-compile-timing` で `scripts/bench_t1b_precision.py` を追加し、
`scripts/train_t1b.py` に `--tf32` と `--amp {no,bf16,fp16}` を足した。
`docs/stage0/C2_amp_compile_timing.md` に結果を置いた。

🔴 **既定は従来と同一である。** `--tf32` を付けなければ `torch.backends.cuda.matmul.allow_tf32`
には**触れない**（既定値の再確認すらしない。将来 torch の既定が変わったときに挙動を固定しないため）。
`--amp no`（既定）では autocast を張らず `GradScaler` も作らないため、経路は分岐する前と同じである。

- `bench_t1b_precision.py` — 条件（fp32 / tf32 / bf16 / fp16 / compile 系）ごとに 1 step を測る。
  バッチは最初に一度だけ取り出して保持し、**全条件へ同じ列を与えて**形の列の要約値で同一性を示す。
  暖機を捨て、**同期を取ってから**計時する（同期なしの値も併記する。取らないと速く見える）。
  `--trainable all` で W2 相当、`--dynamo-suppress-errors` で dynamo の eager 退避を測れる。

**結果（efros・A6000・実測）**: 行列積の TF32 を許すだけで W1 が **1.182×**、W2 が **1.286×**。
bf16 / fp16 はほぼ同じ倍率で、記憶領域が W1 で 12.8%・W2 で 27.1% 減る。
非有限の損失と跳ねは全条件で 0 件。**`torch.compile` は完走しない**
（`set_criterion.py:199` の `F.one_hot` が記号のままの形を扱えず、eager へ退避させると
Hungarian matcher の費用行列に非数が入る）。利用者の判断で実装は改変せず除外した。

`tools/estimate_tier_cost.py` の `det_iface_w2` を 4.00 h → **4.82 h** に直した
（前契約の実測比 1.205 から導いた。`measured` は False のまま）。
`docs/stage0/B1_tier1_cost_estimate.md` の 8 区画を再生成し `--check-doc` は差 0 件。

## Stage 1 工程塔の二周目: backbone の fine-tune（2026-09-18）

一周目（`T-2026-09-18-stage1-phase-tower`）は backbone を凍結したままだった。検出塔 D\* が
backbone を手術データで fine-tune しているのに工程塔 P\* を凍結のままにするのは不公平で、
近年の工程認識研究にも例が無い（利用者の指摘）。二周目
`T-2026-09-19-stage1-phase-tower-r2` は backbone を折りごとに工程ラベルで fine-tune し、
D\* と対称にする。

追加した道具:

- `scripts/stage1_ptower_r2.py` — Hydra の `action=finetune/extract/train`。`finetune` は
  **stem（conv1・bn1）だけを凍結**して layer1〜4 と fc を学習する（検出塔の
  `freeze_indices=(0,)` と揃えた）。折りの train 動画だけを使い、val が最良 epoch を選び、
  **test は読まない**。`extract` は fine-tune 後の backbone から、一周目と同じ前処理で
  C5 GAP を書き出す（差が backbone の重みだけになるようにするため）。`train` は一周目の
  `stage1_ptower.train` をそのまま呼ぶ
- `scripts/run_stage1_ptower_r2.py` — FT（14 本）・EX（14 本）・HEAD（140 run）の格子を
  2 並列で回す。証跡のある設定は飛ばすため、中断しても続きから再開できる
- `scripts/select_stage1_ptower_r2.py` — val だけで選定し、確定塔の test を折りごとに一度
  評価する。**判定規則は一周目の `select_stage1_ptower.select` を import してそのまま使う**
  （同点規則とその試験を共有するため）。学習率は表を広げるだけで同点規則には入らない

既存スクリプトへの変更は後方互換のみ。`stage1_ptower.py` の 5 箇所を `cfg.get(...)` へ変え
（`step` / `data_setting` / `desc_suffix` / `backbone_tag`）、`run_stage1_ptower.py` の
`completed()` に `task` 引数を足した。**既定値はすべて一周目の値**であり、一周目の試験 8 件は
そのまま通る。

実測・確定 recipe・一周目との差は当該タスクの `RESULT.md`・`audit.md` を参照。

### Stage 1 検出塔の 5 折り確定（2026-09-21）

`T-2026-09-18-stage1-detector-towers` で `scripts/make_fold_annotations.py` /
`run_stage1_dtower.sh` / `stage1_dtower_queue.sh` / `eval_stage1_dtower.sh` /
`write_stage1_dtower_evidence.py` を追加し、`scripts/eval_relation_detr_map.py` に `--split` を足した
（**既定は従来どおり** config の `test_dataset` を使う）。

- `make_fold_annotations.py` — `conventions#folds` の 5 折りへ COCO 注釈を動画単位で組み替える。
  🔴 **公式 3 ファイルの ID は 0 始まりで衝突する**（image 4,265 件・annotation 12,673 件）ため
  プールして振り直す。**折り A は公式分割そのものなので複製して使い、ID を振り直さない**
  （再現の忠実さのため。sha256 一致を検査する）。陰性対照つき
- `stage1_dtower_queue.sh` — **常に 2 本だけ**同時に走らせる。2 本が最適であることは実測で決めた
  （1 本 1.805 step/s → 2 本 2.17 → 3 本 2.19 で頭打ち。GPU 使用率は 2 本で 91〜96%）
- `write_stage1_dtower_evidence.py` — `main.py` は `metrics.json` も `per_class_ap.json` も
  書かないため、評価の出力からのみ証跡を作る（**手で数値を書かない**）

**検出塔のフル学習の入口は `third_party/Relation-DETR/main.py`（accelerate）であり、
`scripts/train_t1b.py` ではない**（後者は P→D 界面の学習器）。数値精度は凍結源と同じ **fp16**。

`tools/estimate_tier_cost.py` の `det_tower_train` を 8.00 h（代理）→ **8.35 h（実測・`measured: True`）**
にした。計算器の UNKNOWN は 10 → 9 件。

### L3 P13 を完了済み契約で SKIP にした（2026-09-21）

`T-2026-09-19-symmetry-gate` が入れた P13 `symmetry_table_complete` は、**完了済みの
exp 契約 13 件すべてを FAIL にしていた**（prereg に対称性の表が無い）。関門の意図は
これから起票する契約に効かせるものであり、過去の契約の再現や追試を妨げない。

`tools/preflight_task.py` に `completed_verdicts(task_id)` を足し、
`check_symmetry_table` の冒頭で完了済みを見る。

| 入力 | P13 |
|---|---|
| `result.yaml` の `gates[].verdict` に空でない値がある | **SKIP**（理由に「完了済み」） |
| `result.yaml` が無い／`gates` が無い／verdict が空／壊れた YAML | 従来どおり検査する |
| `kind != exp` | 従来どおり SKIP（`EXP_ONLY`） |

🔴 **`verdict` は `result.yaml` の最上位の項目ではない。** 様式が持つのは
`gates[].verdict` であり、最上位は `status` である。**判定に使うのは `result.yaml` の
実在と verdict の有無だけ**で、名前の部分一致・日付・配布台帳は使わない。
部分一致にすると無関係な契約を完了済みと誤認する。

実測: 変更前は exp 13 件が 13/13 FAIL、変更後は 13/13 SKIP。未完了に対する挙動は
対照 11 件で不変であることを確認した（`tests/test_symmetry_gate.py`、42 件）。

### 起票者の誤りの型が 6 種になった（2026-09-21）

`tasks/_schema/result.schema.json` の `issuer_defects[].type` の列挙に
`asymmetric_comparison`（比較対象の処方を読まずに候補を設計した）と
`rule_read_narrowly`（規則の字面を狭く読み、その読みを既定にした）を足した。
`docs/issuer-defects.md` の「`result.yaml` の enum には未追加」の注記は消えている。

`tools/build_taskindex.py` の `DEFECT_TYPES` も同じ 6 種へ揃えた。**片方だけ増やすと
新しい型の欠陥が `context/auto/followups.md` の集計表から黙って落ちる。**
一致は試験で縛ってある。

### 手順書に契約の始め方と終え方を入れた（2026-10-07、philip）

`T-2026-10-07-skill-task-start-and-release`（GPU 不使用）。

- `.claude/skills/task/SKILL.md` に `### 0. 始める` と `### 8. 終える` を足した（既存の 1〜7 の番号は不変）。
  始める段は、読み取りだけの命令で状態を判定してから task-start を呼ぶ（再開・分岐の重複・detached・汚れ・清浄・失敗）。
  終える段は、`make task-release` の状態表示で扱いを決める
- 利用者は `/task <task_id>` を一行送るだけでよい。汚れがあるときだけ、分類した一覧から選ぶ
- 目印を手で置く・外す指示は、条件つきの 2 か所だけにした。`tasks/README.md` と `scripts/task_start.sh` の案内文も合わせた
- 構造は `tests/test_skill_task_doc.py` で縛る（段の位置、状態の一覧の一致、手作業の指示の位置）

### 抑止の所有の記録と解除の道具、会話の抽出物の置き場の移動（2026-10-07、philip）

`T-2026-10-07-pause-release-tool-digest-relocate`（GPU 不使用）。

- `scripts/task_start.sh` — 新たに置く `.sync-pause` の中身に所有の記録（`task_id=` と `branch=`）を書く。終了コードと巻き戻しは変えていない
- `scripts/task_release.py`（`make task-release TASK=<id> END=complete|abort [REASON=...]`）— その契約が置いた目印だけを、前提を確かめてから外す。状態は一行で表示する（`task-release: RELEASED` など）
- `tools/session_digest.py` — 抽出物の出力先を `~/claude-sync/session-digest/<ホスト名>/` へ移した。旧い置き場 `docs/sessions/digest/` は `.gitignore` に載せた（追跡済みの 48 件は追跡のまま）。2026-08-09 の「抽出物は版管理へ記録する」は撤回した
- 文書: `tasks/README.md`、`docs/sessions/README.md`、`OPERATION.md`、`context/env-facts.md`

### 生成物の自動 PR の自動の統合（2026-10-07、philip）

`T-2026-10-07-auto-merge-regen-pr`（GPU 不使用）。

- `regen-projections.yml` に統合の段を足した。三条件（作成元が `auto/regen-projections`、基点が phase0 の先頭、差分が生成物だけ）を統合の直前に読み直す。満たせば `GITHUB_TOKEN` で merge commit を作る。満たさなければ統合せず、失敗で終える
- 差分が無いときは、開いたままの自動 PR を閉じる。PAT の失敗は「未設定」と「無効」で文言を分ける
- **人の操作は不要になる見込み。** ただし `GITHUB_TOKEN` で実際に統合できるかは、統合後の実測で判定する（`tasks/T-2026-10-07-auto-merge-regen-pr/RESULT.md` §4）

### 生成物の自動の作り直し（2026-10-07、philip）

`T-2026-10-07-auto-regen-projections`（GPU 不使用）。

- `.github/workflows/regen-projections.yml` — phase0 への push で `make taskindex` と `make inbox` を走らせる。
  生成物（`context/auto/` の 3 つと `tasks/inbox.md`）に差分があれば `auto/regen-projections` へ push し、phase0 への PR を作る
- phase0 は PR が必須（承認 0 件、enforce_admins）のため、直接 push はしない。**統合は人手で行う。**
  PR の作成には `auto-draft-pr.yml` と同じ `AUTOSYNC_PR_TOKEN` を使う
- 統合後に動作を確かめる手順は `tasks/T-2026-10-07-auto-regen-projections/RESULT.md` §4

### 追加動画 17〜21 の工程の注釈の追跡（2026-10-07、efros）

`T-2026-10-07-track-extra-phase-annotations`（GPU 不使用）。

- `data/annotations/egosurgery_phase/` の追加動画 17〜21 の CSV 20 件（210618 バイト）を今の場所のまま版管理に入れた。
  動画 22 は含まない。一覧・要約値と、同じ経路に未追跡の写しを持つホストでの手順は `docs/stage1/extra_phase_annotations.md`
- `scripts/analysis/a1_fold_table.py` — `load_phase` に `videos` を足し、`main` が公式分割の 15 動画を渡す。
  20 件が在っても止まらず、表の要約値は折り表の契約の記録と一致する
- このディレクトリを丸ごと読む 7 月の監査と EDA の 8 本は変えていない。再実行すると 17〜21 が入り値が変わる（同文書の表）

### 設計に使う val 動画の部分集合の全数列挙（2026-10-07、efros）

`T-2026-10-07-design-val-subset-balance`（GPU 不使用）。ラベルの統計だけを読み、モデルの出力と評価値は読まない。

- `scripts/analysis/design_val_subsets.py` — 折り表の val 10 本の空でない部分集合 1023 通りについて、設計側 S と
  清浄側 C（15 動画から S を除く）の欠落・均衡指標 d・折りごとの清浄本数・非劣の印を出す。注釈の読み込みと d は
  生成器 `a1_fold_table.py` の関数をそのまま使い、工程は折り表の 15 動画に絞る。`--write` で
  `docs/stage1/design_val_subsets.{csv,md}` を書く。集合は選ばない
- 注意: `data/annotations/egosurgery_phase/` に追加動画（17〜21）の CSV が置かれたホストでは、
  `a1_fold_table.load_phase` がそれも読むため、生成器 `a1_fold_table.py` 自体は 20 動画で分け方が 0 通りになり止まる
  （`T-2026-10-07-track-extra-phase-annotations` で解消）

### 工程塔の寄与の診断（2026-10-05、dlsta）

`T-2026-10-04-ptower-attribution-val`。学習なし、推論と勾配のみ。W&B へは送らない（契約の禁止事項）。

- `scripts/ptower_attribution.py` — 三周目の確定工程塔（seed 42、COCO 系・ImageNet 系）を、公式 test を除く val 七動画に
  その動画を val に持つ折りの塔でだけ通す。基準の再現（`baseline`）、現フレームの Grad-CAM・遮蔽 14 条件×2 範囲・
  過去フレームの寄与（`run`）、規則で選んだ過去フレームの地図（`positional`）。特徴キャッシュは対象の行だけを memmap で読む。
  全件の出力は repo の外（既定 `/home/ubuntu/local/ptower_attribution_20261005/`、環境変数 `PTOWER_ATTR_OUT`）
- `scripts/ptower_attribution_summary.py` — 集計。小さい表と報告は `experiments/analysis/ptower_attribution/`
- `tests/test_ptower_attribution.py` — 対象集合、読み込みの記録、四領域、人工の地図、面積を揃えた対照、memmap の行読み、過去フレームの選定規則

### Stage 2 の準備: 標的群・交差適合の規約化と日数の出し直し（2026-10-02）

`T-2026-09-27-stage2-prep`（GPU 不使用）。

- `context/conventions.md` に `det_groups` 節（標的群 5 クラス・陰性対照群 4 クラス）と `crossfit` 節（閾値 3pt）を追加。
  既存の節の本文は不変
- `scripts/build_stage1_group_ap.py` — 群を規約の表から読み、既存の `eval_{val,test}.json` の per-class AP から
  標的群 AP と陰性対照群 AP を計算する（**再評価しない**）。評価集合に出現しないクラスは除き 0 で埋めない。
  NaN と注釈の欠落の一致を照合する。出力は `docs/stage1/D_group_ap.md` と
  `experiments/baselines/stage1_dtower_r2/group_ap.json`
- `docs/proposals/2026-09-27-ptower-20.md` — P\*-20 の提案カード（`check_proposal.py` 検出 0 件）
- `tools/estimate_tier_cost.py` — 交差適合の送り手の学び直し二行（`t1_crossfit_det`・`t1_crossfit_phase`）、
  過去の前提を再現する `Assumptions.hours_override`、節 `history`（9/17 と 9/27 の差の分解）と `crossfit`
  （Tier 1 の 4 通りと締切）、`--doc-sections`（節の一部だけを載せる文書の照合）を追加。
  **TF32 は計算器に一度も入っていない**（9/17 の 74.0〜98.7 日は計算器の外で 1/1.182 を当てた値）。
  新しい文書は `docs/stage1/B2_tier1_cost_with_crossfit.md`

### data/README.md の全面更新（2026-10-05）

`data/README.md` を aolab の実測（2026-10-05）に合わせて書き直した。旧版（2026-07-01）は `raw/exo/`・擬似ラベル・
外部データセットを前提にしていたが、いずれも空のまま使われていない。新版は各ディレクトリの規模・内容・生成スクリプト、
追加動画 17〜21 のフレーム（`raw/ego/other(17~21)/`）、5 折りの注釈、`processed/` の成果物、Git 管理の範囲を記す。
🔴 `data/eval_staging/` の 2 リンクは絶対パスで Git 管理されており、経路の違うホストでは切れる。

2026-10-05 追記: `data/README.md` §2.1 に動画単位 5 折りの詳細（折り表、折りごとの画像数・box 数・欠けるクラス、
工程のフレーム数、生成と検証、`file_name` が公式分割のディレクトリ名を保持する点、使い方と規律）を足した。

### Stage 1 工程塔 P\*-20 の確定と送り手の train−val 差（2026-10-05）

`T-2026-09-27-stage1-ptower-20`（efros、GPU 2 枚、fine-tune 90.0 GPU 時間）。三周目の確定 recipe のまま、
追加動画 17〜21 を各折りの train にだけ足した P\*-20 を二系統で確定した。動画 22 はフレームが無いので使わない。

- `scripts/build_phase_manifest_p20.py` — 15 動画の manifest を写し、追加 20 clip を `train.json` にだけ足す。
  **全画像をデコードし、注釈と画像のフレーム集合の一致を要求する**（数だけでは途中で切れた画像を通す。動画 19 の
  1,932 枚が実際に通った）。出力は `data/processed/stage1_features/p20_manifest/`
- `scripts/stage1_ptower_20.py` — 三周目の `finetune` / `extract` / `train` をそのまま呼び、`data_setting=P20` のとき
  折り表の train に 17〜21 を足すだけの入口。`data_setting=P15` は三周目そのもの（ホスト差の対照）
- `scripts/run_stage1_ptower_20.py` — GPU ごとの待ち行列。走行中の同一設定と使用中の GPU を避ける
- `scripts/select_stage1_ptower_20.py` — `table`（P\*-15 と並置）/ `test`（確定塔を折りごとに一度）/
  `gap`（送り手の train と val の差）
- `scripts/stage1_ptower_r3.py` は `data_setting` と `pin_memory` を設定から読む（既定は三周目のまま）。
  **efros（cgroup 上限 52 GiB）で 2 本並べるときは `pin_memory: false`**。PyTorch 2.1 の pinned メモリの
  キャッシュが val 1 回で約 24 GiB まで積もり返らず、OOM になった。数値は同一（logits の要約値で確認）

現状: P\*-20 の val macro Jaccard は COCO 0.7012 / ImageNet 0.5999、test は 0.6402 / 0.5317。
**P\*-15（ilya）との差はホスト差と分離できない**（efros の対照が ilya より +0.0696、閾値 0.0372）。
送り手の train と val の差は 4 塔 × 5 折りの 20 件すべてで 3pt を超え（最小 +0.1254）、工程塔の送り手にも
交差適合が要る。表は `docs/stage1/ptower_20.md`。

### 現行サーバー構成（Ubuntu 24.04 / CUDA 12.9 / gcc 13）への追従（2026-10-13、andrew）

サーバーが文書作成時の構成（Ubuntu 22.04 / nvcc 11.8）から移ったため、環境構築の前提を実測で引き直した。
**torch 2.1.2+cu118 と 2 本の lock は変えていない**（受け取り手を揃える規約のため）。変えたのはホスト側の前提だけである。

- `scripts/setup_env.sh` — nvcc 11.8 の必須検査を外した。全依存が prebuilt wheel で入り、何もビルドしないため。
  それまで efros / dlsta / lecun は `SKIP_CUDA_CHECK=1` で飛ばしていた（受信箱の 2026-09-17・09-20 の指摘）
- `scripts/setup_env_relation_detr.sh` — nvcc 12.x を受け入れ、**MS-Deform-Attn のビルドとロードまで検証する**
  手順 5 を足した。上流は失敗を warning に落として先へ進むので、これまでは初回の forward まで気づけなかった。
  ソースの有無は `main.py` で見る（checkpoints だけのホストを通さない）
- `scripts/restore_relation_detr_source.sh` — 新設。上流 `b485955` + snapshot の patch・tarball でソースを復元する
- `docs/environment.md` / `docs/reproduce_on_new_machine.md` / `CLAUDE.md` — 構成表と手順を現行へ直した
- **`scripts/` の `CUDA_HOME` の既定を `/usr/local/cuda-11.8` から `/usr/local/cuda` へ一括で置き換えた**（24 ファイル）。
  現行サーバーに `/usr/local/cuda-11.8` は無く、拡張の再ビルドが要る場面で失敗していたため。内訳は
  `export CUDA_HOME="${CUDA_HOME:-...}"` の 15 本（`run_t1b*.sh` / `run_t1c_*` / `run_hc_seeds_lecun.sh` /
  `run_l1_2_oracle_phase_lecun.sh` / `verify_*_init_identity.sh`）、固定値の 3 本（`_detector_full_study.sh` /
  `_extract_improved.sh` / `_hand2det_gpu1_chain.sh`）、使い方コメントの 6 か所（`extract_t1a_regiontoken.py` /
  `train_t1b.py` / `train_hand2det.py` / `audit_t1b_l0.py` / `audit_l2_hand2det_l0.py` / `run_t1a.sh`）。
  ホスト名つきの過去スクリプトも含むが、変えたのはこの 1 行だけで、旧構成のホストで流すときは
  `CUDA_HOME=/usr/local/cuda-11.8` を渡せば元どおりになる（固定値の 3 本は該当行を戻す）。
  `docs/` と `tasks/` の過去の記録にある `cuda-11.8` は当時の事実なので書き換えていない

実測（andrew）: 既定値のまま `setup_env_relation_detr.sh` が最後まで通り、凍結源 seed42 で val 先頭 8 フレームを
forward した region token が既存の `t1a_regiontoken/relation_detr_seed42` と **bit 一致**した。本体 `.venv` は
既存のもので mamba の GPU forward と mmcv の GPU 演算（nms / MS-Deform-Attn）を確かめた。

未検証・残り:

- `setup_env.sh` は修正後に頭から流していない（検証済みの `.venv` を作り直さないため）。変えたのは検査の削除だけである
- 検出塔の学習（`main.py`）と逆伝播は andrew では流していない。順伝播の一致だけを見た
- ~~snapshot は 2026-08-02 時点で、それ以降に efros で足した実装を含まない~~ → **2026-10-17 に解消**（`T-2026-10-17-tower-reselect-prereq`）。efros の実体から snapshot を取り直し
  `third_party_snapshot/efros/2026-10-17/Relation-DETR/` に置いた。andrew へ `util/convergence.py`・`main.py`・
  Stage 1 の ImageNet 用 config 3 件を戻し、`tests/test_stage1_dtower_convergence.py` は 9 件収集・9 件 PASS。
  2026-08-02 の snapshot は変えていない（既定の版も efros の 2026-08-02 のまま）
- テスト: 上の 1 ファイルを除き 793 passed / 6 failed。失敗は既知の 5 件と
  `test_fetch_task.py::test_rejects_unknown_file_name`（エラー文言の食い違い。今回の変更とは無関係）
- CUDA 11.8 を足す経路も試し、gcc 11 の追加と `CPATH` の解除で動くことは確かめたが、12.9 のままで足りるので採らない

### Stage 2 の前提の実測: フレームと注釈の対応・送り手信号の時刻（2026-10-14、andrew）

契約 `T-2026-10-14-frame-signal-audit`（analysis。装置も推論も使わない）。結果は `experiments/analysis/frame_signal_audit/REPORT.md`、
道具は同 `tools/`（`audit_frames.py` が注釈・manifest・画像を直接読む方法 A、`count_shell.sh` がシェルで辿る方法 B、
`time_alignment_check.py` が送り手信号の時刻の判定と陽性対照）。既存のスクリプトは変えていない。

- 術具注釈 = 工程塔の manifest（15 動画）= `data/raw/ego/` の画像 = 15,437 で完全一致。工程注釈だけの 1,796 枚は
  `data/raw/OpenSurgery_Dataset/01_frames/initial_videos/` に全数在り復号できる（区間 03_3 の 168 枚を含む）
- 番号は区間ごとの抽出の通し番号で、区間が変わると振り直される。0.5 fps は文書の記載で、番号→秒の対応は配布物に無い（仮定として扱う）
- Stage 1 の工程塔は動画の区間を連結した 1 本の列を見る（履歴は区間の境界をまたぐ）。Jaccard と accuracy は全フレーム合算
- 既存の送り手信号 6 経路はすべて同時刻 t。「一つ前の時刻まで」の規則は実装にも repo の文書にも無い

### 両塔の学び直しの前提: 検出器の収束規則の復元・評価時の入力の大きさ・規約（2026-10-17、andrew）

契約 `T-2026-10-17-tower-reselect-prereq`（impl。装置は使わない）。記録は `tasks/T-2026-10-17-tower-reselect-prereq/`。

- **新しい snapshot** `third_party_snapshot/efros/2026-10-17/Relation-DETR/`。二周目の D\*-COCO を学習した efros の実体を
  読むだけで取り寄せた。`util/convergence.py` は二周目の写しと sha256 一致、`main.py` は写しの抜粋 23 + 61 行が行番号ごと一致。
  2026-08-02 版との差は追加 4（`util/convergence.py`、`train_config_egosurgery_stage1_imagenet_seed{42,123,456}.py`）と変更 1（`main.py`）。
  復元スクリプトを変えずに `bash scripts/restore_relation_detr_source.sh efros/2026-10-17 <dest>` で指定できる
- **andrew の検出器**（`third_party/Relation-DETR/`）へ上の 5 件を置いた。上書きは `main.py` の 1 件で、前の版は
  `~/m2-evacuated/T-2026-10-17-tower-reselect-prereq/` に退避した。拡張の生成物・checkpoints・凍結源・COCO 初期化の重みは前後で sha256 一致。
  `main.py` は `--convergence-schedule` `--plateau-patience` `--plateau-factor` `--max-epochs` を受け付け、二周目の設定を解釈できる（学習はしていない）
- **検出塔の評価時の入力の大きさ（実測）**: 原寸 1920×1080 → 縮小後 **1333×749**、pad 後 **1344×768**（W×H）。
  これまでの計算値 1333×750 は丸めの違いで、実装は `(orig * r).to(int)` で切り捨てる（`base_detector.py:49-50`）。
  前処理だけを装置なしで動かして測った。学習時の多尺度の変換 `presets.detr` は評価の経路に入らない
- **規約**: `conventions#symmetry` の「意図的に変える」の理由に 3「各塔の構造の標準の処方」を足した（使える比較・行・条件と使えない行）。
  `conventions#frame_sets` を新設し、塔と界面が学習・評価に使うフレームの集合を置いた

### Stage 2 の非公式の予備測定（折り A、今ある塔、界面の型の第一波）（2026-10-18、andrew）

契約 `T-2026-10-18-stage2-pilot-folda`（analysis。**非公式の予備測定。関門の判定と設計の判断に使わない**）。
結果は `experiments/analysis/stage2_pilot_folda/REPORT.md`、記録は `tasks/T-2026-10-18-stage2-pilot-folda/`。

- 今ある検出塔（D\*-COCO 折り A seed 42）と工程塔（efros の P\*-15-COCO 折り A seed 42）を凍結し、界面だけを学んで、
  折り A の val で両方向・型ごと・腕ごとの Δ を測った。PD（工程→検出）は P1-W1・P1-W2・P2L・P2F・P3（seed 42 だけ）、
  DP（検出→工程）は D1-L1・D1-L2・D2・D3-L1・D3-L2（seed 42・123・456）。DP 63 本、PD 22 本、交差適合用の塔 4 本。
  正解の腕で PD の標的群 AP は P1 +0.020〜+0.023、P2L +0.014、P3 はほぼ零。DP は D1-L1 の全腕で Jaccard が約 +0.009、D1-L2・D3 は Jaccard と accuracy が逆向き。
  交差適合版の送り手は確定塔の val より大きく弱い（検出 train mAP 0.40、工程 train Jaccard 0.24）。D1・D3 の空の腕は構造上 3 seed で同一（R = 0）
- **`scripts/train_t1b.py` に引数を足した（既定の経路は変えていない。`tests/test_train_t1b_stage2pilot_defaults.py` で固定）**:
  `--det-ckpt`、`--signal-train/--signal-val`（次元は信号から決まる）、`--fixed-table`、`--eval-only`、`--patience`（学習率一定・停滞で停止）、
  `--best-excludes-init`、`--ckpt-dir`、`--save-trainable-only`、`--trainable w2`（decoder の最終層とその層のヘッド）。信号が欠けたフレームがあれば止まる
- **新しい道具 `scripts/stage2pilot/`**: 信号の保存（`extract_det_signals.py`、`phase_signals.py`）、時刻の確認（`time_check.py`）、
  PD の界面（`pd_model.py`、設定 `configs/stage2pilot/pd_*`）、DP の受け取り手と学習器（`dp_model.py`、`dp_train.py`）、
  交差適合（`crossfit_split.py`、`make_cf_annotations.py`、`run_cf_dtower.sh`、`cf_ptower.py`）、集計（`aggregate.py`）、test 不使用の検査（`test_audit.py`）
- **andrew の GPU 2 枚の DDP は `NCCL_P2P_DISABLE=1` が要る**（IOMMU が有効で、P2P の all_reduce が無言で止まる）。andrew で検出塔の学習が動くことを初めて確かめた
- 大きな生成物（信号・checkpoint・交差適合用の検出塔）は版管理と同期の外 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/` に置いた

### 証拠地図の照合器と様式の検査、契約の追加ファイルの宣言（2026-10-19、bengio）

契約 `T-2026-10-18-evidence-verify-place`（impl。装置は使わない）。記録は `tasks/T-2026-10-18-evidence-verify-place/`、置き場の説明は `docs/evidence/README.md`。

- **照合器** `tools/verify_evidence_ids.py`（`make evidence-verify MAP=<地図>`）。地図の DOI と arXiv ID を抜き出し、ID ごとに
  実在・書誌一致 / 実在・書誌に差 / 実在・照合不能 / 不在 / 到達不能 に分ける。DOI の実在は doi.org の handle で確かめ（登録機関によらない）、
  書誌は登録機関（Crossref・DataCite）の API、arXiv は API に一つの地図の ID をまとめて引く。問い合わせに連絡先を入れない。
  結果は `docs/evidence/verification/<地図>.json` と `.md`
- **様式の検査** `tools/check_evidence_map.py`（`make evidence-check`）。雛形 `docs/evidence/_template.md` の「検査が見る項目」を見る。
  禁止語は `context/conventions.md` から `tools/check_proposal.py` の関数で読む
- **spec の schema** に `inputs.bundle_extras` を足した（`tools/fetch_task.py` の `extras_from_spec` と同じ制約）。これまでは宣言つきの契約が
  取り込みの最後の L1-1 で落ちて巻き戻っていた。全 147 契約（本契約を含む）の `make task-validate` の成否は変更の前後で同じ
- **置いたもの**: 地図 C v2・B v2・N v1 と雛形を `docs/evidence/`、元の報告五件を `docs/evidence/reports/`（中身は手を加えていない）。
  旧地図 B（2026-09-16）の冒頭に v1 であることと後継を明記した。旧地図 A は変えていない
- **照合の結果**（2026-10-19）: 地図 C 29 ID（一致 27・差 1・照合不能 1）、B 34 ID（一致 29・差 5）、N 36 ID（一致 16・差 2・照合不能 18）。
  不在と到達不能は 0。様式の検査は三つとも違反 0。地図の本文は書き換えていない（差をどう反映するかは起票者が決める）
- 試験: `tests/test_verify_evidence_ids.py`（HTTP は差し替え、通信の口を塞いで実行）・`tests/test_check_evidence_map.py`・`tests/test_bundle_extras_schema.py`

### Stage 2 予備測定の直し: 4 epoch 目の値と入れ替えの腕（2026-10-19、andrew・一部 bengio）

契約 `T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`（analysis。**非公式の測定。関門の判定と設計の判断に使わない**）。
結果は `experiments/analysis/stage2_pilot_fix/REPORT.md`、記録は `tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/`。

- 前回の予備測定（`T-2026-10-18-stage2-pilot-folda`）の値を、学習を 4 epoch 終えた時点の状態（最良の回を選ばない）で出し直し、
  全型に**入れ替えの腕**（予測-noCF と同じ値の集まりで、フレームとの対応だけを seed 42 の並べ替えで壊した腕）を足した。
  DP 26 本（seed 42 の回し直し 21、入れ替え 5）、PD 12 本（回し直し 8、入れ替え 4）と P2F の入れ替えの評価 1 本。DP の回し直しは前回の epoch 1〜4 と完全一致した。
  予測-noCF の Δ入替（信号の中身による差）は D1-L1 で Jaccard +0.0013（Δ空 +0.0046 の大半は入れ替えた信号でも出る）、P1-W1・P1-W2・P2L で標的群 AP +0.0087・+0.0149・+0.0075、
  D3 と P3 は負。選び方による差は小さかった。P3 の予測-CF・正解予測-CF は利用者の承認で bengio で回した
- **`scripts/train_t1b.py` に `--fixed-epochs` を足した**（`--epochs` の回数を止めずに学び、最後の epoch の状態を結果にする。学習率一定。
  metrics.json・per_class_ap.json・best_t1b.pth・best の予測がその状態になり、`result_selection: final_epoch` を残す）
- **`scripts/stage2pilot/dp_train.py` に `--fixed-epochs N`・`--task-id`・`--exp-prefix`・`--smoke`・腕 `shuffle`・`identity --arm` を足した**。
  どちらも既定の経路は変えていない（`tests/test_train_t1b_stage2pilot_defaults.py`、`tests/test_stage2pilot_dp_train_defaults.py` で固定）
- 新しい道具 `scripts/stage2pilot/`: 入れ替えた信号（`shuffle_signals.py`）、起動（`run_pd_fix.sh`・`run_dp_fix.sh`。`run_pd_fix.sh` は
  `S2FIX_BODY`・`S2FIX_CODE` で別ホストの worktree から回せる）、後処理（`pd_fix_finalize.py`）、集計（`aggregate_fix.py`）、
  前回の材料の照合（`material_check.py`）、test 不使用の検査（`test_audit_fix.py`）、別ホストの入力の照合（`input_digest.py`。Relation-DETR の未 commit の変更を中身で比べる）
- GPU 1 枚に PD を 3 本載せても合計の速さは伸びない（andrew の実測で 3% と 0）。bengio の `third_party/Relation-DETR` は andrew と 23 件違い、
  検出器の仮想環境も壊れていた（この契約では andrew の中身を別の場所に置いて参照させ、仮想環境を uv の 3.11.16 に向け直して回した）
- 大きな生成物（入れ替えた信号・重み）は版管理と同期の外 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/` に置いた

### Stage 2 予備測定に界面の新しい型を四つ足す（2026-10-20、bengio・decoder-xattn は andrew）

契約 `T-2026-10-19-stage2-pilot-four-new-types`（analysis。**非公式の測定。関門の判定と設計の判断に使わない**）。
結果は `experiments/analysis/stage2_pilot_four/REPORT.md`（実行中は `INTERIM.md`）、記録は `tasks/T-2026-10-19-stage2-pilot-four-new-types/`。

- 前回と直しの契約と同じ条件（折り A、seed 42、4 epoch 目の状態、6 腕）で、利用者が送った界面の提案カードのうち四つの型を回す:
  工程から検出の **decoder-xattn**（decoder の全層の FFN の後に工程の token 4 個への cross-attention とゲート tanh(α_l)）と **extra-queries**
  （元の 900 query を変えずに追加の 30 query を足し、凍結した D\* の見落としにだけ当てる）、検出から工程の **logit-correction**
  （最後の段のロジットに零初期化の補正）と **tool-history**（検出の系列を GRU でまとめて最後の段の特徴に足す。カードどおりのゲートつきとゲートなし版）
- 利用者の承認で直しの契約の終了を待たずに bengio の worktree から始めた。主のホストは bengio で、decoder-xattn の 6 本は andrew（`handoff_andrew.md`）。
  逸脱は `spec.yaml` の `meta.amendments`
- **`scripts/train_t1b.py` に `--missed-set`（extra-queries の train の見落としの印）と、`gate_values` を持つ検出器のゲートの epoch ごとの記録を足した。**
  **`scripts/stage2pilot/dp_model.py`・`dp_train.py` に型 LC・TH・TH-NG と 32 次元の x(t) を足した。** どれも既定の経路と既存の型は変えていない
  （`tests/test_train_t1b_stage2pilot_defaults.py`・`tests/test_stage2pilot_dp_train_defaults.py` が通り、既存の型の恒等性と陽性対照が直しの契約の記録と全項目一致）
- 新しい道具 `scripts/stage2pilot/`: 新しい PD の型（`pd_four.py`、設定 `configs/stage2pilot/pd_{dec_xattn,extra_q}_d{9,18}.py`、生成器 `make_pd_four_configs.py`）、
  評価（`pd_four_eval.py`）、起動（`run_pd_four.sh`・`run_dp_four.sh`・`run_pd_four_identity.sh`）、後処理（`pd_four_finalize.py`）、
  見落としの集合と寄与（`xq_missed.py`）、殺し実験（`kill_four.py`）、test 不使用の検査（`test_audit_four.py`）、集計（`aggregate_four.py`）
- extra-queries は、元の query の出力を構成で塔単独と同じに保つため、元の経路を D\* のまま回し、追加の query だけを各層で元の query の入力を key・value に加えて別に回す
  （界面の重みを乱数にしても元の出力は塔単独と差 0、mask を外すと変わることを確かめた）
- 大きな生成物（D\* の train の出力、見落としの集合、界面の重み）は版管理と同期の外 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/` に置いた
- 結果（2026-10-20、非公式。1 折り・val 2 動画・seed 1 つの 1 本ずつの差）: 検出から工程の三つの型はどれも塔単独を上回らず、予測-noCF の Δ入替（信号の中身による差）は logit-correction +0.0016・tool-history 0.0000・ゲートなし版 −0.0045（Jaccard）。tool-history のゲートは開かず（tanh(α) ≤ 0.012）、ゲートなし版は空の腕でも −0.082。extra-queries は追加の出力が上位 300 に一件も出ず全腕が塔単独と同値（スコアの定数 −10 → −9.5）。decoder-xattn は正解の腕で標的群 AP の Δ空 +0.0051・Δ入替 +0.0055、予測-noCF で +0.0006・+0.0010。G1・G2・G3 pass、31 本すべて完了

### task-start の汚れの分類・停止して再開した契約の検査・folds の重なり（2026-10-21、andrew）

契約 `T-2026-10-21-ops-taskstart-resume-folds-val`（impl。GPU 不使用）。記録は `tasks/T-2026-10-21-ops-taskstart-resume-folds-val/`。

- **`scripts/task_start_classify.py` を足した。** 作業ツリーの汚れを `origin/phase0` の木と中身（`git cat-file --filters`）で比べて分類する（読み取りだけ）。
  起点と同じ中身の未追跡・無視されたファイルは通し、中身が違えば無視されていても止める（git は無視された未追跡を切り替えで黙って上書きする）。
  追跡下の変更と起点に無い未追跡は従来どおり止める。止めたときは分類ごとの件数と経路を出す（中身は出さない）
- **`scripts/task_start.sh`**: 取得を汚れの判定の前へ移した（巻き戻しの対象外）。通した経路は切り替えの前に索引へ載せ（書き直されない）、
  巻き戻しでは索引から外してから `read-tree -m -u` で元の木へ戻す（作業ツリーのファイルを消さない）。終了コードの意味は変えていない
- **task スキルの「0. 始める」**は同じ分類器を読む。無視の一覧に足してよいのは分類で phase0 に無いと出た経路だけ（`.codex/skills/task` はシンボリックリンクで写しは一つ）
- **`tools/preflight_task.py` の `completed_verdicts`**: 完了済みを「verdict に空でない値があり、かつ `tasks/<id>/result.yaml` が `origin/phase0` の木に在る」とした。
  停止して再開した契約で P13・P14・allow_write の規則が働く。参照が解決しないときは従来の判定へ戻り、警告を一行出す。phase0 の上の完了済みは前後 128 件・差 0 件
- **規約 `folds` に「val と test の重なり」を置いた**（利用者の決定 2026-10-19）。`docs/issuer-defects.md` に測らずに断定した例を 2 件足した
- 試験: `tests/test_task_start_classify.py`（新規）、`tests/test_symmetry_gate.py`・`tests/test_legacy_exclusions.py`・`tests/test_proposal_card_gate.py`（完了済みの新しい定義）

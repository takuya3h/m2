# 別マシンでの環境再現 — Claude Code 向け指示書

このドキュメントは、**別のマシン（サーバー）の Claude Code が
`egosurgery_multitask` の実行環境を再現する**ための作業指示書である。
リポジトリを clone した直後、環境構築を依頼されたときにこの手順に従うこと。

> [!IMPORTANT]
> 本プロジェクトは **2 つの venv** を持つ。用途で使い分ける:
> - **本体 `.venv`** — 工程認識(TeCNO)・評価・S0〜S9 学習・テスト。mmdet/mamba を含む。
> - **検出器 `.venv-relation-detr`** — Relation-DETR の推論・特徴抽出。①系統の
>   検出器 forward（Stage1 GAP / B2a tool-presence / **T1a region-token**）と
>   B1 統合トレーナーで使う。MS-Deform-Attn を実行時 JIT ビルドする（要 CUDA 11.8）。
>
> **検出器側の実験（B2a / T1a 等）を再現するには両方を構築すること。**

再現セット（方法 A）は次のファイルで構成される。すべて Git 管理されている:

- `requirements.lock.txt` — 本体 `.venv` の全パッケージ厳密版（正本・100 pkg）
- `scripts/setup_env.sh` — 本体 `.venv` の作成〜導入〜検証を自動化
- `requirements.relation_detr.lock.txt` — 検出器 `.venv-relation-detr` の厳密版（正本・72 pkg）
- `scripts/setup_env_relation_detr.sh` — 検出器 venv の作成〜導入〜検証を自動化
- `docs/environment.md` — OS / driver / CUDA 等のシステム層の記録

---

## 手順 0: 前提の確認（必ず最初に実施）

以下を確認し、`docs/environment.md` の「検証済みシステム構成」と照合する。
**不足があれば構築を進める前にユーザーへ報告し、判断を仰ぐこと。**

| 確認 | コマンド | 期待値 |
|---|---|---|
| OS | `. /etc/os-release; echo $PRETTY_NAME` | Linux x86_64（Ubuntu 22.04 系を推奨） |
| NVIDIA driver | `nvidia-smi --query-gpu=driver_version --format=csv,noheader` | 525 以降（検証は 535） |
| **CUDA Toolkit** | `nvcc --version` | **release 11.8**（最重要） |
| uv | `uv --version` | 導入済み |
| GPU | `nvidia-smi -L` | NVIDIA GPU が見える |

判断基準:

- **nvcc が 11.8 でない**: `mamba-ssm` / `causal-conv1d` のソースビルドが torch
  cu118 と不整合になり失敗する。CUDA 11.8 Toolkit の導入をユーザーに依頼する
  （`/usr/local/cuda-11.8` を用意し `CUDA_HOME` で指す）。導入できない場合のみ、
  ユーザー合意のうえ mamba 系を諦めて `SKIP_CUDA_CHECK=1` で続行する。
- **uv が無い**: `curl -LsSf https://astral.sh/uv/install.sh | sh` で導入する。
- **GPU が無い / driver 不可**: CPU でも import・テストは通るが学習は実用的でない。
  その旨をユーザーへ明示する。
- **nvcc が見つからない**: CUDA Toolkit 未導入。導入をユーザーに依頼する。

## 手順 1: 環境構築の実行

前提が満たされたら、プロジェクトルートで次を実行する:

```bash
bash scripts/setup_env.sh
```

このスクリプトは「特殊 tier（torch cu118 / mmcv prebuilt / mamba ソースビルド）を
正しい方法で先に導入 → `requirements.lock.txt` を `--no-deps` で適用し全 100
パッケージを厳密版へ固定 → `egosurgery` を editable install → 検証」を自動で行う。

- mamba-ssm / causal-conv1d の CUDA 拡張ビルドに数分〜十数分かかる。
- 長時間になるため **`run_in_background: true` で起動し、Monitor で
  進捗と失敗（`Traceback|Error|ERROR|fatal`）を監視**すること。

## 手順 1.5: 検出器 venv の構築（B2a / T1a 等を再現する場合のみ）

検出器側の実験（①系統: Stage1 GAP 抽出 / B2a tool-presence / **T1a region-token** /
B1 統合トレーナー）を再現するなら、続けて検出器 venv を構築する:

```bash
CUDA_HOME=/usr/local/cuda-11.8 bash scripts/setup_env_relation_detr.sh
```

- `requirements.relation_detr.lock.txt`（72 pkg, torch 2.1.2+cu118）を厳密適用する。
- mmdet/mamba は**含まない**（検出器の推論専用の軽い env）。
- MS-Deform-Attn はここではビルドされない。**初回の detector forward で JIT ビルド**
  される（`source .venv-relation-detr/bin/activate` で ninja を PATH に載せ、
  `CUDA_HOME` が 11.8 を指していること）。
- `third_party/Relation-DETR` がチェックアウト済みであること。

## 手順 2: 検証

各 `setup_*.sh` の末尾で自動検証が走るが、加えて次を確認する:

```bash
.venv/bin/python -m pytest tests/ -q          # 2026-08-11 の実測で 319 テスト収集
```

- **既知の失敗は 5 件ある。この 5 件以外がパスすれば環境健全とみなす。**
  いずれも**環境非依存**であることを実測で確かめてある（2026-08-11 / lecun）。

  | テスト | 性質 |
  |---|---|
  | `test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics` | 証跡不整合による既知 fail |
  | `test_research_logger.py` の 4 件 | Notion 記録まわりの実装と試験の不一致。`log_run` が `None` を返し `log_experiment_to_notion` が呼ばれない。`origin/phase0` の時点から失敗している（`B-40` として起票済み） |

  **数は増える。** テスト件数と既知の失敗の一覧は、書かれた時点の実測でしかない。
  食い違ったら**この文書ではなく実測を信じ、文書を直すこと**（捏造禁止: 既知 fail を
  隠さず報告する）。
- `.venv/bin/python` で `torch.cuda.is_available()` が `True`、`mmcv` / `mmdet` /
  `mamba_ssm` / `causal_conv1d` が import でき、`egosurgery` が解決できることを確認。
  （スラッシュコマンド `/env-check` が使えるならそれでもよい。）
- 検出器 venv を構築した場合: `.venv-relation-detr/bin/python` で
  `torch.cuda.is_available()` が `True`、`accelerate` が import できることを確認。
  MS-Deform-Attn の JIT ビルドは手順 5 の region-token 抽出スモークで初めて検証される。

## 手順 3: 完了報告

ユーザーへ次を簡潔に報告する:

- 検証済みシステム構成との一致/相違（特に nvcc・driver・GPU）
- `pytest tests/` の結果（パス数）
- `torch.cuda.is_available()` と GPU 名
- mamba-ssm / mmcv 等の導入可否
- 相違や未導入があれば、その理由と影響を**正直に**述べる

---

## 手順 4: 実験データ・凍結資産の配置（検出器側の実験に必須）

`git clone` では入らない大物が複数ある。比較の三角形は**同一の凍結源**を絶対条件と
するため、凍結 ckpt は**再学習せず元サーバー（lecun 等）からバイト一致で転送**する。

| 資産 | パス | サイズ | git | 入手 |
|---|---|---|---|---|
| **凍結源 ckpt** | `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth` | 195MB | 無視 | **必須・転送**（三角形の土台。再学習不可） |
| **画像** | `data/raw/ego/<split>/<video>/*.jpg` | 1.2GB | symlink のみ | **必須・転送**（下記） |
| **phase manifest** | `data/processed/phase_manifest/{train,val,test}.json` + `phase_vocab.json` | 1.7MB | 無し | **必須・転送** |
| COCO annotations | `data/annotations/` | 59MB | 管理(30) | clone で入る（不足あれば転送） |
| GAP cache | `data/processed/stage1_features/relation_detr_seed42/` | 122MB | 無視 | 任意（S4 を server B で再走する場合のみ） |

**画像の配置（symlink の罠に注意）**: 元サーバーでは `data/raw/ego/<split>/<video>` は
外部実体（例: `/home/.../EgoSurgery/images/by_split/...`）への **symlink**。symlink を
そのまま転送すると実体が無く、抽出が「読込失敗→skip」で静かに欠落する（Fail Loud 違反）。
**`rsync -aL` で実体を解決して直置き**するのが最も安全:

```bash
# 元サーバー側で実行（-L で symlink を辿り実ファイルをコピー）
rsync -aL data/raw/ego/  <user>@<serverB>:<repo>/data/raw/ego/
rsync -a  data/processed/phase_manifest/  <user>@<serverB>:<repo>/data/processed/phase_manifest/
rsync -a  third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth \
          <user>@<serverB>:<repo>/third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
```

配置後の整合確認（manifest の image_path が解決し、ckpt が読めること）:

```bash
.venv/bin/python - <<'PY'
import json, pathlib
m = json.loads(pathlib.Path("data/processed/phase_manifest/val.json").read_text())
fr = m["clips"][0]["frames"][0]
p = pathlib.Path(fr["image_path"])
print("image exists:", p.exists(), p)
print("ckpt exists:", pathlib.Path("third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth").exists())
PY
```

## 手順 5: T1a（region-token→工程）を実行する

T1a = Tier-1 主力「TAPIS/GraSP 型 region-token→工程」（②系統・Δ_phase）。
凍結 Relation-DETR seed42 の **object-query 埋め込み（region token）** をフレーム毎に
抽出し、TeCNO の入力を frame GAP → region token に差し替える。分母は **S4 base
（素 TeCNO on GAP = lecun 実測 0.8986±0.0034）を流用**し、サーバー差は §8.0 として
notes/experiment_log に明文化する（同一 ckpt・同一前処理ゆえ差は TeCNO 学習の数値のみ）。

```bash
# 1) 検出器 venv で region-token 抽出（JIT ビルドは初回 forward で走る）
CUDA_HOME=/usr/local/cuda-11.8 CUDA_VISIBLE_DEVICES=0 .venv-relation-detr/bin/python scripts/extract_t1a_regiontoken.py --subset val --limit 8   # スモーク
for sub in train val test; do
  CUDA_HOME=/usr/local/cuda-11.8 CUDA_VISIBLE_DEVICES=0 .venv-relation-detr/bin/python scripts/extract_t1a_regiontoken.py --subset "$sub" --limit 0
done

# 2) 本体 venv で TeCNO 学習（3-seed）
.venv/bin/python scripts/train_t1a.py --smoke          # 疎通
bash scripts/run_t1a.sh 42 0
bash scripts/run_t1a.sh 123 0
bash scripts/run_t1a.sh 456 0
```

- 抽出・学習とも GPU 長時間ジョブは `run_in_background: true` + Monitor で運用。
- 完走後: 証跡 `experiments/transfer/t1a_regiontoken_*` に mAP 不要・工程指標が揃うこと、
  `Δ_phase=(T1a − 0.8986)` を **paired-σ(対seed差)** で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。
- **数値捏造禁止**。未収束・環境制約は実測値と理由をそのまま報告する。

---

## やってはいけないこと

- **`requirements.lock.txt` を無視して最新版を入れ直さない。** バージョンの
  整合（torch cu118 ↔ nvcc 11.8、transformers 4.44.2 ↔ mamba-ssm 2.2.2 等）が
  崩れ、再現が壊れる。
- **torch を `>=2.2` 等へアップグレードしない。** cu118 ビルドと mm 系・mamba の
  prebuilt/ビルド整合が崩れる。
- **`transformers` を 4.45 以降にしない。** mamba-ssm 2.2.2 の import が壊れる。
- 環境が壊れているように見えても、まず `docs/environment.md` の「既知のハマり
  どころ」を確認する。安易な再インストールより原因特定を優先する。
- **metrics / mAP 等の実験数値を捏造しない**（CLAUDE.md の研究インテグリティ）。

## 補足

- `pyproject.toml` の `[project.dependencies]` には torch / mmcv / mamba 系を
  含めていない（CUDA 依存で通常解決に乗らないため）。これらは `setup_env.sh` が
  専用 index・find-links・ソースビルドで導入する。
- より厳密な完全再現が必要なら、`nvidia/cuda:11.8.0-cudnn8-devel` ベースの
  Dockerfile 化（方法 B）をユーザーに提案する。

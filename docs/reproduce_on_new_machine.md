# 別マシンでの環境再現 — Claude Code 向け指示書

このドキュメントは、**別のマシン（サーバー）の Claude Code が
`egosurgery_multitask` の実行環境を再現する**ための作業指示書である。
リポジトリを clone した直後、環境構築を依頼されたときにこの手順に従うこと。

再現セット（方法 A）は次の 3 ファイルで構成される。すべて Git 管理されている:

- `requirements.lock.txt` — 全 Python パッケージの厳密バージョン（正本）
- `scripts/setup_env.sh` — venv 作成〜全依存導入〜検証を自動化したスクリプト
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

## 手順 2: 検証

`setup_env.sh` の末尾で自動検証が走るが、加えて次を確認する:

```bash
.venv/bin/python -m pytest tests/ -q          # 23 テストがパスすること
```

`.venv/bin/python` で `torch.cuda.is_available()` が `True`、`mmcv` / `mmdet` /
`mamba_ssm` / `causal_conv1d` が import でき、`egosurgery` が解決できることを確認。
（プロジェクトのスラッシュコマンド `/env-check` が使えるならそれでもよい。）

## 手順 3: 完了報告

ユーザーへ次を簡潔に報告する:

- 検証済みシステム構成との一致/相違（特に nvcc・driver・GPU）
- `pytest tests/` の結果（パス数）
- `torch.cuda.is_available()` と GPU 名
- mamba-ssm / mmcv 等の導入可否
- 相違や未導入があれば、その理由と影響を**正直に**述べる

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

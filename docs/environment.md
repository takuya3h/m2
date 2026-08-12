# 実行環境（再現用システム情報）

`egosurgery_multitask` を別マシンで再現するためのシステム層の記録。
Python パッケージの版は `requirements.lock.txt`、導入手順は
`scripts/setup_env.sh` を参照（この 3 つで方法 A の再現セットを構成する）。

## 検証済みシステム構成

| 項目 | 値 | 備考 |
|---|---|---|
| OS | Ubuntu 22.04.3 LTS (x86_64) | Linux x86_64 必須 |
| Python | 3.11.4 | `uv venv --python 3.11` |
| uv | 0.11.15 | パッケージ/venv 管理 |
| NVIDIA driver | 535.288.01 | **最低要件: CUDA 12.x 対応（525 以降）** |
| CUDA Toolkit (nvcc) | **11.8** (V11.8.89) | `/usr/local/cuda` → cuda-11.8 |
| GPU | NVIDIA RTX A6000 (49140 MiB) | VRAM 目安。学習構成に応じて要調整 |

## CUDA に関する重要事項

- torch は **cu118 ビルド**（`torch==2.1.2+cu118`）。driver 535 は CUDA 12.2 まで
  対応するが、CUDA の **minor-version 互換**により cu118 ランタイムが動作する。
- **システムの nvcc は 11.8 でなければならない**。`mamba-ssm` / `causal-conv1d`
  （および必要時の `mmcv` ソースビルド）は CUDA 拡張をビルドするため、torch の
  cu118 と nvcc のバージョンが一致している必要がある。nvcc が 12.x 等だと
  ビルドが失敗する。
- `mmcv` は cu118/torch2.1 の prebuilt wheel を使うためビルド不要。

## 主要パッケージ（厳密版は requirements.lock.txt が正本）

| パッケージ | バージョン | 導入方法 |
|---|---|---|
| torch / torchvision | 2.1.2+cu118 / 0.16.2+cu118 | `--index-url .../whl/cu118` |
| mmcv | 2.1.0 | `--find-links` cu118/torch2.1 |
| mmdet / mmengine | 3.3.0 / 0.10.7 | PyPI |
| mamba-ssm / causal-conv1d | 2.2.2 / 1.4.0 | ソースビルド（nvcc 11.8） |
| transformers | 4.44.2 | mamba-ssm 2.2.2 の旧 generation API 互換のため固定 |
| numpy | 1.26.4 (<2) | torch 2.1 系の要件 |

総パッケージ数: 100（`requirements.lock.txt` 参照）。

## 別マシンでの再現手順

1. OS（Ubuntu 22.04 系）・NVIDIA driver（525 以降）・**CUDA Toolkit 11.8** を導入。
2. `uv` を導入: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. リポジトリを clone。
4. `bash scripts/setup_env.sh` を実行（venv 作成〜全依存導入〜検証まで自動）。
5. `.venv/bin/python -m pytest tests/ -q` で 23 テストが通ることを確認。

Claude Code に再現を依頼する場合は `docs/reproduce_on_new_machine.md` を参照。

## 既知のハマりどころ

- `setuptools>=81` は `pkg_resources` を削除済み → mamba 系のソースビルドが失敗。
  `setup_env.sh` は `setuptools<80` を先に導入して回避する。
- `transformers>=4.45` は mamba-ssm 2.2.2 が参照する旧 generation API を削除済み。
  `4.44.2` 固定を厳守する。
- nvcc が 11.8 でない環境では `setup_env.sh` が停止する。CUDA 11.8 を導入するか、
  mamba 系を諦める場合のみ `SKIP_CUDA_CHECK=1` で続行可能。

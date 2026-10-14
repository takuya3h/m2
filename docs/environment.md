# 実行環境（再現用システム情報）

`egosurgery_multitask` を別マシンで再現するためのシステム層の記録。
Python パッケージの版は `requirements.lock.txt`、導入手順は
`scripts/setup_env.sh` を参照（この 3 つで方法 A の再現セットを構成する）。

## 検証済みシステム構成

サーバーは Ubuntu 24.04 / CUDA 12.9 / gcc 13 のコンテナへ移った。**Python 側（torch 2.1.2+cu118 と
lock）は旧構成のまま変えていない。** 変わったのはホスト側だけである。

| 項目 | 現行（2026-10-13 andrew 実測） | 旧構成（文書作成時） |
|---|---|---|
| OS | Ubuntu 24.04.4 LTS (x86_64) | Ubuntu 22.04.3 LTS |
| Python | 3.11.16（`uv venv --python 3.11`） | 3.11.4 |
| uv | 0.12.5 | 0.11.15 |
| NVIDIA driver | 595.84 | 535.288.01 |
| CUDA Toolkit (nvcc) | **12.9** (V12.9.86)、`/usr/local/cuda` | 11.8 (V11.8.89) |
| gcc | 13.3.0 | — |
| GPU | NVIDIA RTX A6000 (49140 MiB) | 同じ |

## CUDA に関する重要事項

- torch は **cu118 ビルド**（`torch==2.1.2+cu118`）。CUDA ランタイムは wheel に同梱されており、
  新しい driver の上でそのまま動く。
- **本体 `.venv` はシステムの nvcc を使わない。** `mmcv` / `mamba-ssm` / `causal-conv1d` は
  すべて cu118/torch2.1 の prebuilt wheel で入り、`setup_env.sh` は何もビルドしない。
  nvcc 12.9 のホストで mamba の GPU forward と mmcv の GPU 演算（nms / MS-Deform-Attn）が
  動くことを確かめてある（2026-10-13 andrew）。
- **検出器 `.venv-relation-detr` だけが nvcc を使う**（MS-Deform-Attn の JIT ビルド）。
  nvcc 12.9 + gcc 13 でビルドした拡張は、凍結源 seed42 の出力を bit 一致で再現する
  （2026-08-29 lecun: val mAP 0.7303 / 2026-10-13 andrew: 既存の region-token キャッシュと一致）。
  拡張は `libcudart.so.12` に動的リンクするため、実行時に `$CUDA_HOME/lib64` が
  `LD_LIBRARY_PATH` に載っている必要がある（現行コンテナは既定で載っている）。
- 🔴 **CUDA 11.8 の toolkit を後から足さないこと。** nvcc 11.8 は gcc 13 を扱えず
  （`_Float32 is undefined`）、コンテナ既定の `CPATH=/usr/local/cuda/include` が 12.9 の
  ヘッダを先に読ませて `undefined symbol: __cudaLaunchKernel` になる。gcc 11 の追加と
  `CPATH` の解除で動かせはするが、12.9 のままで足りるので要らない（2026-10-13 andrew 実測）。

## 主要パッケージ（厳密版は requirements.lock.txt が正本）

| パッケージ | バージョン | 導入方法 |
|---|---|---|
| torch / torchvision | 2.1.2+cu118 / 0.16.2+cu118 | `--index-url .../whl/cu118` |
| mmcv | 2.1.0 | `--find-links` cu118/torch2.1 |
| mmdet / mmengine | 3.3.0 / 0.10.7 | PyPI |
| mamba-ssm / causal-conv1d | 2.2.2 / 1.4.0 | GitHub の prebuilt wheel（cu118/torch2.1） |
| transformers | 4.44.2 | mamba-ssm 2.2.2 の旧 generation API 互換のため固定 |
| numpy | 1.26.4 (<2) | torch 2.1 系の要件 |

総パッケージ数: 100（`requirements.lock.txt` 参照）。

## 別マシンでの再現手順

1. OS・NVIDIA driver・CUDA Toolkit は現行コンテナのままでよい（追加導入は不要）。
2. `uv` を導入: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. リポジトリを clone。
4. `bash scripts/setup_env.sh` を実行（venv 作成〜全依存導入〜検証まで自動）。
5. `.venv/bin/python -m pytest tests/ -q` を実行する（件数と既知の失敗は
   `docs/reproduce_on_new_machine.md` の手順 2）。
6. 検出器側も使うなら `bash scripts/restore_relation_detr_source.sh`（ソースが無いとき）→
   `bash scripts/setup_env_relation_detr.sh`。

Claude Code に再現を依頼する場合は `docs/reproduce_on_new_machine.md` を参照。

## 既知のハマりどころ

- `setuptools>=81` は `pkg_resources` を削除済み。`setup_env.sh` は `setuptools<80` を
  先に導入して回避する。
- `transformers>=4.45` は mamba-ssm 2.2.2 が参照する旧 generation API を削除済み。
  `4.44.2` 固定を厳守する。
- 既存の venv がある状態で `setup_*.sh` を再実行すると `uv venv` が止まる。
  作り直すときは `UV_VENV_CLEAR=1` を付ける。
- `setup_env.sh` は 2026-10-13 まで nvcc 11.8 を必須にしていたが、何もビルドしないため外した
  （それまで各ホストは `SKIP_CUDA_CHECK=1` で飛ばしていた）。

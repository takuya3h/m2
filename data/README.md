# Data

このディレクトリはデータを管理します。**データ本体は Git 管理しません。**

## ディレクトリ構成

| ディレクトリ | 説明 |
|---|---|
| `raw/` | 元データ。ダウンロード後は原則として変更しない |
| `interim/` | 中間生成データ（前処理途中のもの） |
| `processed/` | 学習・評価で使う前処理済みデータ |
| `external/` | 外部から取得した追加データ（公開データセット等） |
| `splits/` | train/val/test 分割ファイル |

## Git 管理ポリシー

- `raw/`, `interim/`, `processed/`, `external/` は `.gitignore` により Git 管理**しない**
- `splits/` は再現性に直結するため Git 管理**する**
- データの取得手順は `scripts/download_data.sh` を参照

## splits/ の形式

各ファイル（`train.txt`, `val.txt`, `test.txt`）には、1行につき1サンプルの識別子（ファイルパスや ID）を記載します。

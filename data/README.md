# data/

データセットの格納ディレクトリ。**`raw/` `processed/` `external/` `annotations/` の中身は
Git 管理しない**（`.gitignore` 参照）。`splits/` とこの `README.md` のみ Git 管理する。

---

## データ取得手順

主データセットは EgoSurgery 系列。各自でダウンロードし、下記の配置に従って展開する。

| データセット | 内容 | 配置先 |
|--------------|------|--------|
| **EgoSurgery-Tool** | 手術器具のバウンディングボックス検出 | `data/annotations/egosurgery_tool/` + `data/raw/ego/` |
| **EgoSurgery-Phase** | 手術フェーズ認識 | `data/annotations/egosurgery_phase/` + `data/raw/ego/` |
| **EgoSurgery-HTS** | Hand-Tool セグメンテーション（mask アノテーション） | `data/annotations/egosurgery_hts/` + `data/raw/ego/` |

EgoSurgery データセットは公式配布元（プロジェクトページ）の手続きに従って取得する。
取得後、フレーム/クリップを `data/raw/ego/{train,val,test}/` に展開し、
アノテーション（COCO 形式 JSON など）を `data/annotations/` 配下に置く。

外部データセット（転移学習・比較用）:

| データセット | 配置先 |
|--------------|--------|
| PHAKIR | `data/external/phakir/` |
| CholecT45 | `data/external/cholect45/` |
| EgoExoR | `data/external/egoexor/` |

> `DATA_ROOT` 環境変数（`.env` 参照）で実体の場所を指定し、`data/` 内へは
> シンボリックリンクを張る運用も可。

---

## ディレクトリの用途

```
data/
├── raw/                      # 生データ（フレーム・動画）
│   ├── ego/{train,val,test}/ # Ego（術者視点）映像。分割ごと。
│   └── exo/view_1..view_5/   # Exo（外部固定カメラ）映像。視点ごと。
├── annotations/              # アノテーション
│   ├── egosurgery_tool/      # 器具検出 bbox
│   ├── egosurgery_phase/     # フェーズラベル
│   ├── egosurgery_hts/       # Hand-Tool セグメンテーション mask
│   └── pseudo_labels/        # 自動生成された擬似ラベル
│       ├── hand_tool_relation/  # 手-器具の関係擬似ラベル
│       ├── exo_phase_transfer/  # Exo から転写したフェーズ擬似ラベル
│       └── bbox_near_contact/   # 接触近傍 bbox 擬似ラベル
├── processed/                # 前処理済みデータ
│   ├── ego_frames/           # 抽出済み Ego フレーム
│   ├── exo_clips/            # 切り出し済み Exo クリップ
│   ├── features/             # 事前抽出特徴量
│   └── copypaste_bank/       # Copy-Paste 拡張用のオブジェクトバンク
├── external/                 # 外部データセット
└── splits/                   # データ分割定義（Git 管理する）
```

`raw/exo/` を `view_1` 〜 `view_5` に分けるのは Ego/Exo パイプラインの明示的分離のため。
推論時は Ego 単独で動作する制約を保つ。

---

## `splits/` のデータ分割定義

| ファイル | 内容 |
|----------|------|
| `ego_train.txt` | Ego 学習サンプルの ID 一覧（1 行 1 ID） |
| `ego_val.txt` | Ego 検証サンプルの ID 一覧 |
| `ego_test.txt` | Ego テストサンプルの ID 一覧 |
| `exo_sync_map.json` | Ego フレームと Exo フレームの時刻同期マップ |
| `surgeon_folds.json` | 術者単位の交差検証 fold 定義（術者リークを防ぐ） |

`splits/` は実験の再現性に直結するため Git 管理する。分割を変更したら必ずコミットする。

---

## Git 管理方針

| 区分 | 対象 |
|------|------|
| **管理する** | `data/README.md`、`data/splits/`（配下ファイルすべて） |
| **管理しない** | `data/raw/`、`data/processed/`、`data/external/`、`data/annotations/`（JSON・HTS・擬似ラベル） |

これはルート `.gitignore` で実装されている。大容量・再生成可能なものを除外し、
分割定義のような「軽量だが再現性の根幹」をなすものだけを残す方針。

# Relation-DETR スナップショット（efros、2026-10-17）

- upstream: https://github.com/xiuqhou/Relation-DETR.git
- base commit: b485955c72452788240600da6d0f0b8cc49f33c7（efros の `git rev-parse HEAD` の実測）
- 取得日: 2026-10-17 / 取得ホスト: efros（andrew から読むだけで取り寄せた）
- 取得時の efros の m2: HEAD `57717f6c`、分岐 `feat/legacy-exclusions-and-type-sync`
- 契約: `T-2026-10-17-tower-reselect-prereq`（命令と出力は同契約の `audit.md`）

**二周目（`T-2026-09-19-stage1-detector-towers-r2`）の D\*-COCO と D\*-ImageNet を学習した efros の実体である。**
二周目の写し（`experiments/baselines/stage1_dtower_r2/impl/`）と次のとおり一致した。

| 照合 | 結果 |
|---|---|
| `util/convergence.py` と `convergence.py.txt` の sha256 | 一致（`299597a2…`） |
| `main.py` と `main_py_arguments.txt`（行番号つき抜粋） | 23 行中 23 行が同じ行番号で一致 |
| `main.py` と `main_py_training_loop.txt`（同） | 61 行中 61 行が一致 |

## 内訳（実測値）

| ファイル | 内容 |
|---|---|
| `reldetr_upstream_mods.patch` | upstream 追跡ファイルへの改変 4 件（`main.py` / `optimizer/param_dict.py` / `transforms/presets.py` / `util/engine.py`）。762 行 |
| `reldetr_project_files.tar.gz` | 未追跡ファイルのうちソースと設定。35 件 |
| `tar_contents.txt` | tarball に実際に含まれる 35 件の一覧 |
| `file_list.txt` | efros の `git status --porcelain --untracked-files=all`（`__pycache__` と `.pyc` を除く）。除外したものも含む全 95 行 |
| `sha256sums.txt` | efros 上で測った 39 件（tarball の 35 件と改変 4 件）の sha256 |
| `diff_vs_2026-08-02.txt` | 2026-08-02 の snapshot（`../../Relation-DETR/`）との差。追加 4 件、変更 1 件 |

`main.py` の patch が大きいのは、上流の `main.py` が CRLF で、efros の版が LF だからである。
改行を揃えた実質の差は 72 行（収束規則の import、引数 4 つ、学習の繰り返しの分岐、収束の記録）。

## 2026-08-02 版との差

| ファイル | 差 |
|---|---|
| `util/convergence.py` | 追加。収束規則 `PlateauSchedule` |
| `main.py` | 変更。`--convergence-schedule` `--plateau-patience` `--plateau-factor` `--max-epochs` |
| `configs/train_config_egosurgery_stage1_imagenet_seed{42,123,456}.py` | 追加。D\*-ImageNet の設定（COCO 重みを読まない点だけが D\*-COCO と違う） |

D\*-COCO の設定 `configs/train_config_egosurgery_seed42.py` は 2026-08-02 版と同一である。

## 含めないもの

checkpoints、学習の出力、データ（入れ子の `third_party/Relation-DETR/data/processed/**/*.bin` 25 件）、
評価の出力の json（`per_class_coco_map/epoch_0{00..30}.json` 31 件）、拡張の生成物とビルドの中間物、
`__pycache__`。**2026-08-02 版は `per_class_coco_map` の json 12 件を tarball に含めていたが、本版は含めない。**

## 使い方

既存の復元スクリプトを変えずに、この版を指定できる。

    bash scripts/restore_relation_detr_source.sh efros/2026-10-17 <dest>

スクリプトは `<dest>/main.py` が既に在ると何もしない。既存のソースへ重ねる用途には使えない。

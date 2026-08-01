# runindex/ — experiments/ から収穫した横断インデックス

**これは派生物です。手で編集しないでください。**

```bash
make runindex      # runindex/ 全体をゼロから再生成する
```

生成元は `tools/harvest_runindex.py`。入力は `experiments/**` のみで、
出力は入力が同じなら常に同じになります (冪等)。

## ファイル

| ファイル | 内容 |
|---|---|
| `index.csv` | 1 行 = 1 **run** の横断インデックス。`runs/*.json` から導出 |
| `per_class.csv` | 1 行 = 1 run × 1 クラス。per-class を long 形式で 1 ファイル化 |
| `experiments.csv` | 1 行 = 1 **実験**（seed 集約 + 対照 Δ）。論文 Table の 1 行に対応 |
| `runs/<ledger_key>.json` | 正規化済みの run 記録 |
| `host_aliases.json` | host 正規化の対応表 |
| `metric_aliases.json` | 指標名の表記ゆれ統合表 |
| `anomalies.md` | 規約から外れたもの・判断を保留したものの一覧 (人間が読む) |
| `anomalies/val_test_pairs.csv` | test 評価を持つ run の val/test 対応表 (縦持ち) |
| `anomalies/backlog.md` | 本タスクの範囲外として起票した未着手事項 |

## index.csv の列

| 列 | 意味 |
|---|---|
| `metric.<name>` | **primary (= `split` 列が指す側。実質 val) の値** |
| `metric_test.<name>` | **test 側の値**。別列なので既存列の意味は変わらない |
| `has_test` | test 評価を持つか。`true` の run だけ `metric_test.*` が埋まる |
| `metrics_primary_split` | `metric.*` が実際にどの split 由来か。`split` 列と一致する |
| `experiment_id` | seed 集約の単位。`experiments.csv` と結合するキー |
| `arm` / `control_of` | 注入か対照か / 対照とする実験 |
| `frozen_source_tag` | 凍結特徴の抽出元。**run 名にも `command.sh` にも現れない条件軸** |

`metric.*` だけを見ると test 評価の存在に気づけません。
val と test は大きく乖離するため、下流解析では `has_test` で分岐してください。
乖離の実測は `anomalies.md` §13.1 と `anomalies/val_test_pairs.csv` にあります。

## per_class.csv（目的①: per-class の横断分析）

`ledger_key` で `index.csv` と結合できます。単独でも分析できるよう
`group` / `step` / `seed` / `split` / `host` / `excluded` を再掲しています。

> **⚠️ `tool` と `phase` を混ぜて集計しないでください。**
> `per_class_kind=tool` は術具 15 クラスの **AP**、
> `per_class_kind=phase` は工程 9 クラスの **F1** です。指標の種類が違います。
> 元ファイルはどちらも `per_class_ap.json` という名前なので、名前では判別できません。
> 必ず `per_class_kind` / `per_class_metric` で分離してください。

`value` が空欄の行は元が `NaN`（`is_nan=true`）。術具側の `NaN` は
**val split に GT が 1 件も無いクラス**であり 0 ではありません。

## experiments.csv（目的②: 機構・条件の横断比較と回帰）

1 行 = 1 実験 = seed をまたいで束ねた 1 条件。

| 列 | 意味 |
|---|---|
| `n_runs` / `n_seeds` / `seeds` | 集約した run 数・seed 数・seed 一覧 |
| `runs_per_seed_max` | 同一 seed の run 数の最大。**> 1 は再実行か条件混在の徴候** |
| `n_command_variants` | `command.sh` 引数の種類数。**> 1 なら条件が混在している** |
| `hosts` | 使われた host。**複数なら交絡の可能性がある** |
| `<metric>_mean` / `_pstd` / `_min` / `_max` | seed 集約 |
| `arm` / `control_of` | 注入 / 対照。`control_of` は対照実験の `experiment_id` |
| `delta_<metric>` / `delta_pstd_<metric>` | `control_of` が確定した実験のみ |
| `delta_method` | `paired` か `unpaired` か。**混同してはいけません** |
| `control_note_value` | `notes.md` に引用されている基準値（実測との突き合わせ用） |

`delta_pstd_*` は `delta_method=paired` のときだけ入ります。
対応が取れない場合に paired-σ は定義できないため、空欄にしてあります。

## 注意

- `runs/*.json` のファイル名は `run_id` (ディレクトリ名) ではなく
  `ledger_key` (experiments/ からの相対パス由来) です。
  ディレクトリ名は 6 種が 3 箇所ずつ衝突するためです。
- `split` は次の順で確定します。**推測値は入れません。**
  1. 指標キーの形式 (`val/…` / `test_…` / `phase_…` + 学習スクリプトのコード)
  2. `command.sh` / `config.yaml` / `eval_recipe.eval_split`
  3. 正本 M2研究計画 §16.7 の既定 (`metrics.json` は全て val)
  由来は `provenance.split` に入ります。指標が 1 つも無い run は `null` です。
- 元データの `NaN` は標準 JSON として不正なため `null` に変換しています。
  どのクラスが `NaN` だったかは `per_class_nan_classes` に保持しています。
- `per_class_ap.json` は名前に反して **中身が F1 の群が 500 run** あります。
  必ず `per_class_metric` 列 (`AP` / `F1` / `unknown`) で判別してください。

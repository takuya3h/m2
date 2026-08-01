# backlog — 本タスクの範囲外として起票した未着手事項

**これは派生物です。手で編集しないでください**（`tools/harvest_runindex.py` が生成）。

指示書 #02 §0「明示的にやらないこと」に該当するため、着手せず記録だけしたもの。
いずれも価値はあるが**監査・整備であって分析可能性を上げない**ため、
分析基盤（`index.csv` / `per_class.csv` / `experiments.csv`）の完成を優先した。

| # | 事項 | 分かっていること | 着手の前提 |
|---|---|---|---|
| B-1 | 573 run の `git_commit.txt` 実在性の全件検査 | `t1b_phasefilm_{001,002}` は記録された commit `a697d90` に `scripts/postprocess_t1b.py` が存在せず、**記録された commit では再現できない**ことが確認済み。他 571 run は未検査 | 全件 `git cat-file` する走査を書く。`experiments/` は読み取りのみ |
| B-2 | `b2b_rescore_alpha{0.5,1.0,2.0}` の entrypoint 特定 | `verify_no_dummy_metrics.py` の死角スキャンが新規に検出。`command.sh` に python 呼び出しが無く、どのコードが mAP を書いたか不明 | 3 run の `command.sh` / `notes.md` / ログを個別に読む |
| B-3 | Notion 実験Run台帳との run_id 単位の突合 | 母数が 616 か 739 か未確定（§14）。データソース重複・フィルタ付きビュー・DB 重複はいずれも排除済み。`Status='failed'` が 0 件であることは母数に依らず確定 | Notion のクエリ利用上限の解除、または `.env` の `NOTION_API_KEY` 使用の承認 |
| B-4 | dummy Trainer の除去 | `src/egosurgery/engines/trainer.py` が乱数で per-class AP を生成し `mAP` として書く。混入は現時点 0 件と検証済みだが**コードは残っている**（§11） | 学習コードの変更にあたるため、本タスクでは触れない |
| B-5 | `experiments/README.md` の更新 | 規定は 17 種の step 識別子だが実データには 156 種ある（§12）。観測された family は b1 / b2a / b2b / t1a / t1b / taux / haux / hires | README は規約側の文書であり、実データに合わせて書き換えるかは方針判断 |
| B-6 | 非標準群の adapter | `analysis` / `detector_improve` / `audit` / `ablations` / `final` / `g2_main_*` は `metrics.json` を持たず収穫できない（§9）。取りこぼした run は 0 件（そもそも run 構造ではない） | 群ごとにファイル形式が違うため個別の読み取りが要る |
| B-7 | `ledger_key` フィールド名の改名 | `ledger/` → `runindex/` の改名後も、フィールド名 `ledger_key` は 573 個の JSON と `index.csv` 第 1 列に残っている | スキーマ変更になるため利用側の合意が要る |
| B-8 | `b2a_ro_oracle_noise000` の名前と実態の食い違い | 名前は noise 0.00 を示すが `--tool-noise-rate` は 0.05/0.10/0.20/0.30 の 4 通り（§7.3）。原因は `scripts/run_b2a_ro_oracle_noise_sweep.sh` のタグ生成が `bc` に依存しており、`bc` 不在時に全水準が `000` に潰れること。実測 accuracy も 0.9549 / 0.9435 / 0.9023 / 0.8106 と水準に応じて単調減衰しており、4 水準であることを独立に裏付ける | ディレクトリ名の改名は `experiments/` の変更にあたるため不可。正本側での扱いを決める必要がある |
| B-9 | σ の規約統一 | `S4 base` が母集団σ `±0.0028` と標本σ `±0.0034` の 2 通りで引用されている（§18.2）。`|Δ| > 1σ` 判定の結論が変わりうる | 正本 §10.1 でどちらを採るかを定める |
| B-10 | paired-σ が計算できない | 基準点実験が 17 run / 3 seed（1 seed に最大 7 run）のため、seed ごとの対応が取れず paired-σ が定義できない（§18.3）。`notes.md` は 439 run で paired-σ 判定を宣言しているが実行不能 | seed ごとの代表 run を決める規約が要る（どの再実行を採るか） |
| B-11 | `logs/phase3seed_results.tsv` の欠落 | `scripts/paired_sigma_3seed.py` はこの TSV の `arm` 列（frozen / augstrong）を読んで paired-σ を出す設計だが、ファイルが repo に存在しない（`.gitignore` 対象）。arm 情報自体は `config.yaml` の `frozen_source.*` に残っており `frozen_source_tag` として収穫済み | TSV の復元、または `paired_sigma_3seed.py` を `runindex` 由来に切り替える |
| B-12 | 573 run の外側にある inj/ctrl ペア | `transfer/*_efros/` と `experiments/transfer/{hc,oracle_phase}_seed*/` に `injected_result.json` / `control_result.json` の対が 18 組あるが、`metrics.json` を持たないため収穫対象外。真の注入/対照ペアはここにある | 非標準群の adapter（B-6）と同じ作業 |
| B-13 | 同一条件が別 `experiment_id` に分裂する 3 組 | `description` / `split` / `frozen_source_tag` が同じで `step` だけ違う組が 3 組ある（§17.2）。うち 2 組は `eval_recipe_id` による意図的分離 | 起動経路が同一かの判断が要るため harvester では決めない |

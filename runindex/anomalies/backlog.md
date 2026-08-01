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
| B-9 | σ の規約統一（**判断: 保留**） | `S4 base` が母集団σ `±0.0028` と標本σ `±0.0034` の 2 通りで引用されている（§18.2）。**利用者の判断で「両方出し続ける」ことになった**（2026-08-01）。`experiments.csv` は `verdict_10_1`（母集団σ）と `verdict_10_1_sstd`（標本σ）を並べ、食い違いを `verdict_10_1_agree=False` で検出する。実測では主指標で 1 件、全指標で 4 件のみ食い違う | **論文に数値を出す段階で必ず決める。**それまでは両方を保持する |
| B-10 | **paired-σ を可能にする「seed ごとの代表 run」規約** | 実測（§22）: `control_of` が確定した 136 実験の**全て**が paired-σ 判定を宣言しているが、実際に計算できるのは **2 実験**。阻害原因は `control_multi_run_per_seed` 119 / `seed_set_differs` 9 / 両方 4 / `both_multi_run_per_seed` 2。**seed ごとに代表 1 本を選ぶ規約を 1 つ足せば 125 実験で計算可能になる**（残り 11 は seed 集合が違うため不可）。注入側 439 run のうち 427 run は対照に同一 seed が存在する | 代表の選び方を決める（`transfer_delta_report.py` は seq 最大＝最新の再実行を採る実装がある）。決まれば harvester 側は機械的に適用できる |
| B-16 | seed 789 / 1000 の非対称な拡張 | 全 615 run 中 12 run だけが seed 789/1000 を持ち、その 12 件すべてが `scripts/run_l3_seed5_extension.sh`（「3-seed→5-seed 化、paired-σ 強化」）の産物。同スクリプトは**注入側 6 variant のみを拡張し対照 (S4 baseline) を呼んでいない**ため片側だけ 5-seed になった。paired は共通 seed で取るので計算自体は成立する | 対照側も 5-seed 化するか、789/1000 を解析から外すかの判断 |
| B-17 | `t1a_regiontraj` 系 3 実験の分母 | `config.yaml` は分母を `t1a_regiontoken base (同env efros paired)` と宣言しているが、`t1a_base_env`（efros・seeds 42/123/456・1 run/seed、config は `server_name` 以外一致）へ付け替えると追加計算なしで完全な paired になるという指摘がある | 分母の付け替えは研究上の判断。`config.yaml` の宣言に反するため harvester では変更しない |
| B-18 | σ 規約の 2 系統併存 | `pstdev` 系 48 箇所（§10.1 判定・レポート層）と `stdev`/`ddof=1` 系 16 箇所（`scripts/analysis/*` の解析・監査層）が併存（§21.2）。**Δ の規約を監査する `delta_convention_audit.py` 自身が判定側と違うσを使っている** | 正本 §10.1 でσを定義したうえで、どちらかに寄せる |
| ~~B-19~~ | ~~空の Δ scaffold~~ | **解決済み**。`scripts/compute_delta.py` / `scripts/export_paper_tables.py` / `tools/generate_delta_report.py` は 3 つとも 0 バイトで scaffold コミット `af1fc58` 以来未実装だったため削除し、`make delta` / `make tables` を `runindex/` への案内に置き換えた（利用者の判断による） | — |
| B-20 | 🔴 **学習の非決定性が制御されていない** | 同一 commit・同一 config・同一コマンド・同一 host の再実行が再現しない（`s4_phase_baseline_015` vs `_017` で macro_f1 が 0.7406 vs 0.6572）。**within-seed σ が between-seed σ を全指標で上回る**（比 1.34〜2.45）。原因は `scripts/train_s4_tecno.py:192-195` が CPU 側の seed しか設定せず、`torch.cuda.manual_seed_all` / `use_deterministic_algorithms` / `cudnn.deterministic` / `worker_init_fn` / `PYTHONHASHSEED` が皆無なこと（§25） | 学習コードの変更にあたるため本タスクでは触れない。**これを直さない限り paired-σ は seed 効果を測れない**ので、優先度は高い |
| B-11 | `logs/phase3seed_results.tsv` の欠落 | `scripts/paired_sigma_3seed.py` はこの TSV の `arm` 列（frozen / augstrong）を読んで paired-σ を出す設計だが、ファイルが repo に存在しない（`.gitignore` 対象）。arm 情報自体は `config.yaml` の `frozen_source.*` に残っており `frozen_source_tag` として収穫済み | TSV の復元、または `paired_sigma_3seed.py` を `runindex` 由来に切り替える |
| B-12 | 573 run の外側にある inj/ctrl ペア | `transfer/*_efros/` と `experiments/transfer/{hc,oracle_phase}_seed*/` に `injected_result.json` / `control_result.json` の対が 18 組あるが、`metrics.json` を持たないため収穫対象外。真の注入/対照ペアはここにある | 非標準群の adapter（B-6）と同じ作業 |
| B-13 | 同一条件が別 `experiment_id` に分裂する組 | `description` / `split` / `frozen_source_tag` が同じで `step` だけ違う組がある（§17.2）。多くは `eval_recipe_id` による意図的分離 | 起動経路が同一かの判断が要るため harvester では決めない |
| B-14 | `notes.md` の凍結源記載が虚偽 | `s4_phase_baseline` の 55 件すべてが「凍結源: Relation-DETR seed42」と書くが、実際の `frozen_source.cache_dir` が違う run が 38 件（うち 24 件は seed 123/456）。`scripts/train_s4_tecno.py` の固定 f-string に由来。`config.yaml` の `frozen_source.seed` も 42 ハードコード | 学習コードの変更にあたるため本タスクでは触れない。過去の `notes.md` は `experiments/` 配下なので修正不可 |
| B-15 | g2_* 群に対照宣言が無い | 42 run が `config.yaml` を持たないため `control_of` を確定できない（§20）。`metrics.json` の `system` フィールド（base / bboxROI / shuffleROI）が arm を表す可能性はあるが、対照関係の明示ではない | 実験設計の意図を確認したうえで、`system` を arm として採用してよいか決める |

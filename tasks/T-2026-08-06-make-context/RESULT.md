# RESULT — T-2026-08-06-make-context

**実行者:** aolab / feat/make-context / 2b353f62b880687ba299cffcc2912902b616cbd6
**実行日時:** 2026-08-06T12:09:54Z
**判定:** PASS

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy | 省略 | 自己契約では未使用 |
| conventions_rev | `8b17c4d` | 実測 `1201f4f`（`git log -1 --format=%h -- context/conventions.md`）。**これは逸脱ではなく SPEC Task 8 Step 1 が明示的に指示する手順**。起票者は前 task（frozen-source-and-sigma-notation, PR #44）で `conventions.md` が更新される前に本 spec.yaml を配布したため、実測値と食い違っていた。実測値へ置換した |
| depends_on | `T-2026-08-06-frozen-source-and-sigma-notation` | PR #44 マージ済み（`fb0daa0`）。依存は満たされている |

`contract.inject_verbatim` の原文（Task 実行前に取得・§10.1 判定と σ の運用に使用）:

- `#sigma`: σ は 4 系統（`{metric}_pstd/sstd`・`delta_pstd/sstd_{metric}`・`sigma_source`・`delta_sigma_source`）。既定値 `series=pstd, sigma_source=paired_delta, delta_sigma_source=paired`。判定規約は `abs(...)` 関数形で書き、縦線記法は使わない
- `#prohibitions`: `no_split_redefine` / `no_raw_write` / `no_frozen_change` / `no_estimated_values` / `no_runindex_hand_edit`
- `#naming`: 実験フォルダは `ExperimentManager` が `{step}_{seq:03d}_{description}_seed{seed}` で自動採番

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（並行 harvester 変更なし） | PASS | `gh pr list --state open` 結果 0 件。harvest_runindex.py を触る open PR なし |
| **G2**（task_id 列追加で回帰なし） | PASS | 行数 749→749 OK / 列数 88→89 OK / 除外内訳（`excluded`・`exclusion_reason` 両方）不変 / `task_id` 列あり / 非空 0 件 |
| **G3**（`make context` 冪等・容量） | PASS | `IDEMPOTENT OK`、`context/auto/` 合計 131801 bytes（≈129KB、上限 1MB 以内） |
| Task 6 手編集検出 | PASS（下記に注記） | 直接スクリプト実行: `0 / 1 / 0`。`make context-check` 経由: `0 / 2 / 0`（後述） |
| Task 8 自己検証 | PASS | `OK T-2026-08-06-make-context` / `exit=0`、WARN なし（`conventions_rev` 置換済みのため） |
| Task 8 全 task 検証 | PASS | `4 task(s), 0 failed`、`exit=0`。他 3 task の `L2-6` WARN は各 task 自身の起票時 `conventions_rev` に対するものであり、本 task の変更対象ではない |

**`make context-check` の exit code についての実測上の注記**: SPEC の完了判定表は「手編集検出 = 0 / 1 / 0」を期待しているが、`make` 経由では `0 / 2 / 0` になる。原因は GNU Make の標準動作で、レシピが失敗すると make 自身は常に exit 2 を返し（"Error N" というメッセージで子プロセスの実際の終了コードだけを表示する）、子プロセスの exit code をそのまま親の exit code にはしない。`/tmp` に最小の Makefile を作って `@exit 1` するだけのターゲットでも同じ挙動を再現した。`tools/build_context.py --check` を直接呼んだ場合は設計どおり `0 / 1 / 0` である。バグではなく make の一般的挙動なので実装は変更していない。

## 3. Task 1 実測値（すべて事前確認・読み取りのみ）

- **除外理由の実列名**: `excluded`（True/False）と `exclusion_reason`（6 種類: `identity_check` 24 / `smoke_test` 7 / `known_bad_split` 6 / `failed_run` 6 / `wrong_frozen_source` 3 / `mislabeled_arm_all_not_film` 2、空 701）の **2 列**。SPEC 付属スクリプトの `"exclud" in c.lower()` ヒューリスティックは `exclusion_reason`（`exclusion` は `exclud` を含まない）を取りこぼす。前 task の教訓どおり両方を実測してから実装に使った。
- **各 CSV の列名（実測、Task 2 前）**: `index.csv` 88 列、`experiments.csv` 402 列（指標ごとに `_mean/_pstd/_sstd/_min/_max/_n` と `delta_*` 系）、`verdicts.csv` 18 列、`per_class.csv` 12 列。
- **`verdicts.csv` の粒度**: 1038 行 / distinct `experiment_id` 159（1 実験あたり 1〜136 行）。`experiments.csv.verdict_metric` と `(experiment_id, metric)` で紐付けると **136 行**（主指標のみ）に絞れることを実測で確認した。
- **`BACKLOG` の構造**: `tools/harvest_runindex.py` の `BACKLOG` は dict/list ではなく **markdown 表を含む素の文字列**（`ast.literal_eval` で文字列として取得できる）。35 エントリ、うち 1 件（B-19）が `~~取り消し線~~` で解決済み。明示的な「重大度」列は無いが、9 件の見出しに 🔴 絵文字マーカーが付いており、これを重大度の代理指標として採用した（データに実在するマーカーを使っており、独自の重大度基準を発明してはいない）。

## 4. 成果物

| 種別 | パス | 内容 |
|---|---|---|
| harvester 拡張 | `tools/harvest_runindex.py` | `harvest_config` に `task_id` 抽出追加、`build_run_record`/`build_transfer_legacy_record` に `task_id` フィールド追加、`SCALAR_COLUMNS` に `task_id`、`EXPERIMENT_SCALAR_COLUMNS` に `task_ids`（複数形・distinct カンマ結合）、`build_experiments` に集約ロジック追加 |
| 生成器 | `tools/build_context.py`（新規） | `STATE.md` / `experiments_summary.csv` / `verdicts_summary.csv` / `open_questions.md` を `runindex/` から冪等に生成。`--only {state,questions}` と `--check` を持つ |
| テスト | `tests/test_build_context.py`（新規） | `_parse_backlog_entries` の純粋関数テスト 7 件（全 pass） |
| Makefile | `Makefile` | `context` / `context-check` ターゲット追加（`runindex-strict` の直後に挿入。既存レシピは無変更） |
| 文書 | `context/README.md` | `make context` の使い方、`auto/` と手動管理の境界、`STATE.md` に判断を書かない理由を追記 |
| 文書 | `README.md` | 「runindex と context の再生成」節を新設し `make runindex` の直後に `make context` を実行することを明記 |
| 自己契約 | `tasks/T-2026-08-06-make-context/{spec.yaml,SPEC.md,RESULT.md}` | 3 files |

**`context/auto/` のファイル別サイズ（実測、合計 131801 bytes ≈ 129KB）**:

| ファイル | サイズ |
|---|---:|
| `STATE.md` | 1997 bytes |
| `experiments_summary.csv` | 70517 bytes |
| `open_questions.md` | 4123 bytes |
| `verdicts_summary.csv` | 51068 bytes |

**`verdicts_summary.csv` は主指標のみに絞った（全行ではない）**。理由: Task 1 Step 4 の実測で `verdicts.csv` 1038 行のうち 1 実験最大 136 行という粒度が判明しており、全行を出すと外部の面での可読性が下がる。`experiments.csv.verdict_metric` と `(experiment_id, metric)` の一致で絞り込むと 136 行になり、実測（131801 bytes 全体、うち `verdicts_summary.csv` 51068 bytes）で 300KB/1MB の上限に対して十分な余裕があるため、縮退の必要は無かった。

**`task_id` 列の非空件数**: 0 / 749（正常。契約から `task_id` を持つ run はまだ存在しない）。

**L2-8 の WARN**: 出なかった。起票時 `created_from.counts`（index 749 / experiments 206 / verdicts 1038）が現在の runindex 実測と完全一致しているため（Task 2 は列を追加しただけで行数は変えていない）。

## 5. 受入基準の充足

| acceptance | 結果 |
|---|---|
| `make context` が exit 0 で四つのファイルを生成する | PASS |
| `make context` を二度実行して差分がゼロである | PASS（`IDEMPOTENT OK`） |
| `make context-check` が手編集を検出して失敗する | PASS（直接実行で `exit 1`。`make` 経由は上記注記のとおり `exit 2`） |
| context auto の総容量が上限内である | PASS（131801 bytes、上限 1MB） |
| index に task 識別子の列が追加され、行数と除外内訳が不変である | PASS |
| 生成物の先頭に自動生成の宣言と反映元の識別子がある | PASS（`STATE.md`/`open_questions.md` は先頭の HTML コメント+ヘッダブロック、CSV 2 種は先頭のコメント行に `generated_from_commit`/`generated_from_date` を埋め込んだ） |
| `make task-validate` が exit 0 | PASS |

## 6. deviations（指示書どおりにしなかった箇所）

- 指示: `tests/test_build_context.py` を書く際、SPEC は BACKLOG 解析の列数判定について具体的な実装を指定していなかった。当初 `len(cells) < 3` で「不足のみ」を不正な行とみなす実装にしていた。
- 実際: テスト作成中に、本文へ半角パイプが混入したケース（B-33 と同型の事故）で `len(cells)` が **想定より増える**ことに気づき、`< 3` では検出できず見出しが静かに切り詰められる実バグを発見した。判定を「ちょうど 5 列」の厳密一致に変更し、過不足どちらも `skipped` としてカウントするよう修正した。実データ（35 エントリ）を再生成して回帰が無いことを確認済み。
- 理由: `no_fabrication` / 未測定は UNKNOWN の原則に反し、パイプ混入時に誤った見出しをそのまま生成物へ書いてしまうため。テストを書く過程で発見した正当なバグ修正であり、SPEC の欠陥ではなく実装上の判断。
- 分類: 判断が必要だった

- 指示: `Makefile` に `context`/`context-check` を追加する際、SPEC のコード例は挿入位置に独立した `.PHONY: context context-check` 行を含んでいた。
- 実際: ファイル冒頭の既存 `.PHONY` 行にも一度 `context context-check` を追記したが、SPEC 例のとおりローカルにも `.PHONY` 行があるため二重宣言になると判断し、冒頭の行への追記は取り消した（SPEC のコード例をそのまま踏襲）。
- 理由: 二重の `.PHONY` 宣言は Make としては無害だが冗長で、既存の記述スタイル（他のターゲットは冒頭の一括 `.PHONY` に列挙）と一貫しない。SPEC のコード例を優先した。
- 分類: 判断が必要だった

- 指示: なし（想定外の観測）。Task 2 で `make runindex` を実行した際、`runindex/anomalies.md` と `runindex/anomalies/backlog.md` にも差分が出た。
- 実際: 差分の内容を確認したところ、`task_id` 列とは無関係で、(1) このホストのディスクに存在する空ディレクトリ `experiments/_smoke_proptest_20260804_223211`（2026-08-04 作成、本セッションより前から存在）が nonstandard group として新規に検出されたこと、(2) `BACKLOG` 文字列の末尾エントリ B-35 が前回コミット時点の生成物より新しく追加されていたこと、の 2 点が原因だった。どちらも `tools/harvest_runindex.py` の現在のソースとディスク状態を正しく反映した正当な再生成結果であり、G2 ゲートが検査する行数・除外内訳（`index.csv`）には影響していない。
- 理由: `git add tools/harvest_runindex.py runindex/` で許可されている再生成の副作用であり、手で編集していない。実測をそのまま記録する。
- 分類: 環境差

## 7. 未解決・申し送り

- **`context/` を外部の面へ接続する設定作業が未実施。** `context/auto/` を生成するところまでが本 task の範囲であり、Claude アプリのプロジェクト知識へこれらのファイルを実際に登録・同期する設定は別途必要（本 task の外）。
- `context/glossary.md` と `context/plan_mirror.md`（人手管理側の想定ファイル）はまだ存在しない。`context/README.md` は将来のファイルとして言及しているが、作成は別 task の範囲。
- `make context-check` の exit code が SPEC 記載の `1` ではなく `make` 経由では `2` になる件（§2 参照）。直接スクリプトを呼べば `1` であり動作は正しいが、SPEC の完了判定表を読む際は「`make` の標準動作でラップされる」ことを踏まえて解釈する必要がある。次に同種の SPEC を書く際は `make` 経由の exit code ではなくスクリプト自身の exit code で期待値を書くことを推奨する。
- 全体テストの既存 5 件の失敗（`tests/test_engines.py` 1 件、`tests/test_research_logger.py` 4 件）は本 task 範囲外の既存不整合であり、実行前から存在し件数も不変。手を付けていない。
- Task 1 開始前から存在する未追跡ファイル（`experiments/transfer/_smoke_artifacts_ctrl/` 等 3 件、`tasks/T-2026-08-03-task-contract-bootstrap/SPEC copy.md` 等 2 件、`experiments/_smoke_proptest_20260804_223211/`）には本 task で一切触れていない。

## 8. 数値の出所

すべての数値は当該コマンドのstdout/stderrまたは正本ファイル（`runindex/*.csv` の実測行数・列数、`git log`/`git diff` の実測出力、`du -sb` の実測バイト数）から取得した。未測定の項目はない。

# RESULT — T-2026-08-06-frozen-source-and-sigma-notation

**実行者:** aolab / feat/frozen-source-and-sigma-notation / 1201f4fac7f2f68457b285683a508b55f07c8dcc
**実行日時:** 2026-08-06T07:28:04Z
**判定:** PASS

## 1. 解決された参照（CLI が実行時に埋める）

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy.series | 省略 | pstd を継承可能。自己契約では未使用 |
| sigma_policy.sigma_source | 省略 | paired_delta を継承可能。自己契約では未使用 |
| sigma_policy.delta_sigma_source | 省略 | paired を継承可能。自己契約では未使用 |
| conventions_rev | `8b17c4d` | `git log -1 --format=%h -- context/conventions.md` の実測値は `1201f4f`（Task 3 の `cac8147` で conventions.md を変更、Task 8 の sha 埋め戻しでさらに `1201f4f` へ進んだ）。差分あり → 意図どおり L2-6 が WARN（下記 §2） |

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（Task 1 Step 2・凍結源ハッシュの監査記録との一致） | PASS | 下記「Task 1 実測」参照。SHA-256・サイズ・mtime とも完全一致 |
| **G2**（Task 4 Step 5・abs 記法契約が L1 を通ることを実行して確認） | PASS | `G2 OK` |

**Task 1 実測（実行ホスト: `aolab`）:**

| 項目 | 監査記録 | 実測値 | 一致 |
|---|---|---|---|
| SHA-256 | `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` | 同左 | 一致 |
| サイズ | `195421066` | `195421066` | 一致 |
| mtime | `2026-05-30 07:42:27.376519004 +0000` | 同左 | 一致 |

**Task 8 Step 3 の L2-6 WARN 生出力:**

```
WARN [L2-6] conventions.md が 8b17c4d 以降に変更されています。差分を確認してください
OK   T-2026-08-06-frozen-source-and-sigma-notation

1 task(s), 0 failed
exit=0
```

前 task（T-2026-08-05-l2-task-id-uniqueness-fix）で「L2-8 は発火条件に到達せず未検証」と申し送られたのと対になる、**L2-6 の初の実発火**を確認した。

## 3. 成果物

| 種別 | パス | 件数 |
|---|---|---:|
| ドキュメント | `context/conventions.md` | `frozen_source` の `UNKNOWN` を実測 SHA-256 へ置換、`sigma` 節に「判定規約の表記」小節を追加、変更履歴に2行追記・sha を2件埋め戻し |
| ドキュメント | `tasks/T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md` | 新規作成（ckpt 44件の棚卸し表、wrong_frozen_source 特定不能の記録、smoke ディレクトリ実測） |
| 実装 | `tools/validate_task.py` | L1-3 を表流入フィールドのみ FAIL・それ以外 WARN(`L1-3W`) に分離。`main()` の集計を warn 非算入に変更 |
| tests | `tests/test_validate_task.py` | 16 tests（旧13から `_hard` ヘルパー1関数 + テスト3件を追加） |
| テンプレート | `tasks/_templates/analysis/spec.yaml` | `sigma_policy: {series: pstd}` の明示指定行を削除（継承に一任） |
| ドキュメント | `tasks/README.md` | 「ホスト環境の既知差」節を追加（efros のパス差、凍結源11/11一致の記録） |
| 自己契約 | `tasks/T-2026-08-06-frozen-source-and-sigma-notation/{SPEC.md,spec.yaml,RESULT.md}` | 3 files |

## 4. 受入基準の充足

| acceptance | 結果 |
|---|---|
| conventions の凍結源節に UNKNOWN が残っていない | PASS |
| conventions の sigma 節に判定規約の表記ルールが明記されている | PASS（`abs(` が本文中2件、変更履歴1件） |
| 判定規約に abs 記法を書いた契約が L1 を通る | PASS（`test_abs_notation_decision_rule_passes` および Task 4 Step 5 の `G2 OK`） |
| 表へ流れるフィールドに区切り文字を書いた契約は L1 で FAIL する | PASS（`test_pipe_in_string_fails`, `test_pipe_in_gate_check_fails`） |
| 表へ流れないフィールドの区切り文字は警告となり exit code を変えない | PASS（`test_pipe_outside_table_fields_is_warning_only`。`make task-validate` は WARN を出しつつ exit=0） |
| analysis テンプレートが sigma policy を明示せず継承に任せている | PASS（`grep -n "sigma_policy" tasks/_templates/analysis/spec.yaml` は出力なし） |
| smoke 系の未追跡ディレクトリが runindex 上でどう扱われているかを実測記録した | PASS（`pth_inventory.md` に記録。3件とも index に不出現・収穫対象外） |
| tasks の README にホスト環境の既知差が記録されている | PASS |
| make task-validate が exit 0 | PASS（全 task で exit=0。L2-6 WARN は3 task 全てで発火するが exit code に影響しない） |

## 5. deviations（指示書どおりにしなかった箇所）

**このセクションは空にしない。以下6件の逸脱を記録する。**

1. 指示: Task 2 Step 2 のスクリプトで `wrong_frozen_source` 除外理由の列を特定し、除外された3 run の凍結源記載を転記する。
   実際: スクリプトの列特定ロジック（`"exclude" in c and "reason" in c`）が実列名 `exclusion_reason` にマッチせず（"exclusion" は "exclude" の部分文字列ではない）、`UNKNOWN` のまま Task 2 を部分完了とした。
   理由: SPEC「想定外が起きたときの扱い」表に明記された既定の停止条件（列特定不能→`UNKNOWN`記録・部分完了・推測で代用しない）に該当するため、実際の列名を知りつつも代用しなかった。
   分類: SPEC の欠陥（スクリプトのバグ）。

2. 指示: Task 3 Step 4 で `grep -n "UNKNOWN" context/conventions.md` の結果が `select_box_nums_for_evaluation` の1件のみになることを確認する。
   実際: 2件ヒットする（もう1件は `prohibitions` 表の `no_estimated_values` 規約説明「未測定は UNKNOWN」）。
   理由: この行は本 task 着手前のコミット（`29dde25` 以前、少なくとも `8b17c4d` 時点）から存在し、`frozen_source` とは無関係の既存記述。SPEC の想定漏れと判断し、`frozen_source` 自体の `UNKNOWN` 解消（本質的なチェック内容）が満たされていることを確認した上でそのまま進めた。
   分類: SPEC の欠陥。

3. 指示: Task 4 Step 2 で新規3テストのうち少なくとも `test_pipe_outside_table_fields_is_warning_only` と `test_abs_notation_decision_rule_passes` の2件が FAIL することを確認する。
   実際: 実装前は `test_pipe_outside_table_fields_is_warning_only` の1件のみ FAIL（15 passed, 1 failed）。
   理由: `test_abs_notation_decision_rule_passes` の `decision_rule` はパイプ文字を含まず（`abs(delta) / sigma >= 1 ...`）、旧実装（全パイプが無条件で L1-3 FAIL）でも元々 findings が空になるため、実装前から green だった。バグ検出という Task 4 の目的には影響しない。
   分類: SPEC の欠陥（想定の見積り過多）。

4. 指示: なし（本 task の対象外）。
   実際: セッション開始時点で `tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md` に無関係な未コミット差分（4行変更）が存在していたが、本 task では一切触れていない。
   理由: 本 task の Files 一覧・禁止事項に含まれず、無関係な他 task のファイルを巻き込むのは「Surgical Changes」に反するため。
   分類: 環境差（他セッションの作業途中状態と推測）。

5. 指示: Task 8 Step 6 で `git add tasks/T-2026-08-06-frozen-source-and-sigma-notation/` のみを stage してコミットする。
   実際: Step 2 で `context/conventions.md` の変更履歴に sha を埋め戻した差分は、Step 6 のコミットに含めず、`docs(context): backfill conventions changelog commit shas`（`1201f4f`）として先に単独コミットした。
   理由: Step 6 の add 対象にこの差分が含まれておらず、含めないと working tree が汚れたまま残るため。意味的にも「タスク自己契約の配置」とは別の変更（conventions.md のドキュメント修正）であり、Task 3 のコミット粒度に揃えた。
   分類: 判断が必要だった（SPEC が明記していない手順の穴）。

6. 指示: なし（Task 8 Step 2 は sha プレースホルダの置換のみを求める）。
   実際: 変更履歴表の既存行（日付列 2026-08-03・commit列 （このコミット）・変更列 新規作成）の日付を検証したところ、実コミット `8b17c4d` の実際の日付は `2026-08-05` であり、表記の `2026-08-03` と食い違うことが判明したが、日付は変更せず sha のみ `8b17c4d` に置換した。
   理由: SPEC が明示的に求めたのは sha プレースホルダの置換のみであり、日付の訂正は指示されていない範囲の変更にあたるため。
   分類: SPEC の欠陥（記録として気付いたが範囲外のため放置）。

## 6. 未解決・申し送り

- **起票時の記述の訂正（SPEC 冒頭の記載どおり）**: 起票者は当初「`third_party/` は git の同期対象外なので、多くのホストで凍結源の `verify` が不能である」と考えていた。2026-08-06 に実施した11ホストの ssh 一括監査により、`third_party/` は git 追跡対象外であっても実体（凍結源 ckpt）はホスト間で完全に同期されている（SHA-256 は11/11一致、mtime もナノ秒まで同一）ことが確認され、この当初の想定は**誤りと判明した**。本 task はこの訂正を前提に `verify: ckpt_sha256` を全ホストで実行可能なものとして `conventions.md` に記録した。
- **Task 2 の `wrong_frozen_source` 除外 run 3件は未特定のまま（`UNKNOWN`）**。除外理由列の特定ロジックのバグ（上記 deviations #1）が原因。実列名 `exclusion_reason` を使って別 task で再調査すれば特定できる見込みだが、本 task の範囲では手を付けていない。正本と同一サイズ（195421066 バイト）だが異なる SHA-256 を持つ「紛らわしい候補」が4件（`experiments/detector_improve/augstrong_*/best_ap.pth` 3件、`third_party/.../train/2026-05-30-04_24_20/best_ap.pth` 1件）見つかっており、これらのいずれかが除外理由に対応する可能性が高い。次 task での調査候補として `pth_inventory.md` に記録済み。
- **Task 6 の smoke 系ディレクトリ3件**は `runindex/index.csv` に一切現れず（index にも除外記録にも無い）、`config.yaml`/`metrics.json` を欠き収穫要件を満たさないため無害と判断した。backlog 起票は不要と結論した。
- 全体テストの既存5件の失敗（`tests/test_engines.py` 1件、`tests/test_research_logger.py` 4件）は本 task 実行前から存在し、件数も不変。本 task では一切手を付けていない。
- `tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md` の無関係な未コミット差分（本 task 開始前から存在）には触れていない（上記 deviations #4）。

## 7. 数値の出所

すべての数値は当該コマンドの stdout/stderr（`sha256sum`/`stat`/`find`/`pytest`/`grep -c`/`git log`/`git diff`/`make task-validate` の実測出力）から取得した。未測定の項目は `UNKNOWN` と明記した（Task 2 の `wrong_frozen_source` 対応表）。

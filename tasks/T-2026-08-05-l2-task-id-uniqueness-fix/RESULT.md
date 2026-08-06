# RESULT — T-2026-08-05-l2-task-id-uniqueness-fix

**実行者:** aolab / fix/l2-task-id-uniqueness / 9154ebf9f0bc6d5dcc735cc9ceaf9d9ecaf0d047
**実行日時:** 2026-08-05T13:41:00Z
**判定:** PASS

## 1. 解決された参照（CLI が実行時に埋める）

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl taskのため対象外 |
| sigma_policy.series | 省略 | pstdを継承可能。自己契約では未使用 |
| sigma_policy.sigma_source | 省略 | paired_deltaを継承可能。自己契約では未使用 |
| sigma_policy.delta_sigma_source | 省略 | pairedを継承可能。自己契約では未使用 |
| conventions_rev | `8b17c4d` | `git log -1 --format=%h -- context/conventions.md` の実測値も `8b17c4d`。差分なし・変更不要 |

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| Task 1 現状診断 | PASS | 下記「Task 1 Step 1 の生の出力」参照 |
| **G1**（Phase A後・置換前実装での失敗確認） | PASS | 追加した3テスト全件が `TypeError: task_id_conflicts() missing 1 required positional argument: 'self_ref'` でFAIL（10 passed, 3 failed） |
| Task 3 実装置換後のunit test | PASS | 13 passed |
| Task 4 end-to-end（重複ref存在時） | PASS | `make task-validate` exit=0、L2-1 findingなし |
| Task 4 end-to-end（ref削除後） | PASS | `make task-validate` exit=0 |
| Task 6 自己検証 | PASS | `OK T-2026-08-05-l2-task-id-uniqueness-fix` / `1 task(s), 0 failed` / exit=0。L2-8 WARNは発生せず（起票時counts index=749/experiments=206/verdicts=1038が現在の実測値と完全一致のため） |
| Task 6 全体テスト回帰 | PASS | 5 failed（本task実行前と同数、後述） |

**Task 1 Step 1 の生の出力（実測）:**

```
===== add-commit の数（旧 L2-1 の入力） =====
cc75a1c2bb8bb5d8642bdf25430b696e474c6e36
tasks/T-2026-08-03-task-contract-bootstrap/spec.yaml

a73288551ddf8583be0bad2091ab266427a85b4e
tasks/_templates/analysis/spec.yaml
tasks/_templates/exp/spec.yaml
tasks/_templates/impl/spec.yaml

===== 現在の L2 結果 =====
OK   T-2026-08-03-task-contract-bootstrap
OK   T-2026-08-05-l2-task-id-uniqueness-fix

2 task(s), 0 failed
exit=0
```

**分類（Task 1 Step 2）**: 各 task_id が現行historyでは1 commitのみで追加されている。**バグは潜在**（`make task-validate` は診断時点で既に exit=0・OK であり、顕在化していなかった）。

**起票時の記述の訂正**: SPEC.md 冒頭は「本 repo は auto-merge が設定済みであり、この不具合は放置すれば必ず発火する」と述べているが、これは起票者の**推測**であった。Task 1 の実測により、現在のマージ戦略・repo履歴では本バグは発火しておらず、squash/rebaseによる重複add-commitはまだ発生していないことが確認された。放置すれば将来発火しうるという設計上の懸念自体は妥当だが、「顕在化済み」という記述は実測で訂正する。

**マージ戦略の実測（2026-08-06 追加）**:

```
$ gh api repos/takuya3h/m2 --jq '{auto_merge: .allow_auto_merge, squash: .allow_squash_merge, merge_commit: .allow_merge_commit, rebase: .allow_rebase_merge, delete_branch: .delete_branch_on_merge}'
{"auto_merge":true,"delete_branch":false,"merge_commit":true,"rebase":true,"squash":true}

$ ls -1 .github/workflows/
auto-draft-pr.yml
```

`allow_squash_merge=true` かつ `allow_rebase_merge=true` であり、旧実装が壊れる発火経路（squash merge・rebase merge）は repo 設定上どちらも有効化されている。**旧実装は将来必ず壊れた**——GitHub の Web UI で本 PR を squash または rebase でマージすれば、同じ `spec.yaml` が「元ブランチの commit」と「マージ後に生成される新 commit」の2箇所で「追加」されたことになり、旧 `task_id_conflicts` は `len(commits) == 2` で FAIL していたはずである。Task 1 で観測した「バグは潜在」という状態は、**このホストでこれまで squash/rebase マージが実行されていなかった**という偶然の結果であり、発火経路そのものが無かったわけではない。

さらに `delete_branch_on_merge=false` であるため、マージ後も元ブランチは自動削除されず残存する。これにより、旧ブランチを fetch 済みのホストと fetch していない（または `fetch --prune` 済みの）ホストとで `git log --all` の到達可能コミット集合が食い違い、SPEC.md が指摘する「判定結果がホストごとに変わる」状態が常態化する設定になっている。**`delete_branch_on_merge=false` によるブランチ残存こそが、本修正（ホスト依存の偽陽性を無くす ref/`created_at` ベースへの置換）の主たる正当化である。**（`.github/workflows/` には `auto-draft-pr.yml` のみが存在し、マージ戦略やブランチ削除を上書きするワークフローは無い。）

**置換前後のテスト件数（実測）**: Task 2実行前は11 test（既存の `test_task_id_conflict_detected` を含む）。Task 2で1件を3件に置換し13 testに増加。置換前実装での実行結果は10 passed / 3 failed（G1ゲート）。Task 3の実装置換後は13 passed（全件pass）。

## 3. 成果物

| 種別 | パス | 件数 |
|---|---|---:|
| validator実装 | `tools/validate_task.py` | `all_task_ids_in_history` 削除、`_origin_refs` / `task_identity_on_refs` / 新 `task_id_conflicts` 追加、`validate_l2` 冒頭差し替え |
| tests | `tests/test_validate_task.py` | 13 tests（旧11から+3/−1） |
| ドキュメント | `tasks/README.md` | 検証表更新 + 「task_id の重複検出の範囲」節を追記 |
| ドキュメント | `README.md` | L2説明を ref ベースの記述へ更新 |
| 自己契約 | `tasks/T-2026-08-05-l2-task-id-uniqueness-fix/{SPEC.md,spec.yaml,RESULT.md}` | 3 files |

## 4. 受入基準の充足

| acceptance | 結果 |
|---|---|
| `make task-validate` が exit 0 | PASS |
| `tests/test_validate_task.py` が全件 pass し、実測件数を RESULT へ記録した | PASS（13 passed。本RESULT §2に記録） |
| `refs/remotes/origin` 配下に同一 task を含む ref が複数あっても L2-1 が発火しない | PASS（Task 4実測。ユニットテスト `test_task_id_single_ref_is_not_conflict` / `test_task_id_same_created_at_across_refs_is_not_conflict` でも回帰検証済み） |
| `created_at` が異なる同名 task_id では L2-1 が発火する | PASS（`test_task_id_differing_created_at_is_conflict` で検証） |
| `all_task_ids_in_history` が削除され、参照が残っていない | PASS（`grep -rn` 出力なし） |
| README の L2 説明が ref ベースの記述へ更新された | PASS（`grep -n "履歴衝突"` は `no stale wording`） |

## 5. deviations（指示書どおりにしなかった箇所）

- 指示: Task 2 の `tests/test_validate_task.py` の import ブロックについて、SPEC.md本文のコメントは「既存の import 行に `task_identity_on_refs` を追加する」と指示していたが、直後に示されたコード例は `task_identity_on_refs` ではなく `Finding` を追加する内容だった。
- 実際: import 行を変更せず（`resolve_sigma_policy`, `task_id_conflicts`, `validate_l1` のまま）、テスト関数のみ置換した。
- 理由: (1) `task_identity_on_refs` はTask 3まで `tools/validate_task.py` に未実装のため、Task 2時点でimportすると `ImportError` でテスト収集自体が失敗し、SPECが明記する期待失敗理由（「旧 `task_id_conflicts` は引数3つで `existing` の意味も違うため」の `TypeError`）と食い違う。(2) `Finding` は新3テストのいずれからも参照されず、importすると `pyproject.toml` の `[tool.ruff.lint] select = ["E","F","W","I"]`（F401: 未使用importを検出）に抵触し、CLAUDE.mdが定めるruffフックで失敗する。実際に `ruff check tests/test_validate_task.py` は変更後 `All checks passed` で確認済み。
- 分類: SPEC の欠陥（ユーザー承認済み・2026-08-05 13:36 UTCの指示で「私のSPECの欠陥」と確認を得た）

他に指示書からの逸脱はなし。

## 6. 未解決・申し送り

- **既知の限界（fetch範囲外の検出不能）**: `task_identity_on_refs` は `refs/remotes/origin` 配下のみを走査するため、衝突しているブランチをfetchしていないホストでは重複を検出できない（偽陰性）。偽陽性より安全側であるため意図的に許容する設計であり、`tasks/README.md`「task_id の重複検出の範囲」節に明記した。
- **PR マージ後の実地検証が未実施**: 本repoはauto-mergeが設定済みのため、本PRのマージ自体がsquash/rebase経路での修正の実地検証になる。マージ後に別ホストで `make task-validate` を回し、exit 0であることを確認する作業がまだ残っている（本commit時点では未判明の情報のため、`meta.amendments` ではなくこの申し送りに記載。確認でき次第この節に追記する）。
- 全体テストの既存5件の失敗（`tests/test_engines.py` 1件、`tests/test_research_logger.py` 4件）は本task範囲外の既存不整合であり、本task実行前から存在し件数も不変。手を付けていない。
- Task 1 開始前から存在する未追跡ファイル（`experiments/transfer/_smoke_artifacts_ctrl/`, `_smoke_artifacts_inj/`, `_smoke_fullval/`、`tasks/T-2026-08-03-task-contract-bootstrap/` 配下の `SPEC copy.md` / `spec copy.yaml`）には本taskで一切触れていない。
- L2-8 は本 task では発火条件に到達せず未検証（起票時 counts と現在の runindex 実測が一致していたため、母集団差分検知の分岐を通過するテストケースには至っていない）。

## 7. 数値の出所

すべての数値は当該コマンドのstdout/stderrまたは正本ファイル（`runindex/*.csv`の実測行数、`git log`/`git diff`の実測出力）から取得した。未測定の項目はない。

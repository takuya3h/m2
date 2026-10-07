# audit — T-2026-10-07-pause-release-tool-digest-relocate

実行ホスト `philip`（`hostname` は `aolab`）。分岐 `feat/pause-release-tool-digest-relocate`。時刻は JST。

## A. 開始状態（G1）

### A1. 作業ツリーと位置

- 分岐: `feat/pause-release-tool-digest-relocate`（`make task-start` が作成）
- HEAD = `origin/phase0` = `c3ca48e3`。left/right は `0 0`
- `git status --porcelain`: 1 件。`?? tasks/T-2026-10-07-pause-release-tool-digest-relocate/`（取り込んだ契約）。ほかに開始前から在る未追跡は無い
- `make task-start` の直前の状態: 作業ツリーは 0 件。分岐は `feat/auto-merge-regen-pr-postmerge`。`.sync-pause` は無く、`.sync-pause.released`（0 バイト、前の契約の解除で移したもの）が在った

### A2. 試験（開始前）

`python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors tests` の結果は exit 1 で、`6 failed, 670 passed, 1 skipped, 20 warnings, 2 errors`。
`--continue-on-collection-errors` を付けないと、収集のエラー 2 件で全体が中断する。

失敗とエラーの名前の集合（8 件）:

```
ERROR tests/test_estimate_tier_cost.py
ERROR tests/test_stage1_dtower_convergence.py
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
```

`test_stage1_dtower_convergence.py` は `third_party/Relation-DETR/util/convergence.py` が無いため、収集で失敗する。

### A3. 目印

- `$M2DIR` = `/home/ubuntu/slocal2/m2`（`~/slocal2` が在るため。`m2-sync.sh:10`）。repo の最上位と一致する
- `.sync-pause`: 在る。`size=0`（旧い task_start.sh が `touch` で置いたもの）
- `.sync-pause.released`: 在る。`size=0`（前の契約で解除のために移したもの。触れていない）

### A4. 追跡済みの抽出物

- `git ls-tree -r --name-only HEAD docs/sessions/digest/` は **48 件**。作業ツリー上の実在も 48 件で、未追跡は 0 件

### A5. m2-sync.sh と keeper が目印をどう読むか

- `scripts/sync/m2-sync.sh:44` は `if [ -f "$M2DIR/.sync-pause" ]; then`、`:45` は記録を書いて `exit 0` する。**実在だけを見る。** 中身を読む処理（`cat`、`<`、`read`、`head`、`grep` で目印を開くもの）は 0 件だった
- 稼働中の `~/bin/m2-sync.sh` は `scripts/sync/m2-sync.sh` と同一（`diff -q`）
- `~/bin/keeper.sh`（52 行）は `.sync-pause` を参照しない。役割は、syncthing の死活監視と、m2-sync.sh の自己更新（`:45-46`）と実行（`:50`）
- `$M2DIR` の解決（`m2-sync.sh:10`、`:14`）:
  - `~/slocal2` が在れば `~/slocal2/m2`。無ければ `~/slocal/m2`
  - `~/slocal2` も `~/slocal` も無く、`~/local/m2` が在れば `~/local/m2`
- repo 全体で `.sync-pause` を参照するコード: `m2-sync.sh`（実在の検査）、`task_start.sh`（置く・消す）、`.gitignore:245`（`.sync-pause*`）、`tests/test_sync_pause_ignore.py`、`tools/check_spec.py:71`（契約の本文を走査するだけ）。**目印の中身を読むものは無い**
- §2 の起票者の事実（`m2-sync.sh:44`、`:10`、`:14`）と一致した

### A6. 版の実測

- `contract.conventions_rev`: `context/conventions.md` の最終 commit は `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6` で、記載と一致する
- `meta.created_from.runindex_commit`: `runindex/` の最終 commit は `63ae65da8c7d32df591f5e2ee4358286b72c726b` で、記載と一致する
- → 差し替えは無い。`meta.amendments` は空のまま

**G1: pass。** 開始状態を記録した。目印の中身を読む処理が無いことを実装で確かめた。

## B. 所有の記録（task_start.sh）

- 変更: `scripts/task_start.sh` の手順 8。`touch "${PAUSE_MARKER}"` を `printf 'task_id=%s\nbranch=%s\n' ... > "${PAUSE_MARKER}"` に替えた。実行前から在る目印の分岐（`created_pause=0`）と巻き戻し（`rollback`）は変えていない
- 中身の形: `task_id=<識別子>` と `branch=<分岐名>` の 2 行（`key=value`）
- 試験 `tests/test_task_start_pause_owner.py`（8 件）。隔離した場（bare な origin と複製）で実物のスクリプトを走らせ、`make task-notion` を Makefile ごと差し替えた
  - 新たに置く場合 → 中身が `task_id=T-2026-10-07-sample-owner\nbranch=feat/sample-owner\n` になる
  - 実行前から在る場合（任意のバイト列）→ sha256 が前後で一致し、「実行前から存在するため触れません」と表示される
  - 取り込みに失敗した場合 → exit 4。自分が置いた目印は消え、分岐も消えて phase0 に戻る
  - 取り込みに失敗し、既存の目印がある場合 → exit 4。既存の目印の sha256 は不変
  - 終了コード → 識別子が空なら 2、形式が不正なら 2、dirty なら 3、分岐の重複なら 3。どれでも目印は作られない
- **変更前の版との比較**: `git show HEAD:scripts/task_start.sh` を同じ試験にかけた。`test_new_marker_records_owner` の 1 件だけが落ち、残る 7 件（終了コード・巻き戻し・既存の目印）は通った → 既存の振る舞いは同じで、試験は所有の記録が無いことを検出する

## C. 外す道具（G2）

- 道具は `scripts/task_release.py`（標準ライブラリだけ）。入口は `make task-release TASK=<id> END=complete|abort [REASON="..."]`（`Makefile` の `task-start` の直後）
- 状態と終了コード: `RELEASED` 0 / `USAGE` 2 / `ABSENT` 10 / `OWNER_MISMATCH` 20 / `OWNER_UNREADABLE` 21 / `POSITION_MISMATCH` 22 / `PREREQ_MISSING` 30 / `PREREQ_UNKNOWN` 31 / `RELEASE_FAILED` 40。一行の状態表示は `task-release: <状態> task=<id> [end=..] [method=..] — <詳細>`
- 判定の順: 使い方 → 位置（repo の最上位と `$M2DIR` の realpath）→ 実在 → 所有者 → 完了の前提 5 つ（中止では見ない）→ 削除、拒まれたら `.sync-pause.released.<task_id>` へ移す → 目印が存在しないことを `lexists` で確かめる
- 前提の照会: 分岐は `git branch --show-current`、未 commit は `git status --porcelain --untracked-files=no`、遠隔は `git ls-remote --heads origin`（参照を書き換えない）、PR は `gh pr list --head <分岐> --base phase0 --state all`、報告は `git ls-tree HEAD -- tasks/<id>/...`。git は `GIT_OPTIONAL_LOCKS=0` で走らせ、index を書き直さない
- 試験 `tests/test_task_release.py`（39 件）は全件 pass

| 判定 | 場 | 結果 |
|---|---|---|
| c | 前提をすべて満たす（PR は開いている／統合済み） | exit 0 `RELEASED method=removed`。外す前に目印が在ることを確かめ、外した後は `lexists` が偽 |
| d | 前提 1〜5 を一つずつ欠けさせる（PR は無い場合と閉じた場合の二通り）、遠隔の分岐が無い | 6 通りとも exit 30 `PREREQ_MISSING`。名指しされた前提の集合はそれぞれ `{1 分岐}` `{2 未 commit}` `{3 遠隔}` `{4 PR}` `{4 PR}` `{5 報告}`。目印は残る |
| e | `gh` が失敗する、origin の URL が壊れている | exit 31 `PREREQ_UNKNOWN` で「確かめられない」と表示し、「欠けている」は出ない。欠けと失敗が重なる場合は 30 で、「確かめられない: 4 PR」を併記する |
| f | 中止で理由なし／空／スペースだけ | exit 2 `USAGE`。目印は残る |
| f | 中止で理由ありで、PR が無い | exit 0 `RELEASED end=abort reason="..."`。同じ場を完了で回すと `PREREQ_MISSING` |
| g | 所有者が別の契約・中身が空・形式が違う（完了と中止の両方） | 20 か 21。目印の sha256 は不変 |
| h | `$M2DIR` を別の場所にする | exit 22 `POSITION_MISMATCH`。一致する場では外れる（c） |
| i | 二度目の実行 | 一度目は 0 `RELEASED`、二度目は 10 `ABSENT` |
| j | `os.remove` が拒まれる | `RELEASED method=moved:.sync-pause.released.<id>`。目印は存在せず、`git status --porcelain --untracked-files=all` は空 |
| j | 削除も移動も拒まれる | 40 `RELEASE_FAILED`。目印は残る |
| k | 外す場と外さない場の前後 | HEAD、分岐、index（`ls-files -s` の要約値）、stash、遠隔以外の refs、status が一致する。意図的に分岐を一つ足すと差が出る |
| R12 | `TASK_RELEASE_M2DIR` が未設定 | `~/slocal2`、`~/slocal`、`~/local/m2`、無し、とその組み合わせの 6 通りで、`m2-sync.sh` の M2DIR の 2 行を bash で評価した値と一致 |

**変異による確認**（scratchpad で道具を書き換え、同じ試験を走らせた）

| 壊し方 | 落ちた試験 |
|---|---|
| 所有者の検査を外す | 4 件 |
| 完了の前提を常に満たす | 11 件 |
| 位置の検査を外す | 1 件 |
| 中止の理由の必須を外す | 3 件 |
| 照会の失敗を欠けとして扱う | 3 件 |

**G2: pass。** 陽性の場合で外れ、陰性の場合のすべてで外れない。判定を壊すと、それぞれ試験が落ちる。

## D. 抽出物の置き場（G3）

- 新しい置き場は `~/claude-sync/session-digest/<ホスト名>/`。ホスト名は `SERVERNAME` → repo の `.servername` → `hostname` の順に決める（`m2-sync.sh` と同じ 3 段）。このホストでは `/home/ubuntu/claude-sync/session-digest/philip`（`--show-out-dir` で表示。ディレクトリは作られなかった）
- 共有フォルダが無いホスト: 出力先を `None` に解決し、何も書かずに exit 0 で終える。終了フックはこれまでどおり失敗を無視する
- 走査: 旧い置き場（`--root` の `docs/sessions/digest/`）に同じ名前があれば、抽出済みとして飛ばす。内容は比べない
- 伏せ字: `render` の中で従来どおり適用する（試験で `API_TOKEN=<redacted>` を確認した）
- `.gitignore` に `docs/sessions/digest/` を足した
  - `git check-ignore docs/sessions/digest/2099-01-01-new-digest.md` は exit 0（無視される）
  - 対照の `docs/sessions/2099-01-01-elsewhere.md` は exit 1（汚れに数えられる）
  - 追跡済みは 48 件のままで、`git status --porcelain docs/sessions` は 0 件
- 終了フック `.claude/hooks/session_end.sh` は変えていない（`--root` を渡すだけで足りる）
- **このホストでの実測**（書き出し先は scratchpad。実物の共有フォルダには書いていない）: 第二の実装系の記録は 2 件
  - 1 件は中身が無い（従来どおり書かない）
  - 1 件は旧い置き場に在り、追跡済み → **作り直さなかった**
  - 書き出しは 0 件。対照として旧い置き場が無い root で走らせると 1 件書き出された
- 試験 `tests/test_session_digest.py` は 34 件で全件 pass。既存の走査の試験 2 件は、home に共有フォルダを作る形に直した。追加は 8 件
- 変異: 旧い置き場を見ないようにすると 2 件、共有フォルダが無くても書くようにすると 2 件落ちた

**G3: pass。**

## E. 文書

- `tasks/README.md`: 「契約の受け取り」の解除の節（所有の記録、`make task-release`、前提、状態表示、手で置いた目印の扱い）と、「対話の記録」の節（新しい置き場、検索、撤回の日付と理由、`git add` の指示を削除、B-30 の当てはめ）
- `docs/sessions/README.md`: 「中身」「抽出物の扱い」「検索」。2026-08-09 の方針を 2026-10-07 に撤回したことと、その理由
- `OPERATION.md`: 「自動化を一時的に止める」に、所有の記録と道具を足した。人が手で置いた目印は道具が外さないことも書いた
- `context/env-facts.md`: 「keeper と m2-sync」に、目印の中身と抽出物の置き場を足した
- **B-30 の当てはめ**: B-30 は、未追跡のファイルと同じパスが統合で取り込まれる木に在るときに起きる（`OPERATION.md` の「未追跡ファイルが merge を止めることがある」）。新しい抽出物は repo の外に書かれ、旧い置き場は無視されるため、phase0 に抽出物の新しいパスは入らない。git は無視された未追跡ファイルを統合の妨げとして扱わない。`m2-sync.sh` の阻害の判定も `--exclude-standard` で無視されたファイルを数えない → 抽出物には当てはまらなくなった、と本文に書いた
- `make docs-check` は exit 2（1 件: `docs/proposal-gate.md:41`）。`make agent-check` も exit 2（1 件: `docs/experiment_settings.md:155`）。どちらのファイルも本契約で変えていない。後者は前の契約で phase0 の上の既存の失敗だと確かめたもの

## F. 検証

- `make task-validate` exit 0。`make forbidden-check` は pass（changed 15、違反 0）。`make spec-check TASK=...` は pass、exit 0
- 試験全体: `6 failed, 725 passed, 1 skipped, 2 errors`。開始前は 670 passed で、増えた 55 件は追加した試験（8 + 39 + 8）。**失敗の名前の集合は開始前と同一**（8 件、`diff` で差なし）
- `context/auto/*` と `tasks/inbox.md` は再生成しておらず、`*-check` も回していない（禁止 6）

### F6. 実物の目印に対する陰性対照（解除の前）

```
$ stat -c '%n size=%s' .sync-pause
.sync-pause size=0
$ make task-release TASK=T-2026-10-07-pause-release-tool-digest-relocate END=complete
task-release: OWNER_UNREADABLE task=T-2026-10-07-pause-release-tool-digest-relocate — 目印の所有者を読めない（人が手で置いた目印か、旧い task_start.sh が置いた目印）。外さない
make: *** [Makefile:221: task-release] Error 21
（make の exit 2）
$ .venv/bin/python scripts/task_release.py T-2026-10-07-pause-release-tool-digest-relocate --end complete
（同じ状態表示、exit 21）
$ stat -c '%n size=%s' .sync-pause
.sync-pause size=0
```

解除（手順書の方法）は、報告と送出の後に行う。解除の後に git の操作をしないため、その結果は版管理に残らない（RESULT の §送出を参照）。

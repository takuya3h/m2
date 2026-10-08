# audit — T-2026-10-08-doc-checks-clean-and-defect-log

実行ホスト `philip`（`.servername`。`hostname` は `aolab`）。分岐 `feat/doc-checks-clean-and-defect-log`。時刻は JST（道具の出力は UTC のため換算した）。

## A. 開始状態（G1）

### A1. 始める段（R6）

利用者が送った命令は `/task T-2026-10-08-doc-checks-clean-and-defect-log` の一行だけ（一度目は利用者がモデルを切り替えるために中断し、同じ一行を送り直した）。

始める段の読み取りの命令の出力（終了コード 1 は、末尾の `ls` と `cat .sync-pause` が対象無しで返したもの）:

```
feat/skill-task-start-and-release
ls: cannot access 'tasks/T-2026-10-08-doc-checks-clean-and-defect-log': No such file or directory
cat: .sync-pause: No such file or directory
```

- 現在の分岐は `feat/skill-task-start-and-release`（`feat/doc-checks-clean-and-defect-log` ではない）→ 再開ではない
- `git branch --list` と `ls-remote` は空、`tasks/<task_id>` の履歴も空 → 分岐の重複ではない
- 分岐名は空でない → detached ではない
- `status --porcelain` は 0 行 → 汚れではない
- **判定: 清浄**。`source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=...` を一つの命令で実行した

```
[task-start] git fetch origin
[task-start] 分岐を作成: feat/doc-checks-clean-and-defect-log（起点 origin/phase0）
[task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-10-08-doc-checks-clean-and-defect-log END=complete）
[task-start] 契約を取り込みます: T-2026-10-08-doc-checks-clean-and-defect-log
OK   T-2026-10-08-doc-checks-clean-and-defect-log
1 task(s), 0 failed
取り込みました: tasks/T-2026-10-08-doc-checks-clean-and-defect-log
[task-start] 完了。分岐 feat/doc-checks-clean-and-defect-log で契約 T-2026-10-08-doc-checks-clean-and-defect-log の作業を開始できます
```

- 目印の表示は **「作成」**。`.sync-pause` は 97 バイト、作成 2026-10-08 18:54:54 JST。中身:

```
task_id=T-2026-10-08-doc-checks-clean-and-defect-log
branch=feat/doc-checks-clean-and-defect-log
```

- 手順書どおりに働かなかった箇所: 無し
- `make task-validate`: `OK`、`1 task(s), 0 failed`。`make task-preflight`: `6 PASS / 0 WARN / 8 SKIP / 0 FAIL`
  - SKIP: P2 cuda_ext_loaded、P3 deterministic_flags、P4 prereg_committed、P5 frozen_source_hash、P11 gpu_free、P12 refs_resolved、P13 symmetry_table_complete、P14 proposal_card_checked
- `grep -c sync-pause ~/bin/m2-sync.sh` = 2（稼働中の版は抑止に対応）

### A2. 作業ツリーと位置

- HEAD = `origin/phase0` = `22b1cd72`（`git rev-list --left-right --count HEAD...origin/phase0` = `0 0`）
- `status --porcelain`: 取り込んだ契約の 2 件（`SPEC.md`、`spec.yaml`）だけ
- `contract.conventions_rev` 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`、`created_from.runindex_commit` 実測 `63ae65da8c7d32df591f5e2ee4358286b72c726b`。**どちらも契約と一致**し、`meta.amendments` は変えていない

### A3. 手元の作業ツリー（変更前）

`make agent-check`（make の終了コード 2）:

```
{"errors": [], "pager_violations": [], "status": "fail", "targets": 145, "violations": [{"command": "source .venv-relation-detr/bin/activate   # 検出系", "line": 155, "next_command": "source .venv/bin/activate                 # 解析・工程系", "next_line": 156, "path": "docs/experiment_settings.md"}]}
```

`make docs-check`（make の終了コード 2）:

```
[docs-check] 1 件の食い違い
[docs-check] 対象 43 文書 / Makefile のターゲット 35 件
  docs/proposal-gate.md:41 実在しない経路 docs/proposals/YYYY-MM-DD-slug.md
```

### A4. 新しく取得した作業ツリー（変更前）

二つの取得元で測った。どちらも無視されている手元のファイルを持たない（`.claude/settings.local.json` と `.claude/hooks/*.log` が無いことを `ls` で確かめた）。検査器は repo の `.venv/bin/python` で直に呼んだ。

**(1) GitHub の origin から `git clone --branch phase0`（HEAD `22b1cd72`）**。以降「新しい作業ツリー」はこちらを指す。

agent-check（終了コード 1）: A3 と同じ 1 件（`docs/experiment_settings.md:155` → `:156`）。

docs-check（終了コード 1）:

```
[docs-check] 7 件の食い違い
[docs-check] 対象 43 文書 / Makefile のターゲット 35 件
  CLAUDE.md:24 実在しない経路 .claude/settings.local.json
  AGENTS.md:24 実在しない経路 .claude/settings.local.json
  docs/host_autosync_onboarding.md:115 実在しない経路 .claude/hooks/auto_notion_sync.log
  docs/host_autosync_onboarding.md:132 実在しない経路 .claude/hooks/auto_notion_sync.log
  docs/host_autosync_onboarding.md:133 実在しない経路 .claude/hooks/auto_notion_sync.log
  docs/host_autosync_onboarding.md:156 実在しない経路 .claude/hooks/auto_notion_sync.log
  docs/proposal-gate.md:41 実在しない経路 docs/proposals/YYYY-MM-DD-slug.md
```

**(2) 手元の repo の経路から `git clone`（HEAD `22b1cd72`）**。agent-check は同じ 1 件。docs-check は 8 件で、(1) の 7 件に次の 1 件が加わる:

```
  OPERATION.md:84 実在しない経路 docs/plan-rewrite-2026-06
```

原因: `docs/plan-rewrite-2026-06` は経路ではなく分岐名で、検査器は `git branch -r` の一覧で分岐名を除外する。(2) の複製の遠隔は手元の repo であり、手元にこの分岐が無いため一覧に現れない。GitHub の origin には在る（`ls-remote` で `753532b2`）。**無視されたファイルではなく遠隔追跡の参照に依存する差であり、本契約の範囲外として扱った**（RESULT §7）。

### A5. 試験（変更前）

`PYTHONPATH=src python -m pytest -q -p no:cacheprovider --continue-on-collection-errors tests`（収集のエラー 2 件で中断するため付けた。前契約と同じ扱い）

```
6 failed, 728 passed, 1 skipped, 20 warnings, 2 errors in 51.62s
```

失敗の名前（8 件）:

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

## B. agent-check

`docs/experiment_settings.md` §1.10 の二行は「系ごとにどちらか一方」の選択肢であり、続けて実行する手順ではない。しかし字下げの二行が並ぶため、読み手にも検査器にも連続した命令に見える。文書の側を、選択肢ごとに見出しの文で分けた二つの字下げの塊に直し、続く操作と同じ命令の中で読み込む形（`source <仮想環境>/bin/activate && <操作>`）を一文で添えた。二つの読み込みの命令そのものは消していない。検査器は変えていない。

## C. docs-check

- R2: `docs/proposal-gate.md:41` の雛形の経路を `docs/proposals/<YYYY-MM-DD>-<slug>.md` に直した。既存の規則（`VAR_MARKS` の `<` を含む記述は実在を約束しない）で対象外になる。外す印は使っていない
- R3: `tools/check_docs.py` に `is_git_ignored`（`git check-ignore -q -- <経路>`）を足し、無視される経路は在っても無くても対象外にした。`git check-ignore` は追跡下のファイルを無視されたことにしないため、版管理に在るはずの経路の検出は変わらない
- 試験 3 件を `tests/test_check_docs.py` に足した（在る場合と無い場合で同じ結果／無視される経路と並んだ追跡下の経路の欠落は検出／`is_git_ignored` を実 repo で確かめる：無視されるものは真、追跡下に強制で足した `*.log` は偽、無関係な経路は偽）

### C1. 変更後の手元

```
{"errors": [], "pager_violations": [], "status": "pass", "targets": 145, "violations": []}
[docs-check] 対象 43 文書 / Makefile のターゲット 35 件
[docs-check] 食い違いなし
```

### C2. 新しい作業ツリー（GitHub の複製）へ変更した 3 ファイルを写して測った

| 場 | docs-check | agent-check |
|---|---|---|
| B1 変更後・手元のファイル無し | 食い違いなし（rc 0） | pass（rc 0） |
| D1 変更後・手元のファイル有り（`touch .claude/settings.local.json .claude/hooks/auto_notion_sync.log`。`status --ignored` で `!!` を確認） | 食い違いなし（rc 0） | pass（rc 0） |
| C1 陽性対照: `docs/proposal-gate.md` に `` `tools/no_such_tool.py` `` を、`docs/experiment_settings.md` に字下げの `source .venv/bin/activate` と `make docs-check` の二行を足した写し | `docs/proposal-gate.md:92 実在しない経路 tools/no_such_tool.py`（rc 1） | fail、`docs/experiment_settings.md` line 372 → 373（rc 1） |
| D2 追跡下の `scripts/sync/m2-sync.sh` を退けた写し・手元のファイル有り | `.claude/skills/task/SKILL.md:163 実在しない経路 scripts/sync/m2-sync.sh`（rc 1） | pass |
| D3 同上・手元のファイル無し | D2 と同じ 1 件（rc 1） | pass |

C1 の後は 2 ファイルを `git checkout` で戻して変更後の版を写し直し、D2・D3 の後は `m2-sync.sh` を戻した。最終の `git status --porcelain` は変更した 3 ファイルだけ。手元のファイルは複製の中にだけ作り、ホストの手元のファイルには触れていない。

手元の repo の経路から複製した場（A4 (2)）に変更を写すと、docs-check は `OPERATION.md:84 実在しない経路 docs/plan-rewrite-2026-06` の 1 件を残した（分岐名の照合が遠隔追跡の参照に依存するため）。

## D. 欠陥の一覧

`docs/issuer-defects.md` の「禁止と要求が両立しなかった」の末尾に一件足した。変更前の一覧に `T-2026-10-07-pause-release-tool-digest-relocate` の文字列は 0 件だった（`grep -n` が空）。

## E. 検証

- 試験（変更後）: `6 failed, 731 passed, 1 skipped, 20 warnings, 2 errors in 49.88s`。失敗の名前は A5 の 8 件と `diff` で同一。通過が 3 件増えたのは足した試験の分
- `ruff check tools/check_docs.py tests/test_check_docs.py`: `All checks passed!`
- `make task-validate`: `1 task(s), 0 failed`
- `make forbidden-check`: `"status": "pass"`、`"violations": []`、changed 7 / checked 7
- `make spec-check TASK=...`: `"status": "pass"`、`"targets": 1`
- `make agent-check`: pass。`make docs-check`: 食い違いなし

### E1. R7（philip の `~/claude-sync/sync-alerts.log`）

記録は全台の共有で、philip の行は `[philip]` で絞った。一時停止の行は 66 件、日付の内訳は 09-20 4、09-21 5、09-22 18、10-07 28、10-08 11。最後の一時停止の行と、その後の行（ログの時刻は UTC。JST に換算して併記）:

```
2026-10-08 05:18:55 [philip] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）   ← 14:18:55 JST
2026-10-08 06:18:58 [philip] auto-merge: feat/skill-task-start-and-release <- origin/phase0 (3 commits)                   ← 15:18:58 JST
2026-10-08 06:19:00 [philip] auto-push: feat/skill-task-start-and-release (3 commits)                                     ← 15:19:00 JST
```

一時停止は 14:18 JST で途切れ、次のループで統合と push が再開している。**一時停止が続いている記録は無い。** 本契約の目印（18:54 JST 作成）による一時停止の行は、確認の時点（19:02 JST）ではまだ出ていない（次のループ待ち）。

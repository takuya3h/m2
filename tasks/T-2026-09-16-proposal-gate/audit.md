# audit — T-2026-09-16-proposal-gate

命令と出力の全文。`RESULT.md` はここを行番号で指す。
時刻は JST。対話シェルは zsh。履歴を読む操作は `git --no-pager` を使った。

## 0. 取り込みと事前検査

### 0.1 契約の取り込み（task-start）

    $ cd /home/ubuntu/slocal/m2 && source .venv/bin/activate && source scripts/load_env.sh \
        && make task-start TASK=T-2026-09-16-proposal-gate
    [load_env] .env をロード（WANDB_API_KEY=set / NOTION_API_KEY=set）
    [task-start] git fetch origin
    [task-start] 分岐を作成: feat/proposal-gate（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら rm -f .sync-pause）
    [task-start] 契約を取り込みます: T-2026-09-16-proposal-gate
    OK   T-2026-09-16-proposal-gate
    1 task(s), 0 failed
    取り込みました: tasks/T-2026-09-16-proposal-gate

### 0.2 自動同期の抑止が効くことの確認

    $ grep -c sync-pause ~/bin/m2-sync.sh
    2
    $ ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Sep 16 14:25 .sync-pause

稼働中の版は抑止に対応している（0 なら未対応）。目印は task-start が置いた。

### 0.3 L1 + L2（取り込み直後）

    $ make task-validate TASK=T-2026-09-16-proposal-gate
    OK   T-2026-09-16-proposal-gate
    1 task(s), 0 failed

WARN は出ていない。`contract.conventions_rev` が差し替え前
（`REPLACE-BY-EXECUTOR-with-measured-rev`）のため、L2-6 の照合は
`git diff <rev>..HEAD` が解決に失敗して沈黙する。差し替え後に測り直す（6.2）。

### 0.4 L3 プリフライト

    $ make task-preflight TASK=T-2026-09-16-proposal-gate
    P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal/m2/.venv sys.prefix=/home/ubuntu/slocal/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS docs/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
    P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
    P12 refs_resolved          SKIP 解決前提の参照は無い

    RESULT: 6 PASS / 0 WARN / 6 SKIP / 0 FAIL

SKIP 6 件（P2 P3 P4 P5 P11 P12）。SKIP は合格ではなく「実行されなかった」。
本契約は GPU を使わず kind=impl で解決前提の参照も持たないため、いずれも対象外。

## 1. Task A — 開始状態の記録

### A-1 作業ツリー

    $ git status --short
    ?? .sync-pause.released
    ?? docs/sessions/digest/2026-08-29-23fa444b-1ed7-4ec8-9280-bf8158c61e16.md

開始前から在る未追跡が 2 件あった。**消さず、移動で退避した。**

    $ git stash push -u -m "pre-T-2026-09-16-proposal-gate: released pause marker + session digest"
    Saved working directory and index state On feat/notion-retire-scripts-and-speccheck: ...
    $ git stash list | head -1
    stash@{0}: On feat/notion-retire-scripts-and-speccheck: pre-T-2026-09-16-proposal-gate: ...

退避先: `stash@{0}`（`git stash pop` で戻る）。件数: 2。
内訳: `.sync-pause.released`（0 バイト、前契約の解除済み目印）、
`docs/sessions/digest/2026-08-29-23fa444b-....md`（277 行、前セッションの機械抽出記録）。

退避後の作業ツリー:

    $ git status --short
    ?? tasks/T-2026-09-16-proposal-gate/

残る未追跡は task-start が置いた本契約そのものだけ。清浄と判定した。

### A-2 conventions.md のアンカー

抽出規則は実装から取った（`tools/validate_task.py:34`）。

    _ANCHOR_RE = re.compile(r'<a id="([a-z0-9_]+)"></a>')

    $ grep -oP '<a id="\K[a-z0-9_]+(?="></a>)' context/conventions.md | nl
         1	split
         2	eval_recipe
         3	frozen_source
         4	sigma
         5	prohibitions
         6	env_p0
         7	naming
         8	issuer_cautions
    $ grep -cP '<a id="[a-z0-9_]+"></a>' context/conventions.md
    8

**変更前のアンカー数: 8。** Task B の後に 9 になることを確かめる（A-2 の対）。

### A-3 spec-check の規則数（実装を読んで数えた）

数え方: `tools/check_spec.py` の `RULES` タプルの要素数。
検査器はこの長さを `rules_checked` として出力する（`tools/check_spec.py:498`）ため、
タプルの要素数が規則数の定義である。

    $ sed -n '447,456p' tools/check_spec.py
    RULES = (
        rule_truncation_in_measurement,
        rule_unquoted_glob,
        rule_separated_source,
        rule_forbidden_vs_output,
        rule_host_mismatch,
        rule_integration_prohibited_without_pause,
        rule_gate_requires_report_before_end,
        rule_reverify_contradiction,
    )

**変更前の規則数: 8。** P9 の出力「規則 8 件を検査し該当なし」と一致する（独立な二経路）。

注: アンカー数も 8 で同値だが無関係である。両者を取り違えない。

### A-4 変更前の試験の失敗件数

比較を成立させるため、変更後もこの同じ命令で測る。

    $ source .venv/bin/activate && pytest tests/ -q -p no:cacheprovider
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics - Ass...
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name - AssertionEr...
    FAILED tests/test_research_logger.py::test_log_run_idempotent - AssertionErro...
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    6 failed, 509 passed, 22 warnings in 30.85s
    exit=1

**変更前: 6 failed / 509 passed。** 6 件は本契約の着手前から落ちている。
完了判定 f は「変更前に失敗していた試験の件数が増えていない」であり、
6 件を直すことは求めていない（本契約の範囲外）。

### A-5 conventions_rev と runindex_commit の実測

測り方は実装から取った。L2-6 は次を実行する（`tools/validate_task.py:443`）。

    git diff --name-only {revision}..HEAD -- context/conventions.md

すなわち `conventions_rev` は git の版（commit）であり、
`context/conventions.md` を最後に変えた commit を書くのが実装の前提である。

    $ git --no-pager log -1 --format='%h %ad %s' --date=iso -- context/conventions.md
    a8c07e81 2026-08-25 15:30:37 +0000 feat(context): move issuer references into version control and inject the cautions
    $ git --no-pager log -1 --format='%h %ad %s' --date=iso -- runindex/
    96eb3a1c 2026-08-30 10:26:08 +0000 exp(pd-b2-b4): build the detector env on lecun and close the remaining direction of G0

測り方の検証（空振りでないことの確認）: 直前の三契約が記録している値と照合した。

    tasks/T-2026-08-31-notion-repo-followup-and-retire  runindex_commit 96eb3a1c / conventions_rev a8c07e81
    tasks/T-2026-09-01-notion-retire-scripts-and-speccheck  runindex_commit 96eb3a1c / conventions_rev a8c07e81
    tasks/T-2026-08-29-lecun-detector-env-pd  runindex_commit 09fdefb3 / conventions_rev a8c07e81

同じ測り方で同じ値が出た。別々の実行者が別の日に書いた値と一致するため、
測り方はこの repo の慣行と同じである。

差し替えた値:

    meta.created_from.runindex_commit: REPLACE-BY-EXECUTOR-with-measured-runindex-commit → 96eb3a1c
    contract.conventions_rev:          REPLACE-BY-EXECUTOR-with-measured-rev            → a8c07e81

`meta.created_from.counts` は差し替えの対象に含まれていない（Task A-5 が挙げるのは
二つだけ）ため触っていない。本契約は `inputs.denominator` を持たないため
L2-8（母集団の移動）は原理的に沈黙する（`tools/validate_task.py:459`）。

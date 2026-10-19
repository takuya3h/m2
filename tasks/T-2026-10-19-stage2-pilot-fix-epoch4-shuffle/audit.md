# audit — T-2026-10-19-stage2-pilot-fix-epoch4-shuffle

命令と出力の記録。時刻は JST（必要なところは UTC を併記）。**非公式の測定**（SPEC §0）。
以下、前回の置き場 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/` を **OLD**、
本契約の置き場 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/` を **FIX** と書く（どちらも版管理と同期の外）。

## 0. 始める（2026-10-19 16:55 JST）

### 0-1 状態の読み取り（task-start の前）

    $ git branch --show-current → feat/stage2-pilot-folda（前回の契約の分岐。phase0 の 5a8baa79 が入った状態）
    $ git status --porcelain --untracked-files=all → （空）
    $ git branch --list feat/stage2-pilot-fix-epoch4-shuffle → （空）／ ls-remote → （空）／ log --all -- tasks/<id> → （空）
    $ cat .sync-pause → No such file or directory

再開・分岐の重複・detached HEAD・汚れのいずれにも当たらない（清浄）。

### 0-2 task-start

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
    [task-start] 分岐を作成: feat/stage2-pilot-fix-epoch4-shuffle（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら make task-release TASK=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle END=complete）
    OK   T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
    [task-start] 完了。分岐 feat/stage2-pilot-fix-epoch4-shuffle で契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle の作業を開始できます
    $ cat .sync-pause → task_id=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle / branch=feat/stage2-pilot-fix-epoch4-shuffle

### 0-3 検証（L1 + L2）

    $ make task-validate TASK=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle → OK、1 task(s), 0 failed、rc=0（WARN なし）

### 0-4 プリフライト（L3）

    $ make task-preflight → RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL、rc=0
    PASS: P1 venv_active、P6 decisions_answered（空）、P7 destination_writable、P8 contract_valid、P9 spec_lint（9 規則で該当なし）、P10 preflight_names_known
    SKIP: P2 cuda_ext_loaded・P3 deterministic_flags・P11 gpu_free（plan.env.preflight に記載なし）、P4 prereg_committed・P5 frozen_source_hash・
          P13 symmetry_table_complete・P14 proposal_card_checked（kind=analysis は対象外）、P12 refs_resolved（解決前提の参照は無い）

### 0-5 参照の解決

`inputs.denominator`・`inputs.frozen_source`・`inputs.sigma_policy` は無い。`contract.inject_verbatim` の 7 節（prohibitions、issuer_cautions、
env_p0、folds、split、eval_recipe、det_groups）は `context/conventions.md` から原文で読んだ（RESULT.md §1 に節の名前と出所、本文はファイルの原文）。

## A. 開始状態

### A-1 分岐と起点（Task A-1、16:56 JST）

    $ git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0 → 5a8baa790fa31ced4c8b891f7ee5ed5906c9d775（3 つとも同じ）
    $ git ls-tree --name-only origin/phase0 scripts/stage2pilot/ | wc -l → 28（aggregate.py、dp_train.py、run_pd.sh、test_audit.py ほか。前回の道具が在る）

分岐 `feat/stage2-pilot-fix-epoch4-shuffle`（`feat/` で始まる）。起点 `origin/phase0` = `5a8baa79`（PR #235 と #236 の統合後）。

### A-2 未追跡（Task A-2）

開始前の未追跡は 0 件（0-1）。退避は行わない。task-start が取り込んだ `SPEC.md` と `spec.yaml` は本契約のもの。

### A-3 compute プロセス（Task A-3、16:57 JST）

道具: 前回の `experiments/analysis/stage2_pilot_folda/tools/proc_enum.py`（読んで実行するだけ。`/proc/PID/exe` の解決と引数の要素の完全一致）。

    $ .venv/bin/python experiments/analysis/stage2_pilot_folda/tools/proc_enum.py --summary
        9 /usr/bin/dash ／ 9 None ／ 8 vscode-server の node ／ 7 /usr/bin/bash ／ 7 /usr/bin/zsh ／ 6 nvm の node ／ 3 zmx ／ 3 /usr/bin/sleep
        2 codex ／ 2 claude 2.1.303 ／ 2 syncthing ／ 1 claude 2.1.301 ／ 1 copilot-runtime ／ 1 code-110a… ／ 1 code-6d62… ／ 1 git ／ 1 head ／ 1 ssh
    --- python 系（exe の basename が python で始まる）→ 0 件
    $ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv → （見出しだけ。0 件）
    $ nvidia-smi --query-gpu=... → 0, RTX A6000, 16 MiB / 49140 MiB, 0 % ／ 1, RTX A6000, 16 MiB / 49140 MiB, 0 %
    exe 不明の 9 件: 1 sshd listener（uid 0）、1899448 sshd [priv]（uid 0）、1899459 sshd ubuntu@notty、ssh-agent -s × 6

**本契約以外の compute プロセスは 0 件。**

対照（完了判定 a の四列目）:

    陽性: bash -c 'sleep 40; true' zzz_s2fix_marker &（exe=/usr/bin/bash）
      $ proc_enum.py --exe /usr/bin/bash --argv zzz_s2fix_marker → 2463812 / count=1
      $ proc_enum.py --exe /usr/bin/zsh  --argv zzz_s2fix_marker → count=0
    陰性: $ proc_enum.py --exe /no/such/exe_zzz → count=0

### A-4 記憶領域（Task A-4）

    $ df -B1 /home/ubuntu/slocal2/m2 → /dev/sdc1 7937302376448 total, 5855826051072 used, 1681381457920 avail（78%）
    $ free -b → Mem total 100259065856、available 87208300544。nproc 32

見積もり（上限側）: 入れ替えた信号 8 本（OLD の元の信号の大きさと同じ。P0・D0・D0-RT・D0-INST-UQ の train と val）1 GB 未満、
PD の run 12 本の学習対象の重み（`--save-trainable-only`）と予測 1 GB 未満、DP の run 26 本の界面の重み 0.1 GB 未満。
計 3 GB 未満 ≪ 空き 1,681 GB。**足りる。**

### A-5 試験（Task A-5、開始時）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    6 failed, 883 passed, 22 warnings in 21.56s

失敗の名前の集合（6 件）は前回の契約の開始時・終了時と同じ。

### A-6 起票時の値（Task A-6）

| 項目 | 起票時 | 実測（前回と同じ読み: `git log -1 -- <経路>`） | 差し替え |
|---|---|---|---|
| `conventions_rev` | 4d42edb9 | **b12eda6cf0f53f4f0d09e5b6c53bb3afde9831ac** | **した**（`meta.amendments` の 1 件目） |
| `runindex_commit` | 31af81e7 | **63ae65da8c7d32df591f5e2ee4358286b72c726b** | **した**（同じ 1 件目） |
| index / experiments / verdicts（行数 − 1） | 1961 / 750 / 1506 | 1961 / 750 / 1506 | 不要 |

    $ git merge-base --is-ancestor 63ae65da 31af81e7 → 真 ／ git log 63ae65da..31af81e7 -- runindex/ | wc -l → 0
    $ git merge-base --is-ancestor b12eda6c 4d42edb9 → 真 ／ git log b12eda6c..4d42edb9 -- context/conventions.md | wc -l → 0
    $ git diff --stat 63ae65da HEAD -- runindex/ → （空）／ git diff --stat b12eda6c HEAD -- context/conventions.md → （空）

起票時の値はどちらも「その時点の phase0 の先頭」で、内容は最新 commit と同一。読みが二つ（最新の変更 commit か、内容が同じ任意の commit か）あり、
前回の契約は前者で測って差し替えたため、同じ読みに揃えた。内容が同一なので実行への影響は無い。差し替えた後も `make task-validate` は OK（rc=0）。

### A-7 抑止の目印（Task A-7）

0-2 のとおり、task-start の表示は「`.sync-pause を作成`」。**この契約の task-start が作成した**（中身は所有の記録 2 行）。

### 関門 G1: **pass**

分岐 `feat/` で起点 `origin/phase0`（5a8baa79）、phase0 に前回の道具 `scripts/stage2pilot/`（28 ファイル）が在る、
本契約以外の compute プロセス 0 件、空き 1,681,381,457,920 B、失敗の名前 6 件を記録した。

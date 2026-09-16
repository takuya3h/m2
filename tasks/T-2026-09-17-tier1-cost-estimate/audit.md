# audit — T-2026-09-17-tier1-cost-estimate

命令と出力の全文、対照の出力、装置の照会結果、変更範囲の一覧。

## 1. 作業ツリーの清浄と退避（Task A-1）

開始前から在った未追跡は **2 件**。消さずに stash へ退避した。

    $ git status --short
    ?? docs/sessions/digest/2026-09-16-b7b71e9f-6ec8-4e6a-887a-4c65cbaa30e0.md
    ?? tasks/T-2026-09-17-fold-table/

    $ git stash push -u -m "pre-T-2026-09-17-tier1-cost-estimate-2"
    Saved working directory and index state On feat/fold-table: pre-T-2026-09-17-tier1-cost-estimate-2

退避先: `stash@{0}`（`On feat/fold-table: pre-T-2026-09-17-tier1-cost-estimate-2`）。件数 **2**。
戻しは `git stash pop`。**開始前から在る未追跡を消していない。**

## 2. 契約の取り込みと検査

    $ make task-start TASK=T-2026-09-17-tier1-cost-estimate
    [task-start] 分岐を作成: feat/tier1-cost-estimate（起点 origin/phase0）
    [task-start] .sync-pause は実行前から存在するため触れません
    OK   T-2026-09-17-tier1-cost-estimate
    1 task(s), 0 failed

`.sync-pause` は **実行前から存在**していたため触れていない。稼働中の keeper が
目印に対応済みであることを確かめた。

    $ grep -c sync-pause ~/bin/m2-sync.sh
    2

### L3 プリフライト（1 回目 — P6 が FAIL）

    P6 decisions_answered     FAIL 未回答 2 件: 所要時間の実測が無い run 型について、どの実測を代理に使うか（代理を置くなら利用者の承認）; 装置の台数の前提（どのホストの GPU を数に入れるか）
    RESULT: 5 PASS / 0 WARN / 6 SKIP / 1 FAIL

ここで**停止して利用者へ提示した**。自分で決めていない。

### L3 プリフライト（2 回目 — 回答後）

    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS docs/stage0/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
    P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
    P12 refs_resolved          SKIP 解決前提の参照は無い

    RESULT: 6 PASS / 0 WARN / 6 SKIP / 0 FAIL

**SKIP は合格ではない。** SKIP された 6 件は P2 / P3 / P4 / P5 / P11 / P12 である。

## 3. 装置の照会（Task A-4）

    $ nvidia-smi --query-gpu=index,name,memory.total --format=csv
    index, name, memory.total [MiB]
    0, NVIDIA RTX A6000, 49140 MiB
    1, NVIDIA RTX A6000, 49140 MiB

    $ hostname
    Bengio

本ホストは **RTX A6000 × 2**。M §5.4 の記載「A6000 × 2」と**一致**する。

**他ホストへは接続していない**（利用者の決定 2 により、本ホストだけを数に入れる）。
`runindex/index.csv` の `host` 列に現れる他ホストは lecun 916 / efros 206 / andrew 69 /
philip 31 / bengio 3 / 空 41 run。`gpu` 列は **全 1266 run で空**であり、
runindex からは台数を読めない。

## 4. 所要時間の実測の出所（Task A-3）

    $ python3 -c "... runindex/index.csv の metric.elapsed_seconds を集計 ..."
    total runs: 1266
    with elapsed_seconds: 426
    --- elapsed_seconds by (group,subgroup,step,arm) ---
    426 ('phase1', '', 's4_grasp_injection', 'unknown')
    elapsed_seconds: min 6.3 med 33.4 max 48.8

runindex で計時が残っているのは `s4_grasp_injection` の 426 run **だけ**である。
**検出系の run には一件も `elapsed_seconds` が無い。**

元の記録から引いた値（契約 §2.5 は「C の要約値を使わず元の記録の行から引く」と定める）:

| run 型 | 値 | 元の記録の行 |
|---|---|---|
| 工程側の界面 run | 11.9〜30.0 s（n=11） | `docs/stage0/B_contract_b_results.md` §3 の表 |
| 工程塔の学習 | 105 s（3 epoch・1 seed） | `docs/stage0/B_pd_b2_b4_results.md` §2.1 |
| 検出側 W1 界面 run | **1 run 約 4 時間**（6 epoch）、2 本並行で 1 epoch 36〜40 分、単独 2.2 it/s = 37 分/epoch | `tasks/T-2026-08-29-lecun-detector-env-pd/RESULT.md:88` |
| B4 の界面 run 12 本 | 各 14.5〜32.2 s（計 約 4 分） | 同上 `:89` |
| 装置の利用実績 | A6000 2 枚 | 同上 `:90` |
| 注入掃引 360 本 | 7510.5 s = 2.09 h（装置 2 枚並行） | `tasks/T-2026-08-15-injection-sweep-deterministic/RESULT.md:277` |

**実測が見つからなかったもの**（探索の全文は §5）:

- 検出塔のフル学習。`runindex/runs/baselines___legacy_score_thr_0__s0_016_relationdetr_bbox_seed42.json`
  の `notes` にも `command` にも計時が無い。塔は philip で学習され完走 ckpt だけが
  配置された（`docs/experiment_log.md` 2026-05-31 項）
- 検出側 W2 の界面 run。**`W2` は `docs/stage0/*.md`・`docs/experiment_log.md`・
  `tasks/*/RESULT.md` のいずれにも現れない**（該当 0 行）

## 5. 探索に使った命令（実測が無いことの根拠）

    $ grep -rn "W2" docs/stage0/*.md docs/experiment_log.md tasks/*/RESULT.md
    （出力なし）

    $ grep -rn "4 時間\|およそ 4\|14400\|秒単位" docs/ tasks/ --include="*.md" | grep -v "^docs/archive"
    … tasks/T-2026-09-17-tier1-cost-estimate/SPEC.md:54 のほかは同期監査の文脈のみ …

    $ grep -n "h/run\|所要\|完走" docs/experiment_log.md
    588: 本番 fixed seed42(GPU0)/seed123(GPU1) を起動、1.7-1.8 it/s で健全進行。~12h/run 見込み。

`:588` は「見込み」であって実測ではない。**実測として採らない**（候補欄にのみ残す）。

## 6. 計算器の対照（完了判定 d）

**両方を出す。片方だけでは線形性の壊れ方と区別できない。**

    $ python tools/estimate_tier_cost.py --control
    前提: K=3 装置=2 1日=24.0h
    
    [対照 1] 所要時間表をすべて 2 倍にする → 総量が 2 倍になるはず
      基準   GPU 時間 = 4,035.1 〜 5,369.6
      2 倍後 GPU 時間 = 8,070.1 〜 10,739.1
      比 = 2.000000 / 2.000000  → PASS
    
    [対照 2] 装置を 2 倍にする → 壁時計時間が半分以下になるはず
      基準   壁時計 = 2,017.5 〜 2,684.8 h（装置 2）
      2 倍後 壁時計 = 1,008.8 〜 1,342.4 h（装置 4）
      比 = 0.500000 / 0.500000  → PASS
    
    RESULT: PASS（片方だけでは線形性の壊れ方と区別できないため両方を出している）

## 7. 完了判定の陽性対照

### [a] 出所を一件消すと 1 件を返すか

    消す前: (0, [])
    消した後: (1, ['phase_iface'])

### [b] 対応表から一項目を消すと 1 件を返すか

    消す前: (0, [])
    消した後: (1, ['t1.pd_w2'])

### [c] 文書の数値を一つ書き換えると差が非零になるか

    $ python tools/estimate_tier_cost.py --check-doc <破壊した写し>
    文書と再計算の差: 1 件
      - base 行 13:
      文書 = | 3 | **Stage 1 + Tier 1** | 9,999〜1,799 | 3,673.5〜5,008.0 | 1,836.7〜2,504.0 | 76.5〜104.3 |
      再計算 = | 3 | **Stage 1 + Tier 1** | 1,309〜1,799 | 3,673.5〜5,008.0 | 1,836.7〜2,504.0 | 76.5〜104.3 |
    (exit=1)

**破壊したのは写し**（scratchpad）であり、本体の文書は書き換えていない。

### 本体に対する検査

    $ python tools/estimate_tier_cost.py --check-sources
    出所の無い run 型: 0 件

    $ python tools/estimate_tier_cost.py --check-coverage
    対応の無い M 項目: 0 件

    $ python tools/estimate_tier_cost.py --check-doc docs/stage0/B1_tier1_cost_estimate.md
    文書と再計算の差: 0 件

## 8. 試験

    $ ruff check tools/estimate_tier_cost.py tests/test_estimate_tier_cost.py
    All checks passed!

    $ python -m pytest tests/test_estimate_tier_cost.py -q
    15 passed

全件（開始前に相当 = 新規試験を除く / 現在）:

    $ python -m pytest tests/ -q --ignore=tests/test_estimate_tier_cost.py
    7 failed, 534 passed, 22 warnings in 43.41s

    $ python -m pytest tests/ -q
    7 failed, 549 passed, 22 warnings in 35.17s

🔴 **失敗 7 件は本契約の変更前から失敗している。** 増減は零で、増えた 15 件は
すべて本契約が足した試験である。既存の失敗は次の 7 件であり、**直していない**
（本契約の変更対象外であり、触れば「変えるのは界面の入力だけ」の原則から外れる）。

    FAILED tests/test_check_spec.py::test_teacher_detection_rate
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

`ruff format --check` は本ファイルを「要整形」と出すが、`tools/` は 26 件中 17 件が
同じ状態であり、**この repo は tools/ に整形器を当てていない**。既存の状態に合わせた。

## 9. 禁止領域と変更範囲

    $ make forbidden-check
    {"base": "origin/phase0", "changed": 5, "checked": 5, "declared_allowances": [],
     "effective_allowances": [], "errors": [], "excluded": 0, "excluded_paths": [],
     "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"],
     "permitted": [], "rejected_allowances": [], "status": "pass", "task": null,
     "violations": []}

    $ make spec-check TASK=T-2026-09-17-tier1-cost-estimate
    "hits": 0, "rules_checked": 8, "status": "pass", "targets": 1

**`experiments/**`・`data/**`・`runindex/**`・`context/conventions.md` は読むだけで
書いていない。** `context/auto/*` と `tasks/inbox.md` は再生成していない（契約 §4-3）。
既存の `tasks/*/` も変えていない。

変更した範囲:

    $ git status --short
    ?? docs/stage0/B1_tier1_cost_estimate.md
    ?? tasks/T-2026-09-17-tier1-cost-estimate/
    ?? tests/test_estimate_tier_cost.py
    ?? tools/estimate_tier_cost.py

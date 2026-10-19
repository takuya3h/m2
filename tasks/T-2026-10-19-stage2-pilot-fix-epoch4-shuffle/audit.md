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

## B. 材料の確認と再現

### B-1 前回の信号（Task B-1、17:2x JST）

道具: `scripts/stage2pilot/material_check.py`（新規。OLD と前回の記録を読むだけ。書くのは `--out` と陽性対照の複製）。
出力: `experiments/analysis/stage2_pilot_fix/material/material_check.json`。

    $ .venv/bin/python scripts/stage2pilot/material_check.py --out experiments/analysis/stage2_pilot_fix/material/material_check.json \
        --flip-dir FIX/controls --count-run stage2pilot_dp_999_ZZZ_none_seed42 'stage2pilot_dp_*_D1-L1_pred_noCF_seed42'
    P0 / P-GT（train・val）                     在る・一致（照合先: 版管理下の signals/record_phase_{train,val}.json）
    D0 / D-GT / D0-RT / D0-INST-UQ / D-GT-INST（train・val）
                                               在る・一致（照合先: OLD/signals/final/record_{train,val}.json と、DP の run の config.yaml の sha256。両方）
    D0・D0-RT・D0-INST-UQ（交差適合版 train）   在る・一致（照合先: DP の run の config.yaml）。半分ずつ（cf_det_from_H1/H2）の sha256 は
                                               版管理下の crossfit/record_det_from_H{1,2}.json と一致。半分から組み直した中身も一致（9,657 フレーム、違い 0）
    P0（交差適合版 train）                      在る・一致（照合先: OLD/queues/cf_ptower_merge.log の全桁と、前回の audit の先頭 8 桁 e7b23991）。
                                               半分ずつの sha256 は crossfit/record_phase_from_H{1,2}.json と一致。組み直した中身も一致
    PD gtpred_CF_train                         在る・一致（照合先: 合わせ込みのログ）。P-GT_train ⊕ 交差適合版 P0 から連結し直した中身も一致
    PD gtpred_noCF_val                         在る。**前回の記録に sha256 が無い**ため、P-GT_val ⊕ P0_val から連結し直して中身の一致だけを確かめた（1,515 フレーム、違い 0）
    陽性対照（OLD の D0_val.npz を FIX/controls へ複製し末尾から 100 バイト目を反転）: 一致 False
    全件在る True、記録と全件一致 True

### B-2 epoch ごとの記録（Task B-2）

    DP 63 本（試走 5 本を除く）: logs/history.json 在る 63、無い 0、epoch 4 の行が無い 0
    名指しの数え: stage2pilot_dp_999_ZZZ_none_seed42 → 0（存在しない名前）、stage2pilot_dp_*_D1-L1_pred_noCF_seed42 → 1

PD 22 本の `logs/val_metrics_by_epoch.json` の 4 epoch 目（epoch 3）のクラス別の行と、前回の最良の epoch:

| run | 記録 | epoch 3 | 最良 |
|---|---|---|---|
| P1-W1 空 | 在る | **無い** | 0 |
| P1-W1 予測-noCF | **無い**（cap_result.json は mAP だけ） | **無い** | 2 |
| P1-W1 正解 / 予測-CF / 正解予測-CF | 在る | 在る | 2 / 2 / 1 |
| P1-W2 空 | 在る | **無い** | 0 |
| P1-W2 予測-noCF / 正解 / 予測-CF / 正解予測-CF | 在る | 在る | 2 / 2 / 2 / 3 |
| P2L 空 / 予測-noCF / 正解 / 予測-CF / 正解予測-CF | 在る | 在る | 1 / 3 / 3 / 2 / 3 |
| P3 の 5 腕 | 在る | **無い**（epoch 2 で止まった） | すべて 0 |
| P2F 予測 / 正解 | 在る | 無い（学習なし。値は epoch に依らない） | −1 |

4 epoch 目の値が無いのは SPEC §2 の 8 本と同じ（P1-W1 の空・予測-noCF、P1-W2 の空、P3 の 5 腕）。
**動画ごとの 4 epoch 目の値**は、回し直さない学習ありの run 12 本のうち、最良が epoch 3 の 4 本（P1-W2 正解予測-CF、P2L の予測-noCF・正解・正解予測-CF）
だけが前回の best の予測（＝epoch 3 の予測）から出せる。残る 8 本（P1-W1 の正解・予測-CF・正解予測-CF、P1-W2 の予測-noCF・正解・予測-CF、
P2L の空・予測-CF）は epoch 3 の予測も重みも残っていないため UNKNOWN（回し直しの表に無く、run は足せない。SPEC §6-12）。

### B-3 塔単独の val の再現（Task B-3、17:3x〜17:4x JST）

台本: `experiments/analysis/stage2_pilot_fix/repro/run_repro.sh`（工程は `repro_ptower.py`、検出は前回の `eval_dtower_val.sh` を読んで実行。出力は本契約の置き場）。

    工程塔: phase_jaccard 0.7762185528074379（前回 0.7762185528074379、差 0.0）／ phase_accuracy 0.8712871287128713（差 0.0）
            動画ごと 09 Jaccard 0.99317 / acc 0.99614、10 Jaccard 0.67537 / acc 0.80642。val 1,515 フレーム、動画 ['09', '10']
    対照（P20 seed42 の時間ヘッド 036）: Jaccard 0.6379452、acc 0.8528053（値が変わる）
    検出塔: Test: Total time 0:01:04、mAP 0.7273450248398429（差 0.0）、標的群 AP 0.7950748008550897（差 −1.1e-16）、
            陰性対照群 AP 0.6726631817581498（差 0.0）。欠けた群のクラス 0。クラス別 AP は前回の再現と完全一致
    対照（seed 123 の checkpoint）: mAP 0.7288631、標的群 0.8234321、陰性対照群 0.6701777（値が変わる）

### 関門 G2: **pass**

前回の信号と記録の要約値はすべて一致し、塔単独の val は工程・検出とも前回の値との差が 0.0（標的群 AP は −1.1e-16 の浮動小数点の差）で、許容差 0.005 の内。

## C. 道具の変更

### C-1 固定の長さ（既定の挙動は変えない。引数を足す形）

- `scripts/train_t1b.py`（PD）: `--fixed-epochs` を足した。`--epochs` の回数を止めずに学び、最後の epoch の状態を結果にする
  （`mAP > best` の比較の代わりに `epoch == epochs − 1` で選ぶ）。学習率は一定（`--patience` の経路と同じく MultiStepLR を作らない）。
  metrics.json・per_class_ap.json・t1b_result.json・best_t1b.pth・val の best の予測が最後の epoch の状態になり、
  `result_selection: final_epoch` を config.yaml・t1b_result.json・metrics.json に書く。`--patience`・`--eval-only` とは組み合わせない。
  **渡さなければ従来の経路のまま**（新しい項目も書かない）。
- `scripts/stage2pilot/dp_train.py`（DP）: `train --fixed-epochs N`（N epoch 学び、止めず、N epoch 目の状態を結果にする）、
  `--task-id`・`--exp-prefix`（既定は前回の契約の識別子と `stage2pilot_dp`。界面の重みは `stage2pilot_store/<task-id>/dp_ckpt`）、
  `--smoke`（`--fixed-epochs` の試走の印。名前に `_smoke`、config に `smoke: true`）、腕 `shuffle`、`identity --arm`・`--task-id` を足した。
  固定の長さのときだけ `result_selection`・`result_epoch` を書く。notes.md に「N epoch 学習し途中で止めない。結果は N epoch 目の状態」と書く。
- `scripts/stage2pilot/pd_fix_finalize.py`（新規）: PD の run の後で、結果が最後の epoch の状態であること
  （result_selection=final_epoch、best_epoch = final_epoch = epochs − 1、mAP = final_mAP）を確かめ、群の AP・動画ごとの mAP を
  `stage2fix_metrics.json` に、notes.md を書く。食い違えば止まる。
- `scripts/stage2pilot/run_pd_fix.sh`・`run_dp_fix.sh`（新規）: 前回の `run_pd.sh`・`run_dp_batch.sh` と同じ設定で、固定の長さと入れ替えの腕だけを変える。
  run は `experiments/phase1/stage2fix_{pd,dp}_*`、重みと入れ替えた信号は FIX。前回の台本の既定は変えていない。
- `scripts/stage2pilot/common.py`: 直しの契約の定数（`FIX_TASK_ID`、`FIX_STORE`、`FIX_ANALYSIS`）を足しただけ。

既定の経路の固定（試験）: 前回の `tests/test_train_t1b_stage2pilot_defaults.py` に `assert not a.fixed_epochs` を足し、
`tests/test_stage2pilot_dp_train_defaults.py`（新規 5 件。既定の契約の識別子・接頭辞・置き場・既存の腕の信号の出所・組み合わせの禁止）を置いた。

    $ pytest tests/test_stage2pilot_dp_train_defaults.py tests/test_train_t1b_stage2pilot_defaults.py → 10 passed
    陽性対照: --fixed-epochs の既定を True にした写し（scratchpad）を T1B_UNDER_TEST に渡す
      1 回目（EGO_BODY なし）→ 3 failed。2・3 件目は写しの置き場から BODY が決まるため（対照の作り方の誤り）
      2 回目（EGO_BODY=/home/ubuntu/slocal2/m2）→ test_new_options_default_to_off の 1 failed / 4 passed。元の版は 5 passed
    試験全体（変更後）: 6 failed, 883 passed。失敗の名前は開始時の 6 件と同じ（新しい 5 件は試験の追加後に数える）

試走（固定の長さの経路が端から端まで動くこと）:

    PD: run_pd_fix.sh P1-W1 shuffle smoke（GPU 1、1 epoch・6 step・val 20 枚、bf16）→ 学習 rc=0、拡張 ms_deform_attn_ext True
        t1b_result: result_selection final_epoch、best_epoch 0 = final_epoch 0、mAP 0.8907087 = final_mAP（学習前 0.8916612 の方が高いが選ばない）
        後処理は 1 回目に落ちた（rc=1）。val 20 枚では陰性対照群のクラスが出現せず群の AP が None になり、None を小数の書式で書こうとした
        **実行者の誤り**。None でも書ける形に直し、後処理だけ手で回し直した（rc=0、finalize_rerun.log）。exit_code.txt は 1 のまま残る
        注: 試走の名前は ep4 を含むが 1 epoch（名前の ep は台本の本番の回数。試走は末尾の _smoke で区別する）
    DP: dp_train.py train --type D1-L1 --arm pred_noCF --seed 42 --fixed-epochs 2 --smoke（GPU 1）→ stage2fix_dp_001_D1-L1_pred_noCF_ep2_smoke_seed42
        history の epoch 1・2 は前回の stage2pilot_dp_009 の epoch 1・2 と全項目（損失・Jaccard・accuracy）が完全一致
        結果は epoch 2（Jaccard 0.7715594）。epoch 1（0.7721016）の方が高いが選ばない。result_selection final_epoch、停止 None

### C-2 入れ替えの腕の信号（`scripts/stage2pilot/shuffle_signals.py`、新規）

出力: FIX/signals/shuffle/{P0,D0,D0-RT,D0-INST-UQ}_{train,val}.npz と mapping_{train,val}.json、記録 `experiments/analysis/stage2_pilot_fix/shuffle/shuffle_record.json`。
並べ替え: split ごとに、フレーム名の昇順の列を `np.random.default_rng(42).permutation` で並べ替え、フレーム f が元のフレーム π(f) の値を持つ。
同じ split の 4 信号はフレームの集合が同じことを確かめてから同じ並べ替えを使う（したがって PD と DP も同じ並べ替え）。D0-INST-UQ は行（トークン全体と count）を丸ごと入れ替える。

| split | フレーム | 対応が変わった割合 | 同じ動画から来た割合 | 全単射 | 対応表の sha256（先頭 16 桁） |
|---|---|---|---|---|---|
| train | 9,657（動画 10 本） | 1.000000 | 0.115357 | True | c62727faebe02252 |
| val | 1,515（動画 09・10） | 0.998680（元と同じフレーム 2 件） | 0.556436 | True | ad9dec099a32e683 |

4 信号とも train・val で: 値の集合が同じ（行を並べ直した要約値が元と一致）True、ファイルの要約値が元と違う True、
元と同じ値が来た割合 train 0.000000 / val 0.001320（= 不動点 2 件）。
陽性対照（完了判定 e の四列目）: 恒等の並べ替え → 対応が変わった割合 0.0。D0 の値を一つ変えた写し → 値の集合の一致 False（train・val とも）。

### C-3 集計（`scripts/stage2pilot/aggregate_fix.py`、新規）と既定の集計の再現

前回の `aggregate.py` を既定のまま前回の run に当てた（出力は本契約の置き場）:

    $ .venv/bin/python scripts/stage2pilot/aggregate.py --out-json experiments/analysis/stage2_pilot_fix/aggregate_default_check/report.json --out-md .../REPORT.md
    PD 22 runs, DP 63 runs。前回の report.json と比べて、comparisons 以外の鍵はすべて一致
    comparisons は 14 件とも値が同じで、並べ直すと一致し、並びだけが違う。aggregate.py 176 行が `set(tx["arms"]) & set(ty["arms"])`
    を回しており、文字列の set の反復順は実行ごとのハッシュの種で変わる（PYTHONHASHSEED 0/1/2 で順が変わることを確かめた）。前回の道具の既存の性質で、直していない

PD の要約の控え `stage2pilot_metrics.json` は前回の 22 本すべてに在り、前回の置き場への書き込みは起きない（aggregate_fix.py は控えが無ければ止まる）。

4 epoch 目の取り出しは epoch の番号を名指しする（PD は epoch 3、DP は epoch 4。最後の行や最良の行で代えない）。陽性対照（完了判定 d の四列目）:

    $ .venv/bin/python scripts/stage2pilot/aggregate_fix.py --self-check
    作り物の PD の記録（最良が epoch 1、epoch 3 は 0.72）→ 0.72 ／ 作り物の DP の記録（最良が epoch 2、5 epoch 目 0.81 もある）→ epoch 4 の 0.72
    epoch 2 で止まった作り物の PD の記録 → None（無いものは無いと返す）。pass true

### C-4 入れ替えの腕の恒等性と陽性対照（17:0x〜17:4x JST、GPU 0）

台本: `experiments/analysis/stage2_pilot_fix/identity/run_identity.sh`（PD は前回の `pd_eval.py`、DP は `dp_train.py identity --arm shuffle`）。

    塔単独の基準の予測を作り直した（FIX/identity/plain_val_preds.json.gz）: 前回の基準（OLD/identity/plain_val_preds.json.gz）との差
      score 0.0、枠 0.0 px、ラベルの食い違い 0、mAP 0.7273450
    PD（入れ替えた P0_val を入れ、零初期化の界面のまま）         恒等: mAP / 差              陽性（最後の層を N(0, 0.05²)、P2F は表を入れる）
      pd_film_d9（P1-W1・P1-W2）                                 0.7273450、score 差 0.0、枠 0.0  0.7287992、score 差の最大 0.4573
      pd_clsbias_lin_d9（P2L）                                   0.7273450、差 0.0               0.7274197、score 差の最大 0.0450
      pd_query_d9（P3）                                          0.7273450、差 0.0               0.7271373、score 差の最大 0.3466
      pd_clsbias_fix_d9（P2F、表なし／表あり）                   0.7273450、差 0.0               0.5843400、score 差の最大 0.9445
      いずれも界面以外の重みの要約値 4fed85166852…（塔単独と同じ）、checkpoint に無い鍵は界面だけ
    DP（入れ替えた val の信号。D3 は D0-INST-UQ）                恒等: Jaccard / ロジット差    陽性: Jaccard / ロジット差の最大
      D1-L1（D0、15 次元）                                       0.7762186 / 0.0              0.766756 / 0.2585
      D1-L2（D0-RT、3840 次元）                                  0.7762186 / 0.0              0.642680 / 2.0524
      D2（D0、15 次元）                                          0.7762186 / 0.0              0.774975 / 0.2229
      D3-L1（D0-INST-UQ から埋め込みを除いたもの、20 次元）       0.7762186 / 0.0              0.761595 / 0.1362
      D3-L2（D0-INST-UQ、276 次元）                              0.7762186 / 0.0              0.742408 / 0.3986
    DP の恒等の Jaccard は Task B の値と完全一致（jaccard_equals_taskB True、5 型とも）

注: `pd_eval.py` の出力の `task_id` は道具の定数（前回の契約の識別子）のまま。本契約の記録である（置き場と台本で区別できる）。

### C-5 test 不使用（`scripts/stage2pilot/test_audit_fix.py`、新規）

    $ test_audit_fix.py --out experiments/analysis/stage2_pilot_fix/test_audit_g3.json
    入れ替えた信号 12 本・対応表 12 本・DP の run の config と信号 12 本・PD の run の信号と注釈 12 本・恒等性と再現の評価 2 本・検出塔の再現の注釈 2 本、共通はすべて 0
    全体の共通 0 件
    陽性対照: --inject 04 → 全体の共通 1 件 ['04']

### 関門 G3: **pass**

固定の長さの仕組みが最後の epoch の状態を結果にし（PD・DP の試走、作り物の記録の取り出し）、既定の経路が前回の集計を同じ値で再現し
（comparisons の並びだけが違う。前回の道具の set の反復順）、入れ替えた信号が値の集合を保ったまま対応だけを壊し（train 100%、val 99.87%）、
入れ替えの腕の学習前の出力が塔単独と一致し（PD 4 構成・DP 5 型とも差 0.0、最後の層を零でない値にすると変わる）、test の動画を通していない。

## D. 再計算（GPU を使わない）

`scripts/stage2pilot/aggregate_fix.py` が前回の 85 本（PD 22、DP 63）の最良の回の値と 4 epoch 目の値を並べる（表は REPORT.md と report.json の `previous_values`）。

- 読む位置の検査（完了判定 g の四列目）: 前回の最良の値は、各 run の epoch ごとの記録の最大と全件一致（PD 20 本〔P2F 2 本は学習なしで対象外〕、DP 63 本）。
  P1-W1 予測-noCF は cap_result.json の epoch ごとの mAP（学習ログの 4 桁の表示）で照合した
- 前回の学習中の評価器（val_metrics_by_epoch.json のクラス別 AP）と、前回の報告の値を作った評価器（best の予測から計算し直す det_metrics）の
  クラス別 AP は、最良の epoch で全 run 差 0.0（P1-W1 予測-noCF は記録が無く対象外）。したがって epoch 3 の行から作る群の AP は前回の報告と同じ物差し
- 4 epoch 目の値が無い run: SPEC §2 の PD 8 本（B-2）。DP は無い run 0 本
- P1-W1 予測-noCF（Task D-3）: andrew に epoch 3 のクラス別の値は残っていない（最良は epoch 2 で、best の予測と重みは epoch 2 の状態）。回し直しの表どおり回し直す

## E. 学習

### E-1 DP の 26 本（17:37:43〜17:39:07 JST、GPU 0 と 1 に 13 本ずつ）

    $ CUDA_VISIBLE_DEVICES=0 bash scripts/stage2pilot/run_dp_fix.sh D1-L1:{empty,pred_noCF,gt,pred_CF,gtpred_CF,shuffle} D1-L2:{empty,pred_noCF,pred_CF,shuffle} D2:{empty,pred_noCF,gt}
    $ CUDA_VISIBLE_DEVICES=1 bash scripts/stage2pilot/run_dp_fix.sh D2:{pred_CF,gtpred_CF,shuffle} D3-L1:{6 腕} D3-L2:{empty,pred_noCF,pred_CF,shuffle}
    26 本すべて rc=0、DP_RUN_COMPLETE、result epoch 4。run は stage2fix_dp_002〜027（通し番号の重なりなし。001 は試走）

- 回し直しの 21 本は、前回の同じ run（seed 42）の history.json の epoch 1〜4 と、損失・Jaccard・accuracy の全項目が**完全一致**（差の最大 0）。
  4 epoch 目の値は前回の記録の epoch 4 と同値。違うのは選び方だけ
- 1 本の所要: 数秒（特徴と信号の読み込みを含めて 10 秒前後）
- 中間記録: `experiments/analysis/stage2_pilot_fix/INTERIM.md`（`aggregate_fix.py --interim`。計算し直しの検査 67 件で食い違い 0）。
  commit 40a8146e を push し、Draft の PR #240（base phase0）を開いた

### E-2 PD（17:39 JST〜）

キュー `FIX/queues/pd.q`（13 行。P2F 入れ替えの評価 → P1-W1 の空・予測-noCF・入れ替え → P1-W2 の空・入れ替え → P2L 入れ替え → P3 の 6 本）を、
前回の `scripts/stage2pilot/gpu_queue.sh` の取り手 4 本（GPU 0 に 2 本、GPU 1 に 2 本）で流す。`pd.q.stop` を置いてあり、キューが空になれば取り手は終わる。

- P2F 入れ替え（評価だけ、17:39:49〜17:44:36 JST、GPU 0）: rc=0。overall mAP 0.584340、標的群 AP 0.483404、陰性対照群 AP 0.659562、
  動画 09 0.548540 / 10 0.497360。G3 の陽性対照（表あり＋入れ替えた P0）の mAP 0.5843400 と同値。拡張 ms_deform_attn_ext True

#### 利用者の指示（18:0x JST）: 10 分ごとに問題がないか監視し、終了をできるだけ早める調整をする。VRAM が余っている

- 18:07 の実測: 4 本とも 1.8 it/s（GPU 1 枚あたり合計 3.6 it/s、1 epoch 約 47 分〔評価込み〕、1 本 約 3.2 時間）。
  GPU 0: P1-W1 空・P1-W2 空、GPU 1: P1-W1 予測-noCF・入れ替え（`/proc/PID/environ` の CUDA_VISIBLE_DEVICES で確かめた）。
  VRAM 15.2 / 49.1 GB と 14.6 / 49.1 GB、使用率 99〜100%、電力 283 / 300 W と 281 / 300 W（上限に近い）、load average 4.9（32 コア）、主記憶の空き 66 GB
- 見立て: VRAM は制約でなく、電力が上限に近いので計算がほぼ飽和している。前回の実測では 1 枚 1 本 → 2 本で合計 1.2 倍
- 試し: キューの次の 1 本（P1-W2 入れ替え）を、キューと同じロックで取り出し、GPU 0 の 3 本目として 1 回だけ起動した（18:08:49 JST。
  取り手は増やさない）。GPU 1 は 2 本のまま対照にする。学習ログの step の行が現れた時刻を 5 秒ごとに記録する
  （`FIX/queues/rate_sampler.sh` → `rate_samples.txt`）。GPU 0 の合計が 2 本のときより 1 割以上速ければ GPU 1 にも足すことを検討する
- 定時確認: セッション内の cron（10 分ごと、b850d33b）
- 判定（18:23 JST）: 3 本目が学習に入った 18:13:35 以後の 500 step の区間（rate_samples.txt の時刻の差）で
  GPU 0（3 本）: P1-W1 空 3000→3500 を 401 秒（1.247 it/s）、P1-W2 空 2500→3000 を 411 秒（1.217）、P1-W2 入れ替え 0→500 を 406 秒（1.232）→ 合計 3.70 it/s
  GPU 1（2 本、対照）: P1-W1 予測-noCF 3500→4000 を 281 秒（1.779）、入れ替え 3500→4000 を 275 秒（1.818）→ 合計 3.60 it/s
  3 本目を足す前の GPU 0 は 1.8 + 1.88 ≒ 3.6〜3.7 it/s。**合計の伸びは約 3%（1 割に届かない）。GPU 1 には足さない。**
  GPU 0 の 3 本目（P1-W2 入れ替え）は本番の仕事なのでそのまま続ける（止めると学習が無駄になる）。1 本あたりは遅くなるが合計は同じで、
  取り手は増やしていないため、この 1 本が終われば GPU 0 は 2 本に戻る。見積もりでは PD の終わりは元の計画（3 巡、10/20 03:00〜03:30 JST）とほぼ同じ
- 21:02 JST: P1-W1 予測-noCF・入れ替えが rc=0 で終わり（結果は epoch 3）、GPU 1 の取り手が P2L 入れ替えと P3 空を取った。
  予測-noCF の epoch 0〜3 の val mAP 0.7320 / 0.7304 / 0.7330 / 0.7268 は前回の同じ run（cap_result.json の 4 桁表示 0.732 / 0.7303 / 0.7336 / 0.7271）と差 0.0006 以内
- 21:13 JST: P2L と P3 は 1 step が軽く（逆伝播が検出器の奥まで届かない）、GPU 1 の 2 本の合計は 5.64 it/s（P2L 500 step を 166 秒で 3.01、
  P3 空 500 step を 190 秒で 2.63）、使用率 82%・電力 276 W と飽和していない。キューの次の 1 本（P3 予測-noCF）を GPU 1 の 3 本目として
  1 回だけ起動した（21:13:52 JST。取り手は増やさない）。3 本の合計が 5.64 it/s をどれだけ超えるかを次の確認で測る
- 判定（21:33 JST）: GPU 1 の 3 本目が学習に入った後の区間で、P2L 入れ替え 3000→3500 を 261 秒（1.92 it/s）、P3 空 2500→3000 を 281 秒（1.78）、
  P3 予測-noCF 1000→1500 を 281 秒（1.78）。合計 5.48 it/s（2 本のとき 5.64）。型で 1 step の重さが違うため 2 本のときの速さで割ると
  0.64 + 0.68 + 0.68 = 2.00（2 本のとき 2.00）で**伸びは 0**。使用率 82% でも計算は飽和していた。これ以上は足さない。
  足した 1 本は本番の仕事なので続ける（取り手は増やしていない）

#### 利用者の承認（21:4x JST）: P3 の残り 4 本を別ホスト bengio で回す（逸脱。`meta.amendments` の 2 件目）

- 提示した見込み（実測の速さで計算）: andrew だけ 10/20 03:05、P3 の 6 本を bengio（andrew の P3 の 2 本を止める）02:30、
  P3 の残り 4 本だけ bengio 01:20。最後の案は P3 の中でホストが混ざる。利用者は最後の案を選んだ
- 21:53 JST: andrew のキュー `pd.q` から P3 の 4 本（正解・予測-CF・正解予測-CF・入れ替え）を、キューと同じロックの下で外した
  （外す前の写し `pd.q.before_bengio_split`、外したもの `pd.q.moved_to_bengio`）。andrew のキューは空。取り手は今の run が終われば抜ける
- 道具: `run_pd_fix.sh` に置き場の切り替え（`S2FIX_BODY`＝データ・仮想環境・Relation-DETR・検出塔の重み、`S2FIX_CODE`＝台本・構成・run の置き場。
  既定は従来どおり）を足した。走っている bash が古い inode を読み続けるよう、写しを書いて `mv` で差し替えた。
  `pd_fix_finalize.py` は `EGO_ANN_DIR` を優先する（worktree には git の外の注釈が無い）。`train_t1b.py` の自動 commit は
  run の置き場から repo を決め、`exp/*` 分岐でなければ何もしない（`git_autosync.py` 171〜175 行）ので、worktree の feat 分岐では動かない

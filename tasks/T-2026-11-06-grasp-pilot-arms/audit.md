# audit — T-2026-11-06-grasp-pilot-arms（非公式の測定。関門と設計の判断に使わない）

ホスト bengio。時刻は JST（ホストの時計は UTC なので +9 時間して書く）。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-grasp-pilot-arms`（bengio）。
前契約の置き場 `R=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild` は読むだけ。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/grasp-tower-rebuild`（PR #295 は統合済み）。`feat/grasp-pilot-arms` は手元にも遠隔（`ls-remote`）にも無く、
  契約の履歴も `.sync-pause` も無かった（2026-11-06 15:4x JST）
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 046a5183）→ `未追跡・起点に無い: 10 件`、`分類: 止める`
  - 10 件はすべて `experiments/analysis/dtower_batch_search/tools/*.py`（禁止領域 `experiments/`、各 4K〜16K）
  - 出所: 別の契約 `T-2026-11-06-dtower-batch-search` の道具。9 件は `origin/feat/dtower-batch-search`（e5dd9a36）の版と中身が同じで、
    `summarize.py` だけその分岐に無い（未 commit の作業中の版が同期で届いたとみる）。その契約の PR は無い
  - 利用者の決定: 経路 `experiments/analysis/dtower_batch_search/` を `.git/info/exclude` に 1 行足す（分類で「phase0 に無い」と出た経路だけ。
    移さない・消さない）。足した後の分類は全区分 0 件、`分類: 通す`
- `source .venv/bin/activate && source scripts/load_env.sh && make task-start` → `分岐を作成: feat/grasp-pilot-arms（起点 origin/phase0）`、
  **`.sync-pause を作成`**（この契約が置いた目印）、契約を台帳から取り込み、`完了。`
  - 目印の中身: `task_id=T-2026-11-06-grasp-pilot-arms` / `branch=feat/grasp-pilot-arms`。`grep -c sync-pause ~/bin/m2-sync.sh` → 2（稼働中の版が対応済み）
- `make task-validate` → `OK`（exit 0）
- 参照の解決: `inject_verbatim` の 8 節（prohibitions・issuer_cautions・env_p0・folds・split・eval_recipe・det_groups・crossfit）は
  `context/conventions.md`（`git log -1` 2d946b07 = 契約の conventions_rev）の原文を読んで適用した。原文は同ファイルの
  12-33・98-119・154-191・297-365・443-468 行。denominator・frozen_source・sigma_policy の参照は無い
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。SKIP: P2・P3（契約に記載なし）、P4・P5・P13・P14（kind=analysis で対象外）、
  P12（解決前提の参照なし）。P9 spec_lint は該当なし。P11 gpu_free は compute 0 件

## Task A — 開始状態（G1）

記録の原本は `$S/start/`。

### A-1 分岐と起点、PR 295 の内容（`$S/start/a12.txt`）

    $ git branch --show-current; git merge-base HEAD origin/phase0; git rev-parse origin/phase0 HEAD
    feat/grasp-pilot-arms
    046a51839cc240b9d6a6e542f7dd27f1f9e8ef2b（merge-base・origin/phase0・HEAD が同じ。origin/phase0..HEAD は 0 件）
    $ git ls-tree --name-only origin/phase0 -- <目録> scripts/grasppilot/g5_{build,train,signals,flip_test,batch_probe}.py tasks/T-2026-11-05-grasp-tower-rebuild/RESULT.md
    7 件すべて在る
    $ git ls-tree -r --name-only origin/phase0 -- experiments/phase1/grasptower_G_{all,H1,H2}_seed42 | wc -l
    27（run の記録）
    $ git log --oneline -1 --grep='#295' origin/phase0
    e389abe5 Merge pull request #295 from takuya3h/feat/grasp-tower-rebuild
    $ git show origin/phase0:experiments/analysis/grasp_tower_rebuild/signals_manifest.json | sha256sum
    1717ae6963ef692faac5015ad9c14ba91162d7e9ad17db4447c874ecad26f090（SPEC §2 の 1717ae69… と一致）

### A-2 開始前から在る未追跡

- 無視されていない未追跡は 2 件（`tasks/T-2026-11-06-grasp-pilot-arms/{SPEC.md,spec.yaml}`、task-start が取り込んだ契約そのもの）
- 開始前から在る未追跡は「0. 始める」の 10 件（`experiments/analysis/dtower_batch_search/tools/*.py`）。無視の一覧に足しただけで、消していない・動かしていない
  （`git status --ignored` で 10 件とも `!!`）

### A-3 GPU の使用（`$S/start/a3_gpu.txt`・`a3_procs.json`）

    $ nvidia-smi --query-gpu=index,uuid,memory.used,utilization.gpu
    0, GPU-1b153400-…, 39 MiB, 0 %
    1, GPU-525aae08-…, 37 MiB, 0 %
    $ nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory
    （0 件）
    $ nvidia-smi -i 7 …            → No devices were found（rc 6。存在しない番号で 0 件）
    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 55、gpu_pids []、n_compute 0
    $ proc_enum.py --match-exe /usr/bin/zsh → count 10、--match-exe /nonexistent/bin/python9 → count 0

- 全体の使用量（39・37 MiB）と一覧の和（0 MiB）の差は駆動の常駐分（compute でない）。利用率 0 %。本契約以外の compute の使用は無い

### A-4 記憶領域（`$S/start/a4_df.txt`）

    $ df -B1 /home/ubuntu/slocal2
    Available 1,299,169,792,000 B（使用 83%）
    $ du -sb <二本目の保存先> <前契約の保存先>
    13,501,146,316 B・22,410,806,115 B
    $ du -sb experiments/phase1/grasppilot2_B_*（最大）
    26,180,783 B

- 見積もり: 術具だけの地図 train 9,657 × 5 × 270 × 480 B = 6,257,736,000 B、val 1,515 × … = 981,720,000 B。
  学習の重み（学ぶ部分だけ）と run の記録を足しても二本目の保存先（13.5 GB）程度。空きの 2% 未満

### A-5 試験と仮想環境（`$S/start/a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    11 failed, 980 passed, 5 skipped, 26 warnings in 49.51s
    失敗の名前（11）: test_check_spec::test_teacher_detection_rate、test_engines::test_mmdet_trainer_eval_recipe_in_metrics、
      test_fetch_task::test_rejects_unknown_file_name、test_research_logger の 4 件、test_stage1_ptower_heads::test_existing_candidates_match_baseline[A,B,C,linear]
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0（108 行）
    .venv-relation-detr a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090（72 行）
    （前契約の audit A-5 の値と一致）

### A-6 GPU の電力の上限と装置の型（`$S/start/a6_gpu_power.csv`）

    0, NVIDIA RTX A6000, 220.00 W（既定 300.00 W、最大 300.00 W）
    1, NVIDIA RTX A6000, 220.00 W（既定 300.00 W、最大 300.00 W）

### A-7 契約の版（`$S/start/a7_versions.txt`）

- `contract.conventions_rev` 2d946b07 = `git log -1 -- context/conventions.md`
- `meta.created_from.runindex_commit` 68befc3b = `git log -1 -- runindex/`。件数 index 2,363・experiments 1,130・verdicts 1,736（見出し行を除く）で一致
- 食い違いが無いので `meta.amendments` は空のまま

**G1: pass**（分岐 feat/・起点 origin/phase0・PR 295 の内容が起点に在る・本契約以外の compute 0 件・空き・失敗の名前・要約値・電力の上限を記録）

## Task B — 材料（G2）

記録の原本は `$S/b/`。

### B-1 目録の信号と G の重み（`$S/b/b1_inputs.json`、道具 `scripts/grasppilot/arms_check_inputs.py`）

    $ .venv/bin/python scripts/grasppilot/arms_check_inputs.py --out $S/b/b1_inputs.json
    一致 26 / 26
      G の重み 3（all 5ea2cbf4…・H1 5cfa055c…・H2 efdefccd…、$R/g/ckpt/<run>/best.pth）
      案 A の g 8（pred_noCF・pred_CF・shuffle・shuffle_CF の train・val。フレーム数 9,657・1,515、14 次元、flag の列なし）
      案 B の view 8（地図の経路とフレーム数も目録と一致）と地図 3（all_train_m・all_val_m・pred_CF_train_m、(N, 5, 270, 480) uint8）
      一本目の正解の g（g_train 741cecb5d42decd7…・g_val 235e2c2bde3a0478…）: $R/inputs/probe_signals と一本目の保存先の 2 か所とも一本目の audit 158 行の値に一致
    $ … --corrupt-copy $S/b/corrupt --out $S/b/b1_inputs_corrupt.json   （対照: pred_noCF_val を写して 100 バイト目を反転）
    一致 25 / 26（NG A_g pred_noCF_val 1831819e…）

### B-2 塔単独の val（`experiments/analysis/grasp_pilot_arms/repro/run_repro.sh`、`b2_summary.json`、16:0x〜16:2x JST）

台本は T-2026-11-01-stage2-w23-bengio の `run_repro.sh` の写しで、BODY を m2 本体（T-2026-11-02-bengio-align-andrew で andrew と一致させた）、置き場を本契約にした（差分は 3 行と見出し）。
拡張の読み込み: `env_check_det.txt` に `ms_deform_attn_ext True`。要約値（`b2_sha256.txt`）: 検出塔 seed 42 30d199b1…（w23-bengio の B-2 と同じ）

| 塔 | 値 | 記録（SPEC §1） | 差 |
|---|---|---|---|
| 検出塔 seed 42 | overall 0.7273450248、標的群 0.7950748009、陰性対照群 0.6726631818、AP50 0.8518074 | 0.7273450・0.7950748・0.6726632 | 2.5e-8・8.6e-10 |
| 対照: 検出塔 seed 123 | overall 0.7288631、標的群 0.8234321、陰性対照群 0.6701777 | — | +0.0015・**+0.0284（標的群が許容差 0.005 を超える）** |
| 工程塔 | macro Jaccard 0.7762185528074379、accuracy 0.8712871287128713（09: 0.99317・0.99614、10: 0.67537・0.80642） | 0.7762186・0.8712871 | −4.7e-8・+2.9e-8（丸めた記録との差）。全桁の記録 `common.PT_RECORD` との差 0.0 |

- 塔単独の予測は `$S/b/plain_val_preds_seed{42,123}.json.gz`（Task C の案 B の恒等性の基準）

### B-3 案 A の旗なしの口（`scripts/stage2pilot/dp_train.py`、`$S/b/b3_dims.txt`）

- 足したのは引数 `--grasp-no-flag`（train と identity）だけ。渡すと GA の x(t) が［予測の 14｜正解の 14］の 28 次元になり、信号のファイルの flag を読まない。
  渡さなければ従来の経路（旗あり 30 次元）のまま。GA 以外の型に渡すと止める。run の名前の desc は `GA-noflag_<腕>`、config に `grasp_no_flag: true`
- 対照（`Signals` を CPU で起こし、工程の経路のフレーム train 9,657・val 1,515 に当てた）:

| 経路 | 腕 | dim | 予測の半分が非零のフレーム | 正解の半分が非零のフレーム |
|---|---|---|---|---|
| 旗あり（既定） | 空 / 正解 | 30 / 30 | 0 / 0 | 0 / 9,356（val 1,514） |
| 旗なし | 空 | 28 | 0 | 0 |
| 旗なし | 予測-noCF・予測-CF・入れ替え | 28 | 9,657（val 1,515） | 0 |
| 旗なし | 正解 | 28 | 0 | 9,356（val 1,514） |
| 旗なし | 正解予測-CF | 28 | 9,657（val 1,515） | 9,356（val 1,514） |

- 旗なしの正解の半分は、注釈の無いフレーム（train 301・val 1）で零になる（旗が無いので「注釈なし」と「把持なし」を区別しない。利用者の決定 1 のとおり）

### B-4 術具だけの信号（`scripts/grasppilot/arms_tool_only.py`、`$S/signals/tool_only/tool_only_report.json`、`$S/b/b4_tool_only.log`）

- 元: 目録の B_m pred_noCF の地図（確定の G）。チャネルの並びは `grasp_signals.MAP_CHANNELS` = tool_L, tool_R, tool_B, hand_L, hand_R。
  器具の 3 チャネル（0〜2）の画素ごとの最大を 1 チャネル目（tool_L の位置）に置き、他の 4 チャネルを零にした

| part | フレーム | 地図の sha256 | 1 チャネル目の範囲 | 3 つのどれとも一致しない画素 | 3 つのどれかより小さい画素 | 他の 4 チャネルの非零 |
|---|---|---|---|---|---|---|
| train | 9,657 | 9e0685853cc466c150e08f3852243831d7f7c4885daa1607edb48c424d8ee26a | 0〜252 | 0 | 0 | 0 |
| val | 1,515 | 6758234ceb2d362ca157b307f6b817bd2fbe24997978514708e231510f234341 | 0〜252 | 0 | 0 | 0 |

- 対照 1（手のチャネルを零にしない写し [最大, 0, 0, hand_L, hand_R]）: 一致しないフレーム train 9,657 / 9,657・val 1,515 / 1,515（画素 764,372,515・143,069,614）
- 対照 2（1 チャネル目に hand_L を置いた壊れた写し）: 「3 つのどれとも一致しない画素」train 374,073,311・val 66,837,872（確かめが外れを拾う）
- 入れ替え: 規則（`stage2pilot.shuffle_signals.make_mapping`、seed 42、フレーム名の昇順）で作り直した並べ替えが目録の B_shuffle の見取りの mapping と
  train・val とも一致。seed 43 では一致しない。動かないフレームの割合 train 0.0・val 0.00132
- 見取り: `B_toolonly_pred_noCF_{train,val}.json`（a45e9168…・dd76c566…）、`B_toolonly_shuffle_{train,val}.json`（9385664e…・6f8c925e…）

### B-5 案 B の空の腕の code_sha256

    $ sha256sum <pd_grasp.py pd_grasp_model.py grasp_signals.py train_t1b.py pd_graspmap_{d5,pred5,d10}.py> | diff - experiments/phase1/grasppilot2_B_empty_ep4_seed42/code_sha256.txt
    （差なし。7 件一致）

- 本契約の案 B の経路はこの 7 件を変えない（起動台本は写し `scripts/grasppilot/run_pd_grasparms.sh` を新しく置き、別のファイル `runner_sha256.txt` に要約値を残す）。
  **空の腕は回し直さない。** 二本目の空の腕は andrew で回した run である（`server.txt`）

**G2: pass**（目録の信号と G の重みの sha256 一致、塔単独の val が許容差の中、術具だけの信号が定義どおり、旗なしの案 A の入力が 28 次元）

## Task C — 恒等性と対照（G3）

台本は `experiments/analysis/grasp_pilot_arms/taskC/`。GPU 0・1 で並行（16:3x〜16:5x JST）。記録 `$S/logs/c_*.log`

### C-1・C-2 案 A（`taskC/caseA/identity_<腕>.json`、`run_caseA_identity.sh`。`dp_train.py identity --type GA --grasp-no-flag`）

| 腕 | dim | 学習前の Jaccard / accuracy | ロジットの差の最大 | 塔単独と完全一致 | 陽性対照: ロジットの差の最大 / Jaccard |
|---|---|---|---|---|---|
| 空 | 28 | 0.7762185528 / 0.8712871287 | 0.0 | True | 0.0 / 0.7762186（信号が零なので変わらない） |
| 正解 | 28 | 同 | 0.0 | True | 0.2637 / 0.7822880 |
| 予測-noCF | 28 | 同 | 0.0 | True | 0.4796 / 0.7551561 |
| 予測-CF | 28 | 同 | 0.0 | True | 0.4796 / 0.7551561（val は予測-noCF と同じ信号） |
| 正解予測-CF | 28 | 同 | 0.0 | True | 0.6692 / 0.7666244 |
| 入れ替え | 28 | 同 | 0.0 | True | 0.4513 / 0.7547256 |

- 学ぶ集合: `iface.weight` だけ（1,792 = 28 × 64）で界面の名前の集合と一致。受け取り手のパラメータを一つ混ぜると不一致（6 腕すべて）

### C-1・C-2 案 B と術具だけ（`taskC/caseB/identity_<腕>.json`、`run_caseB_identity.sh`、`$S/logs/c_caseB_summary.txt`。道具 `pd_grasp_eval.py`）

基準は Task B-2 の塔単独の予測 `$S/b/plain_val_preds_seed42.json.gz`。凍結部の要約値 `non_interface_digest` 4fed8516… は 9 件で同じ

| 腕 | 学習前の mAP / 標的群 / 陰性対照群 | score の差・枠の差・ラベルの食い違い | 学ぶ集合 |
|---|---|---|---|
| 予測-noCF | 0.7273450 / 0.7950748 / 0.6726632 | 0.0・0.0 px・0 | `phase_iface.weight` 10,240、外を一つ混ぜると不一致 |
| 予測-CF | 同 | 0.0・0.0 px・0 | — |
| 入れ替え | 同 | 0.0・0.0 px・0 | — |
| 正解予測-CF（10 チャネル） | 同 | 0.0・0.0 px・0 | `phase_iface.weight` 20,480、外を一つ混ぜると不一致 |
| 術具だけ 予測-noCF | 同 | 0.0・0.0 px・0 | `phase_iface.weight` 10,240、外を一つ混ぜると不一致 |
| 術具だけ 入れ替え | 同 | 0.0・0.0 px・0 | — |

| 陽性対照（重み N(0, 0.05²)） | mAP / 標的群 | score の差の最大 | ラベルの食い違い |
|---|---|---|---|
| 予測-noCF | 0.7279864 / 0.7963757 | 0.443 | 329,497 |
| 正解予測-CF | 0.7279510 / 0.7957365 | 0.627 | 332,330 |
| 術具だけ 予測-noCF | 0.7274696 / 0.7949265 | 0.332 | 326,624 |

- 注記: `pd_grasp_eval.py` の出力 JSON の `task_id` は道具の既定（T-2026-10-31-grasp-pilot-probe）が書かれる。置き場は本契約の `taskC/caseB/`

### C-3 既定の挙動（`taskC/run_dp_default_check.sh`・`compare_default.py`、`taskC/dp_default/compare.json`）

- 起点の版（`git show 046a5183:scripts/stage2pilot/dp_train.py` → `$S/check/dp_train_old.py`、443a4543…）と変更後の版（a82e25d5…）で、
  `--grasp-no-flag` を渡さない同じ命令を回した。W&B は手元だけ（`WANDB_MODE=offline`、仮の鍵。資格情報は読み込まない）
- identity（GA 旗あり 30 次元の空・正解・予測-noCF・入れ替え。二本目の旗ありの予測の g、D1-L1 の既定の腕）の JSON: 差 0 件
- 試走（`--fixed-epochs 1 --smoke`、GA 正解）`grasparms_chk_dpold_001_GA_gt_ep1_smoke_seed42` 対 `grasparms_chk_dpnew_001_…`:
  metrics・config・history・クラス別・notes・val の確率・界面の重みの全テンソルが一致（Jaccard 0.770503 で同じ）。**`all_equal: true`**
- 陽性対照: 新しい版の metrics の phase_jaccard を 1e-9 ずらした写しは不一致として検出（`positive_control_detects: true`）
- 案 B の経路: 二本目の設定のファイル 7 件は変えていない（B-5 の code_sha256 一致）。本契約の台本の試走
  `$S/smoke/grasparms_B_toolonly_pred_noCF_ep4_seed42_smoke`（16:06 JST、28 秒、GPU 1）: rc 0、`ms_deform_attn_ext True`、
  `phase_grad=True init_mAP=0.8917 => PASS`、finalize まで完走。記憶の山（5 秒ごとの観測）約 6.8 GiB
- 試走の run（`grasparms_chk_dp{old,new}_*`、smoke）は腕に数えない

**G3: pass**（全腕で学習前の出力が塔単独と一致、陽性対照で出力が変わり、既定の挙動が変わらない）

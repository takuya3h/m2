# audit — T-2026-11-09-stage2-pd-w3-lowlr-andrew

ホスト andrew。時刻は JST。命令は要旨と出力の要点を書く（全文が要る所は出力を写す）。

## 0. 始める（手順書「0. 始める」〜「4. L3 プリフライト」、2026-11-09 09:58〜10:02）

- 受けた時点の分岐 `feat/dtower-rerun`（PR #305 は統合済み）、目印 `.sync-pause` 無し
- `feat/stage2-pd-w3-lowlr-andrew` は手元にも遠隔にも無く、`tasks/T-2026-11-09-stage2-pd-w3-lowlr-andrew` の履歴も無い
- `git fetch origin` → origin/phase0 5da763fd..129e79b0
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 129e79b0）:
  - 追跡下の変更 0、未追跡・起点に無い 1 件 → `分類: 止める`
  - `止めた理由 [未追跡・起点に無い] experiments/analysis/grasp_roitoken_transition_pilot/tools/digests.py`（禁止領域 `experiments/` に属する、8.0K、mtime 2026-11-09 09:58）
  - 中身の冒頭は「本契約が変えてはならない場所の要約値（T-2026-11-09-grasp-roitoken-transition-pilot …）」。T-2026-11-08-grasp-cards-survey（bengio で実行）の digests.py の写しと書かれている。
    どの遠隔の分岐にも無い。同期で届いた別の契約の生成物と判断した（bengio の作であることの直接の記録は無い）
- 利用者の指示（`/task` の引数「bengio の生成物のせいで止まったら .git/info/exclude において」）と SPEC Task A-2 に従い、
  起点に無いことを確かめて（`git cat-file -e origin/phase0:experiments/analysis/grasp_roitoken_transition_pilot` → 無し）、
  `.git/info/exclude` の 22 行目に `experiments/analysis/grasp_roitoken_transition_pilot/` をフォルダで足した。ファイルは消さず動かしていない
  - 20・21 行（`experiments/phase1/grasparms_B_empty_ep4_seed42/`、`experiments/phase1/grasparms_B_gt_ep4_seed42/`）は前の契約 T-2026-11-07-dtower-rerun で書いたもので、そのまま
- 分類のやり直し → `分類: 通す`
- `make task-start TASK=T-2026-11-09-stage2-pd-w3-lowlr-andrew`:
  - `[task-start] 分岐を作成: feat/stage2-pd-w3-lowlr-andrew（起点 origin/phase0）`
  - **`[task-start] .sync-pause を作成`**（この契約が置いた目印。中身 `task_id=T-2026-11-09-stage2-pd-w3-lowlr-andrew` / `branch=feat/stage2-pd-w3-lowlr-andrew`）
  - `[task-start] 完了。`。稼働中の `~/bin/m2-sync.sh` の `sync-pause` の出現 2 件（対応済み）
- `make task-validate` → `OK`、`1 task(s), 0 failed`、WARN なし
- 参照の解決:
  - `contract.conventions_rev` 2d946b07 は `context/conventions.md` を最後に変えた commit（2026-10-21T07:35:09Z）と同じ。2d946b07..HEAD の差分なし
  - `contract.inject_verbatim` の 7 節の錨は実在する: prohibitions 98 行、issuer_cautions 154、env_p0 109、folds 297、split 12、eval_recipe 24、det_groups 443
  - `inputs.sigma_policy` 省略 → `conventions#sigma`（65 行）の既定を継承
  - `meta.created_from`: 記載 d3e319ac・{index 2623, experiments 1305, verdicts 1947}。実測（起点 129e79b0、L2-8 と同じ数え方 = 行数 − 1）は
    runindex を最後に変えた commit b524173e・{2647, 1327, 1977}。食い違う（Task A-7 で差し替える）。分母を宣言しない契約なので L2-8 は WARN を出さない
  - `meta.created_at` 2026-11-09T01:30:00Z（10:30 JST）は取り込み（10:00 JST 前後）より後の時刻
- `make task-preflight` → `RESULT: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL`、rc 0
  - SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（plan.env.preflight に記載なし）、P4・P5・P13・P14（kind=analysis で対象外）、P12（解決前提の参照なし）
  - P11 gpu_free PASS（GPU を占有する compute プロセス 0 件）

## Task A — 開始状態（G1）

保存先 `S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-stage2-pd-w3-lowlr-andrew`（`mkdir -p $S/start`）。集計の置き場 `A=experiments/analysis/stage2_pd_w3_lowlr_andrew`。

### A-1 分岐と起点、前提の統合（10:02）

    $ git branch --show-current → feat/stage2-pd-w3-lowlr-andrew
    $ git rev-parse HEAD; git merge-base HEAD origin/phase0 → 129e79b05845dc966e9ace30cd209af08d7fdf38（同じ）
    $ git cat-file -e origin/phase0:<経路>
    起点に在る: tasks/T-2026-11-01-stage2-w23-bengio、tasks/T-2026-11-01-stage2-w23-andrew、scripts/w23、tasks/T-2026-11-02-bengio-align-andrew
    scripts/w23/: run_dp_w23_bengio.sh run_pd_w23_andrew.sh run_pd_w23_bengio.sh w23a_{aggregate,armcheck,bench,finalize,identity,material,report}.py

### A-2 開始前から在る未追跡

- task-start の前: 無視されていない未追跡 1 件 `experiments/analysis/grasp_roitoken_transition_pilot/tools/digests.py`（§0。無視の一覧にフォルダで足した。消していない・動かしていない）
- task-start の後の無視されていない未追跡は、取り込んだ契約の 2 本（`tasks/<id>/{SPEC.md,spec.yaml}`）と本 audit.md だけ

### A-3 compute プロセス（`$S/start/a3_procs.json`、道具 `scripts/grasppilot/proc_enum.py`、10:02）

    $ hostname → Andrew
    $ python3 scripts/grasppilot/proc_enum.py                              → n_processes 41、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh     → count 5（自分のシェルを含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0
    $ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv → 見出しだけ（0 件）
    $ ps -eo pid,user,comm,args で comm が python・torchrun で始まるもの（道具自身を除く）→ 0 件

**本契約以外の compute プロセスは 0 件**

### A-4 記憶領域（`$S/start/a4_df.txt`）

    $ df -B1 /home/ubuntu/slocal2
    /dev/sdc1  7937302376448  5936873795584  1600333713408  79%
    $ du -sb /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-andrew → 2030491205（前回の andrew の保存先。16 本）
    $ du -sb experiments/phase1/w23a_pd_DX_W3_{empty,gt}_ep4_seed42 → 71181731、73049894

空き 1,600,333,713,408 B。見積もり（上限側）: 保存先は前回の 2.03 GB に近い（同じ 16 本）ので ≤ 4 GB、run の置き場 16 本 × 75 MB ≤ 1.2 GB、合計 ≤ 6 GB（空きの 0.4 %）。足りる

### A-5 試験と仮想環境（`$S/start/`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped, 26 warnings in 29.02s

失敗の名前（`$S/start/a5_fail_names.txt`。前回の andrew の契約の開始時と同じ 6 件）:

    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    tests/test_fetch_task.py::test_rejects_unknown_file_name
    tests/test_research_logger.py::test_log_run_idempotent
    tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv                 108 行  9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0
    .venv-relation-detr    72 行  a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090
    （どちらも前回の andrew の契約の記録の値と一致）

重ねの BODY（`/home/ubuntu/slocal2/s2fix-bengio-body`）は andrew に無い（`ls` → No such file or directory）。SPEC §2 の注記どおり andrew では該当しない。学習は andrew の main（`EGO_BODY=/home/ubuntu/slocal2/m2`）と `.venv-relation-detr` で行う（前回の andrew の台本と同じ）

### A-6 GPU（`$S/start/a6_gpu.csv`）

| GPU | 型 | 電力の上限 | 既定の上限 | 最大の上限 | 記憶 | 使用中 |
|---|---|---:|---:|---:|---:|---:|
| 0 | NVIDIA RTX A6000 | 300.00 W | 300.00 W | 300.00 W | 49,140 MiB | 16 MiB |
| 1 | NVIDIA RTX A6000 | 300.00 W | 300.00 W | 300.00 W | 49,140 MiB | 16 MiB |

### A-7 起票時の値

- `contract.conventions_rev` 2d946b07 は実測と一致（§0）
- `meta.created_from` を d3e319ac・{2623, 1305, 1947} → b524173e・{2647, 1327, 1977} に差し替え、`meta.amendments` に記録した。`make task-validate` → OK（差し替えの後）

### G1 の判定（10:10）

分岐 `feat/stage2-pd-w3-lowlr-andrew`、起点 origin/phase0 129e79b0 に前回の二契約と `scripts/w23/` が在り、本契約以外の compute プロセス 0 件、
空き・失敗の名前・仮想環境の要約値・電力の上限と装置の型を記録した。**通過。**

## Task B — 材料と再現（G2）

道具はすべて本契約の置き場 `$A/tools/` に置いた（`scripts/` は allow_write の外なので書かない）。既存のファイルは変えていない。

### B-1 材料（`$A/material/material.json`、道具 `tools/w3lra_material.py`、10:10）

本契約が読む信号 6 本・検出塔 2 本（seed 123 は B-2 の対照だけ）・設定 4 本・学習のコード 2 本の在否と sha256 を、前回の記録と照合した。
記録は前回の andrew の B-1（`stage2_w23_andrew/material/material.json`）、前回の bengio の B-1（`stage2_w23_bengio/material/material_check.json`。
重ねの BODY の経路は andrew の main に読み替える）、前回の W3 の run の `input_sha256.txt`・`code_sha256.txt`、
設定とコードは前回の andrew の W3 の run の `code_commit.txt`（6edae0e9）の版の同じ経路の中身（`git show`）、seed 123 は前の契約の repro の記録。

    $ .venv/bin/python $A/tools/w3lra_material.py --out $A/material/material.json --flip-dir $S/material/flip

| 区分 | ファイル | sha256 の頭 | 記録の数 | 結果 |
|---|---|---|---:|---|
| 空・予測-noCF | folda `signals/final/P0_{train,val}.npz` | e58308d3・082387a0 | 4・4 | 一致 |
| 正解 | folda `signals/final/P-GT_{train,val}.npz` | 6cb729a9・d21a3cf0 | 3・3 | 一致 |
| 入れ替え | 直しの契約 `signals/shuffle/P0_{train,val}.npz` | 09814ab2・9ffc4e4d | 3・3 | 一致 |
| 検出塔 seed 42 | `stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth` | 30d199b1 | 4 | 一致 |
| 検出塔 seed 123（対照） | 同 seed123 | 5842a2ae | 2 | 一致 |
| 設定 | `configs/stage2pilot/pd_{film,clsbias_lin,query,dec_xattn}_d9.py` | a2cab596・b67d3287・e01b1cc2・c32c18b6 | 1・1・1・5 | 一致 |
| コード | `scripts/train_t1b.py`・`scripts/stage2pilot/pd_model.py` | 501f4413・05b76a3f | 17・17 | 一致 |

**all_exist true、all_with_record true、all_match true**。andrew に無いものは無い（他の台から写していない）。
陽性対照: `P0_val.npz` の複製の 1000 バイト目を反転すると sha256 286564a6… で記録と一致しない（`flip_control.matches_record` false）。変えない複製は一致する（`copy_control` true）

- 最初の版は設定 P1・P2L・P3 と seed 123 に記録を持たなかった（bengio の run の `git_commit.txt` は `unknown`、`code_sha256.txt` は設定を含まない）。
  版管理の版の中身と前の契約の repro の記録を足して照合し直した（上の表はその結果）

### B-2 塔単独の再現（`$A/repro/`、台本 `tools/run_repro.sh`、10:11:27〜10:14:09）

前回の andrew の `repro/run_repro.sh` の写し（変えたのは置き場だけ。`diff` で 3 行）。道具は `scripts/stage2pilot/pd_eval.py --cfg plain`、val だけ。

| 塔 | 指標 | andrew（本契約） | 記録（SPEC §2） | 差 |
|---|---|---|---|---|
| 検出 seed 42 | overall mAP | 0.7273450248398429 | 0.7273450 | 0.0 |
| | 標的群 AP | 0.7950748008550897 | 0.7950748 | 0.0 |
| | 陰性対照群 AP | 0.6726631817581498 | 0.6726632 | 0.0 |

許容差 0.005 の中。AP50 0.851807、動画ごと 09 0.704273・10 0.642097、1,515 枚（動画 09・10）。`env_check_det.txt` `ms_deform_attn_ext True`。
塔単独の予測を `$S/identity/plain_val_preds.json.gz`（26,929,542 B）に保存（恒等性の基準）。

対照（判定が働くこと）: seed 123 の検出塔で overall 0.7288631（差 +0.0015）、**標的群 AP 0.8234321（差 +0.0284、許容差を超える）**、陰性対照群 0.6701777（差 −0.0025）

### B 腕と信号の対応（`$A/armcheck/`、道具 `tools/w3lra_armcheck.py`）

起動の台本 `tools/run_w3lra.sh`（前回の andrew の `scripts/w23/run_pd_w23_andrew.sh` の写し。P2L・P3 を足し、W3 と 4 腕だけに絞り、
`--lr 1e-5 --film-lr 5e-4` を明示し、包み `tools/w3lra_lrwrap.py` を通して起動する）の dryrun を、前回の W3 の run の `config.yaml`
（P1・P2L・P3 は bengio の `w23b_pd_<型>-W3_<腕>`、DX は andrew の `w23a_pd_DX_W3_<腕>`）と突き合わせた。

    $ .venv/bin/python $A/tools/w3lra_armcheck.py --out $A/armcheck/armcheck.json
    {"swap": null, "n": 16, "n_match": 16, "all_match": true, "lr_now_all": [1e-05], "lr_prev_all": [0.0001]}
    $ .venv/bin/python $A/tools/w3lra_armcheck.py --swap gt,pred_noCF --out $A/armcheck/armcheck_swap_control.json
    {"swap": "gt,pred_noCF", "n": 16, "n_match": 8, "all_match": false, ...}      ← 陽性対照

一致を見た項目: 設定の名前、学習と評価の信号、零の信号、`trainable`（all）、界面の学習率 5e-4、bf16・seed 42・4 epoch・固定の長さ。
**違うのは受け取り手の学習率だけ**（前回 1e-4、本契約 1e-5）。台本は表に無い腕（`pred_CF` → 回さない腕）・型（`EQ` → 回さない型）・モード（`smoke_lr1e-3` → 不明）を拒む

### B-3 学習率が群に届くこと（`$S/smoke/`、10:16:51〜10:17:29）

`train_t1b.py` は optimizer の群の学習率を記録に出さない。既存のファイルを変えずに記録するため、包み `tools/w3lra_lrwrap.py` を置いた。
読み込んだ後の `param_dict.finetune_t1b`・`torch.optim.AdamW`・`train_t1b.eval_detection` を、元を呼んでから記録するものに差し替えるだけで、
学習の計算は元のまま。記録 `lr_groups.json`: 群の順の名前・学習率・weight decay・テンソルと要素の数、作った直後（init）・各評価の直前（eval_k）・最初の更新の後の学習率。
本番の 16 本も同じ包みを通す（各 run の `lr_groups.json`）。`--fixed-epochs` では `train_t1b.py` は scheduler を作らない（`sched = None`、402 行付近）。

    $ CUDA_VISIBLE_DEVICES=0 bash $A/tools/run_w3lra.sh P1 gt smoke; ... P3 gt smoke; ... P1 gt smoke_lr1e-4
    $ CUDA_VISIBLE_DEVICES=1 bash $A/tools/run_w3lra.sh P2L gt smoke; ... DX gt smoke
    5 本とも rc 0（1 本 12〜14 秒。1 epoch・6 step・val 20 枚）、ms_deform_attn_ext True

| 群（`finetune_t1b` の順） | 要素（P1） | 1e-5 の写し（P1・P2L・P3・DX） | 陽性対照（P1、受け取り手 1e-4） | weight decay |
|---|---:|---|---|---|
| other | 24,384,000 | 1e-5 | 1e-4 | 1e-4 |
| backbone（× 0.1） | 23,232,512 | 1e-6 | 1e-5 | 1e-4 |
| backbone_norm（× 0.1） | 0（bn は FrozenBatchNorm2d の buffer） | 1e-6 | 1e-5 | 0 |
| linear_projection（× 0.1） | 786,432 | 1e-6 | 1e-5 | 1e-4 |
| linear_projection_norm（× 0.1） | 3,072 | 1e-6 | 1e-5 | 0 |
| other_norm | 65,184 | 1e-5 | 1e-4 | 0 |
| phase（界面。名前はすべて `phase_iface.*`、他の群に `phase` を含む名前は無い） | P1 266,880・P2L 150・P3 2,560・DX 210,374 | 5e-4 | 5e-4 | 1e-4 |

- 学習率は 4 時点（init・eval_0・after_step_1・eval_1、更新 0・0・1・6 回目）すべてで同じ値（1e-6 は浮動小数で 1.0000000000000002e-06）
- 群の要素の合計（学ぶ要素）: P1 48,738,080・P2L 48,471,350・P3 48,473,760・DX 48,681,574。前回の W3 の記録（andrew の DX・P1、bengio の P2L の `config.yaml` の total_trainable）と同じ
- **陽性対照**: 受け取り手を 1e-4 にした写しでは、受け取り手の群が 1e-4、比 0.1 の群が 1e-5 に変わり、界面の群は 5e-4 のまま

記憶: 試走の間の 3 秒ごとの採取（`$S/smoke/gpu_mem_samples.txt`）で、1 本の最大 10,434・10,846 MiB（試走は 1 本ずつ）。
前回の andrew の計測（W3 の記憶の山 12,594 MiB reserved、1 枚 3 本で nvidia-smi の最大 39.8 / 40.0 GB）に合わせ、**1 枚に載せる本数は 3 本**とする

### B-4・B-5 学ぶ集合と恒等性（`$A/identity/`、台本 `tools/run_identity.sh`、10:28:00〜10:52:18、GPU 2 枚・1 枚 3 並列）

道具 `tools/w3lra_identity.py`（前回の andrew の `scripts/w23/w23a_identity.py` の写し。型に P2L・P3 を足し、陽性対照は `pd_eval.py` の
`iface_last_params` と同じく界面の最後の層の weight と bias。識別子と PROJ の深さを変えた。`diff` で 5 か所）。学習の経路と同じ
`train_t1b.build_model`・`register_classes`・`set_trainable`・`eval_detection` を使う。4 型 × 4 腕の identity と型ごとの perturb（正解の腕）の 20 件、すべて rc 0。

| 型 | 学ぶ名前・要素 | §3.1 から組んだ集合 | 外を一つ混ぜた集合 | 学習前の出力（4 腕） | 陽性対照（正解の腕、界面の最後の層を N(0, 0.05²)） |
|---|---|---|---|---|---|
| P1 | 376・48,738,080 | 4/4 一致 | 4/4 不一致 | 4/4 差 0（score・box・ラベル）、AP 0.7273450248398429 | AP 0.731952、score の差の最大 0.511、ラベルの不一致 341,484 |
| P2L | 374・48,471,350 | 4/4 | 4/4 不一致 | 4/4 差 0 | AP 0.727179、0.0461、333,821 |
| P3 | 374・48,473,760 | 4/4 | 4/4 不一致 | 4/4 差 0 | AP 0.727251、0.333、276,614 |
| DX | 413・48,681,574 | 4/4 | 4/4 不一致 | 4/4 差 0 | AP 0.727248、0.00701（`phase_iface.alpha`）、166,268 |

評価した動画は全件 {09, 10}（1,515 枚）。

B-4 の前回との照合（`tools/w3lra_scopes.py`、`$A/identity/scopes_vs_prev.json`）:

    $ .venv/bin/python $A/tools/w3lra_scopes.py --out $A/identity/scopes_vs_prev.json
    P1  376 arms_same True opt True {bengio_pd_scopes_P1 (376, True), andrew_identity_{empty,pred_noCF,gt,shuffle} (376, True) ×4}
    P2L 374 arms_same True opt True {bengio_pd_scopes (374, True)}
    P3  374 arms_same True opt True {bengio_pd_scopes (374, True)}
    DX  413 arms_same True opt True {andrew_identity_{empty,pred_noCF,gt,shuffle} (413, True) ×4}
    {'all_equal': True, 'control_all_unequal': True}

- 本契約の集合は型ごとに 4 腕で同じ、B-3 の試走の optimizer の群に入った名前の和集合と同じ、前回の W3 の集合（P1・P2L・P3 は bengio の `taskC/pd_scopes*.json`、
  P1・DX は andrew の `identity/<型>_W3_<腕>.json`）と同じ
- 陽性対照: 本契約の集合に名前を 1 個足すと、すべての前回の集合と一致しない

### G2 の判定（10:53）

信号と checkpoint の要約値が記録と一致し、塔単独の val が差 0.0 で再現し、受け取り手の学習率 1e-5 が optimizer の群に届き（比 0.1 の群は 1e-6）、
界面の群が 5e-4 のままであることを試走の記録から示した。学ぶ集合は前回の W3 と一致し、全腕で学習前の出力が塔単独と一致した。**通過。**

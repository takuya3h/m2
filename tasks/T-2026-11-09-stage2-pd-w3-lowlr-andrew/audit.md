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

## Task C — 学習（10:53:32 起動）

- 起動の直前: `nvidia-smi --query-compute-apps` 0 件。`proc_enum.py` をパイプで受けた数えは 1 件だったが、起動の後にファイル経由（30 件 = 学習 6 本 ＋ DataLoader の worker 24 本）と
  パイプ経由（31 件）を比べ、差の 1 件は数えを受け取る `python3` 自身と確かめた（前回の andrew の契約と同じ。`$S/start/c_launch_procs.json`）
- 起動時の commit 3dc8b512（push 済み。各 run の `code_commit.txt`）。待ち行列 `tools/run_queue.sh`（GPU ごとに `xargs -P 3`、列 `queue/gpu{0,1}.txt` 各 8 本、
  出力 `queue/gpu{0,1}.out`）を `setsid nohup` で切り離して起動
- 最初の巡: GPU 0 に P1 空・P1 正解・P2L 空、GPU 1 に P1 予測-noCF・P1 入れ替え・P2L 予測-noCF
- 監視: 16 本の終了か、train.log・finalize.log の異常（Traceback・溢れ・非数・Killed・RuntimeError）か、rc ≠ 0 で通知する待ちのループ（2 分ごと）
- 点検 11:08: 最初の 6 本とも epoch 0 の 500/4,809 step、約 1.0 it/s（前回の andrew の本番の最初の巡と同じ速さ）。GPU 0・1 とも使用率 100 %、記憶 38,191・38,182 MiB / 49,140 MiB、電力 283・288 W。
  見積もり: 1 本 = 4 × 4,809 step ÷ 1.0 it/s ≈ 5.3 時間 ＋ 評価 5 回 ≈ 6 時間。1 枚 8 本を 3・3・2 本の巡で回すので 6 ＋ 6 ＋ 約 4.5 ≈ 16.5 時間、終了は 11-10 03:00〜04:00 JST 頃
- 終了 11-10 02:37:00（最後の run の `end.txt` 17:37:00 UTC）。待ちのループは「16 本終了」で抜けた（異常の通知 0 件）
  - 16 本とも `exit_code.txt` 0、train.log に非数の出現 0 件、溢れ・発散で止まった run 0 本（`$S/aborted/` は作っていない）
  - 総所要 15 時間 43 分 28 秒（01:53:32〜17:37:00 UTC）。1 本の所要: P1・P2L・P3 は 5.74〜5.85 時間（1 枚 3 本）、DX は 3.99〜4.04 時間（最後の巡で 1 枚 2 本）
  - 巡の実際: GPU 0 は P1 空・P1 正解・P2L 空 → P2L 正解・P3 空・P3 正解 → DX 空・DX 正解、GPU 1 は P1 予測-noCF・P1 入れ替え・P2L 予測-noCF → P2L 入れ替え・P3 予測-noCF・P3 入れ替え → DX 予測-noCF・DX 入れ替え
  - 終了の後: `nvidia-smi --query-compute-apps` 0 件、GPU 0・1 とも電力の上限 300.00 W（`$S/end/gpu_end.csv`）
  - 保存先 `$S` 4,115,274,944 B、run の置き場 16 本 1,217,994,153 B（A-4 の見積もり ≤ 6 GB の中）。W&B は `$S/wandb/wandb/` に offline の run 16 件

## Task D — 集計・検証・報告（11-10 02:37〜）

### D-1 集計（`$A/report.json`、道具 `tools/w3lra_aggregate.py --recompute`、表 `tools/w3lra_report.py` → `report_tables.md`）

前回の andrew の `scripts/w23/w23a_aggregate.py`・`w23a_report.py` を `A/tools/` に写し、型（P1・P2L・P3・DX）と参考の表（前回の W3・W2）を変えた。

    $ PYTHONPATH=src:scripts .venv/bin/python $A/tools/w3lra_aggregate.py --out $A/report.json --recompute   （出力 $A/aggregate.log）
    acceptance_e: expected 16, measured 16, hosts [andrew], unmeasured [], n_epochs_recorded [5]（学習前 ＋ 4 epoch）,
                  lr_by_epoch_all_constant true, control_nonexistent_name_count 0
    acceptance_g: videos_used 01 02 03 06 08 09 10 11 12 13 14 15、overlap []、control_overlap_with_04 ["04"]
    acceptance_f: recompute_max_abs_diff 0.0、recompute_per_video_max_abs_diff 0.0（16 本。epoch 3 の予測 val_*_ep3.json.gz から M.summary で計算し直した値と後処理の記録の差）
    predictions: 1 当たり（4 型とも |Δ塔| が縮んだ）、2 当たり（P1 +0.0125、前回 +0.0333）、3 外れ（P2L −0.0066 → +0.0077、P3 −0.0062 → −0.0005）
    $ python3 $A/tools/w3lra_report.py $A/report.json > $A/report_tables.md   （434 行）

- 前回の W3 の値は SPEC §1 から写さず、前回の各 run の記録（`w23b_pd_<型>-W3_<腕>_ep4_seed42/w23_metrics.json`、`w23a_pd_DX_W3_<腕>_ep4_seed42/w23a_metrics.json`）から
  同じ関数で Δ を計算した。SPEC §1 の表の値（P1 −0.0578 / −0.0703、+0.0333 / +0.0637、+0.0055 / +0.0091、P2L −0.0372 / −0.0436、−0.0066 / −0.0043、−0.0061 / +0.0026、
  P3 −0.0292 / −0.0098、−0.0062 / −0.0131、+0.0010 / +0.0012、DX −0.0327、+0.0145、−0.0104）と小数 4 桁で全件一致
- W2 の参考: P2L は bengio の `w23b_pd_P2L-W2_*`、DX は andrew の `w23a_pd_DX_W2_*`、P1 は直しの契約の `stage2_pilot_fix/report.json` の `tables.P1-W2`、
  P3 は W2 を回していない（W1 と同じ集合。前回 bengio の REPORT §3.1）
- 完了判定 f の陽性対照: P1 正解の記録に P1 空の epoch 3 の予測から計算した値を突き合わせると差 overall −0.012471・標的群 −0.030138・陰性対照群 −0.000255。
  DX 正解の記録に DX 入れ替えの予測を突き合わせると overall +0.000167・標的群 +0.000494・陰性対照群 +0.002224（どちらも 0 でない）
- epoch ごとの overall（学習前 → epoch 1〜4）は `report_tables.md` の各型の表。P1 は 4 腕とも epoch 3 → 4 で −0.0100〜−0.0116 下がった。
  P2L・P3 は −0.0004〜+0.0023、DX は −0.0012〜−0.0018。学習率は 4 epoch で一定（`lr_groups.json` の eval_1〜eval_4 の記録）なので学習率の変化では説明できない。理由は測っていない

### D-1 終了時の試験と仮想環境（`$S/end/`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped, 26 warnings in 29.60s
    $ diff $S/start/a5_fail_names.txt $S/end/fail_names.txt   → 差なし（失敗の名前は開始時と同じ 6 件）
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 108 行 9c7be5c9…、.venv-relation-detr 72 行 a74c9c78…（開始時と一致）

### D-1 禁止の場所の不変

- 材料の照合を終了時にもう一度回した（`$S/end/material_end.json`）: 信号 6 本・検出塔の重み 2 本・設定 4 本・学習のコード 2 本の 14 本の sha256 が開始時と記録の全件で一致。
  陽性対照: 1000 バイト目を反転した複製は不一致、変えない複製は一致
- `git diff --name-status 129e79b0 -- . ':!tasks/T-2026-11-09-stage2-pd-w3-lowlr-andrew' ':!experiments/analysis/stage2_pd_w3_lowlr_andrew' ':!experiments/phase1/w3lra_*'` → 空
  （README.md・docs/experiment_log.md を書く前）。陽性対照: 同じ命令で `experiments/analysis/stage2_pd_w3_lowlr_andrew/tools` を指すと、本契約の新しいファイルが `A` として出る
- `third_party/`・`data/raw`・`data/external`・注釈・凍結源・既存の checkpoint・既存の仮想環境・前回までの契約の run の置き場と保存先は触れていない（上の diff と要約値で確かめた。読むことだけをした）

### D-1 forbidden-check（作業ツリー）

    $ source .venv/bin/activate && make forbidden-check TASK=T-2026-11-09-stage2-pd-w3-lowlr-andrew
    status fail、changed 434、violations 9

違反 9 件はすべて `experiments/analysis/grasp_pilot_converge/tools/`（同期で届いた別の契約の出力。フォルダの mtime 11-09 12:44 JST。本契約は触れていない・動かしていない）。
**本契約の経路の違反 0 件。** 分岐の HEAD の写しでの結果は下に足す

### D-2 README.md・docs/experiment_log.md

両方の末尾に本契約の節を足した（どちらにも「非公式の測定」と明記）。SPEC D-2 の指示で、`allow_write` の外（起票者の誤り self_contradiction）

### D-3 make runindex（03:3x）

    $ source .venv/bin/activate && make runindex
    runs/*.json = 2668, index.csv = 2668 行（起点 2647 から +21）
    [FAIL] C5 per_class.csv の整合 — value 空欄と is_nan が食い違う行: 51（phase1__grasppilot2_G_{H1,H2,all}_seed42 の 17 行ずつ）
    ほかの C1〜C9 は PASS

- 足された 21 行: 本契約の 16 本（`index.csv`・`experiments.csv` に task_id つきで各 16 行）と、起点の版管理に在るが索引に載っていなかった
  別の契約の 5 本（`grasparms_B_{empty,gt}_ep4_seed42`・`graspd2_{gteach_ep15_seed42,shuf_ep15_seed42,smoke}`。どれも `git ls-tree origin/phase0` に在る）
- C5 の FAIL は起点でも同じ: 起点 129e79b0 の写しの作業ツリー（`git worktree add --detach`）で `tools/verify_runindex.py` を回すと同じ 51 行で FAIL。本契約の run は含まない
- 前例（T-2026-11-07-dtower-rerun、利用者の決定）どおり、作り直した runindex 全体を commit する。手では編集していない
- 補足: `.git/info/exclude` の 20・21 行（`grasparms_B_{empty,gt}_ep4_seed42/`）の 2 本は起点の版管理に入った。追跡下のファイルには無視の一覧が効かないので、この 2 行はもう働いていない

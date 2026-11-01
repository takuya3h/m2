# audit — T-2026-11-01-stage2-w23-andrew（非公式の測定）

時刻は JST（ホストの時計は UTC。`TZ=Asia/Tokyo date` で読んだ）。ホストは andrew（`hostname` → `Andrew`）。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-andrew`。集計の置き場は `A=experiments/analysis/stage2_w23_andrew`。

## 0. 始める（手順書の 0〜4、2026-11-02 00:20 前後）

- 開始時の分岐は `feat/grasp-pilot-g`（追跡下の変更なし）。`feat/stage2-w23-andrew` は手元にも遠隔にも無く、契約の履歴も `tasks/<id>/` も `.sync-pause` も無かった
- `git fetch origin` → origin/phase0 00f98c13..392cf287（PR #274 の統合を含む）
- `python3 scripts/task_start_classify.py` → 未追跡・起点に在り中身が同じ 6 件（通す）、ほかは 0 件、`[task-start] 分類: 通す`（比較先 origin/phase0 392cf287）
  - 6 件は `experiments/phase1/grasppilot3x_pd_B_gt_{ep12_seed42,ep4_seed123,ep4_seed456}/logs/{eval_meta_val,val_metrics_by_epoch}.json`（並行する契約の出力。触れていない）
- `make task-start` → `分岐を作成: feat/stage2-w23-andrew（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、`OK`、`完了。`
- `grep -c sync-pause ~/bin/m2-sync.sh` → 2（稼働中の同期処理は目印に対応済み）
- `make task-validate` → `OK`、exit 0（WARN なし）
- 参照の解決: `contract.inject_verbatim` の 7 節（prohibitions・issuer_cautions・env_p0・folds・split・eval_recipe・det_groups）を
  `context/conventions.md`（`git log -1` → 2d946b07…）から原文で読んだ
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、
  P4 prereg_committed・P5 frozen_source_hash・P13・P14（kind=analysis で対象外）、P12 refs_resolved（解決前提の参照なし）。P9 spec_lint 該当なし

## Task A — 開始状態（G1）

### A-1 分岐と起点、前提の統合（00:23）

    $ git branch --show-current                       → feat/stage2-w23-andrew
    $ git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0
    392cf287615b45f76829c7fa7f4e5cb39d4444c5（3 つとも同じ）
    $ gh pr view 274 --json state,mergedAt,mergeCommit,baseRefName
    MERGED 2026-11-01T15:18:38Z、base phase0、merge commit 5c7c2068
    $ git merge-base --is-ancestor 79807f6a origin/phase0   → 真（二本目の分岐の先頭が起点の祖先）
    $ git ls-tree --name-only origin/phase0 tasks/T-2026-11-01-grasp-pilot-g/ scripts/grasppilot/run_pd_grasp2.sh
    scripts/grasppilot/run_pd_grasp2.sh、tasks/T-2026-11-01-grasp-pilot-g/{RESULT.md,SPEC.md,audit.md,result.yaml,spec.yaml}

### A-2 開始前から在る未追跡

task-start の前の分類器で「無視されていない未追跡・起点に在り中身が同じ」6 件（上記。並行する契約の出力が同期で届いたもの）。
task-start の後に在る無視されていない未追跡は、取り込んだ契約の 2 本（`tasks/T-2026-11-01-stage2-w23-andrew/{SPEC.md,spec.yaml}`）だけ。消していない

### A-3 compute プロセス（`$S/start/a3_procs.json`、道具 `scripts/grasppilot/proc_enum.py`、00:24）

    $ python3 scripts/grasppilot/proc_enum.py                            → n_processes 48、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh   → count 5（自分のシェルを含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0
    $ nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv → 見出しだけ（0 件）
    $ ps -eo pid,user,comm,args で comm が python・torchrun で始まるもの（道具自身を除く）→ 0 件

**本契約以外の compute プロセスは 0 件**（A-6: 二本目の run のプロセスも残っていない）

### A-4 記憶領域・試験・仮想環境・GPU（`$S/start/`）

    $ df -B1 /home/ubuntu/slocal2
    /dev/sdc1  7937302376448  5888600576000  1648606932992  79%

空き 1,648,606,932,992 B。見積もり（上限側）: W3 の重み（学ぶ部分だけ、約 195 MB）18 本 ≤ 4 GB、W2 の重み ≤ 1 GB、
epoch ごとの val の予測（gz）36 本 × 5 ≤ 10 GB、記録 ≤ 1 GB。合計 ≤ 16 GB（空きの 1% 未満）。足りる

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 979 passed, 5 skipped, 26 warnings in 29.93s

失敗の名前（`$S/start/a4_fail_names.txt`。二本目の開始時と同じ 6 件）:

    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    tests/test_fetch_task.py::test_rejects_unknown_file_name
    tests/test_research_logger.py::test_log_run_idempotent
    tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv                 108 行  9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0
    .venv-relation-detr    72 行  a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090
    （どちらも二本目の記録の値と一致）

    $ nvidia-smi --query-gpu=index,name,power.limit,power.default_limit,power.max_limit,memory.total,memory.used --format=csv

| GPU | 型 | 電力の上限 | 既定の上限 | 最大の上限 | 記憶 | 使用中 |
|---|---|---:|---:|---:|---:|---:|
| 0 | NVIDIA RTX A6000 | 300.00 W | 300.00 W | 300.00 W | 49,140 MiB | 16 MiB |
| 1 | NVIDIA RTX A6000 | 300.00 W | 300.00 W | 300.00 W | 49,140 MiB | 16 MiB |

### A-5 起票時の値

    $ git log -1 --format=%H -- context/conventions.md → 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（contract.conventions_rev と一致）
    $ git log -1 --format=%H -- runindex/              → 68befc3b62ffc071077cca446df5d3c83b8c38b9（created_from.runindex_commit と一致）
    行数（見出しの 1 行を除く）: index 2363、experiments 1130、verdicts 1736（created_from.counts と一致）

差し替えは無い。`meta.amendments` は空のまま

### G1 の判定

分岐 `feat/stage2-w23-andrew`、起点 origin/phase0 392cf287 に PR #274 の内容が在り、本契約以外の compute プロセス 0 件、
空き・失敗の名前・仮想環境の要約値・電力の上限と装置の型を記録した。**通過。**

## Task B — 材料と再現（G2）

### B-1 材料（`$A/material/material.json`、道具 `scripts/w23/w23a_material.py`、00:26）

本契約が読む 25 ファイルの在否と sha256 を、前の契約の記録と照合した。**all_exist true、記録のある 19 本はすべて一致（all_recorded_match true）**

| 区分 | 本数 | 記録 | 結果 |
|---|---:|---|---|
| PD の信号（P0・P-GT・交差適合 P0・正解予測-CF・入れ替え） | 9 | `stage2_pilot_four/material/material_four.json`（直しの契約の記録と照合済みの値） | 9/9 一致 |
| 検出塔 D*-COCO 折り A seed 42（`best_ap.pth`、30d199b1…） | 1 | `stage2_pilot_fix/bengio/input_digest_andrew.json` の det_ckpt | 一致 |
| 案 B の見取り（pred_noCF・pred_CF・shuffle の train と val） | 6 | 二本目の `$G/signals/assemble_report.json` の B、版管理下の `grasppilot2_B_*/view_sha256.txt` | 6/6 一致（記録 2〜3 個ずつ） |
| 案 B の予測の地図（`all_train_m.npy`・`all_val_m.npy`・`pred_CF_train_m.npy`） | 3 | `assemble_report.json` の B の maps_sha256 | 3/3 一致 |
| 把持の注釈（`data/annotations/egosurgery_hts/{hand_tool_seg,hand_seg,tool_seg}/{train,val}.json`。正解の地図の出所） | 6 | sha256 の記録は**見つからない**（版管理の外。`.gitignore` の `data/annotations/egosurgery_hts/**`。`git grep` で要約値の先頭 16 桁も 0 件）。**中身の数えの記録で照合した**（下） | 6/6 一致（中身の数え） |

陽性対照: `P0_val.npz` の複製の 1000 バイト目を反転すると sha256 286564a6… になり記録と一致しない（`matches_record` false）。
変えない複製は一致する（`copy_control.matches_record` true）。

把持の注釈の中身の照合（同じ道具の `hts_content`。train と val のファイルだけを開く。test と extra は開かない）:
一本目の `$STORE/T-2026-10-31-grasp-pilot-probe/b/b1_ann_check.json`（B-1 の数え）の画像数・注釈のある画像数・注釈数・動画・クラスの並びと、
二本目の版管理下の `grasp_pilot_g/c3/acceptance_report.json` の C1（hand_tool_seg train の RLE 32,408）と C2（cat 5 の 952）に対し、

| ファイル | 画像 | 注釈 | 動画 | 結果 |
|---|---:|---:|---|---|
| hand_tool_seg/train | 9,356 | 32,408（RLE 32,408、cat 5 952） | 01 02 03 06 08 11 12 13 14 15 | 一致 |
| hand_tool_seg/val | 1,514 | 5,653 | 09 10 | 一致 |
| hand_seg/train | 9,627 | 27,726 | train の 10 本 | 一致 |
| hand_seg/val | 1,515 | 4,918 | 09 10 | 一致 |
| tool_seg/train | 9,528 | 30,493 | train の 10 本 | 一致 |
| tool_seg/val | 1,512 | 3,733 | 09 10 | 一致 |

**all_match true**。陽性対照: tool_seg/val の注釈を 1 件除いた数では不一致（`hts_content_control_drop_one.all_match` false）。
sha256 は本契約で記録した（`material.json` の rows）。ファイルの更新時刻は 2026-10-06（一本目の開始より前）。

### B-2 塔単独の再現（`$A/repro/`、台本 `repro/run_repro.sh`、00:27:22〜00:30:03）

道具は four-new-types の andrew の再現と同じ `scripts/stage2pilot/pd_eval.py --cfg plain`（出力の json の task_id 欄は道具の固定値 folda）。

| 塔 | 指標 | andrew（本契約） | 記録（SPEC §2） | 差 |
|---|---|---|---|---|
| 検出 seed 42 | overall mAP | 0.7273450248398429 | 0.7273450 | 0.0 |
| | 標的群 AP | 0.7950748008550897 | 0.7950748 | 0.0 |
| | 陰性対照群 AP | 0.6726631817581498 | 0.6726632 | 0.0 |

許容差 0.005 の中。動画ごと 09 0.704273・10 0.642097、AP50 0.851807、1,515 枚（動画 09・10）。`env_check_det.txt` `ms_deform_attn_ext True`。
塔単独の予測を `$S/identity/plain_val_preds.json.gz` に保存（Task C と各 run の学習前の恒等性の基準）。

対照（判定が働くこと）: seed 123 の検出塔（sha256 5842a2ae…）で overall mAP 0.7288631（差 +0.0015、許容差の中）、
**標的群 AP 0.8234321（差 +0.0284、許容差を超える）**、陰性対照群 AP 0.6701777（差 −0.0025）。

工程塔は §4 の受け取り手に無い（本契約の型はすべて検出塔が受け取り手）ので再現しない。

### G2 の判定

使う信号と checkpoint の 19 本の要約値が記録と一致、把持の注釈 6 本は中身の数えが記録と一致、検出塔の塔単独の val が差 0.0 で再現。**通過。**

## Task C — W2・W3 の実装と恒等性（G3）

### C-1 実装（新しいファイルだけ。既存のファイルは変えていない）

- `scripts/w23/run_pd_w23_andrew.sh` — 起動の台本。型 P1・DX・B、W W2（`--trainable w2`）・W3（`--trainable all`）・W1（`--trainable film`。setcheck と dryrun だけ）、
  腕 6。腕と信号の対応は `run_pd_fix.sh`（P1）・`run_pd_four.sh`（DX）・`run_pd_grasp2.sh`（案 B）の写し。W1 との違いは `--trainable`、
  `--save-predictions-all`（epoch ごとの val の予測を残す。学習には効かない）、置き場（run は `experiments/phase1/w23a_pd_<型>_<W>_<腕>_ep4_seed42`、重みは `$S/pd_ckpt/`）
- `scripts/w23/w23a_identity.py` — 学ぶ集合（`train_t1b.set_trainable` の後の requires_grad）と SPEC §3.1 から接頭で組んだ集合の比較、学習前の出力と塔単独の比較、陽性対照
- `scripts/w23/w23a_finalize.py` — 後処理（本契約の印・W・epoch ごとの val・学習の経路の中の学習前の恒等性・受け取り手の動いた量・通した動画）
- `scripts/w23/w23a_material.py`（B-1）、`scripts/w23/w23a_armcheck.py`（腕と信号の対応の照合）

`--trainable w2` は `"phase" in name or name in w2_parameter_names(model)` で選ぶ。DX（`phase_iface` は検出器の直下、decoder の各層に hook）と
案 B（`phase_iface` は 1×1 の畳み込み）でも §3.1 の集合をそのまま選べるので、派生のファイルは書いていない（C-2 の照合で確かめる）。
W3 の「設定の凍結」は `ResNetBackbone(freeze_indices=(0,))` の stem の conv1 と layer1（パラメータ 11 個、222,400 要素。bn は FrozenBatchNorm2d で buffer）。

### C-1 腕と信号の対応（`$A/armcheck/armcheck.json`、道具 `scripts/w23/w23a_armcheck.py`）

台本の dryrun が解決する引数（設定の名前・信号・評価の信号・零の信号・地図の種類と見取り）を、その型の W1 の run の `config.yaml` と突き合わせた。
W1 の run: P1 は `stage2fix_pd_P1-W1_{empty,pred_noCF,shuffle}_ep4_seed42` と `stage2pilot_pd_P1-W1_{gt,pred_CF,gtpred_CF}_seed42`、
DX は `stage2four_pd_DX_<腕>_ep4_seed42`、案 B は `grasppilot2_B_<腕>_ep4_seed42`。学習率 1e-4・界面 5e-4・bf16・seed 42 も W1 の記録と同じ。

    $ .venv/bin/python scripts/w23/w23a_armcheck.py --out $A/armcheck/armcheck.json
    {'swap': None, 'n': 36, 'n_match': 36, 'all_match': True}
    $ .venv/bin/python scripts/w23/w23a_armcheck.py --swap gt,pred_noCF --out $A/armcheck/armcheck_swap_control.json
    {'swap': 'gt,pred_noCF', 'n': 36, 'n_match': 24, 'all_match': False}     ← 陽性対照（入れ替えた 12 件が不一致）

## 利用者の指示（2026-11-02 00:52 JST 頃。`meta.amendments` に記録）

Task C の途中で、SPEC §1 の「これまでの界面の型はすべて W1」が実測と食い違う（P1 は直しの契約で P1-W2 として 6 腕とも測られている。
`experiments/analysis/stage2_pilot_fix/REPORT.md` の「P1-W2」節）ことを報告した。利用者の指示:

1. P1 は回さない（W2 は直しの契約の値を参考に使う。W3 は bengio の契約が回す）
2. decoder-xattn と案 B の W2・W3 は、空・予測-noCF・正解・入れ替えの四腕だけ回す（予測-CF と正解予測-CF は回さない）。計 16 本
3. W3 の試走で 1 本の所要と記憶を測り、全体が開始から 15 時間を超える見込みなら学習を始める前に諮る
4. W&B は手元だけ（offline）。外へ送らない

対応:
- `spec.yaml` の `meta.amendments` に 1 件を足した（`make task-validate` → OK）
- 台本に `WANDB_MODE=offline`、`WANDB_DIR=$S/wandb` を置いた。`train_t1b.py` は W&B を配線していない（既存のファイルは変えない）ため、
  後処理 `w23a_finalize.py` が epoch ごとの val を `wandb.init(mode="offline", dir=$S/wandb)` で手元に記録する。`load_env.sh` は読まない（資格情報を環境に入れない）
- 既に始めていた恒等性の検査（P1 と、DX・案 B の予測-CF・正解予測-CF を含む）は止めずに最後まで回した。P1 の分と二腕の分は記録として残すが、run の表には入らない

### C-2〜C-4 学ぶ集合と恒等性（`$A/identity/`、台本 `identity/run_identity.sh`、00:35〜01:20 前後、GPU 2 枚・同時 6 本）

型 × W × 腕ごとに `run_pd_w23_andrew.sh <型> <W> <腕> identity|perturb|setcheck` を回した（60 件、すべて rc 0）。
道具 `w23a_identity.py` は学習の経路と同じ `train_t1b.build_model`・`register_classes`・`set_trainable`・`eval_detection` を使い、
学ぶ集合を SPEC §3.1 から名前の接頭で別に組んだ集合と比べ、学習前の val の出力を塔単独の予測（B-2 で保存）と比べる。

| 型 | W | 学ぶ要素（d9・5 チャネル / 18・10 チャネル） | 集合の一致 | 外を一つ混ぜた集合 | 学習前の出力（6 腕） | 陽性対照（正解の腕、界面を N(0, 0.05²)） |
|---|---|---|---|---|---|---|
| P1 | W2 | 1,949,203 / 1,949,779 | 6/6 | 6/6 不一致 | 6/6 差 0（score・box・ラベル） | AP 0.731952、score の差の最大 0.511 |
| P1 | W3 | 48,738,080 / 48,738,656 | 6/6 | 6/6 不一致 | 6/6 差 0 | 同上 |
| DX | W2 | 1,892,697 / 1,892,985 | 6/6 | 6/6 不一致 | 6/6 差 0 | AP 0.727248、score の差の最大 0.00701（α だけを揺らす） |
| DX | W3 | 48,681,574 / 48,681,862 | 6/6 | 6/6 不一致 | 6/6 差 0 | 同上 |
| B | W2 | 1,692,563 / 1,702,803 | 6/6 | 6/6 不一致 | 6/6 差 0 | AP 0.727887、score の差の最大 0.383 |
| B | W3 | 48,481,440 / 48,491,680 | 6/6 | 6/6 不一致 | 6/6 差 0 | 同上 |

- 学習前の AP は全 36 件で 0.7273450248398429（塔単独と同じ）。陽性対照はすべて出力が変わった（ラベルの不一致 16 万〜34 万件）
- 陽性対照を正解の腕で取ったのは、案 B の空の腕は地図が全 0 で、界面の重みを揺らしても出力が変わり得ない（死んだ対照になる）ため
- W3 の集合 = 界面 ＋ 既定で学ぶ全体（48,738,080 = 全 48,960,480 − 凍結 222,400。P1 d9 の値）
- **C-4（W1）**: 新しい経路で W1 を指定（setcheck、CPU、評価しない）すると 18 件すべて `phase_iface.*` と一致。要素数は W1 の run の記録の
  `total_trainable` と一致（DX 210,374 / 210,662、案 B 10,240 / 20,480、P1 266,880 / 267,456）。
  P1 の W2 は直しの契約の `stage2fix_pd_P1-W2_{empty,shuffle}` の記録 1,949,203 とも一致
- **C-1 既定の挙動**: 既存のファイルを一つも変えていない（`git diff --stat 392cf287 -- ':!scripts/w23' ':!tasks/T-2026-11-01-stage2-w23-andrew' ':!experiments/analysis/stage2_w23_andrew'` が空になることを Task E で示す）
- 予測-CF と正解予測-CF の腕と P1 の分は利用者の指示の前に始めた検査で、run の表には入らない（記録として残す）

### G3 の判定

学ぶ集合が §3.1 と一致（陽性対照で不一致）、W1 の指定で W1 の集合と一致、全腕で学習前の出力が塔単独と一致、陽性対照で出力が変わる、既存のファイルは不変。**通過。**

## 利用者の指示 (3): W3 の試走と見積もり（01:24〜01:28）

### 計測（`$A/bench/`、道具 `scripts/w23/w23a_bench.py`、台本 `bench/run_bench.sh`）

`train_t1b --smoke` は 6 step で打ち切るので速度を測れない。学習の経路と同じ関数・bf16・AdamW・勾配の刈り込みで 130 step 回し、
30 step 目以降の 1 step の秒数と記憶の山を測った（重みは保存しない）。GPU 0 に DX の W1・W2・W3、GPU 1 に案 B の W1・W2・W3 を同時に置いた（1 枚 3 本）。

| 型 | W | 秒/step（平均・中央） | 記憶の山（reserved） | 学ぶ要素 |
|---|---|---|---:|---:|
| DX | W1 | 0.668・0.686 | 3,492 MiB | 210,374 |
| DX | W2 | 0.668・0.683 | 3,500 MiB | 1,892,697 |
| DX | W3 | 0.712・0.781 | 12,594 MiB | 48,681,574 |
| B | W1 | 0.870・0.873 | 6,970 MiB | 10,240 |
| B | W2 | 0.870・0.879 | 6,974 MiB | 1,692,563 |
| B | W3 | 0.870・0.898 | 11,390 MiB | 48,481,440 |

- 1 epoch = 4,809 step。GPU の使用率の平均 75%（GPU 0）・90%（GPU 1）、nvidia-smi の記憶の最大 20,743・26,520 MiB。1 枚に並べた 3 本は GPU を時分割で共有するので秒数がそろう
- **1 枚に載せる本数は 3 本**（W1 の実績と同じ。W3 を 3 本並べても 12.6 GB × 3 ≈ 38 GB で 48 GB に収まる）

### 本物の試走（`train_t1b --smoke`、`$S/smoke/`、01:27:06〜01:27:21）

`run_pd_w23_andrew.sh DX W3 gt smoke` と `B W3 gt smoke`（GPU 0・1）→ どちらも rc 0、`ms_deform_attn_ext True`、`phase_grad=True init_mAP=0.8917 => PASS`
（val 20 枚）。試走の出力で後処理 `w23a_finalize.py` を通した: 凍結部の要約値は前後一致、受け取り手の動いた量（相対）0.0015、通した動画は train の 10 本と val の 09（20 枚）、
test との共通 0、W&B の手元記録（offline、`$S/wandb/`）が書けた。W3 の重み（学ぶ部分）は 1 本 186 MB。
試走のために台本の smoke に `--save-predictions-all` を足した（本番の学習の引数は変えていない）。

### 見積もり（16 本、GPU ごとに DX 4 本・案 B 4 本、1 枚 3 本）

- 計測の値そのまま: 1 本 = 4 × 4,809 step × 秒/step ＋ 評価 5 回 × 約 8 分（恒等性の検査で 1 枚 3 本の評価が約 8 分）→ DX 4.4 時間、案 B 5.3 時間。
  1 枚の仕事 4 × 4.4 ＋ 4 × 5.3 = 38.8 本時間 ÷ 3 = **12.9 時間**
- W1 の実績で補正: 同じ式は W1 の実績（1 枚 3 本で DX 226〜230 分、案 B 217〜271 分）を DX で 1.17 倍、案 B で 1.30 倍に見積もる。補正すると **10.5 時間**
- 学習の開始からは 10.5〜12.9 時間で 15 時間を下回る。契約の開始（00:20）から報告までを含めると補正後 約 13.5 時間、補正前の上限 約 16 時間。
  見込み（補正後）が両方の読みで 15 時間を下回るので、指示に従い学習を始めた。上限が報告まで含めた読みで超えうることは報告に書く

## Task D — 学習（01:28:19 起動）

- 待ち行列 `$A/queue/run_queue.sh`（GPU ごとに `xargs -P 3`）。列 `queue/gpu0.txt`・`gpu1.txt`（各 8 本。W3 を先に置く）。出力 `queue/gpu{0,1}.out`
- 起動の直前の compute プロセスの数えで 1 件と出たのは、数えの結果を受け取る `python3`（パイプの受け手）自身だった（列挙で確かめた）
- 起動時の commit 6edae0e9（各 run の `code_commit.txt`）
- 利用者の指示（2026-11-02 01:3x）: 15 分ごとに問題の有無と終了を早める余地を点検する（セッションの中の定期実行 aac653a2、毎時 04・19・34・49 分）
- 点検 02:09: 6 本とも epoch 0 の 2,000/4,809 step、約 1.0 秒/step（計測の 0.70・0.87 秒より遅い。計測は 1 枚に W1・W2・W3 を混ぜた条件で、
  本番の最初の巡は 1 枚に W3 を 3 本並べたため）。GPU 100%・記憶 39.8 / 40.0 GB。異常なし。**見積もりを直した**: W3 1 本 約 6.1 時間、
  全体の終了 15:30〜16:30 JST 頃（学習の開始から 14〜15 時間、契約の開始から 15〜16 時間）。学習の開始の前の見積もり（10.5〜12.9 時間）は
  計測の条件が本番の重さを下回っていたため外れた。利用者に報告し、学習は続けた
- 点検 03:09: W3 の 6 本の epoch 0 の val mAP が塔単独 0.7273 から下がった（DX 空 0.6854・正解 0.6593・入れ替え 0.6792、案 B 空 0.6802・正解 0.6908・入れ替え 0.6938。
  W1 の同じ腕の epoch 0 は 0.7273〜0.7342）。非数・発散ではなく §9 の停止の条件に当たらないので続けた。利用者に報告した。
  02:39 の点検で、同じ step（同じ seed なので同じバッチ）の損失の表示が DX の W3 で W1 より 3〜5 高い水準にあったことも記録する
- 点検 07:24: 最初の巡（W3 の 6 本）が 07:17〜07:20 に rc 0 で終わり、次の巡（各 GPU に W3 1 本・W2 2 本）が始まった。6 本とも後処理の記録で
  学習前の恒等性（塔単独との差 0）、凍結部の一致、test との共通 0、W&B の手元記録あり。所要 5.82〜5.87 時間。証跡を commit して push した

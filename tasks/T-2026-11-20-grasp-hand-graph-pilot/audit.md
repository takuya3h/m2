# audit — T-2026-11-20-grasp-hand-graph-pilot

ホスト andrew（容器の中。`/.dockerenv` が在る）、repo `~/slocal2/m2`、分岐 `feat/grasp-hand-graph-pilot`。時刻は JST。
`$S` = `/home/ubuntu/slocal2/stage2pilot_store`、本契約の保存先 `$O` = `$S/grasp_hand_graph/`（開始時に無く、本契約が作った）。

## 0. 始める（手順書 0〜4）

- 開始時の分岐 `feat/stage2-pd-w3-lowlr-andrew`。`feat/grasp-hand-graph-pilot` は手元にも遠隔にも無く、`tasks/T-2026-11-20-grasp-hand-graph-pilot` の履歴も無い。`.sync-pause` は無い
- 分類器（`scripts/task_start_classify.py`、比較先 origin/phase0 89b9406d）: 追跡下の変更 0、未追跡・起点に在り同じ 9（`experiments/analysis/grasp_pilot_converge/tools/`）、
  未追跡・起点に無い 782 → 「止める」。782 件はすべて禁止領域 `experiments/` の下の 2 フォルダ
  （`experiments/analysis/stage2_pilot_viz/` 673 件 170M、`experiments/analysis/stage2_slides_qual/` 109 件 369M）。どちらも phase0 の追跡 0 件、どの commit にも無い
- 退避（選択肢 1）は対象が 0 件（すべて禁止領域）。利用者の選択「1 で除外に足す」で、上の 2 フォルダを `.git/info/exclude` に注記つきで足した（消さず移さず）。分類は「通す」に変わった
- `make task-start`: 分岐を origin/phase0 89b9406d から作成、`[task-start] .sync-pause を作成`（本契約が置いた目印。中身は task_id と branch の 2 行）、契約を台帳から取り込み `OK`
- `make task-validate`: `OK`（終了コード 0、WARN なし）
- `make task-preflight` 1 回目: 6 PASS / 0 WARN / 7 SKIP / 1 FAIL。FAIL は P6 decisions_answered（未回答 2 件）。
  利用者の回答「両方その都度諮る」（2026-11-20）を `meta.amendments` に記録し `decisions_required` を空にした
- `make task-preflight` 2 回目: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL。SKIP は P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、P4・P5・P13・P14（exp のみ）、P12（解決する参照なし）
- 稼働中の `~/bin/m2-sync.sh` は目印に対応済み（`grep -c sync-pause` = 2）

### 解決された参照（手順書 3）

`contract.inject_verbatim` の 7 節（prohibitions・issuer_cautions・env_p0・folds・split・crossfit・symmetry）は `context/conventions.md`（`git log -1` = 2d946b07）の原文を読んだ。
原文はその版の該当アンカー（`<a id="prohibitions">` 98 行〜、`env_p0` 109 行〜、`issuer_cautions` 154 行〜、`folds` 297 行〜、`split` 12 行〜、`crossfit` 457 行〜、`symmetry` 367 行〜）にあり、要約せずに従う。
denominator・frozen_source・sigma_policy の参照は無い。`inputs.data.split_files`（`data/splits/ego_val.txt`）は SPEC §0 のとおり参照しなかった（使う分割は conventions#folds の折り A）。

## Task A — 開始状態（G1）

記録の原本は `$O/start/`。

### A-1 分岐・起点・前提の道具（`$O/start/a1.txt`、2026-11-20 14:23 JST）

    $ git branch --show-current; git rev-parse HEAD; git merge-base HEAD origin/phase0; git rev-parse origin/phase0
    feat/grasp-hand-graph-pilot
    89b9406dcf8577e894d2c0c030cb4484b5012de3（3 つとも同じ。origin/phase0..HEAD は 0 件）
    $ git log --oneline origin/phase0 | grep "Merge pull request #309|#307|#295"
    a1cae664（#309 grasp-pilot-converge）、26722ffd（#307 grasp-roitoken-transition-pilot）、#295 も 1 件
    $ git ls-tree --name-only origin/phase0 -- dp_train.py dp_model.py g5_train.py g5_signals.py g5_build.py g5_flip_test.py proc_enum.py
    7 件すべて在る
    $ git show origin/phase0:scripts/stage2pilot/dp_train.py | grep -c '"--converge"|"RT": (|"TW": ('   → 3
    $ git show origin/phase0:scripts/stage2pilot/dp_model.py | grep -c 'class RoiTokens|class TransWindow'  → 2

### A-2 開始前から在る未追跡

- 0. の分類のとおり。起点と同じ中身の 9 件（`experiments/analysis/grasp_pilot_converge/tools/`）と、除外に足した 2 フォルダ（782 件）。どれにも触れていない
- 本契約の置き場は開始時に空: `experiments/phase1/grasp_hand_graph_*` 0 件、`experiments/analysis/grasp_hand_graph*` 0 件、`$O` は無い

### A-3 compute プロセス（`$O/start/a3_procs.json`、`a3_a4_a6.txt`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 37、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh            → count 6
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0
    $ nvidia-smi --query-gpu=index,memory.used ...; nvidia-smi --query-compute-apps=...
    GPU 0・1 とも 16 MiB 使用、0 %、compute の行 0 件（容器の外の使用者も見えない。全体の使用量とプロセスの一覧の差は 0）
    $ nvidia-smi -i 7 --query-compute-apps=pid   → No devices were found（存在しない GPU の番号）

### A-4 保存先の空き（`$O/start/a4_df.txt`）

    $ df -B1 /home/ubuntu/slocal2
    Available 1,578,110,177,280 B（使用 80%）

### A-5 試験と仮想環境（`$O/start/a5_pytest_start.txt`・`a5_fail_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped（34.51 s）
    失敗の名前: test_engines::test_mmdet_trainer_eval_recipe_in_metrics、test_fetch_task::test_rejects_unknown_file_name、
      test_research_logger の 4 件（test_log_run_idempotent、test_run_logging_invokes_log_run_on_finally、
      test_run_logging_no_double_post_on_normal_exit、test_run_logging_swallows_exception_in_user_block）
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0（108 行）
    .venv-relation-detr a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090（72 行）
    （T-2026-11-05-grasp-tower-rebuild の A-5 の値と一致）

### A-6 GPU（`$O/start/a6_gpu_power.csv`）

    0, NVIDIA RTX A6000, 300.00 W（既定 300.00 W、最大 300.00 W）
    1, NVIDIA RTX A6000, 300.00 W（既定 300.00 W、最大 300.00 W）

### A-7 契約の版（`$O/start/a7.txt`）

- `contract.conventions_rev` 2d946b07 = `git log -1 -- context/conventions.md`（2d946b07）
- `meta.created_from.runindex_commit` b524173e = `git log -1 -- runindex/`（b524173e）。件数（`csv.DictReader`、見出し行を除く）index 2,647・experiments 1,327・verdicts 1,977 で一致
- 起票者は「測れていない」と書いたが、実測で食い違いが無いので差し替えない（`meta.amendments` に足していない）

### A-8 前提の材料（SPEC §1.3。`$O/start/a3b_materials.txt`）

| 材料 | 在否 | 要約値・照合 |
|---|---|---|
| 工程塔の時間ヘッド `$S/T-2026-10-18-stage2-pilot-folda/efros_ptower/.../stage1_ptower_20_009_.../checkpoints/best.pth` | 在る | 0d76d446…6ad6d。前回の run（`grasprc_tw_036_...`）の config の head_sha256 と一致 |
| 特徴のキャッシュ `.../p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz` | 在る | c402e214…172da。同 cache_sha256 と一致 |
| 検出塔の上位 300、val（確定）`signals/final/pred_val_top300.json` | 在る | 172,962,966 B、454,500 行（= 1,515 × 300） |
| 同 train（交差適合の半分）`signals/cf_det_from_H1/`・`cf_det_from_H2/pred_train_top300.json` | 在る | 638,816,639 B・466,795,637 B |
| 同 train（確定。noCF の腕に要る）`signals/final_recheck/pred_train_top300.json` | 在る | 1,107,823,434 B |
| **G の入力の写し `$S/inputs/`** | **無い** | `$S/inputs` も `$S/T-2026-11-05-grasp-tower-rebuild/inputs` も無い。andrew の 11-05 の保存先には `g/ann/`（g5_train・g5_val・g5_summary）と start・flip・smoke などだけで、G の重みと信号は無い |
| COCO instance の重み（11-05 が `$S/inputs/coco/` に写した原本） | 原本は在る | `$S/T-2026-10-31-grasp-pilot-probe/e/weights/mmdet/mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth` の sha256 41b088b62838c986…de06879（`g_train.WEIGHT_SHA256` の先頭 41b088b62838c986 と一致） |
| 把持の注釈 `data/annotations/egosurgery_hts/hand_tool_seg/{train,val}.json` | 在る | 5 クラス。train 9,356 フレーム、val 1,514。器具 3・4・5 の同じフレームの重なり 0 件 |
| 手の注釈 `data/annotations/egosurgery_hts/hand_seg/{train,val}.json` | 在る | 4 クラス（1 自分の左手、2 自分の右手、3 他者の左手、4 他者の右手）。train 9,627 フレーム（術具の 9,657 のうち 30 欠落）、val 1,515。欠落の印（loss_mask）の一覧は無い |

- 自分の手の同じ側に複数のインスタンスを持つフレーム（SPEC §1.2 の未測定の前提）: train 左 45・右 61、val 左 14・右 4。他者の手は train 651・360、val 88・87
- 11-05 の G（bengio）の学習の最大確保は 25,634,898,432 B（batch 8・bf16）。RTX A6000（49,140 MiB）に 2 本は載らないので、塔は GPU ごとに 1 本ずつ回す見込み
- `g5_train.py` は COCO の重みを `$S/T-2026-11-05-grasp-tower-rebuild/inputs/coco/…` に決め打ちしており、andrew ではそのままでは塔を学べない

### A-9 W2・W3 の学習率の写し（SPEC §6）

型 TW の W2・W3（T-2026-11-09-grasp-roitoken-transition-pilot）の run の記録 `experiments/phase1/grasprt_tw_030_TW-W3-a-L8-K64_pred_CF_ep4_seed42/config.yaml` から写した値:

    stop_rule.lr 0.0005、stop_rule.weight_decay 0.01（界面）
    receiver_optim: lr 0.0005、weight_decay 0.01、optimizer AdamW（界面と別の群）
    学ぶ範囲: W2 = 界面 ＋ head.refine_stages の最後の要素、W3 = 界面 ＋ head 全体（dp_train.apply_scope。時間ヘッドは eval、dropout なし）

`dp_train.py` の定数 `STOP`（lr 5e-4、weight_decay 0.01）・`RECEIVER`（lr 5e-4、weight_decay 0.01）と一致する。収束規則は `CONVERGE`（patience 8、lr_factor 0.1、max_epochs 120、min_delta 1e-4）

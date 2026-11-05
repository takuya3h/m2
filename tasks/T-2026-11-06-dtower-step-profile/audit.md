# audit — T-2026-11-06-dtower-step-profile

時刻は UTC で記録し、括弧内に JST を添える。計測の生の出力は版管理の外
`/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-step-profile/`（以下 `$STORE`）に在る。
道具は `experiments/analysis/dtower_step_profile/tools/`。

## 0. 開始（手順書 0〜4）

- ホスト名 `Andrew`。開始時の分岐は `feat/tower-batch-probe`。`feat/dtower-step-profile` は手元にも遠隔にも無く、`tasks/T-2026-11-06-dtower-step-profile` の履歴も無い。`.sync-pause` は無い
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 271cf8c0）: `未追跡・起点に無い: 1 件`、`止めた理由 [未追跡・起点に無い] run_ptower_search.log`、`分類: 止める`
  - `run_ptower_search.log` は repo 直下、0 bytes、mtime 2026-11-05T17:21:03Z（11-06 02:21:03 JST）で、禁止領域に属さない。`lsof` で開いている処理は無い
  - 前の契約 T-2026-11-06-tower-batch-probe の工程塔の起動で、Hydra が作ったもの（同契約の audit §5）
- 利用者の選択 1（退避）に従い、**`~/m2-evacuated/T-2026-11-06-dtower-step-profile/run_ptower_search.log` へ移した**（`mv -n`、経路の階層を保つ。消していない）。退避の一覧はこの 1 件だけ。戻すかどうかは報告の後に利用者へ確かめる
- 移した後、`git status --porcelain --untracked-files=all` は空
- `make task-start`（一度だけ）: `分類: 通す`、`分岐を作成: feat/dtower-step-profile（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、契約の取り込みは `OK`、`[task-start] 完了。`
- `.sync-pause` の中身: `task_id=T-2026-11-06-dtower-step-profile` / `branch=feat/dtower-step-profile`
- `make task-validate`: `OK`、exit 0、WARN なし
- 参照の解決（A-5）
  - `contract.conventions_rev` = `context/conventions.md` の最終 commit `2d946b07a57abebc4a8f66150d6dbaf2ccd22186`（一致）
  - `meta.created_from.runindex_commit` = `runindex/` の最終 commit `68befc3b62ffc071077cca446df5d3c83b8c38b9`（一致）
  - 行数（見出しを除く）は index 2363・experiments 1130・verdicts 1736（一致）
  - **`meta.amendments` は空のまま**
- `make task-preflight`: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0
  - SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、P4・P5・P13・P14（kind=analysis）、P12（解決前提の参照なし）
  - P9 spec_lint は「規則 9 件を検査し該当なし」

## 1. Phase A — 開始状態（2026-11-05T19:57Z = 11-06 04:57 JST 前後）

### A-1 分岐と起点

- `git branch --show-current` = `feat/dtower-step-profile`
- `HEAD` = `origin/phase0` = `git merge-base HEAD origin/phase0` = `271cf8c0d1b28eded421bf5b1b13a3c1808d876f`
- PR 290 の内容が起点に在る: `git ls-tree -r --name-only origin/phase0` で次を確かめた
  - `tasks/T-2026-11-06-tower-batch-probe/` の 5 ファイル（RESULT.md・SPEC.md・audit.md・result.yaml・spec.yaml）
  - `experiments/analysis/tower_batch_probe/` の 9 ファイル（REPORT.md・levels.json・tools/ の 7 本）
  - 履歴には `7f7d6ea5 Merge pull request #290 from takuya3h/feat/tower-batch-probe`

### A-2 開始前から在る未追跡

- task-start の前は 1 件（`run_ptower_search.log`、上の §0 で退避）
- task-start の後に在る未追跡は、取り込んだ `tasks/T-2026-11-06-dtower-step-profile/{spec.yaml,SPEC.md}` と、本契約の道具だけ

### A-3 andrew の compute プロセス（19:57:18Z）

道具 `tools/procs.py`（PR 290 の写し）は、`/proc/PID/exe` を解決して、既定の実行ファイルと**完全一致**するものを選ぶ。

- 既定の実行ファイルは `.venv/bin/python`、`.venv-relation-detr/bin/python`、`/usr/bin/python3` の realpath
- `--arg` を渡すと、argv の要素の完全一致も要る

| 呼び方 | 件数 | 出力 |
|---|---|---|
| 既定 | **0**、nvidia-smi の compute プロセス 0 | `$STORE/A/procs_default.json` |
| 陽性対照 `--exe /usr/bin/bash --arg probe_self_marker_8842`（自分のシェルから `bash -c 'sleep 25; true' probe_self_marker_8842 &` を起こして） | **1**（argv `['bash','-c','sleep 25; true','probe_self_marker_8842']`） | `$STORE/A/procs_ctrl_pos.json` |
| 部分一致の対照 `--arg probe_self_marker_884` | 0 | `$STORE/A/procs_ctrl_substr.json` |
| 陰性対照 `--exe /nonexistent/zzz_no_such_exe` | 0 | `$STORE/A/procs_ctrl_neg.json` |
| G1 の直前（試験の後、20:28:27Z） | **0**、nvidia-smi 0 | `$STORE/A/procs_g1.json` |

### A-4 記憶領域・装置・試験・仮想環境（`$STORE/A/host_state.txt`）

- 記憶領域の空き（`df -B1`）: `/home/ubuntu/slocal2`（/dev/sdc1）は 1,644,104,179,712 bytes、`/` は 1,493,667,704,832 bytes
- 装置: NVIDIA RTX A6000 × 2（49140 MiB）、driver 595.84、PCI 00000000:01:00.0 と 00000000:17:00.0、組は PHB
- CPU: 論理 32（`nproc`、AMD Ryzen 9 7950X、16 コア × 2 スレッド、1 ソケット）。主記憶 100,259,065,856 bytes
- 電力の上限: 両 GPU とも power.limit 300.00 W（既定 300.00 W、最大 300.00 W）
- 開始時の GPU: 両方 16 MiB、使用率 0 %
- 要約値（`tools/digests.py`、`$STORE/A/digests_before.json`、19:57:38Z）
  - 取り方: 各経路の全ファイルを内容の sha256 で取り、(相対経路, 大きさ, sha256) の並びをさらに sha256 にした値
  - 仮想環境は、`uv pip freeze` を並べ替えた一覧の sha256 と、site-packages の同じ要約で取った
  - 経路は PR 290 の 16 経路に `experiments/analysis/tower_batch_probe` を足した 17 経路

| 対象 | files | 要約値（先頭 12 桁） |
|---|---|---|
| `third_party` | 319 | `2e4de92b9b10` |
| `data/raw/ego` | 25902 | `a19c4a819260` |
| `data/raw/OpenSurgery_Dataset/01_frames/initial_videos` | 27535 | `aa4c1c6e748d` |
| COCO の重み `relation_detr_resnet50_800_1333_coco_1x.pth` | 1 | `f68913a5abf4` |
| `data/annotations/egosurgery_tool_folds` | 16 | `5c46a6de5d31` |
| `data/processed/phase_manifest_all_phase` | 4 | `52dd18581674` |
| `experiments/analysis/tower_reselect_search_dlsta` | 33 | `191608de9472` |
| `experiments/analysis/tower_batch_probe` | 9 | `76819b80eb85` |
| `configs/detector_relation_detr/train_search.py` | 1 | `640649e1f7ee` |
| scripts 7 本と `configs/stage1_ptower_r3.yaml` | 各 1 | JSON に在る |
| 凍結源 `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth` | 1 | ファイルの sha256 `03936318…75e824`、195,421,066 bytes |
| `.venv` の freeze（108 行） / site-packages | 34123 | `f6c43729f527` / `cfb4f4f7e477` |
| `.venv-relation-detr` の freeze（72 行） / site-packages | 21257 | `d072487642c0` / `f79c8309cada` |

- 開始前の試験（19:57:38Z〜20:28:15Z、30 分 34 秒）
  - 命令: `PYTHONPATH=src python -m pytest tests/ -q -p no:cacheprovider --junitxml=$STORE/A/pytest_before.xml`
  - 結果: **7 failed, 989 passed**、rc=1
  - 失敗の名前（`$STORE/A/pytest_before_failed.json`）は 7 件で、PR 290 の開始前と同じ集合である
    - `tests.test_engines::test_mmdet_trainer_eval_recipe_in_metrics`
    - `tests.test_fetch_task::test_rejects_unknown_file_name`
    - `tests.test_research_logger` の 4 件（`test_log_run_idempotent`・`test_run_logging_invokes_log_run_on_finally`・`test_run_logging_no_double_post_on_normal_exit`・`test_run_logging_swallows_exception_in_user_block`）
    - `tests.test_stage1_ptower_r3_dist::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail`

### A-5 G1

- **G1: pass**
  - 分岐 `feat/` で起点 origin/phase0 = HEAD。PR 290 の内容が起点に在る
  - 本契約以外の compute プロセスは 0 件（対照は 1 / 0 / 0）
  - 空き・失敗の名前・両仮想環境の要約値・電力の上限 300 W を記録した

## 2. 測り方（Phase B）

- 実行器 `tools/run_level.py <1..8>`（SPEC §2.1 の番号）
  - 起動の前に、全 GPU の記憶が 100 MiB 以下で、compute プロセスが 0 件（自分の PID を除く）であることを確かめ、満たさなければ拒む
  - nvidia-smi を 200 ms ごとに `nvsmi.csv` へ採る
  - 終了後に作業場所の重みのファイル（`.pth` `.pt` `.safetensors` `.bin` `.ckpt` と `checkpoint*` の下）を数える
- 共通の環境
  - `WANDB_MODE=offline` で、`WANDB_DIR` は作業場所
  - `PYTHONDONTWRITEBYTECODE=1`、`PYTORCH_CUDA_ALLOC_CONF` は外す
  - `TOWER_SEARCH_TASK=T-2026-11-06-dtower-step-profile`、`TOWER_SEARCH_OBSERVER=tools/observer.py`
  - 探索の検出塔の環境: `DTOWER_LR=0.0001`、`DTOWER_WEIGHT_DECAY=0.0001`、`DTOWER_MAX_NORM=0.1`、`TOWER_SEARCH_POINT=0`、`EGO_ROOT`、`EGO_ANN_DIR=…/egosurgery_tool_folds/A`、`RELDETR_COCO_CKPT`
  - これに `TOWER_SEARCH_CONTROL_STEPS=81`、`PROBE_BATCH_SIZE`、`PROBE_NUM_WORKERS`、`PROBE_NO_LOAD` を足した
  - 命令は `source scripts/load_env.sh` の後に起動した
- 命令（cwd `third_party/Relation-DETR`、`.venv-relation-detr`）: `accelerate launch {--multi_gpu --num_processes 2 --main_process_port 29801 | --num_processes 1} scripts/train_relation_detr_search.py --config-file $STORE/config/train_search_profile.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36`
  - 2 プロセスは `CUDA_VISIBLE_DEVICES=0,1` と `NCCL_P2P_DISABLE=1`、1 プロセスは `CUDA_VISIBLE_DEVICES=0`
  - accelerate の既定の設定ファイル（`~/.cache/huggingface/accelerate/`）は無い
- 設定の写し（`tools/make_det_config.py`、差分は `$STORE/config/diff.txt`）: 原本と違うのは次の 2 行だけである
  - `-batch_size = 2` / `+batch_size = int(os.environ["PROBE_BATCH_SIZE"])`
  - `-num_workers = 4` / `+num_workers = int(os.environ["PROBE_NUM_WORKERS"])`
- 観測器 `tools/observer.py`（実装を読んで決めた口。詳細はファイルの冒頭）
  - モデルの順伝播の前と後の hook、criterion の前の hook、`HungarianMatcher` の前と後の hook を差し込んだ
  - `util.engine.DataPrefetcher`（モジュールの global）を包んだ
  - `accelerator.backward`・`accelerator.reduce`・`optimizer.step` は、インスタンスの属性を包んだ
  - `hungarian_matcher.linear_sum_assignment` と `torch.distributed.all_reduce` も包んだ
  - 各境界で `torch.cuda.synchronize()` の前後の時計を記録し、記録は最後に一度だけ書く
  - `optimizer.step` は `types.MethodType` で束縛した。epoch 0 の `LinearLR` が `optimizer.step` を `__self__` / `__func__` で包むため（`torch/optim/lr_scheduler.py` 50〜75 行）
  - ファイル・既定の挙動・third_party は変えていない
- 読み込み無し（`PROBE_NO_LOAD=1`）
  - `DataPrefetcher` を、rank の batch sampler（`loader.batch_sampler`、accelerate の `BatchSamplerShard`）の最初の batch を主プロセスで組んで GPU に置く類に置き換えた
  - DataLoader は回さない
  - `prepare_targets` は targets を deepcopy するため（`models/detectors/base_detector.py` 178〜188 行）、同じ batch を繰り返しても入力は書き換わらない。batch の和は始めと終わりで一致した
- 集計: `tools/summarize.py`（歩 21〜80）、`tools/derive.py`（水準の差）

## 3. Phase B — 計測（2026-11-05 20:28〜20:39Z = 11-06 05:28〜05:39 JST）

| 水準 | 開始 (UTC) | status / rc | 壁時計 | 重み | 備考 |
|---|---|---|---|---|---|
| L1_b2_p2_w4_load | 20:28:31 | exited / 0 | 60 s | 0 | 両 rank で `CONTROL_COMPLETE` |
| L2_b4_p2_w4_load | 20:29:52 | exited / 0 | 83 s | 0 | 同上 |
| L3_b2_p2_w8_load | 20:31:22 | exited / 0 | 81 s | 0 | 同上 |
| L4_b2_p2_w16_load | 20:32:50 | exited / 0 | 122 s | 0 | 同上 |
| L5_b2_p1_w4_load | 20:34:59 | exited / 0 | 55 s | 0 | `CONTROL_COMPLETE` 1 行 |
| L6_b4_p1_w4_load | 20:36:01 | exited / 0 | 77 s | 0 | 同上 |
| L7_b2_p2_w4_noload | 20:37:25 | exited / 0 | 33 s | 0 | 両 rank |
| L8_b4_p2_w4_noload | 20:38:06 | exited / 0 | 57 s | 0 | 両 rank |

- 起動の失敗は無い（各水準一度ずつ）
- 各水準の前の GPU 0・1 は 16 MiB で、compute プロセスは 0 件（`run.json` の `before`）
- 記録した値（各 rank の DataLoader）
  - `num_workers` は 4・4・8・16・4・4・4・4、`batch_sampler.batch_size` は 2・4・2・2・2・4・2・4
  - `num_processes` は 2・2・2・2・1・1・2・2、模型の型は DDP / RelationDETR（1 プロセス）
  - 1 epoch の歩数は 2405・1202・2405・2405・4809・2404・2405・1202、データセットは 9,618 フレーム
- COCO の重み: 各水準の学習ログに `[RANK 0] load pretrained from …/relation_detr_resnet50_800_1333_coco_1x.pth` が 1 行在る。`initialization_rank*.json` は全 rank で `matched: true`、596 テンソル、`source_sha256 2d2c19a7a49e…`
- 全 rank で次を記録した: `ms_deform_attn_cuda_ext_loaded: true`、`mixed_precision: fp16`、`alloc_conf: None`、SyncBatchNorm 0 個
- 各歩でモデルに渡った枚数: 全水準・全 rank で、81 回の入りの集合が {batch}。80 歩の合計が batch × 80
- 読み込み無しの batch
  - L7: rank 0 は番号 [4752, 9180]、rank 1 は [6430, 8276]
  - L8: rank 0 は [4752, 9180, 1150, 3732]、rank 1 は [5777, 2155, 4562, 6240]
  - 画像の和と box の和は、始めと終わりで全 rank 一致した
- 水準 1 の一歩: 0.3905 s（歩 21〜80）。直前の計測は 0.3915 s（同期なし、歩 11〜60）
- ログの `raise ValueError("Search never evaluates test")` の行は、`default_setup` が設定ファイルの中身を表示したもの（stdout.log 87 行の `Contents of args.config_file=` 以下）で、例外ではない

## 4. Phase C — 検証

- 集計
  - `summarize.py --out $STORE/levels.json --md $STORE/tables.md --steps-dir $STORE/steps` を回した
  - 写しを `experiments/analysis/dtower_step_profile/{levels.json,tables.md,steps/}` に置いた
  - `steps/` は水準・rank ごとに 80 行（見出しを除く）の 14 ファイル
- 見込みの計算し直し: `summarize.py` が各 rank で「歩数 × 平均 − 見込み」< 1e-9 を、実の歩数と換算の歩数の両方で assert して通った
  - `derive.py` は「1 プロセスの epoch − 2 プロセスの epoch = 2 倍の歩数の分 − 同期の分」を assert して通った
- 内訳の和: 全水準・全 rank で、残り = 損失の和 + zero_grad + 末尾 が成り立つ（最大の差 0.0）
- 同期を入れない時計の場合に当たる値（各部分の終わりの同期の前の時計で取った和）: 水準 1 の rank 0 で 0.3542 s（同期ありの 1〜5 の和 0.3841 s、一歩 0.3905 s）
- 読み込み無しの読み込みの待ち: 4.8〜5.5 × 10⁻⁶ s/歩（L7・L8 の全 rank）
- test 不使用
  - 全 8 水準で、読んだ動画と {04,05,07} の共通は 0 件
  - 陽性対照 `--inject-video 04` を足すと、全 8 水準で共通が 1 件になる（`levels_inject04.json`）
- 事後の要約値（`$STORE/A/digests_after.json`、20:42:27Z）: `digests_before.json` と、roots 17 項目・凍結源・両仮想環境（freeze と site-packages）がすべて一致した
- 要約値の道具の陽性対照（scratchpad に `configs/stage1_ptower_r3.yaml` を写した 1 ファイルの場所）
  - 写したままは `63b6958c2988`（原本の行と同じ値）
  - 新しいファイルを足すと `b54463479e52`、その中身を 1 文字変えると `57381016e080`
- `py_compile` と、道具を import した対照で、`tools/__pycache__/` ができた（git では無視される）
  - 最初の `rm -r` は対話の確認で消えず、後で `rm -rf` で消した。commit していない
- 事後の試験・forbidden-check・L1 と L2 の検証は §5 に記録する

## 5. 送出の前の検査

- 事後の試験（20:42:41Z〜21:13:17Z、30 分 33 秒）: 命令は開始前と同じ。**7 failed, 989 passed**、rc=1
  - 失敗の名前の集合は開始前と同じ（新規 0、消えた 0。`$STORE/A/pytest_after_failed.json`）
- 仮想環境の要約値: 事後（§4）で両仮想環境の freeze と site-packages が開始前と一致した
- `make task-validate TASK=T-2026-11-06-dtower-step-profile`（L1 + L2）: `OK`、exit 0（報告を書いた後にもう一度回す）
- `make forbidden-check TASK=T-2026-11-06-dtower-step-profile`: `status: pass`、`violations: []`
  - changed 29。うち本契約の置き場の 26 件が `allow_write experiments/analysis/dtower_step_profile` で permitted
  - 本契約の新しいファイル（道具 7 本・REPORT・表・集約・歩ごとの表 14 本）がすべて変更として検出された
- 追跡下の変更は `README.md` と `docs/experiment_log.md` の追記だけ（本契約の記録）

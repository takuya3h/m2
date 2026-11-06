# audit — T-2026-11-06-tower-batch-probe

時刻は UTC で記録し、括弧内に JST を添える。計測の生の出力は版管理の外
`/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-tower-batch-probe/`（以下 `$STORE`）に在る。
道具は `experiments/analysis/tower_batch_probe/tools/`。

## 0. 開始（手順書 0〜4）

- ホスト名 `Andrew`。開始時の分岐 `feat/grasp-tower-rebuild`、作業ツリーは清浄（`git status --porcelain --untracked-files=all` が空）
- `feat/tower-batch-probe` は手元にも遠隔にも無く、`tasks/T-2026-11-06-tower-batch-probe` の履歴も無い。`.sync-pause` は無い
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 89fe4a41）: 7 区分すべて 0 件、`分類: 通す`
- `make task-start`: `分岐を作成: feat/tower-batch-probe（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、契約の取り込み OK、`[task-start] 完了。`
- `.sync-pause` の中身: `task_id=T-2026-11-06-tower-batch-probe` / `branch=feat/tower-batch-probe`
- 稼働中の `~/bin/m2-sync.sh` の `grep -c sync-pause` は 2（対応済み）
- `make task-validate`: `OK`、exit 0
- 参照の解決: `contract.conventions_rev` = `context/conventions.md` の最終 commit `2d946b07…`（一致）。`meta.created_from.runindex_commit` = `runindex/` の最終 commit `68befc3b…`（一致）。行数 index 2363・experiments 1130・verdicts 1736（見出しを除く。一致）。**`meta.amendments` は空のまま**
- `make task-preflight`: 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。SKIP は P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、P4・P5・P13・P14（kind=analysis）、P12（解決前提の参照なし）。P9 spec_lint は該当なし

## 1. Phase A — 開始状態（2026-11-05T16:31Z 前後 = 11-06 01:31 JST）

### A-1 分岐と起点

- `git branch --show-current` = `feat/tower-batch-probe`
- `git merge-base HEAD origin/phase0` = `git rev-parse origin/phase0` = `HEAD` = `89fe4a417e51ddc830e275ff8cd718a475ad36ba`

### A-2 開始前から在る未追跡

- task-start の前: 0 件（分類器の「未追跡・起点に無い: 0 件」、`git status --porcelain --untracked-files=all` が空）
- task-start の後に在る未追跡は、取り込んだ `tasks/T-2026-11-06-tower-batch-probe/{spec.yaml,SPEC.md}` と本契約の道具だけ

### A-3 andrew の compute プロセス

道具 `tools/procs.py`: `/proc/PID/exe` を解決し、既定の実行ファイル（`.venv/bin/python`、
`.venv-relation-detr/bin/python`、`/usr/bin/python3` の realpath）と**完全一致**するものを選ぶ。
`--arg` があれば argv の要素の完全一致も要る。自分の PID は除き、除いた PID を出力に書く。
nvidia-smi の compute プロセスも併記する。

| 呼び方 | 件数 | 出力 |
|---|---|---|
| 既定（16:31:36Z） | **0**、nvidia-smi の compute プロセス 0 | `$STORE/A/procs_default.json` |
| 陽性対照 `--exe /usr/bin/bash --arg probe_self_marker_7731`（`bash -c 'sleep 20; true' probe_self_marker_7731 &` を起こして） | **1**（argv `['bash','-c','sleep 20; true','probe_self_marker_7731']`） | `$STORE/A/procs_ctrl_pos.json` |
| 部分一致の対照 `--arg probe_self_marker_773` | 0 | `$STORE/A/procs_ctrl_substr.json` |
| 陰性対照 `--exe /nonexistent/zzz_no_such_exe` | 0 | `$STORE/A/procs_ctrl_neg.json` |

陽性対照の一度目は `bash -c 'sleep 20'` で取り、**0 件**だった。bash が単一の命令を exec で置き換え、
bash のプロセスが残らないためである（命令を二つにした二度目で 1 件）。道具の欠陥ではなく対照の作り方の誤り。

### A-4 記憶領域・試験・仮想環境・装置

- 記憶領域: `/home/ubuntu/slocal2`（/dev/sdc1）空き 1,644,111,155,200 bytes（`df -B1`）。`/` は 1.4 TB 空き
- 装置: NVIDIA RTX A6000 × 2（49140 MiB）、driver 595.84、PCI 01:00.0 と 17:00.0、組は PHB、論理 CPU 32
- 電力の上限: 両 GPU とも power.limit 300.00 W（既定 300.00 W、最大 300.00 W）
- 開始時の GPU: 両方 16 MiB、利用率 0 %
- 要約値（`tools/digests.py`、`$STORE/A/digests_before.json`）: 各経路の全ファイルを内容の sha256 で取り、
  (相対経路, 大きさ, sha256) の並びをさらに sha256 にした値。仮想環境は `uv pip freeze` の並べ替えた一覧の sha256 と site-packages の同じ要約

| 対象 | files | sha256 |
|---|---|---|
| `third_party` | 319 | `2e4de92b…44901` |
| `data/raw/ego` | 25902 | `a19c4a81…7e0d8` |
| COCO の重み `relation_detr_resnet50_800_1333_coco_1x.pth` | 1 | `f68913a5…398ed` |
| `data/annotations/egosurgery_tool_folds` | 16 | `5c46a6de…34696` |
| `data/processed/phase_manifest_all_phase` | 4 | `52dd1858…c3893` |
| `experiments/analysis/tower_reselect_search_dlsta`（点の表を読む） | 33 | `191608de…535ac0` |
| 凍結源 `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth` | 1 | `03936318…75e824`（conventions#frozen_source の正本と一致、195421066 bytes） |
| `.venv` の freeze（108 行） | — | `f6c43729…124a8265` |
| `.venv` の site-packages | 34123 | `cfb4f4f7…bdc5` |
| `.venv-relation-detr` の freeze（72 行） | — | `d0724876…aad1d` |
| `.venv-relation-detr` の site-packages | 21257 | `f79c8309…88e1` |

表の sha256 は経路ごとの要約値（行の並びのハッシュ）で、ファイル自体の sha256 ではない（COCO の重みのファイルの sha256 は `2d2c19a7a49e…`、`sha256sum` で直接取った）。凍結源の行だけはファイル自体の sha256。
使う設定と実装 8 本（`configs/detector_relation_detr/train_search.py` ほか）の sha256 も同じ JSON に在る。

### A-5 G1 の判定

- 要約値を計測の前にもう一度取った（`$STORE/A/digests_before2.json`、試験の終了後）。一度目は試験の実行中に取ったもので、工程塔が読む画像の置き場 `data/raw/OpenSurgery_Dataset/01_frames/initial_videos`（27,535 files、`aa4c1c6e…`）が入っていなかった。重なる項目は一度目と全項目同じ
- 開始前の試験: `python -m pytest tests/ -q -p no:cacheprovider --junitxml=…`（30 分 34 秒）。**7 failed, 989 passed**、rc=1。失敗の名前は `$STORE/A/pytest_before_failed.json`:
  `test_engines::test_mmdet_trainer_eval_recipe_in_metrics`、`test_fetch_task::test_rejects_unknown_file_name`、
  `test_research_logger` の 4 件（`test_log_run_idempotent`、`test_run_logging_invokes_log_run_on_finally`、`test_run_logging_no_double_post_on_normal_exit`、`test_run_logging_swallows_exception_in_user_block`）、
  `test_stage1_ptower_r3_dist::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail`
- 試験の後の列挙で 1 件出た。中身はその命令の中で出力を受けていた自分の `python3 -c …`（uv の python3.11 は `.venv/bin/python` と同じ実体）。本契約以外のプロセスではない
- **G1: pass**

## 2. 測り方（Phase B・C 共通）

- 実行器 `tools/run_level.py <det|ph2|ph1> <GPU ごとの batch>`。起動の前に、GPU 0・1 の記憶が 100 MiB 以下で、compute プロセスが 0 件（自分の PID は `--exclude-pid` で除く）であることを確かめ、満たさなければ拒む。nvidia-smi を 200 ms ごとに `nvsmi.csv` へ採る。終了後に作業場所の重みのファイル（`.pth` `.pt` `.safetensors` `.bin` `.ckpt` と `checkpoint*` の下）を数える
- 共通の環境: `WANDB_MODE=offline`、`WANDB_DIR` は作業場所、`PYTHONDONTWRITEBYTECODE=1`（third_party と仮想環境に .pyc を書かない）、`PYTORCH_CUDA_ALLOC_CONF` は外す、2 枚では `NCCL_P2P_DISABLE=1`、`TOWER_SEARCH_TASK=T-2026-11-06-tower-batch-probe`、`TOWER_SEARCH_OBSERVER=tools/observer.py`。命令は `source scripts/load_env.sh` の後に起動
- 検出塔の命令（cwd `third_party/Relation-DETR`、`.venv-relation-detr` を有効化）:
  `accelerate launch --multi_gpu --num_processes 2 --main_process_port 29801 scripts/train_relation_detr_search.py --config-file $STORE/config/train_search_batch.py --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36`。
  環境は探索の `detector_environment` と同じ値（`DTOWER_LR=0.0001`、`DTOWER_WEIGHT_DECAY=0.0001`、`DTOWER_MAX_NORM=0.1`、`TOWER_SEARCH_POINT=0`、`EGO_ROOT`、`EGO_ANN_DIR=…/egosurgery_tool_folds/A`、`RELDETR_COCO_CKPT`）に、`TOWER_SEARCH_CONTROL_STEPS=61` と `PROBE_BATCH_SIZE` を足した
- 設定の写し（`tools/make_det_config.py`、`$STORE/config/diff.txt`）: 原本と違うのは `-batch_size = 2` / `+batch_size = int(os.environ["PROBE_BATCH_SIZE"])` の 1 行だけ
- 工程塔の命令（cwd repo、`.venv`）: `[python -m torch.distributed.run --nproc_per_node=2 --master_port=29811 | python] scripts/run_ptower_search.py action=finetune +point_id=0 +artifact_root=<work> manifest_dir=data/processed/phase_manifest_all_phase cache=<work>/features/all_gap.npz workers=4 +control_only=true ft_batch_size=<GPU ごと × 枚数>`。一枚の道は `CUDA_VISIBLE_DEVICES=0`
- `run_ptower_search.py` は ExperimentManager の置き場を `<work>/runs` へ差し替えるので、証拠のフォルダは repo の外にできる。`+control_only=true` で repo への公開（`experiments/phase1/stage1_ptower_search`）を止めた
- 観測器 `tools/observer.py`:
  - 検出塔: `CocoDetection.load_image` で読んだ画像名を worker ごとに記録。外側の `train_one_epoch_acc` を包み、モデルの forward の前の hook で歩の開始時刻・batch の枚数・image_id を記録する。OOM は歩と記憶を記録して再送出する。`models.bricks.ms_deform_attn._C` の有無（CUDA 拡張の読み込み）を記録
  - 工程塔: `FoldFrames.__getitem__` で読んだフレームを記録。学習の DataLoader（`shuffle=True` か `batch_sampler` を持つもの）を包み、前の歩の GPU 処理を `torch.cuda.synchronize()` で待った時刻と、次の batch を渡した時刻を記録する。61 歩目の後に記録を書いて `SystemExit(0)` で止める（val・checkpoint の保存の前）。`finetune` を包んで OOM を記録する
- 一歩の時間: 歩 k の開始から歩 k+1 の開始まで。61 の開始時刻から 60 歩分が出る。定常は歩 11〜60 の 50 歩の平均と標本標準偏差（`tools/summarize.py`）

## 3. Phase B — 検出塔（2026-11-05 17:03〜17:12Z = 11-06 02:03〜02:12 JST）

起動の失敗（記録は消さずに移した）:

1. 一度目: `det_b2: GPUs not idle, refused`。数えられたのは実行器自身（`.venv/bin/python …/run_level.py det 2`）。`procs.py` に `--exclude-pid` を足し、実行器が自分の PID を渡すようにした。記録は `$STORE/refused_det_b2_try1/`
2. 二度目: `RuntimeError: W&B offline tracking unavailable`（rc=1、3 秒）。`tracking.enabled()` が `WANDB_API_KEY` を要り、`load_env.sh` を読まずに起動したため。記録は `$STORE/failed_det_b2_try2_no_env/`。三度目から `source scripts/load_env.sh` を同じ命令に入れた

| 水準 | status / rc | 壁時計 | 重み | 備考 |
|---|---|---|---|---|
| det_b2 | exited / 0 | 52 s | 0 | `CONTROL_COMPLETE` を両 rank で出力 |
| det_b4 | exited / 0 | 69 s | 0 | 同上 |
| det_b6 | exited / 0 | 88 s | 0 | 同上 |
| det_b8 | exited / 1 | 78 s | 0 | rank 1 が `torch.cuda.OutOfMemoryError: … Tried to allocate 2.28 GiB. GPU 1 has a total capacty of 47.40 GiB of which 1.32 GiB is free …`（stdout.log 349 行） |

- 各水準の前に GPU 0・1 は 16 MiB、compute プロセス 0 件（`run.json` の `before`）
- COCO の重み: 学習ログ `[RANK 0] load pretrained from /home/ubuntu/slocal2/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`。`initialization_rank{0,1}.json` は `matched: true`、596 テンソル、`source_sha256 2d2c19a7a49e…`（`sha256sum` で直接取った値と一致）
- CUDA 拡張: 全 rank で `ms_deform_attn_cuda_ext_loaded: true`、`mixed_precision: fp16`、`num_processes: 2`
- 読み込んだ枚数: 全水準・全 rank で各歩の枚数の集合が {2}・{4}・{6}・{8}（`steps_rank*.json` の `frames`）
- 学習ログの `data_time`（歩 50、rank 0 / 1）: b2 0.0010 / 0.0030、b4 0.0018 / 0.0053、b6 0.0025 / 0.0078 s
- **G2: pass**（4 水準すべてで結果・記憶・一歩の時間を記録。b8 は溢れた歩 38 と rank 1 の記憶。rank 0 の torch の値は記録の前に止められ UNKNOWN）

## 4. Phase C — 工程塔（2026-11-05 17:21〜17:29Z = 11-06 02:21〜02:29 JST）

起動の失敗: 一度目は `for lv in "ph2 8" …; run_level.py $lv` と書き、zsh が `$lv` を単語に分けないため 6 本とも `IndexError: list index out of range`（引数が 1 つ）で、何も起動しなかった（C/ は空のまま）。`for kind b in ph2 8 …` に直した

| 水準 | ft_batch_size | status / rc | 壁時計 | 重み | 備考 |
|---|---|---|---|---|---|
| ph2_b8 | 16 | exited / 0 | 46 s | 0 | `PROBE_COMPLETE rank=0/1 steps=61` |
| ph2_b12 | 24 | exited / 0 | 61 s | 0 | 同上 |
| ph2_b16 | 32 | exited / 0 | 81 s | 0 | 同上 |
| ph1_b16 | 16 | exited / 0 | 72 s | 0 | `PROBE_COMPLETE rank=0` |
| ph1_b24 | 24 | exited / 0 | 106 s | 0 | 同上 |
| ph1_b32 | 32 | exited / 1 | 7 s | 0 | 歩 1 で `torch.cuda.OutOfMemoryError: … Tried to allocate 558.00 MiB. GPU 0 has a total capacty of 47.40 GiB of which 21.94 MiB is free …`（stdout.log 59 行） |

- COCO の backbone: `load pretrained COCO backbone data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth sha256=a755b3eb…`（`run_ptower_search.py` の `observed_backbone` が探索の入力の記録と照合し、違えば止まる）
- 決定性: 両 rank で `deterministic_algorithms=True, cudnn_deterministic=True, cudnn_benchmark=False, matmul_tf32=False, cudnn_tf32=False, cublas_workspace_config=:4096:8`
- 入力の形 [batch, 3, 800, 1422]。データセットは 10,580 フレーム。二枚の道は rank ごとに 8・12・16 枚、一枚の道は 16・24・32 枚で全歩一致
- 証拠のフォルダは `<work>/runs/phase1/stage1_ptower_search_001_ft_coco_lr0.0001_foldA_point00_seed42/`（repo の外）。`checkpoints/` は空

## 5. Phase D — 検証

- 集計: `tools/summarize.py --out $STORE/levels.json`（写しを `experiments/analysis/tower_batch_probe/levels.json` に置いた）。表は `tools/make_tables.py`
- test 不使用: 全 10 水準で読んだ動画 = {01,02,03,06,08,11,12,13,14,15}、{04,05,07} との共通 0 件。陽性対照 `--inject-video 04` で全 10 水準 1 件（`$STORE/levels_inject04.json`）
- 見込み時間の計算し直し: `make_tables.py` が各 rank で `歩数 × 平均 − 見込み < 1e-9` を assert して通った
- 事後の要約値（`$STORE/A/digests_after.json`、17:30Z）: `digests_before2.json` と roots 17 項目・凍結源・両仮想環境（freeze と site-packages）がすべて一致
- 要約値の道具の陽性対照（scratchpad の写し）: 1 ファイルの場所 `63b6958c2988` → 新しいファイルを足すと `d8eabb91c346` → その中身を 1 文字変えると `da0f0800c0d8`
- `make forbidden-check TASK=T-2026-11-06-tower-batch-probe`: `status: pass`、`violations: []`、changed 15（本契約の新しいファイルがすべて変更として検出され、`allow_write experiments/analysis/tower_batch_probe` で許可）
- 事後の試験（17:30Z〜、30 分 33 秒）: **7 failed, 989 passed**、rc=1。失敗の名前の集合は開始前と同じ（新規 0、消えた 0。`$STORE/A/pytest_after_failed.json`）
- repo 直下に未追跡の `run_ptower_search.log` が出た（0 bytes、mtime 2026-11-05T17:21:03Z = ph2_b8 の起動時刻）。`configs/stage1_ptower_r3.yaml` の `hydra.run.dir: .` により Hydra がジョブのログを cwd（repo 直下）に作ったもの。消さず、commit もしていない

# audit — T-2026-11-06-dtower-batch-search

時刻は UTC で記録し、括弧内に JST を添える。版管理の外の置き場は
`/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-batch-search/`（以下 `$STORE`）。
道具は `experiments/analysis/dtower_batch_search/tools/`。

## 0. 開始（手順書 0〜4、2026-11-05 22:07Z 前後 = 11-06 07:07 JST）

- 前段: 同じ識別子の一度目の着手（21:56Z）は G1 の前で中止した。カードが四版のままだったためで、利用者の指示により「実行しなかった扱い」とし、記録・分岐・置き場を消した。学習は 0 本、prereg の commit も無い。抑止は `task-release END=abort` で外した
- 二度目の着手で、利用者から次の三つを受けた
  - 「最新の phase0 に五版が入っている」
  - 同点幅は 0.0076（runindex の mAP_sstd 0.0038 の 2 倍。prereg の定義どおり。0.0106 は起票者の誤り）
  - S は 12 番の実際の値 4.976e-3。weight decay は b2 を 3.37e-4 のまま、b4・b6 を歩数の比で換算する
  - 二つとも `meta.amendments` に記録し、prereg を直してから学習の前に commit する
- ホスト名 `Andrew`。開始時の分岐 `feat/dtower-step-profile`、作業ツリーは清浄。`feat/dtower-batch-search` は手元にも遠隔にも無く、`tasks/T-2026-11-06-dtower-batch-search` の履歴も無い。`.sync-pause` は無い
- `git fetch origin`: phase0 が da8dcc54 → 9d45351b（`Merge pull request #294 … proposal-card-tower-reselect-v5`）
- `python3 scripts/task_start_classify.py`（比較先 origin/phase0 9d45351b）: 7 区分すべて 0 件、`分類: 通す`
- `make task-start`: `分岐を作成: feat/dtower-batch-search（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、契約の取り込み OK、`[task-start] 完了。`
- 取り込んだ 3 ファイルの sha256: SPEC.md `7664f527…`、prereg.md `28fb6088…`、spec.yaml `b392856a…`。値は一度目と同じ（同点幅 0.0106、weight decay 3.386e-4・6.775e-4・1.015e-3）
- `make task-validate`: `OK`、exit 0

## 1. 参照の解決と改訂（手順書 3、22:08Z）

- `inputs.denominator.ref` = `exp:baselines/dcoco_foldA/dcoco_foldA@val`（`runindex/experiments.csv`）
  - split val、n_runs 6、n_seeds 3（42,123,456）
  - task_ids は `T-2026-09-18-stage1-detector-towers`・`T-2026-09-19-stage1-detector-towers-r2`
  - mAP_mean 0.7242877、**mAP_sstd 0.0037965**、mAP_pstd 0.0034657
  - require（n_seeds ≥ 3、sigma あり、split val）は満たす
- 二周目の RESULT 64 行: 折り A 3 seed の D\*-COCO は一周目 0.7235 (0.0024)、二周目 0.7251 (0.0053)
- 12 番（`points.csv` 14 行、`results_dtower.csv` rank 1）: lr 0.000307、detector_weight_decay 0.000337、max_norm 0.059、detector_S 0.005
- S = 0.000307 × 0.000337 × 48,100 = 0.0049763779
- 換算（weight decay = 3.37e-4 × 2,405 ÷ 歩数）
  - 2,405 → 3.37e-4
  - 1,202 → 6.742803660565724e-4
  - 802 → 1.0105798004987532e-3
  - S はどれも 0.0049763779
- 利用者の決定に従い、prereg・SPEC・spec.yaml を書き換え、`meta.amendments` に 2 件を記録した（diff は spec.yaml）
  - prereg: §1、§2.1 の表と本文、§3.3、§3.1 の 1、§4 の weight decay と S の行
  - SPEC: §1 の S の行と seed 間の行、§2 の 2 か所
  - spec: acceptance d
- 書き換えの後の `make task-validate`: `OK`

## 2. prereg の commit（Task A-1、学習の前）

- `b71ffafd85634e2d92a29866c009d4bb440bfb97`（2026-11-05T22:08:51+00:00 = 11-06 07:08:51 JST）`docs(dtowerbatch): 事前登録（学習の前、同点幅と S の改訂つき）`。spec.yaml・SPEC.md・prereg.md
- `a141077e`: spec.yaml の `prereg.commit` と `committed_at` に上の値を記入
- push: `origin/feat/dtower-batch-search`
- `make task-preflight`: **11 PASS / 0 WARN / 3 SKIP / 0 FAIL**、exit 0
  - PASS: P4 `b71ffafd… committed_at=2026-11-05T22:08:51+00:00`、P5 `best_ap.pth sha256=03936318…75e824`、P13 `対称性の表 1 個 / 23 行に UNKNOWN と理由欠落は無い`、P14 `検出 0 件（カード 16 件 / 禁止語 15 語を検査）`
  - SKIP: P2・P3（契約に記載なし）、P12（解決前提の参照なし）
  - P9 spec_lint: 規則 9 件で該当なし

## 3. Phase A — 開始状態（22:10〜22:20Z = 11-06 07:10〜07:20 JST）

### A-2 分岐と起点

- `feat/dtower-batch-search`、`HEAD~2` = `origin/phase0` = merge-base = `9d45351b0bcccab564616a443e333853f3522cd9`
- PR 290 の内容（`tasks/T-2026-11-06-tower-batch-probe/` 5 ファイル、`experiments/analysis/tower_batch_probe/` 9 ファイル）と、PR 292 の内容（`tasks/T-2026-11-06-dtower-step-profile/` 5 ファイル、`experiments/analysis/dtower_step_profile/` 26 ファイル）が `git ls-tree -r origin/phase0` に在る
- 履歴: `7f7d6ea5 Merge pull request #290`、`84bfe82d Merge pull request #292`

### A-3 カードの版

- `docs/proposals/2026-10-21-tower-reselect-search.md` 3 行の「版:」は **五版**（`版: 五版（2026-11-06。利用者の決定〔F 2026-11-06〕を反映。…）`、commit `e0d2d2e8`）
- 道具 `tools/check_card.py`: 本物で `version=五版`、rc 0。陽性対照として 3 行を「四版」にした写し（scratchpad）では `version=四版`、rc 1

### A-4 開始前から在る未追跡

- 0 件（`git status --porcelain --untracked-files=all` が空。task-start の分類も 0 件）

### A-6 入力・道具・記憶領域

- `tools/check_inputs.py --pin $STORE/A/pins.json`: 13 件、不一致 0、rc 0（`$STORE/A/check_inputs.json`）
  - COCO の重み `relation_detr_resnet50_800_1333_coco_1x.pth` の sha256 `2d2c19a7a49e…` は、PR 290・292 の `initialization_rank*.json` の `source_sha256` と一致
  - 折り A の注釈 3 本（train `fc63621e…`・val `db605c06…`・test `f4ce5243…`）と、道具・設定 9 本の sha256 を開始時に固定した
- 陽性対照: `instances_val.json` の 1 バイトを変えた写しを `--override` で読ませると、不一致 1、rc 1
- 要約値（`tools/digests.py`、`$STORE/A/digests_before.json`）
  - PR 292 の事後の要約値と重なる 17 経路は全項目一致（third_party `2e4de92b…`、data/raw/ego `a19c4a81…`、注釈 `5c46a6de…`、COCO の重み `f68913a5…`、設定と scripts 9 本）
  - 凍結源は `03936318…`
  - 両仮想環境の freeze と site-packages も PR 292 と一致（`.venv` `f6c43729…`/`cfb4f4f7…`、`.venv-relation-detr` `d0724876…`/`f79c8309…`）
  - 本契約で足した経路は 6 本: `experiments/analysis/dtower_step_profile` `6251fab8…`、`experiments/baselines/stage1_dtower_search` `98dcd518…`、`scripts/eval_relation_detr_map.py`・`scripts/tower_search_records.py`・`scripts/tower_search_track.py`・`third_party/Relation-DETR/main.py`
- 記憶領域: `/home/ubuntu/slocal2` の空き 1,644,097,175,552 bytes（`df -B1`）
  - 見込みは andrew の前例（T-2026-11-02-hostdiff-andrew の検出塔 3 本、各 3.2 GB）× 6 本 ≈ 19.2 GB で、その 2 倍は約 38.4 GB。空きはその 2 倍以上
- 同期の経路: Syncthing の同期フォルダは `~/.claude`・`~/.codex`・`~/.agents`・`~/claude-sync`・`~/slocal2/m2` の 5 つ
  - `path="~"` の行は id と label が空の既定の雛形で、同期フォルダではない
  - `$STORE` は同期の外にある

### A-7 環境（prereg §7、`tools/env_capture.py`、`$STORE/A/env_relation_detr.json`・`env_body.json`）

| 項目 | `.venv-relation-detr`（学習・評価） | `.venv`（記録） |
|---|---|---|
| Python | 3.11.16 | 3.11.16 |
| torch / CUDA の実行時の版 | 2.1.2+cu118 / 11.8 | 同じ |
| cuDNN / NCCL | 8700 / 2.18.6 | 同じ |
| torchvision | 0.16.2+cu118 | 同じ |
| accelerate | 1.14.0 | 1.13.0 |
| 画像の復号 | Pillow 12.2.0（libjpeg-turbo、`PIL.Image.open(...).convert('RGB')`） | 同じ |
| TF32 の既定（新しいプロセス） | matmul False、cudnn True | 同じ |
| 装置 | RTX A6000 × 2、driver 595.84、power.limit 300.00 W（既定 300.00 W）、SM 2100 MHz、PCIe gen 4 × 16 | 同じ |

- 論理 CPU 32
- 学習のプロセスが実際に読んだ TF32 と autocast は、各 run の `initialization_rank*.json` と `optimizer_rank*.json` の `runtime`・`autocast` に記録される

（以下、試験・compute プロセス・G1 は試験の後に追記する）

### A-7（続き）試験の前の値

- 開始前の試験（22:14:10Z〜22:44:49Z、30 分 36 秒）
  - 命令: `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/ -q -p no:cacheprovider --junitxml=$STORE/A/pytest_before.xml`
  - 結果: **7 failed, 989 passed**、rc=1
  - 失敗の名前（`$STORE/A/pytest_before_failed.json`）は、PR 290・292 の開始前と同じ 7 件
    - `tests.test_engines::test_mmdet_trainer_eval_recipe_in_metrics`
    - `tests.test_fetch_task::test_rejects_unknown_file_name`
    - `tests.test_research_logger` の 4 件
    - `tests.test_stage1_ptower_r3_dist::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail`

### A-5 compute プロセス（22:44:58Z、試験の後）

| 呼び方 | 件数 | 出力 |
|---|---|---|
| 既定（`.venv/bin/python`・`.venv-relation-detr/bin/python`・`/usr/bin/python3` の realpath と完全一致） | **0**、nvidia-smi の compute 0 | `$STORE/A/procs_default.json` |
| 陽性対照 `--exe /usr/bin/bash --arg probe_self_marker_9931`（自分のシェルから `bash -c 'sleep 25; true' probe_self_marker_9931` を起こして） | **1** | `$STORE/A/procs_ctrl_pos.json` |
| 部分一致 `--arg probe_self_marker_993` | 0 | `$STORE/A/procs_ctrl_substr.json` |
| 陰性対照 `--exe /nonexistent/zzz_no_such_exe` | 0 | `$STORE/A/procs_ctrl_neg.json` |

- GPU は両方 16 MiB、使用率 0 %

### A-1 の空振りの確認（SPEC §5 a）

- `tools/preflight_task.py` の P13・P14 を、本物の入力と壊した写しに当てた
  - P13: 本物は PASS（23 行）。写しの prereg の「数値精度」の行を UNKNOWN にすると **FAIL**（`23 行を検査。UNKNOWN 1 行: 数値精度`）
  - P14: 本物は PASS。`intent.proposal_card` を `docs/proposals/zzz_no_such_card.md` にした spec では **FAIL**（`提案カードが無い`）

### G1

- **G1: pass**
  - 分岐 `feat/` で起点 origin/phase0 9d45351b。prereg の commit b71ffafd は学習の前
  - カードは五版。PR 290・292 の内容が起点に在る
  - 入力・道具・COCO の checkpoint が在り、要約値が記録と一致
  - 本契約以外の compute プロセスは 0 件
  - 空きは見込みの 2 倍以上

## 4. Phase B — 口と対照（22:45〜22:51Z = 11-06 07:45〜07:51 JST）

### B-1 口

- batch と worker 数: 原本 `configs/detector_relation_detr/train_search.py` は `batch_size = 2` と `num_workers = 4` を固定し、口が無い
  - この 2 行だけを `PROBE_BATCH_SIZE`・`PROBE_NUM_WORKERS` にした写しを `$STORE/config/train_search_batch.py` に置いた（`tools/make_det_config.py`。差分は `$STORE/config/diff.txt`）
  - worker 数は 4 に固定して渡した
- 学習率・weight decay・max_norm: 既存の `DTOWER_LR`・`DTOWER_WEIGHT_DECAY`・`DTOWER_MAX_NORM` で渡した
- **点の照合**: `scripts/train_relation_detr_search.py` は epoch 0 で、optimizer の群を `load_point(TOWER_SEARCH_POINT)` の値と 1e-15 の精度で照合する（`tower_search_common.check_detector_groups`）
  - `load_point` は dlsta の `points.csv` を読み、12 番の weight decay は 3.37e-4 である。このため b4・b6 は値が optimizer に届いても止まる
  - 包み `tools/train_level.py` を置いた。探索のスクリプトを変えずに import し、`load_point` だけを `DTOWER_LEVEL_POINT`（実行器が prereg §2.1 の値から書く JSON）を読む関数に差し替えて `main()` を呼ぶ
  - 照合そのものはそのまま働き、prereg の値と違う `DTOWER_*` を渡すと止まる（下の wd_mismatch）
- 観測器 `tools/observer.py`（既存の `TOWER_SEARCH_OBSERVER` で読ませる）が記録するもの
  - DataLoader の batch と長さ、各歩でモデルに渡った枚数
  - 第 0 epoch の各歩の学習率
  - 各 epoch の評価の時間と組ごとの AP（評価の道具と同じ計算）
  - 読んだ動画
  - `PROBE_EXPECT_BATCH` と枚数が違えば、最初の歩で止める
- 実行器 `tools/run_batch.py`: 対照と本番。起動は探索の検出塔の段（`run_tower_search.py` の `detector_point`）と同じ並びにした
  - 学習 → best の val と train の評価（`skip loading`・`State dict is None` で止める）→ `tower_search_records.py detector` → 記録の写し

### B-2 対照（`run_batch.py control <名前>`、各 5 歩で止める `TOWER_SEARCH_CONTROL_STEPS=5`、`$STORE/B/control_*/result.json`）

| 対照 | 入力 | rc | optimizer の 6 群（学習率, weight decay） | DataLoader の batch / 長さ | 各歩の枚数 |
|---|---|---|---|---|---|
| b2 | 包み、写し、batch 2、wd 3.37e-4 | 0（CONTROL_COMPLETE） | (3.07e-4, 3.37e-4), (3.07e-5, 3.37e-4), (3.07e-5, 0), (3.07e-5, 3.37e-4), (3.07e-5, 0), (3.07e-4, 0) | 2 / 2,405 | {2: 5} |
| b4 | batch 4、wd 6.7428e-4 | 0 | (3.07e-4, 6.7428e-4), (3.07e-5, 6.7428e-4), (3.07e-5, 0), (3.07e-5, 6.7428e-4), (3.07e-5, 0), (3.07e-4, 0) | 4 / 1,202 | {4: 5} |
| b6 | batch 6、wd 1.01058e-3 | 0 | (3.07e-4, 1.01058e-3), (3.07e-5, 1.01058e-3), (3.07e-5, 0), (3.07e-5, 1.01058e-3), (3.07e-5, 0), (3.07e-4, 0) | 6 / 802 | {6: 5} |
| changed（陽性対照） | batch 3、wd 5e-4 | 0 | (3.07e-4, 5e-4), …（同じ型） | 3 / 1,603 | {3: 5} |
| wd_mismatch（照合の陽性対照） | 点の JSON は 3.37e-4、`DTOWER_WEIGHT_DECAY` は 6.7428e-4 | **1**（`detector optimizer groups differ from the preregistered point`） | 記録なし（照合で止まった） | 2 / 2,405 | 0 歩 |
| batch_mismatch（枚数の陽性対照） | batch 2、`PROBE_EXPECT_BATCH=4` | **1**（`frames per step 2 differ from the level batch 4`） | b2 と同じ | 2 / 2,405 | {2: 1} |
| default（既定の挙動） | 既存の `train_relation_detr_search.py` と既存の設定、`TOWER_SEARCH_POINT=0`（lr 1e-4、wd 1e-4、max_norm 0.1） | 0 | (1e-4, 1e-4), (1e-5, 1e-4), (1e-5, 0), (1e-5, 1e-4), (1e-5, 0), (1e-4, 0) | 2 / 2,405 | {2: 5} |

- 群は、本体の 2 群が水準の値、backbone と線形射影の群が学習率 0.1 倍、norm と bias が weight decay 0（`check_detector_groups` と同じ型）
- 7 本とも保存された重み（`.pth`）は 0 件
- 読んだ動画は train の 10 本だけ（b2 の対照: 01・02・03・06・08・11・12・13・14・15）

### B-3 立ち上げの歩数

- 実装（`third_party/Relation-DETR/util/engine.py` 32 行）は `warmup_iters = min(1000, len(data_loader) - 1)` の `LinearLR`
  - 期待値は b2 1,000、b4 1,000、b6 801（b6 の第 0 epoch は 802 歩で、802 歩目で目標の学習率に達する）
- 観測器の記録の口: 対照（5 歩で、立ち上げは 4 歩）で学習率が 3.07e-7 → 7.698e-5 → 1.53653e-4 → 2.30327e-4 → 3.07e-4 と進み、`first_step_at_target` = 5
- 本番の各 run で実測する

### B-4 weight decay の換算の照合

- DataLoader の長さの実測は 2,405・1,202・802（対照の `loader_rank0.json`）で、prereg §2.1 の表と同じ
- 換算 3.37e-4 × 2,405 ÷ 歩数 = 3.37e-4・6.742803660565724e-4・1.0105798004987532e-3。表の 6.7428e-4・1.01058e-3 と 5 桁で一致し、改訂は不要

### G2

- **G2: pass**
  - 各水準の設定が optimizer の群と DataLoader に届き、陽性対照で値が変わった
  - 立ち上げの歩数の記録の口が働く
  - 既存スクリプトの既定の挙動が変わっていない（default の対照。要約値で scripts は無変更）

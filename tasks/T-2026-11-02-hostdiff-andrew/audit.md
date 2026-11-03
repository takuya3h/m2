# audit — T-2026-11-02-hostdiff-andrew（andrew）

時刻は UTC と JST を併記する。大きな出力は repo の外 `~/m2-scratch/T-2026-11-02-hostdiff-andrew/` に置き、ここには要約と経路を書く。

## 0. 開始

- 2026-11-02 13:2x UTC（22:2x JST）。ホスト名 `Andrew`、repo `~/slocal2/m2`
- 開始時の分岐 `feat/stage2-w23-andrew`。分類器 `scripts/task_start_classify.py`: 追跡下の変更 0、未追跡・起点に在り中身が同じ 41（通す）、ほか 0 → `分類: 通す`
- `make task-start` → `分岐を作成: feat/hostdiff-andrew（起点 origin/phase0）`（d145854e）、`[task-start] .sync-pause を作成`、`[task-start] 完了。`
- `make task-validate` → `OK`、exit 0
- `make task-preflight` → `7 PASS / 0 WARN / 6 SKIP / 1 FAIL`、exit 2

      P2 cuda_ext_loaded  FAIL models.bricks.relation_transformer を import できない: ModuleNotFoundError: No module named 'fvcore'

  SKIP: P3（判定基準が未確定、backlog B-20）、P4・P5・P13・P14（kind=analysis で対象外）、P12（解決前提の参照なし）。P9 spec_lint 該当なし

### 0.1 逸脱 1: P2 の FAIL を利用者の承認で通した

- P2 は検査器の Python（P1 が要求する本体 `.venv`）で import する（`tools/preflight_task.py:217`）。`fvcore` は `.venv-relation-detr` にだけ在る（0.1.5.post20221221）。本体 `.venv` には無い
- 同じ import を `.venv-relation-detr` で回すと `Loading extension module MultiScaleDeformableAttention...` → `ok`
- 利用者に 3 択を示し、利用者は「2」（構造的な FAIL として承認し続行）を選んだ

### 0.2 逸脱 2: 空の分岐を最新の phase0 へ早送りした

- SPEC §1 は PR #284（`T-2026-11-02-bengio-align-andrew`）が本契約の開始前に phase0 へ統合されていることを求める。#284 の統合は 2026-11-02T13:27:38Z。task-start の取得時の `origin/phase0` は d145854e で、#284 を含まなかった
- 分岐に commit が無いことを確かめ、`git merge --ff-only origin/phase0` で d145854e → 7f9e31f6 に早送りした（統合の commit は作らない）。d145854e..7f9e31f6 の差はコードを含まない（`experiments/analysis/bengio_align_andrew/`、`tasks/T-2026-11-02-bengio-align-andrew/`、`context/auto/` の 3 件、`tasks/inbox*`）
- 早送りの後、HEAD == origin/phase0 == 7f9e31f6581a7d615b2402fb40929a48d3aacf2e（`git merge-base --is-ancestor` を両向きで確認）。`.sync-pause` は置いたまま（中身 `task_id=T-2026-11-02-hostdiff-andrew` / `branch=feat/hostdiff-andrew`）
- 戻し方: `git reset --hard d145854e`（本契約の commit の前に限る）

### 0.3 想定外: MS-Deform-Attn の `.so` がプリフライトと確認の import で作り直された

- `~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/.ninja_log` に今日のビルドが二度ある

  | 時刻（UTC） | 対象 | ninja のコマンド要約 | 起こしたもの（時刻からの推定） |
  |---|---|---|---|
  | 2026-10-13 19:48:12〜19:48:54 | `.o`・`.so` | df4dbe4b6d55ac3a・7c89d0a9e86d2e3d | 記録の `.so`（79b55a8a…、`bengio_andrew_env_survey/c/andrew_venv-relation-detr.json`） |
  | 2026-11-02 13:25:40〜13:26:23 | `.o`・`.so` | 45957ad25f8a372a・f8fdc8e5e7bdcfc2 | `make task-preflight` の P2（本体 `.venv` の Python。import は拡張の構築の後で `fvcore` に落ちた） |
  | 2026-11-02 13:26:52〜13:27:34 | `.o`・`.so` | df4dbe4b6d55ac3a・7c89d0a9e86d2e3d | 0.1 の確かめ（`.venv-relation-detr` の Python） |

- 今の `.so` は 1,655,680 B、sha256 d1d9d1ac5470d3f6750fabae2d7912d3b70e97be2092282683a72c100dac5c04。`.o` は d294bc9a5d9ecd5e…（記録は 966a3806518a4a80…）。`build.ninja` は 2,706 B、f72b62a067a6540a…（記録と同じ）
- ninja のコマンド要約が 2026-10-13 と同じなので、命令（版・旗・経路）は同じで、nvcc の出力のバイトだけが違う、と読む。79b55a8a… の写しはディスクに無い（`find / -xdev -name 'MultiScaleDeformableAttention*.so'` は 1 件だけ）
- 本測定の andrew の `.so` は d1d9d1ac… である。SPEC §3 の 79b55a8a… ではない。§3 はこの行を「測る違いに含まれる」としているので、値はそのまま記録して続ける
- 以後、本体 `.venv` から Relation-DETR の拡張を import しない。プリフライトは回し直さない

## A. 開始状態と照合（G1）

出力の全件は repo の外 `~/m2-scratch/T-2026-11-02-hostdiff-andrew/A/`。

### A-1 分岐と起点

- 分岐 `feat/hostdiff-andrew`、起点 `origin/phase0` 7f9e31f6581a7d615b2402fb40929a48d3aacf2e（0.2 の早送りの後）。HEAD == origin/phase0

### A-2 compute・GPU・記憶領域

- `scripts/grasppilot/proc_enum.py`: プロセス 39、GPU の compute PID なし、compute 0 件（`A/proc_enum.json`）
- 陽性対照 `--match-exe /usr/bin/zsh` → 5 件。陰性対照 `--match-exe /nonexistent/path/python9` → 0 件
- GPU: RTX A6000 × 2（0: GPU-06de23a6…、1: GPU-07e03d7e…）、driver 595.84、使用 16 MiB・使用率 0 %、compute なし
- 記憶領域: `~/m2-scratch` の空き 1,505,154,605,056 B

### A-3 Relation-DETR

`python3 scripts/grasppilot/reldetr_digest.py --root third_party/Relation-DETR --venv .venv-relation-detr`（`A/reldetr_digest.json`）

| 項目 | 実測 | andrew main の記録（`bengio_align_andrew/start/andrew_reldetr_main.json`、SPEC §3） | 一致 |
|---|---|---|---|
| source | 142・2f08e5213cb5c377c576172b0d39964f46fb6afb80532ce11f8bad7437f1e393 | 142・2f08e5213cb5c377… | 一致 |
| all | 155・20f15c061b435ce44d45f3da2e2b225548fffaea0422bbcc2aedfb72775c94f6 | 155・20f15c061b435ce4… | 一致 |
| `.venv-relation-detr` のパッケージ | 72・8f08a2457e681d6d… | — | — |

### A-4 入力の要約値

`tasks/T-2026-11-02-hostdiff-andrew/tools/check_inputs.py`（`A/inputs.json`）。記録は andrew の列と dlsta の固定記録だけを使った。test の注釈と manifest は要約値も取っていない。

| 項目 | 実測 | 記録 | 一致 |
|---|---|---|---|
| `image_input_lock.json` 17,233 行（selected と counterpart の 32,670 経路） | 不一致・欠け 0、2,110,782,515 B | 各画像の sha256 | 一致 |
| `phase_manifest_all_phase/train.json` | 1,204,959 B・0d25c99f97df63c2… | 同じ | 一致 |
| `phase_manifest_all_phase/val.json` | 221,723 B・fe3da175937033d8… | 同じ | 一致 |
| `phase_manifest_all_phase/phase_vocab.json` | 164 B・ad3c1e4a4b0913bc… | 同じ | 一致 |
| 折り A `instances_train.json` | 14,801,507 B・fc63621ea496ccdc… | 同じ | 一致 |
| 折り A `instances_val.json` | 2,184,273 B・db605c06626ff824… | 同じ | 一致 |
| `data/splits/ego_{train,val,test}.txt` | 30・6・9 B、c28816de…・f1bc456a…・7edeab62… | 同じ | 一致 |
| COCO の重み（両塔） | 196,140,106 B・2d2c19a7a49e7d77… | 同じ | 一致 |
| COCO の重みの backbone 要約値（工程塔の初期化） | a755b3eb22a3c199… | `inputs_inventory.json` B5b と同じ | 一致 |
| 空振りの対照: 記録の要約値の先頭一文字を変えた値 | — | — | 不一致（期待どおり） |

### A-5 env（静的な欄。`A/env_venv.json`、`A/env_venv-relation-detr.json`）

| 欄 | `.venv`（工程塔） | `.venv-relation-detr`（検出塔） |
|---|---|---|
| Python | 3.11.16 | 3.11.16 |
| torch・CUDA 実行時・cuDNN・NCCL | 2.1.2+cu118・11.8・8700・2.18.6 | 同じ |
| torchvision | 0.16.2+cu118 | 同じ |
| accelerate | 1.13.0 | 1.14.0 |
| 画像の復号 | Pillow 12.2.0（libjpeg-turbo、jpeg 6.2）。`PIL.Image.open(...).convert('RGB')`、torchvision の backend は PIL | 同じ |
| TF32 の既定（新しいプロセス） | matmul False・cudnn True | 同じ |

装置: driver 595.84（nvidia-smi の CUDA 13.2）、電力の上限 300 W（既定 300 W）× 2、最大クロック SM 2,100 MHz・メモリ 8,001 MHz、PCIe gen4 x16。CPU AMD Ryzen 9 7950X（32 スレッド）、メモリ 100,259,065,856 B。nvcc 12.9.86（`/usr/local/cuda`）。`~/.cache/huggingface/accelerate/` は無い（accelerate の既定設定ファイルなし）。
学習のプロセスが読んだ値（TF32・決定性・autocast）は各 run の記録（`*_optimizer_rank*.json`、`initialization_rank*.json`）から取る。

### A-6 起動の設定の差

手本の run は `scripts/run_tower_search.py` の 11ab3747（工程塔）と bce323bc（検出塔）の版で回った。どちらも、二枚へ配る変更 3c562015（2026-10-23）より前の版である。
この版では、fine-tune の後の train の評価・特徴の取り出し・時間ヘッド 10 本と、検出塔の評価を、**一枚目の GPU だけで順に**回す。ヘッドは point の作業場所を共有する。
本契約の管理台本 `run_hostdiff.py` はこの版の順と起こし方に合わせた（今の `run_tower_search.py` の並べ方には合わせていない）。

command.sh（`tools/plan_diff.py`。`A/plan_diff_seed42.json`、`A/plan_diff_seed123.json`）: 手本の各行に許した置き換えを当て、本契約の行と一行ずつ比べた。

- seed 42・123 とも 13 本（finetune・extract・head00〜09・detector）で、**許した違いの他の差は 0 行**
- 差の分類: 経路（repo `/home/ubuntu/local/m2` → `/home/ubuntu/slocal2/m2`）、GPU の番号（`1,2` → `0,1`、`1` → `0`）、出力と記録の置き場（scratch の経路）、seed（`seed=123`、`--seed 123`）。追加の行は `NCCL_P2P_DISABLE=1`、`TOWER_SEARCH_TASK`（識別子）、`TOWER_SEARCH_OBSERVER`（記録）、`TOWER_SEARCH_PHASE_PUBLISH`（置き場）、`TOWER_SEARCH_SEED`（W&B に書く seed）
- 空振りの対照（`--self-test`）: 手本の finetune の `workers=4` を `workers=8` にした写しでは、その行が差に出た

config.yaml（`tools/config_diff.py --seed`。`A/config_diff_seed{42,123}.json`）: hydra で組んだ設定に、`run_ptower_search.py` が足す契約の値を足して、手本と全キーで比べた。

- 12 本（finetune・extract・head00〜09）とも、**許した違いの他の差は 0 キー**（差は task_id・artifact_root・cache・checkpoint、seed 123 では seed）
- 手本にあって組んだ設定に無いキーは、実行時にコードが足すもの（`source_sha256`・`contract_sha256`・`data.*`・`transform_*` など）。実物は学習の後に `--actual` で比べる。`source_sha256` は `scripts/stage1_ptower.py` の要約値で、手本の commit の後にこの台本が変わっている（908aed25・7cf83fed・502e6af7・1afc4ad1。新しいヘッドの候補を足した変更）ため、違う値になる見込み。これは「コード: 起点 origin/phase0 の同じ commit（揃える）」の行（SPEC §3）で、起動の設定ではない
- 検出塔の config.yaml は管理台本が書く（手本と同じキーに `repeat` を足す）
- 空振りの対照（`--self-test`）: 手本の `ft_patience` を 5 にした写しでは `ft_patience` が差に出た

### A-7 道具の合わせ方

`scripts/` の変更（既定の挙動は変えない。上書きは環境変数だけ）:

| ファイル | 変更 | 未設定のとき |
|---|---|---|
| `scripts/tower_search_common.py` | `TASK` を `TOWER_SEARCH_TASK` で上書き（`SCRATCH` も従う）。`load_observer()` を足した（`TOWER_SEARCH_OBSERVER` の台本を読み込む） | dlsta の識別子、観測器なし |
| `scripts/run_ptower_search.py` | 公開先 `PUBLISH` を `TOWER_SEARCH_PHASE_PUBLISH` で上書き。観測器の `install_phase` を呼ぶ | `experiments/phase1/stage1_ptower_search`、呼ばない |
| `scripts/train_relation_detr_search.py` | W&B の設定に書く seed を `TOWER_SEARCH_SEED` で上書き（手本は 42 の固定）。観測器の `install_detector` を呼ぶ | 42、呼ばない |

新しい台本（`tasks/T-2026-11-02-hostdiff-andrew/`）: `run_hostdiff.py`（管理）、`tools/observer.py`（一歩ごとの時刻）、`tools/check_inputs.py`、`tools/env_capture.py`、`tools/plan_diff.py`、`tools/config_diff.py`。
試験: `tests/test_tower_search_overrides.py`（新しい 8 件）と既存の `tests/test_tower_search.py`（9 件）→ 17 passed。壊した写し（既定の識別子を変えた `tower_search_common.py`）で既定の検査が落ちることを試験の中で確かめる（`test_breaking_control_changed_default_fails`）。

### G1

分岐と起点、Relation-DETR、入力、起動の設定（command.sh・config）が一致し、GPU 2 枚が空いている → **通過**。

## B. 工程塔の決定性の確かめ（G2）

- `run_hostdiff.py determinism`、2026-11-02 22:45:03〜22:49:33 JST。seed 42、0 番の設定に `+control_frames=3200 ft_epochs=1` と `TOWER_SEARCH_LOSS_HEX=1` を足した fine-tune を二度（a・b、壁時計 135.0 s・135.0 s）。出力は repo の外 `~/m2-scratch/T-2026-11-02-hostdiff-andrew/determinism/`（control の経路なので repo へ写さない）
- 両 rank の記録: `deterministic_algorithms True、cudnn_deterministic True、cudnn_benchmark False、matmul_tf32 False、cudnn_tf32 False、CUBLAS_WORKSPACE_CONFIG :4096:8`。COCO の重みを読んだ行 `load pretrained COCO backbone … sha256=a755b3eb…` が二回とも両 rank にある
- `tools/compare_determinism.py a b`（`determinism/compare.json`）:

  | rank | micro-step | optimizer step | 損失の列の sha256（a・b） | 一致 |
  |---|---|---|---|---|
  | 0 | 200・200 | 50・50 | 3cd3c19c313a27b3…・同じ | 一致（bit 単位） |
  | 1 | 200・200 | 50・50 | 4a89babb4fda3f8a…・同じ | 一致（bit 単位） |

- 空振りの対照（`--self-test`、二回目の列の 100 番目の値の最下位 bit を反転）: 両 rank とも不一致、最初の差は 100 番目
- epoch の平均損失 1.288784 は a・b とも同じ
- **G2 通過**

### B-1 試行の実物の config.yaml（`determinism/config_diff_actual.json`）

手本と比べた差: 許した欄（task_id・contract_sha256・artifact_root・cache）のほか、`control_frames`・`ft_epochs`・`data.train_frames`・`data.val_frames`（試行だけの値。本測定には付かない）と `source_sha256`。
`source_sha256` は `scripts/stage1_ptower.py` の要約値（手本 4ec5b574…、本契約 77485307…）。手本の commit 11ab3747 の後に、新しいヘッドの候補を足す変更が入った（`train`・`evaluate`・`build_model`・`load_fold` に分岐の追加）。
既存の候補 A・B・C の出力が変わっていないことは `tests/test_stage1_ptower_heads.py` が固定の要約値で確かめる。andrew で 35 passed・4 skipped（CUDA が要る mamba の 2 件ほか）。`test_existing_candidates_match_baseline` の 5 件と `test_new_keys_are_absent_from_the_default_config` が通った。
判断: これは SPEC §3 の「コード: 起点 origin/phase0 の同じ commit（揃える）」の行であって、§4 の起動の設定ではない。手本の版のコードへ戻すと §3 に反する。止めずに続け、逸脱として報告に書く。

## C 前. 検出塔の経路の対照（本測定に数えない）

- 検出塔の学習の経路（観測器・warmup の LinearLR・COCO の読み込み）を、`TOWER_SEARCH_CONTROL_STEPS=60`・`--max-epochs 1` で一度だけ確かめた。2026-11-02 22:50〜22:52 JST 頃、`~/m2-scratch/T-2026-11-02-hostdiff-andrew/controls/detector_seed42/`
- exit 0。`load pretrained from …/relation_detr_resnet50_800_1333_coco_1x.pth` と `CONTROL_COMPLETE` が両 rank に出た。`initialization_rank0.json` は matched True・sha256 2d2c19a7…。autocast fp16。プロセスが読んだ値は tf32_matmul False・tf32_cudnn True・deterministic_algorithms False・cudnn_benchmark False
- 観測器は rank ごとに 60 歩の optimizer step の時刻を書いた。ログの `raise ValueError(...)` などの 2 行は、設定ファイルの本文の色付きの印字で、Traceback は 0 件
- MS-Deform-Attn の `.so` は作り直されていない（d1d9d1ac…、`.ninja_log` の最後の行は 13:27:34 UTC のまま）

## C の途中の所見（2026-11-03 04:20 JST）

- 段ごとの壁時計（`*.timing.json` の `wall_s`）は、監督の処理が子の終わりを 5 秒ごとに見る（`run_hostdiff.py` の `stopping.wait(5)`）ため、**5 秒の刻み**で丸まる。ヘッド一本 10.0 s・記録の段 5.0 s・特徴の取り出し 245.0 s はこの刻みの値であり、実際の所要はその値以下 5 秒の幅に在る。一歩の秒数と epoch の秒数は観測器が `time.perf_counter` で書くので、この刻みを受けない。
- 工程塔 seed 123: 01:21:32 開始、04:19:47 終了（JST）。上限 36 epoch に達していない（停止 epoch 23）。COCO の重みを読んだ記録あり。本契約以外の GPU の使用なし。
- 検出塔 seed 42a: 04:19:52 JST に `load pretrained from .../relation_detr_resnet50_800_1333_coco_1x.pth` の行を確認。

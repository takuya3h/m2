# audit — T-2026-10-17-tower-reselect-prereq

実行ホスト andrew（`hostname` = `Andrew`）、repo `/home/ubuntu/slocal2/m2`、分岐 `feat/tower-reselect-prereq`。
時刻は JST。装置は使っていない（§G-3）。

## 0. 開始

### 0-1 状態の判定（task-start の前）

    $ git branch --show-current            → feat/frame-signal-audit
    $ git status --porcelain -uall         → （空）
    $ git branch --list feat/tower-reselect-prereq → （空）
    $ git ls-remote --heads origin refs/heads/feat/tower-reselect-prereq → （空）
    $ git log --all -1 -- tasks/T-2026-10-17-tower-reselect-prereq → （空）
    $ ls -d tasks/T-2026-10-17-tower-reselect-prereq → No such file or directory
    $ cat .sync-pause                      → No such file or directory

判定は「清浄」。**開始前に `.sync-pause` は無かった。** 未追跡も無く、退避したものは 0 件（`~/m2-evacuated/` は
§D-2 の `main.py` の退避で初めて作った）。

### 0-2 task-start（2026-10-17 05:2x JST）

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-17-tower-reselect-prereq
    [task-start] 分岐を作成: feat/tower-reselect-prereq（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら make task-release ... END=complete）
    OK   T-2026-10-17-tower-reselect-prereq
    [task-start] 完了。

目印は **「作成」**（本契約が置いた）。中身は `task_id=T-2026-10-17-tower-reselect-prereq` / `branch=feat/tower-reselect-prereq`。
稼働中の `~/bin/m2-sync.sh` は `grep -c sync-pause` = 2（対応済み）。

### 0-3 検証とプリフライト

- `make task-validate` → `OK`、WARN なし
- `make task-preflight`（1 回目）→ `5 PASS / 0 WARN / 8 SKIP / 1 FAIL`。FAIL は `P6 decisions_answered`（未回答 2 件）
- 利用者に提示して停止。回答（2026-10-17）: 決定 1 = 発火した時点で停止して諮る。決定 2 = 残す（上書きしない）。
  記録 = `meta.amendments` に追記して `decisions_required` を空にする
- `spec.yaml` に amendment を 1 件追記（reason に回答の全文）。`make task-validate` → OK
- `make task-preflight`（2 回目）→ `6 PASS / 0 WARN / 8 SKIP / 0 FAIL`

SKIP 8 件: P2 cuda_ext_loaded、P3 deterministic_flags、P4 prereg_committed、P5 frozen_source_hash、
P11 gpu_free、P12 refs_resolved、P13 symmetry_table_complete、P14 proposal_card_checked。

### 0-4 参照の解決

`contract.inject_verbatim` の 4 アンカーは、`context/conventions.md` の `073f9dc0` 版（HEAD と同一）の原文を読んだ。
`prohibitions`（99-107 行）、`issuer_cautions`（151-187 行）、`env_p0`（110-119 行）、`symmetry`（321-360 行）。
原文は repo の当該版にあるため、ここに写さない（行番号は本契約の変更前）。
`inputs.denominator` と `inputs.frozen_source` は契約に無い。凍結源は §B で `conventions#frozen_source` の正本と照合した。

## A. 開始状態

### A-1 分岐と起点

    $ git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0
    31af81e7720db51372a1659c844e7806a3b36563   （3 つとも同じ）

分岐 `feat/tower-reselect-prereq`（`feat/` で始まる）。起点 `origin/phase0` = `31af81e7`。
`context/env-facts.md` の repo の位置（andrew は `~/slocal2/m2`）と一致。

### A-4 装置（開始時、2026-10-17 05:34 JST）

    $ nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv
    0, NVIDIA RTX A6000, 37480 MiB, 99 %
    1, NVIDIA RTX A6000, 37480 MiB, 97 %
    $ nvidia-smi --query-compute-apps=pid ... ; readlink /proc/PID/exe
    1493750 -> /usr/bin/python3.12  （起動 2026-10-15 07:02:39、argv0 /usr/bin/python3、引数は libcuda を ctypes で掴む常駐）
    1493762 -> /usr/bin/python3.12  （起動 2026-10-15 07:02:40、同上）

**本契約の処理ではない**（本契約の開始より前に起動、venv の実体 `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` ではない）。

### A-5 起票時の値

| 項目 | 起票時 | 実測 | 差し替え |
|---|---|---|---|
| `conventions_rev`（`git log -1 -- context/conventions.md`） | 073f9dc0 | 073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6 | 不要 |
| `runindex_commit`（`git log -1 -- runindex/`） | 63ae65da | 63ae65da8c7d32df591f5e2ee4358286b72c726b | 不要 |
| index / experiments / verdicts（行数 − 1） | 1961 / 750 / 1506 | 1961 / 750 / 1506 | 不要 |

### A-6 試験（開始時の値）

1 回目（`--continue-on-collection-errors` なし）は収集エラーで全体が中断した:

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE
    ERROR tests/test_stage1_dtower_convergence.py - FileNotFoundError: [Errno 2] No such file or directory:
          '/home/ubuntu/slocal2/m2/third_party/Relation-DETR/util/convergence.py'
    !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!

2 回目（`--continue-on-collection-errors` 付き）:

    6 failed, 793 passed, 22 warnings, 1 error in 22.32s
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    ERROR  tests/test_stage1_dtower_convergence.py   ← 収束規則の試験は開始時に収集エラー（完了判定 e の四列目）

**関門 G1: pass。** 分岐 `feat/`、起点 `origin/phase0`、装置を使わないことと失敗の名前を記録した。

## B. andrew の検出器のソースの棚卸し

### B-1 在る場所

| 方法 | 結果 |
|---|---|
| `find / -xdev -type d -name 'Relation-DETR*'` | **0 件**。`-xdev` のため `/home/ubuntu/slocal2`（別の FS `/dev/sdc1`）に降りなかった |
| `find /home /opt /data /mnt /srv -type d -name 'Relation-DETR*'` | `m2/third_party/Relation-DETR`、その入れ子 `.../third_party/Relation-DETR`（`data/processed/**/*.bin` だけ）、`third_party_snapshot/{philip,Bengio,efros,lecun}/Relation-DETR` |

検出器のソースは `/home/ubuntu/slocal2/m2/third_party/Relation-DETR/`（git の作業ツリー、HEAD `b485955`）。
`git status` は改変 3（`optimizer/param_dict.py` `transforms/presets.py` `util/engine.py`）と未追跡 68（本体 31 + `per_class_coco_map` 12 + 入れ子の `.bin` 25）。

### B-2 四つの集合の前の値

道具: scratchpad の `inventory.py`（下の定義で sha256 を取る。付録 1 に全行）。

| 集合 | 定義 | 件数 |
|---|---|---|
| src | `third_party/Relation-DETR/` の全ファイルから `.git` `__pycache__` `checkpoints` `per_class_coco_map` 入れ子 `third_party` と `.pyc .pth .pt .bin` を除く | 151 |
| ext | `~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/` の全ファイル（`.so` `.cuda.o` `build.ninja` `.ninja_log` `.ninja_deps`） | 5 |
| ckpt | `third_party/Relation-DETR/checkpoints/` の全ファイル（凍結源を含む） | 12 |
| weights | `data/external/weights/relation_detr*.pth` | 2 |

拡張は `models/bricks/ms_deform_attn.py:15-26` の `torch.utils.cpp_extension.load` による JIT で、**`torch.cuda.is_available()` が真のときだけ**
ビルドと読み込みが起きる。`third_party/Relation-DETR/` の中に `.so` と `build/` は無い。

凍結源: `checkpoints/incoming/seed42/best_ap.pth` = `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824`、195421066 bytes。
**`conventions#frozen_source` の正本と一致。**

### B-3 二周目の写しと照らした欠け

- `util/convergence.py`: **無い**
- `main.py`: `grep -c convergence` = 0。写しの抜粋の照合は 61 行中 0 行一致（§C-3 の陰性側）
- 二周目の D\*-COCO の設定 `configs/train_config_egosurgery_seed42.py`: **在る**（efros の版と同一。§C-5）
- 二周目の D\*-ImageNet の設定 `configs/train_config_egosurgery_stage1_imagenet_seed{42,123,456}.py`: 無い

### B-4 2026-08-02 の efros の snapshot との照合

snapshot の版を一時の場所に組み立てた（andrew の `.git` から `git archive b485955c…` → `patch -p1` → tarball を展開）。

    $ diff -rq -x .git -x __pycache__ -x checkpoints -x third_party -x per_class_coco_map -x '*.pyc' <efros0802> third_party/Relation-DETR
    Only in /home/ubuntu/slocal2/m2/third_party/Relation-DETR: data      ← 空のディレクトリ
    $ diff -rq <efros0802>/per_class_coco_map third_party/Relation-DETR/per_class_coco_map → 差なし

**どの snapshot にも無い andrew だけの改変は 0 件。** 決定 2（残すか置き換えるか）は発火しなかった。

## C. efros の実体の取り寄せ

### C-1 経路

- `~/.ssh/config.d/aolabnet.conf` の `Host efros`（192.168.196.227:50072）へ andrew から**直接**届いた。中継は使っていない
- `context/env-facts.md` と SPEC §3 は「直接接続は不可で中継が要る」と書くが、実測では直接届いた（`hostname` → `efros`）
- 既知のホスト: `ssh-keygen -F "[192.168.196.227]:50072"` → 既知。念のため `~/.ssh/known_hosts` の写しを scratchpad に作り、
  `-o UserKnownHostsFile=<写し> -o StrictHostKeyChecking=yes -o BatchMode=yes` で接続した。`~/.ssh/known_hosts` の sha256 先頭 16 桁は前後とも `1e5ff1f5e8af7b7c`
- 資格情報は既存の鍵で足り、パスワードは求められなかった

### C-1' efros で使った操作（すべて読むだけ）

git の `status` は index を書き換えうるため、すべて `GIT_OPTIONAL_LOCKS=0` を付けた。

| 時刻 | 命令（`cd ~/slocal2/m2/third_party/Relation-DETR &&` に続く部分） | 実行 |
|---|---|---|
| 12:28:10 | `git rev-parse HEAD`、`git diff --name-only`、`git status --porcelain -uall`、`sha256sum` 4 件、`git -C ~/slocal2/m2 rev-parse HEAD` と `branch --show-current` | 実行 |
| 12:28:31 | 一覧・diff・tar・sha256 の 4 本 | **一覧だけ未実行（rc=127）**。zsh で `$SSH` が単語分割されず ssh が起動しなかった。残り 3 本も同様 |
| 12:28:43 | 未追跡の一覧（`git status ... | sed | grep -v`） | 実行 |
| 〃 | diff・tar・sha256 の 3 本 | **未実行**。前の ssh が heredoc の残りを標準入力として読み込んだ |
| 12:28:56 | `git diff b485955c…`（標準出力へ） | 実行 |
| 12:28:56 | 未追跡の一覧 `| tar czf - ... -T -`（標準出力へ） | 実行 |
| 12:28:57 | 未追跡の一覧 `| xargs sha256sum`、`sha256sum` 改変 4 件 | 実行 |

**efros への書き込み 0。** 導入・学習・試験・設定の変更はしていない。efros 以外のホストには接続していない。
取得時の efros の m2: HEAD `57717f6c`、分岐 `feat/legacy-exclusions-and-type-sync`。

efros の状態: HEAD `b485955c…`、改変 4（`main.py` が 2026-08-02 版より増えた）、未追跡は本体 35 + `per_class_coco_map` 31 + 入れ子の `.bin` 25。

### C-3 二周目の写しとの照合（比較元 = 写し `experiments/baselines/stage1_dtower_r2/impl/`、比較先 = efros の実体）

| 照合 | 比較元 | 比較先 | 結果 |
|---|---|---|---|
| sha256 | `convergence.py.txt` = `299597a2…6456514d` | efros `util/convergence.py` = `299597a2…6456514d` | 一致 |
| 行番号つき抜粋 | `main_py_arguments.txt`（23 行） | efros `main.py` | 23/23 一致 |
| 行番号つき抜粋 | `main_py_training_loop.txt`（61 行） | efros `main.py` | 61/61 一致 |

道具: scratchpad の `excerpt_match.py`（`  NNN\t本文` の各行が対象の NNN 行目と完全一致するかを見る。全行一致で rc=0）。

**対照（完了判定 a の四列目）**

| 入力 | 期待 | 実測 |
|---|---|---|
| `convergence.py.txt` の `patience` を 1 文字変えた写し（`cmp -l` で 1 byte 差） | sha256 不一致 | 不一致 |
| `main_py_arguments.txt` の `max-epochs` を `max-epocks` にした写し（1 byte 差） | rc=1 | `matched=22 mismatched=1`、rc=1（60 行目を名指し） |
| `main_py_training_loop.txt` を andrew の変更前の `main.py` に当てる | 不一致 | `matched=0 mismatched=61` |

**関門 G2: pass。** efros に届き、収束規則の実装が写しと一致した。決定 1 は発火しなかった。

### C-4 新しい snapshot

取り寄せた patch（762 行）・tarball（22865 bytes、35 件）・sha256（39 件）を一時の場所で上流に当てて組み立て、
`sha256sum -c` で 39 件すべて OK。`third_party_snapshot/efros/2026-10-17/Relation-DETR/` に置いた。

| ファイル | 内容 |
|---|---|
| `reldetr_upstream_mods.patch` | 上流 `b485955c` への改変 4 件 |
| `reldetr_project_files.tar.gz` | 未追跡のソースと設定 35 件 |
| `tar_contents.txt` / `file_list.txt` / `sha256sums.txt` | tarball の一覧 35 / efros の `git status`（`__pycache__` を除く 95 行）/ efros で測った sha256 39 |
| `diff_vs_2026-08-02.txt` | 2026-08-02 版との差 |
| `README.md` | 出所の記録 |

含めないもの: checkpoints、学習の出力、入れ子の `.bin` 25（データ）、`per_class_coco_map` 31（評価の出力の json）、拡張の生成物、`__pycache__`。

**完了判定 f の四列目**: repo に置いた tarball を一時の場所に展開した一覧 = `tar_contents.txt`（35 件、`diff` 差なし）。
上流 + repo の patch + 展開で組み立てた木が `sha256sums.txt` の 39 件すべてに一致。
既存の復元スクリプトの読み方（`SNAP=third_party_snapshot/${HOST}/Relation-DETR`、`HOST=efros/2026-10-17`）で patch と tarball が見つかる（`ls` で確認。clone はしていない）。
陽性対照: 組み立てた木の `util/convergence.py` を 1 文字変えて同じ `sha256sum -c` を回すと `util/convergence.py: FAILED`、rc=1。

### C-5 2026-08-02 版との差

    Only in efrosNew/configs: train_config_egosurgery_stage1_imagenet_seed123.py
    Only in efrosNew/configs: train_config_egosurgery_stage1_imagenet_seed42.py
    Only in efrosNew/configs: train_config_egosurgery_stage1_imagenet_seed456.py
    Files efros0802/main.py and efrosNew/main.py differ
    Only in efrosNew/util: convergence.py

`main.py` の `diff` は 492 行だが、上流の版が CRLF で efros の版が LF であるため。`--strip-trailing-cr` で 72 行。
`optimizer/param_dict.py` `transforms/presets.py` `util/engine.py` `configs/train_config_egosurgery_seed42.py` は差 0 行。
ImageNet 用の設定と seed42 の設定の差は `resume_from_checkpoint`（COCO 重み → `None`）の 4 行だけ。

### C-6 既存の snapshot の不変

`third_party_snapshot/` の全ファイル（新しい場所を除く）の sha256 を置く前と後で比べ、65 件すべて一致。
（`third_party_snapshot/efros/` の mtime が 2026-10-16 20:34 UTC になっているのは L3 の P7 の書き込み試験による。ファイルは不変）

## D. andrew への復元

### D-1/D-2 置いたもの（前後の要約値）

退避: `main.py` の変更前の版を `~/m2-evacuated/T-2026-10-17-tower-reselect-prereq/third_party/Relation-DETR/main.py` へ `cp -p`。
退避した版の sha256 = `6c14063a…` = 前の値（一致を確かめてから上書き）。

| path | 前 | 後 | 操作 |
|---|---|---|---|
| `main.py` | `6c14063af155bea99fc43e3c14d1c28dcb2b9d8c07f98b96a45eb4ca9b57e641` | `ffbd6deb9ad48ec348f05f4eff8f949e97647dd74b996689af5477db8d281415` | 上書き |
| `util/convergence.py` | − | `299597a252674450babf7b31f889fd752848ec2dac070215223706ee6456514d` | 追加 |
| `configs/train_config_egosurgery_stage1_imagenet_seed42.py` | − | `c252e9c90329fe885cb8befc9893b845e566300c4be249a3ccf5c0625bf58afe` | 追加 |
| `configs/train_config_egosurgery_stage1_imagenet_seed123.py` | − | `92275cc9548d1f9bfe4849e51365a35034e959a808d6aebb97297552051534d0` | 追加 |
| `configs/train_config_egosurgery_stage1_imagenet_seed456.py` | − | `8a72d01fce0fe820199bdb706563006ba996754f2ec8acddc68a4d9872ae5929` | 追加 |

後の値は efros で測った `sha256sums.txt` の該当 5 行と `sha256sum -c` で全件 OK。
依存: `main.py` が新しく import するのは `util.convergence`、`accelerate.utils.broadcast`（`.venv-relation-detr` の accelerate 1.14.0 に在る）、`json`。
ほかの改変 3 件と D\*-COCO の設定は andrew と efros で同一なので置いていない。

### D-4 動く状態の確認

**収束規則の試験**（`.venv-relation-detr` に pytest が無いため本体 `.venv` で実行。試験は torch を import しない）:

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -p no:cacheprovider -v tests/test_stage1_dtower_convergence.py
    collected 9 items ... 9 passed in 0.02s

**引数**（検出器の環境、装置なし、`PYTHONDONTWRITEBYTECODE=1`）:

    $ cd third_party/Relation-DETR && CUDA_VISIBLE_DEVICES="" ../../.venv-relation-detr/bin/python main.py --help
      [--convergence-schedule] [--plateau-patience PLATEAU_PATIENCE] [--plateau-factor PLATEAU_FACTOR] [--max-epochs MAX_EPOCHS]

**二周目の命令行と設定の解釈**（`dcoco_foldA_seed42/command.sh` と同じ引数と `EGO_ANN_DIR`。`main.parse_args()` と `Config(...)` だけを呼ぶ。
モデルの組み立て、重みの読み込み、`update_checkpoint_path` は呼ばない。`RELDETR_OUTPUT_DIR=/nonexistent/...` で出力先が作られないことも確かめた）:

    cuda_available False
    args {'config_file': 'configs/train_config_egosurgery_seed42.py', 'seed': 42, 'mixed_precision': 'fp16',
          'convergence_schedule': True, 'plateau_patience': 4, 'plateau_factor': 0.1, 'max_epochs': 36}
    cfg.num_epochs 12 batch_size 2 max_norm 0.1 lr 0.0001
    cfg.model_path configs/relation_detr/relation_detr_resnet50_egosurgery.py
    cfg.resume_from_checkpoint /home/ubuntu/slocal2/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
    train ann 9657 val imgs 1515
    test_dataset transforms None
    schedule PlateauSchedule(patience=4, factor=0.1, best=None, ...)
    $ ls -d /nonexistent → No such file or directory

二周目の `config.yaml`（lr 0.0001、batch_size_per_gpu 2、max_norm 0.1、patience 4、factor 0.1、max_epochs 36）と一致。

### D-5 後の値

    ext/ckpt/weights: 19 件すべて一致（前後の TSV を diff。付録 1・2）
    src の差: main.py（sha 変化）と追加 4 件だけ

**関門 G3: pass。**

## E. 検出塔の評価時の入力の大きさ

### E-1 経路（実装の行）

| 段 | 行 |
|---|---|
| 評価の道具がデータセットを作る（`--split` 指定時。未指定なら config の `test_dataset`） | `scripts/eval_relation_detr_map.py:73-77`（`transforms=None`）、`:79-81` DataLoader（batch 1） |
| config の `test_dataset` | `configs/train_config_egosurgery_seed42.py:53`（`transforms=None`）。学習側だけ `:47` `transforms=presets.detr` |
| collate は束ねるだけ | `util/collate_fn.py:8-9` |
| モデルへ渡す | `util/engine.py:115` `model(images)` |
| 前処理の呼び出し | `models/detectors/relation_detr.py:54` → `base_detector.py:200-202` `DETRDetector.preprocess` → `:119-130` `BaseDetector.preprocess_image` |
| 大きさの変換 | `base_detector.py:45-50` `EvalResize`（`r = min(800/短辺, 1333/長辺)`、`(orig*r).to(int)` で切り捨て）。`:75` で `min_size=800, max_size=1333` |
| pad | `util/misc.py:95-98` `image_list_from_tensors`（32 の倍数へ切り上げ）。`size_divisible` は `BaseDetector.__init__` の既定 32（`RelationDETR.__init__` は `super().__init__(min_size, max_size)` だけ） |
| 大きさの引数 | `configs/relation_detr/relation_detr_resnet50_egosurgery.py:91` `min_size=800, max_size=1333` |

`presets.detr` は `train_dataset`（`train=True`）だけに付く。評価の経路の `test_dataset` と評価の道具のデータセットは `transforms=None`（E-4）。

### E-2/E-3 実測（`.venv-relation-detr`、装置なし、重みなし、モデルを組み立てない）

道具: scratchpad の `measure_eval_input.py`。`BaseDetector(min_size=800, max_size=1333).eval()` の `preprocess_image` を直に呼ぶ。
評価の経路が同じ関数を通ることをクラスの解決順で示した。

    [path] RelationDETR.preprocess       is DETRDetector.preprocess: True
    [path] RelationDETR.preprocess_image is BaseDetector.preprocess_image: True
    [path] RelationDETR.__init__ の super 呼び出し: ['super().__init__(min_size, max_size)']
    [path] BaseDetector.__init__ の既定 size_divisible: 32
    [data] ann=.../egosurgery_tool/instances_val.json images=1515 注釈上の (H,W) 分布={(1080, 1920): 1515}
    [real] i=0    file=val/09/09_1_0213.jpg dtype=torch.uint8 原寸(H,W)=(1080, 1920) 縮小後=(749, 1333) pad後=(768, 1344) 一致=True
    [real] i=757  file=val/10/10_1_0553.jpg ... 原寸(H,W)=(1080, 1920) 縮小後=(749, 1333) pad後=(768, 1344) 一致=True
    [real] i=1514 file=val/10/10_2_0299.jpg ... 原寸(H,W)=(1080, 1920) 縮小後=(749, 1333) pad後=(768, 1344) 一致=True
    [neg] 同じ入力の二度目: 縮小後=(749, 1333) pad後=(768, 1344) テンソル同一=True
    [pos] 入力(H,W)=(1080, 1080) 縮小後=(800, 800)   pad後=(800, 800)   期待=(800, 800)/(800, 800) 一致=True
    [pos] 入力(H,W)=(1920, 1080) 縮小後=(1333, 749)  pad後=(1344, 768)  一致=True
    [pos] 入力(H,W)=(480, 640)   縮小後=(800, 1066)  pad後=(800, 1088)  一致=True
    [pos] 入力(H,W)=(1080, 1920) 縮小後=(749, 1333)  pad後=(768, 1344)  一致=True

原寸の分布（読み取りのみ）: `data/annotations/egosurgery_tool*/**/instances_*.json` の 21 ファイル、延べ 108,059 枚がすべて (W,H) = (1920, 1080)。

画像そのものと派生物は repo に入れていない（大きさの数値だけを記録した）。

### E-5 計算値との対照

| 量 | `REPORT.md:200`（計算値） | 実測 |
|---|---|---|
| 縮小後（W×H） | 1333×750 | **1333×749** |
| pad 後（W×H） | 1344×768 | 1344×768 |

差は丸め。1080 × 1333/1920 = 749.81 を、実装は `.to(int)` で切り捨てる（`base_detector.py:49-50`）。

## F. 規約と README

### F-1/F-2 規約の差分の突き合わせ（完了判定 h・i の四列目）

**symmetry（SPEC §5.1）**

| SPEC §5.1 の項 | 規約の行（変更後） | 一致 |
|---|---|---|
| 理由 1 仮説の操作である | 347 | 同文 |
| 理由 2 タスクの性質上避けられない | 348 | 同文 |
| 理由 3 各塔の構造の標準の処方である | 349 | 同文 |
| 使える比較: 類型「塔どうし」だけ | 360 | 同文 |
| 使える行: 正規化層の扱い、学習率、勾配の刈り込み、weight decay、実効 batch、数値精度、決定性 | 361 | 同文（7 項目） |
| 使える条件: 主判定に入らない／比べる腕と分母が同じ受け取り手 | 362 | 同文 |
| 使えない行: 初期化の鎖の各段、in-domain のデータの範囲、相手タスクのラベルを使わないこと、収束規則 | 363 | 同文（4 項目） |
| 同じ塔の変種どうし（確定塔、交差適合用の塔、診断点の塔）には使わない。変える一点以外を揃える | 365 | 同文 |
| 理由の欄に「各塔の構造の標準の処方」と書き、両腕の実際の値を書く | 366 | 同文 |
| 出所: 利用者の決定 2026-10-17 | 367 | 同文（契約名を添えた） |

足した文: 355-356 行の説明 2 文は SPEC §2 の利用者の決定（2026-10-17）の言い換え。範囲・条件・数は変えていない。

**frame_sets（SPEC §5.2）**

| SPEC §5.2 の項 | 規約の行 | 一致 |
|---|---|---|
| アンカー `frame_sets` | 411 | `validate_task.conventions_anchors()` に `frame_sets` が現れる |
| 用途の表 5 行 | 418-422 | 同文 |
| 規則 4 項 | 426-429 | 同文 |
| 数 17,233 / 15,437 / 1,796 | 418-419 | `REPORT.md:14`（17,233）、`:15`（15,437）、`:22`・`:43`（1,796）と一致 |

### F-3 変更履歴

150 行に本契約の行を足した。commit の欄は本契約の commit（§G-5）。

### F-4 README

`README.md` の Relation-DETR の節「未検証・残り」の 🔴 の項を、解消の記録に置き換えた。末尾に本契約の節を足した。

### 規約の変更が既存の読み手に与える影響

- `tests/test_symmetry_gate.py`（symmetry 節の列名と三値を読む）: 51 passed
- `scripts/analysis/design_val_subsets.py` の `parse_det_groups`: 変更後も標的群 5・陰性対照群 4 を返す
- L3 の P13 は理由の欄が空でないことだけを見る（`tools/preflight_task.py:659-663`）。文言には依存しない
- `crossfit` 節は、これまで文書の末尾までだったが、`frame_sets` のアンカーまでになった。`crossfit` を節で切り出す道具は repo に無い（`grep`）

## G. 検証

### G-1 検査

    $ make task-validate TASK=...   → OK（規約の変更の commit 前。commit 後は L2-6 の WARN が出る想定）
    $ make forbidden-check TASK=... → status pass、changed 11、violations []、permitted: context/conventions.md（allow_write）
    $ make spec-check TASK=...      → status pass、rules_checked 9、hits 0

`make taskindex-check` と `make inbox-check` は回していない（SPEC §6-8）。

### G-2 試験（後の値）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 802 passed, 22 warnings in 21.86s

失敗の名前の集合の前後差（`diff`）: 前にだけ在るのは `tests/test_stage1_dtower_convergence.py`（収集エラー）の 1 件。後にだけ在るもの 0。
802 = 793 + 9（収束規則の試験）。

### G-3 装置（終了時、2026-10-17 12:35 JST）

    0, 37480 MiB, 99 % / 1, 37480 MiB, 97 %
    1493750 -> /usr/bin/python3.12 （起動 2026-10-15 07:02:39、argv0 /usr/bin/python3）
    1493762 -> /usr/bin/python3.12 （起動 2026-10-15 07:02:40、argv0 /usr/bin/python3）

開始時と同じ 2 プロセスだけ。venv の実体（`readlink -f .venv*/bin/python` = uv の python3.11）と `exe` の完全一致 0、
argv0 と venv の経路の完全一致 0。陽性対照として自分のシェルは `exe=/usr/bin/zsh argv0=/usr/bin/zsh` と読めた。
**本契約の装置の使用 0。** 検出器の処理は全件 `CUDA_VISIBLE_DEVICES=""` で動かし、`torch.cuda.is_available()` = False を表示か assert で確かめた。

### G-4 data 配下

`data/` へは読むだけ（注釈 json と画像 3 枚）。`git status` に `data/` の変更なし。`forbidden-check` の violations 0。

### 変更範囲

| 経路 | 種別 |
|---|---|
| `context/conventions.md` | 変更（allow_write） |
| `README.md` | 変更 |
| `third_party_snapshot/efros/2026-10-17/Relation-DETR/`（7 ファイル） | 追加（allow_write） |
| `tasks/T-2026-10-17-tower-reselect-prereq/`（spec.yaml、SPEC.md、audit.md、RESULT.md、result.yaml） | 追加 |
| `tasks/inbox.d/T-2026-10-17-tower-reselect-prereq.md` | 追加 |
| repo の外: `third_party/Relation-DETR/`（版管理の外）に 5 件、`~/m2-evacuated/T-2026-10-17-tower-reselect-prereq/` に退避 1 件 | − |

## 付録 1. 四つの集合の前の値（set / path / sha256 / bytes）

```
src	.gitignore	3aaba4c6a1311cf56476085e8cf57b0abd712460041214b827e399cc73640221	3171
src	LICENSE	c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4	11357
src	README.md	8bbe6e4b38e41c8043469e0d81c4d0ad08e47743cb6772790120ddd3dd409253	16656
src	inference.ipynb	22847b7c5b7110aa32ddd00da2ffba4456fa801c32a2472d891985fa81c476e2	377492
src	inference.py	0a3ec3e806ea19cd329eaa1c6d0f1dda7459425c524d9150408fb3d49cf6b72e	5766
src	main.py	6c14063af155bea99fc43e3c14d1c28dcb2b9d8c07f98b96a45eb4ca9b57e641	9337
src	requirements.txt	c68d308fc092b6247aa096b4e5159acb333a8cb90fb78a0c019a1047be0243de	110
src	test.py	48e9a96e16770726769026a357508041cdd3815e003636842e02a5775ee8e3c1	7939
src	.github/ISSUE_TEMPLATE/bug-report-chinese.yml	e21ec49926442fca3ebddf7b8ad4679a52d096195062ed97347c28502b079b6c	1358
src	.github/ISSUE_TEMPLATE/bug-report-english.yml	da0a885e4f142b64d4dd62384c051d1562f2c97ae61c4f0cf6245be5b8b8e434	1355
src	.github/ISSUE_TEMPLATE/feature-request-chinese.yml	b4ab573bfb29316fe98112846b439b74dbf52cb53010c381ff0415b2de5bda18	821
src	.github/ISSUE_TEMPLATE/feature-request-english.yml	4be9f49cba1ceb4babf119b8bacb91e8e67a9fd60365673b47e00658de07466f	819
src	.github/ISSUE_TEMPLATE/question-chinese.yml	b376f38189ede339c230a7ed316194ab47285a2025c98799f12b1cfcd236e48a	592
src	.github/ISSUE_TEMPLATE/question-english.yml	dd4440aca1a2f25ec2cd14a0449012439bc41a96f3186ca622c3ea03516b483a	584
src	configs/train_config.py	11a75d4a4f849673c58d60be2130249280d50124fa561829f7d60003fe7b8080	1880
src	configs/train_config_egosurgery.py	e28a9dff0428cb57eb76a397e38d6758c995af3f541e727885ac7b972757a0fa	2706
src	configs/train_config_egosurgery_s0_frozen.py	3a0e88485c16e528fee67efa0c64ec195a3989825de833c70d3465ab1e039417	1966
src	configs/train_config_egosurgery_s0_frozen_neck.py	841f1befdbce0296abacb8476cb61f95e3aceea3e528e817cd35d28521f49ca7	2413
src	configs/train_config_egosurgery_seed123.py	41a931aad26838a75bb87e1a664faf0ad6a904ffd6e5b6d97c4c0a767dcd3d29	3230
src	configs/train_config_egosurgery_seed42.py	509c4a5923e4948115ccd8712cf7f85050a269998ec1e50f81d9fd10d98c2bc7	3229
src	configs/train_config_egosurgery_seed42_augstrong.py	7d07d8a7799edc906babd681065c6a92598eaf839c11de53aab0081e3ca18083	2937
src	configs/train_config_egosurgery_seed42_augstrong_hires.py	c173d76e71486a072a5337628f698508fed9a9cb78a5c4c0adea80cec564ef31	2904
src	configs/train_config_egosurgery_seed42_hires.py	ae93906a17e1e2648930d48ba95693abfe07202e68084864ce643bf3dfee614d	2865
src	configs/train_config_egosurgery_seed456.py	5efceac791433b63a386b2815e3a0d56b685274599fcfd6eb75a677c7a1456d3	3230
src	configs/train_config_egosurgery_smoke.py	efb1f56231c47e252e817f015428f2571775c46f9fd9c4fd71b931ba84acc57a	2701
src	configs/dab_def_detr_pp/dab_def_detr_pp_resnet50_800_1333.py	c78327fe95417a11886bfd26cd30160226aa8aa2497957354445ddcf70471204	3113
src	configs/deformable_detr_pp/def_detr_pp_resnet_800_1333.py	3c4afa3361b4d33be6e1f9b22f07fe0db5d16a32ab497f937faebe8e0f165ed2	3265
src	configs/dino_pp/dino_pp_resnet50_800_1333.py	67063a87a1aaeb344dce4d6f96bd78e2cb45910e3ab759c1efc35e5acbc40d85	3219
src	configs/dn_def_detr_pp/dn_def_detr_pp_resnet50_800_1333.py	c8594b76f90430f2f9d89b1ed3707189f673ef11a9f69e8c1c7767c9551e0f73	3099
src	configs/relation_detr/relation_detr_convnext_l_800_1333.py	9a868c99a32a853345103f9734449bbd2325e73e6f115952862ed62c214610ff	3570
src	configs/relation_detr/relation_detr_focalnet_large_lrf_fl4_1200_2000.py	8cc67d50046269cdf1073f89cf5dda9f185caf4dd985ca067a41dbc7bbda906e	3450
src	configs/relation_detr/relation_detr_focalnet_large_lrf_fl4_800_1333.py	9994b4ee2408b8407efcab3af8df8daba19376090a7c062446cde278b545d006	3552
src	configs/relation_detr/relation_detr_resnet50_800_1333.py	4d50d9b9dd231e250abb481c35ca7ba1416df2e4053a48a4c01befd6e13219e9	3654
src	configs/relation_detr/relation_detr_resnet50_egosurgery.py	a7f3490035d108be96e4484a5011869925f4982ffef58f4db43e9c26554fee14	4067
src	configs/relation_detr/relation_detr_resnet50_egosurgery_b1_mtl.py	14bfbbd3f92504d01362148afd8c83494c8b49ecb451ef83f4e4f667ce16762e	4145
src	configs/relation_detr/relation_detr_resnet50_egosurgery_hand2det.py	19d9434d0398dddd22912bcc0e9b7ec42085c08840fe8530ef3277b46ec03acc	4331
src	configs/relation_detr/relation_detr_resnet50_egosurgery_lockeddown.py	e109dbb774c5a7fd619fd418e2540ad7640b3006692774fbc63214e431e741b4	4080
src	configs/relation_detr/relation_detr_resnet50_egosurgery_s0_frozen.py	e99cb03dce96ab5a61db5e1108e4c2e7c8314ce9c2545da2d51b99e6f557da2b	3623
src	configs/relation_detr/relation_detr_resnet50_egosurgery_s0_frozen_neck.py	50272814461b4777eb5b45fabd283bd4be9e3d93e1154f0c781113caec46a2b0	3846
src	configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py	3987e5a51be0c5986058e3e4b7432fb2895287c78fc05736276f892d154b064f	3935
src	configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_ca.py	25df3016923c8f272fd5a2e59c729f8295f3d06c7e728ab3a8096cdb03e2ee64	4140
src	configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_camt.py	87494e07c555efac8e36df223585dffe8e4938acc9f43b699d0a2be8ce070ba4	4120
src	configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_clsbias.py	044cdb02fa4d2c0fe25429e1a87f47ce1af1e7481858583e9c8cc575e2e91b40	4248
src	configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_hc.py	a3b895534e64a2fdc8acaac763df926ea7687437ecdd7e3621a1d57f67ade0d6	4834
src	configs/relation_detr/relation_detr_swin_l_800_1333.py	957954bb17e64180968f0800861427d900455c75973f8716b3b92398633d1956	3585
src	datasets/coco.py	d8daed2d35082722594c3ebf5cb0690bcdcee0eb3c5f1f03098f02f30218d826	6082
src	images/convergence_curve.png	a67e2d58768c5b848ee6677a173f2c6c80b858f1d7ab657082954f96f6219da3	110997
src	models/backbones/base_backbone.py	8893ccd55044bd4618eb3a3ff407f41ce6da36df5df8ec78bc2159ec2e7d6423	2308
src	models/backbones/convnext.py	9157a8043148bf9a1fd758f9e57134690f76aab7a69bf2f91d4d3c7de525e83a	9458
src	models/backbones/focalnet.py	3a298afdc2fb8efb0ae750a67e388d427d69dd5cd20bb3c4a24a5b4d27c6ad5a	22011
src	models/backbones/resnet.py	97519abcc5a0a4aedeb54df1f46437f4faba4381861d76c672c9578777a21def	16394
src	models/backbones/swin.py	086b49b547f838fc9dc14103d2adff02275f11b6064fbdce6413ded1a7c01518	31708
src	models/backbones/vit.py	a8ef563d55d1813415400b6b8154ea70053c76fd3a707fc263cbeda14bb33392	34067
src	models/bricks/base_transformer.py	971e1fe60947cbdc7be30e7f57ee894dae02b8158a551d9a62ec0f0a958e9f85	5780
src	models/bricks/basic.py	25bd0eb6f45c6609390dbdf5cd1edef364cda771503243fde816e11622dc5ff6	7337
src	models/bricks/dab_transformer.py	2716b13b1db04867a6d2012ff08d710c358da7200028b691b224173ade3182de	4068
src	models/bricks/deform_conv2d_pack.py	f8ea8079574bb0bd1a2ac5a11867da984e3da83fc9c5aa22db2ef14aee526e08	2473
src	models/bricks/deformable_transformer.py	c279d79250b468f0d00e46349a724aac5d0d852ac4fd6a98a31cdd2981701d34	8904
src	models/bricks/denoising.py	fe7d5fa19309fe2b1af20ab98110cd19b57436766bafaea7e33b6e55579a3c58	15723
src	models/bricks/dino_transformer.py	70870891717d2e49ee7b0ad153e286ff217dc455672e0db61d936859af989c83	10099
src	models/bricks/dn_transformer.py	f5900117e3cee77627efd4c38cd4bbc2bb29d0bf3cbd02ce8c09632143d9fb60	8082
src	models/bricks/losses.py	7af9402cc6d297a8df52f6c1d47b11087a4d61b2ff829fb09d4af83a4358851a	1852
src	models/bricks/misc.py	bd2ea0c30ea80706b42e679693ac9ba6b4460f0a54d418c21aeb29aa16782e59	12541
src	models/bricks/ms_deform_attn.py	d78fb92b3b6370124d56f1a757ffcb3b5575a1216f48e65dee10d03ff71cbc0c	14688
src	models/bricks/position_encoding.py	26b8f8ecdd92bf43efda7ea026954c1464656c115df2fe408c7dd8254381107c	5488
src	models/bricks/post_process.py	14d902d3ddfac06dcea31d5bfe6411a1ecea7e829267474d73df309059f7df16	5173
src	models/bricks/relation_decoder_phaseca.py	29461046c5a1fc6bde600bde5d15a784a6bbc3992a9b3e0923d44c40056211db	4055
src	models/bricks/relation_transformer.py	87251e0b7734c199b75197d399bd341bdd21817f0fca8cc2b19e0f94afc3be91	20011
src	models/bricks/set_criterion.py	93f1b43fe180940a40ee14e73cd9f6c4dc2c1e6a6f4fcea0eebb69e798d6cf19	9095
src	models/bricks/ops/__init__.py	e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855	0
src	models/bricks/ops/cuda/ms_deform_attn_cuda.cu	307450b39b66d140e95ca80d8ff40b2979b03d848a53ee415afbb2f0e7314dcd	7009
src	models/bricks/ops/cuda/ms_deform_im2col_cuda.cuh	4248f2b3b45619dd452065f51c60410867e3e41df9c269453accaa2ca945b511	54214
src	models/detectors/base_detector.py	a5ca9ffab4718862d191ea9501e11f1074a9c24015035fba7bf4cf00d7948519	12046
src	models/detectors/dab_deformable_detr.py	09edcbc6413b0f6537261924d12df91da3729acd8dc5d7841dcc91e66bb1c15b	2290
src	models/detectors/deformable_detr.py	0a79d529f08bf9d70830a878b14c98c6c916abf164020cc8babede45669305a6	2281
src	models/detectors/dino.py	24a27133b6e17e4d08f8832bf7283f0a0ad213d93e6e1c6f13f9ae592ccb0f91	4422
src	models/detectors/dn_deformable_detr.py	326cc05ad097fee01e6066f4dd49b38f028829f3a2e686692de2e25d781d3f29	4470
src	models/detectors/relation_detr.py	4a5548334cdd3f230fe8a07e8e7b81e00ce5b58f7aefe8b589e6dcd661cc0ecc	5534
src	models/detectors/relation_detr_b1_mtl.py	e0869a6029f419bba8627499e075aa018a477018c8dfe0ec962ca03efe2db4f3	3101
src	models/detectors/relation_detr_c5neck.py	8b0d656dd06f41ed8bb8311b47f0088e084af5520ad77b182a8a7c306949aed9	4402
src	models/detectors/relation_detr_handprior.py	d7976009465b316117985f981b2f892542595234103a00e55460f2f774eb2819	6818
src	models/detectors/relation_detr_phase_hc.py	af5104bcd0915ca7122d022df43683b21502f23dddca553928b951ba0e3bf665	3987
src	models/detectors/relation_detr_phaseclsbias.py	7dbac50b1fb702dba9a7e27931c0d3f6f69917a4affdfb84e33111d8d0386cf4	3130
src	models/detectors/relation_detr_phasecrossattn.py	f3930ff63ecc509fb825626b26f28d2ff3dd9c1253e3ad62f5f555c154b0d70f	2715
src	models/detectors/relation_detr_phasecrossattn_mt.py	3c7eb208fd36ef61f51731401d9976f7c29cf0990755d9f9567b28ede651c708	3656
src	models/detectors/relation_detr_phasefilm.py	6bd3abc5c086650861d616001c7d5097a77a62f2a1c88a16a1b4df8576e7a2c3	4142
src	models/matcher/hungarian_matcher.py	ea7383dbe47be2030343a68879b53b7d81697bbd0781d90f4e8d7d940a5b59bc	4159
src	models/necks/channel_mapper.py	c2c92bc8d793da0ea6c260a2ab0b8283757feadad80fd6d67eba4d430037f481	3035
src	models/temporal/tecno_mirror.py	f044649ce52caeba6c54daf61c4ff8f53f89fac8a886f3a8912d087c8bb2d6d1	3698
src	optimizer/param_dict.py	d32e9f6b69dabddc2026c9eb505bf1a13315288d45807f025a8193833d00c132	12839
src	tools/benchmark_model.py	d39891f2df401e165226879a1ae434425d4619abb5b00d87b45255e11bb49ba4	2183
src	tools/pytorch2onnx.py	5f1e3ad2affd2460e75343eb7c96dd0ec29ddc6b638d178a74ad9a716e3935bb	4649
src	tools/visualize_datasets.py	675fe9ed4115fac1fe957cd9b990f84074f9129fca5bc3774bbd8ab5950715d2	3242
src	transforms/__init__.py	452544a2056ba0329c554207e015b037c5e4b35fab345e95053344889d6391aa	163
src	transforms/_functional_pil.py	d8195ee48abc988d72a8d6d6ec6fc14a5dca6d7538cdda6a48a936b45308491b	12018
src	transforms/_functional_tensor.py	91db8688355499e6ddb8d9fc0fbdb98b2f1e406d3f76b164100db6efd3a9f394	33965
src	transforms/_functional_video.py	61c579e7b62095b26cabd4911891c5a116edc5ac222d2275a0ce6b57be4ecaa4	3857
src	transforms/_presets.py	81a9397b2fe1721a161e522480cbb8d8792d6af6b808fe0873b7c09fc73890e4	8519
src	transforms/_transforms_video.py	b62fe5e19e07c7387acfd1e30ffcc3f314422997e052f8c7d4009eeafaab255f	4938
src	transforms/_utils.py	85af6c9fb6ecb812e11024c91ff21f9d855880366ca1c1981813cf4e7a4aab35	3923
src	transforms/album_transform.py	73c8e15fee15d1d39e97d01b20572ceb2e145e0a65330bb87bd45b372f622dd9	10539
src	transforms/albumentations_warpper.py	01194d1dc9a3db42a5cb07beb7839e25685906d97f86dddab5a5fff0eea244da	3141
src	transforms/autoaugment.py	25c6dd1036d1d3e3aa4c4e1cc24855481e39c2815943f16ae719a316eff76e38	28243
src	transforms/convert_coco_polys_to_mask.py	25f310e3aea671996d307470881bacd77dd19214be836d23608ff3da8cd1f7ed	3639
src	transforms/crop.py	aa01794fbcf78c6d48079cf74ba2d356b26ec3043fecd7dc4eef69dd0bebf568	4136
src	transforms/functional.py	754868e8230fc714550cf7e359e7a59df2ef8aece153702607b3b590ba6629d8	65589
src	transforms/functional_pil.py	d1e959f202f39dc6c8c1b2f8e4a833134b23b3d1777f9b97e6fe281de8c1983e	363
src	transforms/functional_tensor.py	12645dbbb8f39889af6daef810559f0d31bc74a7b931a127c7a4c4c6565d6849	369
src	transforms/mix_transform.py	15198315d12dd10b5c47cd1e01b97dfc75aa631c0a797166a4413f179894acb5	12903
src	transforms/presets.py	03812cf89589e0bf6da9b27d5f05aaefa7c1bdaee47666423c1e13413fca329c	11186
src	transforms/simple_copy_paste.py	1f791cd9b1d155f87936507750ab8e8151916c3873e600ec2e6e46ec1a5bd1f6	6622
src	transforms/transforms.py	e523dea2050a22c02c4ca3e4b42073fcda08887ac889dc52ce768475cf221b1d	84911
src	transforms/utils.py	19b05e35c95261fddfb3a6a37e50c15b543fd25b1d6135b818064207fbe1c603	2990
src	transforms/v2/__init__.py	d26415a278bd84bf714847a1e0be548fe7b8df6779dc2e3a4473c6df85126b50	1270
src	transforms/v2/_augment.py	d4009b1fbc33e19d4f5799a0f5c674d7ce122f2fcc54f230f306b955278da628	5341
src	transforms/v2/_auto_augment.py	88b07d14c6c9193855d699fa427a55279a60303c89f038f4c82caf8e11eb43bb	31735
src	transforms/v2/_color.py	8b52de24fab6cf3d9253184d3f3eafab707586619782b003e40852e7e7cc53b8	17273
src	transforms/v2/_container.py	35df119ce8055e63bd16775ecd65fda8bc8f3cf0541deafaa099a10128e3e06b	5955
src	transforms/v2/_deprecated.py	a640e79731166a70993e0b5f66722b00ee51389f34566c6b8ed2deb765d32a02	1791
src	transforms/v2/_geometry.py	7606b5151605c532c18922992003e3644ee94fdc769c547bf3130cbe41a489e2	67689
src	transforms/v2/_meta.py	a72670f0ccd96646dff06246eae1d3a1531ad6cf414bcaa2b5f58221746e12a8	3297
src	transforms/v2/_misc.py	af4e1001e455386b2c11986fe720b229e589e8315b4d1cde300feae52d8c7b27	17354
src	transforms/v2/_temporal.py	ee7340ad07618c344bd72044118f678f78e3c586018e3a12b2c40389b7a4166f	1062
src	transforms/v2/_transform.py	b14864ea621fabf465dd929878bef40e7ce0acd42f966b3cf6c618194570558f	8132
src	transforms/v2/_type_conversion.py	77c7d9e2d13e26eea99b3f2a98e7af4292f2ebd76bd6736202733cb3e70f6c4e	2849
src	transforms/v2/_utils.py	85af6c9fb6ecb812e11024c91ff21f9d855880366ca1c1981813cf4e7a4aab35	3923
src	transforms/v2/utils.py	205f89810ba4faac86b093ed43b4cef2b66dd1a0004c4069a5f23748cb6a22df	2987
src	transforms/v2/functional/__init__.py	440ef81e7d649618634ffcbc7b7ea4e237fa1e71e108729c140dd800229bb14a	4301
src	transforms/v2/functional/_augment.py	4dc905fa93d612a48d6e03e85b9f520170b57ec0bc98e4e602241f218d80b4c2	2085
src	transforms/v2/functional/_color.py	fa4a78fddb858651d5c2b1801af6799ee0d3836520d24cb000da8fafb4405856	26294
src	transforms/v2/functional/_deprecated.py	a393d062db67172c732c5f58354bcdc99b09916cc9749de430d7ffc6cab2cd51	1471
src	transforms/v2/functional/_geometry.py	b6fc1261f89da44610eff9a8931a3601c8d8d0c3b5e55ad5401e196d7043671e	75980
src	transforms/v2/functional/_meta.py	ab33cc2e1335289988db8ea8cdcde4a1cee1a2df261aa901f1cf6966c1d209c8	14043
src	transforms/v2/functional/_misc.py	75f3a6fb1852602d6737e687e6855cd4fea54522e800069bdf5130f6bfca9f2a	6430
src	transforms/v2/functional/_temporal.py	ea6869d1d4dd9780dde259f40a4610c9c3b66c83b230f1f415310143ca346874	1019
src	transforms/v2/functional/_type_conversion.py	732fff2fdb08b5b0efcb51bd89c3953bd70a5f97246e642b2fd5b0069debd4f2	942
src	transforms/v2/functional/_utils.py	82b27aca582d239bdb3efddeaa4b2ab99deaed913e6a67066cf7b7efa5e48ca6	196
src	util/coco_eval.py	4ab59e6d8793d8f9e0b4ab258e621e4701190dcb8e67b1c158eecc614509bee8	12280
src	util/coco_utils.py	6fb8449c15507d292933e4b4f27f8ecf0f8fb0f857f51e8a0abadf7f114c18f5	3138
src	util/collate_fn.py	733d32547907fb0fb6303270c99aa9235eb4ba57bb7b5e67d995339a878021ce	1466
src	util/collect_env.py	d2c88290013d28bd929a3d1098585d23d97a7d21bb9546ac197be5d8d2275266	4723
src	util/datapoints.py	41bf1429467bd7d7b86c823e00fdc514fec2ba9f7854d5ef3e543c1f69c55b7b	34121
src	util/engine.py	60c61c7b888ea3166d6687f6afa3ab160a431fce1ae80f5fb60e07f0dc7a8c3b	10216
src	util/group_by_aspect_ratio.py	629aee554a00346aba73864c03efc855180c96372da6b703e3171a90e253e301	6928
src	util/lazy_load.py	875d0e0f6ede548d939ed7975fea904408897cb34d73a7f62acefc1f84c292db	11340
src	util/logger.py	f397ec5febca9bf933287d68dd0e98450982a1bc085842d9a9cda9418f563549	6078
src	util/misc.py	2ff6d538e8ceb41896fa36f3ec2bc63d232283069a49cc65fe7480cb85ac2194	8184
src	util/tune_mode_convbn.py	c749a91a668aaf282b7947b53d91ee169e71bd7f48c6e16f52c8b6ecf11e1ca9	5771
src	util/utils.py	898d69977e91c1e1f0d808bd1088eeae6abcc6985bf56ad23a6dbbe7e0339b1c	14539
src	util/visualize.py	1384cb94ae5b28b57fd83455127f82b6fa5d1051f83badfba13eda69eb02b4df	19380
src	visualization/mc_distribution.ipynb	9feee0fadab1af083d7acf42cc548710058c016dce0403910eef639b528197b7	37133
ext	/home/ubuntu/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/.ninja_deps	90399d91afa28a8c374fd30c71a380be37a5fd4601d9095b4fd6a0dc0e2b73f7	100
ext	/home/ubuntu/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/.ninja_log	a47f5cddbcfef78b82244206364cc2bd0c890fcc29f29b477d0509318c193341	476
ext	/home/ubuntu/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/MultiScaleDeformableAttention.so	79b55a8ab270ed6d8d994352f31df08a52f2d93b147cb086d841374d9aad976f	1655680
ext	/home/ubuntu/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/build.ninja	f72b62a067a6540a5e4ce31470867a0adf4332b97ffb34985e2fb231bd7df00b	2706
ext	/home/ubuntu/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/ms_deform_attn_cuda.cuda.o	966a3806518a4a806f743431714f9b14042c278e7263328f677542b693fc848e	2423632
ckpt	checkpoints/incoming/seed123/best_ap.pth	bb01eb27385d4fd967abe06742e9a590066c0ca83c3c25c4da73a376e87cb332	195421066
ckpt	checkpoints/incoming/seed42/best_ap.pth	03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824	195421066
ckpt	checkpoints/incoming/seed456/best_ap.pth	f0204ae9843e052949209259c73fd6ce7e327e709c59fbde2e08aa26ec2f1ef8	195421066
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap.pth	5992c5ee518de62b050256b553a3d0ce7dbff8072b039b963bf7d89a809e5cfe	195421066
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap50.pth	f9dabee44638b262c00f8f6e0ba0436f7650761da28ed048e007887885b68c94	195422778
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/checkpoints/checkpoint_0/scaler.pt	b8e23a14af81a4a44c0c2328d05f6dd29912230bbbfd2acff2cf9251005a8d7c	988
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/seed123/best_ap.pth	bb01eb27385d4fd967abe06742e9a590066c0ca83c3c25c4da73a376e87cb332	195421066
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/seed123/best_ap50.pth	d5d2dee55d7a9879252f29c291671142ecbbb9cc1fb70617e7c2ec91bac19a45	195422778
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/seed42/best_ap.pth	03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824	195421066
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/seed42/best_ap50.pth	430e6d247822437a2ca959cf99210006e223eea871fcb7e340045b1a6c0aa3a0	195422778
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/seed456/best_ap.pth	f0204ae9843e052949209259c73fd6ce7e327e709c59fbde2e08aa26ec2f1ef8	195421066
ckpt	checkpoints/relation_detr_resnet50_egosurgery/train/seed456/best_ap50.pth	fd4cf4fbc01f2bcd6101175a24397d845c0611eec2caf9a38362d681aef066a5	195422778
weights	data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth	2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff	196140106
weights	data/external/weights/relation_detr_s0frozen_init_seed42.pth	8ab3d011f5c0069ce10c4fbe232c54e9af00a88e2a9800e4aab04f1c72441637	196112466
```

## 付録 2. 後の値と前の値の差（diff 前 後）

```
6c6
< src	main.py	6c14063af155bea99fc43e3c14d1c28dcb2b9d8c07f98b96a45eb4ca9b57e641	9337
---
> src	main.py	ffbd6deb9ad48ec348f05f4eff8f949e97647dd74b996689af5477db8d281415	12809
25a26,28
> src	configs/train_config_egosurgery_stage1_imagenet_seed123.py	92275cc9548d1f9bfe4849e51365a35034e959a808d6aebb97297552051534d0	3390
> src	configs/train_config_egosurgery_stage1_imagenet_seed42.py	c252e9c90329fe885cb8befc9893b845e566300c4be249a3ccf5c0625bf58afe	3389
> src	configs/train_config_egosurgery_stage1_imagenet_seed456.py	8a72d01fce0fe820199bdb706563006ba996754f2ec8acddc68a4d9872ae5929	3390
141a145
> src	util/convergence.py	299597a252674450babf7b31f889fd752848ec2dac070215223706ee6456514d	4054
```

後の値は前の値に上の差を当てたもの（170 行 → 174 行）。ext 5・ckpt 12・weights 2 の 19 行に差は無い。

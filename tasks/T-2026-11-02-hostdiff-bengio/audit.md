# audit — T-2026-11-02-hostdiff-bengio

時刻は UTC（JST = UTC+9）。出力の置き場 `$D = experiments/analysis/hostdiff_andrew_bengio/bengio`。repo の外の置き場 `$S = ~/m2-scratch/T-2026-11-02-hostdiff-bengio`。
相手のホスト（andrew）には何も送っていない（ssh を使っていない）。

## 0. 始める

- 13:2x UTC。開始時の分岐 `feat/bengio-align-andrew`、清浄。分類（比較先 origin/phase0 d145854e）→ 通す。
- `make task-start`: 分岐 `feat/hostdiff-bengio`（起点 d145854e）、**`[task-start] .sync-pause を作成`**、`[task-start] 完了。`。
- SPEC §1 の前提「#284 が phase0 に統合済み」が満たされていなかった（#284 OPEN）。利用者に諮り、利用者が統合した（mergeCommit 8aefdce3、13:27:38）。
  分岐はまだ commit を持たなかったので `git merge --ff-only origin/phase0` で起点を 8aefdce3 へ早送りした（新しい merge commit は無い）。
- `make task-validate` → OK。`make task-preflight` → 7 PASS / 0 WARN / 6 SKIP / **1 FAIL**:

      P2 cuda_ext_loaded        FAIL models.bricks.relation_transformer を import できない: ModuleNotFoundError: No module named 'fvcore'

  SKIP: P3（判定基準が未確定、B-20）、P4、P5、P12、P13、P14。P9 spec_lint 該当なし。P11 gpu_free PASS。
  原因: P2 は `sys.executable`（契約の `env.venv: .venv`）で検出器を import する（`tools/preflight_task.py` 218〜236 行）。`.venv` に `fvcore` は無く、
  `.venv-relation-detr` にだけある（0.1.5.post20221221）。同じ import を `.venv-relation-detr` で回すと `ok True`（拡張も読み込めた）。
  利用者に諮り「記録して続ける」の回答を得た。代わりの確かめは、各 run の学習の記録の拡張と COCO の重みの読み込み（Task C・D）。

## Task A — 開始状態と照合（G1）

- A-1・A-2（`$D/a_state.txt`、13:33:57）: 分岐 `feat/hostdiff-bengio`、HEAD = origin/phase0 = 8aefdce3。GPU 0・1 は 39・20 MiB、使用率 0%、compute 0、電力の上限 220 W。
  空き `/dev/sdb1` 1,401,511,628,800 B、overlay 1,400,372,150,272 B。`proc_enum.py`: n_compute 0。陽性 zsh 8、陰性 0。
- A-3（`$D/a_reldetr.json`）: source 142 / 2f08e5213cb5c377…、all 155 / 20f15c061b435ce4…、`.venv-relation-detr` 72 / 8f08a2457e681d6d…。§3 の andrew main と同じ。
- A-4（`$D/a_inputs.json`。前の調査と同じ道具 `tasks/T-2026-11-02-bengio-andrew-env-survey/tools/data_inventory.py`）:
  `image_input_lock.json` 17,233 行（32,670 経路）の不一致・欠け 0。対照: 記録の一画像の要約値を一文字変えると不一致。B1 45ee4cc2… は記録と同じ。
  `phase_manifest_all_phase` の 4 件は dlsta の `manifest_summary.json` の `manifest_sha256` と同じ（train 10,580・val 1,904・test 4,749 フレーム）。
  折り A の `instances_{train,val}.json` は記録（fc63621e…・db605c06…）と同じ。COCO の重み 2d2c19a7… は記録と同じ。
- A-5（`$D/a_env_static.json`）: driver 595.84、二つの仮想環境とも torch 2.1.2+cu118・CUDA 11.8・cuDNN 8700・NCCL 2.18.6・torchvision 0.16.2+cu118、
  accelerate 1.13.0（本体）・1.14.0（検出）、Pillow 12.2.0（libjpeg-turbo、jpg 6.2）、画像の読み込みは PIL。TF32 の既定は matmul false・cudnn true。
  学習のプロセスが読んだ値（決定性・TF32・autocast）は各 run の `*_optimizer_rank0.json` の `runtime`（`tower_search_common.runtime_state`）から取る。
- A-6（`$D/a_launch_compare.json`、道具 `tools/compare_launch.py`）: 手本の `command.sh`（工程塔 001・002・003〜012、検出塔 point00）と本契約の再現台本（dry-run で書き出し）を、
  seed 42・123 の工程塔 24 本と検出塔 3 本の計 27 組で比べた。差の全行は JSON の `raw_diff`。許した違い（経路・GPU の番号・ポート・seed・置き場・
  `NCCL_P2P_DISABLE=1`・`TOWER_SEARCH_TASK/SCRATCH/PHASE_PUBLISH/STEP_LOG`）を正規化した後、**27/27 が同じ**。
  対照: 手本の 1 行（`workers=4` → `workers=2`）を変えた写しでは不一致。
  `TOWER_SEARCH_STEP_LOG` は記録の置き場（一歩ごとの時刻の記録先）として許した違いに数えた。
- 手本の run の commit（工程塔 11ab3747、検出塔 bce323bc）から HEAD までに、学習に関わるファイルで変わったのは `scripts/stage1_ptower.py`（候補 5 の時間ヘッドの追加。
  キーが無いときは従来どおりと注記）、`configs/stage1_ptower.yaml`（注記だけ）、`scripts/run_ptower_search.py`（`control_only` の 1 行）。
  コードは両ホストで同じ commit を使う（§3）。dlsta の値とは比べない（§2）ので、この差は記録だけにした。
- A-7 道具の合わせ方（既定の挙動は変えない）:
  - `scripts/tower_search_common.py`: `TASK`・`SCRATCH` を `TOWER_SEARCH_TASK`・`TOWER_SEARCH_SCRATCH` で上書きできる形に
  - `scripts/run_ptower_search.py`: 公開先を `TOWER_SEARCH_PHASE_PUBLISH` で上書きできる形に（既定 `experiments/phase1/stage1_ptower_search`）。
    `TOWER_SEARCH_STEP_LOG` があるときだけ backbone の学習の micro-step の入口・optimizer step の後・val の始めと終わりの時刻を書く。
    `TOWER_SEARCH_LOSS_LOG=1` のときだけ micro-step の損失を 16 進で書く（Task B だけ）
  - `scripts/train_relation_detr_search.py`: `TOWER_SEARCH_STEP_LOG` があるときだけ optimizer step の後の時刻を書く
  - 新しい台本は `tasks/T-2026-11-02-hostdiff-bengio/tools/`（`run_hostdiff.py` 起動、`launch.sh` 順に起こす、`compare_launch.py`、`test_defaults.py`）
  - 試験 `tools/test_defaults.py`: **4 passed**（`$D/a_test_defaults.txt`）。対照: 既定の契約名を一つ変えた写しの置き場に向けると 2 failed（`$D/a_test_defaults_mutant.txt`。
    もう一つの失敗は写しの置き場では `ROOT` が変わるため）
  - ruff は 3 ファイルとも通過
- 段取り: 手本は backbone の後の「記録の評価」と「取り出し」を GPU 2 枚で並行、ヘッド 10 本を 2 枚で 2 本ずつ回した。契約の「一度に走らせる学習は一本」との関係を
  利用者に諮り、「手本どおり並行」の回答を得た（塔の run を同時に 2 本走らせない意味と読む）。

### G1 の判定

分岐 feat/、起点 origin/phase0（8aefdce3）。Relation-DETR・入力・起動の設定（27/27）が一致、`env` を記録、GPU 2 枚が空き。**通過。**

## Task B — 工程塔の決定性（G2）

- `launch.sh control1 control2`（13:53:19〜13:58:17）: 0 番の設定で backbone を `+control_frames=3200 ft_epochs=1`（global batch 16 × 累積 4 × 50 = optimizer step 50）、
  `TOWER_SEARCH_LOSS_LOG=1` で二度。出力は `$S/controls/control{1,2}/`（公開しない。本測定に数えない）。両方とも `load pretrained COCO backbone ... sha256=a755b3eb…`。
- 比べ（`tools/compare_determinism.py` → `$D/b_determinism.json`）: rank0・rank1 とも micro-step 200・optimizer step 50、損失の列は **bit 単位で一致**
  （rank0 3cd3c19c313a27b3…、rank1 4a89babb4fda3f8a…）。対照: 二回目の列の一つの値の最下位の bit を変えると不一致。

### G2 の判定

二回の損失の列が bit 単位で一致。**通過。** §6.2 の工程塔の d_rerun は 0 とする前提が bengio 側で成り立つ。

## 本測定の前の検出塔の確かめ（本測定に数えない）

- 12 歩の制御（`TOWER_SEARCH_CONTROL_STEPS=12`、`$S/controls/detector12/`）が `AttributeError: 'function' object has no attribute '__self__'` で落ちた。
  原因: 一歩ごとの時刻を取るため `optimizer.step` を素の関数に差し替えたが、`util/engine.py:33` が epoch ごとに作る `LinearLR` が束縛メソッドを要求する。
- 直し: `optimizer.step` を差し替えず、毎歩一度呼ばれる勾配のクリップの観察点（`clipped`）で時刻を書く形にした。試験 `test_defaults.py` に「`optimizer.step =` を含まない」を足し、4 passed。
- やり直し（`$S/controls/detector12b/`）: 終了コード 0、`CONTROL_COMPLETE`、クリップの記録 12 件、`initialization_rank0.json` の `matched true`・COCO 2d2c19a7…、
  `runtime`（tf32 matmul false・cudnn true、決定性 false、benchmark false）。
- 本測定（`launch.sh phase42 phase123 det42a det42b det123`）は 14:00:17 UTC に起こした。
- 道具は repo 直下に Hydra の記録 `run_ptower_search.log` を書く（手本の道具と同じ挙動。`.stignore` の同期の対象には当たらない）。学習の後に repo の外へ移す。

## Task C — 工程塔（本測定）

- phase42（14:00:17〜16:47:10、終了コード 0、wall 10,013 s）: backbone の学習 9,642 s、両 rank とも `load pretrained COCO backbone ... sha256=a755b3eb…`、
  `early stop at epoch=19`、`FINETUNE_COMPLETE ... acc=0.8125`。取り出し 265 s、記録の評価 298 s、ヘッド 10 本（各 10〜14 s、2 本ずつ）は全部 `RUN_COMPLETE`、指標は有限。
  GPU の見本 993 件のうち本契約以外の使用 0。公開先に同期の対象の種類（.py/.npy/.pt/.pth、logs・checkpoints・predictions）は無い（676 KB）。
- 公開名の番号: ヘッドは 1 本ずつ別の作業場で回すため `ExperimentManager` の連番が振り直され、10 本とも `001_P15_…` になった（手本は `003`〜`012`）。
  名前の後半（`P15_A_L6_w0.0_h30` 等）で手本の順へ対応づける。起動の引数は A-6 で照合済みで、この差は公開名だけ。
- phase123（16:47:10〜20:08:45、終了コード 0）: backbone の学習 11,722 s、両 rank とも COCO の重み a755b3eb… を読み込み、lr を epoch 12 で下げ、epoch 23 で早期停止、
  `acc=0.7957`。設定に `seed: 123`。ヘッド 10 本とも `RUN_COMPLETE`、記録に非数なし。GPU の見本 1,199 件のうち本契約以外の使用 0。公開先に同期の対象の種類は無い。

## Task D — 検出塔（本測定）

- det42a（2026-11-02 20:08:45〜11-03 04:25:24、終了コード 0）: 学習 29,164 s、評価 val 89 s・train 543 s（どちらも "skip loading" なし）。`initialization_rank0.json` は `matched true`。
  `convergence.json`: lr を下げた epoch 15、最良 17、停止 21、観測 22 epoch（番号は 0 起点）、上限に届かず。val mAP 0.7264（標的群 0.8133、陰性対照群 0.6616）、train mAP 0.8644。
  学習の記録に非数なし。GPU の見本 2,955 件のうち本契約以外の使用 0。公開先に同期の対象の種類は無い（128 KB）。

## Task E — 値の表（下書き）

- 道具 `tools/build_values.py`: 記録のファイルだけから `values.json` を書き、§6.1 のキーの欠けを検査する。未完了の run の欄は理由つきの UNKNOWN。
  対照（`--selftest`）: 写しから `detector.seed42b.AP50` を消すと `broken_missing: ["/detector/seed42b/AP50"]`、元は `[]`。ruff 通過。
- commit の記録: phase42 の backbone だけ `git_commit.txt` が 8aefdce3（14:00:17 起動、22ce24b2 の commit は 14:01:26）。
  道具 3 本と起動の台本の最後の変更は 13:48〜13:59 で起動より前のため、5 本とも 22ce24b2 の内容で動いた。`values.json` の `code_commit.note` に書いた。

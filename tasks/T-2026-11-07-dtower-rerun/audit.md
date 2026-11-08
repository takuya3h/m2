# audit — T-2026-11-07-dtower-rerun

時刻は UTC で記録し、括弧内に JST を添える。版管理の外の置き場は
`/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-07-dtower-rerun/`（以下 `$STORE`）。
道具は `experiments/analysis/dtower_rerun/tools/`。前例の置き場（PR 299）は `$PREV` =
`/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-batch-search/`。

## 0. 開始（手順書 0〜2、2026-11-07 09:1x〜10:13Z = 18:1x〜19:13 JST）

- ホスト名 `Andrew`。開始時の分岐 `feat/dtower-batch-search`。`feat/dtower-rerun` は手元にも遠隔にも無く、`tasks/T-2026-11-07-dtower-rerun` の履歴も無い。`.sync-pause` は無い
- `git fetch origin` の後の `python3 scripts/task_start_classify.py`（比較先 origin/phase0 a68672f1）
  - 追跡下の変更 0、未追跡・起点に在り中身が同じ 13（通す）、**未追跡・起点に無い 2**、`分類: 止める`
  - 止めた理由の 2 件: `experiments/phase1/grasparms_B_empty_ep4_seed42/logs/eval_meta_val.json`、`experiments/phase1/grasparms_B_gt_ep4_seed42/logs/eval_meta_val.json`（各 16K、禁止領域）
- 利用者の選択 1（禁止領域外の未追跡を退避してやり直す）: 禁止領域外の未追跡は 0 件で、**退避したものは無い**（`~/m2-evacuated/` は作っていない）。やり直しの `make task-start` は同じ 2 件で止まった
- 利用者の選択 1（無視の一覧へ足す）: 2 ファイルを `.git/info/exclude` に足したが効かなかった
  - `git check-ignore -v` の結果: `.gitignore:116:!experiments/**/logs/eval_meta_*.json` が効いている。`.gitignore` の再包含は `.git/info/exclude` より優先される
  - 足した 2 行は戻した（`.git/info/exclude` は元の内容）
- 読み取りの調べ（作り手は調べなかった。利用者の指示）: 2 フォルダは 2026-11-07 08:06〜08:10Z に作られ、中身は `logs/eval_meta_val.json` と `predictions/val_inj_ep-1.json.gz`（各 13,032,761 bytes、無視の対象）だけ。phase0 とどの遠隔分岐にも記録が無い。GPU・Python の処理は無かった
- 利用者の説明と指示: 2 件は bengio で実行中の契約 `T-2026-11-06-grasp-pilot-d-rerun` の Task C の生成物が同期で届いたもの。触らない・移さない・消さない・commit しない
  - 一度目: task-start に受け入れの口は無いことを確かめた（`scripts/task_start.sh` は識別子だけを受け、起点は `BASE_REF="origin/phase0"` に固定。分類器の引数は `--base` と `--adopt-list` だけ）。指示に従い中止とし、`make task-release END=abort` は `task-release: ABSENT … 元から無い。何もしていない`
  - 二度目の指示: `.git/info/exclude` に **2 つのフォルダ** `experiments/phase1/grasparms_B_empty_ep4_seed42/`・`experiments/phase1/grasparms_B_gt_ep4_seed42/` を書いて task-start をやり直す（親フォルダを無視すると再包含は効かない）
- `.git/info/exclude` の 20・21 行に 2 フォルダを追記した。`git check-ignore -v` は両ファイルとも `.git/info/exclude:20` と `:21` で無視と判定。`git ls-tree -r origin/phase0` に 2 フォルダの経路は 0 件（切り替えで上書きされない）
- 分類: 7 区分のうち未追跡・起点に無い 0、`分類: 通す`
- `make task-start`: `分岐を作成: feat/dtower-rerun（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、取り込み OK、`[task-start] 完了。`
  - 取り込みの L2-8 の WARN 3 件: index.csv 2363 → 2623、experiments.csv 1130 → 1305、verdicts.csv 1736 → 1947
- `make task-validate`（取り込み直後）: `OK`、rc 0、同じ WARN 3 件
  - 分母 `baselines/dcoco_foldA/dcoco_foldA@val` の行を、起票時の `runindex_commit` 68befc3b と現在で比べた。値は同じ（mAP_mean 0.7242876868136648、**mAP_sstd 0.0037964726778790692**、n_runs 6、n_seeds 3「42,123,456」、split val）。行数の増加は他の契約の run の収穫による
  - 利用者の判断: 続ける
- 抑止の稼働: `grep -c sync-pause ~/bin/m2-sync.sh` = 2（稼働中の版が対応済み）

## 1. 参照の解決と改訂（手順書 3、10:0x〜10:13Z）

- `inputs.denominator.ref` = `exp:baselines/dcoco_foldA/dcoco_foldA@val`（上の値。require の n_seeds ≥ 3、sigma あり、split val を満たす）
- `inputs.sigma_policy` は省略 → `context/conventions.md#sigma` の既定値を継承
- `contract.conventions_rev` 2d946b07: `git log -1 -- context/conventions.md` の実測と一致
- 改訂 1（利用者の決定 1、2026-11-07）: 0 番の折り A の weight decay を 3.0e-4 → **2.998753e-4**（S 4.81e-4 ÷ (1e-4 × 20 × 802) = 2.9987531172069825e-4）。全折りで S を 0 番 4.81e-4・12 番 4.976e-3 にちょうど揃える。学習は weight decay = S ÷ (学習率 × 20 × 実測の 1 epoch の歩数) を丸めずに使う
  - 書き換えた箇所: prereg §2.1 の表、prereg §4 の weight decay の行、SPEC §2 の batch 6 の weight decay の行、SPEC §4 Task B-5、spec の acceptance d
- 改訂 2（Task A-8 の実測）: `meta.created_from` を 68befc3b（2026-10-29）→ **d3e319ac**（origin/phase0 で runindex を最後に変えた commit、PR 299 の収穫、2026-11-07T08:05Z）、counts を {2363, 1130, 1736} → {2623, 1305, 1947}（`git show origin/phase0:runindex/*.csv` の行数）。L2-8 の WARN の原因はこの食い違い
- 改訂の後の `make task-validate`: `OK`、rc 0、**WARN 0 件**

## 2. prereg の commit と L3 プリフライト（Task A-1、手順書 4）

- 一度目の `make task-preflight`（commit の前）: 10 PASS / 0 WARN / 3 SKIP / **1 FAIL**（P4 `prereg.commit が未記入`）、rc 2。手順に従い停止して報告し、上の改訂 1 の決定を受けた
- **`df18070d5e5840483ef61d17fdb15d0fd49b9940`（2026-11-07T10:13:18+00:00 = 19:13:18 JST）** `docs(dtowerrerun): 事前登録（学習の前、0 番の weight decay と created_from の改訂つき）`。SPEC.md・prereg.md・spec.yaml
- `e2fd7502`: spec の `prereg.commit` と `committed_at` を記入。push `origin/feat/dtower-rerun`
- 二度目の `make task-preflight`: **11 PASS / 0 WARN / 3 SKIP / 0 FAIL**、rc 0
  - P4 `df18070d… committed_at=2026-11-07T10:13:18+00:00`、P5 `best_ap.pth sha256=03936318…75e824`、P11 compute 0 件、P13 `対称性の表 1 個 / 26 行に UNKNOWN と理由欠落は無い`、P14 `検出 0 件（カード 16 件 / 禁止語 15 語）`
  - SKIP: P2 `cuda_ext_loaded`・P3 `deterministic_flags`（契約に記載なし）、P12（解決前提の参照なし）
  - P9 spec_lint: 規則 9 件で該当なし

## 3. Phase A — 開始状態（10:15Z〜）

### A-2 分岐と起点

- `feat/dtower-rerun`、`HEAD~2` = `origin/phase0` = merge-base = `a68672f1f44a94a6b8fdc41c4d6a0a918dbebf9e`
- PR 299 の内容（`c2207ab9 Merge pull request #299`）: `git ls-tree -r origin/phase0` に `tasks/T-2026-11-06-dtower-batch-search/` 6 件、`experiments/analysis/dtower_batch_search/` 13 件、`experiments/baselines/stage1_dtower_batch/` 90 件
- PR 294 の内容（`9d45351b Merge pull request #294`）: カード `docs/proposals/2026-10-21-tower-reselect-search.md` が在り、最後の変更は `e0d2d2e8 docs(proposals): tower-reselect-search カードを五版に`

### A-3 カードの版

- 道具 `tools/check_card.py`（前例の写し）: 本物で `version=五版`、rc 0
- 陽性対照: 最初の「版: 五版」を「版: 四版」にした写し（`$STORE/A/card_v4_copy.md`）で `version=四版`、rc 1

### A-4 開始前から在る未追跡

- task-start の分類（§0）: 未追跡・起点に在り中身が同じ 13 件（`experiments/analysis/grasp_pilot_arms/taskC/compare_default.py` と `experiments/phase1/grasparms_B_*_ep4_seed42/logs/` の 12 件）。切り替えで追跡下の同じ中身になった
- `.git/info/exclude` で無視した 2 フォルダ（§0。SPEC §4 Task A-4 の「四本目（PR 297）の前例」に当たる扱い）。中身は `logs/eval_meta_val.json` と `predictions/val_inj_ep-1.json.gz` の各 2 件。消さない・動かさない
- 切り替えの後の `git status --porcelain --untracked-files=all`: 本契約の 3 ファイル以外は空

### A-5 入力・道具（G1）

- 注釈の要約値の記録: `data/annotations/egosurgery_tool_folds/fold_report.json` の `folds.<折り>.splits.<区分>.sha256`（15 件）。折り A の 3 件は前例の固定値（`$PREV/A/pins.json`）と同じ
- 固定値 `$STORE/A/pins.json` = 注釈 15 件 ＋ 前例の道具・設定・探索の表 9 件（前例と同じ値）。`tools/check_inputs.py --pin $STORE/A/pins.json`: **25 件（COCO の重み 1 件を含む）、不一致 0、rc 0**（`$STORE/A/check_inputs.json`）
  - COCO の重み `relation_detr_resnet50_800_1333_coco_1x.pth` の sha256 `2d2c19a7a49e…` は前例の `initialization_rank*.json` の `source_sha256` と同じ値
- 陽性対照: 折り C の `instances_val.json` の末尾に 1 バイト足した写し（`$STORE/A/val_C_1byte.json`。`rm` が確認を求める別名で止まったため残してある）を `--override` で読ませると不一致 1、rc 1
- 動画の集合（`tools/check_folds.py`、`$STORE/A/check_folds.json`）: 学習が使う設定の写しを `main.py` と同じ `Config` で折りごとに読み、train と val のデータセット、評価の道具の `--split test` と同じ test のデータセットが出す画像の動画を規約の表と比べた。**5 折りとも 3 区分が一致し、互いに素。不一致 0、rc 0**
  - 出す枚数（train は注釈の無い画像を除いた後）: A 9,618 / 1,515 / 4,265、B 9,659 / 1,861 / 3,812、C 10,728 / 1,988 / 2,615、D 10,215 / 2,554 / 2,621、E 11,090 / 2,131 / 2,124
  - 2 プロセス・batch 6 の rank ごとの DataLoader の長さの見込み（実測は Task B）: A 802、B 805、C 894、D 852、E 925
  - 陽性対照 `--inject-test C`（折り C の val に test の 02 を足す）: 不一致 1（`$STORE/A/check_folds_inject_C.json`）
- 設定の写し: 前例の道具 `make_det_config.py` の写しで `$STORE/config/train_search_batch.py` を作った。sha256 `295d2446…1a189f` は前例の写し `$PREV/config/train_search_batch.py` と同じ。原本との差は `batch_size` と `num_workers` の 2 行（`$STORE/config/diff.txt`）

### A-6 環境（prereg §7、`tools/env_capture.py`、`$STORE/A/env_relation_detr.json`・`env_body.json`）

| 項目 | `.venv-relation-detr`（学習・評価） | `.venv`（記録） |
|---|---|---|
| Python | 3.11.16 | 3.11.16 |
| torch / CUDA の実行時の版 | 2.1.2+cu118 / 11.8 | 同じ |
| cuDNN / NCCL | 8700 / 2.18.6 | 同じ |
| torchvision | 0.16.2+cu118 | 同じ |
| accelerate | 1.14.0 | 1.13.0 |
| 画像の復号 | Pillow 12.2.0（libjpeg-turbo） | 同じ |
| TF32 の既定（新しいプロセス） | matmul False、cudnn True | 同じ |
| 装置 | RTX A6000 × 2、driver 595.84、power.limit 300.00 W（既定 300.00 W）、SM 2100 MHz、PCIe gen 4 × 16 | 同じ |

- 論理 CPU 32。PR 299（前例 audit 87〜103 行）の値とすべて同じ
- 両仮想環境の Python は同じ実体（`~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11`）を指す。このため実行器の run の合間の検査は、GPU の compute のアプリと記憶量、および実引数に `launch` を持つ起動に限った（`run_rerun.py` の `gpu_idle`）。開始時の列挙（A-3 の compute プロセス）は前例どおり実行ファイルと引数の完全一致で行う

### A-7 禁止の場所の開始時の要約値（`tools/digests.py`、`$STORE/A/digests_before.json`、10:23:07〜10:26:48Z）

- 前例の道具の写し。根を SPEC §6 の 2・3・4 に合わせて広げた（`data/external` 全体、`data/splits`、`scripts`・`configs` 全体、前回までの契約の run の置き場・解析・`tasks/` のフォルダ 4 件、前例の版管理の外の置き場 `$PREV`）
- 前例の事後の要約値（`$PREV/D/digests_after.json`）と重なる 12 項目はすべて一致: third_party `2e4de92b…`、data/raw/ego `a19c4a81…`、初期の動画 `aa4c1c6e…`、注釈 `5c46a6de…`、工程の manifest `52dd1858…`、探索の解析 `191608de…`、tower_batch_probe `76819b80…`、dtower_step_profile `6251fab8…`、stage1_dtower_search `98dcd518…`
- 凍結源 `03936318…`（同じ）。仮想環境 `.venv` freeze `f6c43729…`・site-packages `cfb4f4f7…`、`.venv-relation-detr` `d0724876…`・`f79c8309…`（同じ）
- 本契約で足した根の開始時の値: data/external `37acfc82…`（38 件）、data/splits `a757e013…`、scripts `c7377340…`（423 件）、configs `9f912b5f…`（105 件）、dtower_batch_search `7eb7e23c…`、stage1_dtower_batch `bc610236…`、stage1_dtower_r2 `86e561e9…`、tasks の 4 件 `1396cdb7…`・`a66bc74a…`・`b08eaf80…`・`38f76a5b…`、`$PREV` `37fda8f7…`（1,162 件）

### A-5（続き）記憶領域

- `/home/ubuntu/slocal2` の空き 1,623,953,760,256 bytes（`df -B1`、10:2xZ）
- 見込み: 前例の 6 本の置き場 `$PREV/runs` の実測 19,940,058,795 bytes（1 本 3.32 GB）× 20 本 ≈ 66.5 GB。その 2 倍 ≈ 133 GB。空きはその 2 倍以上
- 同期の経路: `$STORE` は前例と同じ親（`/home/ubuntu/slocal2/stage2pilot_store/`）の下で、Syncthing の同期フォルダ（前例 audit 83〜85 行の 5 つ）の外

### A-6（続き）試験の前の値

- 開始前の試験（10:15:06Z〜10:45:48Z、30 分 35 秒）
  - 命令: `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider --junitxml=$STORE/A/pytest_before.xml`
  - 結果: **7 failed, 989 passed**、rc 1
  - 失敗の名前（`$STORE/A/pytest_before_failed.json`）は前例の事後（`$PREV/D/pytest_after_failed.json`）と同じ 7 件: `tests.test_engines::test_mmdet_trainer_eval_recipe_in_metrics`、`tests.test_fetch_task::test_rejects_unknown_file_name`、`tests.test_research_logger` の 4 件、`tests.test_stage1_ptower_r3_dist::test_two_gpus_give_the_one_gpu_gradient_over_an_uneven_tail`
  - 試験の最中、GPU の使用は試験自身（pytest と、その 2 GPU の分散試験の子 2 つ）だけだった（10:24Z の nvidia-smi）

### A-3 compute プロセス（10:46:02Z、試験の後）

| 呼び方 | 件数 | 出力 |
|---|---|---|
| 既定（`.venv/bin/python`・`.venv-relation-detr/bin/python`・`/usr/bin/python3` の realpath と完全一致） | **0**、nvidia-smi の compute 0 | `$STORE/A/procs_default.json` |
| 陽性対照 `--exe /usr/bin/bash --arg probe_self_marker_7741`（自分のシェルから起こした `bash -c 'sleep 25; true' probe_self_marker_7741`） | **1** | `$STORE/A/procs_ctrl_pos.json` |
| 部分一致 `--arg probe_self_marker_774` | 0 | `$STORE/A/procs_ctrl_substr.json` |
| 陰性対照 `--exe /nonexistent/zzz_no_such_exe` | 0 | `$STORE/A/procs_ctrl_neg.json` |

- GPU は両方 16 MiB、使用率 0 %

### G1

- **G1: pass**
  - 分岐 `feat/dtower-rerun`、起点 origin/phase0 a68672f1。prereg の commit df18070d は学習の前
  - カードは五版。PR 299 と PR 294 の内容が起点に在る
  - 5 折りの注釈・COCO の checkpoint・道具が在り、要約値が記録と一致（25 件）。動画の集合が規約の表と一致
  - 本契約以外の compute プロセスは 0 件
  - 空きは見込みの 2 倍以上

## 4. Phase B — 口と対照

### B-1 口（前例の作法）

- batch と worker 数: 設定の写し `$STORE/config/train_search_batch.py`（A-5。前例の写しと同じ sha256）を `PROBE_BATCH_SIZE=6`・`PROBE_NUM_WORKERS=4` で読ませる
- 学習率・weight decay・max_norm: 既存の `DTOWER_LR`・`DTOWER_WEIGHT_DECAY`・`DTOWER_MAX_NORM`
- 点の照合: 前例の包み `train_level.py` の写し（挙動は同じ）。実行器が点・学習率・weight decay・max_norm を JSON に書き、`load_point` をそれに差し替える。epoch 0 の群の照合（1e-15）はそのまま働く
- 折り: `EGO_ANN_DIR=data/annotations/egosurgery_tool_folds/<折り>`
- 観測器 `tools/observer.py`: 前例の観測器に、重みを読む前後のモデルの要約値（`load_digest_rank<R>.json`）と学習のデータセットの動画の集合（`loader_rank<R>.json` の `dataset_videos`）を足した。どちらも読むだけ
- 評価: 包み `tools/eval_dump.py` が評価の道具 `scripts/eval_relation_detr_map.py` を変えずに読み込み、`util.engine.evaluate_acc` を、元の関数を呼んだ後に評価器の集約済みの予測（`CocoEvaluator.predictions["bbox"]`）を読む関数に差し替える。動画ごとの COCO の値と、予測の全件（val と test）を書く。全画像で計算し直した AP と評価器の AP の差も書く
- test: 設定は `Search never evaluates test` で test を拒むので、評価の道具の `--split test`（注釈だけを `instances_test.json` に差し替え、前処理は `transforms=None` で val と同じ）で評価する
- 実行器 `tools/run_rerun.py`（前例の `run_batch.py` が土台）: 学習 → best の val と train の評価 → `tower_search_records.py detector` → test の評価（一度。既に記録が在れば止める）→ 記録の写し

### B-2 長さの対照と weight decay の換算（各 5 歩、`run_rerun.py control len_<折り>`、10:47〜10:51Z）

- 仮の weight decay（1.01058e-3、点 12、batch 6）で各折り 5 歩。5 本とも rc 0、`CONTROL_COMPLETE`
- 実測の rank ごとの DataLoader の長さ（2 rank で同じ。`$STORE/B/fold_steps.json`）: **A 802**、B 805、C 894、D 851、E 924。学習のデータセットの枚数は A 9,618、B 9,659、C 10,728、D 10,215、E 11,090
  - **折り A は 802 歩で、PR 299 の実測と同じ**（止める条件に当たらない）
  - D と E は A-5 の見込み（ceil(ceil(N/2)/6) の 852・925）より 1 歩少ない。換算には実測を使う
- 換算（weight decay = S ÷ (学習率 × 20 × 歩数)、`run_rerun.py steps`）

| 折り | 歩数 | 12 番（S 4.976e-3） | 0 番（S 4.81e-4） |
|---|---|---|---|
| A | 802 | 1.0105798004987532e-3 | 2.9987531172069826e-4 |
| B | 805 | 1.0068136645962733e-3 | 2.987577639751553e-4 |
| C | 894 | 9.065827740492169e-4 | 2.6901565995525727e-4 |
| D | 851 | 9.52391304347826e-4 | 2.8260869565217394e-4 |
| E | 924 | 8.771482683982684e-4 | 2.602813852813853e-4 |

- 折り A は prereg §2.1 の 1.01058e-3（5 桁）と改訂後の 2.998753e-4（7 桁）に一致した
- 各折りの学習のデータセットの動画の集合は 2 rank とも規約の train の 10 本と一致。5 歩で読んだ動画（各 10 本）に範囲の外は 0 件
- 道具の誤り（記録）: 対照の結果の `file_not_found` を学習の記録の文字列 `FileNotFoundError` の有無で数えていた。記録の冒頭が設定ファイルの本文を色つきで出すため、正常な 5 本で真になった。例外の行の形 `FileNotFoundError: ` に直した（5 本の記録では 0 件）。以下の 7 本は直した後の道具で数えた

### B-3 設定の到達と陽性対照（各 5 歩、10:52〜10:57Z、`$STORE/B/control_*/result.json`、`$STORE/B/controls.log`）

| 対照 | 入力 | rc | optimizer の 6 群（学習率, weight decay） | max_norm | DataLoader の batch / 長さ |
|---|---|---|---|---|---|
| p12_A | 包み、写し、batch 6、点 12、wd 1.0105798e-3 | 0（CONTROL_COMPLETE） | (3.07e-4, 1.0105798e-3), (3.07e-5, 1.0105798e-3), (3.07e-5, 0), (3.07e-5, 1.0105798e-3), (3.07e-5, 0), (3.07e-4, 0) | 0.059 | 6 / 802 |
| p0_A | 点 0、wd 2.9987531e-4 | 0 | (1e-4, 2.9987531e-4), (1e-5, 2.9987531e-4), (1e-5, 0), (1e-5, 2.9987531e-4), (1e-5, 0), (1e-4, 0) | 0.1 | 6 / 802 |
| changed（陽性対照） | batch 3、学習率 2e-4、wd 5e-4、max_norm 0.07 | 0 | (2e-4, 5e-4), (2e-5, 5e-4), (2e-5, 0), (2e-5, 5e-4), (2e-5, 0), (2e-4, 0) | 0.07 | 3 / 1,603 |
| wd_mismatch（照合の陽性対照） | 点の JSON は 12 番の値、`DTOWER_WEIGHT_DECAY` は 0 番の値 | **1**（`detector optimizer groups differ from the preregistered point`） | 記録なし | — | 6 / 802 |
| batch_mismatch（枚数の陽性対照） | batch 6、`PROBE_EXPECT_BATCH=4` | **1**（`frames per step 6 differ from the level batch 4`） | p12_A と同じ | 0.059 | 6 / 802 |
| default（既定の挙動） | 既存の `train_relation_detr_search.py` と既存の設定、`TOWER_SEARCH_POINT=0` | 0 | (1e-4, 1e-4), (1e-5, 1e-4), (1e-5, 0), (1e-5, 1e-4), (1e-5, 0), (1e-4, 0) | 0.1 | 2 / 2,405 |
| coco_missing（重みの読み込みの対照） | `RELDETR_COCO_CKPT=/nonexistent/zzz_no_such_coco_checkpoint.pth` | **1**（設定の読み込みで `FileNotFoundError: `） | 記録なし | — | 記録なし |

- 群は、本体の 2 群が点の値、backbone と線形射影の群が学習率 0.1 倍、norm と bias が weight decay 0
- default は前例の default（前例 audit 173 行）と同じ値で、既存スクリプトの既定の挙動は変わっていない
- 7 本とも保存された重み（`.pth`）は 0 件

### B-4 COCO の重みの読み込み

- 正常な対照（p12_A・p0_A・len の 5 本）: 学習の記録に `load pretrained from` が在り、`initialization_rank0/1.json` は `matched: true`、`source_sha256` `2d2c19a7a49e…`（COCO の checkpoint と同じ）、一致したテンソル 596
- 読む前後のモデルの要約値（`load_digest_rank*.json`）: rank 0 は `541b1258…` → `41a2d984…`、rank 1 は `5741eb85…` → `0239d4d4…`。両 rank とも変わった（`changed: true`）
  - rank 0 と rank 1 で値が違う。15 クラスに作り直す頭の初期化が rank ごとに違うためと見られる（確かめていない。記録だけ）
- 対照 coco_missing: `load pretrained from` の行、初期化の記録、要約値の記録がどれも無い。既存の設定は経路がファイルでなければ起動で止まる（`configs/detector_relation_detr/train_search.py` 24〜25 行）

### B-5 評価の包みの確認（10:57〜11:04Z、`$STORE/B/evalcheck_b6_seed42/`）

- 前例の checkpoint `$PREV/runs/dtowerbatch_b6_dcoco_foldA_seed42/best_ap.pth`（読むだけ。記号の繋がりを置いた）を、本番と同じ `run_rerun.evaluate` で val と test に当てた。腕に数えない
- val: AP **0.7384689855086581**。前例の `eval_val.json` の AP と全桁で一致（包みは評価の値を変えない）。全画像で計算し直した AP − 評価器の AP = 0.0。動画ごと 09 0.7172（518 枚）、10 0.6408（997 枚）。予測 454,500 件（1,515 枚 × 300）
- test: 評価の記録に `instances_test.json` の行が在り、04・05・07（1,329・1,225・1,711 枚）が評価された。計算し直しとの差 0.0。予測 1,279,500 件
- **逸脱**: test の口を確かめるために、前例（test を使わない契約）の checkpoint で折り A の test を一度評価した。値（AP 0.5099）は本契約の腕ではなく、判定・選定・記録の表のどれにも使わない。本来は本契約の run の中で確かめるべきだった
- 1 回の評価の壁時計: val 120 s、test 270 s（30 s 刻みの見回りの粒度）。予測の書き出し val 13.3 MB、test 34.2 MB

### G2

- **G2: pass**
  - 両方の点の設定（学習率、weight decay、max_norm、batch 6）が optimizer の群と DataLoader に届き、陽性対照（changed）で値が変わった。照合（wd_mismatch）と枚数の検査（batch_mismatch）は外れで止まった
  - 折り B〜E の注釈が train と val の動画の集合どおりに読める（A-5 の照合、B-2 の学習のデータセットの集合）。test の動画を混ぜた写しで外れる
  - 既存スクリプトの既定の挙動が変わっていない（default の対照）

## 5. Phase C（学習 20 本）

- 起動 2026-11-07T11:05:51Z（20:05:51 JST）。命令 `source scripts/load_env.sh && PYTHONDONTWRITEBYTECODE=1 setsid nohup .venv/bin/python experiments/analysis/dtower_rerun/tools/run_rerun.py train >> $STORE/runs.log`。実行器 PID 2255389（`setsid` で切り離し）。記録は `$STORE/runs.log`
- 順（prereg §2.1）: 12 番 seed 42 の A→E、12 番 seed 123 の A→E、0 番 seed 42 の A→E、0 番 seed 123 の A→E
- 道具の commit: 10b1961d（起動時の HEAD。各 run の `git_commit.txt` に記録される）

### C-1 1 本目（`dtowerrerun_p12_dcoco_foldA_seed42`）の記録の確かめ（15:24〜15:40Z）

- 学習 11:05:51Z〜15:07:21Z（rc 0、14,490 s）、評価と写し 15:07:21Z〜15:24:21Z。続く run（折り B）は 15:24:22Z に始まった
- 最良 epoch 12、観測 17 epoch（11 epoch 目で ×0.1、16 epoch 目で停止）、上限 36 に届かない。学習中の val AP の最良 0.72014、最良の checkpoint を評価し直した val mAP **0.7196251153088346**（AP_target 0.8044、AP_negative 0.6782）、train mAP 0.8406、test mAP（副次、1 回）0.5140285941561032
  - 学習中の値と評価し直した値の差 −5.2e-4（評価の経路の違い。記録だけ）
- 写した記録に在る: config.yaml（task_id・点・折り・seed・batch・lr・weight decay・max_norm・S・実測の歩数 802）、metrics.json、per_class_ap(_test).json、per_video_val/test.json、eval_val/train/test.json、eval_timing.json、test_access.json（`evaluations: 1`、動画 04・05・07）、warmup_rank0.json（`first_step_at_target` 802 = `steps_in_epoch0` 802）、initialization_rank0.json（`matched: true`、sha `2d2c19a7…`）、load_digest_rank0/1.json、loader_rank0/1.json、notes.md、command.sh、git_commit.txt
- 評価の壁時計は val 120 s、train 600 s、test 270 s。**30 s 刻み**（実行器が 30 s ごとに見回るため）。それより細かい精度は無い
- **集計の道具（`summarize.py`、未 commit）の試し**: 1 本で回した。表・凍結の記録（sha256 `4c542a8b5977…`、epoch 12）・恒等性の確かめを出す
- **恒等性の確かめで差が出た → 原因を特定して確かめを直した**:
  - 自分の 3 動画をプールした AP 0.5142559856 と run の test AP 0.5140285942 の差は +2.27e-4
  - 原因: どの annotation ファイル（5 折り × val/test/train の 15 個）にも `id: 0` の注釈が 1 つある。pycocotools の COCOeval は一致した GT の id を `dtm` に入れ、0 を「一致なし」と読む。このため run 自身の評価では、その注釈に一致した検出が誤検出に数えられる。プールの関数は注釈の id を 1 から振り直すため、この影響が無い
  - 確かめ: 生の test の GT で注釈の id だけを +1 ずらし、run の検出で評価し直すと 0.5142559856169862 になった。プールの値と全桁で一致した
  - 確かめを直した: 恒等性は「プールの値 = 注釈の id だけを +1 ずらした生の GT での値」で見る（完全一致を求める。1 本目は差 0.0、`exact: true`）。run の test AP との差（`run_minus_shifted`）を並べて書く
  - 副次の test の値（prereg §2.4）は、プールも動画ごとも id を振り直した評価で出す。評価器の GT による動画ごとの値は `per_video_evaluator_gt` として並べる
  - 各 run の val・train・test の値（評価器の値）は変えない。前例と同じ経路で、前例とも全桁で一致している（B-5）。id 0 の影響は、すべての評価で注釈 1 つ分だけ一様にかかる
  - 副次の 5 動画のうち、注釈 id 0 が入るのは動画 01（折り B の test の `train/01/01_1_0124.jpg`）だけである。折り C の id 0 は動画 02、折り D の id 0 は動画 06 で、どちらも副次の集合の外にある

### C-2〜C-5 12 番 seed 42 の折り B〜E

| run | 学習（UTC） | 学習の壁時計 | 最良 / 観測 epoch | val mAP | test（副次、1 回） | 動画（test） | 学習率が目標に届いた歩 = 実測の歩数 |
|---|---|---|---|---|---|---|---|
| foldB | 11-07 15:24:22〜20:42:22 | 19,080 s | 17 / 22 | 0.4755093444 | 0.4148299431 | 01・03・14 | 805 = 805 |
| foldC | 11-07 20:59:22〜11-08 01:15:22 | 15,360 s | 11 / 16 | 0.4427707417 | 0.4888533894 | 02・08・11 | 894 = 894 |
| foldD | 11-08 01:32:22〜05:59:22 | 16,020 s | 12 / 17 | 0.5062879070 | 0.5629261421 | 06・13・15 | 851 = 851 |
| foldE | 11-08 06:16:22〜10:08:52 | 13,950 s | 5 / 14 | 0.5226364946 | 0.5789070430 | 09・10・12 | 924 = 924 |

- どの run も写した記録は 28 個（1 本目と同じ）。`test_access.json` は `evaluations: 1`
- 5 本で `summarize.py` を回した（作業用の場所へ出力。commit しない）。恒等性の確かめは 5 本とも `exact: true`（差 0.0）。run の test AP − 注釈 id を +1 ずらした値: A −2.27e-4、B −1.65e-3、C −7.08e-5、D −4.87e-3、E −2.74e-4（id 0 の注釈のクラスと、それに当たる検出の数で大きさが変わる）
- 副次の 5 動画のうち動画 01 だけ、評価器の GT の値（0.6514634）と振り直した値（0.6571886）が違う。ほかの 4 動画は一致した（C-1 の予想どおり）
- 凍結する 5 つの checkpoint の sha256 を `sha256sum` で測り、`summarize.py` の値と一致した。`experiments/analysis/dtower_rerun/INTERIM.md` に書いた（Task C-4）

### C-x 前例の道具が作業ツリーから消えた（気づいたのは 2026-11-08T10:32Z）

- `git status` に、追跡下の 10 個（`experiments/analysis/dtower_batch_search/tools/*.py`：check_card・check_inputs・digests・env_capture・make_det_config・observer・procs・run_batch・summarize・train_level）の未ステージの削除が出た。フォルダの更新時刻は 2026-11-08T01:45:54Z（10:45:54 JST）。残っているのは `__pycache__/summarize.cpython-311.pyc`（11-07 05:51Z）だけ
- その時刻、この台で動いていたのは本契約の実行器（折り D の学習中）だけである。実行器と道具はこの場所に書かない（`run_rerun.py` は書き込み先として `$STORE` と `experiments/baselines/stage1_dtower_rerun/` しか持たない）
- `.stignore` には `!experiments/**/*.py` の行がある。`experiments/` の下の `.py` は git とは別に Syncthing で全台に配られるので、別の台での削除が届いたものと見ている。**他の台には接続していないため確かめていない**
- 本契約の対応: 前例の場所なので**戻さない**（契約の禁止事項。戻すと同期が他の台へ配る）。commit にも入れていない（`git add` は経路を名指しした）。利用者に伝えた
- 影響: A-7 の要約値の根に `experiments/analysis/dtower_batch_search` が入っているため、Task D の比較でこの根は変わって出る。原因はこの項に書いたとおりで、本契約の操作ではない
- 本契約の道具 `experiments/analysis/dtower_rerun/tools/*.py` も同じ規則で同期の対象である。10:32Z の時点では消えていない（`git status` に出ない）。実行器は run ごとに `train_level.py` と `eval_dump.py` を起こすので、消えればその run の起動で止まる
- **復元（利用者の指示、2026-11-08T11:15:55Z = 20:15:55 JST）**: 10 個は origin/phase0 で追跡されており、HEAD と origin/phase0 のどちらにも削除の commit は無い（`git log --diff-filter=D` が 0 件）。作業ツリーの削除は同期で届いたものと読み、`git checkout HEAD -- experiments/analysis/dtower_batch_search/tools/` で分岐の HEAD の blob から戻した。HEAD の blob と origin/phase0 の blob は同じ（`ls-tree` が一致）
  - 復元後の sha256（= HEAD の blob の sha256、10 個とも一致）: check_card `e0140eeb5cdc…`、check_inputs `b9315bd2a54b…`、digests `c6f7b525c868…`、env_capture `6ae0891feab2…`、make_det_config `3c705f9970e6…`、observer `4afbaf9b57de…`、procs `92c77add35cf…`、run_batch `b289457e9c8c…`、summarize `cce5ecb22057…`、train_level `361355eb4c78…`
  - 復元後の `git status`: 追跡ファイルの削除・変更は 0 件（本契約の audit.md の変更を除く）。削除も復元も PR の差分に入らない
  - 復元は Syncthing で他の台にも配られる。中身は phase0 と同じである
  - RESULT の逸脱（environment）に書く。完了判定 k（既存を変えていない）は、復元後の要約値で確かめる。学習はこの場所を読まないため、学習の結果には影響しない
- 同じころ、未追跡のフォルダ `experiments/analysis/grasp_cards_survey/`（11:07:38Z に作られ、無視されていない）が現れた。別の契約の生成物が同期で届いたものと見ている。**触らない・commit しない**

### C-y 利用者の決定で学習を止める（2026-11-09 02:2x JST に受けた）

- 決定: 進行中の #7（`dtowerrerun_p12_dcoco_foldB_seed123`）が終わった所で学習を止める。新しい run を始めない。#7 は捨てずに完走させる。残りの run は後日、続きの契約で回す。Task D は完了した run だけで行う。status は partial
- 止める位置の確かめ: 指示の文面に「12 番の 10 本」「14〜15/20 本」もあり、「#7 の後」と同時には成り立たないため、利用者に選択肢で確かめた。答えは「#7 の後で止める（7/20）」
- 止め方: 実行器には「今の run の後で止める」口が無い。`train_one` は始めに作業フォルダを `mkdir(exist_ok=False)` で作るので、次の run（#8 `dtowerrerun_p12_dcoco_foldC_seed123`）の作業フォルダ `$STORE/runs/dtowerrerun_p12_dcoco_foldC_seed123/` を 2026-11-08T18:13:43Z に空で作った。#7 の評価と写しの後、#8 は GPU の確かめと起動の前に `FileExistsError` で止まる（何も起動しない）
- 実行器の停止: #7 は 2026-11-08T18:52:22Z に `RUN_DONE`（val mAP 0.4897、test 0.4434）。実行器は 18:52:51Z に #8 の `work.mkdir` で `FileExistsError` を出して終わった（`runs.log` の末尾）。#8 の作業フォルダは空のまま。#8 の置き場（`experiments/baselines/stage1_dtower_rerun/` の下）は作られていない。GPU は 2 枚とも 16 MiB・0 %、compute のアプリ 0 件
- 空の作業フォルダ `$STORE/runs/dtowerrerun_p12_dcoco_foldC_seed123/` は残した（消さない。続きの契約は別の置き場を使う。同じ置き場で続けるなら、先に外す必要がある）
- `runs.log` の `STOP` の行は 0 件

## 6. Phase D（7 本で集計、2026-11-08T18:53Z〜）

### G3（完了した 7 本について）

- 7 本とも学習 rc 0、`RUN_DONE` あり。学習の記録に `load pretrained from` が在り、`initialization_rank0.json` は `matched: true`（sha `2d2c19a7…`）
- 損失の非数で止まった run 0 件（`STOP nonfinite_loss` 0 件。学習の記録の `nan` は 0 件）
- GPU の記憶の溢れ 0 件（`STOP overflow` 0 件）。学習の記録の「overflow」の 3 件は、どの run でもビルド設定の行の `-Wno-strict-overflow`・`-Wno-stringop-overflow`（2 回）である
- 勾配が非有限の歩（fp16 の scaler が飛ばした歩。学習は止まらない）: A42 13、A123 12、B42 13、B123 11、C42 11、D42 13、E42 12。前例 b6 は 12・12（`stage1_dtower_batch/*/posthoc_records.json`）。最初の数歩（scaler の立ち上がり）と、ときどき後の epoch に出る
- 13 本は回していない（利用者の決定、§5 C-y）。**G3: 完了した 7 本について pass。20 本の完了は満たさない → status partial**

### D-1 集計（`summarize.py`、出力 `experiments/analysis/dtower_rerun/summary.json`・`tables.md`・`frozen_towers.json`）

- 揃わない所を UNKNOWN にするよう集計の道具を直した: 折りの平均と |差| は 2 seed が揃う折りだけ、10 本の平均は 10 本が揃う点だけ。揃った所の記述として、5 折りが揃った seed の平均（12 番 seed 42）と、揃った折りの対だけからの seed 間 SD を件数つきで足した。回していない run の一覧（13 本）を `runs_not_done` に出す
- 結果: 12 番の折り A 0.7196 / 0.7366（平均 0.7281）、B 0.4755 / 0.4897（平均 0.4826）、C・D・E は seed 42 だけ（0.4428・0.5063・0.5226）。0 番は 0 本。12 − 0 はすべて UNKNOWN
- 12 番 seed 42 の 5 折りの平均 0.5333659205939725。seed 間の SD（折り A・B の 2 対から）0.011086676598913502。5 折りの合算は UNKNOWN
- 折り A と b6: seed 42 −0.018843870199823587（同点幅 0.0076 の外）、seed 123 +0.0038106348457985773（内）
- 副次の test（12 番 seed 42 だけ。ほかは B・C・D の run が揃わず UNKNOWN）: 5 動画を一つにまとめた AP 0.4354845117002228（5,388 枚、注釈 18,006、検出 1,616,400）。動画ごと 01 0.6572、03 0.3471、11 0.5959、13 0.5889、14 0.3142（注釈の id を振り直した評価。評価器の GT では 01 だけ 0.6515）
- 恒等性の確かめ: 7 本とも `exact: true`

### D-2 陽性対照

- 副次を 6 動画（15 を足す）にした写し: 0.4354845117 → 0.4579923925（5,808 枚）。値が変わる
- 表の値を `metrics.json` から別の命令で計算し直した: 22 マス、不一致 0（全桁）
- 存在しない名前: `dtowerrerun_p05_*` 0 件、`*foldF*` 0 件（`p12` は 7 件）。`run_record(5, A, 42)` と `run_record(12, F, 42)` は `missing`
- 凍結する塔の sha256: 折り A の checkpoint の写しの 1,001 バイト目を 0x00 に変えると sha256 `2e7d47d0…` になり、`frozen_towers.json` の `4c542a8b…` と一致しない（本物は一致）
- 同期の対象: `experiments/baselines/stage1_dtower_rerun/` と `experiments/analysis/dtower_rerun/` の下の `.pth` は 0 件。凍結する 5 本の checkpoint はすべて repo の外（`/home/ubuntu/slocal2/stage2pilot_store/`、Syncthing の同期フォルダの外）

### D-3 無変更と環境

- 禁止の場所の要約値（`$STORE/D/digests_after.json`、19:08:10〜19:11:34Z）: 根 21 件・仮想環境 2 件・凍結源がすべて A-7 と一致。`experiments/analysis/dtower_batch_search` は復元後の値で `7eb7e23c…`（開始時と同じ）
- 環境（`$STORE/D/env_relation_detr.json`・`env_body.json`）: 両方とも 22 項目で A-6 と差 0
- `make forbidden-check TASK=T-2026-11-07-dtower-rerun`: changed 254、permitted 242、**violations 8**、status fail。8 件はすべて同期で届いた別の契約の未追跡 `experiments/analysis/grasp_cards_survey/tools/*.py`（§5 C-x の終わり）。本契約の経路の違反は 0 件。8 件は消さず、無視の一覧にも足していない
- `make task-validate`: `OK`、rc 0。WARN 3 件（L2-8: index.csv 2623 → 2647、experiments.csv 1305 → 1327、verdicts.csv 1947 → 1977。runindex を作り直したため）

### D-4 runindex

- `make runindex`: 書き出し runs/*.json 2,647、index.csv 2,647 行。検証は C1〜C4・C6〜C9 PASS、**C5 FAIL**（value 空欄と is_nan が食い違う行 51。すべて `phase1__grasppilot2_G_H1_seed42`・`G_H2_seed42`・`G_all_seed42` の各 17 行。本契約の行は 0）。rc 2
- index.csv に本契約の 7 本が task_id つきで現れた
- 作り直しは、同期で届いた統合前の別の契約の run（`phase1__grasparms_*` など 17 件の新しい runs/*.json）も拾った。利用者に諮り「全体を commit（前例どおり）」の決定を受けた

### D-5 P13・P14 の陽性対照（`tools/preflight_task.py` の関数を直に呼んだ。写しは作業用の場所に置き、repo は変えていない）

- P13: 本物は PASS（`対称性の表 1 個 / 26 行に UNKNOWN と理由欠落は無い`）。写しの prereg の「数値精度」の行の判定を UNKNOWN にすると **FAIL**（`26 行を検査。UNKNOWN 1 行: 数値精度`）
- P14: 本物は PASS（`docs/proposals/2026-10-21-tower-reselect-search.md は検出 0 件（カード 16 件 / 禁止語 15 語を検査）`）。`intent.proposal_card` を `docs/proposals/zzz_no_such_card.md` にした spec では **FAIL**（`提案カードが無い`）
- 規約: `context/conventions.md` の最後の変更は 2d946b07（`conventions_rev` と同じ）、`git diff 2d946b07 HEAD -- context/conventions.md` は空。`inject_verbatim` の 11 節（prohibitions・issuer_cautions・proposal_gate・folds・split・eval_recipe・symmetry・det_groups・precision・sigma・env_p0）のアンカーはどれも 1 件在る

### D-6 終わりの試験（19:07:45〜19:38:22Z、30 分 34 秒、`$STORE/D/pytest_after.{xml,log}`）

- 命令は開始前と同じ（`PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/ -q -p no:cacheprovider --junitxml=$STORE/D/pytest_after.xml`）
- 結果: **7 failed, 989 passed**、rc 1。失敗の名前（`$STORE/D/pytest_after_failed.json`）は開始前の 7 件と同じ集合（増えていない）

### D-7 commit の前の作業ツリー（2026-11-08T19:4xZ）

- `git status --porcelain --untracked-files=all`: 追跡ファイルの**削除 0 件**。変更は本契約の `audit.md`・`tools/summarize.py`、`README.md`・`docs/experiment_log.md`（契約の Task D-4）、`runindex/` の 6 ファイル（allow_write）だけ。前例の道具 10 件は復元済みで差分に出ない
- 未追跡: 本契約の出力（REPORT・summary・tables・frozen_towers、run の記録 2 本 × 28、RESULT・result.yaml・inbox.d）、runindex/runs/ の 24 件（本契約 7、同期の別の契約 17）、同期で届いた `experiments/analysis/grasp_cards_survey/tools/` 8 件（commit しない）

## 7. 送出

- push: `origin/feat/dtower-rerun` = b524173e。PR **#305**（`gh pr view 305`: base phase0、head feat/dtower-rerun、isDraft false、state OPEN）
- RESULT.md・result.yaml に PR 番号を入れ、result.yaml を `tasks/_schema/result.schema.json` で検証して合格

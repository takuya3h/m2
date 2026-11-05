# audit — T-2026-11-05-grasp-tower-rebuild（非公式の測定。関門と設計の判断に使わない）

時刻は JST（ホストの時計は UTC なので +9 時間して書く）。ホストは andrew。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild`。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/hostdiff-andrew`。`feat/grasp-tower-rebuild` は手元にも遠隔にも無く、契約の履歴も `.sync-pause` も無かった
- `python3 scripts/task_start_classify.py` → `止めた理由 [未追跡・起点に無い] run_ptower_search.log`、`分類: 止める`（比較先 origin/phase0 89fe4a41）
  - `run_ptower_search.log`: 0 バイト、更新 2026-11-02 22:45 JST、禁止領域に属さない
- 利用者の選択（選択肢 1）: repo の外へ移して退避し、task-start を一度だけやり直す
  - **退避先** `~/m2-evacuated/T-2026-11-05-grasp-tower-rebuild/`。**一覧**: `run_ptower_search.log`（0 B、2026-11-05 23:34 JST に移した）。消していない。戻すかは報告の後に利用者へ確かめる
- 退避の後の分類 → `分類: 通す`
- `make task-start` → `分岐を作成: feat/grasp-tower-rebuild（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、`完了。`
  - 目印の中身: `task_id=T-2026-11-05-grasp-tower-rebuild` / `branch=feat/grasp-tower-rebuild`
- `make task-validate` → `OK`、exit 0
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、
  P4 prereg_committed・P5 frozen_source_hash・P13・P14（kind=analysis で対象外）、P12 refs_resolved（解決前提の参照なし）。P9 spec_lint は該当なし

## Task A — 開始状態（G1）

### A-1 分岐と起点、二本目と三本目の内容

    $ git branch --show-current; git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0
    feat/grasp-tower-rebuild
    89fe4a417e51ddc830e275ff8cd718a475ad36ba（3 つとも同じ）
    $ git ls-tree -r --name-only origin/phase0 -- <経路> | wc -l
    tasks/T-2026-11-01-grasp-pilot-g/: 5
    scripts/grasppilot/g_train.py: 1
    tasks/T-2026-11-01-grasp-pilot-d/: 5
    scripts/grasppilot/d_targets.py: 1

### A-2 開始前から在る未追跡

task-start の前に在った無視されていない未追跡は `run_ptower_search.log` の 1 件だけ（利用者の選択で退避。上記）。
task-start の後に在る無視されていない未追跡は、取り込んだ契約の 2 本だけ（`tasks/T-2026-11-05-grasp-tower-rebuild/SPEC.md`、`spec.yaml`）。消していない

### A-3 compute プロセス（`$S/start/a3_procs.json`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 53、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh            → count 6（自分のシェルの親を含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0
    $ nvidia-smi --query-compute-apps=pid,name --format=csv,noheader | wc -l       → 0

**本契約以外の compute プロセスは 0 件**

### A-4 記憶領域（`$S/start/a4_df.txt`）

    $ df -B1 /home/ubuntu/slocal2
    /dev/sdc1  7937302376448  5891984543744  1645222965248  79%
    $ du -sb /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g
    28629765031

空き 1,645,222,965,248 B。見積もり: 二本目の保存先 28,629,765,031 B（G・信号・案 A〜D の腕まで含む）を上限の目安とする。
本契約は腕を回さず t も作らないので、それ以下（空きの 1.8% 未満）。足りる

### A-5 試験と仮想環境（`$S/start/a5_pytest_start.txt`・`a5_failed_names.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped, 32 warnings in 28.12s

失敗の名前（二本目の開始時と同じ 6 件）:

    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    tests/test_fetch_task.py::test_rejects_unknown_file_name
    tests/test_research_logger.py::test_log_run_idempotent
    tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv                 108 行  9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0
    .venv-relation-detr    72 行  a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090
    （どちらも二本目の値と一致）

### A-6 GPU（`$S/start/a6_gpu_power.csv`）

| GPU | 型 | 電力の上限 | 既定の上限 | 最大の上限 | 記憶 |
|---|---|---:|---:|---:|---:|
| 0 | NVIDIA RTX A6000 | 300.00 W | 300.00 W | 300.00 W | 49,140 MiB |
| 1 | NVIDIA RTX A6000 | 300.00 W | 300.00 W | 300.00 W | 49,140 MiB |

### A-7 起票時の値

    $ git log -1 --format=%H -- context/conventions.md → 2d946b07a57abebc4a8f66150d6dbaf2ccd22186（contract.conventions_rev と一致）
    $ git log -1 --format=%H -- runindex/              → 68befc3b62ffc071077cca446df5d3c83b8c38b9（created_from.runindex_commit と一致）
    行数（見出しを除く）: index 2363、experiments 1130、verdicts 1736（created_from.counts と一致）

差し替えは無い。`meta.amendments` は空のまま

### G1 の判定

分岐 `feat/grasp-tower-rebuild`、起点 origin/phase0 89fe4a41 に二本目と三本目の内容が在り、本契約以外の compute プロセス 0 件、
空き・失敗の名前・仮想環境の要約値・電力の上限を記録した。**通過。**

## Task B — 注釈と反転の経路（G2）

### B-0 把持関係の注釈の実測（組む前）

    data/annotations/egosurgery_hts/hand_tool_seg/{train,val}.json の画像と、折り A の工程の経路のフレームを突き合わせた
    train: 画像 9,356（すべて注釈あり）、工程の経路 9,657、経路 ∩ 画像 9,356、画像 − 経路 0、loss_mask/train.txt 301 件、loss_mask ∩ 画像 0
    val:   画像 1,514（すべて注釈あり）、工程の経路 1,515、経路 ∩ 画像 1,514、画像 − 経路 0、loss_mask/val.txt 1 件、loss_mask ∩ 画像 0
    loss_mask の行数: train 301・val 1・test 158 = 460（test.txt は行数だけ数え、中身を読んでいない）

- フレーム数は §2 の値（train 9,356、val 1,514）と一致。停止しない
- **欠落の印の付いたフレームは、把持関係の注釈ファイルに 1 件も含まれない**（README §4「v1 にも v2 にも hand_tool_seg アノテーションが存在しないフレーム」と一致）。
  9,657 − 9,356 = 301、1,515 − 1,514 = 1 がちょうど印の件数。§3.1 の「印の付いたフレームを学習の対象から外す」は、注釈のあるフレームだけを学ぶことで構造的に満たされる

### B-1・B-2 5 クラスの注釈（`scripts/grasppilot/g5_build.py`、出力 `$S/g/ann/`、記録 `$S/g/ann/g5_summary.json`）

二本目の `g38_build.py` を変えずに足した派生。把持関係の注釈（hand_tool_seg）だけを開き、id 1〜5 をそのまま写す。手 4 クラスと術具 31 クラスは開かない。
学ぶフレームは工程の経路のフレームのうち把持関係の注釈があるもの（三種がそろう条件は外した。二本目の `frames_all_three` との違い）

    $ .venv/bin/python scripts/grasppilot/g5_build.py --out $S/g/ann --check-frames 16
    train 9657 9356 32408 {'01': 912, '02': 460, '03': 1068, '06': 1355, '08': 1305, '11': 747, '12': 485, '13': 809, '14': 1801, '15': 414} restore_equal True class_viol 0 ctrl 1 lm_in 0 lm_ctrl 1
    val 1515 1514 5653 {'09': 518, '10': 996} restore_equal True class_viol 0 ctrl 1 lm_in 0 lm_ctrl 1

| id | 名前 | 反転で | train インスタンス | train フレーム | val インスタンス | val フレーム |
|---:|---|---:|---:|---:|---:|---:|
| 1 | First Person's Left Hand | 2 | 8,704 | 8,659 | 1,505 | 1,491 |
| 2 | First Person's Right Hand | 1 | 8,447 | 8,386 | 1,467 | 1,463 |
| 3 | Left Hand Tool | 4 | 7,129 | 7,129 | 1,231 | 1,231 |
| 4 | Right Hand Tool | 3 | 7,176 | 7,176 | 1,274 | 1,274 |
| 5 | Two Hands Tool | 5 | 952 | 952 | 176 | 176 |

- フレーム: train 9,356、val 1,514（§2 と一致）。インスタンス: train 32,408（二本目の C1 の RLE 32,408 件と一致）、val 5,653
- 要約値: `g5_train.json` aa88bee27f6773484401f6880fc5b4176b8cf794916bbcef20c46e2a684d3f42、`g5_val.json` 762af7e8249299025e8662d4cea96ea35bcca3dc3862860480b4fb9650c9a18e
- 欠落の印の付いたフレーム（分割ごと）: train の一覧 301 件・学ぶフレームに入った件数 0、val の一覧 1 件・0 件
- 戻したマスクの一致（B-2）: 16 フレーム（seed 42 で選んだ）とも、(クラス, マスクの画素) の集合が元の注釈と一致（train・val とも `restore_equal True`）
- 対応表の検査: 外れ 0 件。**陽性対照**: 手 4 クラスの注釈（source hand_seg、id 3）を 1 件混ぜた写しで外れ 1 件（train・val とも）
- 印の検査: 入った件数 0。**陽性対照**: 印の付いたフレームを 1 件混ぜた写しで 1 件（train・val とも）

### B-3 反転の経路（`scripts/grasppilot/g5_train.py` の `G5Flip`、対照 `scripts/grasppilot/g5_flip_test.py`、出力 `$S/g/b3_flip_take.json`）

`G5Flip` は二本目の `G38` を継いだ派生のデータセットで、反転のときラベルを 0 始まりで [1, 0, 3, 2, 4] に写す（1↔2、3↔4、5 はそのまま）。
`G38` と `g_train.py` は変えていない（二本目の経路で学ぶと 38 クラスのまま動く）。
対照: 左右のラベル（1〜4）を持つ train のフレームを seed 42 で 24 枚選び、反転なし・反転ありを強制して取り出し、インスタンスごとに比べた

    $ CUDA_VISIBLE_DEVICES="" .venv/bin/python scripts/grasppilot/g5_flip_test.py --ann-dir $S/g/ann --out $S/g/b3_flip_take.json --frames 24
    G5Flip_swap {'image_flipped': 24, 'masks_flipped': 24, 'labels_swapped': 24, 'labels_unchanged': 0}
    G5Flip_noswap_copy {'image_flipped': 24, 'masks_flipped': 24, 'labels_swapped': 0, 'labels_unchanged': 24}
    G38_second_path {'image_flipped': 24, 'masks_flipped': 24, 'labels_swapped': 0, 'labels_unchanged': 24}

- 本契約の経路: 画像とマスクが反転し、ラベルが 24/24 で入れ替わる
- 入れ替えない写し（swap=False）と二本目の `G38` そのもの（`torch.rand` を差し替えて反転を強制）: 画像とマスクは反転し、ラベルは 0/24 で入れ替わらない（24/24 で元のまま）。両方向の対照で見分けられる

### B-4 欠落の印の付いたフレームを損失に入れない

- 実装の判断: 印の付いたフレームは注釈を持たない（B-0）ので学ぶフレームに入らない。`g5_train.py` は学ぶフレームと val に印の付いたフレームが 1 件でもあれば、**モデルを作る前に止める**（学習の対象から外す形。§3.1 の「外す形でよい」）
- **陽性対照**: `g5_train.json` に印の付いたフレーム `01_1_0698` を 1 件足した写し（`$S/smoke/ann_lm/`）で起動 →
  `RuntimeError: 欠落の印の付いたフレームが学ぶフレームに 1 件ある（['01_1_0698']）。学習を始めない`。歩は 0、run の置き場も作られない
- 本物の注釈の試走（`$S/smoke/smoke_all.log`、GPU 0、20 歩と val 20 枚）: 印のフレーム 0 件で通り、学習前 0.0006 → 20 歩の後 0.5043（val 20 枚だけの値。参考: 二本目の試走は把持関係 5 クラス 0.4206）。
  COCO の重み 610 個のうち 608 個を読んだ（`panoptic_head.cls_embed.{weight,bias}` は形が違い読まない）。最大確保 9,846,922,752 B。W&B は offline

### G2 の判定

5 クラスの注釈から元のマスクが戻り（16 フレーム）、反転の経路が左右のラベルを入れ替え（24/24）、入れ替えない写しと二本目の経路が同じ検査で見分けられる（0/24）。**通過。**

## Task C — G の学習（G3）

### C-1 起動と並べ方（`$S/logs/G_{all,H1,H2}.log`）

    2026-11-05 23:42 JST 起動（setsid nohup で親から切り離した。終了コードは $S/logs/G_<g>.rc）
    CUDA_VISIBLE_DEVICES=0  g5_train.py --run-dir experiments/phase1/grasptower_G_all_seed42 --ckpt-dir $S/g/ckpt/all --ann-dir $S/g/ann --videos all
    CUDA_VISIBLE_DEVICES=1  g5_train.py --run-dir experiments/phase1/grasptower_G_H1_seed42  --ckpt-dir $S/g/ckpt/H1  --ann-dir $S/g/ann --videos H1
    CUDA_VISIBLE_DEVICES=1  g5_train.py --run-dir experiments/phase1/grasptower_G_H2_seed42  --ckpt-dir $S/g/ckpt/H2  --ann-dir $S/g/ann --videos H2

- 1 枚に載せる本数: 試走の最大確保 9.85 GB/本（`$S/smoke/smoke_all.log`）から、GPU 0 に確定の G 1 本、GPU 1 に H1・H2 の 2 本（約 20 GB < 48 GB）。worker 8 × 3 = 24 < 32 CPU
- 学習前の val（3 本とも）: 5 クラスの mask mAP 0.0060。一歩の速さ（epoch 1 の 200 歩目）: 確定 0.726 秒、H1 1.011 秒、H2 1.013 秒。1 epoch の歩数 4,678・1,956・2,721

### C-3 反転の整合（学習前と二本目の G。`scripts/grasppilot/g5_signals.py flipcheck`、出力 `$S/flip/`）

val の 40 フレーム（seed 42）。P_c を 270×480 で作り、反転した画像の P を入れ替え（swap: 1↔2、3↔4）または入れ替えず（noswap）に反転し直して元の画像の P と比べた。
soft IoU = Σmin/Σmax、相関 = 画素の Pearson。両方の最大が 0.05 未満のクラスは数えない（括弧はフレーム数）

| G | 比べ方 | hand_L | hand_R | tool_L | tool_R | tool_B |
|---|---|---|---|---|---|---|
| 二本目の確定の G（38 クラス、読むだけ） | swap | 0.002 / −0.082 (40) | 0.002 / −0.094 (40) | 0.018 / 0.136 (40) | 0.025 / 0.147 (40) | 0.624 / 0.927 (8) |
| 同上 | noswap | 0.921 / 0.983 (40) | 0.901 / 0.983 (40) | 0.735 / 0.931 (35) | 0.755 / 0.913 (40) | 0.624 / 0.927 (8) |
| 学習前（COCO の重み、頭 5 クラスは乱数の初期値） | swap | 0.483 / 0.276 (40) | 0.394 / 0.136 (40) | 0.298 / 0.065 (40) | 0.278 / 0.009 (40) | 0.741 / 0.670 (40) |
| 同上 | noswap | 0.799 / 0.695 (40) | 0.521 / 0.606 (40) | 0.679 / 0.709 (40) | 0.426 / 0.533 (40) | 0.741 / 0.670 (40) |

（値は soft IoU / 相関）。二本目の G は、反転した画像でも左右のラベルを変えずに出す（入れ替えると一致がほぼ 0）。反転でラベルを入れ替えずに学んだことと合う

### 学習前の val（印を除いた値と含めた値。`g5_signals.py evalval --ckpt coco`、`$S/flip/evalval_pre_coco.json`）

- val の印の付いたフレーム: `10_1_0595` の 1 件。含めた値は、このフレームを注釈なしの画像として評価に足した値
- 除いた値（1,514）0.006026350690、含めた値（1,515）0.006025121379。除いた値は学習の記録の epoch 0（0.0060）と一致（同じ順で初期化を再現）

### C-2 利用者の指示による一時停止（2026-11-06 00:55 JST）

- 00:08 JST の測定: GPU 0（確定の G）使用率 66〜92%・VRAM 10.3/48 GB、GPU 1（H1・H2）使用率 100%・VRAM 20.6/48 GB。律速は計算で、全体の終わりは確定の G（1 epoch 約 52 分）
- 利用者の指示「VRAM の余裕あるからフルで使って一番早く終わるようにして」→ 選択肢（処方を保って詰める / DDP / batch を上げる）を示した →
  **利用者「一旦、バッチサイズについて検討するので停止して」**
- 3 本のプロセスグループ（pgid 1748461・1748462・1748463、各 10 プロセス）に SIGSTOP。状態は全員 T、GPU 使用率 0%（VRAM は確保されたまま）。出力は消していない
- 止めた時点: 確定 epoch 1 = 0.5747・epoch 2 の 2,600/4,678 歩、H1 epoch 1 = 0.5179・epoch 2 の 1,600/1,956 歩、H2 epoch 1 = 0.5666・epoch 2 の 800/2,721 歩
- 再開は SIGCONT（`kill -CONT -- -<pgid>`）。batch を変えるなら 3 本を止め、出力を `$S/aborted/` へ移してから起動し直す（利用者の決定を待つ）

### C-4 利用者の指示による契約の中止（2026-11-06 01:05 JST）

- 利用者「ごめん契約も停止して良い」→ 3 本のプロセスグループに SIGTERM、続けて SIGCONT（停止中のプロセスに終了を届けるため）。8 秒後に各グループの残り 0、GPU 0・1 とも 16 MiB・compute 0 件
- 終了の処理は走らない形で終わった（`$S/logs/G_<g>.rc` は書かれていない。metrics.json・per_class_ap.json・notes.md・end.txt も無い）
- 途中の出力は消さずに移した: `experiments/phase1/grasptower_G_{all,H1,H2}_seed42/` → `$S/aborted/try1/`、`$S/g/ckpt/` → `$S/aborted/try1/ckpt/`（各 best.pth は epoch 1 の重み）、
  ログの写し `$S/aborted/try1/G_*.log`。`experiments/phase1/` に本契約の run は残っていない（`grasptower` の件数 0）

## Task E — 終わりの確かめ（中止の時点）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped, 26 warnings in 28.65s（失敗の名前の集合は開始時と diff なし。$S/end/pytest_end.txt）
    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv 9c7be5c9…94c0、.venv-relation-detr a74c9c78…b090（開始時と一致）
    $ make forbidden-check TASK=T-2026-11-05-grasp-tower-rebuild
    changed 17、violations 10、status fail

- 違反 10 件はすべて同期処理が実行中に運んだ別の契約の未追跡のファイル（`experiments/analysis/stage2_pd_w3_lowlr/tools/*.py` 4 件、
  `experiments/phase1/w3lr_pd_*/logs/eval_meta_val.json` 6 件）。**本契約の経路の違反は 0 件**。届いたファイルには触れていない（§7-10）
- changed 17 のうち 7 件は本契約のファイル（契約 2 本、audit、scripts/grasppilot/g5_*.py 4 本）で、道具は本契約の新しいファイルを変更として拾っている（禁止領域の外なので違反にならない）

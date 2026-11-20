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

**G1: 利用者の判断で pass**（2026-11-20）。欠けは `$S/inputs/` だけで、停止して諮った。利用者の選択「原本を本契約へ写す」:

    $ cp -p $S/T-2026-10-31-grasp-pilot-probe/e/weights/mmdet/mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth $O/inputs/coco/
    $ sha256sum <原本> <写し>     （$O/start/a8_coco_copy_sha256.txt）
    41b088b62838c986004f94bab2870395b669ec6bd11b6590369b838b0de06879（両方）

同じ時に §4 の読み 3 点を諮った（`meta.amendments` の 3 件目）: 辺は 3 種、DGH-U は [u, u, u]、正解の手の節は同じ側のマスクの和集合。

## Task B — 塔（G2）

### B-1 注釈（`$O/ann/{G3,H4,G5r}_{train,val}.json`・`*_summary.json`、道具 `scripts/grasppilot/ghg_tower.py build`）

学ぶフレーム = 折り A の train / val の動画の工程の経路のうち、その注釈のファイルに在るフレーム。注釈の無いフレームは入れない。

| 塔 | part | フレーム | インスタンスの無いフレーム | インスタンス | クラス別（インスタンス） | 戻したマスク | 対照（クラスの外を 1 件混ぜる） |
|---|---|---|---|---|---|---|---|
| G3 | train | 9,356 | 192 | 15,257 | 左手の器具 7,129・右手の器具 7,176・両手 952 | 16/16 一致 | 外れ 1 |
| G3 | val | 1,514 | 6 | 2,681 | 1,231・1,274・176 | 16/16 | 外れ 1 |
| H4 | train | 9,627 | 0 | 27,726 | 自分の左 8,704・右 8,447・他者の左 6,542・右 4,033 | 16/16 | 外れ 1 |
| H4 | val | 1,515 | 0 | 4,918 | 1,505・1,467・1,079・867 | 16/16 | 外れ 1 |
| G5r | train | 9,356 | 0 | 32,408 | 11-05 の G5 と同じ件数 | 16/16 | 外れ 1 |
| G5r | val | 1,514 | 0 | 5,653 | 11-05 と同じ | 16/16 | 外れ 1 |

- 欠落の印: hand_tool_seg の一覧（train 301・val 1）は G3・G5r の学ぶフレームに 0 件（印のフレームは注釈のファイルに無い。11-05 と同じ）。
  H4 の学ぶフレームには train 271・val 1 件が入る。README（`hand_tool_seg/README.md` §4）は印を「hand_tool_seg タスクは loss=0（他タスクは通常評価）」とするので、hand_seg の H4 はそのまま学ぶ。hand_seg に欠落の印の一覧は無い
- G3 のインスタンスの無いフレーム（train 192・val 6）は、把持の注釈が在り器具のクラスが無いフレーム（手だけ）。注釈が「持つ器具なし」と言うフレームとして学ぶ（judgement）

### B-2 反転の取り出し（`$O/flip/flipdata_{G3,H4,G5r}.json`、`ghg_tower.py flipdata`、train の 24 フレーム、反転を強制）

| 塔 | 経路 | 画像 | マスク | ラベルを入れ替えた | ラベルが変わらない |
|---|---|---|---|---|---|
| G3・H4・G5r | swap（本契約の経路） | 24/24 | 24/24 | 24/24 | 0/24 |
| G3・H4・G5r | noswap_copy（入れ替えない写し） | 24/24 | 24/24 | 0/24 | 24/24 |

### B-3 試走（`$O/smoke/`、60 歩、val は 10 batch）

    G3: 1 歩 1.03 秒（GPU 2 枚で同時）、最大確保 25,634,862,592 B、COCO の重み 608/610、学習前 0.0657 → 60 歩後 0.7003（val の 20 フレームだけ）
    H4: 1 歩 1.07 秒、最大確保 25,634,881,024 B、学習前 0.0004 → 0.5866（同）

- 1 epoch の見込み 約 20 分 ＋ 評価。1 枚に 1 本ずつ（2 本は記憶に載らない）。本番は `tools/run_towers.sh`（待ち行列、G3・H4 を先、G5r を最後）で 2026-11-20 15:22 JST に始めた

### B-4 本番の塔 7 本と G2（`experiments/phase1/grasp_hand_graph_tower_*`、待ち行列の記録 `$O/queues/towers/events.log`）

7 本とも rc=0。最後の G5r が 2026-11-21 04:21 JST に終わった。val は 09・10（H1・H2 の塔も打ち切りの判定は同じ val で行う）。

| 塔 | 学ぶ動画 | 学習前 | 選んだ回の val の mask mAP | 選んだ回 | 打ち切り（忍耐 4） | 上限 36 | 時間 |
|---|---|---|---|---|---|---|---|
| G3 | train 全体 | 0.0050 | 0.5737 | 7 | 11 | 届かない | 4.08 h |
| G3 | H1 | 0.0050 | 0.4955 | 4 | 8 | 届かない | 1.47 h |
| G3 | H2 | 0.0050 | 0.5384 | 4 | 8 | 届かない | 1.87 h |
| H4 | train 全体 | 0.0055 | 0.6045 | 6 | 10 | 届かない | 4.04 h |
| H4 | H1 | 0.0055 | 0.6317 | 11 | 15 | 届かない | 3.01 h |
| H4 | H2 | 0.0055 | 0.5799 | 2 | 6 | 届かない | 1.91 h |
| G5r | train 全体 | 0.0060 | 0.6560 | 8 | 12 | 届かない | 4.76 h |

学習後の反転の整合（SPEC §3.4。`$O/flip/flipmodel_{塔}_{final,coco}.json`。val の数十フレーム、左右のクラスだけの soft IoU の平均）

| 塔 | 学習後 入れ替え | 学習後 入れ替えない写し | 学習前（COCO）入れ替え | 学習前 入れ替えない写し |
|---|---|---|---|---|
| G3 | 0.6504 | 0.0220 | 0.5164 | 0.7737 |
| H4 | 0.7361 | 0.1934 | 0.4079 | 0.6758 |
| G5r | 0.7951 | 0.0194 | 0.3631 | 0.6064 |

- G3・H4 は推論の前に `run_signals.sh` が測って関門にした（入れ替え ＞ 入れ替えない写し）。G5r は推論しないので §3.4 の対象外だが、G2 の「三種の塔」に合わせて同じ道具で測った（2026-11-21 04:2x JST）
- 対照: 左右を学んでいない COCO の重みでは大小が逆になる（入れ替えない写しの方が高い）。測り方が左右の学習を見分けている
- **G2 は通る**（三種とも打ち切りで止まり、上限に届かず、選んだ回が学習前を上回り、反転で入れ替えた一致が入れ替えない写しを上回る）

## Task C — 道具と確かめ（G3 の前半）

### C-1 dp_train・dp_model に足したもの（commit ad0e32ea）

- `dp_model.ToolHandGraph`（型 graph）と `dp_train` の型 GR（`--gr-dir`・`--gr-N`・`--gr-L`）、腕 D・DG・DH・DGH・DGH-U・DGH-noCF・DGH-GT
- `--ckpt-dir`（界面の重みの置き場。既定は従来の `$S/<task-id>/dp_ckpt`）、`--save-last-probs`（最後の epoch の val の確率と値）
- 界面の大きさ: 術具・手の MLP（→ 64 → 64）、辺の種類ごとの伝播の線形 64×64 を 3 種 × 2 向き × L 段、出力射影 256 → 2048。
  パラメータ数は L 1 で 561,728、L 2 で 586,688（N は行の数だけを変え、パラメータは変えない）

### C-2 既定の挙動が変わらないこと（SPEC §2）

主: andrew で回した前回の run `stage2pilot_dp_009_D1-L1_pred_noCF_seed42`（T-2026-10-18、既定の引数）を本契約の識別子で回し直した。

    $ python scripts/stage2pilot/dp_train.py train --type D1-L1 --arm pred_noCF --seed 42 --task-id T-2026-11-20-grasp-hand-graph-pilot \
        --exp-prefix grasp_hand_graph_repro --ckpt-dir $O/repro/dp_ckpt
    → experiments/phase1/grasp_hand_graph_repro_001_D1-L1_pred_noCF_seed42
    phase_jaccard 0.785115373498492・accuracy・macro F1・best_epoch 6・epochs_run 16・早期停止 16・init 0.7762185528074379・per_video・クラス別: すべて記録と一致
    history 16 epoch の val の Jaccard 一致、train の損失の差の最大 0.0、val の確率の差の最大 0.0
    界面の重みのテンソルはすべて一致（ファイルの sha256 は違う: torch の zip の中のフォルダ名がファイル名から付くため）

補助: andrew には W3・収束規則の前回の run が無い（前回は bengio、材料も andrew に無い）。起点 origin/phase0 の `dp_train.py`・`dp_model.py` の写しと今の版を、
同じ入力・同じ引数（`--type D2 --arm pred_noCF --scope W3 --seed 42 --converge`）で回した（`tools/run_repro_oldnew.sh`、`$O/repro/cmp_result.txt`）。
変えていない部品（common・shuffle_signals・__init__）は記号リンクで、`git diff origin/phase0` は空（0 B）。

    old・new とも J 0.7304483966054434、選んだ epoch 56、72 epoch、学習率を落とした epoch 64
    metrics の違い 0 件（所要・重みの経路と要約値を除く）、history 72 epoch 一致、確率の差 0.0、界面と受け取り手のテンソル一致、config の違い 0 件
    今の版は新しい引数を渡さなければ metrics_last.json・val_probs_last.npz を書かない

1 回目は起点の版の写しの `common.py` が repo の根を引けずに止まった（`$O/repro/` を根と読んだ）。写すのを変えた 2 ファイルに絞って回し直した

### C-3 グラフの経路の試走（試走の塔の重みで各 30 フレーム、`$O/smoke/`）

- `ghg_graph.py det`: 検出の上位 300 を 4 つの配列に（val 確定 1,515・train 確定 9,657・train 交差適合 H1 の塔 → H2 の動画 5,582・H2 の塔 → H1 の動画 4,075。各フレーム 300 query）
- 工程の経路のフレームはすべて検出の出力を持つ（train 9,657・val 1,515、欠け 0）。正解の枠が 10 を超えるフレームは train に 1 件（11 個）、30 を超えるものは 0 件
- 試走の組み立て: 表の検査の外れ 0（D に手の節を入れた写しで外れ 1）、交差適合の外れ 0（確定の G3 を 5 フレーム混ぜた写しで外れ 5）、
  val の正解の持ち手と注釈の把持の一致 3,610/3,807（0.948）、左右を入れ替えた写し 424/3,807（0.111）
- 恒等性（N10 L2、W1、5 腕）: 学習前のロジットの差の最大 0.0、Jaccard 0.7762185528074379 が記録と一致、出力射影を N(0, 0.05²) にすると差 0.116〜1.346
- 学習の試走（`grasp_hand_graph_chk_001`・`_002`。腕に数えない）: W1 2 epoch、W3 の A0 2 epoch。W3 の A0 の陰性対照（DGH の材料を入れても出力が変わらない）は差 0.0
- 塔単独（本契約の識別子で 1 回、`tools/tower_alone.py`、`$O/e/tower_alone.json`）: J 0.7762185528074379・acc 0.8712871287128713・6 工程 0.7773831834035493、記録と一致

### C-4 段取りの直し（見直しの後）

- `tools/run_signals.sh` の学習後の反転の整合（§3.4）を推論より前へ移し、G2 の反転の部分の門（左右のクラスで swap の soft IoU > noswap）を足した。
  外れ・塔の学習の失敗・G2 の部分の外れでは `$O/logs/STOP_<塔>` を置いて推論せずに止まる。直す前の段取りは、塔の記録を待つ段階で止めた（推論は 0 件）
- 反転の整合の道具は試走の重み（H4、4 フレーム）で動くことを確かめた: swap 0.640・noswap 0.327
- `tools/aggregate.py` に run の終わりの確かめを足した: 期待 96 本と見つけた本数、存在しない腕の名前で 0 件・在る run の名前で 1 件（SPEC §8 Task D）

### C-5 G3・H4 の推論（`$O/signals/raw/*`、`tools/run_signals.sh`、記録 `$O/logs/signals_events.log`）

8 本とも rc=0。工程の経路のフレームをすべて覆い、画像の欠け 0。上位 100 のインスタンスを持つ。

| 名前 | 当てた塔（選んだ回） | 動画 | フレーム | 空のマスクのインスタンス | 秒 |
|---|---|---|---|---|---|
| G3_all_val | G3 確定（7） | 09,10 | 1,515 | 775 | 183 |
| G3_H1_train | G3 H1（4） | 02,03,08,13,14 | 5,582 | 3,008 | 714 |
| G3_H2_train | G3 H2（4） | 01,06,11,12,15 | 4,075 | 1,092 | 593 |
| G3_all_train | G3 確定（7） | train 全体 | 9,657 | 4,133 | 1,379 |
| H4_all_val | H4 確定（6） | 09,10 | 1,515 | 352 | 141 |
| H4_H1_train | H4 H1（11） | 02,03,08,13,14 | 5,582 | 9,051 | 517 |
| H4_H2_train | H4 H2（2） | 01,06,11,12,15 | 4,075 | 584 | 378 |
| H4_all_train | H4 確定（6） | train 全体 | 9,657 | 5,255 | 895 |

- 空のマスク（確率 > 0.5 の画素が無い）のインスタンスの枠は 0。持ち手の重なり（IoU）は 0 になる。得点との関係は測っていない

### C-6 グラフの組み立て（`$O/graph/{腕}_{train,val}.npz`・`assemble_report.json`、`ghg_graph.py assemble --agree-train`、記録 `$O/logs/assemble*.log`）

3 回回した。1・2 回目は道具の誤りで、どちらも自分の道具を直した。

1. 1 回目（rc=1）: train の正解の持ち手と注釈の一致を数える段で KeyError（`02_1_0141`）。正解の器具の枠が 0 個で把持の注釈が在るフレームを、一致の関数が飛ばしていなかった。
   枠が 0 個なら数える枠が無いので飛ばす条件に足した。train の 7 腕の出力は 1 回目と 2 回目で要約値が一致（`$O/logs/assemble_try1_train_sha.txt`）
2. 2 回目（rc=0）の記録を読み直すと、グラフの段の試験の動画の検査（i）にフレームの識別子を渡していた。動画の番号と照らさないため、試験の動画が混ざっても外れが出ない（検査が働いていない）。
   対照も動画の一覧に「04」を足すだけで、同じ経路を通っていなかった。フレーム → 動画に直し、対照は train のフレームに動画 04 のフレームを 1 つ混ぜて同じ経路に通すようにした
3. 3 回目（rc=0、道具の要約値 `0be2a0af…`）: 14 の出力すべてが 2 回目と要約値で一致（`$O/logs/assemble_try2_sha.txt`）。以下はこの回の値

| 確かめ | train | val | 対照（失敗するはずの入力 → 観測） |
|---|---|---|---|
| 腕の表（節・持ち手・手・辺の有無、DGH-U の一様、辺 = 持ち手） | 外れ 0（7 腕） | 外れ 0 | D に手の節を入れた写し → 外れ 1 |
| 交差適合の出所（その塔が学んだ動画のフレームに当てていない） | 検出・G3・H4 とも外れ 0（9,657） | — | 確定の G3 を 5 フレーム混ぜる → 外れ 5 |
| 正解の持ち手と注釈の把持の一致 | 20,433/21,021（0.972） | 3,610/3,807（0.948） | 持ち手の左右を入れ替えた写し → 0.092・0.111 |
| 試験の動画（04・05・07）を使っていない | 塔 6・推論 8・検出 4・グラフ 2 の段とも 0 | 同 | train のフレームに 04 のフレームを 1 つ混ぜる → 1 |

- 数: 把持の注釈の無いフレーム train 299・val 1、正解の器具の枠の無いフレーム train 39、手の注釈の無いフレーム train 30。正解の枠が 10 を超えるフレーム train 1
- 予測の手の節は全フレームで左右とも在る（H4 の上位 100 に各側のインスタンスが必ず含まれた。§4.1 は得点の閾値を置かない）

### C-7 恒等性（完了判定 g。`$O/identity/GR_{W}_N{N}_L{L}.json`・`identity_summary.json`、`tools/run_identity.sh`、GPU 0）

4 設定 × W1・W2・W3 × 8 腕 = 96 組み合わせ、12 本とも rc=0。

| 確かめ | 観測 | 対照（失敗するはずの入力 → 観測） |
|---|---|---|
| 学習前のロジットが塔単独と一致 | 96/96 で差の最大 0.0、Jaccard 0.7762185528074379 が記録と一致 | 零初期化の出力射影を N(0, 0.05²) にする → 96/96 で変わる（差の最小 0.116 は W1 N10 L1 の A0、最大 3.135 は W1 N30 L2 の DGH-U） |
| 学ぶ範囲（W2・W3） | 定義（W2 = 界面と末端の refine、W3 = 界面と head 全体）の名前と学ぶ名前が一致 | 範囲の外の名前を 1 つ混ぜる → 一致しない |
| 学ぶ範囲（W1） | 学ぶ名前 = 界面の名前 | head の名前を 1 つ混ぜる → 一致しない |

- 不合格 0 件（`bad: []`）。界面の大きさ L1 561,728・L2 586,688（N によらない）
- **G3 は通る**（C-6 の正解のグラフと注釈の一致、C-7 の恒等性と陽性対照）。2026-11-21 JST

## Task D — 腕（G4）

### D-1 96 本（`experiments/phase1/grasp_hand_graph_arm_{001..096}_*`、`tools/run_arms.sh`、記録 `$O/logs/arms/events.log`）

    2026-11-21 04:38:41 JST 開始、05:00:30 JST 終わり（21 分 49 秒）。GPU 2 枚 × 4 本並行（NW = 8）
    rc=0 96 本、rc≠0 0 本、飛ばし 0 本。1 本 4.3〜182.8 s

- 収束規則: 96 本とも打ち切りで止まった（上限 120 に届いた本 0）。総 epoch 17〜51、選んだ回 1〜35
- 証拠: 96 本とも config.yaml・command.sh・git_commit.txt・metrics.json・metrics_last.json・per_class_ap.json・notes.md・logs/history.json・
  predictions/val_probs_{best,last}.npz が在る。config の task_id は 96/96 で本契約、git_commit は 96/96 で 096d56b9
- 受け取り手: W1 の 32 本は `receiver_unchanged` が True（W2・W3 の 64 本は学ぶので False）
- 終わりの確かめ（`tools/aggregate.py` の end_check）: 期待 96・見つけた 96、存在しない腕の名前で 0 件、在る run の名前で 1 件
- **G4 は通る**

### D-2 腕の間でちょうど同じになったもの（確率で確かめた）

- 辺の無い腕（A0・D・DG・DH）は、同じ W・同じ N で L1 と L2 の val の確率が一致した（12 組とも差 0・argmax の違い 0、選んだ回も同じ）。
  辺が無いと伝播の層に流れるものが無く、L の層は出力に効かない。辺の在る DGH は L で変わる（確率の差 0.201〜0.724、argmax の違い 17〜72 フレーム）。
  A0 はさらに N にもよらない（入力が空）。SPEC §5 の「A0 は interface の大きさが設定で変わるので設定ごとに回す」は、W ごとに 4 本とも同じ値になった
- W2 の N10（L1・L2）の DG − D は指標がちょうど同じ（2 個）。確率は最大 0.0146 違うが、argmax が全フレームで一致した

## Task E — 集計・報告

### E-1 集計（`$O/e/summary.json`、`tools/aggregate.py`）と REPORT（`experiments/analysis/grasp_hand_graph_pilot/REPORT.md`、`tools/make_report.py`、477 行）

    {"expected_runs": 96, "found_runs": 96, "nonexistent_arm_hits": 0, "known_run_hits": 1, "all_converged": true, "reached_cap": []}
    {"n_runs": 96, "recompute_max_dev": 0.0, "recompute_control_all_detected": true, "j7_equals_phase_jaccard_all": true,
     "n_diffs_best": 96, "n_metrics_identical_best": 2, "n_unreadable_best": 66}

- 測り直し: 96 本の最良と最後の回の val の確率から J・acc・工程別 J を測り直し、記録とのずれの最大 0.0。1e-6 ずらした写しは 96/96 で検出
- `make_report.py` に G5r の反転の行と並行の数を足した（集計の前）

### E-2 変えていないこと（完了判定 j。`$O/end/`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 985 passed, 5 skipped（30.89 s）。失敗の名前は開始時（A-5）と diff で一致
    $ uv pip list ... | sha256sum   → .venv 9c7be5c9…、.venv-relation-detr a74c9c78…（A-5 と一致）
    $ sha256sum 工程塔の best.pth・特徴のキャッシュ all_gap.npz・COCO の重みの写し
    0d76d446…6ad6d・c402e214…172da・41b088b6…de06879（A-8・G1 と一致）
    $ find data/annotations data/raw data/external third_party $S/T-2026-10-18-stage2-pilot-folda $S/T-2026-11-05-grasp-tower-rebuild $S/T-2026-10-31-grasp-pilot-probe -newer $O/start/a1.txt
    （0 件。開始の記録より後に書き換わったファイルは無い。検出塔の上位 300 の 4 ファイルの大きさは A-8 と一致、注釈 4 ファイルの更新は 2026-10-06・07）
    $ git diff --stat origin/phase0 -- data third_party   → 差 0
    $ git diff --numstat origin/phase0 -- scripts/ src/ tests/ configs/
    ghg_graph.py +504・ghg_tower.py +670（新規）、dp_model.py +67 −3、dp_train.py +75 −5（消した 8 行は型・腕の組や分岐の条件に要素を足した行の旧版）
    $ make forbidden-check TASK=T-2026-11-20-grasp-hand-graph-pilot
    status pass、changed 987、permitted 979、violations 0、effective_allowances 2（allow_write の 2 経路）
    対照: TASK を渡さないと status fail・本契約の経路が違反として名指される（許可を読まないと拾う）

### E-3 腕の学習・評価の段の test（完了判定 i の残り）

    96 本の config.yaml の videos: train 01,02,03,06,08,11,12,13,14,15・val 09,10（96/96 同じ）、{04, 05, 07} との共通 0
    （dp_train は実行時に `C.assert_no_test` で共通 1 件以上なら止まる）。対照: 同じ数え方に 04 を混ぜた集合で共通 1
- 塔・推論・検出・グラフの段は C-6（20 段とも 0、04 のフレームを混ぜた対照で 1）

## 逸脱と判断の控え（RESULT へ写す）

- judgement: `meta.created_from`・`contract.conventions_rev` は起点の実測と一致し、§0 の「差し替えて amendments に記録」は差し替えるものが無かった（起票者は食い違いを想定）
- judgement: `inputs.data.split_files`（`data/splits/ego_val.txt`）は参照しなかった（§0 の指示どおり）
- judgement: G3 のインスタンスの無いフレーム（train 192・val 6）は「持つ器具なし」として学ぶ。H4 は hand_tool_seg の欠落の印のフレーム（train 271・val 1）も学ぶ（README §4）
- judgement: 正解の枠が N を超えるフレーム（train 1 件、11 個）は得点がすべて 1 で順が決まらないため、注釈の順（annotation id の昇順）に先頭 N 個を取る
- judgement: 確かめの run（`grasp_hand_graph_chk_*`・`grasp_hand_graph_repro_*`・`grasp_hand_graph_cmp_{old,new}_*`）は腕に数えない。
  `cmp` の 2 本は界面の重みを `$S/grasp_hand_graph/` の下へ置くため、識別子を `grasp_hand_graph/repro_cmp` にして回した（本契約の識別子ではない）
- judgement: 型 GR の空のグラフは読み出しが 0 なので、A0 が学べるのは出力射影の bias だけ（全腕で同じ仕組み。W1 で A0 が塔単独から動くのは学んだ定数の足し分）
- judgement: G3・H4 の推論（Task C）は、その塔の 3 本の G2 の部分（打ち切り・学習前を上回る・反転の整合）を確かめた後、残りの塔（H4 の半分・G5r）の学習と並行して始める
- environment: ruff の指摘が新しい道具に 4 件（import の並び 3、変数名 `O` 1）。学習中の塔の記録に要約値が入っている `ghg_tower.py` は書き換えていない
- judgement: G5r の学習後の反転の整合は §3.4（G3・H4）の外だが、G2 の「三種の塔」に合わせて同じ道具で測った（B-4）
- judgement（実行者の道具の誤り）: `ghg_graph.py assemble` の誤り 2 件を直して回し直した（C-6。一致の関数の KeyError、試験の動画の検査がフレームの識別子を見ていた）。グラフの出力は直す前後で要約値が一致

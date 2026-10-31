# audit — T-2026-11-01-grasp-pilot-g（非公式の測定）

時刻は JST。ホストは andrew。版管理の外の置き場は
`S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g`。

## 0. 始める（手順書の 0〜4）

- 開始時の分岐は `feat/grasp-pilot-probe`（清浄）。`feat/grasp-pilot-g` は手元にも遠隔にも無く、契約の履歴も `.sync-pause` も無かった
- `python3 scripts/task_start_classify.py` → 全区分 0 件、`[task-start] 分類: 通す`（比較先 origin/phase0 ebc35d7b）
- `make task-start` → `分岐を作成: feat/grasp-pilot-g（起点 origin/phase0）`、**`.sync-pause を作成`**（この契約が置いた目印）、`完了。`
- `make task-validate` → `OK`、exit 0
- `make task-preflight` → 7 PASS / 0 WARN / 7 SKIP / 0 FAIL、exit 0。SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（契約に記載なし）、
  P4 prereg_committed・P5 frozen_source_hash・P13・P14（kind=analysis で対象外）、P12 refs_resolved（解決前提の参照なし）。P9 spec_lint は該当なし

## Task A — 開始状態（G1）

### A-1 分岐と起点、PR 272

    $ git branch --show-current; git rev-parse HEAD origin/phase0; git merge-base HEAD origin/phase0
    feat/grasp-pilot-g
    ebc35d7b67d85983d31af087a08a4c2968950fad（3 つとも同じ）
    $ gh pr view 272 --json state,mergedAt,mergeCommit
    MERGED 2026-10-31T15:57:36Z、merge commit c942fd13
    $ git merge-base --is-ancestor 3eb81227 origin/phase0   → 真（一本目の分岐の先頭が起点の祖先）
    $ git ls-tree --name-only origin/phase0 scripts/grasppilot/ | wc -l   → 17
    $ git ls-tree --name-only origin/phase0 tasks/T-2026-10-31-grasp-pilot-probe/  → RESULT.md SPEC.md audit.md result.yaml spec.yaml

### A-2 開始前から在る未追跡

task-start の前の分類器で全区分 0 件。task-start の後に在る無視されていない未追跡は、取り込んだ契約の 2 本だけ
（`tasks/T-2026-11-01-grasp-pilot-g/SPEC.md`、`spec.yaml`）。消していない

### A-3 compute プロセス（`$S/start/a3_procs.txt`、道具 `scripts/grasppilot/proc_enum.py`）

    $ python3 scripts/grasppilot/proc_enum.py
    n_processes 39、gpu_pids []、n_compute 0
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /usr/bin/zsh            → count 5（自分のシェルの親を含む）
    $ python3 scripts/grasppilot/proc_enum.py --match-exe /nonexistent/bin/python9 → count 0
    $ ps -eo pid,user,comm,args で comm が python・torchrun で始まるもの（道具自身を除く）→ 0 件
    $ nvidia-smi --query-compute-apps → 0 件

**本契約以外の compute プロセスは 0 件**

### A-4 記憶領域（`$S/start/a4_df.txt`）

    $ df -B1 /home/ubuntu/slocal2
    /dev/sdc1  7937302376448  5859693723648  1677513785344  78%

空き 1,677,513,785,344 B。見積もり（上限側）: 38 クラスの注釈 ≤ 2 GB、G の重み 3 本 × （最良と最後）≤ 3 GB、
信号と標的 ≤ 10 GB、工程塔の重み 3 本 ≤ 1 GB と特徴 3 組 ≤ 1 GB、案 B の界面の重み ≤ 1 GB、予測と記録 ≤ 10 GB。合計 ≤ 28 GB（空きの 1.7%）。足りる

### A-5 試験と仮想環境（`$S/start/a5_pytest_start.txt`・`a5_pkgs_*.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    6 failed, 975 passed, 5 skipped, 26 warnings in 27.73s

失敗の名前（一本目の開始時・終了時と同じ 6 件）:

    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    tests/test_fetch_task.py::test_rejects_unknown_file_name
    tests/test_research_logger.py::test_log_run_idempotent
    tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

    $ uv pip list --python <venv>/bin/python --format freeze | sha256sum
    .venv                 108 行  9c7be5c99d6b768ab3cfa5a0c2f479520b7486cffbd866de0f3759a6682f94c0
    .venv-relation-detr    72 行  a74c9c787e79f01405b27797cf5fa9b3ff3f3858caf65e641bec1a86dad5b090
    （どちらも一本目の値と一致）

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

分岐 `feat/grasp-pilot-g`、起点 origin/phase0 ebc35d7b に PR 272 の内容が在り、本契約以外の compute プロセス 0 件、
空き・失敗の名前・仮想環境の要約値・電力の上限を記録した。**通過。**

## Task B — C3 の直し（G2）

### B-1 直したところ（`scripts/audit_l0_hts_acceptance.py`。直す前の写しは `$S/b/audit_l0_hts_acceptance.orig.py`、sha256 06ba1b2d…0899 → bbd23ef3…805a）

- **C3 の定義（§3.1）**: 左辺は raw 02_hand の注釈の `file_name` から導く区間の集合（手注釈が 1 件以上ある区間）、右辺は候補の注釈の `file_name` から導く区間の集合。
  両辺とも区間の名前で比べる（旧版の左辺はディレクトリ名 26 件で、`03_3` が構成上いつも欠けた＝欠陥 2）。
  合格は「左辺が 25 件で `03_3` を含まず、右辺に欠けが無く、集合件数が 57,172」。判定の鍵は `C3_hand_coverage_57172`（旧 `C3_hand_total_57173`）
- **集合件数の鍵は (フレーム名, 枠を小数 2 桁に丸めたもの, クラス)**。前回の数え（`experiments/analysis/hts_candidate_acceptance/hand_count.py` の `set_by_frame_bbox_cat`）と同じ鍵。
  **重複の 1 件（`05_1_0575.jpg`、cat 4、bbox (0, 6, 940, 1066)、`hand_seg/test.json` の ann 5889・5890、正本の ann 1519・1520）はマスクが同一ではない**:
  RLE の sha256 は 4366db94… と 735dcfdb…、面積は 542,293 と 542,541。マスクまで鍵に入れると集合件数は 57,173 になり、57,172 にならない
- **欠陥 1**: `_splits()` は指定の split のファイルが一つでも無ければ `FileNotFoundError` で止まる（旧版は黙って飛ばし、0 件として通した）。raw 02_hand の JSON が一つも無いときも止まる
- **欠陥 3**: C1 の `seg_profile` は全件を見る（旧版は先頭 3,000 件）
- 入力と出力の引数を足した（`--hand-dir`・`--hand-prefix`・`--hand-splits`・`--toolhand-dir`・`--toolhand-prefix`・`--out`）。**渡さなければ入力と出力は従来の経路**
  （既定の出力は従来どおり `experiments/audit/l0_hts_acceptance/acceptance_report.json`。本契約は `--out` で本契約の出力先へ書いた）

### B-3 受け入れの測り直し（`experiments/analysis/grasp_pilot_g/c3/run_c3.sh` → `acceptance_report.json`、sha256 97f3195e…2d34）

    $ bash experiments/analysis/grasp_pilot_g/c3/run_c3.sh     （4.0 秒、rc 0）
    主判定(C1/C2/C3/C4): ALL PASS ✓   verdict: ACCEPTED
    C3: 手 集合 57172（単純加算 57173）/ 目標 57172 / 手注釈のある区間 25 / 欠落 []

候補: 手 = `egosurgery_hts/hand_seg/{train,val,test,extra}.json`、把持関係 = `egosurgery_hts/hand_tool_seg/{train,val,test}.json`

| 基準 | 結果 | 実測 |
|---|---|---|
| C1 真マスク | ✓ | 把持関係 train 32,408 件すべて RLE（全件を見た。profiled 32,408 = 注釈 32,408）。raw 04 5cls RLE 21,949、master は polygon 7,507（4 頂点） |
| C2 値 5 | ✓ | `hand_tool_seg` train の cat 5 = Two Hands Tool、952 件。raw 04 の cat 5 は 399 件 |
| C3 被覆と件数 | ✓ | 手注釈のある区間 25（`03_3` を含まない。raw のディレクトリは 26）、欠けなし。集合 57,172・単純加算 57,173、raw 02_hand は単純加算 57,173・集合 57,172 |
| C4 リーク | ✓ | train・val・test のフレームと動画の共有 0（extra は検査器の対象の組に入らない） |
| C5 公式 split | ✗（主判定でない） | 9,627 / 1,515 / 4,255（公式 9,657 / 1,515 / 4,265。前回と同じく手注釈 0 件のフレーム 40 枚の差） |
| C6 | 報告 | 工程の区間 43、HTS の区間 25、共存 22 |

- 既存の `experiments/audit/l0_hts_acceptance/acceptance_report.json` の sha256 は前後で d9ac7ced…7126 のまま（上書きしていない）
- この検査は 25 区間（test の動画 04・05・07 を含む）の手の注釈の**件数と区間名だけ**を読む。G の学習・信号の作成・腕の学習・評価の経路ではない（§7-1 の対象外。test のフレームの画像は開いていない）

### B-2 対照（`experiments/analysis/grasp_pilot_g/c3/c3_controls.py` → `c3_controls.json`。判定の関数を import して呼び、`main()` を呼ばない。写しは `$S/b/controls/`）

| 入力 | 期待 | 実測 |
|---|---|---|
| そのまま | 合格 | pass、区間 25、集合 57,172 |
| raw 02_hand の写しの `03_3` に手を 1 件足す（03_3 を被覆の対象に戻す） | 不合格 | pass false（coverage false、区間 26、欠け `['03_3']`） |
| 候補の val の注釈を 1 件除いた写し（ann id 0） | 不合格 | pass false（count false、集合 57,171） |
| 候補の `extra.json` を隠した写し | 止まる | `FileNotFoundError: 入力が無い: <work>/hand_hidden_extra/extra.json` |
| 候補の `val.json` を隠した写し | 止まる | `FileNotFoundError`（**直す前の版は止まらず手 41,402 件を返した**＝欠陥 1 の再現） |
| 直す前の版の C3 を候補（train・val・test）に当てる | 構成上落ちる | pass false、欠け `['03_1','03_3','12_2','15_2']`（ディレクトリ 26 対 区間 22）＝欠陥 2 の再現 |

### G2 の判定

直した C3 が §3.1 の定義（25 区間の被覆、集合件数 57,172）で判定し、三つの対照で不合格か停止になり、欠陥 1・3 が直り、
受け入れを測り直した結果（主判定 ALL PASS）を本契約の出力先に記録した。**通過。**

## Task C — G の学習

### C-1 38 クラスの注釈（`scripts/grasppilot/g38_build.py` → `$S/g/ann/g38_{train,val}.json`、要約 `experiments/analysis/grasp_pilot_g/g/g38_summary.json`）

    $ PYTHONPATH=src .venv/bin/python scripts/grasppilot/g38_build.py --out $S/g/ann --check-frames 8     （3.4 秒）
    train 9657 9269 72113 {'01': 912, '02': 460, '03': 1051, '06': 1335, '08': 1268, '11': 745, '12': 484, '13': 806, '14': 1798, '15': 410} True
    val   1515 1511 11314 {'09': 518, '10': 993} True

- 38 クラス = 把持関係 5（hand_tool_seg 1〜5 → 1〜5）＋ 他者の手 2（hand_seg 3・4 → 6・7）＋ 術具 31（tool_seg 1〜31 → 8〜38）。名前は `grasp:`・`hand:`・`tool:` を前置き
- 学ぶフレーム = 三種の注釈がそろうフレーム（一本目の E-2 の組み合わせ 111 と同じ定義）: train 9,269・val 1,511（一本目の値と一致）。
  H1 = {01,06,11,12,15} は 3,886 枚、H2 = {02,03,08,13,14} は 5,383 枚
- sha256: g38_train.json 3485bb69bcc6e2f3…、g38_val.json d985397786d6d8d4…
- クラスごとのインスタンス数とフレーム数は要約にある。train で 0 件のクラスは 9 個（Chisel、Drill、Hammer、Malleable Retractor、Mouth Gag、Ruler、Screwdriver、
  Suture・Suture Needle、Trephine）、val で 0 件は 17 個。**COCO の評価の平均は val に正解のあるクラス（21 個）にわたる**
- 一度目の要約はクラスごとのフレーム数の数え方を誤り（集合の要素の組を数えた）、全クラス 0 と書いた。直して `$S/g/ann_rebuild` に組み直し、
  注釈の JSON の sha256 が train・val とも同じであることを確かめて、要約だけを差し替えた。G の 3 本が記録した `g38_build.py` の sha256 は直す前の版のもの

### C-2 戻しの照合

組んだ注釈から三種のマスクを戻し、元の注釈と画素で比べた（train・val 各 8 フレーム、seed 42 で選ぶ。hand_seg の 1・2 は把持関係の 1・2 から戻す）。
16 フレームすべてで三種とも一致（`g38_summary.json` の `check`）。人工の入力の試験 `tests/test_grasppilot_g.py`（4 件 pass）

### C-3 処方（`scripts/grasppilot/g_train.py`、起動 `scripts/grasppilot/run_g.sh`）

- mmdet 3.3.0 の Mask2Former R50（`mask2former_r50_8xb2-lsj-50e_coco.py`）。重みは一本目の保存先の `e/weights/mmdet/…-41b088b6.pth`（sha256 が 41b088b62838c986 で始まることを照合）。
  **610 個のうち 608 個を読んだ**。読まなかったのはクラス数で形が変わる `panoptic_head.cls_embed.{weight,bias}` の 2 個
- 入力: 短辺 800・長辺 1333 まで（PIL の双線形）、学習は左右反転 0.5、batch 2、LSJ の 1024 への詰め物（batch_augments）を外す（一本目の計測と同じ）。マスクは最近傍で縮める
- 最適化: 設定の optim_wrapper のまま（AdamW lr 1e-4・wd 0.05・eps 1e-8、backbone の lr ×0.1、query_embed・query_feat・level_embed と norm の減衰 0、勾配の L2 の切り 0.01）。
  学習率の予定は一定（設定の MultiStepLR の節目 327,778 歩は本契約の長さに届かない）で、収束規則だけが下げる
- 収束規則: epoch ごとに val の 38 クラスの mask mAP（pycocotools の segm、元の解像度 1080×1920、上位 100、`ev.stats[0]`）。
  **改善の判定は `scripts/stage1_ptower_r3.py` の `plateau_action` を import して使う**（改善 = 最良の値を厳密に上回る。4 epoch 停滞で学習率 × 0.1、再び 4 epoch で打ち切り、上限 36）。
  最良の epoch の重みを `$S/g/ckpt/<run>/best.pth` に置く。把持関係 5 クラスの mask mAP は同じ評価のクラス別 AP（IoU 0.5:0.95 の平均）の 5 個の平均
- 数値精度は fp32。**fp16 の自動混合精度を試走で試したら 40 歩目で損失が非数になった**（`$S/smoke/G_fp16.log`）。fp32 の試走は 60 歩・val 20 枚で通った（一歩 0.53 秒、最大確保 10.3 GB）
- 3 本で同じ処方。学ぶ動画だけが違う（all = train 10 動画、H1、H2）。val は 3 本とも折り A の val（1,511 枚）
- W&B: `egosurgery.utils.tracking` の init・log・finish を配線した（group grasppilot2_G）

### C-3 起動（2026-11-01 01:22 JST）

- GPU 0: `experiments/phase1/grasppilot2_G_all_seed42`（確定の G）
- GPU 1: `grasppilot2_G_H1_seed42`、終われば続けて `grasppilot2_G_H2_seed42`。GPU 1 には案 C の補助損失なしの腕（01:31 起動、最大確保 29.0 GB）を並べた
  （G 1 本 10.3 GB ＋ 工程塔 29.0 GB ≒ 39 GB < 48 GB。確定の G は信号と腕の全部の前にあるため GPU 0 に単独で置いた）
- 学習前の val（確定の G）: segm mAP 0.0004、把持関係 5 クラス 0.0015（頭は乱数）

# 監査記録: T-2026-10-19-stage2-pilot-four-new-types（非公式の測定）

実行者: bengio の Claude Code（セッション 3b1ce848-537b-4944-accf-99ec720d3316）。時刻は JST。測っていない値は UNKNOWN と書く。
作業場所は bengio の git worktree `/home/ubuntu/slocal2/m2-four`（分岐 `feat/stage2-pilot-four-new-types`）。
利用者の承認（2026-10-20 01 時台 JST）による逸脱は `spec.yaml` の `meta.amendments`（6 件）に置いた。

以下、`WT=/home/ubuntu/slocal2/m2-four`、`OV=/home/ubuntu/slocal2/s2fix-bengio-body`（重ねの BODY）、
`OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda`、`FIX=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle`、
`FOUR=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types`（本契約の版管理外の置き場）。
命令の生の出力は `experiments/analysis/stage2_pilot_four/` の下に置き、ここから経路で指す。

## 0. 取り込み（01:08〜01:10 JST）

- 開始時: `hostname` = `Bengio`、2026-10-20 01:07:42 JST。`git status -sb` は清浄、分岐 `feat/stage2-pilot-four-new-types`、HEAD `a7a5aa67`
- 1 回目: `source scripts/load_env.sh && $OV/.venv/bin/python tools/fetch_task.py --notion T-2026-10-19-stage2-pilot-four-new-types`
  → 取得は通ったが検証で `make: .venv/bin/python: No such file or directory`（`make task-validate` が worktree 直下の `.venv/bin/python` を固定で呼ぶ）。
  道具が設置を巻き戻した（「痕跡は残していません」）
- 対処: worktree に追跡外の記号リンク `.venv -> /home/ubuntu/slocal2/m2/.venv` を置いた（`.gitignore` の `.venv*/` は記号リンクに当たらないので `git status` に `?? .venv` が出る。commit しない。`rm .venv` で戻せる）
- 2 回目: 同じ命令（python は `.venv/bin/python`）→ `OK T-2026-10-19-stage2-pilot-four-new-types`、`WARN [L2-6] conventions.md が 5c0eaeeb… 以降に変更されています`（A-6 で扱う）。
  `tasks/T-2026-10-19-stage2-pilot-four-new-types/{SPEC.md,spec.yaml}` を設置
- 上流: 分岐の上流が `origin/feat/stage2-pilot-fix-epoch4-shuffle` になっていたため、誤 push を防ぐため `git branch --unset-upstream`（遠隔に同名の分岐は無かった）

## A. 開始状態（G1）

### A-1 分岐・起点・直しの道具（`experiments/analysis/stage2_pilot_four/start/a1_branch_tools.txt`）

| 項目 | 値 |
|---|---|
| 分岐 | `feat/stage2-pilot-four-new-types`（`feat/` で始まる） |
| HEAD | `a7a5aa67db5e1ac9c7b978eeb05fa33019948012` = `origin/feat/stage2-pilot-fix-epoch4-shuffle` の先頭（逸脱 2 の起点） |
| origin/phase0 | `23183b42`。HEAD の祖先ではない（共通の祖先は `5a8baa79`） |
| PR #240 | `gh pr view 240` → state OPEN、isDraft false、mergedAt null、base phase0、head `feat/stage2-pilot-fix-epoch4-shuffle` |
| 直しの道具（HEAD） | `shuffle_signals.py`・`aggregate_fix.py`・`run_pd_fix.sh`・`run_dp_fix.sh` は在る。`--fixed-epochs` は `train_t1b.py` に 3 行、`dp_train.py` に 7 行 |
| 空振りでないこと | 存在しない名前 `scripts/stage2pilot/no_such_tool_four.py` は ABSENT、`--no-such-flag-four` は 0 行 |
| 同じ道具（origin/phase0） | 4 本とも ABSENT（PR #240 が未統合のため。逸脱 2 の想定どおり） |

### A-2 未追跡の退避

開始時の `git status --porcelain` は 0 行で、開始前から在る未追跡は無い。退避したものは無い。
本契約が作った追跡外: `.venv`（記号リンク、上記）、`data/processed/phase_manifest`（記号リンク、下記「入力の写し」）。

### A-3 bengio の compute プロセス（`start/a3_a4_host_procs.txt`）

- 01:19:13 JST。`nvidia-smi`: GPU 0 39 MiB・0%、GPU 1 20 MiB・0%（RTX A6000 × 2）。`--query-compute-apps` は 0 行
- `proc_enum.py --summary`（`/proc/PID/exe` の解決）: python 系（exe の basename が python で始まる）は **0 件**。在るのは zsh・bash・node・claude・codex・syncthing・ssh など（compute ではない）
- **本契約以外の compute プロセスは 0 件**
- 空振りでないこと: `bash -c 'sleep 15; :' zzz_four_marker` を起こすと `--exe /usr/bin/bash --argv zzz_four_marker` は **count=1**、`--exe /nonexistent/bin/bash` は **count=0**。
  1 回目は `bash -c 'sleep 15'` で count=0（bash が単一の命令を exec で置き換え、印が消えた）。exec されない形でやり直した

### A-4 記憶領域

`df -B1 /home/ubuntu/slocal2`: 総 7,937,302,376,448、使用 6,657,328,488,448、**空き 879,879,020,544**（89%）。`free -b`: available 112,991,805,440。
見積もり: 入力の写し 1,455,773,778 B（下記）、D\* の train の出力（上位 300、約 9,657 枚）は前回の val の 1,515 枚で 172,962,966 B なので train は約 1.1 GB、
run 30 本の予測と界面の重みは前回の run の大きさ（予測 2 本で約 25 MB、界面の重みは数 MB）から 1 GB 未満。合計 5 GB 未満で、空きに対して足りる。

### A-5 試験（開始時、`start/a5_pytest_start.txt`）

    $ CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors
    8 failed, 862 passed, 15 skipped, 22 warnings, 1 error in 32.51s

失敗の名前（bengio の開始時の集合。終了時に同じホストで比べる）:

    FAILED tests/test_check_spec.py::test_teacher_detection_rate
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
    FAILED tests/test_stage1_ptower_r3.py::test_only_the_stem_is_frozen_in_both_chains
    ERROR  tests/test_stage1_dtower_convergence.py（収集の誤り）

andrew の直しの契約の開始時（6 件）より 3 件多い。増えた 3 件の理由: `test_stage1_dtower_convergence.py` は worktree に版管理外の
`third_party/Relation-DETR/util/convergence.py` が無い（FileNotFoundError）、`test_only_the_stem_is_frozen_in_both_chains` は worktree に
`data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth` が無い、`test_teacher_detection_rate` は期待値をホスト名から計算する試験で
（`host_mismatch`）bengio では検出 14 件・期待 15 件。どれも本契約の変更の前から在り、取り込んだ契約は入力に入らない。

### A-6 起票時の値（`start/a6_conventions_anchor_diff.txt`）

| 項目 | 起票時 | 実測 | 扱い |
|---|---|---|---|
| `conventions_rev` | 5c0eaeeb | 起点の `git log -1 -- context/conventions.md` は **b12eda6c**。5c0eaeeb は origin/phase0 に在り、起点の祖先ではない | **差し替えない**（amendments 6 件目） |
| `runindex_commit` | 31af81e7 | `git log -1 -- runindex/` は **63ae65da**。31af81e7 はその子孫で間に runindex/ を変えた commit 0 件、31af81e7..HEAD の差分も空 | 差し替えた（同 6 件目） |
| index / experiments / verdicts（行数 − 1） | 1961 / 750 / 1506 | 1961 / 750 / 1506 | 不要 |

注入する 7 節を 5c0eaeeb と b12eda6c で節ごとに比べた（`<a id>` で区切った本文の sha256）: prohibitions・issuer_cautions・env_p0・split・eval_recipe・det_groups は**同一**、
folds は**追加 6 動画の記述だけ**が違う（5c0eaeeb は「22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で P\*-20 と呼ぶ」を足す）。折り A の 15 動画は同じ。
precision 節は 5c0eaeeb にだけ在る（symmetry 節・naming・proposal_gate・crossfit も違う）。起票者は 5c0eaeeb に対して書いたので、注入する節は
`git show 5c0eaeeb:context/conventions.md` の原文で解く。差し替えた後の `make task-validate` は OK（rc=0、WARN L2-6 は残る）。
`make task-preflight`（`start/preflight.txt`）: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL（SKIP は P2・P3・P4・P5・P11・P12・P13・P14。kind=analysis か plan.env.preflight に記載なし）。

### A-7 抑止の目印（`start/a7_sync_scope.txt`）

**`make task-start` を使っていない**（逸脱 1）。目印 `.sync-pause` は worktree にも `/home/ubuntu/slocal2/m2` にも無く、置いていない。
`~/bin/m2-sync.sh` は `M2DIR=~/slocal2/m2` に `cd "$M2DIR"`（29 行）して動き、`worktree` の語は 0 件なので、この worktree には触れない。
bengio の main の作業場所は分岐 `feat/proposal-gate-brief`、`status --porcelain` 14 行（触れていない）。

### G1: **pass**（逸脱 2・3 の読み替えで）

分岐は `feat/`、起点は直しの分岐の先頭（a7a5aa67）でそこに直しの道具が在る、bengio に本契約以外の compute プロセス 0 件、空き 879,879,020,544 B、失敗の名前 9 件を記録した。

## 入力の写し（利用者の指示 4、01:20〜01:25 JST、`experiments/analysis/stage2_pilot_four/inputs/`）

- andrew へは `ssh -o BatchMode=yes andrew` で届いた（hostname `Andrew`）。andrew では読むだけ（`du -sb`、`stat`、`sha256sum`、`find`）
- 写す前の一覧: `andrew_manifest.txt`（44 ファイル、計 **1,455,773,778 B**。`$OLD/signals/final` 21 本 629,737,148 B、`$OLD/signals/cf` 5 本 384,698,782 B、
  `$OLD/arms` 2 本 1,207,588 B、`$FIX/signals/shuffle` 10 本 309,803,780 B、工程塔の特徴 `all_gap.npz` 127,016,156 B と時間ヘッド `best.pth` 1,610,970 B、
  andrew の `data/processed/phase_manifest` 4 本 1,699,354 B）。空き 879,879,020,544 B に対して 0.17%
- bengio に既に在ったもの: 直しの契約が置いた 8 本（P 側）。`/home/ubuntu/slocal2/m2/data/processed/phase_manifest` は bengio の main に在る（**写さない**）
- 写し: `rsync -a --ignore-existing andrew:<経路>/ <同じ経路>/`（既存の 8 本は上書きしない）。01:23:53〜01:24:08 JST、6 回とも rc=0、**32 本**を写した（`rsync.log`）
- 写した後: bengio の 44 ファイル（写した 32、既存 8、bengio の main のマニフェスト 4）の大きさと sha256 が andrew の値と **44/44 一致**（`bengio_manifest.txt`、`manifest_diff.txt` は 0 行）。
  陽性対照: `D0_val.npz` の複製の 1000 バイト目を変えると sha256 が `2b10b078…` になり andrew の `4403d1fe…` と一致しない
- 前回と直しの契約の版管理外の保存先（bengio の写し）に、andrew と同じ中身のファイルを足した（既存のファイルは変えていない）。SPEC §7-2 の字面に当たるが、利用者の指示 4 による（amendments 4 件目）
- マニフェスト: `common.MANIFEST_DIR` は worktree の `data/processed/phase_manifest` を読むため、worktree に記号リンク
  `data/processed/phase_manifest -> /home/ubuntu/slocal2/m2/data/processed/phase_manifest` を置いた（`data/processed/**` は追跡外。main は変えていない。`rm` で戻せる）

## 環境の確認（利用者の指示 5、01:25〜01:26 JST、`experiments/analysis/stage2_pilot_four/env/`）

- `$OV/.venv-relation-detr/bin/python scripts/stage2pilot/input_digest.py --body $OV --out env/input_digest_bengio.json`（rc=0）を、直しの契約の
  `bengio/input_digest_andrew.json` と比べた: `relation_detr.commit`・`relation_detr.uncommitted`・`torch.gpus` を除く **167 個の値がすべて一致**
  （`source_files` 142、`source_tree_sha256` `2f08e5213cb5c377…`、torch 2.1.2+cu118・CUDA 11.8・cuDNN 8700）
- 今の andrew と比べ直した（記録が直しの契約の時点のものなので）: Relation-DETR のソース（.py .cu .cuh .cpp .h、`input_digest.py` と同じ除外）のファイルごとの sha256 の一覧を
  andrew の `/home/ubuntu/slocal2/m2/third_party/Relation-DETR` と `$OV/third_party/Relation-DETR` で取り、**142 本とも一致**（`reldetr_src_*`）
- パッケージ: `importlib.metadata` で「名前（小文字）==版」を並べた一覧を両ホストで取り、`.venv-relation-detr` は **72 個が一致**
  （sha256 `2c7b070c93ca5a39…`、直しの契約の `venv_relation_detr_freeze_andrew.txt` とも同じ）、本体の `.venv` は **108 個が一致**。
  本体の python の実体は両ホストとも uv の `cpython-3.11.16`
- 食い違いが無いので作り直していない。bengio の main の `third_party` と作業場所は変えていない

## B. 材料の確認と再現（G2）

### B-1 材料（`experiments/analysis/stage2_pilot_four/material/material_four.json`、道具 `tools/material_four.py`）

本契約が読む 18 ファイル（PD の信号 9、DP の信号 7、工程塔の特徴と時間ヘッド）の sha256 を、直しの契約の版管理下の記録
（`material/material_check.json`、`shuffle/shuffle_record.json`、`bengio/input_digest_andrew.json`、`repro/ptower_val.json`）と照合した:
**all_exist true、all_have_record true、all_match true**（記録 1〜3 個ずつ）。陽性対照: `D0_val.npz` の 1 バイトを変えた複製は記録と一致しない（`matches_record` false）。

### B-2 塔単独の再現（bengio、01:26:49〜01:32:46 JST、`experiments/analysis/stage2_pilot_four/repro/`、台本 `repro/run_repro_bengio.sh`）

| 塔 | 指標 | bengio | 前回の記録 | 差 |
|---|---|---|---|---|
| 工程（`repro_ptower.py`、本体の .venv、1,515 フレーム、動画 09・10） | macro Jaccard | 0.7762185528074379 | 0.7762185528074379 | 0.0 |
| | frame accuracy | 0.8712871287128713 | 0.8712871287128713 | 0.0 |
| 検出（`pd_eval.py --cfg plain`、重ねの BODY、1,515 枚） | overall mAP | 0.7273450248398429 | 0.7273450248398429 | 0.0 |
| | 標的群 AP | 0.7950748008550897 | 0.7950748008550899 | −1.1e−16 |
| | 陰性対照群 AP | 0.6726631817581498 | 0.6726631817581498 | 0.0 |

許容差 0.005 の中。動画ごと: 工程 09 Jaccard 0.99317・10 0.67537、検出 09 mAP 0.70427・10 0.64210。
`env_check_det.txt` `ms_deform_attn_ext True`。検出の基準の予測を `$FOUR/identity/plain_val_preds.json.gz` に保存（恒等性の基準）。
対照（値が変わること）: 工程は別の時間ヘッド（P20 seed42 の 036）で Jaccard 0.6379452（差 −0.1383）、検出は seed 123 の checkpoint で mAP 0.7288631（差 +0.0015）。
台本は `PYTHONUTF8=1` を置いた（直しの契約の bengio の R5 の 1 回目が `read_text()` の ascii の UnicodeDecodeError で落ちた件を避けるため。数値には効かない）。

### B-3

**UNKNOWN**（逸脱 5。直しの契約が終わってから Task F で行う）。

### G2: **pass**（B-1・B-2。B-3 は Task F へ移した）

## C. 実装と恒等性（G3）

### C-1 実装（版管理下、`third_party/` は変えていない）

| ファイル | 中身 | 既存の経路への影響 |
|---|---|---|
| `scripts/stage2pilot/dp_model.py`（変更） | 型 `logit_corr`・`tool_hist`・`tool_hist_nogate`（`LogitCorrection`、`ToolHistory`）。時間ヘッドの最後の段（続きの段の最後）だけを変える | 既存の 3 型の分岐は同じ（新しい型の名前のときだけ通る経路を足した） |
| `scripts/stage2pilot/dp_train.py`（変更） | 型 `LC`・`TH`・`TH-NG`、32 次元の x(t)（`x32`）、`trainable_report`、epoch ごとのゲートの記録 | 既存の型の `Signals` と学習の流れは同じ。ゲートは持つ型だけ記録に足す |
| `scripts/stage2pilot/pd_four.py`（新規） | `RelationDETRStage2Four`（`dec_xattn`、`extra_q`）、見落としの印つきの train の読み込み | 既存の `pd_model.py` は変えていない |
| `configs/stage2pilot/pd_{dec_xattn,extra_q}_d{9,18}.py`（新規） | `make_pd_four_configs.py` で `pd_query_d9.py` から生成。差は検出器のクラスと界面の指定だけ | — |
| `scripts/train_t1b.py`（変更） | `--missed-set`（extra_q の train の読み込み）、`gate_record`（`gate_values` を持つ検出器だけ epoch ごとのゲートを記録） | 渡さなければ従来の経路。`gate_values` の無い検出器では記録の中身も同じ |
| `scripts/stage2pilot/{run_pd_four.sh,run_dp_four.sh,pd_four_eval.py,pd_four_finalize.py,xq_missed.py,kill_four.py,test_audit_four.py,aggregate_four.py,run_pd_four_identity.sh,make_pd_four_configs.py}`（新規） | 起動・評価・後処理・見落とし・殺し実験・test の監査・集計 | — |

型の定義の読み（SPEC §3 の範囲で実行者が決めたもの）:

- logit-correction: `b` は `W_in` の bias に一つだけ置き、`W_p` は bias なし。`W_out` と bias を零初期化。損失は前回と同じ形で全段の出力に当てる（変わるのは最後の段だけ）
- tool-history: GRU の入力 `W_in x + b_in` は 64 次元。`W_o` は 64 → 64（z の次元）。ゲートなし版は `W_o` と bias を零初期化、カードどおりの版は α を 0 から（`W_o` は既定の初期化）
- decoder-xattn: 工程の token は key と value に**そのまま**使う（射影を挟まない。token の生成が学習する線形写像なので）。各層の部分層は LayerNorm・射影・出力射影・α_l を層ごとに持ち、
  token の生成と入力適合層は全層で共有。forward hook で decoder を通るすべての query（学習時の denoising と hybrid の経路を含む）に当てる
- extra-queries: 元の query の出力を構成で塔単独と同じに保つため、元の経路は D\* のまま回し、追加の query だけを各層で元の query のその層の入力を key と value に加えて別に回す
  （mask を張った一つの計算にすると行列積の形が変わって丸めが変わり得るため）。位置関係の埋め込みは追加の query の行について元と追加の両方の box との間で D\* と同じ式で作る。
  学習では元の経路を勾配なし・評価と同じ形（denoising と hybrid なし）で回し、追加の query だけを見落としの box に `HybridSetCriterion`（各層の補助の損失つき）で当てる。
  e_i と u_i は正規分布（nn.Embedding の既定と同じ）、スコアの定数は一つのスカラー（−10 から。全層の追加の出力に足す）
- 界面の初期化は `torch.random.fork_rng` と固定の種で大域の乱数から切り離し、入力適合層を最後に作る（正解予測-CF の 18 次元の腕でも、界面の他の部分の初期値とその後の学習の乱数が同じになる）

### C-2・C-3・C-5 DP（検出から工程）の恒等性（01:42〜01:44 JST、`experiments/analysis/stage2_pilot_four/identity/dp_*.json`、台本 `identity/run_dp_identity.sh`）

三つの型 × 6 腕 = 18 本。すべて rc=0。

- 学習前の val の macro Jaccard は 18 本とも 0.7762185528074379（塔単独と同値、`jaccard_equals_taskB` true）、ロジットの差の最大 **0.0**
- 陽性対照（零から始めた部分を零でない値にする。LC は `W_out`、TH は α、TH-NG は `W_o`、尺度 0.05）でロジットが変わる: 差の最大 LC 0.164〜0.229、TH 0.000244〜0.000478、TH-NG 0.0624〜0.127
- 学習する名前の集合（requires_grad）が界面のパラメータの名前の集合と **18 本とも一致**し、受け取り手のパラメータを一つ混ぜた集合では一致しない（`equal_with_one_head_param_mixed` false）。
  界面のパラメータ数: LC 1,641、TH 31,233、TH-NG 31,232
- x(t) の旗と出所（`x_layout`）: 空 (0, 0)・すべて 0、予測-noCF と予測-CF (1, 0)・`signals/final/D0_val.npz`、正解 (0, 1)・`signals/final/D-GT_val.npz`、
  正解予測-CF (1, 1)・D-GT と D0、入れ替え (1, 0)・直しの契約の `signals/shuffle/D0_val.npz`。train は予測-CF と正解予測-CF の予測の半分が `signals/cf/D0_train.npz`（学習の run の config に残る）
- TH の学習前の tanh(α) は 0.0

### C-7 DP の試走（01:45:21〜01:45:49 JST、`run_dp_four.sh smoke LC TH TH-NG`、腕は予測-noCF、1 epoch）

| run | val Jaccard | 学習の秒 | ゲート | 受け取り手の不変 |
|---|---|---|---|---|
| `stage2four_dp_001_LC_pred_noCF_ep1_smoke_seed42` | 0.770786 | 0.5 | — | true |
| `stage2four_dp_002_TH_pred_noCF_ep1_smoke_seed42` | 0.776219 | 0.6 | tanh(α) 0.000948 | true |
| `stage2four_dp_003_TH-NG_pred_noCF_ep1_smoke_seed42` | 0.768957 | 0.5 | — | true |

1 epoch（10 歩）の学習が 1 秒未満なので、4 epoch の 1 本は特徴の読み込みを含めて数十秒の見込み（測っていない）。W&B の記録（`wandb_run.json`）は作られた。

### C-5 PD（工程から検出）の decoder-xattn の恒等性と陽性対照（01:52〜02:13 JST、`identity/pd_DX_*.json`、台本 `identity/run_pd_identity.sh`）

道具 `scripts/stage2pilot/pd_four_eval.py`（`pd_eval.py` と同じ評価の経路）。基準は B-2 の塔単独の予測 `$FOUR/identity/plain_val_preds.json.gz`。val 全 1,515 枚、重ねの BODY、bengio。

| 腕 | 信号（val） | overall mAP | score 差の最大 | 枠の差の最大（px） | ラベル不一致 | 学習する集合 = 界面 | 学習対象 |
|---|---|---|---|---|---|---|---|
| 空 | `P0_val`（零にする、`--zero-ctx`） | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | 210,374 |
| 予測-noCF | `signals/final/P0_val` | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | 210,374 |
| 正解 | `signals/final/P-GT_val` | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | 210,374 |
| 予測-CF | `signals/final/P0_val` | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | 210,374 |
| 正解予測-CF | `arms/PD/gtpred_noCF_val`（18） | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | 210,662 |
| 入れ替え | 直しの契約の `signals/shuffle/P0_val` | 0.7273450248398429 | 0.0 | 0.0 | 0 | true | 210,374 |
| 陽性対照（`--perturb gate`、α を尺度 0.05 の乱数に） | `P0_val` | 0.7272701920052 | 0.0070025 | 1955.03 | 161,010 | true | 210,374 |

- 6 腕とも標的群 AP 0.7950748008550897、陰性対照群 AP 0.6726631817581498（塔単独と同値）、学習前のゲート tanh(α_l) はすべて 0、
  凍結部（界面以外の state）の要約値 `4fed85166852…`（B-2 の塔単独と同じ）。陽性対照の α の tanh は [+0.0023, +0.0201, −0.0505, +0.0108, −0.0306, +0.0252]
- 学習する集合: `--trainable film`（名前に phase を含む）で requires_grad になる名前の集合が `phase_iface.*` の全部と一致し、検出器のパラメータを一つ混ぜると一致しない
  （`equal_with_one_detector_param_mixed` false）。数は token 8,448 ＋ 層ごと（LN 512・q 16,448・out 16,640）× 6 ＋ α 6 ＋ 入力適合層 320（d18 は 608）

### C-1 既存の型と既定の経路が変わらないこと（02:03〜02:13 JST）

本契約で変えた `train_t1b.py`・`dp_train.py`・`dp_model.py` で、直しの契約と同じ命令を回し、直しの契約の記録と比べた（出力は `identity/existing_*`）:

| 照合 | 相手（直しの契約の記録） | 結果 |
|---|---|---|
| PD P3（`pd_query_d9`）入れ替えの陽性対照（`pd_eval.py --perturb`） | `stage2_pilot_fix/bengio/pd_query_d9_shuffle_positive_bengio.json` | 全項目一致（mAP 0.7271372958311481、score 差 0.34662654995918274、枠 1932.9268646240234、ラベル不一致 267,542、凍結部の要約値、群 AP・動画ごと） |
| PD P1（`pd_film_d9`）入れ替えの陽性対照 | `stage2_pilot_fix/identity/pd_film_d9_shuffle_positive.json`（andrew） | `det_ckpt` の経路の文字列（andrew の main と bengio の重ねの BODY）以外の全項目一致（mAP 0.7287992265410653、score 差 0.45731912553310394） |
| DP D1-L1・D1-L2・D2・D3-L1・D3-L2 の入れ替えの腕の恒等性と陽性対照（`dp_train.py identity --arm shuffle`） | `stage2_pilot_fix/identity/dp_<型>_shuffle.json`（andrew） | 5 型とも全鍵一致（信号の sha256、恒等性 0.0、陽性対照の Jaccard とロジットの差） |

phase0 を merge した後に、既定の経路を固定する試験（`tests/test_train_t1b_stage2pilot_defaults.py`、`tests/test_stage2pilot_dp_train_defaults.py`）も回す（下記）。

### 誤った書き込み（02:03 JST に気づいた、記録）

`pd_eval.py`・`pd_four_eval.py` は import 時に作業場所を `$EGO_BODY/third_party/Relation-DETR` へ移す。私が**相対経路の `--out`** で回した 3 本
（`existing_pd_query_d9_shuffle_positive`、`existing_pd_film_d9_shuffle_positive`、`pd_DX_positive_gate`）の json が、
重ねの BODY の `third_party/Relation-DETR/experiments/analysis/stage2_pilot_four/identity/` に書かれた（重ねの BODY に元は `experiments` が無く、私が作ったフォルダ）。
3 本を worktree の `experiments/analysis/stage2_pilot_four/identity/` へ `mv -n` で移し、空になった作ったフォルダ 4 段を `rmdir` で除いた（02:1x JST）。
移した後、重ねの BODY の Relation-DETR のソース 142 本の一覧が `env/reldetr_src_bengio_overlay.txt` と全行一致（`cmp` 一致）。bengio の main の `third_party` には触れていない。
以後は `--out` を絶対経路で渡す（`run_pd_identity.sh`・`run_pd_four_identity.sh`・`run_repro_bengio.sh` は初めから絶対経路）。

### C-4 extra-queries の見落としの集合（01:50〜02:08 JST、道具 `scripts/stage2pilot/xq_missed.py`、`experiments/analysis/stage2_pilot_four/xq/`）

- D\* の train の出力: `predict --split train --shard {0,1}/2`（GPU 0・1、重ねの BODY、検出塔 `30d199b1…`、上位 300・確信度の下限なし・NMS なし。増強なし）
  - shard 0: 4,829 枚、1,448,700 件、sha256 `141f43a972b2654c…`（mAP 0.8406 は記述だけ）、shard 1: 4,828 枚、1,448,400 件、sha256 `5ac974d8072590c3…`（0.8383）。
    動画は 01・02・03・06・08・11〜15。版管理外 `$FOUR/xq/dstar_train_top300_shard{0,1}.json.gz`（要約値は `xq/*.meta.json`）
- 見落とし（SPEC §3.2 の字面どおり。学習に残る正解の box〔iscrowd 0、幅と高さが正〕で、同じクラスで IoU 0.5 以上の検出が上位 300 に一つも無いもの）:

| | 正解の box | 見落とし | 割合 | 見落としの在る画像 |
|---|---|---|---|---|
| train（9,657 枚） | 32,272 | **73** | 0.00226 | 73 |
| val（1,515 枚、K1 用。B-2 の塔単独の予測から） | 4,707 | **78** | 0.01657 | 74 |

  train のクラスごと: Forceps 18、Tweezers 18、Gauze 13、Retractor 8、Suction Cannula 5、Hook 2、Raspatory 2、Scissors 2、Syringe 2、Electric Cautery 1、Mouth Gag 1、Needle Holders 1（他 0）。
  val のクラスごと: Gauze 27、Tweezers 13、Forceps 10、Hook 10、Mouth Gag 9、Scissors 7、Suction Cannula 2
- 確信度の閾値ごとの見落とし（記述。「覆う」に数える検出をスコアが閾値以上のものに限る）: 閾値は、覆われた正解の覆う検出のスコアの最大の分布
  （最小 0.0069、0.1% 点 0.0217、1% 点 0.330、5% 点 0.719、10% 点 0.807、中央値 0.923）を見て {0（定義）, 0.01, 0.05, 0.1, 0.3, 0.5} に決めた。
  train 73 / 78 / 131 / 176 / 368 / 632、val 78 / 81 / 215 / 302 / 469 / 638
- 空振りでないこと（完了判定 f、両方向）: ある正解をただ一つ覆う検出を消した写しで、その正解が見落としに数えられる（train: 画像 41・注釈 42、覆うスコア 0.665 → −1、
  val: 画像 111・注釈 111、0.487 → −1）。正解をそのまま検出（スコア 1）として足した写しで見落としは 0 件（train・val とも）
- 集合 `$FOUR/xq/missed_train.json`（注釈の id 73 個。写しを `xq/missed_train.json` に置いた）を、extra-queries の全腕で使う

### C-7 PD の試走（`run_pd_four.sh <型> gt smoke`、1 epoch・6 歩・val 20 枚、GPU 0、重ねの BODY）

| run | 時刻（JST） | 学習対象 | 学習前 mAP（20 枚） | 後処理の AP | 界面への勾配 | 凍結部の前後 | epoch 0 のゲート |
|---|---|---|---|---|---|---|---|
| `stage2four_pd_DX_gt_ep4_seed42_smoke` | 01:51:47〜01:52:10 | 210,374 | 0.8916611661166115 | 0.891661 | true | 一致（`4fed8516…`） | tanh(α_l) +0.00117, −0.00076, −0.00122, +0.00094, −0.00063, +0.00082 |
| `stage2four_pd_EQ_gt_ep4_seed42_smoke` | 02:08:17〜02:08:37 | 16,701 | 0.8916611661166115 | 0.891661 | true | 一致 | スコアの定数（記録は `stage2four_metrics.json`） |

学習前 mAP は直しの契約の P3 の試走（andrew・bengio とも 0.8916612）と同じ。`env_check.txt` は両方 `ms_deform_attn_ext True`。
試走は 6 歩なので 1 本の所要は本番の run の壁時計で測る（`start.txt`・`end.txt`）。

## phase0 の取り込みと Task A-6 の測り直し・Task B-3（利用者の決定 01:44 JST の 2、02:1x JST）

- 02:1x JST に G3 の記録と引き渡しを commit（`659378f6`）し、`git merge --no-ff origin/phase0`（`42070946`）→ `0d717f09`。衝突なし（事前の `git merge-tree --write-tree` も rc=0）。
  起点 a7a5aa67 以降に phase0 で変わった scripts・configs は `scripts/stage2pilot/test_audit_fix.py` だけで、本契約の変更と重ならない。push 済み（`ed53c672..0d717f09`）
- merge の後の既定の経路の試験: `pytest tests/test_train_t1b_stage2pilot_defaults.py tests/test_stage2pilot_dp_train_defaults.py` → **10 passed**
- A-6 の測り直し: `git log -1 -- context/conventions.md` = **5c0eaeeb**（契約の `conventions_rev` と一致。検証の WARN L2-6 は出なくなった）、
  `git log -1 -- runindex/` = 63ae65da（差し替え済みの値と一致）、件数 1961 / 750 / 1506 は一致。`make task-validate` OK
- B-3（amendments 7 件目。相手は直しの分岐の 5c89f5d2 の集計）: 本分岐の `experiments/phase1`・`experiments/analysis/stage2_pilot_fix`・`stage2_pilot_folda` と集計の道具
  （`aggregate_fix.py`・`aggregate.py`・`common.py`・`det_metrics.py`）は 5c89f5d2 と同じ（`git diff --name-status 5c89f5d2 HEAD` は本契約の `stage2four_*` の追加だけ）
  - 1 回目（worktree のまま）: rc=1。前回の DP の run の `logs/history.json` が版管理外（共通の `.git/info/exclude` 23 行 `experiments/phase1/stage2pilot_*/`）で worktree に無い
  - 2 回目: 作業用の場所（scratchpad の `b3tree`）に `git archive HEAD` を書き出し、bengio の main の前回・直しの run 143 本から版管理外のファイルだけを
    `rsync -a --ignore-existing`（`predictions/`・`checkpoints/`・`visualizations/` を除く）で足した（bengio の main は読むだけ）。その木で
    `aggregate_fix.py --out-json <本契約>/b3/report.json --out-md <本契約>/b3/REPORT.md --head … --tail …`（既定のまま）→ rc=0、
    「前回 PD 22・DP 63、本契約 PD 13・DP 26、計算し直し 124 件で食い違い 0 件」（直しの契約の F-1 と同じ行）
  - 5c89f5d2 の `experiments/analysis/stage2_pilot_fix/report.json` と比べて **値 5,818 個の差 0**、ファイルの sha256 も同じ（`1440d944e832e718…`）。`REPORT.md` も同一
  - 空振りでないこと: 直しの report.json の一つの値（P3 の空の腕の overall mAP）を 1e−12 だけ変えた写しでは、同じ比べ方の差が 1 件になる
- **G2: pass**（B-1・B-2・B-3）

### C-8 test 不使用（02:1x JST の時点、`experiments/analysis/stage2_pilot_four/test_audit/test_audit_c8.json`、道具 `scripts/stage2pilot/test_audit_four.py`）

各段の実体（DP の試走の run の config の動画と読んだ信号、PD の試走の run が読んだ信号と注釈、見落としの集合と D\* の train の出力の記録、恒等性・再現・見落としの評価の記録）から
通した動画の集合を作った: 全体は 01・02・03・06・08・09・10・11・12・13・14・15 の 12 本で、**{04, 05, 07} との共通 0 件**。
空振りでないこと: `--inject 04` で全体の共通が 1 件（`['04']`）。本番の run の後に Task F で回し直す。

### C-5・C-6 PD の extra-queries の恒等性・陽性対照・追加の検査（02:0x〜02:32 JST、`identity/pd_EQ_*.json`）

最終の検出（元と追加の和集合の上位 300）と、元の出力だけの検出の両方を、一回の順伝播から取った。基準は B-2 の塔単独の予測。val 全 1,515 枚、bengio。

| 腕 | 信号（val） | 最終の mAP | 最終の差（score / 枠 / ラベル） | 元の出力の差 | 追加の最大スコア | 元の 300 番目の最小 | 上位 300 に入った追加 | 学習対象 |
|---|---|---|---|---|---|---|---|---|
| 空 | `P0_val`（零） | 0.7273450248398429 | 0.0 / 0.0 / 0 | 0.0 / 0.0 / 0 | 1.06e−3 | 0.00480 | 0 | 16,701 |
| 予測-noCF | `P0_val` | 0.7273450248398429 | 0.0 / 0.0 / 0 | 0.0 / 0.0 / 0 | 1.10e−3 | 0.00480 | 0 | 16,701 |
| 正解 | `P-GT_val` | 0.7273450248398429 | 0.0 / 0.0 / 0 | 0.0 / 0.0 / 0 | 1.12e−3 | 0.00480 | 0 | 16,701 |
| 予測-CF | `P0_val` | 0.7273450248398429 | 0.0 / 0.0 / 0 | 0.0 / 0.0 / 0 | 1.10e−3 | 0.00480 | 0 | 16,701 |
| 正解予測-CF | `gtpred_noCF_val`（18） | 0.7273450248398429 | 0.0 / 0.0 / 0 | 0.0 / 0.0 / 0 | 6.33e−4 | 0.00480 | 0 | 16,989 |
| 入れ替え | 直しの契約の `shuffle/P0_val` | 0.7273450248398429 | 0.0 / 0.0 / 0 | 0.0 / 0.0 / 0 | 1.15e−3 | 0.00480 | 0 | 16,701 |

- C-6: 6 腕とも、追加の出力の最大スコアが塔単独の 300 番目を下回らない画像は **0 枚**（画像ごとの差の最小 0.00478〜0.00480）。スコアの定数の初期値 −10 は変えていない
- 学習する集合: 6 腕とも `phase_iface.*` の全部と一致し、検出器のパラメータを一つ混ぜると一致しない。学習前のスコアの定数 −10.0

| 陽性対照・検査（信号は `P0_val`） | 最終の mAP | 最終の差（score / 枠 / ラベル） | 元の出力の差 | 上位 300 に入った追加 |
|---|---|---|---|---|
| スコアの定数を 0（`--perturb score0`） | 0.7175541209142418 | 0.8425 / 2250.3 / 257,196 | **0.0 / 0.0 / 0** | 27,594 件（1,422 枚） |
| 界面の重みをすべて乱数（`--perturb random`、スコアの定数も乱数で 0.372） | 0.727053065155761 | 0.1997 / 2081.7 / 185,802 | **0.0 / 0.0 / 0** | 29,536 件（1,354 枚） |
| 自己注意の mask を外す（`--perturb unmask`、元と追加を一つの計算にし元も追加を参照） | 0.7252771741231229 | 0.5636 / 1958.5 / 322,869 | **0.5636 / 1958.5 / 322,869（変わる）** | 0 |

界面の重みを乱数で変えても元の query の出力は塔単独と差 0 で、mask を外すと変わる（完了判定 e の空振りでないことの確認）。

### G3: **pass**（02:32 JST）

五つの界面の全腕（DP 18、PD 12）で学習前の出力が塔単独と一致（差の最大 0）し、陽性対照で出力が変わり、extra-queries の元の query の出力は界面の重みによらず塔単独と同じで
mask を外すと変わり、学習前の上位 300 は全 val 画像で塔単独と同じ。既定の経路は直しの契約の集計を同じ値で再現（B-3）し、既存の型の照合も一致、test の動画は通していない（C-8）。
K3 の GRU の試走（`stage2four_k3_001_gru_D0only_ep4_smoke_seed42`、1 epoch。run 名の ep4 は誤りで、以後は実際の epoch 数を名前に入れるよう直した）も通った。

## E. 学習（bengio、02:32 JST〜）

起動（`run_pd_four.sh EQ <腕>`、`S2FIX_BODY=$OV`、`S2FIX_CODE=$WT`、20 秒ずつずらす。1 枚に 3 本まで）:

| GPU | 載せたもの |
|---|---|
| 0 | extra-queries の空・予測-noCF・正解 |
| 1 | extra-queries の予測-CF・正解予測-CF、3 本目の枠に `launch/gpu1_chain.sh`（検出から工程の 18 本 → K3 の GRU → extra-queries の入れ替え） |

起動の前の GPU の compute プロセスは 0 件。decoder-xattn の 6 本は andrew（`handoff_andrew.md`）。

### E-1 検出から工程の 18 本（02:32〜02:52 JST、bengio の GPU 1、`launch/gpu1_chain.sh` → `run_dp_four.sh`）

18 本とも rc=0、`result_selection` final_epoch・`result_epoch` 4、受け取り手の不変 true。値は `experiments/analysis/stage2_pilot_four/INTERIM.md`（`aggregate_four.py --interim`。
確率から計算し直した値と run の記録の差の最大 0.0）。1 本の学習の壁時計（`elapsed_seconds`）: LC empty 117.1 秒、LC pred_noCF 97.5 秒、LC gt 20.1 秒、LC pred_CF 18.8 秒、LC gtpred_CF 22.8 秒、LC shuffle 32.6 秒、TH empty 37.2 秒、TH pred_noCF 37.9 秒、TH gt 44.4 秒、TH pred_CF 48.6 秒、TH gtpred_CF 48.2 秒、TH shuffle 48.7 秒、TH-NG empty 43.2 秒、TH-NG pred_noCF 45.8 秒、TH-NG gt 47.5 秒、TH-NG pred_CF 47.7 秒、TH-NG gtpred_CF 39.6 秒、TH-NG shuffle 46.4 秒。

- tool-history（カードどおり）の 4 epoch 目の tanh(α) は 0.0050〜0.0125。空以外の 5 腕は予測した工程（argmax）がすべて同じで（事後確率の差の最大 2.6e−4〜1.0e−3）、空の腕と 2 フレームだけ違う
- 空の腕の陰性対照（学んだ界面に零の代わりに予測の信号を入れる）は各 run の `metrics.json` の `negative_control` に在る
- K3 の GRU（`stage2four_k3_002_gru_D0only_ep4_seed42`、02:52 JST、rc=0）: val の macro Jaccard 0.220015（記述だけ。Task D で使う）

## D. 殺し実験（記述だけ）

### K1 見落としの数え上げと神託（extra-queries。学習なし。02:5x JST、CPU、`kill/k1.json`）

    $ python scripts/stage2pilot/kill_four.py k1 --preds $FOUR/identity/plain_val_preds.json.gz --missed $FOUR/xq/missed_val.json --ann <折り A>/instances_val.json --out .../kill/k1.json

- val の見落とし 78 個（C-4 の表。閾値ごとの数も同じ表）を、正しいクラスと位置・確信度 1 で塔単独の出力に足し、画像ごとに上位 300 を取って評価した
- 塔単独 → 神託: overall mAP 0.7273450 → 0.7481827（**+0.0208**）、標的群 AP 0.7950748 → 0.7950748（+2.3e−8。val の見落としに標的群のクラスが無い）、
  陰性対照群 AP 0.6726632 → 0.7017099（**+0.0290**）。動画ごとの mAP: 09 0.70427 → 0.73219、10 0.64210 → 0.65810
- クラス別の差: Gauze +0.087、Forceps +0.081、Hook +0.075、Scissors +0.020、Tweezers +0.015、Mouth Gag +0.010、Suction Cannula +0.005（他は 1e−9 以下）
- 空振りでないこと: 見落としを 0 件にした写し（`--empty-missed`）では神託の差が 0.0（`kill/k1_control_empty_missed.json`）

### K2 多項ロジスティック回帰（logit-correction。界面の学習なし。05:0x JST、GPU 1、`kill/k2.json`）

設定は測る前に一つに固定した（`kill_four.py` の `LR_SETTING`: sklearn の LogisticRegression、L2、C=1.0、lbfgs、max_iter 5000、特徴の標準化なし）。
val の 2 本で、片方で当てはめもう片方で測った。特徴 (i) 工程塔単独の softmax(ℓ0)、(ii) (i) と D0（確定塔）、(iii) (ii) と D-GT。

| 特徴 | 09 で当てはめ 10 で測る（Jaccard / accuracy / NLL） | 10 で当てはめ 09 で測る（同） |
|---|---|---|
| (i) | 0.3122 / 0.3420 / 17.75 | 0.9366 / 0.9614 / 0.286 |
| (ii) | 0.2892 / 0.3571 / 17.74 | 0.9832 / 0.9865 / 0.177 |
| (iii) | 0.2875 / 0.3581 / 17.75 | 0.9751 / 0.9710 / 0.192 |

- 2 方向の平均: (ii)−(i) Jaccard **+0.0118**・accuracy +0.0201・NLL −0.0577、(iii)−(i) Jaccard **+0.0069**・accuracy +0.0129・NLL −0.0456
- 当てはめた動画に無い工程: 09 には closure・dressing・hemostasis が無く、10 のその 638 フレーム（1,015 中）は当てはめた回帰が出せない工程（NLL は確率を 1e−12 で切って数えた。`mean_nll_seen_only` も記録）。10 には 09 の工程がすべて在る
- 空振りでないこと: (ii) の D0 を正解の工程の one-hot に替えた写し（`kill/k2_control_onehot.json`）で (ii)−(i) の Jaccard が **+0.0952**（正）

### K3 検出の系列だけの GRU と stacking（tool-history。`stage2four_k3_002_gru_D0only_ep4_seed42`、`kill/k3.json`）

- (1) GRU（1 層、64、線形で 9 工程。train は交差適合版の D0、val は確定塔の D0。学習率 5e-4 一定・weight decay 0.01・1 歩 = train の動画 1 本・4 epoch・seed 42、
  損失は DP と同じクラスの重みつき交差エントロピーと平滑化 0.3）: val の macro Jaccard **0.2200**（動画の中で時間の順だけ入れ替えた D0 を入れると 0.0398）
- (2) K2 と同じ形で (i) と「(i) と (1) の事後確率」を比べる: 2 方向の平均の差 Jaccard **+0.0009**・accuracy 0.0000・NLL −0.0000
- (3) (1) の GRU に時間の順を入れ替えた val の D0（seed 42、動画ごとに一つの並べ替え）を入れて (2) を繰り返す: Jaccard **+0.0009**。(3)−(2) は Jaccard 0.0000、NLL +0.0001
- 「GRU の最終状態から術式を当てる精度」: **UNKNOWN**（動画ごとの術式の対応が repo に無い。`context/auto/results_recent.md` 194・204 行。作っていない）

### extra-queries の寄与（予測-CF、学習後。`xq_contrib/pd_EQ_pred_CF_{trained,contrib}.json`）

4 epoch 目の界面で val を評価し直すと、最終の mAP は run の記録と同じ 0.7273450248398429 で塔単独と出力の差 0（score・枠・ラベル）。
スコアの定数は −10 → −9.500。追加の出力の最大スコア 0.00126 は元の 300 番目の最小 0.00480 を下回ったままで、**上位 300 に入った追加の出力は 0 件**、照合した見落としは val 78 個中 0 個。

### E-2 extra-queries の 6 本（bengio、02:32〜05:17 JST）

6 本とも rc=0、`result_selection` final_epoch・`result_epoch` 3、`frozen_unchanged` true、`env_check.txt` `ms_deform_attn_ext True`、`server.txt` bengio、学習前の mAP 0.7273450248398429。

| 腕 | GPU | 開始〜終了（JST） | 所要 | 4 epoch 目の overall mAP | 標的群 AP | 陰性対照群 AP | スコアの定数（4 epoch 目） |
|---|---|---|---|---|---|---|---|
| 空 | 0 | 02:32:42〜05:15:23 | 2.71 時間 | 0.7273450248398429 | 0.7950748008550897 | 0.6726631817581498 | −9.4633 |
| 予測-noCF | 0 | 02:33:02〜05:16:27 | 2.72 時間 | 同上 | 同上 | 同上 | −9.4708 |
| 正解 | 0 | 02:33:22〜05:16:48 | 2.72 時間 | 同上 | 同上 | 同上 | −9.4986 |
| 予測-CF | 1 | 02:33:42〜05:01:38 | 2.47 時間 | 同上 | 同上 | 同上 | −9.5002 |
| 正解予測-CF | 1 | 02:34:02〜05:02:20 | 2.47 時間 | 同上 | 同上 | 同上 | −9.4351 |
| 入れ替え | 1 | 02:52:20〜05:17:19 | 2.42 時間 | 同上 | 同上 | 同上 | −9.4993 |

6 腕とも epoch 0〜3 のすべての val の mAP が塔単独と同値（`per_epoch_mAP` の値が一つ）。速さは 1 枚 3 本で 2.6 it/s、2 本で 3.4〜3.8 it/s（1 epoch 4,809 歩）。

### extra-queries の寄与（6 腕、学習後。05:1x〜05:3x JST、`xq_contrib/run_xq_contrib.sh`、`xq_contrib/pd_EQ_<腕>_{trained,contrib}.json`）

| 腕 | 最終の mAP（評価し直し） | 最終と元の出力だけの差 | 塔単独との出力の差 | 追加の最大スコア | 元の 300 番目の最小 | 上位 300 の追加 | 照合した見落とし |
|---|---|---|---|---|---|---|---|
| 空 | 0.7273450248398429 | 0 | 0 | 0.00176 | 0.00480 | 0 | 0 / 78 |
| 予測-noCF | 同上 | 0 | 0 | 0.00166 | 0.00480 | 0 | 0 / 78 |
| 正解 | 同上 | 0 | 0 | 0.00126 | 0.00480 | 0 | 0 / 78 |
| 予測-CF | 同上 | 0 | 0 | 0.00126 | 0.00480 | 0 | 0 / 78 |
| 正解予測-CF | 同上 | 0 | 0 | 0.00128 | 0.00480 | 0 | 0 / 78 |
| 入れ替え | 同上 | 0 | 0 | 0.00131 | 0.00480 | 0 | 0 / 78 |

評価し直した最終の mAP は 6 腕とも run の記録と同値。追加の出力を除いたとき（元の出力だけ）との差はクラス別 AP・群 AP ともすべて 0。
空振りでないこと: 予測-noCF の学習した界面のままスコアの定数を 0 にした評価（`xq_contrib/control_score0_*`）では、上位 300 に入った追加が 425,322 件（1,515 枚すべて）、
そのうち正解に当たる 5,247 件、見落としに当たる 4 件で、照合した見落としは 3 / 78 個。

### E-4・E-5 decoder-xattn の 6 本（andrew、副の実行者。詳細は `audit_andrew.md`）

andrew の記録の写し（利用者の決定 01:44 JST の 6）:

| 項目 | andrew の値 | bengio との照合 |
|---|---|---|
| S1 開始状態（02:20 JST） | compute プロセス 0 件、RTX A6000 × 2、main の作業場所は変えていない | — |
| S3 環境 | `input_digest.py --body $A` が bengio の `env/input_digest_bengio.json` と、除く 3 個以外の 177 個（末端まで平らにした数え方）で一致。Relation-DETR のソース 142 本・パッケージ 72 個も一致 | 一致 |
| S4 検出塔の塔単独の val | overall mAP 0.7273450248398429、標的群 0.7950748008550897、陰性対照群 0.6726631817581498（seed 123 の対照も bengio と全項目一致） | 差 0.0 |
| S5 恒等性と陽性対照（全 6 腕と陽性対照） | 6 腕とも学習前 mAP 0.7273450248398429、score・枠の差 0.0、ラベル不一致 0、学習する集合 = 界面（210,374、d18 は 210,662）、学習前のゲート 0。陽性対照で変わる | bengio の `identity/pd_DX_*.json` と同値 |
| S6 試走（写しの場所） | 学習前 mAP（20 枚）0.8916611661166115、後処理の AP 0.891661、epoch 0 の tanh(α_l) は bengio と 1e−5 程度違う（bf16 で 6 歩の後） | 学習前の値は同値 |
| S8 起動 | 02:43:44〜02:45:24 JST、GPU 0 に empty・pred_noCF・gt、GPU 1 に pred_CF・gtpred_CF・shuffle（1 枚 3 本）。1 回目は zsh の単語分割で 6 本とも即座に止まった（run は作られていない） | — |
| S10 終わり（06:37 JST） | 6 本とも rc=0、final_epoch・epoch 3、`init` 0.7273450248398429、`frozen_unchanged` true、`ms_deform_attn_ext True`、`server.txt` andrew、学習前のゲート 0。所要 3.782〜3.843 時間 | bengio で `stage2four_metrics.json` を読み直して学習前の値とゲートを確かめた |

4 epoch 目の値（val、`stage2four_metrics.json`）:

| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | 4 epoch 目の tanh(α_l)（層 1〜6） |
|---|---|---|---|---|
| 空 | 0.7286351809653658 | 0.7971802124759885 | 0.674744871212618 | +0.0607, −0.0801, −0.0922, −0.0769, +0.0678, +0.0464 |
| 予測-noCF | 0.7285507127170769 | 0.7977964150437383 | 0.6743162666121828 | +0.0829, −0.0861, −0.0998, −0.0937, +0.0821, +0.0572 |
| 正解 | 0.7307424633845512 | 0.8023051689913743 | 0.6748186678418289 | +0.0765, −0.0914, −0.0883, −0.0970, +0.0779, −0.0758 |
| 予測-CF | 0.7280597990708618 | 0.7956651065025846 | 0.674161721518428 | +0.0730, −0.0870, −0.0987, −0.0932, +0.0769, −0.0480 |
| 正解予測-CF | 0.7304329266677848 | 0.8002190391680053 | 0.6743968833150071 | +0.0945, −0.0915, −0.1224, −0.1037, +0.0988, +0.0642 |
| 入れ替え | 0.728501777648758 | 0.7968013222990057 | 0.6745119663775374 | +0.0605, −0.0648, −0.0806, −0.0660, +0.0772, +0.0431 |

引き渡しの不備（bengio の誤り）: bengio の decoder-xattn の試走の置き場を分岐に commit していたため、andrew の S6 の試走が名前の衝突で止まり、andrew の実行者が利用者の承認を得て
同じ commit の写しの場所で回した。andrew の run の `git_commit.txt` は main の作業場所の HEAD を書く（`EGO_BODY` で取るため）。

## F. 集計・検証・報告（06:40 JST〜）

### 統合と照合（`launch/finalize_after_andrew.sh`、06:40:46〜06:46:49 JST、出力 `experiments/analysis/stage2_pilot_four/final/`）

- andrew の分岐（5d753beb）と本分岐の差は新しいファイルの追加 170 本だけ（`andrew_diff_name_status.txt`）。6 本の `stage2four_metrics.json` と `audit_andrew.md` の S10 の節を確かめてから
  `git merge --no-ff` → **7a2cdcc2**
- 照合（完了判定 j）に要る 6 本の val の予測（版管理外）12 本を andrew から bengio の同じ run の置き場へ写し、sha256 が **12/12 一致**（`dx_predictions_sha256.txt`）
- `aggregate_four.py`（REPORT.md・report.json）: PD 12 本・DP 18 本、予測と事後確率から計算し直した値と run の記録の差の最大 **0.0**、型ごとのホスト decoder-xattn {andrew}、他 {bengio}
- `test_audit_four.py`: 全体の共通 **0 件**、`--inject 04` で 1 件（`test_audit/test_audit_final*.json`）。andrew の run の注釈の経路（andrew の main）は bengio の main にも同じ経路で在り、
  その sha256 が andrew と同じことは andrew の S3（`input_digest`）で確かめてある
- 試験（終了時）: 8 failed、862 passed、15 skipped、収集の誤り 1（`final/pytest_end.txt`）。**失敗の名前の集合は開始時と同じ**
- `make forbidden-check TASK=T-2026-10-19-stage2-pilot-four-new-types`: status pass、変更 722 本、**violations 0**

### 送出（07:0x JST）

- 報告一式の commit `6287b174` を push。挙げた commit 15 個（andrew の 3 個を含む）がすべて遠隔の先頭の祖先（`git merge-base --is-ancestor`。存在しない commit では祖先でない）
- `gh pr edit 243`（題から「実行中」を外し、本文を完了の内容に）→ `gh pr ready 243` → `isDraft: false`、base phase0、head `feat/stage2-pilot-four-new-types`
- `source scripts/load_env.sh && make task-report TASK=T-2026-10-19-stage2-pilot-four-new-types` → **rc=0**（verdict pass、n_issuer_defects 3、report_sha256 `b47dc73cd4911776a9dd6d1d6321e25beb5ae90a1417d3ae1c2c147a83533a10`、
  13,579 B。出力は `final/task_report.txt`）
- `make task-release` は回していない（task-start を使っていないため。amendments 1 件目）

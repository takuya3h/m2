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

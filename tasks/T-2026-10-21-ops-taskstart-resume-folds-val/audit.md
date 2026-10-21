# audit — T-2026-10-21-ops-taskstart-resume-folds-val

実行ホスト andrew（`hostname` = `Andrew`）、repo `/home/ubuntu/slocal2/m2`（`context/env-facts.md` 26 行の andrew の位置と一致）。
時刻は JST。Python の処理はすべて `CUDA_VISIBLE_DEVICES=""` で動かした。証拠のファイルは `evidence/` に置いた。

## 0. 始める・読む・検証・プリフライト

- 1 回目の `/task`（15:5x 頃）: 分岐 `feat/stage2-pilot-fix-epoch4-shuffle`、汚れ 9 行（追跡下 1、未追跡 2、`experiments/` の未追跡 6）。
  手順どおり選択肢を示し、利用者が「3 中止」を選んだ。`make task-release END=abort` → `task-release: ABSENT ...`（目印は元から無い）
- 2 回目の `/task`（16:1x）: 分岐 `feat/ops-taskstart-resume-folds-val`、`tasks/<id>/` 在り → 「再開」。task-start は利用者が実行した
  - `.sync-pause` は開始前から在り、中身は `task_id=T-2026-10-21-ops-taskstart-resume-folds-val` / `branch=feat/ops-taskstart-resume-folds-val`（この契約の所有の記録）（A-2）
  - 前回の汚れのうち未追跡 3 経路は `.git/info/exclude` の 20〜22 行に足され、`docs/analysis_scripts/README.md` は skip-worktree の印つき（`git ls-files -v` で `S`）。
    控え `~/m2-hold/T-2026-10-21-ops-taskstart-resume-folds-val/`: `exclude.before`（現行との差は上の 3 行の追加だけ）、`skip.txt`（README の 1 行）、`status.before`（4 行）
  - `ls-remote` で `Warning: Identity file /home/ubuntu/.ssh/id_Andrewdeploy not accessible`（照会は成功）
- `make task-validate` → `OK`（WARN なし）。`make task-preflight` → `6 PASS / 0 WARN / 8 SKIP / 0 FAIL`（SKIP: P2 P3 P4 P5 P11 P12 P13 P14）
- `grep -c sync-pause ~/bin/m2-sync.sh` → `2`（稼働中の版は抑止に対応）

## A. 開始状態（16:20〜16:23）

| 項目 | 実測 |
|---|---|
| A-1 分岐 | `feat/ops-taskstart-resume-folds-val`（`feat/` で始まる） |
| A-1 起点 | `HEAD` = `origin/phase0` = `merge-base` = `3cb3db070eb0735b974933223e1fb8eb4dfb262b` |
| A-1 作業ツリー | `status --porcelain --untracked-files=all` は契約の 2 ファイル（`SPEC.md`・`spec.yaml` の未追跡）だけ。cbcf05f5 で commit して 0 行にした |
| A-2 目印 | 開始前から在り、この契約の所有の記録（上記） |
| A-3 装置（開始 16:21） | GPU 0・1 とも 16 MiB / 0 %。`nvidia-smi --query-compute-apps` は 0 件（`/proc/PID/exe` を解決する対象なし） |
| A-4 規約 | `git log -1 origin/phase0 -- context/conventions.md` = `5c0eaeeb4551…`（起票時と同じ） |
| A-4 runindex | `git log -1 origin/phase0 -- runindex/` = `63ae65da8c7d…`（同じ） |
| A-4 行数 | `git show origin/phase0:runindex/{index,experiments,verdicts}.csv \| wc -l` = 1962 / 751 / 1507。見出しの 1 行を除いて 1961 / 750 / 1506（同じ）。`meta.amendments` は足さない |
| A-5 除外の一覧 | `.git/info/exclude` の注釈と空行を除く行数 15 |
| A-5 突き合わせ | 無視された未追跡のうち `origin/phase0` に同じ経路が在るもの 0 件（同じ 0 / 違う 0） |
| A-6 試験 | 894 件、失敗 6、収集エラー 0（`evidence/tests_before.set`） |
| A-7 規約の節 | 16 節（`_preamble` + アンカー 15）。`evidence/a7_before.tsv` |
| A-8 完了済み | 契約 154 件のうち 128 件。うち stop か ask を含む 15 件。128 件すべての `result.yaml` が `origin/phase0` の木に在る（在らないもの 0 件） |

A-5 の数え方（`evidence/a5_measure.py`）: 方法 1 は「phase0 の木 − 索引 → 手元に在る → `git check-ignore --no-index`」（0.03 秒）、
方法 2 は `git ls-files --others --ignored --exclude-standard` の全数と木の積（0.68 秒）。両者一致（0 件）。
中身は `git cat-file --filters origin/phase0:<経路>` と手元のバイト列を比べる。

**数え方の対照**（隔離した場。phase0 に `s.txt`・`d.txt`、手元に無視された `s.txt`（同じ）・`d.txt`（違う）・`n.txt`（phase0 に無い））:
`method1 ignored&in_base=2 … agree=True` / `same=1 diff=1` / `DIFF d.txt` / `SAME s.txt`。phase0 に無い `n.txt` は数えに入らない。

A-6 の失敗 6 件（3 回とも同じ集合）:
`test_engines::test_mmdet_trainer_eval_recipe_in_metrics`、`test_fetch_task::test_rejects_unknown_file_name`、
`test_research_logger::{test_log_run_idempotent, test_run_logging_invokes_log_run_on_finally, test_run_logging_no_double_post_on_normal_exit, test_run_logging_swallows_exception_in_user_block}`。

**関門 G1: pass。** 分岐・起点・作業ツリー（契約自身の 2 ファイルを commit した後に 0 行）・目印の所有・中身の違う無視されたファイル 0 件。

## B. task-start の直し

### 設計を決めた実測（隔離した場、`git 2.43.0`）

1. 「起点と同じ中身の未追跡を索引へ載せてから `checkout -b`」→ 成功。載せたファイルは inode も mtime も変わらない（書き直されない）
2. 巻き戻しを `git rm --cached` → `git checkout <元>` で行う → `error: The following untracked working tree files would be removed by checkout: s.txt` で拒まれる。
   無視されたものは拒まれずに消される（拒否の一覧に `si.txt` が出ない）
3. 巻き戻しを `git rm --cached` → `git read-tree -m -u "$(git write-tree)" <元>` → `git symbolic-ref HEAD refs/heads/<元>` で行う →
   分岐・索引・`.git/info/exclude`・通したファイル（inode まで）が実行前と同じ。追跡下で両分岐の中身が違うファイルは git が書き戻す（従来の checkout と同じ）

### 比べ方

通常のファイルは `git cat-file --filters <起点>:<経路>`（切り替えで書かれる、属性による変換を経た内容）と手元のバイト列。
シンボリックリンクは `readlink` と blob（phase0 に 4 件ある）。手元がディレクトリなどで比べられないものは「違う」（止める側）に数える。
無視されたものは列挙しない（起点の木 − 索引 − 無視されていない未追跡 のうち手元に在るものだけを比べる）。

### 所要時間（andrew の実物、読み取りだけ、16:30）

`python3 scripts/task_start_classify.py` → 0.41 秒（木 22,801 件）。前後で `git ls-files -s | sha256sum` = `db6cf545…` で同じ、
`.git/info/exclude` の sha256 `0c862f0c…` は変えていない。出力（このときは作業中の変更があった）:

    [task-start] 分類（比較先 origin/phase0 3cb3db07）
    [task-start]   追跡下の変更: 2 件
    [task-start]   未追跡・起点に在り中身が同じ: 0 件（通す）
    [task-start]   未追跡・起点に在り中身が違う: 0 件
    [task-start]   未追跡・起点に無い: 2 件
    [task-start]   無視・起点に在り中身が同じ: 0 件（通す）
    [task-start]   無視・起点に在り中身が違う: 0 件
    [task-start]   無視・起点に無い: 数えない（触れない）
    [task-start]   止めた理由 [追跡下の変更]  M scripts/task_start.sh
    （… 4 行）
    [task-start] 起点に無いと分類で確かめた経路は、無視の一覧（.git/info/exclude）に足せば切り替えで触れられない。…
    [task-start] 分類: 止める

### 試験（`tests/test_task_start_classify.py`、18 件）

| §5.1 の行 | 陽性（止まる） | 陰性（通る） |
|---|---|---|
| 追跡下の変更 | `test_row1_tracked_change_stops`（rc 3、前後の状態が同じ） | `test_row1_control_clean_tree_passes` |
| 未追跡・在り・同じ | `test_row3_…`（一文字変えると rc 3） | `test_row2_…`（rc 0、中身と inode が同じ、`status` 空） |
| 未追跡・在り・違う | `test_row3_untracked_one_char_different_stops` | row2 |
| 未追跡・無い | `test_row4_…`（経路と無視の一覧の案内が出る） | row1 の陰性 |
| 無視・在り・同じ | `test_row6_…`（中身を変えると rc 3） | `test_row5_…`（rc 0、中身と inode が同じ、除外の一覧が同じ） |
| 無視・在り・違う | `test_row6_ignored_different_content_stops` | row5 |
| 無視・無い | `test_row7_control_unignored_same_file_stops`（無視を外すと rc 3） | `test_row7_…`（rc 0、触れない） |

止めた場合はどれも `_state`（作業ツリー全ファイルの sha256 と inode、`ls-files -s` の要約値、除外の一覧、分岐の一覧、目印）が前後で同じ。
目印: `test_marker_classes_are_unchanged`。スキルの読む分類: `test_classifier_alone_is_read_only_and_matches_task_start`（単独の出力行が task-start の出力に同じ順で含まれ、単独の実行は状態を変えない）。

巻き戻し（完了判定 c）:
- `test_failed_import_after_adoption_restores_everything`: 未追跡・同じ と 無視・同じ を通した後に取り込みを失敗させる → rc 4、`_state` が前後で同じ
- `test_failed_checkout_after_adoption_restores_index`: 載せた後に切り替えが拒まれる（skip-worktree の変更）→ rc 4、`_state` が前後で同じ
- `test_rollback_without_unadopt_is_detected`（変異）: 巻き戻しの「索引から外す」を `true` に替えた写し → rc 4 だが状態が違う。差の中身（`evidence` 外の手元の確認）:
  `p0/other.txt` と `p0/same.txt` が作業ツリーから消え、表示は「実行前の状態へ戻しました」のまま

§3.2 の再現（直す前の版は `git show 3cb3db07:scripts/task_start.sh` を作業ツリーの外に置いて使う）:
- 1 行目: 直す前の task-start はその前の汚れの判定で rc 3 になり切り替えに届かない。git そのもので再現した（`test_git_refuses_unignored_untracked_in_the_way`、同じ中身でも違う中身でも `would be overwritten` で拒む）
- 2 行目: `test_pre_fix_task_start_silently_overwrites_ignored_file`（直す前は rc 0 で、無視された手元の中身が phase0 の版になった）
- 3 行目: `test_pre_fix_task_start_is_refused_on_skip_worktree_change`（直す前も後も rc 4、状態は前後で同じ。§5.1 の外なので挙動を変えていない）
- 加えて `test_pre_fix_task_start_stops_on_any_untracked`（直す前は同じ中身の未追跡でも rc 3）

既存の試験 `tests/test_task_start_pause_owner.py` は場の作り方に分類器の写しを 1 行足しただけで、主張は変えていない（8 件通過）。

**関門 G2: pass。** `pytest tests/` → 912 件、失敗 6、収集エラー 0。失敗の名前の集合は A-6 と同じ（`evidence/tests_g2.set`）。

## C. task スキル

- 「0. 始める」に `git fetch origin && python3 scripts/task_start_classify.py` を足し、汚れ／清浄は分類の最後の行（`分類: 止める`／`分類: 通す`）で判定する。
  分類の実装はスキルに無い（スキルが呼ぶのは `scripts/task_start_classify.py`、task-start も同じファイルを `CLASSIFY` で呼ぶ）
- 汚れの扱いに §5.1 の表、止めた経路に添える二つ（禁止領域・大きさ）、移す選択肢の前に「同期処理が他の台へ削除として伝えうる」、
  無視の一覧に足してよいのは「phase0 に無い」と出た経路だけ、を書いた。既存の三つの選択肢は残した
- **`.codex/skills/task` は `../../.claude/skills/task` へのシンボリックリンク**（`readlink`）。写しは一つで、要約値は両経路とも
  前 `4b1f1c2f…`、後 `038a5d71…`
- `make agent-check` → pass（158 対象）、`make docs-check` → 食い違いなし、`tests/test_skill_task_doc.py`・`tests/test_check_docs.py` 22 件通過

## D. 停止して再開した契約の検査

- 定義: `completed_verdicts` は従来の印（`gates[].verdict` の空でない値）に加え、`merged_task_ids()`（`git ls-tree -r origin/phase0 -- tasks/` の
  `tasks/<id>/result.yaml`、一度だけ読んで保持）に識別子が在るときだけ印を返す。参照が解決しなければ `None` を返し、標準エラーへ一行
  `警告: origin/phase0 を解決できないため、完了済みの判定から統合の条件を外す（result.yaml の gates[].verdict に空でない値があれば完了）`。
  P13・P14・allow_write は従来どおり `completed_verdicts` だけを呼ぶ（呼び出しの形は変えていない）
- **D-2 集合の差**: 前 `evidence/a8_before.txt`（128 件）、後 `evidence/a8_after.txt`（128 件）、`diff` 0 行
- D-3 試験を直す前に新しい定義で回すと 12 件が落ちた（一時の木の契約が統合済みでないため）:
  `test_symmetry_gate::{test_completed_contract_is_skipped, test_completed_verdicts_reads_only_the_gates}`、
  `test_legacy_exclusions::test_completed_contracts_are_not_detected[{exp,impl}-{pass,ask,stop,skip}]`（8 件）、
  `test_legacy_exclusions::test_the_completed_check_is_the_same_function_as_p13_and_p14`、`test_proposal_card_gate::test_p14_skips_for_completed_contract`
- D-3 直した試験と、何を固定する試験に変えたか:
  - 三つの場（`test_symmetry_gate.tasks_dir`、`test_legacy_exclusions._contract_tree`、`test_proposal_card_gate.tasks_dir`）に
    「一時の木の報告は統合済みとみなす」差し替えを足した。上の 12 件は「**統合済み**で印があれば完了」を固定する試験になった
  - `test_legacy_exclusions::test_completed_contracts_are_not_detected` の説明「stop・ask を含む。定義は変えない」→「統合済みで verdict に空でない値があれば完了（stop・ask を含む）」
  - 新規: `test_stopped_unmerged_contract_is_checked`（未統合の stop → 印は空、表を欠く prereg で P13 FAIL）、
    `test_stopped_merged_contract_is_still_skipped`（同じ報告が統合済みなら SKIP）、
    `test_merged_ids_come_from_the_phase0_tree`（実物の木に `T-2026-09-19-symmetry-gate` が在り、存在しない名は無い）、
    `test_unresolvable_ref_falls_back_with_one_warning`（参照 `refs/remotes/origin/no-such-ref-zz` → `["stop"]`、二回呼んで警告は一行）、
    `test_stopped_unmerged_contract_is_checked_by_all_three`（統合済みとみなすと allow_write 非検出・P13 SKIP・P14 SKIP、未統合にすると検出・FAIL・FAIL）
  - `tools/check_spec.py` 513〜515 行の注記「定義は変えない」を新しい定義に合わせた
- D-4 「再開の前に `result.yaml` を進行中に戻す」と書いた箇所を探した範囲: `.claude/skills/task/SKILL.md`、`context/conventions.md`、`tasks/README.md`、
  `tools/preflight_task.py`、`tools/check_spec.py`、`docs/issuer-defects.md`、`docs/proposal-gate.md`、`docs/symmetry-checklist.md`、`tasks/_templates/`
  （語「進行中」「in_progress」「再開」）と、repo 全体の `*.md` の `result.yaml.*(戻|消|退)`。該当 0 件
- 起票者の数（gate の判定を持つ 128 件、stop か ask を含む 15 件）は実測と一致

## E. 規約 folds

- 4e67202c で folds の「規律」の後・`---` の前に小節「val と test の重なり」を足した。既存の表・追加動画・規律は無変更
- 2d946b07 で変更履歴の表（naming 節の範囲）に 1 行（commit 欄は小節を置いた 4e67202c）
- val の対応の突き合わせ（folds の表から機械的に導いたものと、書いた表）:

  | val | val に使う折り | test に持つ折り | 導出と一致 |
  |---|---|---|---|
  | 09, 10 | A | E | 一致 |
  | 02, 08 | B | C | 一致 |
  | 06 / 12 | C | D / E | 一致 |
  | 04, 05 | D | A | 一致 |
  | 07 / 15 | E | A / D | 一致 |

  val に一度も入らない: `['01', '03', '11', '13', '14']`、test の折りごと `{A: [], B: [01, 03, 14], C: [11], D: [13], E: []}`（SPEC §5.3 と同じ）。
  `docs/stage1/design_val_subsets.md` 223 行は `| 清浄本数 A,B,C,D,E | 0, 3, 1, 1, 0 | 3, 3, 1, 1, 0 |`
- 節ごとの要約値の前後（`evidence/a7_before.tsv` → `a7_after.tsv`）: 変わった節は `folds`（`19251e44…` → 変化）と `naming`（`07f0b9f1…` → 変化）だけ。
  ほかの 14 節は同じ。アンカーの名前と数（15 + 先頭）は同じで、`validate_task.conventions_anchors()` が 15 個すべてを返す
- 対照: 写しの prohibitions 節を一文字変える（「再定義」→「再定議」）と `CHANGED prohibitions` が出る（`evidence/a7_mut.tsv`）
- `make task-validate` は L2-6 の WARN（規約が `conventions_rev` 以降に変わった）を出す。SPEC §10 の想定内

**関門 G3: pass。**

## F. 起票者の欠陥

`docs/issuer-defects.md` の「測らずに断定した」の末尾（既存の 4 件の後）に 2 件。`git diff --numstat` = `2 0`、旧版にあって新版に無い行 0 件。
出所の行番号: `tasks/T-2026-10-19-conventions-and-defect-records/spec.yaml` 13〜16 行（`meta.amendments`）、同 `RESULT.md` 184 行（判定）・208〜210 行（起票者の誤り）、
本契約 `SPEC.md` 12〜17 行（§1 の 1）・54〜64 行（§3.2）。

## G. 検証

| 検査 | 結果 |
|---|---|
| L1 `make task-validate LEVEL=l1` | OK |
| L2 `make task-validate` | OK（WARN L2-6 のみ） |
| `make forbidden-check TASK=…` | `status: pass`、changed 14、violations 0、permitted は `context/conventions.md`（allow_write） |
| 対照: 変更の一覧に `data/splits/ego_val.txt` を足した写し（`changed_paths` の差し替え。data へは書かない） | `status: fail`、`禁止領域 data/ の内側` |
| `make spec-check TASK=…` | `status: pass`、9 規則とも 0 |
| `make task-preflight` | 6 PASS / 0 WARN / 8 SKIP / 0 FAIL（警告行なし） |
| `pytest tests/`（16:36） | 917 件、失敗 6、収集エラー 0。集合は A-6 と同じ（`evidence/tests_final.set`） |
| 装置（終了 16:36） | GPU 0・1 とも 16 MiB / 0 %、compute apps 0 件 |
| 生成物 | `context/auto/*`・`tasks/inbox.md` は再生成していない。`taskindex-check`・`inbox-check` は回していない |
| 接続 | `origin` への照会（「0. 始める」の `ls-remote` 2 回）、push、PR、`make task-report` だけ。本セッションで `git fetch` は実行していない（`origin/phase0` は 3cb3db07 のまま）。試験の fetch は一時ディレクトリの裸の repo が相手 |

変更範囲（`git diff --stat origin/phase0..HEAD`、15 ファイル）: `.claude/skills/task/SKILL.md`、`README.md`、`context/conventions.md`、`docs/issuer-defects.md`、
`scripts/task_start.sh`、`scripts/task_start_classify.py`（新規）、本契約の `SPEC.md`・`spec.yaml`、`tests/test_legacy_exclusions.py`、`tests/test_proposal_card_gate.py`、
`tests/test_symmetry_gate.py`、`tests/test_task_start_classify.py`（新規）、`tests/test_task_start_pause_owner.py`、`tools/check_spec.py`、`tools/preflight_task.py`。
`data/` への書き込み 0。`.git/info/exclude` は変えていない（sha256 `0c862f0c…`）。

## 送出

（commit・push・PR・`make task-report` の後に追記する）

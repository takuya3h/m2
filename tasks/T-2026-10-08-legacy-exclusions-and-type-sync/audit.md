# audit — T-2026-10-08-legacy-exclusions-and-type-sync

実行ホスト: efros。コマンドと出力の記録。判断に使う要約は RESULT.md。

## A. 前提と開始前の数値（G1）

| 項目 | 実測 |
|---|---|
| HEAD / 分岐 | c919388a / feat/legacy-exclusions-and-type-sync（起点 origin/phase0） |
| 前提 #194 | 統合 commit cb3fcaa1 は origin/phase0 の祖先（`merge-base --is-ancestor` が成功）。陰性対照: 存在しない名 deadbeef00 は exit 128 |
| 未統合 PR | 開いている PR は #223（exp/ops-autodraft-probe）のみ。本契約の経路（tools/ tasks/_* tests/ .claude/skills/task tasks/README）への変更は 0 件 |
| `docs/issuer-defects.md` | #221（4cd382cf）で統合済み。本契約は読むだけ |
| 作業ツリー（task-start 直後） | 未追跡 2 件（本契約の SPEC.md・spec.yaml）のみ。開始前の汚れは 0 |
| stash | 4 件（stash@{0}〜{3}）。触れていない |
| 試験 | 6 failed / 760 passed。失敗名: test_engines::test_mmdet_trainer_eval_recipe_in_metrics, test_fetch_task::test_rejects_unknown_file_name, test_research_logger::{test_log_run_idempotent, test_run_logging_invokes_log_run_on_finally, test_run_logging_no_double_post_on_normal_exit, test_run_logging_swallows_exception_in_user_block} |
| 全契約の検証 | 144 task(s), 1 failed。失敗は T-2026-08-22-philip-hub-foundation の 1 件（result.yaml の様式エラー 16 件）。SPEC が述べる inbox.d の件は SKIP で、失敗に数えられていない（起票者の記述と実測が違う） |
| 報告の様式エラー | 契約ごと: philip-hub-foundation 16 件、他 0 件。合計 16 |
| spec-check（契約指定なし） | hits 232 / rules_checked 9。`allow_write_incomplete` 15 件（exp 10、impl 5。一覧は基準値ファイル） |
| 型の集合 | schema 6 語。build_taskindex.py 6 語（一致）。docs/issuer-defects.md 6 語。**雛形 4 語、手順書 4 語、tasks/README.md 4 語** |
| 占位の置換 | runindex_commit 63ae65da、counts 1961/750/1506。conventions_rev は 073f9dc0 で記載と一致、置換せず |
| split_files | 参照しなかった |

spec-check の allow_write_incomplete 15 件（開始前）:
exp: phase-baseline-power, grasp-injection-effect, injection-form-sweep, injection-sweep-deterministic, denoise-falsification, det2phase-segmentation-lovo, oracle-ceiling-and-tool-drop, oracle-ceiling-lovo, lecun-detector-env-pd, stage0-contract-b
impl: proposal-gate, amp-compile-timing, fold-table, p13-skip-and-enum, symmetry-gate

旧様式の `result.yaml` の md5: 87d316d203ee5efec89ff09bd54b6fff（T-2026-08-22-philip-hub-foundation）

### G1: 通過（前提は満たされ、開始前の数値はすべて実数で記録した）

## A-4. 取り込まない項目の確認（読み取りのみ）

| 項目 | 見た場所 | 結果 |
|---|---|---|
| digest の出力先が版管理の外 | `.gitignore:235-239`（docs/sessions/digest/）、`.claude/hooks/session_end.sh:15,18` | 達成 |
| 開始処理が止まるとき汚れた経路・退避・戻し方を表示 | `scripts/task_start.sh:106-111` | **一部未達**。汚れた経路は `git status --short` で表示されるが、退避の方法と戻し方の表示は無い（件数と「片付けてから」の一文のみ） |
| 投影の再生成の規則 | `.claude/skills/task/SKILL.md:208-210,233-234`、`tasks/README.md:229-232`、`.github/workflows/regen-projections.yml` | 達成 |

確認の前後で `git status --porcelain` の要約値は同じ（読み取りのみ。直していない）。

## A-5. 本契約自身の spec-check

hits 3（gate_requires_report_before_end 1、host_mismatch 1、integration_prohibited_without_pause 1）。
`allow_write_incomplete` は 0 件。これら 3 件は起票者の規則の誤検出または記述で、本契約の実行に影響しない。

## B. 旧様式の除外

- 置き場: `tasks/_schema/result_legacy_exclusions.yaml`（P14 の例外 `PRE_GATE_EXEMPT_TASKS` と同じ「完全一致」の流儀。一覧は yaml、理由・決定日・出所を同じ行に持つ）。初期は T-2026-08-22-philip-hub-foundation の 1 件
- 組み込み: `tools/validate_task.py` の `load_legacy_result_exclusions` と `main`。辞書の完全一致（ディレクトリ名）。除外した契約は `除外（旧様式） <契約名>: result.yaml の様式検査を行わない` を出す。spec の検査は続く。最終行 `N task(s), M failed` は変更なし
- 実測（l1）: 変更前 `144 task(s), 1 failed` → 変更後 `144 task(s), 0 failed`。除外の行は 72 行目、OK の行が 73 行目で、最終行ではない
- 旧様式ファイルの md5: 変更前後とも 87d316d203ee5efec89ff09bd54b6fff。`git status` に tasks/T-2026-08-22-* は現れない
- 契約ごとの様式エラー（除外を考慮した件数）: 変更前 {philip-hub-foundation: 16} → 変更後 {}。旧様式以外の差は空集合
- `tasks/_schema/` を走査する道具・試験: `*.schema.json` だけを schema とみなす（tests/test_legacy_exclusions.py の最後の試験で固定）。全試験で新ファイルによる失敗の増加は無い

| 入力（tests/test_legacy_exclusions.py） | 結果 |
|---|---|
| 一覧と同じ名前 + 旧様式の報告 | 除外され、FAIL なし、終了コード 0 |
| 一文字違い（末尾 n→m） | 除外されない。L1-6 で FAIL、終了コード 1 |
| 末尾に改行 | 同上 |
| 末尾に半角スペース | 同上 |
| 大文字小文字 | 同上 |
| 接頭辞のみ | 同上 |
| 接尾辞つき（-r2） | 同上 |
| 一覧に無い名前 + 不適合の報告 | 従来どおり FAIL |
| 一覧の名前 + spec の kind を壊す | 除外の行は出るが spec の検査で FAIL（外すのは様式の検査だけ） |
| 同内容の旧様式報告を別名で置く | 除外されない（照合は名前であり内容ではない） |

## C. 完了済みの契約の除外

- G2: `check_symmetry_table`（P13）と `check_proposal_card`（P14）はどちらも `preflight_task.completed_verdicts` を呼ぶ（tools/preflight_task.py:628, :696）。食い違いなし。`check_spec.py` も同じ関数を `preflight_task.completed_verdicts(c.task)` で呼ぶ（モジュールごと import し、呼び出し時点で解決）。関数の位置は移していない
- 循環 import の有無: preflight_task は check_spec を関数の内側（P9）でのみ import するため、モジュール読み込み時の循環は無い
- spec-check（契約指定なし）: hits 232 → 217、`allow_write_incomplete` 15 → 0、rules_checked 9 → 9。他の規則の件数は不変（hits_by_rule の差は allow_write_incomplete のみ）
- 減った 15 件はすべて `completed_verdicts` が空でない。残った契約に verdict ありは 0。追加された該当は 0
- 内訳（status）: pass 10、partial 4、stopped 1。pass 以外 5 件: T-2026-08-11-phase-baseline-power (partial)、T-2026-08-26-denoise-falsification (stopped、gates に stop)、T-2026-08-26-det2phase-segmentation-lovo (partial、gates に ask)、T-2026-08-26-oracle-ceiling-and-tool-drop (partial)、T-2026-08-29-stage0-contract-b (partial)
- 変異（実物の木、`completed_verdicts` を常に空にする）: 変異前 awi=0 / P13=SKIP / P14=SKIP → 変異中 awi=15 / P13=FAIL / P14=FAIL → 戻した後 awi=0 / P13=SKIP / P14=SKIP。作業ツリーの要約値は変異の前後で一致
- 教師データの試験: `tests/test_check_spec.py::test_teacher_detection_rate` が除外で落ちた（検出 12、期待 15）。入力が完了済みの実契約（proposal-gate#1、amp-compile-timing#5、p13-skip-and-enum#4）。**期待値は変えず**、試験だけが使う専用のフィクスチャ `findings_before_completed_exclusion`（`completed_verdicts` を切って全契約を検査）へ入力を置き換えた。ツール側に引数は足していない（規則の署名と数を動かさないため）。除外なしの全体の検査を使う他の試験は変更なし

## D. 型の写し

- 検索: テキスト検索（`git ls-files -z | xargs -0 grep`、先頭がドットの `.claude/` を含む）と、schema の列挙を実行時に読む試験（実ファイルの区間から語を取り出す）の二つ
- 空振り対策: 実在する型の語（check_does_not_check）で 1 以上、存在しない語（zz_unknown_type）で 0 を試験で固定
- 分類:
  - 直した（allow_write の内側）: `.claude/skills/task/SKILL.md`、`tasks/README.md`、`tasks/_templates/result.yaml`
  - 読むだけ・ずれなし: `docs/issuer-defects.md`（6 語で schema と一致）
  - 既に一致: `tools/build_taskindex.py`（既存の試験が縛っている）
  - 記録・投影のため触れない: `tasks/T-*/`、`context/auto/`、`tasks/inbox.md`
  - `.codex/skills/task` は `.claude/skills/task` へのシンボリックリンクで、別の写しではない
  - allow_write の外で見つかった写し: なし
- 個数を述べる語句の残存: 型の一覧の区間で 0（試験で固定）。雛形の「type は 3 種に固定」は deviations の型（schema と一致）の語句で、型の写しではないため触れていない
- 試験: 既存の `test_defect_types_in_the_projection_match_the_schema` と同じファイル（tests/test_symmetry_gate.py）へ追加。四つの写し（手順書・README の表・雛形・docs/issuer-defects.md）を schema の列挙と双方向で比べ、個数の語句を拒む
- 変異（tests/test_symmetry_gate.py の失敗名。`scratchpad/mutate_d.py` が復元つきで実行し、前後の sha256 が一致）:

| 変異 | 結果 |
|---|---|
| 変異前 | 51 passed |
| 手順書から rule_read_narrowly を消す | 2 failed（…[skill]、空振り対策の試験） |
| README の表から asymmetric_comparison の行を消す | 2 failed（…[readme]、空振り対策） |
| 雛形の rule_read_narrowly の行を消す | 2 failed（…[template]、空振り対策） |
| 雛形へ schema に無い語を足す | 2 failed（…[template]、空振り対策） |
| schema の列挙へ一語足す（写しは古いまま） | 6 failed（build_taskindex・四つの写し・空振り対策） |
| 手順書に「6 語」を戻す | 1 failed（個数の試験[skill]） |
| 戻した後 | 51 passed、md5 一致 |

## E. 検証

- 試験一式: 開始前 6 failed / 760 passed → 6 failed / 802 passed。失敗名の集合差は空。新規に入れた試験は 42 件（tests/test_legacy_exclusions.py 33、tests/test_symmetry_gate.py 9）
- 禁止領域: `make forbidden-check BASE=c919388a`（分岐点）は status pass、violations 0、changed 12。BASE 省略（origin/phase0 と比較）も同じ結果（分岐後に phase0 へ入った他の PR が無いため差が出ない）
- 変更範囲: tasks/T-2026-10-08-legacy-exclusions-and-type-sync/、tasks/_schema/、tasks/_templates/、tasks/README.md、tools/、tests/、.claude/skills/task/ のみ。宣言との差集合は空
- 既存行の削除（文書・雛形・手順書）: 型の一覧の 3 行のみ（手順書 1、README 1、雛形 1）。それ以外の削除行は tools/・tests/ の置換
- ruff: 触った 5 ファイル（validate_task.py、check_spec.py、test_legacy_exclusions.py、test_symmetry_gate.py、test_check_spec.py）が合格
- 禁止語検査（`tools/check_proposal.py --only forbidden`、件数で判定）: SPEC.md 0 件、audit.md 0 件、RESULT.md 0 件。囮（禁止語を 1 語含む文書、版管理の外 = scratchpad）は 1 件検出、終了コード 1
- 秘匿の検査: 変更・新規の 15 ファイルを、環境にある二つの資格情報の値そのものとの一致と、鍵の形（ntn_／secret_／sk-／40 桁 hex）で走査。一致 0 件、形の一致 0 件。出力は件数だけで値は出していない。陽性対照（メモリ上の囮）は形 1 件、環境の値そのもの 1 件を検出
- `.env` と `load_env.sh` の警告（平文 .env が .env.gpg と異なる）は task-start の出力に出たもので、触っていない
- 全契約の検証（L2、`validate_task.py --level l2`）: 変更後 `144 task(s), 0 failed`、終了コード 0（変更前は `144 task(s), 1 failed`）

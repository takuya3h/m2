# audit — T-2026-10-07-skill-task-start-and-release

実行ホスト `philip`（`hostname` は `aolab`）。分岐 `feat/skill-task-start-and-release`。時刻は JST。

## A. 開始状態（G1）

### A1. 作業ツリーと位置

- `make task-start` の前: 分岐 `feat/pause-release-tool-digest-relocate`（前の契約の分岐。#217 は 2026-10-07 20:27 JST に統合済み）。`git status --porcelain` は 0 件、未 push は 0 件、`.sync-pause` は無かった
- 開始後: 分岐 `feat/skill-task-start-and-release`。HEAD = `origin/phase0` = `08224414`（#218 の統合）
- `git status --porcelain`: `?? tasks/T-2026-10-07-skill-task-start-and-release/` の 1 件だけ（取り込んだ契約）

### A2. task-start の表示と目印

```
[task-start] 分岐を作成: feat/skill-task-start-and-release（起点 origin/phase0）
[task-start] .sync-pause を作成（報告まで終えたら rm -f .sync-pause）
```

- 表示は **「作成」**（実行前から存在、ではない）
- 目印 `.sync-pause` は `size=91`、sha256 の先頭は `e064c0a33cce7053`。中身は次の 2 行（新しい task_start.sh が置いた所有の記録）:

```
task_id=T-2026-10-07-skill-task-start-and-release
branch=feat/skill-task-start-and-release
```

→ **Task F の 6 は、改めた終える段の完了の終わり方で実地に試せる。**

### A3. 手順書の見出しと要約値（変更前）

`.claude/skills/task/SKILL.md` の sha256 の先頭は `5e986c786138658b`。

```
6:# task — TASK 契約の実行
8:## 実装系について
17:## 命令の書き方
29:## 使い方
33:## 手順（この順序を変えない）
35:### 1. 読む
48:### 2. 検証する（L1 + L2）
55:### 3. 参照を解決する
67:### 4. L3 プリフライト（実行直前）
86:### 5. 実行する
88:#### 実行前に自動同期を止める（契約の禁止事項を守るため）
134:### 6. 報告する
162:#### 禁止領域に触れていないことを確かめる
176:#### 生成物が併合で衝突したとき
184:#### 報告を配布台帳へ送り返す
214:### 7. 禁止事項
233:## kind ごとの完了条件
```

### A4. 試験と文書検査（変更前）

- 試験（`--continue-on-collection-errors`）: `6 failed, 725 passed, 1 skipped, 2 errors`。失敗とエラーの名前は 8 件で、前の契約の開始前と同じ集合（`diff` で差なし）
  - `ERROR tests/test_estimate_tier_cost.py`、`ERROR tests/test_stage1_dtower_convergence.py`
  - `FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`、`FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name`
  - `FAILED tests/test_research_logger.py` の 4 件（`test_log_run_idempotent`、`test_run_logging_invokes_log_run_on_finally`、`test_run_logging_no_double_post_on_normal_exit`、`test_run_logging_swallows_exception_in_user_block`）
- `make agent-check` は exit 1 相当。違反は `docs/experiment_settings.md:155` の 1 件、`pager_violations` は 0 件
- `make docs-check` は exit 1 相当。不合格は `docs/proposal-gate.md:41 実在しない経路 docs/proposals/YYYY-MM-DD-slug.md` の 1 件

### A5. 版

- `conventions_rev`: 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`。記載と一致
- `runindex_commit`: 実測 `63ae65da8c7d32df591f5e2ee4358286b72c726b`。記載と一致
- → `amendments` は空のまま
- §2 の起票者の事実: phase0 は起票時の `39c4ff1` から `08224414` へ進んでいた（#218 は生成物の自動 PR）。手順書の行番号（`:97` `:103-113` `:124`）と task_start.sh の行番号（`:145-150`。前の契約の変更後）は、現物と照合して後で記録する

**G1: pass。**

- §2 の起票者の事実を現物と照合した。手順書 `:97`（無条件の `touch`）、`:103-113`（手で外す命令）、`:124`（対応の確かめ）、task_start.sh `:145-150` と `:148`（案内文）、`tasks/README.md:151-156` はいずれも一致した。`39c4ff1` は #217 の統合 commit（`39c4ff10`）で、phase0 の祖先である

## B・C. 手順書の改訂

変更後の `.claude/skills/task/SKILL.md` は 345 行、sha256 の先頭は `5d24ccbbd5949e48`。見出しは次のとおり。

```
6:# task — TASK 契約の実行
8:## 実装系について
20:## 命令の書き方
32:## 使い方
36:## 手順（この順序を変えない）
41:### 0. 始める          ← 追加
91:### 1. 読む
104:### 2. 検証する（L1 + L2）
111:### 3. 参照を解決する
123:### 4. L3 プリフライト（実行直前）
142:### 5. 実行する
144:#### 実行前に自動同期を止める（契約の禁止事項を守るため）
189:### 6. 報告する
217:#### 禁止領域に触れていないことを確かめる
231:#### 生成物が併合で衝突したとき
239:#### 報告を配布台帳へ送り返す
271:### 7. 禁止事項
294:### 8. 終える          ← 追加
339:## kind ごとの完了条件
```

既存の 1〜7 の見出しの文字列は変えていない。

- **0. 始める**: 読み取りだけの命令（現在の分岐、`status --porcelain --untracked-files=all`、`branch --list`、`ls-remote --heads`、`log --all -- tasks/<id>`、`ls -d`、`cat .sync-pause`）で状態を先に調べる。判定は 1 再開 → 2 分岐の重複（停止）→ 3 detached（停止）→ 4 汚れ（分類して利用者に選んでもらう）→ 5 清浄（task-start）→ 6 task-start の失敗（`[task-start] 完了。` が無ければ停止）の順。目印の表示（作成か実行前から存在か）を記録し、後者なら利用者に確かめる。手順書は居る分岐の版で動くことを `## 手順` の冒頭に一行書いた
- **汚れ**: 追跡下か未追跡か（`??`）、禁止領域か（`experiments/` `data/` `runindex/`）、大きさ（`du -sh`）の三つで分類する。選択肢は番号つきの文で示す（1 退避して task-start を一度だけやり直す／2 利用者が片付ける／3 中止）。退避の対象は、未追跡かつ禁止領域に属さないものだけ。repo の外の `~/m2-evacuated/<task_id>/` へ移し、消さない。禁止領域を外したのは、同期処理が全台へ配るため移すと他の台でも消えるからである
- **5. 実行する**: 無条件の `touch .sync-pause` と、手で外す `mv`／`rm` を消した。目印は task-start が所有の記録つきで置くと書き、task-start を経ない場合だけ同じ形（`printf 'task_id=%s\nbranch=%s\n' ... > .sync-pause`）で置く。存在だけを見る仕様、2026-08-11 の実測、外し忘れの警告、稼働版の確かめ（`grep -c sync-pause ~/bin/m2-sync.sh`）は残した
- **6. 報告する**: 末尾に「台帳へ送ったら『8. 終える』へ進む」を足した
- **7. 禁止事項**: 「目印を手で置かない・手で外さない（例外は二つ）」と「外した後に git の状態を変える操作をしない」を足した
- **8. 終える**: 完了（commit、push、PR、task-report の後）と中止（理由つき）の命令を書いた。同じセッションで続ける問い合わせでは呼ばないこと、前提を満たせないときに自分で中止へ切り替えないこと、前提 5 つ、状態 9 つの扱いの表、`OWNER_UNREADABLE` の分け方、外した後に git の状態を変えないこと、最後の応答で状態表示を伝えることを書いた
- **実装系について**: 「終了コードと状態表示に従った停止」とし、利用者の選択は番号つきの文で示して返事を待つと書いた（R4）

## D. 周辺の整合

- `tasks/README.md`: 中身の無い目印（`OWNER_UNREADABLE`）の扱いを、始めの task-start の表示で分ける形に直した（手順書の「8. 終える」と同じ）。「人が手で置いた目印 … この場合は手で外す」と読める文は、変更前の 1 件から 0 件になった
- `scripts/task_start.sh:148`: 案内文を `（報告まで終えたら make task-release TASK=<id> END=complete）` に変えた。変えたのは表示の文字列だけ。手順書の判定が読む `[task-start] .sync-pause を作成` と `[task-start] 完了。` は変わっていない
- 既存の試験: `test_task_start_pause_owner.py`、`test_task_release.py`、`test_sync_pause_ignore.py`、`test_check_spec.py`、`test_check_agent_docs.py` の 92 件が pass。案内文そのものを検査する試験は無かった

## 追加した試験

`tests/test_skill_task_doc.py`（3 件）:

1. 0 が 1 より前、既存の 1〜7 の見出しが順に在る、8 が 7 より後
2. 「8. 終える」の表の状態の集合と、`scripts/task_release.py` の `EXIT` の集合が両方向で一致する
3. 目印を手で置く・外す命令（`touch`、`rm -f`、`mv`、`>`）は、5 の「task-start を経ない場合だけ」の行と、8 の字下げした命令行にしか無い

対照:

| 入力 | 結果 |
|---|---|
| 改めた手順書 | 3 passed |
| 変更前の手順書 | 3 件とも落ちた |
| 表から `PREREQ_UNKNOWN` の行を消した写し | 2 だけが落ちた |
| 5 に無条件の `touch .sync-pause` を足した写し | 3 だけが落ちた |

## E. 隔離した場で辿る（G2）

台本は scratchpad の `sk/walk.py`。手順書から次の命令を正規表現で取り出し、そのまま実行した: 状態を調べる命令、task-start の命令、`make task-release ... END=complete`、`... END=abort REASON="<理由>"`。判定と扱いは手順書の順と表のとおりに書いた。
場は一時ディレクトリの bare な origin と複製。取り込みの段（`task-notion`）は Makefile で差し替え、`gh` は偽物、`task-release` の入口は実物の Makefile の行をそのまま写した。

```
== 始める段
清浄: 判定=5 清浄 / task-start exit=0 完了=True 目印の表示=作成 / 目印=在る(57B) 中身=['task_id=T-2026-10-07-walk-sample', 'branch=feat/walk-sample']
再開: 判定=1 再開 / 目印=在る(57B)
分岐の重複: 判定=2 分岐の重複（停止） / （対照）task-start を直に呼ぶと exit=2
遠隔だけの重複: 判定=2 分岐の重複（停止）
detached HEAD: 判定=3 detached HEAD（停止） / 現在の分岐の表示=''
汚れ: 判定=4 汚れ（分類して利用者へ。task-start を呼ばない） / 目印=無い（task-start を呼んでいない）
    ('README.md', '追跡下の変更', '-', '4.0K')
    ('experiments/run.log', '未追跡', '禁止領域', '4.0K')
    ('note.txt', '未追跡', '-', '4.0K')
    （対照）task-start を直に呼ぶと exit=2。分岐の重複と同じ終了コードだが、判定は分かれている
task-start の失敗: 判定=5 清浄 / exit=2 完了=False → 停止 / 巻き戻し後の分岐=phase0 目印=無い

== 終える段
完了: 始めの表示=作成 / task-release: RELEASED ... end=complete method=removed — 目印が存在しないことを確かめた → 扱い=終わり / 目印=無い
前提の欠け: task-release: PREREQ_MISSING ... 欠けている: 3 遠隔（遠隔に分岐が無い）。外さない → 扱い=前提を満たしてもう一度 / 目印=在る(57B)
    前提を満たしてもう一度: task-release: RELEASED ... / 目印=無い
OWNER_UNREADABLE（作成）: 始めの表示=作成 / OWNER_UNREADABLE → 扱い=手で外す / 目印=無い
OWNER_UNREADABLE（実行前から存在）: 始めの表示=実行前から存在 / OWNER_UNREADABLE → 扱い=外さず利用者へ / 目印=在る(0B)
中止: task-release: RELEASED ... end=abort method=removed reason="walk の中止" ... → 扱い=終わり / 目印=無い
```

- 「OWNER_UNREADABLE（作成）」の場は、変更前の task_start.sh（`c3ca48e3`）で始めた。中身の無い目印を「作成」と表示する場が作れる
- 実物の目印の sha256 の先頭は、辿る前後とも `e064c0a33cce7053`

**G2: pass。** すべての状態が手順書に書いた動作になった。

## F. 検証

- `make task-validate` は exit 0。`make forbidden-check` は pass（changed 7、違反 0）。`make spec-check TASK=...` は exit 0
- `agent-check`: 全体の違反は `docs/experiment_settings.md:155` の 1 件で、変更前と同じ。手順書だけ（`--path`）なら pass。対照として、読み込みを別の命令に分けた行を足した写しは fail（違反 1）
- `docs-check`: 不合格は変更前と同じ（`docs/proposal-gate.md:41` の 1 件。`diff` で差なし）
- 試験全体: `6 failed, 728 passed, 1 skipped, 2 errors`。開始前の 725 から増えた 3 件は追加した試験。失敗の名前の集合は開始前と同一
- `context/auto/*` と `tasks/inbox.md` は再生成しておらず、`*-check` も回していない（禁止 4）

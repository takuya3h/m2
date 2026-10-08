# RESULT — T-2026-10-08-doc-checks-clean-and-defect-log

実行ホスト `philip`（`hostname` は `aolab`）。分岐 `feat/doc-checks-clean-and-defect-log`。時刻は JST。
命令と出力の全文は `audit.md` に置く。

## 1. 判定

**verdict: pass**

- **G1 pass**: 手元の作業ツリーと新しく取得した作業ツリー（GitHub の origin から複製）の両方で、二つの検査の出力を全件記録した（`audit.md` A3・A4）
- **G2 pass**: 両方の作業ツリーで二つの検査が合格し、陽性対照（実在しない経路、分けた読み込み）はそれぞれ検出した（`audit.md` C1・C2）

解決された参照: `contract.conventions_rev` と `created_from.runindex_commit` は実測と一致した。`inject_verbatim`
（`conventions#prohibitions`、`conventions#issuer_cautions`）は本契約の操作の制約として読んだ。
`inputs.data` は雛形の必須項目であり、**本契約はデータを参照しなかった。**

## 2. 始める段（R6・R7）

- 利用者が送った命令: `/task T-2026-10-08-doc-checks-clean-and-defect-log` の一行だけ（モデル切り替えのため一度中断し、同じ一行を送り直した）。task-start を手で打っていない
- 判定した状態: **清浄**（分岐は `feat/skill-task-start-and-release`、汚れ 0 行、分岐の重複と契約の履歴は無し）
- 目印の表示: **作成**。中身は `task_id=T-2026-10-08-doc-checks-clean-and-defect-log` と `branch=feat/doc-checks-clean-and-defect-log` の 2 行（97 バイト、18:54:54 作成）
- 手順書どおりに働かなかった箇所: **無し**
- R7: philip の一時停止の記録は 2026-10-08 14:18:55 が最後で、15:18:58 に auto-merge が再開している。**一時停止が続いている記録は無い**（`audit.md` E1）

## 3. 完了判定

| # | 期待 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 手元で二つの検査が合格 | agent-check pass、docs-check 食い違いなし | 変更前の手元は各 1 件の不合格（A3） |
| b | 新しい作業ツリーで合格 | GitHub の複製に変更を写して両方合格（C2 の B1） | 変更前の同じ複製は agent-check 1 件、docs-check 7 件（A4 (1)） |
| c | 二つを変更後も検出 | 実在しない経路 `tools/no_such_tool.py` と、字下げの `source` の直後に `make` を置いた行を、それぞれ検出（C2 の C1） | 対照を足さない写し（B1）では検出しない |
| d | 手元のファイルの有無で同じ | 無し（B1）と有り（D1）でともに食い違いなし | 追跡下の `scripts/sync/m2-sync.sh` を退けた写しは、有り（D2）と無し（D3）のどちらでも同じ 1 件を検出 |
| e | 一件足し、出所を指す | `docs/issuer-defects.md` の「禁止と要求が両立しなかった」に一件。`T-2026-10-07-pause-release-tool-digest-relocate` RESULT §5-1 を指す | 変更前の一覧にこの識別子は 0 件 |
| f | 失敗の名前の集合 | 変更前と同一の 8 件（`diff` が空）。通過は 728 → 731（足した試験 3 件） | 名前で比べた（A5、E） |
| g | 始める段の記録 | §2 のとおり。目印の中身を値で記録 | 表示の文言だけでなく中身の 2 行を記録 |
| h | PR | #221。Draft でない、base `phase0` | 分岐名 `feat/doc-checks-clean-and-defect-log` |

`make forbidden-check` は pass（違反 0）。`task-validate` と `spec-check` も合格。

## 4. 実測と選んだ手段

| 検査 | 手元 前 → 後 | 新しい作業ツリー 前 → 後 |
|---|---|---|
| agent-check | 1 → 0 | 1 → 0 |
| docs-check | 1 → 0 | 7 → 0 |

- **R1（文書の側）**: `docs/experiment_settings.md` §1.10 の二行は選択肢であって連続した手順ではないが、並んだ字下げは読み手にも連続した命令に見える。系ごとに見出しの文で塊を分け、続く操作と同じ命令で読み込む形を一文で添えた。検査器の判定は変えていない。
  **検査が誤っていたとは判断しなかった。** 文書の書き方が曖昧だった
- **R2（文書の側）**: 雛形の経路を `docs/proposals/<YYYY-MM-DD>-<slug>.md` にした。読み手に置き場であることが分かり、
  既存の規則（`<` を含む記述は実在を約束しない）で対象外になる。外す印は使っていない
- **R3（検査器の側）**: `tools/check_docs.py` が `git check-ignore` で無視される経路を、在っても無くても対象外にする。
  手元のファイルの有無で結果が変わるのは「在るホストでだけ通る」ためであり、存在で判定する限り揃わない。
  `git check-ignore` は追跡下のファイルを無視されたことにしないため、版管理に在るはずの経路の検出は減らない（d の対照、試験）。
  `.gitignore` は変えていない
- 試験を 3 件足した（`tests/test_check_docs.py`）。`README.md` の検査の節に一段落を足した

## 5. 起票者の誤り

1. **check_does_not_check**: 完了判定 b の「新しく取得した作業ツリー」は取得元を定めていない。docs-check は分岐名を遠隔追跡の参照で除外するため、
   手元の repo から複製すると `OPERATION.md:84`（分岐名 `docs/plan-rewrite-2026-06`）が追加で 1 件出る（変更前 8 件、変更後 1 件）。
   GitHub から複製すると起票者の 7 件と一致した。判定 b は取得元しだいで結果が変わり、ホストに左右されないことを測りきれない
2. §2 の事実は実測とすべて一致した（行番号を含む）

## 6. 逸脱

- 新しい作業ツリーを二つの取得元で測り、GitHub の origin からの複製を判定に用いた。手元の repo からの複製は遠隔に分岐が揃わず、新しく取得した状態を代表しないため
- 新しい作業ツリーでの変更後の測定は、commit 前の 3 ファイル（`tools/check_docs.py`、`docs/proposal-gate.md`、`docs/experiment_settings.md`）を複製へ写して行った。README と欠陥の一覧はどちらの検査の結果にも影響しないため写していない（手元の最終状態で合格を確認）
- 試験全体は収集のエラー 2 件で中断するため、変更前後とも `--continue-on-collection-errors` を付けた
- 陽性対照 d には `scripts/sync/m2-sync.sh` を使った（`.claude/skills/task/SKILL.md:163` が参照する追跡下の経路）。複製の中で退けて戻し、手元の repo には触れていない

## 7. 想定外・UNKNOWN

- 手元の repo から複製した作業ツリーでは、変更後も docs-check が `OPERATION.md:84` の 1 件を出す。原因は無視されたファイルではなく遠隔追跡の参照（分岐の一覧）であり、本契約の範囲外として直していない。
  `git clone --single-branch` などでも同じことが起きうる
- 本契約の目印による一時停止の記録は、確認の時点（19:02）では次のループ待ちで、まだ出ていない
- 他のホストでの二つの検査の結果は測っていない（禁止事項 9）。UNKNOWN

## 8. 送出

- PR: #221（base `phase0`、head `feat/doc-checks-clean-and-defect-log`、`isDraft: false`、OPEN）。`gh pr create` は URL を返して成功
- `make task-report`: 送出後に結果を最後の応答で伝える（版管理には残らない）

# RESULT — T-2026-10-07-pause-release-tool-digest-relocate

## 判定

**verdict: pass。** G1・G2・G3 はすべて pass。実行ホストは `philip`（`hostname` は `aolab`）、分岐は `feat/pause-release-tool-digest-relocate`、起点は `origin/phase0` = `c3ca48e3`。実施は 2026-10-07 JST。命令と出力は `audit.md` にある。

## 1. 解決された参照

- `conventions_rev` と `runindex_commit` を実測した。どちらも記載と一致したので、`amendments` は空のまま（`audit.md` A6）。
- `inject_verbatim`: `conventions#prohibitions`（`context/conventions.md:98-107`）と `conventions#issuer_cautions`（`:150-187`）。原文はその行番号のとおり。本契約に効いたのは注意 1、3、4、8、11、12 である。
- `inputs.data` は**参照しなかった**。本契約はデータを読まない。

## 2. 完了判定

| # | 判定 | 実測 |
|---|---|---|
| a | 所有の記録 | 新たに置く目印の中身は `task_id=<id>\nbranch=<分岐>\n` になった。既存の目印（任意のバイト列）は sha256 が前後で一致した |
| b | 既存の振る舞い | 終了コード 2・2・3・3・4・4 と巻き戻しは変更前と同じ。変更前の版でも同じ 7 件が通り、所有の記録の 1 件だけが落ちた |
| c | 完了で外れる | 外す前に目印が在ることを確かめた。結果は exit 0 `RELEASED method=removed` で、目印は存在しない |
| d | 前提の欠け | 6 通りとも exit 30 `PREREQ_MISSING`。名指しされた前提は、それぞれ 1・2・3・4・4・5 だけだった |
| e | 確かめられない | `gh` の失敗と遠隔の照会の失敗は exit 31 `PREREQ_UNKNOWN` で、「確かめられない」と表示された。欠けている場合とは別の状態と別の文言になる |
| f | 中止 | 理由なし・空・空の文字だけ、の 3 通りは exit 2。理由があれば PR が無くても exit 0 で外れた。同じ場を完了で回すと 30 |
| g | 所有者 | 別の契約は 20、読めないものは 21 で、完了と中止の両方で外さなかった。**実物の目印（0 バイト）にも 21 `OWNER_UNREADABLE` を返し、外さなかった**（`audit.md` F6） |
| h | 位置 | 一致しなければ 22。一致する場では外れる（c） |
| i | 冪等 | 一度目は 0 `RELEASED`、二度目は 10 `ABSENT` |
| j | 削除の拒否 | `moved:.sync-pause.released.<id>` で外れた。目印は存在せず、`git status` にも出ない。移動も拒まれれば 40 |
| k | 副作用 | HEAD・分岐・index・stash・遠隔以外の refs・status が前後で一致した。分岐を一つ足すと差が出る |
| l | 抽出物の置き場 | 既定の出力先は `/home/ubuntu/claude-sync/session-digest/philip`。旧い置き場の新しいファイルは無視され、置き場の外のファイルは汚れに数えられる。追跡済みは 48 件のまま |
| m | 走査 | 旧い置き場に同名があれば作り直さず、新しい記録だけを書いた。旧い置き場から消すと書き出された |
| n | 試験 | 追加した 55 件はすべて pass。失敗の名前の集合（8 件）は開始前と同一。道具の判定を壊した版では、どの壊し方でも試験が落ちた |
| o | PR | #217。Draft ではなく、base は `phase0`、分岐は `feat/pause-release-tool-digest-relocate` |

## 3. 実測

- **道具の名前と入口**: `scripts/task_release.py` と `make task-release TASK=<id> END=complete|abort [REASON="..."]`
- **状態表示と終了コード**:

  | 状態 | 終了コード |
  |---|---:|
  | `RELEASED` | 0 |
  | `USAGE` | 2 |
  | `ABSENT` | 10 |
  | `OWNER_MISMATCH` | 20 |
  | `OWNER_UNREADABLE` | 21 |
  | `POSITION_MISMATCH` | 22 |
  | `PREREQ_MISSING` | 30 |
  | `PREREQ_UNKNOWN` | 31 |
  | `RELEASE_FAILED` | 40 |

  表示は一行で、`task-release: <状態> task=<id> [end=..] [method=..] — <詳細>` の形。`make` 経由では失敗の終了コードが 2 に潰れる。
- **目印の中身の形**: `task_id=<識別子>` と `branch=<分岐名>` の 2 行（`key=value`）。m2-sync.sh も keeper も中身を読まない（`audit.md` A5）。
- **抽出物の新しい置き場**: `~/claude-sync/session-digest/<ホスト名>/<日付>-<識別子>.md`。ホスト名は `SERVERNAME` → `.servername` → `hostname` の順。共有フォルダが無いホストでは何も書かず、exit 0 で終える。
- **走査の件数（このホスト）**: 第二の実装系の記録は 2 件。書き出しは 0 件で、作り直さなかったものが 1 件（旧い置き場に在り追跡済み）、中身が無いものが 1 件。
- **追跡済みの抽出物**: 開始前 48 件、変更後 48 件。
- **試験**: 開始前は `6 failed, 670 passed, 1 skipped, 2 errors`。変更後は `6 failed, 725 passed, 1 skipped, 2 errors`。

## 4. 後続の契約へ（SKILL.md の改訂）

- 契約の終わりの解除は `make task-release TASK=<task_id> END=complete` で行う。PR を起票し、`make task-report` を送った後に実行する。
- 中止は `make task-release TASK=<task_id> END=abort REASON="<理由>"`。理由は必須で、PR が無くてよい。
- 結果は一行の状態表示で判定する。`RELEASED` と `ABSENT` は外れた状態、それ以外は外していない。`PREREQ_MISSING` は欠けた前提を名指しし、`PREREQ_UNKNOWN` は照会の失敗を示す。
- **本契約より前の `task_start.sh` が置いた目印（中身なし）は `OWNER_UNREADABLE` で外れない。** その場合だけ、現行の手順書の方法（`rm -f` か `mv`）で外す。
- 抽出物は `~/claude-sync/session-digest/` にある。SKILL.md と手順に `git add docs/sessions/digest/` が残っていれば消す。

## 5. 起票者の誤り

1. **self_contradiction**: §4 Task F の 6 は、解除を報告と送出の後に置き、「解除の後に git の操作をしない」と定める。一方で、完了判定 g は実物の目印に対する陰性対照を報告に含めることを求める。書かれた順のまま実行すると、陰性対照の結果は報告に入らない。本契約では、陰性対照（外さない操作）を commit の前に取り、解除だけを最後に回した。
2. **§2 の事実**は、実測とすべて一致した（行番号のずれは `:280` と実際の `:281` の 1 行だけ）。

## 6. 送出

- 検証: `task-validate` は exit 0。`forbidden-check` は pass（違反 0）。`spec-check TASK=...` は exit 0。
- 禁止語: 送出物 4 件、変更した文書・コードの追加行、追加したコードと試験に当てた。初回は audit.md に 1 語、tasks/README.md の追加行に 1 語が一致した（後者は元の本文の表現を引き継いだもの）。言い換えた後は全件 0。陽性対照（禁止語を 2 語含む合成文）は検出した。
- 秘匿: 同じ 16 件に `scan_secrets` を、資格情報を環境に読み込んだうえで当て、0 件だった。陽性対照（鍵の形の合成文字列と、合成した環境値の照合）はどちらも検出した。出力は種別だけ。

- push は exit 0。PR は **#217**（base `phase0`、Draft ではない）。台帳への送り返しは `make task-report` で行う。抑止の解除は、報告と送出の後に、手順書の方法で行う。その結果は版管理に残らない（§5 の 1）。

## 7. 逸脱

- **判断**: 実物の目印に対する陰性対照（Task F の 6 の前半）を、commit の前に行った。外さない操作であり、結果を報告に含めるためである（§5 の 1）。
- **判断**: 道具を Python で書き、`scripts/` に置いた（`task_release.py`）。試験から関数として呼べ、`gh` の JSON を読めるためである。依存は標準ライブラリだけ。
- **判断**: 走査が抽出済みかを判定するとき、旧い置き場の内容ではなく名前の有無だけを見る。旧い書式の抽出物を未抽出と取り違えると、過去分が一斉に書き出されるためである。そのため、置き場を移す前に抽出した記録のセッションが移した後も続いた場合、続きは新しい置き場に書き出されない。
- **環境**: 試験全体は、収集のエラー 2 件があると中断する。開始前と変更後の両方で、`--continue-on-collection-errors` を付けて回した。

## 8. 想定外・UNKNOWN

- `make docs-check`（`docs/proposal-gate.md:41`）と `make agent-check`（`docs/experiment_settings.md:155`）がそれぞれ 1 件で落ちる。どちらも本契約で触れていないファイルにある。
- 他のホストでの動作（共有フォルダが無いホスト、`.servername` が無いホスト）は、試験の場では確かめた。実機では UNKNOWN。
- 終了フックが実際に新しい置き場へ書くことは、本セッションの終了時に初めて起きる。報告の時点では UNKNOWN。

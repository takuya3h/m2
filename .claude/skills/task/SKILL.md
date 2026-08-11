---
name: task
description: tasks/<task_id>/ の契約を解決・検証・実行する。ユーザーが「/task <task_id>」または「この task を実行して」と言ったときに使う。
---

# task — TASK 契約の実行

## 実装系について

この手順は実装系に依存しない。Claude Code では `/task <task_id>`、
Codex では `$task` または本ファイルを読ませることで同じ手順を実行できる。

検査は `make task-validate` と `make task-preflight` が行う。
**判断を実装系に委ねる箇所は無い。** 手順書が求めるのはコマンドの実行と、
終了コードに従った停止だけである。

## 使い方

    /task T-YYYY-MM-DD-slug

## 手順（この順序を変えない）

### 1. 読む

- `tasks/<task_id>/spec.yaml`
- `tasks/<task_id>/SPEC.md`
- `kind: exp` なら `tasks/<task_id>/prereg.md`

契約が `tasks/<task_id>/` に無い場合、配布台帳から取得する。

    source scripts/load_env.sh    # 資格情報が要る
    make task-notion TASK=<task_id>

取得と検証までを行う。失敗したらそこで停止し、出力をそのまま報告する。
**本文の要約値が一致しない場合は取り込まない。** 台帳が本文を改変した可能性がある。

### 2. 検証する（L1 + L2）

    make task-validate TASK=<task_id>

**exit != 0 なら、ここで停止して報告する。** 修正を推測で行わない。
WARN が出た場合は、内容をユーザーに提示してから続行の可否を尋ねる。

### 3. 参照を解決する

| spec の記載 | 解決先 |
|---|---|
| `inputs.denominator.ref` | `runindex/experiments.csv` から実測値・n_seeds・split を取得 |
| `inputs.sigma_policy`（省略時） | `context/conventions.md#sigma` の既定値を継承 |
| `inputs.frozen_source.ref` | ckpt の sha256 を照合 |
| `contract.inject_verbatim` | `context/conventions.md` の該当アンカーの**原文** |

解決結果は `RESULT.md` の「1. 解決された参照」に記録する。
**要約してはならない。原文をそのまま使う。**

### 4. L3 プリフライト（実行直前）

    make task-preflight TASK=<task_id>

**終了コードが 0 でなければ、ここで停止して報告する。** 出力をそのまま提示すること。
検査項目を自分で判断してはならない。何を検査するかは契約と検査器が決める。

`SKIP` は「合格」ではなく「実行されなかった」を意味する。SKIP された項目があれば、
その一覧を報告に含める。

`P6 decisions_answered` が FAIL なら、出力に列挙された項目をユーザーへ提示して停止する。
**自分で決めてはならない。**

### 5. 実行する

#### 実行前に自動同期を止める（契約の禁止事項を守るため）

常駐する `m2-sync.sh` は 30 分ごとに **実行者の操作なしで作業分岐へ `origin/phase0` を
統合し、push し、Draft PR を作る。** 契約は「統合しない / 自動統合を有効化しない」を
禁止事項に置くため、実行者がどれだけ気を付けても守れない。実際に統合された記録がある
（`~/claude-sync/sync-alerts.log` の `auto-merge: feat/canonical-index-refresh <- origin/phase0`）。

**目印のファイルを置いて止める。**

    touch .sync-pause             # 実行前に置く

置いてある間、`m2-sync.sh` は分岐へ一切書き込まず、毎ループ記録だけ残す。
常駐処理そのものは止まらないので、消せば次のループから元に戻る。
目印は `.gitignore` 済みで、同期の総取り規則 `**` にも落ちるため **その 1 台にだけ効く。**

    rm -f .sync-pause             # 報告まで終えたら必ず消す

🔴 **消し忘れると、そのホストだけ自動同期が止まったままになる。** 他ホストの更新が
入らず、commit も push されない。止まっていることは記録に出る。

    grep '一時停止中' ~/claude-sync/sync-alerts.log | tail -3

**この抑止は `origin/phase0` に届いてから効く。** keeper は毎ループ `origin/phase0` から
`~/bin/m2-sync.sh` を自己更新するため、phase0 に無い版は稼働中の常駐処理に反映されない。
届く前は目印を置いても止まらない。稼働中の版が対応済みかは次で確かめる。

    grep -c sync-pause ~/bin/m2-sync.sh    # 0 なら未対応

- `plan.phases` の順に実行する。
- `plan.gates` は `after` で指定されたフェーズの直後に評価する。
  - `on_fail: stop` — 停止して報告
  - `on_fail: ask` — ユーザーに判断を求める
  - `on_fail: skip` — 以降のフェーズを飛ばして報告
- `outputs.stamp.task_id_in` が指定されていれば、生成される設定ファイルに
  `task_id` を書き込む。これが指示書と run を結ぶ唯一の鍵である。

### 6. 報告する

報告は 2 つ書く。**同じ結果を、人が読む形と機械が読む形で別々に書く。**

| ファイル | 何を書くか |
|---|---|
| `tasks/<task_id>/RESULT.md` | 散文。解決した参照、判断の理由、実測の経緯 |
| `tasks/<task_id>/result.yaml` | 事実だけの対。様式 `tasks/_schema/result.schema.json`、雛形 `tasks/_templates/result.yaml` |

散文から値を機械で抜こうとしない。**書き手が最初から対で書く。**
`issuer_defects` を空にしない。型は `check_does_not_check`
`asserted_without_measuring` `self_contradiction` `shell_assumption` の 4 語である。

書いたら投影に現れることを確かめる。

    make taskindex         # context/auto/tasks_summary.csv と followups.md を生成
    make taskindex-check   # 差分が無ければ exit 0

**`deviations` セクションを空にしてはならない。** 指示書どおりに実行できなかった箇所、
自分で判断した箇所を必ず書く。逸脱が無い場合は「なし」と明記する。
このセクションが次の指示書の品質を決める。

対話で出た判断は、**その契約の記録へ 1 行で置く。**

    tasks/inbox.d/<task_id>.md

集約結果 `tasks/inbox.md` は `make inbox` が生成する。**手で編集しない。**
契約ごとに別のファイルへ書くため、並行して進む契約が同じ場所を書き換えず、
併合しても元の記録は衝突しない。集約結果が衝突した場合は再生成すれば解消する。

**1 契約 = 最低 1 行。** 置くものが無い場合も「なし」と書いた行を残す。
書式は `tasks/README.md` の「判断の受け皿」を参照。

### 7. 禁止事項

- 検証エラーを推測で修正しない
- `decisions_required` を自分で決めない
- 未測定の値を書かない（UNKNOWN と書く）
- `runindex/` を手で編集しない
- `tasks/inbox.md` を手で編集しない（`tasks/inbox.d/` へ書く）
- 数値を捏造しない

## kind ごとの完了条件

| kind | 完了条件 |
|---|---|
| `impl` | `outputs.acceptance` が全て充足し、テストが通り、commit 済み |
| `exp` | `expected_runs` の run が生成され、`make runindex` 後に index.csv に task_id 付きで現れる |
| `analysis` | `outputs.destination` にレポートが生成され、数値の出所が全て実測である |

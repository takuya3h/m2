# L3 P13 を完了済み契約で SKIP にし、result.yaml の型に二型を足す

**task_id:** T-2026-09-19-p13-skip-and-enum  **kind:** impl

## 1. 背景

T-2026-09-19-symmetry-gate（PR #186）で L3 に P13 `symmetry_table_complete` が入った。実測で、**完了済みの exp 契約 12 件が
すべて P13 で FAIL になる**（prereg に対称性の表が無い）。関門の意図は「これから起票する契約」に対するもので、
過去の契約の再現や追試を妨げる意図は無い。利用者の決定（2026-09-19）: **完了済み契約は P13 を SKIP する。**

同契約で `docs/issuer-defects.md` に 2 型（`asymmetric_comparison`、`rule_read_narrowly`）を足したが、
`tasks/_schema/result.schema.json` の enum は 4 語のまま。利用者の決定: **enum に足す。**

**本契約では GPU を使用しない。**

## 2. 確定した事実（ホストによらない値だけ）

- P13 は `tools/preflight_task.py` にある（前契約の実測）。exp 以外は SKIP、exp は prereg の表を列名で探す
- 完了済み契約は `tasks/TASK_ID/result.yaml` を持ち、`verdict` が入っている。未完了はこのファイルが無いか verdict が空
- `result.schema.json` の `issuer_defects[].type` の enum は 4 語（`asserted_without_measuring`、`self_contradiction`、`check_does_not_check`、他 1 語。実測で確かめる）
- `docs/issuer-defects.md` の型の一覧に「`result.yaml` の enum には未追加」の注記がある（前契約が残した）
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装を読んで決めてよい。**

### Task A — 開始状態

1. 作業ツリーの清浄、HEAD が phase0。未追跡は移動で退避（拒まれたら残して要約値を記録）
2. P13 の現行の判定の流れを読み、記録する。完了済み exp 契約の一覧（result.yaml と verdict を持つもの）を機械で数える
3. enum の現行の語を記録する。既存の result.yaml 全件が schema を通ることを確かめる（変更前の基準）
4. `conventions_rev` と `runindex_commit` を実測し占位を差し替える

### Task B — 変更

1. P13 に「完了済み」の判定を足す。**判定は `tasks/TASK_ID/result.yaml` の実在と `verdict` の有無だけで行う。** 名前の部分一致・日付・台帳は使わない。
   完了済みなら SKIP とし、理由に「完了済み（result.yaml に verdict あり）」と出す。未完了の exp は従来どおり
2. `result.schema.json` の enum に `asymmetric_comparison` と `rule_read_narrowly` を足す。既存の語は変えない
3. `docs/issuer-defects.md` の「enum には未追加」の注記を消す（それ以外は触らない）

### Task C — 検証と報告

1. 対照: 完了済み exp 1 件で SKIP／未完了 exp（雛形から作った一時契約）で FAIL／表を埋めた一時契約で PASS／
   result.yaml を verdict なしにした一時契約で FAIL（完了済みと誤認しない）。**部分一致の対照**: task_id が完了済み契約の名前を含む未完了の一時契約で FAIL
2. schema: 既存 result.yaml 全件が通る。二型を使った一時 result.yaml が通る。未知の型 `zz_unknown` が落ちる
3. L1、L2、`make forbidden-check`、`make spec-check TASK=T-2026-09-19-p13-skip-and-enum`、試験
4. 完了判定 a〜g を実測で埋める。`RESULT.md`、`result.yaml`、`audit.md`、`tasks/inbox.d/`、`notes.md`（変更の要点）
5. commit、push、**PR の base は phase0**。分岐名 `feat/p13-skip-and-enum`。`.sync-pause` を移動で解除

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. `tools/check_spec.py` の規則を増減しない
2. P1〜P12 の番号・順序・挙動を変えない。P13 の未完了 exp に対する挙動を変えない
3. 過去の契約の prereg・result.yaml を書き換えない
4. `context/conventions.md`、`context/auto/*`、`tasks/inbox.md`、`experiments/**`、`data/**`、`runindex/**` に触れない
5. 開始前から在る未追跡を消さない
6. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 完了済み exp で SKIP | 理由に完了済み | 完了済み 12 件全件で SKIP。件数を記録 |
| b | 未完了 exp は従来どおり | 表なし FAIL、UNKNOWN FAIL、揃う PASS | 前契約の 6 種の入力で同じ結果 |
| c | 判定の方法 | result.yaml の実在と verdict のみ | verdict を消した一時契約で FAIL。名前が完了済みを含む未完了で FAIL |
| d | enum | 二型が通り、未知が落ちる | 既存 result.yaml 全件の件数と通過数が一致 |
| e | 注記の削除 | 注記が 0 件 | 変更前は 1 件（行番号） |
| f | 試験と規則数 | 失敗数不変、規則数不変 | 変更前の数を Task A で記録 |
| g | PR | 番号、base phase0 | 分岐名 |

## 6. 想定外と停止条件

- 完了済みの印が result.yaml 以外に要る → 停止して諮る
- 既存 result.yaml に schema を通らないものがある（本契約と無関係）→ 触らず記録し、そのまま続ける
- 実行基盤が書き込みや `mv` を拒む → 回避せず提示

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。判定／完了判定／実測（完了済み件数、enum の前後、対照の結果）／起票者の誤り／逸脱／想定外／送出。

## 8. 申し送り

- 本契約は GPU を使わない。他の契約と並行可。生成物は `tools/preflight_task.py`、schema、issuer-defects.md、試験
- 三周目の工程塔（exp）は本契約と無関係に起動できる（未完了なので P13 は従来どおり働く）

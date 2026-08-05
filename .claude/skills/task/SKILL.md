---
name: task
description: tasks/<task_id>/ の契約を解決・検証・実行する。ユーザーが「/task <task_id>」または「この task を実行して」と言ったときに使う。
---

# task — TASK 契約の実行

## 使い方

    /task T-YYYY-MM-DD-slug

## 手順（この順序を変えない）

### 1. 読む

- `tasks/<task_id>/spec.yaml`
- `tasks/<task_id>/SPEC.md`
- `kind: exp` なら `tasks/<task_id>/prereg.md`

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

| 検査 | 落ちる事故 |
|---|---|
| `plan.env.venv` が activate されている | CUDA 拡張の無言フォールバック |
| `preflight` の各項目（cuda_ext_loaded / deterministic_flags） | 同上・非決定性 |
| `kind: exp` かつ `prereg.commit` が学習開始より前 | 結果を見てから予測を書く |
| `governance.decisions_required` が空、または回答済み | CLI の越権 |
| `outputs.destination` に書き込み権限がある | 実行後の書き込み失敗 |

**1 つでも赤なら GPU を 1 本も回さない。**

`decisions_required` が未回答なら、その項目をユーザーに提示して停止する。
自分で決めてはならない。

### 5. 実行する

- `plan.phases` の順に実行する。
- `plan.gates` は `after` で指定されたフェーズの直後に評価する。
  - `on_fail: stop` — 停止して報告
  - `on_fail: ask` — ユーザーに判断を求める
  - `on_fail: skip` — 以降のフェーズを飛ばして報告
- `outputs.stamp.task_id_in` が指定されていれば、生成される設定ファイルに
  `task_id` を書き込む。これが指示書と run を結ぶ唯一の鍵である。

### 6. 報告する

`tasks/<task_id>/RESULT.md` を埋めて commit する。

**`deviations` セクションを空にしてはならない。** 指示書どおりに実行できなかった箇所、
自分で判断した箇所を必ず書く。逸脱が無い場合は「なし」と明記する。
このセクションが次の指示書の品質を決める。

### 7. 禁止事項

- 検証エラーを推測で修正しない
- `decisions_required` を自分で決めない
- 未測定の値を書かない（UNKNOWN と書く）
- `runindex/` を手で編集しない
- 数値を捏造しない

## kind ごとの完了条件

| kind | 完了条件 |
|---|---|
| `impl` | `outputs.acceptance` が全て充足し、テストが通り、commit 済み |
| `exp` | `expected_runs` の run が生成され、`make runindex` 後に index.csv に task_id 付きで現れる |
| `analysis` | `outputs.destination` にレポートが生成され、数値の出所が全て実測である |

# RESULT — T-2026-08-13-implementation-history-index

| 項目 | 値 |
|---|---|
| host | lecun |
| branch | `feat/implementation-history`（`origin/phase0` = `d01ff10` から作成） |
| status | pass |
| ゲート | G1 pass / G2 pass / G3 pass |
| 試験 | 開始前 5 failed / 271 passed → 完了時 5 failed / 292 passed |
| commits | `9a2e2fc` `8254d6a` `48a6b66` `b2675e3` |

構造化された対は `result.yaml` にある。**本 task がこの様式の最初の利用者である。**

---

## 1. 解決された参照

### `conventions#prohibitions`（原文）

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `conventions_rev` の差分

| 起票時 | 実測 | 措置 |
|---|---|---|
| `1201f4f` | `d422b08` | 置換した（SPEC Task 4 Step 1 の手順であり逸脱ではない） |

`d422b08` は `context/conventions.md` を最後に変更した commit（2026-08-07,
"docs(context): backfill the changelog sha for the frozen-source scope note"）。

### 検証時の WARN（2 件・いずれも続行可）

    WARN [L2-8] index.csv: 起票時 749 → 現在 751（分母が動いています）
    WARN [L2-8] experiments.csv: 起票時 206 → 現在 207（分母が動いています）

本 task は分母を使う解析を行わないため、判断に影響しない。

---

## 2. Phase A — 様式と、それに加えた検査

`tasks/_schema/result.schema.json`（draft 2020-12, `additionalProperties: false`）と
`tasks/_templates/result.yaml` を作り、`tools/validate_task.py` に 3 検査を足した。

| id | 検査 |
|---|---|
| L1-6 | 様式に沿わない記述（未知の誤りの型・不正な `result_version`・不正なゲート判定） |
| L1-7 | `task_id` がディレクトリ名と一致しない |
| L1-8 | `status` が `partial`/`stopped` なのに `unknowns` も `followups` も空 |

**対を持たない契約は失敗にしない。** `load_result()` はファイルが無ければ `None` を返し、
検査そのものを行わない。既存 23 契約は `0 failed` のまま（実測）。

### G1 — 双方向で確認した

| 例 | 期待 | 実測 |
|---|---|---|
| 正しい記述 | 通る | exit 0 / `OK` |
| `task_id` がディレクトリ名と違う | 拒む | `[L1-7]` |
| 未知の誤りの型 | 拒む | `[L1-6]` |
| 不正な `result_version` | 拒む | `[L1-6]` |
| 不正なゲート判定 | 拒む | `[L1-6]` |
| `stopped` なのに理由が無い | 拒む | `[L1-8]` |
| 対が存在しない | 失敗しない | exit 0 |

試験 `tests/test_result_schema.py` 13 件。**先に書いて RED を確認してから実装した。**

---

## 3. Phase B — 投影の列と、既存の投影との関係

`make taskindex` が `result.yaml` と `spec.yaml` から 2 ファイルを生成する。

| 出力 | 内容 |
|---|---|
| `context/auto/tasks_summary.csv` | 1 契約 1 行 |
| `context/auto/followups.md` | 申し送りの転記、断定できなかった事項、誤りの型の件数 |

列は 16。`task_id` `kind` `status` `host` `pr` `merged` `gates_pass` `gates_ask`
`gates_stop` `tests_before_failed` `tests_after_failed` `deviations`
`n_issuer_defects` `n_followups` `n_unknowns` `depends_on`。
`kind` と `depends_on` は契約側から、他は対から取る。

**散文（RESULT.md）は読まない。** 解析して要約を作ると捏造を生むため、読むのは
構造化された対と契約だけにした。**壁時計も使わない**（`build_inbox.py` と同じ方針）。
日時が混ざると `--check` が「手による編集」と「時刻の経過」を区別できなくなる。

### 既存の投影との関係（Step 7）

`context/auto/` は `build_context.py` と共有する。**変更前に実測した**ところ、
既存の検査は未知のファイルを差分として数えた。

    context/auto/ に未知のファイルを置くとどうなるか
    検査器の exit=1
    === _probe_unknown.csv ===
    (再生成すると存在しなくなる)
    差分あり: _probe_unknown.csv

原因は `check()` が `existing | fresh` を走査していたこと。
**各生成器が自分の出力だけを検査する**ように `build_context.py` を直した
（`fresh` のみを走査）。`build_taskindex.py` も同じ方針で書いた。

| 検査 | 見るもの |
|---|---|
| `make context-check` | `build_context.py` が生成する 4 ファイル |
| `make taskindex-check` | `tasks_summary.csv` と `followups.md` の 2 ファイル |
| `make inbox-check` | `tasks/inbox.md` |

実測: `make context` exit 0 → `make context-check` exit 0 → `make taskindex-check` exit 0。
`make context` を実行しても taskindex 側の検査は 0 のまま。

### G2 — 冪等と、陽性対照

| 確認 | 実測 |
|---|---|
| 2 回生成して md5 が一致 | 一致 |
| `taskindex-check` | exit 0 |
| `followups.md` へ手で 1 行足す | 検査器 exit 1（`make` は exit 2） |
| 再生成 | exit 0 に復帰 |
| `tasks_summary.csv` へ手で 1 行足す | 検査器 exit 1 |
| 再生成 | exit 0 に復帰 |

**陽性対照は 2 ファイルとも実際に失敗させて確認した。** 試験
`tests/test_build_taskindex.py` 8 件（壁時計が出力に混ざらないことの検査を含む）。

---

## 4. Phase C — 編集が消えることの実測と、直し方を選んだ理由

### 4-1. 消えることの実測（直す前）

平文を控えたうえで印の行を足し、パイプを挟まずに読み込んだ。

| 段階 | 印の数 |
|---|---|
| 印を足した直後 | 1 |
| `source scripts/load_env.sh` の後 | **0** |

`.env.gpg` の md5 は前後で一致。**編集は平文側でのみ失われる。**

### 4-2. 平文を読む他の箇所（推奨案を採らなかった理由）

SPEC の推奨は「復号先を平文の設定ファイル以外にする」だった。
**実装を数えたところ、平文 `.env` を読む実行コードが 34 箇所ある。**

| 種別 | 例 |
|---|---|
| 実験起動スクリプト | `scripts/run_b2a_*.sh` `run_t1a_*.sh` `run_l1_2_*.sh` `run_s0.sh` ほか 28 本 |
| フック | `.claude/hooks/auto_notion_sync.py:62` |
| 後処理 | `post_process_detrex.py` `post_process_relation_detr.py` `post_process_sensex_codino.py` |
| 通知・補填 | `notify_experiment.py` `wandb_backfill_detectron2.py` |

いずれも `[ -f .env ] && { set -a; source .env; set +a; }` 型の **fail-open** である。
復号先を移すと、**エラーを出さずに**資格情報が載らなくなり、W&B と Notion の自動記録が
静かに no-op 化する。同型の事故はこのリポジトリで既に起きている（`s0_010-012` の env 漏れ。
`docs/notion_run_ledger_auto_post.md`）。よって**置き場は変えず、扱いを変える**方針にした。

「警告に留める案」も単独では採れない。判定 11 が「印が残る」を要求するため、
上書きを続けたままでは満たせない。**上書きしない + 警告する**の両方が要る。

### 4-3. 直したこと（書き出し先の扱いだけ）

復号を一時ファイル（`umask 077` で作成）へ行い、

- 平文が無い → そのまま `.env` にする
- 平文が暗号文と同じ → 一時ファイルを消すだけ
- 平文が暗号文と違う → **上書きせず警告する**（両方の直し方を出力する）

復号の手順・変数の設定方法・完了時の文言には触れていない。

**副次的に見つかった 2 つめの欠陥。** 従来はリダイレクトが `gpg` より先に走るため、
復号に失敗すると `.env` が空になり、続く `rm -f` で消えていた。実測:

| 版 | 誤ったパスフレーズで読み込んだ結果 |
|---|---|
| 修正前 | **`.env` が消えた** |
| 修正後 | `.env` は残った（33 行） |

権限も変わった。従来のリダイレクトは umask 002 のもとで **664**（誰でも読める平文の
資格情報）を作っていた。修正後は **600**。ただし**新規作成時だけ**である。

### 4-4. G3 — 両方向の確認（パイプを挟んでいない）

| 向き | 版 | 印 | 資格情報 |
|---|---|---|---|
| 順 | 修正後 | **残った**（1 個） | `WANDB_API_KEY=set` / `NOTION_API_KEY=set` |
| 逆 | 修正前（`HEAD` 版） | **消えた**（0 個） | 同上 |

`HEAD` 版は zsh 対応を含み直接リダイレクトのままであるため、対照は本 task の変更だけを
切り出している。**修正前で印が残っていないことを確認済み**（対照は有効）。
zsh と bash の双方で順方向を実測した。`.env.gpg` の md5 は全工程を通じて不変。

### 4-5. 後始末

印を削除し、`.env` が控えとバイト一致することを確認したうえで控えを削除した。
`git check-ignore .env` は IGNORED、`git status` に `.env` は現れない。
一時ファイル `.env.tmp.*` の残存は 0 個。

### 4-6. 文書化

`docs/secrets_and_tracking.md` に「編集と再暗号化の順序」を追加した。
**編集 → 再暗号化 → commit → 読み込み直し**の順であること、警告が出たときに
どちらを正とするかを選ぶこと、放置するとそのホストだけ古い資格情報で走り続けることを書いた。

---

## 5. 完了判定

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 様式が定義された | スキーマが存在 | `tasks/_schema/result.schema.json` |
| 2 | 正しい記述が通る | 通る | exit 0 |
| 3 | 誤った記述が拒まれる | 拒まれる | 5 例すべて拒否 |
| 4 | 対が無くても失敗しない | 失敗しない | exit 0 / 既存 23 契約 0 failed |
| 5 | 投影が生成される | 2 ファイル | `tasks_summary.csv` `followups.md` |
| 6 | 投影が冪等 | 一致 | md5 一致 |
| 7 | 手による編集を検出 | 非ゼロ から 0 | 2 ファイルとも確認 |
| 8 | 申し送りが集約される | 件数が 1 以上 | 5 件 |
| 9 | 誤りの型が数えられる | 表がある | 4 型の表・合計 3 件 |
| 10 | 既存の投影が壊れていない | `context-check` が exit 0 | exit 0 |
| 11 | 編集が消えない | 印が残る | 残った |
| 12 | 修正前は消える | 陰性対照が働く | 消えた |
| 13 | 資格情報が従来どおり読める | 両方とも設定あり | 両方 set |
| 14 | 暗号化された設定が不変 | 差分が空 | md5 一致 |
| 15 | 平文が版管理外 | 追跡されていない | IGNORED |
| 16 | 本 task の対がある | 投影に現れる | 現れた |
| 17 | 契約検証が通る | exit 0 | exit 0（WARN 2） |
| 18 | 実行前検査が通る | exit 0 | 4 PASS / 4 SKIP / 0 FAIL |
| 19 | 試験が不変 | 開始前を先に測る | 5 failed のまま・271 → 292 passed |
| 20 | 禁止領域が無変更 | 出力なし | `runindex` `experiments` `transfer` `data/splits` `src` すべて出力なし |

### preflight で SKIP された項目（合格ではない・実行されていない）

| 項目 | 理由 |
|---|---|
| P2 `cuda_ext_loaded` | `plan.env.preflight` に記載なし |
| P3 `deterministic_flags` | `plan.env.preflight` に記載なし |
| P4 `prereg_committed` | `kind=impl` のため対象外 |
| P5 `frozen_source_hash` | `kind=impl` のため対象外 |

### 判定 20 についての注記

`context/auto/` には新しい 2 ファイルが現れる。これは `make taskindex` による生成物で
あり、禁止 6 が禁じる「手で編集する」には当たらない。再生成して一致することを
`make taskindex-check` の exit 0 で示している。

---

## 6. 起票者の誤り（3 件）

| 型 | 内容 |
|---|---|
| `self_contradiction` | 禁止 6 が `context/auto/**` を挙げる一方で Task 2 は同じ場所へ生成させる。判定 20 を素直に読むと自分の成果物で不合格になる |
| `self_contradiction` | 判定 10 が `context-check` の exit 0 を要求するが、Files に `tools/build_context.py` が無い。既存の検査は `context/auto/` の全ファイルを走査するため、変更なしでは必ず非ゼロになる |
| `asserted_without_measuring` | Task 3 Step 2 の推奨（復号先の変更）は、平文を読む 34 箇所を数えると採れない。すべて fail-open のため無言で資格情報が載らなくなる |

`conventions_rev` のずれは SPEC が手順として定めているため、誤りに数えていない。

---

## 7. deviations（指示書どおりにしなかった箇所・自分で判断した箇所）

1. **`tools/build_context.py` を変更した。** SPEC の Files に無い。判定 10
   「`context-check` が exit 0」は、この変更なしでは達成できない（未知のファイルを
   差分と数える挙動を実測済み）。変更は検査範囲を自分の出力に絞る 1 箇所のみ。

2. **Task 3 で推奨案を採らなかった。** 「復号先を平文の設定ファイル以外にする」ではなく
   「上書きしない + 警告する」を選んだ。理由は §4-2。SPEC は
   「平文を読む他の箇所があるかを実装から確かめてから決める」としており、確かめた結果である。

3. **SPEC に無い測定を 1 つ追加した。** 復号に失敗したときに平文が消えるかどうかを、
   修正前後の両方で測った（§4-3）。`load_env.sh` の書き出し先の扱いを変える以上、
   失敗経路も変わるため、断定する前に測る必要があった。

**逸脱は以上 3 件。**

---

## 8. 残った課題

`result.yaml` の `followups` に転記した。投影 `context/auto/followups.md` にも現れる。

1. 配布台帳の本契約の行は、本文が markdown として解釈されて壊れたままである。
   要約値の照合が働いて取り込みは拒まれた。起票者がコードブロックとして貼り直すこと。
2. 他ホストの `.env` は本修正より前に作られている。鍵を更新すると警告が出るので、
   `rm .env` して再実行するか再暗号化するかを必ず選ぶこと。
3. 平文 `.env` の権限が 600 になるのは新規作成時だけ。既存ホストは 664 のまま。
4. `context/auto/` は 2 つの生成器が共有する。生成器を足すときは自分の出力だけを検査すること。
5. `tests/test_branch_naming.py` に既存の ruff 指摘 I001 が 1 件。本 task では触れていない。

### 断定できなかったこと

他ホスト（lecun 以外）では `load_env.sh` の修正を実行していない。
lecun 上の zsh と bash の双方でのみ実測した。

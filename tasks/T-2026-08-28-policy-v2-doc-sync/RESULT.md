# RESULT — T-2026-08-28-policy-v2-doc-sync

**kind:** `impl` / ホスト `philip` / 分岐 `feat/policy-v2-doc-sync` / **GPU 不使用**

証跡は `audit.md`。**同じ内容を二度書かない。**

---

## 判定

**verdict: pass**（逸脱 5 件、UNKNOWN 0 件）

| Gate | 結果 | 根拠 |
|---|---|---|
| G1 | **pass** | Step A-1 の置換 3 件を実測して置き、L1/L2 が exit 0・WARN 無し（`audit.md:45-74`）。Step A-2 で境界が一意に決まらず **escalate して利用者の回答（候補 B）を得た**（`audit.md:85-101`）。Step A-3 の分布を記録（`audit.md:106-117`） |

---

## 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 履歴移設の同一性 | 移設元・移設先とも **554 行 / `sha256 419de04d85f55e8809568f73b110bbc76ed975e34a56d2a501a96e9898827815`** で一致 | 一文字だけ変えた一時複製（`S0-frozen`→`S0-frozeN`）で `247efd8b…` へ変わり**不一致になった**。複製は消した（0 件） |
| b | 撤回済みの語の残存 | 「比較の三角形」README **0**・CLAUDE **0**（変更前は README 3 件）。「分析ファースト」**0**（変更前も 0）。旧判定規則 `\|Δ\| > 1σ` / `S0〜S9 で揃える` / `§10.1` は CLAUDE **各 0** | 「比較の三角形」は履歴ファイルに **3 件**で検出。旧判定規則は**版管理の旧版（HEAD）に各 1 件**で検出。**「分析ファースト」は元から存在しない語のため、この対照は成立しない**（下記の起票者の誤り 2） |
| c | リンクの健全性 | **今回私が張った相対リンク 3 件はすべて実在**。ただし**移設本文の中の 2 件が解決しなくなった** | 実在しない経路を含む一時複製で **exit 1・1 件検出**。複製は消した（0 件） |
| d | 既存の文書検査 | `docs-check` **exit 0**（対象 42 文書）／`agent-check` **exit 0**（94 対象）／`forbidden-check` **exit 0・違反 0**。`context-check` `taskindex-check` `inbox-check` は **exit 2**（下記） | README に実在しない経路を一時的に足すと `docs-check` が `README.md:1117` を指して **exit 2**。**走査零件のまま通っていない。** 復元の要約値一致も確認 |
| e | 変更範囲 | **4 件**（`M README.md` / `M CLAUDE.md` / `?? docs/history/` / `?? tasks/T-2026-08-28-policy-v2-doc-sync/`）。§2 の対象と契約ディレクトリのみ | 全量を `audit.md:253-268` に載せた。**対象外の変更は 0 件** |

### 判定 c で解決しなくなった 2 件（直していない）

```
docs/history/README_log_2026-05_to_2026-08.md: docs/research_review_and_next_plan_2026-08-22.md
docs/history/README_log_2026-05_to_2026-08.md: docs/task_drafts/README.md
```

**どちらも移設本文の中にあり、私が張ったものではない。** README（リポジトリ直下）を基点に
書かれていたため、`docs/history/` へ移すと解決しなくなった。**移設前の README では 0 件**
（相対リンク 43 件すべて解決）だったので、**移設が原因である。**

**禁止 1（移設本文の改変）により直せない。** 先頭注記に基点が README である旨を明記した。
**指す先はリポジトリ直下から見れば 2 件とも実在する。**

### 判定 d で exit 0 にならなかった 3 件（回していない）

`context-check` `taskindex-check` `inbox-check` は投影・集約が他ホストの統合に対して
古いために落ちる。**今回の変更が原因ではない。**

- 生成器 3 つの入力に README.md / CLAUDE.md は無い（`build_inbox.py:104` の 1 件は案内文字列）
- 今回の変更で `runindex/` **0 件**、`tasks/*/result.yaml` **0 件**、`tasks/inbox.d/` **0 件**

**禁止 3・4 が再生成を禁じている**（「統合後に正本ホストで行う」）ため回していない。

---

## 実測（次の契約で使う値）

| 値 | 実測 |
|---|---|
| 履歴ファイルの経路 | `docs/history/README_log_2026-05_to_2026-08.md`（**582 行**、うち移設本文 554 行） |
| 移設本文の要約値 | `sha256 419de04d85f55e8809568f73b110bbc76ed975e34a56d2a501a96e9898827815` |
| 移設本文の範囲（履歴側） | **22 〜 575 行**（先頭注記は 1〜20 行、末尾の変更履歴は 576 行以降） |
| 時系列ログの境界（README 側・移設前） | **646–1069 行**（20 見出し）と **1250–1379 行**（1 見出し）の**二範囲。連続していない** |
| `runindex_commit` | `7918b5dd9aab3d15b3c459f87aebdd9eb1653116` |
| `conventions_rev` | `a8c07e813696d3720ceee648e8aa202224285955` |
| `counts` | index **1177** / experiments **213** / verdicts **1038** |
| 撤回済みの語の残存 | README **0** / CLAUDE **0**（検査語 x・y・z すべて） |
| README / CLAUDE の変更前 | 1612 行 `fdb26e80…` / 90 行 `0a41ac93…` |
| README / CLAUDE の変更後 | **1114 行** / **108 行** |
| 文書系の検査 | `docs-check` `agent-check` `forbidden-check` の 3 つが exit 0。投影系 3 つは統合後に正本ホストで回す |

---

## 起票者の誤り

1. **`self_contradiction`** — バンドルに四つ目のファイル `research_policy_v2_2026-08-28.md` を
   同梱したため、**初回の取り込みが拒否された**（`ALLOWED_FILES` は 3 種）。SPEC §0 は
   この失敗を自ら記しているが、**同じバンドルで再配布されたため実行者側で二度止まった。**
2. **`asserted_without_measuring`** — 検査語 y「分析ファースト」は **README・CLAUDE.md とも
   変更前から 0 件**であった。存在しない語を検査語に指定したため、**判定 b の空振り確認
   （履歴ファイルへ当てて 1 件以上）が y については原理的に成立しない。**
3. **`asserted_without_measuring`** — 「2026-06 中旬から 2026-08 下旬に及ぶ日付見出し節が
   **連続している**」は誤り。日付見出しは 21 件あり、**あいだに三つの参照用の節が挟まる。**
   さらに**連続する塊の最後は 2026-08-13（中旬）**で、下旬の見出しは分離した 1 件だけである。
   **記述の二条件が両立せず、指示どおりでは境界を決められない。**
4. **`self_contradiction`** — 禁止 1「移設本文を一字も変えない」と判定 c「リンクがすべて実在」が
   両立しない場合がある。**移設は相対リンクの基点を変えるため、本文を変えずに解決させられない。**
   実測で 2 件が該当した。SPEC §7 は「既存の壊れリンク」しか想定しておらず、
   **移設によって新たに壊れる場合の行が無い。**
5. **`self_contradiction`** — 判定 d「Makefile の文書・生成物系の検査がすべて exit 0」と
   禁止 3・4「投影と集約と runindex の再生成を行わない」が両立しない。
   **投影は他ホストの統合で古くなっており、再生成しない限り exit 0 にできない。**
6. **`check_does_not_check`** — Task 5 が追記先を「README の変更履歴に相当する節」とするが、
   **README にも CLAUDE.md にも docs/*.md にもその節は存在しない**（機械的に走査して 0 件）。
   指示どおりの場所が無いため、実行者が新設先を判断するほかなかった。

---

## 逸脱・想定外・UNKNOWN

### 逸脱

1. **開始前から在った汚れを 2 回に分けて退避した。** `task-start` が汚れた作業ツリーでは
   分岐を作らないため。**`mv` は使っていない。契約が終わり元の分岐へ戻るまで戻さない。**
   - `stash@{1}` … `.stglobalignore` の変更 + 未追跡 5 件
   - `stash@{0}` … `experiments/analysis/` の 3 ディレクトリ（**中身は phase0 に保全済みと照合**）
2. **時系列ログの境界を利用者へ escalate して決めた。** SPEC §7 の指示どおり候補と根拠を提示し、
   **候補 B（日付見出し 21 件すべて）**の回答を得た。自分では決めていない。
3. **Task 5 の追記先を履歴ファイルの末尾に新設した。** README に変更履歴の節が無いため。
   **移設本文の範囲外であることを本文中に明記し、判定 a を取り直して一致を確認した。**
4. **2026-08-27 の指摘整理へのリンクを張っていない。** 成果物がリポジトリに実在しないため
   （名前・中身の両方で走査して 0 件）。SPEC の「実在を確かめずにリンクを書かない」に従った。
5. **投影系 3 検査（`context-check` `taskindex-check` `inbox-check`）を exit 0 にしていない。**
   禁止 3・4 が再生成を禁じているため。今回の変更が原因でないことを入力側から示した。

### 想定外

- **取り込みが二度、作業ツリーの汚れで止まった**（6 件 → 3 件）。二度目の 3 件は
  実行の合間に同期処理が他ホストから運んできたものである。**触らず退避した。**
- **`docs-check` の空振り確認で README を一時的に書き換えた。** 検査が README を走査して
  いることを示すため。**要約値の一致で復元を確認済み**（`9323eff0…`）。

### UNKNOWN

**無し。** 本契約で測れなかった値は無い。

---

## 送出

| # | 実測 |
|---|---|
| commit | `8aca4fe3`（**9 ファイル**）。対象外の混入 **0 件** |
| push | `origin/feat/policy-v2-doc-sync` **exit 0**（`* [new branch]`） |
| PR | **#160**。**`base=phase0`**（分岐の起点と同じ）。既定の `master` **ではない**。接頭辞 `feat/` |
| `make task-validate` | **exit 0**、**WARN 無し** |
| `make task-preflight` | **exit 0**（5 PASS / 4 SKIP / 0 FAIL）。SKIP は P2 P3 P4 P5 |
| `make docs-check` | **exit 0**（対象 42 文書） |
| `make agent-check` | **exit 0**（94 対象） |
| `make forbidden-check` | **exit 0・違反 0 件** |
| `make context-check` / `taskindex-check` / `inbox-check` | **exit 2**。投影が他ホストの統合に対して古い。禁止 3・4 により再生成していない |
| `make task-report` | （送信後に記す） |
| `.sync-pause` | （解除後に記す） |
| 退避 | **戻していない**（`stash@{0}` と `stash@{1}`。元の分岐へ戻ってから戻す） |

### 秘匿の自主検査

| 対照 | 対象 | 結果 |
|---|---|---|
| **陽性** | 実値を埋めた囮（**版管理外**） | `live:NOTION_API_KEY=1, live:WANDB_API_KEY=1, notion_token=1, pem_private_key=1` **exit 1** |
| **陰性** | 送出する 9 ファイル | `wandb_key_shape=6`（`spec.yaml` `audit.md` `RESULT.md` に各 2 件）**exit 1** |

🔴 **陰性対照で一致が出たため、何に一致したかを目視した。**
**6 件すべて git の commit** であった（`git cat-file -t` で `commit` と確認。
`runindex_commit = 7918b5dd…`「exp(s4): 60-seed deterministic sweep」と
`conventions_rev = a8c07e81…`「feat(context): move issuer references…」。
**SPEC Step A-1 が 40 桁の全長で書くよう求めている値である**）。

**環境の実値との照合は 0 件。** 秘匿は含まれていない。
既知の型の誤検知である（`tasks/T-2026-08-12-sync-audit-efros/RESULT.md:291` に同じ実測）。
**検査は無効にしていない。**

# audit — T-2026-08-31-notion-repo-followup-and-retire

実行ホスト `lecun` / 分岐 `feat/notion-repo-followup-and-retire`。GPU 未使用。
Notion への書き込みは行っていない（読み取りと乾燥走行のみ）。

---

## 1. Task A 前提と門

### 1.1 退避した未追跡（A-1）

`.sync-pause.released`（前契約の解除マーカー。同期対象外）を
`/tmp/claude-1000/.../scratchpad/parked/` へ退避。**消していない。**

### 1.2 事前記入値（A-3）

    runindex: 96eb3a1c   conventions: a8c07e81
    index 1266 / experiments 285 / verdicts 1506

`resolve-at-intake` 2 箇所と `counts` の零を差し替え、L1・L2 は exit 0。

`make spec-check` は **1 件で fail**。

    integration_prohibited_without_pause @ SPEC.md:82
      「6 統合（merge）。push と PR の作成は行う」

**前契約と同型の偽陽性である。** SPEC §5 A-2 に「`make task-start` で分岐と抑止を置く」、
F-7 に「抑止を移動で解除」、判定 N にも抑止の記載がある。契約 §1 罠 14 が
「通すために本文を書き換えない」と定めるため書き換えていない。

### 1.3 門（A-4）

    $ git cat-file -e origin/phase0:docs/archive/notion/manifest.csv
    → 成功（前契約 PR #170 は統合済み）

**空振り確認**: 存在しない経路 `NO_SUCH_FILE.csv` で同じ確認をすると失敗する。

### 1.4 open な PR（A-5）

    $ gh pr list --state open
    []

**0 件。** 本契約の後に投影が再び古くなる見込みは無い。

### 1.5 試験の基準（A-6）

    6 failed, 509 passed
    FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    FAILED tests/test_fetch_task.py::test_rejects_unknown_file_name
    FAILED tests/test_research_logger.py::test_log_run_idempotent
    FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

### 1.6 資格情報（A-7）

    NOTION_API_KEY: 設定あり（長さ 50）  /  WANDB_API_KEY: 設定あり（長さ 86）

**値は出力していない。** 成立したため Task E を UNKNOWN にする必要は生じなかった。

---

## 2. Task B 投影の再生成（一度だけ）

    B-1 再生成の前:  taskindex-check exit=2 / inbox-check exit=2 / context-check exit=0
    B-2 make taskindex exit=0 / make inbox exit=0   ← 一度だけ
    B-3 再生成の後:  taskindex-check exit=0 / inbox-check exit=0 / context-check exit=0

**判定 B は前後の出力そのものが両方向である。**
`make context` は runindex が変わっていないため回していない（契約 §4 禁止 3）。
差分は commit `72d23568`。以後の Task で再生成していない。

---

## 3. Task C 退役

### 3.1 書き込み経路の列挙（C-1・異質な二通り）

**方法 1: HTTP メソッドと endpoint から**（`requests.post` / `requests.patch` で `/pages`）

    src/egosurgery/utils/notion_logger.py:181,240,275
    src/egosurgery/utils/notion_ops.py:109,112
    scripts/post_eval_to_notion.py:154,273,278
    scripts/draft_master_update.py:94,222
    scripts/post_t1b_ca_to_notion.py:83,87
    scripts/post_hc_to_notion.py:83,87
    tools/fetch_task.py:363          ← 配布台帳（退役対象外）

**方法 2: 公開関数の名前とファイル単位の集計から**

    notion_logger.log_experiment_to_notion
    notion_ops.log_decision / log_lesson / save_prompt
    書き込み候補を持つファイル: notion_ops 2 / notion_logger 3 / post_t1b_ca 3 /
      post_hc 3 / draft_master_update 2 / post_eval 3 / fetch_task 1 / notion_context_pack 1

**二通りの結果は一致した。** 書き込み先の DB は次のとおり。

| 経路 | 書き込み先 | 扱い |
|---|---|---|
| `notion_logger.log_experiment_to_notion` | `NOTION_DB_ID`（run 台帳） | **退役** |
| `notion_ops._upsert` | `decision_log` / `lessons` / `prompt_library` | **退役** |
| `scripts/post_eval_to_notion.py` ほか 3 本 | `NOTION_DB_ID`（run 台帳） | `notion_logger` 経由でないため個別に呼ぶが、DB は退役済み |
| `scripts/draft_master_update.py` | `decision_log` | 同上 |
| `scripts/notion_context_pack.py` | 読み取りのみ（query） | **移動して退役** |
| `tools/fetch_task.py` / `tools/report_task.py` | `task_distribution` | **退役対象外**（契約 §4 禁止 10） |

### 3.2 呼び出し元（C-2・異質な二通り）

**方法 1: 関数名で全域検索** — `scripts/post_experiments_to_notion.py`、
`scripts/reeval_s0_nms_free.py`、`scripts/sync_experiments_to_notion.py`、
`CLAUDE.md` / `README.md` / `docs/notion_integration.md`、
`tests/test_sync.py` / `tests/test_research_logger.py`。

**方法 2: import とモジュール参照で集計** — 25 ファイル。学習スクリプト 10 本以上
（`train_b2a` `train_s4_tecno` `train_haux` `train_taux` `postprocess_*` 等）が
`mmdet_trainer` や `research_logger` を経由して届く。

**呼び出し元が広いため、退役は呼び出し規約を変えない方式にした**（§3.3）。

### 3.3 退役の方式（C-4）

契約 §1 罠 6 が「識別子を消すだけでは『壊れた』と『退役した』を区別できない」と定める。
**入口で明示的に止め、退役の旨を返す。**

| 実装 | 印 | 位置 |
|---|---|---|
| `src/egosurgery/utils/notion_ops.py` | `RETIRED_DB_KEYS`（5 鍵） | `_upsert` の先頭 |
| `src/egosurgery/utils/notion_logger.py` | `RUN_LEDGER_RETIRED = True` | `log_experiment_to_notion` の先頭 |

戻り値は `{"retired": True, "db_key": ..., "posted": False, "since": "2026-08-31",
"archive": "docs/archive/notion/db/<KEY>/"}`。**引数と戻り値の型は変えていない。**
`notion_logger` は識別子が `NOTION_DB_ID` と登録簿の二経路で解決されうるため、
**入口で止めた**（片方だけ塞いで他方が生きる形にしない。罠 5）。

### 3.4 退役の確認（C-5・両方向。実際には送らない）

**陽性側（退役した経路）**

    log_decision             -> retired=True posted=False db_key=decision_log
    log_lesson               -> retired=True posted=False db_key=lessons
    save_prompt              -> retired=True posted=False db_key=prompt_library
    log_experiment_to_notion -> retired=True posted=False db_key=run_ledger
    （いずれも警告ログに「2026-08-31 に退役した。投稿しない」と写しの場所が出る）

**陰性側（退役の印を外した模擬）**

一度目は **HTTP を 0 回**しか試みず、対照にならなかった。登録簿から鍵を退役節へ移した
ため `_db_id` が解決できず、HTTP に届く前に止まっていた（ログに `DB id 未解決`）。
**鍵も与えて当て直した。**

    notion_ops   : HTTP を試みた 1 回 -> [('post', 'databases/dummy-db-id/query')]
    notion_logger: HTTP を試みた 1 回 -> [('post', 'databases/dummy-db-id/query')]

`requests` を差し替えており**実際には一度も送信していない**。

### 3.5 登録簿（C-3）

| 節 | 内容 |
|---|---|
| `databases` | `task_distribution` のみ |
| `claude_app_surfaces` | 新しい面 5 件（`kind` と `id`、知見 DB は `data_source_id` も併記）。**コードは読まない** |
| `retired_databases` | 旧 DB 5 件 |
| `retired_pages` | 旧頁 6 件（前契約で export した `plan_current` を含む） |

**判定 C の照合**

    登録簿 databases の鍵: {'task_distribution'}
    コードが読む鍵        : {'task_distribution'}   ← NOTION_REGISTRY_KEY と _db_id(" ") から抽出
    一致: True
    空振り確認: 鍵を一つ消した写しでは不一致になる

---

## 4. Task D 文書の追随

### 4.1 `notion_context_pack.py` の退役（D-1）

`git mv scripts/notion_context_pack.py scripts/retired/notion_context_pack.py`。
**削除していない。** `scripts/retired/README.md` に退役の理由と写しの引き方を書いた。

### 4.2 書き換えた文書（D-2）

`CLAUDE.md`（`AGENTS.md` は symlink のため片方だけ直した。罠 4）、`README.md`、
`docs/notion_integration.md`（全面）、`context/README.md`。

### 4.3 検査（D-3）

    make docs-check  -> exit=0（対象 42 文書 / Makefile のターゲット 34 件）
    make agent-check -> exit=0（targets 116）

🔴 **一度 `agent-check` が exit 2 で落ちた。**

    docs/notion_integration.md:34  source scripts/load_env.sh
                              :35  make task-start TASK=...

`source` と `make` を別行に置いたためである（命令ごとに新しいシェルが起きる実装系で
読み込みが引き継がれない。罠 15）。`&&` で同じ命令に入れて解消した。

### 4.4 残存の確認（D-4・異質な二通り）

**方法 1**（現行手順 3 文書を直接検索）: 5 語すべて **0 件**。

🔴 **方法 2**（`docs_audit.md` の「現行手順」42 文書を全走査）で**見落としを検出した**。

    notion_context_pack : 2 件（README.md, docs/notion_integration.md）
    MCP                 : 1 件（docs/notion_integration.md）
    運用ハブ             : 3 件（context/README.md 2, docs/notion_integration.md 1）

**何に一致したのかを目視した**（注意 2）。`README.md` と `docs/notion_integration.md` の
一致は**退役を説明する記述**で問題ない。`context/README.md:46` は
**旧手順への案内が残っていた**ため追随させた。再走査後の残り 4 件はすべて退役の説明である。

**契約が「異質な二通りで確かめる」と定めていた理由がそのまま出た。**

### 4.5 判定 F の空振り確認

🔴 **一度目の当て方が誤りだった。** Makefile に退役経路への目標を足しても `docs-check` は
exit 0 のままだった。実装を読むと `docs-check` は**文書に書かれた経路の実在**を見るもので、
Makefile の中身は見ない（`tools/check_docs.py` の docstring と `exists` の使われ方）。

**文書側へ当て直した。**

    （docs/notion_integration.md に旧経路を一行足す）
    make docs-check -> exit=2
      docs/notion_integration.md:81 実在しない経路 scripts/notion_context_pack.py
    （復元）
    make docs-check -> exit=0   復元後の sha256 2916a327f0429955... / 76 行

---

## 5. Task E 再 export と旧マスター

### 5.1 🔴 旧マスター頁が到達可能になった

前契約では HTTP 404 だったが、本契約の実測では **reachable**。
利用者が共有したものと見られる（契約 §1 罠 11 が想定していた事象）。

    見出し 222 件（H1 7 / H2 71 / H3 119 / PAGE 25）、形式検査 不適合 0 件、再試行 3 回

`docs/archive/notion/toc_plan_master.md` を未取得の説明から実際の見出しへ置き換えた。

### 5.2 run 台帳の再 export（E-1）

**自動投稿の退役の後**に取り直した。

    {"key": "run_ledger", "n_items": 767, "retries": 8}
    前回 767 行 / 今回 767 行
    raw.jsonl / properties.csv / bodies.jsonl の sha256 が三つとも前回と一致

**行数だけでなく内容まで一致した。退役後に 1 行も増えていないことの実測である。**

### 5.3 `last_edited_time` の前後照合（E-3）

    run_ledger  前 2026-08-23T16:39:00.000Z / 後 2026-08-23T16:39:00.000Z -> 同じ

### 5.4 manifest の更新

**対象 7 件すべてが `exported` になった**（前契約は 6/7）。

    plan_master    exported n= 222 bytes=21904    ← 前契約は unreachable
    plan_current   exported n= 199 bytes=19327
    run_ledger     exported n= 767 bytes=4809853  ← 退役後に取り直し
    decision_log   exported n=  65 / lessons 31 / procedure_docs 6 / prompt_library 3

---

## 6. Task F 検査

### 6.1 試験（F-1・判定 H）

    作業後: 6 failed, 509 passed
    増えた失敗: 0 件 / 減った失敗: 0 件

**退役は既存の試験と両立した。** 試験は関数を patch して呼び出し回数を見ており、
呼び出し規約を変えなかったため影響しない。`decisions_required` の一つ目は発火しない。

### 6.2 forbidden-check（F-2・判定 M）

    {"base": "origin/phase0", "changed": 17, "checked": 13, "excluded": 4,
     "status": "pass", "violations": []}
    exit=0

### 6.3 秘匿と個人情報（F-3・判定 K）

変更ファイル 16 件を走査。**検査は値を出力していない。**

    token 接頭辞  : 0 件 /  鍵の書き出し: 0 件 /  Bearer 直書き: 0 件
    電子メールの形: 9 件  ← 何に一致したのかを目視した

🔴 **9 件はすべて個人の電子メールではない。**

    git@github.com          SSH の clone 先（README.md:192 ほか）
    ubuntu@<ホスト>.local    SSH の接続先表記
    SPEC.md@...             文書内の位置指示

**実在の個人アドレスは 0 件。** いずれも本契約が書いたものではなく、`README.md` の既存行と
Task B の投影再生成で取り込まれた既存の記録である。停止条件には該当しない。

**空振り確認**: 合成フィクスチャで token 接頭辞 1 件・鍵の書き出し 1 件・メール 1 件を検出。

---

## 7. 送出

（Phase F の後半をここへ置く。）

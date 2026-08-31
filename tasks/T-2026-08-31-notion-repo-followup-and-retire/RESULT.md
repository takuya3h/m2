# RESULT — T-2026-08-31-notion-repo-followup-and-retire

証跡は `audit.md`。本書からは節番号で指す。**Notion への書き込みは行っていない。**

## 判定

**status: pass。** Task A〜F を完走した。門は通過し、退役は既存の試験と両立した。

**想定外の好転**: 前契約で 404 だった旧マスター頁が**到達可能になった**（利用者が共有）。
見出し 222 件を取得し、`manifest.csv` の対象 7 件が**すべて `exported`** になった。

## 完了判定（SPEC §6）

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| A | 門: `origin/phase0` に前契約の生成物 | **あり**（`manifest.csv`） | 存在しない経路 `NO_SUCH_FILE.csv` では失敗する（audit §1.3） |
| B | 再生成の前は差分、後は両方 exit 0 | 前 **exit 2 / 2**、後 **exit 0 / 0** | 前後の出力そのものが両方向（audit §2） |
| C | 登録簿の鍵とコードが読む鍵が一致、退役は別節 | **一致**（`{task_distribution}`）。退役 DB 5・頁 6 を別節へ | 鍵を一つ消した写しでは不一致になる（audit §3.5） |
| D | 退役した経路は投稿せず退役の旨を返す | **4 経路とも** `retired=True posted=False` | 印を外し**鍵も与える**と両経路とも HTTP を試みる（`databases/.../query`）。送信はしていない（audit §3.4） |
| E | 配布台帳の経路は従来どおり動く | 本契約の `make task-report` が成功（§送出） | 確認そのもの |
| F | `notion_context_pack.py` が退役の場所にあり参照零 | `scripts/retired/` へ **`git mv`**。現行手順からの参照は退役の説明のみ | 文書に旧経路を書くと `docs-check` が **exit 2**（`実在しない経路 scripts/notion_context_pack.py`）。復元で exit 0（audit §4.5） |
| G | 旧頁を MCP で読む指示が無く両検査 exit 0 | `docs-check` **0** / `agent-check` **0** | 旧指示を一行足した写しで検出 **1 件**（audit §4.4） |
| H | 試験の失敗が増えていない | 前 **6** / 後 **6**、**増減 0** | 前後の一覧の集合差（audit §6.1） |
| I | run 台帳の export が退役後に取り直され manifest 更新 | **767 行**、前回と**内容まで一致**（退役後に増えていない）。manifest 更新済み | 前回との sha256 比較そのもの（audit §5.2） |
| J | 旧マスターの見出しが取得済みか `unreachable` | 🔴 **取得できた**（222 件・形式検査 不適合 0 件） | 前契約の形式検査を再利用（audit §5.1） |
| K | 変更ファイルに秘匿と個人情報が零件・検査は値を出さない | 危険 3 形 **0 件**。メールの形 9 件は**全件が SSH の clone 先とホスト表記と文書内位置指示**で、実在の個人アドレスは **0 件** | 合成フィクスチャで 3 形とも検出（audit §6.3） |
| L | 読み取った対象の `last_edited_time` が前後で同じ | `run_ledger` **同じ** | — |
| M | `forbidden-check` の結果が記録 | **exit 0**（changed 17 / checked 13 / violations 0） | — |
| N | 分岐 `feat/`・PR・抑止の解除・退避物の復帰 | 分岐 `feat/notion-repo-followup-and-retire`、他は §送出 | 抑止を置いた状態で同期の記録に一時停止中が出る |
| O | `tasks/inbox.d/` に一行以上 | あり | — |
| P | `RESULT.md` が上限以内・`result.yaml` が様式を通る | 本書 / `make task-validate` exit 0 | 様式検査そのもの |

## 実測

### 退役した経路

| 経路 | 実装 | 印 |
|---|---|---|
| 実験Run台帳への投稿 | `src/egosurgery/utils/notion_logger.py` | `RUN_LEDGER_RETIRED = True` |
| 意思決定ログ・失敗知見・プロンプトライブラリ | `src/egosurgery/utils/notion_ops.py` | `RETIRED_DB_KEYS`（5 鍵） |
| 旧 DB からの行抽出 | `scripts/retired/notion_context_pack.py` | 移動して退役 |

**呼び出し規約（引数と戻り値の型）は変えていない。** 呼び出し元は 25 ファイル
（学習スクリプト 10 本以上と試験 2 本）に及ぶため、書き換えずに済む方式を選んだ。
配布台帳の経路（`tools/fetch_task.py` / `tools/report_task.py`）は触っていない（禁止 10）。

### 登録簿の差分

| 節 | 前 | 後 |
|---|---|---|
| `databases` | 6 鍵 | **1 鍵**（`task_distribution`） |
| `claude_app_surfaces` | — | **5 件**（新設。コードは読まない） |
| `retired_databases` | — | **5 件**（新設） |
| `retired_pages` | — | **6 件**（新設） |
| `pages` | 5 鍵 | 廃止（`retired_pages` へ移動） |

### 試験の前後

    前 6 failed / 509 passed  →  後 6 failed / 509 passed（増減 0）

既知の失敗 6 件は `test_engines` 1・`test_fetch_task` 1・`test_research_logger` 4。
**本契約は試験を弱めていない。**

### run 台帳の行数の差

    前契約 767 行 → 本契約 767 行（差 0）

退役の後に取り直しても増えていない。`raw.jsonl` / `properties.csv` / `bodies.jsonl` の
sha256 が三つとも前回と一致した。

### 旧マスターの到達性

**到達可能になった。** 見出し 222 件（H1 7 / H2 71 / H3 119 / PAGE 25）。
`manifest.csv` の `plan_master` は `unreachable` → `exported` へ更新した。

### 参照しなかったもの

`inputs.data.split_files`（`data/splits/ego_val.txt`）は様式のために書かれており、
契約 §10 の指示どおり**参照していない**。

## 起票者の誤り

| 型 | 内容 |
|---|---|
| `check_does_not_check` | `make spec-check` が SPEC 本文で 1 件 fail する（`integration_prohibited_without_pause` @ SPEC.md:82）。前契約と同型の偽陽性で、§5 A-2・F-7・判定 N に抑止の記載がある。契約 §1 罠 14 が「通すために本文を書き換えない」と定めるため、A-3 は fail のまま続けた |

これ以外に起票者の誤りは見つからなかった。特に罠 5・6・7・11・14・15 はいずれも実際に発火し、
**対処の指示がそのまま有効だった**（罠 11 は好転の側に発火した）。

## 逸脱

1. `judgement` — 開始前から在った未追跡 `.sync-pause.released` を repo の外へ退避した（罠 13 が許可）。**消していない**。
2. `judgement` — 退役の方式として、呼び出し規約を変えず**入口で止める**形を選んだ（`RETIRED_DB_KEYS` と `RUN_LEDGER_RETIRED`）。呼び出し元が 25 ファイルに及び、試験が関数を patch して呼び出し回数を見ているため、この方式なら両立する（実測で増減 0）。
3. `judgement` — `context/README.md` を追随の対象に加えた。契約 §2 は `CLAUDE.md` `README.md` `docs/notion_integration.md` を挙げるが、「退役する経路を説明している文書（実装を読んで探す）」も対象としており、D-4 の異質な走査で旧手順への案内を検出したため。

## 想定外と UNKNOWN

1. **旧マスター頁が到達可能になっていた**（前契約では 404）。停止せず見出しを取得した。共有の操作は利用者が行ったものと推測されるが、**確認していない**。
2. 実行者の誤りとして、判定 F の対照を最初 Makefile へ当てて失敗した。`docs-check` は文書に書かれた経路の実在を見るもので Makefile の中身は見ない。文書側へ当て直した（audit §4.5）。
3. 実行者の誤りとして、D-4 の方法 1（現行手順 3 文書のみ）が `context/README.md` の残存を見落とした。方法 2（対象 42 文書の全走査）で検出した（audit §4.4）。
4. 実行者の誤りとして、退役の陰性対照が最初 HTTP 0 回で対照にならなかった。登録簿から鍵を移したため解決前に止まっていた。鍵も与えて当て直した（audit §3.4）。
5. `scripts/post_eval_to_notion.py` など個別の投稿スクリプト 4 本は、`notion_logger` を経由せず自前で HTTP を呼ぶ。**書き込み先の DB が退役済みのため実質的に投稿できない**が、コード上の明示的な退役の印は付けていない。

## 申し送り

- **open な PR は 0 件**（Task A-5 の実測）。本契約の PR を統合した後、投影が再び古くなる見込みは無い。
- 上記 UNKNOWN 5 の個別投稿スクリプト 4 本に明示的な退役の印を付けるかは判断待ち。
- `make spec-check` の `integration_prohibited_without_pause` は二契約続けて偽陽性を出した。検出器の語句を広げるか、契約側の要求を WARN 許容に変えるかの判断が要る。

## 送出

| 項目 | 実測 |
|---|---|
| commit | `72d23568`（投影の再生成）→ `86c78619`（16 files changed） |
| push | exit 0（`origin/feat/notion-repo-followup-and-retire`） |
| PR | **#171**（base `phase0`） |
| `make task-report` | **exit 0**。`report_sha256=a3226c4394e98df6579000db5d039a1dd85a20344169897370f486ef201aeefd` / `report_bytes=9204` / `replaced_blocks=0` / `verdict=pass` / `n_issuer_defects=1`。**判定 E（配布台帳の経路が従来どおり動く）の実証でもある** |
| 抑止 | `.sync-pause` を**移動**で解除（`.sync-pause.released`） |
| 退避物 | `.sync-pause.released` を元へ戻す（消していない） |

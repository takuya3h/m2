# RESULT — T-2026-08-31-notion-legacy-toc-and-export

証跡は `audit.md`。本書からは節番号で指す。**読み取り専用の契約で、Notion へ書いていない。**

## 判定

**status: partial。** Phase A〜E は完走したが、**対象 7 件のうち旧マスター頁 1 件が到達不能**で
`toc_plan_master.md` の中身を作れなかった。共有設定は利用者の操作領域である（契約 §9）。

## 完了判定（SPEC §6）

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| A | `manifest.csv` の集合が対象の集合と一致 | **7/7 一致・差なし** | 1 行消した写しは不一致になる（audit §10 の集合差） |
| B | 見出しファイルが見出し行と子頁行だけ | **不適合 0 件**（H1 7 / H2 72 / H3 119 / PAGE 1） | 段落を 1 行足した写しで**不適合 1 件**を検出（audit §6.2） |
| C | 抽出器 陽性で全件・陰性で零件 | 陽性 **7 件** / 陰性 **0 件** | toggle 内側を 1 件落とすと 7→**6 件**へ減る。`child_page` の内側の見出しは拾わない（audit §6.1） |
| D | 頁の大きさ二通りで一致 | `page_size` 100 と 7 で **199 行が完全一致** | 途中で打ち切った写し（150 行）とは**不一致**になる（audit §6.2） |
| E | 三つの生成物と `n_items` が一致 | **5 DB すべて一致**（767 / 65 / 31 / 6 / 3） | 🔴 `wc -l` で一度誤判定した。CSV として読めば一致（audit §7） |
| F | 二回の export の要約値が一致 | `prompt_library` `procedure_docs` の **6 ファイルすべて sha256 一致** | — |
| G | 存在しない id が失敗として記録 | `unreachable` として記録。**零件の成功にならない** | 反対側として `task_distribution` に本契約の行 **1 件**（audit §7） |
| H | 秘匿の形が零件・検査は値を出さない | 危険 3 形は **0 件**。長い符号化 8 件は**全件偽陽性**（sha256 と本文の長い語。環境の資格情報との一致 0 件） | 合成フィクスチャで 3 規則とも 1 件ずつ検出（audit §9.1） |
| I | 個人情報の形が零件 | 電子メールの形 **0 件**（20 ファイル走査） | 合成フィクスチャで 1 件検出（audit §9.1） |
| J | 生成物の合計が閾値以下 | **5,627,935 バイト = 5.37 MB** / 閾値 50 MB | 閾値を実測値の半分に置くと**発火する**（audit §9.3） |
| K | `last_edited_time` が前後で同じ | **5/5 不変**（読み取りだけで副作用が無いことの実測） | — |
| L | `forbidden-check` の結果が記録 | **exit 0**（changed 23 / checked 23 / violations 0） | 開始前の未追跡を §1 で退避したため罠 10 は発火せず（audit §9.4） |
| M | 分岐 `feat/`・PR・抑止の解除・退避物の復帰 | 分岐 `feat/notion-legacy-toc-and-export`。他は §送出 | 抑止を置いた状態で同期の記録に一時停止中が出ることを確認（audit §11） |
| N | `tasks/inbox.d/` に一行以上 | **3 行** | — |
| O | `RESULT.md` が上限以内・`result.yaml` が様式を通る | 本書 / `make task-validate` exit 0 | 様式検査そのもの |

## 実測

### 到達性と件数

| key | 種別 | status | n_items | bytes |
|---|---|---|---|---|
| `plan_master` | page | 🔴 **unreachable**（HTTP 404 `object_not_found`） | 0 | 0 |
| `plan_current` | page | exported | 199 | 19,327 |
| `run_ledger` | database | exported | 767 | 4,809,853 |
| `decision_log` | database | exported | 65 | 495,342 |
| `lessons` | database | exported | 31 | 217,103 |
| `procedure_docs` | database | exported | 6 | 53,232 |
| `prompt_library` | database | exported | 3 | 11,428 |

DB 合計 **872 行**。頁送りの再試行 合計 8 回（DB 6・見出し 2）。

### 要約値

生成物の合計 **5,627,935 バイト（5.37 MB）**。各対象の sha256 は `manifest.csv` の列にある。

### 退役の候補（登録簿との差）

`configs/notion.yaml` の `databases` は 5 件で、**起票時点の記載と差なし**。
到達できた 5 DB はアーカイブへ移せる状態にある。
**旧マスター頁は共有されていないため、移す前に共有設定の判断が要る。**

### 参照しなかったもの

`inputs.data.split_files`（`data/splits/ego_val.txt`）は様式のために書かれており、
契約 §10 の指示どおり**参照していない**。

## 起票者の誤り

| 型 | 内容 |
|---|---|
| `check_does_not_check` | 契約 §5 A-3 は「`make spec-check` を通す」と求めるが、SPEC 本文が `integration_prohibited_without_pause` を 2 件踏んで **fail する**。実体は偽陽性で、§5 A-2・E-5・判定 M に抑止の記載がある。検出器の語句パターンに合致しないだけであり、指示どおりでは A-3 を満たせない |
| `asserted_without_measuring` | §2 は旧マスター頁を対象に含め §3 は `toc_plan_master.md` を生成物に挙げるが、実測では **HTTP 404** で到達できない。契約 §1 の罠 1 が「404 は失敗ではなく `unreachable`」と定めているため停止はしないが、生成物の要求と到達性の見込みが食い違っている |

## 逸脱

1. `judgement` — 開始前から在った未追跡 5 件を repo の外へ退避した（契約 §1 罠 9 が許可）。うち `experiments/analysis/hts_candidate_acceptance/*.py` 4 件は**同期対象**（`.stignore:51`）のため、`origin/phase0` に同一内容が commit 済みであることを先に確かめてから動かした。**消していない**（audit §1）。
2. `judgement` — 作業中に生成された `docs/archive/notion/__pycache__` を退避した（禁止 5 に従い削除していない）。
3. `spec_defect` — `export_notion.py` の再試行を 429 だけでなく `OSError`（読み取りタイムアウトを含む）へ広げた。`page_size=7` の走行が 2 度落ちたためで、契約 §1 罠 6 の範囲である（audit §8）。
4. `environment` — 契約 §4 禁止 3 に従い `make context` `make taskindex` `make inbox` とその check を回していない。技能書 §6 は投影の再生成を求めるが、契約 §1 罠 11 が「本契約の禁止が優先する」と定めている。

## 想定外と UNKNOWN

1. **旧マスター頁の見出しは取得できていない。** 404 のため。推定で埋めていない。
2. `page_size=7` は読み取りタイムアウトを 2 度起こした。再試行で完走したが、**原因は特定していない**（Notion 側の応答か経路かは切り分けていない）。
3. 実行者の誤りとして、判定 E を `wc -l` で数えて一度「不一致」と誤判定した。CSV として読めば一致する（audit §7）。生成物の欠陥ではない。
4. 実行者の誤りとして、`pgrep -f` の自己一致で自分のシェルを 2 度停止させた（`conventions#issuer_cautions` 注意 6）。`/proc/PID/exe` で絞る形に直した。

## 判断待ち

1. **旧マスター頁の共有設定**（実行者は記録するだけ。契約 §9）。共有後は同じ命令で取得できる（`toc_plan_master.md` に記載）。
2. 到達できた 5 DB をアーカイブへ移すか。
3. `make spec-check` の `integration_prohibited_without_pause` の語句を広げるか、契約 §5 A-3 の要求を WARN 許容に変えるか。

## 送出

（PR 番号と `make task-report` の終了コードは下に入れる。）

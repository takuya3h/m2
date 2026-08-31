# Notion の旧頁の見出し抽出と旧データベースの保全 export

出所: `T-2026-08-31-notion-legacy-toc-and-export`（2026-08-31、lecun）。**読み取り専用。**
Notion へは一切書いていない（判定 K で `last_edited_time` の不変を実測）。

数値はすべて実測である。本文は人が読んでいない。

## 1. 対象と到達性

`manifest.csv` に一件一行。対象の集合は `configs/notion.yaml` の登録簿から決めた
（`databases` の全キーから `task_distribution` を除く。起票時点の記載 5 件と**差なし**）。

| key | 種別 | status | n_items | bytes |
|---|---|---|---|---|
| `plan_master` | page | 🔴 **unreachable** | 0 | 0 |
| `plan_current` | page | exported | 199 | 19,327 |
| `run_ledger` | database | exported | 767 | 4,809,853 |
| `decision_log` | database | exported | 65 | 495,342 |
| `lessons` | database | exported | 31 | 217,103 |
| `procedure_docs` | database | exported | 6 | 53,232 |
| `prompt_library` | database | exported | 3 | 11,428 |

🔴 **旧マスター頁（`pages.plan_master`）は HTTP 404 `object_not_found`。**
Integration に共有されていない。契約 §1 の罠 1 が実際に発火した。
**共有設定は利用者の操作領域**であり、実行者は記録するだけである。
このため `toc_plan_master.md` は生成できていない。

対象 7 件中 6 件が到達可能。過半が到達不能ではないため続行した。

## 2. 見出し抽出

`toc_plan_current.md` に 199 件。**本文の段落を含まない**（形式検査で不適合 0 件）。

| 種別 | 件数 |
|---|---|
| H1 | 7 |
| H2 | 72 |
| H3 | 119 |
| PAGE（子頁） | 1 |
| DB（子 DB） | 0 |

頁の大きさ 100 と 7 の二通りで走らせ、**出力が完全一致**した（判定 D）。
`page_size=7` は呼び出しが増えて読み取りタイムアウトが起きたため、
実装の再試行を 429 だけでなくタイムアウトにも広げた（再試行 2 回で完走）。

## 3. データベースの export

到達できた 5 DB の全行。合計 **872 行**。各 DB は `raw.jsonl`・`properties.csv`・`bodies.jsonl` を持ち、
**三つのレコード数と manifest の `n_items` が全 DB で一致**する（判定 E）。

    run_ledger 767 / decision_log 65 / lessons 31 / procedure_docs 6 / prompt_library 3

頁送りの再試行は合計 6 回（run_ledger 5・lessons 1）。

`properties.csv` はセルに改行を含む本文を持つため、**`wc -l` では行数が水増しされる**
（decision_log は 65 行だが `wc -l` は 848）。数えるときは CSV として読むこと。

## 4. 対照（両方向）

| 対照 | 入力 | 結果 |
|---|---|---|
| 抽出器 陽性 | 各階層の見出し・toggle の内側・段組みの中・子頁・子 DB を含むフィクスチャ | **7 件検出**（H1 1 / H2 2 / H3 2 / PAGE 1 / DB 1）。`child_page` の内側の見出しは**降りずに拾わない**ことも確認 |
| 抽出器 陰性 | 段落・箇条書き・番号付き・コードだけのフィクスチャ | **0 件** |
| 抽出器 減少 | toggle の内側の見出しを 1 件落とした写し | 7 → **6 件**に減った |
| 頁送り | 途中で打ち切った写し（150 行）と比較 | **不一致**（検査が働いている） |
| 形式検査 | 段落を 1 行足した写し | **不適合 1 件**を検出 |
| DB 陰性 | 存在しない database id | **`unreachable` として失敗記録**。零件の成功にならない |
| DB 陽性 | `task_distribution` に本契約の行 | **1 件**（export はしていない。件数だけ） |
| 再現性 | `prompt_library` と `procedure_docs` を二回 export | 6 ファイルすべて **sha256 一致** |
| 副作用 | 5 DB の `last_edited_time` を Task A と Task D で照合 | **5/5 不変** |

## 5. 秘匿と個人情報

**検査は値を出力していない。** 件数と形と長さだけを扱った。

| 検査 | 件数 |
|---|---|
| notion token の接頭辞 | 0 |
| 鍵の書き出し | 0 |
| Bearer の直書き | 0 |
| 長い符号化文字列 | 8（**すべて偽陽性**。下記） |
| 電子メールの形 | **0** |

長い符号化文字列 8 件の内訳を**何に一致したのか目視**した（値は出していない）。

- `manifest.csv` の 6 件 = 本契約が書いた **sha256**（64 桁の 16 進）
- `db/lessons/` の 2 件 = 本文中の長い語（英小 40・数 19・記号 4 で 16 進ではない）

環境にある資格情報との**完全一致は 0 件**。検査器は合成フィクスチャで
3 規則とも検出しており、空振りしていない。

## 6. サイズ

生成物の合計 **5,621,830 バイト = 5.36 MB**。閾値 50 MB の範囲内。
閾値を実測値の半分に置くと停止条件が発火することを確かめた。

## 7. 退役の候補

`configs/notion.yaml` の登録簿と起票時点の記載に**差は無かった**（5 件で一致）。
到達できた 5 DB はアーカイブへ移せる状態にある。
**旧マスター頁は共有されていないため、移す前に共有設定の判断が要る。**

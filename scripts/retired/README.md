# 退役したスクリプト

**現行手順ではない。** ここにあるものは動かす前提で置いていない。
削除せず移動して残しているのは、当時の経路を後から読めるようにするためである。

| ファイル | 退役 | 理由 |
|---|---|---|
| `notion_context_pack.py` | 2026-08-31 | 旧データベース群（意思決定ログ・失敗知見・実験手順書・プロンプトライブラリ）から行を抽出する道具だった。旧 DB は凍結し、全行の写しは `docs/archive/notion/db/<KEY>/` にある。**CLI が Notion に触れるのは配布台帳だけになった**（`T-2026-08-31-notion-repo-followup-and-retire`） |

退役した DB の内容を引くときは Notion ではなく写しを読む。

    docs/archive/notion/db/decision_log/properties.csv
    docs/archive/notion/db/lessons/properties.csv
    docs/archive/notion/db/procedure_docs/properties.csv
    docs/archive/notion/db/prompt_library/properties.csv
    docs/archive/notion/db/run_ledger/properties.csv

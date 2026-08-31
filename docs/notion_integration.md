# Notion 連携の仕組み

**CLI が Notion に触れるのは配布台帳（`task_distribution`）だけである。**

2026-08-31 に記録系を再構成した（`T-2026-08-31-notion-repo-followup-and-retire`）。
それ以前の「運用ハブ駆動」の手順（旧頁を MCP で読み、旧 DB へ自動投稿する）は**退役した**。

## 使う経路（この二つだけ）

| 目的 | 入口 | 実装 |
|---|---|---|
| 契約の取り込み | `make task-notion` / `make task-start` | `tools/fetch_task.py` |
| 完了報告の送り返し | `make task-report` | `tools/report_task.py` |

いずれも配布台帳 1 件だけを読み書きする。**他の面には触れない。**

## ID レジストリ

`configs/notion.yaml`（非秘密・commit 可）。認証 `NOTION_API_KEY` は暗号化 `.env.gpg` にあり、
`source scripts/load_env.sh` が現在のシェルへ読み込む。

| 節 | 何が入るか | コードが読むか |
|---|---|---|
| `databases` | 配布台帳のみ | **読む**（`fetch_task.py` の `NOTION_REGISTRY_KEY`） |
| `claude_app_surfaces` | Claude アプリの面（運用正本・現在地と現行計画・マスター・知見/決定・アーカイブ） | **読まない**（人が引くための記載） |
| `retired_databases` / `retired_pages` | 凍結した旧 DB と旧頁 | **読まない** |

新しい面は Integration へ共有されていないため、CLI が読めば 404 になる。
**コードから解決してはならない。**

## セットアップ

**読み込みは同じ命令に入れる。** 命令ごとに新しいシェルが起きる実装系があり、
別の行にすると `NOTION_API_KEY` が次の命令へ引き継がれない。

```bash
source scripts/load_env.sh && make task-start TASK=T-YYYY-MM-DD-slug
```

`NOTION_DB_ID` は使わない（実験Run台帳の投稿が退役したため）。

## 退役した経路

自動書き込みは**明示的に**止めてある。識別子を消すだけでは fail-open のまま無言で
何もせず、「壊れた」と「退役した」を区別できないためである。
呼ばれたときは投稿せず、退役の旨を記録して `{"retired": True, "posted": False, ...}` を返す。

| 経路 | 実装 | 印 |
|---|---|---|
| 実験Run台帳への投稿 | `src/egosurgery/utils/notion_logger.py` | `RUN_LEDGER_RETIRED` |
| 意思決定ログ・失敗知見・プロンプトライブラリ | `src/egosurgery/utils/notion_ops.py` | `RETIRED_DB_KEYS` |
| 旧 DB からの行抽出 | `scripts/retired/notion_context_pack.py` | 移動して退役 |

呼び出し規約（引数と戻り値の型）は変えていないため、呼び出し元は書き換えていない。

## 退役した内容の引き方

Notion ではなく repo の写しを読む。全行が `T-2026-08-31-notion-legacy-toc-and-export`（PR #170）で
保全されている。

```
docs/archive/notion/manifest.csv          対象と件数と要約値
docs/archive/notion/db/<KEY>/raw.jsonl        query の応答そのまま
docs/archive/notion/db/<KEY>/properties.csv   プロパティの平坦化（セルに改行を含むため CSV として読む）
docs/archive/notion/db/<KEY>/bodies.jsonl     各行の本文ブロック
docs/archive/notion/toc_plan_current.md       現行版頁の見出し
```

## いまの記録先

| 記録するもの | 置き場 |
|---|---|
| 契約ごとの判断 | `tasks/inbox.d/<task_id>.md` |
| 再発防止の教訓 | `tasks/lessons.md` |
| 実験の結果 | `experiments/` の証跡と `runindex/`（`make runindex`） |
| 完了報告 | `tasks/<task_id>/RESULT.md` と `result.yaml`、配布台帳へは `make task-report` |

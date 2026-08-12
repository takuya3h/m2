---
description: 直近 N 日の意思決定・主要 run を集約し、M2 研究計画マスター §0 変更履歴 + 進捗反映スナップショット page への追記ブロックを **ドラフト**生成する（自動マージしない）
argument-hint: [--days=N] [--write-snapshot] (省略時 7 日 / 進捗 page は更新しない)
---

このスラッシュコマンドは「マスター昇格」運用の入口です。auto_logging_implementation.md §5.6 に従い、
**ドラフトのみ**生成し、マスター本文には**勝手に書き込みません**（マージは人間）。

引数: `$ARGUMENTS` （`--days N` `--write-snapshot` など）

手順:

1. `python scripts/draft_master_update.py $ARGUMENTS` を実行（既定 --days=7）
2. stdout に生成された:
   - **§0 変更履歴エントリ草案**（マスター冒頭に追記する形）
   - **進捗反映スナップショット page への追記ブロック草案**
   を表示
3. `--write-snapshot` 指定時は進捗 page へ追記済の旨を案内（REST 経由）
4. **§0 のマージは必ず手動で**:
   - ユーザーに「上の草案をマスター §0 冒頭に追記してください」と表示
   - 自動 MCP/REST 投稿はしない（§2 鉄則 5.6）

注意:
- 数値は実測値のみ。`metrics.json` 直読みで捏造ゼロ。
- 意思決定は Notion 意思決定ログ DB から **read-only** で取得（fail-open: 認証無しなら空 list）。
- 散文の自動生成はしない（ドラフトの骨子のみ）。
- 失敗実験フォルダ（`_smoke_prior/` 等）は **除外しない**（研究 integrity の証拠）。

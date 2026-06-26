# Notion 連携の仕組み（M2研究計画 × M2研究運用ハブ）

研究運用を Notion の 2 ページにフルで連動させ、**コンテキスト消費を抑えつつ DB 駆動**で回すための仕組み。

| ページ | 役割 | 使い方 |
|---|---|---|
| **M2研究計画**（マスター・長文 `361ee4d4…`） | 方針〜詳細手順の正本 | **全文は読まない**。該当 § セクションだけ MCP で取得 |
| **M2研究運用ハブ**（軽量入口 `36bee4d4…819c`） | DB 駆動の運用（結果記録・プロンプト・状態・意思決定・失敗知見） | セッションの入口。下記 DB を読み書き |

## チャネル（ハイブリッド）
- **REST**（`NOTION_API_KEY` + DB ID）: スクリプト/headless からの**自動記録**。`notion_logger`（Run台帳）/ `notion_ops`（意思決定・失敗知見・プロンプト）。
- **MCP**（Claude 対話接続）: **読み取り**（現在の研究状態・計画スライス・context pack）と、アドホックな書き込み。

## ID レジストリ
`configs/notion.yaml`（**非秘密**・コミット可）に 5 DB と主要ページの ID を集約。トークンは `.env` のみ。
`NOTION_DB_<KEY>` 環境変数で個別上書き可。token の Notion Integration に**全 DB/ページを share** しておくこと。

| key | DB | 書き込みヘルパ |
|---|---|---|
| run_ledger | 実験Run台帳 | `notion_logger.log_experiment_to_notion(exp_dir)` |
| decision_log | 意思決定ログ | `notion_ops.log_decision(name, rationale=…, type_=…, impact=…)` |
| lessons | 失敗知見・教訓 | `notion_ops.log_lesson(name, category=…, severity=…, prevention=…)` |
| prompt_library | プロンプトライブラリ | `notion_ops.save_prompt(name, prompt_file=…, target=…)` |
| procedure_docs | 実験手順書 | （主に手動/Claude が MCP で作成・更新） |

## セットアップ
```bash
# .env（コミットしない）に:
#   NOTION_API_KEY=secret_xxx          # Notion Integration トークン
#   NOTION_DB_ID=ef4ccd02-...          # 実験Run台帳 DB（notion_logger 用）
# 読み込み:
set -a; source .env; set +a
export NOTION_SERVER_OPTION=lecun      # Run台帳 Server 列（実行サーバー名）
```
Notion 側: Integration を作成し、運用ハブ配下の 5 DB を share。`configs/notion.yaml` の ID と一致させる。

## 読む（コンテキスト削減・運用ループ §2）
```bash
# 構造化 DB 行（指定 step の意思決定/失敗知見/プロンプト/手順書を関連行だけ）
.venv/bin/python scripts/notion_context_pack.py --step S0
```
narrative な「現在の研究状態」は Claude が MCP fetch（`configs/notion.yaml` pages.current_state）。
**M2研究計画は該当 § のみ**取得（全文を LLM に渡さない）。CLAUDE.md「Notion 連携」に規約。

## 書く（自動記録・運用ループ §3-6）
```python
from egosurgery.utils import notion_ops
notion_ops.log_decision("凍結源をRelation-DETRに確定", rationale="3-seed mAP 0.727で1位",
                        type_="method", impact="high", related_steps=["S0"], source="file://...")
notion_ops.log_lesson("base-σ偽陽性", category="evaluation", severity="P1",
                      symptom="ΔL2が有意判定", root_cause="符号反転をbase-σが見落とす",
                      prevention="paired-σ(対seed差・同符号)で判定", related_steps=["S4"])
notion_ops.save_prompt("S0 DDP runbook prompt", prompt_file="file://.../prompt.md", target="Claude Code CLI")
```
- 実験 Run の自動投稿は学習/後処理スクリプトに配線済（postprocess_b1 / train_b2a / train_t1a / postprocess_t1b）。
  既存分の一括投稿は `scripts/post_experiments_to_notion.py`（`--dry-run` でプレビュー）。
- すべて `NOTION_API_KEY` 未設定なら **no-op**（warn のみ・研究フローを止めない）。Name 冪等（同名は update）。

## 運用ループ（ハブ §運用ループ）との対応
1. 実験前: 実験手順書を作成/更新（MCP）。
2. 「現在の研究状態」+ 手順書 + 関連意思決定/失敗知見 → 実装プロンプト生成（context_pack）。
3. 実験後: Run台帳に自動記録（notion_logger）。
4. 方針変更: `log_decision`。 5. 再発防止: `log_lesson`。 6. 次アクション変化時: 現在の研究状態を更新（MCP）。
7. 計画本文反映は週次/マイルストーン単位。

## 制約・注意
- MCP 接続は対話セッション限定（cron/headless では不在のことがある）→ 自動記録は **REST 一択**。
- DB の select 値は schema に存在するもの。新値（例 Step="B"）を POST すると Notion が option を自動作成する。
- `.env`・トークンは **コード/コミットに含めない**。`configs/notion.yaml` は ID のみ。

## 全面自動化（auto_logging）

2026-06-26 から `ResearchLogger` ファサード + 取りこぼし防止スイープ + Claude Code フックで
**研究記録の全面自動化**が稼働。詳細 → [`docs/auto_logging.md`](auto_logging.md)。

主要要素:
- **ライブラリ**: `src/egosurgery/utils/{research_logger,run_logging,idempotency,notes_schema}.py`
- **スイープ**: `scripts/sync_experiments_to_notion.py`（`--dry-run` 既定で安全・冪等）
- **マスター昇格ドラフタ**: `scripts/draft_master_update.py`（人間レビュー後マージ）
- **Claude Code 連携**: `.claude/hooks/auto_notion_sync.py` + `/log` / `/promote-to-master`
- **notes.md スキーマ**: `​```decision` / `​```lesson` / `​```prompt` fenced block を sweep が拾って投稿

設計鉄則: REST 経由・fail-open・冪等（`.notion_sync.json` マーカー）・本文は人間が書く（捏造防止）。

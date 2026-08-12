# 研究記録の全面自動化（auto_logging）

> 実装ブリーフ: [`prompts/files111/auto_logging_implementation.md`](../prompts/files111/auto_logging_implementation.md)
> 既存連携: [`docs/notion_integration.md`](notion_integration.md) / 秘密管理: [`docs/secrets_and_tracking.md`](secrets_and_tracking.md)

## 1. ルーティング表（誰が何を書くか）

| 記録対象 | 書き手 | 投稿先 | 経路 |
|---|---|---|---|
| **実験 run（数値・eval_recipe・証跡）** | コード（trainer 完走時）| 実験Run台帳 DB | REST（`ResearchLogger.log_run`）|
| **意思決定（採用/撤退/保留）** | 人間が `notes.md` に `​```decision` ブロック追記 | 意思決定ログ DB | REST スイープ |
| **失敗知見・教訓** | 人間が `notes.md` に `​```lesson` ブロック追記 | 失敗知見・教訓 DB | REST スイープ |
| **プロンプト** | 人間が `notes.md` に `​```prompt` ブロック追記 | プロンプトライブラリ DB | REST スイープ |
| **現在の研究状態（散文）** | コードがドラフト → 人間レビュー後 MCP/REST | 現在の研究状態 page | ハイブリッド |
| **マスター §0 変更履歴** | コードがドラフト → 人間が**手動マージ** | M2研究計画 page | ❌ 自動投稿しない（HARD ルール）|
| **進捗反映スナップショット** | `draft_master_update.py --write-snapshot` でドラフト追記 | 進捗反映スナップショット page | REST（オプション）|

## 2. 運用ループ（実験 → 記録）

```
1. 学習 / 評価コマンド実行 (trainer or scripts/eval_*)
   └─ コード内で ExperimentManager.setup() → 証跡ファイル生成
   └─ trainer 完走時 (内部) or 直接呼び出し
       ResearchLogger(cfg, manager).log_run()  ← 既存 trainer に薄く配線

2. Claude Code Stop / PostToolUse hook (auto_notion_sync.py)
   └─ scripts/sync_experiments_to_notion.py を timeout=60s + fail-open で実行
   └─ 未投稿 run + 未投稿 notes.md ブロックを冪等 upsert

3. 人間が必要に応じて `/log` slash command で
   notes.md に decision/lesson の草案を追記（本文は人間が書く）

4. 週次 / マイルストーン `/promote-to-master`:
   └─ draft_master_update.py で §0 草案 + 進捗 page 追記ブロックをドラフト
   └─ §0 のマージは人間が手動（自動投稿しない）
```

## 3. 冪等性（§6 キー設計）

- **run**: マーカー `experiments/<run>/.notion_sync.json` の `run_ledger_page` が既にあれば skip
- **decision/lesson/prompt**: `sha1(title + date + body)` を hash としてマーカーに記録、重複検出
- Notion 側でも `_find_existing_page` による Name 完全一致 upsert で二重防止（多層防御）
- マーカーは `.gitignore` 対象（同期状態であり証跡ではない）

## 4. Fail-open（§2 鉄則 4）

すべての記録ヘルパは:
- `NOTION_API_KEY` 未設定 → no-op で `None` 返却（警告ログのみ）
- REST 例外 → 例外を投げず `None` 返却、マーカー書かず（再試行可）
- hook timeout (60s) → 警告ログのみ、Claude Code を絶対に止めない
- `notes.md` パース失敗 → 該当ブロック skip、空 list 返却

→ Notion 障害でも学習・評価は絶対に止まらない。

## 5. 構成要素

### 5.1 ライブラリ

| ファイル | 役割 |
|---|---|
| `src/egosurgery/utils/research_logger.py` | 単一ファサード `ResearchLogger`（既存 `notion_ops` / `notion_logger` のオーケストレータ）|
| `src/egosurgery/utils/run_logging.py` | trainer の `run()` を 1 行で包む `with run_logging(cfg, manager) as rlog:`（atexit fallback あり）|
| `src/egosurgery/utils/idempotency.py` | `.notion_sync.json` マーカーの読み書き + `content_hash`（SHA1）|
| `src/egosurgery/utils/notes_schema.py` | `notes.md` fenced block (decision/lesson/prompt) の parser/validator |

### 5.2 スクリプト

| ファイル | 役割 |
|---|---|
| `scripts/sync_experiments_to_notion.py` | 取りこぼし防止スイープ（`--dry-run` 既定で安全）|
| `scripts/draft_master_update.py` | マスター §0 変更履歴 + 進捗 page 追記ブロック をドラフト生成 |
| `scripts/post_experiments_to_notion.py` | 既存の DEFAULT_GLOBS / FAMILY meta を継承し sweep から再利用 |
| `scripts/post_hc_to_notion.py` / `post_t1b_ca_to_notion.py` | injected/control 形式の派生実験用 |

### 5.3 Claude Code 連携

| 場所 | 役割 |
|---|---|
| `.claude/hooks/auto_notion_sync.py` | Stop / PostToolUse hook（学習・評価コマンド検知でスイープ実行）|
| `.claude/commands/log.md` | `/log` slash command（notes.md に草案追記、人間が本文を書く）|
| `.claude/commands/promote-to-master.md` | `/promote-to-master`（マスター §0 草案生成）|
| `.claude/agents/notion-archivist.md` | サブエージェント（セッション終了時の取りこぼし検出）|
| `.claude/settings.json` | フック登録（PostToolUse + Stop の auto_notion_sync）|

## 6. `notes.md` 構造化スキーマ（§8）

人間が書く最小入力。複数ブロック可・前方互換（未知キーは警告のみ）:

````markdown
```decision
title: phase→det は機構非依存で弱い
status: 撤退        # 採用 / 撤退 / 保留 のいずれか
affects: §17.1, 方向非対称
body: |
  oracle-phase を入れても mAP は上がらず、FiLM/CA/rescore の3機構すべてで overall 改善せず。
```

```lesson
title: NpzFile 反復展開で RSS 40GB 超 → OOM
recurrence_guard: _index_npz で一括展開する（per-key ループ禁止）
body: |
  eval_det2phase_test.py の npz[key][i] ループが exit 137 の原因。
```
````

日本語 status は英語へ自動正規化（採用→active, 撤退→superseded, 保留→needs review）。
**LLM に本文を作らせない**（数値捏造禁止・研究 integrity の必須制約）。

## 7. 受け入れ基準（§9・全 PASS）

- **A 単体**: `pytest tests/test_research_logger.py` 12/12 PASS（冪等 / fail-open / マーカー）
- **B 統合**: `pytest tests/test_notes_schema.py tests/test_sync.py` 15/15 PASS（パーサ / dry-run / 冪等）
- **C 配線**: `train_t1a.py` の直接呼び出しを `ResearchLogger.log_run()` に統一済（二重化解消）
- **D 品質**: `ruff check . && black --check . && PYTHONPATH=src pytest tests/ -q`

## 8. 限界（§10・必ず守る）

1. **意思決定/失敗知見は半自動**: 本文は人間が書く。LLM 自動生成は禁止（捏造防止）。
2. **マスター本文は人間マージ**: 自動はドラフト生成まで。
3. **承認ゲート回避**: 自動記録は REST 経由のみ。MCP Notion は対話セッションでの読取り + アドホック書込みに限定。
4. **二重投稿防止**: マーカー + Notion Name 一致 upsert で 1 回に収束。
5. **秘密管理**: `.env` のみ。`configs/notion.yaml` は非秘密 ID のみ。

## 9. 補助: 既知のドリフトと対処

- **`NOTION_SERVER_OPTION` 不一致**（philip→lecun 移行で発生済）: `notion_logger.py` が
  server.txt を fallback として使うよう修正済（2026-06-26）。新規マシン移行時も自動で正しい Server 列に。
- **post_t1b_ca / post_hc 系の専用スクリプト**: Started/Finished/Eval Recipe/GPU Config が
  notion_logger 経由でないと埋まらないので、専用スクリプトでは後追い PATCH するか、
  `ResearchLogger.log_run()` 経由に統一する（推奨）。

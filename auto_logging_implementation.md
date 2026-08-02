# 実装ブリーフ：研究記録の全面自動化（Notion 連携）— Claude Code 用

> **これは何か**: `egosurgery_multitask` リポジトリのルートで **Claude Code に実行させる実装指示書**。
> 「実験が終わったら、ほぼ無人で正しい Notion DB／ページへ記録が入る」状態を作る。
> このファイルを上から順に読み、§7 のマイルストーン順に実装し、各マイルストーン後に §9 の受け入れ基準を必ず実行すること。
> 既存の `prompts/` 規約（`prompts/phase1_patch_eval_recipe.md` 等）に倣い、本ファイルは `prompts/auto_logging_implementation.md` としてコミットする。

---

## 0. 実行手順（Claude Code への指示）

1. **まず §3 の既存資産をすべて `view` で読む**（推測でコードを書かない。既存 API・スキーマを再利用する）。
2. §4 の ID レジストリを `configs/notion.yaml` と突き合わせ、欠けていれば追記（**非秘密のみ**）。
3. §7 の Milestone A → B → C → D の順で実装。各マイルストーン完了ごとに §9 を実行し、緑になってから次へ進む。
4. 破壊的操作（ファイル削除・既存トレーナの大改造）はしない。**追加と薄いラッパー**で実現する。
5. 最後に §11 のドキュメント更新と、マスター §0 への「**手動**」変更履歴記入（§2 の HARD ルール）を行う。

---

## 1. ゴールと非ゴール

### ゴール
- **実験完了 → 実験Run台帳へ自動 upsert**（数値・eval_recipe・証拠パスを含む）。人手ゼロ。
- **意思決定 / 失敗知見 / プロンプト**を「半自動」で起票：人間が `notes.md` に最小の構造化ブロックを書く → 投稿は自動。
- **取りこぼし防止**：未投稿の run / notes を検出して一括投稿するスイープを常設し、Claude Code フックから自動起動。
- **マスター昇格の半自動化**：週次／マイルストーンで「§0 変更履歴エントリ」と「進捗反映スナップショットへの追記」をドラフト生成（人間がマージ）。

### 非ゴール（**重要・前提として明記**）
- ❌ **意思決定／失敗知見の「内容」を完全自動生成しない**。これらは人間の判断であり、LLM に本文を捏造させることは
  リポジトリの「研究インテグリティ（実測値のみ・捏造禁止）」に反する。→ **半自動**（構造化入力からの起票＋人間承認）に留める。
- ❌ **マスター文書（M2研究計画）の §0 や「現在の研究状態」ページの散文を無断で自動改変しない**。
  prose の自動上書きは事故源。週次／マイルストーンで「**ドラフト → 人間マージ**」（運用ハブ「運用ループ」step 7 と一致）。
- ❌ 数値をマスター本文へ転記しない（台帳が単一情報源）。

---

## 2. 鉄則（必ず守る制約）

1. **数値捏造禁止**。実測値のみを記録する。値が無ければ空欄／`null`。
2. **失敗実験フォルダを消さない**（`experiments/_smoke_prior/` 等）。
3. **書き込みは REST 経由のみ**（`src/egosurgery/utils/notion_ops.py` / `notion_logger.py` が使う Notion REST API）。
   - **Claude の MCP Notion ツールは自動記録に使わない**。理由：(a) MCP 書き込みは対話的な承認ゲートがあり無人実行で停止する、
     (b) コードからの REST 呼び出しは `.env` のトークンで承認不要に完結する、(c) 環境差を作らない。
4. **Fail-open**：Notion 障害・トークン未設定でも学習／解析を絶対に止めない。証拠ファイルはローカルに必ず残す
   （`NOTION_API_KEY` 未設定なら全 no-op、既存設計を踏襲）。
5. **冪等 upsert**：`experiment_id` / content-hash をキーに、二重実行で重複行を作らない。
6. **秘密は `.env`、ID は `configs/notion.yaml`**。新規シークレットをコミットしない（`.gitignore` を確認）。
7. **§15 整合**：`eval_recipe` が不一致な Δ は記録しない（既存 `DeltaCalculator` / `InconsistentRecipeError` を尊重）。
8. **ruff / black clean**、テストは `pytest tests/ -q` が全パスを維持。

---

## 3. 最初に読む既存資産（必須・順番）

```
src/egosurgery/utils/notion_ops.py          # log_decision / log_lesson / save_prompt の実 API・対象 DB・プロパティ写像
src/egosurgery/utils/notion_logger.py       # log_experiment_to_notion の実 API・Run台帳のカラム写像（★これを再利用）
src/egosurgery/utils/experiment_manager.py  # 証拠ファイル生成・server.txt・log_eval_recipe()・experiment_id 採番
src/egosurgery/utils/eval_recipe.py         # build_eval_recipe() / locked-down test_cfg / 公式 split サイズ
src/egosurgery/metrics/delta.py             # DeltaCalculator / InconsistentRecipeError
scripts/post_experiments_to_notion.py       # 既存の一括投稿（--dry-run の作法・重複回避の有無を確認）
scripts/post_t1b_ca_to_notion.py            # injected/control 形式の upsert 作法
configs/notion.yaml                         # 非秘密 ID レジストリ（database id / server option 等）
docs/notion_integration.md                  # 現行の連携仕様（REST + MCP ハイブリッド）
.claude/settings.json / .claude/hooks/ など # フック・スラッシュコマンド・サブエージェントの既存構成
```

> **再利用の原則**：Run台帳のカラム名・選択肢・データ型は **`notion_logger` が既に正しく持っている**。
> 新しいカラム名を発明せず、既存写像を関数として括り出して使う。スキーマ確認が必要なら各 DB を一度だけ `fetch` する。

---

## 4. ID レジストリ（ground truth・2026-06-26 時点）

`configs/notion.yaml` に下表が揃っているか確認し、欠けを追記する（**database id を使う。`collection://…` は data source id で REST のページ作成にそのまま使えない**）。

| 対象 | 種別 | database id | data source (collection) id |
|---|---|---|---|
| 実験Run台帳 | DB | `ef4ccd02-0a97-41af-814e-9acc44e1e0d3` | `7bcf9406-29fc-4b2a-8a9e-0be02fc1fc20` |
| 意思決定ログ | DB | `c3f27d4a-0d9f-4c52-adb9-1137efac38b6` | `68d469d8-da47-4eb3-b355-47aa051080fb` |
| 失敗知見・教訓 | DB | `9f6d6a56-0244-4977-84d3-7c55e9b32768` | `0a0ff6a6-7aba-4ffc-947b-011f5ec62101` |
| 実験手順書 | DB | `5b8d9c8d-fa78-49c1-a1de-fd9d03b318a2` | `78611470-d3f7-48dd-a35a-4228d18aa0ef` |
| プロンプトライブラリ | DB | `1c60213a-bf84-4a91-ab50-7eefcb4cffea` | `d0968373-20d0-4a59-9f4d-7878171e5bc4` |
| 現在の研究状態 | Page | `36bee4d4-7777-815d-90e7-e669503f994b` | — |
| 進捗反映スナップショット（適用待ち差分） | Page | `388ee4d4-7777-81da-a260-e764de73bfb0` | — |
| M2研究計画（マスター） | Page | `361ee4d4-7777-804f-b7e6-c023cf50267d` | — |
| M2研究運用ハブ | Page | `36bee4d4-7777-819c-8495-e48d1a71e500` | — |

> これらは「読み書きの宛先」を一元化するためのもの。`configs/notion.yaml` を単一情報源にし、コード内のハードコードを禁止する。

---

## 5. アーキテクチャ

### 5.1 単一ファサード `ResearchLogger`
`src/egosurgery/utils/research_logger.py` を新設。既存 `notion_ops` / `notion_logger` の薄いオーケストレータ。
**全記録はこのファサードを通す**（二重投稿を構造的に防ぐ単一入口）。

```python
# 参考スケッチ（実装時は既存 API のシグネチャに合わせて調整すること）
class ResearchLogger:
    def __init__(self, cfg, manager): ...        # configs/notion.yaml と experiment_manager を受ける
    def log_run(self) -> str | None: ...         # metrics.json + eval_recipe + 証拠パスを Run台帳へ冪等 upsert。page_id を返す
    def log_decision(self, decision: Decision): ...# 意思決定ログへ upsert（content-hash で冪等）
    def log_lesson(self, lesson: Lesson): ...     # 失敗知見・教訓へ upsert
    def save_prompt(self, name, body, tags): ...  # プロンプトライブラリへ
    def draft_state_update(self) -> str: ...      # 「現在の研究状態」更新文をドラフト（自動投稿しない）
    def stage_master_diff(self, entry: str): ...  # 進捗反映スナップショットへ「適用待ち差分」を追記
```

### 5.2 自動 run 記録（人手ゼロ）
コンテキストマネージャ + `atexit` フォールバック + デコレータを提供し、**各トレーナの `run()` を 1 行で包む**。

```python
# src/egosurgery/utils/run_logging.py
from contextlib import contextmanager
import atexit

@contextmanager
def run_logging(cfg, manager):
    logger = ResearchLogger(cfg, manager)
    posted = {"done": False}
    def _flush():
        if not posted["done"]:
            try: logger.log_run()           # fail-open
            except Exception: pass
            posted["done"] = True
    atexit.register(_flush)                  # 異常終了でも証跡を投稿（ベストエフォート）
    try:
        yield logger
    finally:
        _flush()
```

**配線対象（README から判明している実行経路すべて）**：
- `src/egosurgery/engines/mmdet_trainer.py::MMDetTrainer.run`（既に投稿しているなら **ファサード経由に統一**して二重化を除去）
- `src/egosurgery/engines/stage_a_trainer.py`、`phase_trainer.py`
- standalone 経路：`scripts/train_s4_tecno.py`、`scripts/run_s0_frozen*.sh` が呼ぶ学習、`scripts/train_b1_mtl.py` /
  `train_b2a.py` / `train_t1a.py` / `train_t1b.py`、`scripts/postprocess_b1.py` / `postprocess_t1b.py`
- これらで `with run_logging(cfg, manager) as rlog:` を学習・評価ループの外側に追加。

### 5.3 半自動 decision / lesson（人間は notes.md に最小入力）
人間が各実験の `notes.md` に **構造化ブロック**（§8）を書くだけで、投稿は自動。LLM に本文を作らせない。

### 5.4 取りこぼし防止スイープ（冪等・常設）
`scripts/sync_experiments_to_notion.py` を新設。`experiments/**` を走査し、
**未投稿の run / notes** を検出して該当 DB へ upsert する。
- 各 run フォルダにローカルマーカー `.notion_sync.json`（`{ "run_ledger_page": "...", "decisions": ["<hash>"], "lessons": ["<hash>"] }`）を置き、
  既投稿は skip（Run台帳を毎回 query しなくても冪等）。
- `--dry-run`（投稿せず差分一覧）、`--since <date>`、`--only run|decision|lesson` を実装。

### 5.5 Claude Code 連携（手動コール無しで capture）
- **フック**：`.claude/hooks/` に Stop（またはトレーニング系コマンド検知の PostToolUse）フックを追加し、
  学習/評価コマンド完了後に `python scripts/sync_experiments_to_notion.py`（**timeout 付き・fail-open**）を実行。
  これで「実験が終わると勝手に台帳へ入る」を実現。**MCP ではなく REST スクリプトを叩く**こと。
- **スラッシュコマンド `/log`**：`.claude/commands/log.md` を追加。現在のチャット文脈から decision/lesson の
  **草案**を作り、対象 run の `notes.md` に §8 ブロックとして追記（人間が確認）→ スイープが投稿。
- **サブエージェント `notion-archivist`**：`.claude/agents/` に追加。セッション終了時に
  「新規 run・新規 notes ブロックの投稿漏れスイープ」＋「マスター適用待ち差分のドラフト」を担当。

### 5.6 マスター昇格（週次・半自動）
`scripts/draft_master_update.py` を新設。前回マージ以降の意思決定・主要 run を集約し、
(a) **§0 変更履歴エントリ** と (b) **進捗反映スナップショットpage への追記ブロック**をドラフト。
**マスター §0 を無人で書かない**（人間がレビューしてマージ）。

---

## 6. 冪等性・キー設計

- **run**：キー = `experiment_id`（例 `s0_001_..._seed42`）。Run台帳の一意プロパティ（例「Run ID」）で upsert。
  既存行があれば update、無ければ create。
- **decision / lesson**：キー = `sha1(title + "\n" + date + "\n" + body)`。`.notion_sync.json` に記録し再投稿を防ぐ。
- **マーカー**：`experiments/<run>/.notion_sync.json`。`.gitignore` に追加（証跡ではなく同期状態のため）。
- **二重投稿防止**：トレーナ内 atexit と外部スイープが両方走っても、マーカーにより 1 回に収束。

---

## 7. ファイル別タスク（マイルストーン順）

### Milestone A — 自動 run 記録の土台
- 追加：`src/egosurgery/utils/research_logger.py`、`src/egosurgery/utils/run_logging.py`、
  `src/egosurgery/utils/idempotency.py`（hash・マーカー読み書き）。
- 変更：`MMDetTrainer.run` ほか 1 経路を `run_logging` 経由へ。**既存の直接投稿があれば除去して二重化を解消**。
- 追加：`tests/test_research_logger.py`（§9 の A 項）。
- **完了条件**：スモーク学習で Run台帳に **ちょうど 1 行**増える／二重実行で増えない。

### Milestone B — notes.md スキーマ＋スイープ
- 追加：`src/egosurgery/utils/notes_schema.py`（§8 ブロックの parser・validator）。
- 追加：`scripts/sync_experiments_to_notion.py`（`--dry-run` 既定で安全）。
- 変更：`scripts/post_experiments_to_notion.py` を新スイープへ委譲 or 統合（重複ロジックを一本化）。
- 追加：`tests/test_notes_schema.py`、`tests/test_sync.py`。
- **完了条件**：`notes.md` に decision/lesson を 1 つ書く → `--dry-run` が **その 1 件だけ**を列挙 → 実投稿で該当 DB に 1 行。

### Milestone C — Claude Code 連携
- 追加：`.claude/hooks/auto_notion_sync.*`（Stop/PostToolUse、timeout・fail-open）、`.claude/commands/log.md`、
  `.claude/agents/notion-archivist.md`。
- 変更：`.claude/settings.json` にフック登録（**Git 管理対象**であることを確認）。
- **完了条件**：学習コマンド終了後にフックがスイープを呼び、台帳が更新される（手動コール無し）。

### Milestone D — マスター昇格ドラフタ
- 追加：`scripts/draft_master_update.py`（§0 エントリ＋スナップショット追記をドラフト、**自動マージしない**）。
- 追加：`.claude/commands/promote-to-master.md`（週次運用の入口）。
- **完了条件**：直近 decision/run から §0 エントリ草案が生成され、進捗反映スナップショットへ追記される。

---

## 8. `notes.md` 構造化スキーマ（人間が書く最小入力）

各実験フォルダの `notes.md` に、以下のフェンス付きブロックを書く。スイープがこれを解析して該当 DB へ投稿する。
**本文は人間が書く**（LLM に作らせない）。複数ブロック可。

````markdown
```decision
title: phase→det は機構非依存で弱い（CA でも overall 非改善）
status: 撤退        # 採用 / 撤退 / 保留 のいずれか
affects: §17.1, 方向非対称の主張
body: |
  oracle-phase を入れても mAP は上がらず、FiLM/CA/rescore の3機構すべてで overall 改善せず。
  情報理論的非対称が確定。§7.5 撤退ラインに到達。
```

```lesson
title: NpzFile 反復展開で RSS 40GB 超 → OOM
recurrence_guard: _index_npz で一括展開する（per-key ループ禁止）
body: |
  eval_det2phase_test.py の npz[key][i] ループが exit 137 の原因。一括展開で RSS 0.9GB に是正。
```
````

- パーサは未知キーを警告して無視（前方互換）。`status` / `affects` は意思決定ログの対応プロパティへ写像。
- ブロックが無ければ何もしない（fail-open）。**数値は書かない**（台帳が持つ）。

---

## 9. 受け入れ基準（pytest + dry-run・必須）

### A. ユニット（`tests/test_research_logger.py` ほか）
- **冪等**：同じ run を 2 回 `log_run()` → Notion 呼び出しは create 1 回のみ（2 回目は update か skip）。モックで検証。
- **fail-open**：`NOTION_API_KEY` 未設定／REST 例外を注入 → 例外を投げず、学習継続。**マーカーは書かない**（未投稿として残す）。
- **notes パーサ**：正常／壊れたブロック／複数ブロック／未知キーを検証。
- **eval_recipe 整合**：不一致 Δ を投稿しようとすると `InconsistentRecipeError`（既存挙動）を尊重。

### B. 統合（dry-run）
```bash
python scripts/sync_experiments_to_notion.py --dry-run        # 未投稿の run/notes を「正確に」列挙
python scripts/draft_master_update.py --dry-run               # §0 エントリ草案を表示（投稿しない）
```

### C. 配線スモーク
```bash
# 内蔵 SimpleDetectionHead の 1-epoch スモークで Run台帳に 1 行だけ増えることを確認
S0_EXTRA_ARGS="train.real_detector=false model.backbone=dinov2_vits14_reg data.limit=16 \
  data.img_size=224 train.epochs=1 train.freeze_backbone=true data.num_workers=0 \
  logging.wandb_enabled=false" bash scripts/run_s0.sh
```

### D. 品質
```bash
ruff check . && black --check . && PYTHONPATH=src pytest tests/ -q   # 既存 28 件 + 新規が全パス
git status --porcelain                                               # .env 等の秘密が混入していないこと
```

---

## 10. 前提・限界（`docs/auto_logging.md` に必ず明記）

1. **「ほぼ全自動」の境界**：*数値*（run）は完全自動。*意思決定／失敗知見*は半自動（人間が notes に最小入力 → 投稿は自動）。
   これは捏造防止のための意図的設計であり、研究インテグリティ上の必須制約。
2. **承認ゲート回避**：自動記録は **REST トークン経路**（`.env`）で行う。Claude の MCP Notion ツール経路は対話承認が必要で
   無人実行に不向き。両者を混在させない。
3. **マスター／状態 prose は人間マージ**：自動はドラフト生成まで。週次／マイルストーンでレビューしてマージ。
4. **二重投稿防止**：全記録は `ResearchLogger` ファサード＋ローカルマーカー＋冪等キーで 1 回に収束。
5. **秘密管理**：`.env`（暗号化運用は `docs/secrets_and_tracking.md` 準拠）。`configs/notion.yaml` は非秘密 ID のみ。

---

## 11. ドキュメント更新（最後に実施）

- `docs/auto_logging.md` を新設：記録ルーティング表（run→台帳／decision→意思決定ログ／lesson→失敗知見／prompt→プロンプトライブラリ／
  state→現在の研究状態／master 昇格→スナップショット）、運用ループ、§10 の限界。
- `docs/notion_integration.md` と `README.md` の Notion 節に、ファサード・スイープ・フックの存在と使い方を追記。
- **マスター M2研究計画の §0 変更履歴に「手動で」エントリを追加**（HARD ルール）。ただし本文への詳細反映は
  進捗反映スナップショットへドラフトを溜め、週次でマージする旨を記す。

---

## 付録：実装の最小コア（参考・要 in-repo 調整）

```python
# src/egosurgery/utils/idempotency.py
import hashlib, json, pathlib

def content_hash(*parts: str) -> str:
    return hashlib.sha1("\n".join(parts).encode()).hexdigest()

def marker_path(run_dir: pathlib.Path) -> pathlib.Path:
    return run_dir / ".notion_sync.json"

def load_marker(run_dir):
    p = marker_path(run_dir)
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: return {}
    return {}

def save_marker(run_dir, marker: dict):
    marker_path(run_dir).write_text(json.dumps(marker, ensure_ascii=False, indent=2))
```

> 上記はあくまで雛形。**実 API（`notion_ops` / `notion_logger` のシグネチャ）・Run台帳のプロパティ名は
> リポジトリ内の実コードから取得して合わせること**。推測で進めない。

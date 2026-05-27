# Notion「実験Run台帳」自動投稿

`MMDetTrainer.run()` の学習完了時に、実験フォルダのメタデータを Notion の
「実験Run台帳」DB に自動で投稿する仕組みのセットアップ・運用ドキュメント。

簡易な概要は [`../README.md` §5](../README.md) を参照。本書はそれを補完し、
**スキーマ要件・手動投稿・既知の制約・トラブルシュート**を扱う。

---

## 1. 全体像

```
学習完了 (rank=0)
   └─ MMDetTrainer.run()
        ├─ best metrics 計算 → metrics.json 書き出し
        ├─ confusion 計算
        ├─ notes.md 更新
        └─ log_experiment_to_notion(exp_dir, status="completed")    ← ここで投稿
                ├─ NOTION_API_KEY / NOTION_DB_ID 未設定なら no-op
                ├─ DB を Name で query → 既存行があれば PATCH、無ければ POST
                └─ 例外発生時も学習プロセスは止めない (warn のみ)
```

- 呼び出し点: `src/egosurgery/engines/mmdet_trainer.py:262`
- 本体: `src/egosurgery/utils/notion_logger.py`
- 設定の雛形: `.env.example` の Notion セクション

### 設計方針

| 原則 | 実装 |
|---|---|
| 学習を絶対に巻き込まない | 例外は全て `warn` で握りつぶし。`metrics.json` 等の証拠は既に書き出し済み。 |
| DDP 重複投稿しない | `manager` は rank=0 のみ存在 (`mmdet_trainer.py:249`)。rank≥1 は早期 return で notion 呼び出しに到達しない。 |
| 冪等 | 同名タイトル (Name) の行があれば PATCH、無ければ POST。実験フォルダ名 = タイトル。 |
| 依存追加なし | `requests` のみ使用 (`mmcv` 経由で既に依存ツリーに入っている)。 |

---

## 2. 事前準備

### 2-1. Notion Integration の作成

1. <https://www.notion.so/profile/integrations> を開く。
2. **New integration** → タイプ「Internal」を選び、ワークスペースを指定。
3. **Capabilities** で `Read content` / `Update content` / `Insert content` を有効化。
4. 作成された **Internal Integration Secret** をコピーする (`ntn_...` または `secret_...`)。
   - これが `NOTION_API_KEY` の値になる。

### 2-2. DB への接続 (Connections)

1. Notion で「実験Run台帳」DB ページを開く。
2. 右上の `...` → **Add connections** → 2-1 で作成した Integration を選択。
3. これにより API キーが当該 DB を読み書きできるようになる。

> **重要**: ワークスペース全体には自動接続されない。**台帳 DB ごとに明示的に Add connections する**必要がある。

### 2-3. Database ID の取得

DB ページの URL は `https://www.notion.so/<workspace>/<DB_ID>?v=<view_id>` の形式。
このうち `<DB_ID>` (32 桁 hex を 8-4-4-4-12 で区切ったもの) が `NOTION_DB_ID` に入る値。

> ⚠️ **Database ID ≠ Data Source ID**。Notion REST API `/v1/databases/{id}/query` は
> **Database ID** を要求する。MCP の data source 系ツールで見える `data_source_id`
> をそのまま入れると `404 object_not_found` で失敗する (本実装の過去事例)。

### 2-4. 環境変数の設定

`~/.zshrc` 等の shell rc に以下を追記して `source` する (推奨)。`.env` で
渡しても良いが、`.env` は `.gitignore` 済み・shell rc はリポジトリ外であり、
**いずれも git に乗らないこと**を確認してから書く。

```bash
export NOTION_API_KEY='ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
export NOTION_DB_ID='ef4ccd02-0a97-41af-814e-9acc44e1e0d3'  # 例
export NOTION_SERVER_OPTION='philip (RTX 6000 Ada)'         # DB の Server select の値と完全一致
# SERVERNAME はサーバ側で既に export 済みのことが多い。未設定なら以下:
# export SERVERNAME='philip'
```

---

## 3. 環境変数一覧

| 変数 | 必須 | 用途 | 未設定時の挙動 |
|---|---|---|---|
| `NOTION_API_KEY` | ✓ | Integration の Bearer token | no-op (学習は通常完走) |
| `NOTION_DB_ID` | ✓ | 投稿先 DB の Database ID | no-op |
| `NOTION_SERVER_OPTION` | 推奨 | Server select の値 (例: `philip (RTX 6000 Ada)`) | Server 列は空のまま作成 |
| `SERVERNAME` | 任意 | GPU Config 列・Server 列 fallback の物理サーバ名 | `exp_dir/server.txt` → `unknown` の順で fallback |

---

## 4. Notion DB のスキーマ要件

`log_experiment_to_notion()` は以下のプロパティを書き込む。**事前に DB 側で同名・
同型のカラムを用意しておくこと**。プロパティ名と型が一致しないと `400 validation_error`。

| プロパティ名 | 型 | 内容 |
|---|---|---|
| `Name` | Title | 実験フォルダ名 (例 `s0_001_maskdino_bbox_seed42`) |
| `Status` | Select | `completed` / `running` / `failed` / `archived` |
| `Step` | Select | `S0`〜`S9` (本実装では `step=` 引数で渡す、既定 `S0`) |
| `Tier` | Select | `must` / `effort` / `cut` (既定 `must`) |
| `Server` | Select | `NOTION_SERVER_OPTION` の値。DB の select 候補に**先に**追加しておく |
| `Seed` | Number | 実験フォルダ名末尾の `seedN` から自動抽出 |
| `Started` | Date | `exp_dir/YYYYMMDD_HHMMSS/` サブディレクトリ名、または exp_dir mtime |
| `Finished` | Date | 最終 `epoch_*.pth` の mtime (status=completed のときのみ) |
| `Primary Metric` | Text | 既定: `tool bbox mAP / AP_50 / AP_75 / AP_rare / AP_common ...` |
| `Result` | Text | `mAP=..., AP_50=..., AP_75=..., AP_rare=..., AP_common=... @ epoch N (best)` |
| `Eval Recipe` | Text | `effective_bs / lr_scaling / test_cfg / split` を 1 行整形 |
| `GPU Config` | Text | `DDP NGPU (<gpu_name> xN) on <server_name>, manual launcher ...` |
| `Commit` | Text | `git_commit.txt` の内容 |
| `Artifacts` | URL | `file:///abs/path/to/exp_dir` |
| `Decision Needed` | Checkbox | 既定 `false` |

### Server select に新しいサーバを追加する手順

DB の Server select に未登録の値を投稿すると `400` になる。新サーバ初投稿前に
**先に DB 側へ select オプションを追加**する。Notion MCP の `notion-update-data-source`
を使う場合の例:

```
ALTER COLUMN "Server" SET SELECT(
    "philip (RTX 6000 Ada)",
    "bengio (RTX A6000)",
    "aolab (RTX 3090)"
)
```

> オプション追加は **既存の選択肢を含めて全列挙**で `SELECT(...)` を書くこと
> (差分指定ではなく全置換のため)。

---

## 5. 動作仕様

### 冪等性
- 同名タイトルが存在 → `PATCH /v1/pages/{id}` で `Status` / `Result` /
  `Eval Recipe` / `GPU Config` / `Finished` のみ更新。
- 存在しない → `POST /v1/pages` で全プロパティを作成。

### no-op 条件
- `NOTION_API_KEY` または `NOTION_DB_ID` が空 → `logger.info` のみ出力して `None` を返す。

### 失敗時の挙動
- Notion API が 4xx/5xx を返す、ネットワークエラー、JSON 不正 等
  → `logger.warning("Notion logging skipped: %s", exc)` を出して関数は `None`。
- `MMDetTrainer.run()` 側でも try/except で包んで `print(...)` のみ。
  **学習プロセス自体は終了コード 0 で完走する**。

### Started / Finished の推定ロジック
- **Started**: `exp_dir/` 配下に `20260525_155843` 形式 (8桁_6桁) のサブディレクトリが
  あればその時刻、無ければ `exp_dir` の mtime。
- **Finished**: `status="completed"` のときのみ、`exp_dir/epoch_*.pth` のうち最終 mtime。
  該当 pth が無ければ現在時刻。

---

## 6. 手動投稿 (running → completed の更新、過去実験の遡及記録)

### 6-1. なぜ必要か

Python は**プロセス起動時に import 済みのモジュールしか使えない**。
`notion_logger.py` の追加**より前に**起動された学習プロセスは、再起動するまで
新コードを読まない。このため:

1. すでに走っている学習を `running` で台帳に置いたあと、自動 PATCH ができない。
2. notion_logger 導入以前の過去実験を遡及登録したい場合。

これらは**実験完了後に 1 行スクリプトを手動実行**して対処する。

### 6-2. 手動投稿コマンド (1 件)

```bash
cd /home/ubuntu/slocal2/m2
.venv/bin/python -c "
from egosurgery.utils.notion_logger import log_experiment_to_notion
r = log_experiment_to_notion(
    'experiments/baselines/s0_009_codetr_bbox_seed456',
    status='completed',
)
print('result:', 'OK' if r else 'failed (env vars unset or API error)')
"
```

### 6-3. 引数のオプション

`log_experiment_to_notion()` は以下のキーワード引数を受け付ける:

| 引数 | 既定 | 用途 |
|---|---|---|
| `status` | `"completed"` | `"running"` / `"failed"` / `"archived"` も可 |
| `step` | `"S0"` | DB の Step select と一致させる |
| `tier` | `"must"` | `"effort"` / `"cut"` |
| `primary_metric` | `"tool bbox mAP / AP_50 / ..."` | 任意のテキスト |
| `extra_result_text` | `None` | Result の末尾に改行付きで追記 |

---

## 7. 既知の制約と回避策

| 制約 | 詳細 | 回避策 |
|---|---|---|
| 走行中のプロセスは新コードを使えない | 学習起動後に notion_logger.py を編集しても反映されない | プロセス完了後に §6 の手動投稿 |
| Server select オプションは事前登録が必要 | 未登録の文字列を投稿すると 400 | §4 の ALTER COLUMN で追加 |
| Database ID と Data Source ID は別物 | data_source_id を入れると 404 | DB ページ URL の hex を採用 |
| `NOTION_VERSION` は `"2022-06-28"` を直書き | Notion 側の breaking change で動かなくなる可能性 | API バージョンを `notion_logger.py:35` で更新 |
| `requests` への依存 | `mmcv` 経由で入っているが、`mmcv` を外すと壊れる | 環境再構築時は `requests` 単独でも確認 |

---

## 8. トラブルシュート

### `OK update_response keys: no-op`
- `NOTION_API_KEY` または `NOTION_DB_ID` が現在のシェルから見えていない。
- 対処: `echo $NOTION_API_KEY` で空文字を確認 → `~/.zshrc` を編集後 `source ~/.zshrc`、
  または `.env` を `set -a; source .env; set +a` で反映。

### `Notion query failed: 404 ... Could not find database with ID`
- `NOTION_DB_ID` に Data Source ID を入れている。Database ID を使う。
- もしくは Integration が当該 DB に Add connections されていない (§2-2)。

### `Notion create failed: 400 ... is not a valid select option`
- Server / Step / Tier / Status のいずれかに、DB に未登録の select 値を投稿した。
- 対処: DB 側の select オプションを先に追加 (§4)。

### `Notion create failed: 400 ... is not a property that exists`
- DB に該当プロパティが無い、または名前/型が一致していない (§4)。

### `Notion ... 401 unauthorized`
- API キーが間違っている / 期限切れ / 失効済み。
- 対処: Integration 画面で再発行し、`.zshrc` を更新。**古いキーが万一リポジトリや
  公開チャネルに出ていたら必ず Regenerate** (旧キーが即座に失効する)。

---

## 9. セキュリティ注意点

- `NOTION_API_KEY` は **Internal Integration Secret** であり、ワークスペース内の
  接続済み DB を全権限で操作できる。コミット禁止。
- 本リポジトリの `.gitignore` 68 行目で `.env` を除外済み。`.env.example` には
  実値を**書かない**(雛形のみ)。
- shell rc (`~/.zshrc` 等) は通常リポジトリ外だが、dotfiles を git 管理している
  場合は対象に含まれていないか確認すること。
- 万一漏えいが疑われたら **即 Regenerate**。旧トークンは Notion 側で即座に失効する。

---

## 10. 関連ファイル

| ファイル | 役割 |
|---|---|
| `src/egosurgery/utils/notion_logger.py` | 本体 (query / create / update / 整形ヘルパ) |
| `src/egosurgery/engines/mmdet_trainer.py:257-264` | 学習完了時の呼び出し点 (rank=0 のみ) |
| `src/egosurgery/utils/experiment_manager.py` | `exp_dir` 採番・`server.txt` 等の証拠生成 |
| `.env.example` (16-25 行) | 環境変数の雛形 |
| `README.md` §5 | 簡易概要 (本ドキュメントへのリンク元) |

---

## 11. 改訂履歴

- 2026-05-27: 初版。S0 baseline 9 件 (MaskDINO / VarifocalNet / Co-DETR) 登録時に
  確立した運用ノウハウを統合。

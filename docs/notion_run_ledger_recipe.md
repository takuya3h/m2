# Notion 実験Run台帳 記録レシピ（Claude Code 用）

全実験 Run を Notion「実験Run台帳」へ**漏れなく**記録するための手順。
2026-06-20、lecun サーバーの 21 Run（s0_frozen/s4_phase/b2a/t1a）が台帳に1件も
記録されていなかった事故（手動転記が server pivot で脱落）を受けて整備。

## 台帳の座標（固定）

- データベース ID: `ef4ccd02-0a97-41af-814e-9acc44e1e0d3`（タイトル「実験Run台帳」）
- データソース URL: `collection://7bcf9406-29fc-4b2a-8a9e-0be02fc1fc20`
- 親ページ: `36bee4d4-7777-803f-9dcc-c5b4ede29412`（管理データベース配下）

## 読み取り（行の確認）

- `query_data_sources`（SQL）は **Enterprise + Notion AI 限定**で本環境では 400 エラー。使わない。
- 行の確認は次で代替:
  - `notion-search`（`data_source_url` を指定）→ 名前・本文の意味検索でヒット確認。
  - `notion-fetch`（行ページ ID）→ 個別行のプロパティ全取得。

## 列 ↔ ローカル証跡 の対応

`ExperimentManager` が各 Run に残す証跡から機械的に転記する。**数値は metrics.json を逐語転記**（捏造禁止）。

| 台帳列(SQLite名) | 型 | 取得元 |
|---|---|---|
| `Name`(title) | text | Run ディレクトリ名 `{step}_{seq:03d}_{desc}_seed{seed}` |
| `Step` | select(S0–S9) | 検出=S0 / 工程=S4。**legacy S 軸に該当バケツが無い結合系(B2a/T1a)は空**にし Name+Tier で識別（偽 S 番号を割り当てない） |
| `Seed` | number | dir 名 / notes.md |
| `Status` | select | completed / running / failed / planned / archived。未達は failed＋Result に理由 |
| `Server` | select | `metrics.json.eval_recipe.server_name`（※後述の「新サーバー対応」） |
| `Primary Metric` | text | 検出=`val/mAP` / 工程=`phase_accuracy` |
| `Result` | text | metrics.json の確定値（mAP/AP50/75 or acc/macro_f1/jaccard/edit + best_epoch） |
| `Eval Recipe` | text | eval_recipe.description / 結合構成（in_dim 等） |
| `GPU Config` | text | `gpu_count` / `effective_batch_size` / lr scaling |
| `Commit` | text | `git_commit.txt`（先頭 10–12 桁） |
| `Tier` | select(must/effort/cut) | 新フレーム Tier0=must / Tier1=effort / Tier2=cut |
| `date:Started:start` (+`:is_datetime`=1) | **datetime** | **必須**。後述「時刻ソース」参照（起動時刻） |
| `date:Finished:start` (+`:is_datetime`=1) | **datetime** | **必須**。metrics.json の mtime（最終評価書き出し＝完了）。秒まで・tz `+00:00` |
| `Artifacts` | url | 任意（W&B run URL 等。本プロジェクト工程系は wandb 未使用＝TensorBoard） |

## Started / Finished の時刻ソース（必須・datetime）

両列とも **datetime（`date:<col>:is_datetime`=1, tz `+00:00`, 秒まで）**で記録する。
証跡ファイルの mtime を素朴に Started に使うと「梱包時刻」を学習時刻と誤記録するので、次の優先順で取る:

- **Started**
  - phase 系（TeCNO 等・ExperimentManager 起動）: `command.sh` 冒頭の `# 生成日時: <ISO+tz>` を使う。
  - 検出（Relation-DETR accelerate）: `command.sh` の `RELDETR_OUTPUT_DIR=..._YYYYMMDD_HHMMSS` に埋め込まれた起動タイムスタンプ。
  - いずれも無ければ 学習ログ(work_dir)の最初の行 / dir 作成時刻。それも無ければ**空**（捏造しない）。
- **Finished**: `metrics.json` の mtime（最終評価書き出し＝完了）。秒まで。
- 注意: 検出の 3-seed バッチは起動 stamp が 3 本共通・metrics も一括梱包で近接することがある（＝Started/Finished が**バッチ粒度の近似**になる）。その旨を行本文 content に明記する。
- 制約: **Notion の date プロパティは分精度**（秒は切り捨て）。数十秒で終わる run は Started==Finished に見える。秒単位の duration が要るときは content/Result に ISO(秒) を併記する。

## 新サーバー対応（重要 / 未登録サーバーでも最初から記録）

`Server` は select で、**`create-pages` は未登録の値を 400 で弾く**（公開 API の auto-create とは挙動が違う）。
新しいサーバーで実験したら、行作成の**前に**オプションを追加する:

1. `notion-fetch collection://7bcf9406-...` で現在の Server オプション全列挙（名前+色）を取得。
2. `update_data_source` で次を実行（**SET は全置換**なので既存を色ごと完全列挙し、新サーバーを1つ足す）:
   ```
   ALTER COLUMN "Server" SET SELECT(
     'bengio':blue, 'RTX 6000 Ada':green, 'A6000':blue, 'A5000':purple,
     'RTX 8000':gray, 'philip (RTX 6000 Ada)':yellow, 'lecun':red,
     '<新サーバー>':<color>)
   ```
   既存オプション名を1つでも落とすと既存行の値が孤立するので必ず全列挙する。
3. これで `create-pages` の `Server` にその名前を書ける。

（色分け/絞り込み UX を捨ててよいなら、`ALTER COLUMN "Server" SET RICH_TEXT` でフリーテキスト化すれば
新サーバーは値を書くだけで済む。現状は select 維持。）

## 行作成（create-pages）

- parent: `{"type":"data_source_id","data_source_id":"7bcf9406-29fc-4b2a-8a9e-0be02fc1fc20"}`
- `properties` は SQLite 列名キーの JSON。select は値の文字列、number は数値、日付は `date:Finished:start` キーに ISO 文字列。
- `content`（本文）に provenance を残す: ローカル path / 証跡一覧 / 「metrics.json から逐語」。
- 大量時は **1 行試験 → fetch/echo 検証 → 残りを一括（最大100/call）→ search で件数確認**。

## インテグリティ規約（厳守）

- metrics / mAP 等を**絶対に捏造しない**。未達は「未達/failed」と正直に。
- legacy Step に該当が無ければ**空**（偽の S 番号を作らない）。
- best_epoch が浅い等の注意点は Result/content に明記（隠さない＝Fail Loud）。

## 即実行チェックリスト

- [ ] 対象 Run に metrics.json/git_commit.txt が実在するか（Read で確認）
- [ ] `eval_recipe.server_name` が Server オプションに在るか。無ければ ALTER で追加（全列挙）
- [ ] 1 行試験 → エコー/プロパティ一致を確認
- [ ] 残りを一括作成 → `notion-search`(data_source) で件数・可視化を確認
- [ ] experiment_log.md に記録した旨を1行残す

---
description: 現在の文脈から decision/lesson の **草案**を作り、対象 run の notes.md に §8 ブロックとして追記する（人間確認・スイープが投稿）
argument-hint: [run_dir] [type=decision|lesson] (省略時は最新 run を自動推定 / type=decision)
---

このスラッシュコマンドは、現在のチャット文脈から得られた知見を **`notes.md` の構造化ブロック**として
追記するためのものです。**実投稿はしません**（後続スイープ `scripts/sync_experiments_to_notion.py` が REST 経由で行う）。

引数: `$ARGUMENTS` （`<run_dir> [type]` または省略）

手順:

1. **対象 run の特定**:
   - 引数で run_dir が指定されたらそれを使う
   - 省略時は `experiments/transfer/` または `experiments/baselines/` の **mtime 最新** ディレクトリを推定
   - 該当が無ければ "対象が見つかりません" と返して終了

2. **草案作成（人間の本文を勝手に LLM 生成しない）**:
   - 直近のチャット要約から `title` のみ抽出してプレースホルダで `body: TODO` を埋める
   - **数値は書かない**（台帳が持つ・§8 鉄則）
   - decision の場合: `status:`（採用/撤退/保留）と `affects:`（影響先 §）を空欄で挿入
   - lesson の場合: `recurrence_guard:` を空欄で挿入（人間が書く）

3. **`notes.md` への追記**:
   - 既存内容の末尾に空行 + 新ブロックを append（既存ブロックには触らない）
   - フェンス記法は `auto_logging_implementation.md §8` のサンプルを正確にコピー

4. **人間への案内**:
   - 「`notes.md` に草案を追記しました。本文を埋めてから次回スイープで投稿されます」と表示
   - `scripts/sync_experiments_to_notion.py --dry-run` での確認方法を案内

5. **投稿は絶対にしない**（このコマンドの責務範囲外）。スイープに任せる。

注意:
- LLM が本文を捏造することは禁止（§2 鉄則 1 数値捏造禁止、§5.3 半自動の原則）。
- 既存の `notes.md` 構造を壊さない。append のみ。
- ファイルが書き込めない場合は理由を表示して終了。

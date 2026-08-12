# 完了報告 — T-2026-08-12-tooling-defect-fixes

## 1. 解決された参照

`contract.inject_verbatim: conventions#prohibitions` の原文:

> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`git --no-pager log -1 --format=%h -- context/conventions.md` の実測は `d422b08` で、
`spec.yaml` の `conventions_rev` と一致した。

L3 プリフライトは `5 PASS / 0 WARN / 4 SKIP / 0 FAIL`。SKIP は
`cuda_ext_loaded`、`deterministic_flags`、impl では対象外の `prereg_committed` と
`frozen_source_hash` だった。

## 2. 実装と判断

- 秘匿検査は、裸の 40 桁 hex を資格情報とみなす規則を外した。環境値の直接照合と
  Notion 鍵接頭辞の検出は維持し、資格情報名に値が代入される形を大小文字非依存かつ
  `_` / `-` 区切り対応で検出する。
- `rich_text` は Python の文字を一つずつ走査し、基本多言語面外の文字を 2 UTF-16 単位として
  数え、2,000 単位を超える直前で分割する。文字の途中では切らない。
- ホスト比較は `casefold()` した値で行い、大小文字だけの差を無視する。別ホストは検出する。
- 固定 `SELF_TASK` に依存した試験を、一時契約または判定状態の直接対照へ置換した。

## 3. ゲート

- G1: PASS。起票者訂正後の範囲で、hex40 偽陽性、`api-key` と小文字 `password` の偽陰性、
  UTF-16 上限超過、ホスト大小文字の偽陽性を再現した。`NOTION_API_KEY` と
  `WANDB_API_KEY` は修正前から検出されていたため回帰対照へ変更した。
- G2: PASS。秘匿七件は全件期待どおり。UTF-16 四入力は最大 2,000 単位以下で、全件の連結が
  元本文と一致した。
- G3: PASS。`Efros` 対 `efros` は 1 件から 0 件へ変化し、別ホストは修正前後とも 1 件。
  対象試験は `2 failed, 35 passed` から `64 passed` へ変化した。全体失敗は 7 件から
  5 件へ減り、残存 5 件は同一内訳だった。

## 4. 完了判定

| # | 実測結果 |
|---|---|
| 1 | PASS。該当実装と判定式を `audit.md` に行番号つきで記録した。 |
| 2 | PASS。裸の 40 桁 hex が修正前に 1 finding、修正後に 0 finding。 |
| 3 | PASS（訂正後範囲）。`api-key` と小文字 `password` は修正前 0、修正後 1 finding。NOTION/W&B は前後とも 1 finding。 |
| 4 | PASS。修正前の先頭切片は 2,010 UTF-16 units。 |
| 5 | PASS（人工入力）。`Efros` で修正前 1 warning。固定契約依存の対象試験は 2 failed。 |
| 6 | PASS。訂正後の秘匿七件は `all_seven_pass True`。 |
| 7 | PASS。`Permission denied (publickey,password)` を含む本文は finding 0。 |
| 8 | PASS。追加試験を旧実装へ当てると 6 failed。 |
| 9 | PASS。修正後の最大 UTF-16 units は元入力 2,000、境界三入力も最大 2,000 以下。 |
| 10 | PASS。元入力と境界三入力は全件 `joined=True`。 |
| 11 | PASS。本契約 P9 は `spec_lint PASS`。 |
| 12 | PASS。別ホスト人工入力は修正後も `hits=1`。 |
| 13 | PASS。比較可能な全体試験は 7 failed から 5 failed、対象範囲は 2 failed から 0 failed。 |
| 14 | PASS。残存は engine 証跡 1 件、research logger の空 metrics 仕様 4 件。 |
| 15 | PASS。この表の 1〜14 にすべて実測値を記載した。 |
| 16 | PASS。未併合 0、禁止領域 violations 0。変更は道具・試験・契約・専用 inbox と必須 README 更新。 |
| 17 | UNKNOWN。push 前。 |
| 18 | UNKNOWN。PR 作成前。 |
| 19 | UNKNOWN。報告送信直前まで同期抑止を維持中。 |
| 20 | UNKNOWN。`make task-report` 実行前。 |

## 5. 試験

- 追加試験＋旧実装: `6 failed, 58 passed`
- 修正後近接試験: `64 passed`
- 修正前全体: `7 failed, 407 passed, 14 skipped`
- 修正後全体: `5 failed, 430 passed, 4 skipped`
- ruff: `All checks passed!`
- `git diff --check`: exit 0

pass / skip 数の差は、一時 worktree に現行 repo の未追跡データ manifest を持ち込まなかったため。
失敗内訳は対象 2 件だけが消え、既存 5 件が残ったことをファイル名で突合した。

## 6. 起票者の欠陥

1. `self_contradiction`: 前提節が契約自身の取り込みを未追跡物として停止対象にしていた。
   Task 5 Step 5 では本契約のディレクトリを許容しており、同一契約内で不整合だった。
2. `asserted_without_measuring`: 欠陥 2 の根拠にした前契約の実測は報告本文への grep 式であり、
   `report_task.py` の秘匿検査ではなかった。実測すると NOTION/W&B は既に検出され、実際の
   取りこぼしは `api-key` と小文字 `password` だった。

## 7. deviations

- 実行者の判断による機能範囲の逸脱はなし。ユーザーによる停止条件と G1 の訂正は起票者欠陥への
  対処として適用した。
- プロジェクト最上位指示がコード変更後の README 更新を必須とするため、契約 Files 欄外の
  `README.md` に現在の実装状態を追記した。

## 8. 未解決と配布

- PR: UNKNOWN
- commit: UNKNOWN
- 台帳送信: UNKNOWN
- 残存 5 テストは本契約の対象外であり、変更していない。

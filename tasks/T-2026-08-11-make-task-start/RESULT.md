# T-2026-08-11-make-task-start — 完了報告

契約の取り込み開始を一つの操作にまとめた。`make task-start TASK=<task_id>` を追加し、
分岐の作成・同期の抑止・契約の取り込みを 1 操作で行う。

**起票者の中心的な推測は実測で否定された。** 起票者は「識別子から日付を剥がしたものが
分岐名」と考えていたが、**分岐が現存する 23 契約のうち 10 件は手で短縮されていた。**
規則は既に守られていたのではなく、**守られていなかった。** 本 task の動機はむしろ強まる。

---

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]` — `context/conventions.md` の
`#prohibitions` アンカーの原文（`conventions_rev: d422b08`、実測で一致・置換不要）:

> ## prohibitions
>
> | id | 禁止事項 |
> |---|---|
> | `no_split_redefine` | split を再定義しない |
> | `no_raw_write` | `data/raw` `data/external` に書き込まない |
> | `no_frozen_change` | 凍結源を変更しない |
> | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
> | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`meta.created_from.runindex_commit` は `UNKNOWN` だったため、実測した `44697d9`
（`2026-08-11T08:41:54+00:00`）に置換した。SPEC が定める手順であり逸脱ではない。

---

## 2. 検証と事前検査

| 段階 | 結果 |
|---|---|
| `make task-validate` | exit 0、WARN 0 件 |
| `make task-preflight` | **4 PASS / 4 SKIP / 0 FAIL** |

**SKIP は「合格」ではなく「実行されなかった」を意味する。** SKIP された 4 項目:
`P2 cuda_ext_loaded` と `P3 deterministic_flags`（`plan.env.preflight` に記載なし）、
`P4 prereg_committed` と `P5 frozen_source_hash`（`kind: impl` のため対象外）。

---

## 3. 実装した操作の使い方と、成功後の状態

    source .venv/bin/activate && source scripts/load_env.sh
    make task-start TASK=T-YYYY-MM-DD-slug

**`source` の 2 行は残る。** make はサブシェルでレシピを動かすため、呼び出し元のシェルへ
環境を返せない。まとめられるのは残りの 4 行である。

成功後の状態（実測、`audit/case_normal.txt`）:

| 確認 | 実測 |
|---|---|
| 現在の分岐 | `feat/s0-reevaluation-feasibility`（導出名と一致） |
| `.sync-pause` | 存在する |
| `tasks/<task_id>/` | 展開されている |
| 展開されたファイル | `SPEC.md` `spec.yaml` |
| `make task-validate` | exit 0（`OK / 0 failed`） |

### 実装の要点

`scripts/task_start.sh`（新規）と `Makefile` への追記（新規ターゲットのみ）。
スクリプトは 9 段階で動き、**各段階の前に前提を確認し、満たさなければ何もせずに停止する。**

| 順 | 動作 | 満たさないときの終了コード |
|---|---|---|
| 1 | 識別子の形式（`T-YYYY-MM-DD-slug`、slug は小文字英数とハイフン 3〜60 字） | 2 |
| 2 | 仮想環境が有効か（`VIRTUAL_ENV`） | 3 |
| 3 | 資格情報が**存在するか**（`NOTION_API_KEY`。**値は見ない・出さない**） | 3 |
| 4 | 作業ツリーが汚れていないか | 3 |
| 5 | 分岐が既に存在しないか | 3 |
| 6 | `git fetch origin` | 4 |
| 7 | 分岐を作って切り替える（起点 `origin/phase0`） | 4 |
| 8 | `.sync-pause` を作る（**実行前の有無を先に控える**） | — |
| 9 | 契約を取り込む（`make task-notion` を再利用。複製しない） | 4（**7 と 8 を巻き戻す**） |

**巻き戻しの範囲。** 元の分岐名を段階 6 の前に控え、失敗時はそこへ戻してから新しい分岐を
削除する。`.sync-pause` は**自分が作った場合にのみ**消す。実行前から存在していた場合は
触れない（実測で確認済み。§4 の case 5）。

---

## 4. 異常系 5 通りの実測結果

**「通ること」だけを確かめていない。止まるべきときに止まることを測った。**
記録は `audit/case_*.txt`。

| # | 起こした状況 | 停止 | 分岐 | `.sync-pause` | 契約dir | 汚れ |
|---|---|---|---|---|---|---|
| 1 | 識別子を空にする | **した**（使い方を表示） | 残らず | 保持 | 無し | 0 |
| 2 | 形式を崩す（`not-a-task-id`） | **した** | 残らず | 保持 | 無し | 0 |
| 3 | 作業ツリーを汚す | **した** | 残らず | 保持 | 無し | 1 → 片付け後 **0** |
| 4 | 同じ識別子で二度実行 | **した** | 既存のまま | 保持 | 既存のまま | 0 |
| 5 | **台帳に無い識別子** | **した** | **残らず** | **保持** | **無し** | **0** |

**5 番が本命である。** 分岐 `feat/no-such-contract` が実際に作られたあと、取り込みの失敗を
受けて巻き戻され、`branch_exists=no` / `task_dir=no` / `porcelain=0` に戻った。
現在の分岐も実行前の `feat/make-task-start` へ復帰している。

### 巻き戻しが `.sync-pause` を作った場合の挙動も測れた

`T-2026-08-12-probe-intake` を正常系に使おうとした試行で、**実行前に `.sync-pause` が
無い状態**から分岐と `.sync-pause` が作られ、取り込みの失敗で巻き戻された。
結果は `sync_pause=no`、すなわち**自分が作った分だけが消えた**。
実行前からある場合（case 5）と作った場合の**両方が実測できている。**

### 陽性対照 — 痕跡確認そのものが働くこと

    git branch feat/__probe_only__     → 「検出できた」
    git branch -D feat/__probe_only__  → 「消えた」

**両方が出た。** 痕跡確認は何も見ていないわけではない。

---

## 5. 終了コードの実測（スクリプト単体と `make` 経由）

**`make` 経由の終了コードは make 自身のものである（失敗時は一律 2）。**
スクリプトの区別は make 経由では失われる。

| 場面 | `bash scripts/task_start.sh` | `make task-start` |
|---|---|---|
| 正常系 | **0** | **0** |
| 1 識別子が空 | **2** | 2 |
| 2 形式が不正 | **2** | 2 |
| 3 作業ツリーが汚れている | **3** | 2 |
| 4 分岐が既に存在する | **3** | 2 |
| 5 台帳に無い識別子（巻き戻し） | **4** | 2 |

**二度実行しても壊れない。** 正常系の直後に同じ識別子で実行すると
「分岐が既に存在します」で停止し（script=3 / make=2）、`.sync-pause` は保持され、
作業ツリーの汚れは 0 のままだった（`audit/case_second.txt`）。

---

## 6. 起票者の推測のうち、実測で裏づけられたもの・否定されたもの

### 否定された — 分岐名の導出規則（本 task の中心）

起票者は「識別子から日付までを剥がしたものが分岐名」と考えていた。
**契約 30 件について集合演算で測った結果、この規則に従っているのは 13 件だけだった。**

| 区分 | 件数 |
|---|---|
| 導出名の分岐が実在する | **13** |
| **人が短縮していた** | **10** |
| 分岐が存在しない（統合後に削除された等） | 7 |

短縮の実例（語の集合が導出名の真部分集合であるものを機械的に抽出）:

| 実在する分岐 | 導出されるはずだった名前 |
|---|---|
| `feat/report-back` | `T-2026-08-18-report-back-to-ledger` |
| `feat/report-projection` | `T-2026-08-17-report-projection-and-friction` |
| `feat/template-and-autosync` | `T-2026-08-15-template-leak-and-autosync-conflict` |
| `feat/attachment-transport` | `T-2026-08-14-bundle-attachment-transport` |
| `feat/implementation-history` | `T-2026-08-13-implementation-history-index` |
| `feat/notion-distribution` | `T-2026-08-12-contract-distribution-via-notion` |
| `feat/env-loader-portability` | `T-2026-08-12-env-loader-shell-portability` |
| `feat/inbox-split` | `T-2026-08-11-inbox-per-task-split` |
| `feat/identity-and-tracking` | `T-2026-08-11-identity-tracking-and-harvest-scope` |
| `feat/branch-naming` | `T-2026-08-10-branch-naming-and-canonical-index` |

契約と対応しない分岐が 3 件ある（`feat/analysis-artifacts` `feat/runindex-analysis`
`feat/sync-automation-20260805`）。うち `feat/analysis-artifacts` は
`T-2026-08-10-analysis-artifact-integration` の短縮に見えるが、
**語が `artifacts` と `artifact` で異なるため集合の包含では対応しない。**
目視で対応づけず、対応しないものとして数えた。

**導出規則は `T-YYYY-MM-DD-<slug>` → `feat/<slug>`（そのまま）と定めた。** 外れ値 10 件は
いずれも「人が短くした」結果であり、規則そのものに欠陥があるわけではない。既存の分岐は
改名しない（統合済み・PR 進行中のものがあるため）。**今後作る分岐が規則に従う。**

### 否定された — 正常系の検査に使える契約

SPEC は「台帳にある未取り込みの契約を使う」としたが、**未取り込みの 5 件のうち 4 件は
`superseded` で取得できなかった**（`probe-intake` `probe-roundtrip` `probe-attachment`
`probe-report`）。取得可能な未取り込み契約は `T-2026-08-11-s0-reevaluation-feasibility`
の 1 件だけだった。**これを検査に使い、検査後に手元を片付けた。** 取り込みは台帳を
変更しない読み取り操作であり、この契約は台帳に残っているため後続の実行に影響しない。

### 裏づけられた — `task-notion` の失敗時挙動

実装（`tools/fetch_task.py`）を読んで確定した。**推測で書いていない。**

| 確認事項 | 実装の答え |
|---|---|
| 引数の受け取り方 | Makefile が `TASK=`、スクリプトは `--notion <task_id>` |
| 失敗時の終了コード | `1`（`make` 経由では 2） |
| 既に `tasks/<task_id>/` がある場合 | `ensure_absent` が失敗させる。**上書きしない** |
| 必要な環境変数 | `NOTION_API_KEY`（**名前のみ記録。値は扱わない**） |
| 展開先と失敗時に残るもの | `tasks/<task_id>/`。検証に落ちれば `rollback()` が削除し、**消えたことを確認**する |

`fetch_task.py` は一時ディレクトリへ書いてから `tasks/` へ移し、`mkdir` で名前を
アトミックに確保して**この run が作ったものだけ**を巻き戻す。SIGTERM も巻き戻しの
経路に載せてある。**この設計をそのまま踏襲した。**

### 裏づけられた — 対話シェルの注意

SPEC の「配列の添字による終了コードの取得は使えない」は正しかった。
`${PIPESTATUS[0]}` は空文字を返し、case 2 の終了コードが測れなかった。
**パイプを使わずに測り直した**（§10 の逸脱 4）。

---

## 7. 変更範囲

| ファイル | 種別 |
|---|---|
| `scripts/task_start.sh` | **新規** |
| `Makefile` | **追記のみ**（10 行追加・**削除行 0**） |
| `tasks/README.md` | 追記（取り込み手順に 1 操作の形を追加） |
| `tasks/inbox.d/T-2026-08-11-make-task-start.md` | 判断の受け皿 |
| `context/auto/` 3 ファイル | **生成物**（`make taskindex`。`taskindex-check` は exit 0） |
| `tasks/T-2026-08-11-make-task-start/` | 契約・報告・`audit/` 7 ファイル |

`context/auto/` は SPEC の想定変更範囲に挙がっていないが、手順書が「報告を書いたら投影に
現れることを確かめる」ことを求めている。**手編集ではなく生成であり**、禁止事項が挙げる
`src/` `configs/` `experiments/` `data/` `runindex/` のいずれにも該当しない（§10 の逸脱 7）。

`git diff Makefile | grep -c '^-[^-]'` は **0**。既存レシピは 1 行も変えていない。
追記位置は 178 行目の直前（`task-report` のレシピと空行の後、`clean:` の前）で、
**直前の行が `^I` で始まらないことを `cat -A` で確認してから挿入した**（G1）。

---

## 8. 判断が要る事項

### データに触れない契約が、意味のないプレースホルダを書き続けている

**本契約自身が初回配布時にこれで検証に落ちた**（`inputs.data.split_files` が空配列）。
実測は次のとおり。

スキーマが最低 1 件を要求する欄は **9 個**（走査 9 = `grep -c minItems` 9 で漏れなし）:
`inputs.data.split_files` / `inputs.code.entrypoints` / `contract.inject_verbatim` /
`contract.prohibitions` / `plan.phases` / `prereg.stop_conditions` /
`outputs.must_have` / `outputs.acceptance` / `governance.integrity`。

既存契約 30 件の `split_files` の実測:

| 値 | 本数 |
|---|---|
| `['data/splits/ego_val.txt']` | **29** |
| `['data/splits/ego_train.txt', 'data/splits/ego_val.txt', 'data/splits/ego_test.txt']` | 1 |

`entrypoints` に `src/` `data/` `configs/` `scripts/train` を含む契約は **1 本だけ**
（`T-2026-08-11-split-and-recipe-audit`）。**残る 29 本はデータに触れないのに
`split_files` を埋めている。** 埋めた値は検証を通すためだけのものである。

**三択を提示する。本 task では直していない。**

1. **スキーマを緩める** — `inputs.data` を任意にする、または `split_files` の
   `minItems` を外す。最も単純だが、**データを扱う契約で欄が空のまま通る**ようになる。
2. **`kind` に応じて必須を分ける** — `kind: exp` と `analysis` では必須、
   `impl` では任意にする。意図に最も忠実だが、スキーマの条件分岐が増える。
3. **慣行として残す** — プレースホルダを書き続ける。変更は不要だが、
   **起票のたびに同じ失敗が起こりうる**（起票者の自己検査はスキーマ検証を含まない）。

**直さなかった理由**: スキーマの変更は既存 30 契約の検証結果を変えうる。
性質の異なる変更を同じ PR に混ぜない。

### 起票者の自己検査にスキーマ検証が含まれていない

申し送りによれば起票前の自己検査は 3 項目で、スキーマ検証を含まない。
**本契約は実際にそれで落ちた。** 落ちる欄は取り込み時まで分からない。
起票側で `jsonschema` による検証を回すか、台帳へ置く前に `--pack` で
組み立てて検証するか、いずれかを決める必要がある。**本 task の対象外である。**

---

## 9. Phase A〜C の完了判定の対応

| 判定項目 | 対応する実測 |
|---|---|
| 現在値の確認と置換 | `conventions.md` = `d422b08`（一致・置換不要）、`runindex` = `44697d9`（置換した） |
| 追記位置の行番号とタブ確認 | 178 行目の直前。直前行は空行で `^I` 始まりでない（`cat -A` で確認） |
| `task-notion` の 5 項目 | §6「裏づけられた」の表。実装から確定 |
| 分岐名の導出規則と外れ値 | §6。一致 13 / 短縮 10 / 分岐なし 7、外れ値は全件列挙 |
| 前提の確認方法 | §3 の 9 段階。資格情報は真偽のみ（陽性対照で未読込 `False` → 読込後 `True`） |
| 最低 1 件を要求する欄の一覧 | §8。9 個、`grep -c` と一致 |
| スクリプトが 9 段階を持つ | §3 の表 |
| 実行前の `.sync-pause` の有無を記録 | §3。case 5 と probe 試行の**両方**で実測 |
| 元の分岐名を控えている | §3。段階 6 の前に控える |
| Makefile の差分が追加のみ | §7。削除行 **0** |
| 異常系 5 通りの停止と痕跡 | §4。全件で停止・痕跡なし |
| 痕跡確認の陽性対照 | §4。「検出できた」と「消えた」の両方 |
| 正常系の 5 項目 | §3 の表。全て確認 |
| 終了コード（両系統・正常異常） | §5 |
| 二度実行の挙動 | §5。壊れずに停止・`.sync-pause` 保持 |

**UNKNOWN として残った項目は無い。**

---

## 10. deviations（逸脱）

1. **検査記録を作業ツリーの外（スクラッチ）で取り、最後に `audit/` へ移した。**（spec_defect）
   SPEC は `A=tasks/<task_id>/audit` へ case ごとに書けと指示するが、**その書き込み自体が
   作業ツリーを汚す。** スクリプトは段階 4 で汚れを検知して停止するため、case 4 と 5 は
   意図した経路（分岐の重複／取り込みの失敗）に到達せず、すべて「汚れている」で止まる。
   **指示どおり実行すると、本命の case 5 を一度も測れない。**
2. **正常系の検査に実契約 `T-2026-08-11-s0-reevaluation-feasibility` を使った。**（judgement）
   probe 行 4 件はすべて `superseded` で取得できなかった。取り込みは台帳を変更しないため
   後続に影響しない。**検査後に分岐と展開物を片付け、元の分岐へ戻った。**
3. **二度実行の初回測定を破棄して測り直した。**（judgement）
   正常系の成功後は `origin/phase0` から作られた分岐にいるため、そこに `task_start.sh` は
   まだ無く、`script=127`（file not found）になった。**実装の欠陥ではなく測定の副作用**で
   あり、統合後は解消する。元の分岐へ戻ってから測り直した。
4. **`${PIPESTATUS[0]}` を使った case 2 の測定を破棄し、パイプ無しで測り直した。**（environment）
   対話シェルが zsh のため空文字が返った。**SPEC の注意どおりだった。**
5. **Makefile のレシピに `TASK` 空の番人を置かなかった。**（judgement）
   SPEC は「`TASK` が空のときは使い方を出して停止すること」と書くが、既存の `task-*`
   ターゲットはいずれも番人を持たず、値の検査を呼び先の実装に委ねている。
   スクリプトが使い方を出して 2 で止まり make も止まるため要件は満たされる。**慣例に合わせた。**
6. **`meta.created_from.runindex_commit` を `UNKNOWN` から `44697d9` に置換した。**（judgement）
   SPEC が定める手順であり逸脱ではないが、契約ファイルへの変更であるため記録する。
7. **`context/auto/` の 3 ファイルを生成して変更に含めた。**（judgement）
   SPEC の想定変更範囲には無いが、手順書が投影への反映を確かめるよう求めている。
   **手編集ではなく生成であり**、禁止事項の対象（`src/` `runindex/` 等）にも該当しない。

---

## 11. 生成物

| ファイル | 内容 |
|---|---|
| `scripts/task_start.sh` | 取り込み開始の 1 操作。9 段階・巻き戻しつき |
| `Makefile` の `task-start` | 追記のみ。既存レシピ無変更 |
| `audit/case_1.txt` 〜 `case_5.txt` | 異常系 5 通りの痕跡確認 |
| `audit/case_normal.txt` | 正常系の 5 項目 |
| `audit/case_second.txt` | 二度実行の挙動 |

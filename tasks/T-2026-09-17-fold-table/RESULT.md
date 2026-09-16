# RESULT — T-2026-09-17-fold-table

5-fold の折り表を A1 の材料から確定し、`context/conventions.md` に `folds` 節として置いた。残件三つも反映した。

## 1. 解決された参照

| 記載 | 解決先 | 値 |
|---|---|---|
| `contract.conventions_rev`（占位） | `context/conventions.md` を最後に変えた commit | `4300b7d2` |
| `meta.created_from.runindex_commit`（占位） | `runindex/` を最後に変えた commit | `96eb3a1c` |
| `meta.created_from.counts`（0 のまま） | `runindex/*.csv` の行数（ヘッダ除く） | index 1266 / experiments 285 / verdicts 1506 |
| `contract.inject_verbatim` | `conventions#prohibitions`（表 5 行）、`conventions#issuer_cautions`（注意 13 件＋実測 3 件＋シェルの前提） | 原文のまま適用。要約していない |
| `contract.allow_write` | `context/conventions.md` | `forbidden-check` の `permitted` に 1 件として現れた |

`inputs.sigma_policy` と `inputs.frozen_source.ref` は本契約に無い（`kind: impl`・GPU 不使用）。

## 2. 判定

**verdict: pass（ただし `forbidden-check` は非ゼロ。理由は §6）**

| Gate | 判定 | 根拠 |
|---|---|---|
| G1（A1 の材料が実在し、15 動画が公式分割と一致） | **通過** | 材料を A1 の表から写さず同じ出所から読み直し、総フレーム 17233 / images 15437 / boxes 49652 が A1 の合計行と一致。工程・術具・HTS のいずれも公式分割 15 動画との集合差 **0 件** |
| G2（制約をすべて満たし、再実行で同一の表） | **通過** | 制約違反 0 件。二度の生成で要約値が一致し、ファイルも byte 一致（`eb66170a8565b993…`） |

`escalate_if` の 3 条件はいずれも該当しなかった（材料の欠落なし／合計 15／`issuer-defects.md` は生成物でない）。

## 3. 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 15 動画が 5 折りに過不足なく | 制約検査の違反 **0 件**。各動画が test にちょうど一度 | 動画 `02` を折り B と C の test に置くと `動画 02 が test に現れた回数が 1 でない: ['B','C']` で落ちた |
| b | 折り A が公式分割に一致 | test `04, 05, 07` = `ego_test.txt`、val `09, 10` = `ego_val.txt` | test の一本を `01` へ入れ替えると `折り A の test が公式 test と一致しない` で落ちた。val の入れ替えも同様に落ちた |
| c | B〜E の test 3 本・val 2 本・非重複 | 4 折り × 3 = 12 本。val は自分の test と交わらず、全折りを通じて各動画高々一度 | val に自分の test の動画を入れると `val が test と重なる`、折り C の val を D と同じにすると `動画 04 が val に 2 回以上現れる`、test を 2 本にすると `test が 3 本でない` で落ちた（計 7 対照すべて狙った文言で一致） |
| d | 決定性 | 二度の要約値 `237837faa843e1b3…` が一致。ファイルも `sha256 eb66170a8565b993…` で byte 一致 | 入力を一行変える（動画 01 の `anesthesia` に +100000 フレーム。記憶上のみ）と要約値は `febee3775bec5785…` へ**変わった** |
| e | 均衡指標 | 定義・折りごとの値・最大差を表と共に記載。折り B〜E の `max d = 0.2844` / `min = 0.2628` / **最大差 0.0216** | 無作為（**seed 20260917**）は `max d = 0.6102` → **悪化していない**。さらに全数列挙 15400 通りの分布（最小 0.2844 / 中央 0.5246 / 最大 0.7972）に対し提案の表は**最小値そのもの** |
| f | 追加 6 動画 | `17, 18, 19, 20, 21, 22`。15 動画との重複 **0 件**、公式 test との重複 **0 件**（val・train とも 0） | 追加動画の集合へ `04` を混ぜると重複 **1 件** `['04']` → 集合演算は重複を検出できる |
| g | `conventions#folds` が L2 で引ける | `conventions_anchors()` に `folds` が現れた（アンカー 9 → 10）。表の数値は docs と**差分 0 行** | `conventions#folds_zz` は引けない（陰性対照） |
| h | 残件三つ | docs-check 対象 **42 → 43**（食い違いなし・exit 0）。変更履歴に `a8c07e81` 行。`issuer-defects.md` に **4 件**追記 | `issuer-defects.md` は生成物でない（`generated_locations()` は `context/auto/` と `tasks/inbox.md` のみ）ので手編集した。3 ファイルとも **削除行 0** |
| i | PR が Draft でなく存在 | §7 に記載 | 分岐名 **`feat/fold-table`**（`task_start.sh` が識別子から機械的に導いた） |

## 4. 実測

### 折り表

| 折り | test（3） | val（2） | train（10） | d(test) |
|---|---|---|---|---|
| A | 04, 05, 07 | 09, 10 | 01, 02, 03, 06, 08, 11, 12, 13, 14, 15 | 0.2966（固定・最適化対象外）|
| B | 01, 03, 14 | 02, 08 | 04, 05, 06, 07, 09, 10, 11, 12, 13, 15 | 0.2844 |
| C | 02, 08, 11 | 06, 12 | 01, 03, 04, 05, 07, 09, 10, 13, 14, 15 | 0.2628 |
| D | 06, 13, 15 | 04, 05 | 01, 02, 03, 07, 08, 09, 10, 11, 12, 14 | 0.2667 |
| E | 09, 10, 12 | 07, 15 | 01, 02, 03, 04, 05, 06, 08, 11, 13, 14 | 0.2811 |

**均衡指標** `d(S) = TV(工程比率, 全15動画) + TV(術具クラス比率, 全15動画)`（`TV` は全変動距離）。
選び方は `max_f d(test_f)` → `sum_f d(test_f)` → 動画識別子の辞書順。
12 動画の分け方 **15400 通りを全数列挙**したので、選ばれた表は近似ではなく最適である。

**HTS は 15 動画すべてが 3 系統とも持つため、どの折りの test も 3/3 で、偏りは原理的に生じない。**

### その他の実測

| 項目 | 値 |
|---|---|
| アンカー数（`context/conventions.md`） | 9 → **10**（`folds` を追加）|
| `conventions_rev` | 前 `4300b7d2` → 後 `PENDING`（commit 後に埋める。変更履歴の行も同様）|
| conventions.md の行数 | 260 → 297（**+37 行、削除 0**）|
| `make docs-check` の対象数 | 42 → **43** |
| 試験 | **6 failed / 535 passed**（直前契約の基準と同一。増減 0）|
| `git stash list` | **4 件**（本契約が 2、前契約が 2。前契約のものには触れていない）|

## 5. 起票者の誤り

**1 件。**

1. **`asserted_without_measuring`** — SPEC Task D-3 は 4 件の出所を `T-2026-09-16-evidence-map-ab/RESULT.md §4・§5`
   と書くが、当該 §4 は「起票者の誤り **無し**」と述べている（3 件目は §4 の「補足（誤りではない）」、
   4 件目は §5 の「逸脱 2（judgement）」）。また 2 件目の型を `asserted_without_measuring` と指定するが、
   出所の `T-2026-09-16-proposal-gate/RESULT.md §4-2` は **`check_does_not_check`** と分類している。
   4 件とも内容は実測で裏が取れたため契約の指定どおり書き、食い違いをここに記録する。

## 6. 逸脱

1. **`decisions_required` の 2 件を利用者へ諮り、回答を得てから続行した**（judgement）。
   P6 が FAIL で止まったため手順どおり停止した。回答は (1) 同点は SPEC Task B §2 の辞書順で決着させ、
   辞書順でも決まらない場合だけ停止、(2) 追加 6 動画の重複は陽性対照つきで再実測し 0 件を記録して続行。
   **実行の結果、いずれの条件も発生しなかった**（同点は 1 通り、重複は 0 件）。
   回答は `spec.yaml` の `meta.amendments` と `tasks/inbox.d/` に記録し、`decisions_required` を空にした。
2. **`spec.yaml` を編集した**（judgement）。`REPLACE-BY-EXECUTOR` の占位 2 件を実測値へ確定し（Task A-5）、
   `decisions_required` を空にした。いずれも `meta.amendments` に記録した。
3. **`forbidden-check` が `violations` 7 件で非ゼロのまま終えた**（environment）。
   7 件は**すべて syncthing の一時ファイル** `experiments/analysis/**/.syncthing.*.py.tmp` である。
   開始時に stash した 31 件の削除（`experiments/analysis/**/*.py` を含む）を syncthing が他ホストから
   復元した際の取り残しで、**mtime は 20:06 で 8 分後も変化なし、内容は復元済みの `.py` と byte 一致**、
   syncthing は稼働中（`pgrep -a syncthing` で確認）。**実行者が作ったファイルではない。**
   SPEC §4 前文が「禁止は実行者の操作に対するものであり、同期処理による配布を含まない」と定め、
   禁止事項 4 が `experiments/**` に触れることを禁じるため、**削除せず記録した。**
   `permitted` は要求どおり `context/conventions.md` **1 件**である。
4. **`make taskindex` / `make inbox` を実行していない**（judgement）。SPEC 禁止事項 3 が並行契約との衝突を
   理由に `context/auto/*` と `tasks/inbox.md` の再生成を禁じているため。**投影への反映は未確認である。**
   前契約 `T-2026-09-16-evidence-map-ab` も同じ理由で同じ逸脱を記録している。
5. **作業ツリーの退避に `git stash` を使った**（judgement。SPEC Task A-1 が許している）。
   追跡下の削除 31 件を `stash@{1}`、未追跡 2 件を `stash@{0}` へ。
   `task_start.sh` は `git status --porcelain` が非ゼロなら exit 3 で止まる実装のため、未追跡も退避が要った。
6. **生成器を `tools/` ではなく `scripts/analysis/a1_fold_table.py` に置いた**（judgement）。
   同ディレクトリが解析用スクリプトの既存の置き場であり、SPEC 申し送りが並行契約に「`tools/` の新規一件」を
   割り当てているため、生成物の分離を保った。

## 7. 想定外・UNKNOWN

- **投影（`context/auto/`・`tasks/inbox.md`）への反映は UNKNOWN。** 逸脱 4 のとおり再生成を禁じられている。
  並行契約の統合後に一台で回す必要がある。
- **`conventions_rev` と変更履歴の commit 欄は `PENDING`。** commit 後に確定する値であり、未測定のまま
  数値を置かない。
- **L2-6 の WARN は出なかった。** SPEC §2 は規約ファイルの変更で全契約に出ると述べるが、本契約の
  L1+L2 は規約を変える前に実行したためである。規約を変えた後に他契約を検証すれば出るはずだが、
  **本契約では測っていない（UNKNOWN）。**
- PR 番号と push の終了コードは §8 に記す。

## 8. 送出

（commit・push・PR・`make task-report` の結果をここに記す）

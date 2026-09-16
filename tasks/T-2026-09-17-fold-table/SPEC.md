# 5-fold の折り表を A1 の材料から確定し、context/conventions.md に節として置く

**task_id:** T-2026-09-17-fold-table  **kind:** impl

## 1. 背景

関門 G0 の三条件のうち「折りが固定された」が未成立で、Stage 1 以降の全契約がこれを待っている。
一度 Stage 1 を走らせてから折りを変えると、それ以前の run が比較不能になる。だから今、固定する。

決め方の正本は Notion M §3.1（利用者が 2026-09-17 に承認）。要点を写す。

- 対象は Tool subset の 15 動画（両ラベルが要る）
- 動画単位の 5-fold。**折り A は Tool 公式 test と val に固定。** 折り B〜E は残り 12 動画を 3 本ずつ
- 各折りの val 2 本は事前登録した表で固定する
- 割り当ては Stage 0 で実測した工程分布・術具出現数・HTS 注釈の有無を見て決める
- 折り表は `context/conventions.md` に新しい節として置き、他の頁には数値を書かない

Stage 0 で材料は `docs/stage0/A1_fold_material.md` に用意されている（起票者は本文を読んでいない。
本契約が読む）。

**本契約では GPU を使用しない。**

## 2. 確定した事実（ホストによらない値だけ）

- 公式分割は `data/splits/ego_train.txt`、`ego_val.txt`、`ego_test.txt`。過去の実測で実体は 10／2／3 の 15 動画
  （`PAPER_SPLIT_VIDEOS` は名称に反し Tool subset。tasks/todo.md の 2026-06 の記録）
- 工程塔 P\*-21 は 15 動画に追加 6 動画（訓練のみ）を足す。追加 6 動画と test 折りの重複、Phase 公式 test
  との重複は Stage 0 で確認する、と M §3.3 にある。A1 の材料に無ければ本契約で測る
- `context/conventions.md` は forbidden-check の禁止ファイル。**本契約は `contract.allow_write` に宣言済み**
- 逐語注入のアンカーは `[a-z0-9_]` のみ。新節のアンカーは `folds`
- L2-6 の WARN は規約ファイルが変わると全契約に出る（注入アンカーを見ない）。想定内で FAIL ではない
- `make forbidden-check` は開始前から在る未追跡も列挙する。消さず記録する
- 対話シェルは zsh。`git --no-pager`。命令ごとにシェルが新しくなる実装系があるため `make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装と材料を読んで決めてよい。** 出力は `audit.md` に残す。

### Task A — 開始状態と材料

1. 作業ツリーの清浄を確かめる。開始前から在る未追跡は repo 外へ**移動**で退避し、退避先と件数を記録する
   （前契約では `git stash push -u` が使われた。それでもよいが、報告に stash の名前と件数を残す）
2. `docs/stage0/A1_fold_material.md` を読み、15 動画の識別子・工程分布・術具出現数・HTS 注釈の有無が
   揃っているかを記録する。欠けていれば停止（escalate_if）
3. 公式分割の三ファイルの動画識別子を読み、合計 15 で A1 の 15 と集合として一致することを確かめる
   （集合差 0 件。名前の部分一致で見ない）
4. 追加 6 動画の識別子を A1 かデータの注釈から得て、15 動画との重複 0 件、Phase 公式 test との重複の有無を記録する
5. `conventions_rev` と `runindex_commit` を実測し spec.yaml の占位を差し替える。アンカー数を記録する

### Task B — 折り表の生成

**達成すべきこと**（手段は実行者が決める。決定的で、再実行しても同じ表が出ること）:

1. 制約（必ず満たす）
   - 折り A: test = 公式 test（3 本）、val = 公式 val（2 本）、train = 残り 10 本
   - 折り B〜E: test は公式 train の 10 本と公式 val の 2 本、計 12 本を 3 本ずつ。各動画は test にちょうど一度
   - 各折りの val 2 本は、その折りの test と重ならない動画から選ぶ。val も表で固定する
2. 目的（制約の中で良くする）
   - 折り間で工程分布（工程ごとのフレーム数の比率）と術具出現数（クラスごとの box 数）ができるだけ均衡する
   - HTS 注釈のある動画が一つの折りに偏らない
   - 均衡の指標は実行者が定義してよい。**定義と値を表と一緒に書く。** 候補が同点なら動画識別子の辞書順で決める
3. 対照
   - 無作為割り当て（seed を書く）を一件作り、同じ指標で比べる。提案の表が無作為より悪ければ手続きを疑う
   - 制約検査を機械で行い、制約に反する表（例: 同じ動画を二つの test に置く）を与えて検査が落ちることを一度示す
4. 出力: `docs/stage0/A1_fold_table.md`。表（折り／test／val／train）、均衡指標の定義と折りごとの値、
   無作為対照との比較、追加 6 動画の重複確認、手続きの記述（再現に要る入力と規則）

複数の表が同点で規則でも決まらない場合は、候補を並べて停止し利用者に諮る（decisions_required）。

### Task C — conventions.md に節を置く

1. 既存節の本文を変えず、ファイル末尾（`proposal_gate` 節の後）に `folds` 節を置く。既存節と同じ形のアンカー要素
2. 節の内容: 表（折り／test 動画／val 動画）、追加 6 動画の一覧と用途（訓練のみ。test には現れない）、
   規律の一文（選定・early stopping・ハイパラ・界面の型の選択は折り内 val、test は腕ごとに一度）、
   出所（`docs/stage0/A1_fold_table.md`、本契約の task_id）
3. 変更履歴の表に本契約の行を足す（commit は commit 後に埋める）

### Task D — 残件三つ（前契約の申し送り）

1. `docs/docs_audit.md` に `docs/proposal-gate.md` を登録し、`make docs-check` の対象数が 42 から 43 になることを記録する
2. `context/conventions.md` の変更履歴に、欠落している `a8c07e81`（2026-08-25、issuer_cautions 節の追加）の行を足す。
   既存行は変えない
3. `docs/issuer-defects.md` に 2026-09-16 の起票者の誤り 4 件を追記する。型と内容は次のとおり。
   出所は `tasks/T-2026-09-16-proposal-gate/RESULT.md` §4 と `tasks/T-2026-09-16-evidence-map-ab/RESULT.md` §4・§5
   - self_contradiction: 規約ファイルへの追記を命じながら allow_write を宣言しなかった
   - asserted_without_measuring: L2-6 が inject_verbatim を見ると書いたが実装は見ない
   - asserted_without_measuring: repo に無い報告ファイルの名前とバイト数を書けと指示した
   - self_contradiction: 付録に無い節を完了判定で要求した
   同ファイルが生成物で手編集できないなら、触らず停止して諮る（escalate_if）

### Task E — 検証と報告

1. L1、L2、`make forbidden-check`（`permitted` に conventions.md が一件、`violations` 0）、
   `make spec-check TASK=T-2026-09-17-fold-table`、`make docs-check`、試験
2. 完了判定 a〜i を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/T-2026-09-17-fold-table.md`
4. commit、push、PR（Draft でない）。分岐名が `feat/fold-table` であることを記録する
5. 報告後に `.sync-pause` を移動で解除する

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. `data/splits/` の既存ファイルを変えない（公式分割の再定義に当たる）。折り表は conventions と docs に置く
2. `context/conventions.md` の既存節の本文を変えない（変更履歴への行追加と末尾への新節は除く）
3. `context/auto/*` と `tasks/inbox.md` を再生成しない。並行契約があるため統合後に一台で回す
4. `experiments/**`、`data/raw`、`data/processed`、`runindex/**` に触れない
5. 既存の `tasks/*/` を変えない
6. 開始前から在る未追跡を消さない
7. 均衡のために動画を除外しない。15 動画すべてを使う
8. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 15 動画が 5 折りに過不足なく | 各動画が test にちょうど一度 | 同じ動画を二つの test に置いた表で制約検査が落ちる |
| b | 折り A が公式分割に一致 | test 3 本・val 2 本が集合として一致 | 公式 test の一本を入れ替えた表で検査が落ちる |
| c | B〜E の test 3 本、val 2 本、非重複 | 4 折り × 3 = 12、val が test と交わらない | val に test の動画を入れた表で検査が落ちる |
| d | 決定性 | 二度の実行で表が同一 | 同一性は要約値で比べる。入力の一行を変えると表が変わることを一度示す |
| e | 均衡指標 | 定義・折りごとの値・最大差が表と共にある | 無作為割り当て（seed 記録）より悪化していない。悪化なら手続きを疑い報告する |
| f | 追加 6 動画 | 15 動画との重複 0、Phase 公式 test との重複の有無 | 集合差で数える。重複を一件作った入力で 1 になることを示す |
| g | `conventions#folds` が L2 で引ける | 解決結果に表が現れる | `conventions#folds_zz` で失敗する。表の数値が docs の表と一致（差分 0 行） |
| h | 残件三つ | docs-check 対象 42→43、変更履歴に a8c07e81 行、issuer-defects に 4 件 | それぞれ前後の件数を記録。issuer-defects が生成物なら触らず UNKNOWN |
| i | PR が Draft でなく存在 | PR 番号 | 分岐名 `feat/fold-table` |

## 6. 想定外と停止条件

- A1 の材料が欠ける、公式分割の合計が 15 でない → 停止して諮る
- 同点の表が規則で決まらない → 候補を並べて停止（decisions_required）
- 追加 6 動画が Phase 公式 test と重複 → 記録して停止（decisions_required）。表の生成自体は続けてよい
- `docs/issuer-defects.md` が生成物 → 触らず記録
- 実行基盤が書き込みや `rm` を拒む → 回避せず提示

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。目安百五十行以内。

| 節 | 内容 |
|---|---|
| 判定 | `verdict` と各 Gate |
| 完了判定 | 表。各項目に実測値 |
| 実測 | 折り表そのもの、均衡指標、追加 6 動画の重複、アンカー数、conventions_rev 前後、docs-check の対象数 |
| 起票者の誤り | 型と内容。一件三行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、終了コード |

`audit.md` へ命令と出力の全文、制約検査の対照の出力、無作為対照の出力、変更範囲の一覧。

## 8. 申し送り

- 本契約と `T-2026-09-17-tier1-cost-estimate` は並行する。生成物は分かれている（本契約: conventions、docs/stage0/A1_*、
  docs/docs_audit.md、docs/issuer-defects.md。相手: docs/stage0/B1_*、tools/ の新規一件）
- 前契約の実行ホストに `git stash` が残っている可能性がある。本契約は触らない。報告で `git stash list` の件数だけ記録する
- 均衡指標の定義は実行者に委ねる。ただし「何を均衡させたか」を表に書かなければ、後で表を疑えない

# 教師データ — 起票者の誤りの全件と検出可能性

`tasks/*/result.yaml` の `issuer_defects` を全件抽出したもの。**本文は原文である。**
要約していない。分類と理由は実行者が書いた。

教師データは**固定である**（禁止 8）。過去の `result.yaml` を書き換えないため、
本表を作り直す必要は無い。検出率の判定に使う機械可読の対応は
`tests/test_check_spec.py` の `TEACHER` が持つ。**本文はそこと突き合わせて固定してある。**

## 1. 対象の一覧

一覧は 3 通りの方法で取り、完全に一致した（`ls` の glob / `find` / `git ls-files`）。
いずれも 13 件を返し、差分は無い。**素朴な glob は雛形を拾う。**

| 項目 | 件数 |
|---|---|
| 契約ディレクトリ `tasks/T-*` | 35 |
| glob `tasks/*/result.yaml` が拾う対 | 13 |
| うち契約でないもの（雛形） | 1 |
| 実契約の対 | 12 |
| **対を持たない契約** | **23** |

除外したもの: `tasks/_templates/result.yaml`

雛形を除外した理由。`issuer_defects: []` は placeholder であり実測ではない。
教師データに混ぜると検出率の分母が汚れる。

対を持たない契約の一覧（本契約自身を含む）:

- `T-2026-08-03-task-contract-bootstrap`
- `T-2026-08-05-l2-task-id-uniqueness-fix`
- `T-2026-08-06-frozen-source-and-sigma-notation`
- `T-2026-08-06-make-context`
- `T-2026-08-07-propagation-and-distribution`
- `T-2026-08-07-task-preflight`
- `T-2026-08-08-regex-audit-and-cleanup`
- `T-2026-08-08-session-durability`
- `T-2026-08-08-stdin-intake-and-anchor-cleanup`
- `T-2026-08-09-run-wiring-verification`
- `T-2026-08-09-scoped-integration`
- `T-2026-08-09-wiring-followup-and-integration`
- `T-2026-08-10-analysis-artifact-integration`
- `T-2026-08-10-branch-naming-and-canonical-index`
- `T-2026-08-10-conventions-survey`
- `T-2026-08-10-third-host-verification`
- `T-2026-08-11-canonical-index-refresh`
- `T-2026-08-11-identity-tracking-and-harvest-scope`
- `T-2026-08-11-inbox-per-task-split`
- `T-2026-08-11-issuer-defect-detector`
- `T-2026-08-11-leftover-relocation`
- `T-2026-08-12-contract-distribution-via-notion`
- `T-2026-08-12-env-loader-shell-portability`

## 2. 型ごとの件数

| 型 | 件数 |
|---|---|
| `check_does_not_check` | 12 |
| `asserted_without_measuring` | 13 |
| `self_contradiction` | 11 |
| `shell_assumption` | 3 |
| **合計** | **39** |

`issuer_defects` が空の対: 0 件。12 件すべてが 1 件以上を持つ。

契約ごとの件数:

| 契約 | 版 | 件数 |
|---|---|---|
| `T-2026-08-11-artifact-merge-and-pause` | 2 | 3 |
| `T-2026-08-11-codex-parity` | 2 | 4 |
| `T-2026-08-11-hts-comparability-audit` | 2 | 3 |
| `T-2026-08-11-make-task-start` | 2 | 3 |
| `T-2026-08-11-s0-reevaluation-feasibility` | 2 | 4 |
| `T-2026-08-11-split-and-recipe-audit` | 2 | 4 |
| `T-2026-08-13-implementation-history-index` | 1 | 3 |
| `T-2026-08-14-bundle-attachment-transport` | 1 | 5 |
| `T-2026-08-15-template-leak-and-autosync-conflict` | 1 | 4 |
| `T-2026-08-16-docs-reconciliation` | 1 | 3 |
| `T-2026-08-17-report-projection-and-friction` | 2 | 2 |
| `T-2026-08-18-report-back-to-ledger` | 2 | 1 |

## 3. 検出可能性の分類

| 分類 | 件数 | 意味 |
|---|---|---|
| `syntactic` | 3 | 契約の本文の構文から検出できる |
| `structural` | 13 | 契約の構造どうしの矛盾から検出できる |
| `semantic` | 23 | 意味論。構文でも構造でも捕まらない |
| **合計** | **39** | 第 2 節の合計と一致すること |

合計の一致: **一致** （型ごと 39 / 分類ごと 39）

**検査の対象は `syntactic` と `structural` の 16 件である。**
`semantic` の 23 件は検査の対象にしない。

### 分類の境界について

`structural` の定義は「契約の構造どうしの矛盾」だが、`host_mismatch` の 2 件は
**本文の宣言と実行環境の事実**の照合である。構文単体では判定できず、
契約どうしの矛盾でもない。機械で確実に検出できるため `semantic` には入れなかった。
3 分類の定義がこの型を持たないことを申し送りに記す。

## 4. 全件

`規則` は Phase B で実装した検査規則の名。空欄は規則を持たない。

### syntactic（3 件）

#### `T-2026-08-11-codex-parity#1`

- **型**: `shell_assumption`
- **契約**: `T-2026-08-11-codex-parity`（報告の版 2）
- **SPEC の該当箇所**: UNKNOWN（監査対象の手順書側の記述であり、本 SPEC 内の行を特定できない）
- **規則**: venv_dependent_without_source

本文（原文）:

> 現行手順はsourceで読み込んだ仮想環境と資格情報が次の命令へ残る前提で、sourceとmakeを別行にしていた。指示どおりCodexへ別命令として渡すとPROBEもVIRTUAL_ENVも未設定になり、preflightはvenv_active FAILで停止した

#### `T-2026-08-11-hts-comparability-audit#3`

- **型**: `shell_assumption`
- **契約**: `T-2026-08-11-hts-comparability-audit`（報告の版 2）
- **SPEC の該当箇所**: Phase A Step 2（SPEC.md:136）
- **規則**: unquoted_glob

本文（原文）:

> SPEC Phase A Step 2 の grep コマンドが --include=*.md を引用していない。実行シェルは zsh であり、グロブが展開に失敗して no matches found となり 0 件を返す。指示どおり実行し 件数だけを見ると「領域注釈の監査物が 1 件も無い」と誤読する。SPEC 自身が注意 8 で 「変数の直後に記号が続く場合は波括弧で囲む。実行シェルは bash ではない」と警告しながら、 自らのコマンドが同種の罠を踏んでいる。引用して再実行し 25 件を得た。

#### `T-2026-08-17-report-projection-and-friction#2`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-17-report-projection-and-friction`（報告の版 2）
- **SPEC の該当箇所**: Task 6 Step 2（SPEC.md:279）
- **規則**: truncation_in_measurement

本文（原文）:

> Task 6 Step 2 が案を読むために示した探し方 grep -rn スタンプ ... | head は、表示用の切り詰めによって肝心の案の一覧（3 案が並ぶ行）を落とす。指示どおり実行すると案を読まずに選ぶことになり、SPEC 自身が注意 3 で禁じた「記録を作る流れに表示用の切り詰めを混ぜない」を起票者が犯している

### structural（13 件）

#### `T-2026-08-11-codex-parity#2`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-11-codex-parity`（報告の版 2）
- **SPEC の該当箇所**: Task 4 Files 欄 と Task 5 の検査要求
- **規則**: files_vs_check

本文（原文）:

> Task 4の変更ファイルはskillとtasks/READMEの2文書だけと指定したが、Task 5はMakefileとdocsを含む同じ69文書を検査対象にするよう要求した。指示どおり全体検査すると追加4文書が違反となり、列挙ファイルだけではG2を通せなかった

#### `T-2026-08-11-codex-parity#4`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-11-codex-parity`（報告の版 2）
- **SPEC の該当箇所**: 手順 6 と Phase C 完了判定 14
- **規則**: forbidden_vs_output

本文（原文）:

> 手順6はRESULTとresult.yamlを書いた後にmake taskindexを実行してcontext/autoへ投影することを必須とするが、Phase Cの完了判定14はcontext/autoを含む差分が空であることを要求する。指示どおり投影すると必ず3生成物が表示され、両要件を同時に満たせない

#### `T-2026-08-11-hts-comparability-audit#2`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-11-hts-comparability-audit`（報告の版 2）
- **SPEC の該当箇所**: SPEC 冒頭「先に確定していること（再検証しない）」 と Phase B Step 4
- **規則**: reverify_contradiction

本文（原文）:

> SPEC は同じ事実について再検証を禁じる記述と要求する記述を両方持つ。冒頭は 460 フレームの 構造的除外を「先に確定していること（再検証しない）」に置くが、Phase B Step 4 は 「実装とデータの両方を読み、実数と内訳を出す」「Skewer と Mouth Gag に偏っているという 記述が実データで確かめられるかを見る」と再検証を要求する。前者に従えば測らず後者に従えば測る。 実際に測った結果、前者の記述が誤りだった。後者に従ったため誤りを検出できた。

#### `T-2026-08-13-implementation-history-index#1`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-13-implementation-history-index`（報告の版 1）
- **SPEC の該当箇所**: 禁止 6（SPEC.md:41） と Task 2 の生成先・判定 20（SPEC.md:266）
- **規則**: forbidden_vs_output

本文（原文）:

> 禁止 6 が context/auto/** を挙げる一方で Task 2 は同じ場所へ生成させる。判定 20 を素直に読むと自分の成果物で不合格になる。禁止を『手による編集』と読んで解決した

#### `T-2026-08-13-implementation-history-index#2`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-13-implementation-history-index`（報告の版 1）
- **SPEC の該当箇所**: 判定 10 と Files 欄
- **規則**: files_vs_check

本文（原文）:

> 判定 10 が context-check の exit 0 を要求するが、Files に tools/build_context.py が無い。既存の検査は context/auto/ の全ファイルを走査するため、変更なしでは新しい出力を差分と見なして必ず非ゼロになる

#### `T-2026-08-14-bundle-attachment-transport#3`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-14-bundle-attachment-transport`（報告の版 1）
- **SPEC の該当箇所**: SPEC.md:6「実行ホスト: lecun」
- **規則**: host_mismatch

本文（原文）:

> 実行ホストを lecun と指定しているが、実行環境は bengio である。ホスト固有の前提は本 task には無かったため bengio で実行した

#### `T-2026-08-14-bundle-attachment-transport#5`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-14-bundle-attachment-transport`（報告の版 1）
- **SPEC の該当箇所**: 禁止 9（SPEC.md:55） と SPEC.md:270
- **規則**: integration_prohibited_without_pause

本文（原文）:

> 禁止 9 は統合を禁じるが、常駐の m2-sync.sh が 30 分毎に作業分岐へ origin/phase0 を自動 merge する。20:06:40 に auto-merge が実行され、実行者の操作なしに merge commit 9d89a7b が入った。契約が環境の既定動作と衝突している

#### `T-2026-08-15-template-leak-and-autosync-conflict#1`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-15-template-leak-and-autosync-conflict`（報告の版 1）
- **SPEC の該当箇所**: 禁止 4（SPEC.md:42） と Task 1 Step 5
- **規則**: forbidden_vs_output

本文（原文）:

> 禁止 4 が runindex/** の手編集を禁じる一方、Task 1 Step 5 は起票を指示する。この repo の起票先 backlog.md は runindex/ 配下にある。投影の出所が生成器の BACKLOG 定数（ast.literal_eval で読む）だと実装で確かめ、生成器だけを編集して解決した

#### `T-2026-08-15-template-leak-and-autosync-conflict#2`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-15-template-leak-and-autosync-conflict`（報告の版 1）
- **SPEC の該当箇所**: 禁止 9（SPEC.md:221） と 判定 8
- **規則**: integration_prohibited_without_pause

本文（原文）:

> 禁止 9 が統合を禁じる一方、判定 8 は無効時に書き込むことの確認を求める。契約の分岐で測ると自分で禁止 9 を破る。HOME を差し替えた隔離環境で実物のスクリプトを走らせて解決した

#### `T-2026-08-15-template-leak-and-autosync-conflict#3`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-15-template-leak-and-autosync-conflict`（報告の版 1）
- **SPEC の該当箇所**: 判定 15（SPEC.md:206） と 判定 5
- **規則**: forbidden_vs_output

本文（原文）:

> 判定 15「禁止領域が無変更」と判定 5「件数が増える」が両立しない。件数が現れる投影 context/auto/open_questions.md は禁止 4 の領域にある。禁止を「手による編集」と読み、make context による生成として解決した

#### `T-2026-08-16-docs-reconciliation#2`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-16-docs-reconciliation`（報告の版 1）
- **SPEC の該当箇所**: 判定 5（SPEC.md:266）
- **規則**: （規則を実装しない。Phase C の様式で構造的に防ぐ）

本文（原文）:

> 判定 5『検査が実在を確かめる／現行手順の文書が通る』は、検査の対象一覧が正しいことを確かめない。対象が 42 件でなく 25 件へ落ちていても通るため合格する。実際に落ちたが、判定ではなく件数の表示で気付いた

#### `T-2026-08-16-docs-reconciliation#3`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-16-docs-reconciliation`（報告の版 1）
- **SPEC の該当箇所**: SPEC.md:6「実行ホスト: bengio」
- **規則**: host_mismatch

本文（原文）:

> 実行ホストを bengio と断定しているが、契約は lecun へ配布され lecun で実行された。起票時に配布先を測っていない。測定対象がホストに依存しないため作業内容は変えていない

#### `T-2026-08-17-report-projection-and-friction#1`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-17-report-projection-and-friction`（報告の版 2）
- **SPEC の該当箇所**: G1（SPEC.md:153） と Task 8（SPEC.md:332）
- **規則**: gate_requires_report_before_end

本文（原文）:

> G1 が Phase A の直後に「本 task 自身の完了報告を拡張した様式で書き、投影を生成する」ことを求める一方、報告の作成は Task 8 に置かれている。指示どおり Phase A の直後に評価しようとすると、まだ測っていないゲートの判定や試験の件数を書くことになり、禁止 10「未測定の値を書かない」と衝突する

### semantic（23 件）

#### `T-2026-08-11-artifact-merge-and-pause#1`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-artifact-merge-and-pause`（報告の版 2）
- **SPEC の該当箇所**: Task 1 Step 2
- **規則**: —
- **`semantic` と分類した理由**: grep が各ファイルで何件返すかは走査対象の中身に依存する。契約の本文だけでは一致件数が 0 になるファイルがあることを判定できない。命令を実際に走らせる以外に知る道がない。

本文（原文）:

> Task 1 Step 2 の生成物一覧の取り方（grep -n "NAME = \|_NAME\b" を 3 生成器へ）は 9 件を 返すがすべて build_taskindex.py からで、build_inbox.py と build_context.py は 0 件である。 指示どおり一覧を作ると生成物 8 件のうち 3 件しか拾えず、tasks/inbox.md と build_context 由来の 4 件が漏れる。Phase B Step 1 が「Task 1 Step 2 と同じ取り方にする」と指示している ため、誤りがそのまま検査器の除外一覧へ伝播し、生成物が違反として検出されることになる。

#### `T-2026-08-11-artifact-merge-and-pause#2`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-artifact-merge-and-pause`（報告の版 2）
- **SPEC の該当箇所**: Task 3 Step 3
- **規則**: —
- **`semantic` と分類した理由**: 空振りだと分かるには「清潔な作業ツリーでは生成器が差分を作らない」という実行時の性質を知る必要がある。契約の本文には生成器の挙動が書かれていない。

本文（原文）:

> Task 3 Step 3 は「make taskindex && python tools/check_forbidden.py で生成物だけの差分では 0」を期待するが、清潔な作業ツリーでは生成器が差分を作らないため excluded=0 のまま exit 0 に なる。指示どおり実行しても除外が効いていることを一切示せない空振りの検査である。実際に 実行したところ生成器は差分を作らず、起点を HEAD~1 に変えて初めて除外の発火を測れた。

#### `T-2026-08-11-artifact-merge-and-pause#3`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-artifact-merge-and-pause`（報告の版 2）
- **SPEC の該当箇所**: Task 3 Step 5
- **規則**: —
- **`semantic` と分類した理由**: 2 つの終了コードに差が出る根拠があるかは Makefile のレシピとスクリプトの関係を読まないと判定できない。「前提とする」という語だけでは正誤が決まらない。

本文（原文）:

> Task 3 Step 5 は script_exit と make_exit について「両方を記録する。値が異なることを 前提とする」と書くが、実測ではどちらも 0 で標準出力もバイト一致だった。差が出る根拠は 示されていない。指示どおり「異なる」を前提に読むと、同一であることを異常と誤読しかねない。

#### `T-2026-08-11-codex-parity#3`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-codex-parity`（報告の版 2）
- **SPEC の該当箇所**: 隔離の原因を測る手順
- **規則**: —
- **`semantic` と分類した理由**: 因果対照が成立しないと分かるには、設定の開始値が既に目標値と同じであることを実行環境から読む必要がある。契約の本文は開始値を持たない。

本文（原文）:

> 隔離の原因を測る手順は現在値を記録した後、常にkernel.unprivileged_userns_cloneを1へ設定する。今回の開始値は既に1だったため、仮にsudoできても同じ値の再設定となり、隔離命令が通るかの因果対照を作れない

#### `T-2026-08-11-hts-comparability-audit#1`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-hts-comparability-audit`（報告の版 2）
- **SPEC の該当箇所**: SPEC 冒頭「先に確定していること（再検証しない）」
- **規則**: —
- **`semantic` と分類した理由**: 断定が誤りだと分かるには注釈データを実際に集計する必要がある。除外率が 0.00% かどうかは契約の本文からは決まらない。

本文（原文）:

> SPEC 冒頭の「先に確定していること（再検証しない）」で「hand_tool_seg の生成経路は Mouth Gag と Skewer と器具なしフレームを構造的に除外する」と断定した。実測では Skewer の除外率は 0.00%（0/343）、器具の箱が 1 つも無いフレームは 460 中 6 枚、 Mouth Gag は 2.74% で全体基準 2.98% より低い。指示どおり再検証せずに信じていれば、 交絡源を Skewer と読み違えたまま設計判断に進んでいた。実際の偏りは希少工程にあり （irrigation 8.47%・anesthesia 6.81%）、向きが逆である。

#### `T-2026-08-11-make-task-start#1`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-make-task-start`（報告の版 2）
- **SPEC の該当箇所**: 検査の記録手順（case 4・5）
- **規則**: —
- **`semantic` と分類した理由**: 矛盾に気付くには、検査対象のスクリプトが段階 4 で作業ツリーの汚れを検知して停止するという実装の性質を読む必要がある。契約の本文はスクリプトの停止条件を持たない。

本文（原文）:

> 検査の記録手順が、その検査自身を壊している。case ごとの記録を tasks 配下へ書けと指示するが、書いた瞬間に作業ツリーが汚れ、スクリプトは段階 4 の汚れ検知で停止する。case 4 と 5 は意図した経路を通らず、本命である巻き戻しの検証が一度も行われない

#### `T-2026-08-11-make-task-start#2`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-make-task-start`（報告の版 2）
- **SPEC の該当箇所**: 分岐名の規則の記述
- **規則**: —
- **`semantic` と分類した理由**: 規則が守られているかは過去 30 件の分岐名の分布という repo の外部状態に依存する。契約の本文からは規則の充足率を判定できない。

本文（原文）:

> 分岐名は識別子から日付を剥がしたものだと書いたが、これは過去の分岐名からの推測だった。契約 30 件を集合演算で測ると規則に従うのは 13 件で、分岐が現存する 23 件のうち 10 件は人が短縮していた。規則は守られていたのではなく守られていなかった

#### `T-2026-08-11-make-task-start#3`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-make-task-start`（報告の版 2）
- **SPEC の該当箇所**: 正常系の検査の入力指定
- **規則**: —
- **`semantic` と分類した理由**: 使える行が何件あるかは外部の配布台帳の状態（superseded の印）に依存する。契約の本文には台帳の各行の状態が書かれていない。

本文（原文）:

> 正常系の検査に台帳の未取り込み契約を使えと書いたが、未取り込み 5 件のうち 4 件は superseded で取得できなかった。使えるのは実契約 1 件だけで、検査用の行を用意したつもりが実際には使えない状態になっていた

#### `T-2026-08-11-s0-reevaluation-feasibility#1`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-s0-reevaluation-feasibility`（報告の版 2）
- **SPEC の該当箇所**: 走査能力の陽性対照
- **規則**: —
- **`semantic` と分類した理由**: 対照が目標の性質を再現しないと分かるには、rglob が根の symlink は辿るが途中のsymlink は辿らないという標準ライブラリの挙動を知る必要がある。本文からは決まらない。

本文（原文）:

> 走査能力の陽性対照が、確かめたい性質を確かめていない。symlink を走査の根に置いているため rglob も検出してしまい、前 task の致命的欠陥である途中のディレクトリが symlink という状況を再現しない。この対照を通しても、後続の走査が安全である保証は得られない

#### `T-2026-08-11-s0-reevaluation-feasibility#2`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-s0-reevaluation-feasibility`（報告の版 2）
- **SPEC の該当箇所**: Phase C の成果物走査
- **規則**: —
- **`semantic` と分類した理由**: 見落としが起きると分かるには、索引が指すディレクトリと重みが実在するディレクトリが別であるという repo の配置を読む必要がある。契約の本文には両者の対応が無い。

本文（原文）:

> Phase C の成果物走査が索引パスのみを対象としている。索引は 6 点証跡のディレクトリを指しており重みは別の同名ディレクトリにあるため、指示どおり実行すると重みを持つ run は 11 件しか見つからず codetr の 1.13 GB 三件を見落とす。起票者が最も恐れた誤結論そのものである

#### `T-2026-08-11-s0-reevaluation-feasibility#3`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-s0-reevaluation-feasibility`（報告の版 2）
- **SPEC の該当箇所**: eval_recipe_id の扱い
- **規則**: —
- **`semantic` と分類した理由**: id が 10 キーのハッシュだと分かるには実装を読む必要がある。契約の本文は id の構成要素を持たないため、6 種類という数え方の誤りを本文だけでは判定できない。

本文（原文）:

> 6 種類の eval_recipe_id を 6 種類の評価条件として扱ったが、実装では id は split サイズと GPU 構成も含む 10 キーのハッシュである。後処理の設定だけで数えると 4 系統であり、dacdetr の topk 記法を NMS-free と読めば実効的には 2 系統にすぎない

#### `T-2026-08-11-s0-reevaluation-feasibility#4`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-s0-reevaluation-feasibility`（報告の版 2）
- **SPEC の該当箇所**: 系統差の分離可能性の記述
- **規則**: —
- **`semantic` と分類した理由**: 分離が可能だと分かるには、同一検出器が両系統で評価された実例が索引に存在することを調べる必要がある。契約の本文には索引の中身が無い。

本文（原文）:

> 系統差が検出器の実力差と分離できないと書いたが、同一検出器 maskdino が両系統で評価されている実例が既に存在した。その差は 0.000333 で σ の 0.05 倍であり、検出器間の幅 約 4.6σ と比べて無視できる。分離は再評価なしで可能だった

#### `T-2026-08-11-split-and-recipe-audit#1`

- **型**: `shell_assumption`
- **契約**: `T-2026-08-11-split-and-recipe-audit`（報告の版 2）
- **SPEC の該当箇所**: Phase B Step 1
- **規則**: —
- **`semantic` と分類した理由**: 自明な 0 だと分かるには、動画ディレクトリ 15 本が symlink であるという repo の配置と、rglob が symlink を辿らないという挙動の両方を知る必要がある。本文にはどちらも無い。

本文（原文）:

> Phase B Step 1 が Path.rglob で画像を数えるが、動画ディレクトリ 15 本は全て symlink であり rglob は辿らない。指示どおり実行すると画像 0 枚・split 跨ぎ 0 件という自明な 0 が返り、それを健全の証拠として読むと分割を一度も測らないまま健全と結論する

#### `T-2026-08-11-split-and-recipe-audit#2`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-split-and-recipe-audit`（報告の版 2）
- **SPEC の該当箇所**: recipes_match の記述
- **規則**: —
- **`semantic` と分類した理由**: 記述と実装の食い違いを知るには実装の比較キーを読む必要がある。契約が自ら「実装を読まずに書いた」と断っていても、どこがどう違うかは本文からは決まらない。

本文（原文）:

> recipes_match について split サイズの一致を見ると書いたが、実装は test_cfg の実効キー全比較と GPU 構成も見る。SPEC 自身が実装を読まずに書いたと断っており実装に従ったが、この記述だけを信じると対照ペアの不一致 136 件を評価条件の食い違いと誤読する

#### `T-2026-08-11-split-and-recipe-audit#3`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-11-split-and-recipe-audit`（報告の版 2）
- **SPEC の該当箇所**: 工程側の注釈ファイルの確認手順
- **規則**: —
- **`semantic` と分類した理由**: ls では到達しないと分かるには、config が実体の無いプレースホルダを指し 9657 が定数の転記であるという実装の連鎖を追う必要がある。本文には出所が書かれていない。

本文（原文）:

> 工程側の注釈ファイルの有無を ls させるだけで、存在しない場合に 9657 がどこから来たのかを問うていない。実際には実測経路の config が実体の無いプレースホルダを指しており、503 run の 9657 は定数 PAPER_SPLIT_SIZES の転記だった。ls の結果を見るだけではこれに到達しない

#### `T-2026-08-11-split-and-recipe-audit#4`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-11-split-and-recipe-audit`（報告の版 2）
- **SPEC の該当箇所**: 除外規則の取りこぼしの記述
- **規則**: —
- **`semantic` と分類した理由**: 混入が 0 件だと分かるには索引を集計する必要がある。問題の形が別（唯一の記録が退避配下にある）だと気付くのも実データの分布に依存する。本文からは決まらない。

本文（原文）:

> 除外規則の取りこぼしを退避 run が解析対象に混入しうる問題として書いたが、実測では同一 experiment_id の新旧混在は 0 件だった。起きていたのは混入ではなく、9 検出器の唯一の記録が退避配下にあり除外されないまま S0 の比較表を構成しているという別の形である

#### `T-2026-08-13-implementation-history-index#3`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-13-implementation-history-index`（報告の版 1）
- **SPEC の該当箇所**: Task 3 Step 2
- **規則**: —
- **`semantic` と分類した理由**: 平文を読む実行コードが 34 箇所あり fail-open だと分かるには、repo 全体を走査して読み出し側の実装を数える必要がある。契約の本文には箇所数も失敗時の挙動も無い。

本文（原文）:

> Task 3 Step 2 が『復号先を平文の設定ファイル以外にする』を推奨としたが、平文を読む実行コードは 34 箇所あり、すべて fail-open のため無言で資格情報が載らなくなる。同型の事故は s0_010-012 で既に起きている

#### `T-2026-08-14-bundle-attachment-transport#1`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-14-bundle-attachment-transport`（報告の版 1）
- **SPEC の該当箇所**: Task 1 Step 3 と G2 正常系
- **規則**: —
- **`semantic` と分類した理由**: 両立しないと分かるには、read_notion_bundle が設計上 superseded の行を候補から除外することを実装で読む必要がある。契約の本文には除外の仕様が書かれていない。

本文（原文）:

> Task 1 Step 3 は確認用の行を superseded にせよと言うが、G2 正常系はその行から取り込めと言う。read_notion_bundle は設計上 superseded の行を候補から除外するため両立しない。確認用の行の状態を一時的に戻して測り、直後に superseded へ復した

#### `T-2026-08-14-bundle-attachment-transport#2`

- **型**: `self_contradiction`
- **契約**: `T-2026-08-14-bundle-attachment-transport`（報告の版 1）
- **SPEC の該当箇所**: Task 1 Files 欄 と 同 Task Step 3
- **規則**: —
- **`semantic` と分類した理由**: 担当の不定を検出するには、2 つの自然文からそれぞれの動作主を同定して比べる必要がある。担当を表す構造化された欄が契約に無いため、意味の読み取りが避けられない。

本文（原文）:

> Task 1 の Files が『台帳へ確認用の行を作り、確認後に印を付ける』としながら、同じ Task の Step 3 が『この段階は起票者が行う』としている。担当が定まらない。確認用の行は存在しなかったため、判断を仰いだうえで実行者が作成した

#### `T-2026-08-14-bundle-attachment-transport#4`

- **型**: `asserted_without_measuring`
- **契約**: `T-2026-08-14-bundle-attachment-transport`（報告の版 1）
- **SPEC の該当箇所**: 添付の忠実性に関する記述
- **規則**: —
- **`semantic` と分類した理由**: 置き場所が未測定だと分かるには、台帳の列に files 型が存在しないことを外部のスキーマから確かめる必要がある。契約の本文には台帳の列の型が無い。

本文（原文）:

> 『添付が同じ忠実性を持つかは未測定である』は正しいが、添付の置き場所（行の列か、ページの子か）も未測定のまま『行に添付があれば』と書かれている。台帳の列に files 型は存在せず、添付はページの子の file ブロックとしてしか置けない

#### `T-2026-08-15-template-leak-and-autosync-conflict#4`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-15-template-leak-and-autosync-conflict`（報告の版 1）
- **SPEC の該当箇所**: 判定 6・7
- **規則**: —
- **`semantic` と分類した理由**: 稼働中の常駐処理が抑止対象かは、repo 外の ~/bin/m2-sync.sh の中身と自己更新の経路を読まないと判定できない。契約の本文は repo 側の実装しか指していない。

本文（原文）:

> 判定 6・7 はリポジトリ側の実装に対して成立するが、稼働中の常駐処理が抑止対象になっていることを確かめない。~/bin/m2-sync.sh は keeper が origin/phase0 から自己更新するため、phase0 に届くまで抑止は効かない（実測 grep -c = 0）。契約の目的『実行中に書き込ませない』はこの判定群を満たしても達成されない

#### `T-2026-08-16-docs-reconciliation#1`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-16-docs-reconciliation`（報告の版 1）
- **SPEC の該当箇所**: Phase A Step 2 の測り方
- **規則**: —
- **`semantic` と分類した理由**: 文字クラスが取りこぼすかは Makefile の実際のターゲット名に数字が含まれるかに依存する。契約の本文には対象ファイルの中身が無いため、22 と 27 の差を判定できない。

本文（原文）:

> Phase A Step 2 が示す実態の測り方 grep -E '^[a-z-]+:' Makefile が数字を含むターゲットに一致しない。22 件と出るが実際は 27 件で、落ちた s0 s2 s4 s5 s6 がそのまま『存在しない操作』の誤検出になった。SPEC が 15 task 連続で起きていると警告した型が、SPEC 自身の測定コマンドに入っていた

#### `T-2026-08-18-report-back-to-ledger#1`

- **型**: `check_does_not_check`
- **契約**: `T-2026-08-18-report-back-to-ledger`（報告の版 2）
- **SPEC の該当箇所**: 台帳の列の記述
- **規則**: —
- **`semantic` と分類した理由**: 混ざりが起きると分かるには、_scan_children が子ブロックを連結する実装を読む必要がある。契約の本文には取り込み側の走査の仕様が書かれていない。

本文（原文）:

> 台帳の列を 6 つ挙げる一方で、報告の本文をどのブロックへ置くと契約の取り込みと混ざるかを問うていない。指示どおり code ブロックへ置くだけでは、本文で配布された行で _scan_children が契約本文と報告を連結してしまい、以後その契約を取り込めなくなる


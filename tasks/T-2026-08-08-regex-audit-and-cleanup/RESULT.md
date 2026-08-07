# RESULT — T-2026-08-08-regex-audit-and-cleanup

**実行者:** aolab（論理名 `ilya`）/ feat/regex-audit-and-cleanup / 944a2fd59c8be7d5bec3966741ab5a3bc54d9c5c
**実行日時:** 2026-08-07T15:31:23Z
**判定:** PASS

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy | なし | 自己契約では未使用 |
| frozen_source | なし（`inputs` に記載なし） | 契約側の参照は無し。Task 6 で除外 run 側の記載を実測した |
| conventions_rev | `1201f4f` | 実測 `d422b08` へ置換した。差分は前 task（PR #47）で入れた frozen_source の「検査の適用範囲」追記 2 commit（`290da51` と `d422b08`）。**本 task は `conventions.md` を変更していない**（`git diff --name-only origin/phase0...HEAD -- context/conventions.md` が 0 件）ため、この値は以後も陳腐化しない |
| depends_on | `T-2026-08-07-propagation-and-distribution` | PR #47 マージ済み。本ブランチの基点 `46e935a` は `origin/phase0` と一致 |

`contract.inject_verbatim` の原文（要約せず転記）。

**`conventions#frozen_source`**

    比較の三角形で認める凍結源は Relation-DETR seed42 完走 checkpoint。
    同定パスは `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。
    転記元: `docs/experiment_log.md` の STEP 0-2、および `configs/stage/s4_phase_baseline.yaml`。

    凍結源を変更してはならない。変更が必要な場合は別 task で判断を記録し、同じ凍結源を使う比較群と分母を再構成する。

    checkpoint の正本 SHA-256 は次のとおり。

        03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824

    サイズは 195421066 bytes。転記元は 2026-08-06 に実施した11ホストの ssh 一括監査であり、
    11 ホスト全てで SHA-256 が一致し、mtime もナノ秒まで同一であった。
    `third_party/` は git の追跡対象外だが、実体はホスト間で同期されている。

    `verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は
    `no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。
    skip する経路は設けない。

    ### 検査の適用範囲

    凍結源の照合は、凍結源を使う契約に対して適用される。実行直前の検査では
    `meta.kind` が `exp` の契約に対して実施し、それ以外は適用対象外として
    未実施と記録する。

    **適用対象となった場合に、照合を省略する経路は存在しない。**
    照合に失敗した場合は実行を中止し、人へ差し戻す。

**`conventions#prohibitions`**

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

**`conventions#naming`**

    実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

        {step}_{seq:03d}_{description}_seed{seed}

    - `step`: `s0`〜`s9`、または `a1`〜`a7`
    - `seq`: 同一 category と step 内の3桁ゼロ埋め連番
    - `description`: 実験内容の短い説明
    - `seed`: 乱数シード。既定42

    転記元: `README.md` の「命名規則」。

## 2. L3 プリフライトの結果

`make task-preflight TASK=T-2026-08-08-regex-audit-and-cleanup` は `exit=0`。

    RESULT: 4 PASS / 4 SKIP / 0 FAIL

**SKIP された項目（合格ではなく未実行）**: `P2 cuda_ext_loaded` / `P3 deterministic_flags` /
`P4 prereg_committed` / `P5 frozen_source_hash`。前 2 者は契約の `plan.env.preflight` に
未記載のため、後 2 者は `kind` が `impl` で `exp` 限定の検査だからである。

## 3. Phase A — 棚卸しの実測

詳細は `regex_audit.md`。生の出力と要点のみ再掲する。

### Step 3 の生の出力（書き方ごとの末尾改行の通過可否）

SPEC の probe をそのまま実行した結果は次のとおりで、**すべて `evil=False`** であった。

    task_id_dollar_fullmatch           benign=True evil=False
    task_id_dollar_match               benign=True evil=False
    task_id_zed_fullmatch              benign=True evil=False

    schema pattern: ^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}$
    schema benign: True
    schema evil  : False

**この結果は「安全」を意味しない。** SPEC の `evil` payload
`"T-2026-08-08-evil\nrm -rf /"` は改行の**後ろに文字がある**ため、`$` でも一致しない。
実際に悪用できるのは**末尾改行**である。payload を増やして測り直した結果が次である。

| payload | `$` + `match` | `$` + `fullmatch` | `\Z` + `match` | `\Z` + `fullmatch` | JSON Schema |
|---|---|---|---|---|---|
| 正常 | True | True | True | True | True |
| **末尾に改行 1 つ** | **True** | False | False | False | **True** |
| 中間に改行 + 後続文字 | False | False | False | False | False |
| 末尾に改行 2 つ | False | False | False | False | False |
| 末尾にキャリッジリターン | False | False | False | False | False |
| 末尾に空白 | False | False | False | False | False |

危ないのは **`$` + `match`** と **JSON Schema の `pattern`** の 2 つだけである。
`fullmatch` は `$` を使っていても安全であった。JSON Schema が危ないのは、`jsonschema` が
`pattern` を Python の `re` で解釈するため、ECMA-262 ではなく Python の `$` の意味論が
適用されるからである。

### Step 4 の生の出力（実際の検証系へ通した結果）

    SPEC の payload（中間改行）: hard findings = ["[L1-1] meta.task_id: 'T-2026-08-08-evil\\nmalicious' does not match '^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}$'"]
    末尾改行（実際の悪用形）: hard findings = なし（=素通り）

**`task_id` の末尾に改行を付けた契約は `validate_l1` を hard finding ゼロで通過した。**

### 悪用可能だった箇所の件数と場所

| 項目 | 実測 |
|---|---|
| 棚卸しした正規表現 | Python 側 15 箇所 + JSON Schema 側 4 箇所 |
| 末尾改行が通る箇所 | Python 側 7 箇所、JSON Schema 側 4 箇所 |
| **実際に悪用可能な箇所** | **1 箇所。`tasks/_schema/spec.schema.json:15` の `meta.task_id`** |

`meta.task_id` だけは Python 側に対応する正規表現が存在せず、**Schema が唯一の門番**だった。
L1-2 は `task_id != dir_name` の文字列比較であり、両方に同じ改行が入れば一致してしまう。
他の 3 パターンは Schema 単体では通るが、Python 側の `fullmatch`（L1-4）または
アンカー照合（L2-5）が拒否することを実測で確認した。

**これまでの検証結果への影響は無い。** 既存 7 契約すべての `spec.yaml` から `meta.task_id` を
読み出し、改行を許さない形で照合したところ、該当は **0 件**であった。

`escalate_if: additional_bypass_found` に該当するため、件数と場所を隠さず記録した。
G1 は「悪用可能な箇所がある」判定であり、SPEC の指示どおり停止せず Phase B へ進んだ。

## 4. Phase B — 修正と回帰

### JSON Schema 側を修正したか、その判断理由

**修正した。** SPEC Step 4 は「Phase A Step 3 で `schema evil` が `True` だった場合のみ修正する」と
定めているが、SPEC の probe payload では `False` になる。**正しい payload（末尾改行）で測ると
`True`** であり、しかも `meta.task_id` は Python 側に二重防御が無く Schema が唯一の門番である。
したがって修正が必要と判断した。

ECMA-262 には `\Z` が無いため、SPEC の助言どおり否定先読みを使った。
`(?![\s\S])` は Python でも ECMA-262 でも「文字列の絶対的な末尾」を意味し、可搬である。
二重防御のある 3 パターンも同時に直した。門番が 1 つでも通してしまう状態を残さないためである。

    "^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}(?![\\s\\S])"
    "^exp:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?![\\s\\S])"
    "^run:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?![\\s\\S])"
    "^conventions#[a-z0-9_]+(?![\\s\\S])"

Python 側は `_PIPE_STRICT_PATHS` の 5 パターンを `$` から `\Z` へ変え、`_is_pipe_strict` の
照合を `match` から `fullmatch` へ寄せた。`fetch_task.py` の `_DELIM_RE` と `_HEADER_RE` も
同様に統一し、`_TASK_ID_RE` を含む 3 箇所の呼び出しを `fullmatch` にした。

### Step 6 の反証入力の結果

SPEC が指定する 5 種に 4 種を足して測った。**全件が期待どおり**であった。

| 入力 | 期待 | 実測 |
|---|---|---|
| 末尾に改行 1 つ | 拒否 | 拒否 |
| 中間に改行 | 拒否 | 拒否 |
| 末尾にキャリッジリターン | 拒否 | 拒否 |
| 末尾に空白 | 拒否 | 拒否 |
| 末尾に CRLF | 拒否 | 拒否 |
| 末尾にタブ | 拒否 | 拒否 |
| 先頭に改行 | 拒否 | 拒否 |
| NUL 文字 | 拒否 | 拒否 |
| 正常な識別子 | 受理 | 受理 |

JSON Schema の 4 パターンも、Python 側の二重防御に頼らない**単体の状態**で
正常を受理し末尾改行・中間改行を拒否することを確認した。

既存 7 契約が引き続き通ることも確認した（`make task-validate` が `7 task(s), 0 failed`）。

## 5. Phase C — 作業領域の整理と記録の訂正

### Task 3: 未追跡ディレクトリの無視設定

前 task の実測記録（`T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md`）を
引用する。

    `runindex/index.csv` を `ledger_key` および `path` 列で全文検索したが、3件とも
    **1件もヒットしない**（`excluded` 済み run としても含まれていない）。各ディレクトリの
    中身は `checkpoints/` `logs/` `predictions/` のみで、`config.yaml` と `metrics.json` が
    存在しない。

**SPEC が指示するパターン `experiments/**/_smoke_*/` は採用しなかった。**
実測したところ、このパターンは `experiments/_smoke_prior/`（**追跡 36 ファイル・
`index.csv` に 6 run 収録**）にも一致し、そこへ後から加わる証跡を静かに取りこぼす。
backlog **B-28**（`_legacy_score_thr_0` は `_` 接頭辞だが除外してはいけない）と同型の危険である。

実測が収穫対象外と裏付けているのは `transfer/` 配下の 3 件だけなので、既存 `.gitignore` の
慣例（ディレクトリの明示列挙）に合わせて 3 件を明示した。

| 検査 | 実測 |
|---|---|
| 対象 3 件が無視される | 3 件とも OK |
| `experiments/_smoke_prior/` の新規ファイル | 無視されない（B-28 同型の事故を回避できている） |
| `git status --porcelain experiments/` | 出力なし |
| ディレクトリの存在 | 3 件とも残っている（削除していない） |
| `transfer/` 配下の追跡ファイル・収穫 run | いずれも 0 件（無視しても失うものが無い） |

### Task 4: 整形のみの差分の破棄

破棄の前にバイト単位で内容変更が無いことを確かめた。

    行末空白を無視した内容は同一: True
    行数: 71 -> 71
    差異のある行: 4
      行3: '**task_id:** `T-2026-08-03-task-contract-bootstrap`  ' -> '…bootstrap`'
      行4: '**kind:** `impl`  ' -> '**kind:** `impl`'
      行5: '**origin:** `claude-app`  ' -> '**origin:** `claude-app`'
      行6: '**作成日:** 2026-08-03  ' -> '**作成日:** 2026-08-03'

4 行の行末 2 空白の除去のみで内容変更は無い。破棄後に `cat -A` で行末 2 空白が
復元されたことを確認した。破棄は取り消せないため、実行前に控えを作業用一時領域へ保存した。

### Task 5: 伝播経路の記述

`tasks/README.md` に「伝播の経路」節を追加した。**「全 11 台へ届いている」とは書いていない**
（実測されていないため）。`grep` で未実測の断定が無いことを確認済み。

## 6. Task 6 — 凍結源の取り違えで除外された run

### 実列名の確認

`runindex/index.csv` の除外関連の列は **`excluded` と `exclusion_reason` の 2 つ**。
前 task の記録と食い違いは無かった。

### 特定結果

`exclusion_reason == "wrong_frozen_source"` は **3 件**、いずれも `host = philip`。
3 件とも `config.yaml` の `frozen_source` は同一であった。

    detector: align_detr / seed: 42 / backbone: resnet50
    cache_dir: data/processed/stage1_features/aligndetr_seed42

**除外理由は特定できた。** 破棄記録
`evidence/discarded_caches/stage1_features/aligndetr_seed42.discarded_20260705.md` により、
このキャッシュは 2026-07-03 の AlignDETR-S0-frozen 学習が NCCL ALLREDUCE タイムアウトで
失敗したあと、`entry5.sh` が **2026-05-31 の通常学習 AlignDETR ckpt**
（`/tmp/aligndetr_work_seed42/model_final.pth`）で代替して抽出したものと判明した。
すなわち除外理由は「宣言している S0-frozen 条件で走っていない」であり、数値記録が
壊れているわけではない。

**4 候補との対応は UNKNOWN である。** 理由は 2 つあり、いずれも実測に基づく。

| # | 障害 | 実測 |
|---|---|---|
| 1 | 実際に使われた checkpoint が現存しない | `/tmp/aligndetr_work_seed42/model_final.pth` は存在しない。`evidence/aligndetr_s0frozen_incident_20260703/` に保全されているのは実行痕跡（合計 788KB）のみで checkpoint 本体を含まない |
| 2 | 証跡にハッシュもサイズも記録が無い | 全ログと `entry5.sh` を検索したが、残っているのはパスのみ |

加えて候補側 4 件は `config.yaml` を持たず、detector を実測で確認できない。
パス上は Relation-DETR 系だが**名前からの推定にすぎないため断定しない**。

**正本と一致しないことは確定している。** 正本は Relation-DETR seed42 の S0 完走 checkpoint
であり、3 run が依拠したのは AlignDETR の、しかも S0-frozen ではない checkpoint から
作られた特徴である。検出器の系統も学習条件も異なるため一致する余地が無い。
この結論はハッシュ照合を要しない。

## 7. テスト件数（実測）

| 対象 | 件数 |
|---|---|
| `tests/test_validate_task.py` | **18 passed**（本 task 前は 16。改行拒否の 2 件を追加） |
| `tests/test_fetch_task.py` + `tests/test_build_context.py` | **31 passed**（前 task から不変。`fullmatch` への変更で壊れていないことを確認） |
| 全体 `tests/` | **5 failed / 215 passed**。失敗は実行前と同じ 5 件で不変。passed が 213 から 215 へ増えた 2 件は本 task が追加した分と一致する |

前 task の RESULT は「31 passed」（`test_fetch_task.py` 22 + `test_build_context.py` 9）を
記録していた。本 task はその 31 件を維持したまま `test_validate_task.py` を 16 から 18 へ
増やした。

## 8. 完了判定

| # | 判定 | 結果 |
|---|---|---|
| 1 | 棚卸しが記録された | PASS（`regex_audit.md` の 6 表が埋まっている） |
| 2 | 改行入り識別子が拒否される | PASS |
| 3 | 反証入力が全て拒否される | PASS（9 種すべて期待どおり） |
| 4 | 動作確認用が無視される | PASS（`git status --porcelain experiments/` の出力なし） |
| 5 | 動作確認用が削除されていない | PASS（3 件存在） |
| 6 | 整形差分が解消 | PASS |
| 7 | 伝播経路が文書化 | PASS（1 件） |
| 8 | 除外理由が特定または UNKNOWN と明記 | PASS（除外理由は特定、候補との対応は UNKNOWN と理由つきで明記） |
| 9 | 契約検証が通る | PASS（`7 task(s), 0 failed`、exit 0） |
| 10 | 実行前検査が通る | PASS（exit 0） |
| 11 | テストが全 pass | PASS（**18 passed**） |
| 12 | 全体テストが不変 | PASS（**5 failed / 215 passed**） |
| 13 | 禁止領域が無変更 | PASS（出力なし） |

## 9. 受入基準の充足

| acceptance | 結果 |
|---|---|
| 検証系の終端一致の棚卸し結果が表として記録されている | PASS |
| 改行を含む入力が検証を素通りしない | PASS |
| 動作確認用の未追跡ディレクトリが無視設定へ追加されている | PASS |
| 整形のみの未コミット差分が解消されている | PASS |
| 伝播経路の実体が文書へ反映されている | PASS |
| 凍結源の取り違え候補について除外理由が実測で特定されている | PASS（除外理由は特定。候補との対応は測定不能のため UNKNOWN） |
| `make task-validate` が exit 0 | PASS |
| `make task-preflight` が exit 0 | PASS |

## 10. deviations（指示書どおりにしなかった箇所）

- 指示: Task 1 Step 3 の probe で `evil = "T-2026-08-08-evil\nrm -rf /"` を使い、`evil=True` になったものを脆弱と判定する。
- 実際: この payload を実行したうえで、**末尾改行を含む 6 種類の payload へ拡張して測り直した**。
- 理由: SPEC の payload は改行の後ろに文字があるため `$` でも一致せず、**全て `evil=False`** になる。これだけで判断すると「検証系は安全」という誤った結論に至る。実際に悪用できるのは末尾改行であり、前 task で `fetch_task.py` に見つかった形もそれである。拡張した測定で `validate_l1` の素通りを再現できた。
- 分類: SPEC の欠陥

- 指示: Task 3 Step 2 で `.gitignore` に `experiments/**/_smoke_*/` を追加する。
- 実際: このパターンは採らず、実測が裏付ける 3 ディレクトリを明示列挙した。
- 理由: 実測したところ `experiments/**/_smoke_*/` は `experiments/_smoke_prior/`（追跡 36 ファイル・`index.csv` に 6 run 収録）にも一致し、そこへ後から加わる証跡を静かに取りこぼす。backlog B-28 と同型の危険である。既存 `.gitignore` の慣例もディレクトリの明示列挙であり、そちらに合わせた。
- 分類: SPEC の欠陥

- 指示: Task 2 Step 4 は「Phase A Step 3 で `schema evil` が `True` だった場合のみ」JSON Schema を修正する。
- 実際: 修正した。あわせて二重防御のある 3 パターンも同時に直した。
- 理由: SPEC の payload では `False` だが、正しい payload では `True` である。`meta.task_id` は Python 側に二重防御が無く Schema が唯一の門番であるため修正が必要だった。他 3 パターンも、門番が 1 つでも通す状態を残さないために揃えた。
- 分類: 判断が必要だった

- 指示: なし（棚卸し文書の作成中に自分で起こした事故）。
- 実際: `regex_audit.md` の表のセルに正規表現をそのまま載せたところ、本文に含まれる縦線で列数が崩れた（2 行が 9 区切り、他が 8 区切り）。検査で気づき、該当セルを日本語の説明へ書き換えて解消した。あわせて検査スクリプトを `\|`（エスケープ済みの縦線）を区切りと数えないよう直した。
- 理由: `conventions#sigma` は「区切りを表したいときは `/` かスラッシュ区切りの語を使う」と定めており、エスケープすれば描画は壊れないとしても規約に反する。backlog B-33 と同型の事故であり、記録に残す価値がある。
- 分類: 判断が必要だった

- 指示: Task 4 Step 2 で `git checkout --` により整形差分を破棄する。
- 実際: 破棄の前に、バイト単位で内容変更が無いことを確認し、控えを作業用一時領域へ保存した。
- 理由: 破棄は取り消せない操作であるため。SPEC も Step 1 で内容確認を求めており、それを機械的な照合として実施した。
- 分類: 判断が必要だった

- 指示: Task 1 Step 2 の監査結果保存先など、一時ファイルの置き場は指定されていない。
- 実際: 実行環境が定める作業用一時ディレクトリを使った。
- 理由: 本セッションの実行環境が「一時ファイルは所定の作業ディレクトリを使う」と定めているため。
- 分類: 環境差

## 11. 未解決・申し送り

- **他ホストからの伝播監査が引き続き未達。** 前 task から継続する申し送りである。実測ホストから他 10 ホストへ ssh 到達できないため（LAN への経路が無く、ホスト名も解決できない）、他ホストの状態は UNKNOWN のままである。監査を完遂するには LAN に到達できるホストから同じ手順を回す必要がある。
- **`wrong_frozen_source` の 3 run が使った checkpoint の同定が未達。** 実際に使われた `/tmp/aligndetr_work_seed42/model_final.pth` が揮発しており、証跡にハッシュもサイズも残っていない。同定するには `philip` 上に当時の `/tmp` が残っているか、2026-05-31 の AlignDETR 通常学習の成果物が別の場所に保存されているかを確認する必要がある。**実測ホストから philip へ到達できないため未実施。** backlog B-25 および B-27 の管轄として残す。
- **`tools/harvest_runindex.py` の `$` 終端 3 件は未修正。** 本 task の禁止事項 3 により変更していない。これらはディスク上のディレクトリ名を解析するもので契約検証の門番ではないが、同型の書き方が残っている事実は記録する。別 task の対象。
- **`auto-merge` を阻害していた未 commit 差分は解消した。** Task 4 で整形差分を破棄し、Task 3 で未追跡 3 件を無視設定へ入れたため、作業ツリーは本 task の成果物のみになった。ただし**これが keeper の auto-merge を実際に動かすかは未検証**（次の 30 分周期を待つ必要がある）。
- 全体テストの既存 5 件の失敗（`tests/test_engines.py` 1 件、`tests/test_research_logger.py` 4 件）は本 task 範囲外の既存不整合であり、実行前から存在し件数も不変。

## 12. 数値の出所

すべての数値は当該コマンドの stdout / stderr、または正本ファイルから実測した。
正規表現の通過可否、`index.csv` の件数、`config.yaml` の記載、ファイルの存在、
終了コード、テスト件数はいずれも実行結果である。
未測定の項目は §6 と §11 に UNKNOWN として明示した。

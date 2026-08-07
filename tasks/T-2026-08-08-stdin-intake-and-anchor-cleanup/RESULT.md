# RESULT — T-2026-08-08-stdin-intake-and-anchor-cleanup

**実行者:** aolab（論理名 `ilya`）/ feat/stdin-intake-and-anchor-cleanup / 6e8caf5ade5fa815b66a585a9511a285afc30171
**実行日時:** 2026-08-07T18:35:24Z
**判定:** PASS

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy | なし | 自己契約では未使用 |
| frozen_source | なし（`inputs` に記載なし） | 契約側の参照は無し |
| conventions_rev | `1201f4f` | 実測 `d422b08` へ置換した。差分は PR #47 で入れた frozen_source の「検査の適用範囲」追記 2 commit。**本 task は `conventions.md` を変更していない**（`git diff --name-only origin/phase0...HEAD -- context/conventions.md` が 0 件）ため、この値は陳腐化しない |
| depends_on | `T-2026-08-08-regex-audit-and-cleanup` | PR #48 マージ済み。本ブランチの基点 `b2c63fe` は `origin/phase0` と一致 |

`contract.inject_verbatim` の原文（要約せず転記）。

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

`make task-preflight TASK=T-2026-08-08-stdin-intake-and-anchor-cleanup` は `exit=0`。

    RESULT: 4 PASS / 4 SKIP / 0 FAIL

**SKIP された項目（合格ではなく未実行）**: `P2 cuda_ext_loaded` / `P3 deterministic_flags` /
`P4 prereg_committed` / `P5 frozen_source_hash`。前 2 者は契約の `plan.env.preflight` に
未記載のため、後 2 者は `kind` が `impl` で `exp` 限定の検査だからである。

## 3. Phase A — 陽性対照の設計と実測

### 現在の取り込み経路（変更前）

`tools/fetch_task.py` の `--src` はローカルファイルパスまたは URL を受け取る。
`read_source` は URL なら `urllib`、それ以外は `Path(src)` として扱い、
ファイルが無ければ `入力が見つかりません` で失敗する。標準入力の経路は存在しなかった。

### 陽性対照の設計

| # | 入力 | 作り方 | 期待 |
|---|---|---|---|
| N1 | 正常なバンドル | 既存契約から `--pack` で組み立て | 取り込み。ただし `task_id` が重複するため**重複拒否**されるはず |
| N2 | 先頭行が宣言でないテキスト | 平文 1 行 | 失敗・痕跡なし |
| N3 | 区切りが本文と衝突するバンドル | N1 の `SPEC.md` 本文へ区切り文字列を行の途中として挿入 | 失敗・痕跡なし |
| N4 | 検証を通らない契約 | N1 の `task_id` を未使用のものへ変え、`meta` に未知キー `nickname` を混入 | 失敗・**巻き戻し**・痕跡なし |

N3 と N4 の作り方は SPEC が「実装を読んでから決める」としていたため、
`parse_bundle` の衝突検出と `validate_l1` の `additionalProperties: false` を
それぞれ狙う形にした。

### 陽性対照が実際に失敗するか（実装前に既存のファイル経路で確認）

**SPEC の申し送りに従い、対照が本当に失敗することを実装前に確かめた。**
確認しなければ、この検証は無効である。

    before=8

    === n1_valid       exit=1
          取り込みを中止しました: 同名の契約が既にあります: tasks/T-2026-08-08-regex-audit-and-cleanup（上書きしません）
    === n2_no_header   exit=1
          取り込みを中止しました: 先頭行が #!TASK-BUNDLE v1 delim=<区切り> の形式ではありません
    === n3_collision   exit=1
          取り込みを中止しました: 区切りが SPEC.md の本文と衝突しています
    === n4_invalid     exit=1
          make: *** [Makefile:93: task-validate] Error 1
          検証に失敗したため tasks/T-2026-08-09-invalid-probe を巻き戻しました（痕跡は残していません）

    after=8  (before=8)
    本 task 以外の痕跡なし

**4 種すべてが失敗し、しかも互いに異なる層で失敗した。** N1 は重複拒否、N2 はヘッダ解析、
N3 は衝突検出、N4 は**設置まで進んでから巻き戻し**である。対照として有効であることを
確認できた。

## 4. Phase A — 標準入力への対応

### テストが対象を検証していなかった件（実測で判別）

SPEC Step 2 は「FAIL しなければ、既に実装済みかテストが対象を検証していない。
どちらかを実測で判別する」と定めている。実測の結果は**後者**であった。

追加した 3 テストのうち **FAIL したのは 1 件のみ**で、空入力を拒否する 2 件は
実装前から pass していた。理由は「空入力が拒否されたから」ではなく、
`read_source("-")` が `-` を**存在しないファイル**として扱い
`BundleError("入力が見つかりません: -")` を投げていたためである。
すなわち **2 件は誤った理由で pass する偽の合格**だった。実装後は本来の理由で pass する。

この観測を踏まえ、空白のみの入力を拒否するテストを 1 件追加した
（「空でないこと」だけを見ると空白の貼り付けが素通りし、分かりにくい失敗になるため）。

### 実装

`read_source` に `-` の分岐を足しただけである。**取り込みの流れ（一時ディレクトリへの
展開・設置・検証・巻き戻し）は取得方法によらず共通であり、複製していない。**
`fetch()` 側は一切変更していない。

`Makefile` には `task-paste` を追加した。`task-fetch` は既存のまま残してある。

### G1 ゲート — 陽性対照を標準入力経由で全て投げた結果

    before=8

    ===== n1_valid       make_exit=2   同名の契約が既にあります（上書きしません）
    ===== n2_no_header   make_exit=2   先頭行が #!TASK-BUNDLE v1 delim=<区切り> の形式ではありません
    ===== n3_collision   make_exit=2   区切りが SPEC.md の本文と衝突しています
    ===== n4_invalid     make_exit=2   検証に失敗したため tasks/T-2026-08-09-invalid-probe を巻き戻しました
    ===== 空入力          make_exit=2
    ===== 空白のみ         make_exit=2

    before=8 after=8

**6 種すべてが非ゼロで終了し、件数は不変、`tasks/` に痕跡は残らなかった。**

空入力と空白のみについては、**失敗した理由が新しい検査によるものか**をスクリプト単体で
確かめた（`make` は終了コードを 2 に丸めるため理由が見えない）。

    取り込みを中止しました: 標準入力が空です。バンドルを貼り付けてから入力を終了してください
      空入力 script_exit=1
    取り込みを中止しました: 標準入力が空です。バンドルを貼り付けてから入力を終了してください
      空白のみ script_exit=1

ファイル経路が退行していないことも確認した（`n2` は同じ理由で失敗し、存在しないパスは
従来どおり `入力が見つかりません` で失敗する）。

### 正常系

`task_id` を未使用の値へ書き換えたバンドルを標準入力から投入し、取り込みに成功した。

    OK   T-2026-08-09-paste-probe
    1 task(s), 0 failed
    取り込みました: tasks/T-2026-08-09-paste-probe
    make_exit=0
    before=8 after=9

確認後、SPEC の指示どおり取り込んだ契約を削除し、作業領域を元へ戻した（件数 8、残骸なし）。

## 5. Phase B — 収穫器の終端一致

### Step 3 の実測（各パターンの挙動）

対象は 3 つの定数。いずれも `.match()` で呼ばれており、**3 つとも末尾改行を通した。**

| 定数 | 行 | 正常 | 末尾改行 | 中間改行 | 末尾空白 |
|---|---|---|---|---|---|
| `RUN_NAME_RE` | 203 | True | **True** | False | False |
| `RUN_NAME_NOSEQ_RE` | 206 | True | **True** | False | False |
| `IDENTIFIER_RE` | 1362 | True | **True** | False | False |

**通ったときに何が捕獲されるか**まで測った。ここが実害である。

    RUN_NAME_RE.match("s0_001_maskdino_bbox_seed42\n")
      -> {'step': 's0', 'seq': '001', 'desc': 'maskdino_bbox', 'seed': '42'}
    RUN_NAME_NOSEQ_RE.match("hc_seed42\n")
      -> {'desc': 'hc', 'seed': '42'}

`\d+` が改行の手前で止まり `$` がその直前に一致するため、**改行を落とした値が捕獲される**。
末尾に改行を持つディレクトリと持たないディレクトリが同じ `ledger_key` へ潰れうる。
backlog B-34（`ledger_key` の名前空間衝突）と同型の危険である。

**該当するディレクトリが現に存在するかも測った。** `experiments/` 配下の全ディレクトリ名を
走査し、空白・改行・タブを含むものは **0 件**であった。したがって修正しても
出力は変わらないはずであり、その予測は G2 で確認された。

### 変更しなかった箇所とその理由

| 箇所 | 内容 | 理由 |
|---|---|---|
| `tools/harvest_runindex.py:1287` | `re.sub(rf"(?:^\|_)p{seed_phase}(?=_\|$)", "_", out)` | **置換**用途であり門番ではない。`$` は先読みの中で「語の終わり」を表しており、`fullmatch` へ寄せる対象ではない |
| `tools/harvest_runindex.py:3403` | `re.sub(r": .*$", "", key)` | 同じく**置換**用途。警告文の接尾辞を落とすための部分一致であり、意図的である |

SPEC の指示「`re.search` を `fullmatch` に変えてはならない。意味が変わる」に従い、
`re.sub` / `re.search` の系統には一切触れていない。**`UNKNOWN` として保留した箇所は無い**
（3 定数はすべて実測できたため）。

### 修正

3 定数の終端を `$` から `\Z` へ変え、呼び出し 3 箇所を `.match()` から `.fullmatch()` へ
寄せた。修正後の挙動も実測した。

    RUN_NAME_RE            正常=True  末尾改行=False
    RUN_NAME_NOSEQ_RE      正常=True  末尾改行=False
    IDENTIFIER_RE          正常=True  末尾改行=False

### G2 ゲート — 出力が変わらないことの実測

    ===== ハッシュ比較 =====
    IDENTICAL

    行数: 749 -> 749 不変
    列数: 89 -> 89 不変
    除外内訳 不変: True

`runindex/*.csv` 4 ファイルの md5 が完全に一致した。`git status --porcelain runindex/` も
空であり、生成物は 1 バイトも変わっていない。

冪等性も確認した（`make runindex` を再実行してハッシュ比較 → `IDEMPOTENT OK`）。

軽量ビューへの影響も無かった（`make context` 後の `make context-check` が `exit=0`、
`git status --porcelain context/auto/` が空）。

## 6. Phase C — 到達可能な範囲での伝播監査

追記先は `tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md` の
「再監査（2026-08-08）」節。**既存の記録は書き換えていない。**

| 項目 | 実測 |
|---|---|
| 到達できたホスト | **0 台** |
| 到達できなかったホスト | **11 台** |
| `philip` の理由 | `ssh: connect to host 192.168.196.150 port 50072: No route to host` |
| 他 10 台の理由 | `ssh: Could not resolve hostname <host>: Name or service not known` |
| 迂回手段 | `~/.ssh/config` に `ProxyJump` / `ProxyCommand` の定義なし |
| 名前解決 | `getent hosts` が 11 台とも NG |

前回（2026-08-07）と同じ結果である。**到達できないことは伝播の欠落を意味しない。**
他ホストの状態は引き続き **UNKNOWN** である。

G3 は `on_fail: ask` であり、この結果をユーザーへ提示して判断を仰ぎ、
**「記録して続行」**との回答を得て Task 5 へ進んだ。

### 前 task の申し送りが解決したことを実測で確認

前 task は「auto-merge が実際に動くかは未検証（次の 30 分周期を待つ必要がある）」と
申し送っていた。数時間が経過したため測ったところ、**実際に動いていた**。

    2026-08-07 14:25:16 [ilya] auto-merge skip: 追跡変更 1 件 (behind 1)
    2026-08-07 17:55:45 [ilya] auto-merge: feat/regex-audit-and-cleanup <- origin/phase0 (1 commits)
    2026-08-07 17:55:48 [ilya] auto-push: feat/regex-audit-and-cleanup (1 commits)

前 task で整形差分を破棄し smoke ディレクトリを無視設定へ入れたことが、
auto-merge の閉塞を実際に解いたことになる。

### 検査コマンド自身が検査対象に混入する誤りの再発

keeper のプロセス数を `pgrep -c -f 'bin/keeper.sh'` で数えたところ **3** を返した。
これは検査コマンド自身のコマンドラインに一致した偽陽性であり、
前 task で `pgrep -af 'ssh.*-L 22001'` について記録したのと同型の誤りである。
`ps -eo args` と文字クラスによる自己除外で数え直し、**1**（PID 73082）と確定した。
**同じ誤りが 2 度起きているため、監査文書に注記として残した。**

## 7. テスト件数（実測）

| 対象 | 件数 |
|---|---|
| `tests/test_fetch_task.py` | **25 passed**（本 task 前は 22。標準入力の 3 件を追加） |
| 全体 `tests/` | **5 failed / 218 passed**。失敗は実行前と同じ 5 件で不変。passed が 215 から 218 へ増えた 3 件は本 task が追加した分と一致する |

前 task の RESULT は `test_fetch_task.py` 22 件を記録していた。本 task で 25 件になった。

## 8. 完了判定

| # | 判定 | 結果 |
|---|---|---|
| 1 | 標準入力から取り込める | PASS（正常系 `make_exit=0`） |
| 2 | 陽性対照が全て失敗する | PASS（N2 から N4 と空入力・空白のみが全て非ゼロ） |
| 3 | 失敗時に痕跡が残らない | PASS（before=8 after=8、`git status` に該当なし） |
| 4 | 収穫器の出力が不変 | PASS（`IDENTICAL`） |
| 5 | 収穫器が冪等 | PASS（`IDEMPOTENT OK`） |
| 6 | 軽量ビューが不変 | PASS（`context-check` exit 0、`git status` 空） |
| 7 | 到達範囲が区別して記録 | PASS（到達 0 台 / 未確認 11 台を理由つきで別記） |
| 8 | 契約検証が通る | PASS（exit 0） |
| 9 | 実行前検査が通る | PASS（exit 0） |
| 10 | テストが全 pass | PASS（**25 passed**） |
| 11 | 全体テストが不変 | PASS（**5 failed / 218 passed**） |
| 12 | 禁止領域が無変更 | PASS（出力なし） |

## 9. 受入基準の充足

| acceptance | 結果 |
|---|---|
| 標準入力からの取り込みが一つの操作で完結する | PASS（`make task-paste` に貼り付けるだけ） |
| 標準入力からの取り込みが失敗した場合に作業領域へ痕跡が残らない | PASS |
| 収穫器の終端一致が他の検証系と同じ書き方に揃っている | PASS（`\Z` + `fullmatch`） |
| 収穫器の再生成で行数と除外内訳が変わらない | PASS（ハッシュまで一致） |
| 到達できたホストと到達できないホストが区別して記録されている | PASS |
| `make task-validate` が exit 0 | PASS |
| `make task-preflight` が exit 0 | PASS |

## 10. deviations（指示書どおりにしなかった箇所）

- 指示: Task 2 Step 1 のテストは 2 件（`--src -` の読み取りと空入力の拒否）。
- 実際: 空白のみの入力を拒否するテストを 1 件足して 3 件にした。
- 理由: 実装で「空でないこと」だけを見ると、空白だけの貼り付けが素通りして「先頭行が形式ではありません」という分かりにくい失敗になる。SPEC の禁止事項 6（件数合わせのためのテスト）には当たらず、実際に別の分岐を検証している。
- 分類: 判断が必要だった

- 指示: Task 1 Step 3 は `/tmp/intake_probe` に陽性対照を作る。
- 実際: 実行環境が定める作業用一時ディレクトリに作った。
- 理由: 本セッションの実行環境が「一時ファイルは所定の作業ディレクトリを使う」と定めているため。並行する別作業と `/tmp` を共有すると衝突しうる。
- 分類: 環境差

- 指示: Task 3 Step 4 は「終端が `$` のものを `\Z` へ、`re.match` を `re.fullmatch` へ揃える」。
- 実際: 3 定数（`RUN_NAME_RE` / `RUN_NAME_NOSEQ_RE` / `IDENTIFIER_RE`）のみ変更し、`re.sub` の 2 箇所（`harvest_runindex.py:1287` と `:3403`）は変更しなかった。
- 理由: どちらも置換用途であり門番ではない。SPEC 自身が「`re.search` を `fullmatch` に変えてはならない。意味が変わる」「判断できなければ変更せず `UNKNOWN` として記録する」と定めており、用途を読んで意図的な部分一致と判断した。`UNKNOWN` ではなく「用途が読めたうえで対象外」として記録する。
- 分類: 判断が必要だった

- 指示: なし（作業中に自分で起こした誤り）。
- 実際: keeper のプロセス数を `pgrep -c -f 'bin/keeper.sh'` で数えて **3** という誤った値を得た。検査コマンド自身のコマンドラインへの自己マッチである。`ps -eo args` と文字クラスで数え直し **1** と確定した。
- 理由: 前 task で `pgrep -af 'ssh.*-L 22001'` について同型の偽陽性を記録していたにもかかわらず再発させた。**同じ誤りが 2 度起きたため、監査文書に注記として残した。**
- 分類: 判断が必要だった

- 指示: Task 3 Step 3 の probe スクリプトは、正規表現を静的に抜き出して一致を試す形。
- 実際: 静的抽出ではなく、`harvest_runindex` から定数を実際に import し、その関数へ**実際に渡される形の値**（run ディレクトリ名・分母の括弧内文字列）を与えて測った。
- 理由: SPEC 自身が「パターン単体では試せない場合、実際に渡される値の形を確認してから試すこと」と述べている。静的抽出では名前付きグループを含むパターンの一致例を作れず、また「通ったときに何が捕獲されるか」という実害の部分を測れない。
- 分類: 判断が必要だった

## 11. 未解決・申し送り

- **他 10 ホストの伝播状況は引き続き UNKNOWN。** 実測ホストから到達する手段が無い（LAN への経路なし、名前解決なし、`ProxyJump` の定義なし）。監査を完遂するには LAN に到達できるホスト（`philip` など）から同じ手順を回す必要がある。**2 回続けて 0 台であり、実測ホストを変えない限り前進しない。**
- **`philip` への SSH トンネルは依然未稼働。** Syncthing の星型同期（git 追跡外の実験証跡）はこのホストで機能していない可能性が高い。git 追跡物には影響しない。
- **`wrong_frozen_source` の 3 run が使った checkpoint の同定は未達。** 前 task からの継続。`philip` 到達が前提である。
- **`re.sub` 系の `$` は残っている。** `harvest_runindex.py:1287` と `:3403` の 2 箇所。用途を読んだうえで意図的に残したものであり、脆弱性ではない。将来同じ棚卸しを行う人が「見落とし」と誤解しないよう、本 RESULT §5 に理由を記録した。
- **標準入力経路の URL 取得は引き続き未検証。** `read_source` の `http(s)` 分岐は前 task から未使用のままである。
- 全体テストの既存 5 件の失敗（`tests/test_engines.py` 1 件、`tests/test_research_logger.py` 4 件）は本 task 範囲外の既存不整合であり、実行前から存在し件数も不変。

## 12. 数値の出所

すべての数値は当該コマンドの stdout / stderr、または正本ファイルから実測した。
正規表現の一致可否と捕獲内容、`runindex/*.csv` の md5 と行数・列数・除外内訳、
ホスト到達性、プロセス数、終了コード、テスト件数はいずれも実行結果である。
未測定の項目は §6 と §11 に UNKNOWN として明示した。

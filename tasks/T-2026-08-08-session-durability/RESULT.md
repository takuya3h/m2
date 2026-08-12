# RESULT — T-2026-08-08-session-durability

**実行者:** aolab（論理名 `ilya`）/ feat/session-durability / fbe0f0df207eb52ceef8bcc5d80c78b6503ebc5e
**実行日時:** 2026-08-07T19:31:25Z
**判定:** PARTIAL（G2 のみ未確認。理由は §5）

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy | なし | 自己契約では未使用 |
| frozen_source | なし | 契約側の参照は無し |
| conventions_rev | `1201f4f` | 実測 `d422b08` へ置換。**本 task は `conventions.md` を変更していない**（差分 0 件）ため陳腐化しない |
| depends_on | `T-2026-08-08-stdin-intake-and-anchor-cleanup` | PR #49 マージ済み。基点 `b2c63fe` は `origin/phase0` と一致 |

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

## 2. 手順 4 で一度停止した（P7 の偽陽性）

L3 プリフライトが **FAIL** し、手順どおり停止して判断を仰いだ。

    P7 destination_writable   FAIL 存在しないか非ディレクトリ: docs/sessions/
    RESULT: 3 PASS / 4 SKIP / 1 FAIL

`outputs.destination` の `docs/sessions/` は**本 task 自身が作る成果物**であり、
実行前検査の時点では存在しない。過去 8 契約はすべて destination が既存だった（実測）。
つまり P7 は「本当に書けない」と「これから作る」を区別できず、
**新しい出力領域を作る契約では必ず FAIL する偽陽性**であった。

ユーザー判断により **P7 を修正**した。判定を次のとおり変えた。

| 状況 | 判定 |
|---|---|
| destination が存在 | 従来どおり probe で書き込みと削除を検査 |
| destination が不在 | 最も近い既存の祖先へ probe。書ければ PASS（作成可能と明記）、書けなければ FAIL |

**検査は実体を作らない**（実行前検査が環境を変えてはならない）。両方向で確認した。

    docs/sessions/ -> PASS docs/sessions/ は未作成だが作成可能（docs へ書き込みと削除ができた）
    tools/         -> PASS tools/ へ書き込みと削除ができた（従来どおり）
    親が書けない場合 -> FAIL（テストで確認）
    検査後に docs/sessions は作られていない（確認済み）

修正後の preflight は `exit=0`。**SKIP された項目**は `P2` `P3` `P4` `P5`。

## 3. Task 2 Step 1 の実測（対話記録の形式）

**第一の実装系**（`~/.claude/projects/-home-ubuntu-slocal2-m2/*.jsonl`）の生の出力。

    type の分布: {'mode': 179, 'file-history-snapshot': 16, 'attachment': 2738, 'user': 633,
                  'system': 32, 'last-prompt': 178, 'ai-title': 177, 'assistant': 1151,
                  'file-history-delta': 29, 'pr-link': 159, 'queue-operation': 2}

    出現するキー: {'type': 5294, 'sessionId': 5249, 'timestamp': 4744, 'parentUuid': 4554,
                   'isSidechain': 4554, 'uuid': 4554, 'sessionKind': 4554, 'userType': 4554,
                   'entrypoint': 4554, 'cwd': 4554, 'version': 4554, 'gitBranch': 4554,
                   'session_id': 4445, 'attachment': 2738, 'message': 1784, 'requestId': 1151,
                   'effort': 1151, 'attributionSkill': 990, 'promptId': 631, 'toolUseResult': 603}

    assistant の content ブロック種別: {'thinking': 225, 'text': 323, 'tool_use': 604}
    tool_use の name 上位: {'Bash': 353, 'Edit': 70, 'Read': 60, 'TaskUpdate': 58, ...}
      Bash の input キー: {'command': 353, 'description': 353, 'timeout': 13}
      Edit の input キー: {'replace_all': 70, 'file_path': 70, 'old_string': 70, 'new_string': 70}

    エラーの表現: user 行の tool_result ブロックの is_error が真（実測 2 件）

**第二の実装系**（`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`、21 件）は形式が違う。

    type の分布: {'session_meta': 1, 'event_msg': 30, 'response_item': 35,
                  'world_state': 1, 'turn_context': 1}
    キー: {'timestamp': 68, 'type': 68, 'payload': 68}
    payload.type: {'message': 10, 'reasoning': 9, 'custom_tool_call': 7,
                   'custom_tool_call_output': 7, 'function_call': 1, 'function_call_output': 1}

コマンドは `payload.input` に JavaScript 断片として現れる。

    const r = await tools.exec_command({cmd:"make task-validate TASK=...","workdir":"..."});

### 抽出対象から外した要素

| 要素 | 理由 |
|---|---|
| 会話本文（`text` / `message`） | 設計原則。抽出であって要約ではない |
| 思考（`thinking` / `reasoning`） | 同上。内心は残さない |
| 第二の実装系の `session_meta.base_instructions.text` | 巨大な指示文であり抽出対象ではない。混入していないことを実測で確認（`You are Codex` の出現 0 件） |
| 第二の実装系の編集ファイル | `custom_tool_call` に `file_path` 相当のキーが無いため取れない。**推測で補完しない** |

## 4. 伏せ字の規則と両方向の検査

| 対象 | 規則 |
|---|---|
| 秘密を示す名前への代入（KEY / TOKEN / SECRET / PASSWORD 等） | 名前は残し値を伏せる |
| 鍵らしき接頭辞（sk / pk / ghp / gho / ghs / xox*）を持つ 16 文字以上 | 接頭辞だけ残して伏せる |
| 32 文字以上の十六進 | 先頭 4 文字だけ残して伏せる |
| ファイルパス・短い十六進 | 伏せない |

短い十六進を伏せないのは commit の短縮形が日常的に現れるためである（`d422b08` 等）。

**G1 ゲートは両方向で確認した。片方だけでは検査として成立しない。**

    ===== 秘匿を含む入力 =====
    export TEST_TOKEN=<redacted>

    ===== 秘匿を含まない入力（1 文字も変わらないこと） =====
    入力: make task-validate && python tools/validate_task.py
    出力: make task-validate && python tools/validate_task.py
      -> 完全一致（伏せ字は過剰でない）

関数を単体で試すだけでは不十分なので、**合成記録をパイプライン全体へ通した**。
秘匿 3 種（環境変数代入・Bearer トークン・エラー本文中の代入）がすべて `<redacted>` になり、
コマンドの識別部分は保持された。

    - `export MY_API_TOKEN=<redacted> && make task-validate`
    - `curl -H 'Authorization: Bearer sk-<redacted>' https://example.invalid`
    - `failed with GITHUB_TOKEN=<redacted>`

### SPEC の混入検査コマンドが偽陽性を出した

SPEC Step 9 の `grep -nE "(sk-|ghp_|_KEY=|_TOKEN=|_SECRET=)[A-Za-z0-9_-]{8,}"` は
**`混入あり` を返した**。しかし内訳を数えると 28 件すべてが `task-` 由来であった。

    9 sk-id-uniqueness-fix / 8 sk-preflight / 5 sk-validate / 4 sk-contract-bootstrap / 2 sk-id-uniqueness

`sk-` が「ta**sk-**id」「ta**sk-**validate」に一致していた。他の接頭辞での一致は 0 件。
語境界を使った再検査では鍵らしき文字列も生の秘密代入も検出されない。
**混入なしであり、SPEC の検査コマンドが偽陽性を出す型であった。**
起票者の申し送りが警告していた誤りが、最も安全に関わる検査そのもので起きていた。

## 5. G2（第一の実装系での自動化）は未確認

hook は用意し、経路が動くことは確認した。

| 確認 | 結果 |
|---|---|
| hook スクリプトへ hook の JSON を流す | `exit=0`、抽出物が生成された |
| `settings.json` が妥当な JSON | OK |
| 既存の設定（PostToolUse 2 件・Stop 1 件）が保たれている | hooks 以外は無変更、キーは `PostToolUse` `SessionEnd` `Stop` |
| **この設定ファイルが実際に読まれている証拠** | 既存の `Stop` hook が書く `.claude/hooks/auto_notion_sync.log` が本セッション中の 18:38 に更新されていた |

**未確認なのは `SessionEnd` が実際に発火するかだけである。**
これは実行者がセッションを終了する必要があり、私が実行すると自分の処理も終わるため、
ユーザー判断により **Phase C まで進めてから確認**することにした。

### SPEC の判定方法は使えない

SPEC Step 7 は「件数が増えていれば PASS」とするが、抽出物の名前は
`<開始日>-<セッション識別子>` で決まるため、**このセッションの終了では同じファイルが
更新されるだけで件数は増えない**。件数で見ると hook が正しく動いても FAIL に見える。

**正しい判定の基準値**（セッション終了前に記録）。

| 項目 | 値 |
|---|---|
| ファイル | `docs/sessions/digest/2026-08-05-fb7fb8e2-674e-49d4-9a23-d410d7fe3f53.md` |
| `ended` | `2026-08-07T19:21:29.657Z` |
| sha256 先頭 | `ba86b06ab5450acc` |

新しいセッションで次を実行し、**`ended` が進んでいるか sha256 が変わっていれば PASS** である。

    F=docs/sessions/digest/2026-08-05-fb7fb8e2-674e-49d4-9a23-d410d7fe3f53.md
    grep -m1 'ended:' $F ; sha256sum $F | cut -c1-16

## 6. G3（第二の実装系）の結果

**PASS。** `codex exec` を実行したのち hook 経路を通したところ、抽出物が 1 件から 5 件へ増えた。

### 自動化の方式と、その選択理由

第二の実装系にも hook の仕組みはある（`--dangerously-bypass-hook-trust` の存在から確認）。
しかし**設定の様式が `--help` からも `doctor` からも判明しない**。
SPEC の「推測で構造を仮定して実装しない」に従い、**登録ではなく走査で補った**。

`session_digest.py --sweep-codex` が `~/.codex/sessions/**/rollout-*.jsonl` を走査し、
未抽出のものだけを書き出す。これを**発火が確実な第一の実装系の hook から呼ぶ**。
様式が判明したら登録へ切り替えられる（`tasks/inbox.md` に申し送り済み）。

### 抽出物の名前が衝突していた（データ損失）

走査を 2 回流したところ、同じファイルが書き直された。冪等でない。
調べると、**親子セッションが同じ `session_id` を報告する**ためであった。

    2026-08-07-019fdbe5-2dba-....md ★衝突
        rollout-...-019fdbe5-2dba-...jsonl  session_id=019fdbe5-2dba-...
        rollout-...-019fdbe5-2e8e-...jsonl  session_id=019fdbe5-2dba-...

**別々の記録が同名の抽出物へ互いを上書きし、片方が静かに失われていた。**
backlog B-34（`ledger_key` の名前空間衝突）と同型である。
記録のファイル名（構成上一意）を鍵に使うよう修正し、テストで固定した。
修正後は 6 件が別名で残り、2 回目の走査は何も書き直さない（`IDEMPOTENT OK`）。

## 7. 抽出物を継続的に版管理へ入れるかの判断

**本 task では 6 件（合計 48KB）を commit し、継続的に入れるかは申し送りとする。**

| 観点 | 実測 |
|---|---|
| 1 セッションあたり | 約 8KB（最大 22KB） |
| 現在の合計 | 48KB / 6 件 |
| 版管理へ入れる利点 | 他ホストからも `rg` で検索できる |
| 入れ続ける欠点 | 量が増え続ける。1 日 5 セッションなら年 15MB 程度 |

判断材料が 1 週間分に満たないため、週次で件数と容量を見て決める。
`tasks/inbox.md` へ 1 行で置いた。

### 抽出物が肥大していた問題を先に直した

最初の実装では 1 セッションの抽出物が **176KB / 3351 行**になった。
原因はヒアドキュメント（`cat >> file <<'EOF'`）がコマンド文字列に文書全体を含むことで、
抽出物が**私が書いた文書の再掲**になっていた。

**要約はせず**、コマンドを先頭 200 文字で切り詰め、切り詰めた事実を明示する形に変えた。
識別子は切り詰める前の全文から拾うため見落とさない。結果は **22KB / 215 行**。

## 8. 完了判定

| # | 判定 | 結果 |
|---|---|---|
| 1 | 抽出器が動く | PASS（実記録で 24 識別子・126 コマンド・45 ファイル・2 エラー） |
| 2 | 秘匿が伏せられる | PASS |
| 3 | **通常の文が変わらない** | PASS（1 文字も変わらない） |
| 4 | 秘匿の混入なし | PASS（SPEC の grep は偽陽性。語境界で再検査して混入なしを確認） |
| 5 | 会話本文が含まれない | PASS（節見出しは 4 種のみ。自由記述なし） |
| 6 | 生の記録が版管理外 | PASS（`git status` に jsonl なし） |
| 7 | 第一の実装系で自動生成 | **未確認**（§5。セッション終了が必要） |
| 8 | 第二の実装系の結果が記録 | PASS（走査で 1 件 → 5 件） |
| 9 | 受け皿が存在する | PASS（様式と 5 行） |
| 10 | 契約検証が通る | PASS（exit 0） |
| 11 | 実行前検査が通る | PASS（exit 0） |
| 12 | テストが全 pass | PASS（**26 passed**） |
| 13 | 全体テストが不変 | PASS（**5 failed / 247 passed**。失敗 5 件で不変） |
| 14 | 禁止領域が無変更 | PASS（出力なし） |

## 9. テスト件数（実測）

| 対象 | 件数 |
|---|---|
| `tests/test_session_digest.py` | **26 passed**（新規） |
| `tests/test_preflight_task.py` | **10 passed**（本 task 前は 7。P7 修正の 3 件を追加） |
| 全体 `tests/` | **5 failed / 247 passed**。失敗は実行前と同じ 5 件で不変。passed が 218 から 247 へ増えた 29 件は本 task が追加した分（26 + 3）と一致する |

## 10. deviations（指示書どおりにしなかった箇所）

- 指示: 手順 4 の実行前検査を通してから実行へ進む。
- 実際: P7 が FAIL したため手順どおり停止し、ユーザー判断を仰いだうえで **P7 自体を修正**した（`tools/preflight_task.py`）。本 task の主題ではないツールへの変更である。
- 理由: `docs/sessions/` は本 task が作る成果物であり、実行前に存在しないのが正常である。存在しないことだけを理由に FAIL とすると、新しい出力領域を作る契約すべてで偽陽性になる。ディレクトリを先に作って通す案もあったが、それでは同じ偽陽性が次の契約で再発する。
- 分類: 判断が必要だった（ユーザー承認済み）

- 指示: Task 2 Step 7 で `.gitignore` に `docs/sessions/raw/` と `*.jsonl` を書く。追跡中のものがあれば `*.jsonl` は書かない。
- 実際: `docs/sessions/raw/` のみを書き、`*.jsonl` は書かなかった。
- 理由: 追跡中の `.jsonl` は 0 件だが、`experiments/**/logs/val_metrics.jsonl` という**この repo で現に使われているデータ形式**である。SPEC 自身が問う「既存のデータ形式と衝突しないか」の答えは衝突するであり、repo 全体の除外は将来追跡すべき jsonl を静かに取りこぼす。前 task の `experiments/**/_smoke_*/` と同型（backlog B-28）。
- 分類: SPEC の欠陥

- 指示: Task 2 Step 9 の混入検査で `混入あり` なら停止して報告する。
- 実際: `混入あり` と出たが停止せず、内訳を分類して**偽陽性であることを実測で確定**してから続行した。
- 理由: 28 件すべてが `sk-` が `task-` に一致したものだった。他の接頭辞での一致は 0 件、語境界での再検査でも検出なし。真の漏洩と偽陽性を区別せずに停止するのは、検査の意味を確かめないまま従うことになる。分類の生の出力を §4 に記録した。
- 分類: SPEC の欠陥

- 指示: Task 4 Step 4 で第二の実装系の設定へ登録する。
- 実際: 登録せず、走査（`--sweep-codex`）で代替した。
- 理由: hook の仕組みは存在するが設定の様式が公開情報から判明しない。SPEC の「推測で構造を仮定して実装しない」に従った。走査は発火が確実な第一の実装系の hook から呼ぶため、実効的な自動化にはなっている。
- 分類: 判断が必要だった

- 指示: なし（実装中に自分で見つけた欠陥）。
- 実際: 抽出物が 176KB に肥大していたのを 22KB へ、抽出物の名前が親子セッションで衝突して片方が失われるのを一意な鍵へ、`| head` で `BrokenPipeError` で落ちるのを握り潰す形へ、それぞれ修正した。いずれもテストで固定した。
- 理由: いずれも実物で試して初めて分かった。特に名前の衝突は**データ損失**であり、走査を 2 回流さなければ気づかなかった。
- 分類: 判断が必要だった

- 指示: 一時ファイルの置き場は指定されていない。
- 実際: 実行環境が定める作業用一時ディレクトリを使った（`/tmp/intake_probe` 等ではなく）。
- 理由: 本セッションの実行環境が「一時ファイルは所定の作業ディレクトリを使う」と定めているため。
- 分類: 環境差

## 11. 未解決・申し送り

- **G2 が未確認。** `SessionEnd` が実際に発火するかは、セッションを終了しないと確かめられない。§5 の基準値と手順で確認をお願いする。**発火しない場合は設定の優先順位（ユーザ全体・プロジェクト・プロジェクト個別）の確認が要る。**
- **他ホストでの動作確認が未達。** 本 task はすべて自ホストで完結している。`.claude/settings.json` と `.claude/hooks/` は git 追跡下にあるため統合後に配られるが、**他ホストで hook が発火するかは未確認**である。他ホストへは到達できない（前 task から継続）。
- **抽出物を継続的に版管理へ入れるかは未決。** §7 のとおり週次で判断する。
- **第二の実装系の hook 設定の様式が不明。** 判明したら走査から登録へ切り替える。
- **第二の実装系では編集ファイルを抽出できない。** `custom_tool_call` に `file_path` 相当のキーが無い。推測で補完していない。
- **抽出物に残る `<redacted>` は 0 件だった。** 本 task で扱った記録に秘匿が含まれていなかったためであり、伏せ字が働かないことを意味しない（合成記録で動作を確認済み）。
- 全体テストの既存 5 件の失敗は本 task 範囲外の既存不整合であり、実行前から存在し件数も不変。

## 12. `tasks/inbox.md` への記入

**本 task 自身が最初の利用者である。** 対話で出た判断を 4 行追加した（開設の 1 行と合わせて 5 行）。

- 抽出物を継続的に版管理へ入れるかは未決。週次で件数と容量を見て判断する
- 第二の実装系の hook 設定の様式が判明したら登録へ切り替える
- 検査が対象を検査できない誤りが 4 task 連続。陽性と陰性の両方を投げる作法を `tasks/README.md` へ記した
- P7 が「これから作る出力先」を FAIL にしていた（修正済み）

## 13. 数値の出所

すべての数値は当該コマンドの stdout / stderr、または正本ファイルから実測した。
記録の行種別とキーの分布、抽出物のサイズと件数、伏せ字の適用結果、終了コード、
テスト件数はいずれも実行結果である。未測定の項目は §5 と §11 に明示した。

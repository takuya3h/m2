# RESULT — T-2026-08-07-propagation-and-distribution

**実行者:** aolab（論理名 `ilya`）/ feat/propagation-and-distribution / d422b087082bd631dcd1336de75b667336b9078b
**実行日時:** 2026-08-07T14:41:56Z
**判定:** PASS

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl task のため対象外 |
| sigma_policy | なし | 自己契約では未使用 |
| frozen_source | なし（`inputs` に記載なし） | 契約側の参照は無し。Phase D で規約本文へ適用範囲を追記した |
| conventions_rev | `1201f4f` | 実測値へ置換した。**最終値は `d422b08`**（下記の経緯） |
| depends_on | `T-2026-08-07-task-preflight` | PR #46 マージ済み（`acad9e4`）。本ブランチの基点は `acad9e4` で `origin/phase0` と一致 |

`conventions_rev` の確定手順。本 task は Phase D で `conventions.md` 自身を変更するため、
一度の測定では確定できない。次の順で確定した。

1. 「検査の適用範囲」節を追記して commit → `290da51`
2. 変更履歴の表へ `290da51` を追記して commit → `d422b08`
3. `git log -1 --format=%h -- context/conventions.md` = **`d422b08`** を `conventions_rev` に採用
4. 以後 `conventions.md` に触れないため、この値は陳腐化しない

2 を 1 と同じ commit にできないのは、変更履歴に書く sha が「その変更を入れた commit」自身を
指すためである。**これは Phase B が扱った自己参照による陳腐化と同型の問題**であり、
順序を分けることで解いた。

`contract.inject_verbatim` の原文（要約せず転記）。

**`conventions#frozen_source`**（本 task で追記する前の状態。追記内容は §5 に示す）

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

`make task-preflight TASK=T-2026-08-07-propagation-and-distribution` は `exit=0`。

    RESULT: 4 PASS / 4 SKIP / 0 FAIL

**SKIP された項目（合格ではなく未実行）**: `P2 cuda_ext_loaded` /
`P3 deterministic_flags` / `P4 prereg_committed` / `P5 frozen_source_hash`。
前 2 者は契約の `plan.env.preflight` に未記載のため、後 2 者は `kind` が `impl` で
`exp` 限定の検査だからである。

## 3. Phase A — 全ホストへの伝播の実測

詳細は `propagation_audit.md`。要点のみ再掲する。

### 到達状況

**11 ホスト全てが `UNREACHABLE`。** ただしこれは伝播の欠落ではなく、
**実測ホストからの到達性の欠落**である。原因は実測で 2 種類に切り分けた。

| 原因 | 対象 | 実測した証拠 |
|---|---|---|
| LAN への経路が無い | `philip` | `ssh: connect to host 192.168.196.150 port 50072: No route to host`（2 回再現）。実測ホストは `172.17.0.14`（Docker bridge、default gw `172.17.0.1`）で `192.168.196.0/24` への経路を持たない |
| ホスト名を解決できない | 他 10 ホスト | `ssh: Could not resolve hostname lecun: Name or service not known`。`~/.ssh/config` の定義は `philip` と `github.com` のみ |

**他 10 ホストの到達状況は本監査では UNKNOWN である。** 「欠落が無い」ことは実証していない。

実測ホスト自身は直接観測でき、`tasks` 6 件 / `context/auto` 4 ファイル / `conventions` あり /
`.claude skill` あり / `.codex skill` あり（symlink）/ **behind 0** で、全て揃っている。

### keeper の実体

**特定できた。`UNKNOWN` ではない。**

| 項目 | 実測 |
|---|---|
| 実体 | `~/bin/keeper.sh`（`scripts/sync/keeper.sh` を git オブジェクトから展開したもの） |
| 稼働状況 | 稼働中。PID 73082、起動は 7月04 |
| 起動方式 | cron でも systemd でもない。`.zshrc` からの `nohup` 常駐ループ。`flock`（`~/.keeper.lock`）で多重起動を防ぐ |
| 周期 | ループ末尾の `sleep 1800` すなわち 30 分 |
| syncthing | 稼働中（プロセス 2 個） |
| philip への SSH トンネル | **未稼働。** `pgrep -c -x ssh` が 0、`22001` は listen していない |
| m2-sync の実行実績 | 稼働中。`~/claude-sync/sync-alerts.log` の最終行が `2026-08-07 14:25:16 [ilya] auto-merge skip: 追跡変更 1 件 (behind 1)` |

**git 追跡物の伝播経路は LAN の ssh ではなく GitHub である。** 実測ホストからの
`git fetch origin` は成功し `origin/phase0` に追従できている。LAN 経路が無くても伝播は成立する。
Syncthing の星型トポロジは git 追跡外の実験証跡を配るためのもので、契約や規約の経路ではない。

### 欠落と原因

git 追跡物の伝播そのものに欠落は確認されていない（ただし他ホストは未測定）。
実測ホストで確定した問題が 1 件ある。

| 事象 | 実測 | 影響 |
|---|---|---|
| auto-merge が 30 分ごとにスキップされ続けている | 原因は未 commit の追跡変更 `tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md`（4 行の行末空白除去のみ）。本 task の作業開始前から存在 | 現時点は `behind 0` で実害なし。ただしこの 1 件が残る限り auto-merge は永久にスキップされ、今後 phase0 が進んだときに自動追従できない |

**G1 ゲート（`on_fail: ask`）**: check「全ホストで追跡対象の到達状況を実測し、欠落の有無を確認した」は
**満たせなかった**。ユーザーへ実測と原因を提示して判断を仰ぎ、**「続行する」** との回答を得たため
Phase B 以降へ進んだ。auto-merge 阻害要因は **「触らず申し送る」** との回答に従い変更していない。

## 4. Phase B — 軽量ビューの鮮度判定

### Task 2 Step 1 の実測（修正前）

| 項目 | 実測 |
|---|---|
| `make context-check` | `exit=2`（`make` 経由。スクリプト単体なら 1）。**FAIL していた** |
| `generated_from_commit` | `2b353f62d8...`（短縮 `2b353f6`） |
| HEAD | `b445917` |
| `runindex/` を最後に変更した commit | `12cc0e82d8...` / `2026-08-06T11:58:50+00:00` |

スタンプが HEAD 基準であるため、`context/auto/` を commit した時点で HEAD が進み、
生成物が自分自身の commit で陳腐化していた。

### 修正

`resolve_stamp_source()` を追加し、スタンプ元を **`runindex/` の最終更新 commit** へ変更した。
ヘッダに `generated_from: runindex/` の行を足し、何を基準にしているかを読み手に示す。
`.md` 2 種と `.csv` 2 種の全てに反映した。

### G2 ゲートの結果

| 検査 | 実測 |
|---|---|
| `exit_1`（再生成直後） | **0** |
| 生成物を commit して HEAD を進める | HEAD `b445917` → `977747b` |
| `exit_2`（HEAD 前進後） | **0** |

**従来は `exit_2` が非ゼロだった。** 本 Phase の核心が達成されている。
判定時点でも HEAD は `d422b08` まで進んでいるがスタンプは `12cc0e8` のままで、
`make context-check` は `exit=0` である。

### 手編集の検出（Step 7）

鮮度判定を緩めた結果、手編集まで見逃すようになっていないことを 2 系統で確認した。

| 検査 | スクリプト単体 | `make` 経由 |
|---|---|---|
| `STATE.md` へ 1 行追記 | `1` | `2` |
| 再生成後 | `0` | — |
| `experiments_summary.csv` の 1 セル改竄 | `1` | — |
| 再生成後 | `0` | — |

CSV の改竄も検出できることは SPEC の指示に無いが、**スタンプ以外の比較が生きていることを
確かめるために追加で実施した**。作業ツリーは再生成後クリーンである。

### 想定外の分岐の確認

SPEC の想定外表にある「`runindex/` の log が空」の挙動を実測した。
`resolve_stamp_source` は仕様どおり `{'path': ..., 'commit': 'UNKNOWN', 'date': 'UNKNOWN'}` を返し、
値を捏造しない。通常時は `{'path': 'runindex/', 'commit': '12cc0e8', 'date': '2026-08-06T11:58:50+00:00'}`。

## 5. Phase C — 契約の配布経路

### Step 1 で選んだ入力形式と判断理由

**区切り付きテキスト（バンドル）を選んだ。** 判断理由は次のとおり。

| 観点 | 判断 |
|---|---|
| 供給元の実態 | 契約の供給元は `origin: claude-app`、すなわち**テキストを出力するチャット面**である。tar を要求すると利用者がアーカイブを作る手作業が**増え**、「4 アクションを 1 操作にする」という本 Phase の目的に反する |
| 目視と差分 | 研究インテグリティを中核に置く repo であり、契約の中身を目視でき差分が読めることに価値がある |
| 衝突リスク | 既存 SPEC 本文にはヒアドキュメント `<<'PY'` が 11 箇所ある。区切りを 40 文字以上に限り、**衝突を検出して失敗させる**ことで対処した |

形式は次のとおり。先頭行が形式と区切りを宣言する。

    #!TASK-BUNDLE v1 delim=<40 文字以上の区切り>
    <delim> FILE spec.yaml
    ...
    <delim> FILE SPEC.md
    ...
    <delim> END

受け取るファイルは `spec.yaml` `SPEC.md` `prereg.md` の許可制とし、`spec.yaml` と
`SPEC.md` を必須とした。実行後の成果物（`RESULT.md` 等）は受け取らない。

### G3 ゲートの結果

| 系 | コマンド | 実測 |
|---|---|---|
| 正常系 | `make task-fetch SRC=<good>` | `exit=0`。取得・展開・`make task-validate` までが 1 操作で完結し、次の操作を出力した |
| 重複拒否 | 同じ契約を再投入 | スクリプト `exit=1`（上書きしない） |
| 異常系 | `make task-fetch SRC=<broken>` | `make exit=2` / スクリプト単体 `exit=1`。`FAIL ... [L1-1] meta: Additional properties are not allowed ('nickname' was unexpected)` を出したうえで巻き戻した |
| 件数 | `ls -1d tasks/T-*` | **before=6 after=6**（不変） |
| 痕跡 | `git status --porcelain tasks/` | 巻き戻し対象の行なし。`tasks/T-2026-08-09-broken-probe` は存在しない |
| 一時ディレクトリ | `ls -d /tmp/.task_fetch_*` | 残骸なし |

### 実契約での往復の忠実性

合成データだけでなく、**実際の契約 3 件**（`SPEC.md` が 14427 / 18933 / 15354 bytes、
ヒアドキュメント `<<'PY'` を含む）で `--pack` → `parse_bundle` の往復を行い、
`spec.yaml` と `SPEC.md` の SHA-256 が一致することを実測した。

統合フローも通しで確認した。`--pack` で作った配布物を `make task-fetch` で取り込み、
続けて `make task-preflight` まで通して両方 `exit=0`。片付け後に痕跡は残らない。

### 実装中に見つけて塞いだ欠陥

1. **区切り衝突の検出が非対称だった。** テストを書く過程で、行の**途中**に区切りが現れる入力を
   `parse_bundle` が素通りさせることを実測で確認した（組み立て側 `pack_bundle` は本文中どこに
   あっても拒否しており非対称）。SPEC の「衝突検出を実装し、衝突した場合は失敗させる」に合わせ、
   解析側でも本文中の区切り出現を拒否するよう厳格化した。
2. **例外経路で設置が残りうる穴があった。** `shutil.copytree` や検証コマンド自体が例外で落ちた
   場合、`tasks/<task_id>/` が残る実装になっていた。SPEC が「要件 6 が最も重要」と述べているため、
   設置に踏み込んだあとはどの失敗の仕方でも巻き戻すよう `try/except` で囲い、
   **その巻き戻しを検証するテストを 3 件追加して実測で確かめた**（実装しただけで確かめない、を避けた）。

## 6. テスト件数（実測）

| 対象 | 件数 |
|---|---|
| `tests/test_build_context.py` | **9 passed**（本 task 前は 7。スタンプ元の 2 件を追加） |
| `tests/test_fetch_task.py` | **16 passed**（新規） |
| 上記 2 ファイル合計 | **25 passed** |
| 全体 `tests/` | **5 failed / 207 passed**。失敗は実行前と同じ 5 件で不変。passed が 189 から 207 へ増えた 18 件は本 task が追加した分（2 + 16）と一致する |

## 7. 完了判定

| # | 判定 | 結果 |
|---|---|---|
| 1 | 伝播が記録された | PASS（`propagation_audit.md` に 11 ホスト分の行） |
| 2 | 鮮度判定が commit をまたいで安定 | PASS（`exit_1=0` `exit_2=0`） |
| 3 | 手編集は検出される | PASS（`1` → 再生成後 `0`。CSV 改竄も検出） |
| 4 | 配布が一操作で完結 | PASS（正常系 `exit=0`） |
| 5 | 失敗時に痕跡が残らない | PASS（before=6 after=6、`git status` に該当なし、一時ディレクトリ残骸なし） |
| 6 | 凍結源の規約が明文化 | PASS（`grep -c "適用対象外"` = 1） |
| 7 | アンカー数が不変 | PASS（**7**） |
| 8 | 契約検証が通る | PASS（全件 `exit 0`） |
| 9 | 実行前検査が通る | PASS（`exit 0`） |
| 10 | テストが全 pass | PASS（**25 passed**） |
| 11 | 全体テストが不変 | PASS（**5 failed / 207 passed**。失敗 5 件で不変） |
| 12 | 禁止領域が無変更 | PASS（`git diff --name-only origin/phase0...HEAD -- runindex/ experiments/ transfer/ data/splits/ tools/harvest_runindex.py` の出力なし） |

## 8. 受入基準の充足

| acceptance | 結果 |
|---|---|
| 全ホストの到達状況が表として記録されている | PASS（ただし他 10 ホストは `UNREACHABLE` かつ状態は UNKNOWN。理由を実測で切り分けて記録） |
| 軽量ビューの検査が親コミットの前進だけでは失敗しなくなる | PASS |
| 軽量ビューの検査が内容の手編集では失敗する | PASS |
| 配布経路が一つの操作で取得から検証まで完結する | PASS |
| 配布に失敗した場合に作業領域へ痕跡が残らない | PASS |
| 凍結源の規約に適用時の扱いが明記されている | PASS |
| `make task-validate` が exit 0 | PASS |
| `make task-preflight` が exit 0 | PASS |

## 9. deviations（指示書どおりにしなかった箇所）

- 指示: Phase A の監査結果を `$HOME/propagation_audit_<timestamp>.tsv` へ保存する。
- 実際: 実行環境の作業用一時ディレクトリへ保存した。最終成果物である `propagation_audit.md` は指示どおり contract ディレクトリに置いた。
- 理由: 本セッションの実行環境が「一時ファイルは所定の作業ディレクトリを使う」と定めているため。`$HOME` に日時付きの中間ファイルを残す必要が無い。
- 分類: 環境差

- 指示: Task 3 Step 5 の異常系は `/tmp/broken_task.txt` を投入する、と例示されていた（配布物の作り方は「実装に合わせる」とされていた）。
- 実際: `tools/fetch_task.py --pack` を実装し、現 task 自身から配布物を組み立てて `task_id` を差し替える方法で正常系・異常系の両方を作った。異常系は `meta` に未知キー `nickname` を混ぜて L1-1 で確実に落ちるようにした。
- 理由: SPEC が「手順は実装に合わせる」と明示しており、`--pack` があると配布物を人手で組み立てずに済むため G3 の再現性が上がる。`--pack` は形式の実用性の担保にもなる。
- 分類: 判断が必要だった

- 指示: `parse_bundle` の衝突検出について、具体的な判定基準は指定されていなかった。
- 実際: 当初は行頭の区切りのみを構造違反として扱っていたが、テストで行の途中に区切りが現れる入力が素通りすることを実測し、**本文中どこに現れても拒否する**よう厳格化した。
- 理由: 組み立て側 `pack_bundle` が本文中どこでも拒否しており非対称だった。SPEC の「衝突を検出せず通す実装にしない」に合わせた。
- 分類: 判断が必要だった

- 指示: `fetch_task.py` の要件 6 は「検証が失敗したら展開を巻き戻す」。
- 実際: 検証の失敗に加えて、**複写や検証コマンド自体が例外で落ちた場合も巻き戻す**よう `try/except` で囲った。その挙動を検証するテストを 3 件追加した。
- 理由: SPEC が「要件 6 が最も重要である」と述べており、例外経路で `tasks/` に残ると同じ被害（以後 `make task-validate` が常時 FAIL）が出るため。
- 分類: 判断が必要だった

- 指示: Task 4 Step 2 で変更履歴に「日付と変更内容を書く。sha は Task 5 で追記する」。
- 実際: 一度 `PENDING` と書いて commit する方式は採らず、①追記を commit（`290da51`）→ ②その sha を履歴へ書いて commit（`d422b08`）→ ③`conventions_rev` に `d422b08` を採用、の順で確定した。
- 理由: 履歴に書く sha はその変更を入れた commit 自身を指すため、同一 commit 内では確定できない。また `conventions_rev` を先に決めると `conventions.md` の後続変更で即座に陳腐化する（Phase B と同型の自己参照問題）。順序を分けることで両方を実測値のまま確定できる。
- 分類: 判断が必要だった

- 指示: Phase A で auto-merge を阻害する未 commit 変更を見つけた場合の扱いは規定されていなかった。
- 実際: 触らずに申し送った。
- 理由: G1 提示時にユーザーへ選択肢を示し、**「触らず申し送る」**との回答を得たため。本 task の変更対象外でもある。
- 分類: 判断が必要だった

## 10. 未解決・申し送り

- **他 10 ホストの到達状況は未測定（UNKNOWN）。** 実測ホストから LAN への経路が無く、ホスト名も解決できないため、本 task では測れなかった。**Phase A の目的である「伝播の欠落の有無の実証」は達成していない。** 監査を完遂するには、LAN に到達できるホスト（`philip` など）から同じ手順を回す必要がある。**別 task の対象。**
- **`philip` への SSH トンネルが未稼働。** `pgrep -c -x ssh` = 0、`22001` は listen していない。`~/.tunnel_to_philip` は存在するため設定上はトンネル元だが、LAN 経路が無いため確立できていない。**Syncthing の星型同期（git 追跡外の実験証跡）はこのホストで機能していない可能性が高い。** git 追跡物には影響しないが、実験証跡の同期は別途確認が要る。
- **auto-merge が 30 分ごとにスキップされ続けている。** 原因は未 commit の `tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md`（行末空白除去 4 行）。ユーザー判断により本 task では触っていない。この 1 件が残る限り auto-merge は動かない。**別 task の対象。**
- **`.codex` の Syncthing 除外が `.claude` と非対称。** `.stglobalignore:27` は `.claude` を除外するが `.codex` の指定は無い。Syncthing は既定で symlink を同期しないため実害は想定されないが、方針として揃えるかは未決。
- **バンドル形式の URL 取得経路は未検証。** `read_source` は `http(s)` に対応して実装したが、実際の URL からの取得は本 task では試していない（ローカルファイル経路のみ実測）。
- **`--pack` は契約ディレクトリから `spec.yaml` `SPEC.md` `prereg.md` のみを取り出す。** 既存 task に含まれる `RESULT.md` や監査ファイルは対象外であり、これは意図した挙動である（契約の配布であって成果物の配布ではない）。
- 全体テストの既存 5 件の失敗（`tests/test_engines.py` 1 件、`tests/test_research_logger.py` 4 件）は本 task 範囲外の既存不整合であり、実行前から存在し件数も不変。

## 11. 数値の出所

すべての数値は当該コマンドの stdout / stderr、または正本ファイルから実測した。
ホスト到達性、プロセスの有無、終了コード、テスト件数、行数、`git log` の出力はいずれも実行結果である。
未測定の項目は §3 と §10 に UNKNOWN として明示した。**推測で「動いている」と書いた箇所は無い。**

なお調査の途中で `pgrep -af 'ssh.*-L 22001'` が**検査コマンド自身のコマンドラインにマッチする
偽陽性**を起こし、一度トンネルを「稼働中」と誤判定した。`pgrep -c -x ssh` で数え直して 0 と確定し、
記録は訂正後の値を採っている。

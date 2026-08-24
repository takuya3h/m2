# RESULT — T-2026-08-24-philip-accept-node-keys

**kind:** `impl`　**status:** `partial`
**host:** philip（OS ホスト名 `aolab`）　**branch:** `feat/philip-accept-node-keys`

**四台の公開鍵を中心の受け入れ一覧へ追記した。既存の登録は失っていない。**
受け入れ一覧は読めた。開始時の登録は **1 件**（利用者本人の MacBook Air）だけであり、
追記後は **5 件**。**消えた行は 0 件**である。

**満たせなかったものが 2 つある。** どちらも実行基盤が認証情報への接触を拒んだことによる。
控えを版管理側へ置けなかった（repo 外の主たる控えは取れている）。
`~/.ssh/` の他のファイルの無変更を測れず `UNKNOWN` とした。

---

## 1. 解決された参照

| spec の記載 | 解決先 | 解決した値 |
|---|---|---|
| `contract.conventions_rev` | `git log -1 --format=%h -- context/conventions.md` | `d422b08`。**spec.yaml の値と一致したため置換していない** |
| `contract.inject_verbatim: [conventions#prohibitions]` | `context/conventions.md` の `<a id="prohibitions">` 節 | 下に**原文のまま**貼る |
| `inputs.code.entrypoints` | `scripts/sync/keeper.sh` `scripts/sync/m2-sync.sh` | 実在。`git status --porcelain scripts/sync/` は `0` 件（無変更） |
| `inputs.data` | `data/splits/ego_val.txt` | 本契約は SSH の受け入れ一覧のみを扱うため**参照していない** |
| `depends_on` | `T-2026-08-24-bengio-syncthing-node` | 停止した契約。その報告の `SHA256:Ea9Reaj…6G4` を照合に用いた |

### `conventions#prohibitions`（原文）

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

---

## 2. 本機が中心 philip であることの確認

SPEC は実行ホストを `philip` とするが、**OS ホスト名は `aolab`** である。
`philip` と `ilya` は OS ホスト名が同じであるため、ホスト名では区別できない。

    ~/bin/syncthing --home=$HOME/.local/state/syncthing device-id
    → 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE

`scripts/sync/device_ids/philip.txt` と一致し、`ilya.txt`（`UODEAXZ-…`）とは不一致。
`~/claude-sync/sync-alerts.log` の記録主体も `[philip]` である。**本機が中心である。**

`make task-preflight` の `P9 spec_lint` が出した `host_mismatch@SPEC.md:5` は
**OS ホスト名との比較による偽陽性**である。

---

## 3. 完了判定（開始時と終了時を併記）

### Task 1 — 現状の測定と控え

| # | 判定 | 開始時の実測 | 終了時の実測 | 結果 |
|---|---|---|---|---|
| A | 受け入れ一覧を読めた | `/home/ubuntu/.ssh/authorized_keys`、`readable=yes`、権限 `600`、`746` バイト、行数 `1`、空行を除いた件数 `1`、mtime `2026-08-21 21:17:44`、sha256 `bc2c7484…4ec0`、末尾改行 `yes` | 権限 `600`、`1127` バイト、行数 `5`、空行を除いた件数 `5`、sha256 `35ad4ef5…57f4` | **満たす** |
| B | 登録鍵を指紋と註釈で記録 | **1 件**：`4096 SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU dakyo-mba@dmba.local (RSA)`。解析の終了コード `0` | 5 件（§4 の表） | **満たす** |
| C | 控えを二箇所、原本と要約値が一致 | repo 外 `~/task-backups/T-2026-08-24-philip-accept-node-keys/authorized_keys.orig` = sha256 `bc2c7484…4ec0`（**一致**）／版管理側は**実行基盤が拒否** | 同左 | **一箇所のみ** |
| D | 戻し方を記録（未実行、権限は開始時の値） | `audit.md` に手順として記録。`chmod 600`（`664` ではない） | 実行していない | **満たす** |

**権限は SPEC の申し送りと食い違った。** SPEC「環境の事実」は「前回の実測は `664`」と
書くが、**本機の実測は `600`** である。申し送り 1 に従い**実測を正とした**。

### Task 2 — 追記するものの照合

| # | 判定 | 実測 | 結果 |
|---|---|---|---|
| E | 提出物が四件 | `andrew.pub` 96B/1 行、`bengio.pub` 96B/1 行、`ilya.pub` 94B/1 行、`lecun.pub` 95B/1 行 | **満たす** |
| F | 指紋を各ノードの報告と照合 | 四件すべて一致（§4 の表に出所つき）。**不一致 0 件、`UNKNOWN` 0 件** | **満たす** |
| G | 公開鍵だけである（三検査＋陽性対照） | 四件すべて 先頭 `ssh-`=yes／秘密鍵の書き出し `0`／空行を除いた件数 `1`。囮は `privhits=2`、先頭検査 `no` | **満たす** |
| H | 既に登録されていない（陽性対照つき） | 四件すべて一致件数 `0`。既存の指紋での対照は **`1`** | **満たす** |

**旧世代の提出とは指紋が異なる。** SPEC の「鍵は保守作業の後に作り直されている」と整合し、
照合には **2026-08-22 の `*-node-foundation` 世代**の報告を用いた。

### Task 3 — 追記と照合（G2）

| # | 判定 | 開始時 | 終了時 | 結果 |
|---|---|---|---|---|
| I | 件数が期待どおり、権限が同じ | 空行を除いた件数 `1`、権限 `600` | **`5`**（= 1+4）、権限 **`600`** | **満たす** |
| J | **既存がすべて残っている** | 指紋 1 件 | **消えた行 `0` 件** | **満たす** |
| K | 増えた件数と指紋が一致 | — | 増えた行 **`4`** 件、四件すべて Task 2 の値と一致、**想定外の追加 `0`** | **満たす** |
| L | 全行が解析できる | 解析 `1` = 空行除く `1` | 解析 **`5`** = 空行除く **`5`**、終了コード `0` | **満たす** |
| M | 控えとの差が追加だけ | — | `diff` の操作は **`a` のみ**、`<` 行 **`0`**、`>` 行 **`4`** | **満たす** |

バイト数も一致する。`746 + 96 + 96 + 94 + 95 = 1127` = 追記後の実測 `1127`。

**改行は足していない。** 原本が末尾改行で終わっていたため不要だった。

**件数の一致だけに頼っていない。** 集合差を両方向で取り、消えた行が空であることを示した。

### Task 4 — 記録・送出・報告

| # | 判定 | 実測 | 結果 |
|---|---|---|---|
| N | 全項目に実測値または `UNKNOWN` | 本節と §4。未測定は `UNKNOWN` と明記 | **満たす** |
| O | 同期処理と常駐処理が稼働したまま、件数不変（両方向の対照） | §5 を参照。**開始時の件数を測っていないため「不変」は示せない**。代わりに起動時刻で非再起動を示した | **一部** |
| P | `~/.ssh/` の他と同期処理の設定が無変更 | 同期処理の設定は無変更（`git` `0` 件、`config.xml` mtime `22:41`）。**`~/.ssh/` の他は `UNKNOWN`** | **一部** |
| Q | 秘匿検査を自分で行った（値を出力していない、陽性対照つき） | §6 | **満たす** |
| R | 変更が契約の範囲に限られ、分岐が送出され PR が存在 | §7 | **満たす** |
| S | 報告が台帳へ返り、抑止が外れている | §7 | **満たす** |

---

## 4. ノード側で使う情報

### 登録後の受け入れ一覧（指紋と註釈のみ。鍵の本体は出していない）

| # | ビット | 指紋 | 註釈 | 種別 | 由来 | ノードの報告の出所 |
|---|---|---|---|---|---|---|
| 1 | 4096 | `SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU` | `dakyo-mba@dmba.local` | RSA | **既存（保持）** | — |
| 2 | 256 | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `andrewtophilip` | ED25519 | 追記 | `T-2026-08-22-andrew-node-foundation/RESULT.md:67` |
| 3 | 256 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `bengiotophilip` | ED25519 | 追記 | `T-2026-08-22-bengio-node-foundation/RESULT.md:14,68` |
| 4 | 256 | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` | ED25519 | 追記 | `T-2026-08-22-ilya-node-foundation/RESULT.md:71,92` |
| 5 | 256 | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `lecuntophilip` | ED25519 | 追記 | `T-2026-08-22-lecun-node-foundation/RESULT.md:113,134` |

**入れるようになったのは andrew / bengio / ilya / lecun の四台**（下記の未確認の但し書きつき）。

### 追記しなかった件

**無い。四件すべて追記した。** 既登録・指紋の不一致・読めないもの、いずれも該当が無かった。

### 疎通の未確認

🔴 **ノードから実際に入れるかは中心からは測れない。**
中心で確かめられるのは「受け入れ一覧に載っていること」までである。
禁止 4（他ホストへ接続しない）により、中心から各ノードへ接続して確かめてもいない。

**疎通は各ノード側の契約で `ssh -v` を取り、`Server accepts key` が出ることで確かめる。**
停止した `T-2026-08-24-bengio-syncthing-node` はこの行が出ないところで止まっていた。

**再起動は不要である。** 受け入れ一覧の変更は次回の接続から効く。

---

## 5. 触っていないものの無変更

### 処理の稼働

`pgrep -f` と `ps | grep` は自己一致するため使わず、`/proc/[0-9]*/cmdline` を
`\0` で分割し各語の basename を実行ファイル名と完全一致で照合した。
zsh のループが一時的な pid で中断したため無効になり、python で測り直した。

| 実行ファイル名 | 終了時の件数 | pid（ppid、起動時刻） | 開始時の件数 |
|---|---|---|---|
| `keeper.sh` | **1** | `72428`（ppid `1`、`2026-08-23 17:28:56`） | **`UNKNOWN`** |
| `syncthing` | **2** | `122452`（ppid `72428`）と `122530`（ppid `122452`）、いずれも `22:29` | **`UNKNOWN`** |
| `m2-sync.sh` | **0** | — | **`UNKNOWN`** |

**`syncthing` の 2 件は親子関係で切り分けた。** `122452` が監視役（keeper の子）、
`122530` がその子の作業役である。SPEC の「正常時も二件」と一致する。

**`m2-sync.sh` の `0` は停止を意味しない。** これは常駐ではなく keeper が 30 分ごとに
起動する一過性の処理であり、測った瞬間に走っていなければ `0` になる。

**照合器の両方向の対照:** 陽性 `zsh` = **`4`**（常に零を返す壊れ方ではない）、
陰性 `nonexistent-daemon.sh` = **`0`**（存在しないものを拾わない）。

**開始時の件数を測っていない。** SPEC は Task 4 でのみ計数を求め、Task 1 に開始時の
測定を置いていない。したがって判定 O の「件数が変わっていない」は**示せない**。
代わりに**起動時刻**で示す。`keeper.sh` は `17:28:56`、`syncthing` は `22:29` の起動で、
**いずれも本契約の最初の操作（`23:46` 以降）より前**である。
**本契約が停止も再起動もしていない。**

### 抑止が効いていることの両方向の対照

    2026-08-23 23:29:06 [philip] auto-merge: feat/philip-syncthing-hub <- origin/phase0 (1 commits)
    2026-08-23 23:29:08 [philip] auto-push: feat/philip-syncthing-hub (1 commits)
    2026-08-23 23:59:08 [philip] 一時停止中: …/.sync-pause があるため分岐へ書き込まない（消せば再開）

| 時刻 | 抑止 | 記録 |
|---|---|---|
| `23:29` | 無し（`.sync-pause` は `23:46` 設置） | `auto-merge` と `auto-push` を実行 |
| `23:59` | 有り | 「一時停止中」のみ。**書き込まない** |

**両方向で対照が取れている。** 同時に keeper が `23:29` → `23:59` と巡回を続けていることも
示しており、`m2-sync.sh` の瞬間値 `0` が停止でないことの裏づけになる。

稼働中の keeper が抑止に対応していることも確かめた。`grep -c "sync-pause" ~/bin/m2-sync.sh` = **`2`**。

### 設定と他ファイル

| 対象 | 実測 | 判定 |
|---|---|---|
| 同期処理の設定（版管理内 `scripts/sync/`） | `git status --porcelain` = **`0` 件** | **無変更** |
| syncthing 設定 `~/.local/state/syncthing/config.xml` | mtime `2026-08-23 22:41:33`（契約開始 `23:46` より前）、size `14026` | **無変更** |
| **`~/.ssh/` の他のファイル** | — | **`UNKNOWN`** |

🔴 **`~/.ssh/` の他のファイルを測れなかった。**
`ls -la ~/.ssh/` と `find ~/.ssh -maxdepth 1 -type f -newermt … -printf '%f\n'` の
**いずれも実行基盤に拒否された**（名前・権限・更新時刻だけを取る形にしても拒否された）。
SPEC「環境の事実」の「認証情報への接触を実行基盤が拒むことがある」に該当する。

積極的に言えることは次に限る。**本契約が `~/.ssh/` に対して行った書き込みは
`cat scripts/sync/hub_keys/$n.pub >> ~/.ssh/authorized_keys` の 4 回だけ**であり、
他のパスを対象とする書き込み・削除・権限変更の命令は一度も実行していない。
**ただしそれは「実行していない」の記録であって「無変更を測った」ではない。**
申し送り 2 と 6 に従い `UNKNOWN` と書く。

---

## 6. 秘匿の検査（自分で行った）

**判定したのは件数ではなく形である。** 2 つの型を一件ずつ照合した。

| 型 | 形 | 扱い |
|---|---|---|
| `private_key_block` | `-----BEGIN [A-Z ]*PRIVATE KEY-----` | 削る |
| `assignment_secretish` | `api_key`/`secret`/`token`/`password`/`NOTION_API_KEY`/`WANDB_API_KEY` に区切りと値が続く形 | 削る |

説明文・変数名・指紋・公開鍵は差し支えないものとして通した。

| 送出対象 | 該当件数 |
|---|---|
| `RESULT.md` | `0` |
| `SPEC.md` | `0` |
| `audit.md` | `0` |
| `spec.yaml` | `0` |
| **合計** | **`0`** |

**陽性対照**: 秘密鍵の書き出しと `NOTION_API_KEY=...` を含む囮に同じ検査をかけた。

    decoy hits=2  private_key_block@line1(len=35); assignment_secretish@line4(len=38)

**一以上を返した。検査は働いている。** 囮は版管理外に置き、commit していない。

🔴 **検査そのものが値を出力していない**（申し送り 5）。
出力は**型・行番号・長さ**だけであり、一致した文字列そのものは出していない。
前契約が指摘された「鍵の先頭十二文字を出す書き方」はしていない。

**環境の資格情報そのものとの直接照合は `UNKNOWN`。**
`NOTION_API_KEY` `WANDB_API_KEY` `NOTION_DB_ID` `GITHUB_TOKEN` `GH_TOKEN` のいずれも
このシェルの env に無く（`env_present=no`）、照合できなかった。
**`make task-report` が読み込み済みの env で自前の検査を行う。**

---

## 7. 検証・生成物・送出

### 検証

| 命令 | 終了コード | 結果 |
|---|---|---|
| `make task-validate` | `0` | `OK T-2026-08-24-philip-accept-node-keys`（1 task, 0 failed） |
| `make task-preflight` | `0` | 4 PASS / 1 WARN / 4 SKIP / 0 FAIL |
| `make forbidden-check` | `0` | `status: pass`、`violations: []`、`errors: []`、`changed: 8`、`checked: 8` |

`conventions_rev` は実測 `d422b08` で spec.yaml と一致したため置換していない。

`P9 spec_lint` の WARN 2 件（**終了コードを変えない**）:

| 規則 | 位置 | 判断 |
|---|---|---|
| `host_mismatch` | `SPEC.md:5` | **偽陽性。** OS ホスト名 `aolab` と論理名 `philip` の差（§2） |
| `separated_source` | `SPEC.md:39` | 記録のみ。`make task-start` を含む手順の記述にかかっている |

`P2` `P3` `P4` `P5` の 4 件は **SKIP**（合格ではなく「実行されなかった」）。
`P2`/`P3` は `plan.env.preflight` に記載が無いため、`P4`/`P5` は `kind: impl` のため対象外。

### 生成物（禁止 7）

**再生成していない。検査の結果を記録するだけにした。**

| 命令 | 終了コード | 記録 |
|---|---|---|
| `make taskindex-check` | `2` | 差分あり: `tasks_summary.csv`, `followups.md`, `results_recent.md` |
| `make inbox-check` | `2` | 差分あり: `inbox.md` |

**差分には他契約に由来する内容が含まれる。** `andrew-node-foundation` の申し送りや
`philip-syncthing-hub` の受け皿の行など、本契約が書いていないものが差分に現れる。
**投影は本契約の前から古かった。** 再生成すれば無関係な内容まで本 PR が抱え込む。

**逸脱の記録**: 一度 `make taskindex` と `make inbox` を実行してしまった。
禁止 7 に反するため、生成された 4 ファイル（`context/auto/` 3 件と `tasks/inbox.md`）を
`git checkout --` で HEAD へ戻した。戻した後の `git status` に当該 4 件は現れない。
**版管理へ入れていない。**

**したがって本契約の報告は投影（`context/auto/`）に現れない。** これは意図した結果である。

### 変更範囲

| パス | 状態 | 扱い |
|---|---|---|
| `tasks/T-2026-08-24-philip-accept-node-keys/` | 未追跡 | **本契約。commit する** |
| `tasks/inbox.d/T-2026-08-24-philip-accept-node-keys.md` | 未追跡 | **本契約。commit する** |
| `.sync-pause.released` | 未追跡 | **前契約の残り。触らない**（禁止 8） |
| `docs/sessions/digest/2026-08-22-d0076c74-….md` | 未追跡 | **前契約の残り。触らない**（禁止 8） |

**`~/.ssh/` は版管理の外なので `git status` に現れない。** 現れていない。
**`.sync-pause` は `.gitignore` 済みで現れない。** 現れていない。

`forbidden-check` は生成物（`context/auto/` と `tasks/inbox.md`）を除外してから検査し、
`violations: []` を返した。**禁止領域に触れていない。**

### 送出

| 項目 | 値 |
|---|---|
| commit | `e667b4a feat(sync): accept four node public keys on the hub`（6 files） |
| push | `origin/feat/philip-accept-node-keys` へ**新規分岐**として送出 |
| PR | **[#142](https://github.com/takuya3h/m2/pull/142)**（`feat/philip-accept-node-keys` → `phase0`） |
| 既存 PR | **無かった。** `gh pr list --state all` が `[]` を返したため新規作成した |
| base との関係 | 送出前に `origin/phase0...HEAD` が `0 0`（ahead も behind も無い） |

---

## 8. 逸脱

**「なし」ではない。** 次の 5 件である。

### 逸脱 1 — 版管理側の控えを取れなかった（G1 が満たせず、停止して判断を仰いだ）

`cp ~/.ssh/authorized_keys tasks/…/authorized_keys.orig.bak` が実行基盤の判定器に拒否された。
判定器の意図（SSH の資格情報ファイルを版管理へ複製しない）は正当と判断し、
**別の道具を使った迂回は行わなかった。**

G1 は `on_fail: stop` であるため**実行を止め、利用者へ提示した。**
「repo 外の控えで続行」との回答を得て続行した。
**主たる控え**（SPEC も「こちらが主」と定める）は取れており、**復旧能力は失われていない。**

### 逸脱 2 — `~/.ssh/` の他のファイルの無変更を測れなかった

上記 §5。`UNKNOWN` とした。**「たぶん無変更」とは書いていない。**

### 逸脱 3 — 処理の件数の開始時の値を測っていない

SPEC が Task 1 に開始時の計数を置いていないため、終了時にしか測っていない。
**判定 O の「件数が変わっていない」を示せない。** 起動時刻で非再起動を示した。
自分で気づいて先に測るべきだった。**実行者の落ち度でもある。**

### 逸脱 5 — 生成物を一度再生成してしまい、戻した（禁止 7 に反した）

`task` スキルの手順が `make taskindex` を求めるのに対し、**本契約の禁止 7 は再生成を禁じる。**
手順に従って `make taskindex` と `make inbox` を実行してしまった。

**契約の禁止を優先し、生成された 4 ファイルを `git checkout --` で HEAD へ戻した。**
戻した後の `git status` に当該 4 件は現れず、**版管理へ入れていない。**
以後は検査（`taskindex-check` `inbox-check`）だけを走らせ、差分は記録に留めた。

**結果として本契約の報告は投影に現れない。** 禁止 7 の意図どおりである。

### 逸脱 4 — `conventions_rev` を実測したが置換は不要だった

SPEC は「実行者が実測して置換する」と書くが、実測値 `d422b08` が spec.yaml の値と
**一致した**ため、置換していない。**手順を飛ばしたのではなく、差が無かった。**

---

## 9. 起票者の誤り

§10 の `result.yaml` に型つきで書く。要点は 3 件。

1. **自ら「実行基盤が認証情報への接触を拒むことがある」と書きながら、
   G1（`on_fail: stop`）に版管理内への控えを置いた。** 指示どおり実行すると拒否され、必ず停止する。
2. **同じ矛盾が Task 4 Step 2 にもある。** `~/.ssh/` の他のファイルの無変更を求めるが、
   その列挙自体が拒否されうることを SPEC は先に書いている。
3. **「件数が変わっていない」を求めながら、開始時の計数を手順に置いていない。**
   指示どおり実行すると比較対象が無く、変化の有無を示せない。

**なお SPEC の「権限は前回 `664`」は誤りではない。** 「`600` と断定しない」と正しく留保しており、
本機の実測が `600` だっただけである。申し送り 1 の指示どおり実測を正とした。

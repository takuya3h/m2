# audit — T-2026-08-24-philip-accept-node-keys

**実行ホスト:** 本機（OS ホスト名 `aolab`、syncthing 登録名 `philip` = 中心）
**分岐:** `feat/philip-accept-node-keys`

## 0. 前提の実測

| 項目 | 実測値 |
|---|---|
| 抑止の目印 | `.sync-pause` 存在（`2026-08-23 23:46`） |
| 稼働中 keeper の対応 | `grep -c "sync-pause" ~/bin/m2-sync.sh` = **2**（効く） |
| 分岐 | `feat/philip-accept-node-keys`（`feat/` で始まる） |
| `conventions_rev` | 実測 `d422b08`（spec.yaml の値と一致。置換不要） |

### 本機が中心 philip であることの独立確認

SPEC の「実行ホスト philip」に対し OS ホスト名は `aolab`。
`philip` と `ilya` は OS ホスト名が同じであるため、ホスト名では区別できない。

    ~/bin/syncthing --home=$HOME/.local/state/syncthing device-id
    → 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE

これは `scripts/sync/device_ids/philip.txt` と一致し、`ilya.txt`（`UODEAXZ-…`）とは不一致。
**本機は中心 philip である。**

`make task-preflight` の `P9 spec_lint` は `host_mismatch@SPEC.md:5` を WARN として出す。
これは OS ホスト名との比較による**偽陽性**である。もう一件 `separated_source@SPEC.md:39`。
いずれも終了コードを変えない（`EXIT=0`、4 PASS / 1 WARN / 4 SKIP / 0 FAIL）。

---

## Task 1 — 現状の測定と控え

### Step 1: 受け入れ一覧を読めるか

**読めた。** 不在でも実行基盤の拒否でもない。

| 項目 | 開始時の実測値 |
|---|---|
| 場所 | `/home/ubuntu/.ssh/authorized_keys` |
| 存在 | `exists=yes` |
| 読取 | `readable=yes` |
| 権限 | **`600`**（所有 `ubuntu:ubuntu`） |
| 更新時刻 | `2026-08-21 21:17:44.309101436 +0000` |
| バイト数 | `746` |
| 行数（`wc -l`） | `1` |
| 空行を除いた件数 | **`1`** |
| 要約値（sha256） | `bc2c7484ae084c8c8e62814fe3970fd684a0dff4e6044cd86ff4d076a8234ec0` |
| 末尾の改行 | `ends_with_newline=yes`（行の連結は起きない。改行の追加は不要） |

**SPEC「環境の事実」は権限の前回実測を `664` としていたが、本機の実測は `600` である。**
申し送り 1 に従い**実測を正とする**。

### Step 2: 登録されている鍵

`ssh-keygen -l -f ~/.ssh/authorized_keys` の終了コードは `0`（**解析は成功**）。

| # | ビット | 指紋 | 註釈 | 種別 |
|---|---|---|---|---|
| 1 | 4096 | `SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU` | `dakyo-mba@dmba.local` | RSA |

- **件数 = 1**（起票者は現在の件数を知らなかった）
- 解析できた件数 `1` = 空行を除いた件数 `1`（**一致**）
- 鍵の本体は出力していない。指紋と註釈のみ
- **この 1 件は利用者本人の MacBook Air である。失うと本人の経路が切れる**

### Step 3: 控え

| 置き場所 | 経路 | 結果 |
|---|---|---|
| **repo の外（主）** | `~/task-backups/T-2026-08-24-philip-accept-node-keys/authorized_keys.orig` | **取得済み。** 権限 `600`、`746` バイト、sha256 `bc2c7484…4ec0` = 原本と**一致** |
| 契約のディレクトリ | `tasks/T-2026-08-24-philip-accept-node-keys/authorized_keys.orig.bak` | **取得できなかった。実行基盤が拒否**（下記） |

秘匿の混入検査（件数のみ。値は出力していない）:

    原本   privhits = 0
    repo外 privhits = 0

**契約ディレクトリへの控えが取れなかった理由。**
`cp ~/.ssh/authorized_keys tasks/…/authorized_keys.orig.bak` が実行基盤の判定器に拒否された。
SPEC「環境の事実」の**「認証情報への接触を実行基盤が拒むことがある」に該当**する。
判定器の意図（SSH の資格情報ファイルを版管理へ複製しない）は正当であるため、
**別経路での迂回は行わなかった。** 逸脱として `RESULT.md` に記録する。

代替として、起票者が読める形の情報は本 `audit.md` に指紋と註釈で残している。
**復旧に使う控えは repo 外の主たる控え**（SPEC も「こちらが主」と定める）であり、
**復旧能力は失われていない。**

### Step 4: 戻し方（記録のみ。実行していない）

    # 1. 主たる控えから書き戻す
    cp ~/task-backups/T-2026-08-24-philip-accept-node-keys/authorized_keys.orig \
       ~/.ssh/authorized_keys

    # 2. 権限を開始時の値へ戻す（600。664 ではない）
    chmod 600 ~/.ssh/authorized_keys

    # 3. 一致を要約値で確かめる
    sha256sum ~/.ssh/authorized_keys
    # 期待: bc2c7484ae084c8c8e62814fe3970fd684a0dff4e6044cd86ff4d076a8234ec0

    # 4. 解析と件数を確かめる
    ssh-keygen -l -f ~/.ssh/authorized_keys   # 期待: 1 件、SHA256:hCrPAm1y…/ADU

| # | 完了判定 | 結果 |
|---|---|---|
| A | 受け入れ一覧を読めた（場所・行数・要約値・権限・更新時刻） | **満たす** |
| B | 登録鍵を指紋と註釈で記録（件数 1、解析成功） | **満たす** |
| C | 控えを二箇所へ取り原本と要約値が一致 | **一箇所のみ満たす**（repo 外は一致。版管理側は実行基盤が拒否） |
| D | 戻し方を記録（未実行、権限は開始時の `600`） | **満たす** |

---

## Task 2 — 追記するものの照合

### Step 1: 版管理の提出物

`scripts/sync/hub_keys/` に **四件すべて存在**（統合済み）。

| 件 | バイト数 | 行数 | 空行を除いた件数 |
|---|---|---|---|
| `andrew.pub` | 96 | 1 | 1 |
| `bengio.pub` | 96 | 1 | 1 |
| `ilya.pub` | 94 | 1 | 1 |
| `lecun.pub` | 95 | 1 | 1 |

### Step 2: 指紋を各ノードの報告と照合

| 件 | `hub_keys/*.pub` の指紋 | 註釈 | ノードの報告（出所） | 判定 |
|---|---|---|---|---|
| andrew | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `andrewtophilip` | `tasks/T-2026-08-22-andrew-node-foundation/RESULT.md:67` | **一致** |
| bengio | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `bengiotophilip` | `tasks/T-2026-08-22-bengio-node-foundation/RESULT.md:14,68`／SPEC 記載 `Ea9Reaj…6G4` | **一致** |
| ilya | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` | `tasks/T-2026-08-22-ilya-node-foundation/RESULT.md:71,92` | **一致** |
| lecun | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `lecuntophilip` | `tasks/T-2026-08-22-lecun-node-foundation/RESULT.md:113,134` | **一致** |

**読めなかった報告は無い。`UNKNOWN` は無い。四件すべて追記対象として残る。**

旧世代の提出（`T-2026-08-12-submit-hub-key-*` の `SHA256:i7+kCZH9…`・`SHA256:5auPdGk/…` 等）
とは指紋が異なる。SPEC の「鍵は保守作業の後に作り直されている」と整合する。
**照合には 2026-08-22 の `*-node-foundation` 世代を用いた。**

### Step 3: 公開鍵だけであることの三つの検査

| 件 | 先頭が `ssh-` | 秘密鍵の書き出し | 空行を除いた件数 | 判定 |
|---|---|---|---|---|
| andrew | yes | 0 | 1 | **追記する** |
| bengio | yes | 0 | 1 | **追記する** |
| ilya | yes | 0 | 1 | **追記する** |
| lecun | yes | 0 | 1 | **追記する** |

種別はいずれも `ssh-ed25519`、フィールド数 3。

**陽性対照（囮）**: 秘密鍵の書き出しを模した囮に同じ検査をかけた。

    decoy starts_ssh=no  privhits=2  lines=3

`privhits` が **2（一以上）** を返し、先頭検査も `no` を返した。**検査は働いている。**
囮は `…/scratchpad/decoy_priv.txt`（版管理外）に置き、`git ls-files` は **0 件**。
**版管理へ入れていない。**

### Step 4: 既に登録されていないか

開始時の指紋の集合（1 件）に対し、四件それぞれを完全一致で照合した。

| 件 | 一致件数 | 判定 |
|---|---|---|
| andrew | 0 | 未登録 → 追記する |
| bengio | 0 | 未登録 → 追記する |
| ilya | 0 | 未登録 → 追記する |
| lecun | 0 | 未登録 → 追記する |

**陽性対照**: 既存の指紋 `SHA256:hCrPAm1y…/ADU` を同じ照合にかけた → **一致件数 = 1**。
**照合が常に零を返す壊れ方をしていないことを示している。**

| # | 完了判定 | 結果 |
|---|---|---|
| E | 提出物が四件（バイト数と行数） | **満たす** |
| F | 指紋を各ノードの報告と照合（不一致は無し） | **満たす** |
| G | 公開鍵だけである（三検査＋陽性対照） | **満たす** |
| H | 既に登録されていない（陽性対照つき） | **満たす** |

### 追記の予定

**四件すべてを追記する。** 追記後の期待値:

| 項目 | 開始時 | 期待 |
|---|---|---|
| 空行を除いた件数 | 1 | **5** |
| 権限 | 600 | **600（不変）** |
| 消えた指紋 | — | **0 件** |
| 増えた指紋 | — | 上記四件 |

---

## G1 の判定と対話

G1 は「控えを二箇所へ取って原本と一致することを確かめた」を求める。
**版管理側の控えが実行基盤に拒否されたため、そのままでは満たさない。**
`on_fail: stop` に従い実行を止め、利用者へ提示した。

| 提示 | 回答 |
|---|---|
| 控えが一箇所しか取れない扱い | **repo 外の主たる控えで続行**（逸脱として記録する） |
| `~/.ssh/authorized_keys` への 4 行追記の実行 | **追記してよい** |

判定器の意図の迂回は行っていない。

---

## Task 3 — 追記と照合

### Step 1: 追記

原本は末尾が改行で終わっていた（`ends_with_newline=yes`）ため、
**改行の追加は不要だった。足していない。**

    for n in andrew bengio ilya lecun; do
      cat scripts/sync/hub_keys/$n.pub >> ~/.ssh/authorized_keys
    done

**追記のみ。上書きしていない。** 終了コード `0`。

### Step 2: 件数と権限

| 項目 | 開始時 | 追記後 | 期待 | 判定 |
|---|---|---|---|---|
| 空行を除いた件数 | `1` | **`5`** | 1 + 4 = 5 | **一致** |
| 行数（`wc -l`） | `1` | `5` | — | — |
| バイト数 | `746` | `1127` | 746+96+96+94+95 = **1127** | **一致** |
| 権限 | `600` | **`600`** | 不変 | **一致**（戻す必要なし） |
| sha256 | `bc2c7484…4ec0` | `35ad4ef5f372b1e31952d6cb919515bd76bf29e6a32996a77e4ff23e66b457f4` | — | — |

### Step 3: 既存が残っていることの集合差（両方向）

| 差 | 件数 | 期待 | 判定 |
|---|---|---|---|
| **消えた行**（開始時 − 追記後） | **`0`** | 空 | **既存を一件も失っていない** |
| 増えた行（追記後 − 開始時） | `4` | 4 | **一致** |

増えた指紋の内訳（Task 2 Step 2 の値と一件ずつ照合）:

| 件 | 指紋 | 増えた集合に含まれるか |
|---|---|---|
| andrew | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `1`（含む） |
| bengio | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `1`（含む） |
| ilya | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `1`（含む） |
| lecun | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `1`（含む） |

**想定外の追加 = `0` 件**（増えた集合から期待四件を差し引いた残り）。

**件数の一致だけに頼っていない。** 集合差を両方向で取っている。

### Step 4: 全行が解析できるか

`ssh-keygen -l -f ~/.ssh/authorized_keys` の終了コード `0`、解析できた件数 **`5`**。
空行を除いた件数 `5` と**一致**。書式は壊れていない。

追記後の登録一覧（指紋と註釈のみ。鍵の本体は出していない）:

| # | ビット | 指紋 | 註釈 | 種別 | 由来 |
|---|---|---|---|---|---|
| 1 | 4096 | `SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU` | `dakyo-mba@dmba.local` | RSA | **既存（保持）** |
| 2 | 256 | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `andrewtophilip` | ED25519 | 本契約で追記 |
| 3 | 256 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `bengiotophilip` | ED25519 | 本契約で追記 |
| 4 | 256 | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` | ED25519 | 本契約で追記 |
| 5 | 256 | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `lecuntophilip` | ED25519 | 本契約で追記 |

### Step 5: 控えとの差が追加だけか

`diff ~/task-backups/…/authorized_keys.orig ~/.ssh/authorized_keys`

| 項目 | 実測 | 期待 |
|---|---|---|
| 差分の操作 | **`a` のみ**（1 箇所） | 追加のみ |
| `<` の行（削除・変更） | **`0`** | 0 |
| `>` の行（追加） | **`4`** | 4 |

**削除も変更も無い。**

| # | 完了判定 | 結果 |
|---|---|---|
| I | 件数が期待どおり、権限が開始時と同じ | **満たす**（1→5、`600`→`600`） |
| J | **既存がすべて残っている**（消えた行が空） | **満たす**（消えた行 `0`） |
| K | 増えた件数と指紋が期待と一致 | **満たす**（4 件、想定外 `0`） |
| L | 全行が解析できる | **満たす**（解析 `5` = 空行除く `5`） |
| M | 控えとの差が追加だけ | **満たす**（`a` のみ、`<` が `0`） |

**G2 は満たした。**

---

## Task 4 Step 2 — 触っていないものの無変更

### 処理の稼働（`/proc/*/cmdline` を実行ファイル名で照合）

`pgrep -f` と `ps | grep` は自己一致するため使っていない。
`/proc/[0-9]*/cmdline` を `\0` で分割し、各語の basename を実行ファイル名と完全一致で照合した。
zsh のループは一時的な pid で中断したため無効となり、python で測り直した。

| 実行ファイル名 | 件数 | pid（ppid、起動時刻） |
|---|---|---|
| `keeper.sh`（常駐処理） | **1** | `72428`（ppid `1`、`2026-08-23 17:28:56`） |
| `syncthing`（同期処理） | **2** | `122452`（ppid `72428`）、`122530`（ppid `122452`）、いずれも `22:29` |
| `m2-sync.sh` | **0** | — |

**親子関係で切り分けた。** `syncthing` の 2 件は `122452`（監視役、keeper の子）と
その子 `122530`（作業役）である。SPEC の「正常時も二件」と一致する。

`m2-sync.sh` が `0` 件なのは異常ではない。**これは常駐ではなく keeper が 30 分ごとに
起動する一過性の処理**であり、測った瞬間に走っていなければ `0` になる。
稼働の証拠は下記の記録側で取る。

**照合器の両方向の対照:**

| 対照 | 実行ファイル名 | 件数 | 意味 |
|---|---|---|---|
| 陽性 | `zsh` | **`4`** | 照合器は動いている。**常に零を返す壊れ方ではない** |
| 陰性 | `nonexistent-daemon.sh` | **`0`** | 存在しないものを拾わない。偽陽性ではない |

**起動時刻による非再起動の証拠:** `keeper.sh` は `17:28:56`、`syncthing` は `22:29` に
起動しており、**いずれも本契約の最初の操作（`23:46` 以降）より前**である。
**本契約が停止も再起動もしていない。**

### 抑止が効いていることの両方向の対照（記録側）

`~/claude-sync/sync-alerts.log`:

    2026-08-23 23:29:06 [philip] auto-merge: feat/philip-syncthing-hub <- origin/phase0 (1 commits)
    2026-08-23 23:29:08 [philip] auto-push: feat/philip-syncthing-hub (1 commits)
    2026-08-23 23:59:08 [philip] 一時停止中: …/.sync-pause があるため分岐へ書き込まない（消せば再開）

| 時刻 | 抑止 | 記録 | 意味 |
|---|---|---|---|
| `23:29` | 無し（`.sync-pause` は `23:46` に設置） | `auto-merge` と `auto-push` | 抑止が無ければ書き込む |
| `23:59` | 有り | 「一時停止中」のみ | **抑止が効いて書き込まない** |

**両方向で対照が取れている。** 同時に、**keeper が 23:29 → 23:59 と巡回を続けている**ため
`m2-sync.sh` の瞬間値 `0` は停止を意味しないことも示している。
記録の主体が `[philip]` である点も、本機が中心であることと整合する。

### 設定と他ファイル

| 対象 | 実測 | 判定 |
|---|---|---|
| 同期処理の設定（版管理内 `scripts/sync/`） | `git status --porcelain` が **`0` 件** | **無変更** |
| syncthing 設定 `~/.local/state/syncthing/config.xml` | mtime `2026-08-23 22:41:33`（本契約開始 `23:46` より前）、size `14026` | **無変更** |
| `~/.ssh/` の他のファイル | **`UNKNOWN`** | 下記 |

**`~/.ssh/` の他のファイルを測れなかった。**
`ls -la ~/.ssh/` と `find ~/.ssh -maxdepth 1 …` の**いずれも実行基盤に拒否された**
（名前・権限・更新時刻だけを取る形にしても拒否された）。
SPEC「環境の事実」の「認証情報への接触を実行基盤が拒むことがある」に該当する。

積極的に言えることは次に限る。**本契約が `~/.ssh/` に対して行った書き込みは
`cat scripts/sync/hub_keys/$n.pub >> ~/.ssh/authorized_keys` の 4 回だけ**であり、
他のパスを対象とする書き込み・削除・権限変更の命令は一度も実行していない。
**ただしそれは「実行していない」の記録であって「無変更を測った」ではない。**
申し送り 2 と 6 に従い、**測っていないものは `UNKNOWN` と書く。**

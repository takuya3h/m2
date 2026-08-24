# RESULT — T-2026-08-24-bengio-syncthing-node

**status:** `pass`（**G1 / G2 / G3 すべて pass**）  **PR:** #143
**kind:** `impl`  **host:** `bengio`  **repo:** `~/slocal2/m2`
**branch:** `feat/bengio-syncthing-node-2`  **実行日:** 2026-08-24 (UTC)

**一台目のノードが中心へ繋がり、ファイルが実際に届いた。**
本再構築で最初に同期が成立した契約である。

前回の実行は Gate G1 で停止した（中心が bengio の公開鍵を受け入れなかった）。
その報告は `feat/bengio-syncthing-node` として PR #141 で取り込まれている。
その後 `T-2026-08-24-philip-accept-node-keys`（PR #142、`e667b4af`）が
中心の受け入れ一覧へ 4 台の公開鍵を入れたため、本分岐で再実行した。

生の出力は要約せず `audit.md` の「再開（2026-08-24、PR #142 マージ後）」以降に貼ってある（申し送り #8）。

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md:97-107` の**原文**（要約していない）:

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `contract.conventions_rev`

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b087
```

`spec.yaml` の `d422b08` はこの値の前置である。**一致するため置換は不要だった。**

### 中心の値（**本文の転記を信用せず版管理から読んだ**）

| 項目 | 出所 | 実測 |
|---|---|---|
| 中心の識別子 | `scripts/sync/device_ids/philip.txt` | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| 自分の識別子 | `scripts/sync/device_ids/bengio.txt` | `4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO`（設定内と一致） |
| 中心の実行ファイル | 前契約 `T-2026-08-24-philip-syncthing-hub/audit.md:308` | `e8a08fdd8b25…b96c4` 27045912 B v2.1.3 |
| 除外規則 | `.stignore` / `.stglobalignore` | ともに `61593e99292e…9a2a` |

### `handoff.md` の所在（SPEC の記載と食い違う。前回と同じ）

SPEC は前契約 `tasks/T-2026-08-24-philip-syncthing-hub/` にあると書くが実在しない。
実体は `tasks/T-2026-08-24-syncthing-config-survey/handoff.md` である。そちらを読んだ。

`inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は本契約の作業に現れない。
**参照していない。**

---

## 2. 完了判定

| # | 判定 | 実測 |
|---|---|---|
| A | 設定・実行ファイル・常駐処理・除外規則の要約値（実行権 644、目印零件） | `config.xml` `d4928c2d…` 8495 B 600 / `cert.pem` `b53eba6d…` / `key.pem` `99dfaa2c…` / `syncthing` `32ab747e…` 26730145 B **644** / `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / `.stignore` = `.stglobalignore` = `61593e99…` / `marker_count=0` |
| B | 稼働を両方向の対照つきで数えた | 同期処理 **0**、中継 **0**。肯定の対照 `zsh=5`、否定の対照 `zzz_no_such=0` |
| C | 控えを repo の外へ取り、画面の鍵の有無を確かめた | `~/.local/state/syncthing.bak.20260824-003520`。`apikey_elements=1 len=32 empty=False`（**値は出していない**）→ 版管理へ置かない |
| D | 戻し方を記録した（実行していない） | `audit.md` Task 1 Step 4（前回分をそのまま使う。加えて旧実行ファイルを `/tmp/syncthing.v1.27.10.bak` へ退避） |
| E | 自分の識別子が版管理の値と一致した | `in_config=True` |
| F | **中心への認証が通った** | 🟢 `Server accepts key … SHA256:Ea9Reaj…` / `Authenticated to 192.168.196.150 … using "publickey"` / `denied=0`。中心側 `authorized_keys:3` に `port-forwarding` 許可 |
| G | 中心と同じ版を取得し、要約値を記録した | 取得物 `f929eb8e…` 11821325 B。展開後 `e8a08fdd8b25…b96c4` |
| H | 置き換えた実行ファイルの要約値が中心と一致し、権限が `644` | `e8a08fdd8b25…b96c4` 27045912 B `644`。**中心の実測値と完全一致** |
| I | 自動更新を止めた | `autoUpgradeIntervalH: 12 -> 0`（要素名は実在を確かめてから変更） |
| J | 自分の登録名を確かめた | `Bengio` → **`bengio`** へ直した（先頭が大文字だった） |
| K | 告知と中継を無効にした | `globalAnnounceEnabled: true -> false` / `relaysEnabled: true -> false` / `localAnnounceEnabled` は `true` のまま |
| L | 中心を相手として登録した | `id=3J4TRX4-…-DZOCQQE`（版管理から）name=`philip` address=`tcp://127.0.0.1:22001`。**他の三台は登録していない** |
| M | 共有フォルダを二つ定義した（識別子が中心と同じ） | `claude-sync` = `/home/ubuntu/claude-sync`、`m2` = `/home/ubuntu/slocal2/m2`、ともに `sendreceive`、共有相手は自分と中心。中心の識別子（前契約 audit）と一致。`default` は削除 |
| N | 書式が解析でき、実体の件数と権限が期待どおり | `xml_ok` / `device_count=2` / `folder_count=2` / `600` |
| O | 目印を置いた（内容と権限） | `~/.tunnel_to_philip` 60 B `600` 2 行。`11:03:09 UTC` |
| P | **中継が立った**（`22001` が待ち受け、引数に中心の住所） | `11:10:02 UTC`（**目印から 413 秒**）。`port_22001=LISTEN`。引数に `ubuntu@192.168.196.150` |
| Q | 実行権を戻し、要約値が変わっていない | `755` ctime `12:52:02 UTC`、`e8a08fdd…` 不変。**中継の成立が 1 時間 42 分早い** |
| R | 同期処理が起動した（処理の数と親子関係、版） | `13:10:04 UTC`（実行権の復帰から 1082 秒）。**2 件**：`332564`（親 `157746` = keeper）と `332580`（親 `332564`）。**v2.1.3 で中心と同じ** |
| S | 設定の定義が保たれ、自動更新が零のまま | `config_version 37→52` へ移行（要約値は変わる）。共有フォルダ 2 件・相手 2 件・`global=false` `relays=false` `local=true` **`autoUpgradeIntervalH=0`** すべて保持。**自動更新の記録は無い** |
| T | 自分から中心へ送る試験を行った | `probe-bengio.txt` 40 B `2d693215…`。**`availability` に philip の識別子。中心が保有している** |
| U | **共有領域の中身が増えたかを記録した** | 開始 **4031 B / 1 件** → 終了 **9702 B / 4 件**。**消えたものは無い** |
| V | repo の同期の様子を記録した | `m2` は `sync-preparing`。local 3646 件 / 40.74 GB、global 3720 件 / 40.74 GB、**残り 1413 件 / 14.83 GB**、errors 0 |
| W | 目印が一件、常駐処理が無変更 | `marker_count=1`。`keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` は Task 1 と同じ |
| X | 秘匿検査を自分で行った（陽性対照つき） | §5 |
| Y | 分岐が送出され PR が存在する | **PR #143**（base `phase0`、OPEN、Draft ではない）。先頭 `96232900` が手元と `origin` で一致。**push は分類器に拒否されたため利用者が実行した**（§6） |
| Z | 報告が台帳へ返り、抑止が外れている | 台帳は `report_exit=0`（`report_sha256=688b6a78…`）。**抑止は外れた**（`repo 直下から消えた`）。§6 |

---

## 3. 何が起きたか

### 中心との接続

```
13:10:02 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001
             remote.name=philip remote.client=syncthing remote.version=v2.1.3)
```

中継の出口 `127.0.0.1:22001` を通って中心へ繋がり、**版も一致している**。
公開の探索網も公開中継も使っていない（`global=false` `relays=false`）。

### 届いたことの確かめ方（**中心で命令を実行していない**）

自ホストの `127.0.0.1:8384` の REST へ問い合わせた。合言葉は変数へ読み込み、画面へ出していない。

| 問い | 実測 |
|---|---|
| 中心は `claude-sync` を全部持っているか | `philip_completion=100.0000% needBytes=0` |
| 中心は `m2` を全部持っているか | `philip_completion=100.0000% needBytes=0 globalBytes=40743989547` |
| **自分が作った試験ファイルを中心が持っているか** | `probe availability=[3J4TRX4-…-DZOCQQE]` → **持っている** |

`availability` は「そのファイルの中身をどの相手から取れるか」を表す。
bengio が作り（`modifiedBy=4NIRI4M`）、philip が保有している。**片道ではなく往復している。**

### 記録の衝突（handoff §2.3 の懸念に対する実測の答え）

両ホストの `sync-alerts.log` は別内容だった。**結果は上書きではなく衝突ファイルである。**

```
13:10:10 INF Synced file (folder.id=claude-sync
             file.name=sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log
             file.size=4784 blocks.local=0 blocks.download=1)
```

`sync-alerts.log`（4761 B）と `sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log`（4784 B）が
並んでおり、**両方の内容が残っている。消えたものは無い。**
`handoff.md` が心配した「空の側が `sendreceive` で参加すると中身を消しうる」は、
**両側とも中身があり削除の履歴が無い今回の条件では起きなかった。**

---

## 4. 起票者の誤り

`result.yaml` の `issuer_defects` と対で書いてある。要約すると 6 件。

1. **`self_contradiction`** — 禁止 1 の但し書きは「中心で命令を実行してはならない」と定めるが、
   Task 1 Step 6 は `ssh … 'echo REACHABLE'` を指示する。**本契約では `ssh -N`（命令を伴わない）で測った。**
2. **`check_does_not_check`** — Task 1 Step 3 の `grep -o 'apikey>[^<]*' … | cut -c1-12` は
   秘匿の実値の先頭 12 文字を画面へ出す。禁止 7 と両立しない。**長さと空判定だけで足りる。**
3. **`shell_assumption`** — `P9 spec_lint` が `separated_source` を 5 件返した
   （`SPEC.md:50,473,476,479,507`）。
4. **`asserted_without_measuring`** — SPEC Task 5 Step 1 は「repo は約十九ギガ」と書くが、
   **実測は 51 GB（syncthing の global で 40.74 GB）である。**
5. **`check_does_not_check`** — Task 3 Step 5 は「使わない共有フォルダ（`default`）があれば消す」と
   **名前で**指定する。`<defaults>` 配下には `id=""` の folder ひな型があり、名前が一致しないため残る。
   ひな型は同期対象ではないので実害は無いが、**「`default` を消した」という確認だけでは
   `id=""` の要素が残っていることに気づけない。**実際に利用者がこれを共有対象と誤認して削除した。
   確認は名前ではなく**最上位の `<folder>` の列挙**で行うべきである。
6. **`asserted_without_measuring`** — SPEC Task 5 Step 2 は「開始時は八キロバイト・一件だった」と
   断定するが、これは前契約が **philip 上で**測った値である。bengio の実測は **4031 B / 1 件**
   （`du -sh` の丸めで 8.0K と表示されるだけ）。**丸めた表示を実数として引き継いでいる。**

---

## 5. 送信前の秘匿検査（自分で実施）

§6 に実測を貼る。判定は件数ではなく**形**で行った。
**画面の鍵（`apikey`）を版管理へ置いていない。** `config.xml` の控えは repo の外
（`~/.local/state/syncthing.bak.20260824-003520`）だけにある。
REST への問い合わせでも合言葉は変数へ読み込み、画面へ出していない。
本文に現れる `<KEYDIR>` `<KEY_PATH>` は伏せ字であり、鍵の値ではない。

---

## 6. 送出、抑止、台帳

### 検証（報告を書いたあと）

    make task-validate   → OK   T-2026-08-24-bengio-syncthing-node / 1 task(s), 0 failed / validate_exit=0
    make task-preflight  → 4 PASS / 1 WARN / 4 SKIP / 0 FAIL / preflight_exit=0
    make forbidden-check → {"base": "origin/phase0", "changed": 4, "checked": 4, "errors": [],
                            "excluded": 0, "generated_directories": ["context/auto/"],
                            "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
                            forbidden_exit=0

**一度目の `task-validate` は失敗した。** `status: done` と書いたが様式が許すのは
`pass` / `partial` / `stopped` の 3 語である。`pass` へ直して通した。推測で直していない
（`tasks/_schema/result.schema.json` の `enum` を読んだ）。

`P9 spec_lint` の WARN は 5 件（`separated_source@SPEC.md:50,473,476,479,507`）。
SKIP は 4 件（`P2 cuda_ext_loaded` `P3 deterministic_flags` `P4 prereg_committed` `P5 frozen_source_hash`）。
**SKIP は合格ではなく、実行されなかったことを意味する。**

### 秘匿検査（陽性対照つき）

語による走査の該当は、**すべて要素名・検査命令そのもの・`ssh` が返した認証方式の一覧**であり、
値ではない。加えて**合言葉の実値そのもの**を本文と照合した。

    apikey_literal_in_task_files=0 []          ← 32 文字の実値はどのファイルにも無い

陽性対照（囮は `/tmp` に置き、commit していない）

    decoy_hits=3                    ← 語による走査が囮を拾う
    decoy_detects_apikey=True       ← 実値の照合が囮を拾う

**検査は働いており、そのうえで該当が無い。**

### 変更範囲

    count=5
     M docs/sessions/digest/2026-08-23-a5cc9299-5f4d-433e-99ca-ef63c4707c22.md
     M tasks/T-2026-08-24-bengio-syncthing-node/RESULT.md
     M tasks/T-2026-08-24-bengio-syncthing-node/audit.md
     M tasks/T-2026-08-24-bengio-syncthing-node/result.yaml
     M tasks/inbox.d/T-2026-08-24-bengio-syncthing-node.md

`docs/sessions/digest/…` は**本実行より前からある変更**であり、触っていない。commit していない。
`~/claude-sync/probe-bengio.txt` は版管理の外である。

### 記録

    57aeecac feat(sync): connect bengio to the syncthing hub
    4 files changed, 540 insertions(+), 177 deletions(-)

### 送出 — **利用者が実行して完了した**

`git push` は**実行基盤の分類器に拒否された**（利用者の承認を得たあとも同じ）。
**利用者が同じ命令をセッション内で直接実行して送出した。**

    remote: Create a pull request for 'feat/bengio-syncthing-node-2' on GitHub by visiting:
    remote:      https://github.com/takuya3h/m2/pull/new/feat/bengio-syncthing-node-2
    To github.com:takuya3h/m2.git
     * [new branch]        HEAD -> feat/bengio-syncthing-node-2
    branch 'feat/bengio-syncthing-node-2' set up to track 'origin/feat/bengio-syncthing-node-2'.
    Warning: 1 uncommitted change
    https://github.com/takuya3h/m2/pull/143

    $ gh pr list --head feat/bengio-syncthing-node-2 --json number,isDraft,state,baseRefName
    [{"baseRefName":"phase0","isDraft":false,"number":143,"state":"OPEN"}]

    $ git rev-parse --short HEAD ; git rev-parse --short origin/feat/bengio-syncthing-node-2
    96232900
    96232900

**PR #143（base `phase0`、Draft ではない、OPEN）。手元と `origin` の先頭が一致している。**
`gh` が警告した「1 uncommitted change」は `docs/sessions/digest/…`（本実行より前からある変更）である。

### 台帳 — 返した

    {
      "task_id": "T-2026-08-24-bengio-syncthing-node",
      "verdict": "pass",
      "n_issuer_defects": 6,
      "report_sha256": "688b6a78e4f7ef5ba5beb0267bb9cee0b37017b61f227e5a43d46355f6fed74f",
      "report_bytes": 16112,
      "replaced_blocks": 1
    }
    report_exit=0

**前回の報告は「合言葉が失われており `load_env.sh` が使えない」と記録したが、本実行では
`source scripts/load_env.sh && make task-report` が成功した。** 前回の記録は本実行には当てはまらない。

**一度目は送出より先に返した。** 送出が実行基盤に拒否されて完了しないため待たせなかった。
そのため一度目の本文には PR 番号が入っていない。**送出が済んだあと、PR 番号を含めて返し直した。**

    {
      "task_id": "T-2026-08-24-bengio-syncthing-node",
      "verdict": "pass",
      "n_issuer_defects": 6,
      "report_sha256": "83fd9e3d1bbcc80896ef9c28413e2c56f20e3814bb1b9ada19dc5a679c93f041",
      "report_bytes": 22036,
      "replaced_blocks": 1
    }
    report_exit=0

**台帳には PR #143 を含む版が載っている。**

### 抑止 — 外れた

    $ mv .sync-pause /tmp/.sync-pause.released.T-2026-08-24-bengio-syncthing-node
    repo 直下から消えた
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 24 00:34 /tmp/.sync-pause.released.T-2026-08-24-bengio-syncthing-node

外した直後の記録に**中心の行が現れた。**

    2026-08-24 13:40:02 [bengio] 一時停止中: …
    2026-08-24 13:59:10 [philip] 一時停止中: …

`[philip]` は bengio が書いた行ではない。**同期で届いた行である。**
`~/claude-sync/sync-alerts.log` が両ホストで共有されていることの、もう一つの裏づけになった。
（中心側も現在 `.sync-pause` を置いている。これは中心の別の作業によるものであり、本契約は触っていない。）

---

## 7. 次にやるべきこと

| 順序 | 内容 |
|---|---|
| **1** | 残る三台（`andrew` `ilya` `lecun`）の同種契約を起票する。**本契約の手順がそのまま使える。** ただし `lecun` は repo が `~/slocal/m2` である |
| 2 | `m2` の同期完了を次の契約で確かめる（本契約は完了を待たない。残り 1413 件 / 14.83 GB） |
| 3 | 中心側で `sync-alerts.log` の衝突ファイルをどう扱うかを決める（全台が繋がると台数分生まれる） |
| 4 | 全台の統合後に**一台で一度だけ** `make taskindex` と `make inbox` を回す（本契約は禁止 5 により再生成していない） |

### 次の契約で使える実測値

| 項目 | 値 |
|---|---|
| 版を揃える手順 | `https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz`。取得物 `f929eb8e…`、実行ファイル `e8a08fdd8b25…b96c4` 27045912 B。**中心と完全一致** |
| 中継が立つまで | 目印 `11:03:09` → 中継 `11:10:02`。**413 秒**。常駐処理の周回は毎時 `:10:02` と `:40:02` |
| 起動まで | 実行権 `755` へ `12:52:02` → 起動 `13:10:04`。**1082 秒**。次の周回で起こる |
| 届いたかの確かめ方 | 自ホストの `127.0.0.1:8384` REST。`/rest/db/file?folder=claude-sync&file=<probe>` の **`availability` に中心の識別子が現れる**。`/rest/db/completion?folder=&device=` も使える。**中心で命令を実行しない** |
| repo の同期 | global 40.74 GB / 3720 件。起動 1 分後で残り 14.83 GB / 1413 件。**完了は待っていない** |
| `.stignore` | `.git` を除外している。**同期と git の操作は衝突しない** |
| 衝突の実測 | `sync-alerts.log` は上書きされず `…sync-conflict-<日時>-<自分の識別子先頭>.log` が生まれた。**両方残る** |
| 登録名 | bengio の初期値は `Bengio`（先頭が大文字）だった。**他の三台も確かめること** |
| 設定の移行 | 起動時に `config_version 37 → 52` へ移行され、`config.xml.v37` が控えとして残る。**要約値は必ず変わる。定義の有無で確かめる** |
| つまずいた点 | `pgrep -f 'ssh.*-L 22001…'` は**自分自身の待機命令の文字列**を拾う。ポート（`/proc/net/tcp`）だけで測ること |

---

## 8. 逸脱

`result.yaml` の `deviations` と対で書いてある。要約すると 7 件。

1. **環境** — `make task-start` を実行していない。分岐 `feat/bengio-syncthing-node-2` は既に作られていた。**前回記録した「`load_env.sh` が使えない」は本実行には当てはまらない**（`make task-report` が exit 0 で成功した）。
2. **判断** — Task 1 Step 6 を `ssh … 'echo REACHABLE'` ではなく `ssh -N` で行った。禁止 1 の但し書きを守るため。
3. **判断** — `apikey` の検査で `cut -c1-12` を採らず、長さと空かどうかだけを測った。
4. **環境** — `~/.ssh/**` は実行基盤の deny 規則で読めないため、鍵の指紋の再照合ができなかった。前回の実測値（`SHA256:Ea9Reaj…`）と、今回の `ssh -v` が出した同じ指紋で代えた。
5. **判断（利用者）** — 実行権の復帰（Task 4 Step 4）と `<defaults>` の folder ひな型の削除は**利用者が行った**。前者は中継の成立より後であり順序は守られている。後者は同期対象ではない要素であり、最上位の共有フォルダは前後とも 2 件のままである。
6. **判断（利用者）** — 共有フォルダの型は `handoff.md` が `UNKNOWN` として残した未決の判断だった。実測（bengio 4031 B / 1 件、中心も 1 件、削除の履歴なし）を示したうえで**利用者が両方 `sendreceive` を選んだ**。中心側の選択と揃う。
7. **判断** — 禁止 5 に従い `make taskindex` と `make inbox` を実行していない。技能書は投影の確認を求めるが、契約の禁止が勝つ。
8. **環境** — `git push` が実行基盤の分類器に拒否された（利用者の承認後も同じ）。**利用者がセッション内で直接実行して送出し、PR #143 が作られた。** 判定 Y は充足している。

**逸脱は「無し」ではない。** 上記 8 件がすべてである。

## 9. 禁止 5 の遵守

**生成物を再生成していない。** `make taskindex` と `make inbox` は実行していない。
検査が差分を報告した場合も、事実として記録するにとどめた（§6）。

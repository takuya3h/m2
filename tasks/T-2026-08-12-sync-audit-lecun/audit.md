# audit — 設定同期の停止に関する実測（lecun）

**task_id:** `T-2026-08-12-sync-audit-lecun`  **実行ホスト:** `lecun`
**実行日:** 2026-08-12  **読み取りのみ。復旧操作は行っていない。**

出力は要約せずそのまま貼る（注意 8）。**他ホストの値は推測で埋めない。**

---

## Task 1 測定系の健全性

### Step 2 プローブの陽性対照

「全部つながらない」という結果は、経路が無いことと道具が壊れていることの
どちらでも起きる。**区別できない道具で測ると原因の見立てを検証できない。**
`192.0.2.1` は RFC 5737 の TEST-NET-1 であり、意図的に経路を持たない。

| 対照 | 期待 | 実測 |
|---|---|---|
| `A_open` | `OPEN` | `OPEN` |
| `B_closed` | `REFUSED` | `REFUSED` |
| `C_noroute` | `TIMEOUT` | `TIMEOUT` |

出力（原文）:

    A_open    127.0.0.1:44737 OPEN
    B_closed  127.0.0.1:44737 REFUSED
    C_noroute 192.0.2.1:22000 TIMEOUT

**三通りすべてが期待と一致した。以後の到達性の結論は道具の欠陥では説明できない。**

### Step 3 版管理側の経路（第二の陽性対照）

    git --no-pager ls-remote origin -h refs/heads/phase0
    a85cf78d9f8fc5895839bdf523e957f3da8a1f0e	refs/heads/phase0
    exit=0

参照が 1 行返り `exit=0`。**外向きの通信全体は落ちていない。**
したがって設定同期の不具合は、外向き通信の全面的な障害では説明できない。

### Task 1 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 1 | プローブが三通りを出し分けた | `OPEN` / `REFUSED` / `TIMEOUT`（期待と全一致） |
| 2 | 版管理側の経路が生きている | 参照 1 行、`exit=0`（`refs/heads/phase0` = `a85cf78`） |

---

## Task 2 常駐処理の実装

### Step 1 と Step 2 稼働数を二通りで数えた（食い違った）

**二つの数え方が食い違った。両方を記録する。**

| 方法 | keeper.sh | 判定 |
|---|---|---|
| `ps -eo args \| grep -c "[k]eeper.sh"` | **2** | **誤り** |
| `/proc/*/cmdline` を読み自分と祖先を除く | **1** | 正 |

角括弧法が失敗した理由。**この実行環境では測定命令の全文が別プロセスの `args` に
埋め込まれる**（`/usr/bin/zsh -c ... eval '<命令全文>'`）。角括弧法は「`grep` 自身」を
除くだけであり、コマンド全文を `args` に持つ別プロセスは除けない。
SPEC が禁じた `pgrep -f` の誤りと**同じ型が、その回避策でも起きる。**

`/proc` を読む方法の出力（原文）:

    === keeper.sh ===
      一致 2 件 / 自分と祖先を除いて 1 件（除外 1 件）
      pid=1071 ppid=1 argv=/bin/bash /home/ubuntu/bin/keeper.sh
      [除外] pid=3665465 ppid=3228844 自分または祖先

    === syncthing ===
      一致 3 件 / 自分と祖先を除いて 2 件（除外 1 件）
      pid=1079 ppid=1071 argv=/home/ubuntu/bin/syncthing serve --no-browser
      pid=1395414 ppid=1079 argv=/home/ubuntu/bin/syncthing serve --no-browser
      [除外] pid=3665465 ppid=3228844 自分または祖先

    === ssh の中継（-L / -N）===
      ssh プロセス 0 件

    全プロセス数 385

`ps -eo pid,etime,args` による経過時間:

    1071 24-22:29:41 /bin/bash /home/ubuntu/bin/keeper.sh
    1079 24-22:29:41 /home/ubuntu/bin/syncthing serve --no-browser
    1395414  6-18:48:08 /home/ubuntu/bin/syncthing serve --no-browser

`~/.keeper.lock` は存在する（`8月 12 07:14` 更新）。keeper は生きている。

**syncthing の 2 行は二重起動ではない。** `ppid` 連鎖が `1071 -> 1079 -> 1395414` であり、
監視親（24日22時間）と実働子（6日18時間）の正常な構成である。
実働子だけが約 6.8 日前に入れ替わっている。

### Step 3 中心ホストの決め方（実装からの引用）

`~/bin/keeper.sh` は 34 行。稼働中の版と正本 `scripts/sync/keeper.sh` の差は
**0 行**（`git diff --no-index` の出力が 0 行 = バイト一致）。

該当行（原文）:

    13:  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
    14:  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
    15:  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    16:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
    19:      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &

読み取れること。**中心は名前ではなく実装に埋め込まれている。**

| 項目 | 実装から読んだ値 |
|---|---|
| 中心ホスト | `philip` = `192.168.196.150` |
| 中継の条件 | `~/.tunnel_to_philip` が存在するノードのみ |
| 中継の形 | ローカル `22001` -> philip の `127.0.0.1:22000` |
| 経路 | SSH ポート `50072` |
| 理由（コメント） | コンテナ間は SSH(50072) しか通らない |

**実装自身が `pgrep -f` を使っている**（15 行）。SPEC が禁じた手法だが、
このパターン（`ssh.*-L 22001:...`）は keeper 自身の `args` に現れないため実害は薄い。
23 行の `pgrep -x syncthing` は完全一致であり安全。**事実として記録する。**

### Step 4 中継の目印（集合として列挙）

    .tunnel.log
    .tunnel_to_philip
    count=2
    home_total=69

零件ではないため別の探し方でも確認した（注意 1 の逆方向）。
`find ~/ -maxdepth 1 -name '*tunnel*'` も **2 件**、`test -f ~/.tunnel_to_philip` は `EXISTS`。

**自ホストは中継を張るべきノードである。** それでも `ssh -N` は 0 件である。

`~/.tunnel.log` は **275 行**。**時刻を持たない。** 行の種類を集合として列挙した:

    263 ssh: connect to host 192.168.196.150 port 50072: No route to host
      3 channel 1: open failed: connect failed: Connection refused
      3 bind [::1]:22001: Cannot assign requested address
      2 Timeout, server 192.168.196.150 not responding.
      1 kex_exchange_identification: read: Connection reset by peer
      1 channel 4: open failed: connect failed: Connection refused
      1 Connection reset by 192.168.196.150 port 50072
      1 Connection closed by 192.168.196.150 port 50072

先頭 3 行は `bind ... Cannot assign requested address` と `channel N: open failed`。
**これはトンネルが張れていた時期の記録である**（向こう側の口が拒否した）。
その後 `Connection reset` と `Timeout` を経て `No route to host` に至る。
**機器ごと到達不能になったのは最後の段階である。**

ファイルの最終更新は `2026-08-12 08:05:26 UTC`（keeper が直前に追記した）。

### Task 2 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 3 | 常駐処理の稼働数を二通りで数えた | 角括弧法 **2**（誤り）/ `/proc` 法 **1**（正）。食い違いの原因を特定した |
| 4 | 中心ホストの決め方を実装から読んだ | `keeper.sh` 13-19 行を引用。中心 = `philip` = `192.168.196.150`、条件 = `~/.tunnel_to_philip` の存在 |
| 5 | 中継の目印を集合として列挙した | **2 件**（`.tunnel.log` / `.tunnel_to_philip`）。`home_total=69` |

---

## Task 3 同期処理の状態と設定

### Step 1 稼働

    2 /tmp/st.txt
       1079    1071 24-22:31:50 /home/ubuntu/bin/syncthing serve --no-browser
    1395414    1079  6-18:50:17 /home/ubuntu/bin/syncthing serve --no-browser

`ssh -L` の件数は `ps` 法で **1** と出たが、**その 1 件は測定命令自身**である
（`/proc` 法では ssh プロセス **0 件**）。**同じ誤りが本 Task でも再現した。**
実際の `ssh -L` は **0 件**。

### Step 2 待ち受けの一覧

    1 /tmp/listen.txt
    手段なし

`ss` `netstat` `lsof` の**いずれも未導入**（`command -v` で 3 件すべて「無い」）。
SPEC の想定した手段が無いため、別の探し方として `/proc/net/tcp` と
`/proc/net/tcp6` を直接復号した（状態 `0A` = LISTEN）。

    /proc/net/tcp:  55 行を走査 / LISTEN 14 件
      LISTEN 0.0.0.0:22
      LISTEN 127.0.0.1:8384
      LISTEN 127.0.0.1:11056
      LISTEN 127.0.0.1:24282 24283 24284 24285 24286
      LISTEN 127.0.0.1:37071 39205 41663 41913 46033 46169
    /proc/net/tcp6: 2 行を走査 / LISTEN 2 件
      LISTEN v6:(全アドレス):22
      LISTEN v6:(全アドレス):22000

    LISTEN 合計 16 件
    ポートの集合: [22, 8384, 11056, 22000, 24282..24286, 37071, 39205, 41663, 41913, 46033, 46169]
      22000: あり
      22001: なし
      8384: あり
      50072: なし

**自ホストの syncthing は 22000 で待ち受けている。中継の入口 22001 は存在しない。**

### Step 3 中継の入口への接続

    127.0.0.1:22001 REFUSED
    127.0.0.1:22000 OPEN
    127.0.0.1:8384  OPEN

`22001` が `REFUSED`。localhost であるため機器には必ず届く。
**したがってこれは「入口が存在しない」ことを意味する**（待ち受け一覧と整合）。

### Step 4 と Step 5 設定を構造として読む

設定の場所は `/home/ubuntu/.local/state/syncthing/config.xml`（21750 バイト、`7月 4 07:19`）。
決め打ちを避けて `find ~/ -maxdepth 4 -name 'config.xml' -path '*syncthing*'` でも **1 件**。

    device_count=11
    device name=hinton id7=CK3ACOY paused=None addrs=dynamic,tcp://192.168.196.78:22000
    device name=bengio id7=E7NPG4Q paused=None addrs=dynamic,tcp://192.168.196.105:22000
    device name=philip id7=GO2U7PF paused=None addrs=tcp://192.168.196.150:22000,tcp://127.0.0.1:22001
    device name=andrew id7=KYZK57M paused=None addrs=dynamic,tcp://192.168.196.190:22000
    device name=adam id7=QGS35FJ paused=None addrs=dynamic,tcp://192.168.196.58:22000
    device name=ilya id7=QNQZIGJ paused=None addrs=dynamic,tcp://192.168.196.63:22000
    device name=dlsta id7=RMG3SUE paused=None addrs=dynamic,tcp://192.168.196.54:22000
    device name=lecun id7=UDRM53M paused=None addrs=dynamic
    device name=efros id7=23MMNBA paused=None addrs=dynamic,tcp://192.168.196.227:22000
    device name=ian id7=5GHYFIC paused=None addrs=dynamic,tcp://192.168.196.143:22000
    device name=he id7=5YNIXSO paused=None addrs=dynamic,tcp://192.168.196.106:22000
    folder_count=2
    folder id=claude-sync path=/home/ubuntu/claude-sync paused=None type=sendreceive shared=（11 台すべて）
    folder id=m2 path=/home/ubuntu/slocal2/m2 paused=None type=sendreceive shared=（11 台すべて）
    option globalAnnounceEnabled=false
    option localAnnounceEnabled=true
    option relaysEnabled=false
    option listenAddress=default

**構成上の重要点。**

- **`philip` だけが `tcp://127.0.0.1:22001` を持つ。** 他の 10 台は `192.168.196.X:22000` のみ
- **`globalAnnounceEnabled=false` かつ `relaysEnabled=false`** — 大域探索も中継も無効
- 接続経路は「設定に書かれた直結」か「局所探索（同一ブロードキャストドメイン）」のみ
- **したがって philip 経由の星型が落ちたときの代替が構成上存在しない**
- `paused` はすべて `None`（一時停止されている相手・フォルダは無い）

### Step 6 秘匿の検査

    grep -c -i -E "apikey|password|token|secret" /tmp/stcfg.txt
    0

**Expected `0` / 実測 `0`。** 識別子は先頭 7 文字のみ。API キーは読んでいない。

### Task 3 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 6 | 同期処理と中継の稼働状況を記録した | syncthing **2 プロセス**（監視親 + 実働子、`ppid` で確認）/ `ssh -L` **0 件** |
| 7 | 中継の入口への接続結果 | `127.0.0.1:22001` = **REFUSED**（入口が存在しない） |
| 8 | 共有相手と共有フォルダの件数 | device **11 台** / folder **2 件**（いずれも 11 台全部と共有、`paused` なし） |
| 9 | 記録に秘匿の値が含まれない | 検査 **0** |

---

## Task 4 到達可否（拒否と経路なしの区別）

### Step 1 対象の一覧（三つの出所）

| 出所 | 件数 | 内容 |
|---|---|---|
| `~/.ssh/config` | `ssh_count=4` | `github.com` / `bengio` .105 / `philip` .150 / `efros` .227（後 3 者は Port 50072） |
| `/etc/hosts` | `hosts_count=7` | 遠隔の対象は **0 件**。`172.17.0.22 lecun`（自ホスト）と loopback 系のみ |
| syncthing の設定 | `stcfg_count=11` | `192.168.196.X:22000` が 10 件 + `127.0.0.1:22001` |

**和集合の対象ホスト = 10 件**（すべて `192.168.196.X`）。
`~/.ssh/config` の 3 台は syncthing の集合に含まれ、新規を出さない。

    192.168.196.105 106 143 150 190 227 54 58 63 78
    target_hosts=10
    probe_targets=30

**既知の構成は 11 台。** 内訳は遠隔 10 台 + 自ホスト（`lecun`、`addrs=dynamic`）であり、
**一覧は縮んでいない。**

**自ホストの経路。** `ip` 命令が無いため `/proc/net/route` を読んだ。

    eth0 destination=00000000 gateway=010011AC  -> 既定経路は 172.17.0.1
    eth0 destination=000011AC mask=0000FFFF     -> 172.17.0.0/16 が直結

**自ホストは `172.17.0.0/16`（Docker ブリッジ）にあり、`192.168.196.0/24` への
個別経路を持たない。** 既定ゲートウェイ経由で出る。

### Step 2 と Step 3 測定と集計

ポートは実装と設定から得た値を使った（記録から決め打ちしていない）。
`22000` = syncthing の待受、`22001` = 中継の入口、`50072` = コンテナ間の SSH。

    OPEN=9
    REFUSED=18
    TIMEOUT=0
    OTHER=3
    total=30

**分類の合計 30 = 行数 30 = 対象数（10 台 x 3 ポート）30。一致した。**

`TIMEOUT=0` の確認。**`awk` による確認は引用の誤りで走っていない**
（`awk: unexpected character '\'`）。それでも `wc -l` が `0` を返すため、
**見た目には確認できたように見える空振りだった。**
有効な確認は 2 経路。`grep -c 'TIMEOUT'` = **0**、python による末尾一致 = **0**
（`TIMEOUT` を含む行は `(なし)`）。

ホストごとの結果（原文）:

    192.168.196.105  22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.106  22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.143  22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.150  22000=OSERROR:No_route_to_host 22001=OSERROR:No_route_to_host 50072=OSERROR:No_route_to_host
    192.168.196.190  22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.227  22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.54   22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.58   22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.63   22000=REFUSED 22001=REFUSED 50072=OPEN
    192.168.196.78   22000=REFUSED 22001=REFUSED 50072=OPEN

**区別の意味を記録する。**

| 分類 | 意味 | 件数 |
|---|---|---|
| `OPEN` | 相手の機器に届き、その口が開いている | 9（すべて `50072`） |
| `REFUSED` | **相手の機器までは届いている。** 口が閉じている | 18（`22000` と `22001` の 9 台分） |
| `OSERROR:No_route_to_host` | **経路が無い。** 機器まで届かない | 3（**philip の 3 ポートすべて**） |
| `TIMEOUT` | 応答が返らない | 0 |

### Step 4 版管理側との対比

| 相手 | 結果 |
|---|---|
| 外（`github.com`、版管理） | 届く（`ls-remote` が参照を返し `exit=0`） |
| 同一構内の 9 台 | **届く**（`50072` が `OPEN`、`22000`/`22001` は `REFUSED`） |
| 同一構内の philip 1 台 | **届かない**（3 ポートすべて `No route to host`） |

**非対称は「構内 vs 外」ではない。「philip vs それ以外」である。**
同一構内の他 9 台へは機器まで到達できており、構内全体の障害では説明できない。
**philip 固有の到達不能である。**

`22000` が 9 台すべてで `REFUSED` であることは、`keeper.sh` 14 行のコメント
「コンテナ間は SSH(50072) しか通らない」と整合する。**機器までは届くが
syncthing の口は転送されていない。**

### Task 4 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 10 | 対象一覧を三つの出所から集め件数を記録した | ssh **4** / hosts **7**（遠隔 0）/ syncthing **11** -> 和集合 **10 台**。既知 11 台 = 遠隔 10 + 自ホスト。縮んでいない |
| 11 | 全対象を測り合計が一致した | 30 = 30 = 30（分類の合計 / 行数 / 対象数） |
| 12 | 拒否と経路なしを区別した | `OPEN` 9 / `REFUSED` 18 / `TIMEOUT` 0 / `No_route_to_host` 3。philip のみ経路なし |

---

## Task 5 設定共有の棚卸しと停止時期

### Step 1 総件数

    test -d ~/claude-sync -> EXISTS
    通常ファイル: 2532
    symlink:      1
    ディレクトリ: 900

零件ではないため別の探し方でも確認した。`ls -R ~/claude-sync | wc -l` = **4999 行**。

### Step 2 一覧に要約値を付けた

    stat の行数      : 2531
    inventory の行数 : 2531
    読み取り失敗     : 0

`find` の 2532 件との差 1 件は `.stfolder/` の除外による（SPEC 指定の `-not -path`）。
**件数が一致している。**

### Step 3 秘匿の検査（該当 4 件。**すべて名前の語である**）

    grep -c -i -E "apikey|password|token|secret|PRIVATE KEY" inventory.tsv
    4

**Expected は `0` だが 4 件該当した。** SPEC が想定した場合（ファイル名に該当語がある）に当たる。
該当した 4 件:

    agents/skills/transformers/references/tokenizers.md
    agents/skills/modal/references/secrets.md
    codex/plugins/cache/.../analytics-app/tokens.css
    codex/plugins/cache/.../analytics-app/charting/chart-tokens.css

**内容を含まないことを構造で検査した。**

    行数 2531 / 列数の分布 {4: 2531}
    4 列でない行: 0
    第2列が整数でない: 0 / 第3列が時刻でない: 0 / 第4列が16桁hexでない: 0

    該当した 4 件は第 1 列（経路名）にのみ現れる:
      名前に含む=True 名前以外に含む=False  （4 件すべて）

第 1 列は経路名、第 2〜4 列は大きさ・時刻・16 桁の要約値のみ。
**一覧に内容は含まれない。資格情報の値も含まれない。**

### Step 4 退避と衝突の痕跡、更新時刻の分布

    .stversions ディレクトリ: 0
    衝突ファイル:             10

**`.stversions` が 0 件である。版の退避機構が働いていない。**
衝突ファイル 10 件（すべて `sync-alerts.log` の衝突）:

    sync-alerts.sync-conflict-20260803-235225-5YNIXSO.log   (he)
    sync-alerts.sync-conflict-20260803-235315-QGS35FJ.log   (adam)
    sync-alerts.sync-conflict-20260803-235316-QGS35FJ.log   (adam)
    sync-alerts.sync-conflict-20260805-045431-RMG3SUE.log   (dlsta)
    sync-alerts.sync-conflict-20260805-045432-RMG3SUE.log   (dlsta)
    sync-alerts.sync-conflict-20260805-104822-QNQZIGJ.log   (ilya)
    sync-alerts.sync-conflict-20260805-104823-QNQZIGJ.log   (ilya)
    sync-alerts.sync-conflict-20260805-104824-QNQZIGJ.log   (ilya)
    sync-alerts.sync-conflict-20260806-162223-QNQZIGJ.log   (ilya)
    sync-alerts.sync-conflict-20260806-162224-QNQZIGJ.log   (ilya)

更新時刻の分布（月ごと）:

    2026-05   952
    2026-06     1
    2026-07  1172
    2026-08   406

最も古い 3 件はいずれも `2026-05-10T09:45:28`（`agents/skills/` 配下）。
最も新しいものは `sync-alerts.log` の `2026-08-12T07:05:19`（keeper による自ホストの書き込み）。

**復旧時に他ホストの版と衝突しうるもの。** 接続喪失の時刻（後述の `2026-08-06 20:24:02`）
より後に自ホストで更新されたファイルを数えた。

| 項目 | 実測 |
|---|---|
| 一覧の総件数 | 2531 |
| 停止前に最終更新 | 2359 |
| **停止後に最終更新** | **172** |
| 停止後の合計サイズ | **2,059,010 バイト（約 2.0 MB）** |

内訳は `codex/` が **170 件**、直下が **2 件**（`sync-alerts.log` と `settings.json`）。
`codex/plugins/cache/` 配下の大半は自動生成物である。人が触る設定に当たるのは
`settings.json`（14419 バイト、`2026-08-11T05:49:59`）と
`codex/config.toml`（901 バイト、`2026-08-11T21:59:17`）。

### Step 5 停止時期の推定（**四つの情報。整合する**）

**同期処理のログの場所について。** SPEC の `find ~ -maxdepth 3 -name "syncthing*.log"` は
**0 件**を返した。しかし `~/.syncthing.log` は **31137 行で実在する**。
`-name "syncthing*.log"` は先頭の `.` に一致しないためである。
`keeper.sh` 24 行（`>>~/.syncthing.log`）を読んでいたため気付けた。
**指示どおり実行して件数だけを見ると「別の場所にログは無い」と誤読する。**

| # | 情報 | 推定 | 独立性 |
|---|---|---|---|
| A | 最新の衝突ファイルの名前に埋め込まれた時刻 | `2026-08-06 16:22:24` | 独立 |
| B | `sync-alerts.log` の他ホスト最終行（hinton） | `2026-08-06 20:20:11` | B と D は同一事象の両面 |
| C | `~/.tunnel.log` の連続失敗 263 行 x 1800 秒からの導出 | `2026-08-06 21:05:26` | 独立 |
| D | `~/.syncthing.log` の最後の同期 | `2026-08-06 20:20:23` | B と D は同一事象の両面 |

**三者（A / B・D / C）の幅は 4 時間 43 分。整合する。**
順序も意味を持つ。A（最後の衝突）<= B・D（最後に届いた行）<= C（最初のトンネル失敗）。

**接続喪失の瞬間が `~/.syncthing.log` に残っている（最も直接的な記録）。**

    2026-08-06 19:55:08 INF Synced file (folder.id=claude-sync ... file.name=sync-alerts.log ...)
    2026-08-06 19:55:48 INF Synced file (folder.id=claude-sync ... file.name=sync-alerts.log ...)
    2026-08-06 20:00:06 INF Synced file (folder.id=claude-sync ... file.name=sync-alerts.log ...)
    2026-08-06 20:20:23 INF Synced file (folder.id=claude-sync ... file.name=sync-alerts.log ...)
    2026-08-06 20:24:02 INF Lost device connection (kind=secondary device=GO2U7PF connection=127.0.0.1:55248-127.0.0.1:22001/tcp-client/TLS...)
    2026-08-06 20:24:02 INF Lost device connection (kind=secondary device=GO2U7PF connection=127.0.0.1:35008-127.0.0.1:22001/tcp-client/TLS...)
    2026-08-06 20:24:02 INF Connection closed (device=GO2U7PF connection=127.0.0.1:55248-127.0.0.1:22001/tcp-client/TLS1.3-...)
    2026-08-06 20:24:02 INF Lost device connection (kind=primary device=GO2U7PF connection=127.0.0.1:22000-127.0.0.1:22001/tcp-client/TLS1.3-...)

**以後 5 日間、記録が一行も無い。**

    2026-08-07: 0 行
    2026-08-08: 0 行
    2026-08-09: 0 行
    2026-08-10: 0 行
    2026-08-11: 0 行
    2026-08-12: 1 行  <- WRN Failed TLS handshake (address=127.0.0.1:55292 error=EOF)

**2026-08-12 の 1 行は本契約のプローブの痕跡である。** 読み取りのみの契約だが、
`127.0.0.1:22000` への TCP 接続が対象のログに 1 行を残した。**状態は変えていない。**
観測が観測対象に痕跡を残した事実として記録する。

**星型の構成が実測で裏づけられた。**

    Established secure connection の相手: {'GO2U7PF': 21}

**接続を確立した相手は 21 件すべて `GO2U7PF`（philip）である。**
ログ全体に現れる `device=` の集合は 11 種だが、他の 10 台は各 6 件前後の
設定読み込みに関する記録のみで、**一度も接続していない。**
すなわち他 10 台とは常に philip 経由でのみ同期していた。

**同期処理の再起動の履歴（経過時間の説明）。**

    2026-07-03 22:59:26 INF syncthing v2.1.1
    2026-07-08 23:19:13 ERR Automatically upgraded, restarting in 1 minute (newVersion=v2.1.2)
    2026-07-08 23:20:14 INF syncthing v2.1.2
    2026-07-18 09:44:51 INF syncthing v2.1.2
    2026-08-05 13:25:23 ERR Automatically upgraded, restarting in 1 minute (newVersion=v2.1.3)
    2026-08-05 13:26:24 INF syncthing v2.1.3

    /home/ubuntu/bin/syncthing      27045912 バイト  更新 2026-08-05 13:25:23
    /home/ubuntu/bin/syncthing.old  26933720 バイト  更新 2026-07-08 23:19:13

バイナリの更新時刻とログが一致する。**実働子の経過時間 6 日 18 時間は
2026-08-05 13:26 の自動更新による再起動で説明される**（二重起動ではない）。
keeper の経過時間 24 日 22 時間は 2026-07-18 09:44 の記録と整合する。

### Task 5 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 13 | 設定共有の件数を記録した | `EXISTS`。ファイル **2532**（symlink 1・ディレクトリ 900）、一覧は **2531**（`.stfolder` の 1 件を除外） |
| 14 | 一覧に内容が含まれない | 検査は **4** だが**すべて第 1 列の名前の語**。列の型検査で内容不含を証明（4 列固定・整数・時刻・16 桁 hex） |
| 15 | 退避と衝突の痕跡を数えた | `.stversions` **0**（版の退避が無効）／衝突ファイル **10** |
| 16 | 停止時期を二つ以上の独立した情報から推定した | **四つ**（A 16:22:24 / B 20:20:11 / C 21:05:26 / D 20:20:23、いずれも 2026-08-06）。**整合する**（幅 4 時間 43 分）。接続喪失の瞬間は **2026-08-06 20:24:02** |

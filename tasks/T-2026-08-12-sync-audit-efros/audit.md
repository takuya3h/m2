# audit — T-2026-08-12-sync-audit-efros

実行ホスト `efros` / repo `~/slocal/m2` / 測定開始 `2026-08-12T08:13:48Z`。
**読み取りのみ。復旧操作は行っていない。**

| 項目 | 実測値 |
|---|---|
| `hostname` | `efros` |
| `SERVERNAME` | `efros` |
| `uname -srm` | `Linux 5.15.0-179-generic x86_64` |
| `uptime -p` | `up 10 weeks, 5 days, 3 hours, 2 minutes` |
| 契約ブランチ | `feat/sync-audit-efros`（起点 `origin/phase0`） |
| `.sync-pause` | 設置済み（`task_start.sh` が作成）。稼働中の `~/bin/m2-sync.sh` に `sync-pause` の参照が **2 箇所** → 抑止は実効 |

---

## Task 1 測定系の健全性

### Step 2 陽性対照（プローブが三通りを出し分けるか）

命令:

    .venv/bin/python - <<'PY'
    import socket, subprocess, sys
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    port = srv.getsockname()[1]
    run = lambda t: subprocess.run([sys.executable, "tasks/T-2026-08-12-sync-audit-efros/probe.py", t],
                                   capture_output=True, text=True).stdout.strip()
    print("A_open   ", run("127.0.0.1:" + str(port)))
    srv.close()
    print("B_closed ", run("127.0.0.1:" + str(port)))
    print("C_noroute", run("192.0.2.1:22000"))
    PY

出力:

    A_open    127.0.0.1:60109 OPEN
    B_closed  127.0.0.1:60109 REFUSED
    C_noroute 192.0.2.1:22000 TIMEOUT
    exit=0

| 対照 | 期待 | 実測 | 判定 |
|---|---|---|---|
| `A_open`（listen 中の局所ポート） | `OPEN` | `OPEN` | 一致 |
| `B_closed`（同じポートを閉じた直後） | `REFUSED` | `REFUSED` | 一致 |
| `C_noroute`（RFC 5737 の到達しない網 `192.0.2.1`） | `TIMEOUT` | `TIMEOUT` | 一致 |

**三通りすべて期待と一致した。** よって以後「つながらない」と出た場合、それは
道具の欠陥ではなく相手側または経路の状態である、と言える。
とくに `REFUSED`（相手の機器までは届いている）と `TIMEOUT`（経路が無い）を
実際に別々の値として返すことを、この場で確認した。

### Step 3 版管理側の経路（第二の陽性対照）

命令:

    git --no-pager ls-remote origin -h refs/heads/phase0
    echo "exit=$?"

出力:

    a85cf78	refs/heads/phase0
    exit=0

参照が 1 行返り `exit=0`。**外向きの通信そのものは生きている。**
したがって以後に同一構内への不通が出た場合、それを「外向き通信全体の障害」で
説明することはできない。

### Task 1 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 1 | プローブが三通りを出し分けた | 期待 `OPEN`/`REFUSED`/`TIMEOUT` に対し実測 `OPEN`/`REFUSED`/`TIMEOUT`。**全一致** |
| 2 | 版管理側の経路が生きている | `refs/heads/phase0` = `a85cf78d9f8f...`、`exit=0` |

**G1（`after: A`、`on_fail: stop`）: 通過。**

---

## Task 2 常駐処理の実装

### Step 1 稼働数（数え方 1）と、その数え方が汚染された事実

`~/bin/` の中身:

    -rwxrwxr-x 1 ubuntu ubuntu     2250  7月  4 07:17 keeper.sh
    -rwxrwxr-x 1 ubuntu ubuntu     7342  8月 12 08:03 m2-sync.sh
    -rwxr-xr-x 1 ubuntu ubuntu 27045912  8月  5 13:22 syncthing
    -rwxr-xr-x 1 ubuntu ubuntu 26933720  7月  8 23:19 syncthing.old
    exit=0

**最初の測定は誤った値を返した。記録する。**
`ps -eo args | grep -c "[k]eeper.sh"` が **2** を返したが、実体は 1 行しかない。
原因は実行者が付けた表示用ラベル `echo "... keeper.sh ..."` である。この harness は
命令全体を `zsh -c '<script>'` として起動するため、**スクリプト本文が `ps -eo args`
に現れる。** `[k]` の技は grep が自分の引数に一致するのを防ぐだけで、囲みの命令行に
平文が入ることは防げない。SPEC 申し送り #3（記録を作る流れに表示用を混ぜない）が
禁じていた事象であり、**起票者の誤りではなく実行者の逸脱である。**

**記録を先に作り、別命令で読む方式で測り直した。**

    ps -eo pid,ppid,etime,args > /tmp/ps_snapshot.txt     # 命令に "keeper" の平文を含まない
    wc -l /tmp/ps_snapshot.txt                            # 748
    grep -c "keeper.sh" /tmp/ps_snapshot.txt              # 1
    grep "keeper.sh" /tmp/ps_snapshot.txt

    225212       1 39-00:57:01 /bin/bash /home/ubuntu/bin/keeper.sh

汚染機構が実在することの確認（この撮影自体はスナップショットに写っている）:

    grep -c "ps -eo pid,ppid,etime,args" /tmp/ps_snapshot.txt   # 2

| 数え方 | 結果 | 採否 |
|---|---|---|
| `ps -eo args \| grep -c "[k]eeper.sh"`（表示用ラベル付きで実行） | **2** | **棄却**。ラベルが自分の命令行に一致した |
| スナップショットを撮ってから読む | **1** | 採用 |

`keeper.sh` は pid 225212 / ppid 1 / etime **39-00:57:01**（39 日 0 時間 57 分）。
起動は約 2026-07-04 07:07 で、`~/bin/keeper.sh` の mtime `7月 4 07:17` と符合する。

### Step 2 別の探し方（同じスナップショットから）

    grep -v "grep" /tmp/ps_snapshot.txt | grep -i -E "keeper|syncthing|ssh -N"

    216757       1 39-08:52:54 /home/ubuntu/bin/syncthing serve --no-browser
    225212       1 39-00:57:01 /bin/bash /home/ubuntu/bin/keeper.sh
    883188  216757  6-18:51:19 /home/ubuntu/bin/syncthing serve --no-browser

**`ssh -N` は 0 件。トンネルは張られていない。**
syncthing の 2 行は **二重起動ではない**。pid 883188 の ppid が 216757 であり、
監視プロセスと実体の親子である。子の etime `6-18:51:19` は約 2026-08-05 の再起動を示し、
`~/bin/syncthing` の mtime `8月 5 13:22` と符合する（バイナリ更新に伴う再起動）。

    ls -la ~/.keeper.lock  →  -rw-rw-r-- 1 ubuntu ubuntu 0  8月 12 08:05
    ls -a ~/ | grep -i -E "lock|keeper"  →  1 件（.keeper.lock）

🔴 **`.keeper.lock` の mtime をループ生存の根拠にしてはならない。**
`keeper.sh:7` の `exec 9>~/.keeper.lock` は**起動のたびに truncate** するため、
`.zshrc` から呼ばれて `flock -n 9 || exit 0`（8 行目）で即 exit した二重起動でも
mtime が動く。08:05 はまさにそれである（本セッションのシェル起動）。
**ループが生きている根拠は `~/bin/m2-sync.sh` の mtime `8月 12 08:03`（自己更新）と
`~/.tunnel.log` の mtime `2026-08-12 08:03:59` の方である。**

### Step 3 中心ホストの決め方（実装からの引用）

`~/bin/keeper.sh` は **34 行**。稼働中の実体と正本 `scripts/sync/keeper.sh` の差は
**0 行**（`git diff --no-index` の出力が空）。つまり **稼働中の実体 = 正本**。

該当行の引用（`~/bin/keeper.sh:13-19`）:

    13:  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
    14:  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
    15:  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    16:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
    17:      -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
    18:      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    19:      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &

読み取れること（**推測ではなく実装の記述**）:

| 項目 | 実装が定める値 |
|---|---|
| 中心 | **philip**、`192.168.196.150` |
| 中心への経路 | SSH **50072** 番（コメント 14 行目「コンテナ間は SSH(50072) しか通らない」） |
| 転送 | 局所 **22001** → philip の `127.0.0.1:22000`（syncthing の同期ポート） |
| 中心を張る条件 | `~/.tunnel_to_philip` が**存在するノードのみ**。中身は秘密鍵のパス |
| 構成 | **星型**（各ノード → philip）。コメント 14 行目に明記 |

**中心の名前は実装に直書きされており、設定や環境変数では動かせない。**
中心を別ホストへ移すには `scripts/sync/keeper.sh` の変更が要る（本契約では行わない）。

なお実装自身が 15 行目で `pgrep -f` を使っている。SPEC 申し送りが禁じた形だが、
`keeper.sh` はスクリプトファイルとして起動されるため命令行は
`/bin/bash /home/ubuntu/bin/keeper.sh` であり、探索文字列を含まない。**この場では
誤りを生じていない。** ただし `bash -c` で起動する形へ変えると壊れる。

### Step 4 中継の目印（集合として列挙）

    ls -a ~/ | grep -i tunnel   →  count=2
    .tunnel.log
    .tunnel_to_philip
    home_total=61

    /home/ubuntu/.tunnel_to_philip size=43 mtime=2026-07-03 23:36:06 +0000
    /home/ubuntu/.tunnel.log       size=18591 mtime=2026-08-12 08:03:59 +0000

🔴 **efros は `~/.tunnel_to_philip` を持つ。** すなわち実装上、efros は philip へ
トンネルを張るべきノードである。**にもかかわらず `ssh -N` は 0 件。**
`~/.tunnel.log` が 30 分ごとに伸びていることが、試行と失敗の継続を示す。
**中身（秘密鍵のパス）は読んでいない。大きさのみ記録した。**

### Task 2 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 3 | 常駐処理の稼働数を二通りで数えた | 数え方 1 = **2**（自己汚染により棄却、原因を上に記載）/ スナップショット方式 = **1**（pid 225212, etime 39-00:57:01）。**両方を記載した** |
| 4 | 中心ホストの決め方を実装から読んだ | `~/bin/keeper.sh:13-19` を引用。中心 = **philip / 192.168.196.150**、SSH **50072**、`22001→127.0.0.1:22000`、条件 = `~/.tunnel_to_philip` の存在、構成 = **星型**。正本との差 **0 行** |
| 5 | 中継の目印を集合として列挙した | `count=2`（`.tunnel.log` / `.tunnel_to_philip`）、`home_total=61` |

---

## Task 3 同期処理の状態と設定

### Step 1 稼働（`ppid` で親子を判定）

    2 /tmp/st.txt
     216757       1 39-08:52:54 /home/ubuntu/bin/syncthing serve --no-browser
     883188  216757  6-18:51:19 /home/ubuntu/bin/syncthing serve --no-browser

    ssh .*-L の件数 = 0     （該当なし）

**二行は二重起動ではない。** 883188 の `ppid` が 216757 であり、syncthing の
監視プロセスと実体の親子である。**`ssh -L` は 0 件。中継は張られていない。**

### Step 2 待ち受け一覧 — SPEC の命令では取れず、別の探し方で取れた

SPEC の命令:

    (ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null || echo "手段なし") > /tmp/listen.txt
    wc -l /tmp/listen.txt   →  1
    cat /tmp/listen.txt     →  手段なし

`ss` も `netstat` も**このホストに存在しない**。SPEC は「零行なら手段が無かった
ということ」としているが、**これを結論にすると誤る。** 申し送り #1 に従い別の
探し方を試したところ、`/proc/net/tcp` と `/proc/net/tcp6` から **26 件**取れた。

    listen_count=26
    /proc/net/tcp    0.0.0.0:22        inode=57089
    /proc/net/tcp    127.0.0.1:8384    inode=239674196     ← syncthing GUI/API
    /proc/net/tcp    127.0.0.1:10341   inode=267595817
    /proc/net/tcp    127.0.0.1:24282..24291（10 件）
    /proc/net/tcp    127.0.0.1:35405 / 35815 / 36733 / 37019 / 40825 / 41615 / 42159 / 43431 / 43615 / 44033 / 45621
    /proc/net/tcp6   :::22000          inode=239682699     ← syncthing 同期ポート
    /proc/net/tcp6   :::22             inode=57091

    lsof: なし

🔴 **`22001` は待ち受けに存在しない。** 中継の入口が無いことが、プロセス一覧
（`ssh -L` = 0 件）とは独立に確認された。

**これは起票者の誤りとして記録する（型: `check_does_not_check`）。**
「手段なし」は「データが無い」ではなく「その 2 つの道具が無い」に過ぎない。
`/proc/net/tcp` は Linux なら必ず読める。SPEC のままなら `UNKNOWN` と書いて
終わっていたが、実際には測れた。

### Step 3 中継の入口への接続（ポートは Task 2 Step 3 の実装から取得）

    .venv/bin/python probe.py 127.0.0.1:22001 127.0.0.1:22000 127.0.0.1:8384

    127.0.0.1:22001 REFUSED
    127.0.0.1:22000 OPEN
    127.0.0.1:8384  OPEN

| 対象 | 結果 | 意味 |
|---|---|---|
| `127.0.0.1:22001`（philip への転送入口） | **REFUSED** | 機器（localhost）は生きているが**待ち受けが無い**。トンネル未確立 |
| `127.0.0.1:22000`（局所 syncthing 同期） | OPEN | 局所の同期処理は健在 |
| `127.0.0.1:8384`（局所 syncthing GUI） | OPEN | 同上 |

**局所側は壊れていない。壊れているのは philip への経路である。**

### Step 4 設定ファイルの位置（集合として探索）

    FOUND /home/ubuntu/.local/state/syncthing
      cert.pem 623 / config.xml 21749 (7月 4 07:19) / https-cert.pem 692
      https-key.pem 227 / key.pem 119 / index-v2/ / syncthing.lock 0 (8月 5 13:23)
    起動引数の home/config 指定: なし（既定位置を使用）

`key.pem` `https-key.pem` は秘密鍵である。**開いていない。** 読んだのは `config.xml` のみ。

### Step 5 設定の構造（識別子は先頭 7 文字のみ）

    device_count=11
    device name=hinton id7=CK3ACOY paused=None addrs=dynamic,tcp://192.168.196.78:22000
    device name=bengio id7=E7NPG4Q paused=None addrs=dynamic,tcp://192.168.196.105:22000
    device name=philip id7=GO2U7PF paused=None addrs=tcp://192.168.196.150:22000,tcp://127.0.0.1:22001
    device name=andrew id7=KYZK57M paused=None addrs=dynamic,tcp://192.168.196.190:22000
    device name=adam   id7=QGS35FJ paused=None addrs=dynamic,tcp://192.168.196.58:22000
    device name=ilya   id7=QNQZIGJ paused=None addrs=dynamic,tcp://192.168.196.63:22000
    device name=dlsta  id7=RMG3SUE paused=None addrs=dynamic,tcp://192.168.196.54:22000
    device name=lecun  id7=UDRM53M paused=None addrs=dynamic,tcp://192.168.196.176:22000
    device name=efros  id7=23MMNBA paused=None addrs=dynamic
    device name=ian    id7=5GHYFIC paused=None addrs=dynamic,tcp://192.168.196.143:22000
    device name=he     id7=5YNIXSO paused=None addrs=dynamic,tcp://192.168.196.106:22000
    folder_count=2
    folder id=claude-sync path=/home/ubuntu/claude-sync paused=None type=sendreceive shared=（11 台すべて）
    folder id=m2          path=/home/ubuntu/slocal/m2  paused=None type=sendreceive shared=（11 台すべて）
    option globalAnnounceEnabled=false
    option localAnnounceEnabled=true
    option relaysEnabled=false
    option listenAddress=default

読み取れること:

| 項目 | 値 | 含意 |
|---|---|---|
| 相手の数 | **11**（自分 efros を含む → 他 10 台） | SPEC の「既知の構成は 11 台」と一致 |
| philip の宛先 | `tcp://192.168.196.150:22000` **と `tcp://127.0.0.1:22001`** | **philip だけが局所トンネル入口を宛先に持つ。星型が設定側にも現れている** |
| efros 自身 | `dynamic` のみ | 自分には固定宛先を書かない（正常） |
| 共有フォルダ | **2**（`claude-sync` と `m2`）、いずれも `sendreceive`、11 台全員と共有 | `paused` はいずれも `None`（=停止指定なし） |
| `globalAnnounceEnabled` | **false** | 大域探索を使わない |
| `relaysEnabled` | **false** | **中継サーバへの退避経路が無い** |
| `localAnnounceEnabled` | true | 同一 L2 内の通知のみ |

🔴 **大域探索も中継も無効であるため、philip への経路が落ちると迂回路が無い。**
残る手段は各 `tcp://192.168.196.x:22000` への直接接続と局所通知だけであり、
それが通るかは Task 4 で測る。

### Step 6 秘匿が混ざっていないこと

    grep -c -i -E "apikey|password|token|secret" /tmp/stcfg.txt   →  0
    grep -c -i -E "BEGIN .*PRIVATE KEY|-----BEGIN" /tmp/stcfg.txt →  0

**陽性対照**（申し送り #4）。この検査が空振りでないことを確かめた:

    printf 'apikey=DUMMY\n' > /tmp/canary.txt
    grep -c -i -E "apikey|password|token|secret" /tmp/canary.txt  →  1

検査は働いており、そのうえで実際の記録には該当が無い。

### Task 3 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 6 | 同期処理と中継の稼働状況を記録した | syncthing **2 プロセス（親子、二重起動ではない）**、`ssh -L` **0 件**、待ち受け **26 件**（`/proc/net/tcp` 経由。`ss`/`netstat` は不在） |
| 7 | 中継の入口への接続結果を記録した | `127.0.0.1:22001` = **REFUSED**（待ち受けなし）。対照として `22000`/`8384` = OPEN |
| 8 | 共有相手と共有フォルダを記録した | device **11**、folder **2**（`claude-sync`, `m2`）、いずれも 11 台全員と共有 |
| 9 | 記録に秘匿の値が含まれない | 検査 **0**、陽性対照 **1**（検査は働いている） |

---

## Task 4 到達可否（拒否と経路なしを区別する）

### Step 1 対象一覧を三つの出所から集める

| 出所 | 件数 | 内容 |
|---|---|---|
| `~/.ssh/config` | `ssh_count=3` | `philip`(192.168.196.150:50072) / `github.com` / `lecun`(192.168.196.176:50072) |
| `/etc/hosts` | 7 行 | 自ホスト `172.17.0.21 efros` と loopback/IPv6 予約のみ。**他ノードの記載なし** |
| syncthing 設定の `tcp://` | 11 | 他ノード 10 個の `192.168.196.x:22000` + `127.0.0.1:22001`（philip 用の局所入口） |

**和集合（自分と外部を除いた他ノード）= 10 台。** 自分 efros を足して **11 台**であり、
SPEC の「既知の構成は 11 台」と一致する。**一覧が縮んでいる兆候は無い。**

    peer_count=10
    192.168.196.54  .58  .63  .78  .105  .106  .143  .150  .176  .190

⚠️ **出所を 1 つに絞ると一覧は縮む。** `~/.ssh/config` だけなら 2 台、`/etc/hosts` だけなら
0 台しか得られない。**全体像は syncthing の設定にしか無い。** 三つから集めよという
SPEC の要求は、実測上そのとおりに効いた。

### Step 2 各アドレスへ 2 ポート（実装と設定から得た値）

ポートの根拠: `22000` = syncthing 同期ポート（設定の `tcp://...:22000` と局所待ち受け
`:::22000`）、`50072` = `keeper.sh:16` の `-p 50072` および `~/.ssh/config` の `Port 50072`。
**記録から決め打ちしていない。**

    probe_targets=20
    192.168.196.54:22000  REFUSED     192.168.196.54:50072  OPEN
    192.168.196.58:22000  REFUSED     192.168.196.58:50072  OPEN
    192.168.196.63:22000  REFUSED     192.168.196.63:50072  OPEN
    192.168.196.78:22000  REFUSED     192.168.196.78:50072  OPEN
    192.168.196.105:22000 REFUSED     192.168.196.105:50072 OPEN
    192.168.196.106:22000 REFUSED     192.168.196.106:50072 OPEN
    192.168.196.143:22000 REFUSED     192.168.196.143:50072 OPEN
    192.168.196.150:22000 OSERROR:No_route_to_host   192.168.196.150:50072 OSERROR:No_route_to_host
    192.168.196.176:22000 REFUSED     192.168.196.176:50072 OPEN
    192.168.196.190:22000 REFUSED     192.168.196.190:50072 OPEN

### Step 3 三分類の集計（合計が対象数と一致すること）

    OPEN=9   REFUSED=9   TIMEOUT=0   OTHER=2
    total=20   sum_check=20

**`9+9+0+2 = 20 = total`。測り漏れは無い。**

| 分類 | 件数 | 意味 | 該当 |
|---|---|---|---|
| `OPEN` | 9 | 接続確立 | 他 9 台の **SSH 50072** |
| `REFUSED` | 9 | **相手の機器までは届いている**（RST が返る）が待ち受けが無い | 他 9 台の **22000** |
| `TIMEOUT` | 0 | — | なし |
| `OTHER`（`OSERROR:No_route_to_host`） | 2 | **経路が無い**（ICMP 到達不能） | **philip 192.168.196.150 の両ポート** |

🔴 **philip だけが、両ポートとも `No route to host`。他の 9 台はすべて生きている。**

この区別が結論を分ける。9 台の `22000` が `TIMEOUT` ではなく **`REFUSED`** であることは、
**そのアドレス自体は応答している**（構内が丸ごと落ちたのではない）ことを意味する。
`22000` に待ち受けが無い理由は `keeper.sh:14` が述べる「コンテナ間は SSH(50072) しか
通らない」構成と整合するが、**これは実装の記述であって本契約で測ったものではない。**
測ったのは「`192.168.196.x:22000` は RST を返す」「`:50072` は接続できる」までである。

### Step 4 版管理側との対比（非対称の有無）

    github.com:443 OPEN
    github.com:22  OPEN
    git ls-remote origin -h refs/heads/phase0  →  参照が返る / exit=0（Task 1 Step 3）

**非対称が存在する。** 外部（github, 443/22）へは届き、同一構内の他 9 台へも
SSH では届く。**届かないのは philip 1 台だけである。**
したがって「外向き通信の障害」でも「構内全体の障害」でもない。

### 見立ての確認

`escalate_if` は「中心として想定していたホストへ到達できてしまい、原因の見立てが
崩れる場合」に停止を求めている。**philip へは到達できなかった**ため見立ては崩れて
おらず、停止条件に該当しない。

### Task 4 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 10 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config`=3 / `/etc/hosts`=7 行（他ノード 0）/ syncthing 設定=11。**和集合の他ノード = 10 台**、自分を足して 11 台で既知の構成と一致 |
| 11 | 全対象を測り合計が一致した | `total=20`、`OPEN 9 + REFUSED 9 + TIMEOUT 0 + OTHER 2 = 20`。**一致** |
| 12 | 拒否と経路なしを区別した | `REFUSED` 9（他 9 台の 22000、機器は生存）/ `OSERROR:No_route_to_host` 2（**philip のみ**、経路なし）/ `TIMEOUT` 0 |

**G2（`after: B`、`on_fail: ask`）: 通過。** 件数が一致し、拒否と経路なしを区別して
全対象を記録したため、ユーザーへの判断要求は発生しない。

---

## Task 5 設定共有の棚卸しと停止時期

時刻はすべて **UTC**（`date` と `date -u` が一致、`TZ` 未設定）。

### Step 1 総件数

    ~/claude-sync   EXISTS
    files=2532   symlinks=1   dirs=900

零件ではない。第一階層は `CLAUDE.md` `agents/` `claude/` `codex/` `commands/`
`settings.json` `sync-alerts.log` と衝突ファイル群、`.stfolder/`。
**ディレクトリ自身の mtime は `2026-08-06 20:20`。**

### Step 2 一覧（名前・大きさ・更新時刻・要約値のみ）

    find ~/claude-sync -type f -not -path "*/.stfolder/*" | xargs stat -c "%n\t%s\t%Y"  →  2531 件
    total_bytes=60101493   （約 57 MiB）

生成物 `inventory.tsv`:

    行数            2531
    列数            全行 4 列（名前 / 大きさ / 更新時刻 / sha256 先頭 16 文字）
    要約値の失敗    0 件（`ERR:` 0）

**内容は 1 バイトも記録していない。** 要約値は sha256 の先頭 16 文字のみ。
他ホストの同名ファイルと突き合わせるための一覧である。

### Step 3 秘匿が混ざっていないこと — **0 ではなく 4。理由を明記する**

    grep -c -i -E "apikey|password|token|secret|PRIVATE KEY" inventory.tsv   →  4

該当 4 行はいずれも**ファイル名に一般語として含まれるもの**であり、資格情報ではない:

| ファイル名 | 語 | 実体 |
|---|---|---|
| `agents/skills/transformers/references/tokenizers.md` | token | NLP の tokenizer 解説 |
| `agents/skills/modal/references/secrets.md` | secret | Modal の secrets **機能の説明文書** |
| `codex/.../analytics-app/tokens.css` | token | CSS のデザイントークン |
| `codex/.../charting/chart-tokens.css` | token | 同上 |

**一覧が持つのは名前・大きさ・更新時刻・要約値の 4 列のみで、内容を含まない。**
よって資格情報の値が外部へ出ることはない。**陽性対照**で検査自体は働いている:

    printf 'x/secret.md\t1\t...\tdead\n' > /tmp/canary2.tsv
    grep -c -i -E "apikey|password|token|secret|PRIVATE KEY" /tmp/canary2.tsv  →  1

### Step 4 退避と衝突の痕跡、更新時刻の分布

    .stversions ディレクトリ = 0
    *.sync-conflict-* ファイル = 10

    [最古 3 件]  2026-05-10T09:45:28  agents/skills/...
    [最新 5 件]  2026-08-12T07:03:51  codex/plugins/cache/... と sync-alerts.log

衝突ファイルの日付は `20260803` × 3、`20260805` × 5、`20260806-1622` × 2 で、
**2026-08-06 16:22 が最後**。以後は衝突が発生していない（＝同期が止まっている）。

🔴 **`versioning.type` が両フォルダとも `(none)`。退避が無い。**

    folder id=claude-sync  versioning.type=(none)  maxConflicts=10
    folder id=m2           versioning.type=(none)  maxConflicts=10

`maxConflicts=10` なので、**両側が編集した**ファイルは `.sync-conflict-*` として
最大 10 世代まで残り、黙って消えることはない。**一方で `versioning` が無いため、
他ホストで削除されたファイルは復旧時にこちらでも削除され、戻す手段が無い。**

### Step 5 停止時期を二つの独立した情報から推定する

**情報源 A: `~/.tunnel.log`（時刻なし。ループ周期から逆算）**

    総行数 280
    18〜280 行目 = 263 行が連続して "No route to host"（192.168.196.150:50072）
    1〜17 行目  = 接続できていた時期の別種の記録（Connection refused / Timeout 等）
    ファイル mtime = 2026-08-12 08:03:59

ループ周期を**実測**した（`~/claude-sync/sync-alerts.log` の時刻から）:

    20:02:08 → 22:02:28  /  4 loops = 1805.0 s
    22:02:28 → 07:03:48  / 18 loops = 1804.4 s
    検算: 07:03:48 + 1805×2 = 08:03:58 ≒ tunnel.log の mtime 08:03:59（秒単位で一致）

    262 間隔 × 1805 s を 08-12 08:03:59 から逆算 →  推定 2026-08-06T20:42:09Z
    （公称 sleep 1800 で計算した場合 →  2026-08-06T21:03:59Z）

**情報源 B: `~/.syncthing.log`（時刻つき。直接の記録）**

    2026-08-06 20:23:41  Lost device connection (kind=primary   device=GO2U7PF… error="reading length: EOF" remaining=1)
    2026-08-06 20:23:41  Lost device connection (kind=secondary device=GO2U7PF… error="reading length: EOF" remaining=2)
    2026-08-06 20:23:41  Lost device connection (kind=secondary device=GO2U7PF… error="reading length: EOF" remaining=0)
    2026-08-06 20:23:41  Connection closed      (device=GO2U7PF… error="reading length: EOF")

    2026-08-06 20:23:41 以降の GO2U7PF 関連事象 = 0 件
    最後の Established secure connection = 2026-08-05 13:26:05（相手は GO2U7PF）
    Established 総数 27 / Lost 総数 27  →  収支 0 = **現在の接続数は零**

**二つは整合する。**

| 情報源 | 推定 | 性質 |
|---|---|---|
| A `~/.tunnel.log` + 実測ループ周期 | `2026-08-06T20:42:09Z` | 逆算。**真の喪失時刻より 0〜30 分遅れる**（ssh は `ServerAliveCountMax=3` で気付くのに時間がかかり、次のループまで再試行しない） |
| B `~/.syncthing.log` | `2026-08-06T20:23:41Z` | **直接の記録** |
| 傍証 `~/claude-sync/` の mtime | `2026-08-06 20:20` | 第一階層の最終変化 |

差は **18 分 28 秒**で、keeper の 1 ループ（約 30 分）未満。**符号も予測どおり
A が後**である。食い違いではなく整合と判定する。**採用値は B の
`2026-08-06T20:23:41Z`**（直接の記録であるため）。経過は測定時点で **5 日 11 時間 50 分**。

**同期処理のログの場所: `~/.syncthing.log`（8,553,294 バイト、mtime 2026-08-12 08:20:13）。**
⚠️ SPEC の `find ~ -maxdepth 3 -name "syncthing*.log"` は **0 件**を返した。
実ファイルは**先頭がドット**の `.syncthing.log` で、この模様には一致しない。
**起票者の誤りとして記録する（型: `check_does_not_check`）。**

### 補: efros が繋がっていた相手は philip ただ一つ

    Established した相手の内訳:      27 件すべて device=GO2U7PF（philip）
    接続先アドレスの内訳:            27 件すべて connection.remote=127.0.0.1:22001（トンネル経由）
    最初 2026-07-04 07:19:30 / 最後 2026-08-05 13:26:05

**efros は他の 9 台へ一度も直接接続したことがない。** 星型は設計どおりに機能して
いたのであって、philip を失うことは efros にとって同期の全損である。

### 補: 停止期間の分岐（未伝播の変更）

停止時刻 `2026-08-06T20:23:41` 以降に更新された共有ファイル:

    diverged_files=171   diverged_bytes=2044979   （約 2.0 MB）

| 区分 | 件数 | 性質 |
|---|---:|---|
| `codex/plugins/cache/**` | 110 | **再生成可能なキャッシュ** |
| `codex/skills/.system/**` | 59 | すべて mtime `2026-08-11T16:11:59` の**一括導入**。ベンダ提供物で再導入可能 |
| `sync-alerts.log` | 1 | 局所の追記ログ（各ホストで別内容。既に 10 件の衝突ファイルがある） |
| **`codex/config.toml`** | **1** | **1008 バイト、mtime `2026-08-11T20:15:28`。実体のある局所設定** |

**efros 側で失うと困る分岐は実質 `codex/config.toml` 1 件である。**
ただしこれは efros が**書いた**側の話であり、**他ホストで削除された結果が復旧時に
こちらへ及ぶ**ぶんは efros からは測れない（`versioning=none` のため戻せない）。
**他ホストの状態は UNKNOWN。**

### Task 5 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 13 | 設定共有の件数を記録した | `EXISTS`、files **2532** / symlinks 1 / dirs 900。一覧は 2531 行（`.stfolder` 除く）、計 **60,101,493 バイト** |
| 14 | 一覧に内容が含まれない | 検査 **4**（0 ではない）。全て**ファイル名の一般語**（tokenizers / secrets 説明文書 / CSS デザイントークン ×2）で資格情報ではない。一覧は名前・大きさ・更新時刻・要約値の 4 列のみ。陽性対照 **1** |
| 15 | 退避と衝突の痕跡を数えた | `.stversions` **0 件**（退避なし）、`*.sync-conflict-*` **10 件**（最後は 2026-08-06 16:22）。`versioning.type=(none)` / `maxConflicts=10` |
| 16 | 停止時期を二つの独立した情報から推定した | A（tunnel.log 逆算）**2026-08-06T20:42:09Z** / B（syncthing.log 直接）**2026-08-06T20:23:41Z**。差 18 分 28 秒＝1 ループ未満、符号も予測どおり。**整合。採用は B** |

**G3（`after: C`、`on_fail: stop`）: 通過。** 一覧に内容と資格情報は含まれない
（該当 4 件はファイル名の一般語であり、理由を上に明記した）。

---

## Task 6 検証

### 宣言された入力の解決

| spec.yaml の記載 | 解決結果 |
|---|---|
| `contract.inject_verbatim: [conventions#prohibitions]` | `context/conventions.md:98-107` の原文（下に逐語） |
| `contract.conventions_rev: "d422b08"` | 実測 `git log -1 --format=%h -- context/conventions.md` = **`d422b08`**。**一致するため置換不要** |
| `inputs.code.entrypoints[0]: scripts/sync/keeper.sh` | 稼働実体 `~/bin/keeper.sh` 34 行、正本との差 **0 行** |
| `inputs.code.entrypoints[1]: scripts/sync/m2-sync.sh` | 稼働実体 `~/bin/m2-sync.sh` **133 行**、正本との差 **0 行**。抑止判定は `:40-41` |
| `inputs.data.dataset: egosurgery_phase_v1` | **本契約のどの Task も使用しない** |
| `inputs.data.split_files: ["data/splits/ego_val.txt"]` | 実在する（6 バイト / 2 行）が、**本契約のどの Task も使用しない** |
| `inputs.denominator.ref` | spec.yaml に記載なし（該当なし） |
| `inputs.sigma_policy` | spec.yaml に記載なし。既定は `conventions#sigma` を継承するが、本契約は Δ を主張しないため**不使用** |
| `inputs.frozen_source.ref` | spec.yaml に記載なし（該当なし） |

`conventions#prohibitions` の**原文**（要約していない）:

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

契約の `prohibitions` 5 件はこの 5 行と一対一で対応する。**いずれにも抵触していない。**
split は読んでいない / `data/raw` `data/external` に書いていない / 凍結源に触れていない /
未測定は UNKNOWN と書いた / `runindex/` を手で編集していない。

### 抑止（`.sync-pause`）が実際に効いていることの陽性対照

設置前の `一時停止中` の記録は **2 件**（いずれも 2026-08-11 の別契約）。
本契約で `.sync-pause` を置いた後、次のループで記録が現れた:

    2026-08-12 08:34:00 [efros] 一時停止中: /home/ubuntu/slocal/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
    総数 2 → 3

**予測 08:34:03（= 08:03:58 + 1805 s）に対し実測 08:34:00。** ループ周期 1805 秒の
三度目の裏づけであり、同時に**抑止が空振りでないこと**を示す。
測定中に常駐処理による統合・push は発生していない。

### 試験

    python -m pytest -q  →  7 failed, 417 passed, 4 skipped （28.39 s）
    実行前後の作業ツリー: 3 件 → 3 件（差分なし。試験は何も書いていない）

**7 件が本契約に起因しないことを切り分けで確認した。**
契約群を走査する 2 件について、本契約のディレクトリを退避して再実行:

    mv tasks/T-2026-08-12-sync-audit-efros <退避先>
    python -m pytest tests/test_check_spec.py::test_self_contract_has_no_hit \
                     tests/test_preflight_task.py::test_spec_lint_passes_on_clean_contract
    →  2 failed   （本契約が無くても同じく失敗）

`test_check_spec` の指摘対象は `T-2026-08-11-issuer-defect-detector` の `host_mismatch`
であり、`Makefile:156-157` が「省略すると全契約を回すため過去の契約が該当して非ゼロに
なる（実際に誤りがあったのだから正常である）」と記す既知の状態。
残る 5 件（`test_engines` 1 / `test_research_logger` 4）は環境起因で、
`tasks/` への追加とは無関係である。**本契約が増やした失敗は 0。**

### 検証コマンド

    make task-validate TASK=T-2026-08-12-sync-audit-efros   →  OK / 1 task(s), 0 failed / validate_exit=0
    make task-preflight TASK=T-2026-08-12-sync-audit-efros  →  5 PASS / 0 WARN / 4 SKIP / 0 FAIL / preflight_exit=0

プリフライトの SKIP 4 件（**合格ではなく「実行されなかった」**）:

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし |
| `P4 prereg_committed` | `kind=analysis` のため対象外（exp のみ） |
| `P5 frozen_source_hash` | `kind=analysis` のため対象外（exp のみ） |

`P9 spec_lint` は規則 8 件を検査して該当なし（PASS）。**ただし本報告は実行者の観察に
基づく起票者の誤りを 3 件記録している。機械の網と実行者の観察は独立の層である。**

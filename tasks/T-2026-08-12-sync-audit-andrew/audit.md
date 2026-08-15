# audit — T-2026-08-12-sync-audit-andrew

実行ホスト: `Andrew`（`socket.gethostname()` の実測値。SPEC 本文の宣言は `andrew`）
repo: `/home/ubuntu/slocal2/m2`  分岐: `exp/andrew`

出力は要約せずそのまま貼る（起票者からの申し送り 8）。

---

## Task 1 測定系の健全性

### Step 2 陽性対照（プローブが三通りを出し分けるか）

命令:

    .venv/bin/python - <<'PY'
    import socket, subprocess, sys
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    port = srv.getsockname()[1]
    run = lambda t: subprocess.run([sys.executable, "tasks/T-2026-08-12-sync-audit-andrew/probe.py", t],
                                   capture_output=True, text=True).stdout.strip()
    print("A_open   ", run("127.0.0.1:" + str(port)))
    srv.close()
    print("B_closed ", run("127.0.0.1:" + str(port)))
    print("C_noroute", run("192.0.2.1:22000"))
    PY

出力:

    A_open    127.0.0.1:37769 OPEN
    B_closed  127.0.0.1:37769 REFUSED
    C_noroute 192.0.2.1:22000 TIMEOUT

| 対照 | 期待 | 実測 | 判定 |
|---|---|---|:--:|
| A_open（待ち受け中の口） | `OPEN` | `OPEN` | 一致 |
| B_closed（閉じた口） | `REFUSED` | `REFUSED` | 一致 |
| C_noroute（経路の無い先） | `TIMEOUT` | `TIMEOUT` | 一致 |

**三通りが実際に出し分けられた。以後の到達性の結論は道具の欠陥では説明できない。**

### Step 3 版管理側の経路（第二の陽性対照）

命令:

    git --no-pager ls-remote origin -h refs/heads/phase0
    echo "exit=$?"

出力:

    a85cf78d9f8fc5895839bdf523e957f3da8a1f0e	refs/heads/phase0
    exit=0

参照が 1 行返り `exit=0`。**外向きの通信そのものは生きている。**
したがって「全部つながらない」が観測されたとしても、それは外向き通信全体の障害では
説明できない。

### G1 判定

| # | 完了判定 | 実測 |
|:--:|---|---|
| 1 | プローブが三通りを出し分けた | OPEN / REFUSED / TIMEOUT の 3 種、期待と全一致 |
| 2 | 版管理側の経路が生きている | `refs/heads/phase0` = `a85cf78`、`exit=0` |

**G1 通過。**

---

## Task 2 常駐処理の実装

### Step 1 常駐処理の稼働を数える（その一）

    ls -la ~/bin/ ; echo "exit=$?"

    total 52744
    drwxrwxr-x 2 ubuntu ubuntu     4096  8月 12 07:10 .
    drwxr-x--- 1 ubuntu ubuntu     4096  8月 12 07:28 ..
    -rwxrwxr-x 1 ubuntu ubuntu     2250  7月  4 07:17 keeper.sh
    -rwxrwxr-x 1 ubuntu ubuntu     7342  8月 12 07:10 m2-sync.sh
    -rwxr-xr-x 1 ubuntu ubuntu 27045912  8月  5 13:25 syncthing
    -rwxr-xr-x 1 ubuntu ubuntu 26933720  7月  8 23:19 syncthing.old
    exit=0

    ps -eo args | grep -c "[k]eeper.sh"   → 1
    ps -eo args | grep    "[k]eeper.sh"   → /bin/bash /home/ubuntu/bin/keeper.sh

`m2-sync.sh` の更新時刻が 8月12 07:10 と当日である。keeper が毎ループ `origin/phase0` から
自己更新するため。`keeper.sh` 自体は 7月4 のまま（自己更新の対象外）。

### Step 2 別の探し方（その二）

    ps -eo pid,etime,args | grep -v grep | grep -i -E "keeper|syncthing|ssh -N"

        869 20-23:32:27 /bin/bash /home/ubuntu/bin/keeper.sh
        881 20-23:32:27 /home/ubuntu/bin/syncthing serve --no-browser
     522602  6-18:02:58 /home/ubuntu/bin/syncthing serve --no-browser

    ls -la ~/.keeper.lock
    -rw-rw-r-- 1 ubuntu ubuntu 0  8月 11 21:56 /home/ubuntu/.keeper.lock

**二通りで一致。keeper は 1 件。** `ssh -N` は 0 件（中継が張られていない）。
lock の更新時刻 8月11 21:56 は keeper が生きている証拠。

### Step 3 中心ホストの決め方（実装から読む）

    test -f ~/bin/keeper.sh && wc -l ~/bin/keeper.sh   → 34 /home/ubuntu/bin/keeper.sh

該当行（引用）:

    13:  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
    14:  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
    15:  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    16:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
    19:      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &

**中心は実装に直書きされている。** ホスト名 `philip`、宛先 `192.168.196.150`、SSH ポート
`50072`、転送は `-L 22001:127.0.0.1:22000`。中心の決め方は動的ではなく定数である。
条件は `~/.tunnel_to_philip` の存在のみ。

稼働中の実体と正本の差:

    git --no-pager diff --no-index -- scripts/sync/keeper.sh ~/bin/keeper.sh > /tmp/kd.txt 2>&1
    wc -l /tmp/kd.txt   → 0 /tmp/kd.txt

**差分 0 行。稼働中の `keeper.sh` は repo の正本と完全に一致する。**

### Step 4 中継の目印を集合として列挙

    ls -a ~/ | grep -i tunnel
    .tunnel.log
    .tunnel_to_philip
    count=2
    home_total=60

`~/.tunnel_to_philip` が存在する。**したがって本ホストは中継を張る側であり、
keeper は毎ループ接続を試みているはずである。**

### 完了判定（Task 2）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 3 | 常駐処理の稼働数を二通りで数えた | 方法1 `grep -c "[k]eeper.sh"` = 1 / 方法2 `ps -eo pid,etime,args` = keeper 1・syncthing 2・`ssh -N` 0。**一致** |
| 4 | 中心ホストの決め方を実装から読んだ | `keeper.sh:13-19` を引用。中心 = `philip` (`192.168.196.150`, SSH `50072`, `-L 22001:127.0.0.1:22000`)。定数であり動的解決ではない |
| 5 | 中継の目印を集合として列挙した | `.tunnel.log` / `.tunnel_to_philip` の 2 件（`home_total=60`） |

---

## Task 3 同期処理の状態と設定

### Step 1 稼働を数える（二重起動か親子かを ppid で確認）

    ps -eo pid,ppid,etime,args | grep "[s]yncthing" > /tmp/st.txt
    wc -l /tmp/st.txt   → 2

        881     869 20-23:32:53 /home/ubuntu/bin/syncthing serve --no-browser
     522602     881  6-18:03:24 /home/ubuntu/bin/syncthing serve --no-browser

**二重起動ではない。** 881 の親は 869（keeper）、522602 の親は 881。
すなわち 881 が監視役、522602 が実体という親子関係である。

中継（`ssh -L`）の数:

**最初の測定は偽陽性だった。** `ps -eo args | grep -c "[s]sh .*-L"` は `1` を返したが、
該当行は実行中の対話シェルの包み（`zsh -c ... grep -c "[s]sh .*-L" ...`）そのものであった。
**検索命令自身に一致する**という、申し送りが `pgrep -f` について警告したのと同型の誤りである。
測定と検索を別命令に分けて測り直した。

    # 命令1（測定）
    ps -eo pid,ppid,etime,args > /tmp/ps_snapshot.txt   → 147 行
    # 命令2（走査）
    grep -c 'ssh .*-L' /tmp/ps_snapshot.txt             → 0
    grep -E 'ssh' /tmp/ps_snapshot.txt
          1       0 21-02:31:53 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups

陽性対照（走査が空振りでないこと）:

    grep -c 'keeper.sh' /tmp/ps_snapshot.txt            → 1
        869       1 20-23:33:20 /bin/bash /home/ubuntu/bin/keeper.sh

**中継の実プロセスは 0 件。** ssh 関連は `sshd` の待受のみ。

### Step 2 待ち受けの一覧

    (ss -ltn || netstat -ltn || echo "手段なし") > /tmp/listen.txt
    wc -l /tmp/listen.txt   → 1
    cat /tmp/listen.txt     → 手段なし

**`ss` も `netstat` も存在しない。待ち受け一覧は取得できなかった（UNKNOWN）。**
零行ではなく「手段が無かった」である。代替として次項の直接接続で確認した。

### Step 3 中継の入口へ接続（ポートは Task 2 Step 3 の実装値）

    .venv/bin/python probe.py 127.0.0.1:22001 127.0.0.1:22000 127.0.0.1:8384

    127.0.0.1:22001 REFUSED
    127.0.0.1:22000 OPEN
    127.0.0.1:8384  OPEN

**22001（中継の入口）は REFUSED。** 自ホストは応答しているが誰も待ち受けていない
＝**転送が張られていない**。22000（syncthing 本体の待受）と 8384（GUI）は OPEN で、
syncthing 自体は生きている。

### Step 4 設定ファイルの場所（集合として探索）

    for d in ~/.config/syncthing ~/.local/state/syncthing ~/.syncthing; do ... done

    FOUND /home/ubuntu/.local/state/syncthing
    (config.xml 21750 bytes, 7月4 07:19 / cert.pem / key.pem / index-v2/ / syncthing.lock)

3 候補のうち該当は 1 つ。起動引数に `home`/`config` の指定は無し（既定の場所を使用）。

### Step 5 設定を構造として読む（識別子は先頭 7 文字のみ、API キーは読まない）

    wc -l /tmp/stcfg.txt   → 19

    device_count=11
    device name=hinton id7=CK3ACOY paused=None addrs=dynamic,tcp://192.168.196.78:22000
    device name=bengio id7=E7NPG4Q paused=None addrs=dynamic,tcp://192.168.196.105:22000
    device name=philip id7=GO2U7PF paused=None addrs=tcp://192.168.196.150:22000,tcp://127.0.0.1:22001
    device name=Andrew id7=KYZK57M paused=None addrs=dynamic
    device name=adam id7=QGS35FJ paused=None addrs=dynamic,tcp://192.168.196.58:22000
    device name=ilya id7=QNQZIGJ paused=None addrs=dynamic,tcp://192.168.196.63:22000
    device name=dlsta id7=RMG3SUE paused=None addrs=dynamic,tcp://192.168.196.54:22000
    device name=lecun id7=UDRM53M paused=None addrs=dynamic,tcp://192.168.196.176:22000
    device name=efros id7=23MMNBA paused=None addrs=dynamic,tcp://192.168.196.227:22000
    device name=ian id7=5GHYFIC paused=None addrs=dynamic,tcp://192.168.196.143:22000
    device name=he id7=5YNIXSO paused=None addrs=dynamic,tcp://192.168.196.106:22000
    folder_count=2
    folder id=claude-sync path=/home/ubuntu/claude-sync paused=None type=sendreceive shared=CK3ACOY,E7NPG4Q,GO2U7PF,KYZK57M,QGS35FJ,QNQZIGJ,RMG3SUE,UDRM53M,23MMNBA,5GHYFIC,5YNIXSO
    folder id=m2 path=/home/ubuntu/slocal2/m2 paused=None type=sendreceive shared=CK3ACOY,E7NPG4Q,GO2U7PF,KYZK57M,QGS35FJ,QNQZIGJ,RMG3SUE,UDRM53M,23MMNBA,5GHYFIC,5YNIXSO
    option globalAnnounceEnabled=false
    option localAnnounceEnabled=true
    option relaysEnabled=false
    option listenAddress=default

`device_count=11` は零でない。**11 台は「既知の構成 11 台」と一致する。**
`paused` は全件 `None`（属性なし＝停止指定なし）。共有フォルダは 2 つで、
いずれも 11 台全部と共有されている。

**発見（重要）**: `globalAnnounceEnabled=false` かつ `relaysEnabled=false`。
すなわち**外部の発見サーバも中継サーバも使わない設定**であり、到達手段は
`localAnnounceEnabled=true` による同一構内の告知と、各機器に書かれた静的アドレスのみ。
`philip` だけが `tcp://127.0.0.1:22001`（＝SSH 転送の入口）を持つ。

### Step 6 秘匿の検査

    grep -c -i -E "apikey|password|token|secret" /tmp/stcfg.txt   → 0   (Expected: 0)

陽性対照（この検査が空振りでないこと）:

    printf 'apikey=DUMMY\n' > /tmp/pc_secret.txt
    grep -c -i -E 'apikey|password|token|secret' /tmp/pc_secret.txt → 1

さらに、元の `config.xml` には該当語が **25 行**実在する（値は出力していない）。
**検査は働いており、抽出処理が実際に秘匿を落としていることが示された**
（「元から無いので 0」ではない）。

### 完了判定（Task 3）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 6 | 同期処理と中継の稼働状況を記録した | syncthing 2 プロセス（881 と 522602、親子。二重起動ではない）／中継 `ssh -L` **0 件**（測定と検索を分離して再測定、陽性対照 keeper=1 で空振りでないことを確認） |
| 7 | 中継の入口への接続結果を記録した | `127.0.0.1:22001` = **REFUSED**（22000 = OPEN、8384 = OPEN） |
| 8 | 共有相手と共有フォルダを記録した | device 11 件・folder 2 件（`claude-sync` / `m2`）。両方とも 11 台全部と共有 |
| 9 | 記録に秘匿の値が含まれない | `/tmp/stcfg.txt` の検査 = **0**（陽性対照 1・元ファイルには 25 行該当） |

---

## Task 4 到達可否（拒否と経路なしの区別）

### Step 1 対象一覧を三つの出所から集める

**出所1 `~/.ssh/config`**（`ssh_count=2`）

    Host philip
        HostName 192.168.196.150
        Port 50072
    Host github.com
      HostName github.com

**出所2 `/etc/hosts`**（`hosts_lines=7`）

    127.0.0.1	localhost
    ::1	localhost ip6-localhost ip6-loopback
    fe00::0	ip6-localnet
    ff00::0	ip6-mcastprefix
    ff02::1	ip6-allnodes
    ff02::2	ip6-allrouters
    172.17.0.26	Andrew

**出所3 同期処理の設定の静的アドレス**（`stcfg_addr_count=11`）

    tcp://127.0.0.1:22001
    tcp://192.168.196.54:22000
    tcp://192.168.196.58:22000
    tcp://192.168.196.63:22000
    tcp://192.168.196.78:22000
    tcp://192.168.196.105:22000
    tcp://192.168.196.106:22000
    tcp://192.168.196.143:22000
    tcp://192.168.196.150:22000
    tcp://192.168.196.176:22000
    tcp://192.168.196.227:22000

**和集合と件数**

| 区分 | 件数 | 内訳 |
|---|---:|---|
| 構内の他ホスト（`192.168.196.0/24`） | **10** | `.54 .58 .63 .78 .105 .106 .143 .150 .176 .227` |
| 自ホスト | 1 | `172.17.0.26`（`/etc/hosts` の `Andrew`） |
| 自ホスト内の中継入口 | 1 | `127.0.0.1:22001`（Task 3 Step 3 で測定済み） |
| 構外 | 1 | `github.com` |

**構内の対象は 10 台、自ホストを加えて 11 台。既知の構成 11 台と一致し、一覧は縮んでいない。**

**注意すべき事実**: 自ホストの住所は `/etc/hosts` によれば `172.17.0.26` であり、
**`192.168.196.0/24` に属さない**。同期処理の設定でも `Andrew` の住所は `dynamic` のみで
静的アドレスを持たない。すなわち `192.168.196.x` の 10 個は**各機の外側の住所**であり、
本ホストはその網の内側には居ない。

### Step 2 各アドレスへ二つのポートを測る

ポートは実装と設定から得た値を使った。`22000` は同期処理の待受（設定の静的アドレス）、
`50072` は中継用 SSH（`keeper.sh:16` と `~/.ssh/config`）。

    targets=20
    wc -l /tmp/reach.txt   → 20

    192.168.196.54:22000 REFUSED
    192.168.196.54:50072 OPEN
    192.168.196.58:22000 REFUSED
    192.168.196.58:50072 OPEN
    192.168.196.63:22000 REFUSED
    192.168.196.63:50072 OPEN
    192.168.196.78:22000 REFUSED
    192.168.196.78:50072 OPEN
    192.168.196.105:22000 REFUSED
    192.168.196.105:50072 OPEN
    192.168.196.106:22000 REFUSED
    192.168.196.106:50072 OPEN
    192.168.196.143:22000 REFUSED
    192.168.196.143:50072 OPEN
    192.168.196.150:22000 OSERROR:No_route_to_host
    192.168.196.150:50072 OSERROR:No_route_to_host
    192.168.196.176:22000 REFUSED
    192.168.196.176:50072 OPEN
    192.168.196.227:22000 REFUSED
    192.168.196.227:50072 OPEN

### Step 3 三分類の集計と照合

    OPEN=9
    REFUSED=9
    TIMEOUT=0
    OTHER=2
    total=20
    OPEN+REFUSED+TIMEOUT+OTHER = 20 / total = 20 → 一致

**測り漏れなし。**

`TIMEOUT=0` の再確認（零を別の探し方でも確かめる）:

    grep -c 'TIMEOUT' /tmp/reach.txt   → 0   （行末指定を外しても零）

道具が `TIMEOUT` を出せること自体は Task 1 の陽性対照 `C_noroute`
（`192.0.2.1:22000 → TIMEOUT`）で実証済みである。**したがって零は道具の欠陥ではない。**

### 結果の読み方（拒否と経路なしの区別）

| 分類 | 件数 | 意味 | 該当 |
|---|---:|---|---|
| `OPEN` | 9 | 相手まで届き、待ち受けている | 9 台の `:50072` |
| `REFUSED` | 9 | **相手の機器までは届いている**が、その口は開いていない | 同じ 9 台の `:22000` |
| `TIMEOUT` | 0 | 経路が無く応答も無い | なし |
| `OSERROR:No_route_to_host` | 2 | **経路が無い**（網側が明示的に到達不能を返した） | `192.168.196.150`（philip）の両ポート |

**核心。** 中心と想定された `philip` だけが `No route to host` であり、
**他の 9 台へは SSH の口（50072）が開いている＝機器は生きていて届く。**
一方その 9 台の `22000` はすべて `REFUSED` で、**同期処理の待受は外側の住所には出ていない。**
これは `keeper.sh:14` の記述「コンテナ間はSSH(50072)しか通らない」と整合する。

**中心へは到達できなかった。** したがって「中心が停止している」という見立ては
本ホストからの実測と矛盾しない（想定が崩れる事象＝到達できてしまう、には該当しない）。

### Step 4 版管理側との対比（非対称の有無）

| 経路 | 結果 |
|---|---|
| 構外 `github.com`（版管理） | 到達（`ls-remote` が `refs/heads/phase0` を返し `exit=0`） |
| 構内 9 台の `:50072` | 到達（`OPEN`） |
| 構内 9 台の `:22000` | 届くが閉（`REFUSED`） |
| 構内 `philip` 両ポート | **経路なし**（`No route to host`） |

**非対称がある。** 外向きの通信は生きており、構内の 9 台へも届く。
**届かないのは `philip` ただ一台である。** よって「外向き通信全体の障害」でも
「構内全体の遮断」でもなく、**単一ホストの不達**として切り分けられる。

### 完了判定（Task 4）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 10 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config` 2 件 / `/etc/hosts` 7 行 / 同期設定 11 アドレス → 構内 10 台 + 自ホスト = **11 台**（既知の構成と一致、縮んでいない） |
| 11 | 全対象を測り合計が一致した | 20 対象を測定、`9+9+0+2=20=total` で**一致** |
| 12 | 拒否と経路なしを区別した | `REFUSED` 9（届くが閉）/ `No route to host` 2（経路なし、philip のみ）/ `TIMEOUT` 0（別の探し方でも零、道具は出力可能） |

---

## Task 5 設定共有の棚卸しと停止時期の推定

### Step 1 総件数

    test -d ~/claude-sync   → EXISTS
    files    = 2497
    symlinks = 1
    dirs     = 896

零件ではない。

### Step 2 一覧（名前・大きさ・更新時刻・要約値のみ）

    find ~/claude-sync -type f -not -path "*/.stfolder/*" -print0 | xargs -0 -r stat -c "%n\t%s\t%Y" > /tmp/inv.tsv
    wc -l /tmp/inv.tsv   → 2496

    wc -l inventory.tsv  → 2496

生成前に、名前にタブを含む行が無いことを確認した（`awk -F'\t' 'NF!=3'` の件数 = 0）。
含む場合は SPEC の 3 分割が壊れるため。**ハッシュ失敗（`ERR:`）は 0 件。**

### Step 3 秘匿の検査

    grep -c -i -E "apikey|password|token|secret|PRIVATE KEY" inventory.tsv   → 4   (Expected: 0)

該当 4 行（**いずれもファイル名に語が含まれるだけで、値ではない**）:

    agents/skills/transformers/references/tokenizers.md	9904	2026-05-10T09:45:32	cb33dfe12db114af
    agents/skills/modal/references/secrets.md	2874	2026-05-10T09:45:30	fa0718268752bf6d
    codex/plugins/.../analytics-app/tokens.css	11016	2026-07-13T07:18:59	5453eb6085330604
    codex/plugins/.../charting/chart-tokens.css	14311	2026-07-13T07:18:59	bc1915546e693c0c

SPEC Step 3 の但し書きに従い**行を残す**。**一覧が内容を含まないことの確認:**

    awk -F'\t' '{print NF}' inventory.tsv | sort -u   → 4   （列数の種類は 1 つだけ）

すなわち一覧は 4 列（名前・大きさ・更新時刻・要約値の先頭 16 文字）のみからなり、
**ファイルの中身は一切含まない。** 陽性対照（`x/token.md` を含む行を検査 → 1）により
検査が働いていることも確認した。

### Step 4 退避と衝突の痕跡

    stversions_dirs = 0
    conflict_files  = 10

衝突ファイル 10 件（**すべて `sync-alerts.*.log`**）:

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

**`.stversions` が 0 件であることの意味**: 版の退避が働いていない。したがって復旧時に
上書きが起きた場合、**上書きされた側は同期処理からは復元できない。**

### 更新時刻の分布（日別・2026-07-20 以降）

        292 2026-07-22
         84 2026-07-31
        106 2026-08-01
        119 2026-08-03
         62 2026-08-05
         12 2026-08-06
          1 2026-08-12

全体の期間: 最古 `2026-05-10T09:45:28` / 最新 `2026-08-12T07:11:02` / 総件数 2496。

**2026-08-06 を最後に、2026-08-12 の 1 件（後述）を除いて更新が途絶えている。**

### Step 5 停止時期を二つの独立した情報から推定する

#### 情報 A: 更新時刻の分布（Step 4）

自ホストが書くファイルを除いた最新は **`2026-08-06T17:05:14`**
（`codex/plugins/cache/openai-curated-remote/*/.codex-remote-plugin-install.json` の 12 件）。

#### 情報 B: 同期処理自身の記録 `~/.syncthing.log`（39955 行、`2026-07-03 22:59:51` 以降）

    grep -c 'Established secure connection'   → 21
    接続相手の内訳                            → 21 件すべて device=GO2U7PF（philip）

**21 件すべてが philip 宛であり、他の 9 台へ直接つながった記録は 1 件も無い。**
星型の構成は設定上だけでなく**実際の接続履歴でもそうなっている。**

    最初の接続確立: 2026-07-04 07:19:30
    最後の接続確立: 2026-08-05 13:26:36  (device=GO2U7PF, remote=127.0.0.1:22001 ＝中継経由)
    2026-08-05 13:26:36 より後の Established: 0 件

接続が切れた瞬間の記録:

    2026-08-06 20:24:02 INF Lost device connection (kind=secondary device=GO2U7PF connection=127.0.0.1:53284-127.0.0.1:22001/tcp-client/...)
    2026-08-06 20:24:02 INF Lost device connection (kind=secondary device=GO2U7PF connection=127.0.0.1:53268-127.0.0.1:22001/tcp-client/...)
    2026-08-06 20:24:02 INF Lost device connection (kind=primary   device=GO2U7PF connection=127.0.0.1:22000-127.0.0.1:22001/tcp-client/...)
    2026-08-06 20:24:02 INF Connection closed (device=GO2U7PF connection=127.0.0.1:22000-127.0.0.1:22001/tcp-client/...)

#### 二つの情報は整合する

| 情報 | 値 | 測っているもの |
|---|---|---|
| A 更新時刻の分布 | `2026-08-06T17:05:14` | 内容が最後に変わった時刻 |
| B 同期処理の記録 | `2026-08-06 20:24:02` | 接続が最後に失われた時刻 |

**食い違いではなく整合である。** 内容の最終更新（17:05）が接続喪失（20:24）の
約 3.3 時間前にあり、その後の 3.3 時間は単に更新が無かったと読める。順序が逆
（接続喪失より後に内容が変わる）であれば矛盾するが、そうなっていない。
**停止は 2026-08-06 20:24:02（UTC）とみて矛盾が無い。**

#### 情報 C（第三の裏取り）: 中継の記録 `~/.tunnel.log`

    total = 270 行 / 'No route to host' = 263 行
    先頭 9 行が移行期（channel open failed → Timeout → No route が混在）
    10 行目以降は 261 行すべてが 'No route to host' の連続

keeper は 30 分周期で 1 回試行する（`keeper.sh` の `sleep 1800`）。

    2026-08-06 20:24:02 → 2026-08-12 07:11:00 = 130.8 時間 = 261.6 個の 30 分周期
    実測の連続失敗行数                          = 261 行

**261 行と 261.6 周期がほぼ一致する。** 情報 B の推定を独立に裏付ける。
なお `~/.tunnel.log` には時刻が無いため、これは周期からの導出であって直接の測定ではない。

#### 記録の所在

| ファイル | 行数 | 内容 |
|---|---:|---|
| `~/claude-sync/sync-alerts.log` | 868 | **git 層の記録**（`auto-merge` / `auto-push`）。同期処理の状態ではない |
| `~/.syncthing.log` | 39955 | 同期処理本体の記録。時刻あり。**停止時期の主たる根拠** |
| `~/.tunnel.log` | 270 | SSH 中継の記録。時刻なし |

**`sync-alerts.log` は同期処理の記録ではない**（`m2-sync.sh:11` の `LOG=~/claude-sync/sync-alerts.log`）。
その末尾は `2026-08-12 07:11:02 [andrew] auto-push: exp/andrew (7 commits)` であり、
**git 層は本日も動いている。** 同期処理の停止と git 層の健全性は独立である。

### 復旧時に失われうるもの

接続喪失（`2026-08-06T20:24:02`）以降に自ホストで変わったファイル:

    awk -F'\t' -v cut='2026-08-06T20:24:02' '$3 > cut' inventory.tsv
    件数 = 1
    sync-alerts.log	59006	2026-08-12T07:11:02	d5d6bd0ae893e4c5

最終内容更新（`2026-08-06T17:05:14`）以降でも同じく **1 件**。
陽性対照（閾値 `2000-01-01` で 2496 件＝総件数と一致）により、この `1` が
走査の失敗による見かけの値でないことを確認した。

> **測定の誤りとその是正**: 最初にこの件数を測った命令は zsh のクォートが壊れて awk が
> 起動せず、`件数=0` という**偽の零**を返した。申し送り 1・6 に従い、別の書き方で
> 測り直し、陽性対照を付けて確認した。**偽の零をそのまま採用していない。**

**したがって自ホストの分岐は 1 ファイル（`sync-alerts.log`）のみ。** これは
`m2-sync.sh` が 30 分ごとに追記する自ホスト由来の記録であり、他ホストにも同名で
存在する。既存の衝突ファイル 10 件がすべて `sync-alerts.*.log` であることから、
**復旧時にはこのファイルが再び衝突する見込みが高い。**
`.stversions` が無いため、衝突以外の形で上書きされた場合は復元できない。

### 完了判定（Task 5）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 13 | 設定共有の件数を記録した | `EXISTS`／ファイル 2497・symlink 1・ディレクトリ 896。一覧 2496 行（`.stfolder` 除く）。**零ではない** |
| 14 | 一覧に内容が含まれない | 列数の種類 = 1（4 列）。秘匿検査 4 件はすべて**ファイル名**（`tokenizers.md` / `secrets.md` / `tokens.css` / `chart-tokens.css`）で値ではない。陽性対照 1 で検査が働くことを確認 |
| 15 | 退避と衝突の痕跡を数えた | `.stversions` **0 件**／衝突ファイル **10 件**（全て `sync-alerts.*.log`、08-03〜08-06、由来は he/adam/dlsta/ilya の 4 台） |
| 16 | 停止時期を二つの独立した情報から推定した | A 更新時刻分布 = `2026-08-06T17:05:14`／B 同期処理の記録 = `2026-08-06 20:24:02` に接続喪失。**整合**（内容更新が接続喪失の 3.3 時間前）。第三の裏取りとして中継の連続失敗 261 行 ≒ 261.6 周期 |

---

## Task 6 検証

### 参照の解決

| spec の記載 | 解決 |
|---|---|
| `contract.conventions_rev` | 実測 `git --no-pager log -1 --format=%h -- context/conventions.md` → **`d422b08`**。spec.yaml の記載 `d422b08` と**一致したため置換不要** |
| `contract.inject_verbatim: [conventions#prohibitions]` | `context/conventions.md:98-107` の原文（下記） |

`conventions#prohibitions` の原文（要約せず原文のまま）:

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`spec.yaml` の `contract.prohibitions` 5 件はいずれもこの表に存在する。

### 検証コマンド

    make task-validate  TASK=T-2026-08-12-sync-audit-andrew   → OK / validate_exit=0
    make task-preflight TASK=T-2026-08-12-sync-audit-andrew   → preflight_exit=0

    P1 venv_active            PASS
    P2 cuda_ext_loaded        SKIP （plan.env.preflight に記載なし）
    P3 deterministic_flags    SKIP （plan.env.preflight に記載なし）
    P4 prereg_committed       SKIP （kind=analysis のため対象外）
    P5 frozen_source_hash     SKIP （kind=analysis のため対象外）
    P6 decisions_answered     PASS （decisions_required は空）
    P7 destination_writable   PASS
    P8 contract_valid         PASS
    P9 spec_lint              WARN  host_mismatch@SPEC.md:4
    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL

`P9` の該当は `rule_host_mismatch`（`tools/check_spec.py:296`）が `socket.gethostname()` を
本文の宣言と比較するもので、実測は `Andrew`、宣言は `andrew`。**大文字小文字の差**である。
同一の機体を指しており、実行ホストの取り違えではない。

### 禁止領域

    make forbidden-check   → {"base": "origin/phase0", "changed": 5, "checked": 5, "errors": [],
                              "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"],
                              "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
                              exit=0

    git --no-pager status --porcelain   → 1 行
    ?? tasks/T-2026-08-12-sync-audit-andrew/

    unmerged = 0

**作業ツリーの変更は本契約のディレクトリ 1 件のみ。**
`.sync-pause` は `.gitignore` 済みのため一覧に現れない（実在は `ls -la` で確認済み）。

### 零と判定した項目の再確認（申し送り 1）

| 項目 | 一次測定 | 別の探し方 | 道具が非零を出せることの確認 |
|---|---:|---|---|
| `TIMEOUT` の件数 | 0 | 行末指定を外した `grep -c 'TIMEOUT'` でも **0** | Task 1 陽性対照 `C_noroute` が `TIMEOUT` を出力 |
| 中継 `ssh -L` の実プロセス | 0 | `ps` を先に保存し別命令で走査して **0**（`sshd` のみ） | 同じ走査で `keeper.sh` を **1** 件検出 |
| `.stversions` | 0 | `ls -a` 直下 **0** / 種類を問わない `find -name` **0** の計 4 通りで一致 | 設定には `<versioning>` 要素が 3 件あるが中身は空（無効） |
| ハッシュ失敗 `ERR:` | 0 | 生成物 2496 行すべてが 4 列で要約値を持つ | — |
| 未解決ファイル | 0 | `git diff --diff-filter=U` が空 | — |
| `find ~ -maxdepth 3 -name "syncthing*.log"` | 0 | **`*syncthing*.log` にすると 1 件**（`/home/ubuntu/.syncthing.log`） | 下記の起票者の誤り 4 を参照 |


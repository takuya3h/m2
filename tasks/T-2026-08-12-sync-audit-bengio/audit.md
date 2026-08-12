# audit — T-2026-08-12-sync-audit-bengio

実行ホスト: bengio / 実行日: 2026-08-12 / 分岐: feat/sync-audit-bengio
本ファイルは実測出力をそのまま貼るためのものである。要約しない。

## Task 1 測定系の健全性

### Step 2: 到達性プローブの陽性対照

期待: A_open=OPEN / B_closed=REFUSED / C_noroute=TIMEOUT

```
A_open    127.0.0.1:49869 OPEN
B_closed  127.0.0.1:49869 REFUSED
C_noroute 192.0.2.1:22000 TIMEOUT
```

実測: 期待と一致（三通りを出し分けた）。

### Step 3: 版管理側の経路（第二の陽性対照）

```
a85cf78d9f8fc5895839bdf523e957f3da8a1f0e	refs/heads/phase0
exit=0
```

実測: 参照が 1 行返り exit=0。外向きの通信は生きている。

**G1: PASS**

## Task 2 常駐処理の実装

### Step 1: 常駐処理の稼働を数える

```
$ ls -la ~/bin/
total 52744
drwxrwxr-x 2 ubuntu ubuntu     4096  8月 12 07:41 .
drwxr-x--- 1 ubuntu ubuntu     4096  8月 12 08:06 ..
-rwxrwxr-x 1 ubuntu ubuntu     2250  7月  4 07:17 keeper.sh
-rwxrwxr-x 1 ubuntu ubuntu     7342  8月 12 07:41 m2-sync.sh
-rwxr-xr-x 1 ubuntu ubuntu 27045912  8月  5 13:25 syncthing
-rwxr-xr-x 1 ubuntu ubuntu 26933720  7月  8 23:19 syncthing.old
exit=0

$ ps -eo args | grep -c "[k]eeper.sh"
2
$ ps -eo args | grep "[k]eeper.sh"
/bin/bash /home/ubuntu/bin/keeper.sh
/usr/bin/zsh -c source /home/ubuntu/.claude/shell-snapshots/snapshot-zsh-1786285084881-18nkau.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin unalias -- 'unsetenv'; \builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'cd ~/slocal2/m2 D=tasks/T-2026-08-12-sync-audit-bengio { echo echo "## Task 2 常駐処理の実装" echo echo '"'"'### Step 1: 常駐処理の稼働を数える'"'"' echo echo '"'"'```'"'"' echo '"'"'$ ls -la ~/bin/'"'"' } >> $D/audit.md ls -la ~/bin/ >> $D/audit.md 2>&1; echo "exit=$?" >> $D/audit.md { echo echo '"'"'$ ps -eo args | grep -c "[k]eeper.sh"'"'"' } >> $D/audit.md ps -eo args | grep -c "[k]eeper.sh" >> $D/audit.md { echo '"'"'$ ps -eo args | grep "[k]eeper.sh"'"'"' } >> $D/audit.md ps -eo args | grep "[k]eeper.sh" >> $D/audit.md echo '"'"'```'"'"' >> $D/audit.md echo "--- 画面表示 ---" ls -la ~/bin/ 2>&1 | head -12 echo "keeper.sh の件数: $(ps -eo args | grep -c '"'"'[k]eeper.sh'"'"')" ps -eo args | grep "[k]eeper.sh"' < /dev/null && pwd -P >| /tmp/claude-6d9a-cwd
```

**素朴な数え方は 3 を返したが、これは誤りである。** `[k]eeper.sh` の角括弧は grep 自身の
自己一致を防ぐだけで、**計測側シェルのコマンドライン引数に文字列が載る**場合は一致する。
SPEC が `pgrep -f` を禁じたのと同じ機序が `ps | grep` でも起きた。

### Step 2: 別の探し方（argv 精査・自分と祖先を除外）

```
pid=773      自分/祖先=False  /bin/bash /home/ubuntu/bin/keeper.sh
素朴な数え方 = 3 / argv 精査・自己除外の実数 = 1
```

**両方を記録する。** 実数は 1（pid 773）。素朴な 3 は計測側の混入である。

### Step 2b: 別系統の確認

```
$ ps -eo pid,etime,args | grep -v grep | grep -i -E "keeper|syncthing|ssh -N"
    773  6-23:05:51 /bin/bash /home/ubuntu/bin/keeper.sh
    789  6-23:05:51 /home/ubuntu/bin/syncthing serve --no-browser
   2070  6-18:41:53 /home/ubuntu/bin/syncthing serve --no-browser

$ ls -la ~/.keeper.lock
-rw-rw-r-- 1 ubuntu ubuntu 0  8月 11 21:55 /home/ubuntu/.keeper.lock
```

### Step 3: 中心ホストの決め方（実装から読む）

```
$ wc -l ~/bin/keeper.sh
34 /home/ubuntu/bin/keeper.sh

$ grep -n -i -E "tunnel|hub|ssh |22000|22001|50072" ~/bin/keeper.sh
13:  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
14:  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
15:  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
16:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
19:      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &

$ git --no-pager diff --no-index -- scripts/sync/keeper.sh ~/bin/keeper.sh
0 /tmp/kd.txt
```

**実装から読み取った中心ホストの決め方**（`~/bin/keeper.sh` 13-19 行、正本と差分 0 行）

```
  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
      -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &
  fi
```

- 中心は **philip**（`192.168.196.150`）。SSH は **50072**、同期処理は中心側 **22000**。
- 各ノードは局所 **22001** を中心の 22000 へ転送する星型。
- **トンネルを張る条件は `~/.tunnel_to_philip` の存在**（中身は秘密鍵のパス）。
  この目印を持たないノードはトンネルを張らない。
- 実装自身が `pgrep -f` を使っている（15 行）。本 SPEC が実行者へ禁じた命令である。

### Step 4: 中継の目印を集合として列挙

```
$ ls -a ~/ | grep -i tunnel
.tunnel.log
.tunnel_to_philip
count=2
home_total=74
```

別の探し方（目印の実在確認）:
```
EXISTS /home/ubuntu/.tunnel_to_philip (44 bytes, mtime=2026-07-03 23:36:06.855297554 +0000)
EXISTS /home/ubuntu/.tunnel.log (18290 bytes, mtime=2026-08-12 07:41:53.408419994 +0000)
```

**bengio は `~/.tunnel_to_philip` を持つ。** よって keeper.sh はトンネル維持の対象ノードである。
`~/.tunnel.log` は 20 分前まで更新されており、試行が継続していることを示す。

## Task 3 同期処理の状態と設定

### Step 1: 同期処理と中継の稼働（ppid で二重起動を確かめる）

```
3 /tmp/st.txt
    789     773  6-23:07:04 /home/ubuntu/bin/syncthing serve --no-browser
   2070     789  6-18:43:06 /home/ubuntu/bin/syncthing serve --no-browser
 394319   98113       00:00 /usr/bin/zsh -c source /home/ubuntu/.claude/shell-snapshots/snapshot-zsh-1786285084881-18nkau.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin unalias -- 'unsetenv'; \builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'cd ~/slocal2/m2 D=tasks/T-2026-08-12-sync-audit-bengio { echo echo '"'"'別の探し方（目印の実在確認）:'"'"' echo '"'"'```'"'"' } >> $D/audit.md for f in ~/.tunnel_to_philip ~/.tunnel.log; do   test -e "$f" && echo "EXISTS $f ($(stat -c '"'"'%s bytes, mtime=%y'"'"' "$f"))" >> $D/audit.md || echo "ABSENT $f" >> $D/audit.md done { echo '"'"'```'"'"' echo echo '"'"'**bengio は `~/.tunnel_to_philip` を持つ。** よって keeper.sh はトンネル維持の対象ノードである。'"'"' echo '"'"'`~/.tunnel.log` は 20 分前まで更新されており、試行が継続していることを示す。'"'"' echo echo '"'"'## Task 3 同期処理の状態と設定'"'"' echo echo '"'"'### Step 1: 同期処理と中継の稼働（ppid で二重起動を確かめる）'"'"' echo echo '"'"'```'"'"' } >> $D/audit.md ps -eo pid,ppid,etime,args | grep "[s]yncthing" > /tmp/st.txt wc -l /tmp/st.txt >> $D/audit.md cat /tmp/st.txt >> $D/audit.md { echo echo '"'"'$ ps -eo args | grep -c "[s]sh .*-L"'"'"' } >> $D/audit.md ps -eo args | grep -c "[s]sh .*-L" >> $D/audit.md ps -eo args | grep "[s]sh .*-L" >> $D/audit.md 2>&1 || true echo '"'"'```'"'"' >> $D/audit.md echo "--- 画面表示: syncthing ---" cat /tmp/st.txt echo "行数: $(wc -l < /tmp/st.txt)" echo "--- ssh -L の件数（素朴） ---" ps -eo args | grep -c "[s]sh .*-L" echo "--- 別の探し方: argv 精査で ssh トンネルを数える ---" .venv/bin/python - <<'"'"'PY'"'"' import os, pathlib me = os.getpid(); anc, p = set(), me for _ in range(20):     try: ppid = int(pathlib.Path(f"/proc/{p}/stat").read_text().rsplit(")",1)[1].split()[1])     except Exception: break     if ppid <= 1: break     anc.add(ppid); p = ppid anc.add(me) n = 0 for d in pathlib.Path("/proc").iterdir():     if not d.name.isdigit(): continue     try: argv = [a.decode("utf-8","replace") for a in d.joinpath("cmdline").read_bytes().split(b"\0") if a]     except Exception: continue     if argv and pathlib.Path(argv[0]).name == "ssh" and int(d.name) not in anc:         n += 1; print(f"  pid={d.name} {'"'"' '"'"'.join(argv)[:100]}") print("argv[0] が ssh のプロセス数 =", n) PY' && pwd -P >| /tmp/claude-4cc4-cwd

$ ps -eo args | grep -c "[s]sh .*-L"
1
/usr/bin/zsh -c source /home/ubuntu/.claude/shell-snapshots/snapshot-zsh-1786285084881-18nkau.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin unalias -- 'unsetenv'; \builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'cd ~/slocal2/m2 D=tasks/T-2026-08-12-sync-audit-bengio { echo echo '"'"'別の探し方（目印の実在確認）:'"'"' echo '"'"'```'"'"' } >> $D/audit.md for f in ~/.tunnel_to_philip ~/.tunnel.log; do   test -e "$f" && echo "EXISTS $f ($(stat -c '"'"'%s bytes, mtime=%y'"'"' "$f"))" >> $D/audit.md || echo "ABSENT $f" >> $D/audit.md done { echo '"'"'```'"'"' echo echo '"'"'**bengio は `~/.tunnel_to_philip` を持つ。** よって keeper.sh はトンネル維持の対象ノードである。'"'"' echo '"'"'`~/.tunnel.log` は 20 分前まで更新されており、試行が継続していることを示す。'"'"' echo echo '"'"'## Task 3 同期処理の状態と設定'"'"' echo echo '"'"'### Step 1: 同期処理と中継の稼働（ppid で二重起動を確かめる）'"'"' echo echo '"'"'```'"'"' } >> $D/audit.md ps -eo pid,ppid,etime,args | grep "[s]yncthing" > /tmp/st.txt wc -l /tmp/st.txt >> $D/audit.md cat /tmp/st.txt >> $D/audit.md { echo echo '"'"'$ ps -eo args | grep -c "[s]sh .*-L"'"'"' } >> $D/audit.md ps -eo args | grep -c "[s]sh .*-L" >> $D/audit.md ps -eo args | grep "[s]sh .*-L" >> $D/audit.md 2>&1 || true echo '"'"'```'"'"' >> $D/audit.md echo "--- 画面表示: syncthing ---" cat /tmp/st.txt echo "行数: $(wc -l < /tmp/st.txt)" echo "--- ssh -L の件数（素朴） ---" ps -eo args | grep -c "[s]sh .*-L" echo "--- 別の探し方: argv 精査で ssh トンネルを数える ---" .venv/bin/python - <<'"'"'PY'"'"' import os, pathlib me = os.getpid(); anc, p = set(), me for _ in range(20):     try: ppid = int(pathlib.Path(f"/proc/{p}/stat").read_text().rsplit(")",1)[1].split()[1])     except Exception: break     if ppid <= 1: break     anc.add(ppid); p = ppid anc.add(me) n = 0 for d in pathlib.Path("/proc").iterdir():     if not d.name.isdigit(): continue     try: argv = [a.decode("utf-8","replace") for a in d.joinpath("cmdline").read_bytes().split(b"\0") if a]     except Exception: continue     if argv and pathlib.Path(argv[0]).name == "ssh" and int(d.name) not in anc:         n += 1; print(f"  pid={d.name} {'"'"' '"'"'.join(argv)[:100]}") print("argv[0] が ssh のプロセス数 =", n) PY' && pwd -P >| /tmp/claude-4cc4-cwd
```

**素朴な `ps | grep` は 3 行を返したが、3 行目は計測側シェルである**（同じコマンドライン内の
表示用 echo に素の文字列が入ったため）。SPEC 注意 3「記録を作る流れに表示用の切り詰めを
混ぜない」と同じ構図。argv 精査・自己除外で測り直した結果を正とする。

```
=== 同期処理（argv[0] の基底名で判定・自己除外） ===
  pid=789     ppid=773     /home/ubuntu/bin/syncthing serve --no-browser
  pid=2070    ppid=789     /home/ubuntu/bin/syncthing serve --no-browser
count = 2
親子関係: {789: 773, 2070: 789}

=== 中継（argv[0] が ssh・自己除外） ===
count = 0
```

- 同期処理は **2 プロセスだが親子**（789 の親は 773=keeper、2070 の親は 789）。**二重起動ではない。**
- **中継トンネルは 0 件。** bengio は `~/.tunnel_to_philip` を持つのでトンネル維持の対象だが、走っていない。

### Step 2: 待ち受けの一覧

```
1 /tmp/listen.txt
手段なし
```

`ss` も `netstat` も無い。**零行ではなく「測る手段が無かった」。**

### Step 3: 中継の入口と同期処理への接続

```
127.0.0.1:22001 REFUSED
127.0.0.1:22000 OPEN
```

- **22001（中継の入口）= REFUSED。** 局所で待ち受けが無い＝トンネル不在。ssh 0 件と整合。
- **22000（同期処理）= OPEN。** 同期処理そのものは健在である。

### Step 4: 設定ファイルの場所を集合として探す

```
FOUND /home/ubuntu/.local/state/syncthing
total 52
drwx------ 3 ubuntu ubuntu  4096  8月  5 13:26 .
drwxrwxr-x 6 ubuntu ubuntu  4096  7月  3 22:59 ..
-rw------- 1 ubuntu ubuntu     0  7月  3 23:17 .syncthing.tmp.239490227
-rw-rw-r-- 1 ubuntu ubuntu   623  7月  3 22:59 cert.pem
-rw------- 1 ubuntu ubuntu 21750  7月  4 07:19 config.xml
-rw-rw-r-- 1 ubuntu ubuntu   700  7月  3 22:59 https-cert.pem
-rw------- 1 ubuntu ubuntu   227  7月  3 22:59 https-key.pem
drwx------ 3 ubuntu ubuntu  4096  8月  5 13:26 index-v2
-rw------- 1 ubuntu ubuntu   119  7月  3 22:59 key.pem
-rw------- 1 ubuntu ubuntu     0  8月  5 13:26 syncthing.lock
$ 起動引数の home/config 指定
arg: /home/ubuntu/bin/syncthing
arg: /home/ubuntu/bin/syncthing
```

### Step 4-5: 設定の場所と構造

設定は `~/.local/state/syncthing/config.xml`（起動引数での指定は無く既定の場所）。

```
device_count=11
device name=hinton id7=CK3ACOY paused=None addrs=dynamic,tcp://192.168.196.78:22000
device name=Bengio id7=E7NPG4Q paused=None addrs=dynamic
device name=philip id7=GO2U7PF paused=None addrs=tcp://192.168.196.150:22000,tcp://127.0.0.1:22001
device name=andrew id7=KYZK57M paused=None addrs=dynamic,tcp://192.168.196.190:22000
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
```

### Step 6: 秘匿の検査

```
$ grep -c -i -E "apikey|password|token|secret" /tmp/stcfg.txt
0
```

**Expected: 0 / 実測: 0。** 識別子は先頭 7 文字のみ。API キーは読んでいない。

要点:
- `device_count=11`（既知の構成 11 台と一致）。`folder_count=2`（`claude-sync` と `m2`、
  いずれも sendreceive で全 11 台と共有）。
- **`globalAnnounceEnabled=false` かつ `relaysEnabled=false`。** 外部発見も中継も無効で、
  到達手段は局所告知と静的アドレスに限られる。
- philip だけが `tcp://127.0.0.1:22001` を持つ。**中継トンネル前提の経路**である。

## Task 4 到達可否（拒否と経路なしの区別）

### Step 1: 対象一覧（三つの出所の和集合）

```
127.0.0.1 etc_hosts,philip
172.17.0.15 etc_hosts
192.168.196.54 dlsta
192.168.196.58 adam
192.168.196.63 ilya
192.168.196.78 hinton
192.168.196.106 he
192.168.196.143 ian
192.168.196.150 philip,ssh_config
192.168.196.176 lecun,ssh_config
192.168.196.190 andrew
192.168.196.227 efros
総件数=12
遠隔（自ホスト 172.17.0.15 と loopback を除く）=10
```

出所は 3 つ。`~/.ssh/config`（`ssh_count=3`: github.com / philip / lecun）、`/etc/hosts`
（`127.0.0.1` と `172.17.0.15 Bengio`）、syncthing 設定の `tcp://`（10 台 + `127.0.0.1:22001`）。
**自ホスト 1 + 遠隔 10 = 11 台で、既知の構成 11 台と一致する。一覧は縮んでいない。**

**自ホストの IP は `172.17.0.15`（docker bridge）で、他 10 台は `192.168.196.x` である。**
keeper.sh の「コンテナ間は SSH(50072) しか通らない」という記述と符合する。

### Step 2: 各アドレスへ二つのポート（22000 待受 / 50072 中継）

ポートは実装（keeper.sh の 50072）と設定（`tcp://…:22000`）から得た値。記録から決め打ちしていない。

```
192.168.196.54:22000 REFUSED
192.168.196.54:50072 OPEN
192.168.196.58:22000 REFUSED
192.168.196.58:50072 OPEN
192.168.196.63:22000 REFUSED
192.168.196.63:50072 OPEN
192.168.196.78:22000 REFUSED
192.168.196.78:50072 OPEN
192.168.196.106:22000 REFUSED
192.168.196.106:50072 OPEN
192.168.196.143:22000 REFUSED
192.168.196.143:50072 OPEN
192.168.196.150:22000 OSERROR:No_route_to_host
192.168.196.150:50072 OSERROR:No_route_to_host
192.168.196.176:22000 REFUSED
192.168.196.176:50072 OPEN
192.168.196.190:22000 REFUSED
192.168.196.190:50072 OPEN
192.168.196.227:22000 REFUSED
192.168.196.227:50072 OPEN
total=20
```

### Step 3: 集計

```
OPEN=9
REFUSED=9
TIMEOUT=0
OTHER=2
total=20
```

**合計 20 = 対象数 20。測り漏れなし。**

TIMEOUT が零であることは別の探し方でも確認した（文字列一致 0 件、分類辞書に鍵なし、
分類は OPEN / REFUSED / OSERROR の 3 種のみ）。

| 分類 | 件数 | 意味 |
|---|---|---|
| OPEN | 9 | 50072（SSH）は 9 台すべてで開いている |
| REFUSED | 9 | 22000（同期処理）は 9 台すべてで拒否。**機器までは届いている** |
| OSERROR:No_route_to_host | 2 | philip の両ポート。**経路が無い** |
| TIMEOUT | 0 | 該当なし |

**philip（192.168.196.150）だけが経路なしである。** 他 9 台は機器まで届いており、
22000 が拒否されるのは待ち受けていない（またはコンテナ間で通らない）ためで、経路の問題ではない。

### Step 4: 版管理側との対比

同一構内の philip へは届かないが、外部の版管理へは届く（Task 1 Step 3 で `exit=0`）。
**非対称がある。** 外向きの通信全体が落ちているのではなく、philip への経路だけが失われている。

## Task 5 設定共有の棚卸しと停止時期

### Step 1: 総件数

```
~/claude-sync: EXISTS
通常ファイル: 2532
シンボリック: 1
ディレクトリ: 900
一覧の行数  : 2531
```

### Step 3: 秘匿の検査

```
$ grep -c -i -E "apikey|password|token|secret|PRIVATE KEY" inventory.tsv
4
--- 一致した 4 行（目視）---
agents/skills/modal/references/secrets.md	2874	2026-05-10T09:45:30	fa0718268752bf6d
agents/skills/transformers/references/tokenizers.md	9904	2026-05-10T09:45:32	cb33dfe12db114af
codex/plugins/cache/openai-curated-remote/data-analytics/0.2.8-13ceeea1f599/src/analytics-app/tokens.css	11016	2026-07-13T07:18:59	5453eb6085330604
codex/plugins/cache/openai-curated-remote/data-analytics/0.2.8-13ceeea1f599/src/analytics-app/charting/chart-tokens.css	14311	2026-07-13T07:18:59	bc1915546e693c0c
```

**Expected 0 に対し実測 4。ただし 4 件すべてファイル名であり、資格情報の値ではない。**
`secrets.md` は秘密情報の扱いを説明する文書、`tokenizers.md` は ML のトークナイザ、
`tokens.css` / `chart-tokens.css` は意匠のデザイントークンである。
**一覧は名前・大きさ・更新時刻・要約値のみからなり、内容を一切含まない。**

### Step 4: 退避と衝突の痕跡、更新時刻の分布

```
退避ディレクトリ .stversions = 0
衝突ファイル sync-conflict   = 10
--- 最も古い 3 件 ---
agents/skills/bgpt-paper-search/SKILL.md	2479	2026-05-10T09:45:28	033461b042b0b31d
agents/skills/citation-management/scripts/generate_schematic_ai.py	32647	2026-05-10T09:45:28	0e1708bc163eab7e
agents/skills/autoskill/scripts/autoskill.py	1169	2026-05-10T09:45:28	117df2358135df4a
--- 最も新しい 5 件 ---
codex/plugins/cache/openai-curated-remote/product-design/.codex-remote-plugin-install.json	91	2026-08-08T03:41:31	870b356037f7f1ad
codex/plugins/cache/openai-curated-remote/data-analytics/.codex-remote-plugin-install.json	91	2026-08-08T03:41:31	ea28c53a9c185ced
settings.json	14419	2026-08-09T14:17:49	e90afc605dd7d4b6
codex/config.toml	901	2026-08-11T19:59:01	510aedc0f32390a6
sync-alerts.log	59221	2026-08-12T08:11:54	068be40038dd4e7e
```

**`.stversions` が 0 件であることは重要である。** 退避された旧版が無いため、
経路が復旧して遠隔側の版が流れ込んだ場合、**局所の版を戻す手段が同期処理側に無い。**

### Step 5: 停止時期を二つの独立した情報から推定

**情報源 A: 遠隔由来の証拠（衝突ファイル）**

```
      1 20260803 5YNIXSO
      2 20260803 QGS35FJ
      3 20260805 QNQZIGJ
      2 20260805 RMG3SUE
      2 20260806 QNQZIGJ
（識別子の対応）
  20260803 5YNIXSO = he
  20260803 QGS35FJ = adam
  20260805 QNQZIGJ = ilya
  20260805 RMG3SUE = dlsta
  20260806 QNQZIGJ = ilya
```

衝突ファイルは**遠隔から競合版を受け取らないと生成されない**。最後の衝突は
**2026-08-06 16:22 UTC（ilya 由来）**。よってこの時刻までは同期が機能していた。

**情報源 B: 中継トンネルの記録**

```
総行数 = 276
末尾の連続『No route to host』= 263 行
最後の別事象 = 13 行目 'Timeout, server 192.168.196.150 not responding.'
keeper.sh の周期 = 1800 秒（33 行目 sleep 1800）
ログ最終更新 = 2026-08-12T08:11:57 UTC
逆算した連続失敗の開始 ≈ 2026-08-06T20:41 UTC
（事象の種類と件数）
    265 ssh: connect to host <IP> port <N>: No route to host
      4 bind [::1]:22001: Cannot assign requested address
      3 Timeout, server <IP> not responding.
      2 channel 1: open failed: connect failed: Connection refused
      1 ssh: connect to host <IP> port <N>: Connection timed out
      1 channel 3: open failed: connect failed: Connection refused
```

**判定: 二つは整合する。** A は 08-06 16:22 まで機能、B は 08-06 20:41 頃から連続失敗。
差の約 4 時間は、B の逆算が「1 周回あたり 1 行」を仮定した目安であることで説明がつく範囲。
**停止は 2026-08-06 と推定する。** ただし B に時刻印は無く、逆算は上限に近い目安である。

08-08 の 169 件は**すべて `codex/` 配下**であり局所の導入によるもの。遠隔由来ではなく矛盾しない。

```
（08-06 以降に更新された項目の最上位内訳）
    170 codex
      1 sync-alerts.sync-conflict-20260806-162224-QNQZIGJ.log
      1 sync-alerts.sync-conflict-20260806-162223-QNQZIGJ.log
      1 sync-alerts.log
      1 settings.json
```

**同期処理のログの場所**: `~/.syncthing.log`（10730567 バイト）、`~/.tunnel.log`（18357 バイト）。
`~/claude-sync/sync-alerts.log` は **git 側の操作のみ**を記録しており、同期処理の停止時期は判定できない。

### G3 の検証（陽性対照つき）

一覧の構造検査:
```
行数=2531  列数の種類={4}  4 列でない行=0
4 列目が 16 桁 hex の行=2531/2531   3 列目が ISO 時刻の行=2531/2531
```

**一覧は 4 列固定（名前・大きさ・更新時刻・要約値）で、内容を一切含まない。**

陽性対照（SPEC の検査式に既知の値を仕込む）:
```
元の一致件数        : 4
password を足した後 : 5   ← 検出する
API_KEY を足した後  : 5   ← **増えない。逃している**
```

🔴 **SPEC の検査式には取りこぼしがある。** `apikey` は区切りを含まないため
`API_KEY` / `api-key` / `API-KEY` に一致しない。本プロジェクトの実際の変数名は
`NOTION_API_KEY` と `WANDB_API_KEY` であり、いずれも区切りを含む。
**この検査だけでは資格情報の混入を保証できない。**

強化版（`api[_-]?key|password|passwd|token|secret|credential|BEGIN … PRIVATE KEY|ntn_…|ghp_…`）
で実際の一覧を再検査した結果:
```
強化版での一致件数: 4
agents/skills/modal/references/secrets.md	2874	2026-05-10T09:45:30	fa0718268752bf6d
agents/skills/transformers/references/tokenizers.md	9904	2026-05-10T09:45:32	cb33dfe12db114af
codex/plugins/cache/openai-curated-remote/data-analytics/0.2.8-13ceeea1f599/src/analytics-app/tokens.css	11016	2026-07-13T07:18:59	5453eb6085330604
codex/plugins/cache/openai-curated-remote/data-analytics/0.2.8-13ceeea1f599/src/analytics-app/charting/chart-tokens.css	14311	2026-07-13T07:18:59	bc1915546e693c0c
```

**強化版でも一致は同じ 4 件のファイル名のみ。資格情報の値は 0 件。G3 PASS。**

## Task 6 検証

### 検証の終了コード

```
make task-validate  → exit=0（WARN 0 件）
make task-preflight → exit=0（4 PASS / 1 WARN / 4 SKIP / 0 FAIL）
validate_task.py 単体 → exit=0（make 経由と食い違いなし）
make forbidden-check → exit=0
  {"base": "origin/phase0", "changed": 5, "checked": 5, "errors": [],
   "excluded": 0, "status": "pass", "violations": []}
```

P9 の WARN は `host_mismatch@SPEC.md:4`。**偽陽性である。**
`rule_host_mismatch` は生の `socket.gethostname()`（=`Bengio`）を宣言値 `bengio` と
大文字小文字を区別して比べる。本プロジェクトの正規化 `resolve_server_name()` は
小文字化して `bengio` を返し、宣言と一致する。**実行ホストは正しく bengio である。**

### 試験

```
7 failed, 421 passed, 21 warnings in 21.34s
```

本契約はコードを変更していない。7 件のうち 2 件は `spec_lint` 関連で、
**本契約とは無関係**であることを実測で示した。

```
$ grep -n "SELF_TASK" tests/test_check_spec.py tests/test_preflight_task.py
tests/test_check_spec.py:34:SELF_TASK = "T-2026-08-11-issuer-defect-detector"
tests/test_preflight_task.py:137:SELF_TASK = "T-2026-08-11-issuer-defect-detector"

$ 本契約のディレクトリを一時退避して同じ 2 件を測る
FAILED tests/test_check_spec.py::test_self_contract_has_no_hit
FAILED tests/test_preflight_task.py::test_spec_lint_passes_on_clean_contract
2 failed in 0.10s   ← 退避しても失敗する
```

失敗の理由は `tasks/T-2026-08-11-issuer-defect-detector/SPEC.md:5` が実行ホストを
`lecun` と宣言しており、bengio で走らせると一致しないため。**この 2 件は lecun 以外の
すべてのホストで失敗する。** P9 の WARN と同一の根本原因である。

### 作業ツリー

```
?? tasks/T-2026-08-12-sync-audit-bengio/
wt_lines=1
unmerged=0
context/auto/ の変更 = 0 件   tasks/inbox.md の変更 = 0 件（禁止 8 を遵守）
.sync-pause は .gitignore:240 により追跡外
```

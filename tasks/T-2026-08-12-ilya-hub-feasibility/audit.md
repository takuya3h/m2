# audit — ilya hub feasibility（停止条件までの実測）

**task_id:** `T-2026-08-12-ilya-hub-feasibility`  **実行日:** 2026-08-12

読み取りのみ。鍵・設定・常駐処理は変更していない。Task 3 の陽性対照が当初契約の期待と
一致しなかったため一度停止し、ユーザー承認のamendment後に再開した。

## 前提

出力（原文）:

```text
2
feat/ilya-hub-feasibility
?? tasks/T-2026-08-12-ilya-hub-feasibility/
```

- 稼働中の `m2-sync.sh` は `sync-pause` を2箇所参照する。
- 契約用分岐であり、開始時の未追跡物は契約ディレクトリだけだった。
- preflight は `4 PASS / 1 WARN / 4 SKIP / 0 FAIL`。WARN は既知のhost mismatch。

## Task 1: 受け入れ一覧

### Step 1–2: 場所、行数、指紋、注釈

出力（原文）:

```text
FILE /home/ubuntu/.ssh/authorized_keys lines=2
-rw-rw-r-- 1 ubuntu ubuntu 668 Jul  1 02:12 /home/ubuntu/.ssh/authorized_keys
#Port 22
#PermitRootLogin prohibit-password
#PubkeyAuthentication yes
#AuthorizedKeysFile	.ssh/authorized_keys .ssh/authorized_keys2
# the setting of "PermitRootLogin without-password".
#GatewayPorts no
count=2
256 SHA256:30y00ixicNIVEovdR82sNN0xJTtYZ5G+lJdfxY4ndZY dakyo-mba@dmba.local (ED25519)
3072 SHA256:7DqWCg8978q2A/fTUwHy8W1JbKvatp6bXCt4F4DzM2A ubuntu@aolab (RSA)
```

既定の受け入れ場所は `.ssh/authorized_keys` と `.ssh/authorized_keys2`。実在したのは
前者だけで、空でない行は2件。指紋と注釈だけを記録し、鍵本体は記録していない。

### Step 3: 目標4台

| 送り出し側 | 注釈への直接の該当 | 判定 |
|---|---:|---|
| efros | なし | 登録が要る |
| lecun | なし | 登録が要る |
| bengio | なし | 登録が要る |
| andrew | なし | 登録が要る |

`ubuntu@aolab` は契約上 ilya と philip の双方が返す文字列であり、単独ホストへ帰属させない。
目標4台を直接示す注釈は0件なので、追加登録が要る台数は4台。

### Step 4: 中継目印と鍵ファイル名

出力（原文。内容は表示していない）:

```text
.tunnel.log
.tunnel_to_philip
tunnel_count=2
total 52
drwx------ 2 ubuntu ubuntu 4096 Aug  3 22:14 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 12 19:06 ..
-rw-rw-r-- 1 ubuntu ubuntu  668 Jul  1 02:12 authorized_keys
-rw------- 1 ubuntu ubuntu  242 Jul  1 05:11 config
-rw------- 1 ubuntu ubuntu  399 Jul  1 05:11 id_ed25519_github
-rw-r--r-- 1 ubuntu ubuntu   94 Jul  1 05:11 id_ed25519_github.pub
-rw------- 1 ubuntu ubuntu  399 Jul  3 23:36 id_ed25519_ilyatophilip
-rw-r--r-- 1 ubuntu ubuntu   94 Jul  3 23:36 id_ed25519_ilyatophilip.pub
-rw------- 1 ubuntu ubuntu 2602 Jul  1 02:24 id_rsa_ilyatophilip
-rw-r--r-- 1 ubuntu ubuntu  566 Jul  1 02:24 id_rsa_ilyatophilip.pub
-rw------- 1 ubuntu ubuntu 1956 Aug  3 22:14 known_hosts
-rw------- 1 ubuntu ubuntu 1120 Jul  4 07:18 known_hosts.old
known_hosts size=1956 mtime=2026-08-03 22:14:59.236043451 +0000
1956 /home/ubuntu/.ssh/known_hosts
```

中継の目印は2件。中心へ移す場合は扱いを決める必要があるが、本契約では変更しない。

## Task 2: 入られる側

### Step 1: LISTEN復号と陽性対照

出力（原文）:

```text
listen_count=7
ports=22,8384,22000,24282,24283,24284,43493
port_22=LISTEN
port_50072=-
port_22000=LISTEN
port_22001=-
port_8384=LISTEN
positive_control_port=51525
while_open=True
after_close=False
```

復号は空振りでなく、一時ソケットが開いている間だけ現れた。

### Step 2–4: SSH、同期処理、住所

出力（原文）:

```text
設定を読めない
syncthing=2
keeper.sh=1
zzz_no_such_process=0
           |-- 127.0.0.1
              /32 host LOCAL
           |-- 172.17.0.14
              /32 host LOCAL
           |-- 127.0.0.1
              /32 host LOCAL
           |-- 172.17.0.14
              /32 host LOCAL
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
ff00::0	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.14	aolab
aolab
```

`sshd_config` に有効な `Port` / `ListenAddress` 行はなく、実際のLISTENは22番。
外から見えるSSH番号は `UNKNOWN`。同期処理は自己・祖先を除いて2プロセス、keeperは1、
不存在語は0で、局所22000番もLISTEN。コンテナ内住所は `172.17.0.14`、外から見える住所は
`UNKNOWN`。hostnameは契約の既知事実どおり `aolab`。

## Task 3: 構内到達性

### Step 1: 対象一覧

三出所の出力（原文）:

```text
[ssh_config]
Host philip
    HostName 192.168.196.150
Host github.com
  HostName github.com
[etc_hosts]
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
ff00::0	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.14	aolab
[syncthing_addresses]
tcp://127.0.0.1:22001
tcp://192.168.196.105:22000
tcp://192.168.196.106:22000
tcp://192.168.196.143:22000
tcp://192.168.196.150:22000
tcp://192.168.196.176:22000
tcp://192.168.196.190:22000
tcp://192.168.196.227:22000
tcp://192.168.196.54:22000
tcp://192.168.196.58:22000
tcp://192.168.196.78:22000
```

直接のdevice階層を解析した出力（原文）:

```text
direct_device_count=11
adam tcp://192.168.196.58:22000
andrew tcp://192.168.196.190:22000
aolab NO_TCP_ADDRESS
bengio tcp://192.168.196.105:22000
dlsta tcp://192.168.196.54:22000
efros tcp://192.168.196.227:22000
he tcp://192.168.196.106:22000
hinton tcp://192.168.196.78:22000
ian tcp://192.168.196.143:22000
lecun tcp://192.168.196.176:22000
philip tcp://127.0.0.1:22001,tcp://192.168.196.150:22000
```

名前付き対象は既知構成と一致する11台。目標4台をすべて含む。

### Step 2: 陽性対照 — 停止条件

期待は `OPEN / REFUSED / TIMEOUT`。出力（原文）:

```text
A_open    127.0.0.1:52049 OPEN
B_closed  127.0.0.1:52049 REFUSED
C_noroute 192.0.2.1:22000 OSERROR:Network_is_unreachable
```

三つ目が期待の `TIMEOUT` と一致しなかった。契約のG2および「想定外が起きたときの扱い」に
従い、ここで停止した。実対象への到達性、外向きGit経路、SSH認証、測定後の
`known_hosts` 比較は未実施であり `UNKNOWN`。

停止後の `/proc/net/route` 出力（原文）:

```text
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT
eth0	00000000	010011AC	0003	0	0	0	00000000	0	0	0
eth0	000011AC	00000000	0001	0	0	0	0000FFFF	0	0	0
```

プローブは「経路なし」をTIMEOUTではなくOSERRORとして区別した。当初契約の期待値を
満たさなかったため一度停止した。その後ユーザー承認を受け、2026-08-12 amendmentで
`OSERROR:Network_is_unreachable` を同値な経路なし分類として許容し、ここから再開した。

## 現時点の中心要件（判断はしない）

| 要件 | 実測 |
|---|---|
| efros / lecun / bengio / andrew が入れるか | 4台とも注釈への直接該当なし（各台「登録が要る」） |
| SSHの口が待ち受けているか | コンテナ内22番はLISTEN。外から見える番号はUNKNOWN |
| 同期処理が局所で待ち受けているか | syncthing=2、22000番LISTEN |
| 追加で登録が要る台数 | 4 |
| 今日の構内到達性 | 10台中9台の50072番へ到達（目標4台を含む）。philipのみ経路なし |

### Step 2再開後: 実対象20組

他ノード10台について、Syncthingの22000番とSSHの50072番を測った。出力（原文）:

```text
21 /tmp/reach.txt
target_count=20
192.168.196.58:22000 REFUSED
192.168.196.58:50072 OPEN
192.168.196.105:22000 REFUSED
192.168.196.105:50072 OPEN
192.168.196.106:22000 REFUSED
192.168.196.106:50072 OPEN
192.168.196.143:22000 REFUSED
192.168.196.143:50072 OPEN
192.168.196.150:22000 OSERROR:No_route_to_host
192.168.196.150:50072 TIMEOUT
192.168.196.176:22000 REFUSED
192.168.196.176:50072 OPEN
192.168.196.190:22000 REFUSED
192.168.196.190:50072 OPEN
192.168.196.227:22000 REFUSED
192.168.196.227:50072 OPEN
192.168.196.54:22000 REFUSED
192.168.196.54:50072 OPEN
192.168.196.78:22000 REFUSED
192.168.196.78:50072 OPEN
classified_total=20
OPEN=9
OSERROR=1
REFUSED=9
TIMEOUT=1
```

意味上の三分類は `OPEN=9`、`REFUSED=9`、経路なし=2（`OSERROR` 1 + `TIMEOUT` 1）で
合計20、対象数と一致する。目標4台 efros (`.227`) / lecun (`.176`) / bengio (`.105`) /
andrew (`.190`) はすべて22000番REFUSED、50072番OPEN。機器とSSH口へは届いている。

過去2回の「ilyaは構内へ出られない」と**食い違う**。今日の値では、philipを除く9台の
SSH口へ到達できるため、ilyaは構内へ出られる。

### Step 3: 外向き経路

出力（原文）:

```text
6ed77e9f929e0ddc3e27fe6ee9cfde5fff8fed0f	refs/heads/phase0
exit=0
```

外向きGit経路も生きている。

### Step 4: OPEN先のSSH認証

使用した鍵の経路は `/home/ubuntu/.ssh/id_ed25519_ilyatophilip`。鍵本文は表示していない。
`BatchMode=yes`、`IdentitiesOnly=yes`、`UserKnownHostsFile=/tmp/kh_audit.txt`、
`StrictHostKeyChecking=accept-new` を指定し、他ホストで許可した命令は `echo REACHABLE` のみ。

出力（原文）:

```text
TARGET 192.168.196.58:50072
Warning: Permanently added '[192.168.196.58]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.58: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.105:50072
Warning: Permanently added '[192.168.196.105]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.105: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.106:50072
Warning: Permanently added '[192.168.196.106]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.106: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.143:50072
Warning: Permanently added '[192.168.196.143]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.143: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.176:50072
Warning: Permanently added '[192.168.196.176]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.176: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.190:50072
Warning: Permanently added '[192.168.196.190]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.190: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.227:50072
Warning: Permanently added '[192.168.196.227]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.227: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.54:50072
Warning: Permanently added '[192.168.196.54]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.54: Permission denied (publickey,password).
ssh_exit=255
TARGET 192.168.196.78:50072
Warning: Permanently added '[192.168.196.78]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.78: Permission denied (publickey,password).
ssh_exit=255
```

9台すべてTCP/SSH口までは到達したが、philip専用の対別鍵では認証されなかった。

### Step 5: `known_hosts` 前後比較

出力（原文）:

```text
known_hosts size=1956 mtime=2026-08-03 22:14:59.236043451 +0000
1956 /home/ubuntu/.ssh/known_hosts
9 /tmp/kh_audit.txt
-rw-r--r-- 1 ubuntu ubuntu 1278 Aug 12 19:18 /tmp/kh_audit.txt
```

Task 1 時点とサイズ・mtimeが一致する。禁止領域の `~/.ssh/known_hosts` は無変更で、
ホスト鍵9件は隔離先だけへ書かれた。

## 秘匿検査と停止時の副作用確認

秘匿検査の出力（囮本文だけは外部へ送らないため件数へ置換）:

```text
[audit_scan]
32:#PermitRootLogin prohibit-password
35:# the setting of "PermitRootLogin without-password".
[positive_control_scan]
match_count=1
positive_control_exit=0
```

監査本文の2件はsshd設定の説明語であり、区切りと値が続く資格情報ではない。長い基数六十四の
塊や鍵本文もない。囮の鍵ヘッダーは1件検出できたため、検査は空振りではない。囮は `/tmp` に
のみ置き、外部へ送っていない。

停止時の出力（原文）:

```text
known_hosts size=1956 mtime=2026-08-03 22:14:59.236043451 +0000
1956 /home/ubuntu/.ssh/known_hosts
```

Task 1 時点とサイズ・mtimeが一致し、停止までに `known_hosts` は変わっていない。

## commit前検証

出力（原文）:

```text
OK   T-2026-08-12-ilya-hub-feasibility
1 task(s), 0 failed
validate_exit=0
RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
{"base": "origin/phase0", "changed": 7, "checked": 7, "errors": [], "excluded": 0, "excluded_paths": [], "status": "pass", "violations": []}
forbidden_exit=0
diff_check_exit=0
3 /tmp/wt.txt
 M tasks/todo.md
?? tasks/T-2026-08-12-ilya-hub-feasibility/
?? tasks/inbox.d/T-2026-08-12-ilya-hub-feasibility.md
unmerged=0
```

preflightのWARNは既知のhost mismatchだけ。変更は契約ディレクトリ、判断受け皿、上位指示で
必須の`tasks/todo.md`追記に限られ、競合と禁止領域違反は0。

## commit・push・PR

出力（原文）:

```text
e80025b docs(sync): measure hub feasibility on ilya
Already up to date.
HEAD -> feat/ilya-hub-feasibility
Branch 'feat/ilya-hub-feasibility' set up to track remote branch 'feat/ilya-hub-feasibility' from 'origin'.
{"baseRefName":"phase0","headRefName":"feat/ilya-hub-feasibility","isDraft":false,"number":93,"state":"OPEN","url":"https://github.com/takuya3h/m2/pull/93"}
0 0
```

commitは`e80025b`。分岐は上流設定済みでahead/behindとも0。PR #93はOPEN・非Draft。
phase0への統合は行っていない。

## 同期抑止解除

出力（原文）:

```text
released
repo 直下から消えた
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 12 19:09 /tmp/.sync-pause.released.T-2026-08-12-ilya-hub-feasibility
```

`.sync-pause`はrepo外へ移動され、必要なら退避先から戻せる。

## 台帳報告（初回）

出力（SHA-256は秘匿検査の誤検出を避け先頭8文字へ短縮）:

```text
task_id=T-2026-08-12-ilya-hub-feasibility
verdict=partial
n_issuer_defects=1
report_sha256_prefix=ba86b290
report_bytes=6307
replaced_blocks=0
report_exit=0
```

初回報告はexit 0。最終成果物をcommit・pushした後、verdict=passの内容を再送する。

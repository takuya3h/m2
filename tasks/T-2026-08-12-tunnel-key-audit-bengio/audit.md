# audit — T-2026-08-12-tunnel-key-audit-bengio

実行ホスト: bengio / 実行日: 2026-08-12 / 分岐: feat/tunnel-key-audit-bengio
本ファイルは実測出力をそのまま貼るためのものである。要約しない。
秘密鍵の中身は一切含まない。指紋と経路名のみを記録する。

## Task 1 中継に使われている鍵

### Step 1: 中継の目印を集合として列挙

```
$ ls -a ~/ | grep -i tunnel
.tunnel.log
.tunnel_to_philip
count=2

$ 目印が指す経路（中身は経路であり鍵本体ではない）
FILE /home/ubuntu/.tunnel_to_philip size=44
POINTS_TO=/home/ubuntu/.ssh/id_ed25519_bengiotophilip

$ 別の探し方（先頭ドットを落とさない）
/home/ubuntu/.tunnel.log
/home/ubuntu/.tunnel_to_philip
```

### Step 2: 鍵の実在と指紋

```
-rw------- 1 ubuntu ubuntu 399  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_bengiotophilip
-rw-r--r-- 1 ubuntu ubuntu 95  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_bengiotophilip.pub
256 SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE ubuntu@Bengio (ED25519)
```

### Step 3: 手元にある鍵を集合として列挙

```
$ ls -la ~/.ssh/
total 76
drwx------ 3 ubuntu ubuntu 4096  7月  3 23:36 .
drwxr-x--- 1 ubuntu ubuntu 4096  8月 12 11:34 ..
drwxrwxr-x 4 ubuntu ubuntu 4096  5月 22 10:32 .remember
-rw-rw-r-- 1 ubuntu ubuntu 2227  6月 21 16:23 authorized_keys
-rw------- 1 ubuntu ubuntu  432  5月 22 10:32 bengiotoGithub
-rw-r--r-- 1 ubuntu ubuntu  117  5月 22 10:32 bengiotoGithub.pub
-rw------- 1 ubuntu ubuntu  373  6月 22 10:49 config
-rw------- 1 ubuntu ubuntu  399  7月  3 23:36 id_ed25519_bengiotophilip
-rw-r--r-- 1 ubuntu ubuntu   95  7月  3 23:36 id_ed25519_bengiotophilip.pub
-rw------- 1 ubuntu ubuntu  399  6月 20 17:55 id_ed25519_github
-rw-r--r-- 1 ubuntu ubuntu   94  6月 20 17:55 id_ed25519_github.pub
-rw------- 1 ubuntu ubuntu  399  6月 22 10:44 id_rsa_bengiotolecun
-rw-r--r-- 1 ubuntu ubuntu   95  6月 22 10:44 id_rsa_bengiotolecun.pub
-rw------- 1 ubuntu ubuntu  411  5月 24 16:38 id_rsa_bengiotophilip
-rw-r--r-- 1 ubuntu ubuntu   96  5月 24 16:38 id_rsa_bengiotophilip.pub
-rw-rw-r-- 1 ubuntu ubuntu  746  5月  9 04:09 id_rsa_mactobengio.pub
-rw------- 1 ubuntu ubuntu 4054  6月 22 10:45 known_hosts
-rw------- 1 ubuntu ubuntu 3218  6月 22 10:45 known_hosts.old

$ 公開鍵すべての指紋
256 SHA256:qNDPs2683f8X3NvfXmIsWbH/FYaLaskRs9uAkFbE+Bw daky.o7600@gmail.com bengiotoGithub (ED25519)
  ^ /home/ubuntu/.ssh/bengiotoGithub.pub
256 SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE ubuntu@Bengio (ED25519)
  ^ /home/ubuntu/.ssh/id_ed25519_bengiotophilip.pub
256 SHA256:yvG5eGkXvCnyD4FgOXtWBMn0gfV3aAISAhCvFh5VvWo ubuntu@lecun (ED25519)
  ^ /home/ubuntu/.ssh/id_ed25519_github.pub
256 SHA256:MKli4Hqp8sYzekheqdjEYKJiYALrCkJqSKGZzZ+VY58 bengiotolecun (ED25519)
  ^ /home/ubuntu/.ssh/id_rsa_bengiotolecun.pub
256 SHA256:pgaKMBqJNKERWNvzUAeYZi9PsQv9gb/ZF1hLTWE6PsU bengiotophilip (ED25519)
  ^ /home/ubuntu/.ssh/id_rsa_bengiotophilip.pub
4096 SHA256:Vrh/uPWK0qwR5eV9Ywtm+tFajl8S/quBOAL+CZWfXrw dakyo-mba@dmba.local (RSA)
  ^ /home/ubuntu/.ssh/id_rsa_mactobengio.pub
公開鍵の件数: 6

$ 別の探し方: 秘密鍵側から導出して突き合わせる
256 SHA256:qNDPs2683f8X3NvfXmIsWbH/FYaLaskRs9uAkFbE+Bw daky.o7600@gmail.com bengiotoGithub (ED25519)
  ^ /home/ubuntu/.ssh/bengiotoGithub
256 SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE ubuntu@Bengio (ED25519)
  ^ /home/ubuntu/.ssh/id_ed25519_bengiotophilip
256 SHA256:yvG5eGkXvCnyD4FgOXtWBMn0gfV3aAISAhCvFh5VvWo ubuntu@lecun (ED25519)
  ^ /home/ubuntu/.ssh/id_ed25519_github
256 SHA256:MKli4Hqp8sYzekheqdjEYKJiYALrCkJqSKGZzZ+VY58 bengiotolecun (ED25519)
  ^ /home/ubuntu/.ssh/id_rsa_bengiotolecun
256 SHA256:pgaKMBqJNKERWNvzUAeYZi9PsQv9gb/ZF1hLTWE6PsU bengiotophilip (ED25519)
  ^ /home/ubuntu/.ssh/id_rsa_bengiotophilip
秘密鍵から導出できた件数: 5
```

## Task 2 自ホストが受け入れる側として登録しているもの

### Step 1: 受け入れの一覧

```
FILE /home/ubuntu/.ssh/authorized_keys lines=3
-rw-rw-r-- 1 ubuntu ubuntu 2227  6月 21 16:23 /home/ubuntu/.ssh/authorized_keys

$ 別の場所を指す設定がないか
#Port 22
#PermitRootLogin prohibit-password
#AuthorizedKeysFile	.ssh/authorized_keys .ssh/authorized_keys2
# the setting of "PermitRootLogin without-password".
#GatewayPorts no
```

sshd の設定は該当行がすべて番号記号で始まる既定値のままである。
受け入れの場所は既定の .ssh/authorized_keys と .ssh/authorized_keys2 で、後者は存在しない。

### Step 2: 登録されている鍵の指紋

```
4096 SHA256:Vrh/uPWK0qwR5eV9Ywtm+tFajl8S/quBOAL+CZWfXrw dakyo-mba@dmba.local (RSA)
4096 SHA256:438go0wAQ1G7lk9DqMj4+45U+1bhEm5XJ2068TeCi8w philip-to-bengio (RSA)
4096 SHA256:xkvYaIjppz1ZQflZSM+oPOpkNEkCNlujjAGREQOdkaU lecuntobengio (RSA)
count=3
```

### Step 3: 中継の鍵が自ホストに登録されているかの照合

```
中継の鍵の指紋: SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE
authorized_keys 内の一致件数: 0

$ 陽性対照（実在する別の指紋で同じ照合）
philip-to-bengio の指紋で照合: 1 件
lecuntobengio の指紋で照合  : 1 件
```

照合の結果は 0、陽性対照は 1 を返す。**照合機構は健全であり、0 は本物の不在である。**

**ただしこの検査は、SPEC が主張する問いに答えていない。**
中継の鍵 id_ed25519_bengiotophilip はコメントが ubuntu@Bengio であり、
**bengio 自身が philip へ出て行くための鍵**である。それが bengio の受け入れ一覧に
あるかは「bengio が自分自身へ入れるか」を測っているにすぎない。
「bengio が中心になれるか」を決めるのは**他ノードの鍵が bengio に登録されているか**である。

```
$ 別の探し方: 手元の鍵と受け入れ一覧を集合として突き合わせる
手元の公開鍵の指紋数 : 6
受け入れ一覧の指紋数 : 3
両方に現れる指紋の数 : 1
   手元= ['id_rsa_mactobengio.pub']  受け入れ= dakyo-mba@dmba.local

受け入れ一覧にあるが手元に秘密鍵が無いもの（他ノード由来）:
    philip-to-bengio
    lecuntobengio
```

**受け入れ 3 件のうち遠隔ノード由来は philip-to-bengio と lecuntobengio の 2 件のみ。**
残る 1 件は dakyo-mba@dmba.local で、手元に公開鍵の写しがある外部の機械である。
**他の 8 台は bengio に鍵を登録していない。**

### Step 4: 自ホストの住所

```
$ ip コマンドは存在しない。/proc/net/fib_trie から読む
fib_trie 由来の /32: ['127.0.0.1', '172.17.0.15']

$ 外向き経路で使われる自分の住所
172.17.0.15
hostname: Bengio

$ /etc/hosts
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
ff00::0	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.15	Bengio
```

自ホストは容器の内側の 172.17.0.15 のみを持つ。他ノードは 192.168.196.x 帯にある。
**bengio がその帯からどの住所で見えるかは自分では測れない。UNKNOWN とする。**

## Task 3 他の九台へ認証が通るか

### Step 1: 対象一覧（三つの出所の和集合）

```
$ ~/.ssh/config
Host github.com
    HostName github.com
    IdentityFile ~/.ssh/bengiotoGithub
Host philip
    HostName 192.168.196.150
    IdentityFile /home/ubuntu/.ssh/id_rsa_bengiotophilip
    Port 50072
Host lecun
  HostName 192.168.196.176
  Port 50072
  IdentityFile ~/.ssh/id_rsa_bengiotolecun
ssh_count=3

$ 和集合
127.0.0.1 etc_hosts
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
和集合の件数=12
遠隔の件数=10（自ホスト込みで 11 台。既知の構成 11 台と一致）
```

**~/.ssh/config は philip に id_rsa_bengiotophilip を指定しているが、
中継が使う鍵は id_ed25519_bengiotophilip であり別物である。** 本 Task は後者で測る。

### Step 2: 認証の実測（実行した命令は echo だけ）

禁止 2 は ~/.ssh の変更を禁じるが、SPEC の命令にある StrictHostKeyChecking=accept-new は
未知のホスト鍵を ~/.ssh/known_hosts へ書き込む。**意図（対話的な問い合わせで止まらない）を
保ちつつ禁止を守るため、UserKnownHostsFile を /tmp 側へ向けた。**

```
192.168.196.54	dlsta	ubuntu@192.168.196.54: Permission denied (publickey,password). 
192.168.196.58	adam	ubuntu@192.168.196.58: Permission denied (publickey,password). 
192.168.196.63	ilya	ubuntu@192.168.196.63: Permission denied (publickey,password). 
192.168.196.78	hinton	ubuntu@192.168.196.78: Permission denied (publickey,password). 
192.168.196.106	he	ubuntu@192.168.196.106: Permission denied (publickey,password). 
192.168.196.143	ian	ubuntu@192.168.196.143: Permission denied (publickey,password). 
192.168.196.150	philip,ssh_config	ssh: connect to host 192.168.196.150 port 50072: No route to host 
192.168.196.176	lecun,ssh_config	ubuntu@192.168.196.176: Permission denied (publickey,password). 
192.168.196.190	andrew	ubuntu@192.168.196.190: Permission denied (publickey,password). 
192.168.196.227	efros	ubuntu@192.168.196.227: Permission denied (publickey,password). 
total=10
```

### Step 3: 集計

```
AUTH_OK=0
DENIED=9
NOCONN=1
total_lines=10
未分類の行=なし  合計 10 = 対象数 10
```

| 分類 | 件数 | 意味 |
|---|---|---|
| AUTH_OK | 0 | 中継の鍵で入れるホストは**一台も無い** |
| DENIED | 9 | 口は開いているが**鍵が通らない**。登録の追加が要る |
| NOCONN | 1 | philip のみ。No route to host（前契約と一致） |

### Step 4: 陰性対照

```
$ 通らないはずの鍵（/dev/null）を、口が開いていた住所へ
ubuntu@192.168.196.176: Permission denied (publickey,password).
```

**REACHABLE は返らない。期待どおりである。**

### 追加の確認: 拒否が「提示したうえでの拒否」であること

陰性対照と本測定が同じ文言を返すため、鍵が実際に提示されているかを詳細出力で分けた。

```
$ 中継の鍵を指定した場合
debug1: Will attempt key: /home/ubuntu/.ssh/id_ed25519_bengiotophilip ED25519 SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE explicit
debug1: Offering public key: /home/ubuntu/.ssh/id_ed25519_bengiotophilip ED25519 SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE explicit
debug1: Authentications that can continue: publickey,password
debug1: No more authentication methods to try.

$ /dev/null を指定した場合
debug1: Will attempt key: /dev/null  explicit
debug1: Trying private key: /dev/null
debug1: No more authentication methods to try.
```

**実鍵は Offering まで到達してサーバに拒否されている。** /dev/null は提示にすら至らない。
したがって 9 台の Permission denied は「鍵を提示したうえでの拒否」であり、
「鍵を提示していないための拒否」ではない。**測定は健全である。**

### 禁止 2 の確認

```
実行前: 50a529d298ef93ce… 4054 bytes mtime=2026-06-22 10:45:33  known_hosts
        40c2c29852990447… 3218 bytes mtime=2026-06-22 10:45:33  known_hosts.old
実行後: 50a529d298ef93ce… 4054 bytes mtime=2026-06-22 10 known_hosts
実行後: 40c2c29852990447… 3218 bytes mtime=2026-06-22 10 known_hosts.old
```

**要約値も更新時刻も不変。~/.ssh は変更していない。**

**一致 13 件はすべて名前であり値ではない。** 内訳は次のとおり。

| 箇所 | 実体 |
|---|---|
| 97, 99 行 | sshd_config の既定コメント（PermitRootLogin prohibit-password） |
| 219-228, 252, 265 行 | SSH が返した認証方式の名前 publickey,password。拒否を示す文言 |
| private 1 件 | Trying private key という経路の説明。鍵の中身ではない |

```
BEGIN で始まる行            : 0
base64 の長い連続（60 文字超）: 0
公開鍵本体（AAAAB3/AAAAC3） : 0
```

**値の混入は 0 件である。**

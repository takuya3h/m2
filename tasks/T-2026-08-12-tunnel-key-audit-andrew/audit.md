# audit — T-2026-08-12-tunnel-key-audit-andrew

実行ホスト: `Andrew`（`socket.gethostname()` の実測値。SPEC 本文の宣言は `andrew`）
repo: `/home/ubuntu/slocal2/m2`  分岐: `exp/andrew`

出力は要約せずそのまま貼る（申し送り 8）。
**秘密鍵の中身は一切含まない。指紋と経路名のみ。**

---

## Task 1 中継に使われている鍵の特定

### Step 1 中継の目印を集合として列挙し、指す経路を読む

    ls -a ~/ | grep -i tunnel
    .tunnel.log
    .tunnel_to_philip
    count=2

    for f in ~/.tunnel_to_*; do ... done
    FILE /home/ubuntu/.tunnel_to_philip size=44
    POINTS_TO=/home/ubuntu/.ssh/id_ed25519_andrewtophilip

目印は 2 件（うち経路を指すものは `.tunnel_to_philip` の 1 件、他方は記録ファイル）。
中身は 44 バイトで、**秘密鍵そのものではなく経路**であった。実装のコメント
（`keeper.sh:13` の「中身=秘密鍵パス」）と一致する。

以降 `KEY=/home/ubuntu/.ssh/id_ed25519_andrewtophilip` とする。

### Step 2 その鍵が実在するか、種別と指紋

    ls -la "${KEY}"
    -rw------- 1 ubuntu ubuntu 399  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_andrewtophilip
    ls -la "${KEY}.pub"
    -rw-r--r-- 1 ubuntu ubuntu 95  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_andrewtophilip.pub

    ssh-keygen -lf "${KEY}.pub"
    256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)

鍵は実在する。種別 ED25519（256）、権限 `600`、公開鍵が並置されている。
`ssh-keygen -yf` による導出は不要だったため実行していない。
**`-----BEGIN` で始まる行は一度も出力していない。**

以降 `FP=SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` とする。

### Step 3 手元にある鍵を集合として列挙する（名前を決め打ちしない）

    ls -la ~/.ssh/
    total 60
    drwx------ 2 ubuntu ubuntu 4096  7月 13 08:26 .
    drwxr-x--- 1 ubuntu ubuntu 4096  8月 12 11:33 ..
    -rw-rw-r-- 1 ubuntu ubuntu  668  7月  3 20:22 authorized_keys
    -rw------- 1 ubuntu ubuntu  229  7月 13 08:26 config
    -rw------- 1 ubuntu ubuntu  399  7月 13 07:03 id_Andrewdeploy
    -rw-r--r-- 1 ubuntu ubuntu   95  7月 13 07:03 id_Andrewdeploy.pub
    -rw------- 1 ubuntu ubuntu  399  7月  3 23:36 id_ed25519_andrewtophilip
    -rw-r--r-- 1 ubuntu ubuntu   95  7月  3 23:36 id_ed25519_andrewtophilip.pub
    -rw------- 1 ubuntu ubuntu  399  7月  3 00:42 id_ed25519_github
    -rw-r--r-- 1 ubuntu ubuntu   95  7月  3 00:42 id_ed25519_github.pub
    -rw------- 1 ubuntu ubuntu 2602  7月  3 00:20 id_rsa_andrewtophilip
    -rw-r--r-- 1 ubuntu ubuntu  567  7月  3 00:20 id_rsa_andrewtophilip.pub
    -rw------- 1 ubuntu ubuntu 1956  7月  3 00:47 known_hosts
    -rw------- 1 ubuntu ubuntu 1120  7月  3 00:45 known_hosts.old

公開鍵の指紋（全 4 件。名前を決め打ちせず `*.pub` を総当たり）:

    256  SHA256:dvnHdaFxvmC+scQO2cuXk+quEHNuw3uqeqIQjnUzkO8 deploy-Andrew (ED25519)
      ^ /home/ubuntu/.ssh/id_Andrewdeploy.pub
    256  SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
      ^ /home/ubuntu/.ssh/id_ed25519_andrewtophilip.pub
    256  SHA256:zcSWxJOCKZZNmnZMv9N6FZkKwb/2BozprdV+hvdtIdk ubuntu@andrew (ED25519)
      ^ /home/ubuntu/.ssh/id_ed25519_github.pub
    3072 SHA256:DIwYkcsX+tHAXs3ZG9P+mbI4Cl6Vq5kq0ipcAtNAg0o ubuntu@Andrew (RSA)
      ^ /home/ubuntu/.ssh/id_rsa_andrewtophilip.pub

秘密鍵は 4 件、公開鍵は 4 件で対応している。**中継に使われているのは 2 番目
（`id_ed25519_andrewtophilip`）である。** 同じ宛先を指す RSA 版
（`id_rsa_andrewtophilip`、7月3 00:20）も残っているが、目印が指しているのは
ED25519 版（7月3 23:36）であり、こちらが後から作られている。

### 完了判定（Task 1）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 1 | 中継の目印を集合として列挙した | 2 件（`.tunnel.log` / `.tunnel_to_philip`）。経路を指すのは後者のみで `POINTS_TO=/home/ubuntu/.ssh/id_ed25519_andrewtophilip` |
| 2 | 鍵の実在と指紋を測った | 実在する（ED25519 256、権限 600、公開鍵並置）。`FP=SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` |
| 3 | 手元の公開鍵を集合として列挙した | 4 件（deploy-Andrew / ubuntu@Andrew ED25519 / ubuntu@andrew / ubuntu@Andrew RSA）。指紋は上記 |
| 4 | 記録に鍵の値が含まれない | Task 1 Step 4 として末尾に検査結果を記す |

---

## Task 2 自ホストが受け入れる側として何を登録しているか

### Step 1 受け入れの一覧を集合として探す

    for f in ~/.ssh/authorized_keys ~/.ssh/authorized_keys2; do ... done
    FILE /home/ubuntu/.ssh/authorized_keys lines=2

    ls -la ~/.ssh/authorized_keys*
    -rw-rw-r-- 1 ubuntu ubuntu 668  7月  3 20:22 /home/ubuntu/.ssh/authorized_keys

`authorized_keys2` は存在しない。存在するのは `authorized_keys` の 1 件・2 行。

別の場所を指す設定が無いことの確認:

    grep -i -E "AuthorizedKeysFile|Port|PermitRootLogin" /etc/ssh/sshd_config
    #Port 22
    #PermitRootLogin prohibit-password
    #AuthorizedKeysFile	.ssh/authorized_keys .ssh/authorized_keys2
    # the setting of "PermitRootLogin without-password".
    #GatewayPorts no

**該当行はすべて注釈である。** すなわち既定値が効いており、参照先は
`.ssh/authorized_keys` と `.ssh/authorized_keys2` の 2 つ。別の場所を指していない。
`Port` も注釈のため sshd は 22 で待ち受けており、外から見える `50072` は
容器の外側での対応付けであると読める（**内側からは確かめられないため UNKNOWN**）。

### Step 2 登録されている鍵の指紋

    ssh-keygen -lf ~/.ssh/authorized_keys | tee /tmp/authfp.txt
    3072 SHA256:NtZ4KlVTRANofdQ8ZRbAga9Gh1jOov1nqNJqJhZBQXk ubuntu@aolab (RSA)
    256  SHA256:rpVfpsVCGe3sHKUVx06VczkyEcMTFdqZ9P5ipvi+Ip8 dakyo-mba@dmba.local (ED25519)
    count=2

**登録は 2 件のみ。** 註釈欄は `ubuntu@aolab` と `dakyo-mba@dmba.local` である。
前契約で `hostname` が `aolab` を返すのは `philip` と `ilya` の 2 台であると分かっている
（本ホストからはどちらかを判別できない。**UNKNOWN**）。
`dakyo-mba@dmba.local` は構成十一台のいずれとも名前が一致せず、手元の機器と読める。

### Step 3 中継の鍵が自ホストに登録されているかの照合

    grep -c -F "${FP}" /tmp/authfp.txt
    0

**一致は 0。中継に使われている鍵は、自ホストの受け入れ一覧に無い。**

陽性対照（照合が常に零を返す壊れ方をしていないこと）:

    実在する指紋 SHA256:NtZ4KlVTRANofdQ8ZRbAga9Gh1jOov1nqNJqJhZBQXk  ->  1
    実在する指紋 SHA256:rpVfpsVCGe3sHKUVx06VczkyEcMTFdqZ9P5ipvi+Ip8  ->  1

**照合は働いている。** 零は道具の欠陥ではない。

手元の 4 鍵それぞれについて同じ照合を行った結果（別の探し方による零の再確認）:

    0  SHA256:dvnHdaFxvmC+scQO2cuXk+quEHNuw3uqeqIQjnUzkO8   (deploy-Andrew)
    0  SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k   (中継鍵)
    0  SHA256:zcSWxJOCKZZNmnZMv9N6FZkKwb/2BozprdV+hvdtIdk   (github 用)
    0  SHA256:DIwYkcsX+tHAXs3ZG9P+mbI4Cl6Vq5kq0ipcAtNAg0o   (RSA 版)

**自ホストの鍵はどれも自ホストの受け入れ一覧に無い**（自分自身へ入る必要が無いので当然）。
登録されている 2 件は、いずれも手元の 4 鍵とは別物である。

### Step 4 自ホストが外からどの住所で見えるか

    ip -4 addr show   ->  ip コマンドなし

代替として経路表から読んだ:

    cat /proc/net/fib_trie | grep -A1 "32 host" | head -20
                  /32 host LOCAL
            |-- 127.255.255.255
    --
                  /32 host LOCAL
            |-- 172.17.255.255
    --
                  /32 host LOCAL
            |-- 127.255.255.255
    --
                  /32 host LOCAL
            |-- 172.17.255.255

    grep -v "^#" /etc/hosts | grep -v "^$"
    127.0.0.1	localhost
    ::1	localhost ip6-localhost ip6-loopback
    fe00::0	ip6-localnet
    ff00::0	ip6-mcastprefix
    ff02::1	ip6-allnodes
    ff02::2	ip6-allrouters
    172.17.0.26	Andrew

自ホストが持つ帯は **`127.0.0.0/8`（環回）と `172.17.0.0/16`（容器の橋）のみ**。
`/etc/hosts` によれば自ホストの住所は `172.17.0.26`。
**`192.168.196.0/24` の住所は持たない。**

**他ノードから自ホストがどの住所で見えるかは自分では測れない（UNKNOWN）。**
外側での対応付け（どの `192.168.196.x` の `50072` が本容器へ転送されるか）は
容器の内側からは観測できない。

### 完了判定（Task 2）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 5 | 受け入れの一覧を集合として探した | `~/.ssh/authorized_keys` の 1 件・**2 行**。`authorized_keys2` は不在。`sshd_config` の該当行はすべて注釈で、参照先は既定のまま |
| 6 | 登録されている指紋を列挙した | **2 件**（`ubuntu@aolab` RSA 3072 / `dakyo-mba@dmba.local` ED25519） |
| 7 | 中継の鍵が自ホストに登録されているかを照合した | **0 件**。陽性対照は実在する 2 指紋でいずれも **1**。手元 4 鍵すべてでも 0 |
| 8 | 自ホストの住所を測った | `172.17.0.26`（容器の橋）。帯は `127.0.0.0/8` と `172.17.0.0/16` のみ。`192.168.196.0/24` は持たない。**外からどう見えるかは UNKNOWN** |

---

## Task 3 他の九台へ実際に認証が通るか

### 実行前の判断（SPEC の命令と禁止 2 の矛盾）

SPEC Task 3 Step 2 は `-o StrictHostKeyChecking=accept-new` を指定するが、これは未知の
宛先の公開鍵を `~/.ssh/known_hosts` へ**書き込む**。禁止 2 は `~/.ssh/**` の変更を禁じている。
実際に書き込みが発生するかを事前に測った。

    ssh-keygen -F "[192.168.196.54]:50072"  -> 未知（accept-new なら書き込みが発生する）
    ssh-keygen -F "[192.168.196.150]:50072" -> 既知
    ssh-keygen -F "[192.168.196.227]:50072" -> 未知（accept-new なら書き込みが発生する）

十台のうち既知は `philip` のみで、残りは未知である。**指示どおりなら禁止 2 に触れる。**
そこで書き込みの起きない等価な指定に替えた。

    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null

無変更であることを前後の要約値で示す。

    測定前  sha256(先頭16)=66ecff7020e05c5b  mtime 7月3 00:47  size 1956
    測定後  sha256(先頭16)=66ecff7020e05c5b  mtime 7月3 00:47  size 1956

### Step 1 対象の一覧を三つの出所から集める

**出所1 `~/.ssh/config`**（`ssh_count=2`）

    Host philip
        HostName 192.168.196.150
        Port 50072
        IdentityFile ~/.ssh/id_rsa_andrewtophilip
    Host github.com
      HostName github.com
      IdentityFile ~/.ssh/id_ed25519_github

**注記**: `Host philip` の `IdentityFile` は **RSA 版**（`id_rsa_andrewtophilip`）を指しており、
中継の目印が指す **ED25519 版**（`id_ed25519_andrewtophilip`）と異なる。常駐処理は
別名を経由せず住所へ直接つなぎ `-i "$(cat ~/.tunnel_to_philip)"` を明示するため
（`keeper.sh:16`）、**実際に中継で使われるのは ED25519 版である。**
この食い違いは本契約の測定結果を左右しないが、事実として記録する。

**出所2 `/etc/hosts`**（`hosts_lines=7`）

    127.0.0.1	localhost
    ::1	localhost ip6-localhost ip6-loopback
    fe00::0	ip6-localnet
    ff00::0	ip6-mcastprefix
    ff02::1	ip6-allnodes
    ff02::2	ip6-allrouters
    172.17.0.26	Andrew

**出所3 同期処理の設定**（`stcfg_count=11`）

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

**和集合と件数**: 構内の他ホスト **10 台** + 自ホスト（`172.17.0.26`）= **11 台**。
既知の構成十一台と一致し、**一覧は縮んでいない。**
`127.0.0.1:22001` は自ホスト内の中継入口、`github.com` は構外のため認証の対象から外した。

### Step 2 認証を測る（実行する命令は `echo` だけ）

鍵は中継の目印が指す `KEY=/home/ubuntu/.ssh/id_ed25519_andrewtophilip`。
結果は一件ずつファイルへ書き、あとで別命令で表示した。

    192.168.196.54 :: ubuntu@192.168.196.54: Permission denied (publickey,password).
    192.168.196.58 :: ubuntu@192.168.196.58: Permission denied (publickey,password).
    192.168.196.63 :: ubuntu@192.168.196.63: Permission denied (publickey,password).
    192.168.196.78 :: ubuntu@192.168.196.78: Permission denied (publickey,password).
    192.168.196.105 :: ubuntu@192.168.196.105: Permission denied (publickey,password).
    192.168.196.106 :: ubuntu@192.168.196.106: Permission denied (publickey,password).
    192.168.196.143 :: ubuntu@192.168.196.143: Permission denied (publickey,password).
    192.168.196.150 :: ssh: connect to host 192.168.196.150 port 50072: No route to host
    192.168.196.176 :: ubuntu@192.168.196.176: Permission denied (publickey,password).
    192.168.196.227 :: ubuntu@192.168.196.227: Permission denied (publickey,password).

対話的な問い合わせは一度も出ていない（`BatchMode=yes`）。

### Step 3 三分類の集計と照合

    AUTH_OK=0
    DENIED=9
    NOCONN=1
    total_lines=10
    AUTH_OK+DENIED+NOCONN = 10 / total = 10 -> 一致

**分類から漏れた行は無い。**

`AUTH_OK=0` の別の探し方による再確認:

    行末以外も含めた REACHABLE の出現              = 0
    成功を示す語（Welcome / Last login）の出現     = 0

### 結果の読み方（認証の失敗と接続の失敗の区別）

| 分類 | 件数 | 意味 | 該当 |
|---|---:|---|---|
| 認証が通る | **0** | 中継を張れる | なし |
| `Permission denied (publickey,password)` | **9** | 口は開いており相手の sshd まで届いているが、**鍵が通らない** | 9 台 |
| 接続そのものが失敗 | **1** | 経路の問題 | `192.168.196.150`（philip、`No route to host`） |

**九台は「届くが鍵が通らない」。** 前契約で測った口の開閉（`50072` が `OPEN`）と整合する。
口が開いていることと鍵が通ることは別であり、**本契約でその差が確定した。**

### Step 4 陽性対照（通らないはずの鍵で通らないこと）

到達できた住所 `192.168.196.54` に対して二通りを与えた。

    (a) 空の鍵 /dev/null                        -> ubuntu@192.168.196.54: Permission denied (publickey,password).
    (b) 用途の違う実在の鍵（github 用 ED25519） -> ubuntu@192.168.196.54: Permission denied (publickey,password).

**いずれも `REACHABLE` を返さない。** 鍵が効いていないまま通ってしまう壊れ方はしていない。

**測定の限界（正直に記す）**: 通らないはずの鍵も、中継の鍵と**同じ文言**で拒否される。
したがって本測定が示せるのは「誤った鍵が誤って通ることはない」ことまでである。
**正しい鍵なら `REACHABLE` が返る、という向きの対照は取れていない。** 唯一の
実績のある宛先（philip）が経路の消失により到達できないためである。
この向きの確認は **UNKNOWN** とする。

### 完了判定（Task 3）

| # | 完了判定 | 実測 |
|:--:|---|---|
| 9 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config` 2 件 / `/etc/hosts` 7 行 / 同期設定 11 アドレス -> 構内 10 台 + 自ホスト = **11 台**。既知の構成と一致 |
| 10 | 全対象で認証を測り合計が一致した | 10 対象を測定、`0+9+1=10=total` で**一致** |
| 11 | 認証の可否と接続の可否を区別した | 認証成功 **0** / 鍵が通らない **9** / 接続失敗 **1**（philip のみ） |
| 12 | 通らないはずの鍵で通らないことを確かめた | `/dev/null` と github 用鍵の 2 通りとも `Permission denied`。`REACHABLE` は返らず。**ただし正方向の対照は取れず UNKNOWN** |

---

## Task 1 Step 4 記録に鍵の値が含まれないことの検査

    grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" audit.md
    2

該当行の実体（**値ではなく名前・説明文**）:

    108:    #PermitRootLogin prohibit-password
    110:    # the setting of "PermitRootLogin without-password".

いずれも Task 2 Step 1 で貼った `sshd_config` の**注釈行**であり、`password` という語が
設定項目名の一部として現れているだけである。**鍵の値・資格情報の値は含まれていない。**
SPEC の指示（値の混入と名前の一致を分けて判定する）に従い、削らずに残す。

鍵の中身に由来する一致は **0 件**。`-----BEGIN` で始まる行は記録中に存在しない。

陽性対照（検査が空振りでないこと。囮は外部へ送らない）:

    printf -- '-----BEGIN OPENSSH PRIVATE KEY-----\n' > /tmp/decoy_key.txt
    grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" /tmp/decoy_key.txt
    1

**検査は働いている。** 囮は測定後に削除した。

### G1 の判定

| 条件 | 実測 |
|---|---|
| 指紋の照合が空振りでないことを、実在する別の指紋で確かめた | 実在指紋 -> **1**、存在しない指紋 -> **0**。識別している |
| 秘匿の検査が働くことを、鍵の書き出しを模した囮で確かめた | 囮 -> **1**、記録本体の値由来 -> **0** |

**G1 通過。**

### G2 の判定

| 条件 | 実測 |
|---|---|
| 認証が通らないはずの鍵を与えて、実際に通らないことを確かめた | `/dev/null` と github 用鍵の 2 通りとも `Permission denied`。`REACHABLE` は返らず |
| 対象一覧を複数の出所から集め、件数を記録し、測定件数が対象数と一致することを確かめた | 3 出所から 11 台（構内 10 + 自ホスト）。測定 10 対象で `0+9+1=10=total` |

**G2 通過。**

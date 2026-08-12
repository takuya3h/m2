# audit — 中継の鍵の配布状況の実測（lecun）

**task_id:** `T-2026-08-12-tunnel-key-audit-lecun`  **実行ホスト:** `lecun`
**実行日:** 2026-08-12  **読み取りのみ。鍵の生成・配布・変更は行っていない。**

出力は要約せずそのまま貼る（注意 8）。**秘密鍵の中身はどこにも含まない。**
指紋（`SHA256:` で始まる値）は公開鍵の要約であり秘匿ではない。
**基本多言語面の外の文字と四十桁の十六進は使わない**（送信側の道具の欠陥を避けるため）。

---

## 前提の確認

    抑止の目印: あり（make task-start が設置）
    grep -c sync-pause ~/bin/m2-sync.sh -> 2

**二つ目の値が 0 でないため抑止は効いている。** 常駐処理は分岐へ書き込まない。

    conventions_rev の実測: d422b08   （spec.yaml の記載と一致。置換不要）

`inputs.data` と `split_files` は雛形の必須項目として残っているが、
**本契約はいずれの Task でもデータも分割も参照していない。**
`no_split_redefine` `no_raw_write` `no_frozen_change` も成立しようがない。
**参照しなかったことを記録する。**

---

## Task 1 中継に使われている鍵の特定

### Step 1 中継の目印を集合として列挙

    .tunnel.log
    .tunnel_to_philip
    count=2

先頭がドットのものを落とさない別の探し方でも同じ件数（注意 7）。

    find ~/ -maxdepth 1 -name '*tunnel*' -> 2 件
    /home/ubuntu/.tunnel.log
    /home/ubuntu/.tunnel_to_philip

**目印は `.tunnel_to_philip` の一件だけである。** `.tunnel_to_<他のホスト>` は存在しない。

**中身を印字する前に、それが経路であって鍵の中身でないことを確かめた。**
印字は取り消せないため、種別の判定を先に行った。

    FILE /home/ubuntu/.tunnel_to_philip size=43 lines=1 BEGIN行=0

一行・43 バイト・`-----BEGIN` を含まない。経路として整合する（鍵の中身なら数百バイト以上で
`BEGIN` 行を持つ）。**判定してから印字した。**

    FILE /home/ubuntu/.tunnel_to_philip size=43
    POINTS_TO=/home/ubuntu/.ssh/id_ed25519_lecuntophilip

### Step 2 鍵の実在と種別と指紋

    KEY=/home/ubuntu/.ssh/id_ed25519_lecuntophilip
    -rw------- 1 ubuntu ubuntu 399  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_lecuntophilip
    -rw-r--r-- 1 ubuntu ubuntu 94  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_lecuntophilip.pub

    256 SHA256:dL4qKLl4pYnZpvnVL3kRlipacdq7ipqTpxExhCJqRr8 ubuntu@lecun (ED25519)

    鍵の中身の BEGIN 行の件数: 1   （件数のみ。中身は印字していない）

| 項目 | 実測 |
|---|---|
| 秘密鍵 | `~/.ssh/id_ed25519_lecuntophilip`（399 バイト、権限 600、2026-07-03 23:36） |
| 公開鍵 | 並置あり（94 バイト、権限 644） |
| 種別 | ED25519、256 ビット |
| 指紋 | `SHA256:dL4qKLl4pYnZpvnVL3kRlipacdq7ipqTpxExhCJqRr8` |
| 註釈 | `ubuntu@lecun` |

**鍵の名前が `lecuntophilip` である。** 名前の上では lecun から philip 専用に作られている。
名前は用途の宣言であって、どこで受け入れられるかを決めるものではない（Task 3 で実測する）。

### Step 3 手元にある鍵を集合として列挙

`~/.ssh/` の一覧:

    drwx------ 3 ubuntu ubuntu 4096  7月 22 08:23 .
    drwx------ 4 ubuntu ubuntu 4096  6月 21 16:20 .remember
    -rw-rw-r-- 1 ubuntu ubuntu 1504  7月 29 17:33 authorized_keys
    -rw------- 1 ubuntu ubuntu  475  7月  1 09:11 config
    -rw------- 1 ubuntu ubuntu  399  6月 14 18:36 id_ed25519_github
    -rw-r--r-- 1 ubuntu ubuntu   94  6月 14 18:36 id_ed25519_github.pub
    -rw------- 1 ubuntu ubuntu  399  7月  3 23:36 id_ed25519_lecuntophilip
    -rw-r--r-- 1 ubuntu ubuntu   94  7月  3 23:36 id_ed25519_lecuntophilip.pub
    -rw------- 1 ubuntu ubuntu  399  7月 22 08:23 id_lecundeploy
    -rw-r--r-- 1 ubuntu ubuntu   94  7月 22 08:23 id_lecundeploy.pub
    -rw------- 1 ubuntu ubuntu 3381  6月 21 16:21 id_rsa_lecuntobengio
    -rw-r--r-- 1 ubuntu ubuntu  739  6月 21 16:21 id_rsa_lecuntobengio.pub
    -rw------- 1 ubuntu ubuntu 2602  7月  1 09:09 id_rsa_lecuntoefros
    -rw-r--r-- 1 ubuntu ubuntu  566  7月  1 09:09 id_rsa_lecuntoefros.pub
    -rw------- 1 ubuntu ubuntu 2602  7月  1 02:31 id_rsa_lecuntophilip
    -rw-r--r-- 1 ubuntu ubuntu  566  7月  1 02:31 id_rsa_lecuntophilip.pub
    -rw------- 1 ubuntu ubuntu 5032  7月  1 09:11 known_hosts
    -rw------- 1 ubuntu ubuntu 4196  7月  1 09:11 known_hosts.old

公開鍵の指紋（**特定の名前を探していない。見つかったものすべて**）:

    256 SHA256://dnKA2FpWTwcgBv3ir62nnpzED3xPUn24uge9vPLw4 ubuntu@lecun (ED25519)
      /home/ubuntu/.ssh/id_ed25519_github.pub
    256 SHA256:dL4qKLl4pYnZpvnVL3kRlipacdq7ipqTpxExhCJqRr8 ubuntu@lecun (ED25519)
      /home/ubuntu/.ssh/id_ed25519_lecuntophilip.pub
    256 SHA256:PK9k6A98J/Ma2nYvoNPPWbaKg9tuRjtqsc3CdVwir/s deploy-lecun (ED25519)
      /home/ubuntu/.ssh/id_lecundeploy.pub
    4096 SHA256:xkvYaIjppz1ZQflZSM+oPOpkNEkCNlujjAGREQOdkaU lecuntobengio (RSA)
      /home/ubuntu/.ssh/id_rsa_lecuntobengio.pub
    3072 SHA256:bIJpiGyR1Pa8elZjeCiuJjcC4R+qzU8DCliW5JaT7aI ubuntu@lecun (RSA)
      /home/ubuntu/.ssh/id_rsa_lecuntoefros.pub
    3072 SHA256:yLlX2CaNQrdN3NIFkhNmbGuFrXUOw1OtANN1P46vJUI ubuntu@lecun (RSA)
      /home/ubuntu/.ssh/id_rsa_lecuntophilip.pub

    公開鍵の件数: 6

秘密鍵の側（**中身は出さない。大きさと権限と BEGIN 行の件数のみ**）:

    秘密鍵 id_ed25519_github          size=399  perm=600 BEGIN行=1
    秘密鍵 id_ed25519_lecuntophilip   size=399  perm=600 BEGIN行=1
    秘密鍵 id_lecundeploy             size=399  perm=600 BEGIN行=1
    秘密鍵 id_rsa_lecuntobengio       size=3381 perm=600 BEGIN行=1
    秘密鍵 id_rsa_lecuntoefros        size=2602 perm=600 BEGIN行=1
    秘密鍵 id_rsa_lecuntophilip       size=2602 perm=600 BEGIN行=1

**六対。秘密鍵はすべて権限 600 である。**

| 鍵 | 種別 | 指紋（先頭） | 註釈 | 名前が示す用途 |
|---|---|---|---|---|
| `id_ed25519_github` | ED25519 256 | `SHA256://dnKA2F` | `ubuntu@lecun` | 版管理 |
| `id_ed25519_lecuntophilip` | ED25519 256 | `SHA256:dL4qKLl4` | `ubuntu@lecun` | **中継に使用中** |
| `id_lecundeploy` | ED25519 256 | `SHA256:PK9k6A98` | `deploy-lecun` | 配備 |
| `id_rsa_lecuntobengio` | RSA 4096 | `SHA256:xkvYaIjp` | `lecuntobengio` | lecun から bengio |
| `id_rsa_lecuntoefros` | RSA 3072 | `SHA256:bIJpiGyR` | `ubuntu@lecun` | lecun から efros |
| `id_rsa_lecuntophilip` | RSA 3072 | `SHA256:yLlX2CaN` | `ubuntu@lecun` | lecun から philip（旧） |

**philip 向けの鍵が二本ある**（ED25519 が 7 月 3 日、RSA が 7 月 1 日）。
中継が使うのは目印が指す ED25519 の方である。

**bengio 向けと efros 向けの鍵が既に存在する。** 鍵の存在は認証が通ることを意味しない。
相手側の受け入れの一覧に登録されているかは自ホストからは読めない。**Task 3 で実測する。**

### Step 4 秘匿の検査（陽性対照つき）

    本番: grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" audit.md
    0
    一致した行: (なし)

    陽性対照: 囮の行（BEGIN OPENSSH PRIVATE KEY の見出し）を含む一時ファイル
    囮の行数: 2
    一致: 1
    一致した行番号: 1
    囮を消した（外部へ送らない）

**本番が零、囮が一。検査は空振りではない。** 値の混入と名前の一致を分ける必要は
生じなかった（一致が零だったため）。

### Task 1 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 1 | 中継の目印を集合として列挙した | **2 件**（`.tunnel.log` / `.tunnel_to_philip`）。`find` でも 2 件。経路は `~/.ssh/id_ed25519_lecuntophilip` |
| 2 | 鍵の実在と指紋を測った | 実在。ED25519 256、指紋 `SHA256:dL4qKLl4pYnZpvnVL3kRlipacdq7ipqTpxExhCJqRr8`、権限 600、公開鍵の並置あり。**中身は出していない** |
| 3 | 手元の公開鍵を集合として列挙した | **6 件**（指紋を全件記載）。秘密鍵も 6 件でいずれも権限 600 |
| 4 | 記録に鍵の値が含まれない | 本番 **0** / 囮 **1**（空振りでない） |

---

## Task 2 自ホストが受け入れる側として登録しているもの

### Step 1 受け入れの一覧を集合として探す

    FILE /home/ubuntu/.ssh/authorized_keys lines=4
    -rw-rw-r-- 1 ubuntu ubuntu 1504  7月 29 17:33 /home/ubuntu/.ssh/authorized_keys

`authorized_keys2` は存在しない。別の場所を指す設定を確かめた。

    #Port 22
    #PermitRootLogin prohibit-password
    #AuthorizedKeysFile	.ssh/authorized_keys .ssh/authorized_keys2
    # the setting of "PermitRootLogin without-password".
    #GatewayPorts no

**`AuthorizedKeysFile` の行は註釈されている**（先頭が `#`）。すなわち既定のまま
`.ssh/authorized_keys` と `.ssh/authorized_keys2` が使われる。**別の場所を指していない。**
`Port` も註釈されており既定の 22 である（前契約で `0.0.0.0:22` の待ち受けを実測済み）。

### Step 2 登録されている鍵の指紋

    4096 SHA256:hWCLg+DQJe40cDk5CQoFd1pShHt3SI8lHv90Gf/nGJo philip-to-lecun (RSA)
    256 SHA256:KS+FRL3p+yF2prUwbbZZB587yx6pebLdQCpEkMhNgLc dakyo-mba@dmba.local (ED25519)
    256 SHA256:MKli4Hqp8sYzekheqdjEYKJiYALrCkJqSKGZzZ+VY58 bengiotolecun (ED25519)
    3072 SHA256:fOip68JPi/q8Hq9BjhqJ9Zate/2tYMa8/y8M9gZHR0s ubuntu@efros (RSA)
    count=4

| # | 種別 | 指紋（先頭） | 註釈 | 対応 |
|---|---|---|---|---|
| 1 | RSA 4096 | `SHA256:hWCLg+DQ` | `philip-to-lecun` | **philip** |
| 2 | ED25519 256 | `SHA256:KS+FRL3p` | `dakyo-mba@dmba.local` | 人の端末（device 一覧に無い） |
| 3 | ED25519 256 | `SHA256:MKli4Hqp` | `bengiotolecun` | **bengio** |
| 4 | RSA 3072 | `SHA256:fOip68JP` | `ubuntu@efros` | **efros** |

**遠隔の peer 10 台のうち lecun へ入れるのは 3 台である。**

    遠隔の peer 10 台のうち lecun へ入れるのは 3 台: ['bengio', 'efros', 'philip']
    入れない 7 台: ['adam', 'andrew', 'dlsta', 'he', 'hinton', 'ian', 'ilya']

device の集合は 11 台（`adam, andrew, bengio, dlsta, efros, he, hinton, ian, ilya, lecun, philip`）。
註釈から対応づけたものであり、**指紋そのものを相手ホストで確認したわけではない。**
註釈は自己申告である。

### Step 3 中継の鍵が自ホストに登録されているかの照合

SPEC 指定の照合を実行した。

    照合する指紋（中継に使用中の鍵）: SHA256:dL4qKLl4pYnZpvnVL3kRlipacdq7ipqTpxExhCJqRr8
    grep -c -F "${FP}" /tmp/authfp.txt
    0

**陽性対照**（`/tmp/authfp.txt` に実在する別の指紋で同じ照合）:

    与えた指紋: SHA256:hWCLg+DQJe40cDk5CQoFd1pShHt3SI8lHv90Gf/nGJo
    1

**照合は空振りではない。** 実在する指紋には 1 を返し、実在しない指紋には 0 を返す。

**ただしこの照合は「自ホストが中心になれるか」を判定していない。**
手元の 6 公開鍵すべてを同じ照合にかけた結果:

    id_ed25519_github.pub          SHA256://dnKA2FpWTwcgB -> 登録 0 件
    id_ed25519_lecuntophilip.pub   SHA256:dL4qKLl4pYnZpvn -> 登録 0 件
    id_lecundeploy.pub             SHA256:PK9k6A98J/Ma2nY -> 登録 0 件
    id_rsa_lecuntobengio.pub       SHA256:xkvYaIjppz1ZQfl -> 登録 0 件
    id_rsa_lecuntoefros.pub        SHA256:bIJpiGyR1Pa8elZ -> 登録 0 件
    id_rsa_lecuntophilip.pub       SHA256:yLlX2CaNQrdN3NI -> 登録 0 件

**六件すべてが 0 である。これは正常であり、異常の兆候ではない。**
鍵は対ごとに別に作られている（外向きが `lecuntophilip`、受け入れが `philip-to-lecun`）。
外向きの鍵を自分の受け入れ一覧に置く理由が無い。
**したがってこの照合は構造的に必ず 0 を返し、中心になれるかを判定できない。**

**中心になれるかの答えは Step 2 のデータにある。**
lecun は philip・bengio・efros の 3 台からの接続を受け入れる。残る 7 台は受け入れない。

### Step 4 自ホストの住所

`ip` 命令は存在しない（前契約で既知）。SPEC 指定の代替命令を実行した。

    cat /proc/net/fib_trie | grep -A1 "32 host" | head -20
    行数: 11
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

**この出力は broadcast の住所である。自ホストの住所ではない。**
`/32 host LOCAL` の行の**後ろ**を取っているが、住所は**前**の行にある。
正しく解析した結果:

    /32 host LOCAL の項 4 件 / 重複を除いて 2 件
      127.0.0.1
      172.17.0.22

`/etc/hosts` と経路表による裏づけ:

    127.0.0.1	localhost
    172.17.0.22	lecun

    eth0  宛先 0.0.0.0     ゲートウェイ 172.17.0.1  マスク 0.0.0.0
    eth0  宛先 172.17.0.0  ゲートウェイ 0.0.0.0     マスク 255.255.0.0

**自ホストの住所は `172.17.0.22`**（容器の内側の帯）。既定経路は `172.17.0.1`。
他ノードは `192.168.196.0/24` にあり、**別の帯である**（前契約で実測）。

**他ノードから lecun がどの住所で見えるかは自ホストからは測れない。UNKNOWN とする。**
容器の外側で住所の変換が行われている可能性があるが、その設定は自ホストから読めない。

### Task 2 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 5 | 受け入れの一覧を集合として探した | `~/.ssh/authorized_keys`（**4 行**、1504 バイト）。`authorized_keys2` なし。`AuthorizedKeysFile` は註釈されており既定のまま |
| 6 | 登録されている指紋を列挙した | **4 件**（philip / 人の端末 / bengio / efros） |
| 7 | 中継の鍵が自ホストに登録されているかを照合した | **0**。陽性対照は **1**（空振りでない）。**ただしこの照合は中心になれるかを判定していない**（外向き鍵と受け入れ一覧の比較であり構造的に必ず 0） |
| 8 | 自ホストの住所を測った | **`172.17.0.22`**（`127.0.0.1` も LOCAL）。既定経路 `172.17.0.1`。**他ノードから見える住所は UNKNOWN** |

---

## Task 3 他ホストへ実際に認証が通るか

### Step 1 対象の一覧（三つの出所）

| 出所 | 件数 | 内容 |
|---|---|---|
| `~/.ssh/config` | `ssh_count=4` | `github.com` / `bengio` .105 / `philip` .150 / `efros` .227（後 3 者は Port 50072） |
| `/etc/hosts` | 7 行 | 遠隔の対象は **0 件**。`172.17.0.22 lecun`（自ホスト）と loopback 系のみ |
| syncthing の設定 | `stcfg_count=11` | `192.168.196.X:22000` が 10 件 + `127.0.0.1:22001` |

    192.168.196.105 106 143 150 190 227 54 58 63 78
    target_hosts=10

**和集合の対象は 10 台。** `~/.ssh/config` の 3 台は syncthing の集合に含まれ新規を出さない。
**既知の構成 11 台は遠隔 10 台と自ホストの内訳であり、一覧は縮んでいない。**

`~/.ssh/config` の `IdentityFile` の対応:

    Host github.com  IdentityFile ~/.ssh/id_ed25519_github
    Host bengio      HostName 192.168.196.105  Port 50072  IdentityFile ~/.ssh/id_rsa_lecuntobengio
    Host philip      HostName 192.168.196.150  Port 50072  IdentityFile /Users/dakyo-mba/.ssh/id_rsa_lecuntophilip
    Host efros       HostName 192.168.196.227  Port 50072  IdentityFile ~/.ssh/id_rsa_lecuntoefros

**`philip` の `IdentityFile` は不在である。**

    /home/ubuntu/.ssh/id_ed25519_github                  実在
    /home/ubuntu/.ssh/id_rsa_lecuntobengio               実在
    /Users/dakyo-mba/.ssh/id_rsa_lecuntophilip           不在
    /home/ubuntu/.ssh/id_rsa_lecuntoefros                実在

経路が macOS の形（`/Users/dakyo-mba/...`）であり、lecun は Linux（`/home/ubuntu`）である。
**人の端末の設定がそのまま写されたものと読める。**
ただし**中継はこの設定を使っていない。** `keeper.sh` は
`-i "$(cat ~/.tunnel_to_philip)"` で経路を明示的に渡すため、中継の動作には影響しない。

### 禁止 2 との衝突を避けた（`known_hosts` へ書き込まない）

SPEC Step 2 の命令は `-o StrictHostKeyChecking=accept-new` を含むが、これは
`~/.ssh/known_hosts` へ**追記する**。禁止 2 は `~/.ssh/**` の変更を禁じている。
**指示どおり実行すると禁止事項を破る。**

`-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` に置き換えた。
**変更していないことを要約値で証明する。**

測定前:

    b7dd7291ed3c8b6a292b04d31cef9f16  /home/ubuntu/.ssh/known_hosts
    0a28d54b47b6123483867831639f18f7  /home/ubuntu/.ssh/known_hosts.old
    /home/ubuntu/.ssh/known_hosts 5032 バイト 更新 2026-07-01 09:11:14
    登録されているホストの件数: 16

測定後:

    b7dd7291ed3c8b6a292b04d31cef9f16  /home/ubuntu/.ssh/known_hosts
    0a28d54b47b6123483867831639f18f7  /home/ubuntu/.ssh/known_hosts.old
    /home/ubuntu/.ssh/known_hosts 更新 2026-07-01 09:11:14

**要約値も更新時刻も変わっていない。**

### Step 2 中継の鍵での認証（実行した命令は `echo` だけ）

鍵は `~/.ssh/id_ed25519_lecuntophilip`（目印が指すもの）。利用者は `ubuntu`
（`keeper.sh` 19 行が `ubuntu@192.168.196.150` を使うため）。

    192.168.196.105 :: ubuntu@192.168.196.105: Permission denied (publickey,password).
    192.168.196.106 :: ubuntu@192.168.196.106: Permission denied (publickey,password).
    192.168.196.143 :: ubuntu@192.168.196.143: Permission denied (publickey,password).
    192.168.196.150 :: ssh: connect to host 192.168.196.150 port 50072: No route to host
    192.168.196.190 :: ubuntu@192.168.196.190: Permission denied (publickey,password).
    192.168.196.227 :: ubuntu@192.168.196.227: Permission denied (publickey,password).
    192.168.196.54 :: ubuntu@192.168.196.54: Permission denied (publickey,password).
    192.168.196.58 :: ubuntu@192.168.196.58: Permission denied (publickey,password).
    192.168.196.63 :: ubuntu@192.168.196.63: Permission denied (publickey,password).
    192.168.196.78 :: ubuntu@192.168.196.78: Permission denied (publickey,password).

**中継の鍵はどこにも通らない。** 名前の上でも実測の上でも philip 専用である
（philip 自身は到達できないため確かめられない）。

### Step 3 三分類の集計

    AUTH_OK=0
    DENIED=9
    NOCONN=1
    total_lines=10

**0 + 9 + 1 = 10 = 対象数。一致した。分類から漏れた行は無い。**

| 分類 | 意味 | 件数 |
|---|---|---|
| `REACHABLE` | 認証が通る。中継を張れる | **0** |
| `Permission denied` | **口は開いているが鍵が通らない。** 登録の追加が要る | **9** |
| 接続の失敗 | 経路または口の問題 | **1**（philip の `No route to host`。前契約の結果と一致） |

### 追加の測定 `~/.ssh/config` が宣言する対応で測り直した

中継の鍵は philip 専用であるため、それだけでは「どのホストが中心になれるか」に答えられない。
`~/.ssh/config` が宣言する対応（実在する `IdentityFile`）で測り直した。

    192.168.196.105 key=id_rsa_lecuntobengio :: REACHABLE
    192.168.196.227 key=id_rsa_lecuntoefros :: REACHABLE

**lecun から bengio と efros へは、既に存在する鍵で認証が通る。**

### Step 4 陽性対照（通らないはずの鍵）

代理（`ssh-agent`）の状態を先に確かめた。**代理経由での偶然の成功を排除するためである。**

    SSH_AUTH_SOCK=/tmp/vscode-ssh-auth-sock-148739828
    Error connecting to agent: No such file or directory

**環境変数は設定されているが代理は到達不能である。** したがって認証の成否は
`-i` で渡した鍵だけで決まる。**これは陽性対照だけでなく、上の REACHABLE 二件の
妥当性も裏づける。**

到達できた住所（bengio）へ通らないはずの鍵を与えた。

    陽性対照 A（SPEC 指定のまま）:
      Load key "/dev/null": error in libcrypto
      ubuntu@192.168.196.105: Permission denied (publickey,password).

    陽性対照 B（鍵を隔離 IdentitiesOnly=yes）:
      Load key "/dev/null": error in libcrypto
      ubuntu@192.168.196.105: Permission denied (publickey,password).

    機械判定:
      IdentitiesOnly=なし: REACHABLE の件数 0（Expected 0）
      IdentitiesOnly=yes : REACHABLE の件数 0（Expected 0）

**両方の形で `REACHABLE` が返らない。鍵による識別は働いている。**
`IdentitiesOnly` を付けない形も測ったのは、既定の鍵へ落ちて偶然通る可能性を
排除するためである。**両方とも 0 であり、対照は空振りしていない。**

### Task 3 完了判定

| # | 完了判定 | 実測 |
|---|---|---|
| 9 | 対象一覧を三つの出所から集め件数を記録した | `ssh_count=4` / `/etc/hosts` の遠隔 **0** / `stcfg_count=11` -> 和集合 **10 台**。既知 11 台 = 遠隔 10 + 自ホスト。**縮んでいない** |
| 10 | 全対象で認証を測り合計が一致した | **10 行**。0 + 9 + 1 = **10 = 対象数** |
| 11 | 認証の可否と接続の可否を区別した | `REACHABLE` **0** / `Permission denied` **9** / 接続の失敗 **1**（philip） |
| 12 | 通らないはずの鍵で通らないことを確かめた | `/dev/null` で `REACHABLE` **0 件**（`IdentitiesOnly` の有無の二通りで測定）。代理は到達不能で偶然の成功はない |

---

## Task 4 送信前の検査

### 送信前の自己検査（Step 6）

    RESULT.md    bmp_over=0 hex40=0
    result.yaml  bmp_over=0 hex40=0
    audit.md     bmp_over=0 hex40=0
    inbox.d      bmp_over=0 hex40=0

**両方とも零。** 基本多言語面の外の文字は使っておらず、四十桁の十六進も含まない。
履歴の識別子は短縮形にした。要約値は三十二桁であり四十桁の検査には触れない。

### 秘匿の検査の再実行と一件ずつの判定

記録を書き進めた後に再実行すると一致が増える。**この検査には自己言及の性質がある。**
検査の型そのものや、`ssh` の誤りの表示（`publickey,password` を含む）を記録に書くと、
その語がまた一致する。**したがって判定は件数ではなく形で行う。**

    RESULT.md    一致 2 件
    result.yaml  一致 1 件
    audit.md     一致 15 件
    一致の総数 18 件

一致した十八件を一件ずつ、値の形に該当するかで判定した。値の形として次の三つを見た。

| 見た形 | 意味 |
|---|---|
| 秘密鍵の見出し行そのもの | 鍵の書き出し |
| 基数六十四の長い塊（六十文字以上の一行） | 鍵の本体らしき行 |
| 語に区切りと値が続く形 | 設定の値としての秘匿 |

    一致の総数 18 / 値の形に該当 0

内訳は次のとおり。**いずれも説明文または誤りの表示である。**

| 由来 | 件数 |
|---|---|
| `ssh` の認証失敗の表示（`publickey,password` を含む） | 13 |
| 検査の型そのものの引用 | 2 |
| `sshd_config` の註釈行（`PermitRootLogin` の既定） | 2 |
| 囮の説明（見出しの名を書いたもの） | 1 |

**値の形に該当するものは無い。鍵の中身は記録に含まれていない。**

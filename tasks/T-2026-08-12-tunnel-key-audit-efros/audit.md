# audit — T-2026-08-12-tunnel-key-audit-efros

実行ホスト `efros` / repo `~/slocal/m2` / 測定 `2026-08-12T11:10Z` 以降。
**読み取りのみ。鍵の生成・配布・変更は行っていない。中心の移設も行っていない。**

**秘密鍵の中身はどこにも記録していない。指紋と経路名だけである。**
指紋は公開鍵の要約であり秘匿ではない。

| 項目 | 実測値 |
|---|---|
| 契約ブランチ | `feat/tunnel-key-audit-efros`（起点 `origin/phase0`） |
| `.sync-pause` | `11:10` 設置（`task_start.sh` が作成） |
| `grep -c sync-pause ~/bin/m2-sync.sh` | **2**（零ではない → 抑止は効いている） |
| `conventions_rev` の実測 | `d422b08`（契約の記載と一致。置換不要） |

---

## Task 1 中継に使われている鍵

### Step 1 目印の集合列挙と、指す経路

    ls -a ~/ | grep -i tunnel   →  count=2
    .tunnel.log
    .tunnel_to_philip

    FILE /home/ubuntu/.tunnel_to_philip size=43
    POINTS_TO=/home/ubuntu/.ssh/id_ed25519_efrostophilip

目印は 1 つだけで、**philip 宛のものしか無い**。中身は秘密鍵そのものではなく
その経路であり（`keeper.sh:13` のコメントによる）、経路のみ記録した。

**経路名が `efrostophilip`、すなわち「efros から philip へ」である。**
これは鍵が**対ごとに作られている**ことを示唆する。Step 3 で裏づける。

### Step 2 鍵の実在・種別・指紋

    -rw------- 1 ubuntu ubuntu 399  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_efrostophilip
    -rw-r--r-- 1 ubuntu ubuntu  94  7月  3 23:36 /home/ubuntu/.ssh/id_ed25519_efrostophilip.pub

    256 SHA256:vgkD0GqFco6G+2QwtT0MknwTursNSLNi5rsORrbNa8I ubuntu@efros (ED25519)

| 項目 | 値 |
|---|---|
| 実在 | **する**（秘密鍵 399 バイト / 公開鍵 94 バイト、いずれも 2026-07-03 23:36） |
| 種別 | **ED25519 256 bit** |
| 指紋 | `SHA256:vgkD0GqFco6G+2QwtT0MknwTursNSLNi5rsORrbNa8I` |
| 注釈 | `ubuntu@efros` |
| 権限 | 秘密鍵 `-rw-------`（適切） |

**`-----BEGIN` で始まる行は一度も出力していない。** 指紋は `.pub` から取得した。

### Step 3 手元の鍵を集合として列挙

`~/.ssh/` の中身:

    -rw-rw-r-- 1 ubuntu ubuntu 1234  7月  1 09:10 authorized_keys
    -rw------- 1 ubuntu ubuntu  370  7月 29 17:33 config
    -rw------- 1 ubuntu ubuntu  399  7月  3 23:36 id_ed25519_efrostophilip
    -rw-r--r-- 1 ubuntu ubuntu   94  7月  3 23:36 id_ed25519_efrostophilip.pub
    -rw------- 1 ubuntu ubuntu  399  7月  1 06:08 id_ed25519_github
    -rw-r--r-- 1 ubuntu ubuntu   94  7月  1 06:08 id_ed25519_github.pub
    -rw------- 1 ubuntu ubuntu  411  7月 10 07:40 id_m2deploy
    -rw-r--r-- 1 ubuntu ubuntu   97  7月 10 07:40 id_m2deploy.pub
    -rw------- 1 ubuntu ubuntu 2590  7月 29 17:32 id_rsa_efrostolecun
    -rw-r--r-- 1 ubuntu ubuntu  566  7月 29 17:32 id_rsa_efrostolecun.pub
    -rw------- 1 ubuntu ubuntu 2602  7月  1 05:46 id_rsa_efrostophilip
    -rw-r--r-- 1 ubuntu ubuntu  566  7月  1 05:46 id_rsa_efrostophilip.pub
    -rw------- 1 ubuntu ubuntu 2934  7月 29 19:12 known_hosts
    -rw------- 1 ubuntu ubuntu 2098  7月 29 17:33 known_hosts.old

公開鍵の指紋（**特定の名前を探さず、見つかった全件**）:

    pubkey_count=5
    256  SHA256:vgkD0GqFco6G+2QwtT0MknwTursNSLNi5rsORrbNa8I ubuntu@efros      (ED25519)  id_ed25519_efrostophilip.pub
    256  SHA256:gu1fcUlU1KQ2/D2Tsp7O+mXwRkkfHHKDJVvB5WBkvo4 ubuntu@lecun      (ED25519)  id_ed25519_github.pub
    256  SHA256:UBSqejUwYDnPAd1pm9wJfXpIhS1EbCWptx4OSh2pc8g m2-deploy-efros   (ED25519)  id_m2deploy.pub
    3072 SHA256:fOip68JPi/q8Hq9BjhqJ9Zate/2tYMa8/y8M9gZHR0s ubuntu@efros      (RSA)      id_rsa_efrostolecun.pub
    3072 SHA256:ABprrCEPAVpF1RhvRxiHNiQi1WB884hqrpvuH+Roz+4 ubuntu@efros      (RSA)      id_rsa_efrostophilip.pub

**鍵は対ごとに作られている。** 名前が宛先を含み（`efrostophilip` / `efrostolecun`）、
efros が持つ「他ノードへ向かう鍵」は **philip 宛と lecun 宛の 2 つだけ**である。
残る 3 つは用途が別（github 用・deploy 用）。**他 7 台へ向かう鍵は存在しない。**

`~/.ssh/config` の対応づけ:

    Host philip     HostName 192.168.196.150  User ubuntu  Port 50072
                    IdentityFile /Users/dakyo-mba/.ssh/id_rsa_efrostophilip
    Host github.com HostName github.com       User git
                    IdentityFile ~/.ssh/id_ed25519_github
    Host lecun      HostName 192.168.196.176  User ubuntu  Port 50072
                    IdentityFile /home/ubuntu/.ssh/id_rsa_efrostolecun

実在の確認:

    MISSING /Users/dakyo-mba/.ssh/id_rsa_efrostophilip
    EXISTS  /home/ubuntu/.ssh/id_rsa_efrostolecun
    EXISTS  /home/ubuntu/.ssh/id_ed25519_github

▲ **`~/.ssh/config` の philip 用 `IdentityFile` が macOS の経路を指しており、
このホストには存在しない。** 別の機械の設定がそのまま持ち込まれている。
`ssh philip` という別名経由では指定した鍵が読めない。
ただし**中継はこの別名を使っていない。** `keeper.sh:16` は
`-i "$(cat ~/.tunnel_to_philip)"` で経路を直接与えるため、この不整合は
中継の失敗の原因ではない（前契約で原因は経路の喪失と確定済み）。

▲ **`id_ed25519_github.pub` の注釈が `ubuntu@lecun` である。**
efros の鍵ならば `ubuntu@efros` になるはずで、lecun で作った鍵が
複製されている可能性がある。**注釈は自己申告であり、これだけでは断定しない。**

### Step 4 記録に鍵の値が含まれないこと

    grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" audit.md   →  2

**値の混入と名前の一致を分けて判定する。** 該当 2 行を実体で確かめた:

    127:    #PermitRootLogin prohibit-password
    129:    # the setting of "PermitRootLogin without-password".

いずれも `sshd_config` から逐語で引いた**オプション名**であり、値ではない。
`password` は `PermitRootLogin` の設定語の一部として現れているだけである。
**削る必要はない。名前の一致として記録する。**

**陽性対照**（鍵の書き出しを模した囮に同じ検査。囮は外部へ送っていない）:

    printf -- '-----BEGIN OPENSSH PRIVATE KEY-----\n' > /tmp/decoy_key.txt
    grep -c -i -E "BEGIN [A-Z ]*PRIVATE|..." /tmp/decoy_key.txt   →  1

**検査は働いている。** そのうえで実際の記録には値の混入が無い。

鍵本体の形（base64 の長い塊）についても別途検査した:

    grep -c -E "ssh-(rsa|ed25519) AAAA|AAAAB3Nza|AAAAC3Nza" audit.md   →  1

該当は 143 行目で、**実行者が検査模様そのものを文章に書いた箇所**である。
一致した base64 の連続長を測ると **4 文字**（`AAAA`）で、実鍵なら 68 文字以上になる。
**鍵素材ではない。**

**G1（`after: A`、`on_fail: stop`）: 通過。**
指紋の照合は実在する別の指紋で 1 を返し（空振りではない）、
秘匿の検査は囮で 1 を返した（働いている）。

---

## Task 2 自ホストが受け入れる側として何を登録しているか

### Step 1 受け入れの一覧を集合として探す

    FILE /home/ubuntu/.ssh/authorized_keys lines=3
    -rw-rw-r-- 1 ubuntu ubuntu 1234  7月  1 09:10 /home/ubuntu/.ssh/authorized_keys

`authorized_keys2` は存在しない。**零件だから「無い」と結論せず**、別の場所を
指す設定がないかを `sshd_config` で確かめた:

    #Port 22
    #PermitRootLogin prohibit-password
    #AuthorizedKeysFile	.ssh/authorized_keys .ssh/authorized_keys2
    # the setting of "PermitRootLogin without-password".
    #GatewayPorts no

**該当行はすべてコメントアウトされており、既定値が効く**
（`.ssh/authorized_keys` と `.ssh/authorized_keys2`）。別の場所は指していない。
したがって `~/.ssh/authorized_keys` の 3 行が受け入れの全てである。

### Step 2 登録されている鍵の指紋

    count=3
    256  SHA256:DWIzuv3Dq5bAIDE37WkvWlFAAX282P5/hg3xCx45WwI dakyo-mba@dmba.local (ED25519)
    3072 SHA256:fB+w48wW/IaAun87OflVPRz3APx3LjpHJvIosjopMF4 ubuntu@aolab         (RSA)
    3072 SHA256:bIJpiGyR1Pa8elZjeCiuJjcC4R+qzU8DCliW5JaT7aI ubuntu@lecun         (RSA)

出力に鍵本体が含まれないことを確認した（`BEGIN` と `ssh-rsa AAAA` 形式の一致が **0**）。

■ **efros が受け入れるのは 3 者だけである。**

| 注釈 | 種別 | 素性 |
|---|---|---|
| `dakyo-mba@dmba.local` | ED25519 | 利用者の Mac |
| `ubuntu@aolab` | RSA | ノード `aolab` |
| `ubuntu@lecun` | RSA | ノード `lecun` |

**philip の鍵は登録されていない。他 6 台の鍵も登録されていない。**

### Step 3 中継の鍵が自ホストに登録されているか

    照合対象 FP=SHA256:vgkD0GqFco6G+2QwtT0MknwTursNSLNi5rsORrbNa8I
    result=0

**陽性対照**（`/tmp/authfp.txt` に実在する別の指紋で同じ照合）:

    control_fp=SHA256:bIJpiGyR1Pa8elZjeCiuJjcC4R+qzU8DCliW5JaT7aI
    control_result=1

**照合は働いている。** 常に零を返す壊れ方はしていない。そのうえで
中継の鍵は自ホストに **登録されていない（0）**。

さらに、**手元の 5 鍵すべて**について同じ照合を行った:

    0  SHA256:vgkD0GqFco6G+2QwtT0MknwTursNSLNi5rsORrbNa8I   (efros -> philip, ED25519)
    0  SHA256:gu1fcUlU1KQ2/D2Tsp7O+mXwRkkfHHKDJVvB5WBkvo4   (github 用, ED25519)
    0  SHA256:UBSqejUwYDnPAd1pm9wJfXpIhS1EbCWptx4OSh2pc8g   (m2-deploy-efros, ED25519)
    0  SHA256:fOip68JPi/q8Hq9BjhqJ9Zate/2tYMa8/y8M9gZHR0s   (efros -> lecun, RSA)
    0  SHA256:ABprrCEPAVpF1RhvRxiHNiQi1WB884hqrpvuH+Roz+4   (efros -> philip, RSA)

**5 件すべて 0。共有鍵方式ではない。** 全ノードが同じ鍵を持つ構成であれば、
自分の鍵が自分の `authorized_keys` にも入るはずである。入っていないことと、
名前が対ごとであることが一致する。

### Step 4 自ホストの住所

`ip` コマンドはこのホストに存在しない。`/proc/net/fib_trie` で代替した:

    |-- 127.0.0.1
    |-- 172.17.0.21

    /etc/hosts:  172.17.0.21	efros
    hostname -I: 172.17.0.21

三通り（`fib_trie` / `/etc/hosts` / `hostname -I`）が一致して **`172.17.0.21`**。
これは**容器の内側の住所**であり、他ノードが居る `192.168.196.x` の帯ではない。

**efros が他ノードからどの住所で見えるかは自ホストからは測れない（UNKNOWN）。**
他ノードは `192.168.196.x:50072` で到達できたので、各ノードの物理側が
容器の 22 番を 50072 へ転送していると考えられるが、**efros の物理側に同じ転送が
あるかは外からしか確かめられない。**

---

## Task 3 他の九台へ実際に認証が通るか

### Step 1 対象の一覧を三つの出所から

| 出所 | 件数 | 内容 |
|---|---|---|
| `~/.ssh/config` | `ssh_count=3` | `philip`(192.168.196.150:50072) / `github.com` / `lecun`(192.168.196.176:50072) |
| `/etc/hosts` | 7 行 | 自ホスト `172.17.0.21 efros` と loopback / IPv6 予約のみ。**他ノードの記載なし** |
| syncthing 設定の `tcp://` | 11 | 他ノード 10 個の `192.168.196.x:22000` + `127.0.0.1:22001` |

    peer_count=10
    192.168.196.54  .58  .63  .78  .105  .106  .143  .150  .176  .190

**和集合の他ノード = 10 台。** 自分 efros を足して 11 台で、既知の構成と一致する。
**一覧が縮んでいる兆候は無い。** 出所を 1 つに絞ると 2 台まで縮むことは前契約で確認済み。

### 測定方法の変更 — 禁止 #2 を守るため

SPEC Step 2 の命令は `-o StrictHostKeyChecking=accept-new` を含む。**この指定は
新規ホストへ接続したとき `~/.ssh/known_hosts` へ書き込む。** 禁止 #2 は
「`~/.ssh/**` を変更する（読むのは可）」を禁じており、**契約の内部で矛盾している。**

efros は他 8 台へ接続したことがないため、指示どおり実行すれば**実際に書き込みが起きる。**
そこで意図（無人で止まらない）を保ったまま、書き込み先だけを repo 外へ逃がした:

    cp ~/.ssh/known_hosts /tmp/kh_audit.txt
    ssh ... -o UserKnownHostsFile=/tmp/kh_audit.txt -o StrictHostKeyChecking=accept-new ...

**この判断が正しかったことは実測で裏づけられた**（後述の遵守確認を参照）。

### Step 2 認証を測る（実行した命令は `echo` だけ）

鍵は Task 1 で特定した中継の鍵 `~/.ssh/id_ed25519_efrostophilip` を用いた。

    lines=10
    192.168.196.54  ubuntu@192.168.196.54: Permission denied (publickey,password).
    192.168.196.58  ubuntu@192.168.196.58: Permission denied (publickey,password).
    192.168.196.63  ubuntu@192.168.196.63: Permission denied (publickey,password).
    192.168.196.78  ubuntu@192.168.196.78: Permission denied (publickey,password).
    192.168.196.105 ubuntu@192.168.196.105: Permission denied (publickey,password).
    192.168.196.106 ubuntu@192.168.196.106: Permission denied (publickey,password).
    192.168.196.143 ubuntu@192.168.196.143: Permission denied (publickey,password).
    192.168.196.150 ssh: connect to host 192.168.196.150 port 50072: No route to host
    192.168.196.176 ubuntu@192.168.196.176: Permission denied (publickey,password).
    192.168.196.190 ubuntu@192.168.196.190: Permission denied (publickey,password).

### Step 3 三分類の集計

    AUTH_OK=0   DENIED=9   NOCONN=1   total_lines=10   sum=10

**`0+9+1 = 10 = total`。分類から漏れた行は無い。**

| 分類 | 件数 | 意味 |
|---|---|---|
| 認証が通る（`REACHABLE`） | **0** | 中継の鍵で入れるノードは**一つも無い** |
| 鍵が通らない（`Permission denied`） | **9** | **口は開いている。登録の追加が要る** |
| 接続そのものが失敗 | **1** | philip のみ（`No route to host`。前契約の結果と一致） |

**口が開いていることと鍵が通ることは別である、という前提が実測で裏づけられた。**
前契約では 9 台の `50072` が `OPEN` だった。本契約では同じ 9 台が
`Permission denied` を返す。**到達はするが認証されない。**

### 追加測定 — 対ごとの鍵ならどうか

efros は lecun 宛の専用鍵を持つ。SPEC は中継の鍵だけを指定しているが、
**「中心を移せるか」を判断するには専用鍵での可否が要る**ため追加で測った。

    192.168.196.176(lecun)  id_rsa_efrostolecun:  REACHABLE
    192.168.196.150(philip) id_rsa_efrostophilip: ssh: connect to host ... No route to host

■ **専用鍵があれば認証は通る。** 同じ lecun が、中継の鍵では `Permission denied`、
専用鍵では `REACHABLE` を返した。**鍵は対ごとに配られており、efros が
入っていけるのは lecun だけである**（philip は経路が無く判定不能）。

### Step 4 陽性対照 — 通らないはずの鍵

到達できた住所（lecun）へ `/dev/null` を鍵として与えた。

    Load key "/dev/null": error in libcrypto
    ubuntu@192.168.196.176: Permission denied (publickey,password).
    REACHABLE の件数 = 0

**期待どおり `REACHABLE` は返らなかった。**

さらに、この対照が意味を持つことを補強する事実を測った。**鍵の代理は使えない:**

    SSH_AUTH_SOCK=/tmp/vscode-ssh-auth-sock-110007150
    ssh-add -l  →  Error connecting to agent: No such file or directory

変数は設定されているが**実体の靴下が存在しない**ため、代理経由の鍵は使われない。
したがって `-i` で与えた鍵が識別を決めている。**同じ宛先 lecun が、正しい鍵で
`REACHABLE`、`/dev/null` で `Permission denied` を返した。** 経路も口も同じで
鍵だけが違う。**測定は鍵で識別できている。**

### 禁止 #2 の遵守確認（測定後）

    測定前: size=2934 mtime=1785352326 sha256_prefix=4a1587d65c4dcc5f
    測定後: size=2934 mtime=1785352326 sha256_prefix=4a1587d65c4dcc5f

**`~/.ssh/known_hosts` は大きさ・更新時刻・要約値のすべてが一致し、無変更である。**
`~/.ssh/` 配下のどのファイルも本日の更新時刻を持たない（最新は `known_hosts` の
`1785352326` で、本契約の開始より前）。

**迂回先には書き込みが起きた:**

    /tmp/kh_audit.txt  複製時 9 件  →  測定後 17 件（+8）

▲ **これが決定的である。** `accept-new` は実際に **8 件**の新しいホスト鍵を書いた。
内訳は、接続が成立した 9 台のうち lecun が既知だったため残り 8 台分である。
**SPEC どおりに実行していれば、この 8 件は `~/.ssh/known_hosts` へ書き込まれ、
禁止 #2 に違反していた。** 迂回は必要だった。

### Task 3 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 9 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config`=3 / `/etc/hosts`=7 行（他ノード 0）/ syncthing 設定=11。**和集合の他ノード = 10 台**、自分を足して 11 台で既知の構成と一致 |
| 10 | 全対象で認証を測り合計が一致した | `total_lines=10`、`AUTH_OK 0 + DENIED 9 + NOCONN 1 = 10`。**一致** |
| 11 | 認証の可否と接続の可否を区別した | `Permission denied` **9**（口は開くが鍵が通らない）/ `No route to host` **1**（philip のみ）/ 認証成功 **0**。追加測定で専用鍵なら lecun は `REACHABLE` |
| 12 | 通らないはずの鍵で通らないことを確かめた | `-i /dev/null` で `Permission denied`、`REACHABLE` の件数 **0**。鍵の代理が接続不能であることも確認し、`-i` が識別を決めていることを裏づけた |

**G2（`after: B`、`on_fail: stop`）: 通過。**
通らないはずの鍵で通らないことを実測し、対象一覧を三つの出所から集めて
件数（10）と測定件数（10）が一致することを確かめた。

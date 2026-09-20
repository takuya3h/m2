# audit — T-2026-09-20-dlsta-syncthing-join

手続きの証跡。`RESULT.md` はここを行番号で指す。
**秘匿の値は一切含めない。** 識別子・指紋・住所は秘匿ではないため載せる。

実行ホスト `dlsta`（`hostname` は `4f3861ae8d3b`） / repo `/home/ubuntu/local/m2` / 2026-09-20（JST）

---

## A0. 計数の器の検証（Task 1 Step 1 / 完了判定 B）

**測る前に器を検証した。** 前契約で陽性対照が二度落ちたためである。

器は `/proc/PID/exe` の実体の basename で絞り、**自分と祖先をすべて除外**する
（`/proc/PID/stat` の第 4 欄を根まで辿って集合を作る。`issuer_cautions` #6）。

    自分の実体の basename = zsh
    陽性対照 zsh               → 3 件   （1 以上。器は働く）
    陰性対照 zzz_no_such_binary → 0 件   （偽陽性なし）

**陽性対照は自分の exe の実体から取った。** 語を決め打ちにすると、
その語のプロセスが本ホストに無いときに 0 を返し、壊れと区別できない（前契約の実測）。

## A1. 開始状態（完了判定 A・C）

### 稼働しているもの — すべて零件

| 対象 | 件数 |
|---|---|
| `syncthing` | **0** |
| `keeper` | **0** |
| `m2-sync` | **0** |
| `ssh` | **0** |

### 実行ファイルと設定

| 対象 | 実測 |
|---|---|
| `~/bin/` の中身 | **`syncthing` のみ 1 件** |
| `~/bin/syncthing` | 権限 **644**、sha256 `e8a08fdd8b25340a…`（中心と同じ v2.1.3） |
| **実行権** | **落ちている**（`[ -x ~/bin/syncthing ]` が偽） |
| `~/bin/keeper.sh` | **不在** |
| `~/bin/m2-sync.sh` | **不在** |
| `~/.local/state/syncthing/config.xml` | 権限 **600**、6578 bytes、sha256 `1e9659966afc18634349c15233ad35ea…` |
| 同ディレクトリ | `cert.pem`(623, 664) / `key.pem`(119, 600) / `.syncthing.tmp.214119935`(0, 600) |

`.syncthing.tmp.214119935` は前契約の `generate` が残した 0 バイトの作業ファイルである。

### 中継の目印 — 零件

    ls ~/.tunnel_to_philip → No such file or directory
    目印の件数 = 0                （本判定）
    陽性対照 ~/.ssh の件数 = 1     （器は働く）

### 共有領域と repo の大きさ（**丸めない実数**）

| 対象 | 大きさ (bytes) | 件数 |
|---|---|---|
| `~/claude-sync/` | **存在しない** | — |
| repo `/home/ubuntu/local/m2`（`.git` 込み） | **7,028,316,158** | — |
| repo（file のみ、`.git` を除く） | 6,935,946,154 | **49,918** |
| うち `.venv` | **6,455,707,160** | — |
| うち `.git` | 92,370,004 | — |
| うち `experiments/` | 402,215,550 | — |
| うち `data/` | 23,299,541 | — |
| うち `transfer/` | 839,904 | — |

### 抑止と起動行

    .sync-pause                → 不在（常駐処理が無いため不要。Task 3 で置く）
    ~/.zshrc の keeper 該当行  → 3 件   ← **既に在る**
    陽性対照 ~/.zshrc 総行数   → 138 行

🔴 **`~/.zshrc` に起動行が既に置かれていた**（135–138 行目）。**実行者が書いたものではない。**

    135  # >>> egosurgery keeper >>>
    136  # 常駐スーパーバイザ。flock で多重起動を防ぐため毎回呼んで安全。
    137  ( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
    138  # <<< egosurgery keeper <<<

`~/bin/keeper.sh` が不在のため、**現状は空振りしている。**
SPEC Task 3 Step 3 の「既に在れば追記しない。記録して次へ進む」に従う。

## A2. 控え（完了判定 D）

**repo の外、かつ原本と同一のファイルシステムへ取った。**

🔴 **repo は `~` と別のファイルシステムであった。**

    /home/ubuntu/local/m2                dev=2065  /dev/sdb1  xfs
    /home/ubuntu/.local/state/syncthing  dev=229   overlay
    /home/ubuntu                         dev=229   overlay

退避するのは同期処理の設定と `~/.zshrc` で、**いずれも dev=229 に在る。**
控えの置き場 `/home/ubuntu/.task-stash/T-2026-09-20-dlsta-syncthing-join/` も
**dev=229 で、原本と同一 fs・repo の外**である。

| 控え | 原本との要約値 |
|---|---|
| `config.xml.orig`（6578, 600） | **一致** |
| `zshrc.orig`（4236, 664） | **一致** |

**版管理へは置かない。** `config.xml` は画面の鍵を含むため、伏せる工程を挟むより
版管理の外に留めるほうが誤りが少ない（前契約と同じ判断）。
置かない判断の前提として、**両控えに秘密鍵の塊が 0 件**であることは確かめた。

## A3. 戻し方（完了判定 E / **実行していない**）

    # 1. 起動を止める（実行権を落とせば常駐処理は起こさない）
    chmod 644 ~/bin/syncthing
    pkill -f 'bin/syncthing serve'          # 走っていれば
    # 2. 常駐処理を止める
    pkill -f 'bin/keeper.sh'
    rm -f ~/.keeper.lock
    # 3. 中継を落とす
    pkill -f 'ssh.*-L 22001:127.0.0.1:22000'
    rm -f ~/.tunnel_to_philip
    # 4. 設定を戻す
    cp -p /home/ubuntu/.task-stash/T-2026-09-20-dlsta-syncthing-join/config.xml.orig \
          ~/.local/state/syncthing/config.xml
    chmod 600 ~/.local/state/syncthing/config.xml
    # 5. 起動行を戻す（本契約では追記していないため、通常は不要）
    cp -p /home/ubuntu/.task-stash/T-2026-09-20-dlsta-syncthing-join/zshrc.orig ~/.zshrc
    # 6. 配置した常駐処理を外す
    rm -f ~/bin/keeper.sh ~/bin/m2-sync.sh
    # 7. 除外規則を外す（置いた場合）
    rm -f /home/ubuntu/local/m2/.stignore

**起動の引き金は実行権だけである。** 手順 1 だけで新たな起動は止まる
（`keeper.sh:41` が `[ -x ~/bin/syncthing ]` を見る）。

## A4. 中心への到達（完了判定 F）

**版管理から識別子を読んだ。推測していない。**

    scripts/sync/device_ids/philip.txt → 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
    scripts/sync/device_ids/dlsta.txt  → BRPEYOX-MJ7HMGV-RR2XAUW-CVFVSED-DEMAG5M-EMQNVR6-77XWXPL-ZS26PAI

    設定ファイル内の自分の id と版管理の値の一致 → YES

**命令を伴わない形で入った。** `-N` は「遠隔で命令を実行しない」を意味する
（`ssh(1)`）。**中心では何も実行していない**（禁止 1）。

    timeout 12 ssh -N -v -o BatchMode=yes -o UserKnownHostsFile=<隔離した控え> \
      -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 \
      -i ~/.ssh/id_ed25519_dlstatophilip -p 50072 ubuntu@192.168.196.150

    終了コード = 124                 ← timeout による。-N は繋がり続けるため期待値
    Authenticated to の出現 = 1
    Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey".
    Offering public key: …/id_ed25519_dlstatophilip ED25519 SHA256:5jUsv9rr…KO4 explicit
    Permission denied の出現 = 0
    接続の拒否・到達不能・時間切れの出現 = 0

**指紋は前契約で中心の受け入れ一覧へ入れた値と同じである。**

**`~/.ssh/known_hosts` を汚していない。**

    sha256(前) == sha256(後) → 無変更
    受け入れの控えは隔離先（scratchpad, 142 bytes）に作られた

→ **前契約が UNKNOWN として残した「dlsta から philip へ実際に入れるか」が解消した。**

---

## B. 設定の組み立て（Task 2 / 完了判定 G–L）

**本ホストは未起動のため直接編集した。** 起動後は処理が書き戻すため効かなくなる。

**要素名はすべて実在を確かめてから使った**（`assert` で不在なら止まる形にした）。
編集は `xml.etree.ElementTree` で行い、**既定値のひな型の節は読むだけで編集していない**（禁止 5）。

### 変更の一覧（要素名 / 変更前 / 変更後）

| 要素 | 変更前 | 変更後 | 完了判定 |
|---|---|---|---|
| `options/autoUpgradeIntervalH` | **`12`** | **`0`** | G |
| `options/globalAnnounceEnabled` | **`true`** | **`false`** | H |
| `options/relaysEnabled` | **`true`** | **`false`** | H |
| `options/localAnnounceEnabled` | `true` | `true`（**有効のまま**） | H |
| `device/@name`（自分） | **`4f3861ae8d3b`** | **`dlsta`** | I |
| `device`（中心） | なし | `3J4TRX4…` / `philip` / `tcp://127.0.0.1:22001` | J |
| `folder` | なし | `claude-sync` と `m2` の 2 件 | K |

**自分の登録名の初期値は容器の識別子 `4f3861ae8d3b` であった**（予想せず読んでから直した）。
**置換件数は 1 件**（`id` が版管理の `dlsta.txt` と一致する要素はちょうど 1 件であることを確かめてから変えた）。

### 中心の登録（完了判定 J）

識別子の出所は **`scripts/sync/device_ids/philip.txt`（版管理）**。推測していない。

    3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE

住所は **`tcp://127.0.0.1:22001`**（中継の出口）。**他のノードは登録していない**（星型）。
要素は自分の `device` を複製して作ったため、構造と既定の属性が揃っている。

### 共有フォルダ（完了判定 K）

**設定ファイルでの相手の属性名は `id`。** `defaults/folder` の子要素を読んで確かめた
（`子 <device> 属性キー=['id', 'introducedBy']`）。**推測していない。**
画面の経路での名前 `deviceID` とは異なる（前契約の起票者の誤りの実例）。

| id | label | type | path | 相手 |
|---|---|---|---|---|
| `claude-sync` | `claude-sync` | `sendreceive` | `/home/ubuntu/claude-sync` | 2 件 |
| `m2` | `m2` | `sendreceive` | **`/home/ubuntu/local/m2`** | 2 件 |

🔴 **`m2` の位置は本ホストの実際の値である。** 中心 philip の値は
`/home/ubuntu/slocal2/m2` であり（依存契約の `audit.md:91`）、**写していない。**

識別子は中心と同じ `claude-sync` と `m2` である（同上）。

### 検証（完了判定 L）

**階層を見て数えた**（`root.findall("folder")` は最上位のみを返す。`defaults/folder` は別階層）。

    解析: 成功  version=52
    最上位: folder 2 件 / device 2 件 / gui 1 / ldap 1 / options 1 / defaults 1
    相手の実体: 2 件（dlsta=BRPEYOX…, philip=3J4TRX4…）
    ひな型: defaults/folder id=''  defaults/device id=''  （開始時と同じ。触っていない）
    権限: 600（開始時と同じ）

---

## C. 常駐処理の配置（Task 3 / 完了判定 M–P）

### 正本の配置（完了判定 M）

`keeper.sh:3` の註が「作業ツリーの分岐に依存しないよう git オブジェクトから直接展開する」と
指定しているため、**`git show origin/phase0:` から展開した。**
念のため作業ツリーとの一致も確かめた（両方とも一致）。

| 配置物 | 正本との要約値 | 権限 |
|---|---|---|
| `~/bin/keeper.sh`（2709 bytes） | **一致**（`9fe9c423002e…`） | `755` |
| `~/bin/m2-sync.sh`（7342 bytes） | **一致**（`bcf46ba9031a…`） | `755` |
| `~/bin/syncthing`（27045912 bytes） | 一致（`e8a08fdd…`、前契約で配置） | **`644`（実行権なし）** |

### 構文検査（完了判定 N）

    bash -n ~/bin/keeper.sh    → exit 0
    bash -n ~/bin/m2-sync.sh   → exit 0
    陽性対照（末尾に `if [ 1` を足した写し） → 落ちた（検査は働いている）

### 起動行（完了判定 O）

🔴 **追記していない。開始時から在ったためである**（A1 参照）。

    ~/.zshrc の keeper 該当行 = 3 件（開始時と同じ）
    ~/.zshrc の sha256 が控えと一致 → YES（一文字も変えていない）

### 抑止（完了判定 P）

    touch /home/ubuntu/local/m2/.sync-pause      → 0 bytes で作成
    git check-ignore → .gitignore:240 で無視される（版管理を汚さない）

**配置物が抑止に対応している版であることを確かめた。**

    ~/bin/m2-sync.sh の 'sync-pause' 出現数 = 2   （1 以上で対応版）
      40: if [ -f "$M2DIR/.sync-pause" ]; then
      41:   alert "一時停止中: …"
    陰性対照 'zzz_no_such_token' の出現数 = 0

---

## C2. 除外規則 `.stignore` の設置（**SPEC に無い。利用者の許諾を得て実施**）

🔴 **起動前に見つけた問題。** `m2` 共有フォルダの位置 `/home/ubuntu/local/m2` に
**`.stignore` が存在しなかった。**

    repo 全体      7,028,316,158 bytes
      うち .venv   6,455,707,160 bytes
      うち .git       92,370,004 bytes

`.stglobalignore` は冒頭で **`.git` と `.venv*` を「絶対に同期しない」**と定める。
**除外規則が無いまま起動すると、これらが中心経由で群れ全体へ流れる。**

原因は常駐処理が本ホストの repo を解決できないことである。

    keeper.sh:28   M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)
    m2-sync.sh:10  （同じ行）

    ~/slocal2 exists: NO
    ~/slocal  exists: NO
    → M2DIR = /home/ubuntu/slocal/m2 （存在しない）

したがって `keeper.sh:48-49` の `.stignore` 自動反映は**本ホストでは永久に働かない。**

**利用者へ提示して許諾を得たうえで、keeper と同一の処理を正しい位置へ行った。**
**スクリプトは編集していない**（SPEC Task 3 は正本の配置と要約値の一致を求めるため）。

    git show origin/phase0:.stglobalignore > /home/ubuntu/local/m2/.stignore

    2692 bytes / 正本との要約値 一致 / 実効行数 41
    git check-ignore → .gitignore:192 で無視される（版管理を汚さない）

### 共有領域の用意

`/home/ubuntu/claude-sync` が存在しなかったため作成した（**空。中身は触っていない**、禁止 4）。

    件数 0 / 大きさ 0 bytes

---

## D. 中継を張り、起動する（Task 4 / 完了判定 Q–W）

**順序を守った。** 目印 → 常駐処理 → 中継 → 実行権 → 同期処理。

### 目印（完了判定 Q）

    $ cat -n ~/.tunnel_to_philip
    1  /home/ubuntu/.ssh/id_ed25519_dlstatophilip
    2  192.168.196.150
    権限 600 / 59 bytes / 目印の件数 = 1

`keeper.sh:19-20` と同じ読み方（`sed -n '1p'` / `sed -n '2p'`）で確かめた。
1 行目が指す鍵は実在する。

### 常駐処理（完了判定 R）

    ( nohup ~/bin/keeper.sh >/dev/null 2>&1 & )   ← ~/.zshrc:137 と同じ形
    錠 ~/.keeper.lock が作られた（0 bytes, 21:09:08）
    keeper.sh の件数 = 1

### 中継（完了判定 S）

**起こした直後の周回で立った**（21:09:08 起動 → 21:09:13 の時点で待ち受け確認）。

    port 22001 の待ち受け = 1        （陽性対照 port 22 = 1 / 陰性対照 port 65535 = 0）
    pid=59557 ppid=59550（keeper の子）exe=ssh
      ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i /home/ubuntu/.ssh/id_ed25519_dlstatophilip
          -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes
          -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@192.168.196.150
    → 引数に中心の住所 192.168.196.150 が含まれる

🔴 **最初の計数が誤っていた。** シェルの一行で数えたところ **2 件**と出たが、
実際の中継は 1 件である。**数えている部分シェル自身の命令行に照合語が含まれていた**
（`issuer_cautions` #6）。外側のシェルで作った除外集合は部分シェルを覆わない。

**器を作り直した**（`scratchpad/count_procs.py`）。**`/proc/PID/exe` を `realpath` して
basename で絞り、自分・祖先・子孫をすべて除外する。** 除外集合は器自身の中で作る。

    陽性対照 zsh               → 2 件（1 以上。器は働く）
    陰性対照 zzz_no_such_binary → 0 件

**以後の計数はすべてこの器で行った。**

### 実行権（完了判定 T）

**中継が立っていることを確かめてから戻した。**

    戻す前の sha256 == 戻した後の sha256               → 変わっていない
    中心の期待値 e8a08fdd…b96c4 と一致                  → YES
    権限 644 → 755 / [ -x ] が真
    この時点で port 22001 = 1（中継は維持）/ port 22000 = 0（同期処理はまだ）

### 同期処理の起動（完了判定 U）

`keeper.sh:51` の周期は **1800 秒**である。21:09:08 に起こしたため次の周回は 21:39 であった。
**約 26 分の待ちを避けるため、常駐処理を起こし直した**（逸脱として報告する）。

**中継は別プロセスであり、起こし直しの間も維持された。**

    kill 後: keeper の件数 = 0 / 中継の件数 = 1   ← 中継は残る
    起こし直した後: keeper = 1 / 中継 = 1（重複していない）

**同期処理を起こしたのは常駐処理である**（親子関係が示す）。

    件数 = 2（SPEC の「正常時も二件」と一致）
      pid=61631 ppid=61623（keeper）  exe=syncthing   ← 監視役
      pid=61670 ppid=61631            exe=syncthing   ← 作業役

    版: syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64) 2026-08-03 21:36:05 UTC
    → 中心と同じ v2.1.3

    待ち受け: port 22000 = 1 / port 22001 = 1（中継のまま）/ port 8384 = 1（画面の経路）
    一覧: 22 8384 22000 22001 33059 34303 45053 56304

### 定義が保たれているか（完了判定 V）

**起動時に書き戻されていない。**

    最上位 folder = 2 件 / device = 2 件
      claude-sync  sendreceive  /home/ubuntu/claude-sync   相手 2 件
      m2           sendreceive  /home/ubuntu/local/m2      相手 2 件
    autoUpgradeIntervalH  = 0        （零のまま）
    globalAnnounceEnabled = false    （無効のまま）
    relaysEnabled         = false    （無効のまま）
    localAnnounceEnabled  = true
    ひな型: defaults/folder id='' / defaults/device id=''   （触っていない）
    権限 600

### 中心と繋がった記録（完了判定 W）

    1041: 2026-09-20 21:14:18 INF Established secure connection
          (device=3J4TRX4 connection.local=127.0.0.1:43150 connection.remote=127.0.0.1:22001
           connection.type=tcp-client connection.crypto=TLS1.3-TLS_AES_128_GCM_SHA256 …)
    1042: 2026-09-20 21:14:18 INF Additional device connection (device=3J4TRX4 … count=1)

**中継の出口 `127.0.0.1:22001` を通っている。**

### 除外規則が効いていること

    記録中の '.venv' を含む行        = 0      （運ばれていない）
    記録中の '.git/' を含む行        = 0      （運ばれていない）
    陽性対照 'experiments' を含む行  = 1663   （走査と転送は動いている）
    /rest/db/status の ignorePatterns（m2）= True   ← 除外規則が読まれている

**C2 で置いた `.stignore` が働いている。**

### 本ホストの外向きの住所

| 見え方 | 値 | 出所 |
|---|---|---|
| 容器の内側（中継の足元） | **`172.17.0.12:55930`** | `/proc/net/tcp` の中心宛の確立済み接続 |
| 公開網から見た外向き | **`131.113.39.33:31868`** | `~/.syncthing.log:1286` の `Resolved external address` |
| **中心の側から見た住所** | **UNKNOWN** | 下記 |

🔴 **中心の側から見た住所は測れていない。** 同期処理は中継を通るため、中心から見た相手は
`127.0.0.1:22001` であり、本ホストの住所ではない。SSH の側で中心が見る送信元を知るには
**中心で命令を実行する必要があり、禁止 1 に当たる。**
`scripts/sync/hosts/` が dlsta に与える `192.168.196.54` との照合は、**本契約でも果たせていない。**

🔴 **公開の STUN へ出た。** `告知` と `外部の中継` を無効にしても、
**NAT 越え（`options/natEnabled`）は既定で有効のまま**であり、
起動時に `stun.internetcalls.com:3478` へ問い合わせている。
SPEC が無効化を求めた三要素に `natEnabled` は含まれていない。**指示どおりに実施した結果である。**

---

## E. 実際に届くことの確認（Task 5 / 完了判定 X–AA）

### 試験ファイル（完了判定 X）

    /home/ubuntu/claude-sync/dlsta-join-test-20260920-211747.txt
    大きさ = 120 bytes
    sha256 = 4eb6ae84210789e60324b1a257bdd6203bea1146ad5d86a8183dd43681689cf5
    内容: host=dlsta / task=… / time=2026-09-20T21:17:47+00:00 / nonce=1a03242ea4c96103b408e3dbdfe5cfab

### 中心が持っていること（完了判定 Y）

**中心では命令を実行していない**（禁止 1）。**自ホストの画面の経路へ問い合わせた。**
**合言葉は変数へ読み込み、画面へ出していない**（`gui/apikey` を読むが出力しない）。

**SPEC の警告に従い二度問うた。** 一度目は置いた直後、二度目は落ち着いてから。

| 問い | 1 回目（21:18） | 2 回目（21:19） |
|---|---|---|
| `GET /rest/system/status` の `myID` が版管理と一致 | YES | YES |
| `philip` の接続 | `connected=True` `paused=False` `address=127.0.0.1:22001` `tcp-client` | 同左 |
| `claude-sync` の中心側 completion | **100.0000%** `needBytes=0` `needItems=0` | 同左 |
| `m2` の中心側 completion | **100.0000%** `needBytes=0` `needItems=1` | 同左 |
| **試験ファイルをどの相手から取れるか** | **`['philip']`** | **`['philip']`** |
| **中心が持っている** | **YES** | **YES** |
| 大域の記録 | `size=120` `deleted=False` `version=['BRPEYOX:1789939077']` | 同左 |

**版の欄が `BRPEYOX`（本ホスト）から始まっている。** 本ホストが作り、中心が受け取った。

### 共有領域の増加（完了判定 Z / **実数**）

| 時点 | 大きさ (bytes) | 件数 |
|---|---|---|
| 開始時 | **0**（ディレクトリ自体が無かった） | **0** |
| 21:17 | 937,118 | 18 |
| 21:19 | **937,321** | **18** |

**中心から届いた。** 他台が置いた試験用ファイルは **5 件**である。

    probe-bengio.txt (40 bytes, 2026-08-24)  probe-andrew.txt (83, 2026-08-24)
    probe-ilya.txt   (78, 2026-08-24)        probe-lecun.txt  (86, 2026-08-24)
    probe-efros.txt  (77, 2026-09-17)

**SPEC は「六台が置いた試験用ファイルが届くはず」と述べるが、実測は 5 件である。**
中心 philip は `probe-philip.txt` を置いておらず、代わりに `sync-alerts.log`（103,697 bytes）と
その衝突ファイル 10 件を持つ。**六件目は存在しない。**

**記録の衝突は正常である。** 衝突ファイル 10 件はいずれも `-3J4TRX4`（中心）由来で、
**本ホスト由来（`BRPEYOX`）の衝突は 0 件**である。

### repo の同期の進み方（完了判定 AA / **完了を待たない**）

| 指標（21:19 時点） | `claude-sync` | `m2` |
|---|---|---|
| state | `idle` | **`syncing`** |
| completion（自ホスト） | **100.0000%** | **2.0805%** |
| localBytes | 937,204 | **2,148,216,076** |
| localFiles | 17 | 6,540 |
| globalFiles | 17 | **228,850** |
| needBytes | 0 | **101,106,163,502** |
| needItems | 0 | **223,691** |
| ignorePatterns | False | **True** |

repo の実測（`.git` を除く）は **6,935,946,154 → 9,083,344,492 bytes**（**+2,147,398,338**、約 4 分で）。

**受け取り切るには 101 GB が要る。容量は足りる。**

    repo の載る /dev/sdb1 (xfs, /home/ubuntu/local): 全体 11,998,000,558,080 / 空き 8,326,007,549,952
    受取予定 101,106,226,157  → 差 8,224,901,323,795（足りる）
    容量保護: options/minHomeDiskFree = 1% / 各 folder の minDiskFree = 1%

**完了は待っていない**（SPEC の指示）。

### 常駐処理の副作用（M2DIR の欠陥の実地での現れ）

    ~/claude-sync/sync-alerts.log の '[dlsta]' の行 = 0    （本ホストは一行も書いていない）
    陽性対照 '[philip]' の行 = 139
    ~/bin/m2-sync.sh.new = 0 bytes（21:14）   ← keeper の自己更新が空を書いて失敗した残骸
    ~/bin/m2-sync.sh の要約値は正本のまま      ← 自己更新は働いていない
    本ホスト由来の衝突ファイル = 0 件

`m2-sync.sh:25` の `cd "$M2DIR" || exit 1` は、記録へ書く `alert()`（23 行目で定義）が
呼ばれる前に位置する。**したがって本ホストの m2-sync は何も記録せず即座に終わる。**
`.sync-pause` を見る 40 行目にも到達しない。**抑止は本ホストでは空振りである。**

**分岐は動いていない。**

    git --no-pager log --oneline -1 → 6b163bf2（開始時と同じ）
    git --no-pager status --porcelain → 契約のディレクトリ 1 件のみ

---

## F. 送出前の検査（Task 6 / 完了判定 AB–AG）

### 触っていないものの無変更（完了判定 AC）

**本契約の開始（21:0x）より後に変わった `~/.ssh/` の要素は 1 件だけである。**

    find ~/.ssh -maxdepth 1 -newermt '2026-09-20 21:00'
      → /home/ubuntu/.ssh/known_hosts  2026-09-20 21:09:08

| 対象 | 権限 | 更新時刻 | 判定 |
|---|---|---|---|
| `authorized_keys` | 600 | 2026-09-20 13:52:18 | **無変更**（本契約の開始より前）。行数 2 |
| `config` | 600 | 2026-08-18 12:54:41 | 無変更 |
| `id_ed25519_github` / `.pub` | 600 / 644 | 2026-09-20 14:18:10 | 無変更 |
| `id_ed25519_dlstatophilip` / `.pub` | 600 / 644 | 2026-09-20 14:50:03 | 無変更（**前契約で作った時刻のまま**） |
| **`known_hosts`** | 644 | **2026-09-20 21:09:08** | **変わった**（下記） |

**`known_hosts` の変化は実行者の操作ではない。** `keeper.sh:35` の
`-o StrictHostKeyChecking=accept-new` を付けた中継の ssh が中心の鍵を追記した。

    ~/.tunnel.log: Warning: Permanently added '[192.168.196.150]:50072' (ED25519) to the list of known hosts.
    行数 1 → 2 / ssh-keygen -F '[192.168.196.150]:50072' の該当 = 1
    （HashKnownHosts が既定で有効なため、住所の文字列では引けない）

**鍵を生成・変更・削除していない**（禁止 3）。

    中心宛の鍵の指紋 = SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4
    前契約の報告の値 = SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4   → 一致
    ~/.ssh 直下の鍵の件数 = 4（github 2 + 中心宛 2）

**目印は 1 件である。**

    ~/.tunnel_to_* の件数 = 1   （~/.tunnel_to_philip、600、59 bytes）

### 検証（完了判定 AB）

    make task-validate    → exit 0（1 task(s), 0 failed）
    make task-preflight   → exit 0（5 PASS / 1 WARN / 7 SKIP / 0 FAIL）
    make taskindex-check  → exit 0
    make inbox-check      → exit 0
    make forbidden-check  → exit 0（status: pass / violations: 0 / changed: 10 / excluded: 4）

`P9 spec_lint` の WARN は `host_mismatch`。規則が `socket.gethostname()`（= `4f3861ae8d3b`）と
本文の宣言 `dlsta` を比べており、**本ホストでは必ず該当する既知の限界**である
（前契約と同じ。`tasks/inbox.md` に既出）。

**SKIP された 7 件**: `P2 cuda_ext_loaded` `P3 deterministic_flags`（`plan.env.preflight` に記載なし）、
`P4 prereg_committed` `P5 frozen_source_hash` `P13 symmetry_table_complete`（`kind=impl` のため対象外）、
`P11 gpu_free`（記載なし）、`P12 refs_resolved`（解決前提の参照なし）。

`conventions_rev` は**実測して置換不要と判断した**。

    git --no-pager log -1 --format='%h' -- context/conventions.md → c801e17c
    契約の記載 → "c801e17"（接頭辞であり一致）

### 禁止語（完了判定 AD）

送出物 6 件すべて `exit 0` / `status: pass` / 禁止語 0 件 / errors 0 件。

**陽性対照**: 禁止語 3 語を含む囮は `exit 1` / `status: fail` / 禁止語 **3 件**。
**囮は版管理へ入れていない**（`git status` の該当 0 件）。

集約 `tasks/inbox.md` は該当 **8 件**を持つが、**`origin/phase0` の版も 8 件で増えていない。**
いずれも他契約の 2026-08 の行であり、**本契約の追加分は 0 件**である。

### 秘匿（完了判定 AE）

**形で判定し、検査自身は長さと件数だけを出力する**（禁止 8）。対象は送出される 10 件。

| 検査 | 送出物での出現 | 陽性対照 |
|---|---|---|
| 秘密鍵の塊（開始と終了の標識に挟まれた本体） | **0** | 中心宛の鍵ファイル → **1** |
| 中心宛の秘密鍵の本体（長さ 324） | **0** | **1** |
| **画面の鍵**（同期処理の `apikey`、長さ 32） | **0** | **1** |
| `WANDB_API_KEY`（86）/ `WANDB_PROJECT`（20）/ `WANDB_ENTITY`（10） | **各 0** | **各 1** |
| `DATA_ROOT`（13）/ `NOTION_API_KEY`（50） | **各 0** | **各 1** |
| 合言葉（長さ 15） | **0** | **1** |
| **同期処理の機器の秘密鍵** `key.pem` の本体（長さ 64） | **0** | **1** |

**照合できた資格情報は 5 / 5 で、SKIP は無い。**

### 変更の範囲（完了判定 AF）

**10 件すべてが契約のディレクトリと受け皿、および生成物に限られる。**

    tasks/T-2026-09-20-dlsta-syncthing-join/   （RESULT.md / audit.md / result.yaml / SPEC.md / spec.yaml）
    tasks/inbox.d/T-2026-09-20-dlsta-syncthing-join.md
    context/auto/（3 件）・tasks/inbox.md        ← 生成物（道具が検査から除外する）

**repo の中で同期処理が運んだものは版管理の対象外である**（`.gitignore` と `.stignore` の両方に落ちる）。
`git status --porcelain` の追跡下の変更は **0 件**である。

### 退避（完了判定 AG）

**退避は行っていない。戻すものは 0 件であり、入れ子も生じていない。**

0 節は「開始前から在る未追跡は退避してよい」と述べるが、開始時の作業ツリーは
**本契約のディレクトリ 1 件のみ**で、分岐 `feat/dlsta-syncthing-join` も既に在ったため
切り直しが不要であった。A2 で取った控えは**退避ではなく控えであり、戻さない**
（戻すと本契約の設定がすべて失われる）。

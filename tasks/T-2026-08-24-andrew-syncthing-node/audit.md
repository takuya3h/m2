# audit — T-2026-08-24-andrew-syncthing-node

**手続きの証跡。** 命令とその出力、参照の解決の全文、検証の出力、秘匿検査の出力、
変更範囲の一覧、台帳の応答をここへ置く。判断と結論は `RESULT.md` にある。

**host:** `Andrew`（`hostname` の実測。SPEC の表記は `andrew`）
**repo:** `/home/ubuntu/slocal2/m2`  **branch:** `feat/andrew-syncthing-node`
**開始:** 2026-08-24 15:06 UTC（= 2026-08-25 00:06 JST）

---

## 0. 前提

    $ hostname
    Andrew
    $ git branch --show-current
    feat/andrew-syncthing-node
    $ date -u '+%Y-%m-%dT%H:%M:%SZ'
    2026-08-24T15:06:28Z

### 抑止（SPEC §0）

    $ cd ~/slocal2/m2 && touch .sync-pause && ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 24 15:06 .sync-pause
    $ grep -c "sync-pause" ~/bin/m2-sync.sh
    2

**`2` なので稼働中の版が抑止に対応している。** さらに**効いていることを記録で実測した**
（推定ではない）:

    $ grep '一時停止中' ~/claude-sync/sync-alerts.log | tail -1
    2026-08-24 15:08:21 [andrew] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）

### `make task-start` — 適用できなかった

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-08-24-andrew-syncthing-node
    ?? tasks/T-2026-08-24-andrew-syncthing-node/
    [task-start] 作業ツリーに未commitの変更が 1 件あります。片付けてから実行してください
    make: *** [Makefile:205: task-start] Error 3

未commitの 1 件は**契約そのもの**（`tasks/T-2026-08-24-andrew-syncthing-node/`）である。
`scripts/task_start.sh` は分岐が既にあるときも拒否する（`--- 5. 分岐が既に存在しないか ---`）。
**分岐 `feat/andrew-syncthing-node` と契約は既に存在するため、この命令は原理的に通らない。**
前契約（bengio）も同じ理由で実行していない。**逸脱として記録する。**

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md:98-107` の**原文**（要約していない）:

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `contract.conventions_rev` — 実測して照合した（置換は不要だった）

    $ git --no-pager log -1 --format=%h -- context/conventions.md
    d422b08

`spec.yaml` の `conventions_rev: "d422b08"` と**一致する。置換していない。**

### 中心の値（**本文の転記を信用せず版管理から読んだ**）

    $ cat scripts/sync/device_ids/philip.txt
    3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
    $ cat scripts/sync/device_ids/andrew.txt
    3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4

| 項目 | 出所 | 実測 |
|---|---|---|
| 中心の識別子 | `scripts/sync/device_ids/philip.txt` | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| 自分の識別子 | `scripts/sync/device_ids/andrew.txt` | `3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4` |
| 中心の SSH 住所 | 前契約 `tasks/T-2026-08-24-bengio-syncthing-node/audit.md:547,646` | `192.168.196.150` 口 `50072` |
| 中心の実行ファイル | 前契約 `RESULT.md`（判定 H） | `e8a08fdd8b25…b96c4` 27045912 B v2.1.3 |
| 中継の出口（syncthing の住所） | SPEC | `tcp://127.0.0.1:22001` |

**`inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は本契約の作業に現れない。
参照していない。**（前契約も同じ指摘をしている）

**中心の住所について。** `tasks/T-2026-08-12-submit-hub-key-andrew/handoff.md:8` は
2 行目を `192.168.196.176` と**案として**書くが、これは古い。前契約の**実測**
（`Authenticated to 192.168.196.150`）を正とした。SPEC の申し送り #1 に従う。

---

## 2. Task 1 (Phase A) — 開始状態の封印と中心への到達

### Step 1: 現状を要約値で記録する

    $ stat -c '%n perm=%a size=%s' ~/bin/syncthing ; sha256sum ~/bin/syncthing
    /home/ubuntu/bin/syncthing perm=644 size=26730145
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing

    $ for f in config.xml cert.pem key.pem; do stat -c '%n perm=%a size=%s' ~/.local/state/syncthing/$f; sha256sum ~/.local/state/syncthing/$f; done
    /home/ubuntu/.local/state/syncthing/config.xml perm=600 size=8495
    c3783e9d013c503eb78714f6342f8378c574f76685fa8348db6d98e3b51b3030  …/config.xml
    /home/ubuntu/.local/state/syncthing/cert.pem perm=664 size=794
    bb9a4442311af69d965c4ecb12413071719d1e63c6617625f3be4605de85d141  …/cert.pem
    /home/ubuntu/.local/state/syncthing/key.pem perm=600 size=288
    92f44d2e29e3b4bec46e0eff8c90db336573ef4e429051c83e757556c7e6a904  …/key.pem

    $ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh

    $ sha256sum ~/slocal2/m2/.stignore ~/slocal2/m2/.stglobalignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  …/.stignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  …/.stglobalignore

**実行権は `644`**（起動しない状態）。除外規則は 2 ファイルとも同一で、
前契約 bengio の実測 `61593e99…` とも一致する。
`~/claude-sync/.stignore` と `~/claude-sync/.stglobalignore` は**不在**である
（「無い」と「読めない」の区別 — `ls` が `No such file or directory` を返した）。

#### 中継の目印

    $ ls -la ~/.tunnel_to_philip
    ls: cannot access '/home/ubuntu/.tunnel_to_philip': No such file or directory
    $ ls -1 ~/.tunnel_to_philip 2>/dev/null | wc -l
    0

**marker_count=0。**

#### 共有領域と repo の大きさ（**丸めていない実数**。申し送り #2）

    $ du -sb ~/claude-sync
    1510    /home/ubuntu/claude-sync
    $ find ~/claude-sync -type f | wc -l
    1
    $ find ~/claude-sync -mindepth 1 -printf '%s\t%p\n'
    1510    /home/ubuntu/claude-sync/sync-alerts.log
    $ du -sb ~/slocal2/m2
    54745194976    /home/ubuntu/slocal2/m2

| 項目 | 実数 |
|---|---|
| `~/claude-sync` 合計 | **1510 バイト** |
| `~/claude-sync` の件数 | **1 件**（`sync-alerts.log` のみ） |
| repo `~/slocal2/m2` | **54745194976 バイト**（= 54.7 GB。`.git` を含む） |

**`du -sb` は最上位ディレクトリ自身の 4096 バイトを合計へ入れていない**
（`stat` は `~/claude-sync` を 4096 と報告する）。**両方測って記録する。**

#### 稼働しているものの計数（**両方向の対照つき**。申し送り #5）

`pgrep -f` と `ps|grep` は自己一致するため使わない。**`/proc/*/cmdline` の
`argv[0]` の基底名で照合した**（補助: `scratchpad/procs.py`）。

    $ python3 procs.py syncthing ssh zsh zzz_no_such_exe
    syncthing_count=0
    ssh_count=0
    zsh_count=3
      pid=63104 ppid=61548 argv=/usr/bin/zsh
      pid=78401 ppid=61548 argv=/usr/bin/zsh
      pid=80959 ppid=78754 argv=/usr/bin/zsh -c …
    zzz_no_such_exe_count=0

| 対照 | 語 | 件数 | 意味 |
|---|---|---|---|
| 肯定 | `zsh` | **3** | 実在する語で 1 以上 → 検査は働いている |
| 否定 | `zzz_no_such_exe` | **0** | 存在しない語で 0 → 常に非零を返す壊れ方ではない |
| 測定対象 | `syncthing` | **0** | 同期処理は零件 |
| 測定対象 | `ssh` | **0** | 中継は零件（`sshd` は別の実行ファイル名） |

**片方向では「常に零を返す壊れ方」と区別できない。両方向を取った。**

#### 常駐処理は動いている（禁止 12 により停止・再起動しない）

    $ python3 procs.py bash
    bash_count=1
      pid=40838 ppid=1 argv=/bin/bash /home/ubuntu/bin/keeper.sh

`argv[0]` は `/bin/bash` であるため実行ファイル名での照合では `keeper.sh` に一致しない。
**引数まで見て特定した。**

#### 起動前に記録が無いこと

    $ ls -la ~/.tunnel.log ~/.syncthing.log
    ls: cannot access '/home/ubuntu/.tunnel.log': No such file or directory
    ls: cannot access '/home/ubuntu/.syncthing.log': No such file or directory

#### 設定の階層（**単純検索ではひな型を拾う**。申し送り #7 の実証）

    root = configuration attrib = {'version': '37'}
    top-level <defaults> x1
    top-level <device> x1
    top-level <folder> x1
    top-level <gui> x1
    top-level <ldap> x1
    top-level <options> x1
    --- 最上位の folder ---
      folder id='default' label='Default Folder' path='/home/ubuntu/Sync' type='sendreceive'
    --- 最上位の device ---
      device id=3C2LTP7-…-UVZB5A4 name='Andrew'
    --- defaults 配下（触らない。禁止 5） ---
      defaults/<folder> id=''
      defaults/<device> id=''
      defaults/<ignores> id=None
    --- 単純検索との差 ---
      naive findall(".//folder") = 2
      top-level  findall("folder") = 1

**単純検索は 2、階層を見た数は 1。差はひな型 `defaults/<folder id="">` である。**
以後の計数はすべて**最上位のみ**で行う。

**登録名は `Andrew`（先頭が大文字）。** 前契約 bengio と同じつまずきが本ホストでも起きている。

### Step 2: 控えを repo の外へ取る

    $ BAK=~/.local/state/syncthing.bak.$(date -u +%Y%m%d-%H%M%S)
    $ cp -a ~/.local/state/syncthing "$BAK"
    backup=/home/ubuntu/.local/state/syncthing.bak.20260824-150939
    config.xml MATCH
    cert.pem   MATCH
    key.pem    MATCH

**控えは repo の外だけにある。版管理へは置かない。** 理由は次の実測である。

#### 秘匿の混入検査（**値を出していない。長さと有無で測る**。申し送り #6）

    apikey_elements=1
    apikey_len=32 empty=False
    gui_password_present=False len=n/a
    gui_address='127.0.0.1:8384' tls='false'
    PEM_PRIVATE_in_config=0
    OPENSSH_PRIVATE_in_config=0
    PEM_CERT_in_config=0
    positive_control OPENSSH_PRIVATE_on_decoy=1

**画面の鍵が 32 文字で実在する** → 版管理へ置かない（禁止 8）。
**秘密鍵の書き出しの混入は零。** 陽性対照（囮を末尾に足した文字列）で **1** を返すため、
**検査は働いたうえで該当が無い。** 囮は変数の中だけで、ファイルにも記録にも残していない。

### Step 3: 戻し方（**記録するだけ。実行していない**）

開始状態へ戻す手順は次のとおりである。**上から順に実行する。**

    # 1. 起動を止める（実行権を落とせば常駐処理は起こさない。keeper.sh は `[ -x ~/bin/syncthing ]` を見る）
    chmod 644 ~/bin/syncthing
    #    既に動いている同期処理があれば、その後に自然終了を待つか個別に止める
    #    （禁止 12 は常駐処理 keeper.sh の停止を禁じる。syncthing 本体は対象外）

    # 2. 中継を止める（目印を消せば常駐処理は張り直さない）
    rm -f ~/.tunnel_to_philip

    # 3. 設定を開始状態へ戻す
    cp -a /home/ubuntu/.local/state/syncthing.bak.20260824-150939/config.xml ~/.local/state/syncthing/config.xml
    cp -a /home/ubuntu/.local/state/syncthing.bak.20260824-150939/cert.pem   ~/.local/state/syncthing/cert.pem
    cp -a /home/ubuntu/.local/state/syncthing.bak.20260824-150939/key.pem    ~/.local/state/syncthing/key.pem
    chmod 600 ~/.local/state/syncthing/config.xml ~/.local/state/syncthing/key.pem
    chmod 664 ~/.local/state/syncthing/cert.pem

    # 4. 実行ファイルを開始状態へ戻す（退避した旧版から）
    cp -a /tmp/syncthing.v1.bak ~/bin/syncthing && chmod 644 ~/bin/syncthing

    # 5. 要約値で戻ったことを確かめる（申し送り #8）
    sha256sum ~/bin/syncthing        # → 32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd
    sha256sum ~/.local/state/syncthing/config.xml
    # → c3783e9d013c503eb78714f6342f8378c574f76685fa8348db6d98e3b51b3030
    #   ただし一度起動すると設定は書き戻され version 37 → 52 へ移行するため
    #   **要約値は戻らない。** その場合は控えからの上書き（手順 3）が唯一の戻し方である。

**要点: 実行権を `644` に落とせば起動は止まる。** `keeper.sh` は
`if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing` で起動を判断するためである。

### Step 4: 中心の値を版管理から読み、到達を確かめる

#### 自分の識別子が設定と一致するか

    設定内の device id = 3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4
    scripts/sync/device_ids/andrew.txt = 3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4
    → 一致

#### 鍵の指紋（**`~/.ssh/**` は実行基盤の deny 規則で読めない**）

    $ stat -c '%a %n' ~/.ssh/id_ed25519_andrewtophilip
    Permission to use Bash with command … has been denied.

前契約と同じ環境制約である。**版管理側の公開鍵で照合した。**

    $ ssh-keygen -lf scripts/sync/hub_keys/andrew.pub
    256 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 andrewtophilip (ED25519)

前契約 `T-2026-08-24-philip-accept-node-keys/audit.md:131` の実測と**一致する。**

#### 中心への到達（**`ssh -N`。中心で命令を実行していない**。禁止 1）

    $ timeout 20 ssh -v -N -p 50072 -i ~/.ssh/id_ed25519_andrewtophilip \
        -o StrictHostKeyChecking=accept-new \
        -o UserKnownHostsFile=<SCRATCH>/kh_isolated \
        -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 \
        ubuntu@192.168.196.150
    ssh_exit=124   ← timeout(1) の戻り。**打ち切られるまで接続が維持された**

    debug1: Connection established.
    debug1: Offering public key: <KEYDIR>/id_ed25519_andrewtophilip ED25519 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 explicit
    debug1: Server accepts key: <KEYDIR>/id_ed25519_andrewtophilip ED25519 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 explicit
    Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey".

    denied_count=0
    authenticated_count=1

🟢 **中心へ入れた。** `ssh -N` は遠隔で命令を実行しない形である。
`exit 124` は `timeout` が 20 秒で打ち切ったことを示し、**接続が生きていた証拠である**
（拒否されていれば 20 秒より早く非 124 で終わる）。

#### 受け入れの控えを隔離した（`~/.ssh/known_hosts` を汚していない）

    $ ls -la <SCRATCH>/kh_isolated
    -rw-r--r-- 1 ubuntu ubuntu 142 Aug 24 15:11 …/kh_isolated
    $ wc -l < <SCRATCH>/kh_isolated
    1
    $ cut -d' ' -f1-2 <SCRATCH>/kh_isolated
    |1|IYBiHRcfjXQ6cSHTIDVuiJhNiQk=|Wps6O5vYE2jdIqzD8JRcQnAEuCA= ssh-ed25519

`~/.ssh/known_hosts` は deny 規則で読めないため要約値での前後比較はできないが、
**`UserKnownHostsFile` を隔離先へ向けているため書き込みはそちらへ入る。**
実際に隔離先が 1 行増えている。

---

## 3. Task 2 (Phase B) — 版を揃え、設定を組み立てる

**停止中に直接編集した。** 命令列（`syncthing cli`）は常駐を要するため使えない。

### Step 1: 版を中心に揃える

#### 旧実行ファイルの退避と現在の版

    $ cp -a ~/bin/syncthing /tmp/syncthing.v1.bak && sha256sum /tmp/syncthing.v1.bak
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /tmp/syncthing.v1.bak

    $ cp /tmp/syncthing.v1.bak /tmp/syncthing.probe && chmod 755 /tmp/syncthing.probe
    $ /tmp/syncthing.probe --version
    syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC
    $ rm -f /tmp/syncthing.probe
    $ stat -c '%n perm=%a' ~/bin/syncthing
    /home/ubuntu/bin/syncthing perm=644

**版を問うために `~/bin/syncthing` の実行権を戻していない。** 控えの複製を
`/tmp` で一時的に実行可能にして問い、直後に消した。

#### 取得と展開

    $ curl -fsSL -o /tmp/syncthing-linux-amd64-v2.1.3.tar.gz \
        https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz
    curl_exit=0
    -rw-rw-r-- 1 ubuntu ubuntu 11821325 Aug 24 15:14 syncthing-linux-amd64-v2.1.3.tar.gz
    f929eb8e5b72a85543eeeefb2c38f34a68e0c530e70758a2905b78840c76602c  …tar.gz

**取得物は前契約 bengio の実測（`f929eb8e…` / 11821325 B）と一致する。**

    $ tar xzf … -C /tmp/st213 && find /tmp/st213 -name syncthing -type f -printf '%p size=%s perm=%m\n'
    /tmp/st213/syncthing-linux-amd64-v2.1.3/syncthing size=27045912 perm=755
    /tmp/st213/syncthing-linux-amd64-v2.1.3/etc/freebsd-rc/syncthing size=1709 perm=644
    /tmp/st213/syncthing-linux-amd64-v2.1.3/etc/firewall-ufw/syncthing size=175 perm=644

**配布物の中にも同名の別物が三件ある**（申し送り #7 と同じ罠）。
**大きさと要約値で本体を特定した。**

    $ sha256sum /tmp/st213/syncthing-linux-amd64-v2.1.3/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    $ cp … ~/bin/syncthing && chmod 644 ~/bin/syncthing
    $ stat -c '%n perm=%a size=%s' ~/bin/syncthing ; sha256sum ~/bin/syncthing
    /home/ubuntu/bin/syncthing perm=644 size=27045912
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4  /home/ubuntu/bin/syncthing

🟢 **中心の実測値 `e8a08fdd8b25…b96c4` / 27045912 B と完全一致。実行権は `644` のまま。**

### Step 2〜5: 設定の編集

**要素名は実在を確かめてから変えた**（版によって異なるため）。

    --- options 配下の実在と現在値（編集前） ---
      <autoUpgradeIntervalH> exists x1 value=['12']
      <globalAnnounceEnabled> exists x1 value=['true']
      <localAnnounceEnabled> exists x1 value=['true']
      <relaysEnabled> exists x1 value=['true']
      <upgradeToPreReleases> exists x1 value=['false']

**編集対象がすべて一意であることを先に測った**（誤爆の防止）:

    '^    <folder '           -> 1
    '^    <device '           -> 1
    '<autoUpgradeIntervalH>'  -> 1
    '<globalAnnounceEnabled>' -> 1
    '<relaysEnabled>'         -> 1
    '<localAnnounceEnabled>'  -> 1
    'name="Andrew"'           -> 1

`<defaults>` 配下は 8 桁字下げ、最上位は 4 桁字下げである。
**正規表現を `^    ` に固定したため `<defaults>` には当たらない**（禁止 5）。
設定に注釈は無い（`comments = 0`）ため、生の XML の置換で書式が壊れない。

編集は `scratchpad/build_config.py` が行った。**各置換は件数 1 を表明（`assert n == 1`）
しており、当たらなければその場で失敗する。**

| # | 変更 | 前 | 後 |
|---|---|---|---|
| Step 2 | `options/autoUpgradeIntervalH` | `12` | **`0`** |
| Step 3 | `options/globalAnnounceEnabled` | `true` | **`false`** |
| Step 3 | `options/relaysEnabled` | `true` | **`false`** |
| Step 3 | `options/localAnnounceEnabled` | `true` | **`true`（変えない）** |
| — | 自分の登録名 | `Andrew` | **`andrew`** |
| Step 4 | 中心の登録 | 無し | `id=3J4TRX4-…-DZOCQQE` name=`philip` address=`tcp://127.0.0.1:22001` |
| Step 5 | 共有フォルダ | `default`（`/home/ubuntu/Sync`） | **`claude-sync` と `m2`** |

**登録名の `Andrew` → `andrew`。** 前契約 bengio の申し送り
（「bengio の初期値は `Bengio` だった。他の三台も確かめること」）が本ホストでも当たった。

**他のノード（`bengio` `ilya` `lecun`）は登録していない。** 星型であるため。

### Step 6: 書式と定義を確かめる

    $ python3 verify_config.py
    xml_ok=True root=configuration version=37
    top_level_folder_count=2
    top_level_device_count=2
    naive_folder_count=3  (差はひな型)
    naive_device_count=8  (差はひな型と folder 配下の共有相手)
      folder id='claude-sync' path='/home/ubuntu/claude-sync' type='sendreceive' shared_with=2 ['3C2LTP7', '3J4TRX4']
      folder id='m2'          path='/home/ubuntu/slocal2/m2' type='sendreceive' shared_with=2 ['3C2LTP7', '3J4TRX4']
      device id=3C2LTP7-…-UVZB5A4 name='andrew' address='dynamic'
      device id=3J4TRX4-…-DZOCQQE name='philip' address='tcp://127.0.0.1:22001'
      options/autoUpgradeIntervalH=0
      options/globalAnnounceEnabled=false
      options/localAnnounceEnabled=true
      options/relaysEnabled=false
    --- defaults 配下（触っていないこと） ---
      defaults/<folder> id=''
      defaults/<device> id=''
      defaults/<ignores> id=None

**最上位の folder は 2 件。単純検索は 3 件を返す。差はひな型である。**
**識別子 `claude-sync` と `m2` は中心と同じ**（前契約 bengio の判定 M で同じ 2 語が使われている）。

    $ stat -c '%n perm=%a size=%s' ~/.local/state/syncthing/{config.xml,cert.pem,key.pem}
    …/config.xml perm=600 size=11359
    …/cert.pem   perm=664 size=794
    …/key.pem    perm=600 size=288
    $ sha256sum ~/.local/state/syncthing/config.xml
    5ea372243966ccc4e9e6e99f4eda308786125fc311f96f45d54588b638e7fa3c

**鍵は触っていない**（要約値で確認。申し送り #8）:

    bb9a4442311af69d965c4ecb12413071719d1e63c6617625f3be4605de85d141  cert.pem   ← 開始時と同じ
    92f44d2e29e3b4bec46e0eff8c90db336573ef4e429051c83e757556c7e6a904  key.pem    ← 開始時と同じ

**まだ起動していない**（実行権 `644`）:

    $ python3 procs.py syncthing ssh
    syncthing_count=0
    ssh_count=0

---

## 4. Task 3 (Phase C) — 中継を張り、起動する

**順序: 目印 → 中継 → 実行権 → 起動。**

### Step 1: 目印を置く

    $ umask 077
    $ printf '%s\n%s\n' "$HOME/.ssh/id_ed25519_andrewtophilip" "192.168.196.150" > ~/.tunnel_to_philip
    $ chmod 600 ~/.tunnel_to_philip
    $ stat -c '%n perm=%a size=%s' ~/.tunnel_to_philip
    /home/ubuntu/.tunnel_to_philip perm=600 size=60
    $ wc -l < ~/.tunnel_to_philip
    2
    $ cat ~/.tunnel_to_philip   （鍵の置き場を伏せて表示）
    <KEYDIR>/id_ed25519_andrewtophilip
    192.168.196.150

    marker_placed_at=2026-08-24T15:18:02Z

**1 行目が鍵の経路、2 行目が中心の住所。権限は所有者だけが読める `600`。**
`keeper.sh` の `resolve_tunnel()` はこの 2 行をそれぞれ `TUNNEL_KEY` と
`HUB_ADDRESS` として読む（`sed -n '1p'` / `sed -n '2p'`）。

### Step 2: 中継が立つのを待ち、確かめる

    $ date -u '+%Y-%m-%dT%H:%M:%SZ'
    2026-08-24T15:38:39Z
    $ python3 ports.py 22000 22001 8384
    port_22000=CLOSED hits=0
    port_22001=LISTEN hits=2
    port_8384=CLOSED hits=0
    positive_control port_22(sshd)=LISTEN hits=2
    negative_control port_1=CLOSED hits=0
    total_tcp_rows=22

🟢 **`22001` が待ち受けている。** 対照は両方向とも期待どおり
（実在する口 `22` が LISTEN、使われていない口 `1` が CLOSED）。

    $ python3 procs.py ssh
    ssh_count=1
      pid=86521 ppid=40838 argv=ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <KEYDIR>/id_ed25519_andrewtophilip -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@192.168.196.150

**引数に中心の住所 `ubuntu@192.168.196.150` を含む。**
**親は `40838` = `keeper.sh` である**（常駐処理が張った。自分では張っていない）。

    $ tail -5 ~/.tunnel.log
    Warning: Permanently added '[192.168.196.150]:50072' (ED25519) to the list of known hosts.

**この行は常駐処理が張った中継によるものである。** 自分が Task 1 Step 4 で行った
到達確認は `UserKnownHostsFile` を隔離先へ向けており、`~/.ssh/known_hosts` へ書いていない。

#### 待ち時間の実測

| 事象 | 時刻 (UTC) |
|---|---|
| 目印を置いた | `15:18:02` |
| 中継が立った | `15:38:29` |
| **経過** | **1227 秒（20 分 27 秒）** |

`keeper.sh` の周回は `sleep 1800`（30 分）である。抑止の記録が `15:08:21` にあるため、
次の周回は `15:38` 前後になる。**実測はこれと一致する。**
前契約 bengio は 413 秒だった。**目印を置いた時刻と周回の位相の差であり、ホスト差ではない。**

`ssh` は `-N`（遠隔で命令を実行しない）で張られている。**中心の状態を変えていない。**

### Step 3: 実行権を戻す（**中継が立ってから**）

    $ stat -c '%n perm=%a size=%s ctime=%z' ~/bin/syncthing   # 戻す前
    /home/ubuntu/bin/syncthing perm=644 size=27045912 ctime=2026-08-24 15:14:59.241953803 +0000
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4

    $ chmod 755 ~/bin/syncthing
    $ stat -c '%n perm=%a size=%s ctime=%z' ~/bin/syncthing   # 戻した後
    /home/ubuntu/bin/syncthing perm=755 size=27045912 ctime=2026-08-24 15:39:16.359596127 +0000
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4

**要約値は変わっていない**（`chmod` は中身を変えないため。ctime だけが動く）。

#### 順序の実測（**待ち受けで示す**。時刻の主張ではない）

| 事象 | 時刻 (UTC) | 根拠 |
|---|---|---|
| 目印 | `15:18:02` | `date` の出力 |
| **中継が `22001` を待ち受け** | **`15:38:29`** | `/proc/net/tcp` の復号（監視が検出） |
| **実行権を `755` へ** | **`15:39:16`** | `stat` の `ctime` |

**中継の成立が実行権の復帰より 47 秒早い。** `15:38:39` 時点の測定で
`port_22001=LISTEN` かつ `~/bin/syncthing perm=644` を**同時に**観測している
（上の Step 2 と Step 3 の「戻す前」）。**順序は満たされている。**

### Step 4: 起動を待ち、確かめる

**常駐処理が起こした。** `15:38:21` の周回では実行権がまだ `644` だったため
起こされず（順序どおり）、次の周回 `16:08` で起きた。

    $ date -u ; python3 procs.py syncthing ssh
    2026-08-24T16:08:57Z
    syncthing_count=2
      pid=89005 ppid=40838 argv=/home/ubuntu/bin/syncthing serve --no-browser
      pid=89026 ppid=89005 argv=/home/ubuntu/bin/syncthing serve --no-browser
    ssh_count=1
      pid=86521 ppid=40838 argv=ssh -N -L 22001:127.0.0.1:22000 … ubuntu@192.168.196.150

**プロセスは 2 件。親子関係で切り分けた**（申し送り／つまずき #4）:

| pid | 親 | 役 |
|---|---|---|
| `89005` | `40838`（= `keeper.sh`） | 監視役。常駐処理が直接起こした |
| `89026` | `89005` | 作業役。監視役の子 |

**3 件以上ではない。想定内である。**

    $ python3 ports.py 22000 22001 8384
    port_22000=LISTEN hits=1
    port_22001=LISTEN hits=2
    port_8384=LISTEN hits=1
    positive_control port_22(sshd)=LISTEN hits=2
    negative_control port_1=CLOSED hits=0

**`22000` が待ち受け（自分の同期処理）、`22001` は待ち受けのまま（中継は生きている）。**

    $ python3 rest.py status
    myID=3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4
    startTime=2026-08-24T16:08:21Z uptime=37
    version=v2.1.3 os=linux arch=amd64
    connected_devices=1
      device=3J4TRX4 connected=True address='127.0.0.1:22001' type='tcp-client'

**版は `v2.1.3`。中心と同じ。**

#### 中心と繋がった記録

    ~/.syncthing.log:16
    2026-08-24 16:08:21 INF Established secure connection (device=3J4TRX4
      connection.local=127.0.0.1:22000 connection.remote=127.0.0.1:22001
      connection.type=tcp-client connection.lan=true
      connection.crypto=TLS1.3-TLS_AES_128_GCM_SHA256 connection.prio=10 …)

    ~/.syncthing.log:18
    2026-08-24 16:08:21 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001
      remote.name=philip remote.client=syncthing remote.version=v2.1.3 log.pkg=model)

**中継の出口 `127.0.0.1:22001` を通って中心へ繋がった。相手の版も `v2.1.3`。**

#### 定義が保たれているか（**要約値は変わる。定義で確かめる**。つまずき #6）

    $ sha256sum ~/.local/state/syncthing/config.xml
    7f80508ece4e0b8986110a4f2c6415ba1e47217c51ae2468b7ff13631332a71c   ← 起動前は 5ea37224…

    $ ls -la ~/.local/state/syncthing/
    -rw------- 11331 config.xml
    -rw------- 11359 config.xml.v37      ← 移行前の控えが残る
    -rw-rw-r--   700 https-cert.pem
    -rw-------   227 https-key.pem
    drwx------      index-v2
    -rw-------     0 syncthing.lock

    $ python3 verify_config.py
    xml_ok=True root=configuration version=52      ← 37 から移行された
    top_level_folder_count=2
    top_level_device_count=2
    naive_folder_count=3  (差はひな型)
      folder id='claude-sync' path='/home/ubuntu/claude-sync' type='sendreceive' shared_with=2 ['3C2LTP7', '3J4TRX4']
      folder id='m2'          path='/home/ubuntu/slocal2/m2' type='sendreceive' shared_with=2 ['3C2LTP7', '3J4TRX4']
      device id=3C2LTP7-…-UVZB5A4 name='andrew' address='dynamic'
      device id=3J4TRX4-…-DZOCQQE name='philip' address='tcp://127.0.0.1:22001'
      options/autoUpgradeIntervalH=0
      options/globalAnnounceEnabled=false
      options/localAnnounceEnabled=true
      options/relaysEnabled=false

🟢 **最上位の folder は 2 件のまま。`autoUpgradeIntervalH` は 0 のまま。**
`<defaults>` 配下も起動前と同じ（触っていない）。

    $ grep -c -i 'upgrade' ~/.syncthing.log
    0

**自動更新は走っていない。** Task 2 Step 2 が効いている。

---

## 5. Task 4 (Phase D) — 実際に届くことを確かめる

### Step 1: 自分から中心へ送る

    $ NONCE=$(python3 -c "import secrets; print(secrets.token_hex(16))")
    $ printf 'probe from andrew\ntime=%s\nnonce=%s\n' "$TS" "$NONCE" > ~/claude-sync/probe-andrew.txt
    $ stat -c '%n size=%s' ~/claude-sync/probe-andrew.txt ; sha256sum …
    /home/ubuntu/claude-sync/probe-andrew.txt size=83
    41f4c7dcab706950191ad1062c1b3d6c7d94570cac1f3f3e027de1ff0b3b82a8

    probe from andrew
    time=2026-08-24T16:09:23Z
    nonce=97a528940c9ea6f196967915bb164ba9

**内容に時刻と乱数を含む**（他の実行と取り違えないため）。

### Step 2: 中心が持っていることを確かめる（**中心で命令を実行していない**）

自ホストの `127.0.0.1:8384` の REST へ問い合わせた。
**合言葉は変数へ読み込み、画面へ出していない**（禁止 8）。

一度目（`16:09:40` 頃）は `/rest/db/file` が **404** を返した。**走査前だったためである。**
`/rest/db/status` が `localFiles=6 needFiles=0 state=idle` を返した後は 200 で応答した。
**「無い」ではなく「まだ索引に入っていない」であった。**

    $ python3 rest.py completion claude-sync 3J4TRX4-…-DZOCQQE
    folder=claude-sync device=3J4TRX4 completion=100.0000% needBytes=0 needItems=0 globalBytes=18658

    $ python3 rest.py file claude-sync probe-andrew.txt
    file=probe-andrew.txt size=83 modifiedBy=3C2LTP7 deleted=False
    availability=[{"id": "3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE", "fromTemporary": false}]

🟢 **`availability` に中心の識別子が現れた。**
`modifiedBy=3C2LTP7`（andrew が作った）で、**philip が保有している。往復している。**

#### この判定の陽性対照（**判定が空振りでないことの確認**）

    --- 対照 1: 実在するファイル（真を返すべき入力） ---
      status=200 hub_in_availability=True n=1
    --- 対照 2: 実在しないファイル（偽を返すべき入力） ---
      status=404 body_is_none=True  → 常に真を返す壊れ方ではない
    --- 対照 3: 合言葉を外す（認証が効いているか。値は出さない） ---
      status_without_key=403  → 応答は認証済みの実物
    --- 対照 4: 存在しない共有フォルダ（偽を返すべき入力） ---
      status=404
    --- 対照 5: 合言葉の長さだけを報告（値は出さない） ---
      apikey_len=32 apikey_empty=False

**判定は働いている。そのうえで中心が保有している。**

#### 逆向き（中心 → andrew）も届いている

    $ python3 rest.py raw '/rest/db/browse?folder=claude-sync'
    probe-andrew.txt                                        83 B  2026-08-24T16:09:23Z
    probe-bengio.txt                                        40 B  2026-08-24T13:10:57Z   ← **中心から届いた**
    sync-alerts.log                                       1802 B
    sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log 4784 B
    sync-alerts.sync-conflict-20260824-160823-3C2LTP7.log 6016 B
    sync-alerts.sync-conflict-20260824-160825-3C2LTP7.log 6016 B

**`probe-bengio.txt` は前契約が bengio 上で作ったものである。**
andrew は作っていない。**中心を経由して届いた。**

### Step 3: 中心から届いたものを測る（**実数**）

    $ du -sb ~/claude-sync ; find ~/claude-sync -type f | wc -l
    18858   /home/ubuntu/claude-sync
    7

| 時点 | 大きさ | 件数 |
|---|---|---|
| 開始（Phase A） | **1510 バイト** | **1 件** |
| Phase D | **18858 バイト** | **7 件（+ `.stfolder` 1 ディレクトリ）** |
| 増分 | **+17348 バイト** | **+6 件** |

内訳:

    4096    .stfolder/                          ← 起動時に syncthing が作った
     117    .stfolder/syncthing-folder-e1f429.txt
      83    probe-andrew.txt                    ← 本契約が作った
      40    probe-bengio.txt                    ← **中心から届いた**
    1802    sync-alerts.log
    4784    sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log   ← 中心から届いた（bengio 由来）
    6016    sync-alerts.sync-conflict-20260824-160823-3C2LTP7.log
    6016    sync-alerts.sync-conflict-20260824-160825-3C2LTP7.log

#### 記録の衝突 — **上書きではなく衝突ファイルが生まれた。消えたものは無い**

    ~/.syncthing.log:23,25,28
    16:08:23 INF Synced file (… file.name=sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log
                 file.size=4784 blocks.local=0 blocks.download=1)
    16:08:25 INF Synced file (… file.name=sync-alerts.sync-conflict-20260824-160823-3C2LTP7.log
                 file.size=6016 blocks.local=0 blocks.download=1)
    16:08:27 INF Synced file (… file.name=sync-alerts.sync-conflict-20260824-160825-3C2LTP7.log
                 file.size=6016 blocks.local=1 blocks.download=0)

**どちらが起きたかを内容で確かめた**（件数ではなく中身）:

    開始時の andrew 固有の行（"2026-08-24 15:08:21 [andrew] 一時停止中"）の出現数
      sync-alerts.log                                        hits=1   ← **残っている**
      sync-alerts.sync-conflict-…-160823-3C2LTP7.log         hits=0
      sync-alerts.sync-conflict-…-160825-3C2LTP7.log         hits=0
      sync-alerts.sync-conflict-…-131007-4NIRI4M.log         hits=0

    各ファイルの [ホスト] 別の行数
      sync-alerts.log                        18 行 = [andrew] 17 + [bengio] 1
      …-160823-3C2LTP7.log                   46 行 = [bengio] 40 + [philip] 6
      …-160825-3C2LTP7.log                   46 行 = [bengio] 40 + [philip] 6

🟢 **andrew の内容は本体に残り、中心側の内容は衝突ファイルとして併存している。**
**上書きは起きていない。消えたものは無い。** 前契約 bengio の実測と同じ挙動である。

### Step 4: repo の同期の様子（**完了を待っていない**）

    16:09:40 頃  folder=m2 completion=98.3365% needBytes=689548250 needItems=1731 globalBytes=41451321784
    16:12:52  m2: state=idle localFiles=5193 localBytes=42010521855 needFiles=0 needBytes=0 errors=0
              folder=m2 completion=100.0000% needBytes=0 needItems=1478 globalBytes=42010521855
    16:15:43  m2: state=idle localFiles=5193 localBytes=42010521855 needFiles=0 needBytes=0 errors=0
              folder=m2 completion=100.0000% needBytes=0 needItems=1478 globalBytes=42010521855

    $ grep -c -i 'puller\|Failed to sync' ~/.syncthing.log
    0
    $ grep -c '' ~/.syncthing.log
    2520

**バイトの転送は起動から約 4 分半で収束した**（`689548250` → `0`）。
**andrew 側は `needFiles=0 needBytes=0`。中心側は `needItems=1478` が残る**
（`needBytes=0` であるため、これは大きさ零の要素＝ディレクトリ等である）。
**誤りは 0 件。** 完了を待っていない。次の契約へ渡す。

---

## 6. Task 5 (Phase E) — 報告、検証、送出

### Step 2: 触っていないものが無変更であること

    $ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  keeper.sh    ← Task 1 と同じ
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  m2-sync.sh   ← Task 1 と同じ

    $ git --no-pager diff HEAD -- scripts/sync/ | grep -c ''
    0                                        ← 受け入れ一覧・識別子・常駐処理の版管理側は無変更

    $ ls -1 ~/.tunnel_to_* | wc -l
    1
    -rw------- 1 ubuntu ubuntu 60 Aug 24 15:18 /home/ubuntu/.tunnel_to_philip

    $ sha256sum .stignore .stglobalignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore        ← 開始時と同じ
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore  ← 開始時と同じ

**`keeper.sh` は毎周回 `origin/phase0` から `.stignore` を書き戻すが、内容が同じため
要約値は動いていない。**

### Step 3: 検証（**報告を書いたあと**）

    $ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-andrew-syncthing-node
    OK   T-2026-08-24-andrew-syncthing-node
    1 task(s), 0 failed
    validate_exit=0

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-08-24-andrew-syncthing-node
    P1 venv_active            PASS expected=…/.venv VIRTUAL_ENV=…/.venv sys.prefix=…/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS tasks/T-2026-08-24-andrew-syncthing-node/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              WARN 規則 8 件のうち 1 件が該当: separated_source@…/SPEC.md:41
    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
    preflight_exit=0

**SKIP は 4 件。合格ではなく、実行されなかったことを意味する。**
`P9` の該当は `SPEC.md:41`（`source .venv/bin/activate && source scripts/load_env.sh \`
の行継続）。**契約の誤りであり実行者の責任ではないため終了コードは変わらない。**

    $ source .venv/bin/activate && make forbidden-check
    {"base": "origin/phase0", "changed": 6, "checked": 6, "errors": [], "excluded": 0,
     "excluded_paths": [], "generated_directories": ["context/auto/"],
     "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
    forbidden_exit=0

**`conventions_rev` は実測して照合した（`d422b08`）。一致するため置換していない**（§1）。

**`make taskindex` と `make inbox` は実行していない**（禁止 6）。技能書は投影の確認を
求めるが契約の禁止が勝つ。`taskindex-check` / `inbox-check` も回していない。

### Step 4: 送信前の秘匿検査（**自分で実施。検査が値を出力していない**）

判定は件数ではなく**形**で行い、加えて**環境にある資格情報そのものと本文を照合した。**

    --- 形による走査（値は出さない。件数と位置だけ） ---
      RESULT.md                                該当なし
      audit.md                                 {'HEX32': 1}
          HEX32@audit.md:662
      result.yaml                              {'PEM_PRIVATE': 1}
          PEM_PRIVATE@result.yaml:121
      T-2026-08-24-andrew-syncthing-node.md    該当なし
      shape_hits_total=2

**該当を目視した**（申し送り「一致が出たときは何に一致したのかを目視する」）:

    $ sed -n '662p' audit.md
        nonce=97a528940c9ea6f196967915bb164ba9      ← 試験ファイルの乱数。資格情報ではない
    $ sed -n '121p' result.yaml
        breaking_input: "本文の末尾に -----BEGIN OPENSSH PRIVATE KEY----- を足した…"
                                                    ← 陽性対照の説明文。鍵ではない

    --- 実値との照合（環境にある資格情報そのもの。値は出さない） ---
      literals_available=3 names=['NOTION_API_KEY', 'WANDB_API_KEY', 'syncthing_apikey']
      literal_leaks=0

    --- 陽性対照（囮は変数の中だけ。ファイルにも commit にも残していない） ---
      decoy_literal_detected=3/3
      decoy_shape_hits={'PEM_PRIVATE': 1, 'AWS_AKID': 1}

    --- 版管理へ入る範囲 ---
      worktree_entries=2
        ?? tasks/T-2026-08-24-andrew-syncthing-node/
        ?? tasks/inbox.d/T-2026-08-24-andrew-syncthing-node.md

    secretscan_exit=0

**検査は働いており（囮を 3/3 と 2 種の形で検出）、そのうえで漏洩は 0 件である。**
**この検査の出力に秘匿の値は一つも現れていない**（長さ・件数・位置・真偽だけ）。
画面の鍵は版管理へ置いていない。控えは repo の外（`~/.local/state/syncthing.bak.20260824-150939`）
だけにある。本文の `<KEYDIR>` は伏せ字であり鍵の値ではない。

### Step 5: 送出

    $ git add tasks/T-2026-08-24-andrew-syncthing-node/ tasks/inbox.d/T-2026-08-24-andrew-syncthing-node.md
    $ git --no-pager diff --cached --stat
     6 files changed, 1507 insertions(+)      ← **追加のみ。既存ファイルの変更なし**

    $ git commit …
    cbb5c6c feat(sync): connect andrew to the syncthing hub

    $ git push -u origin feat/andrew-syncthing-node
     * [new branch]      feat/andrew-syncthing-node -> feat/andrew-syncthing-node
    branch 'feat/andrew-syncthing-node' set up to track 'origin/feat/andrew-syncthing-node'.
    push_exit=0

**前契約では push が実行基盤の分類器に拒否されたが、本実行では通った。**

    $ gh pr list --head feat/andrew-syncthing-node --json number,isDraft,state,baseRefName
    []                                        ← 既存の PR は無い。新規に作る

    $ gh pr create --base phase0 --head feat/andrew-syncthing-node …
    https://github.com/takuya3h/m2/pull/144
    pr_exit=0

    $ gh pr list --head feat/andrew-syncthing-node --json number,isDraft,state,baseRefName
    [{"baseRefName":"phase0","isDraft":false,"number":144,"state":"OPEN"}]

    $ git rev-parse --short HEAD ; git rev-parse --short origin/feat/andrew-syncthing-node
    cbb5c6c
    cbb5c6c

**PR #144（base `phase0`、Draft ではない、OPEN）。手元と `origin` の先頭が一致している。**

### 台帳 — 返した（**`make task-report` 以外の経路を使っていない**）

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-report TASK=T-2026-08-24-andrew-syncthing-node
    {
      "task_id": "T-2026-08-24-andrew-syncthing-node",
      "verdict": "pass",
      "n_issuer_defects": 4,
      "report_sha256": "92807a5a3b12fcab41ed0c4fe9c80561210f4c3442bae1bc98a554a3f853183a",
      "report_bytes": 12983,
      "replaced_blocks": 0
    }
    report_exit=0

**PR 番号を含む版を返している**（記録して起票したあとに送った）。
`replaced_blocks: 0` は本契約の報告が台帳に初めて載ったことを示す。


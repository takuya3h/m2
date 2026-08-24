# audit — T-2026-08-24-ilya-syncthing-node

手続きの証跡。命令とその出力、参照の解決、検証の出力を置く。
判断に使う事実は `RESULT.md` にある。

**実行ホスト:** `ilya`（`hostname` は `aolab` を返す。中心と同じ値）
**分岐:** `feat/ilya-syncthing-node`  **repo:** `~/slocal2/m2`
**開始:** 2026-08-24T16:43:14+00:00 (UTC)

---

## 0. 前提と抑止

    $ cd ~/slocal2/m2 && touch .sync-pause && ls -la .sync-pause
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 24 16:43 .sync-pause

    $ grep -c "sync-pause" ~/bin/m2-sync.sh
    2

**2 なので抑止が効く。** 稼働中の `~/bin/m2-sync.sh` は目印に対応済みである。

    $ git branch --show-current
    feat/ilya-syncthing-node        ← `feat/` で始まる

### `make task-start` は通らなかった

    $ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-08-24-ilya-syncthing-node
     M docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md
    ?? tasks/T-2026-08-24-ilya-syncthing-node/
    [task-start] 作業ツリーに未commitの変更が 2 件あります。片付けてから実行してください
    make: *** [Makefile:205: task-start] Error 3

未commit の 2 件は **(1) 契約そのもの**（未追跡）と **(2) 本契約の開始前から存在した
`docs/sessions/digest/…` の差分**である。どちらも片付ければ契約か既存の作業を壊す。
分岐 `feat/ilya-syncthing-node` も既存であり、`scripts/task_start.sh` の前提検査を
原理的に通せない。**前二契約（bengio / andrew）も同じ理由で実行していない。** 逸脱 1 として記録。

    $ git --no-pager diff --stat docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md
     ...6-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md | 41 +++++++++++++++++++---
     1 file changed, 36 insertions(+), 5 deletions(-)

**この差分は本契約が作ったものではない。触っていない。**

---

## 1. 解決された参照

| spec の記載 | 解決先 | 実測 |
|---|---|---|
| `inputs.code.entrypoints[0]` | `scripts/sync/keeper.sh` | 存在。稼働中の実体は `~/bin/keeper.sh`（要約値 `9fe9c423…`、`755`） |
| `inputs.code.entrypoints[1]` | `scripts/sync/m2-sync.sh` | 存在。稼働中の実体は `~/bin/m2-sync.sh`（要約値 `bcf46ba9…`、`775`） |
| `contract.inject_verbatim: conventions#prohibitions` | `context/conventions.md` の該当アンカーの原文 | 下に**原文のまま**転記 |
| `contract.conventions_rev` | 実測して置換する（SPEC の指示） | 実測 `d422b08`。spec.yaml の記載と**一致したため置換不要** |
| 中心の識別子 | `scripts/sync/device_ids/philip.txt` | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| 自分の識別子 | `scripts/sync/device_ids/ilya.txt` | `UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY` |
| 自分の公開鍵 | `scripts/sync/hub_keys/ilya.pub` | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ ilyatophilip (ED25519)` |
| 中心の住所（中継が繋ぐ先） | 前契約 `audit.md` の実測 | `192.168.196.150` 口 `50072`（`handoff.md` の `192.168.196.176` は誤り。使わない） |

### `contract.inject_verbatim: conventions#prohibitions` の原文

`context/conventions.md:98-108` を**要約せず原文のまま**置く。

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

契約 `contract.prohibitions` の 5 件はこの表の 5 件と同じ集合である。**すべて守った**:
`data/` `experiments/` `transfer/` `runindex/` のいずれにも触れていない（§9 の
`forbidden-check` と `git status` で示す）。未測定は `UNKNOWN` と書いた。

### `conventions_rev` の実測

    $ git --no-pager log -1 --format='%h %ad %s' --date=iso -- context/conventions.md
    d422b08 2026-08-07 14:40:56 +0000 docs(context): backfill the changelog sha for the frozen-source scope note

**spec.yaml の `conventions_rev: "d422b08"` と一致した。置換は不要である**（手順として実測した）。

`inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は
**本契約の手順のどこでも使わない。** 契約が同期の設営のみを扱うためである。
起票者の誤り（`check_does_not_check`）として §11 に記録した。

---

## 2. Phase A — 開始状態の封印と中心への到達の確認

### Task 1 Step 1: 現状を要約値で記録する

    $ for f in ~/bin/syncthing ~/bin/keeper.sh ~/bin/m2-sync.sh \
        ~/.local/state/syncthing/config.xml ~/.local/state/syncthing/cert.pem \
        ~/.local/state/syncthing/key.pem; do
        printf '%s ' "$(sha256sum "$f" | cut -c1-64)"; stat -c '%a %s %n' "$f"; done
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd 644 26730145 /home/ubuntu/bin/syncthing
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90 755 2709     /home/ubuntu/bin/keeper.sh
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f 775 7342     /home/ubuntu/bin/m2-sync.sh
    b548d117fee0578430448630efcf9c5b3010a73da5acd5f17a3f7aa780571c63 600 8494     /home/ubuntu/.local/state/syncthing/config.xml
    0081011c3a55634f1304d57f9712fff8d8c2279d6d42720c5f74f4b386a905dc 664 794      /home/ubuntu/.local/state/syncthing/cert.pem
    8fac365bbc2565f963c4b2dc66e6a19ba1607dbea3d8fb101e8cc44eb15d2bd8 600 288      /home/ubuntu/.local/state/syncthing/key.pem

**実行ファイル `~/bin/syncthing` の権限は `644`（実行権が落ちている）。** 起動条件を満たさない。
`keeper.sh` `m2-sync.sh` の要約値は前契約 andrew の開始値と同一である
（常駐処理が `origin/phase0` から書き戻すため）。

#### 除外規則

    $ sha256sum .stignore .stglobalignore && stat -c '%a %s %n' .stignore .stglobalignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore
    664 2223 .stignore
    664 2223 .stglobalignore

`~/.stignore` `~/.stglobalignore` `~/claude-sync/.stignore` は **不在**
（`ls` が `No such file or directory` を返した。**読めないのではなく無い**）。
除外規則の実体は repo 直下の 2 件のみである。

    $ find ~ -maxdepth 3 \( -name '.stignore' -o -name '.stglobalignore' \) 2>/dev/null
    /home/ubuntu/slocal2/m2/.stglobalignore
    /home/ubuntu/slocal2/m2/.stignore

#### 中継の目印

    $ ls -la ~/.tunnel_to_philip
    ls: cannot access '/home/ubuntu/.tunnel_to_philip': No such file or directory

**目印は 0 件。**

#### 共有領域の大きさと件数（丸めない実数）

    $ du -sb ~/claude-sync
    4528    /home/ubuntu/claude-sync
    $ find ~/claude-sync -type f | wc -l
    1
    $ find ~/claude-sync -mindepth 1 | wc -l
    1
    $ ls -la ~/claude-sync/
    -rw-rw-r-- 1 ubuntu ubuntu 4528 Aug 24 16:18 sync-alerts.log

**`~/claude-sync` = 4528 バイト / 1 件。** 中身は `sync-alerts.log` のみ。
`du -sb` の値は最上位ディレクトリ自身の 4096 を含まない（実体 1 件の大きさと一致する）。

**前ホストの値を引き継いでいない**（bengio 4031 B、andrew 1510 B、本ホスト **4528 B**）。

    $ du -sb ~/slocal2/m2
    47515332495     /home/ubuntu/slocal2/m2

**repo = 47515332495 バイト。** andrew の 54745194976 とも bengio とも違う。
**ホストごとに違う。定数として扱わない**（申し送り 9）。

#### 稼働しているものの数（両方向の対照つき）

`pgrep -f` も `ps | grep` も自己一致するため、**`/proc/PID/exe` の実体名**で照合した。
補助は `scratchpad/scan.sh`（exe 照合）と `scratchpad/scanarg.sh`（cmdline 照合。自分と親を除く）。

    $ scan.sh zsh                 → exe=zsh count=5 pids= 7099 71833 88454 89072 92897   ← 肯定対照
    $ scan.sh zzz_no_such_exe     → exe=zzz_no_such_exe count=0 pids=                    ← 否定対照
    $ scan.sh syncthing           → exe=syncthing count=0 pids=
    $ scan.sh ssh                 → exe=ssh count=0 pids=
    $ scanarg.sh keeper.sh        → arg=keeper.sh count=1 pids= 43963                    ← 肯定対照
    $ scanarg.sh m2-sync.sh       → arg=m2-sync.sh count=0 pids=
    $ scanarg.sh zzz_no_such_token→ arg=zzz_no_such_token count=0 pids=                  ← 否定対照

**同期処理 0 件、中継（ssh）0 件。** 常駐処理 `keeper.sh` は 1 件（pid `43963`）。

    $ cat /proc/43963/cmdline | tr '\0' ' '
    /bin/bash /home/ubuntu/bin/keeper.sh
    $ awk '{print "ppid="$4}' /proc/43963/stat
    ppid=1
    $ ls -l /proc/43963/cwd
    /proc/43963/cwd -> /home/ubuntu/slocal2/m2
    $ stat -c '%y' /proc/43963
    2026-08-23 17:31:31.129981149 +0000

**常駐処理は停止しない**（禁止 12）。

**最初の計数は `/proc/*/cmdline` を語で照合したため `tunnel_like=1` を返したが、
これは自分の命令行が `192.168.196.150` を含んだ自己一致であった。** 上の方式で 0 と確定した。

#### 口の状態（両方向の対照つき）

`ss` `netstat` `lsof` が無いため `/proc/net/tcp` と `/proc/net/tcp6` から復号した
（補助は `scratchpad/portstate.sh`）。

    $ portstate.sh 22     → port=22 LISTEN ESTABLISHED LISTEN     ← 肯定対照
    $ portstate.sh 1      → port=1 CLOSED                          ← 否定対照
    $ portstate.sh 22000  → port=22000 CLOSED
    $ portstate.sh 22001  → port=22001 CLOSED
    $ portstate.sh 8384   → port=8384 CLOSED

### Task 1 Step 2: 控えを repo の外へ取る

    $ TS=$(date +%Y%m%d-%H%M%S); BK=~/.local/state/syncthing.bak.$TS
    $ cp -a ~/.local/state/syncthing "$BK"
    backup=/home/ubuntu/.local/state/syncthing.bak.20260824-164557
    -rw-rw-r-- 1 ubuntu ubuntu  794 Aug 23 13:53 cert.pem
    -rw------- 1 ubuntu ubuntu 8494 Aug 23 13:53 config.xml
    -rw------- 1 ubuntu ubuntu  288 Aug 23 13:53 key.pem
    == 要約値の照合 ==
    config.xml MATCH
    cert.pem   MATCH
    key.pem    MATCH

**控えは repo の外**（`/home/ubuntu/.local/state/syncthing.bak.20260824-164557`）。3 件とも要約値が一致。

#### 版管理へ置く前の検査（秘密鍵の書き出しの混入・画面の鍵）

    $ .venv/bin/python  # 正規表現 '-----BEGIN [A-Z ]*PRIVATE KEY-----' で走査
    config.xml 内の秘密鍵の書き出し件数 = 0
    陽性対照 decoy_detected = 1        ← 検査が働いている（囮は変数の中だけ。ファイルへ書かない）
    apikey_len = 32 empty = False

**画面の鍵が実値で入っている**（長さ 32、非空）。値は出力していない。
したがって **設定一式を版管理へは置かない。** 控えは repo の外にのみ置く。

### Task 1 Step 3: 戻し方（**実行していない**。手順として記録するだけ）

1. **起動を止める。** 実行権を落とす。`keeper.sh` は `[ -x ~/bin/syncthing ]` を見て
   起動するため（`~/bin/keeper.sh:41`）、実行権が落ちていれば次の周回で起こさない。

       chmod 644 ~/bin/syncthing

2. **走っている同期処理を終える**（起こし直されないことを 1 で担保してから）。

       kill $(scan.sh syncthing で得た pid)

3. **中継を止める。** 目印を消せば `resolve_tunnel` が失敗し張り直さない（`keeper.sh:33`）。

       rm -f ~/.tunnel_to_philip
       kill $(scan.sh ssh で得た pid)

4. **設定を控えから戻す。**

       rm -rf ~/.local/state/syncthing
       cp -a /home/ubuntu/.local/state/syncthing.bak.20260824-164557 ~/.local/state/syncthing

5. **実行ファイルを開始時の版へ戻す**（版を入れ替えた場合のみ）。開始時の実測は
   要約値 `32ab747e…` / 26730145 バイト / 権限 `644` である。

6. **抑止を外す。**

       mv ~/slocal2/m2/.sync-pause ~/slocal2/m2/.sync-pause.released

**常駐処理 `keeper.sh`（pid 43963）は止めない**（禁止 12）。上の手順はすべて
常駐処理を動かしたまま成立する。

### Task 1 Step 4: 中心の値を版管理から読み、到達を確かめる

    $ cat scripts/sync/device_ids/ilya.txt
    UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY
    $ cat scripts/sync/device_ids/philip.txt
    3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
    $ grep -o 'device id="[A-Z0-9-]*"' ~/.local/state/syncthing/config.xml | sort -u
    device id=""                                                              ← ひな型（`defaults`）
    device id="UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY"

**自分の識別子が現在の設定と一致した**（完了判定 E）。
**本文の転記を信用せず、版管理のファイルから読んだ。**

#### 中心へ入れることの確認（`ssh -N`。中心で命令を実行しない）

    $ ssh-keygen -lf scripts/sync/hub_keys/ilya.pub
    256 SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ ilyatophilip (ED25519)

`~/.ssh/` は実行基盤の deny 規則で読めない（`ls -la ~/.ssh/` を含む命令が拒否された）。
**無いのではなく読めない。** 指紋は版管理側の公開鍵で照合した（前契約の指摘に従う）。

    $ timeout 25 ssh -N -v -p 50072 -i "$HOME/.ssh/id_ed25519_ilyatophilip" \
        -o StrictHostKeyChecking=accept-new \
        -o UserKnownHostsFile="$SP/known_hosts_probe" \
        -o BatchMode=yes -o ConnectTimeout=15 ubuntu@192.168.196.150
    ssh_exit=124                                    ← `timeout` が切った。`-N` は繋ぎ続けるため正常
    debug1: Connection established.
    debug1: Authentications that can continue: publickey,password
    debug1: Offering public key: /home/ubuntu/.ssh/id_ed25519_ilyatophilip ED25519 SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ explicit
    debug1: Server accepts key:  /home/ubuntu/.ssh/id_ed25519_ilyatophilip ED25519 SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ explicit
    Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey".
    $ grep -c -i "denied" ssh_probe.err
    0

**中心へ入れた**（完了判定 F）。指紋 `SHA256:O4FrUiuT3+…` が版管理の `ilya.pub` と一致する。
**`-N` を使ったので中心で命令を実行していない**（禁止 1）。
受け入れの控えは `scratchpad/known_hosts_probe` へ隔離し、`~/.ssh/known_hosts` を触っていない。

### Gate G1

| 条件 | 実測 |
|---|---|
| 開始状態を要約値で記録 | 6 件（§2 Step 1） |
| 実行権が落ちている | `~/bin/syncthing` = `644` |
| 目印が 0 件 | `~/.tunnel_to_philip` 不在 |
| 同期処理が 0 件 | `exe=syncthing count=0` |
| 中継が 0 件 | `exe=ssh count=0`、`port=22001 CLOSED` |
| 両方向の対照 | プロセス `zsh=5` / `zzz_no_such_exe=0`、`keeper.sh=1` / `zzz_no_such_token=0`。口 `22=LISTEN` / `1=CLOSED` |
| 控えを版管理の外へ | `/home/ubuntu/.local/state/syncthing.bak.20260824-164557`（要約値 3 件一致）。秘密鍵の混入 0（陽性対照 1） |
| 識別子が設定と一致 | `UODEAXZ-…-X6SDBQY` |
| 中心へ命令を伴わない形で入れる | `ssh -N`、`Authenticated to 192.168.196.150`、`denied=0` |

**G1 = pass**

---

## 3. Phase B — 版を揃え、設定を組み立てる

### Step 1: 版を中心に揃える

現在の版を**実測した**（前ホストの値を引き継がない）。実行権が `644` のため実行できないので
文字列から読んだ。

    $ ~/bin/syncthing --version
    (eval):1: permission denied: /home/ubuntu/bin/syncthing
    $ strings -a ~/bin/syncthing | grep -E '^(v1|v2)\.[0-9]+\.[0-9]+(-|$)' | sort -u | head -1
    v1.27.10

**本ホストは `v1.27.10`。中心の `v2.1.3` より古い。入れ替えが要る。**

    $ curl -fsSL -o st213.tar.gz \
        https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz
    curl_exit=0
    $ sha256sum st213.tar.gz && stat -c '%s' st213.tar.gz
    f929eb8e5b72a85543eeeefb2c38f34a68e0c530e70758a2905b78840c76602c  st213.tar.gz
    11821325

**取得物は前契約の実測（`f929eb8e…` / 11821325 B）と一致。**

#### 同名の別物 3 件を大きさで切り分けた（つまずき 7）

    $ tar -xzf st213.tar.gz -C st213
    $ find st213 -name 'syncthing' -printf '%s\t%y\t%p\n'
    27045912  f  st213/syncthing-linux-amd64-v2.1.3/syncthing
    175       f  st213/syncthing-linux-amd64-v2.1.3/etc/firewall-ufw/syncthing
    1709      f  st213/syncthing-linux-amd64-v2.1.3/etc/freebsd-rc/syncthing

    $ find st213 -name 'syncthing' -type f -size -27045913c -size +27045911c -printf '%s\t%p\n'
    27045912  st213/syncthing-linux-amd64-v2.1.3/syncthing

    $ sha256sum st213/syncthing-linux-amd64-v2.1.3/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4

🟢 **中心の実測値 `e8a08fdd…` / 27045912 B と完全一致。**

#### 旧版の控え（repo の外・2 か所）

    $ cp -a ~/bin/syncthing $SP/syncthing.v1.27.10.bak
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  (scratchpad)
    $ mkdir -p ~/syncthing-rollback && cp -a ~/bin/syncthing ~/syncthing-rollback/syncthing.v1.27.10
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  644 26730145

#### 実行基盤に一度拒否され、権限の付与を受けてから入れ替えた

一度目は auto mode の分類器が `~/bin/` への書き込みを拒否した。**回避していない。**
技能書の指示に従い停止し、利用者へ提示して判断を仰いだ。**権限の付与を受けて続行した**（逸脱 6）。

    $ cp -f $SP/st213/syncthing-linux-amd64-v2.1.3/syncthing ~/bin/syncthing && chmod 644 ~/bin/syncthing
    $ sha256sum ~/bin/syncthing && stat -c '%a %s %n' ~/bin/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4  /home/ubuntu/bin/syncthing
    644 27045912 /home/ubuntu/bin/syncthing

🟢 **中心と一致。権限は `644` のまま＝起動条件（`keeper.sh:41` の `[ -x ]`）を満たさない。**

### Step 2〜6: 設定の編集

#### 編集対象がすべて一意であることを先に測った（誤爆の防止）

    $ for p in '^    <folder ' '^    <device ' '<autoUpgradeIntervalH>' '<globalAnnounceEnabled>' \
               '<relaysEnabled>' '<localAnnounceEnabled>' 'name="aolab"'; do grep -c -- "$p" config.xml; done
    '^    <folder '           -> 1
    '^    <device '           -> 1
    '<autoUpgradeIntervalH>'  -> 1
    '<globalAnnounceEnabled>' -> 1
    '<relaysEnabled>'         -> 1
    '<localAnnounceEnabled>'  -> 1
    'name="aolab"'            -> 1
    $ grep -c '<!--' config.xml
    0                          ← 注釈が無いので生の XML の置換で書式が壊れない

`<defaults>` 配下は 8 桁字下げ、最上位は 4 桁字下げである。
**正規表現を `^    ` に固定したため `<defaults>` には当たらない**（禁止 5）。

#### 編集前の実測（`.venv/bin/python` の XML 解析。階層を見て数えた）

    root: configuration {'version': '37'}
    直下の要素: folder(id=default), device(id=UODEAXZ…), gui, ldap, options, defaults
    top-level folder count = 1     ← folder id='default' path='/home/ubuntu/Sync' type='sendreceive'
    findall(".//folder")  = 2      ← 単純検索。差はひな型 defaults/<folder id="">
    top-level device count = 1     ← id=UODEAXZ… name='aolab'
    defaults children: folder(id=''), device(id=''), ignores

    options/autoUpgradeIntervalH  = 12
    options/globalAnnounceEnabled = true
    options/localAnnounceEnabled  = true
    options/relaysEnabled         = true
    gui/apikey                    = <len=32 empty=False>   ← 値は出力していない

🔴 **自分の登録名の初期値は `aolab` である。**
SPEC は「初期値は大文字始まりのはず」（`Ilya`）と書き、前契約 andrew の申し送りも
「`ilya` `lecun` も `Andrew` と同じ（先頭が大文字）と見てよい」と予想していたが、
**実測は `aolab`**、すなわち **`hostname` そのもの＝中心と同じ値**であった。
**SPEC が警告した衝突が、予想より直接的な形で実在した。**

#### 編集（`scratchpad/build_config.py`。各置換は `assert n == 1` で件数を表明する）

    $ .venv/bin/python $SP/build_config.py
    編集前 sha256 = b548d117fee0578430448630efcf9c5b3010a73da5acd5f17a3f7aa780571c63
      OK autoUpgradeIntervalH 12->0     (件数 1)
      OK globalAnnounce true->false     (件数 1)
      OK relaysEnabled true->false      (件数 1)
      OK localAnnounceEnabled           (true のまま。変えない)
      OK device name aolab->ilya        (件数 1)
      OK folder の入れ替え               (default -> claude-sync, m2)
      OK 中心の登録                      (philip / tcp://127.0.0.1:22001)
    編集後 sha256 = 2a7433a533ca8029cb2215f2d60b418d82611c3eb61e73ecaa853901527b0c99

| # | 変更 | 前 | 後 |
|---|---|---|---|
| Step 2 | `options/autoUpgradeIntervalH` | `12` | **`0`** |
| Step 3 | `options/globalAnnounceEnabled` | `true` | **`false`** |
| Step 3 | `options/relaysEnabled` | `true` | **`false`** |
| Step 3 | `options/localAnnounceEnabled` | `true` | **`true`（変えない）** |
| Step 4 | 自分の登録名 | **`aolab`** | **`ilya`** |
| Step 5 | 中心の登録 | 無し | `id=3J4TRX4-…-DZOCQQE` name=`philip` address=`tcp://127.0.0.1:22001` |
| Step 6 | 共有フォルダ | `default`（`/home/ubuntu/Sync`） | **`claude-sync` と `m2`** |

**他のノード（`bengio` `andrew` `lecun`）は登録していない。** 星型であるため。

### Step 7: 書式と定義を確かめる

    $ .venv/bin/python  # XML 解析。階層を見て数える
    xml_ok=True root=configuration version=37
    top_level_folder_count=2
    top_level_device_count=2
    naive_folder_count=3   (単純検索。差はひな型)
    naive_device_count=8   (単純検索。差はひな型と folder 配下の共有相手)
      folder id='claude-sync' path='/home/ubuntu/claude-sync' type='sendreceive' shared_with=2 ['UODEAXZ', '3J4TRX4']
      folder id='m2'          path='/home/ubuntu/slocal2/m2'  type='sendreceive' shared_with=2 ['UODEAXZ', '3J4TRX4']
      device id=UODEAXZ… name='ilya'   address='dynamic'
      device id=3J4TRX4… name='philip' address='tcp://127.0.0.1:22001'
      options/autoUpgradeIntervalH=0
      options/globalAnnounceEnabled=false
      options/localAnnounceEnabled=true
      options/relaysEnabled=false
    --- defaults 配下（触っていないこと）---
      [('folder', ''), ('device', ''), ('ignores', '')]

**最上位の folder は 2 件。単純検索は 3 件を返す。差はひな型である**（禁止 5 を守った）。
**識別子 `claude-sync` と `m2` は中心と同じ**（前契約 bengio / andrew と同じ 2 語）。

#### 権限が変わっていないこと・鍵を触っていないこと

    $ stat -c '%n perm=%a size=%s' config.xml cert.pem key.pem
    config.xml perm=600 size=11357
    cert.pem   perm=664 size=794
    key.pem    perm=600 size=288
    $ sha256sum cert.pem key.pem
    0081011c3a55634f1304d57f9712fff8d8c2279d6d42720c5f74f4b386a905dc  cert.pem   ← 開始時と同じ
    8fac365bbc2565f963c4b2dc66e6a19ba1607dbea3d8fb101e8cc44eb15d2bd8  key.pem    ← 開始時と同じ

**鍵は生成も変更も削除もしていない**（禁止 3。申し送り 8 に従い要約値で確かめた）。

#### まだ起動していない

    $ scan.sh syncthing        → exe=syncthing count=0 pids=
    $ scan.sh ssh              → exe=ssh count=0 pids=
    $ scan.sh zsh              → exe=zsh count=5                    ← 肯定対照
    $ scan.sh zzz_no_such_exe  → exe=zzz_no_such_exe count=0        ← 否定対照
    $ portstate.sh 22000       → port=22000 CLOSED
    $ portstate.sh 22001       → port=22001 CLOSED
    $ portstate.sh 22          → port=22 LISTEN ESTABLISHED LISTEN  ← 肯定対照

### Gate G2

| 条件 | 実測 |
|---|---|
| 実行ファイルの要約値が中心と一致 | `e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4` / 27045912 B |
| 実行権が落ちたまま | `644` |
| 自動更新を止めた | `options/autoUpgradeIntervalH = 0` |
| 告知と外部の中継を無効 | `globalAnnounceEnabled=false` / `relaysEnabled=false` / `localAnnounceEnabled=true` |
| 中心を中継の出口で登録 | `id=3J4TRX4-…-DZOCQQE` name=`philip` address=`tcp://127.0.0.1:22001` |
| 最上位の共有フォルダが 2 件 | `claude-sync` / `m2`（中心と同じ識別子） |
| 書式が解析でき権限が保たれている | `xml_ok=True`、device 実体 2 件、`600` / `664` / `600` |

**G2 = pass**

---

## 4. Phase C — 中継を張り、起動する

**順序が要である。目印 → 中継 → 実行権 → 起動。** 実測でこの順に並んだことを下に示す。

### Step 1: 目印を置く

    $ printf '%s\n%s\n' '/home/ubuntu/.ssh/id_ed25519_ilyatophilip' '192.168.196.150' \
        > ~/.tunnel_to_philip
    $ chmod 600 ~/.tunnel_to_philip
    $ stat -c '%a %s %n' ~/.tunnel_to_philip
    600 58 /home/ubuntu/.tunnel_to_philip
    $ wc -l < ~/.tunnel_to_philip
    2
    $ ls -1 ~/.tunnel_to_* | wc -l
    1
    $ sed -n '1p;2p' ~/.tunnel_to_philip
    /home/ubuntu/.ssh/id_ed25519_ilyatophilip
    192.168.196.150
    $ stat -c '%y' ~/.tunnel_to_philip
    2026-08-24 17:26:17.945527412 +0000

**2 行目は `192.168.196.150`。** 版管理内の `handoff.md` が案として持つ `192.168.196.176`
は**使っていない**（前契約の実測を正とする）。**権限は `600`＝所有者だけが読める。**

`printf > ~/.tunnel_to_philip` は auto mode の分類器に拒否されたため、
**同じ目的の別の道具（Write）で置いた**（逸脱 6）。回避ではない。内容と権限は上のとおり。

### Step 2: 中継が立つのを待ち、確かめる

常駐処理の周回は `:18:38` / `:48:38` である（`~/claude-sync/sync-alerts.log` の刻み）。
目印は `17:26:17` に置いたので、**直前の周回（`17:18:38`）には間に合わず、次の周回を待った。**

    $ scratchpad/wait_tunnel.sh   # 30 秒ごとに口とプロセスを見る
    2026-08-24T17:30:54 elapsed=0s    port=22001 CLOSED  exe=ssh count=0
    …
    2026-08-24T17:48:26 elapsed=1052s port=22001 CLOSED  exe=ssh count=0
    2026-08-24T17:48:56 elapsed=1082s port=22001 LISTEN LISTEN  exe=ssh count=1 pids= 102324
    TUNNEL_UP after 1082s

🟢 **`22001` が待ち受けた。**

    $ tr '\0' ' ' < /proc/102324/cmdline
    ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i /home/ubuntu/.ssh/id_ed25519_ilyatophilip
      -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes
      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@192.168.196.150
    $ awk '{print "ppid="$4}' /proc/102324/stat
    ppid=43963                      ← keeper.sh（§2 で pid を確定済み）

🟢 **引数に中心の住所 `ubuntu@192.168.196.150` が含まれる。** 親は常駐処理である。

    $ stat -c '%y /proc/102324' /proc/102324
    2026-08-24 17:48:56.714299178 +0000

**目印 `17:26:17.945` → 中継 `17:48:56.714` = 1358.77 秒。**
前契約の実測（bengio 413 秒、andrew 1227 秒）と同じ幅に収まる。
**差は周回の位相であってホスト差ではない**（本ホストは周回の直後に目印を置いたため長い）。

`~/.tunnel.log` は**空**（作られたが行が無い）。中継の失敗は記録されていない。

### Step 3: 実行権を戻す（**中継が立ってから**）

中継が立った時点で**実行権がまだ `644` であることを同時に観測した**。これが順序の証拠である。

    $ $SP/portstate.sh 22001 ; stat -c '%a %n' ~/bin/syncthing ; $SP/scan.sh syncthing
    port=22001 LISTEN LISTEN
    644 /home/ubuntu/bin/syncthing          ← 中継が立っているのに実行権はまだ落ちている
    exe=syncthing count=0 pids=

    $ chmod 755 ~/bin/syncthing
    $ stat -c '%a %s %n' ~/bin/syncthing && sha256sum ~/bin/syncthing && stat -c 'ctime=%z' ~/bin/syncthing
    755 27045912 /home/ubuntu/bin/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4   ← 変わっていない
    ctime=2026-08-24 17:51:20.223407028 +0000

🟢 **中継 `17:48:56.714` → 実行権 `17:51:20.223`。中継が 143.5 秒早い。**
**要約値は `e8a08fdd…` のまま変わっていない**（権限だけを変えた）。

### Step 4: 起動を待ち、確かめる

    $ scratchpad/wait_syncthing.sh
    2026-08-24T18:18:27 elapsed=1533s exe=syncthing count=0  port=22000 CLOSED
    2026-08-24T18:18:57 elapsed=1563s exe=syncthing count=2 pids= 107755 107777  port=22000 LISTEN ESTABLISHED
    SYNCTHING_UP after 1563s

**実行権 `17:51:20` → 起動 `18:18:38`（記録の刻み）= 1637.8 秒。** 常駐処理の次の周回である。

#### プロセスの数を親子関係で切り分けた

    $ for p in 107755 107777; do echo "pid=$p ppid=$(awk '{print $4}' /proc/$p/stat) cmd=$(tr '\0' ' ' < /proc/$p/cmdline)"; done
    pid=107755 ppid=43963  cmd=/home/ubuntu/bin/syncthing serve --no-browser   ← 監視役。親は keeper.sh
    pid=107777 ppid=107755 cmd=/home/ubuntu/bin/syncthing serve --no-browser   ← 作業役。親は 107755

🟢 **2 件。うち 1 件は他方の子である。** 別々の同期処理が 2 つ走っているのではない（つまずき 4）。

#### 口

    $ portstate.sh 22000  → port=22000 LISTEN ESTABLISHED
    $ portstate.sh 22001  → port=22001 LISTEN ESTABLISHED ESTABLISHED ESTABLISHED LISTEN
    $ portstate.sh 8384   → port=8384 LISTEN

**`22000` が待ち受け、`22001` は待ち受けのまま**（中継は生きている）。
`22001` の `ESTABLISHED` は中継を通っている接続である。

#### 版

    $ grep -m1 'syncthing v' ~/.syncthing.log
    2026-08-24 18:18:38 INF syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64) …

🟢 **`v2.1.3`。中心と同じ。**

#### 定義が保たれ、自動更新が零のまま（Q）

起動時に設定は書き戻され、**要約値は変わった**（`2a7433a5…` → `72fc77b0…`）。
**定義で確かめる**（つまずき 6）。

    $ .venv/bin/python  # XML 解析
    config_version = 52                       ← 37 から移行した
    top_level_folder_count = 2  top_level_device_count = 2
      folder id='claude-sync' path='/home/ubuntu/claude-sync' type='sendreceive' shared=2
      folder id='m2'          path='/home/ubuntu/slocal2/m2'  type='sendreceive' shared=2
      device id=UODEAXZ… name='ilya'   address='dynamic'
      device id=3J4TRX4… name='philip' address='tcp://127.0.0.1:22001'
      options/autoUpgradeIntervalH=0
      options/globalAnnounceEnabled=false
      options/localAnnounceEnabled=true
      options/relaysEnabled=false
      defaults 配下: [('folder', ''), ('device', ''), ('ignores', '')]   ← 触っていない

    $ grep -c -i "upgrade" ~/.syncthing.log
    0                                          ← 自動更新は走っていない

    $ sha256sum cert.pem key.pem
    0081011c3a55634f1304d57f9712fff8d8c2279d6d42720c5f74f4b386a905dc  cert.pem   ← 開始時と同じ
    8fac365bbc2565f963c4b2dc66e6a19ba1607dbea3d8fb101e8cc44eb15d2bd8  key.pem    ← 開始時と同じ

#### 中心と繋がった記録（R）

    $ grep -n "New device connection\|Established secure connection" ~/.syncthing.log | head -3
    16: 2026-08-24 18:18:38 INF Established secure connection (device=3J4TRX4
        connection.local=127.0.0.1:22000 connection.remote=127.0.0.1:22001
        connection.type=tcp-client connection.crypto=TLS1.3-TLS_AES_128_GCM_SHA256 …)
    18: 2026-08-24 18:18:38 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001
        remote.name=philip remote.client=syncthing remote.version=v2.1.3 log.pkg=model)

🟢 **`remote.name=philip`、`remote.version=v2.1.3`、住所は中継の出口 `127.0.0.1:22001`。**

### Gate G3

| 条件 | 実測 |
|---|---|
| 目印を置いて中継が立った | `~/.tunnel_to_philip` 58 B `600` 2 行 → `port=22001 LISTEN`（1358.8 秒後） |
| 中継の引数に中心の住所 | `ubuntu@192.168.196.150`（pid `102324`、親 `43963`＝keeper） |
| 中継が立ってから実行権を戻した | 中継 `17:48:56.714` → `chmod` `17:51:20.223`。**中継が 143.5 秒早い。** 中継が立った時点で `perm=644` を同時観測 |
| 同期処理が起動した | pid `107755`（親 keeper）と `107777`（親 `107755`）の **2 件** |
| 版が中心と同じ | `v2.1.3` |
| 最上位 folder が 2 件のまま | `claude-sync` / `m2` |
| 自動更新が零のまま | `autoUpgradeIntervalH=0`、記録の `upgrade` = 0 件 |

**G3 = pass**

---

## 5. Phase D — 実際に届くことの確認

**「繋がった」ではなく「届いた」を確かめる。**

### Step 1: 自分から中心へ送る

    $ TS=$(date -Iseconds); R=$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)
    $ printf 'probe from ilya\ntime=%s\nnonce=%s\n' "$TS" "$R" > ~/claude-sync/probe-ilya.txt
    $ sha256sum ~/claude-sync/probe-ilya.txt && stat -c 'size=%s' ~/claude-sync/probe-ilya.txt
    9a8acb0912757e28719955c18ba3f6922e51b37d8471476d8696b0dc7a27e23a
    size=78
    $ cat ~/claude-sync/probe-ilya.txt
    probe from ilya
    time=2026-08-24T18:20:26+00:00
    nonce=04M5mcltXNdcPnsNPEiOAfjw

**時刻と乱数を含む。要約値 `9a8acb09…`、大きさ 78 バイト。**

### Step 2: 中心が持っていることを確かめる（**中心で命令を実行しない**）

自ホストの画面の REST（`127.0.0.1:8384`）へ問い合わせた。
**合言葉は `scratchpad/rest.py` の中で変数へ読み込み、画面へ出していない。**

**前契約の指摘に従い、置いた直後には問わず `state=idle` を待った。**

    $ /rest/system/status  -> 200  myID=UODEAXZ-…-X6SDBQY
    $ /rest/system/version -> 200  v2.1.3
    $ /rest/system/connections -> 200
        device=3J4TRX4… connected=True type=tcp-client addr=127.0.0.1:22001
    $ /rest/db/status?folder=claude-sync -> state=idle needBytes=0 errors=0
    $ /rest/db/status?folder=m2          -> state=idle needBytes=0 errors=0

#### 問い 1: 中心は共有フォルダを全部持っているか

    $ /rest/db/completion?folder=claude-sync&device=3J4TRX4-…
      {'completion': 100, 'globalBytes': 28005, 'globalItems': 9,
       'needBytes': 0, 'needDeletes': 0, 'needItems': 0, 'remoteState': 'valid'}
    $ /rest/db/completion?folder=m2&device=3J4TRX4-…
      {'completion': 100, 'globalBytes': 42010655195, 'globalItems': 13031,
       'needBytes': 0, 'needDeletes': 0, 'needItems': 571, 'remoteState': 'valid'}

🟢 **どちらも 100%、不足のバイト数は 0。**
`m2` の `needItems=571` は `needBytes=0` であることから**大きさ零の要素**と解釈した。
**中心で命令を実行できないため内訳は UNKNOWN**（前契約 andrew も同じ扱い。andrew は 1478 件）。

#### 問い 2: 自分の試験ファイルを中心が持っているか

    $ /rest/db/file?folder=claude-sync&file=probe-ilya.txt  -> 200
      availability = [{'id': '3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE',
                       'fromTemporary': False}]
      global: size=78 modifiedBy=UODEAXZ… version=['UODEAXZ:1787595636']
      どの相手から取れるか = ['philip(中心)']

🟢 **`availability` に中心の識別子が現れた。大きさ 78 は置いたものと一致し、
`modifiedBy` は自分である。往復している。**

#### この判定が空振りでないことの確認（陽性対照）

    $ /rest/db/file?folder=claude-sync&file=zzz-no-such-file.txt -> HTTP 404
    $ /rest/db/file?folder=claude-sync&file=probe-ilya.txt       -> HTTP 200

**存在しない名前では 404 を返す。** 判定は「常に 200 を返す壊れ方」ではない。
**一度目から 200 だったのは、`state=idle` を待ってから問うたためである**
（前契約が踏んだ 404 は本契約では起きていない）。

### Step 3: 中心から届いたものを測る

    $ du -sb ~/claude-sync && find ~/claude-sync -type f | wc -l
    28122   /home/ubuntu/claude-sync
    10

**開始時 4528 バイト / 1 件 → 28122 バイト / 10 件（+23594 バイト / +9 件）。**

    $ find ~/claude-sync -type f -printf '%s\t%p\n' | sort -k2
    117   ./.stfolder/syncthing-folder-e1f429.txt            ← 同期処理が作る目印
    83    ./probe-andrew.txt                                 ← 中心から届いた
    40    ./probe-bengio.txt                                 ← 中心から届いた
    78    ./probe-ilya.txt                                   ← 自分が置いた
    5104  ./sync-alerts.log
    4784  ./sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log   ← 中心から届いた
    6016  ./sync-alerts.sync-conflict-20260824-160823-3C2LTP7.log   ← 中心から届いた
    6016  ./sync-alerts.sync-conflict-20260824-160825-3C2LTP7.log   ← 中心から届いた
    2942  ./sync-alerts.sync-conflict-20260824-181840-UODEAXZ.log   ← 本契約で生まれた
    2942  ./sync-alerts.sync-conflict-20260824-181842-UODEAXZ.log   ← 本契約で生まれた

**`probe-andrew.txt` は 83 バイト**で、前契約 andrew の記録（判定 S）と一致する。

#### 衝突は「上書き」ではなく「併存」だった。中身が消えていない

    $ for f in …; do grep -c '\[ilya\]' $f … done
    sync-alerts.log                                        size=5104  ilya=47 bengio=0 andrew=0  philip=0
    sync-alerts.sync-conflict-20260824-181840-UODEAXZ.log  size=2942  ilya=0  bengio=5 andrew=19 philip=4
    sync-alerts.sync-conflict-20260824-181842-UODEAXZ.log  size=2942  ilya=0  bengio=5 andrew=19 philip=4

**起きたのは「自分の内容が勝ち、中心の内容が衝突ファイルとして残った」方である。**
自分の 47 行は `sync-alerts.log` に、中心側の 28 行は衝突ファイル 2 件に**両方残っている。**
**消えたものは無い**（禁止 4 の停止条件に当たらない）。

衝突ファイルは **本契約で 2 件**生まれた。他の 3 件は前契約由来で中心から届いたものである。

### Step 4: repo の同期の様子を測る

**完了を待っていない。** 問い合わせた時点で既に収束していた。

    $ /rest/db/status?folder=m2
      state             idle
      globalBytes       42010655195      globalFiles  5202   globalDirectories 7013
      localBytes        42010655195      localFiles   5202
      needBytes         0                needFiles    0      needDeletes 0
      inSyncBytes       42010655195      inSyncFiles  5202
      errors            0                pullErrors   0

    $ grep -E "Ready to synchronize|Completed initial scan" ~/.syncthing.log
    18:18:38 Ready to synchronize    (folder.id=claude-sync)
    18:18:38 Ready to synchronize    (folder.id=m2)
    18:18:38 Completed initial scan  (folder.id=claude-sync)
    18:19:53 Completed initial scan  (folder.id=m2)          ← 起動の 75 秒後

    $ grep -c -iE "\bWRN\b|\bERR\b" ~/.syncthing.log
    0

**`m2` の初回走査は 75 秒で終わり、`needBytes=0` で収束した。誤りの記録は 0 件。**
本ホストは repo が既に git 経由でほぼ同一だったため、転送すべき差分が小さかったと解釈する。
**前契約 andrew は起動直後 `needBytes=689548250 / needItems=1731` から約 4 分半で収束しており、
本ホストのほうが速い。ホストごとに違う。**

`du -sb` の repo（47515332495 バイト）と同期対象の global（42010655195 バイト）の差は
`.stignore` による除外である。

---

## 6. Phase E — 報告と送出

### Step 2: 触っていないものが無変更であること

    $ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  keeper.sh    ← 開始時と同じ
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  m2-sync.sh   ← 開始時と同じ
    $ git --no-pager diff --stat -- scripts/sync/ | wc -l
    0
    $ git --no-pager diff --stat -- scripts/sync/hub_keys/ scripts/sync/device_ids/ | wc -l
    0                                        ← 受け入れ一覧は変更していない（禁止 3）
    $ sha256sum .stignore .stglobalignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore        ← 開始時と同じ
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore  ← 開始時と同じ
    $ ls -1 ~/.tunnel_to_* | wc -l && stat -c '%a %s %n' ~/.tunnel_to_philip
    1
    600 58 /home/ubuntu/.tunnel_to_philip
    $ scanarg.sh keeper.sh
    arg=keeper.sh count=1 pids= 43963        ← 常駐処理を止めていない（禁止 12）

### Step 3: 検証

    $ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-ilya-syncthing-node
    OK   T-2026-08-24-ilya-syncthing-node
    1 task(s), 0 failed
    validate_exit=0

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-08-24-ilya-syncthing-node
    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=… sys.prefix=…
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS tasks/T-2026-08-24-ilya-syncthing-node/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              WARN 規則 8 件のうち 2 件が該当:
                                   separated_source@SPEC.md:47,
                                   host_mismatch@SPEC.md:5（終了コードは変わらない）
    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
    preflight_exit=0

**`SKIP` は合格ではなく実行されなかったことを意味する。** 実行されなかったのは
`P2 cuda_ext_loaded` `P3 deterministic_flags` `P4 prereg_committed` `P5 frozen_source_hash` の 4 件。

**`P9 spec_lint` の `host_mismatch@SPEC.md:5` は、本契約が実測した事象そのものである。**
契約は実行ホストを `ilya` と書くが、`hostname` は `aolab` を返す。層 4 の機械が
起票者の誤り 1 と同じものを独立に捕まえた。**契約の誤りは実行者の責任ではないため
終了コードは変わらない。**

`conventions_rev` は §1 で実測し、`d422b08` で一致したため置換していない。

    $ source .venv/bin/activate && make forbidden-check
    {"base": "origin/phase0", "changed": 7, "checked": 7, "errors": [], "excluded": 0,
     "excluded_paths": [], "generated_directories": ["context/auto/"],
     "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
    forbidden_exit=0

`changed: 7` の内訳:

    $ git --no-pager diff --name-only origin/phase0 --
    docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md   ← 開始前から存在。触っていない
    $ git status --porcelain
     M docs/sessions/digest/2026-08-23-…md
    ?? tasks/T-2026-08-24-ilya-syncthing-node/          ← SPEC.md spec.yaml audit.md RESULT.md result.yaml
    ?? tasks/inbox.d/T-2026-08-24-ilya-syncthing-node.md

**契約の 5 ファイル＋受け皿の 1 件＝ 6 件が本契約の変更である。**
`docs/sessions/digest/…` は本契約が作ったものではないため **commit に含めない。**

**禁止 6 に従い `make taskindex` / `make inbox` は実行していない**（生成物を再生成しない）。

### Step 4: 送信前の秘匿検査（**検査そのものが値を出力しない**）

`scratchpad/secretscan.py`。`tools/report_task.py` の `scan_secrets` と同じ形の規則を使い、
**実値の直接照合を先に**行う。判定するのは件数ではなく形である。

    $ source scripts/load_env.sh && .venv/bin/python scratchpad/secretscan.py
    照合対象の実値の種類 = 3 ['NOTION_API_KEY', 'WANDB_API_KEY', 'syncthing_gui_apikey']
    literal_leaks = 0
    shape_hits = 0
    decoy_literal_detected = 3/3
    decoy_shape_hits = {'Notion の内部鍵': 1, '鍵らしい代入': 1}
    secretscan_exit = 0

**実値は 3 種とも本文に現れない。形の該当も 0 件。**
**陽性対照は 3/3 と 1/1・1/1 で当たっており、検査は空振りしていない。**
**囮は変数の中だけに置き、ファイルへ書いていないため commit にも含まれない。**
**出力に秘匿の値は現れていない**（種類の名前・件数・長さだけ）。

# audit — T-2026-08-24-philip-syncthing-hub

実測の生出力を要約せずに貼る（SPEC 申し送り 8）。

## Phase A: 開始状態の封印と控えの保存

### Step 1: 設定と実行ファイルの現状（2026-08-23 JST）

`for f in ~/.local/state/syncthing/*; do test -f "${f}" && echo "$(sha256sum "${f}") $(stat -c '%s %a' "${f}")"; done`

    5f3b4bd8791d6fa873f5dd0c1089dc9878b3525e40e612b4cd07ac7558a5b4ac  /home/ubuntu/.local/state/syncthing/cert.pem 794 664
    abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /home/ubuntu/.local/state/syncthing/config.xml 8494 600
    92629ef108b100a80d3d0c511a3679239a7a21e80a67bfe3468dd1294d7d52f6  /home/ubuntu/.local/state/syncthing/key.pem 288 600

`ls -la ~/bin/syncthing` / `sha256sum ~/bin/syncthing`

    -rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing

**実行権は 644。** SPEC の期待どおりで、起動しうる状態ではない。

`ls -a ~/ | grep -c '^\.tunnel_to_'`

    0

`du -sh ~/claude-sync/` / `find ~/claude-sync/ -type f | grep -c ''`

    8.0K	/home/ubuntu/claude-sync/
    1

### Step 1 追加（handoff 2.1 が求める項目）

    syncthing=停止
    keeper=動作中

    -rwxr-xr-x 1 ubuntu ubuntu 2709 Aug 23 17:27 /home/ubuntu/bin/keeper.sh
    -rwxrwxr-x 1 ubuntu ubuntu 7342 Aug 23 21:29 /home/ubuntu/bin/m2-sync.sh

`sha256sum .stglobalignore .stignore`

    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore

除外規則は正本と一致（要約値が同一）。

**handoff 2.1 の基準 4 項目（同期処理が停止 / 実行権 644 / 目印 0 件 / .stignore が正本と一致）をすべて満たす。**

### Step 2: 秘密鍵の本体が無いことの確認

`grep -c "BEGIN.*PRIVATE" ~/.local/state/syncthing/config.xml`

    0

零のため版管理へ控えを置いた。

    abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before

Step 1 の `config.xml` の要約値と一致。

repo の外にも控えを置いた（handoff 2.2。repo 内だけだと同期対象と版管理の両方を汚す）。

    /home/ubuntu/.local/state/syncthing.bak.20260823-214759
    5f3b4bd8791d6fa873f5dd0c1089dc9878b3525e40e612b4cd07ac7558a5b4ac  .../cert.pem 794 664
    abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  .../config.xml 8494 600
    92629ef108b100a80d3d0c511a3679239a7a21e80a67bfe3468dd1294d7d52f6  .../key.pem 288 600

三ファイルとも開始時と一致。控えは完全である。

### Step 3: 戻し方（記録のみ。実行していない）

    cp tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before \
       ~/.local/state/syncthing/config.xml
    chmod 600 ~/.local/state/syncthing/config.xml
    chmod 644 ~/bin/syncthing

最後の一行が要である。実行権を落とせば常駐処理が起こし直さない。

repo 外の控えから戻す場合（handoff 2.7、鍵と証明も含めて戻す）:

    chmod 644 ~/bin/syncthing
    pkill -x syncthing
    cp -a ~/.local/state/syncthing.bak.20260823-214759/. ~/.local/state/syncthing/

### Step 4: 五台の識別子（版管理から読む）

`for f in scripts/sync/device_ids/*.txt; do echo "$(basename "${f}" .txt) $(cat "${f}")"; done`

    andrew 3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4
    bengio 4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO
    ilya UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY
    lecun OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3
    philip 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE

    件数: 5

`grep -o 'device id="[^"]*"' ~/.local/state/syncthing/config.xml`

    device id="3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE"
    device id="3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE"
    device id="3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE"
    device id=""

自分（philip）の値は設定と一致した。三件はいずれも自分の識別子で、実体は一件。
末尾の空の値は既定値の記載である（前契約が「grep -c は 4 だが実体は 1」と記録したものと同じ形）。

### G1 の判定

| # | 完了判定 | 結果 |
|---|---|---|
| 1 | 設定と実行ファイルの要約値と権限を記録した（実行権が 644） | 満たす |
| 2 | 設定に秘密鍵の本体が無いことを確かめ、控えを版管理へ残した | 満たす（0 件） |
| 3 | 戻し方を記録した（実行していない） | 満たす |
| 4 | 五台の識別子を読み、自分の値が設定と一致した | 満たす |

## Phase B: 設定の組み立て

同期処理が停止していることを再確認してから編集した（handoff 2.3。動作中の書き換えは上書きされる）。
一時ファイルへ書き、妥当性を確かめてから本体へ置き換えた。

### 変更点

    登録名: aolab -> philip            （handoff 変更1。philip と ilya が同じ OS ホスト名のため）
    追加した相手: lecun, bengio, andrew, ilya  （住所はすべて dynamic）
    共有フォルダ: claude-sync, m2 (type=sendreceive, 共有相手 5 台=自分＋4台)
    削除: folder id=default            （/home/ubuntu/Sync は実在しない）
    globalAnnounceEnabled: true -> false
    relaysEnabled: true -> false
    localAnnounceEnabled: true -> true （変更なし。旧構成も true）

識別子はすべて `scripts/sync/device_ids/*.txt` から読んだ。SPEC 本文の値は使っていない。

### Step 5: 書式と件数の確認

    xml_ok

実体の device 数（ルート直下の device のみ）:

    実体の device 数: 5
      philip   3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE addr=dynamic
      lecun    OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3 addr=dynamic
      bengio   4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO addr=dynamic
      andrew   3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4 addr=dynamic
      ilya     UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY addr=dynamic

    folder id=claude-sync  path=/home/ubuntu/claude-sync   type=sendreceive  共有相手=5
    folder id=m2           path=/home/ubuntu/slocal2/m2    type=sendreceive  共有相手=5

`grep -o 'folder id="[^"]*"'`:

    folder id="claude-sync"
    folder id="m2"
    folder id=""

三件目は `<defaults>` 内のテンプレートであり、共有フォルダの定義ではない（開始時から在る）。
**`default` は消えている。**

`grep -c 'device id='` は **17**。実体 5 + 共有相手 5×2 + defaults 2 の合計であり、
前契約の「単純な grep は実体の数を表さない」という記録と同じ形である。

`grep -n -E "globalAnnounceEnabled|relaysEnabled|localAnnounceEnabled"`:

    172:        <globalAnnounceEnabled>false</globalAnnounceEnabled>
    173:        <localAnnounceEnabled>true</localAnnounceEnabled>
    179:        <relaysEnabled>false</relaysEnabled>

`gui address = 127.0.0.1:8384`（触っていない）。

### Step 6: 権限

    600 /home/ubuntu/.local/state/syncthing/config.xml

変更後の要約値:

    0b3e96ee96fd2c04d6e9dd3983e68daf3cf91b4484743804710b12ea9b98b867  config.xml

鍵と証明は触っていない（開始時と一致）:

    5f3b4bd8791d6fa873f5dd0c1089dc9878b3525e40e612b4cd07ac7558a5b4ac  cert.pem
    92629ef108b100a80d3d0c511a3679239a7a21e80a67bfe3468dd1294d7d52f6  key.pem

### G2 の判定

| # | 完了判定 | 結果 |
|---|---|---|
| 5 | 告知と中継を無効にした（三つの要素の値を記載） | 満たす |
| 6 | 四台を相手として登録した（識別子の出所を明記） | 満たす（版管理から） |
| 7 | 共有フォルダを二つ定義した | 満たす |
| 8 | 使わない共有フォルダを消した | 満たす |
| 9 | 書式が解析でき、実体の件数が期待どおり | 満たす（実体 5 / folder 2） |
| 10 | 権限が 600 のまま | 満たす |

## Phase C: 起動と待ち受けの確認

### Step 1: 起動前の状態（両方向の対照つき）

    syncthing=0
    keeper.sh=1
    zsh=4
    zzz_no_such=0

実在する語 `zsh` が 1 以上、存在しない語 `zzz_no_such` が 0。**対照は両方向で成立している。**

### Step 2: 実行権を戻す

    -rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing

この時点では Task 1 と要約値が一致していた（権限だけを変えた）。

**起こし方は handoff 2.5 を正とした**（SPEC は「待たずに明示的に起こしてもよい」としたが、
handoff は「手で起動しない。常駐処理に任せる」と指定している。二重起動を避けるため）。

常駐処理による起動を待った。**1760 秒後（2026-08-23T22:29:14+09:00 JST 相当の UTC 表記
2026-08-23T22:29:14+00:00）に起動を検出。** 周期 1800 秒と整合する。

### Step 3: 動いている数

    syncthing=2
    keeper.sh=1
    zsh=4
    zzz_no_such=0

**2 と出るが二重起動ではない。** 親子関係と環境変数で切り分けた。

    PID     PPID    CMD
    122452  72428   /home/ubuntu/bin/syncthing serve --no-browser   STMONITORED=0  ← monitor
    122530  122452  /home/ubuntu/bin/syncthing serve --no-browser   STMONITORED=1  ← その子

72428 は keeper.sh の PID である。**keeper が起こした起動は 1 件**で、monitor が worker を
1 つ持つ Syncthing の標準構成である。常駐処理は 1 件のまま。

**SPEC Step 3 の「実行ファイル名で数えて 1 件」という判定は、この構成では正常時にも必ず 2 を
返す。判定として働いていない**（issuer_defects: check_does_not_check）。

### Step 4: 待ち受け

    count=7
    port_22=LISTEN
    port_22000=LISTEN
    port_22001=-
    port_8384=LISTEN

**`22000` が待ち受け、`8384` も立ち、`22001` は立っていない。** 期待どおり。

### Step 5: 設定の読み込みと共有領域の保全

    folder id="claude-sync"
    folder id="m2"
    folder id=""

    実体の device 数: 5   （lecun / ilya / andrew / philip / bengio、すべて addr=dynamic）
    folder id=claude-sync  path=/home/ubuntu/claude-sync   type=sendreceive  共有相手=5
    folder id=m2           path=/home/ubuntu/slocal2/m2    type=sendreceive  共有相手=5
    globalAnnounceEnabled=false
    relaysEnabled=false
    localAnnounceEnabled=true

起動後の config.xml 要約値: `146b07d436fcb8f1a8d93eaef37473d5d66859c68d3e51a1a3c594123a8c8492`
（Phase B 直後は `0b3e96ee...`）。**起動時に書き戻された。定義は消えていない。** 権限は 600 のまま。

`~/claude-sync/`:

    開始時: 8.0K / 1 ファイル
    終了時: 16K / 2 ファイル
    814 /home/ubuntu/claude-sync/sync-alerts.log
    117 /home/ubuntu/claude-sync/.stfolder/syncthing-folder-e1f429.txt

**開始時からあった `sync-alerts.log` は残っている。増えた 1 件は syncthing が作る目印である。
中身は減っていない**（禁止 5 を守った）。

### Step 6: 起動の記録

記録の場所は **`~/.syncthing.log`**。SPEC は `~/claude-sync/syncthing.log` と書いたが、
**そのファイルは存在しない**。`keeper.sh:42` の出力先が `~/.syncthing.log` であり、
handoff 2.6 の記載と一致する（issuer_defects: shell_assumption）。

    [start] 2026/08/23 22:29:05 INFO: Upgrade available (current "v1.27.10" < latest "v2.1.3")
    [start] 2026/08/23 22:29:18 INFO: Upgraded to "v2.1.3", exiting now.
    [monitor] 2026/08/23 22:29:18 INFO: Restarting monitor...
    2026-08-23 22:29:18 INF syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64)
    2026-08-23 22:29:18 INF Archiving a copy of old config file format (path=.../config.xml.v37)
    2026-08-23 22:29:18 INF Migrating old-style database to SQLite; this may take a while...
    2026-08-23 22:29:18 INF Migration complete (files=0 blocks=0 duration=0s)
    2026-08-23 22:29:18 INF Calculated our device ID (device=3J4TRX4-...-DZOCQQE)
    2026-08-23 22:29:18 INF QUIC listener starting (address="[::]:22000")
    2026-08-23 22:29:18 INF TCP listener starting (address="[::]:22000")
    2026-08-23 22:29:18 INF GUI and API listening (address=127.0.0.1:8384)
    2026-08-23 22:29:18 INF Loaded configuration (name=philip)
    2026-08-23 22:29:18 INF Loaded peer device configuration (device=4NIRI4M name=bengio address="[dynamic]")
    2026-08-23 22:29:18 INF Loaded peer device configuration (device=OOOTQMG name=lecun address="[dynamic]")
    2026-08-23 22:29:18 INF Loaded peer device configuration (device=UODEAXZ name=ilya address="[dynamic]")
    2026-08-23 22:29:18 INF Loaded peer device configuration (device=3C2LTP7 name=andrew address="[dynamic]")
    2026-08-23 22:29:18 INF Ready to synchronize (folder.id=claude-sync folder.type=sendreceive)
    2026-08-23 22:29:18 INF Ready to synchronize (folder.id=m2 folder.type=sendreceive)
    2026-08-23 22:29:18 INF Completed initial scan (folder.id=claude-sync folder.type=sendreceive)
    2026-08-23 22:29:38 INF Detected NAT services (count=0)
    2026-08-23 22:29:48 INF Detected NAT type (uri=quic://0.0.0.0:22000 type="Port restricted NAT")
    2026-08-23 22:29:48 INF Resolved external address (uri=quic://0.0.0.0:22000 address=quic://131.113.39.33:62442 via=stun.voipstunt.com:3478)

相手へ繋がらない記録は出ていない（ノードがまだ中継を張っていないため正常）。

### 想定外 1: 自動アップグレード（v1.27.10 -> v2.1.3）

**起動と同時に本体が更新された。** 原因は `autoUpgradeIntervalH=12`（既定値）であり、
**SPEC も handoff もこの設定に触れていない。**

    起動前: 32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  26730145 bytes  v1.27.10
    起動後: e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4  27045912 bytes  v2.1.3

**完了判定 12「要約値が変わっていない」は満たさない。** 権限の変更だけでは済まなかった。

副作用として設定形式とデータベースが移行された。

    -rw------- config.xml       14027   （新形式）
    -rw------- config.xml.v37   13800   （旧形式の控え。syncthing が自動で残した）
    drwxr-xr-x index-v0.14.0.db-migrated
    drwx------ index-v2

**他 4 台は v1.27.10 のままである**（本契約は他ホストに触れないため未確認・UNKNOWN）。

利用者の判断により **v2.1.3 のまま進め、再発を止めるために自動更新を無効化した。**

    ~/bin/syncthing cli config options auto-upgrade-intervalh set 0   # exit=0
    変更前: 12  ->  変更後: 0
    <autoUpgradeIntervalH>0</autoUpgradeIntervalH>
    600 /home/ubuntu/.local/state/syncthing/config.xml

動作中のため CLI を使った（handoff の言う「常駐が動いていれば命令列が使える」状態になった）。
CLI 経由で告知と中継が維持されていることも確かめた。

    global-ann-enabled     false
    relays-enabled         false
    local-ann-enabled      true

### 想定外 2: 外部通信が意図どおり止まっていない

SPEC と handoff は `globalAnnounceEnabled=false` と `relaysEnabled=false` により
「外部の告知先へ自分の識別子と住所を送らない」ことを意図していた。**別の経路が残っている。**

    stunServer            = default   -> 外部 STUN へ問い合わせ済み（記録に stun.voipstunt.com:3478）
    natEnabled            = true      -> NAT 越えを試行
    crashReportingEnabled = true      -> 障害時に外部へ送信
    autoUpgradeIntervalH  = 12        -> 想定外 1 の原因（本契約で 0 にした）

STUN により外部から見た住所（`131.113.39.33:62442`）が判明している。

**契約の Phase B に記載が無く範囲外のため、利用者の判断により変更していない**（記録のみ）。
`autoUpgradeIntervalH` だけは想定外 1 の再発防止として 0 にした。

### G3 の判定

| # | 完了判定 | 結果 |
|---|---|---|
| 11 | 起動前の状態を記録した（両方向の対照つき） | 満たす |
| 12 | 実行権を戻し、要約値が変わっていない | **満たさない**（自動アップグレードにより変化） |
| 13 | 同期処理が一件だけ動いている | 実体として満たす（monitor+worker。keeper が起こした起動は 1 件） |
| 14 | `22000` が待ち受けている（`22001` は立っていない） | 満たす |
| 15 | 共有フォルダの定義が残り、`~/claude-sync/` の中身が減っていない | 満たす |
| 16 | 起動の記録を読み、異常の有無を記載した | 満たす（想定外 2 件を検出） |

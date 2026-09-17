# audit — T-2026-09-17-efros-syncthing-join

実行ホスト `efros` / repo `~/slocal2/m2` / 分岐 `feat/efros-syncthing-join`（`origin/phase0` = `efc64453` と同一）
開始時刻 **2026-09-17T15:57:31+09:00 (JST)**

測定器は `scratchpad/probe.sh`。プロセスは `/proc/PID/exe`（`count_exe`）または
`/proc/PID/cmdline`（`count_cmd`）で数える。待ち受けは `/proc/net/tcp{,6}` の `st=0A` を数える
（**`ss` `netstat` `lsof` `ip` はいずれも本ホストに不在**）。

## Phase A — 開始状態の封印と中心への到達

### A-1 測定器そのものの検証（両方向の対照）

最初の実装は正の対照が 0 を返した（`/bash` で数えたが bash プロセスが 1 件も無かった）ため破棄した。
次に `count_cmd` の否定対照 `zzz_no_such_token` が **1** を返した。実体を `list_cmd` で特定したところ、
**自分の命令文をそのまま命令行に持つ自分の子シェル**（PPID = 自分の PID、`shell-snapshots` を含む）であった。
`keeper.sh` `m2-sync.sh` `22001` が各 1 件と出ていたのも同一の偽陽性である。
`shell-snapshots` を含む命令行を除外して修正した。修正後の対照:

| 対照 | 値 |
|---|---|
| 正 `count_exe /zsh` | 5 |
| 負 `count_exe zzz_no_such_token` | 0 |
| 正 `count_cmd node` | 12 |
| 負 `count_cmd zzz_no_such_token` | **0**（修正前は 1） |
| 正 `listening 22`（sshd） | 2 |
| 負 `listening 65533` | 0 |

### A-2 開始状態（実測）

| 対象 | 実測値 |
|---|---|
| `~/bin/` の中身 | **`syncthing` の 1 件のみ。`keeper.sh` も `m2-sync.sh` も無い** |
| `~/bin/syncthing` sha256 | `e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4` |
| `~/bin/syncthing` 権限・大きさ | `600` / 27045912 bytes（**実行権が落ちている**） |
| `~/.local/state/syncthing/config.xml` sha256 | `7b060603946c987db7ea33d20710cc83deeafa6a913a97eed26e91a1df2a2fb6` |
| 同 権限・大きさ | `600` / 6571 bytes |
| 中継の目印 `~/.tunnel_to_philip` | **0 件**（存在しない） |
| syncthing プロセス（`exe`） | **0** |
| keeper.sh / m2-sync.sh プロセス | **0 / 0** |
| ssh 中継（`22001` を含む命令行） | **0** |
| 待ち受け `22000` / `22001` / `8384` | **0 / 0 / 0** |
| `~/claude-sync/` | **存在しない**（大きさ 0 bytes、ファイル 0 件、ディレクトリ 0 件） |
| repo `~/slocal2/m2` の大きさ | **68314468570 bytes**（`du -sb`、丸めていない） |
| repo のファイル件数 | **234767 件** |
| `~/.ssh/known_hosts` | 1 行、sha256 `4edcd9020926646dd584e2053c3975b170dc528d9d5843a7be5514fc6ea8de62` |
| `~/.ssh/authorized_keys` sha256 | `59346feef0f797deafea4550c40c68e87d268e1e67106d78a4c2c458e85b38d1` |
| `~/.zshrc` sha256 | `d5e947dfa81c354a4d92afe9cf7eb91ef42c854a4ba71a0f46bfc81f55001729` |
| 開始時の未追跡 | 3 件（`docs/sessions/digest/` 2 件、本契約のディレクトリ 1 件） |

**`~/claude-sync/` が存在しない。** 五台と違い本ホストは一度も群れに入っていないため、共有領域そのものが無い。
`m2-sync.sh` が `mkdir -p ~/claude-sync` を行うため、常駐処理の起動時に作られる。

### A-3 控え

    ~/.syncthing-config-backup-20260917-155900/

repo の外、かつ `~/.local/state/syncthing` と同一のファイルシステム（`stat -c %d` がいずれも **233**）。
`cp -a` で移動ではなく複製。中身（sha256）:

| ファイル | sha256 |
|---|---|
| `config.xml` | `7b060603946c987db7ea33d20710cc83deeafa6a913a97eed26e91a1df2a2fb6` |
| `cert.pem` | `632391d59670df14dd611bad71588d996ff3b3ba73f6a7eaa8855a1e8df054c9` |
| `key.pem` | `98cc18b47912ee62169222e9d77bf93dafe58bb45e60a40ab58c3231c2fdedb6` |

**版管理内へは置かない。** よって画面の鍵を伏せる操作は不要（表示時のみ `apikey` を伏せた）。

### A-4 戻し方（**記録のみ。実行していない**）

    # 1. 同期処理を止める（実行権を落とせば keeper が起こせなくなる）
    chmod 600 ~/bin/syncthing
    pkill -x syncthing
    # 2. 常駐処理と中継を止める
    pkill -f keeper.sh ; pkill -f 'ssh.*-L 22001:127.0.0.1:22000'
    # 3. 中継の目印を外す
    rm -f ~/.tunnel_to_philip
    # 4. 設定を開始時の内容へ戻す
    cp -a ~/.syncthing-config-backup-20260917-155900/config.xml ~/.local/state/syncthing/config.xml
    chmod 600 ~/.local/state/syncthing/config.xml
    # 5. 配置した常駐処理を外す（.zshrc の起動行は本契約の追記ではない。後述 C-3）
    rm -f ~/bin/keeper.sh ~/bin/m2-sync.sh ~/.keeper.lock

**`chmod 600 ~/bin/syncthing` だけで起動は止まる。** keeper は `[ -x ~/bin/syncthing ]` を
起動の条件にしているため、実行権が落ちていれば起こさない。

### A-5 中心への到達（**中心で命令を実行していない**）

版管理から読んだ識別子:

| 項目 | 値 |
|---|---|
| 中心 `scripts/sync/device_ids/philip.txt` | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| 自分 `scripts/sync/device_ids/efros.txt` | `LW4CO4U-XINDYL5-WDTK4LN-NANREIJ-LHSPA6F-6VPGZ3R-2ADLKLP-GG6AUQW` |
| 設定の自分の識別子 | 同上（**一致**） |

到達確認は `ssh -N`（**遠隔で実行する命令を与えない形**）で行い、受け入れの控えは
`-o UserKnownHostsFile=<隔離>` へ逃がした。

| 向き | 命令 | 結果 |
|---|---|---|
| 正 | `ssh -N -p 50072 -i ~/.ssh/id_ed25519_efrostophilip ubuntu@192.168.196.150` | `Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey".` / 終了コード **124**（時間切れ＝認証後に居座った） |
| 負 | 同上で口を `50073` | `Connection refused`。`Authenticated to` は出ない |

`~/.ssh/known_hosts` は前後で sha256 が不変（`4edcd902...`）。隔離側に 1 行だけ増えた。

**Gate G1: PASS**

## Phase B — 設定の組み立て（直接編集。起動前）

組み立ては `scratchpad/build_config.py`（`xml.etree.ElementTree`）で一度に行った。
**`<defaults>` 節は読むだけで編集していない。** 新しい `folder` と `device` は
ひな型を複製して作った（`copy.deepcopy`）。既定値の取りこぼしを避けるためである。

### B-1 要素名は実在を確かめてから変えた

`setval()` は対象の要素が見つからなければ `assert` で止まる。3 件とも実在した。

| 要素 | 変更前 | 変更後 |
|---|---|---|
| `options/autoUpgradeIntervalH` | `12` | **`0`** |
| `options/globalAnnounceEnabled` | `true` | **`false`** |
| `options/relaysEnabled` | `true` | **`false`** |
| `options/localAnnounceEnabled` | `true` | `true`（**有効のまま**） |

### B-2 自分の登録名

**実測値は `efros` であった**（予想せず読んでから判定した）。よって **置換は 0 件**。
五台の実測（`Bengio` / `Andrew` / `aolab`）と違い、本ホストは初期値が既に正しかった。
自分の識別子は `scripts/sync/device_ids/efros.txt` と一致する（A-5）。

### B-3 中心の登録

| 項目 | 値 |
|---|---|
| 識別子 | `scripts/sync/device_ids/philip.txt` を読んだ（**版管理が出所**） |
| 名前 | `philip` |
| 住所 | `tcp://127.0.0.1:22001`（**中継の出口**） |

最上位の `device` は **2 件**（`efros` と `philip`）。**他のノードは登録していない。**

### B-4 共有フォルダ

| 識別子 | 位置 | 型 | 共有相手 |
|---|---|---|---|
| `claude-sync` | `/home/ubuntu/claude-sync` | `sendreceive` | 2 件 |
| `m2` | `/home/ubuntu/slocal2/m2` | `sendreceive` | 2 件 |

共有相手の属性名は **`id`**（`deviceID` ではない）。ひな型の `device` 子要素が自分だけを持つので、
それを複製して識別子だけ中心へ差し替えた。

### B-5 階層を見て数えた（ひな型と取り違えない）

| XPath | 値 |
|---|---|
| `count(/configuration/folder)` | **2** ← 最上位の共有フォルダ |
| `count(/configuration/defaults/folder)` | 1 ← ひな型 |
| `count(//folder)` | 3 ← 対照。2 と 1 が区別できている |
| `count(/configuration/device)` | 2 |
| `count(/configuration/defaults/folder[@id=""])` | 1 ← ひな型は空のまま |
| `count(/configuration/defaults/device[@id=""])` | 1 ← 同上 |

`xmllint --noout` が exit 0（解析できる）。権限は `600` のまま。
大きさ 6571 → 11179 bytes、sha256 `7b060603...` → `c4e6c320949fd1276328c67f7c9d2b35e4b513c5ffbf98db9450f112447d63b5`。

**Gate G2: PASS**

## Phase C — 常駐処理の配置（五台には無かった工程）

### C-1 配置

正本は **`origin/phase0` の git オブジェクトから直接展開**した
（`keeper.sh` の冒頭がその方法を指定している。作業ツリーの分岐に依存させないため）。

    git show origin/phase0:scripts/sync/keeper.sh  > ~/bin/keeper.sh
    git show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh
    chmod 755 ~/bin/keeper.sh ~/bin/m2-sync.sh

| ファイル | 正本の sha256 | 配置物の sha256 | 一致 |
|---|---|---|---|
| `keeper.sh` | `9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90` | 同左 | ○ |
| `m2-sync.sh` | `bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f` | 同左 | ○ |

作業ツリーの `scripts/sync/*.sh` も `origin/phase0` と同一の要約値であった（差分なし）。
`~/bin/` は 1 件（`syncthing`）から **3 件**になった。権限は `755`。

### C-2 構文検査（陰性対照つき）

| 対象 | `bash -n` 終了コード |
|---|---|
| `~/bin/keeper.sh` | **0** |
| `~/bin/m2-sync.sh` | **0** |
| 負の対照（`if true; then` だけの脚本） | **2**（検査は落ちる) |

### C-3 起動行 — **追記していない**

`~/.zshrc` に **既に存在した**（`grep -c 'keeper.sh' ~/.zshrc` = **1**）。

    135:# >>> egosurgery keeper >>>
    136:# 常駐スーパーバイザ。flock で多重起動を防ぐため毎回呼んで安全。
    137:( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
    138:# <<< egosurgery keeper <<<

**本ホストは起動行だけ先に配られていて、指す先の脚本が無い状態であった。**
二重起動になるため追記していない。`~/.zshrc` の sha256 は開始時から不変
（`d5e947dfa81c354a4d92afe9cf7eb91ef42c854a4ba71a0f46bfc81f55001729`）。

### C-4 抑止の目印

`~/slocal2/m2/.sync-pause` を置いた（0 bytes）。

| 確認 | 実測 |
|---|---|
| 版管理が無視するか | `.gitignore:240:.sync-pause` |
| 同期が運ばないか | `.stignore:68` が総取り規則 `**`。**この 1 台にだけ効く** |
| 配置物が対応している版か | `grep -c sync-pause ~/bin/m2-sync.sh` = **2**（0 なら未対応） |

**Gate G3: PASS**

## Phase D — 中継を張り、起動する

順序は **目印 → 常駐処理 → 中継 → 実行権 → 同期処理**。

### D-1 目印

`~/.tunnel_to_philip`（59 bytes、権限 `600`、2 行）。`~/.tunnel_to_*` は **1 件**。

    /home/ubuntu/.ssh/id_ed25519_efrostophilip
    192.168.196.150

### D-2 常駐処理を起こした（16:10:38 JST）

    ( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null

| 確認 | 実測 |
|---|---|
| `keeper.sh` の件数 | **1**（PID 53967、PPID=1。負の対照は 0） |
| 多重起動を防ぐ錠 | `~/.keeper.lock` が作られた（16:10 付） |

### D-3 中継が立った（16:10:42 JST、**起動から約 4 秒**）

SPEC の実測（413〜1569 秒）は既に回っている keeper の次の周回を待つ場合の値である。
**本ホストは自分で起こしたため、最初の周回の先頭で即座に張られた。**

| 確認 | 実測 |
|---|---|
| 中継の処理 | PID 53974、**PPID=53967（keeper の子）** |
| 引数 | `ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i /home/ubuntu/.ssh/id_ed25519_efrostophilip ... ubuntu@192.168.196.150` ← **中心の住所を含む** |
| 待ち受け `22001` | **2**（IPv4 と IPv6）。負の対照 `65533` は 0、正の対照 `22` は 2 |
| 待ち受け `22000` | 0（同期処理はまだ起きていない） |

### D-4 起動に伴う副作用（記録）

| 対象 | 変化 | 出所 |
|---|---|---|
| `~/.ssh/known_hosts` | 1 行 → **2 行**、sha256 `4edcd902...` → `da06a57a32051e2afeb9e9fcf029f6d818f37e9f4445a3b54e789690589baa0a` | keeper の ssh が `StrictHostKeyChecking=accept-new` で追記した |
| `~/slocal2/m2/.stignore` | 2223 → 2692 bytes | keeper が `origin/phase0:.stglobalignore` から反映する（実装のとおり） |
| `~/claude-sync/` | **作られた** | `m2-sync.sh` の `mkdir -p` |
| `~/.ssh/authorized_keys` | **無変更**（`59346feef0f7...`） | — |

**抑止が効いていることを記録で確かめた。**

    2026-09-17 07:10:40 [efros] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）

（`sync-alerts.log` の時刻は UTC。JST では 16:10:40。）

### D-5 実行権を戻した（**中継が立ってから**）

| 項目 | 前 | 後 |
|---|---|---|
| 権限 | `600` | **`700`** |
| 大きさ | 27045912 | 27045912 |
| sha256 | `e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4` | **同一** |

版は `syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64)`。**SPEC の記載と一致。**

### D-6 同期処理が起動した（16:40:41 JST）

実行権を戻したのが 16:12 頃、起動は **16:40:41**。待ち時間は **1695 秒**（keeper の周回 1800 秒の内側）。
**周回を一度越えただけで起きた**（二度は越えていない）。

| 確認 | 期待 | 実測 |
|---|---|---|
| プロセス数 | 2 | **2** |
| 親子関係 | 監視役と作業役 | PID **73191**（PPID=53967 = keeper の子）→ PID **73210**（PPID=73191） |
| `22000` | 待ち受け | **1** |
| `22001` | 待ち受けのまま | **2** |
| `8384`（画面） | — | 1（`127.0.0.1` のみ） |
| 版 | 中心と同じ | 自分 **`v2.1.3`** / 中心 `clientVersion` **`v2.1.3`** |
| keeper と中継 | 生存 | 1 / 1 |

中心との接続（`/rest/system/connections`）:

    device=3J4TRX4 connected=True paused=False addr=127.0.0.1:22001 clientVersion=v2.1.3 type=tcp-client

**繋がっている相手は中心だけ**（接続 1 件）。自分の識別子は `LW4CO4U`（版管理の `efros.txt` と一致）。

記録の該当行:

    07:40:45 INF Established secure connection (device=3J4TRX4 connection.remote=127.0.0.1:22001 ... TLS1.3 ...)
    07:40:45 INF Additional device connection (device=3J4TRX4 address=127.0.0.1:22001 count=1)

`Established secure connection` は **3 件**（再接続を含む）。

### D-7 定義が保たれている（起動後）

| XPath | 値 |
|---|---|
| `count(/configuration/folder)` | **2** |
| `count(/configuration/defaults/folder)` | 1 |
| `count(//folder)` | 3 |
| `count(/configuration/device)` | 2 |
| `folder/@id` | `m2`, `claude-sync` |
| `options/autoUpgradeIntervalH` | **0** |
| `options/globalAnnounceEnabled` | `false` |
| `options/relaysEnabled` | `false` |
| `options/localAnnounceEnabled` | `true` |

**自動更新が走った形跡は無い**（`grep -ci upgrade ~/.syncthing.log` = **0**）。

**起票者の予測と食い違った点**: SPEC は「起動時に設定は書き戻される。要約値は変わる」と書くが、
**本ホストでは sha256 が `c4e6c320949fd1276328c67f7c9d2b35e4b513c5ffbf98db9450f112447d63b5` のまま変わらなかった**
（大きさ 11179 bytes も同じ）。v2.1.3 は内容に変更が無ければ書き戻さない。
定義での確認は SPEC の指示どおり行ったため判定には影響しない。

### D-8 共有フォルダの目印（SPEC に記載が無かった点）

`~/claude-sync/.stfolder` は **開始時に存在しなかった**（`~/slocal2/m2/.stfolder` は 7 月 3 日から在った）。
先回りして作らず実挙動を測ったところ、**syncthing が起動時（07:40 UTC）に自分で作った。**
フォルダは両方とも正常に走り出し、中心から索引を受け取っている。

    07:40:41 INF Peer has a new index ID (device=3J4TRX4 folder.id=claude-sync ...)
    07:40:41 INF Peer has a new index ID (device=3J4TRX4 folder.id=m2 ...)

**新しいホストを入れるとき、目印を人が作る必要は無い。**

**Gate G4: PASS**

## Phase E — 実際に届くことの確認

### E-1 自分から中心へ（16:41:58 JST に置いた）

    ~/claude-sync/probe-efros.txt
    efros probe 2026-09-17T16:41:58+09:00 nonce=1bff02a9dae611258cb35fa790b63229

| 項目 | 値 |
|---|---|
| sha256 | `0055a45f1725a3bda1f8684caebffe000c015d2d60b33fcbb82a86a7af798900` |
| 大きさ | **77 bytes** |

### E-2 中心が持っていることの確認（**中心で命令を実行していない**）

自ホストの画面の経路（`http://127.0.0.1:8384/rest/...`）へ問うた。
合言葉は `xmllint` で変数へ読み込み、**長さ 32 だけを表示して値は出していない。**

| 回 | 時刻 | 問い | 実測 |
|---|---|---|---|
| 一度目 | 16:42:11 | `db/completion?folder=claude-sync&device=<中心>` | `completion=99.997 needItems=1 needBytes=77` ← **中心はまだ持っていない** |
| 一度目 | 16:42:11 | `db/file?folder=claude-sync&file=probe-efros.txt` | `availability=None` |
| 二度目 | 16:44:55 | `db/completion` | **`completion=100 needItems=0 needBytes=0`** |
| 二度目 | 16:45:14 | `db/file` | **`availability=[{id: 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE}]`** |

**中心へ届くまで 121 秒かかった。** SPEC の警告どおり一度目は「無い」と返る。
`availability` に現れた識別子は `scripts/sync/device_ids/philip.txt` と**完全一致**する。

**陰性対照**（同じ経路で存在しないファイルを問う）:

| 問い | HTTP |
|---|---|
| `file=probe-zzz-nonexistent.txt` | **404** |
| `file=probe-efros.txt` | **200** |

### E-3 中心から届いたもの

| 項目 | 開始時 | 現在 |
|---|---|---|
| `~/claude-sync/` の存在 | **無し** | 有り |
| 大きさ（`du -sb`） | **0 bytes** | **2859815 bytes** |
| ファイル件数 | **0** | **17**（`.stfolder` の中身を含む） |
| syncthing の索引（`localFiles`） | — | 16（`globalFiles` 16、`needBytes` **0**） |

五台が置いた試験用ファイルが届いた: `probe-andrew.txt` `probe-bengio.txt` `probe-ilya.txt` `probe-lecun.txt`（**4 件**）。
自分の `probe-efros.txt` を加えて 5 件である。

**記録の衝突が起きた。正常であり、両方残っている。**

    07:40:46 INF Synced file (file.name=sync-alerts.sync-conflict-20260917-074045-LW4CO4U.log ...)
    07:40:48 INF Synced file (file.name=sync-alerts.sync-conflict-20260917-074046-LW4CO4U.log ...)

本ホストの `m2-sync.sh` が中心の索引を受け取る前に `sync-alerts.log` へ書いたためである。
上書きではなく衝突ファイルが生まれた。**消していない。**

### E-4 repo の同期の進み方（**完了を待っていない**）

| 計測点 | 時刻 | 状態 | `localBytes` | `globalBytes` | `needBytes` | `needFiles` |
|---|---|---|---|---|---|---|
| 1 | 16:43:34 | `scanning` | 17654225337 | 46227262086 | 28573036749 | 51222 |
| 2 | 16:45:41 | `sync-preparing` | 44514451803 | 49228326381 | 5915279436 | 102484 |

**この増分は網を通って届いた量ではない。** 同じ区間で `du -sb ~/slocal2/m2` は
**68314486046 → 68314486880**（**834 bytes** 増）にとどまる。
`localBytes` の伸びは **走査が既存のファイルを索引へ入れている**分である。両者を混同しない。

`globalBytes` も伸びている（46.2 → 49.2 GB）。本ホストが持っていて中心が持っていないものを
申告しているためで、中心から見た `m2` の完了率は 67.39%（16:42）→ 28.83%（16:45）へ**下がった**。
**分母が増えているのであって、退行ではない。**

**repo の同期は完了していない。完了を待たずに記録する。**

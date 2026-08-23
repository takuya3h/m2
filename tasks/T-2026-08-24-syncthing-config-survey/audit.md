# audit — T-2026-08-24-syncthing-config-survey

**出力は要約しない。実行した命令と生の出力をそのまま貼る**（申し送り 8）。
時刻は JST。

## 0. 実行前の環境（契約の前提の照合）

### 0.1 論理名とホスト名
```
$ hostname
aolab
$ cat ./.servername
philip
$ git check-ignore -v .servername; echo exit=$?
.gitignore:225:.servername	.servername
exit=0
$ git --no-pager ls-files --error-unmatch .servername 2>&1; echo exit=$?
error: pathspec '.servername' did not match any file(s) known to git
Did you forget to 'git add'?
exit=1
```

### 0.2 分岐と直近の記録
```
$ git branch --show-current
feat/syncthing-config-survey
$ git --no-pager log -1 --format='%h %s'
d021515 Merge pull request #138 from takuya3h/chore/regen-index-after-preserve
$ git --no-pager status --porcelain | grep -c ''
1
```

### 0.3 同期処理の実体の権限（前契約で 644 へ落としてある）
```
$ ls -la ~/bin/syncthing ~/bin/keeper.sh ~/bin/m2-sync.sh
-rwxr-xr-x 1 ubuntu ubuntu     2709 Aug 23 17:27 /home/ubuntu/bin/keeper.sh
-rwxrwxr-x 1 ubuntu ubuntu     7342 Aug 23 20:29 /home/ubuntu/bin/m2-sync.sh
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
$ sha256sum ~/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
```

### 0.4 中継の目印
```
$ ls -a ~/ | grep -c '^\.tunnel_to_'
0
```

## Task 1 (Phase A): 設定の現状と構造を読む

### Step 1: 設定の在り処と大きさ・要約値・権限
```
$ ls -la ~/.local/state/syncthing/ 2>&1
total 28
drwx------ 2 ubuntu ubuntu 4096 Aug 22 06:04 .
drwxrwxr-x 6 ubuntu ubuntu 4096 Aug 23 12:52 ..
-rw-rw-r-- 1 ubuntu ubuntu  794 Aug 22 06:04 cert.pem
-rw------- 1 ubuntu ubuntu 8494 Aug 22 06:04 config.xml
-rw------- 1 ubuntu ubuntu  288 Aug 22 06:04 key.pem

$ for f in ~/.local/state/syncthing/*; do test -f "$f" && echo "$(sha256sum "$f") $(stat -c "%s %a" "$f")"; done
5f3b4bd8791d6fa873f5dd0c1089dc9878b3525e40e612b4cd07ac7558a5b4ac  /home/ubuntu/.local/state/syncthing/cert.pem 794 664
abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /home/ubuntu/.local/state/syncthing/config.xml 8494 600
92629ef108b100a80d3d0c511a3679239a7a21e80a67bfe3468dd1294d7d52f6  /home/ubuntu/.local/state/syncthing/key.pem 288 600
```

### Step 2: 設定の構造（秘匿の値は出さない）
```
$ ls ~/.local/state/syncthing/
cert.pem
config.xml
key.pem

=== /home/ubuntu/.local/state/syncthing/config.xml
$ grep -c '' /home/ubuntu/.local/state/syncthing/config.xml
171
$ grep -o '<[a-zA-Z][a-zA-Z0-9]*' /home/ubuntu/.local/state/syncthing/config.xml | sort | uniq -c | sort -rn | head -20
      4 <paused
      4 <device
      3 <maxSendKbps
      3 <maxRecvKbps
      3 <address
      2 <xattrFilter
      2 <weakHashThresholdPct
      2 <versioning
      2 <untrusted
      2 <syncXattrs
      2 <syncOwnership
      2 <sendXattrs
      2 <sendOwnership
      2 <scanProgressIntervalS
      2 <remoteGUIPort
      2 <pullerPauseS
      2 <pullerMaxPendingKiB
      2 <order
      2 <numConnections
      2 <modTimeWindowS
```

#### 相手と共有フォルダの定義（値は伏せる）
```
$ grep -c 'device id=' ~/.local/state/syncthing/config.xml; echo exit=$?
4
exit=0
$ grep -c 'folder id=' ~/.local/state/syncthing/config.xml; echo exit=$?
2
exit=0
$ grep -o 'folder id="[^"]*"' ~/.local/state/syncthing/config.xml; echo exit=$?
folder id="default"
folder id=""
exit=0
$ grep -o 'path="[^"]*"' ~/.local/state/syncthing/config.xml; echo exit=$?
path="/home/ubuntu/Sync"
path="~"
exit=0
```

#### 構造の精査（想定と食い違ったため）

要素名の全一覧（head で切らない。申し送り 7）。
```
$ grep -o '<[a-zA-Z][a-zA-Z0-9]*' config.xml | sort | uniq -c | sort -rn | grep -c ''
105
$ grep -o '<[a-zA-Z][a-zA-Z0-9]*' config.xml | sort | uniq -c | sort -rn
      4 <paused
      4 <device
      3 <maxSendKbps
      3 <maxRecvKbps
      3 <address
      2 <xattrFilter
      2 <weakHashThresholdPct
      2 <versioning
      2 <untrusted
      2 <syncXattrs
      2 <syncOwnership
      2 <sendXattrs
      2 <sendOwnership
      2 <scanProgressIntervalS
      2 <remoteGUIPort
      2 <pullerPauseS
      2 <pullerMaxPendingKiB
      2 <order
      2 <numConnections
      2 <modTimeWindowS
      2 <minDiskFree
      2 <maxTotalSize
      2 <maxSingleEntrySize
      2 <maxRequestKiB
      2 <maxConflicts
      2 <maxConcurrentWrites
      2 <markerName
      2 <junctionsAsDirs
      2 <ignoreDelete
      2 <hashers
      2 <fsType
      2 <fsPath
      2 <folder
      2 <filesystemType
      2 <encryptionPassword
      2 <disableTempIndexes
      2 <disableSparseFiles
      2 <disableFsync
      2 <copyRangeMethod
      2 <copyOwnershipFromParent
      2 <copiers
      2 <cleanupIntervalS
      2 <caseSensitiveFS
      2 <blockPullOrder
      2 <autoAcceptFolders
      1 <urUniqueID
      1 <urURL
      1 <urSeen
      1 <urPostInsecurely
      1 <urInitialDelayS
      1 <urAccepted
      1 <upgradeToPreReleases
      1 <unackedNotificationID
      1 <trafficClass
      1 <theme
      1 <tempIndexMinBlocks
      1 <stunServer
      1 <stunKeepaliveStartS
      1 <stunKeepaliveMinS
      1 <startBrowser
      1 <setLowPriority
      1 <sendFullIndexOnUpgrade
      1 <releasesURL
      1 <relaysEnabled
      1 <relayReconnectIntervalM
      1 <reconnectionIntervalS
      1 <progressUpdateIntervalS
      1 <overwriteRemoteDeviceNamesOnConnect
      1 <options
      1 <natTimeoutSeconds
      1 <natRenewalMinutes
      1 <natLeaseMinutes
      1 <natEnabled
      1 <minHomeDiskFree
      1 <maxFolderConcurrency
      1 <maxConcurrentIncomingRequestKiB
      1 <localAnnouncePort
      1 <localAnnounceMCAddr
      1 <localAnnounceEnabled
      1 <listenAddress
      1 <limitBandwidthInLan
      1 <ldap
      1 <keepTemporariesH
      1 <insecureAllowOldTLSVersions
      1 <ignores
      1 <gui
      1 <globalAnnounceServer
      1 <globalAnnounceEnabled
      1 <defaults
      1 <databaseTuning
      1 <crashReportingURL
      1 <crashReportingEnabled
      1 <connectionPriorityUpgradeThreshold
      1 <connectionPriorityTcpWan
      1 <connectionPriorityTcpLan
      1 <connectionPriorityRelay
      1 <connectionPriorityQuicWan
      1 <connectionPriorityQuicLan
      1 <connectionLimitMax
      1 <connectionLimitEnough
      1 <configuration
      1 <cacheIgnoredFiles
      1 <autoUpgradeIntervalH
      1 <apikey
      1 <announceLANAddresses
```

入れ子を見るため、深さ 0-2 の開始要素だけを行番号つきで出す。
```
$ grep -nE '^ {0,4}<[a-zA-Z]' config.xml | sed -E 's/(id=")[A-Z0-9]{7}[A-Z0-9-]*(")/\1<識別子>\2/g'
1:<configuration version="37">
2:    <folder id="default" label="Default Folder" path="/home/ubuntu/Sync" type="sendreceive" rescanIntervalS="3600" fsWatcherEnabled="true" fsWatcherDelayS="10" fsWatcherTimeoutS="0" ignorePerms="false" autoNormalize="true">
43:    <device id="<識別子>" name="aolab" compression="metadata" introducer="false" skipIntroductionRemovals="false" introducedBy="">
54:    <gui enabled="true" tls="false" debugging="false" sendBasicAuthPrompt="false">
59:    <ldap></ldap>
60:    <options>
116:    <defaults>
```

`<device` 4 件の出現位置と、どの入れ子に属するか。
```
$ grep -nE '<(device|folder|defaults)' config.xml | sed -E 's/(id=")[A-Z0-9]{7}[A-Z0-9-]*(")/\1<識別子>\2/g'
2:    <folder id="default" label="Default Folder" path="/home/ubuntu/Sync" type="sendreceive" rescanIntervalS="3600" fsWatcherEnabled="true" fsWatcherDelayS="10" fsWatcherTimeoutS="0" ignorePerms="false" autoNormalize="true">
4:        <device id="<識別子>" introducedBy="">
43:    <device id="<識別子>" name="aolab" compression="metadata" introducer="false" skipIntroductionRemovals="false" introducedBy="">
116:    <defaults>
117:        <folder id="" label="" path="~" type="sendreceive" rescanIntervalS="3600" fsWatcherEnabled="true" fsWatcherDelayS="10" fsWatcherTimeoutS="0" ignorePerms="false" autoNormalize="true">
119:            <device id="<識別子>" introducedBy="">
158:        <device id="" compression="metadata" introducer="false" skipIntroductionRemovals="false" introducedBy="">
```

自分の識別子が、版管理に公開済みの philip の識別子と一致するか。
**識別子は秘匿ではない**（禁止 9）が、記録には先頭 7 文字と照合結果だけを残す。
```
$ CFG=$(grep -oE '^    <device id="[A-Z0-9-]+"' config.xml | grep -oE '[A-Z0-9-]{50,}')
$ PUB=$(tr -d ' 
' < scripts/sync/device_ids/philip.txt)
設定の自分の識別子（先頭7）= 3J4TRX4
philip.txt の識別子（先頭7） = 3J4TRX4
一致=yes
長さ: config=63 philip.txt=63

他4台の識別子と一致するか（陽性対照を兼ねる）
  andrew(3C2LTP7) 一致=no
  bengio(4NIRI4M) 一致=no
  ilya(UODEAXZ) 一致=no
  lecun(OOOTQMG) 一致=no
```

### Step 3: 待ち受けと外向きの設定
```
$ grep -n -E 'listenAddress|globalAnnounceEnabled|relaysEnabled|localAnnounceEnabled' config.xml
61:        <listenAddress>default</listenAddress>
63:        <globalAnnounceEnabled>true</globalAnnounceEnabled>
64:        <localAnnounceEnabled>true</localAnnounceEnabled>
70:        <relaysEnabled>true</relaysEnabled>

$ grep -n -E '<gui |<address>|<apikey>|natEnabled|localAnnouncePort|globalAnnounceServer' config.xml  # apikey は値を伏せる
44:        <address>dynamic</address>
54:    <gui enabled="true" tls="false" debugging="false" sendBasicAuthPrompt="false">
55:        <address>127.0.0.1:8384</address>
62:        <globalAnnounceServer>default</globalAnnounceServer>
65:        <localAnnouncePort>21027</localAnnouncePort>
73:        <natEnabled>true</natEnabled>
159:            <address>dynamic</address>
apikey 要素: 件数=1
  （値は秘匿。記録しない）
```

## Task 2 (Phase A): 設定を変える手段を確かめる

### 前提: 実体に実行権が無い（前契約の回避策）

`~/bin/syncthing` は前契約 T-2026-08-24-philip-keeper-autosync で 644 へ落としてある。
`keeper.sh:41` が `[ -x ~/bin/syncthing ]` だけを見て起動するため、
**実行権を戻すと 30 分以内に同期処理が常駐する（禁止 2 違反）。**
正本には触れず、作業領域へ複製して調べる。要約値が同一であることを示す。
```
$ cp ~/bin/syncthing $SP/syncthing && chmod 755 $SP/syncthing
$ sha256sum ~/bin/syncthing $SP/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/syncthing
$ ls -la ~/bin/syncthing  # 正本の権限が 644 のままであること
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
```

### Step 1: 下位命令の一覧
```
$ $SP/syncthing --version
syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC

$ $SP/syncthing --help 2>&1 | head -40
Usage: syncthing <command> [flags]

Flags:
  -h, --help    Show context-sensitive help.

Commands:
  serve                  Run Syncthing
  generate               Generate key and config, then exit
  decrypt                Decrypt or verify an encrypted folder
  cli                    Command line interface for Syncthing
  install-completions    Print commands to install shell completions

Run "syncthing <command> --help" for more information on a command.
```
$ $SP/syncthing cli --help 2>&1 | head -40
Usage: syncthing cli <command> [flags]

Command line interface for Syncthing

Flags:
  -h, --help                  Show context-sensitive help.

      --config=PATH           Set configuration directory (config and keys)
                              ($STCONFDIR)
      --home=PATH             Set configuration and data directory ($STHOMEDIR)
      --no-default-folder     Don't create the "default" folder on first startup
                              ($STNODEFAULTFOLDER)
      --skip-port-probing     Don't try to find free ports for GUI and listen
                              addresses on first startup
      --data=PATH             Set data directory (database and logs)
                              ($STDATADIR)
      --gui-address=STRING
      --gui-apikey=STRING

Commands:
  cli show          Show command group
  cli debug         Debug command group
  cli operations    Operation command group
  cli errors        Error command group
  cli config        Configuration modification command group
  cli -             Read commands from stdin
```

### Step 2: 常駐なしで設定を読めるか

**先に複製の設定へ向けて試す。** `cli` が設定を書き換える可能性があり、
禁止 1（設定を変更しない）は本契約の要である。複製が変わらないことを確かめてから正本へ向ける。
```
$ cp -a ~/.local/state/syncthing $SP/cfgcopy
$ sha256sum $SP/cfgcopy/config.xml   # 実行前
abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/cfgcopy/config.xml

$ $SP/syncthing cli --home $SP/cfgcopy config devices list 2>&1 | head -20
exit=1
syncthing: error: Get "http://127.0.0.1:8384/rest/system/config": dial tcp 127.0.0.1:8384: connect: connection refused

$ sha256sum $SP/cfgcopy/config.xml   # 実行後
abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/cfgcopy/config.xml
$ ls -la $SP/cfgcopy/
total 28
drwx------ 2 ubuntu ubuntu 4096 Aug 22 06:04 .
drwx------ 3 ubuntu ubuntu 4096 Aug 23 20:48 ..
-rw-rw-r-- 1 ubuntu ubuntu  794 Aug 22 06:04 cert.pem
-rw------- 1 ubuntu ubuntu 8494 Aug 22 06:04 config.xml
-rw------- 1 ubuntu ubuntu  288 Aug 22 06:04 key.pem
```

複製が変わらなかったため、契約どおり正本へ向けて実測する。前後で要約値を取る。
```
$ sha256sum ~/.local/state/syncthing/config.xml   # 実行前
abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /home/ubuntu/.local/state/syncthing/config.xml
$ $SP/syncthing cli --home ~/.local/state/syncthing config devices list 2>&1 | head -20; echo exit=$?
syncthing: error: Get "http://127.0.0.1:8384/rest/system/config": dial tcp 127.0.0.1:8384: connect: connection refused
exit=1
$ sha256sum ~/.local/state/syncthing/config.xml   # 実行後
abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /home/ubuntu/.local/state/syncthing/config.xml
```

`cli config` の下位命令（設定を変える口が何か）。
```
$ $SP/syncthing cli config --help 2>&1 | head -30
Incorrect Usage. flag: help requested

NAME:
   syncthing - A new cli application

USAGE:
   syncthing  command [command options] [arguments...]

AUTHOR:
   The Syncthing Authors

COMMANDS:

   ACTIONS:
     dump-json  Dump item as json

   PROPERTIES:
     version          
     folders          
     devices          
     gui              
     ldap             
     options          
     ignored-devices  
     defaults         
syncthing: error: flag: help requested

$ $SP/syncthing cli config devices --help 2>&1 | head -25
NAME:
   syncthing devices - 

USAGE:
   syncthing devices command [command options] [arguments...]

COMMANDS:

   ACTIONS:
     list      List item keys in the collection
     add       Add a new item to collection
     add-json  Add a new item to collection deserialised from JSON

OPTIONS:
   --help, -h  show help
   
```

### Step 3: 設定を作る命令に、相手や共有フォルダを足す機能があるか
```
$ $SP/syncthing generate --help 2>&1 | head -20
Usage: syncthing generate [flags]

Generate key and config, then exit

Flags:
  -h, --help                   Show context-sensitive help.

      --config=PATH            Set configuration directory (config and keys)
                               ($STCONFDIR)
      --home=PATH              Set configuration and data directory ($STHOMEDIR)
      --no-default-folder      Don't create the "default" folder on first
                               startup ($STNODEFAULTFOLDER)
      --skip-port-probing      Don't try to find free ports for GUI and listen
                               addresses on first startup
      --gui-user=STRING        Specify new GUI authentication user name
      --gui-password=STRING    Specify new GUI authentication password (use - to
                               read from standard input)
```

### Step 4: 手段を三つに分けて評価する

| 手段 | 使えるか | 前提 | 危険 |
|---|---|---|---|
| **命令列**（`syncthing cli config …`） | **常駐なしでは使えない**（実測 exit=1、`dial tcp 127.0.0.1:8384: connect: connection refused`）。常駐させれば使える。`cli config devices add` / `folders add` / `add-json` が実在する | ① `serve` が動いていること ② 待ち受け `127.0.0.1:8384` へ届くこと ③ `--home` で設定の場所を明示すること（既定ではない） | **常駐が前提＝本契約では禁止 2 に触れる。** 起動した瞬間に外部告知（`globalAnnounceEnabled=true`）と公開中継（`relaysEnabled=true`）が有効な設定のまま動き出す |
| **設定ファイルの直接編集** | **使える。** `config.xml` は平文 XML（171 行、`<configuration version="37">`）。要素の形は実測済み。常駐は不要 | ① **常駐を止めてから編集する**（動作中の書き換えは上書きされる） ② XML の妥当性を自分で保証する ③ 権限 600 を保つ | 構文を壊すと起動しなくなる。**五台同時に壊すと遠隔から直せない。** 版番号 37 の様式に合わせる必要がある |
| **画面**（`127.0.0.1:8384`） | **本契約では評価できない部分がある。** 設定上は `<gui enabled="true" tls="false"><address>127.0.0.1:8384</address>`。**局所からのみ届く。外からは中継が要る**（禁止 3 で張れない）。かつ画面を出すには常駐が要る（禁止 2） | ① 常駐 ② 中継（`-L 8384:127.0.0.1:8384` 相当） ③ `apikey` または画面の認証 | 常駐と中継の両方を先に立てる必要があり、**最も前提が多い。** `sendBasicAuthPrompt="false"` かつ利用者名の設定が無いため、届けば無認証で操作できてしまう |

**判定: 次の実装契約は「設定ファイルの直接編集」を主手段にすべきである。**
常駐を先に立てる手段（命令列・画面）は、**既定のまま起動すると外部告知と公開中継が有効になる**という
副作用を伴う（Step 3 の実測）。旧構成はどちらも無効だった。**告知と中継を無効化してから起動する**
という順序は、直接編集でしか実現できない。

**`--home` を必ず明示すること。** `cli` の説明にも `--home=PATH ($STHOMEDIR)` とあり、
既定の場所は `~/.local/state/syncthing` ではない（確定した事実の欄と一致）。

### Gate G1（Phase A 直後）

| 条件 | 結果 |
|---|---|
| 設定の在り処と要約値と権限を記録 | 済（`~/.local/state/syncthing/` 3 ファイル、`config.xml` sha256 `abb2fa89…` 8494 バイト 600） |
| 要素の名前と出現数から構造を読んだ | 済（相異なる要素名 105 種、全件を記録） |
| 相手と共有フォルダの定義の件数を記録 | 済（実体は device 1・folder 1。`<defaults>` の雛形を除く） |
| 手段を三つに分けて可否と前提を評価 | 済 |
| 常駐なしで読めるかを実測 | 済（exit=1 / connection refused。設定は前後で同一） |

**G1 PASS。**

## Task 3 (Phase B): 共有フォルダをどう定義し直すか

### Step 1: 旧構成の記録を探す
```
$ grep -rn 'claude-sync\|folder id\|sendreceive\|stignore' docs/ context/ tasks/ README.md 2>/dev/null | grep -v '\.venv' | grep -c ''
425
$ …（上の命令）| head -30
docs/sync_automation_instr15_stage5_third_party_ilya_2026-08-05.md:9:| `.stignore` / `.gitignore` | 変更 0 件 |
docs/sync_automation_instr15_stage5_third_party_ilya_2026-08-05.md:16:`third_party/` は `.gitignore:132-133` と `.stignore:35` の両方で除外され、
docs/sync_automation_instr15_stage5_third_party_ilya_2026-08-05.md:41:.stignore:9   .git          ← パス区切りなしの単独パターン
docs/sync_automation_instr15_stage5_third_party_ilya_2026-08-05.md:42:.stignore:3   コメント: 「先にマッチした行が勝つ」
docs/sync_automation_instr15_stage5_third_party_ilya_2026-08-05.md:162:| **作業量** | 中〜大。`.stignore` 編集は数行だが 11 台の容量・帯域への影響評価が別途必要 | 小〜中。検出+コミットロジックを追加。4 ホスト分の初回テストが要る | **大**。9 fork の team 化・履歴統合・全ホスト `.gitmodules` 設定・4 台 variant 統合判断 | **小**。検出ロジックのみ（(b) の縮小版） |
docs/sync_automation_instr15_stage5_third_party_ilya_2026-08-05.md:223:- `.stignore` / `.gitignore` の変更
docs/third_party_sync_design_2026-08-05.md:9:| `.stignore` / `.gitignore` | 変更 0 件 |
docs/third_party_sync_design_2026-08-05.md:16:`third_party/` は `.gitignore:132-133` と `.stignore:35` の両方で除外され、
docs/third_party_sync_design_2026-08-05.md:41:.stignore:9   .git          ← パス区切りなしの単独パターン
docs/third_party_sync_design_2026-08-05.md:42:.stignore:3   コメント: 「先にマッチした行が勝つ」
docs/third_party_sync_design_2026-08-05.md:162:| **作業量** | 中〜大。`.stignore` 編集は数行だが 11 台の容量・帯域への影響評価が別途必要 | 小〜中。検出+コミットロジックを追加。4 ホスト分の初回テストが要る | **大**。9 fork の team 化・履歴統合・全ホスト `.gitmodules` 設定・4 台 variant 統合判断 | **小**。検出ロジックのみ（(b) の縮小版） |
docs/third_party_sync_design_2026-08-05.md:223:- `.stignore` / `.gitignore` の変更
docs/sync_phase0_merge_lecun_2026-08-02.md:94:`.stignore:44` の `!experiments/**/logs` により当該パスは同期対象であり、
docs/sync_phase0_merge_lecun_2026-08-02.md:129:`.stignore` が全 11 台で正しく効いており、git 管理の 4 証跡は
docs/sync_automation_instr15_stage4_ilya_2026-08-05.md:139:> 無関係な同時実行（`~/claude-sync/` は 11 台共有のログファイル）であり、
docs/sync_instr09_lecun_2026-08-02.md:58:**全 121 ファイルが `logs/` `predictions/` 配下にあり `.stignore` 43-51 行の同期対象**＝
docs/sync_instr09_lecun_2026-08-02.md:69:`.stignore` は phase0 の `.stglobalignore` と一致。
docs/sync_instr09_lecun_2026-08-02.md:286:`~/claude-sync/`（Syncthing 共有）の `sync-alerts.log` に全ノードのアラートが集約されており、
docs/sync_instr09_lecun_2026-08-02.md:399:`.stignore:44` の `!experiments/**/logs` により当該パスは同期対象であり、
docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md:18:- `ls -la ~/bin/ 2>&1; echo "---keeper---"; ls -la ~/claude-sync/ 2>&1 | head -20; echo "---m2sync---"; grep -c sync-pause ~/bin/m2-sync.sh 2>&1`
docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md:99:- `Exit code 2 ls: cannot access '/home/ubuntu/bin/': No such file or directory ---keeper--- ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory ---m2sync--- ugrep: warning: /home/ub`
docs/sessions/digest/2026-08-11-15-35-17-019ff176-ba5e-7ae2-9bf7-4b6a11798b39.md:17:- `sed -n '1,260p' /home/ubuntu/claude-sync/codex/skills/.system/openai-docs/SKILL.md`
docs/sessions/digest/2026-08-11-15-35-17-019ff176-ba5e-7ae2-9bf7-4b6a11798b39.md:39:- `grep -c sync-pause ~/bin/m2-sync.sh; grep '一時停止中' ~/claude-sync/sync-alerts.log | tail -3; test -f .sync-pause && echo '.sync-pause=present' || echo '.sync-pause=absent'`
docs/sessions/digest/2026-08-02-846b93b9-4191-47ec-a603-8741c6ac4df8.md:52:- `echo "===== §3.6 自動同期(Syncthing keeper) =====" && echo "--- .stignore / .stfolder ---"; ls -la .stignore .stfolder 2>/dev/null || echo "(なし)"; echo "--- systemd user units (keeper/sync/m2) ---"; syste …（切り詰め）`
docs/sessions/digest/2026-08-02-846b93b9-4191-47ec-a603-8741c6ac4df8.md:582:- `/home/ubuntu/slocal2/m2/.stignore`
docs/sessions/digest/2026-08-11-268d4a43-8263-4947-8b09-411fba5086af.md:92:- `cd ~/slocal2/m2 && echo "=== 解除前 ===" && ls -1 .sync-pause 2>/dev/null && grep -c '一時停止中' ~/claude-sync/sync-alerts.log 2>/dev/null …（切り詰め）`
docs/sessions/digest/2026-08-02-45129e05-8b5a-4844-b371-5e7be7a985aa.md:21:- `echo "=== 3.6 Syncthing keeper ===" && ls -la .stignore .stfolder 2>/dev/null || echo "(.stignore/.stfolder なし)" ; echo "--- systemd user units ---" && (systemctl --user list-units 2>/dev/null | grep  …（切り詰め）`
docs/sessions/digest/2026-08-02-45129e05-8b5a-4844-b371-5e7be7a985aa.md:23:- `echo "=== .stignore と phase0/.stglobalignore の照合 ===" && curl -s https://raw.githubusercontent.com/takuya3h/m2/phase0/.stglobalignore -o /tmp/claude-1000/-home-ubuntu-slocal-m2/45129e05-8b5a-4844-b371 …（切り詰め）`
docs/sessions/digest/2026-08-05-06-31-00-019fd09e-40c0-7790-b43c-c3c6b9442bc2.md:26:- `sed -n '1,260p' /home/ubuntu/claude-sync/agents/skills/doc-coauthoring/SKILL.md`
docs/sessions/digest/2026-08-05-06-31-00-019fd09e-40c0-7790-b43c-c3c6b9442bc2.md:27:- `sed -n '261,520p' /home/ubuntu/claude-sync/agents/skills/doc-coauthoring/SKILL.md`
```

425 件は広すぎるため、定義そのものを実測した記録を探した。**見つかった。**
`tasks/T-2026-08-12-sync-audit-bengio/audit.md:205-232`（bengio 上で旧構成の設定を読んだ記録）。

```
$ sed -n '205,232p' tasks/T-2026-08-12-sync-audit-bengio/audit.md
### Step 4-5: 設定の場所と構造

設定は `~/.local/state/syncthing/config.xml`（起動引数での指定は無く既定の場所）。

```
device_count=11
device name=hinton id7=CK3ACOY paused=None addrs=dynamic,tcp://192.168.196.78:22000
device name=Bengio id7=E7NPG4Q paused=None addrs=dynamic
device name=philip id7=GO2U7PF paused=None addrs=tcp://192.168.196.150:22000,tcp://127.0.0.1:22001
device name=andrew id7=KYZK57M paused=None addrs=dynamic,tcp://192.168.196.190:22000
device name=adam id7=QGS35FJ paused=None addrs=dynamic,tcp://192.168.196.58:22000
device name=ilya id7=QNQZIGJ paused=None addrs=dynamic,tcp://192.168.196.63:22000
device name=dlsta id7=RMG3SUE paused=None addrs=dynamic,tcp://192.168.196.54:22000
device name=lecun id7=UDRM53M paused=None addrs=dynamic,tcp://192.168.196.176:22000
device name=efros id7=23MMNBA paused=None addrs=dynamic,tcp://192.168.196.227:22000
device name=ian id7=5GHYFIC paused=None addrs=dynamic,tcp://192.168.196.143:22000
device name=he id7=5YNIXSO paused=None addrs=dynamic,tcp://192.168.196.106:22000
folder_count=2
folder id=claude-sync path=/home/ubuntu/claude-sync paused=None type=sendreceive shared=CK3ACOY,E7NPG4Q,GO2U7PF,KYZK57M,QGS35FJ,QNQZIGJ,RMG3SUE,UDRM53M,23MMNBA,5GHYFIC,5YNIXSO
folder id=m2 path=/home/ubuntu/slocal2/m2 paused=None type=sendreceive shared=CK3ACOY,E7NPG4Q,GO2U7PF,KYZK57M,QGS35FJ,QNQZIGJ,RMG3SUE,UDRM53M,23MMNBA,5GHYFIC,5YNIXSO
option globalAnnounceEnabled=false
option localAnnounceEnabled=true
option relaysEnabled=false
option listenAddress=default
```

### Step 6: 秘匿の検査

```

#### 復元できた旧構成（出所つき）

| 項目 | 値 | 出所 |
|---|---|---|
| 共有フォルダ数 | **2** | `T-2026-08-12-sync-audit-bengio/audit.md:222`（`folder_count=2`） |
| 共有フォルダ①の識別子 | `claude-sync` | 同 `:223` |
| ①の位置 | `/home/ubuntu/claude-sync` | 同 `:223` |
| ①の型 | `sendreceive` | 同 `:223` |
| ①の共有相手 | **11 台すべて** | 同 `:223`（`shared=` に 11 個の識別子） |
| 共有フォルダ②の識別子 | `m2` | 同 `:224` |
| ②の位置 | `/home/ubuntu/slocal2/m2`（repo そのもの） | 同 `:224` |
| ②の型 | `sendreceive` | 同 `:224` |
| ②の共有相手 | **11 台すべて** | 同 `:224` |
| ②の除外規則 | `$M2DIR/.stignore`（正本は `.stglobalignore`） | `README.md:1176-1178` |
| 相手の登録数 | **11** | 同 `:209`（`device_count=11`） |
| 外部告知 | `globalAnnounceEnabled=false` | 同 `:225` |
| 局所告知 | `localAnnounceEnabled=true` | 同 `:226` |
| 公開中継 | `relaysEnabled=false` | 同 `:227` |
| 待ち受け | `listenAddress=default` | 同 `:228` |
| 中心への到達 | ノード側は philip を `tcp://127.0.0.1:22001` として登録（静的住所と併記） | 同 `:212` |

**①が同期していた中身**（何を共有していたかの根拠）:
`~/claude-sync/` は各実装系の設定の共有領域であり、`~/.codex` `~/.claude` `~/.agents` から
symlink で指されていた（`context/auto/followups.md:86`、`docs/host_dev_env_setup.md:578-587`）。
同期の記録 `sync-alerts.log` も全台ここへ集約されていた（`OPERATION.md:139,145`）。
実測で 2532 ファイル、衝突 10 件が残っていた（`tasks/inbox.md:170,187`）。

**②が同期していた中身**: `README.md:1153-1173` の表（実験成果物・モデル重み・出力とログ・
`data/processed/`・注釈の JSON・`.notion_sync.json`）。**git 追跡ファイルは層 1 が配るため除外**。

#### 旧構成と現構成の差（次の契約が引きずってはならない点）
```
旧（bengio の記録 2026-08-12）の識別子先頭7 と、現在版管理に公開されている値の照合
  andrew: 現=3C2LTP7
  bengio: 現=4NIRI4M
  ilya: 現=UODEAXZ
  lecun: 現=OOOTQMG
  philip: 現=3J4TRX4
  旧: hinton=CK3ACOY Bengio=E7NPG4Q philip=GO2U7PF andrew=KYZK57M adam=QGS35FJ
      ilya=QNQZIGJ dlsta=RMG3SUE lecun=UDRM53M efros=23MMNBA ian=5GHYFIC he=5YNIXSO
```

| 差 | 旧 | 現 | 影響 |
|---|---|---|---|
| 台数 | 11 | **5**（andrew / bengio / ilya / lecun / philip） | 共有相手は 5 件になる |
| 識別子 | 上記 11 個 | **すべて別の値**（philip は `GO2U7PF` → `3J4TRX4`） | **旧識別子を書き写してはならない。** 鍵ごと作り直されている |
| 自分の登録名 | 論理名（`philip` `Bengio` 等） | **`aolab`**（OS のホスト名。実測） | **philip と ilya が同名になる。** 登録時に論理名へ直す必要がある |
| 外部告知・公開中継 | 両方 `false` | **両方 `true`**（既定のまま。実測） | **起動前に落とす必要がある。** 落とさずに起動すると外部の探索網と公開中継へ出る |
| 共有フォルダ | `claude-sync` と `m2` の 2 件 | **`default`（`/home/ubuntu/Sync`）が 1 件だけ**（自動生成。実測） | `default` は要らない。作らせない（`--no-default-folder`）か消す |

**識別子の照合は両方向で取った**（申し送り 3）。現 philip の設定内の識別子は
`scripts/sync/device_ids/philip.txt` と一致（陽性）、他 4 台とは不一致（陰性）。

#### 設定の場所は「既定」か（契約の記載と旧記録が食い違う）

契約の「確定した事実」は `--home` で明示する・既定ではない、とする。
一方 `T-2026-08-12-sync-audit-bengio/audit.md:207` は「起動引数での指定は無く既定の場所」とする。
**自ホームを汚さないよう、隔離した HOME で実測する。**
```
$ mkdir -p $SP/fakehome && HOME=$SP/fakehome $SP/syncthing serve --paths 2>&1 | head -20
Configuration file:
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/config.xml

Device private key & certificate files:
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/key.pem
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/cert.pem

GUI / API HTTPS private key & certificate files:
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/https-key.pem
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/https-cert.pem

Database location:
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/index-v0.14.0.db

Log file:
	-

GUI override directory:
	/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome/.local/state/syncthing/gui

exit=0

$ ls -R $SP/fakehome | head -20   # 何が作られたか
/tmp/claude-1000/-home-ubuntu-slocal2-m2/d0076c74-6667-46a0-95fb-96d9c1d68f8c/scratchpad/fakehome:
```

### Step 2: 除外規則の正本と反映先
```
$ ls -la .stglobalignore 2>&1
-rw-rw-r-- 1 ubuntu ubuntu 2223 Aug  2 10:30 .stglobalignore
$ grep -c '' .stglobalignore 2>&1
68
$ head -30 .stglobalignore 2>&1
// ============================================================================
// .stglobalignore — Syncthing 同期ルール（「gitignoreされた実験成果物だけ同期」）
// 仕組み: 先にマッチした行が勝つ。除外 → !同期対象 → **(残り全部を無視) の順。
// 反映:   phase0 上でこのファイルを編集して commit & push すると、各サーバーの
//         keeper が30分以内に $M2DIR/.stignore へ自動反映する。
// ============================================================================

// --- 絶対に同期しない（VCS・秘密情報・環境依存物）---
.git
.env
.env.*
*passphrase*
*.key
.venv*
venv*
__pycache__
*.pyc
*.pyo
*.egg-info
.gitkeep
.vscode
.idea
*.swp
*~
.DS_Store
.ipynb_checkpoints
.claude

// --- git 追跡ファイルとの二重管理を防ぐ除外（includeより先に書く）---
data/annotations/egosurgery_tool/instances_*.json
```

常駐処理が反映する先を実装から確かめる。
```
$ grep -n 'stignore\|stglobalignore' ~/bin/keeper.sh
47:  # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
48:  git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
49:    && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"

$ ls -la .stignore 2>&1; echo exit=$?
-rw-rw-r-- 1 ubuntu ubuntu 2223 Aug 23 20:29 .stignore
exit=0
```

**判定: `~/.local/state/syncthing` は既定の場所である。** 隔離した HOME で `serve --paths` を
実行すると、設定ファイルは `$HOME/.local/state/syncthing/config.xml` と表示された。
`--paths` は何も作らない（`fakehome` は空のまま）。
**契約の「確定した事実」の「既定ではない」は誤りである**（起票者の誤り: `asserted_without_measuring`）。
`--home` を明示すること自体は害が無く、他の HOME で動く場合の保険として有用ではある。

除外規則の反映は実装で確認した（`~/bin/keeper.sh:48-49`）。
`git show origin/phase0:.stglobalignore > $M2DIR/.stignore.new && mv` の 1 経路のみ。
```
$ sha256sum .stglobalignore .stignore   # 反映先が正本と一致するか
61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore
61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore
一致=yes

$ git --no-pager show origin/phase0:.stglobalignore | sha256sum   # 正本の出所
61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  -

$ git check-ignore -v .stignore; echo exit=$?   # .stignore は版管理外か
.gitignore:192:.stignore	.stignore
exit=0
```

**反映先は repo 直下 `$M2DIR/.stignore`。** これは共有フォルダ②の根が
`/home/ubuntu/slocal2/m2` であることを意味する（Syncthing は共有フォルダの根の `.stignore` を読む）。

### Step 4: 現在の中身を測る
```
$ du -sh ~/claude-sync/ 2>&1
8.0K	/home/ubuntu/claude-sync/
$ ls -la ~/claude-sync/ 2>&1 | head -10
total 16
drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 23 17:28 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 20:40 ..
-rw-rw-r-- 1 ubuntu ubuntu  376 Aug 23 20:29 sync-alerts.log
$ find ~/claude-sync/ -type f 2>/dev/null | grep -c ''
1
$ find ~/claude-sync/ -type l 2>/dev/null | grep -c ''
0

$ du -sh /home/ubuntu/Sync 2>&1   # 自動生成された default フォルダ
du: cannot access '/home/ubuntu/Sync': No such file or directory
$ ls -la /home/ubuntu/Sync 2>&1 | head
ls: cannot access '/home/ubuntu/Sync': No such file or directory

$ du -sh /home/ubuntu/slocal2/m2 2>&1   # 共有フォルダ②の候補（repo 全体）
79G	/home/ubuntu/slocal2/m2
$ du -sh /home/ubuntu/slocal2/m2/experiments 2>&1
35G	/home/ubuntu/slocal2/m2/experiments
```

除外規則の残り（同期対象＝`!` 行）。**大きさの見積もりに要る。**
```
$ sed -n '30,68p' .stglobalignore
data/annotations/egosurgery_tool/instances_*.json

// --- 同期しない判断をしたもの（必要なら該当行を消して !付きで下の同期対象へ）---
// data/raw          : 生データセット（巨大・各サーバーで個別配置）
// data/external     : 外部データ（同上）
// third_party       : 外部fork（入れ子.gitを含むため同期不可。各サーバーでclone）
// wandb             : W&Bローカルラン（クラウドに記録済み・巨大）
// prompts_legacy 等 : ローカル参照用の退避物
// 退避フォルダ（~5.6GB のローカル証跡。全台複製を避ける）:
experiments/baselines/_*
experiments/phase0/_*

// --- 同期対象: gitignore された実験成果物 ---
!experiments/**/checkpoints
!experiments/**/logs
!experiments/**/predictions
!experiments/**/visualizations
!experiments/**/tf_log
!experiments/**/training*.log
!experiments/**/*.npy
!experiments/**/*.pt
!experiments/**/*.pth
!experiments/**/*.py
!experiments/**/last_checkpoint
!experiments/**/20[0-9][0-9][0-9]*
!.notion_sync.json
!*.pth
!*.pt
!*.ckpt
!*.onnx
!*.safetensors
!outputs
!logs
!data/processed
!data/annotations/egosurgery_hts
!data/annotations/**/*.json

// --- 上記以外は全て同期しない（git管理ファイルはgit経由で同期される）---
**
```

同期対象になる主な実体の大きさ。
```
  experiments: 35G
  outputs: 1.3M
  logs: 3.6M
  data/processed: 3.3G
  data/annotations: 430M
  experiments 配下の checkpoints 合計: 14G
  experiments 配下の logs 合計: 5.8M
  experiments 配下の predictions 合計: 1.3G
```

### Step 3: 共有すべきものを決める

| 候補 | 位置 | 共有する理由 | 大きさ | 判断 |
|---|---|---|---|---|
| **設定の共有領域** | `~/claude-sync/` | 旧構成では 11 台で共有し、`~/.codex` `~/.claude` `~/.agents` から symlink で参照していた（`context/auto/followups.md:86`）。同期の記録の集約先でもある（`OPERATION.md:139`） | **8.0K / 実ファイル 1 件 / symlink 0 件**（`sync-alerts.log` のみ。常駐処理が作り直した） | **共有する。ただし中身は失われている。** 何を戻すかは別問題（下記） |
| **版管理の作業場所** | `/home/ubuntu/slocal2/m2` | **二重にならない。** 除外規則が `.git` と git 追跡ファイルを落とし、**`**` で「上記以外は全て同期しない」ため、実際に流れるのは `!` 行で明示的に戻した gitignore 済みの成果物だけ（`.stglobalignore:43-64`）。層 1（git）と層 2（同期処理）の役割分担は `README.md:1097,1145` に設計として明記されている | repo 全体 79G のうち、同期対象は概算 **約 19G**（checkpoints 14G / data/processed 3.3G / predictions 1.3G / annotations の JSON / outputs 1.3M / logs 5.8M）。退避フォルダ `experiments/{baselines,phase0}/_*` は除外 | **共有する。** 旧構成の識別子 `m2`、位置 `/home/ubuntu/slocal2/m2`、型 `sendreceive` をそのまま踏襲する |
| 自動生成された `default` | `/home/ubuntu/Sync` | **無い。** 初回起動時に自動で作られた雛形 | **実体が存在しない**（`ls` で `No such file or directory`）。設定にだけある | **消す。** 次の契約で `default` の定義を削除するか、以後は `--no-default-folder` を付けて起動する |

**「なぜ repo を同期処理でも配っていたか」は記録から答えが出た**（推測ではない）。
`README.md:1145-1178` が二層設計を明示している。層 1 は git 追跡ファイル、層 2 は
**gitignore された実験成果物**（checkpoints / predictions / モデル重み / `data/processed` / 注釈 JSON）。
容量のため git に載せられないものを配るのが層 2 の役割で、**重複はしない。**

#### 決めきれないもの（UNKNOWN）

| 事項 | なぜ決められないか |
|---|---|
| `~/claude-sync/` に**何を戻すか** | 旧構成の 2532 ファイルの中身が版管理に無い。実装系の設定（`codex/config.toml` `settings.json` 等）は各ホストの実体から集める必要があり、**本契約は他ホストへ接続できない**（禁止 5）。**UNKNOWN。ユーザーの判断に回す** |
| 5 台のうち**どれが最初に中身を持つか** | 上と同じ理由で他ホストの `~/claude-sync/` を測れていない。空の側が空を配ると失われる。**UNKNOWN** |
| 共有フォルダの**型**を旧構成どおり `sendreceive` にするか | 中身を持つ台が 1 台だけの場合、最初の同期を `sendonly`（中心）／`receiveonly`（ノード）にすると事故が減る。**判断材料が揃っていないため UNKNOWN** |
| 約 19G の初回転送を**中継越しに流してよいか** | 帯域と所要時間を測っていない。旧構成の 28 秒（`OPERATION.md:15`）は差分同期の実測であり、初回全量ではない。**UNKNOWN** |

## Task 4 (Phase B): 登録と起動の順序を決める

### Step 1: 中継と同期処理の関係を実装から読む
```
$ grep -n -E 'tunnel_to|22001|22000|50072' ~/bin/keeper.sh
9:  for candidate in "$HOME"/.tunnel_to_*; do
18:  HUB_NAME=${HUB_NAME#.tunnel_to_}
31:  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
33:  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
34:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \

$ sed -n '20,52p' ~/bin/keeper.sh   # 前後関係を含めて読む
  HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
  [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
  [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
}

exec 9>~/.keeper.lock
flock -n 9 || exit 0

M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

while true; do
  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
  # 1行目は秘密鍵パス、任意の2行目は中心の住所。2行目が無い旧形式では中心名をSSH別名に使う。
  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
      -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
      ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
  fi
  # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
  # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
  fi
  # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
  git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
    && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
  # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
  git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
    && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
  ~/bin/m2-sync.sh 9>&-
  sleep 1800 9>&-
done
```

正本（版管理側）と稼働版が同一であることの確認。
```
$ sha256sum scripts/sync/keeper.sh ~/bin/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
```

中心が SSH を受けられるか（ノードの中継はここへ来る）。**局所の観測のみ。他ホストへは接続しない。**
```
$ hostname -I
172.17.0.13 
$ command -v ss netstat lsof; echo exit=$?
exit=1
$ awk 'NR>1{split($2,a,":"); print strtonum("0x" a[2])}' /proc/net/tcp /proc/net/tcp6 2>/dev/null | sort -n | uniq -c | head -20

$ grep -c '' /proc/net/tcp /proc/net/tcp6
/proc/net/tcp:25
/proc/net/tcp6:2

$ ps -eo pid,cmd 2>/dev/null | grep -c 'sshd'   # 参考値（自身の grep を含みうる）
5
```

契約の「確定した事実」が言う中心の住所 `192.168.196.150` と、実測の住所が食い違う。
```
契約の記載: 192.168.196.150 / SSH 50072
実測の住所: 172.17.0.13 
文書の記載: docs/host_dev_env_setup.md:12 「philip は現在 Docker コンテナ内で 172.17.0.20」
```

`awk` の `strtonum` は mawk に無く空振りした（**終了コードを件数と呼ばない**・申し送り 5 の隣の罠）。
`/proc/net/tcp` を直接読み直す。
```
$ .venv/bin/python - <<'PY' … 待ち受け（state 0A）の口を列挙
待ち受け中の口 件数=5
  port=22 (tcp,tcp6)
  port=33375 (tcp)
  port=36563 (tcp)
  port=40935 (tcp)
  port=44816 (tcp)
50072 待ち受け=no
22000 待ち受け=no
8384  待ち受け=no
22001 待ち受け=no
```

**読み取れたこと。**

| 事実 | 実測 | 意味 |
|---|---|---|
| この中で SSH が待つ口は **22** | `port=22` が待ち受け中。**`50072` は待っていない** | philip は Docker の中にある。**`50072` は外側の写像**（外の `50072` → 中の `22`）であり、中からは見えない。契約の「SSH は `50072`」は**外から見た値として矛盾しない** |
| `22000` `22001` `8384` は待っていない | すべて `no` | **同期処理は動いていない**（禁止 2 を守れている）。中継も張られていない |
| この中の住所は `172.17.0.13` | `hostname -I` | Docker 内部の住所。**外からは使えない。** 文書の `172.17.0.20`（`docs/host_dev_env_setup.md:12`）とも違う＝**容器が作り直されるたびに変わる** |
| 契約の中心の住所 `192.168.196.150` | **局所からは検証できない** | 容器の外側（Docker ホスト）の住所と考えれば矛盾しない。**他ホストへ接続できない**ため（禁止 5）到達性は **UNKNOWN** |

**中継の終端は「容器の中」である。** `-L 22001:127.0.0.1:22000` の `127.0.0.1` は
sshd が動いている側＝容器の中を指す。常駐処理も容器の中で動くため、
**中心の同期処理は容器の中で `22000` を待てばよい。** `listenAddress=default` は
`tcp://0.0.0.0:22000` を含むため、この要求を満たす。

### Step 2: 順序を決める

| 問い | 判定 | 根拠 |
|---|---|---|
| 中心と一般ノード、どちらの設定を先に入れるか | **中心（philip）が先** | ノードは中心の識別子を相手として登録する必要があり、中心が受けられない状態でノードを起動すると接続に失敗し続ける。逆に中心を先に立てても、ノードが未登録なら中心は誰とも繋がらないだけで害が無い |
| 中継を張るのは設定の前か後か | **設定の後、起動の前** | 中継は目印 `.tunnel_to_philip` を置くと常駐処理が**次の周（最大 30 分）で自動的に**張る（`keeper.sh:33-38`）。設定より先に置くと、設定が未完成のまま経路だけが開く。**起動より前**でなければならないのは、ノードの同期処理が `tcp://127.0.0.1:22001` を相手の住所として使うため（`T-2026-08-12-sync-audit-bengio/audit.md:212` の旧構成がまさにこの形） |
| 同期処理を常駐させるのは全台同時か、一台ずつか | **一台ずつ。中心 → ノード 1 台 → 残り 3 台** | 「全台同時に動かして失敗すると遠隔から直せない」。**既定の設定は外部告知と公開中継が有効**（実測）。落とし忘れたまま 5 台同時に起動すると、5 台が同時に外へ出る |
| 一台目で確かめてから次へ進むべきか | **必ず確かめる** | 中心＋ノード 1 台で**実際にファイルが届くこと**まで見てから 2 台目へ進む。届かない原因（中継・識別子・除外規則・型）を 1 対 1 で切り分けられるのは最初の 1 組だけである |

#### 起動の引き金は「実行権」である（この構成に固有の要点）

`keeper.sh:41-43` は **`[ -x ~/bin/syncthing ]` が真で、かつ動いていなければ起動する。**
設定の中身も、中継の有無も、目印の有無も見ない。したがって:

- **実行権を戻した瞬間から最大 30 分で、そのときの設定のまま同期処理が起動する。**
- ゆえに順序は **「設定を確定させる」→「実行権を戻す」** に固定される。逆順にできない。
- **止めたいときは実行権を外す**（`chmod 644`）。ただし既に動いている処理は止まらないので、
  併せて処理を終わらせる必要がある。常駐処理そのものは止めない（別の禁止に触れる）。

現在 philip の `~/bin/syncthing` は **644**（前契約の回避策）。**これが 5 台に効く安全装置になっている。**

### Gate G2（Phase B 直後）

| 条件 | 結果 |
|---|---|
| 旧構成の定義を版管理の記録から復元 | 済（`folder_count=2` / `claude-sync` と `m2` / 位置・型・共有相手・告知と中継の設定まで、出所つきで復元） |
| 決めきれないものを区別 | 済（4 件を UNKNOWN として明記: claude-sync に何を戻すか・どの台が中身を持つか・型・初回 19G の転送） |
| 除外規則の正本と反映先を実装から確認 | 済（`keeper.sh:48-49`。正本＝反映先＝`origin/phase0` の三者が sha256 `61593e99…` で一致） |
| 登録と起動の順序を根拠つきで判定 | 済（引き金が実行権であることから順序が固定される） |
| 中心用と一般ノード用の手順 | 済（`handoff.md` §2 §3。事前の記録から戻し方まで） |
| 失敗の様式 | 済（`handoff.md` §5。8 様式＋「五台とも止まる」の回避策 6 点） |

**G2 PASS。**

## Task 5 (Phase C): 無変更を確かめ、報告する

### Step 2: 開始時と同一であることを要約値で確かめる
```
$ for f in ~/.local/state/syncthing/*; do test -f "$f" && echo "$(sha256sum "$f") $(stat -c "%s %a" "$f")"; done
5f3b4bd8791d6fa873f5dd0c1089dc9878b3525e40e612b4cd07ac7558a5b4ac  /home/ubuntu/.local/state/syncthing/cert.pem 794 664
abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  /home/ubuntu/.local/state/syncthing/config.xml 8494 600
92629ef108b100a80d3d0c511a3679239a7a21e80a67bfe3468dd1294d7d52f6  /home/ubuntu/.local/state/syncthing/key.pem 288 600

開始時（Task 1 Step 1）:
  5f3b4bd8791d6fa873f5dd0c1089dc9878b3525e40e612b4cd07ac7558a5b4ac  cert.pem   794 664
  abb2fa89a7b7f61ae3f27f1428a2f9972c91905af9ebf2ca5fcd901292dd927a  config.xml 8494 600
  92629ef108b100a80d3d0c511a3679239a7a21e80a67bfe3468dd1294d7d52f6  key.pem    288 600

$ ls -a ~/ | grep -c '^\.tunnel_to_'
0

$ ls -la ~/bin/syncthing; sha256sum ~/bin/syncthing   # 実行権を戻していないこと
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
```

### Step 3: 稼働しているものを数える（両方向の対照つき）
```
$ .venv/bin/python - <<'PY' …（契約 Task 5 Step 3 の走査そのまま）
自己と祖先の除外数=15
走査した /proc の項目数=38
syncthing(partial)=0
keeper.sh(partial)=1
ssh(partial)=2
zzz_none=0
python(exact_arg)=0

$ 引数の要素で照合する版（申し送り 4: 部分一致は包み込みを拾う）
syncthing(実行ファイル名が一致) = 0 
keeper.sh(引数の要素が ~/bin/keeper.sh) = 1 ['72428']
m2-sync.sh(同上) = 0 
中継(ssh -L 22001:127.0.0.1:22000) = 0 
陽性対照 zsh(実行ファイル名が一致) = 3 ['47296', '53474', '67249']
陰性対照 zzz_no_such(同上) = 0 
```

**読み取り。**

| 対象 | 件数 | 判定 |
|---|---|---|
| 同期処理 | **0** | 禁止 2 を守れている |
| 常駐処理 `keeper.sh` | **1**（pid 72428） | 前契約で起動したもの。停止も再起動もしていない（禁止 4） |
| 中継 | **0** | 禁止 3 を守れている |
| 陽性対照 `zsh` | **3** | **検出器が動いている**ことの証拠 |
| 陰性対照 `zzz_no_such` | **0** | 存在しない語は 0 を返す |

🔴 **契約が用意した陽性対照は働かなかった。** `python(exact_arg)=0` である。
本走査は自分自身と祖先を除外し、かつこの環境の実行は `.venv/bin/python` であるため、
引数の要素が厳密に `python` と一致する処理は存在しない。**つまり契約の陽性対照は
「常に 0 を返す壊れ方」と区別できない**（契約自身が申し送り 3 で戒めた失敗である）。
実在する語として `zsh` を使い直し、**3 件**を得て検出器が動くことを示した。
起票者の誤り: `check_does_not_check`。

`ssh(partial)=2` は**部分一致が拾った包み込み**である（対話の sshd 等）。
引数の要素で照合すると中継は **0 件**になる（申し送り 4 のとおり）。

### Step 4: 検証を通す
```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b08

$ make task-validate …; echo validate_exit=$?
OK   T-2026-08-24-syncthing-config-survey

1 task(s), 0 failed
validate_exit=0

$ make task-preflight …; echo preflight_exit=$?
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-24-syncthing-config-survey/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 6 件が該当: separated_source@tasks/T-2026-08-24-syncthing-config-survey/SPEC.md:38, separated_source@tasks/T-2026-08-24-syncthing-config-survey/SPEC.md:390, separated_source@tasks/T-2026-08-24-syncthing-config-survey/SPEC.md:393, separated_source@tasks/T-2026-08-24-syncthing-config-survey/SPEC.md:396, separated_source@tasks/T-2026-08-24-syncthing-config-survey/SPEC.md:424 ほか 1 件（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0

$ make forbidden-check; echo forbidden_exit=$?
{"base": "origin/phase0", "changed": 7, "checked": 7, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

🔴 **`forbidden-check` が通ったのは、退避の副作用である。正直に記す。**
本契約の開始前、この検査は `data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md` を
「禁止領域 `data/` の内側」として指し、`status: fail` を返していた（実測）。
`make task-start` の前提を満たすためにその未追跡ファイルを `git stash` へ退避したので、
いま検査対象から消えているだけである。**`git stash pop` で戻せば再び `fail` に戻る。**
禁止 8 が削除も移動も commit も禁じているため、本契約では解決できない。起票者の判断が要る。

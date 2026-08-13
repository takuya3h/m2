# T-2026-08-13-hub-role-and-restart audit

## 実行前提

```text
2
feat/hub-role-and-restart
?? tasks/T-2026-08-13-hub-role-and-restart/
```

- 稼働中の同期スクリプトには `sync-pause` が2箇所ある。
- 作業分岐は `feat/hub-role-and-restart`。
- 契約自身の未追跡ディレクトリ以外に開始時差分はない。

## 開始時の無変更基準

```text
=== hashes_before ===
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
marker_count=1
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.tunnel_to_philip
4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db  /home/ubuntu/.ssh/authorized_keys
=== lock_before ===
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 13 07:42 /home/ubuntu/.keeper.lock
=== processes_before ===
ssh -N -L=0
keeper.sh=1
syncthing=2
m2-sync=0
zzz_no_such_process=0
```

## Phase A — Task 1: keeperの役割

### 稼働版と正本の要約値

```text
=== live_summary ===
34 /home/ubuntu/bin/keeper.sh
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
=== source_summary ===
52 scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
```

### 稼働版の全文

```text
     1  #!/bin/bash
     2  # keeper.sh: cron/systemd の無いコンテナ環境用の常駐スーパーバイザ。
     3  # 配置:   git -C <m2> show origin/phase0:scripts/sync/keeper.sh > ~/bin/keeper.sh
     4  #         （作業ツリーのブランチに依存しないよう、git オブジェクトから直接展開する）
     5  # 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
     6  # 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
     7  exec 9>~/.keeper.lock
     8  flock -n 9 || exit 0
     9
    10  M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)
    11
    12  while true; do
    13    # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
    14    # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
    15    if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    16      nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
    17        -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
    18        -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    19        ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &
    20    fi
    21    # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
    22    # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
    23    if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    24      nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
    25    fi
    26    # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
    27    git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
    28      && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
    29    # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
    30    git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
    31      && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
    32    ~/bin/m2-sync.sh 9>&-
    33    sleep 1800 9>&-
    34  done
```

### 正本の全文

```text
     1  #!/bin/bash
     2  # keeper.sh: cron/systemd の無いコンテナ環境用の常駐スーパーバイザ。
     3  # 配置:   git -C <m2> show origin/phase0:scripts/sync/keeper.sh > ~/bin/keeper.sh
     4  #         （作業ツリーのブランチに依存しないよう、git オブジェクトから直接展開する）
     5  # 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
     6  # 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
     7  resolve_tunnel() {
     8    TUNNEL_MARKER=
     9    for candidate in "$HOME"/.tunnel_to_*; do
    10      if [ -f "$candidate" ]; then
    11        TUNNEL_MARKER=$candidate
    12        break
    13      fi
    14    done
    15    [ -n "$TUNNEL_MARKER" ] || return 1
    16
    17    HUB_NAME=${TUNNEL_MARKER##*/}
    18    HUB_NAME=${HUB_NAME#.tunnel_to_}
    19    TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
    20    HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
    21    [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
    22    [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
    23  }
    24
    25  exec 9>~/.keeper.lock
    26  flock -n 9 || exit 0
    27
    28  M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)
    29
    30  while true; do
    31    # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
    32    # 1行目は秘密鍵パス、任意の2行目は中心の住所。2行目が無い旧形式では中心名をSSH別名に使う。
    33    if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    34      nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
    35        -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
    36        -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    37        ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
    38    fi
    39    # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
    40    # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
    41    if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    42      nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
    43    fi
    44    # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
    45    git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
    46      && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
    47    # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
    48    git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
    49      && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
    50    ~/bin/m2-sync.sh 9>&-
    51    sleep 1800 9>&-
    52  done
```

### 全文差分

```text
diff_exit=1
diff_lines=47
diff --git a/home/ubuntu/bin/keeper.sh b/scripts/sync/keeper.sh
index bb6730f..5a4db53 100755
--- a/home/ubuntu/bin/keeper.sh
+++ b/scripts/sync/keeper.sh
@@ -4,19 +4,37 @@
 #         （作業ツリーのブランチに依存しないよう、git オブジェクトから直接展開する）
 # 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
 # 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
+resolve_tunnel() {
+  TUNNEL_MARKER=
+  for candidate in "$HOME"/.tunnel_to_*; do
+    if [ -f "$candidate" ]; then
+      TUNNEL_MARKER=$candidate
+      break
+    fi
+  done
+  [ -n "$TUNNEL_MARKER" ] || return 1
+
+  HUB_NAME=${TUNNEL_MARKER##*/}
+  HUB_NAME=${HUB_NAME#.tunnel_to_}
+  TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
+  HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
+  [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
+  [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
+}
+
 exec 9>~/.keeper.lock
 flock -n 9 || exit 0

 M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

 while true; do
-  # hub(philip)へのSSHトンネル維持（~/.tunnel_to_philip が存在するノードのみ。中身=秘密鍵パス）
-  # コンテナ間はSSH(50072)しか通らないため、syncthingは星型(各ノード→philip)で接続する
-  if [ -f ~/.tunnel_to_philip ] && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
-    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$(cat ~/.tunnel_to_philip)" \
+  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
+  # 1行目は秘密鍵パス、任意の2行目は中心の住所。2行目が無い旧形式では中心名をSSH別名に使う。
+  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
+    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
       -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
       -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
-      ubuntu@192.168.196.150 >>~/.tunnel.log 2>&1 9>&- &
+      ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
   fi
   # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
   # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
```

`diff_exit=1` は差分ありの仕様。判定値は `diff_lines=47`。

### 周回処理と中心での必要性（正本の行番号）

| # | 処理 | 行番号 | 中心で要るか |
|---:|---|---|---|
| 1 | 目印を辞書順で一件解決し、中心名・鍵・任意住所を読む | 7–23、呼出33 | 不要。中心自身は中継を張らず、目印を置かない |
| 2 | 中継が無ければSSHローカル転送を起動する | 31–38 | 不要。中心は入られる側で、22000を直接待ち受ける |
| 3 | syncthingの存在とプロセスを確認し、停止中なら起動する | 39–43 | 必要。中心も同期先であり、実測で22000を待ち受けている |
| 4 | origin/phase0からm2-sync.shを自己更新する | 44–46 | 必要。中心でも後続のGit同期処理を最新版に保つ |
| 5 | origin/phase0の.stglobalignoreを.stignoreへ反映する | 47–49 | 必要。中心の同期対象制御にも使う |
| 6 | m2-sync.shを実行する | 50 | 必要。Git fetch・参照更新・auto-merge/push/PRを行う。中継参照は0件 |
| 7 | 1800秒待って次周回へ進む | 51 | 必要。上記処理を30分周期に制限する |

lock取得（25–26）と `M2DIR` 解決（28）は周回の外側で一度だけ行う。

### 目印の有無で分岐する範囲

- 目印探索と値の導出は7–23行。
- 目印が無ければ15行で `return 1` となり、33–38行のSSH中継起動だけを飛ばす。
- syncthing監視39–43、m2-sync更新44–46、`.stignore`反映47–49、m2-sync実行50、sleep 51は分岐の外。
- よって正本では、中心から目印を外しても中継以外の処理は動き続ける構造である。

### m2-syncの中継依存

```text
133 /home/ubuntu/bin/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
regex_match_count=0
22001=0
127.0.0.1=0
tunnel=0
ssh=0
```

正本も133行、SHA-256は同じで、全文差分は0行だった。全文を読み、45–48行はGit fetch、
50–58行はphase0参照更新、60–88行はauto-merge、90–110行はauto-push、112–133行は
Draft PR作成だった。SSH中継を参照する処理はない。

## Phase A — Task 2: 起動機構と新しい版の開始条件

### 起動経路の検索

```text
=== zshrc ===
37:alias code-tunnel-bg="nohup /home/ubuntu/.code tunnel --accept-server-license-terms > /home/ubuntu/.tunnel.log &!"
56:(nohup ~/bin/keeper.sh >/dev/null 2>&1 &)
=== other_shell_configs ===
他の設定に該当なし
=== systemd_names ===
systemd に該当なし
=== cron ===
cron に該当なし
```

`.zshrc` の周辺:

```text
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

. "$HOME/.local/bin/env"
fpath=(~/.zsh/completions $fpath)
autoload -U compinit && compinit

# dotfiles: failog
source "/home/ubuntu/slocal2/dotfiles/zsh/failog.zsh"
(nohup ~/bin/keeper.sh >/dev/null 2>&1 &)
```

別経路の横断検索:

```text
searched_path_count=7
SEARCHED /etc/systemd/system
SEARCHED /lib/systemd/system
SEARCHED /etc/cron.d
SEARCHED /home/ubuntu/.zshrc
SEARCHED /home/ubuntu/.zshenv
SEARCHED /home/ubuntu/.profile
SEARCHED /home/ubuntu/.bashrc
launch_hit_count=1
/home/ubuntu/.zshrc:56:(nohup ~/bin/keeper.sh >/dev/null 2>&1 &)
```

実在する7出所を横断し、keeper起動記述は1件・場所は `.zshrc:56`。systemdとcronには0件。
`.zshrc` は対話zsh開始時にのみ読まれるため、常時監視してkeeperを復活させる別サービスではない。

### 稼働プロセスの素性

```text
matching_process_count=1
pid=1071 ppid=1 start_ticks=7893775 start_utc=2026-07-18T09:44:50.750000+00:00 exe=/usr/bin/bash
cmd=/bin/bash /home/ubuntu/bin/keeper.sh
parent_cmd=sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
```

```text
descendant_count=3
pid=1079 ppid=1071 cmd=/home/ubuntu/bin/syncthing serve --no-browser
pid=3929423 ppid=1071 cmd=sleep 1800
pid=1395414 ppid=1079 cmd=/home/ubuntu/bin/syncthing serve --no-browser
```

keeperはPPID 1で起動シェルから切り離されている。測定時はsleep中で、syncthingを子孫に持つ。

### lockと本文の読み直し

```text
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 13 07:42 /home/ubuntu/.keeper.lock
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  /home/ubuntu/.keeper.lock
live:   7:exec 9>~/.keeper.lock
live:   8:flock -n 9 || exit 0
source:25:exec 9>~/.keeper.lock
source:26:flock -n 9 || exit 0
fd9=/home/ubuntu/.keeper.lock
lock: 1: FLOCK  ADVISORY  WRITE 0 00:179:35033503 0 EOF
lock_probe_exit=1
```

非待機のlock取得はexit 1となり、PID 1071がWRITE flockを保持している。古いkeeperが生きる間、
`.zshrc` から新しいkeeperを起動しても26行でexit 0となる。

```text
fd255_inode=36197337 size=2250 mode=775
path_inode=36197337 size=2250 mode=775
/home/ubuntu/bin/keeper.sh
```

keeperは同一プロセス内の `while true`（正本30–52）を回り、keeper自身を再実行する箇所はない。
PID 1071は本文をFD255で開いたまま保持している。パス上のファイルを新しいinodeへ置き換えても、
既存PIDは古いFD/実行状態で周回し続け、新版を開始しない。新しい版には旧PIDの終了と新規起動が必要。

### 止め方・起こし方の候補（本契約では未実行）

| 方法 | 副作用 | 中継はどうなるか | 判定 |
|---|---|---|---|
| 配置だけ行い、次周回を待つ | 旧PIDが古い本文で継続。新版は動かない | 旧版の固定philip処理が継続 | 不可 |
| 新しい対話zshを開く | `.zshrc:56` が起動を試すが、旧PIDのflockで新プロセスは即終了 | 旧版の中継が継続 | 単独では不可 |
| 目印を外して次周回を待つ | 正本では新規中継を張らないが、既存旧版は固定目印を見る。既存中継を終了する処理はない | 既存中継は自動では切れない | 再起動方法ではない |
| 旧keeperへTERMを送り、対話zsh開始に任せる | 常時再起動サービスはなく、対話zshが開かれるまでkeeper不在 | 既存SSH子はnohupで独立しており直ちには切れないが、死活監視が止まる | 不確実 |
| 旧keeperへKILLを送る | 強制終了。穏当な終了確認ができない | 同上 | TERM失敗時だけの候補 |
| 正本を検証・退避後に配置し、旧keeperへTERM、PID/lock解放を待ち、明示的にnohup起動 | 短時間keeper監視が止まる。syncthingと既存SSH子はnohupかつFD9を継承していない | 一般ノードの既存中継は新keeper起動まで監視されない。中心には中継不要 | 最も安全 |

最安全候補は最後の方法。広域 `pkill` は使わず、事前に同定したkeeper PIDだけへTERMを送り、
`/proc/PID` 消滅とlock取得可能を確認してから、正本5行の明示コマンドで起動する。起動後は
keeperが1件、FD9 flock保持、実行中FD255のSHA-256が配置版と一致することを確認する。

### 中心の待受と同期対象

`ss` は未導入だったため、`/proc/net/tcp*` で別測定した。

```text
ss_command_missing=1
selected_listen_count=2
tcp4 port=8384 local_hex=0100007F:20C0 inode=27303292
tcp6 port=22000 local_hex=00000000000000000000000000000000:55F0 inode=27311444
```

中心ではSyncthing GUI 8384がloopback、同期入口22000が全IPv6アドレスでLISTENしている。
設定上の同期folderは `/home/ubuntu/claude-sync` と `/home/ubuntu/slocal2/m2` の2件。
`m2/.stignore` は68行、SHA-256
`61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a` で、通常ファイルは
末尾の `**` により無視される。実ファイル疎通試験には明示許可済みの小さな `.pt` 等か、
別folder `claude-sync` 内の契約専用プローブを使う必要がある。

## Gate G1

PASS。keeper両版の全文・SHA-256・行数と47行の全文差分を記録した。周回処理と目印分岐を
行番号付きで判定し、m2-syncに中継参照がないことを二方式で確認した。起動経路は7出所で
1件、プロセスはPID 1071/PPID 1、lock保持を実測。旧PIDは本文を再起動しない構造と判定した。

## Phase B — 配置順序と復旧手順の決定

### 中心を先にするか

| 問い | 判定と根拠 |
|---|---|
| 中心のkeeperが旧版でも他ホストは繋ぎに来られるか | **来られる。** keeperのSSH処理は外向きlocal forwardだけ（稼働版15–20、正本33–38）。中心の着信SSH/authorized_keysを変更する処理はない。ただしSyncthing 22000が動くことは別条件 |
| 中心の目印を外すと他の処理は動き続けるか | **正本では続く。** marker失敗で飛ぶのは33–38。syncthing 39–43、m2-sync更新44–46、ignore反映47–49、実行50は外側 |
| 一般ノードが新markerを持ち、中心未準備なら何が起きるか | keeper33–38は中心50072へSSHを試す。認証・到達失敗ならSSHが終了し、次の試行はsleep 51後の周回。SSHが立っても中心22000停止ならSyncthingデータ面は成立しない |

結論は**中心lecunを先**。lecunで新版keeper・marker 0・keeper 1・flock・Syncthing 22000を
先に確立し、その後は一般ノードを一台ずつ切り替える。efrosとbengioのどちらをcanaryに
するかは実装だけでは決められず `UNKNOWN`。現地preflightの鍵指紋・旧中継・復旧経路で選ぶ。

### 手順書

一般ノード用と中心用について、事前記録、控え、mode 755のkeeper配置、marker、数値PID限定の
TERM、明示nohup起動、成功確認、rollbackを `handoff.md` に記録した。一般ノードでは
旧SSH中継を明示終了する。正本33行のpgrepが接続先を区別せず、旧中継が新中継を抑止するため。

### 疎通確認

`handoff.md` にkeeper/lock、local 22001、SSH 50072認証、中心22000、Syncthing device、
m2-syncログ、一方向/双方向ファイルSHA-256の各確認について「示すこと／示さないこと」を分離した。

```text
.gitignore:46:*.pt  hrr-probe.pt
git_check_ignore_exit=0
```

`.stignore:57` は `!*.pt`、68行は `**`。次契約の強い確認として、一意名のroot `.pt` を
双方向に送り、両端のsize/SHA-256と同時刻のdevice接続先を記録する。現タスクでは作成していない。

### 失敗様式

配置破損、旧keeper残存、旧中継残存、marker/鍵誤り、lecun認証失敗、中心22000停止、
sync-pause解除忘れ、probe不一致、全台同時停止を `handoff.md` に症状・検出・rollback付きで列挙した。

## Gate G2

PASS。中心先行を実装行番号で決定し、中心用・一般ノード用の手順を事前記録からrollbackまで
書いた。疎通確認の証明範囲を分離し、双方向probeを定義した。失敗9様式と全台断回避gateを記録した。

## Phase C — 無変更の確認

```text
=== hashes_after_analysis ===
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
marker_count=1
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.tunnel_to_philip
4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db  /home/ubuntu/.ssh/authorized_keys
=== lock_after_analysis ===
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 13 07:42 /home/ubuntu/.keeper.lock
=== processes_after_analysis ===
ssh -N -L=0
keeper.sh=1
syncthing=2
m2-sync=0
zzz_no_such_process=0
```

開始時と全SHA-256、marker件数、lock属性、全プロセス件数が一致した。

### 中継依存検索の陽性対照

```text
keeper_dependency_positive_count=15
7:resolve_tunnel() {
8:  TUNNEL_MARKER=
9:  for candidate in "$HOME"/.tunnel_to_*; do
11:      TUNNEL_MARKER=$candidate
15:  [ -n "$TUNNEL_MARKER" ] || return 1
17:  HUB_NAME=${TUNNEL_MARKER##*/}
18:  HUB_NAME=${HUB_NAME#.tunnel_to_}
19:  TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
20:  HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
22:  [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
31:  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
32:  # 1行目は秘密鍵パス、任意の2行目は中心の住所。2行目が無い旧形式では中心名をSSH別名に使う。
33:  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
34:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
37:      ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
```

同じ正規表現はkeeperで15件、m2-syncで0件となり、検索器が常に0を返す壊れ方ではない。

## Phase C — 検証と変更範囲

```text
OK   T-2026-08-13-hub-role-and-restart

1 task(s), 0 failed
validate_exit=0
```

```text
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-13-hub-role-and-restart/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 5 件が該当: separated_source@tasks/T-2026-08-13-hub-role-and-restart/SPEC.md:353, separated_source@tasks/T-2026-08-13-hub-role-and-restart/SPEC.md:356, separated_source@tasks/T-2026-08-13-hub-role-and-restart/SPEC.md:359, separated_source@tasks/T-2026-08-13-hub-role-and-restart/SPEC.md:362, separated_source@tasks/T-2026-08-13-hub-role-and-restart/SPEC.md:399（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
```

```text
{"base": "origin/phase0", "changed": 7, "checked": 7, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

投影検査:

```text
taskindex_check_exit=2
inbox_check_exit=2
```

本taskのsummary、followups 3件、unknowns 3件、起票者欠陥2件、判断1件が未投影。
禁止9に従い `make taskindex` と `make inbox` は実行していない。

変更範囲:

```text
status_lines=2
?? tasks/T-2026-08-13-hub-role-and-restart/
?? tasks/inbox.d/T-2026-08-13-hub-role-and-restart.md
unmerged=0
diff_check_exit=0
```

変更は契約ディレクトリと専用受け皿だけで、未解決マージはない。

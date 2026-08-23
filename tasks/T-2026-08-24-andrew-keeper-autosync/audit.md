# audit — T-2026-08-24-andrew-keeper-autosync

出力は要約せず貼る（申し送り 9）。実行ホスト andrew / repo ~/slocal2/m2。

## Phase A / Task 1 Step 1: 開始状態

### 0. 分岐と HEAD（分岐は本セッション外で origin/phase0 から作成済み）
```
## feat/andrew-keeper-autosync...origin/phase0
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
```

### ls -la ~/bin/
```
total 26116
drwxrwxr-x 2 ubuntu ubuntu     4096 Aug 23 13:54 .
drwxr-x--- 1 ubuntu ubuntu     4096 Aug 23 17:31 ..
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:54 syncthing
```

### 目印（.tunnel_to_*）
```
(該当なし)
marker_count=0
```

### 起動行（~/.zshrc）— 無いことと読めないことを区別（申し送り 2）
```
-rw-rw-r-- 1 ubuntu ubuntu 2116 Aug 23 15:23 /home/ubuntu/.zshrc
zshrc_lines=77
keeper_hits=0
0
```

### 錠（~/.keeper.lock）
```
ls: cannot access '/home/ubuntu/.keeper.lock': No such file or directory
lock なし
```

### 記録の置き場所（~/claude-sync/）
```
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
does not exist
```

### 未追跡の件数と内訳
```
untracked_and_changed_count=4
?? .sync-pause.released
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? docs/sessions/digest/2026-08-23-5d62430b-7545-4769-a54e-673ea88fdc8d.md
?? tasks/T-2026-08-24-andrew-keeper-autosync/
```

## Phase A / Task 1 Step 2: 稼働しているものを数える

### 契約の指定どおり（対照 zzz_none）
```
keeper.sh=0
m2-sync=0
syncthing=0
ssh -N -L=0
zzz_none=0
```

### 対照を両方向で取る（申し送り 6）。zzz_none だけでは「数えられること」を示せない
```
excluded_self_chain=[4252, 4263, 4264, 4266, 4284, 4343, 4347, 4524, 4771, 6664, 6665, 6666, 31005, 37582, 37585]
systemd=0 []
sshd=1 ['1']
zzz_none=0 []
```

sshd=1（pid 1）で計数器が生きた処理を検出できることを示した。systemd=0 は本ホストが
コンテナで systemd を持たないためであり、常駐処理を自前で回す keeper.sh の前提と整合する。

## Phase A / Task 1 Step 3: 正本の要約値と、目印による分岐

```
52 scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
--- 分岐点 ---
5:# 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
6:# 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
9:  for candidate in "$HOME"/.tunnel_to_*; do
18:  HUB_NAME=${HUB_NAME#.tunnel_to_}
26:flock -n 9 || exit 0
31:  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
33:  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
34:    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
40:  # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
44:  # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
45:  git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
46:    && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
50:  ~/bin/m2-sync.sh 9>&-
51:  sleep 1800 9>&-
--- m2-sync.sh ---
133 scripts/sync/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
```

### keeper.sh 全文（行番号つき）
```
     1	#!/bin/bash
     2	# keeper.sh: cron/systemd の無いコンテナ環境用の常駐スーパーバイザ。
     3	# 配置:   git -C <m2> show origin/phase0:scripts/sync/keeper.sh > ~/bin/keeper.sh
     4	#         （作業ツリーのブランチに依存しないよう、git オブジェクトから直接展開する）
     5	# 起動:   nohup ~/bin/keeper.sh >/dev/null 2>&1 &   （flock で多重起動防止。.zshrc から毎回呼んで安全）
     6	# 役割:   (1) syncthing の起動・死活監視 (2) m2-sync.sh の30分毎実行 (3) m2-sync.sh の自己更新
     7	resolve_tunnel() {
     8	  TUNNEL_MARKER=
     9	  for candidate in "$HOME"/.tunnel_to_*; do
    10	    if [ -f "$candidate" ]; then
    11	      TUNNEL_MARKER=$candidate
    12	      break
    13	    fi
    14	  done
    15	  [ -n "$TUNNEL_MARKER" ] || return 1
    16	
    17	  HUB_NAME=${TUNNEL_MARKER##*/}
    18	  HUB_NAME=${HUB_NAME#.tunnel_to_}
    19	  TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
    20	  HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
    21	  [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
    22	  [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
    23	}
    24	
    25	exec 9>~/.keeper.lock
    26	flock -n 9 || exit 0
    27	
    28	M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)
    29	
    30	while true; do
    31	  # .tunnel_to_* を辞書順で一つ選び、ファイル名から中心を導出する。目印が無ければ張らない。
    32	  # 1行目は秘密鍵パス、任意の2行目は中心の住所。2行目が無い旧形式では中心名をSSH別名に使う。
    33	  if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
    34	    nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
    35	      -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
    36	      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
    37	      ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
    38	  fi
    39	  # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
    40	  # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
    41	  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
    42	    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
    43	  fi
    44	  # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
    45	  git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
    46	    && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
    47	  # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
    48	  git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
    49	    && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
    50	  ~/bin/m2-sync.sh 9>&-
    51	  sleep 1800 9>&-
    52	done
```

## Phase A / Task 1 Step 4: 版管理の同期の発火条件

```
5:#   加えて、コミット済みで未 push のものを自分の作業ブランチへ送る（auto-push）
14:# 稼働中の keeper は SERVERNAME を設定する前に起動していることがあり
15:# （例: ilya の PID 73082 は 2026-07-04 起動 / SERVERNAME 設定は 2026-08-02）、
18:SRV="${SERVERNAME:-}"
30:# 実行者の操作なしに作業分岐へ auto-merge する。実行者の努力では守れないため、
40:if [ -f "$M2DIR/.sync-pause" ]; then
41:  alert "一時停止中: $M2DIR/.sync-pause があるため分岐へ書き込まない（消せば再開）"
60:# --- auto-merge: phase0 の更新を作業ブランチへ取り込む ---
61:# auto-push より前に置く。merge してから push すれば 1 ループで両方片付く。
70:      alert "auto-merge skip: 追跡変更 ${DIRTY} 件 (behind ${BEHIND})"
78:        alert "auto-merge skip: 未追跡 ${BLOCKED} 件が阻害 (behind ${BEHIND}) 手動対応が必要"
80:        alert "auto-merge: ${BR} <- origin/${MAIN} (${BEHIND} commits)"
84:        alert "auto-merge失敗(abort済): ${BR} <- origin/${MAIN} 手動対応が必要"
90:# --- auto-push: コミット済みで未 push のものを自分の作業ブランチへ送る ---
97:# auto-push とアラートを繰り返す（2026-08-05 に ilya で再現・実測）。
105:      alert "auto-push: $BR ($AHEAD commits)"
107:      alert "auto-push失敗: $BR ($AHEAD commits) 手動確認が必要"
```

### 付随して確かめたこと（keeper が触る repo 内ファイルが版管理を汚さないか）
```
sync_pause_hits_in_canonical=2
-rw-rw-r-- 1 ubuntu ubuntu 2223 Aug 16 08:07 .stignore
.gitignore:192:.stignore	.stignore
.stglobalignore は origin/phase0 に存在
-rw-rw-r-- 1 ubuntu ubuntu 7 Aug  5 05:26 .servername
.gitignore:225:.servername	.servername
SERVERNAME=[andrew]
/usr/bin/flock
```

### 起票者の理解と実装の食い違い（実装を正とする）

SPEC の表は 39–50 行を「同期処理の監視、除外規則の反映、版管理の同期」として
「これを動かす」側に置く。実装ではその範囲の 41–43 行が **syncthing を起動する**。

```
38+1	  # syncthing が入っていて動いていなければ起動（未インストールならスキップ）
38+2	  # 9>&- : ロックFDを子に継承させない（継承するとkeeper再起動時にflockが永久に失敗する）
38+3	  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
38+4	    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
38+5	  fi
38+6	  # m2-sync.sh を phase0 の最新版へ自己更新してから実行（前回 fetch 時点の origin/phase0 を使用）
38+7	  git -C "$M2DIR" show origin/phase0:scripts/sync/m2-sync.sh > ~/bin/m2-sync.sh.new 2>/dev/null \
38+8	    && mv ~/bin/m2-sync.sh.new ~/bin/m2-sync.sh && chmod +x ~/bin/m2-sync.sh
38+9	  # Syncthing の同期ルール (.stignore) も phase0 の .stglobalignore から自動反映
38+10	  git -C "$M2DIR" show origin/phase0:.stglobalignore > "$M2DIR/.stignore.new" 2>/dev/null \
38+11	    && mv "$M2DIR/.stignore.new" "$M2DIR/.stignore"
38+12	  ~/bin/m2-sync.sh 9>&-
```

| 行 | 動作 | 目印による制御 |
|---|---|---|
| 33–38 | 中継 `ssh -N -L 22001:127.0.0.1:22000 -p 50072` | `resolve_tunnel()` が `~/.tunnel_to_*` を要求。**目印が無ければ張らない** |
| 41–43 | `nohup ~/bin/syncthing serve --no-browser &` | **目印と無関係。条件は `[ -x ~/bin/syncthing ]` のみ** |
| 45–46 | `~/bin/m2-sync.sh` を `origin/phase0` から自己更新 | 無条件 |
| 48–49 | `$M2DIR/.stignore` を `origin/phase0:.stglobalignore` から更新 | 無条件（`.stignore` は `.gitignore:192` で除外済み） |
| 50 | `~/bin/m2-sync.sh` 実行 | 無条件 |
| 51 | `sleep 1800` | 無条件 |

`.sync-pause` は救いにならない。抑止は `m2-sync.sh` の 40–43 行にあり、syncthing の起動
（keeper 41 行）はその手前で起きる。抑止が守るのは **分岐への書き込みだけ** である。

### 版管理の同期の発火条件（m2-sync.sh 実測）

| 動作 | 行 | 条件 |
|---|---|---|
| 記録の置き場所 | 11, 22 | `~/claude-sync/sync-alerts.log`。`mkdir -p` で自動作成 |
| 論理名の解決 | 18–20 | `$SERVERNAME` → `$M2DIR/.servername` → `hostname` の 3 段 |
| **抑止** | 40–43 | `.sync-pause` があれば記録だけ残して `exit 0`（fetch より前） |
| auto-merge | 64–88 | 作業分岐 かつ behind>0 かつ 追跡変更 0 件 かつ 未追跡が取り込み先と衝突しない |
| auto-push | 101–110 | 作業分岐 かつ `origin/$BR` が存在 かつ `origin/$BR..HEAD` > 0 |
| auto-PR | 115–132 | 作業分岐 かつ `gh` が在る かつ `origin/phase0..HEAD` > 0 かつ 開いている PR が 0 件 → Draft PR 起票 |

## Phase B / Task 2: 正本を配置する

### Step 1: 配置と要約値の照合
```
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
--- origin/phase0 の git object とも照合（keeper は git object から配る設計） ---
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  -
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  -
--- ls ---
total 26128
drwxrwxr-x 2 ubuntu ubuntu     4096 Aug 23 17:32 .
drwxr-x--- 1 ubuntu ubuntu     4096 Aug 23 17:31 ..
-rwxr-xr-x 1 ubuntu ubuntu     2709 Aug 23 17:32 keeper.sh
-rwxr-xr-x 1 ubuntu ubuntu     7342 Aug 23 17:32 m2-sync.sh
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:54 syncthing
```

四つすべて一致し、`origin/phase0` の git object とも一致した。よって keeper 45–46 行の
自己更新が走っても配置物は変化しない。

### Step 2: 構文検査
```
keeper_syntax=0
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
m2sync_syntax=2
lrwxrwxrwx 1 root root 4 Mar 31  2024 /bin/sh -> dash
#!/bin/bash
#!/bin/bash
keeper_syntax_bash=0
m2sync_syntax_bash=0
```

契約の指定する `sh -n` は本ホストでは dash である。`m2-sync.sh` 75 行の process substitution
`<(...)` は dash に無いため exit 2 になる。両スクリプトの shebang は `#!/bin/bash` であり、
keeper 50 行は `~/bin/m2-sync.sh` を shebang 経由で起動するため、実際に解釈するのは bash である。
**bash では両方 0。** 起票者の誤り（`shell_assumption`）として記録し、実行を止める根拠にはしない。

### Step 3: 目印が零件
```
(該当なし)
marker_count=0
```

### Step 4: 抑止を置く
```
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:32 .sync-pause
sync_pause_hits_in_deployed=2
```

### 承認済みの逸脱: 起動前に syncthing の実行権を外す

keeper 41 行の条件は `[ -x ~/bin/syncthing ]` のみであり、目印では止まらない。
禁止 2「同期処理を起動する」を守るため、起動前に実行権だけを外した（ユーザー承認済み）。
```
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:54 /home/ubuntu/bin/syncthing
keeper_guard_x_test=FALSE_will_not_start
size_bytes=26730145
```
大きさは 26730145 バイトのまま。削除も移動もしていない。戻し方は `chmod 755 ~/bin/syncthing`。

## Phase B / Task 3: 起動し、版管理の同期が回ることを確かめる

### Step 1: 起動行の追記 — **実行できていない**

`~/.zshrc` への追記が実行基盤の分類器に 3 回拒否された（`cat >>` / `tail` / Edit ツール）。
**回避は試みていない。** 追記しようとした内容は次のとおり。

```
# keeper: 常駐スーパーバイザ（flock で多重起動防止。毎回呼んで安全）— T-2026-08-24-andrew-keeper-autosync
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
```

追記前の該当件数は 0 件（Task 1 Step 1 の `keeper_hits=0`）であり、
「既存があれば追記しない」の条件には掛かっていない。

### Step 2–3: 明示起動と計数
```
（起動直前）syncthing_x=no marker_count=0 sync_pause=present
（nohup ~/bin/keeper.sh >/dev/null 2>&1 & のあと 8 秒待機）
keeper.sh=1 ['40838']
ssh -N -L=0 []
syncthing=0 []
zzz_none=0 []
sshd=1 ['1']
--- ポート ---
port_22000=0
port_22001=0
port_8384=0
```

### Step 4: 錠 と その陽性対照
```
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:36 /home/ubuntu/.keeper.lock
--- 二度目の起動を試みた結果（keeper.sh は 1 件のまま。二つ目は flock -n 9 || exit 0 で終了） ---
keeper.sh=1 ['40838']
--- 別プロセスから非ブロッキングで錠を取りに行く ---
flock_exit=1
```
`ACQUIRED_lock_is_free` は出力されず `flock_exit=1`。錠は実際に握られている。

### Step 5: 版管理の同期が一周し、抑止が効いている
```
-rw-rw-r-- 1 ubuntu ubuntu 146 Aug 23 17:35 /home/ubuntu/claude-sync/sync-alerts.log
2026-08-23 17:35:22 [andrew] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
lines_total=1
paused_lines=1
write_lines=0
## feat/andrew-keeper-autosync...origin/phase0
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
ahead=0 behind=0
```

記録の置き場所は `~/claude-sync/sync-alerts.log`（m2-sync.sh 11 行、22 行の `mkdir -p` で自動作成）。
論理名は `andrew` と解決されており、`nohup` 越しでも `SERVERNAME` が伝わっている。

### Step 1（続き）: 起動行の追記 — ユーザーがプロンプトから実行して完了

分類器の拒否は回避せずユーザーへ差し戻した。ユーザーが `!` 経由で `printf ... >> ~/.zshrc` を実行。
```
zshrc_lines_before=77
zshrc_lines_after=80
keeper_hits=2
79:# keeper: 常駐スーパーバイザ（flock で多重起動防止。毎回呼んで安全）— T-2026-08-24-andrew-keeper-autosync
80:( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
--- 末尾 4 行 ---
autoload -U compinit && compinit

# keeper: 常駐スーパーバイザ（flock で多重起動防止。毎回呼んで安全）— T-2026-08-24-andrew-keeper-autosync
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
```

追記した内容はこの 2 行（79–80 行）である。戻し方は末尾の空行を含む 3 行の削除。

### 追加の裏取り: 中継と同期処理の行が一度も走っていないこと

keeper 34 行は `>>~/.tunnel.log`、42 行は `>>~/.syncthing.log` へ追記する。
`>>` は不在ならファイルを作るため、**ログの不在はその行が一度も走っていない証拠**になる。
（この着眼点はユーザーの指摘による。）
```
.tunnel.log 不在 -> 34 行は一度も走っていない
.syncthing.log 不在 -> 42 行は一度も走っていない
--- 対照: >> が実際にファイルを作る側 ---
sync-alerts.log EXISTS -> m2-sync.sh 23 行の >> は走った
```

### keeper 48–49 行が触った repo 内ファイル
```
-rw-rw-r-- 1 ubuntu ubuntu 2223 Aug 23 17:35 .stignore
.gitignore:192:.stignore	.stignore
untracked_and_changed_count=4
?? .sync-pause.released
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? docs/sessions/digest/2026-08-23-5d62430b-7545-4769-a54e-673ea88fdc8d.md
?? tasks/T-2026-08-24-andrew-keeper-autosync/
```
`.stignore` は更新されたが `.gitignore:192` で除外済み。未追跡件数は開始時と同じ 4 件。

## Phase C / Task 4: 記録、抑止の解除、送出

### Step 2: 秘匿の検査（陽性対照を先に取る）
```
--- 囮 /tmp/ka_decoy.md に対して ---
decoy_hits=3   （3 行すべて検出）
decoy_removed=YES （囮は削除済み。commit していない）
--- 本番 ---
tasks/T-2026-08-24-andrew-keeper-autosync/SPEC.md:319:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
```
該当 1 件は SPEC 自身が検査手順として載せている正規表現であり、区切りと値が続く形ではない。

### Step 3: 検証
```
validate_exit=0
OK   T-2026-08-24-andrew-keeper-autosync

1 task(s), 0 failed
forbidden_exit=0
{"base": "origin/phase0", "changed": 9, "checked": 9, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
taskindex_check_exit=2
inbox_check_exit=2
--- 再生成はしていない（禁止 4）。差分の先頭のみ記録 ---
=== tasks_summary.csv ===
--- tasks_summary.csv (現在)
+++ tasks_summary.csv (再生成)
@@ -50,3 +50,4 @@
 T-2026-08-22-ilya-node-foundation,impl,pass,ilya,124,false,2,0,0,5,5,6,3,6,2,T-2026-08-22-philip-hub-foundation
 T-2026-08-22-lecun-node-foundation,impl,pass,lecun,122,false,2,0,0,5,5,6,3,4,3,T-2026-08-22-philip-hub-foundation
--- inbox.md (現在)
+++ inbox.md (再生成)
@@ -13,7 +13,7 @@
 このファイルが併合で衝突した場合は、`make inbox` で再生成すれば解消する。
 書式と面の一覧は `tasks/README.md` の「判断の受け皿」を参照。
 
```

### テスト（本契約は src/ tests/ を変更していないため before と after は同一の測定）
```
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
7 failed, 457 passed, 4 skipped, 16 warnings in 8.72s
```

### Step 5: 送出
```
origin	git@github.com:takuya3h/m2.git (fetch)
origin	https://github.com/takuya3h/m2.git (push)
9b166a6 docs(tasks): record the pause release and the reverse control on andrew
f7d6b98 docs(tasks): record the positive control for the sync pause on andrew
66a069a docs(tasks): record commit 64e7d50, push and PR #128 for the andrew keeper contract
64e7d50 feat(sync): deploy keeper and enable git autosync on andrew
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
## feat/andrew-keeper-autosync...origin/feat/andrew-keeper-autosync
```

### Step 6: 抑止の解除と、その反対方向の対照
```
--- 抑止あり（ahead=1, origin/BR 存在）で m2-sync.sh を回した ---
m2sync_exit=0 / log 1 -> 2 行 / paused_lines=2 / autopush_lines=0 / ahead は 1 のまま
--- 解除 ---
mv_exit=0 / repo 直下から消えた / test_f=absent
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:32 /tmp/.sync-pause.released.T-2026-08-24-andrew-keeper-autosync
--- 抑止なし（ahead=0）で m2-sync.sh を回した ---
m2sync_exit=0 / log 2 -> 2 行（増えない） / paused_lines=2（増えない）
Warning: Identity file ... id_Andrewdeploy not accessible が 2 回 = 45 行と 56 行の git fetch まで到達
--- 記録の全文 ---
2026-08-23 17:35:22 [andrew] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
2026-08-23 18:01:54 [andrew] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
```

### 最終状態
```
keeper.sh=1 ['40838']
ssh -N -L=0 []
syncthing=0 []
zzz_none=0 []
sshd=1 ['1']
tunnel_log=absent
syncthing_log=absent
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:54 /home/ubuntu/bin/syncthing
sync_pause=absent
untracked=4
 M tasks/T-2026-08-24-andrew-keeper-autosync/audit.md
?? .sync-pause.released
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? docs/sessions/digest/2026-08-23-5d62430b-7545-4769-a54e-673ea88fdc8d.md
```

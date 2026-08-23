# audit — T-2026-08-24-philip-keeper-autosync

実行ホスト: SERVERNAME=philip / hostname=aolab / JST 2026-08-24 02:18:59

## Phase A / Step 1: 開始状態を記録する

```
$ ls -la ~/bin/
total 26116
drwxrwxr-x 2 ubuntu ubuntu     4096 Aug 22 06:04 .
drwxr-x--- 1 ubuntu ubuntu     4096 Aug 23 17:18 ..
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 22 06:04 syncthing

$ ls -a ~/ | grep -i "^\.tunnel"
(grep exit=1 — 件数ではない)
marker_count=0
tunnel_any_count=0

$ grep -n "keeper\|nohup" ~/.zshrc
起動行なし
zshrc_exists=yes readable=yes lines=77

$ ls -la ~/.keeper.lock
ls: cannot access '/home/ubuntu/.keeper.lock': No such file or directory
lock なし

$ ls -la ~/claude-sync/ | head -3
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
claude_sync_exists=no readable=no

$ git --no-pager status --porcelain | grep -c ""
6

$ git --no-pager status -sb
## feat/philip-keeper-autosync...origin/phase0
?? data/annotations/_deprecated/
?? data/annotations/egosurgery_hts2_coverage_report.md
?? data/annotations/egosurgery_hts_current_coverage.md
?? data/annotations/egosurgery_hts_frame_coverage_report.md
?? docs/sessions/digest/2026-08-22-d0076c74-6667-46a0-95fb-96d9c1d68f8c.md
?? tasks/T-2026-08-24-philip-keeper-autosync/
$ git --no-pager log -1 --format="%h %s"
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
```

### 補足: 前契約の未追跡3件の現況（消失ではない）
```
experiments/transfer/_smoke_artifacts_ctrl: exists=yes tracked=no
.gitignore:174:experiments/transfer/_smoke_artifacts_ctrl/	experiments/transfer/_smoke_artifacts_ctrl
experiments/transfer/_smoke_artifacts_inj: exists=yes tracked=no
.gitignore:175:experiments/transfer/_smoke_artifacts_inj/	experiments/transfer/_smoke_artifacts_inj
experiments/transfer/_smoke_fullval: exists=yes tracked=no
.gitignore:176:experiments/transfer/_smoke_fullval/	experiments/transfer/_smoke_fullval
untracked_normal=6  untracked_with_ignored=1093
```

### 版管理が最新であることの確認
```
$ git fetch origin && git rev-list --left-right --count origin/phase0...HEAD
0	0
(左=behind 右=ahead)
## feat/philip-keeper-autosync...origin/phase0
```

## Phase A / Step 2: 稼働しているものを数える（対照つき）
```
keeper.sh=0
m2-sync=0
syncthing=0
ssh -N -L=0
zzz_none=0
```

#### 追加した陽性対照（申し送り #6: 対照は両方向で取る）
```
self_and_ancestors_excluded=15
proc_entries_total=38
systemd     =0 []
zsh         =4 ['47296', '47444', '53474', '67249']
keeper.sh   =0 []
m2-sync     =0 []
syncthing   =0 []
ssh -N -L   =0 []
zzz_none    =0 []
```

## Phase A / Step 3: 正本を読み、目印の分岐を確かめる
```
$ wc -l scripts/sync/keeper.sh; sha256sum scripts/sync/keeper.sh
52 scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
$ wc -l scripts/sync/m2-sync.sh; sha256sum scripts/sync/m2-sync.sh
133 scripts/sync/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
$ git show origin/phase0:scripts/sync/{keeper,m2-sync}.sh | sha256sum  （正本＝phase0 の一致確認）
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  -
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  -
$ grep -n -E "tunnel_to|22001|50072|m2-sync|sleep|flock" scripts/sync/keeper.sh
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
```

### 目印が無いとき、何が動き何が動かないか（実装の行番号）

| 行 | 実装 | 目印が無いときの挙動 |
|---|---|---|
| 7-23 | `resolve_tunnel()` — `~/.tunnel_to_*` を走査 | 該当なしで `return 1` |
| 25-26 | `exec 9>~/.keeper.lock` / `flock -n 9 \|\| exit 0` | **多重起動防止の錠。起動時に必ず作られる** |
| 28 | `M2DIR=` `~/slocal2` があれば `~/slocal2/m2` | philip は `~/slocal2/m2` |
| 33-38 | 中継 `ssh -N -L 22001:127.0.0.1:22000 -p 50072` | `resolve_tunnel` が偽なので **動かない** |
| 41-43 | `[ -x ~/bin/syncthing ] && ! pgrep -x syncthing` なら syncthing 起動 | **目印と無関係。実行権があれば起動する** |
| 45-46 | `~/bin/m2-sync.sh` を `origin/phase0` から自己更新 | 毎ループ動く |
| 48-49 | `.stglobalignore` → `$M2DIR/.stignore` | 毎ループ動く。`.stignore` は `.gitignore:192` で無視 |
| 50 | `~/bin/m2-sync.sh 9>&-` | 毎ループ動く（版管理の同期） |
| 51 | `sleep 1800` | 周期 1800 秒 |

**起票者の理解との食い違い（実装を正とする）**: SPEC の表は 39-50 行を「同期処理の監視、
除外規則の反映、版管理の同期」としてまとめ「これを動かす」としているが、41-43 行は
**目印とは無関係に syncthing を起動する**。philip では前契約で `~/bin/syncthing` が
mode 755 で配置済みのため、keeper を起動すると **禁止 2「同期処理を起動する」に触れる**。

## Phase A / Step 4: 版管理の同期の発火条件
```
$ grep -n -E "auto-merge|auto-push|pull request|sync-pause|SERVERNAME|sync-alerts|LOG" scripts/sync/m2-sync.sh
5:#   加えて、コミット済みで未 push のものを自分の作業ブランチへ送る（auto-push）
11:LOG=~/claude-sync/sync-alerts.log
14:# 稼働中の keeper は SERVERNAME を設定する前に起動していることがあり
15:# （例: ilya の PID 73082 は 2026-07-04 起動 / SERVERNAME 設定は 2026-08-02）、
18:SRV="${SERVERNAME:-}"
22:mkdir -p "$(dirname "$LOG")"
23:alert() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$SRV" "$1" >> "$LOG"; }
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

| 発火 | 条件（行） | philip の現況 |
|---|---|---|
| 記録の書き出し | `LOG=~/claude-sync/sync-alerts.log`（11）、`mkdir -p`（22） | **現在 `~/claude-sync/` は不在。m2-sync が自分で作る** |
| **抑止** | `[ -f "$M2DIR/.sync-pause" ]` なら記録して `exit 0`（40-43） | **fetch/merge/push の手前で抜ける** |
| auto-merge | 抑止なし かつ behind>0 かつ 追跡変更0件 かつ 未追跡が阻害しない（60-88） | 現在 behind=0 |
| auto-push | `BR != phase0` かつ **`origin/$BR` が存在** かつ ahead>0（103-112） | `origin/feat/philip-keeper-autosync` は **未登録 → 最初の push までは発火しない** |
| auto-PR | `gh` があるときのみ（115-）| `gh` の有無は Phase C で測る |
| `.sync-pause` の可視性 | `.gitignore:240` で無視。`.stignore` の総取りで同期外 | **この 1 台にだけ効く** |

## Phase B / Step 0: 禁止 2 を守るため syncthing の実行権を一時的に外す（ユーザー承認済み）
```
--- 変更前 ---
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
executable=yes
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
--- 変更後（chmod 644） ---
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 22 06:04 /home/ubuntu/bin/syncthing
executable=no
内容が変わっていないことを要約値で確認（申し送り #5）:
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
```

戻し方: `chmod 755 ~/bin/syncthing`。実体・設定・識別子には触れていない。

## Phase B / Task 2 Step 1: 置き場所を作り、配置する
```
$ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh scripts/sync/keeper.sh scripts/sync/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh

一致判定（要約値の突き合わせ。表示属性では足りない — 申し送り #5）:
keeper_match=yes
m2sync_match=yes
-rwxr-xr-x 1 ubuntu ubuntu 2709 Aug 23 17:27 /home/ubuntu/bin/keeper.sh
-rwxr-xr-x 1 ubuntu ubuntu 7342 Aug 23 17:27 /home/ubuntu/bin/m2-sync.sh
```

## Phase B / Task 2 Step 2: 構文を確かめる
```
keeper_syntax=0
m2sync_syntax=2
--- 追加: 正本は #!/bin/bash なので bash でも確かめる ---
keeper_syntax_bash=0
m2sync_syntax_bash=0
--- 陽性対照: 壊した写しが非零を返すこと（検査器が働いている証拠） ---
broken_syntax=2
```

## Phase B / Task 2 Step 3: 目印が無いことを確かめる
```
(grep exit=1 — 件数ではない)
marker_count=0
```

### 構文検査の食い違い（起票者の誤り: shell_assumption）
```
$ head -1 scripts/sync/m2-sync.sh ; head -1 scripts/sync/keeper.sh
#!/bin/bash
#!/bin/bash
/bin/sh の実体: /usr/bin/dash

$ sed -n "73,77p" scripts/sync/m2-sync.sh  （dash が拒否した箇所）
      # 事前に集合の積を取って判定する（rm はしない）。
      BLOCKED=$(comm -12 \
        <(git ls-files --others --exclude-standard | sort) \
        <(git ls-tree -r --name-only "origin/$MAIN" | sort) | wc -l | tr -d ' ')
      if [ "$BLOCKED" != "0" ]; then

$ sh -n ~/bin/m2-sync.sh  （再掲・全文）
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
exit=2
```

**判定**: 正本は `#!/bin/bash` であり、実際に起動するのも bash（keeper 50 行は
`~/bin/m2-sync.sh` を shebang 経由で呼ぶ）。`/bin/sh` は dash であり、
**契約 Task 2 Step 2 の `sh -n` は解釈系が違う**。したがって完了判定 6 は
`bash -n`（両方 0）を根拠とし、`sh -n` の非零は起票者の誤りとして記録する。
`sh -n` の陽性対照 `broken_syntax=2` により、検査器自体は働いている。

## Phase B / Task 2 Step 4: 抑止の目印を置く
```
$ ls -la .sync-pause
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:27 .sync-pause
$ grep -c "sync-pause" ~/bin/m2-sync.sh   （0 なら抑止未対応の版）
2
$ grep -n "sync-pause" ~/bin/m2-sync.sh
40:if [ -f "$M2DIR/.sync-pause" ]; then
41:  alert "一時停止中: $M2DIR/.sync-pause があるため分岐へ書き込まない（消せば再開）"

陰性対照: 存在しない語は 0 を返すこと
zzz_none_count=0

目印が版管理に現れないこと:
.gitignore:240:.sync-pause	.sync-pause
status_lines=6
```

## Phase B / Task 3 Step 1: 起動行を追記する
```
$ grep -n "keeper" ~/.zshrc   （該当があれば追記しない）
該当なし
keeper_lines_before=0
zshrc_lines_before=77
```
```
判定: 追記した

--- 追記した内容（そのまま） ---

# 常駐スーパーバイザ: 版管理の自動同期（flock で多重起動を防ぐため毎回呼んで安全）
# 設定: T-2026-08-24-philip-keeper-autosync (2026-08-24)
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null

keeper_lines_after=2
zshrc_lines_after=81
$ grep -n "keeper" ~/.zshrc
80:# 設定: T-2026-08-24-philip-keeper-autosync (2026-08-24)
81:( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
```

## Phase B / Task 3 Step 2-3: 起動し、一つだけ動いていることを確かめる
```
$ nohup ~/bin/keeper.sh >/dev/null 2>&1 &   → launched_pid=72428
keeper.sh =1 ['72428']
ssh -N -L =0 []
syncthing =0 []
m2-sync   =0 []
zsh       =4 ['47296', '47444', '53474', '67249']
zzz_none  =0 []
(zsh は陽性対照 / zzz_none は陰性対照)
```

## Phase B / Task 3 Step 4: 多重起動を防ぐ仕掛け
```
$ ls -la ~/.keeper.lock
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:28 /home/ubuntu/.keeper.lock

--- 陽性対照: 二つ目を起動すると片方が終わるか（実測） ---
second_launched_pid=72669
二つ目の起動後: keeper.sh=1 ['72428']
期待: 1（flock -n が取れず二つ目は exit 0 で去る）
```

## Phase B / Task 3 Step 5: 版管理の同期が一周し、抑止が効いていること
```
$ grep -n -E "sync-alerts|LOG=" ~/bin/m2-sync.sh | head -5   （記録の置き場所を実装から読む）
11:LOG=~/claude-sync/sync-alerts.log

$ ls -la ~/claude-sync/sync-alerts.log
-rw-rw-r-- 1 ubuntu ubuntu 146 Aug 23 17:28 /home/ubuntu/claude-sync/sync-alerts.log
claude_sync_exists=yes log_readable=yes
log_lines=1

$ tail -20 ~/claude-sync/sync-alerts.log
2026-08-23 17:28:56 [philip] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）

抑止が効いた記録の件数（終了コードではなく件数で数える — 申し送り #4）:
paused_lines=1
automerge_lines=0
UNKNOWN
autopush_lines=0
UNKNOWN

版管理への書き込みが起きていないこと:
$ git --no-pager status -sb
## feat/philip-keeper-autosync...origin/phase0
?? data/annotations/_deprecated/
?? data/annotations/egosurgery_hts2_coverage_report.md
?? data/annotations/egosurgery_hts_current_coverage.md
?? data/annotations/egosurgery_hts_frame_coverage_report.md
?? docs/sessions/digest/2026-08-22-d0076c74-6667-46a0-95fb-96d9c1d68f8c.md
?? tasks/T-2026-08-24-philip-keeper-autosync/
$ git --no-pager log -1 --format="%h %s"
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
ahead_behind=0	0  (左=behind 右=ahead)

除外規則の反映（keeper 48-49 行）:
ls: cannot access '.stignore.new': No such file or directory
-rw-rw-r-- 1 ubuntu ubuntu 2223 Aug 23 17:28 .stignore
stignore_sha=61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  -
stglobalignore_sha=61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  -
```

### 訂正: 上の件数測定に実行者の誤りがあった

`grep -c PATTERN FILE || echo UNKNOWN` は **該当 0 件のとき grep が exit 1 を返す**ため、
`0` と `UNKNOWN` の両方を出力していた。申し送り #4（終了コードを件数と呼ばない）
および #7（`||` は表示側の失敗も拾う）に該当する、実行者側の測り方の誤り。
「ファイルが読めない」と「該当 0 件」を区別する形で測り直す。

```
log_exists=yes
log_readable=yes
log_lines=1
paused_lines=1
automerge_lines=0
autopush_lines=0
fetch_fail_lines=0
陰性対照 zzz_none_lines=0
陽性対照 philip_lines=1
```

## Phase C / Task 4 Step 2: 送信前の秘匿検査（自分で行う）
```
走査対象: tasks/T-2026-08-24-philip-keeper-autosync/*.md *.yaml と tasks/inbox.d/<task_id>.md
hits=1
tasks/T-2026-08-24-philip-keeper-autosync/SPEC.md:319:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \

判定（件数ではなく形を一件ずつ見る）:
  1 件目 = SPEC.md 自身が載せている検査の正規表現。鍵の書き出し行でも、
           語に区切りと値が続く形でもない。秘匿ではないので削らない。

control_hits=3  （陽性対照。囮は /tmp のみに置き、削除済み。版管理へは入れない）
neg_hits=0      （陰性対照。無害な説明文）

環境の資格情報との直接照合（値は出力しない）:
  NOTION_API_KEY / WANDB_API_KEY / NOTION_DB_ID / GITHUB_TOKEN / GH_TOKEN = すべて unset。照合対象なし
```

**前契約での失敗を繰り返していない。** `T-2026-08-22-philip-hub-foundation` では
囮の原文を audit.md へ貼って commit に含めてしまった。今回は囮を `/tmp` にのみ置き、
記録には件数と形の説明だけを残した。

## Phase C / Task 4 Step 3: 検証を通す
```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b08
spec の conventions_rev:   conventions_rev: "d422b08"

$ make task-validate TASK=T-2026-08-24-philip-keeper-autosync
OK   T-2026-08-24-philip-keeper-autosync

1 task(s), 0 failed
validate_exit=

$ make forbidden-check
{"base": "origin/phase0", "changed": 11, "checked": 11, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "fail", "violations": [{"path": "data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md", "reason": "禁止領域 data/ の内側"}, {"path": "data/annotations/egosurgery_hts2_coverage_report.md", "reason": "禁止領域 data/ の内側"}, {"path": "data/annotations/egosurgery_hts_current_coverage.md", "reason": "禁止領域 data/ の内側"}, {"path": "data/annotations/egosurgery_hts_frame_coverage_report.md", "reason": "禁止領域 data/ の内側"}]}
make: *** [Makefile:151: forbidden-check] Error 1
forbidden_exit=
```

### 訂正: 終了コードの取り方に実行者の誤りがあった

`${PIPESTATUS[0]}` を使ったが **このシェルは zsh** であり、配列添字が効かず
空文字が出た。SPEC の「全台で確定した事実」と申し送り #8 が
「配列添字で終了コードを取らない」と警告していた罠に落ちた。
パイプを使わず、出力をファイルへ落として直後に `$?` を取る形で測り直した。

```
validate_exit=0
forbidden_exit=2
```

### forbidden-check の失敗内容
```
{"base": "origin/phase0", "changed": 11, "checked": 11, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "fail", "violations": [{"path": "data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md", "reason": "禁止領域 data/ の内側"}, {"path": "data/annotations/egosurgery_hts2_coverage_report.md", "reason": "禁止領域 data/ の内側"}, {"path": "data/annotations/egosurgery_hts_current_coverage.md", "reason": "禁止領域 data/ の内側"}, {"path": "data/annotations/egosurgery_hts_frame_coverage_report.md", "reason": "禁止領域 data/ の内側"}]}
```

| 違反 | tracked | staged | mtime |
|---|---|---|---|
| `data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md` | no | 0 | 2026-07-31 22:01 |
| `data/annotations/egosurgery_hts2_coverage_report.md` | no | 0 | 2026-07-31 11:35 |
| `data/annotations/egosurgery_hts_current_coverage.md` | no | 0 | 2026-07-31 11:35 |
| `data/annotations/egosurgery_hts_frame_coverage_report.md` | no | 0 | 2026-07-31 08:20 |

**判定**: 4 件はすべて **mtime 2026-07-31**、本契約の開始（2026-08-23 17:2x JST）より
約 3 週間前から存在する未追跡ファイルであり、Phase A Step 1 で記録した未追跡 6 件に
含まれている。**本契約が作ったものでも、触ったものでもない。** `git ls-files` で
tracked=no、`git diff --cached` で staged=0 を確認した。
`tools/check_forbidden.py` は `origin/phase0` を起点に**未追跡も含めて**列挙するため、
作業ツリーにこれらが在る限り必ず fail する。**禁止 5 が削除・移動・commit を禁じている**ので、
通すために消すことはしない。**記録するにとどめる。**

## Phase C / Task 4 Step 4: 変更範囲と未追跡を確かめる
```
$ git --no-pager status --porcelain
lines=7
?? data/annotations/_deprecated/
?? data/annotations/egosurgery_hts2_coverage_report.md
?? data/annotations/egosurgery_hts_current_coverage.md
?? data/annotations/egosurgery_hts_frame_coverage_report.md
?? docs/sessions/digest/2026-08-22-d0076c74-6667-46a0-95fb-96d9c1d68f8c.md
?? tasks/T-2026-08-24-philip-keeper-autosync/
?? tasks/inbox.d/T-2026-08-24-philip-keeper-autosync.md

開始時（Phase A Step 1）の未追跡 6 件がすべて残っているか:
  data/annotations/_deprecated/ : exists=yes
  data/annotations/egosurgery_hts2_coverage_report.md : exists=yes
  data/annotations/egosurgery_hts_current_coverage.md : exists=yes
  data/annotations/egosurgery_hts_frame_coverage_report.md : exists=yes
  docs/sessions/digest/2026-08-22-d0076c74-6667-46a0-95fb-96d9c1d68f8c.md : exists=yes
  tasks/T-2026-08-24-philip-keeper-autosync/ : exists=yes

版管理の外なので status に現れないもの（正しい挙動）:
  ~/bin/keeper.sh exists=yes
  ~/bin/m2-sync.sh exists=yes
  ~/.zshrc keeper 行数=2
  .sync-pause は .gitignore:240 で無視 / .stignore は .gitignore:192 で無視
```

### 追加測定: 抑止を外したあと auto-merge が阻害されないか

`m2-sync.sh` 73-78 行は、未追跡のうち **`origin/phase0` のツリーにも在るもの** を
`BLOCKED` として数え、1 件以上なら auto-merge を skip する
（`git merge --ff-only` が内容同一でも未追跡の上書きを拒むため）。実際に同じ式で測る。
```
$ comm -12 <(git ls-files --others --exclude-standard | sort) <(git ls-tree -r --name-only origin/phase0 | sort) | wc -l
BLOCKED=0

内訳（0 件なら空）:

陽性対照: 集合の積が働いていることを確かめる（追跡済みの既知ファイルを左側に混ぜる）
control=1  (1 が期待)
陰性対照=0  (0 が期待)
```

**判定**: `BLOCKED=0`。抑止を外したあと、未追跡が auto-merge を阻害することはない。

## Phase C / Task 4 Step 5: commit し、送出する
```
$ git --no-pager diff --cached --name-only  （commit 前の staged）
tasks/T-2026-08-24-philip-keeper-autosync/{RESULT.md,SPEC.md,audit.md,result.yaml,spec.yaml}
tasks/inbox.d/T-2026-08-24-philip-keeper-autosync.md
data_staged=0 experiments_staged=0 runindex_staged=0 context_auto_staged=0 inbox_md_staged=0

commit_exit=0
6f5e7af feat(sync): deploy keeper and enable git autosync on philip

$ git remote -v
origin	https://github.com/takuya3h/m2.git (fetch)
origin	https://github.com/takuya3h/m2.git (push)

$ git push -u origin HEAD
 * [new branch]      HEAD -> feat/philip-keeper-autosync
branch 'feat/philip-keeper-autosync' set up to track 'origin/feat/philip-keeper-autosync'.
push_exit=0

$ gh auth status   （トークンの値は出力しない）
github.com / Logged in to github.com account takuya3h / Active account: true
Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'
auth_exit=0

$ gh pr list --head feat/philip-keeper-autosync --json number,isDraft,state
[]   （作成前）

$ gh pr create --base phase0 --head feat/philip-keeper-autosync ...
https://github.com/takuya3h/m2/pull/126
pr_exit=0
```

`git remote set-url --push origin https://...` と `gh auth setup-git` は**実行していない**。
送出先は既に `https://github.com/takuya3h/m2.git` であり、`git@` ではないため配備鍵が不要で、
push が `exit=0` で通ったため。

## Phase C / Task 4 Step 6: 抑止を外す
```
$ ls -la .sync-pause   （解除前）
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:27 .sync-pause
$ mv .sync-pause /tmp/.sync-pause.released.T-2026-08-24-philip-keeper-autosync
mv_exit=0
$ ls -la .sync-pause   （解除後）
repo 直下から消えた
退避先: -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:27 /tmp/.sync-pause.released.T-2026-08-24-philip-keeper-autosync

解除後も常駐処理は生きている:
keeper.sh =1 [72428]
ssh -N -L =0 []
syncthing =0 []
```

**削除ではなく別名への退避で解除した。** 実装は目印の存在だけを見ている
（`m2-sync.sh` 40 行 `[ -f "$M2DIR/.sync-pause" ]`）ため、移動でも解ける。
次の周回（起動から 1800 秒後、およそ 17:58 JST）から auto-merge と auto-push が働く。
`origin/feat/philip-keeper-autosync` が登録されたので auto-push の条件（103 行）も満たされた。

## Phase C: 記録の追記後に、秘匿と検証を測り直す
```
validate_exit=0   （OK / 1 task(s), 0 failed）

hits=4  （追記により 1 → 4 へ増えたので一件ずつ形を見る）
  1. audit.md:367  — SPEC.md の検査の正規表現を引用した行。秘匿ではない
  2. audit.md:377  — 環境変数の**名前**と「すべて unset」の記載。値は無い
  3. SPEC.md:319   — 起票者が書いた検査の正規表現そのもの
  4. RESULT.md:80  — 完了判定 15 の本文。変数名のみで値は無い
  → 鍵の書き出し行は無し。語＋区切り＋値の形は無し。削る対象は無い

gho_token_leak=0  （gh のトークンは gh 自身が伏せて出力し、こちらも記録していない）
```

**前契約の失敗（囮を版管理へ入れた）を再発させないため、追記のたびに測り直した。**

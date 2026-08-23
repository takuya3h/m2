# audit — T-2026-08-24-lecun-keeper-autosync

- host: `lecun`（`hostname` = `lecun`、`SERVERNAME` = `lecun`）
- repo: `/home/ubuntu/slocal/m2`（SPEC の記載と一致）
- 実行日: 2026-08-23 (JST)

---

## 版管理が最新であることの確認

```
$ git --no-pager status --porcelain | grep -c ''
4
$ git branch --show-current
feat/lecun-keeper-autosync
$ git fetch origin
（出力なし）
$ git --no-pager log -1 --format='%h %s'
3c4c5a60 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
$ git --no-pager log -1 --format='%h %s' origin/phase0
3c4c5a60 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
$ git --no-pager rev-list --left-right --count origin/phase0...HEAD
0	0
```

**HEAD と `origin/phase0` が同一で最新。** 分岐 `feat/lecun-keeper-autosync` は
既に存在し、`origin/phase0` と同じ先頭を指していたため**新規に切っていない**。

前契約の PR #122 は統合済み（`{"mergedAt":"2026-08-23T16:51:23Z","state":"MERGED"}`）。
`origin/phase0` には他台の基盤契約も入っている（#124 ilya、#125 andrew）。

---

## Phase A / Task 1 Step 1: 開始状態

### `ls -la ~/bin/`

```
total 26116
drwxrwxr-x 2 ubuntu ubuntu     4096 Aug 23 13:25 .
drwxr-x--- 1 ubuntu ubuntu     4096 Aug 23 17:24 ..
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:25 syncthing
```

**`~/bin/` は在り、前契約で置いた `syncthing` が一つだけ入っている。**
`keeper.sh` と `m2-sync.sh` は**無い**。

### 目印

```
$ ls -a ~/ | grep -i "^\.tunnel"
（該当なし）
$ echo "marker_count=$(ls -a ~/ | grep -c '^\.tunnel_to_')"
marker_count=0
```

**零件。** `.tunnel_to_` で数えた（`tunnel` だけで数えると記録の類まで拾うため）。

### `~/.zshrc` の起動行

```
$ grep -n "keeper\|nohup" ~/.zshrc
（該当なし）
```

**起動行は無い。** 全台で失われているという事実は lecun でも成立する。

### 錠と記録領域

```
$ ls -la ~/.keeper.lock
ls: cannot access '/home/ubuntu/.keeper.lock': No such file or directory
$ ls -la ~/claude-sync/
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
```

**どちらも無い。**「読めない」ではなく「無い」（親ディレクトリの一覧は成功している）。

### 未追跡・変更

```
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/hosts/
?? tasks/T-2026-08-24-lecun-keeper-autosync/
```

`porcelain_count_start=4`（うち 1 件は本契約の配置ディレクトリ。
**契約由来を除く既存の未追跡は 3 件**で、前契約の開始時と同じ 3 件である）。

---

## Phase A / Task 1 Step 2: 稼働しているものの計数

### 契約が指示した形（負の対照のみ）

```
keeper.sh=0
m2-sync=0
syncthing=0
ssh -N -L=0
zzz_none=0
```

### 両方向の対照（申し送り #6「対照は両方向で取る」に従い追加）

**存在しない語が零を返すことは「偽陽性が無い」ことしか示さない。**
**計数器が検出できることを別に示す必要がある。** 実在する語を足して測った。

```
self_and_ancestors=15
keeper.sh=0 []
m2-sync=0 []
syncthing=0 []
ssh -N -L=0 []
zzz_none=0 []
zsh=1 ['75912']
node=6 ['61592', '61728', '61779', '61844', '61872']
```

**負の対照 `zzz_none=0`、正の対照 `zsh=1` / `node=6`。**
計数器は検出でき、かつ偽陽性を出さない。**よって対象 4 語は真に零件である。**
自身と祖先 15 件を除外しているため、検索命令自身には一致していない。

---

## Phase A / Task 1 Step 3: 正本の要約値と、目印による分岐

```
$ wc -l scripts/sync/keeper.sh
52 scripts/sync/keeper.sh
$ sha256sum scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
$ wc -l scripts/sync/m2-sync.sh
133 scripts/sync/m2-sync.sh
$ sha256sum scripts/sync/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
```

### `grep -n -E "tunnel_to|22001|50072|m2-sync|sleep|flock" scripts/sync/keeper.sh`

```
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

### 実装の行ごとの働き（`cat -n` で全文を読んだ結果）

| 行 | 働き | 目印が無いとき |
|---|---|---|
| 7〜23 | `resolve_tunnel()`。`~/.tunnel_to_*` を辞書順に一つ選ぶ | 候補が無く `return 1`（15 行） |
| 25 | `exec 9>~/.keeper.lock`。錠のファイルを開く | 実行される |
| 26 | `flock -n 9 \|\| exit 0`。多重起動を防ぐ | 実行される |
| 28 | `M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 \|\| echo ~/slocal/m2)` | lecun は `~/slocal2` が無いので `~/slocal/m2` |
| 30 | `while true; do` | — |
| 33〜38 | **中継**。`resolve_tunnel` が偽なら短絡して張らない | **動かない** |
| 41〜43 | **同期処理の起動**。`[ -x ~/bin/syncthing ] && ! pgrep -x syncthing` | **動く**（下記） |
| 45〜46 | `~/bin/m2-sync.sh` を `origin/phase0` から自己更新 | 動く |
| 48〜49 | `.stglobalignore` を `$M2DIR/.stignore` へ反映 | 動く |
| 50 | `~/bin/m2-sync.sh 9>&-` を実行 | 動く |
| 51 | `sleep 1800 9>&-` | 動く |

**起票者の理解との食い違いを次節に記す。**

---

## 🔴 起票者の理解と実装の食い違い（Task 1 Step 3 の指示に従い、実装を正として報告する）

SPEC の Goal は分岐を次のように書いている。

| 分岐 | SPEC の記載する実装の位置 | SPEC の記載する扱い |
|---|---|---|
| 目印があるときだけ中継を維持 | **三十一から三十八行** | 目印を置かないので動かない |
| 同期処理の監視、除外規則の反映、版管理の同期 | **三十九から五十行** | **これを動かす** |

**「三十九から五十行」には、同期処理を起動する 41〜43 行が含まれている。**

```
41	  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
42	    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
43	  fi
```

**この行は「監視」ではなく「起動」である。** 6 行目の役割説明も
`(1) syncthing の起動・死活監視` と書いている。

### lecun では両方の条件が成立する（実測）

```
$ ls -la ~/bin/syncthing
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:25 /home/ubuntu/bin/syncthing
$ test -x ~/bin/syncthing && echo TRUE || echo FALSE
TRUE
$ pgrep -x syncthing
pgrep_exit=1   （未稼働）
```

**`-x` が真、`pgrep -x` が偽。よって 42 行が発火する。**
`~/bin/syncthing` は**前契約 `T-2026-08-22-lecun-node-foundation` が置いたもの**である。

### これが破る契約の条項

| 条項 | 内容 |
|---|---|
| 禁止 2 | **同期処理を起動する**（識別子の登録が済んでいない） |
| 完了判定 11 | **中継が零件、同期処理が零件** |
| Gate G2 | 常駐処理が一件だけ動き、**中継と同期処理が零件である** |
| escalate_if | **同期処理が意図せず起動した場合** |

**目印が無ければ中継は起きない**（33 行が短絡する）ことは実装で確かめた。
**しかし同期処理は目印と無関係に起動する。** 目印が制御するのは中継だけである。

**契約が「目印が無ければ中継を起こさず、版管理の同期だけを行う」と述べる前提は、
`~/bin/syncthing` が置かれていないホストでのみ成立する。**
lecun では前契約がそれを置いたため成立しない。

---

## Phase A / Task 1 Step 4: 版管理の同期の発火条件

### `grep -n -E "auto-merge|auto-push|pull request|sync-pause|SERVERNAME" scripts/sync/m2-sync.sh`

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

### 記録の置き場所

```
11:LOG=~/claude-sync/sync-alerts.log
22:mkdir -p "$(dirname "$LOG")"
23:alert() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$SRV" "$1" >> "$LOG"; }
```

**`~/claude-sync/sync-alerts.log` へ書く。** 22 行で親ディレクトリを自分で作るため、
現在 `~/claude-sync/` が無くても初回実行で作られる。**`UNKNOWN` にする必要はない。**

### 発火条件

| 条件 | 実装 | 効果 |
|---|---|---|
| **抑止** | 40〜41 行。`$M2DIR/.sync-pause` が在れば記録だけ残して分岐へ書き込まない | **本契約で置く** |
| auto-merge | 60〜84 行。`origin/phase0` の更新を作業分岐へ統合する | 抑止中は動かない |
| auto-push | 90〜107 行。commit 済みで未 push のものを送る | 抑止中は動かない |

```
$ grep -c "sync-pause" scripts/sync/m2-sync.sh
（Task 2 Step 4 で配置物に対して測る）
```

**正本は抑止に対応している**（40 行に `.sync-pause` の判定がある）。

---

## Gate G1 — 通過

| 判定 | 実測 |
|---|---|
| 版管理が最新であることを確かめた | `HEAD = origin/phase0 = 3c4c5a60`、`rev-list --left-right --count` が `0 0` |
| 目印の件数と起動行の有無と未追跡の件数を記録した | `marker_count=0` / `~/.zshrc` に該当なし / `porcelain_count_start=4`（契約由来 1 件を含む） |
| 稼働しているものを対照つきで数えた | 対象 4 語すべて `0`。負の対照 `zzz_none=0`、正の対照 `zsh=1` `node=6` |
| 目印による分岐の範囲を行番号つきで記録した | 中継は 33〜38 行（`resolve_tunnel` が 15 行で `return 1` するため短絡）。**同期処理の起動は 41〜43 行で、目印と無関係に発火する** |
| 版管理の同期の発火条件を読んだ | 抑止 40〜41 行、auto-merge 60〜84 行、auto-push 90〜107 行。記録は `~/claude-sync/sync-alerts.log`（22 行で親を作る） |

**ただし Phase B へ進むと禁止 2 に触れる。** 次節の判断が要る。

---

## 判断（ユーザーへ提示して決めた）

Phase A の読解で、**契約の前提と実装が食い違い、Phase B へ進むと禁止 2 に触れる**ことが
分かったため、実行前にユーザーへ三案を提示した。

| 案 | 内容 |
|---|---|
| A | `~/bin/syncthing` の実行属性を外し、keeper 41 行の `[ -x ]` を偽にして同期処理の起動だけを止める |
| B | 契約どおり無改変で起動し、同期処理が起動することを記録して報告する |
| C | Phase B を実行せず差し戻す |

**ユーザーは A を選んだ。** 以下はその判断にもとづく。

---

## Phase B / Task 2 Step 1: 正本の配置

### 作業ツリーが正本と同一であることの確認

keeper.sh の 3 行目は `git show origin/phase0:...` からの展開を推奨している。
SPEC は作業ツリーからの複写を指示するため、**両者が同一であることを先に確かめた。**

```
$ git --no-pager show origin/phase0:scripts/sync/keeper.sh | sha256sum
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  -
$ git --no-pager show origin/phase0:scripts/sync/m2-sync.sh | sha256sum
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  -
$ sha256sum scripts/sync/keeper.sh scripts/sync/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
```

**HEAD が `origin/phase0` と同一のため一致する。** 複写元として等価である。

### 配置と照合

```
$ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh scripts/sync/keeper.sh scripts/sync/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh

$ ls -la ~/bin/
-rwxr-xr-x 1 ubuntu ubuntu     2709 Aug 23 17:31 keeper.sh
-rwxr-xr-x 1 ubuntu ubuntu     7342 Aug 23 17:31 m2-sync.sh
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:25 syncthing
```

**四つの要約値が二対で一致した。**

---

## 🔴 Phase B / Task 2 Step 2: 構文検査 — 契約の検査が対象を検査していない

SPEC は `sh -n` を指示する。**そのとおり実行すると m2-sync.sh が非零を返す。**

```
$ sh -n ~/bin/keeper.sh; echo "keeper_syntax=$?"
keeper_syntax=0
$ sh -n ~/bin/m2-sync.sh; echo "m2sync_syntax=$?"
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
m2sync_syntax=2
```

**しかしこれは検査器の誤りである。**

```
$ head -1 ~/bin/keeper.sh
#!/bin/bash
$ head -1 ~/bin/m2-sync.sh
#!/bin/bash
$ ls -la /bin/sh
lrwxrwxrwx 1 root root 4 Mar 31  2024 /bin/sh -> dash
```

75 行はプロセス置換を使っており、**bash の構文であって dash の構文ではない。**

```
$ sed -n '73,76p' ~/bin/m2-sync.sh
      # 事前に集合の積を取って判定する（rm はしない）。
      BLOCKED=$(comm -12 \
        <(git ls-files --others --exclude-standard | sort) \
        <(git ls-tree -r --name-only "origin/$MAIN" | sort) | wc -l | tr -d ' ')
```

**shebang に合わせた検査器で測り直した。**

```
$ bash -n ~/bin/keeper.sh; echo "keeper_bash_syntax=$?"
keeper_bash_syntax=0
$ bash -n ~/bin/m2-sync.sh; echo "m2sync_bash_syntax=$?"
m2sync_bash_syntax=0
```

**両方とも零。** 実行時に使われるのは shebang の `/bin/bash` であるため、
**こちらが「構文誤りのまま起動すると常駐処理が即座に落ちる」を防ぐ検査である。**

### 陽性対照（検査が働いていることの確認）

`~/bin/keeper.sh` の写しの末尾に閉じない `if` を足した囮を版管理の外に置いた。

```
$ bash -n <囮>
<囮>: line 54: syntax error: unexpected end of file
broken_bash_syntax=2
$ bash -n ~/bin/keeper.sh; echo $?
0
$ bash -n ~/bin/m2-sync.sh; echo $?
0
```

**囮では 2、正本では 0。検査は素通しではない。** 囮は版管理へ入れていない。

---

## Phase B / Task 2 Step 3: 目印

```
$ ls -a ~/ | grep '^\.tunnel_to_'
（該当なし）
$ echo "marker_count=$(ls -a ~/ | grep -c '^\.tunnel_to_')"
marker_count=0
```

**零件。作っていない**（禁止 1）。

---

## Phase B / Task 2 Step 4: 抑止

```
$ touch .sync-pause && ls -la .sync-pause
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:32 .sync-pause
$ grep -c "sync-pause" ~/bin/m2-sync.sh
2
$ grep -n "sync-pause" ~/bin/m2-sync.sh
40:if [ -f "$M2DIR/.sync-pause" ]; then
41:  alert "一時停止中: $M2DIR/.sync-pause があるため分岐へ書き込まない（消せば再開）"
```

**零ではない（2 件）。抑止に対応している版である。**

---

## Phase B: 同期処理の起動を止める措置（案 A）

**契約に無い操作であり、逸脱として記録する。** ユーザーの承認を得て行った。

```
=== 変更前
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:25 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
test -x => TRUE

$ chmod 644 ~/bin/syncthing

=== 変更後
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:25 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
test -x => FALSE
```

**要約値は変更前後で同一** `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`。
**中身は触れておらず、実行属性だけを落とした**（申し送り #5 に従い、表示属性ではなく要約値で確かめた）。

これにより keeper 41 行の `[ -x ~/bin/syncthing ]` が偽になり、42 行は発火しない。

🔴 **次の契約（登録と起動）では `chmod 755 ~/bin/syncthing` で戻す必要がある。**

---

## 🔴 Phase B / Task 3: 実行できなかった

**起動行の追記と常駐処理の起動が、実行基盤の権限判定により拒否された。**

| 操作 | 結果 |
|---|---|
| `~/.zshrc` への追記（`cat >>` による追記） | **拒否**（Blocked by classifier） |
| `~/.zshrc` への追記（編集道具による追記） | **拒否**（Blocked by classifier） |
| `nohup ~/bin/keeper.sh >/dev/null 2>&1 &` | **拒否**（Blocked by classifier） |

**契約の誤りではない。実行基盤の制約である。**
起動していないため、判定 10〜13 は測れていない。

### 追記しようとした内容（他台で同じものを使う）

```
# >>> m2 keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< m2 keeper <<<
```

`~/.zshrc` の現在の行数は 77。`grep -c 'keeper' ~/.zshrc` は **0**（既存の起動行は無い）。

### 起動前の状態（変わっていないこと）

```
$ ls -la ~/.keeper.lock
ls: cannot access '/home/ubuntu/.keeper.lock': No such file or directory
$ ls -la ~/claude-sync/
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
```

---

## Phase B / Task 3 Step 1: 起動行の追記（ユーザーがセッション内で実行）

**実行基盤の分類器が実行者による `~/.zshrc` の書き換えを拒否したため、
ユーザーが同じセッション内で実行した。出力をそのまま貼る。**

```
$ printf '\n# >>> m2 keeper >>>\n( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null\n# <<< m2 keeper <<<\n' >> ~/.zshrc; echo "append_exit=$?"; grep -n -B1 -A2 "m2 keeper" ~/.zshrc; echo "keeper_hits=$(grep -c 'bin/keeper.sh' ~/.zshrc)"; echo "lines=$(grep -c '' ~/.zshrc)"
append_exit=0
78-
79:# >>> m2 keeper >>>
80-( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
81:# <<< m2 keeper <<<
keeper_hits=1
lines=81
```

**追記した内容（他台で同じものを使う）:**

```
# >>> m2 keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< m2 keeper <<<
```

**`~/.zshrc` は 77 行から 81 行へ増えた**（空行 1 + 標識 2 + 起動行 1）。
**`grep -c 'bin/keeper.sh'` は 1。二重に起動する行は無い。**
追記前の実測は `grep -c 'keeper' ~/.zshrc` が **0** であり、既存の起動行は無かった。
**したがって「該当があれば追記しない」の条件には当たらず、追記が正しい。**

---

## Phase B / Task 3 Step 2・4・5: 起動と、錠と記録（ユーザーがセッション内で実行）

**実行基盤の分類器が実行者による常駐処理の起動を拒否したため、
ユーザーが同じセッション内で実行した。出力をそのまま貼る。**

```
$ cd ~/slocal/m2 && nohup ~/bin/keeper.sh >/dev/null 2>&1 & sleep 8; echo "--- lock:"; ls -la ~/.keeper.lock 2>&1; echo "--- log:"; ls -la ~/claude-sync/sync-alerts.log 2>&1; echo "--- tail:"; tail -20 ~/claude-sync/sync-alerts.log 2>&1
--- lock:
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:53 /home/ubuntu/.keeper.lock
--- log:
-rw-rw-r-- 1 ubuntu ubuntu 144 Aug 23 17:53 /home/ubuntu/claude-sync/sync-alerts.log
--- tail:
2026-08-23 17:53:11 [lecun] 一時停止中: /home/ubuntu/slocal/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
```

### 読み取れること

| 項目 | 実測 |
|---|---|
| **多重起動を防ぐ錠**（判定 12） | `~/.keeper.lock` が生成された。起動前は `No such file or directory` だった。keeper.sh 25 行 `exec 9>~/.keeper.lock` が働いた |
| **記録の置き場所** | `~/claude-sync/sync-alerts.log`（144 バイト）。起動前は `~/claude-sync/` ごと無かった。m2-sync.sh 22 行 `mkdir -p "$(dirname "$LOG")"` が親を作った |
| **版管理の同期が一周した**（判定 13） | 記録に 1 行だけ出ている。`~/bin/m2-sync.sh` が実行され、40 行の判定に入った |
| **抑止が効いている**（判定 13） | 記録の内容が `一時停止中: … .sync-pause があるため分岐へ書き込まない`。m2-sync.sh 41 行の文言そのもの。**auto-merge も auto-push も記録に出ていない** |
| 論理名が届いている | 記録の `[lecun]` は `SRV="${SERVERNAME:-}"`（m2-sync.sh 18 行）の値。前契約で設定した論理名が常駐処理まで届いている |

**記録が 1 行だけであることが、抑止が効いた証拠である。**
抑止が無ければ 40 行の分岐を抜けて 60 行以降の auto-merge / auto-push へ進み、
`auto-merge:` か `auto-push:` の行が出るか、あるいは behind/ahead が 0 のため
何も出ないかのいずれかになる。**「一時停止中」は抑止の経路でしか出ない文言である。**

---

## Phase B / Task 3 Step 3: 稼働数の計数（ユーザーがセッション内で実行）

```
$ cd ~/slocal/m2 && .venv/bin/python -c "…（自身と祖先を除外して /proc/*/cmdline を走査）"; git --no-pager status -sb | head -3; git --no-pager log -1 --format='%h %s'
keeper.sh=1 ['89614']
ssh -N -L=0 []
syncthing=0 []
zzz_none=0 []
zsh=2 ['75912', '82916']
## feat/lecun-keeper-autosync...origin/phase0
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
3c4c5a60 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
```

| 項目 | 実測 | 判定 |
|---|---|---|
| **常駐処理**（判定 10） | `keeper.sh=1` **PID 89614** | 一件だけ動いている |
| **中継**（判定 11） | `ssh -N -L=0` | 零件。目印が無いため 33 行が短絡した |
| **同期処理**（判定 11） | `syncthing=0` | 零件。実行属性を外したため 41 行の `[ -x ]` が偽 |
| 負の対照 | `zzz_none=0` | 偽陽性を出さない |
| 正の対照 | `zsh=2` | 検出能力は働いている |

**両方向の対照が取れているため、`ssh -N -L=0` と `syncthing=0` は真に零件である。**
自身と祖先を除外しているため、検索命令自身には一致していない。

### 版管理が動いていないこと

```
## feat/lecun-keeper-autosync...origin/phase0
3c4c5a60 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
```

**`[ahead N]` も `[behind N]` も付いていない。** 分岐の先頭は起動前と同じ `3c4c5a60` のまま。
**未追跡も減っていない**（`docs/sessions/digest/*` の 2 件が引き続き見えている）。
**抑止が効いており、auto-merge も auto-push も起きていない。**

---

## Phase B: 錠が実際に多重起動を防ぐことの確認（陽性対照）

**錠のファイルが在ることは、錠が保持されていることを意味しない。** 別に測った。

```
$ flock -n ~/.keeper.lock -c 'echo acquired'
flock_exit=1        （取得できない = keeper が保持中）

$ : > <空の錠>; flock -n <空の錠> -c 'echo acquired'
acquired
flock_exit=0        （取得できる = 検査は素通しではない）
```

**keeper が保持している錠は取得できず、誰も持っていない錠は取得できた。**
**よって keeper.sh 26 行の `flock -n 9 || exit 0` は実際に働き、二重起動は防がれる。**

---

## Gate G2 — 通過

| 判定 | 実測 |
|---|---|
| 配置物と正本の要約値が一致 | `9fe9c423…dd90`（keeper）と `bcf46ba9…b25f`（m2-sync）が `~/bin/` と `scripts/sync/` の二対で一致 |
| 構文検査が通った | `bash -n` で両方 `0`（shebang が `#!/bin/bash` のため。SPEC の `sh -n` は dash で誤って `2` を返す） |
| 常駐処理が一件だけ動く | `keeper.sh=1` **PID 89614** |
| 中継と同期処理が零件 | `ssh -N -L=0` / `syncthing=0`（負の対照 `zzz_none=0`、正の対照 `zsh=2`） |
| 多重起動を防ぐ錠が作られた | `~/.keeper.lock` 生成。`flock -n` が `1` を返し**保持中であることまで確かめた** |
| 版管理の同期が一周し抑止が効いている | `~/claude-sync/sync-alerts.log` に `一時停止中: … .sync-pause があるため分岐へ書き込まない` の 1 行のみ。先頭は `3c4c5a60` のまま |

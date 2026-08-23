# audit.md — T-2026-08-24-ilya-keeper-autosync

実行ホスト: ilya / repo: `~/slocal2/m2` / 実行日: 2026-08-23 (JST)

出力は要約せず貼る（起票者の申し送り 9）。

---

## 手順 2: 検証（L1 + L2）

```
$ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-ilya-keeper-autosync
OK   T-2026-08-24-ilya-keeper-autosync

1 task(s), 0 failed
validate_exit=0
```

## 手順 3: 参照の解決

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b08
$ grep conventions_rev tasks/T-2026-08-24-ilya-keeper-autosync/spec.yaml
  conventions_rev: "d422b08"
```

実測 `d422b08` と spec の記載が一致。置換は不要（SPEC「実行者が実測して置換する」）。

`inject_verbatim: [conventions#prohibitions]` の原文は RESULT.md §1 に貼る。

## 手順 4: L3 プリフライト

```
$ source .venv/bin/activate && make task-preflight TASK=T-2026-08-24-ilya-keeper-autosync
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-24-ilya-keeper-autosync/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 4 件が該当: separated_source@tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md:329, separated_source@tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md:332, separated_source@tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md:335, host_mismatch@tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md:5（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
```

WARN 4 件の中身を確かめた。

```
$ sed -n '5p;329p;332p;335p' tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md
**実行ホスト:** `ilya`  **repo:** `~/slocal2/m2`
    source .venv/bin/activate \
    source .venv/bin/activate \
    source .venv/bin/activate \
$ hostname
aolab
```

`host_mismatch` は検査器が `socket.gethostname()` を見るが全台が `aolab` を返すため
論理名 ilya と一致しない。`separated_source` は行継続の `\` を伴う 3 行。
いずれも検査器の限界であり起票者の誤りではない（前契約と同じ判定）。

SKIP は P2 P3 P4 P5 の 4 件。

---

## Phase A / Task 1

### Step 0: 版管理を最新にする

```
$ cd ~/slocal2/m2 && git fetch origin && git --no-pager log -1 --format='%h %s'
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
$ echo "HEAD=$(git rev-parse --short HEAD) origin/phase0=$(git rev-parse --short origin/phase0)"
HEAD=3c4c5a6 origin/phase0=3c4c5a6
$ git branch --show-current
feat/ilya-keeper-autosync
```

HEAD と origin/phase0 が一致。分岐は既に切られていた。

### Step 1: 開始状態を記録する

```
$ ls -la ~/bin/ 2>&1 || echo "bin なし"
total 26116
drwxrwxr-x 2 ubuntu ubuntu     4096 Aug 23 13:53 .
drwxr-x--- 1 ubuntu ubuntu     4096 Aug 23 17:20 ..
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:53 syncthing
$ ls -a ~/ | grep -i "^\.tunnel" ; echo "marker_count=$(ls -a ~/ | grep -c '^\.tunnel_to_')"
marker_count=0
$ grep -n "keeper\|nohup" ~/.zshrc 2>&1 || echo "起動行なし"
起動行なし
$ ls -la ~/.keeper.lock 2>&1 || echo "lock なし"
ls: cannot access '/home/ubuntu/.keeper.lock': No such file or directory
lock なし
$ ls -la ~/claude-sync/ 2>&1 | head -3 || echo "同期領域なし"
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
$ git --no-pager status --porcelain | grep -c ''
3
$ git --no-pager status --porcelain
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
?? docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md
?? tasks/T-2026-08-24-ilya-keeper-autosync/
```

**申し送り 2（無いことと読めないことを区別する）に従って確かめ直した。**

```
$ ls -la ~/.zshrc 2>&1
-rw-rw-r-- 1 ubuntu ubuntu 2116 Aug 23 14:48 /home/ubuntu/.zshrc
$ echo "zshrc_exists=$(test -f ~/.zshrc && echo yes || echo no) readable=$(test -r ~/.zshrc && echo yes || echo no)"
zshrc_exists=yes readable=yes
$ echo "zshrc_lines=$(grep -c '' ~/.zshrc 2>/dev/null || echo NA)"
zshrc_lines=77
$ echo "keeper_hits=$(grep -c 'keeper' ~/.zshrc 2>/dev/null || echo NA)"
keeper_hits=0
NA
$ echo "nohup_hits=$(grep -c 'nohup' ~/.zshrc 2>/dev/null || echo NA)"
nohup_hits=0
NA
$ test -e ~/claude-sync && echo "claude-sync exists" || echo "claude-sync absent"
claude-sync absent
$ test -e ~/.keeper.lock && echo "lock exists" || echo "lock absent"
lock absent
```

**自分の命令の欠陥を記録する。** `grep -c` は該当が零のとき終了コード 1 を返すため、
`|| echo NA` が発火して `0` の直後に `NA` が出た。**件数は先に出た `0` が正しい。**
これは申し送り 4（終了コードを件数と呼ばない）と 7（`&&`/`||` は表示側の失敗も拾う）
がまさに指す形であり、起票者の雛形どおりに書いても起きる。

確定した開始状態:

| 項目 | 実測値 |
|---|---|
| `~/bin/` の中身 | `syncthing` のみ（26730145 バイト、755、前契約で配置） |
| 中継の目印 `.tunnel_to_*` | **0 件** |
| `~/.zshrc` の起動行 | **無し**（ファイルは存在・可読・77 行、`keeper` 0 件 `nohup` 0 件） |
| `~/.keeper.lock` | **不在**（読めないのではなく No such file） |
| `~/claude-sync/` | **不在**（同上） |
| 版管理の未追跡 | **3 件**（内訳は上記） |

### Step 2: 稼働しているものを数える（対照つき）

```
$ .venv/bin/python - <<'PY' ... PY
keeper.sh=0
m2-sync=0
syncthing=0
ssh -N -L=0
zzz_none=0
```

**申し送り 6（対照は両方向で取る）に従い、陽性側も取った。**
起票者の雛形の対照は「存在しない語 → 0」の一方向しかなく、
**計数が壊れていても同じ 0 を返す。** 実在する語で 1 以上が出ることを確かめた。

```
$ .venv/bin/python - <<'PY' ... PY
self_chain_pids=[4355, 4366, 4367, 4369, 4387, 4440, 4444, 4628, 4941, 7097, 7098, 7099, 35000, 40896, 40898]
CONTROL systemd=0 []
CONTROL sshd=1 ['1']
CONTROL zzz_none_should_be_zero=0 []
```

`sshd` が pid 1 で 1 件返った。**計数方法は実在するものを拾える。**
`systemd=0` はこの環境の PID 1 が systemd ではなく sshd であることを示す
（keeper.sh の冒頭「cron/systemd の無いコンテナ環境用」と整合）。

**開始時、対象 5 種はすべて 0 件。**

### Step 3: 正本を読み、目印による分岐を確かめる

```
$ wc -l scripts/sync/keeper.sh; sha256sum scripts/sync/keeper.sh
52 scripts/sync/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
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
$ wc -l scripts/sync/m2-sync.sh; sha256sum scripts/sync/m2-sync.sh
133 scripts/sync/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
```

**目印が無いときに何が動き、何が動かないか（行番号つき）:**

| 行 | 内容 | 目印 0 件のときの挙動 |
|---|---|---|
| 25 | `exec 9>~/.keeper.lock` | **動く。** 錠のファイルを作る |
| 26 | `flock -n 9 \|\| exit 0` | **動く。** 二重起動なら静かに終わる |
| 28 | `M2DIR` を `~/slocal2` の有無で決める | **動く。** ilya は `~/slocal2/m2` |
| 30 | `while true` 開始 | **動く** |
| 31-32 | 注釈 | — |
| 33 | `if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001...'` | **`resolve_tunnel` が 15 行で `return 1`。左辺が偽なので短絡し、`pgrep` すら評価されない** |
| 34-37 | `nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 ...` | **動かない**（33 行が偽） |
| 39-40 | 注釈 | — |
| **41** | **`if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing`** | **両条件とも真。下記参照** |
| **42** | **`nohup ~/bin/syncthing serve --no-browser ...`** | **動く（＝同期処理が起動する）** |
| 45-46 | `m2-sync.sh` を origin/phase0 から自己更新 | **動く** |
| 48-49 | `.stglobalignore` を `.stignore` へ反映 | **動く**（repo 直下に `.stignore` を作る） |
| 50 | `~/bin/m2-sync.sh 9>&-` | **動く（＝版管理の同期）** |
| 51 | `sleep 1800 9>&-` | **動く。** 周期は 1800 秒 |

**起票者の理解と食い違う箇所がある。実装を正として記録する（SPEC の指示どおり）。**

SPEC は 39〜50 行を「同期処理の**監視**、除外規則の反映、版管理の同期 → **これを動かす**」
と書くが、**実装の 41〜43 行は監視ではなく起動である。** 条件を実測した。

```
$ ls -la ~/bin/syncthing
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:53 /home/ubuntu/bin/syncthing
$ test -x ~/bin/syncthing && echo "executable=YES → 41行の第一条件が真" || echo "executable=NO"
executable=YES → 41行の第一条件が真
$ pgrep -x syncthing >/dev/null && echo "syncthing_running=YES" || echo "syncthing_running=NO → 41行の第二条件も真"
syncthing_running=NO → 41行の第二条件も真
```

**41 行の両条件が真である。** よって `keeper.sh` を起動すると**一周目で必ず
`~/bin/syncthing serve --no-browser` が起動する。** これは次と衝突する。

- 禁止 2「**同期処理を起動する**（識別子の登録が済んでいない）」
- 完了判定 11「**中継が零件、同期処理が零件**」
- G2「常駐処理が一件だけ動き、**中継と同期処理が零件である**」

**41 行の注釈は「未インストールならスキップ」と書く。** ilya は前契約
（T-2026-08-22-ilya-node-foundation）で `~/bin/syncthing` を 755 で配置済みであり、
**スキップされる側に該当しない。** 前契約は「登録と起動は範囲外」として実体だけを置いた。
その成果物が、本契約では起動条件を満たしてしまう。

### Step 4: 版管理の同期が何をするかを読む

```
$ grep -n -E "auto-merge|auto-push|pull request|sync-pause|SERVERNAME" scripts/sync/m2-sync.sh | head -30
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
$ grep -n -E "sync-alerts|LOG|log" scripts/sync/m2-sync.sh | head -12
11:LOG=~/claude-sync/sync-alerts.log
22:mkdir -p "$(dirname "$LOG")"
23:alert() { printf '%s [%s] %s\n' "$(date '+%F %T')" "$SRV" "$1" >> "$LOG"; }
$ sed -n '36,50p' scripts/sync/m2-sync.sh
# 目印は $M2DIR 直下に置くが .stignore の総取り規則 ** に落ちるため同期されない。
# よって停止は **その 1 台だけ** に効く（全台を止めてしまうことはない）。
#
# 🔴 解除を忘れると、そのホストだけ同期が止まったままになる。気付けるよう毎ループ記録する。
if [ -f "$M2DIR/.sync-pause" ]; then
  alert "一時停止中: $M2DIR/.sync-pause があるため分岐へ書き込まない（消せば再開）"
  exit 0
fi

git fetch -q origin || {
  alert "fetch失敗(PAT期限切れ?)"
  exit 1
}

BR=$(git symbolic-ref --short HEAD 2>/dev/null)
$ grep -c "sync-pause" scripts/sync/m2-sync.sh
2
```

**発火条件（実装から読んだもの）:**

| 条件 | 挙動 |
|---|---|
| `$M2DIR/.sync-pause` が在る（40 行） | 記録を 1 行残して `exit 0`。**分岐へ一切書かない** |
| 抑止が無く、`git fetch` が失敗（45 行） | 「fetch失敗(PAT期限切れ?)」を記録して `exit 1` |
| behind > 0 かつ追跡変更あり（70 行） | auto-merge を見送り、件数を記録 |
| behind > 0 かつ未追跡が阻害（78 行） | auto-merge を見送り、**手動対応が必要**と記録 |
| behind > 0 で阻害なし（80 行） | **`origin/phase0` を作業分岐へ自動で統合する** |
| ahead > 0（105 行） | **作業分岐へ自動で送出する** |

**記録の置き場所は `~/claude-sync/sync-alerts.log`（11 行）。**
22 行が `mkdir -p` するので、いま不在でも実行時に作られる。
`SRV` は `SERVERNAME`（18 行）＝前契約で `ilya` を設定済み。

正本は抑止に対応している（`sync-pause` が 2 件該当）。


---

## G1 の評価（Phase A 直後）

契約の check: 「版管理が最新であることを確かめた。目印の件数と起動行の有無と未追跡の件数を
記録し、稼働しているものを対照つきで数えた。目印による分岐の範囲を行番号つきで記録し、
版管理の同期の発火条件を読んだ」

| 要素 | 実測 | 判定 |
|---|---|---|
| 版管理が最新 | HEAD=3c4c5a6 = origin/phase0=3c4c5a6（fetch 後） | 満たす |
| 目印の件数 | `.tunnel_to_*` = 0 件 | 満たす |
| 起動行の有無 | `~/.zshrc`（存在・可読・77 行）に `keeper` 0 件 `nohup` 0 件 | 満たす |
| 未追跡の件数 | 3 件 | 満たす |
| 稼働の計数（対照つき） | 対象 5 種すべて 0。陽性対照 `sshd`=1、陰性対照 0 | 満たす |
| 分岐の範囲（行番号） | 25〜51 行を表にした。中継は 33〜38、同期処理の起動は 41〜43 | 満たす |
| 同期の発火条件 | 40/45/70/78/80/105 行の条件を表にした | 満たす |

**G1 = PASS。**

---

## Phase A で見つかった契約の矛盾と、その扱い

**keeper.sh 41 行が同期処理を起動するため、禁止 2・完了判定 11・G2 と衝突する。**
Phase B へ進む前にユーザーへ提示し、判断を仰いだ。

提示した選択肢と、選ばれたもの:

| 案 | 内容 | 選択 |
|---|---|---|
| A | `chmod -x ~/bin/syncthing` で 41 行の第一条件を偽にしてから起動 | **選択された** |
| B | 起票どおり起動し、禁止 2 に触れた事実とともに G2 で停止 | — |
| C | 起動せず、契約の矛盾として差し戻す | — |

**案 A を選んだ理由（ユーザーの判断）。** 実体・識別子・公開鍵を一切変えず、
権限ビットだけを変える。契約の Goal（中継を張らず版管理の自動同期だけを動かす）を
そのまま満たす。後の契約が `chmod +x` すれば戻る。

---

## Phase B / Task 2

### Step 1: 置き場所を作り、配置する

**申し送り 5（無変更は要約値で確かめる）に従い、作業ツリーの正本が
`origin/phase0` と同一であることを先に確かめた。**
keeper.sh 自身の 3〜4 行が「作業ツリーのブランチに依存しないよう git オブジェクトから
直接展開する」と書くため、`cp` で同じ結果になることを示す必要がある。

```
$ echo "worktree: $(sha256sum scripts/sync/keeper.sh | cut -d' ' -f1)  keeper.sh"
worktree: 9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  keeper.sh
$ echo "phase0  : $(git show origin/phase0:scripts/sync/keeper.sh | sha256sum | cut -d' ' -f1)  keeper.sh"
phase0  : 9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  keeper.sh
$ echo "worktree: $(sha256sum scripts/sync/m2-sync.sh | cut -d' ' -f1)  m2-sync.sh"
worktree: bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  m2-sync.sh
$ echo "phase0  : $(git show origin/phase0:scripts/sync/m2-sync.sh | sha256sum | cut -d' ' -f1)  m2-sync.sh"
phase0  : bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  m2-sync.sh
```

```
$ mkdir -p ~/bin
$ cp scripts/sync/keeper.sh ~/bin/keeper.sh
$ cp scripts/sync/m2-sync.sh ~/bin/m2-sync.sh
$ chmod 755 ~/bin/keeper.sh ~/bin/m2-sync.sh
$ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh scripts/sync/keeper.sh scripts/sync/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
$ ls -la ~/bin/
total 26128
drwxrwxr-x 2 ubuntu ubuntu     4096 Aug 23 17:26 .
drwxr-x--- 1 ubuntu ubuntu     4096 Aug 23 17:20 ..
-rwxr-xr-x 1 ubuntu ubuntu     2709 Aug 23 17:26 keeper.sh
-rwxr-xr-x 1 ubuntu ubuntu     7342 Aug 23 17:26 m2-sync.sh
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:53 syncthing
```

**四つの要約値が一致した**（作業ツリー = origin/phase0 = 配置物）。

### Step 2: 構文を確かめる

**起票どおりの `sh -n` は m2-sync.sh を不合格にした。**

```
$ sh -n ~/bin/keeper.sh; echo "keeper_syntax=$?"
keeper_syntax=0
$ sh -n ~/bin/m2-sync.sh; echo "m2sync_syntax=$?"
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
m2sync_syntax=2
```

**原因を測った。**

```
$ head -1 ~/bin/m2-sync.sh
#!/bin/bash
$ sed -n '73,77p' ~/bin/m2-sync.sh
      # 事前に集合の積を取って判定する（rm はしない）。
      BLOCKED=$(comm -12 \
        <(git ls-files --others --exclude-standard | sort) \
        <(git ls-tree -r --name-only "origin/$MAIN" | sort) | wc -l | tr -d ' ')
      if [ "$BLOCKED" != "0" ]; then
$ ls -la /bin/sh
lrwxrwxrwx 1 root root 4 Mar 31  2024 /bin/sh -> dash
```

**`/bin/sh` は dash である。** m2-sync.sh は `#!/bin/bash` で始まり、75 行で
プロセス置換 `<(...)` を使う。**dash はこれを解さないため偽の構文誤りを出す。**
正本は壊れていない。**検査する側の解釈系が誤っている。**

**本来の解釈系で検査し直した。**

```
$ bash -n ~/bin/keeper.sh; echo "keeper_bash_n=$?"
keeper_bash_n=0
$ bash -n ~/bin/m2-sync.sh; echo "m2sync_bash_n=$?"
m2sync_bash_n=0
```

**両方 0。完了判定 6 は `bash -n` で満たした。**

**陽性対照。** 最初に取った対照は自分の命令に欠陥があった。

```
$ sh -n /tmp/broken_keeper.sh 2>&1 | head -2; echo "broken_syntax=$?"
/tmp/broken_keeper.sh: 53: Syntax error: end of file unexpected (expecting "then")
broken_syntax=0
```

**`$?` はパイプ末尾の `head` の終了コードであり、`sh -n` のものではない。**
表示上は誤りが出ているのに 0 と読めてしまう。**申し送り 4 と 8 が指す形そのもの。**
パイプを外して取り直した。

```
$ sed '26s/.*/if [ 1/' ~/bin/keeper.sh > /tmp/broken_keeper.sh
$ bash -n /tmp/broken_keeper.sh 2>/tmp/broken_err.txt; echo "broken_bash_n=$?"
broken_bash_n=2
$ cat /tmp/broken_err.txt
/tmp/broken_keeper.sh: line 53: syntax error: unexpected end of file
```

**壊した写しは 2 を返す。検査は働いている。** 囮は消した。

### Step 3: 目印が無いことを確かめる

```
$ ls -a ~/ | grep '^\.tunnel_to_' ; echo "marker_count=$(ls -a ~/ | grep -c '^\.tunnel_to_')"
marker_count=0
```

**零件。** 作っていない（禁止 1）。

### Step 4: 抑止の目印を置く

```
$ cd ~/slocal2/m2 && touch .sync-pause
$ ls -la .sync-pause
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:26 .sync-pause
$ echo "pause_supported=$(grep -c 'sync-pause' ~/bin/m2-sync.sh)"
pause_supported=2
$ echo "ignored=$(git check-ignore .sync-pause && echo yes || echo no)"
ignored=.sync-pause
yes
```

**配置物は抑止に対応している版である**（2 件該当）。目印は `.gitignore` 済みで
未追跡の件数に影響しない。

### 案 A の適用: syncthing の実行権を外す

```
$ ls -la ~/bin/syncthing
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:53 /home/ubuntu/bin/syncthing
$ echo "before_sha=$(sha256sum ~/bin/syncthing | cut -d' ' -f1)"
before_sha=32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd
$ echo "before_size=$(stat -c %s ~/bin/syncthing)"
before_size=26730145
$ chmod -x ~/bin/syncthing
$ ls -la ~/bin/syncthing
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:53 /home/ubuntu/bin/syncthing
$ echo "after_sha=$(sha256sum ~/bin/syncthing | cut -d' ' -f1)"
after_sha=32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd
$ echo "after_size=$(stat -c %s ~/bin/syncthing)"
after_size=26730145
$ test -x ~/bin/syncthing && echo "TRUE（起動する）" || echo "FALSE（起動しない）"
FALSE（起動しない）
```

**要約値は変わっていない**（`32ab747e…` は前契約 T-2026-08-22-ilya-node-foundation の
記録と一致）。**変わったのは権限ビットのみ 755 → 644。**
41 行の第一条件が偽になった。


---

## Phase B / Task 3

### Step 1: 起動行を追記する

**追記前を測った。**

```
$ grep -n "keeper" ~/.zshrc; echo "grep_exit=$? (1=該当なし)"
grep_exit=1 (1=該当なし)
$ echo "keeper_hits_before=$(grep -c 'keeper' ~/.zshrc)"
keeper_hits_before=0
$ echo "zshrc_lines_before=$(grep -c '' ~/.zshrc)"
zshrc_lines_before=77
$ echo "zshrc_sha_before=$(sha256sum ~/.zshrc | cut -d' ' -f1)"
zshrc_sha_before=a00ca89946fa38dcb70c8e417c8744a91faa1e2e655ce158b742e30403b0cca5
```

**既存は無い。追記してよい。** 戻せるように退避した。

```
$ cp ~/.zshrc /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync
$ ls -la /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync
-rw-rw-r-- 1 ubuntu ubuntu 2116 Aug 23 17:28 /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync
```

**追記そのものは実行基盤に三度拒否された。**

```
$ cat >> ~/.zshrc <<'ZRC' ... ZRC
Permission for this action was denied by the Claude Code auto mode classifier. Reason: Blocked by classifier.
```

同じ内容を編集専用の道具でも試み、同じく拒否された。

```
Edit(/home/ubuntu/.zshrc)
Permission for this action was denied by the Claude Code auto mode classifier. Reason: Blocked by classifier.
```

**三つ目の機構を試すことは、拒否の意図の迂回にあたるため行わなかった。**
拒否の文面が「必要ならユーザーへ説明して判断を仰げ」と指示しており、それに従った。

**ユーザーへ提示し、「ユーザー自身が追記する」が選ばれた。** 提示した内容:

```
# >>> egosurgery keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< egosurgery keeper <<<
```

**目印ブロックの形にしたのは前契約の `SERVERNAME` ブロックと揃えるため**
（後から機械的に消せる）。中の 1 行は SPEC の指示どおりである。

追記後の実測は「Task 3 Step 1 の続き」に記す。

### Step 2: 一度だけ明示的に起動する

```
$ cd ~/slocal2/m2 && nohup ~/bin/keeper.sh >/dev/null 2>&1 &
launch_exit=0
launched_pid_of_shell_job=43963
```

**前景の `sleep` はこの実行基盤で使えないため、条件で待つ形に置き換えた。**
起票の `sleep 5` は固定待ちだが、錠の出現を待つほうが確実である。

### Step 3: 一つだけ動いていることを確かめる

```
$ .venv/bin/python - <<'PY' ... PY
waited=0.0s lock_exists=True
keeper.sh=1 ['43963']
ssh -N -L=0 []
syncthing=0 []
m2-sync=0 []
zzz_none=0 []
```

**常駐処理が一件（pid 43963）。中継が零件。同期処理が零件。**
起票の Expected と一致した。

### Step 4: 多重起動を防ぐ仕掛けを確かめる

```
$ ls -la ~/.keeper.lock
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:31 /home/ubuntu/.keeper.lock
```

**錠が作られた。** 起票は存在だけを求めるが、**存在は働きを意味しない。**
実際に二度目を起こして確かめた（陽性対照）。

```
$ nohup ~/bin/keeper.sh >/dev/null 2>&1 &
second_launch_shelljob=44328
$ sleep 3
$ .venv/bin/python - <<'PY' ... PY
keeper.sh=1 ['43963']
ssh -N -L=0 []
syncthing=0 []
```

**二度目は即座に終わり、件数は 1 のまま、pid も最初の 43963 のままである。**
`flock -n 9 || exit 0`（26 行）が働いている。

### Step 5: 版管理の同期が一周したことを確かめる

**`~/claude-sync/` は開始時に不在だったが、m2-sync.sh の 22 行 `mkdir -p` で作られた。**

```
$ ls -la ~/claude-sync/ 2>&1
total 16
drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 23 17:31 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 17:31 ..
-rw-rw-r-- 1 ubuntu ubuntu  144 Aug 23 17:31 sync-alerts.log
$ tail -20 ~/claude-sync/sync-alerts.log 2>&1
2026-08-23 17:31:26 [ilya] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
$ grep -c '一時停止中' ~/claude-sync/sync-alerts.log
1
```

**抑止が効いている。** 記録の `[ilya]` は `SERVERNAME` が前契約どおり効いている証拠でもある
（m2-sync.sh 18 行 `SRV="${SERVERNAME:-}"`）。

**版管理へ書き込まれていないことを確かめた。**

```
$ git --no-pager status -sb
## feat/ilya-keeper-autosync...origin/phase0
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
?? docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md
?? tasks/T-2026-08-24-ilya-keeper-autosync/
$ git --no-pager log -1 --format='%h %s'
3c4c5a6 Merge pull request #125 from takuya3h/feat/andrew-node-foundation
```

**分岐は変わらず、ahead は増えず、未追跡は 3 件のまま。**

### 一周目の副作用を測る（起票に無いが、起きたことは記録する）

```
$ sha256sum ~/bin/m2-sync.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
$ echo "phase0  : $(git show origin/phase0:scripts/sync/m2-sync.sh | sha256sum | cut -d' ' -f1)"
phase0  : bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f
$ ls -la ~/bin/m2-sync.sh ~/bin/m2-sync.sh.new 2>&1 | head -4
ls: cannot access '/home/ubuntu/bin/m2-sync.sh.new': No such file or directory
-rwxrwxr-x 1 ubuntu ubuntu 7342 Aug 23 17:31 /home/ubuntu/bin/m2-sync.sh
$ ls -la .stignore .stignore.new 2>&1
ls: cannot access '.stignore.new': No such file or directory
-rw-rw-r-- 1 ubuntu ubuntu 2223 Aug 23 17:31 .stignore
$ echo "stignore_ignored=$(git check-ignore .stignore 2>/dev/null || echo '追跡対象になりうる')"
stignore_ignored=.stignore
$ sha256sum ~/bin/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
$ ls -la ~/bin/syncthing
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:53 /home/ubuntu/bin/syncthing
$ pgrep -x syncthing >/dev/null && echo "syncthing_running=YES" || echo "syncthing_running=NO"
syncthing_running=NO
$ echo "syncthing_log_exists=$(test -e ~/.syncthing.log && echo yes || echo no)"
syncthing_log_exists=no
$ echo "tunnel_log_exists=$(test -e ~/.tunnel.log && echo yes || echo no)"
tunnel_log_exists=no
```

観測できたこと:

| 行 | 起きたこと |
|---|---|
| 45-46 | `~/bin/m2-sync.sh` を origin/phase0 から自己更新。要約値は不変。**権限が 755 → 775 に変わった**（`mv` が新規ファイルの既定権限を持ち込むため） |
| 48-49 | **`.stignore`（2223 バイト）が repo 直下に作られた。** `git check-ignore` が該当を返すので未追跡の件数には現れない |
| 34 | **`~/.tunnel.log` が存在しない。** 34 行は `>>~/.tunnel.log` で追記するため、**一度でも走れば必ず作られる。無いことが「走っていない」ことの証拠である** |
| 42 | **`~/.syncthing.log` が存在しない。** 同じ理由で、**42 行が走っていない証拠である** |

**中継と同期処理が零件であることを、件数と記録ファイルの不在の二通りで示した。**

---

## G2 の評価（Phase B 直後）

契約の check: 「配置物と正本の要約値が一致し、構文検査が通った。常駐処理が一件だけ動き、
中継と同期処理が零件である。多重起動を防ぐ錠が作られ、版管理の同期が一周して抑止が効いている」

| 要素 | 実測 | 判定 |
|---|---|---|
| 配置物と正本の要約値が一致 | keeper `9fe9c423…` / m2-sync `bcf46ba9…` が三箇所（作業ツリー・phase0・配置物）で一致 | 満たす |
| 構文検査が通った | `bash -n` で両方 0。`sh -n` は dash の限界による偽陽性 | 満たす |
| 常駐処理が一件だけ | `keeper.sh=1 ['43963']`。二度目の起動でも 1 のまま | 満たす |
| 中継が零件 | `ssh -N -L=0`、`~/.tunnel.log` 不在 | 満たす |
| 同期処理が零件 | `syncthing=0`、`~/.syncthing.log` 不在 | 満たす |
| 錠が作られた | `~/.keeper.lock` 存在。二重起動で働きも確認 | 満たす |
| 同期が一周し抑止が効く | `sync-alerts.log` に「一時停止中」1 件、分岐は不変 | 満たす |

**G2 = PASS。**


---

## Task 3 Step 1 の続き: 起動行の追記（ユーザーが実行）

実行基盤が私の書き込みを拒否したため、**ユーザーが自分の端末で追記した。**
私は測るだけである。三度の実測が要った。

### 一度目

```
$ printf '\n# >>> egosurgery keeper >>>\n( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null\n# <<< egosurgery keeper <<<n' >> ~/.zshrc && tail -4 ~/.zshrc
# >>> egosurgery keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< egosurgery keeper <<<n
```

検算した。

```
$ echo "zshrc_lines_after=$(grep -c '' ~/.zshrc)"
zshrc_lines_after=81
$ echo "keeper_hits_after=$(grep -c 'keeper' ~/.zshrc)"
keeper_hits_after=3
$ echo "zshrc_sha_after=$(sha256sum ~/.zshrc | cut -d' ' -f1)"
zshrc_sha_after=380fe20e2c636674ec5fa0c70d5248b321f4a2c24d64c9ad933000c71c643965
$ tail -5 ~/.zshrc | cat -A
autoload -U compinit && compinit$
$
# >>> egosurgery keeper >>>$
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null$
# <<< egosurgery keeper <<<n
$ tail -c 1 ~/.zshrc | od -c | head -2
0000000   n
0000001
```

**閉じ目印の末尾に `n` が混入し、ファイル末尾の改行が無い。**
命令の `<<<n'` で `\n` の `\` が落ちたため。**注釈行なので動作に影響は無いが、
目印ブロックが壊れており、この行はこれから他の四台へ複写される。** 直すことにした。

### 二度目

**退避からの復元を伴わずに追記だけが走り、ブロックが二重になった。**

```
$ printf '\n# >>> ... <<<\n' >> ~/.zshrc && tail -4 ~/.zshrc
# <<< egosurgery keeper <<<n
# >>> egosurgery keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< egosurgery keeper <<<
$ echo "zshrc_lines=$(grep -c '' ~/.zshrc)"
zshrc_lines=84
$ echo "launch_line_count=$(grep -c 'nohup ~/bin/keeper.sh' ~/.zshrc)"
launch_line_count=2
$ echo "open_marker_count=$(grep -c '^# >>> egosurgery keeper >>>$' ~/.zshrc)"
open_marker_count=2
$ echo "close_marker_ok=$(grep -c '^# <<< egosurgery keeper <<<$' ~/.zshrc)"
close_marker_ok=1
$ echo "close_marker_broken=$(grep -c 'keeper <<<n$' ~/.zshrc)"
close_marker_broken=1
$ tail -8 ~/.zshrc | cat -A
autoload -U compinit && compinit$
$
# >>> egosurgery keeper >>>$
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null$
# <<< egosurgery keeper <<<n$
# >>> egosurgery keeper >>>$
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null$
# <<< egosurgery keeper <<<$
```

**起動行が二本になった。** 契約の Task 3 Step 1 は「該当があれば追記しない。
**二重に起動する**」と明示する。**実害は錠が防ぐ**（二重起動しても件数が 1 のままである
ことは既に実測済み）が、契約の意図に反するため直した。

貼り直す前に、退避が開始時と同一であることを確かめた。

```
$ echo "backup_sha=$(sha256sum /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync | cut -d' ' -f1)"
backup_sha=a00ca89946fa38dcb70c8e417c8744a91faa1e2e655ce158b742e30403b0cca5
$ echo "expected  =a00ca89946fa38dcb70c8e417c8744a91faa1e2e655ce158b742e30403b0cca5"
expected  =a00ca89946fa38dcb70c8e417c8744a91faa1e2e655ce158b742e30403b0cca5
$ echo "backup_lines=$(grep -c '' /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync)"
backup_lines=77
$ echo "backup_keeper_hits=$(grep -c keeper /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync)"
backup_keeper_hits=0
```

### 三度目（確定）

```
$ cp /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync ~/.zshrc && printf '\n# >>> egosurgery keeper >>>\n( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null\n# <<< egosurgery keeper <<<\n' >> ~/.zshrc && tail -4 ~/.zshrc
# >>> egosurgery keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< egosurgery keeper <<<
```

```
$ echo "zshrc_lines=$(grep -c '' ~/.zshrc)"
zshrc_lines=81
$ echo "launch_line_count=$(grep -c 'nohup ~/bin/keeper.sh' ~/.zshrc)"
launch_line_count=1
$ echo "open_marker_count=$(grep -c '^# >>> egosurgery keeper >>>$' ~/.zshrc)"
open_marker_count=1
$ echo "close_marker_ok=$(grep -c '^# <<< egosurgery keeper <<<$' ~/.zshrc)"
close_marker_ok=1
$ echo "close_marker_broken=$(grep -c 'keeper <<<n' ~/.zshrc)"
close_marker_broken=0
$ echo "zshrc_sha_final=$(sha256sum ~/.zshrc | cut -d' ' -f1)"
zshrc_sha_final=f91893132f823bd898f83676558b05586c25bbd5c0b20e52a5d5b7306302f788
$ tail -5 ~/.zshrc | cat -A
autoload -U compinit && compinit$
$
# >>> egosurgery keeper >>>$
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null$
# <<< egosurgery keeper <<<$
$ tail -c 1 ~/.zshrc | od -c | head -2
0000000  \n
0000001
$ diff /tmp/zshrc.backup.T-2026-08-24-ilya-keeper-autosync ~/.zshrc; echo "diff_exit=$?"
77a78,81
>
> # >>> egosurgery keeper >>>
> ( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
> # <<< egosurgery keeper <<<
diff_exit=1
```

**確定した追記内容（開始時との差はこの四行だけである）:**

```

# >>> egosurgery keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< egosurgery keeper <<<
```

`~/.zshrc` は 77 行 `a00ca899…` → 81 行 `f9189313…`。
起動行は一本、目印は正しい形、末尾に改行あり。

**他の四台へはこの四行をそのまま使える。** ただし**追記の命令は
`\n` のバックスラッシュを落とさないこと**、および**貼り直すときは先に退避から
戻すこと**（さもないと二重になる）。


---

## Phase C / Task 4

生の出力は RESULT.md §10 に貼った（同じ内容を二度貼らない）。ここには
**RESULT.md に収まらなかった、自分の命令の欠陥だけを残す。**

### `${PIPESTATUS[0]}` が空を返した

```
$ make taskindex-check 2>&1 | tail -20; echo "taskindex_check_exit=${PIPESTATUS[0]}"
taskindex_check_exit=
```

**対話シェルは zsh であり、配列は `pipestatus` かつ添字が 1 始まりである。**
SPEC の「全台で確定した事実」に「`${PIPESTATUS[0]}` のような配列添字は使えない」と
明記され、申し送り 8 にも「配列添字で終了コードを取らない（前契約の指摘）」とある。
**警告を読んでいながら同じ形を書いた。** パイプを外し、ファイルへ落として取り直した。

```
$ make taskindex-check > /tmp/ti_check.txt 2>&1; echo "taskindex_check_exit=$?"
taskindex_check_exit=0
```

**このときはまだ result.yaml を書いていなかったため 0 だった。**
result.yaml と inbox.d を書いた後に取り直すと 2 を返した（RESULT.md §10-3）。
**検査は書いた後に取ること。**

### 解除の後に周期を裏づけた

作業中に二周し、17:31:26 と 18:01:26 の差がちょうど 1800 秒であった。
**keeper.sh 51 行の `sleep 1800` が実測で裏づけられた。**
二周とも抑止が効き、`auto-merge` も `auto-push` も一度も出ていない。


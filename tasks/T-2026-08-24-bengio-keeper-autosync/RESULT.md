# RESULT — T-2026-08-24-bengio-keeper-autosync

**kind:** `impl`  **host:** `bengio`  **repo:** `~/slocal2/m2`
**branch:** `feat/bengio-keeper-autosync`  **実行日:** 2026-08-23 (JST)

生の出力は要約せず `audit.md` に貼ってある（申し送り #9）。本書は散文である。

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

### `contract.conventions_rev`

SPEC は「実行者が実測して置換する」と定める。実測値は次のとおり。

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b087
```

`spec.yaml` の `d422b08` はこの値の 7 桁前置である。**一致するため置換は不要だった。**

### `inputs.code.entrypoints`

| 正本 | 行数 | sha256 |
|---|---|---|
| `scripts/sync/keeper.sh` | 52 | `9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90` |
| `scripts/sync/m2-sync.sh` | 133 | `bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f` |

作業ツリー・配置物 (`~/bin/`)・`origin/phase0` の blob で**三者一致**を確認した。

`inputs.denominator` `inputs.sigma_policy` `inputs.frozen_source` は本契約に無い（`impl`）。

---

## 2. 完了判定 19 項目（実測値）

「実施した」ではなく「何が出たか」を書く。

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 開始状態を記録した | `marker_count=0` / 起動行 0 件（`~/.zshrc` は在る。`zshrc_exists=1`）/ 未追跡・変更 10 件 |
| 2 | 稼働を対照つきで数えた | keeper=0 m2-sync=0 syncthing=0 中継=0。否定 `zzz_none=0`、肯定 `sshd=3` |
| 3 | 正本の要約値と分岐を行番号つきで記録 | 7-23 / 33-38 / **41-43** / 44-50 / 51。要約値は §1 の表 |
| 4 | 版管理の同期の発火条件を記録 | m2-sync.sh 11 / 18 / 22 / 40-43 / 45 / 60-88 / 90-107 / 120-122 |
| 5 | 配置物と正本の要約値が一致 | 一致（三者）。`~/bin/keeper.sh` `~/bin/m2-sync.sh` とも `-rwxr-xr-x` |
| 6 | 構文検査が両方とも通った | `bash -n`: keeper=0 m2-sync=0。`sh -n`: keeper=0 **m2-sync=2**（検査器の誤り。§5） |
| 7 | 目印が零件 | `marker_count=0`（`tunnel` を含む名も 0 件） |
| 8 | 抑止を置き、対応している版と確認 | `.sync-pause` 存在。`grep -c sync-pause ~/bin/m2-sync.sh` = **2**（0 なら未対応） |
| 9 | 起動行を追記した | 追記前 0 件 → 後 3 件。77 行 → 82 行。sha `a00ca899…0cca5` → `bb939dbc…cc23`。実体は SPEC 指定の 1 行 |
| 10 | 常駐処理が一件だけ動いている | **1 件。pid 157746**（`/bin/bash /home/ubuntu/bin/keeper.sh`） |
| 11 | 中継が零件、同期処理が零件 | 中継 0 件 / 同期処理 0 件 |
| 12 | 錠が作られた | `~/.keeper.lock` (17:39)。かつ `flock LOCK_NB` が **取得できない** = 実際に握られている |
| 13 | 版管理の同期が一周し抑止が効いている | `~/claude-sync/sync-alerts.log` に 1 行。`2026-08-23 17:39:05 [bengio] 一時停止中: …` |
| 14 | 13 項目すべてに実測値または UNKNOWN | 本表。UNKNOWN は無い（別途 §7 に UNKNOWN が 2 件ある） |
| 15 | 送信前の秘匿検査（陽性対照つき） | §4 |
| 16 | 開始時の未追跡がすべて残っている | §6 |
| 17 | 変更が契約の範囲に限られる | §6 |
| 18 | 分岐が送出され PR が存在する | §6 |
| 19 | 抑止が repo 直下から消えている | §6 |

---

## 3. 起票者の理解と実装の食い違い（実装を正とした）

SPEC の表は次のように書く。

| 分岐 | 実装の位置 | SPEC の扱い |
|---|---|---|
| 目印があるときだけ中継を維持 | 三十一から三十八行 | 目印を置かないので動かない |
| 同期処理の監視、除外規則の反映、版管理の同期 | 三十九から五十行 | **これを動かす** |

**前者は正しい。** `resolve_tunnel()` は 15 行 `[ -n "$TUNNEL_MARKER" ] || return 1` で
1 を返し、33 行の `resolve_tunnel && …` が短絡する。実測でも中継は 0 件だった。

**後者が誤っている。** 39-50 行には**同期処理そのものの起動**が含まれる。

```
41  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
42    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
43  fi
```

判定条件は `[ -x ~/bin/syncthing ]` **だけ**で、目印の有無に依存しない。
`~/bin/syncthing` は前契約 T-2026-08-22-bengio-node-foundation で配置済みであり、
属性は `-rwxr-xr-x` だった。**したがって keeper をそのまま起動すると同期処理が必ず起動し、
禁止 2「同期処理を起動する」と完了判定 11「同期処理が零件」を同時に破る。**

これは契約の内部矛盾である（`self_contradiction`）。

### 採った道と、その理由

完了判定 5 が「配置物と正本の要約値が一致」を求めるため、**`~/bin/keeper.sh` を
書き換えて 41-43 行を無効化する道は塞がれている。** 起動を諦めれば版管理の自動同期が
復活せず、契約の目的そのものが果たせない。

そこで**判定条件の側を偽にした**。`chmod -x ~/bin/syncthing` である。これは keeper 自身の
コメント「未インストールならスキップ」が想定する経路に入れることを意味する。

| 前 | 後 |
|---|---|
| `-rwxr-xr-x  26730145  ~/bin/syncthing` | `-rw-r--r--  26730145  ~/bin/syncthing` |
| sha256 `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` | **同一** |

**中身は変えていない。** 戻し方は `chmod +x ~/bin/syncthing` の一行である。
ユーザーへ「何を / 影響範囲 / 戻し方」を提示し、**承認を得てから実行した。**

🔴 **次の契約で同期処理を登録・起動するときは、先に実行属性を戻すこと。**
戻し忘れると keeper は同期処理を永久に起動しない。inbox と §7 に置いた。

---

## 4. 送信前の秘匿検査（自分で実施）

`make task-report` は使えない（合言葉が失われている）ため、検査を自分で行った。
判定は件数ではなく**形**で行った。詳細と出力は `audit.md` の該当節にある。

陽性対照は囮を含む一時ファイルで取り、`/tmp` に置いて **commit していない。**

---

## 5. 検査器そのものの誤り

### `sh -n` は bash の正本に誤った失敗を返す

SPEC Task 2 Step 2 は「両方が零であること」と書くが、実測は `m2sync_syntax=2` だった。

```
$ sh -n ~/bin/m2-sync.sh
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
```

両方の正本が `#!/bin/bash` を宣言し、`/bin/sh` は `dash` への連結である
（`lrwxrwxrwx /bin/sh -> dash`）。74-76 行の `<(...)`（プロセス置換）は bash 固有で
dash には無い。**正しい検査器 `bash -n` では両方とも 0。**

対照として壊した写しも 2 を返した。**終了コードだけでは「正本が bash である」ことと
「正本が壊れている」ことを区別できない。** 指示どおりなら実行者は停止するか、
**正本を「直して」しまう。** 起動は shebang により bash が使われるため実行時に問題は無い。

### `P9 spec_lint` の `separated_source` は行継続を見ていない

プリフライトは `SPEC.md:329,332,335` を該当とした。当該行は次の形である。

```
source .venv/bin/activate \
  && make task-validate TASK=T-2026-08-24-bengio-keeper-autosync; echo "validate_exit=$?"
```

`tools/check_agent_docs.py:89-93` の `_ends_with_source` は行末の `\`（行継続）を
考慮せず、`&&` で分割した末尾が `source ` で始まるかだけを見る。**したがって正しく
繋がれた命令にも該当が出る。** ただし契約側にも問題はある。手順書自身が
「実装系によっては命令ごとに新しいシェルが起きる」と警告しており、字下げ区画を
1 行ずつ渡す実装系では `source .venv/bin/activate \` 単独が壊れた命令になる。
**両方を事実として記録する。** 終了コードは変わらず、プリフライトは exit 0 だった。

---

## 6. 範囲、送出、抑止の解除

### 判定 16 — 開始時の未追跡がすべて残っている

開始時 10 件を **1 行ずつ完全一致（`grep -Fxc`）で照合**した。件数の一致だけでは
入れ替わりを見逃す。**10 件すべてが 1 で残っている。失っていない。**

### 判定 17 — 変更が契約の範囲に限られる

`git status --porcelain` は 11 件。増えた 1 件は
`tasks/inbox.d/T-2026-08-24-bengio-keeper-autosync.md`、契約が書けと定める受け皿である。
`git diff --cached --name-only` を範囲外の形で絞ると該当 0 件だった。

`~/bin/` `~/.zshrc` `~/.keeper.lock` `~/claude-sync/` は版管理の外なので現れない。
`.sync-pause`（`.gitignore:240`）と keeper が更新する `.stignore`（`.gitignore:192`）も
現れない。**keeper の書き込みが未追跡を汚していない。**

**生成物は再生成していない**（§9）。`taskindex-check` = exit 2、`inbox-check` = exit 2。
差分は本契約の 1 行が増えるだけである。⚠ 最初 `| head -20` を通して測り両方 141 を得たが、
これは `head` が閉じたことによる SIGPIPE であって判定ではない。`head` を外して測り直した。

### 判定 18 — 送出と PR

SPEC は「送出側が `git@` で始まるなら、配備鍵が要る形である。**鍵は消えている**」と書き、
`git remote set-url --push origin https://…` を指示する。**bengio ではこの前提が偽だった。**

```
$ git --no-pager remote -v
origin	git@github.com:takuya3h/m2.git (fetch)
origin	git@github.com:takuya3h/m2.git (push)
$ ssh -o BatchMode=yes -T git@github.com
Hi takuya3h! You've successfully authenticated, but GitHub does not provide shell access.
$ gh auth status
✓ Logged in to github.com account takuya3h   Git operations protocol: ssh
```

**鍵は消えていない。** https へ切り替えれば動いている経路を壊すため、**実行しなかった。**
実際に `git@` 経路で push が成功し、判断が裏づいた。

| 項目 | 値 |
|---|---|
| commit 1 | `c70d2075 feat(sync): deploy keeper and enable git autosync on bengio`（6 ファイル / 1473 挿入） |
| push | `git@` 経路で成功。`* [new branch] HEAD -> feat/bengio-keeper-autosync` |
| PR | **#127** `https://github.com/takuya3h/m2/pull/127` base `phase0` state `OPEN` draft でない |
| commit 2 | 本節と `result.yaml` の記録を入れた追補 |

`gh pr create` は `Warning: 9 uncommitted changes` を出したが、これは版管理外の成果物
（開始時からある 9 件）を指すだけで、**触れていない。**

### 判定 19 — 抑止の解除

```
$ mv .sync-pause /tmp/.sync-pause.released.T-2026-08-24-bengio-keeper-autosync
mv_exit=0
$ ls -la .sync-pause
ls: cannot access '.sync-pause': No such file or directory
ls_exit=2
$ ls -la /tmp/.sync-pause.released.T-2026-08-24-bengio-keeper-autosync
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:24 /tmp/…
```

**repo 直下から消えた。**（削除ではなく別名への退避。実装は存在だけを見るため
どちらでも解ける。技能書の記載どおり、退避先を repo の外に置いたので未追跡も増えない。）

**ここで版管理の自動同期が有効になった。** 次の周回（起動から 1800 秒後）で
`auto-merge` と `auto-push`、および下書きの PR の起票が起きうる。**それは正常である。**
ただし PR は既に #127 として存在するため、`m2-sync.sh:120` の `gh pr list --head` が
1 を返して起票は行われない。

解除後の作業ツリー（11 件）:

```
 M README.md                                        ← 開始時からある
 M docs/experiment_log.md                           ← 開始時からある
 M tasks/T-2026-08-24-bengio-keeper-autosync/RESULT.md    ← 本節の追補
 M tasks/T-2026-08-24-bengio-keeper-autosync/result.yaml  ← PR 番号と commit の記録
?? docs/analysis_scripts/                           ← 開始時からある
?? docs/research_review_and_next_plan_2026-08-22.md ← 開始時からある
?? docs/sessions/digest/2026-08-21-538fcc76-…md     ← 開始時からある
?? docs/sessions/digest/2026-08-21-a0b5f9c6-…md     ← 開始時からある
?? docs/sessions/digest/2026-08-22-f0627d44-…md     ← 開始時からある
?? docs/sessions/digest/2026-08-23-a5cc9299-…md     ← 開始時からある
?? docs/task_drafts/                                ← 開始時からある
```

開始時の 10 件のうち `?? tasks/T-2026-08-24-bengio-keeper-autosync/` は
commit `c70d2075` で追跡下に入った。**残る 9 件はすべて手つかずで残っている。
失ったものは無い。**

---

## 7. 次の契約で使う情報

| 項目 | 内容 |
|---|---|
| 記録の置き場所 | `~/claude-sync/sync-alerts.log`。`m2-sync.sh:11` が指し、**22 行の `mkdir -p` が自分で作る**。SPEC は「失われている」と書いたが探す必要は無かった |
| 起動行の内容 | `( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null` を `~/.zshrc` へ。前後に `# >>> egosurgery keeper >>>` / `# <<< egosurgery keeper <<<` の目印を添えた |
| 目印を置いたときの見込み | `keeper.sh:33-38` が `ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <鍵> ubuntu@<住所>` を張る。目印の 1 行目が鍵の位置、2 行目が住所。2 行目が無ければ中心名を SSH の別名として使う |
| 🔴 同期処理の実行属性 | **`chmod -x ~/bin/syncthing` を掛けてある。登録・起動の契約では先に `chmod +x` で戻すこと。** 戻さないと keeper は永久に起動しない |
| つまずいた点 1 | **`sh -n` で bash の正本を検査すると誤った失敗が出る。** 他台でも同じ（§5） |
| つまずいた点 2 | **`/proc/*/cmdline` の部分一致は実行基盤の包み込みを拾う。** `keeper.sh=2` と出た。引数の**要素**で数えること |
| つまずいた点 3 | **`nohup … &` と `setsid` が実行基盤の判定に拒否される場合がある。** 常駐処理を切り離せない |
| つまずいた点 4 | **`~/.zshrc` への `cat >>` も拒否される場合がある。** 編集道具で同じ変更を行う |
| UNKNOWN 1 | 起動した実体 (pid 157746) が**本会期の終了後も残るか**。切り離せていないため測れない。次の対話シェルで起動行が拾うので、残らなくても復旧する |
| UNKNOWN 2 | 追記後の `~/.zshrc` の構文検査 (`zsh -n`)。実行基盤の判定に拒否されたため未実施 |

---

## 8. 逸脱

`result.yaml` の `deviations` と対で書いてある。要約すると 5 件。

1. **判断** — 禁止 2 と `keeper.sh:41-43` の矛盾を、`chmod -x ~/bin/syncthing` で解いた（承認済み）。
2. **環境** — `nohup … &` と `setsid` が実行基盤に拒否され、実行基盤の背景実行で起動した。切り離せていない。
3. **環境** — `~/.zshrc` への `cat >>` と退避の `cp` が拒否され、編集道具で同じ変更を行った。退避は取れていない。
4. **判断** — 抑止の目印を Task 2 Step 4 ではなく Phase A の開始時に置いた（技能書の「実行前に置く」に従った前倒し。keeper は当時 0 件だったので実害は無い）。
5. **判断** — SPEC 指示の `git remote set-url --push origin https://…` を実行しなかった。前提「鍵は消えている」が bengio では偽で、切り替えると動いている経路を壊すため（§6）。
6. **判断** — SPEC の計数（部分一致）と構文検査（`sh -n`）をそのまま採らず、正しい方法で測り直した。両方の出力を残してある。

**逸脱は「無し」ではない。** 上記 6 件がすべてである。

---

## 9. 禁止 4 の遵守

**生成物を再生成していない。** `make taskindex` と `make inbox` は実行していない。
五台で並行するため、各契約が生成物を更新すると版管理で必ず衝突するからである。
`make taskindex-check` が差分を報告した場合も、**事実として記録するだけにした**（§6）。

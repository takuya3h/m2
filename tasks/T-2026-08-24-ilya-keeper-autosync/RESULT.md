# RESULT — T-2026-08-24-ilya-keeper-autosync

**task_id:** `T-2026-08-24-ilya-keeper-autosync`  **kind:** `impl`
**実行ホスト:** `ilya`  **repo:** `~/slocal2/m2`  **実行日:** 2026-08-23 (JST)
**分岐:** `feat/ilya-keeper-autosync`  **基点:** `origin/phase0` = `3c4c5a6`

生の出力は `audit.md` に要約せず貼ってある（起票者の申し送り 9）。

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`conventions_rev` は spec に `d422b08` と記載され、実測も一致したため置換していない。

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b08
```

`context/conventions.md` の `#prohibitions` アンカーの**原文**（要約していない）:

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

### その他の参照

| spec の記載 | 解決 |
|---|---|
| `inputs.denominator.ref` | **記載なし。** kind=impl のため分母は不要 |
| `inputs.sigma_policy` | **記載なし。** 数値の主張をしない契約のため参照していない |
| `inputs.frozen_source.ref` | **記載なし。** 凍結源に触れていない |
| `inputs.code.entrypoints` | `scripts/sync/keeper.sh`（52 行 `9fe9c423…`）、`scripts/sync/m2-sync.sh`（133 行 `bcf46ba9…`） |
| `outputs.stamp.task_id_in` | **記載なし。** run を生成しない契約のため刻印先が無い |

---

## 2. 完了判定 19 項目（実測値）

### Phase A

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 開始状態を記録した | **中継の目印 `.tunnel_to_*` = 0 件。起動行 = 無し**（`~/.zshrc` は存在・可読・77 行、`keeper` 0 件 `nohup` 0 件）。**未追跡 = 3 件**（digest 2 件＋本契約のディレクトリ）。`~/.keeper.lock` **不在**、`~/claude-sync/` **不在**（いずれも読めないのではなく No such file）。`~/bin/` は `syncthing` のみ |
| 2 | 稼働しているものを対照つきで数えた | `keeper.sh=0 m2-sync=0 syncthing=0 "ssh -N -L"=0 zzz_none=0`。**すべて零。** 起票の対照は「存在しない語 → 0」の一方向しかなく計数が壊れていても同じ 0 を返すため、**陽性側も取った**: `sshd=1 (pid 1)`、`systemd=0`。計数は実在するものを拾える |
| 3 | 正本の要約値と分岐を行番号つきで記録した | keeper.sh **52 行 `9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90`**、m2-sync.sh **133 行 `bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f`**。分岐は下記「3. 目印が無いときの挙動」の表（25〜51 行） |
| 4 | 版管理の同期の発火条件を記録した | 40 行 抑止 → 記録 1 行を残して `exit 0`／45 行 fetch 失敗 → `exit 1`／70 行 追跡変更あり → 見送り／78 行 未追跡が阻害 → 見送り／**80 行 阻害なし → `origin/phase0` を自動統合**／**105 行 ahead>0 → 自動送出**。記録先は 11 行 `~/claude-sync/sync-alerts.log` |

### Phase B

| # | 判定 | 実測値 |
|---|---|---|
| 5 | 配置物と正本の要約値が一致 | **四値一致。** keeper: 作業ツリー = `origin/phase0` = 配置物 = `9fe9c423…`。m2-sync: 同様に `bcf46ba9…`。**作業ツリーが phase0 と同一であることを先に確かめてから `cp` した**（keeper.sh 3〜4 行が「git オブジェクトから直接展開する」と書くため） |
| 6 | 構文検査が両方とも通った | **`bash -n` で `keeper=0` `m2sync=0`。** 起票の `sh -n` は `m2sync=2`（偽陽性、下記 §8-2）。壊した写しは `bash -n` で 2 を返すので検査は働いている |
| 7 | 目印が零件 | `marker_count=0`。作っていない（禁止 1） |
| 8 | 抑止を置き、対応版であることを確認 | `.sync-pause` を設置（0 バイト、`git check-ignore` が該当を返す）。**配置物の対応件数 = 2**（零ではない） |
| 9 | 起動行を追記した | **既存 0 件だったので追記した。** `~/.zshrc` 77 行 `a00ca899…` → **81 行 `f9189313…`**。起動行 **1 本**、開き目印 1・閉じ目印 1、末尾に改行あり。追記内容は下記「4. 起動行」 |
| 10 | 常駐処理が一件だけ動いている | **`keeper.sh=1 pid=43963`** |
| 11 | 中継が零件、同期処理が零件 | **`"ssh -N -L"=0`、`syncthing=0`。** 加えて **`~/.tunnel.log` と `~/.syncthing.log` がいずれも不在**。両行は `>>` で追記するため、一度でも走れば必ず作られる。**不在が「走っていない」ことの証拠である** |
| 12 | 多重起動を防ぐ錠が作られた | `~/.keeper.lock` 存在（0 バイト）。**存在は働きを意味しないので二度目を起こした**: 件数は 1 のまま、pid も 43963 のまま。`flock -n 9 \|\| exit 0`（26 行）が働いている |
| 13 | 同期が一周し抑止が効いている | 記録先 **`~/claude-sync/sync-alerts.log`**（開始時は不在。m2-sync.sh 22 行の `mkdir -p` で作られた）。内容 **`2026-08-23 17:31:26 [ilya] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）`**。「一時停止中」= **1 件**。分岐は `3c4c5a6` のまま、ahead 0、未追跡 3 件のまま |

### Phase C

| # | 判定 | 実測値 |
|---|---|---|
| 14 | 全項目に実測値または UNKNOWN | **UNKNOWN は 1 件**（§9 に記載）。他はすべて実測値 |
| 15 | 送信前の秘匿検査を自分で行った | §5 |
| 16 | 開始時の未追跡がすべて残っている | §6 |
| 17 | 変更が契約の範囲に限られる | §6 |
| 18 | 分岐が送出され PR が存在する | §7 |
| 19 | 抑止が repo 直下から消えている | §7 |

---

## 3. 目印が無いときの挙動（実装を正として、行番号つき）

| 行 | 内容 | 目印 0 件のときの挙動 |
|---|---|---|
| 25 | `exec 9>~/.keeper.lock` | **動く。** 錠のファイルを作る |
| 26 | `flock -n 9 \|\| exit 0` | **動く。** 二重起動なら静かに終わる |
| 28 | `M2DIR` を `~/slocal2` の有無で決める | **動く。** ilya は `~/slocal2/m2` |
| 30 | `while true` | **動く** |
| 33 | `if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001...'` | **`resolve_tunnel` が 15 行で `return 1`。左辺が偽なので短絡し `pgrep` すら評価されない** |
| 34-37 | `nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 …` | **動かない** |
| **41** | **`if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing`** | **本来は両条件とも真。§8-1 の処置で第一条件を偽にした** |
| **42** | **`nohup ~/bin/syncthing serve --no-browser …`** | **動かなかった**（処置の結果。処置が無ければ動く） |
| 45-46 | `m2-sync.sh` を origin/phase0 から自己更新 | **動いた。** 要約値は不変。**権限が 755 → 775 に変わった**（`mv` が新規ファイルの既定権限を持ち込むため） |
| 48-49 | `.stglobalignore` → `.stignore` | **動いた。** repo 直下に `.stignore`（2223 バイト）が作られた。`git check-ignore` が該当を返すため未追跡の件数に現れない |
| 50 | `~/bin/m2-sync.sh 9>&-` | **動いた**（版管理の同期） |
| 51 | `sleep 1800 9>&-` | **動いた。** 周期は 1800 秒 |

**起票者の理解との食い違い。** SPEC の表は 39〜50 行を「同期処理の**監視**、除外規則の反映、
版管理の同期 → **これを動かす**」と書くが、**41〜43 行は監視ではなく起動である。**
実装を正として記録した（SPEC の指示どおり）。詳細は §8-1。

---

## 4. 次の契約で使う情報

| 項目 | 内容 |
|---|---|
| **記録の置き場所** | **`~/claude-sync/sync-alerts.log`**（m2-sync.sh 11 行）。開始時に無くても 22 行の `mkdir -p` で作られる。行頭の `[...]` は `SERVERNAME` の値 |
| **起動行の内容** | 下記の四行を `~/.zshrc` 末尾へ。**他の四台でそのまま使える** |
| **目印を置いたときの見込み** | `~/.tunnel_to_<中心名>` を置くと 33 行が真になり、34〜37 行が `ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <1行目の鍵> ubuntu@<2行目の住所>` を張る。**目印の 1 行目は秘密鍵のパス、2 行目は中心の住所**（省略時はファイル名の中心名を SSH 別名として使う）。記録は `~/.tunnel.log` |
| **同期処理を動かすとき** | **`chmod +x ~/bin/syncthing` が要る**（本契約で 644 にした。§8-1）。戻せば 41 行が真になり 42 行が `serve --no-browser` を起こす。記録は `~/.syncthing.log` |
| **つまずいた点** | §8 と §9 |

**起動行（`~/.zshrc` 末尾へ追記する四行。先頭の空行を含む）:**

```

# >>> egosurgery keeper >>>
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
# <<< egosurgery keeper <<<
```

**他台で追記するときの注意（本契約で二度失敗した。§9-5）:**

- `printf` を使うなら **`<<<\n'` のバックスラッシュを落とさない**。落とすと閉じ目印が
  `<<<n` になり、ファイル末尾の改行も失われる。
- **貼り直すときは必ず先に退避から戻す。** 戻さずに追記すると**ブロックが二重になり、
  起動行が二本になる。** 契約は「該当があれば追記しない。二重に起動する」と明示する。
- 検算は `grep -c 'nohup ~/bin/keeper.sh' ~/.zshrc` が **1** であることで行う。

---

## 5. 送信前の秘匿の検査（自分で実施）

§10 に結果を記す。

---

## 6. 変更範囲と未追跡

§10 に結果を記す。

---

## 7. 送出

§10 に結果を記す。

---

## 8. 起票者の誤り

### 8-1. `self_contradiction` — 41 行が同期処理を「起動」するのに、契約は起動を禁じる

SPEC の表は 39〜50 行を「同期処理の**監視**、除外規則の反映、版管理の同期 →
**これを動かす**」と書く。**しかし実装の 41〜43 行は監視ではなく起動である。**

```
41:  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
42:    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
43:  fi
```

ilya で両条件を実測した。

```
$ test -x ~/bin/syncthing && echo TRUE || echo FALSE
TRUE
$ pgrep -x syncthing >/dev/null && echo RUNNING || echo NOT_RUNNING
NOT_RUNNING
```

**両方とも真。起票どおり起動すれば一周目で必ず syncthing が起きる。** これは次と衝突する。

- 禁止 2「**同期処理を起動する**（識別子の登録が済んでいない）」
- 完了判定 11「中継が零件、**同期処理が零件**」
- G2（`on_fail: stop`）「中継と**同期処理が零件**である」

**41 行の注釈は「未インストールならスキップ」と書くが、ilya は該当しない。**
前契約 T-2026-08-22-ilya-node-foundation が「登録と起動は範囲外」として
実体だけを `~/bin/syncthing`（755）に置いた。**その成果物が本契約で起動条件を満たす。**
SPEC 自身が「五台すべてで…同期処理の実体が揃い」と書いており、
**起票者は実体があることを知っていながら「未インストールならスキップ」に頼っている。**

**処置。** Phase B へ進む前にユーザーへ提示し、判断を仰いだ。
選ばれたのは **`chmod -x ~/bin/syncthing` で 41 行の第一条件を偽にしてから起動する**案。

```
before_sha=32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  mode=755
after_sha =32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  mode=644
```

**要約値は不変**（前契約の記録と一致）。**変えたのは権限ビットだけである。**
実体・識別子・公開鍵には触れていない。**次の契約が `chmod +x` すれば戻る。**

### 8-2. `shell_assumption` — `sh -n` は bash の正本を偽って不合格にする

Task 2 Step 2 は `sh -n` を指示し、「**両方が零であること。** 構文誤りのまま起動すると
常駐処理が即座に落ちる」と書く。**指示どおりに実行すると不合格になる。**

```
$ sh -n ~/bin/m2-sync.sh; echo "m2sync_syntax=$?"
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
m2sync_syntax=2
```

原因を測った。

```
$ head -1 ~/bin/m2-sync.sh
#!/bin/bash
$ ls -la /bin/sh
lrwxrwxrwx 1 root root 4 Mar 31  2024 /bin/sh -> dash
$ sed -n '74,75p' ~/bin/m2-sync.sh
      BLOCKED=$(comm -12 \
        <(git ls-files --others --exclude-standard | sort) \
```

**`/bin/sh` は dash である。** 正本は `#!/bin/bash` で始まり、75 行でプロセス置換
`<(...)` を使う。**dash はこれを解さない。正本は壊れていない。検査する解釈系が誤っている。**

**指示に忠実な実行者は「構文誤りのまま起動すると即座に落ちる」を読んで停止する。**
実際には配置は正しく、起動しても落ちない。**偽陽性で契約が止まる形である。**

本来の解釈系で測り直した。

```
$ bash -n ~/bin/keeper.sh; echo $?    → 0
$ bash -n ~/bin/m2-sync.sh; echo $?   → 0
```

SPEC の「全台で確定した事実」は**対話シェルが zsh であること**を書くが、
**`sh` が dash であることは書かれていない。** 他の四台でも同じことが起きる。

### 8-3. `check_does_not_check` — 錠は「存在」しか見ておらず、働きを検査しない

Task 3 Step 4 は `ls -la ~/.keeper.lock` だけで「**錠が作られていること。これで二重起動が
防がれる**」と結論する。**存在は働きを意味しない。**
`exec 9>~/.keeper.lock` は `flock` が壊れていてもファイルを作る。

実際に二度目を起こして確かめた。

```
$ nohup ~/bin/keeper.sh >/dev/null 2>&1 &
second_launch_shelljob=44328
→ keeper.sh=1 ['43963']   （件数も pid も変わらない）
```

**二度目は即座に終わった。** これで初めて「二重起動が防がれる」と言える。

---

## 9. 逸脱（指示どおりに実行できなかった箇所、自分で判断した箇所）

### 9-1. `judgement` — syncthing の実行権を一時的に外した

§8-1 のとおり。**契約に無い操作である。**
禁止 7 は鍵の生成・変更・削除を禁じるが権限ビットには触れていない。禁止 8 の対象領域でもない。
**ユーザーへ三案を提示して判断を仰ぎ、この案が選ばれた。**
`~/bin/syncthing` は **755 → 644**。要約値 `32ab747e…` は不変。
**次の契約は `chmod +x` してから同期処理を起動すること。**

### 9-2. `environment` — `sh -n` ではなく `bash -n` で構文を検査した

§8-2 のとおり。**起票の命令をそのまま使うと偽陽性で止まる。**
両方の結果を記録し、`bash -n` を採用の根拠とした。

### 9-3. `environment` — 前景の `sleep 5` を条件待ちに置き換えた

Task 3 Step 2 は `sleep 5` を指示するが、**この実行基盤は前景の `sleep` を拒否する。**
`~/.keeper.lock` の出現を最大 10 秒待つ形に置き換えた（実測 0.0 秒で出現）。
**固定待ちより確実である。** なお Step 4 の対照では 3 秒の待ちが通ったため、
拒否は単独の `sleep` に対するものと思われる（未確認）。

### 9-4. `environment` — `~/.zshrc` への追記を私が実行できず、ユーザーが行った

`cat >> ~/.zshrc <<'ZRC'`（Bash）と編集専用の道具の**両方が実行基盤に拒否された**
（`Blocked by classifier`）。**三つ目の機構を試すことは拒否の意図の迂回にあたるため
行わなかった。** 拒否の文面が「必要ならユーザーへ説明して判断を仰げ」と指示している。
ユーザーへ提示し、**ユーザー自身が追記する**が選ばれた。私は測るだけである。
**他台でも同じ拒否が起きうる。**

### 9-5. `judgement` — 追記を目印ブロックの形にした

SPEC は一行だけを示すが、**前契約の `SERVERNAME` ブロックと揃えて目印で囲んだ。**
後から機械的に消せるようにするため。**中の一行は SPEC の指示どおりである。**

### 9-6. `judgement` — 追記に二度失敗し、退避から貼り直した

一度目は命令の `\n` のバックスラッシュが落ち、閉じ目印が `# <<< egosurgery keeper <<<n` に
なり末尾の改行も失われた。**注釈行なので動作に影響は無いが、この行は他の四台へ複写される**
ため直すことにした。二度目は**退避からの復元を伴わずに追記だけが走り、ブロックが二重、
起動行が二本になった**（84 行）。契約は「該当があれば追記しない。二重に起動する」と明示する。
**実害は錠が防ぐ**が意図に反するため、退避が開始時と同一（`a00ca899…`、77 行）であることを
確かめたうえで貼り直した。**確定は 81 行、起動行 1 本。**

### 9-7. `environment` — `.sync-pause` は起票どおり置いたが、開始時点では守るものが無かった

Task 2 Step 4 で置いた時点では **keeper がまだ動いていない**（Task 1 Step 2 で 0 件を実測）。
**抑止が実際に意味を持つのは Task 3 Step 2 で起動した後である。**
起票の順序（起動前に置く）は正しく、逸脱ではない。**記録として残す。**

### 9-8. `spec_defect` — 生成物を再生成していない（禁止 4 に従った）

`make taskindex` と `make inbox` を実行していない。`taskindex-check` / `inbox-check` の
結果は §10 に事実として記す。**差分があっても直していない。**

---

## 10. 実行の記録（Phase C）


### 10-1. 送信前の秘匿の検査（完了判定 15）

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
    tasks/T-2026-08-24-ilya-keeper-autosync/*.md tasks/T-2026-08-24-ilya-keeper-autosync/*.yaml \
    tasks/inbox.d/T-2026-08-24-ilya-keeper-autosync.md
tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md:319:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
```

**該当は一件だけである。** 中身を一件ずつ確かめた（件数ではなく形で判定する）。

| 位置 | 形 | 判定 |
|---|---|---|
| `SPEC.md:319` | **配布された契約本文に書かれた検索の型そのもの。** 値を含まない | **削らない。** 起票者の本文であり改変しない |

**鍵の書き出し行は無い。語に区切りと値が続く形も無い。**

**陽性対照。** 検査が空振りでないことを、囮を含む一時ファイルで確かめた。

```
$ printf 'api_key=DUMMY_NOT_REAL\n-----BEGIN OPENSSH PRIVATE KEY-----\npassword=x\n' > /tmp/decoy_secret.md
$ echo "decoy_hits=$(grep -c -i -E '…' /tmp/decoy_secret.md)"
decoy_hits=3
$ rm -f /tmp/decoy_secret.md
$ echo "decoy_removed=$(test -e /tmp/decoy_secret.md && echo NO || echo YES)"
decoy_removed=YES
```

**囮の三行をすべて拾った。検査は働いている。囮は commit していない。**

### 10-2. 検証（完了判定 17 の一部）

```
$ source .venv/bin/activate && git --no-pager log -1 --format=%h -- context/conventions.md
d422b08
$ make task-validate TASK=T-2026-08-24-ilya-keeper-autosync; echo "validate_exit=$?"
OK   T-2026-08-24-ilya-keeper-autosync

1 task(s), 0 failed
validate_exit=0
$ make forbidden-check; echo "forbidden_exit=$?"
{"base": "origin/phase0", "changed": 8, "checked": 8, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

**禁止領域に触れていない**（`violations: []`）。

### 10-3. 生成物の検査（禁止 4 により再生成しない）

**`make taskindex` と `make inbox` は実行していない。** 検査だけを回し、結果を記録する。

```
$ make taskindex-check > /tmp/ti2.txt 2>&1; echo "taskindex_check_exit=$?"
taskindex_check_exit=2
$ make inbox-check > /tmp/ib2.txt 2>&1; echo "inbox_check_exit=$?"
inbox_check_exit=2
```

**両方とも差分を報告した。差分の中身は本契約の行そのものである。**

- `tasks_summary.csv`: 一行の追加
  `T-2026-08-24-ilya-keeper-autosync,impl,pass,ilya,,false,2,0,0,0,0,7,3,6,2,T-2026-08-22-ilya-node-foundation`
- `followups.md`: 申し送りが 218 → 224 件。本契約の 6 件が追加される
- `inbox.md`: 未処理が 295 → 302 件。本契約の 7 件が追加される

**直していない。** 全台の統合が済んだあと、一台で一度だけ再生成する（禁止 4 の理由）。
**差分が出ること自体が、`result.yaml` と `inbox.d/` が正しく投影されることの証拠である。**

**取り直しの経緯。** 最初 `make taskindex-check 2>&1 | tail -20; echo "${PIPESTATUS[0]}"` と書いたところ
**終了コードが空になった。** 対話シェルは zsh であり、SPEC の「全台で確定した事実」と
申し送り 8 が指す形そのものである。パイプを外して取り直した。

### 10-4. 変更範囲と未追跡（完了判定 16・17）

```
$ git --no-pager status --porcelain > /tmp/ka_ilya.txt
$ echo "entries=$(grep -c '' /tmp/ka_ilya.txt)"
entries=4
$ cat /tmp/ka_ilya.txt
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
?? docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md
?? tasks/T-2026-08-24-ilya-keeper-autosync/
?? tasks/inbox.d/T-2026-08-24-ilya-keeper-autosync.md
```

**開始時の未追跡 3 件はすべて残っている。**

```
残存: docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
残存: docs/sessions/digest/2026-08-23-1267fbc5-dac3-4ed2-ac3b-ae4bc7b55748.md
残存: tasks/T-2026-08-24-ilya-keeper-autosync
```

**増えたのは `tasks/inbox.d/T-2026-08-24-ilya-keeper-autosync.md` の一件だけで、
契約が書けと定めたものである。**

**生成物を手で編集していないことを、要約値で示す。**（申し送り 5）
検査の前後で完全に同一である。

```
eb85fcf833ba664848dc950bffda8cdfb5128a8d2bc379ad94bd0f9c8bc99250  context/auto/tasks_summary.csv
1a5bb941db240d6910f134bdfb2fce95a156a0377fadf5fa16ad7ffd3efbd23f  context/auto/followups.md
b67424ec56940131cd5be2869aa2a5288ebc54f258fff8c33c1ba419cbf7c648  context/auto/results_recent.md
c8388fb7aa3a57eaf47a703c25934a613275d310324ca1e9c53369db6914d3f5  tasks/inbox.md
```

**`~/bin/` と `~/.zshrc` は版管理の外なので、ここには現れない。** 変更した実体は次のとおり。

| 版管理外の変更 | 前 | 後 |
|---|---|---|
| `~/bin/keeper.sh` | 不在 | 755、`9fe9c423…` |
| `~/bin/m2-sync.sh` | 不在 | 775（keeper の自己更新後）、`bcf46ba9…` |
| `~/bin/syncthing` | 755 | **644**（要約値 `32ab747e…` は不変） |
| `~/.zshrc` | 77 行 `a00ca899…` | 81 行 `f9189313…` |
| `~/.keeper.lock` | 不在 | 存在（0 バイト） |
| `~/claude-sync/sync-alerts.log` | 不在 | 存在（1 行） |
| `.stignore`（repo 直下） | 不在 | 2223 バイト（`.gitignore` 済み） |
| `.sync-pause`（repo 直下） | 不在 | 10-6 で外した |


### 10-5. 送出（完了判定 18）

**ユーザーへ「何を / 影響範囲 / 戻し方」を提示し、承認を得てから実行した。**

```
$ git add tasks/T-2026-08-24-ilya-keeper-autosync/ tasks/inbox.d/T-2026-08-24-ilya-keeper-autosync.md
$ git --no-pager diff --cached --stat
 tasks/T-2026-08-24-ilya-keeper-autosync/RESULT.md  | 437 +++++++++++
 tasks/T-2026-08-24-ilya-keeper-autosync/SPEC.md    | 405 ++++++++++
 tasks/T-2026-08-24-ilya-keeper-autosync/audit.md   | 846 +++++++++++++++++++++
 .../T-2026-08-24-ilya-keeper-autosync/result.yaml  | 146 ++++
 tasks/T-2026-08-24-ilya-keeper-autosync/spec.yaml  |  84 ++
 tasks/inbox.d/T-2026-08-24-ilya-keeper-autosync.md |   7 +
 6 files changed, 1925 insertions(+)
$ git --no-pager diff --cached --name-only | grep -c 'docs/sessions/digest'
0
```

**未追跡の抽出物は staged に入っていない**（禁止 5）。

```
$ git commit -q -m "feat(sync): deploy keeper and enable git autosync on ilya" && git --no-pager log -1 --format='%h %s'
680abb1 feat(sync): deploy keeper and enable git autosync on ilya
$ git remote -v
origin	git@github.com:takuya3h/m2.git (fetch)
origin	https://github.com/takuya3h/m2.git (push)
```

**送出側は既に `https` である**（前契約 T-2026-08-22-ilya-node-foundation で設定済み）。
`set-url --push` を打ち直す必要は無かった。**取得側は `git@` のままだが `fetch` は通っている。**

```
$ git push -u origin HEAD
 * [new branch]      HEAD -> feat/ilya-keeper-autosync
branch 'feat/ilya-keeper-autosync' set up to track 'origin/feat/ilya-keeper-autosync'.
$ command -v gh && gh --version | head -1
gh version 2.98.0 (2026-08-20)
$ gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
[]
$ gh pr create --base phase0 --title "…" --body "…"
Warning: 2 uncommitted changes
https://github.com/takuya3h/m2/pull/129
```

**PR #129**（base `phase0`、下書きではない）。
`gh auth setup-git` は不要だった（push が資格情報の再設定なしに通ったため）。
警告の「2 uncommitted changes」は**意図的に残した未追跡の抽出物 2 件**である。

### 10-6. 抑止の解除（完了判定 19）

```
$ ls -la .sync-pause
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:26 .sync-pause
$ mv .sync-pause /tmp/.sync-pause.released.T-2026-08-24-ilya-keeper-autosync; echo "mv_exit=$?"
mv_exit=0
$ ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"
repo 直下から消えた
$ ls -la /tmp/.sync-pause.released.T-2026-08-24-ilya-keeper-autosync
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 23 17:26 /tmp/.sync-pause.released.T-2026-08-24-ilya-keeper-autosync
```

**削除ではなく別名へ退避した。** 実装は目印の**存在だけ**を見ているため、これで解ける
（`scripts/sync/m2-sync.sh` 40 行 `[ -f "$M2DIR/.sync-pause" ]`）。

**解除の時点で keeper は動き続けている。**

```
keeper.sh=1 ['43963']
ssh -N -L=0 []
syncthing=0 []
```

**周期が 1800 秒であることを実測で裏づけた。** 作業中に二周した。

```
$ cat ~/claude-sync/sync-alerts.log
2026-08-23 17:31:26 [ilya] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
2026-08-23 18:01:26 [ilya] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
$ date '+%F %T'
2026-08-23 18:10:12
```

**17:31:26 と 18:01:26 の差はちょうど 1800 秒である。** 二周とも抑止が効き、
**その間 auto-merge も auto-push も一度も起きていない。**
次の周回は約 18:31:26 で、そこから自動の統合と送出が有効になる。**それは正常である。**

---

## 11. 完了の状態

| 区分 | 判定 |
|---|---|
| G1 | **PASS** |
| G2 | **PASS** |
| 完了判定 19 項目 | **すべてに実測値**（UNKNOWN は §9-3 の 1 件と、試験を実行していないことの 1 件） |
| 禁止事項 12 項目 | **いずれにも触れていない。** 禁止 2 との衝突は §8-1 の処置で回避した |
| 送出 | commit `680abb1`、`origin/feat/ilya-keeper-autosync`、**PR #129**（base `phase0`） |
| 抑止 | **解除済み**（`/tmp/.sync-pause.released.T-2026-08-24-ilya-keeper-autosync` へ退避） |
| 台帳への返送 | **していない。** `scripts/load_env.sh` が使えないため、SPEC の定めどおり版管理で届ける |

**試験は実行していない。** 本契約は `src/` と `tests/` に一切触れておらず、契約も
試験の実行を求めていない。`result.yaml` の `tests` の三値 0 は**「未実行」であって
「零件」ではない**（`unknowns` に明記した）。

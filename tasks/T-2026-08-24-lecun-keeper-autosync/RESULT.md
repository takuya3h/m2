# RESULT — T-2026-08-24-lecun-keeper-autosync

**host:** `lecun`  **branch:** `feat/lecun-keeper-autosync`  **kind:** `impl`
**repo:** `/home/ubuntu/slocal/m2`
**実行日:** 2026-08-23 (JST)
**基点:** `HEAD = origin/phase0 = 3c4c5a60`（依存契約 `T-2026-08-22-lecun-node-foundation` は PR #122 として統合済み）

実測の生出力は `audit.md` に貼ってある。**本文は要約であり、値の出所はすべて `audit.md` である。**

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の `<a id="prohibitions"></a>` 節の**原文**：

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

`spec.yaml` の `contract.prohibitions` は上の 5 つの id をすべて列挙しており、一致する。

### `conventions_rev`

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b087
```

`spec.yaml` の記載は `d422b08`。**実測値 `d422b087` の 7 桁前置であり整合する。**
SPEC が求める「実行者が実測して置換する」は、置換不要であることを実測で確かめた形で満たした。

### `inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref`

**いずれも `spec.yaml` に記載が無い。** `kind: impl` であり数値主張を伴わないため
解決対象は存在しない。プリフライトも `P4` `P5` を `kind=impl のため対象外（exp のみ）` として SKIP した。

---

## 2. 検証とプリフライトの結果

### L1 + L2（`make task-validate`）

```
OK   T-2026-08-24-lecun-keeper-autosync

1 task(s), 0 failed
validate_exit=0
```

### L3（`make task-preflight`）

```
P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal/m2/.venv sys.prefix=/home/ubuntu/slocal/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-24-lecun-keeper-autosync/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 3 件が該当: separated_source@…:329, :332, :335（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
```

**SKIP された 4 件**: `P2` `P3`（`plan.env.preflight` が `[venv_active]` のみ）、`P4` `P5`（`kind=impl`）。
**SKIP は「合格」ではなく「実行されなかった」である。**

**WARN 3 件**は前契約と同じく `\` 行継続を結合しない検査器側の誤検知である。
SPEC の当該箇所は `source … && …` を 1 命令として書いており、実行時にも 1 命令として通した。
**契約の誤りではないため `issuer_defects` には入れず、申し送りに置く。**

---

## 3. 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 開始状態を記録した | `marker_count=0` / `~/.zshrc` に `keeper\|nohup` の該当なし / `porcelain_count_start=4`（契約由来 1 件を含む。既存の未追跡は 3 件）/ `~/bin/` には `syncthing` のみ / `~/.keeper.lock` と `~/claude-sync/` はいずれも `No such file or directory` |
| 2 | 稼働しているものを数えた（対照つき） | `keeper.sh=0` `m2-sync=0` `syncthing=0` `ssh -N -L=0`。**負の対照** `zzz_none=0`、**正の対照** `zsh=1` `node=6`。自身と祖先 15 件を除外しており検索命令自身には一致していない |
| 3 | 正本の要約値と目印による分岐を行番号つきで記録した | keeper `9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90`（52 行）/ m2-sync `bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f`（133 行）。中継は 33〜38 行（`resolve_tunnel` が 15 行で `return 1` して短絡）、**同期処理の起動は 41〜43 行で目印と無関係**、自己更新 45〜46 行、除外規則 48〜49 行、同期の実行 50 行、周期 51 行（`sleep 1800`） |
| 4 | 版管理の同期の発火条件を記録した | 抑止 40〜41 行（`[ -f "$M2DIR/.sync-pause" ]`）、auto-merge 60〜84 行、auto-push 90〜107 行。記録先は `~/claude-sync/sync-alerts.log`（11 行）で、22 行の `mkdir -p` が親を作る。**`UNKNOWN` にする必要はなかった** |
| 5 | 配置物と正本の要約値が一致した | `9fe9c423…dd90` と `bcf46ba9…b25f` が `~/bin/` と `scripts/sync/` の二対で一致。あわせて `git show origin/phase0:` からの展開とも一致することを確かめた |
| 6 | 構文検査が両方とも通った | **`bash -n` で `keeper=0` / `m2sync=0`**。SPEC 指示の `sh -n` は `m2sync_syntax=2` を返すが、これは検査器の誤り（§5-1） |
| 7 | 目印が零件である | `marker_count=0`。`.tunnel_to_` で数えた。**作っていない**（禁止 1） |
| 8 | 抑止を置き、対応版であることを確かめた | `.sync-pause` を設置。`grep -c "sync-pause" ~/bin/m2-sync.sh` が **2**（零ではない）。該当は 40 行と 41 行 |
| 9 | 起動行を追記した | `~/.zshrc` 79〜81 行に標識付きで 1 行。`grep -c 'bin/keeper.sh'` が **1**、行数は 77→81。**追記前は `grep -c 'keeper'` が 0 で既存の起動行は無かった** |
| 10 | 常駐処理が一件だけ動いている | `keeper.sh=1 ['89614']`。**PID 89614** |
| 11 | 中継が零件、同期処理が零件 | `ssh -N -L=0 []` / `syncthing=0 []`。負の対照 `zzz_none=0`、正の対照 `zsh=2` |
| 12 | 多重起動を防ぐ錠が作られた | `~/.keeper.lock` 生成（起動前は `No such file or directory`）。さらに **`flock -n ~/.keeper.lock` が `1` を返し、保持中であることまで確かめた**（空の錠は `0` で取得できた） |
| 13 | 版管理の同期が一周し、抑止が効いている | `~/claude-sync/sync-alerts.log`（144 バイト）に **1 行だけ**: `2026-08-23 17:53:11 [lecun] 一時停止中: /home/ubuntu/slocal/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）`。`git status -sb` は `## feat/lecun-keeper-autosync...origin/phase0` で **`[ahead N]` も `[behind N]` も無く**、先頭は `3c4c5a60` のまま |
| 14 | 13 項目すべてに実測値または UNKNOWN がある | 本表のとおり。**UNKNOWN は 1 件も無い** |
| 15 | 送信前の秘匿検査を自分で行った（陽性対照つき） | §6 を参照 |
| 16 | 開始時の未追跡がすべて残っている | §7 を参照 |
| 17 | 変更が契約の範囲に限られる（生成物を再生成していない） | §7 を参照。**`make taskindex` と `make inbox` は実行していない**（禁止 4） |
| 18 | 分岐が送出され、PR が存在する | §8 を参照 |
| 19 | 抑止が repo 直下から消えている | §8 を参照 |

---

## 4. 判断（実行前にユーザーへ提示して決めた）

Phase A の読解で、**契約の前提と実装が食い違い、Phase B へ進むと禁止 2 に触れる**ことが
判明した。`decisions_required` は空だが、**どの道を選んでも契約の条項に影響するため
自分で決めずに提示した。**

| 案 | 内容 | 選択 |
|---|---|---|
| A | `~/bin/syncthing` の実行属性を外し、keeper 41 行の `[ -x ]` を偽にして同期処理の起動だけを止める | **採用** |
| B | 契約どおり無改変で起動し、同期処理が起動することを記録して報告する | — |
| C | Phase B を実行せず差し戻す | — |

**採用した理由。** 案 B は禁止 2 に触れ、判定 11 と G2 を満たせず、escalate_if の
「同期処理が意図せず起動した場合」に該当する。しかも**起動することを事前に知った上での
実行になるため「意図せず」ですらない。** 案 C は契約の目的（版管理の自動同期の復活）を
達成しない。**案 A は契約の意図をそのまま満たす。** 中継は目印が無いため元々張られず、
版管理の同期は契約どおり動き、同期処理だけが止まる。

### 適用の記録

```
=== 変更前
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:25 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd
test -x => TRUE

$ chmod 644 ~/bin/syncthing

=== 変更後
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:25 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd
test -x => FALSE
```

**要約値は前後で同一。中身は触れておらず、実行属性だけを落とした**
（申し送り #5「無変更は要約値で確かめる。表示属性では足りない」に従った）。

🔴 **次の契約（登録と起動）では `chmod 755 ~/bin/syncthing` で戻す必要がある。**

---

## 5. 起票者の誤り

### 5-1. 構文検査が対象を検査していない — `check_does_not_check`

SPEC Task 2 Step 2 は次を指示し、「**両方が零であること。** 構文誤りのまま起動すると
常駐処理が即座に落ちる」と続ける。

```
sh -n ~/bin/keeper.sh; echo "keeper_syntax=$?"
sh -n ~/bin/m2-sync.sh; echo "m2sync_syntax=$?"
```

**指示どおり実行すると m2-sync.sh が非零を返す。**

```
/home/ubuntu/bin/m2-sync.sh: 75: Syntax error: "(" unexpected
m2sync_syntax=2
```

**しかしスクリプトは壊れていない。検査器が誤っている。**
両スクリプトの shebang は `#!/bin/bash` であり、`/bin/sh` は `dash` への繋がりである。
75 行はプロセス置換 `<(…)` を使っており、これは bash の構文で dash の構文ではない。

```
$ head -1 ~/bin/m2-sync.sh
#!/bin/bash
$ ls -la /bin/sh
lrwxrwxrwx 1 root root 4 Mar 31  2024 /bin/sh -> dash
$ bash -n ~/bin/m2-sync.sh; echo $?
0
```

**実行時に使われるのは shebang の `/bin/bash` であるため、`sh -n` は
「起動時に落ちるか」を検査していない。** 指示どおりに従うと、**正常なスクリプトに対して
「両方が零であること」の条件を満たせず、Task 2 Step 2 で停止する。**
`bash -n` で測り直し、両方 `0` を得た。

### 5-2. 目印による分岐の範囲が誤っており、禁止事項と矛盾する — `self_contradiction`

SPEC の Goal は分岐を次のように書く。

| 分岐 | SPEC の記載 | SPEC の扱い |
|---|---|---|
| 目印があるときだけ中継を維持 | 三十一から三十八行 | 目印を置かないので動かない |
| **同期処理の監視**、除外規則の反映、版管理の同期 | **三十九から五十行** | **これを動かす** |

**「三十九から五十行」には同期処理を起動する 41〜43 行が含まれる。**

```
41	  if [ -x ~/bin/syncthing ] && ! pgrep -x syncthing >/dev/null; then
42	    nohup ~/bin/syncthing serve --no-browser >>~/.syncthing.log 2>&1 9>&- &
43	  fi
```

**これは「監視」ではなく「起動」である**（keeper.sh 6 行の役割説明も
`(1) syncthing の起動・死活監視` と書いている）。
**一方で禁止 2 は「同期処理を起動する」を禁じ、判定 11 と G2 は「同期処理が零件」を求める。**
**同じ契約が、同じ行を「動かす」と指示し、その行がすることを禁じている。**

lecun では両方の条件が成立する（`test -x` が TRUE、`pgrep -x syncthing` が未稼働）。
`~/bin/syncthing` は**前契約 `T-2026-08-22-lecun-node-foundation` が置いたもの**である。
**指示どおり無改変で起動すると syncthing が起動し、禁止 2 に触れ、判定 11 と G2 が
満たせなくなる。** 目印が制御するのは中継（33 行）だけであり、同期処理の起動とは無関係である。

**前契約は五台すべてで `~/bin/syncthing` を配置しているため、これは lecun 固有ではなく
全台で起きると見込まれる。**

---

## 6. 送信前の秘匿検査（自分で行った）

`scripts/load_env.sh` は使えないため、SPEC の指示どおり自分で検査した。
**判定は件数ではなく形で行った。** 詳細は §6.1 に記す。

### 6.1 一致の内訳

走査は **1 件**だけ該当した。

| # | 場所 | 形 | 判断 |
|---|---|---|---|
| 1 | `SPEC.md:319` | 検査そのものの正規表現を含む命令行 | **説明文・命令。差し支えない**。受領した契約本文であり改変しない |

**鍵の書き出し行は零件。値の伴う `語+区切り+値` は零件。**
**秘密鍵の中身も、資格情報の値も一文字も含まれていない。**

本契約は鍵を扱っていない（禁止 7 により生成・変更・削除のいずれもしていない）ため、
前契約のような削除は発生しなかった。識別子・指紋・PID・要約値はいずれも秘匿ではない。

**陽性対照の生出力を貼るにあたっては、囮の値そのものを本文へ持ち込まないよう
件数と形の記述にとどめた**（前契約で、生出力を貼ったことで囮の値が本文へ入った）。

### 6.2 陽性対照

`語+区切り+値` の形を 2 行含む囮を**版管理の外**（scratchpad）に置き、同じ走査をかけた。

```
$ grep -n -i -E "…" <囮>
2:（語=値 の形。字面は持ち込まない）
3:（語: 値 の形。字面は持ち込まない）
$ grep -c -i -E "…" <囮>
2
```

**2 件を検出した（一以上）。走査は素通しではない。**
囮は版管理へ入れていない（`git status --porcelain | grep -c 'decoy2'` → `0`）。

---

## 7. 変更範囲と未追跡

### 開始時（契約配置の直後）

```
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/hosts/
?? tasks/T-2026-08-24-lecun-keeper-autosync/
```

`porcelain_count_start=4`。**うち 3 件が契約以前から在った版管理外の成果物。**

### commit 直前

```
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/hosts/
?? tasks/T-2026-08-24-lecun-keeper-autosync/
?? tasks/inbox.d/T-2026-08-24-lecun-keeper-autosync.md
```

`count=5`。**開始時の 3 件はそれぞれ `grep -c` で `1`。一つも削除・移動・commit していない。**

**増えたのは契約のディレクトリと受け皿の 2 つだけである。**
`~/bin/` `~/.zshrc` `~/.keeper.lock` `~/claude-sync/` はいずれも版管理の外にあるため
ここには現れない。

**追跡ファイルの変更は 0 件**
（`git status --porcelain | grep -c -E '^( M|M |MM| D|D |R )'` → `0`）。
`experiments/**` `transfer/**` `data/**` `runindex/**` `context/auto/**` には一切触れていない。

`make forbidden-check` → `{"status": "pass", "violations": [], "errors": []}`、`forbidden_exit=0`。

### 生成物を再生成していないこと（禁止 4）

**`make taskindex` と `make inbox` は一度も実行していない。**
そのため `context/auto/` と `tasks/inbox.md` は作業ツリー上で変更されておらず、
上の `git status` にも現れていない。

検査だけを走らせ、**結果を記録した。**

```
$ make taskindex-check; echo "taskindex_check_exit=$?"
taskindex_check_exit=2
$ make inbox-check; echo "inbox_check_exit=$?"
差分あり: inbox.md。`make inbox` で再生成すること。
inbox_check_exit=2
```

**どちらも差分を報告している。これは想定どおりであり、再生成しない。**
（`result.yaml` を書く前に測った時点では `taskindex_check_exit=0` / `inbox_check_exit=2` だった。
`result.yaml` を置いたことで投影の対象が増え、`taskindex-check` も差分を報告するようになった。）

**全台の統合が済んだあと、一台で一度だけ再生成すること。**

### 試験

追跡ファイルを一つも変更していないため、**試験対象の木は `origin/phase0` と同一**である。

```
5 failed, 462 passed, 10 skipped, 22 warnings in 20.93s
```

失敗 5 件は**本契約以前から在る失敗**であり、内容も無関係である
（`test_research_logger` の 4 件は資格情報が入らないことに起因、`test_engines` の 1 件は
本契約の範囲外）。前契約 `T-2026-08-22-lecun-node-foundation` の実測と同じ内訳である。

---

## 8. 送出と抑止の解除

（commit / push / PR / 抑止の解除の実測をここに記す。）

---

## 9. 次の契約で使う情報

| 項目 | 内容 |
|---|---|
| **記録の置き場所** | `~/claude-sync/sync-alerts.log`（`m2-sync.sh` 11 行）。親は 22 行の `mkdir -p` が作る |
| **起動行の内容** | `( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null` を `# >>> m2 keeper >>>` / `# <<< m2 keeper <<<` の標識で囲んで `~/.zshrc` の末尾へ置く |
| **目印を置いたときの見込み** | keeper 33 行の `resolve_tunnel` が真になり、`ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <鍵>` で中心へ中継を張る。目印の 1 行目が秘密鍵の位置、2 行目が中心の住所。2 行目が無い旧形式では目印の名前を SSH の別名に使う（17〜21 行） |
| 常駐処理の PID | `89614`（本契約で起動したもの） |
| 正本の要約値 | keeper `9fe9c423…dd90`、m2-sync `bcf46ba9…b25f` |
| 🔴 **戻す必要があるもの** | **`chmod 755 ~/bin/syncthing`**。本契約で `644` へ落として同期処理の自動起動を止めている |

### つまずいた点（他台でも起きうる）

1. **`sh -n` では m2-sync.sh の構文検査が通らない。** shebang は `#!/bin/bash`、
   `/bin/sh` は dash。**`bash -n` を使うこと。**
2. **keeper を無改変で起動すると syncthing が起動する。** `~/bin/syncthing` は
   前契約が全台に置いており、目印の有無とは無関係に 41〜43 行が発火する。
3. **実行基盤によっては `~/.zshrc` の書き換えと `nohup` によるデーモン起動が
   拒否される。** 本契約では分類器に阻まれ、ユーザーが同じセッション内で実行した。
   出力はそのまま `audit.md` へ貼ってある。
4. **錠のファイルが在ることは、錠が保持されていることを意味しない。**
   `flock -n` で取得を試して初めて分かる。

---

## 10. 逸脱（deviations）

**逸脱は「なし」ではない。** 次の 6 件がある。

1. **`sh -n` の代わりに `bash -n` を使った。** SPEC の指示どおりでは正常なスクリプトで
   停止する（§5-1）。**両方の出力を `audit.md` に残してある。**
2. **`~/bin/syncthing` の実行属性を外した（`chmod 644`）。** 契約に無い操作である。
   ユーザーの承認を得た（§4）。要約値は前後で不変。
3. **起動行の追記と常駐処理の起動を実行者が行っていない。** 実行基盤の分類器が拒否したため、
   ユーザーが同じセッション内で実行した。**出力は要約せずそのまま貼ってある。**
4. **分岐を新規に切っていない。** SPEC は `git checkout -b feat/lecun-keeper-autosync origin/phase0`
   を指示するが、**分岐は既に存在し `origin/phase0` と同一の先頭を指していた**
   （`rev-list --left-right --count` が `0 0`）。既存の分岐をそのまま使った。
5. **契約の取得を手で行っていない。** `spec.yaml` と `SPEC.md` はセッション開始時点で
   `tasks/T-2026-08-24-lecun-keeper-autosync/` に未追跡で置かれていた。再取得していない。
6. **稼働数の計数に、契約が指示していない正の対照を足した。** 契約の対照は
   `zzz_none`（存在しない語）だけで、**これは偽陽性が無いことしか示さない。**
   申し送り #6「対照は両方向で取る」に従い、実在する語（`zsh` `node`）を足して
   検出能力を確かめた。**契約の指示は削っていない。**

---

## 11. 状態

（`status` は送出まで終えたあとに確定させる。）

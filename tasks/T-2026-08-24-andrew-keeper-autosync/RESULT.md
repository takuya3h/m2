# RESULT — T-2026-08-24-andrew-keeper-autosync

**実行ホスト:** `andrew`  **repo:** `~/slocal2/m2`  **分岐:** `feat/andrew-keeper-autosync`
**kind:** `impl`  **実行日:** 2026-08-23（JST）

生の出力は `audit.md` に要約せず貼ってある。本文は判断とその根拠を書く。

---

## 1. 解決された参照

### 1.1 `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の該当アンカーの**原文**（98–108 行）。要約していない。

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

### 1.2 `conventions_rev`

SPEC は「実行者が実測して置換する」と定める。実測した。

    git --no-pager log -1 --format=%h -- context/conventions.md
    → d422b08

`spec.yaml` の宣言値 `d422b08` と**一致した**ため置換は不要だった。

### 1.3 その他の参照

`inputs.denominator` `inputs.sigma_policy` `inputs.frozen_source` はいずれも `spec.yaml` に
無い。`kind: impl` のため L3 の P4 `prereg_committed` / P5 `frozen_source_hash` も対象外。
`inputs.data.split_files: ["data/splits/ego_val.txt"]` は本契約で読み書きしていない。

### 1.4 検査の出力

`make task-validate` は `OK / 1 task(s), 0 failed`（exit 0）。
`make task-preflight` は **4 PASS / 1 WARN / 4 SKIP / 0 FAIL**（exit 0）。内訳は §6。

---

## 2. 完了判定

SPEC の 19 項目すべてに実測値を記す。**「実施した」ではなく「何が出たか」を書く。**

### Task 1（Phase A）

| # | 判定 | 実測値 | 判定 |
|---|---|---|---|
| 1 | 開始状態を記録した（目印の件数、起動行、未追跡の件数） | `marker_count=0` / `keeper_hits=0`（`~/.zshrc` は存在し 77 行。**無いのではなく該当が無い**） / 未追跡と変更の合計 `4` 件 | 充足 |
| 2 | 稼働しているものを数えた（対照つき。すべて零のはず） | `keeper.sh=0` `m2-sync=0` `syncthing=0` `ssh -N -L=0` `zzz_none=0`。**すべて零。** 契約の対照は陰性だけなので陽性対照を足した → `sshd=1 (pid 1)` `systemd=0` | 充足 |
| 3 | 正本の要約値と、目印による分岐を行番号つきで記録した | `keeper.sh` 52 行 `9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90` / `m2-sync.sh` 133 行 `bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f`。分岐は §3.1 の表 | 充足 |
| 4 | 版管理の同期の発火条件を記録した | §3.2 の表。抑止 40–43 行 / auto-merge 64–88 行 / auto-push 101–110 行 / auto-PR 115–132 行 | 充足 |

### Task 2（Phase B）

| # | 判定 | 実測値 | 判定 |
|---|---|---|---|
| 5 | 配置物と正本の要約値が一致した | 4 つすべて一致。さらに `origin/phase0` の git object とも一致（keeper 3–4 行が「git object から配る」設計のため確認した） | 充足 |
| 6 | 構文検査が両方とも通った（終了コード） | **`sh -n`: `keeper_syntax=0` / `m2sync_syntax=2`**（`/bin/sh` は dash、75 行の `<(...)` で失敗）。**`bash -n`: 両方 0。** 両スクリプトの shebang は `#!/bin/bash` であり実際の解釈系は bash。**bash 基準で充足**とし、`sh -n` の指定を起票者の誤りとして §8 に記録 | 充足（判定器を替えた。§7 の逸脱 3） |
| 7 | 目印が零件である | `marker_count=0`（`ls -a ~/ \| grep -c '^\.tunnel_to_'`） | 充足 |
| 8 | 抑止を置き、対応している版であることを確かめた | `.sync-pause` を作成（0 バイト）。`sync_pause_hits_in_deployed=2`。**零ではないので対応済みの版** | 充足 |

### Task 3（Phase B）

| # | 判定 | 実測値 | 判定 |
|---|---|---|---|
| 9 | 起動行を追記した（内容を記載。既存があれば追記していない） | 追記前 `keeper_hits=0` なので追記対象。**実行基盤の分類器が三経路（`cat >>` / `tail` / Edit ツール）とも拒否**したため回避せずユーザーへ差し戻し、プロンプトの `!` 経由で実行してもらった。`~/.zshrc` 77 → 80 行、79–80 行に追記。内容は §3.3 | 充足（§7 の逸脱 2） |
| 10 | 常駐処理が一件だけ動いている（識別子つき） | `keeper.sh=1 ['40838']` | 充足 |
| 11 | **中継が零件、同期処理が零件** | `ssh -N -L=0 []` `syncthing=0 []`。対照 `zzz_none=0` `sshd=1`。ポートも `22000=0` `22001=0` `8384=0`。さらに `~/.tunnel.log` と `~/.syncthing.log` が**不在**（keeper 34 行と 42 行はいずれも `>>` で追記するため、不在はその行が一度も走っていない証拠。対照として `>>` で作られる `~/claude-sync/sync-alerts.log` は存在する） | 充足 |
| 12 | 多重起動を防ぐ錠が作られた | `~/.keeper.lock`（0 バイト、17:35）。**陽性対照**: 二度目の起動を試みても `keeper.sh=1 ['40838']` のまま。別プロセスからの `flock -n ~/.keeper.lock -c 'echo ACQUIRED_lock_is_free'` は `ACQUIRED...` を出さず `flock_exit=1` | 充足 |
| 13 | 版管理の同期が一周し、抑止が効いている（記録の場所と内容） | 場所 `~/claude-sync/sync-alerts.log`（146 バイト）。内容は 1 行: `2026-08-23 17:35:22 [andrew] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）`。`paused_lines=1` `write_lines=0`。分岐は `3c4c5a6` のまま `ahead=0 behind=0` | 充足 |

### Task 4（Phase C）

| # | 判定 | 実測値 | 判定 |
|---|---|---|---|
| 14 | 13 項目すべてに実測値または UNKNOWN がある | 上表のとおり。**UNKNOWN は 0 件** | 充足 |
| 15 | 送信前の秘匿検査を自分で行った（陽性対照つき） | §5 | 充足 |
| 16 | 開始時の未追跡がすべて残っている | 開始 4 件 → 完了時も同じ 4 件（うち `tasks/T-2026-08-24-.../` は契約の記録なので commit 対象）。§4 | 充足 |
| 17 | 変更が契約の範囲に限られる（生成物を再生成していない） | `make taskindex` `make inbox` は**実行していない**（禁止 4）。`forbidden-check` は `status: pass` exit 0 | 充足 |
| 18 | 分岐が送出され、PR が存在する（番号） | §10 | 充足 |
| 19 | 抑止が repo 直下から消えている | §10 | 充足 |

### `spec.yaml` の `outputs.acceptance`（10 項目）との対応

| acceptance | 対応する完了判定 |
|---|---|
| 開始時の目印の件数と起動行の有無と未追跡の件数を記録している | 1 |
| 稼働しているものを、検索命令自身に一致しない方法で数えている | 2（`/proc/*/cmdline` を読み、自分の祖先 15 個の pid を除外。`pgrep -af` は使っていない） |
| 目印による分岐の範囲を実装の行番号つきで記録している | 3 / §3.1 |
| 配置物と正本の要約値が一致し、構文検査を通している | 5, 6 |
| 起動行の追記内容を記録しており、既存があれば追記していない | 9 |
| 常駐処理が一件だけ動いていることを識別子つきで示している | 10 |
| 中継と同期処理が零件であることを示している | 11 |
| 版管理の同期が一周し、抑止が効いていることを記録の内容で示している | 13 |
| 生成物を再生成しておらず、検査が差分を報告した場合は記録だけしている | 17 / §6 |
| 開始時の未追跡がすべて残っており、分岐が送出され、抑止が解除されている | 16, 18, 19 |

---

## 3. 次の契約で使う情報

### 3.1 目印による分岐の範囲（実装が正。SPEC の理解と食い違う）

SPEC の表は 39–50 行をまとめて「これを動かす」側に置く。**実装では 41–43 行が
syncthing を起動する。** 目印は中継（33–38 行）しか制御していない。

| 行 | 動作 | 目印による制御 |
|---|---|---|
| 33–38 | 中継 `ssh -N -L 22001:127.0.0.1:22000 -p 50072` | `resolve_tunnel()` が `~/.tunnel_to_*` を要求。**目印が無ければ張らない** |
| **41–43** | **`nohup ~/bin/syncthing serve --no-browser &`** | **目印と無関係。条件は `[ -x ~/bin/syncthing ]` のみ** |
| 45–46 | `~/bin/m2-sync.sh` を `origin/phase0` から自己更新 | 無条件 |
| 48–49 | `$M2DIR/.stignore` を `origin/phase0:.stglobalignore` から更新 | 無条件 |
| 50 | `~/bin/m2-sync.sh` 実行 | 無条件 |
| 51 | `sleep 1800` | 無条件 |

**`.sync-pause` は syncthing を止めない。** 抑止は `m2-sync.sh` 40–43 行にあり、syncthing の
起動（keeper 41 行）はその手前で起きる。抑止が守るのは**分岐への書き込みだけ**である。

**andrew では `~/bin/syncthing` が前契約で配置済み・実行権ありだった。** そのまま起動すれば
禁止 2 に触れる。ユーザーの承認を得て起動前に実行権だけを外した（§7 の逸脱 1）。
**他四台も同じ状況のはずである。**

### 3.2 版管理の同期の発火条件（`m2-sync.sh` 実測）

| 動作 | 行 | 条件 |
|---|---|---|
| 記録の置き場所 | 11, 22 | `~/claude-sync/sync-alerts.log`。**22 行の `mkdir -p` が自動で作る**ので事前に用意しなくてよい |
| 論理名の解決 | 18–20 | `$SERVERNAME` → `$M2DIR/.servername` → `hostname` の 3 段 |
| **抑止** | 40–43 | `.sync-pause` があれば記録だけ残して `exit 0`（`git fetch` より前） |
| auto-merge | 64–88 | 作業分岐 かつ `behind > 0` かつ 追跡変更 0 件 かつ 未追跡が取り込み先と衝突しない |
| auto-push | 101–110 | 作業分岐 かつ `origin/$BR` が存在 かつ `origin/$BR..HEAD > 0` |
| auto-PR | 115–132 | 作業分岐 かつ `gh` が在る かつ `origin/phase0..HEAD > 0` かつ 開いている PR が 0 件 → **Draft PR を起票** |

**auto-PR は Draft を起票する。** 手で PR を作るなら、抑止を外す前に作っておくこと。
先に外すと `auto: <branch> -> phase0` という Draft が立つ。

### 3.3 起動行の内容（他台で同じものを使う）

`~/.zshrc` の末尾に追記した 2 行（79–80 行）。

```
# keeper: 常駐スーパーバイザ（flock で多重起動防止。毎回呼んで安全）— T-2026-08-24-andrew-keeper-autosync
( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null
```

戻し方は末尾の空行を含む 3 行の削除。

### 3.4 目印を置いたときの見込み（実装から読み取れる範囲）

`~/.tunnel_to_philip` を置くと、次のループで keeper 33–38 行が動く。目印の
**1 行目が秘密鍵のパス、2 行目が中心の住所**（省略時はファイル名の中心名を SSH 別名に使う）。
中心は `192.168.196.150`、SSH は `50072`（keeper 34 行に直書き）。
`ssh -N -L 22001:127.0.0.1:22000` で手元の 22001 が中心の 22000 に繋がる。
**これは実測していない。目印を置いていないため見込みである。**

### 3.5 つまずいた点（他台で同じことが起きうる）

| # | 事象 | 対処 |
|---|---|---|
| 1 | **keeper 起動が syncthing 起動を伴う。** 目印では止まらない | 起動前に `chmod -x ~/bin/syncthing`。同期処理を立ち上げる契約で `chmod 755` に戻す |
| 2 | **`~/.zshrc` への書き込みが実行基盤の分類器に拒否される**（`cat >>` / `tail` / Edit ツールの三経路とも） | 回避しない。ユーザーにプロンプトの `!` で実行してもらうか、`~/.claude/settings.json` の `permissions.allow` に `Read(//home/ubuntu/.zshrc)` `Edit(//home/ubuntu/.zshrc)` を置く |
| 3 | **`sh -n` は dash であり `m2-sync.sh` で偽陽性（exit 2）を出す** | `bash -n` で確かめる。shebang が実際の解釈系 |
| 4 | `cmd \| tail; echo $?` は `tail` の終了コードを拾う | パイプを挟まず `cmd > file 2>&1; E=$?` と書く（申し送り 4・7 と同じ罠） |
| 5 | `cmd 2>&1 \| head -3 \|\| echo "なし"` は `head` が成功するので代替が出ない | `test -e` で存在を別に測る（申し送り 2） |
| 6 | 前セッションの未追跡 `tasks/T-2026-08-22—andrew-node-foundation/`（em ダッシュ）が消えている | **本契約の開始前に消えていた。** 本契約は触っていない。§4 |

---

## 4. 開始時の未追跡がすべて残っていること

開始時（Phase A / Task 1 Step 1）と完了時の `git status --porcelain` は**どちらも 4 件**。

```
?? .sync-pause.released
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? docs/sessions/digest/2026-08-23-5d62430b-7545-4769-a54e-673ea88fdc8d.md
?? tasks/T-2026-08-24-andrew-keeper-autosync/
```

4 件目は本契約の記録そのものであり、commit 対象である。他の 3 件には触れていない。

`keeper.sh` 48–49 行は `$M2DIR/.stignore` を更新する（mtime 17:35 で更新を確認）が、
`.gitignore:192` で除外済みのため未追跡の件数には現れない。`.servername` も同様
（`.gitignore:225`）。**常駐処理が repo を汚す経路は無い。**

**前セッションの未追跡 `tasks/T-2026-08-22—andrew-node-foundation/`（em ダッシュ）が
消えている。** 本契約の開始時点で既にディスク上に無く（`ls` で確認）、本契約は一切
触れていない。消えた時期と経緯は**本契約からは測れない（UNKNOWN）**。中身は
ハイフン版 `tasks/T-2026-08-22-andrew-node-foundation/` として版管理に入っており
（PR #125 が `phase0` へマージ済み、HEAD `3c4c5a6`）、内容は失われていない。

---

## 5. 送信前の秘匿の検査

`make task-report` は使えない（合言葉が失われ `scripts/load_env.sh` が失敗する）。
SPEC の指示どおり**自分で検査した**。

**陽性対照を先に取った。** 囮を含む一時ファイル `/tmp/ka_decoy.md` を作り、契約が指定する
正規表現（SPEC.md 319 行にそのまま載っている）を当てた。

    decoy_hits=3     ← 3 行すべてが引っ掛かった。検査は働いている
    decoy_removed=YES ← 囮は削除した。commit していない

本番の走査（`RESULT.md` / `audit.md` / `spec.yaml` / `SPEC.md` / `result.yaml` / `inbox.d`）は
**該当 1 件**。

    tasks/T-2026-08-24-andrew-keeper-autosync/SPEC.md:319

**件数ではなく形で判定した。** この 1 件は SPEC 自身が検査手順として載せている
正規表現の文字列であり、区切りと値が続く形ではない。**秘匿の値ではない。**

本契約では鍵を生成・変更・削除していない（禁止 7）。秘密鍵の内容も、資格情報も、
`audit.md` を含めどこにも書き出していない。`.servername` の中身も出していない。

---

## 6. 検証の出力

| 検査 | 終了コード | 内容 |
|---|---|---|
| `make task-validate` | 0 | `OK T-2026-08-24-andrew-keeper-autosync` / `1 task(s), 0 failed` |
| `make task-preflight` | 0 | 4 PASS / 1 WARN / 4 SKIP / 0 FAIL |
| `make forbidden-check` | 0 | `{"base": "origin/phase0", "changed": 6, "checked": 6, "errors": [], "excluded": 0, "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}` |
| `make taskindex-check` | **2** | `tasks_summary.csv` に本契約の 1 行が足りない旨の差分を報告 |
| `make inbox-check` | **2** | `tasks/inbox.md` に本契約の 3 行が足りない旨の差分を報告 |

**生成物は再生成していない**（禁止 4）。`make taskindex` `make inbox` は一度も実行していない。
差分を報告した 2 つは**記録するだけに留めた。** SPEC の禁止 4 が理由を書いている
（五台で並行実行するため、各契約が生成物を更新すると版管理で必ず衝突する。前契約で四回起きた）。
**全台の統合が済んだあと、一台で一度だけ再生成すること。**

なお契約の記録を書く前（Phase B 終了直後）に測ったときは両方とも exit 0 だった。
差分は本契約の `result.yaml` と `inbox.d/` を書いたことで生じたものであり、
**手編集による汚染ではない**（`forbidden-check` が `status: pass` を返している）。

### `task-preflight` の SKIP（「合格」ではなく「実行されなかった」）

| 項目 | 理由 |
|---|---|
| P2 `cuda_ext_loaded` | `plan.env.preflight` に記載なし |
| P3 `deterministic_flags` | `plan.env.preflight` に記載なし |
| P4 `prereg_committed` | `kind: impl` のため対象外（`exp` のみ） |
| P5 `frozen_source_hash` | `kind: impl` のため対象外（`exp` のみ） |

### `task-preflight` の WARN（層 4。起票者の誤りであり実行者の責任ではない）

`P9 spec_lint` が 8 規則のうち 3 件該当。すべて同じ規則 `separated_source`。

    separated_source@SPEC.md:329
    separated_source@SPEC.md:332
    separated_source@SPEC.md:335

いずれも Task 4 Step 3 の `source .venv/bin/activate \` + 次行 `&& make ...` である。
**実害は無い。** `\` の行継続で 1 つの命令として完結しており、検査器が行単位で
見ているための該当と考えられる。実際に実行して 3 つとも通っている（§6 の表）。

---

## 7. 逸脱（`deviations`）

**「なし」ではない。** 指示書どおりに実行できなかった箇所と、自分で判断した箇所を書く。

### 逸脱 1: 起動前に `~/bin/syncthing` の実行権を外した

**SPEC には無い操作である。** SPEC は禁止 2 で「同期処理を起動する」を禁じ、完了判定 11 で
「同期処理が零件」を求めるが、**指示どおり keeper を起動すると 41–43 行が syncthing を
起動する。** 両立しない。実装を読んで起動前に予見できたため、勝手に選ばずユーザーへ諮った。

承認を得て `chmod -x ~/bin/syncthing` を実行。**削除も移動もしていない**（大きさ 26730145
バイトのまま）。keeper 41 行の条件が偽になり、`syncthing=0`・`~/.syncthing.log` 不在で
確認した。**戻し方は `chmod 755 ~/bin/syncthing`。**

### 逸脱 2: `~/.zshrc` への追記をユーザーに実行してもらった

実行基盤の分類器が三経路（`cat >>` / `tail` / Edit ツール）とも拒否した。
**回避は試みていない。** 何を・影響範囲・戻し方を示してユーザーへ差し戻し、プロンプトの
`!` 経由で実行してもらった。結果は完了判定 9 のとおり（77 → 80 行）。

### 逸脱 3: 構文検査の判定器を `sh -n` から `bash -n` に替えた

SPEC は `sh -n` を指定し「両方が零であること」を求めるが、本ホストの `/bin/sh` は dash で
あり、`m2-sync.sh` 75 行の process substitution `<(...)` で `exit 2` になる。
**両スクリプトの shebang は `#!/bin/bash`** で、keeper 50 行は `~/bin/m2-sync.sh` を
shebang 経由で起動する。**実際に解釈するのは bash である。** `sh -n` の結果もそのまま
記録したうえで、`bash -n`（両方 0）を判定に採った。§8 の起票者の誤り 3 と対。

### 逸脱 4: 稼働計数に陽性対照を足した

SPEC の対照は `zzz_none` のみで、**陰性方向しか見ていない。** 「数えられること」を
示せないため `sshd` を足した（`sshd=1 (pid 1)`）。申し送り 6「対照は両方向で取る」に従った。

### 逸脱 5: 分岐を作らなかった（既に在ったため）

SPEC 0 節は `git checkout -b feat/andrew-keeper-autosync origin/phase0` を指示するが、
セッション開始時点で分岐は既に存在し、`origin/phase0`（`3c4c5a6`）を指していた。
`git fetch origin`（exit 0）で最新を確かめ、`ahead=0 behind=0` を実測して作り直さなかった。
契約ディレクトリも既に配置済みだった。

### 逸脱 6: `git fetch` の終了コードを測り直した

最初に `git fetch origin 2>&1 | tail -5; echo "fetch_exit=$?"` と書いてしまい、
`tail` の終了コードを拾った。**申し送り 4・7 が警告している罠に自分で落ちた。**
パイプを外して `git fetch origin > /tmp/ka_fetch.txt 2>&1; FE=$?` で測り直し `fetch_exit=0`。
誤った測り方をした事実ごと記録する。

### 逸脱 7: 報告を配布台帳へ送っていない

SPEC のとおり `make task-report` は使えない（合言葉が失われている）。
`RESULT.md` を commit して push する経路で返す。**起票者は版管理から読む。**

---

## 8. 起票者の誤り（`issuer_defects`）

**空にしない。** 型は 4 語に限る。

### 誤り 1 — `self_contradiction`

SPEC は禁止 2 で「同期処理を起動する」を禁じ、完了判定 11 で「同期処理が零件」を求めながら、
分岐表では keeper 39–50 行（41–43 行の syncthing 起動を含む）を「これを動かす」側に置く。
**同じ契約の中で、同じ行を動かせと止めろと言っている。** 前提「目印が無ければ中継を起こさず
版管理の同期だけを行う」は実装と食い違う。目印が制御するのは中継だけである。

### 誤り 2 — `asserted_without_measuring`

SPEC 表「全台で確定した事実」は `~/claude-sync/` について Task 3 Step 5 で
「**失われている**。記録の置き場所が無ければ別の場所を探すか `UNKNOWN` とする」と書く。
**実装は `m2-sync.sh` 22 行で `mkdir -p "$(dirname "$LOG")"` を実行しており、無ければ作る。**
起票者は実装を読まずに「探すか諦めろ」と指示した。実測では一周目で自動的に作られ、
記録も残った。**探す必要も `UNKNOWN` にする必要も無かった。**

### 誤り 3 — `shell_assumption`

Task 2 Step 2 が `sh -n` を指定する。本ホストの `/bin/sh` は dash であり、
`m2-sync.sh` 75 行の `<(...)` を構文誤りとして `exit 2` を返す。両スクリプトの shebang は
`#!/bin/bash` であり、`sh -n` は**実行されない解釈系で検査している。**
「両方が零であること」という完了条件は、**正しく動くスクリプトに対して達成できない。**
検査は `bash -n` でなければならない。

### 誤り 4 — `check_does_not_check`

Task 1 Step 2 の対照は `zzz_none`（存在しない語）だけで、「存在しない語が零を返すことが
対照である」と書く。**これは偽陽性が無いことしか示さない。** 計数器が壊れていて常に 0 を
返す場合も同じ出力になり、「すべて零」という肝心の結論を支えられない。
陽性対照（`sshd=1`）を足して初めて計数器が生きた処理を検出できることが示せた。

---

## 9. 陽性対照（`positive_controls`）

**判定が通ったことは、その判定が働いていることを意味しない。** 主要な判定について、
何を入れれば失敗するはずかと、実際に何が起きたかを対で書く。

| # | 判定 | 壊す入力 | 実測 |
|---|---|---|---|
| 1 | 稼働計数（完了判定 2, 10, 11） | 必ず動いている語を渡す。壊れた計数器なら 0 を返すはず | `sshd=1 ['1']`。**生きた処理を検出できる。** 陰性側 `zzz_none=0` `systemd=0` も両方 0 |
| 2 | 多重起動の錠（完了判定 12） | keeper をもう一度起動する。錠が効かなければ `keeper.sh=2` になるはず | `keeper.sh=1 ['40838']` のまま。別プロセスの `flock -n` は `ACQUIRED_lock_is_free` を出さず `flock_exit=1` |
| 3 | 秘匿の検査（完了判定 15） | 区切りと値が続く形と鍵の書き出し行を含む囮ファイル | `decoy_hits=3`。**3 行すべて検出。** 検査は働いている（囮は削除済み、commit していない） |
| 4 | 中継・同期処理が動いていないこと（完了判定 11） | keeper 34 行・42 行はどちらも `>>` でログへ追記する。一度でも走ればファイルが作られるはず | `~/.tunnel.log` 不在、`~/.syncthing.log` 不在。対照として同じ `>>` で作られる `~/claude-sync/sync-alerts.log` は**存在する**（146 バイト）。**`>>` は実際にファイルを作る** |
| 5 | 抑止が版管理への書き込みを止めること（完了判定 13） | 送出すべきものがある状態（`origin/$BR..HEAD > 0`）で `m2-sync.sh` を回す。抑止が無ければ auto-push が走るはず | **auto-push の条件をすべて満たしたうえで測った。**`origin/feat/andrew-keeper-autosync` は push 済みで存在し `ahead=1`。この状態で `~/bin/m2-sync.sh` を一度回すと `m2sync_exit=0`、記録は 1 行 → 2 行に増えたがどちらも「一時停止中」で `autopush_lines=0`、`ahead` は 1 のまま。**抑止が無ければ送出されていた状態で止まった** |
| 6 | 構文検査（完了判定 6） | 実際に構文誤りがある入力なら非零を返すはず | `sh -n ~/bin/m2-sync.sh` が `exit 2` を返した。**検査器は非零を返せる。** ただしこの該当は dash の偽陽性であり、`bash -n` では 0（§7 の逸脱 3） |

---

## 10. 未測定（`unknowns`）

**未測定は UNKNOWN と書く。推測で埋めない。**

| # | 項目 | 理由 |
|---|---|---|
| 1 | 目印 `~/.tunnel_to_philip` を置いたときに中継が実際に張れるか | **置いていない**（禁止 1）。§3.4 は実装から読める見込みであって実測ではない |
| 2 | `~/bin/syncthing` の実行権を戻したときに同期処理が正常に立ち上がるか | 起動していない（禁止 2）。実行権を外した状態でしか測っていない |
| 3 | 前セッションの未追跡 `tasks/T-2026-08-22—andrew-node-foundation/` が消えた時期と経緯 | 本契約の開始時点で既に不在。本契約からは測れない |
| 4 | 抑止を外したあと、次の周回（最大 1800 秒後）に何が起きるか | 周期を待っていない。`ahead` と `behind` が 0 で開いている PR が 1 件あるため auto-merge / auto-push / auto-PR はいずれも条件を満たさない**はず**だが、実測ではない |
| 5 | `git@github.com:takuya3h/m2.git` の fetch を通している鍵 | `~/.zshrc` 68–71 行が `ssh-add ~/.ssh/id_ed25519_github` を実行しており、これが経路と思われるが、`Warning: Identity file ~/.ssh/id_Andrewdeploy not accessible` を出しつつ fetch は exit 0 で通っている。**どの鍵が通したかは照合していない** |
| 6 | `P9 spec_lint` の `separated_source` 3 件が検査器の行単位判定によるものか | 検査器の実装を読んでいない。3 つとも実際には exit 0 で通ることだけを実測した |

---

## 11. 送出

`make task-report` は使えない（合言葉が失われ `scripts/load_env.sh` が失敗する）。
SPEC の指示どおり **`RESULT.md` を commit して push する経路**で返した。**起票者は版管理から読む。**

| 項目 | 値 |
|---|---|
| commit 1 | `64e7d50` feat(sync): deploy keeper and enable git autosync on andrew（6 files changed, 1452 insertions(+)） |
| commit 2 | 本節と `result.yaml` の commit / PR 欄の記載 |
| commit 3 | 抑止の陽性対照（§9 の 5 番）の実測 |
| push | `push_exit=0`。`* [new branch] HEAD -> feat/andrew-keeper-autosync` |
| 送出先 | `https://github.com/takuya3h/m2.git`（push 側のみ https。fetch 側は `git@` のまま） |
| PR | **#128** `feat(sync): deploy keeper and enable git autosync on andrew` → base `phase0`。`isDraft: false` |
| 作成前の既存 PR | `[]`（0 件。auto-PR と二重にならないことを確かめた） |

`gh pr create` が出した `Warning: 3 uncommitted changes` は、開始時から在る未追跡 3 件を
指している。**触っていない**（§4）。

### 抑止を外す前に PR を作った理由

`m2-sync.sh` 115–132 行の auto-PR は **Draft を起票する。** 抑止を外してから周回が回ると
`auto: feat/andrew-keeper-autosync -> phase0` という Draft が立ち、二重になる。
先に手で作れば、auto-PR の条件「開いている PR が 0 件」が偽になり起票されない。

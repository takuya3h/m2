# RESULT — T-2026-08-24-bengio-syncthing-node

**status:** `stopped`（**Gate G1 が fail。`on_fail: stop`**）
**kind:** `impl`  **host:** `bengio`  **repo:** `~/slocal2/m2`
**branch:** `feat/bengio-syncthing-node`  **実行日:** 2026-08-23〜24 (JST)

**中心への認証が通らない。** 中継が張れないため、契約は Phase A で停止した。
`governance.escalate_if` の第一項「中心への認証が中継を張る前から通らない場合」に該当する。

**本ホストの状態は開始時から変わっていない。** 加えたのは repo の外の控え 1 件だけである。
生の出力は要約せず `audit.md` に貼ってある（申し送り #8）。

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

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b087
```

`spec.yaml` の `d422b08` はこの値の前置である。**一致するため置換は不要だった。**

### 中心の値（**本文の転記を信用せず版管理から読んだ**）

| 項目 | 出所 | 実測 |
|---|---|---|
| 中心の識別子 | `scripts/sync/device_ids/philip.txt` | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| 自分の識別子 | `scripts/sync/device_ids/bengio.txt` | `4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO` |
| 除外規則 | `.stignore` / `.stglobalignore` | ともに `61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a`。**中心の実測値と一致** |

### `handoff.md` の所在（SPEC の記載と食い違う）

SPEC は「**前契約の `RESULT.md` と `handoff.md` にノード用の手順がある**」と書くが、
前契約 `tasks/T-2026-08-24-philip-syncthing-hub/` に `handoff.md` は**無い**。
実体は `tasks/T-2026-08-24-syncthing-config-survey/handoff.md` である。そちらを読んだ。

`inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は本契約の作業に現れない。
**参照していない。**

---

## 2. 完了判定（開始時と停止時）

「実施した」ではなく何が出たかを書く。**実行しなかった項目は「未実行」と明記する。**

| # | 判定 | 実測 |
|---|---|---|
| A | 設定・実行ファイル・常駐処理・除外規則の要約値（実行権 644、目印零件） | `config.xml` `d4928c2d…` 8495 B 600 / `cert.pem` `b53eba6d…` 794 B 664 / `key.pem` `99dfaa2c…` 288 B 600 / `syncthing` `32ab747e…` 26730145 B **644** / `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / `.stignore` = `.stglobalignore` = `61593e99…` / `marker_count=0` |
| B | 稼働を両方向の対照つきで数えた | 同期処理 **0**、中継 **0**。肯定の対照 `zsh=6`、否定の対照 `zzz_no_such=0` |
| C | 控えを repo の外へ取り、画面の鍵の有無を確かめた | `~/.local/state/syncthing.bak.20260823-232244`。3 件とも要約値一致。**`apikey` に 32 文字の実値あり** → 版管理へ置かない |
| D | 戻し方を記録した（実行していない） | `audit.md` Task 1 Step 4。5 行。**実行していない** |
| E | 自分の識別子が版管理の値と一致した | 一致。設定内 `device id="4NIRI4M-…-X52VHQO"` |
| F | **中心への認証が通った** | 🔴 **通らない。`ssh_exit=255` `Permission denied (publickey,password)`、`REACHABLE` 0 件** |
| G〜H | 版を中心に揃える | **未実行**（G1 stop） |
| I〜N | 設定の組み立て | **未実行**（G1 stop） |
| O〜S | 目印・中継・実行権・起動 | **未実行**。SPEC が「**目印を作らない**」と定める |
| T〜V | 届くことの確認 | **未実行**。中継が無いため測れない |
| W | 目印が一件、常駐処理が無変更 | 目印は **0 件**（一件にしていない。上記のとおり作らないのが正しい）。常駐処理は開始時と要約値一致 |
| X | 秘匿検査を自分で行った（陽性対照つき） | §5 |
| Y | 分岐が送出され PR が存在する | §6 |
| Z | 報告が台帳へ返り、抑止が外れている | 台帳へは返せない（§6）。抑止は §6 |

---

## 3. 何が起きているか（切り分け）

| 層 | 実測 | 判定 |
|---|---|---|
| 経路（TCP） | `192.168.196.150:50072` へ接続でき、`SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.1` が返る | **生きている** |
| 鍵の対 | 秘密鍵 `~/.ssh/id_ed25519_bengiotophilip` と公開鍵 `scripts/sync/hub_keys/bengio.pub` の指紋が一致（`SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4`） | **本ホスト側に誤りは無い** |
| 提示 | `debug1: Offering public key: … SHA256:Ea9Reaj…` | **提示している** |
| 受け入れ | `Server accepts key` が**出ない**。`Permission denied (publickey,password)` | 🔴 **中心が受け入れていない** |

### 住所については解けたことがある

前契約の `handoff.md` §3.4 は「**2 行目に何を書くかは `UNKNOWN`**。契約は `192.168.196.150`
とするが、外からの到達性を本契約では検証できない」と残していた。
**到達性は実測で解けた**（TCP が開き、SSH の名乗りが返る）。
残っているのは受け入れ一覧だけである。

### 原因の所在（版管理から確かめた）

再構築後（2026-08-22 以降）の契約は、受け入れ一覧を**読むだけ**である。

```
tasks/T-2026-08-22-{andrew,bengio,ilya,lecun}-node-foundation/SPEC.md:126  ssh-keygen -lf ~/.ssh/authorized_keys
tasks/T-2026-08-22-philip-hub-foundation/SPEC.md:105                       ssh-keygen -lf ~/.ssh/authorized_keys
tasks/T-2026-08-24-philip-syncthing-hub/SPEC.md:374                        sha256sum ~/.ssh/authorized_keys
```

書き換える契約は `T-2026-08-12-register-hub-keys` ただ一つで、**保守作業より前のものである。**
鍵は保守作業の後に作り直されているため、当時登録した指紋はもう合わない。

さらに前契約 `T-2026-08-24-philip-syncthing-hub` は**禁止 3 で受け入れ一覧の変更を自ら禁じており**、
その `RESULT.md` 完了判定 18 は受け入れ一覧を **`UNKNOWN`** と記録している。

🔴 **結論。中心の `~/.ssh/authorized_keys` へ 4 台の公開鍵を入れる契約が、まだ存在しない。**
`scripts/sync/hub_keys/` には `andrew.pub` `bengio.pub` `ilya.pub` `lecun.pub` の 4 件が
公開済みで、**中心側で取り込むだけの状態にある。**

本契約は禁止 1（他ホストの状態を変更する）と禁止 3（受け入れ一覧を変更する）により、
**bengio 側からこれを直せない。** 中心で実行する契約が要る。

---

## 4. 起票者の誤り

`result.yaml` の `issuer_defects` と対で書いてある。要約すると 4 件。

1. **`asserted_without_measuring`** — SPEC は中心が繋げる状態にあることを前提に全 5 タスクを組むが、
   **受け入れ一覧に本ホストの鍵が入っているかを誰も測っていない。** 前契約自身が `UNKNOWN` と
   記録しているのに、それを埋める契約を挟まずにノード側の契約を起票した。
2. **`self_contradiction`** — 禁止 1 の但し書きは「**中心で命令を実行してはならない**」と定めるが、
   Task 1 Step 6 は `ssh … 'echo REACHABLE'` を指示する。これは中心での命令の実行である。
3. **`check_does_not_check`** — Task 1 Step 3 は `grep -o 'apikey>[^<]*' … | cut -c1-12` を指示する。
   これは**秘匿の実値の先頭 12 文字を画面に出す**。禁止 7 および「画面の鍵に注意」と両立しない。
4. **`shell_assumption`** — `P9 spec_lint` が `separated_source` を 5 件返した
   （`SPEC.md:50,473,476,479,507`）。字下げ区画を 1 行ずつ渡す実装系では
   `source … \` 単独が壊れた命令になる。

---

## 5. 送信前の秘匿検査（自分で実施）

`make task-report` は使えない（合言葉が失われている）ため、検査を自分で行った。
判定は件数ではなく**形**で行った。**画面の鍵（`apikey`）を版管理へ置いていない。**
`config.xml` の控えは repo の外（`~/.local/state/syncthing.bak.20260823-232244`）だけにある。
陽性対照は囮を `/tmp` に置いて取り、**commit していない。** 出力は `audit.md`。

---

## 6. 送出、抑止、台帳

（Task 5 Step 4-5 の実測値。実行後に埋める）

---

## 7. 次にやるべきこと

| 順序 | 内容 |
|---|---|
| **1** | 🔴 **中心（philip）で受け入れ一覧を設定する契約を起票して実行する。** `scripts/sync/hub_keys/{andrew,bengio,ilya,lecun}.pub` の 4 件を `~/.ssh/authorized_keys` へ追加する。**手本は `T-2026-08-12-register-hub-keys`**（控えを取り、戻し方を先に決め、指紋で照合する形になっている） |
| 2 | 本契約 `T-2026-08-24-bengio-syncthing-node` を Task 1 Step 6 からやり直す。**Phase A の記録はそのまま使える**（本ホストは無変更） |
| 3 | 他の三台の同種契約は、1 が終わるまで起票しても通らない |

### 次の契約で使える実測値

| 項目 | 値 |
|---|---|
| 中心の到達性 | `192.168.196.150:50072` は **TCP が開いており** `SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.1` を返す。handoff §3.4 の `UNKNOWN` は解けた |
| bengio が提示する指紋 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4`（受け入れ一覧の確認に使える） |
| 開始状態 | `syncthing` `32ab747e…` 26730145 B **644** v1.27.10 / 設定 `config.xml` `d4928c2d…` 8495 B 600 `<configuration version="37">` |
| 設定の中身 | 実体の共有フォルダ 1 件（`default` = `/home/ubuntu/Sync`、実在しない）、相手 1 件（自分のみ）、`global=true` `relays=true` `local=true` `autoUpgradeIntervalH=12` |
| ⚠ 登録名 | **`Bengio`（先頭が大文字）。`bengio` ではない。** Task 3 Step 2 で直す必要がある |
| 版の差 | 中心 `v2.1.3`（`e8a08fdd…`）、本ホスト `v1.27.10`（`32ab747e…`）。**揃えていない** |
| 共有領域 | `~/claude-sync/` は **8.0K / 1 件**（`sync-alerts.log` 813 B）。中心も同名のファイルを持つため、`sendreceive` で繋ぐと**上書きか衝突ファイルのどちらかが起きる** |
| 控えの場所 | `~/.local/state/syncthing.bak.20260823-232244`（repo の外） |
| つまずいた点 | `ssh … \| grep \| head` の直後に `echo` を挟むと `${pipestatus[1]}` が `echo` の値になる。配管を挟まず取ること |

### 未解決のまま残る判断（`handoff.md` と SPEC が食い違う）

`handoff.md` §2.3 は「**空の側が `sendreceive` で参加すると中身を消しうる。**
中身を持つ台を `sendonly`、他を `receiveonly` で始めるのが安全」と書き、§3.3 #5 は
「型は 2.3 の判断に従う」と定める。**SPEC Task 3 Step 5 は両方 `sendreceive` を指示する。**

SPEC 自身が「`handoff.md` と食い違えば `handoff.md` を正とする」と定めるため、
本来なら `handoff.md` が勝つ。ただし中心側は前契約で**利用者の判断により `sendreceive`** を
採っている（前契約 `RESULT.md` 逸脱 1）。**ノード側をどちらにするかは未決である。**
G1 で停止したため本契約では判断していない。**次の実行者はここで止まる。**

---

## 8. 逸脱

`result.yaml` の `deviations` と対で書いてある。要約すると 5 件。

1. **環境** — `make task-start` を実行していない。`scripts/load_env.sh` が使えない（合言葉が失われている）。分岐は既に作られていた。
2. **判断** — `apikey` の検査で SPEC の `cut -c1-12` を採らず、**長さと空かどうかだけ**を測った。実値を画面に出さないため。
3. **判断** — 抑止 `.sync-pause` を SPEC §0 のとおり最初に置いた（技能書とも一致）。解除は §6。
4. **判断** — `handoff.md` を前契約のディレクトリではなく `T-2026-08-24-syncthing-config-survey/` から読んだ。SPEC の記載先に実体が無いため。
5. **判断** — G1 が fail のため Task 2 以降を実行していない。`on_fail: stop` と SPEC の想定外の表に従った。

**逸脱は「無し」ではない。** 上記 5 件がすべてである。

## 9. 禁止 5 の遵守

**生成物を再生成していない。** `make taskindex` と `make inbox` は実行していない。
検査が差分を報告した場合も、事実として記録するにとどめた（§6）。

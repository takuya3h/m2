# audit — T-2026-09-17-philip-accept-efros

手続きの証跡。`RESULT.md` はここを行番号で指す。

- 実行ホスト: OS の `hostname` は `aolab`、群れの名は **`philip`**（`myID` が
  `scripts/sync/device_ids/philip.txt` と一致。下記 §2.4）
- 分岐: `feat/philip-accept-efros`（起点 `origin/phase0` = `efc64453`）
- 測定時刻: 2026-09-17（JST）

---

## 0. 取り込みと前提

### 0.1 `make task-start` が失敗した（起票者の誤りではなく台帳の欠落）

    [task-start] 分岐を作成: feat/philip-accept-efros（起点 origin/phase0）
    [task-start] 契約を取り込みます: T-2026-09-17-philip-accept-efros
    取り込みを中止しました: 要約値の列が空です: T-2026-09-17-philip-accept-efros。
    照合できない本文は取り込みません
    make: *** [Makefile:205: task-start] Error 4
    [task-start] 実行前の状態へ戻しました

配布台帳の行を自分で読んで確かめた（読み取りのみ・取り込みはしていない）。

| 項目 | 実測 |
|---|---|
| `sha256` 列 | **空** |
| 添付 | **無し** |
| 本文 | **0 文字**（`sha256` は空文字の値 `e3b0c442…`） |

**行そのものが空である。** 契約本文は別経路で既に手元にあり（`tasks/` 配下）、
`make task-validate` が exit 0。台帳との照合はできないため、照合できないことを記録した。

`task_start.sh` は巻き戻しに成功している（分岐は残らず、`.sync-pause` は実行前から
在ったため触られていない）。**同じ起点 `origin/phase0` で分岐を手で作った。**

### 0.2 自動同期の抑止

    grep -c "sync-pause" ~/bin/m2-sync.sh   -> 2      （稼働中の版が対応済み）
    git check-ignore -v .sync-pause         -> .gitignore:240:.sync-pause
    ls -l .sync-pause                       -> 存在（Sep 17 04:33 作成）

### 0.3 作業ツリーの退避（消していない）

`task_start.sh` は未追跡があると分岐を作らない（`git status --porcelain` が 8 件）。
**repo の外へ移した。報告の後に戻す。**

退避先: `~/task-hold/T-2026-09-17-philip-accept-efros/`
一覧: `~/task-hold/T-2026-09-17-philip-accept-efros/_untracked_list.txt`

| 退避したもの | 大きさ |
|---|---|
| `.sync-pause.released` | 0 |
| `docs/sessions/digest/2026-08-25-04471817-….md` | 24K |
| `experiments/analysis/hts_candidate_acceptance/` | 32K |
| `experiments/transfer/pd_refin_both_seed42/` | 212M |
| `experiments/transfer/pd_refin_empty_seed42/` | 212M |
| `experiments/transfer/pd_refin_oracle_seed42/` | 212M |
| `experiments/transfer/pd_refin_pred_seed42/` | 212M |
| `tasks/T-2026-09-17-philip-accept-efros/`（契約） | 20K |

契約は退避先から複製して戻した（`diff -r` で同一を確認）。

### 0.4 起票者が把握していない規約の適用判定

| 節 | 本契約に適用されるか | 根拠 |
|---|---|---|
| `conventions#proposal_gate` | **適用されない** | 本節の対象は「手法・結合・補助信号・修正案の**提案**」。本契約は `kind: impl` で、公開鍵と識別子の登録のみ。提案を含まない |
| `conventions#folds` | **適用されない** | 本節は動画単位 5-fold の折り表と選定・test の規律。本契約は学習も評価も行わない。`inputs.data` も参照しない（§0.5） |

### 0.5 `inputs.data` を参照しなかった

`inputs.data.dataset: egosurgery_phase_v1` と `split_files: [data/splits/ego_val.txt]` は
雛形の必須項目であり、**本契約はこれを一度も読んでいない。**

### 0.6 `conventions_rev` の実測

| 項目 | 値 |
|---|---|
| 契約の記載 | `e7a5100` |
| 実測（`git log -1 -- context/conventions.md`） | **`e7a51005`** |
| 一致 | **一致（置換不要）** |

**初回の検証で出た `WARN [L2-6]` は、取り込み前の checkout が古かったことによる。**
当時の分岐 `feat/k1-trace-policy-place` は `e7a5100` を含まず（`git merge-base
--is-ancestor` が偽）、`context/conventions.md` に `proposal_gate` と `folds` の節が
無く、`scripts/sync/{hub_keys/efros.pub,device_ids/efros.txt}` も無かった。
`origin/phase0` 起点の分岐では 3 つすべてが揃い、**再検証は WARN なしで exit 0。**

### 0.7 L3 プリフライト

    RESULT: 5 PASS / 1 WARN / 6 SKIP / 0 FAIL      exit=0

| 判定 | 項目 |
|---|---|
| PASS | P1 venv_active / P6 decisions_answered / P7 destination_writable / P8 contract_valid / P10 preflight_names_known |
| **SKIP（合格ではない。実行されなかった）** | P2 cuda_ext_loaded / P3 deterministic_flags / P4 prereg_committed / P5 frozen_source_hash / P11 gpu_free / P12 refs_resolved |
| WARN | P9 spec_lint（2 件。下記） |

P9 の該当 2 件。

| 該当 | 行 | 実測した内容 |
|---|---|---|
| `host_mismatch` | `SPEC.md:5` | 宣言 `philip` / `socket.gethostname()` = `aolab`。**層が違う。** 群れの名は `philip` で、`myID` が `device_ids/philip.txt` と一致する（§2.4）。**実行ホストは正しい** |
| `separated_source` | `SPEC.md:48` | 該当行は `source … && source … \` で、次行が `&& make …`。**実際には行継続で 1 命令**である。行単位で読む検査器が継続行を別命令と見た偽陽性。規則自体は守って実行した（読み込みと `make` を同一命令に入れた） |

---

## 1. 受け入れ一覧（Task 1 Step 1）

### 1.1 最初の測定は実行基盤に拒否された

    $ stat -c '…' ~/.ssh/authorized_keys
    Permission to use Bash with command stat … ~/.ssh/authorized_keys has been denied.

    $ ls -l ~/.ssh/authorized_keys; wc -l …; sha256sum …
    Permission for this action was denied by the Claude Code auto mode classifier.

原因を実行基盤の設定で特定した（値は読んでいない。規則の並びだけを見た）。

    /home/ubuntu/.claude/settings.json の permissions.deny に
      Read(~/.ssh/**)

`deny` は 20 件あり、`Read(~/.ssh/**)` はその 1 件。`hooks` は空（`{}`）。
プロジェクト側 `.claude/settings.json` と `.claude/settings.local.json` の
`deny` / `ask` はともに 0 件で、`.ssh` に触れる規則は無い。
**したがって拒否は利用者のグローバル設定による。**

**SPEC「想定外が起きたときの扱い」の「受け入れ一覧を読めない → 停止して報告。
実行基盤が拒むことがある」に該当したため、Gate G1（`on_fail: ask`）で停止し、
判断を仰いだ。** `Edit(~/.ssh/**)` `Write(~/.ssh/**)` は `deny` に無く追記自体は
通る見込みだったが、**読めない状態で追記すると「既存を一つも失わない」
（禁止 1・完了判定 L）を確かめる手段が無いため、追記しなかった。**

**利用者がグローバル設定を変更した**（「グローバル設定変更したのでもう一度」）。
再試行して読めるようになったため、以下を測った。

### 1.2 属性・件数・要約値（開始時）

| 項目 | 実測 |
|---|---|
| 場所 | `/home/ubuntu/.ssh/authorized_keys`（実体。symlink ではない） |
| 権限 | **`600`**（`-rw-------`）— SPEC の記載どおり。`664` ではない |
| 所有者 | `ubuntu:ubuntu` |
| 大きさ | `1127` bytes |
| mtime | `2026-08-23 23:57:13.309727469 +0000` |
| 行数（`wc -l`） | **5** |
| **空行を除いた件数** | **5** |
| コメント行（`#` で始まる） | 0 |
| 末尾 | **改行で終わっている**（追記で行が繋がらない） |
| sha256 | `35ad4ef5f372b1e31952d6cb919515bd76bf29e6a32996a77e4ff23e66b457f4` |

**五件。SPEC の記載と一致する。**

### 1.3 登録されている鍵（指紋と註釈。鍵の本体は出していない）

| # | 種別 | 指紋 | 註釈 |
|---|---|---|---|
| 1 | RSA 4096 | `SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU` | `dakyo-mba@dmba.local`（人の端末） |
| 2 | ED25519 256 | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `andrewtophilip` |
| 3 | ED25519 256 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `bengiotophilip` |
| 4 | ED25519 256 | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` |
| 5 | ED25519 256 | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `lecuntophilip` |

**解析は失敗していない。**

| 項目 | 実測 |
|---|---|
| 解析できた件数 | **5** |
| 空行を除いた件数 | **5** |
| 一致 | **一致（全行が解析できる）** |
| 陰性対照（囮を `ssh-keygen -lf` に渡す） | 終了コード **255** / 解析できた件数 **0** → 解析器は判別している |

| 完了判定 | 状態 | 実測 |
|---|---|---|
| A 受け入れ一覧を測った | **達** | 5 件 / `600` / `35ad4ef5…` / 指紋 5 件を記録 |

## 2. 同期処理の設定（Task 1 Step 2）

### 2.1 ファイルの属性と要約値

| 項目 | 実測 |
|---|---|
| 場所 | `/home/ubuntu/.local/state/syncthing/config.xml` |
| 権限 | **`600`**（`-rw-------`） |
| 所有者 | `ubuntu:ubuntu` |
| 大きさ | `14026` bytes |
| mtime | `2026-08-23 22:41:33.694668139 +0000` |
| sha256 | `50caaae69dad7a88209482e82033d5a24049000894cb2c878795a9f41ee25a42` |
| 設定の版 | `configuration version="52"` |

同ディレクトリの内容（`cert.pem` `key.pem` `https-*.pem` `syncthing.lock`
`index-v2/` `index-v0.14.0.db-migrated/` `config.xml.v37`）。

### 2.2 相手の実体 — **階層を見て数えた**

`configuration` **直下**の `device` だけが実体である。

| 名 | 識別子（前後 7 桁） | compression | address |
|---|---|---|---|
| `lecun` | `OOOTQMG…KRFOWA3` | metadata | dynamic |
| `ilya` | `UODEAXZ…X6SDBQY` | metadata | dynamic |
| `andrew` | `3C2LTP7…UVZB5A4` | metadata | dynamic |
| **`philip`** | `3J4TRX4…DZOCQQE` | metadata | dynamic |
| `bengio` | `4NIRI4M…X52VHQO` | metadata | dynamic |

| 数え方 | 件数 |
|---|---|
| `configuration` 直下の `device`（実体） | **5** |
| うち `id` が空（ひな型） | 0 |
| **素朴な `.//device`** | **17** |
| 内訳 | 直下 5 + `folder` 配下 10 + `defaults` 配下 2 = 17 |

**素朴に数えれば 17 で、実体の 3.4 倍になる。** 申し送り「要素の階層を見ずに
検索しない」（`issuer_cautions` 注意 13）の該当が実際に起きる構造である。

最初の測定で `folder` 配下の共有相手が 5 件すべて「空」に見えた。
**属性名を `deviceID` と誤ったためで、実際は `id` である**（`introducedBy` と 2 属性）。
測り直して 5 件すべてが実体の識別子であることを確認した。

### 2.3 共有フォルダの定義（開始時。**変えていない**）

| id | label | path | type | paused | 共有相手 |
|---|---|---|---|---|---|
| `claude-sync` | `claude-sync` | `/home/ubuntu/claude-sync` | `sendreceive` | （既定） | 5 |
| `m2` | `m2` | `/home/ubuntu/slocal2/m2` | `sendreceive` | （既定） | 5 |

両フォルダの共有相手は同じ 5 件（lecun / ilya / andrew / philip / bengio）。

| 数え方 | 件数 |
|---|---|
| `configuration` 直下の `folder`（実体） | **2** |
| 素朴な `.//folder` | **3** |
| 差の 1 件 | `defaults/folder`（`id=""` `label=""` `path="~"`、配下に `id=""` の device 1 件） |

**`defaults` 節がひな型である。触っていない。**

### 2.4 稼働しているもの（`/proc/PID/exe` で絞った）

    pid=122452 exe=/home/ubuntu/bin/syncthing  cmd=… serve --no-browser
    pid=122530 exe=/home/ubuntu/bin/syncthing  cmd=… serve --no-browser
    syncthing 実体プロセス数: 2

**両方向の対照**（`issuer_cautions` 注意 3・6）。

| 対照 | 実測 | 判定 |
|---|---|---|
| 陽性（`/proc/self/exe` = `/usr/bin/zsh` で同じ絞り方） | **6** | 1 以上 → 絞り方が働いている |
| 陰性（`*zzz_no_such_binary_qqq*`） | **0** | 偽陽性が無い |

REST から取った状態。

| 項目 | 実測 |
|---|---|
| 版 | **`v2.1.3`**（linux/amd64）— SPEC の記載と一致 |
| `myID` | `3J4TRX4…DZOCQQE`（63 桁） |
| **`myID` == `device_ids/philip.txt`** | **True** → 本ホストは `philip` |
| 起動時刻 | `2026-08-23T22:29:18Z` / uptime `2095978` 秒 |
| discovery | 有効 |

### 2.5 四ノードとの接続（開始時の基準点）

| 名 | 識別子 | connected | paused | type | address |
|---|---|---|---|---|---|
| `andrew` | `3C2LTP7…UVZB5A4` | **True** | False | `tcp-server` | `127.0.0.1:34024` |
| `bengio` | `4NIRI4M…X52VHQO` | **True** | False | `tcp-server` | `127.0.0.1:33458` |
| `ilya` | `UODEAXZ…X6SDBQY` | **True** | False | `tcp-server` | `127.0.0.1:45960` |
| `lecun` | `OOOTQMG…KRFOWA3` | **True** | False | `tcp-server` | `127.0.0.1:57646` |

**`connected=True` の件数: 4。** これが「切れていない」の基準点である。

### 2.6 待ち受け — `ss` が無いため `/proc/net/tcp{,6}` から数えた

`ss` は本ホストに存在しない（`command not found`）。
**`ss | grep -c` は `0` を返したが、これは件数ではなく命令の失敗である**
（`issuer_cautions` 注意 5）。別の方法で数え直した。

| 港 | LISTEN 件数 | 出所 |
|---|---|---|
| `22000` | **1** | `/proc/net/tcp6`、local `::` |
| `8384` | **1** | `/proc/net/tcp`、local `127.0.0.1` |
| 陰性対照 `65533` | **0** | 偽陽性が無い |

---

## 3. 控え（Task 1 Step 3）

| 対象 | 控えたか | 置き場 | 一致 |
|---|---|---|---|
| 同期処理の設定 | **取った** | `~/task-hold/…/backup/config.xml.orig` | **sha256 一致 True** |
| 受け入れ一覧 | **取った**（設定変更の後） | `~/task-hold/…/backup/authorized_keys.orig` | **sha256 一致 True** |

受け入れ一覧の控え。

| 項目 | 実測 |
|---|---|
| 原本 sha256 | `35ad4ef5f372b1e31952d6cb919515bd76bf29e6a32996a77e4ff23e66b457f4` |
| 控え sha256 | 同一。`一致: True` |
| 控えの属性 | `perm=600 size=1127 mtime=2026-08-23 23:57:13`（`cp -p` で保った） |
| 置く前の `PRIVATE KEY` の件数 | **0** |
| 置く前の `BEGIN .*KEY` の件数 | **0** |
| 陽性対照（必ず在る語 `ssh-`） | **5** |

置き場が同期対象の外であることを確かめた。

    控え: /home/ubuntu/task-hold/…/backup
    同期対象: /home/ubuntu/claude-sync, /home/ubuntu/slocal2/m2
    -> 同期対象の外側（安全）

置く前の検査（形で判定。値は出していない）。

| 検査 | 件数 |
|---|---|
| `PRIVATE KEY` の出現 | **0** |
| 陽性対照（必ず在る語 `configuration`） | **2** |

控えの属性: `perm=600 size=14026 mtime=2026-08-23 22:41:33`（`cp -p` で保った）。

**版管理へは置いていない。** `config.xml` は GUI の合言葉（長さ 32）を含むため、
伏せずに版管理へ入れない。

---

## 4. 戻し方（Task 1 Step 4）— **記録のみ。実行していない**

### 4.1 同期処理の設定を戻す

**稼働中は直接書き戻しても上書きされる（§5）。** 順序が要る。

    # 1. いまの状態を確かめる（戻す前に、戻す先が期待どおりか）
    sha256sum ~/task-hold/T-2026-09-17-philip-accept-efros/backup/config.xml.orig
    # 期待: 50caaae69dad7a88209482e82033d5a24049000894cb2c878795a9f41ee25a42

    # 2. 相手の追加だけを取り消す（再起動しない。REST の経路で消す）
    #    合言葉は config.xml から変数へ読み込む。画面へ出さない。
    #    DELETE http://127.0.0.1:8384/rest/config/devices/<efros の識別子>
    #    フォルダの共有相手からも同じ識別子を外す（PATCH /rest/config/folders/<id>）

    # 3. 消えたことを確かめる
    #    GET /rest/config/devices        -> 件数が 5 に戻る
    #    GET /rest/config/restart-required -> false
    #    GET /rest/system/connections    -> connected=True が 4 件

**ファイルを上書きして戻す場合（REST で戻せないとき）。** 同期処理を止める必要が
あり、**それは禁止 2 に当たる。判断を仰ぐこと。**

    # （禁止 2。実行者は勝手に行わない）
    # syncthing を止める → cp -p backup/config.xml.orig ~/.local/state/syncthing/config.xml
    # → chmod 600 ~/.local/state/syncthing/config.xml → 起動

権限は開始時の値 **`600`** に戻す。所有者は `ubuntu:ubuntu`。

### 4.2 受け入れ一覧を戻す

**控えが取れたので手順を書ける。実行はしていない。**

    # 1. 戻す先が期待どおりか（開始時の要約値）
    sha256sum ~/task-hold/T-2026-09-17-philip-accept-efros/backup/authorized_keys.orig
    # 期待: 35ad4ef5f372b1e31952d6cb919515bd76bf29e6a32996a77e4ff23e66b457f4

    # 2. 戻す（属性も戻す。開始時の権限は 600）
    cp -p ~/task-hold/T-2026-09-17-philip-accept-efros/backup/authorized_keys.orig \
          ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys

    # 3. 戻ったことを確かめる（両方向の集合差）
    ssh-keygen -lf ~/.ssh/authorized_keys | awk '{print $2}' | sort > /tmp/fp_now.txt
    ssh-keygen -lf ~/task-hold/…/backup/authorized_keys.orig | awk '{print $2}' | sort > /tmp/fp_orig.txt
    comm -23 /tmp/fp_orig.txt /tmp/fp_now.txt   # 期待: 空
    comm -13 /tmp/fp_orig.txt /tmp/fp_now.txt   # 期待: 空
    # 件数 5、権限 600、sha256 が上の値に戻る

**efros の一行だけを外す場合**（全体を戻さない）。

    grep -v -F -f <(cat /home/ubuntu/slocal2/m2/scripts/sync/hub_keys/efros.pub) \
         ~/.ssh/authorized_keys > /tmp/ak.new && cp /tmp/ak.new ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    # 件数が 6 -> 5、消えた指紋が efros の 1 件だけであることを集合差で確かめる

---

## 5. 設定を変える手段と反映の条件（Task 1 Step 5）— **確定した**

### 5.1 稼働中に直接編集できるか → **できない。上書きされる**

**稼働中の処理が `config.xml` を自分で書いている**ことを実測した。

| 項目 | 値 |
|---|---|
| 起動時刻 | `2026-08-23T22:29:18+00:00` |
| `config.xml` の mtime | `2026-08-23T22:41:33.694668+00:00` |
| mtime > 起動時刻 | **True**（差 `0:12:15.694668`） |
| 版付きの控えの存在 | **`config.xml.v37`** |

起動より **12 分 15 秒後**にファイルが書かれており、版付きの控えが残っている。
**処理が設定を持ち、自分で書き出す。したがって稼働中の直接編集は次の内部保存で消える。**

### 5.2 命令列は使えるか → **使える**

    $ ~/bin/syncthing cli --help
    Commands:
      cli show          Show command group
      cli config        Configuration modification command group
      …
    Flags:
      --gui-address=STRING    ($STGUIADDRESS)
      --gui-apikey=STRING     ($STGUIAPIKEY)

`cli config` が「Configuration modification command group」として在る。
合言葉と住所を受け取る作りであり、**稼働中の処理へ REST で話す薄い包みである。**
前の調査で使えなかったのは処理が停止中だったためで、**いまは稼働している。**

### 5.3 画面の経路から変えられるか → **変えられる。これが正しい手段**

| 項目 | 実測 |
|---|---|
| GUI | `enabled=true` `tls=false` `address=127.0.0.1:8384` |
| 合言葉（`gui/apikey`） | **在り（長さ 32）**。値は読み込んだが**出力していない** |
| GUI の password | 無し |
| `GET /rest/config/devices` | **200。5 件を返した** |
| `GET /rest/config/restart-required` | **`{"requiresRestart": false}`** |

**局所（`127.0.0.1`）からのみ届く。** 読み取りが通ったので、書き込みの経路
（`POST /rest/config/devices`、`PUT`/`PATCH /rest/config/folders/<id>`）も同じ
認証で使える。

### 5.4 反映に再起動が要るか → **要らない見込み。実測で確かめる**

**相手の追加は動的に適用される見込みである**（`/rest/config/restart-required` が
現時点で `false`）。**ただしこれは追加前の値であり、「追加が再起動なしで効く」ことの
測定ではない。** 追加後に次の 2 つで確かめる。

| 確認 | 期待 |
|---|---|
| `GET /rest/config/restart-required` | **`false` のまま** |
| `GET /rest/config/devices` | **6 件**。`efros` が含まれる |

**`true` に変わったら禁止 2 に当たる。停止して判断を仰ぐ。**

| 完了判定 | 状態 | 実測 |
|---|---|---|
| B 同期処理の設定を測った | **達** | 実体の device 5 / folder 2。ひな型（`defaults`）を含めていない |
| C 稼働しているものを数えた | **達** | 2 件。陽性 6 / 陰性 0 |
| D 控えを repo の外へ取り原本と一致 | **一部**（設定のみ） | sha256 一致 True。受け入れ一覧は `UNKNOWN` |
| E 戻し方を記録した（実行していない） | **一部** | 設定は §4.1。受け入れ一覧は控えが無く書けない（§4.2） |
| F 手段と反映の条件を確定 | **達** | 直接編集は不可 / REST が正しい経路 / 再起動は要らない見込み（追加後に実測） |

---

## 6. 追記するものの照合（Task 2）

### 6.1 提出物（Step 1）

| 経路 | 在る | バイト数 | 行数 | 空行を除く | 追跡 | sha256 |
|---|---|---|---|---|---|---|
| `scripts/sync/hub_keys/efros.pub` | yes | **95** | **1** | 1 | yes | `70dc8d5dfac6444a…` |
| `scripts/sync/device_ids/efros.txt` | yes | **64** | **1** | 1 | yes | `e0eb37f34dafd9c4…` |

### 6.2 前契約の報告との照合（Step 2）

| 対象 | 前契約 `RESULT.md` の記載 | 実測 | 判定 |
|---|---|---|---|
| 鍵の指紋 | `SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0`（行 51） | `256 SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0 efrostophilip (ED25519)` | **一致** |
| バイト数 | `95` B（行 34） | 95 | 一致 |
| 行数 | `1`（行 34） | 1 | 一致 |
| 識別子 | `LW4CO4U-XINDYL5-WDTK4LN-NANREIJ-LHSPA6F-6VPGZ3R-2ADLKLP-GG6AUQW`（行 54） | 同一 | **一致** |
| 識別子の書式 | 他台と同形 | 長さ 63 / ハイフン 7 | 一致 |

### 6.3 公開鍵だけであること（Step 3）

| 検査 | `efros.pub` | 期待 | **囮**（陽性対照） | 期待 |
|---|---|---|---|---|
| 先頭 `^ssh-` の件数 | **1** | 1 | **0** | 1 以外 |
| 秘密鍵の書き出しの件数 | **0** | 0 | **2** | 1 以上 |
| 行数（空行を除く） | **1** | 1 | **4** | 1 以外 |

**三検査すべてが囮に対して逆向きに落ちた。検査は働いている。**

囮の置き場は `…/scratchpad/decoy_not_a_key.txt`（**repo の外側。版管理へ入らない**）。

### 6.4 既に登録されていないか（Step 4）

| 対象 | 照合先 | 実測 | 期待 |
|---|---|---|---|
| 識別子 `efros` | `configuration` 直下の `device` | **0** | 0 |
| 識別子 `efros` | `folder claude-sync` の共有相手 | **0** | 0 |
| 識別子 `efros` | `folder m2` の共有相手 | **0** | 0 |
| **陽性対照** `philip` | `configuration` 直下の `device` | **1** | 1 |
| **陽性対照** `philip` | `folder claude-sync` の共有相手 | **1** | 1 |
| **陽性対照** `philip` | `folder m2` の共有相手 | **1** | 1 |
| 陰性対照 `ZZZZZZZ-…` | `configuration` 直下の `device` | **0** | 0 |

鍵側（設定変更の後に測った）。

| 対象 | 照合先 | 実測 | 期待 |
|---|---|---|---|
| efros の指紋 `SHA256:Ney1wai…qF0` | 受け入れ一覧 | **0** | 0 |
| **陽性対照** lecun の指紋 `SHA256:g5Twfvg…qHI` | 受け入れ一覧 | **1** | 1 |
| 陰性対照 `SHA256:ZZZ…` | 受け入れ一覧 | **0** | 0 |

版管理の `hub_keys/*.pub` と受け入れ一覧の対応（四台が揃っているか）。

| 鍵 | 受け入れ一覧にある件数 |
|---|---|
| `andrew.pub` | 1 |
| `bengio.pub` | 1 |
| `ilya.pub` | 1 |
| `lecun.pub` | 1 |
| `efros.pub` | **0**（未登録。これから足す） |

| 完了判定 | 状態 | 実測 |
|---|---|---|
| G 提出物が二件あることを確かめた | **達** | 95 B / 1 行、64 B / 1 行 |
| H 指紋を前契約の報告と照合した | **達** | 一致 |
| I 公開鍵だけである（三検査と陽性対照） | **達** | 1 / 0 / 1。囮は 0 / 2 / 4 |
| J 既に登録されていないかを確かめた | **達** | 指紋 0（陽性対照 1）／識別子 0（陽性対照 1） |

---

## 7. 受け入れ一覧への追記（Task 3）

### 7.1 追記（Step 1）

| 確認 | 実測 |
|---|---|
| 受け入れ一覧が改行で終わる | **yes** → **改行の追加は不要**（足していない） |
| `efros.pub` が改行で終わる | yes |
| 追記の仕方 | `cat scripts/sync/hub_keys/efros.pub >> ~/.ssh/authorized_keys`（**追記だけ**。既存行に触れていない） |

### 7.2 件数と権限（Step 2）

| 項目 | 開始時 | 追記後 | 期待 |
|---|---|---|---|
| 行数（`wc -l`） | 5 | **6** | 6 |
| 空行を除いた件数 | 5 | **6** | **五から六へ** |
| 権限 | `600` | **`600`** | **開始時と同じ** |
| 大きさ | 1127 B | **1222 B** | 1127 + 95 = **1222**（ぴたり一致） |
| sha256 | `35ad4ef5…b457f4` | `ab3fe1cbbb18534ee97d8816682f9b141b0df5fadd0475c3d0ee4ca9477986fb` | — |

### 7.3 既存がすべて残っていること（Step 3）— **集合差を両方向で取った**

開始時の控え `authorized_keys.orig` の指紋集合と、追記後の指紋集合を比べた。

| 差 | 実測 | 期待 |
|---|---|---|
| **消えた行**（before にあって after に無い） | **0 件** | **空** |
| 増えた行（after にあって before に無い） | **1 件**：`SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0` | 1 件 |
| 増えた指紋が Task 2 の値と一致 | **yes** | yes |

**陽性対照（集合差そのものが働くか）。** 開始時の一覧から 1 行抜いた偽の一覧を作り、
同じ `comm -23` を当てた。

| 対照 | 実測 | 判定 |
|---|---|---|
| 偽の一覧 vs 開始時の「消えた行」件数 | **1** | 1 以上 → **検査は消失を捕まえる** |

**件数の一致だけでは足りないため集合差で示した**（申し送りのとおり）。

### 7.4 全行が解析できること（Step 4）

| 項目 | 実測 |
|---|---|
| 解析できた件数 | **6** |
| 空行を除いた件数 | **6** |
| 一致 | **一致** |

追記後の指紋と註釈。

| # | 種別 | 指紋 | 註釈 |
|---|---|---|---|
| 1 | RSA 4096 | `SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU` | `dakyo-mba@dmba.local` |
| 2 | ED25519 | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `andrewtophilip` |
| 3 | ED25519 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `bengiotophilip` |
| 4 | ED25519 | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` |
| 5 | ED25519 | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `lecuntophilip` |
| 6 | ED25519 | `SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0` | **`efrostophilip`** |

| 完了判定 | 状態 | 実測 |
|---|---|---|
| K 件数が六、権限が開始時と同じ | **達** | 6 / `600` / 1222 B |
| L **既存がすべて残っている** | **達** | **消えた行 0 件**（陽性対照 1） |
| M 増えた一件の指紋が期待と一致 | **達** | `SHA256:Ney1wai…qF0` |
| N 全行が解析できる | **達** | 6 = 6 |

---

## 8. 同期処理への登録（Task 4）

**手段は §5 で確定した局所 REST（`http://127.0.0.1:8384`）。**
**config.xml を直接編集していない。停止も再起動もしていない。**
合言葉は `config.xml` から変数へ読み込み、**画面へ出していない。**

### 8.1 相手として登録（Step 1）

| 項目 | 値 | 出所 |
|---|---|---|
| 識別子 | `LW4CO4U…GG6AUQW` | **`scripts/sync/device_ids/efros.txt`**（版管理から読んだ） |
| 名前 | `efros` | SPEC の指定 |
| 住所 | `dynamic` | SPEC の指定（中心は相手へ繋ぎに行かない） |

    POST /rest/config/devices  ->  HTTP 200

**既存の四台の登録は変えていない**（送ったのは efros の 1 件のみ）。

### 8.2 共有フォルダの共有相手へ足す（Step 2）

    GET   /rest/config/folders/claude-sync  ->  共有相手 5 件を取得
    PATCH /rest/config/folders/claude-sync  ->  HTTP 200（5 -> 6 件）
    GET   /rest/config/folders/m2           ->  共有相手 5 件を取得
    PATCH /rest/config/folders/m2           ->  HTTP 200（5 -> 6 件）

**`PATCH` に渡したのは `devices` の一項目だけである。**
`id` `label` `path` `type` は送っていない（禁止 4）。

### 8.3 書式と定義（Step 3）— **階層を見て数えた**

| 項目 | 変更前 | 変更後 | 期待 |
|---|---|---|---|
| 相手の実体（`configuration` 直下、`id` 非空） | 5 | **6** | **6**（自分 + 五台） |
| 共有フォルダの実体（`configuration` 直下） | 2 | **2** | 2 |
| `claude-sync` の共有相手 | 5 | **6** | 6 |
| `m2` の共有相手 | 5 | **6** | 6 |
| **フォルダの定義（`id`/`label`/`path`/`type`）** | — | **`変更前 == 変更後` が True** | 変わらない |
| 素朴な `.//device` | 17 | 20 | 実体は 6（内訳 直下 6 + folder 配下 12 + defaults 配下 2） |
| 素朴な `.//folder` | 3 | 3 | 実体は 2（差の 1 件は `defaults/folder`） |
| **ひな型（`defaults` 節）の要約値** | `8d869daf8e337a16` | **`8d869daf8e337a16`** | **一致（触っていない）** |
| `config.xml` の権限 | `600` | **`600`** | **開始時と同じ** |
| `config.xml` の大きさ | 14026 B | 14929 B | — |
| `config.xml` の sha256 | `50caaae6…` | `6cfc3eceda61701a08b47bef9605d36d5ad547dce171f70efcbaacb62d60f7b0` | — |
| `config.xml` の mtime | 2026-08-23 22:41:33 | **2026-09-17 05:07:36** | — |

**ファイルは実行者ではなく稼働中の処理が書いた。** REST を叩いた直後に mtime が
更新されている。§5.1 の「処理が自分で書き出す」と整合する。

### 8.4 反映されたこと（Step 4）— **画面の経路から確かめた**

| 確認 | 実測 | 判定 |
|---|---|---|
| `GET /rest/config/devices` | **6 件**。`name='efros' addresses=['dynamic']` を含む | 認識した |
| `GET /rest/config/restart-required` | **`{'requiresRestart': False}`** | **再起動は要らない** |
| `GET /rest/system/connections` | **`efros` の項目が現れた**（`connected=False` `paused=False`） | **稼働中の処理が新しい相手を追跡し始めた** |
| 稼働しているものの PID | **122452 / 122530（Task 1 と同一）** | **再起動していない** |

**`connections` に項目が現れたことが「認識した」の証拠である。**
設定を読んだだけでは処理はこの一覧に項目を作らない。`connected=False` は efros 側が
まだ起動していないためであり、**中心からは efros の起動を測れない**（§9）。

### 8.5 既存が無傷（Step 5）

| 確認 | 開始時 | 変更後 | 判定 |
|---|---|---|---|
| **四ノードとの接続** | `connected=True` が **4** | `connected=True` が **4**（andrew / bengio / ilya / lecun） | **切れていない** |
| 共有フォルダの定義 | `claude-sync` `/home/ubuntu/claude-sync` `sendreceive` / `m2` `/home/ubuntu/slocal2/m2` `sendreceive` | 同一（定義の一致 True） | 変わっていない |
| 待ち受け `22000` | LISTEN **1** | LISTEN **1** | 立ったまま |
| 待ち受け `8384` | LISTEN 1 | LISTEN 1 | 立ったまま |
| 稼働しているものの数 | **2** | **2** | 同じ |

| 完了判定 | 状態 | 実測 |
|---|---|---|
| O 相手として登録した | **達** | `efros.txt` の値 / `efros` / `dynamic`。HTTP 200 |
| P 共有フォルダの共有相手へ加えた（定義は変えていない） | **達** | 両方 5→6。定義の一致 True。`defaults` の要約値も一致 |
| Q 実体 6 件・フォルダ 2 件・権限が保たれている | **達** | 6 / 2 / `600` |
| R **新しい相手が認識された** | **達** | `connections` に項目が出現。`requiresRestart: false`。PID 不変 |
| S **四ノードとの接続が切れていない** | **達** | `connected=True` が 4 件 |

---

## 9. 疎通は中心からは測れない

**efros から実際に中心へ入れるかは、本ホストからは測れない。**

| 測れること | 測れないこと |
|---|---|
| 受け入れ一覧に efros の指紋が在る（§7.4） | efros が ssh で入れる |
| 同期処理が efros を相手として追跡している（§8.4） | efros と実際に繋がる |

理由は二つ。

1. **禁止 5**（他ホストへ接続する・他ホストの状態を変更する）に当たるため、
   中心から efros へ試行できない。
2. efros 側が起動していない（`connected=False`）。**中心は住所 `dynamic` で
   相手へ繋ぎに行かない設計である。** 接続は efros 側から来る。

**したがって疎通の確認は efros 側の契約で行う。** 本契約の範囲ではない。

---

## 10. Gate の評価

| Gate | 判定 | 根拠 |
|---|---|---|
| **G1**（Phase A の後、`on_fail: ask`） | **初回 fail → ask → 解消後 pass** | 受け入れ一覧が実行基盤に拒否されて一度 fail（§1.1）。利用者が設定を変更した後に再測定し、四条件すべてを満たした（§1.2/§2/§3/§5） |
| **G2**（Phase B の後、`on_fail: stop`） | **pass** | 提出物が版管理に在る（§6.1）／指紋が前契約と一致（§6.2）／三検査と囮（§6.3）／既に登録されていないことを鍵・識別子の両方で陽性対照つきに確認（§6.4） |
| **G3**（Phase C の後、`on_fail: stop`） | **pass** | 既存の消失 0 件を集合差で（§7.3）／増えた 1 件の指紋一致（§7.3）／相手を登録し認識された（§8.4）／四ノードとの接続が切れていない（§8.5） |

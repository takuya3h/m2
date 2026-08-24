# RESULT — T-2026-08-24-andrew-syncthing-node

**verdict:** `pass`  **kind:** `impl`  **host:** `Andrew`
**branch:** `feat/andrew-syncthing-node`  **repo:** `~/slocal2/m2`  **実行日:** 2026-08-24 (UTC)

**二台目のノードが中心へ繋がり、双方向でファイルが届いた。**
手続きの証跡は `audit.md` にある。本書は起票者が判断に使う事実だけを書く。

## 判定

| Gate | 結果 | 根拠（`audit.md` の行） |
|---|---|---|
| G1 | **pass** | 開始状態を要約値で封印。実行権 `644` / 目印 0 件 / 同期処理 0 件 / 中継 0 件を両方向の対照つきで確認。控えは repo 外。識別子一致。`ssh -N` で中心へ入れた（`audit.md:98-332`） |
| G2 | **pass** | 実行ファイル `e8a08fdd…` が中心と一致・権限 `644`。自動更新 `0`、告知/外部中継を無効、中心を `tcp://127.0.0.1:22001` で登録、最上位 folder 2 件、解析可・権限保持（`audit.md:334-467`） |
| G3 | **pass** | 目印 → 中継（`22001` LISTEN、引数に中心の住所）→ 実行権 → 起動。版が中心と同じ。folder 2 件・自動更新 0 のまま（`audit.md:469-648`） |

## 完了判定

| # | 実測 |
|---|---|
| A | `syncthing` `32ab747e…` 26730145 B **`644`** / `config.xml` `c3783e9d…` 8495 B `600` / `cert.pem` `bb9a4442…` / `key.pem` `92f44d2e…` / `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / `.stignore` = `.stglobalignore` = `61593e99…`。**目印 0 件・同期処理 0 件・中継 0 件**。対照: 肯定 `zsh=3` / 否定 `zzz_no_such_exe=0`、口 `22`=LISTEN / 口 `1`=CLOSED |
| B | `~/claude-sync` = **1510 バイト / 1 件**（`sync-alerts.log` のみ）。repo = **54745194976 バイト**。`du -sb` は最上位ディレクトリ自身の 4096 を含まない |
| C | 控え `~/.local/state/syncthing.bak.20260824-150939`（要約値 3 件とも一致）。`apikey_len=32 empty=False` のため**版管理へ置かない**。秘密鍵の書き出しの混入 0（陽性対照 1） |
| D | `audit.md:246-276`。**実行権を `644` に落とせば起動が止まる**（`keeper.sh` が `[ -x ~/bin/syncthing ]` を見る）ことを含む。実行していない |
| E | 設定内 `3C2LTP7-…-UVZB5A4` = `scripts/sync/device_ids/andrew.txt` |
| F | 🟢 `Server accepts key … SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` / `Authenticated to 192.168.196.150 … using "publickey"` / `denied=0`。`ssh -N` で**中心に命令を実行していない**。受け入れ控えは隔離（`~/.ssh/known_hosts` を触っていない） |
| G | v1.27.10 → **v2.1.3**。取得物 `f929eb8e…` 11821325 B、実行ファイル **`e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4`** 27045912 B、権限 **`644`**。中心の実測と完全一致 |
| H | `options/autoUpgradeIntervalH: 12 → 0`。要素名は `options` 配下の実在一覧を出して確認してから変更 |
| I | `globalAnnounceEnabled: true → false` / `relaysEnabled: true → false` / `localAnnounceEnabled` は `true` のまま |
| J | `id=3J4TRX4-…-DZOCQQE`（`scripts/sync/device_ids/philip.txt` から）name=`philip` address=`tcp://127.0.0.1:22001`。**他の三台は登録していない** |
| K | **最上位 folder = 2 件**（`claude-sync` = `/home/ubuntu/claude-sync`、`m2` = `/home/ubuntu/slocal2/m2`、ともに `sendreceive`、共有相手 2 件）。単純検索は **3 件**を返す（差はひな型 `defaults/<folder id="">`。触っていない） |
| L | `xml_ok=True` / `device_count=2` / `config.xml` `600` / `cert.pem` `664` / `key.pem` `600`（鍵は要約値も開始時と同一） |
| M | `~/.tunnel_to_philip` **60 B `600` 2 行**。1 行目 `<KEYDIR>/id_ed25519_andrewtophilip`、2 行目 `192.168.196.150` |
| N | 🟢 `port_22001=LISTEN hits=2`。中継 pid `86521`（親 `40838` = `keeper.sh`）、引数に **`ubuntu@192.168.196.150`**。目印 `15:18:02` → 中継 `15:38:29` = **1227 秒** |
| O | `644` → `755`（ctime `15:39:16`）。要約値 `e8a08fdd…` **不変**。`15:38:39` 時点で `22001=LISTEN` と `perm=644` を**同時に観測**しており、**中継が 47 秒早い** |
| P | **2 件**：`89005`（親 `40838` = keeper）と `89026`（親 `89005`）。**版 `v2.1.3` で中心と同じ**。`22000` LISTEN、`22001` LISTEN のまま |
| Q | `config_version 37 → 52` へ移行（要約値は `5ea37224…` → `7f80508e…` と変わる）。**最上位 folder 2 件・device 2 件・`autoUpgradeIntervalH=0`・`global=false`・`relays=false`・`local=true` すべて保持。`grep -c -i upgrade ~/.syncthing.log = 0`** |
| R | `16:08:21 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001 remote.name=philip remote.client=syncthing remote.version=v2.1.3)` |
| S | `probe-andrew.txt` **83 B** `41f4c7dcab706950191ad1062c1b3d6c7d94570cac1f3f3e027de1ff0b3b82a8`。内容に時刻 `2026-08-24T16:09:23Z` と乱数を含む |
| T | 🟢 `availability=[3J4TRX4-…-DZOCQQE]`、`modifiedBy=3C2LTP7`。`completion(claude-sync, philip)=100.0000% needBytes=0`。**自ホストの REST のみ。中心で命令を実行していない**。陽性対照 5 件（下記） |
| U | **1510 B / 1 件 → 18858 B / 7 件**（+17348 B / +6 件）。**消えたものは無い**。`probe-bengio.txt`（40 B）が中心から届いた |
| V | `m2`: 起動直後 `needBytes=689548250 needItems=1731` → `16:12:52` に `needBytes=0 needFiles=0 errors=0`。**約 4 分半でバイト転送が収束**。中心側は `needItems=1478`（`needBytes=0` のため大きさ零の要素）。**完了は待っていない** |
| W | 本書は 7 節・150 行以内。手続きの証跡は `audit.md`（779 行）へ分離 |
| X | `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…`（開始時と同一）。`scripts/sync/` の差分 **0 行**。`.stignore` = `.stglobalignore` = `61593e99…`（開始時と同一）。**目印 1 件** |
| Y | §秘匿検査（陽性対照つき。**検査は値を出力していない**） |
| Z | §送出 |

## 実測（次の契約で使う値）

| 項目 | 値 |
|---|---|
| 中心の住所 | **`192.168.196.150` 口 `50072`**。`handoff.md:8` の `192.168.196.176` は**古い案。使わない** |
| 目印の中身 | 1 行目 `~/.ssh/id_ed25519_<host>tophilip`、2 行目 `192.168.196.150`、権限 `600` |
| 版を揃える手順 | `https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz`。取得物 `f929eb8e…` 11821325 B → 実行ファイル `e8a08fdd…` 27045912 B。**配布物の中に同名の別物が 3 件ある。大きさで特定すること** |
| 待ち時間 | 目印 → 中継 **1227 秒**（bengio は 413 秒）。**差は周回の位相であってホスト差ではない**。`keeper.sh` は `sleep 1800`。実行権 → 起動は**次の周回**（本ホストは `15:39:16` → `16:08:21`、1745 秒） |
| 登録名 | andrew の初期値も **`Andrew`**（先頭が大文字）だった。**`ilya` `lecun` も同じと見てよい** |
| `~/claude-sync` の開始値 | andrew は **1510 B / 1 件**（bengio は 4031 B / 1 件）。**ホストごとに違う。前ホストの値を引き継がない** |
| 届いたかの確かめ方 | `/rest/db/file?folder=<f>&file=<name>` の `availability` に中心の識別子。**走査前は 404 を返す。`/rest/db/status` が `state=idle` になってから問うこと** |
| 衝突の実測 | `sync-alerts.log` は**上書きされず**、中心側の内容が `…sync-conflict-<日時>-<識別子先頭>.log` として併存。本ホストでは **2 件**生まれた（bengio 由来の 1 件も届いた）。**中身で確かめること**（本体に andrew の行が 17、衝突側に bengio 40 + philip 6） |
| repo の規模 | `du -sb` **54745194976 B**、syncthing の global **42010521855 B / 5193 件**。bengio の 40.74 GB より大きい |
| `~/.ssh/**` | **実行基盤の deny 規則で読めない**。指紋は `scripts/sync/hub_keys/<host>.pub` で照合する |

## 起票者の誤り

`result.yaml` の `issuer_defects` と対。**4 件**。

1. **`asserted_without_measuring`** — SPEC「前契約で確定した事実」表は repo を「**五十一ギガ**（同期対象は四十・七四ギガ）」と断定するが、andrew の実測は `du -sb` **54745194976 B**、syncthing の global **42010521855 B / 5193 件**。**bengio の値をホスト非依存の定数として書いている。**
2. **`asserted_without_measuring`** — SPEC Task 3 Step 2 は中継まで「**最大六十分**」と書くが、`keeper.sh` の実装は `sleep 1800`（30 分）である。**実測 1227 秒。** 上限が実装の 2 倍で書かれており、待つべき時間の判断を誤らせる。
3. **`check_does_not_check`** — SPEC Task 4 Step 2 は `availability` を見よと指示するが、**走査前は同じ問いが 404 を返す**ことに触れていない。指示どおり置いた直後に問うと 404 が出て「中心が持っていない」と誤読しうる。**`/rest/db/status` が `state=idle` になるのを待つ必要がある。**
4. **`asserted_without_measuring`** — SPEC は中心の住所を「中継の出口 `tcp://127.0.0.1:22001`」としか書かず、**目印の 2 行目に必要な SSH の住所を与えていない**。版管理内の `handoff.md:8` は `192.168.196.176` を案として持つが**これは誤りで**、前契約 `audit.md:547` の実測 `192.168.196.150` が正しい。**契約だけでは目印を作れない。**

## 逸脱

`result.yaml` の `deviations` と対。**逸脱は「なし」ではない。5 件。**

1. **`environment`** — `make task-start` を実行できなかった。未commit 1 件は契約そのものであり、分岐 `feat/andrew-syncthing-node` も既存のため、`scripts/task_start.sh` の前提検査（作業ツリー・分岐重複）を原理的に通せない。前契約も同じ理由で実行していない。
2. **`environment`** — `~/.ssh/**` を読めない（実行基盤の deny）。秘密鍵の権限を直接確認できず、**版管理側の公開鍵の指紋**（`SHA256:7yvApjr/…`）と `ssh -v` が出した同じ指紋で代えた。
3. **`judgement`** — 中心への到達確認を `ssh -N`（中心で命令を実行しない形）で行った。禁止 1 を守るため。前契約の判断を踏襲。
4. **`judgement`** — 秘匿検査で値の一部を表示せず、**長さと有無**だけを測った（申し送り #6）。
5. **`judgement`** — 禁止 6 に従い `make taskindex` / `make inbox` を**実行していない**。技能書は投影の確認を求めるが、契約の禁止が勝つ。

## 想定外・UNKNOWN

| 事象 | 扱い |
|---|---|
| `/rest/db/file` が一度目に **404** | 想定外。**走査前だったため**。`state=idle` 後に 200。起票者の誤り 3 として記録 |
| 衝突ファイルが **2 件**生まれた | **正常**（SPEC「記録が衝突した → 正常である。両方残る」）。中身で両方残存を確認 |
| 中心側 `m2` の `needItems=1478` | `needBytes=0` のため大きさ零の要素と解釈した。**中心で命令を実行できないため内訳は UNKNOWN** |
| `~/.ssh/known_hosts` の前後比較 | **UNKNOWN**（deny 規則で読めない）。自分の確認は隔離先へ書いた。常駐処理の中継が `Permanently added` を書いた記録はある |
| 中心側の状態 | **触っていない**。禁止 1 により中心で命令を実行していないため、中心から見た値は自ホストの REST 経由の観測に限る |

## 送出

（§送出・秘匿検査・台帳は下記。出力の全文は `audit.md` にある）

# RESULT — T-2026-08-24-lecun-syncthing-node

**verdict:** `pass`  **kind:** `impl`  **host:** `lecun`（`hostname` も `lecun` を返す）
**branch:** `feat/lecun-syncthing-node`  **repo:** `~/slocal/m2`  **実行日:** 2026-08-24 (UTC)

**四台目のノードが中心へ繋がり、双方向でファイルが届いた。五台の構成が揃った。**
手続きの証跡は `audit.md` にある。本書は起票者が判断に使う事実だけを書く。

## 判定

| Gate | 結果 | 根拠（`audit.md` の行） |
|---|---|---|
| G1 | **pass** | 開始状態を要約値で封印。実行権 `644` / 目印 0 / 同期処理 0 / 中継 0 を**両方向の対照つき**で確認。控えは repo 外。識別子一致。`ssh -N` で中心へ入れた（`audit.md:119-372`） |
| G2 | **pass** | 実行ファイル `e8a08fdd…` が中心と一致・権限 `644`。自動更新 `0`、告知/外部中継を無効、**登録名は初期値で既に `lecun`**、中心を `tcp://127.0.0.1:22001` で登録、最上位 folder 2 件、解析可・権限保持（`audit.md:373-518`） |
| G3 | **pass** | 目印 → 中継（`22001` LISTEN、引数に中心の住所）→ 実行権 → 起動。版が中心と同じ。folder 2 件・自動更新 0 のまま（`audit.md:520-681`） |

## 完了判定

| # | 実測 |
|---|---|
| A | `syncthing` `32ab747e…` 26730145 B **`644`** / `config.xml` `41a4ab48…` 8494 B `600` / `cert.pem` `bbc68a93…` 790 B `664` / `key.pem` `7b1f37f7…` 288 B `600` / `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / `.stignore` = `.stglobalignore` = `61593e99…`。**目印 0 件・同期処理 0 件・中継 0 件**。対照: 肯定 `zsh=4` / 否定 `zzz_no_such_exe=0`、口 `22`=LISTEN / 口 `1`=CLOSED |
| B | `~/claude-sync` = **1610 バイト / 1 件**（`sync-alerts.log` のみ）。repo = **7652515378 バイト**。**前ホストの値を引き継いでいない**（bengio 4031 B、andrew 1510 B、ilya 4528 B。repo は andrew 54745194976 / ilya 47515332495） |
| C | 控え `~/.local/state/syncthing.bak.20260824-192105`（要約値 3 件とも一致・権限も一致）。旧実行ファイルは `~/syncthing-rollback/syncthing.v1.27.10.orig`（`32ab747e…`）。`apikey_len=32 empty=False` のため**版管理へは置かない**。秘密鍵の書き出しの混入 `config.xml=0`（陽性対照 `key.pem=1`） |
| D | `audit.md:289-314`。**実行権を `644` に落とせば起動が止まる**（`keeper.sh:41` が `[ -x ~/bin/syncthing ]` を見る）ことを含む。**実行していない** |
| E | 設定内 `OOOTQMG-…-KRFOWA3` = `scripts/sync/device_ids/lecun.txt` |
| F | 🟢 `Server accepts key … SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` / `Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey"` / `denied=0`。指紋は版管理の `hub_keys/lecun.pub` と一致。`ssh -N` で**中心に命令を実行していない**。受け入れ控えは隔離（`~/.ssh/known_hosts` を触っていない） |
| G | **v1.27.10**（`strings` で実測）→ **v2.1.3**。取得物 `f929eb8e…` 11821325 B、実行ファイル **`e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4`** 27045912 B、権限 **`644`**。中心の実測と完全一致。配布物の同名 3 件（27045912 / 1709 / 175 B）を大きさで切り分けた。**`644` を付けた別名を作って `mv` で差し替え、実行権が立つ隙を作らなかった** |
| H | `options/autoUpgradeIntervalH: 12 → 0`。`options` 配下の実在 54 件を出して名前を確認してから変更 |
| H2 | 🔴 **初期値は `lecun`。既に正しく、置換件数 0 が正解であった。** 四台の実測は bengio=`Bengio` / andrew=`Andrew` / ilya=`aolab` / **lecun=`lecun`** と**すべて異なった**。置換ではなく**現在値の読み出し**で判定したため、「当たらなかった 0」と「既に正しい 0」を取り違えていない |
| I | `globalAnnounceEnabled: true → false` / `relaysEnabled: true → false` / `localAnnounceEnabled` は `true` のまま |
| J | `id=3J4TRX4-…-DZOCQQE`（`scripts/sync/device_ids/philip.txt` から）name=`philip` address=`tcp://127.0.0.1:22001`。**他の三台は登録していない** |
| K | **最上位 folder = 2 件**（`claude-sync` = `/home/ubuntu/claude-sync`、**`m2` = `/home/ubuntu/slocal/m2`**、ともに `sendreceive`、共有相手 2 件）。単純検索は **3 件**を返す（差はひな型 `defaults/<folder id="">`。触っていない） |
| K2 | 🔴 **`m2` の位置に本ホストの実際の値を使った。** 他四台の `/home/ubuntu/slocal2/m2` を写していない。`~/slocal2` は**存在しない**ことを実測し、`keeper.sh` の `M2DIR` 解決と一致することを確かめた |
| L | `xml_ok=True` / `top_level_device_count=2` / `config.xml` `600` / `cert.pem` `664` / `key.pem` `600`（鍵は要約値も開始時と同一。生成も変更もしていない） |
| M | `~/.tunnel_to_philip` **59 B `600` 2 行**。1 行目 `/home/ubuntu/.ssh/id_ed25519_lecuntophilip`、2 行目 **`192.168.196.150`**（`handoff.md` の `192.168.196.176` は使わない）。`umask 077` を先に置き、権限が緩い隙を作らなかった |
| N | 🟢 `port_22001=LISTEN`。中継 pid `135351`（親 `89614` = `keeper.sh`）、引数に **`ubuntu@192.168.196.150`** と `-L 22001:127.0.0.1:22000`。目印 `19:28:34.892` → 中継 `19:54:44.305` = **1569.413 秒** |
| O | `644` → `755`（`19:55:44.547`、ctime `1787601344.543`）。要約値 `e8a08fdd…` **不変**。**中継が 60.242 秒早い**。中継が立った時点で `22001=LISTEN` と `perm=644` と `syncthing=0 件`を**同時に観測**している |
| P | **2 件**：`140103`（親 `89614` = keeper。監視役）と `140120`（親 `140103`。作業役）。**版 `v2.1.3` で中心と同じ**。`22000` LISTEN、`22001` LISTEN のまま。実行権 → 起動は**次の周回**（`19:55:44.547` → `20:24:50.932`、**1746.4 秒**） |
| Q | `config_version 37 → 52` へ移行（要約値は `8d3145a2…` → `eb3cb64c…` と変わる）。**最上位 folder 2 件・device 2 件・`autoUpgradeIntervalH=0`・`global=false`・`relays=false`・`local=true` すべて保持。`grep -c -i upgrade ~/.syncthing.log = 0`** |
| R | `20:24:42 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001 remote.name=philip remote.client=syncthing remote.version=v2.1.3)` |
| S | `probe-lecun.txt` **86 B** `b10b8fbbe92f109c8ce03ef42d805198efa0829750ff477b7d493fee06c9390d`。内容に時刻 `2026-08-24T20:25:34+0000` と乱数 `f8eef03c…` を含む |
| T | 🟢 `availability=[3J4TRX4-…-DZOCQQE]`、`modifiedBy=OOOTQMG`、`size=86`。`completion(claude-sync, philip)=100% needBytes=0 needItems=0`、`completion(m2, philip)=100%`。**自ホストの REST のみ。中心で命令を実行していない**。陽性対照: 存在しない名前は **404**、実在する名前は **200** |
| U | **1610 B / 1 件 → 38214 B / 13 件**（**+36604 B / +12 件**）。**消えたものは無い**。`probe-bengio.txt`（40 B）`probe-andrew.txt`（83 B）`probe-ilya.txt`（78 B）が中心から届き、**四台の試験ファイルが揃った** |
| V | **T1 20:26:57.693 → T2 20:28:00.749（63.056 秒）で `localBytes` 9285625122 → 15687225893 = 101522468 B/s（≒101.5 MB/s）、`localFiles` 1552 → 2160（9.6 件/s）。残り 26016195954 B。完了は待っていない。** 最終観測 **20:40:44Z** では **収束していた**（`state=idle`、`localBytes=globalBytes=42010845130`、`localFiles=globalFiles=5256`、`needBytes=0` / `needFiles=0`、`errors=0` / `pullErrors=0`、`du -sb` repo = 48999900426）。**収束した時刻そのものは測っていない（UNKNOWN）** |
| W | 本書は 7 節・150 行以内。手続きの証跡は `audit.md` へ分離 |
| X | `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / `~/bin/m2-sync.sh` `bcf46ba9…`（開始時と同一）。`scripts/sync/` の差分 **0 行**（`hub_keys/` `device_ids/` の要約値も同一）。`.stignore` = `.stglobalignore` = `61593e99…`（同一）。**目印 1 件**。常駐処理 pid `89614` は生きている（止めていない） |
| Y | §送出（陽性対照つき。**検査は値を出力していない**） |
| Z | §送出 |

## 実測（次の契約で使う値）

| 項目 | 値 |
|---|---|
| **五台の状態** | **philip（中心）+ bengio / andrew / ilya / lecun の四ノードが接続済み。設定共有の再構築は完了。残るのは共有領域の中身と実験環境の復旧** |
| 版管理の位置 | **`lecun` だけ `~/slocal/m2`。他四台は `~/slocal2/m2`。`keeper.sh` の `M2DIR` が `[ -d ~/slocal2 ]` で分岐するため、写し間違えなければ手順は同一で通る** |
| **待ち時間の上限** | 🔴 **目印 → 中継 = 1569.413 秒。SPEC の「四百十三〜千三百五十九秒」を超えた。** 実装は `sleep 1800` であるから**上限は約 1800 秒 + α と見るべきで、過去の実測の幅を上限として扱ってはならない**。実行権 → 起動は **1746.4 秒**（次の周回） |
| **登録名の初期値** | 🔴 四台とも異なった。bengio=`Bengio` / andrew=`Andrew` / ilya=`aolab` / **lecun=`lecun`（既に正しい）**。**置換ではなく読み出しで判定すること。「件数 0」には「当たらなかった」と「既に正しい」の 2 通りがある** |
| `~/claude-sync` の開始値 | lecun は **1610 B / 1 件**（bengio 4031 / andrew 1510 / ilya 4528）。**ホストごとに違う** |
| repo の規模 | 開始 `du -sb` **7652515378 B**。群れ全体は **42010845130 B / 5256 files**。**本ホストは大きく不足している側で、受け取る量が最も多い**（他三台は 47.5G / 54.7G） |
| 同期の速さ | **101.5 MB/s / 9.6 件/s**（実測 63 秒間）。**起動 20:24:50.932 から 20:40:44Z までのどこかで収束した**（`needBytes=0` / `state=idle`。**上限 949 秒。正確な時刻は UNKNOWN**）。ilya は 75 秒、andrew は約 4 分半。**lecun は 34.4 GB を受け取ったため最も長い** |
| 衝突の実測 | **本契約で 2 件**生まれた（`…-OOOTQMG.log`、6534 B / 61 行）。**自分の内容（20 行・全 `[lecun]`）が `sync-alerts.log` として勝ち、中心側（`[ilya]` 51 / `[bengio]` 4 / `[philip]` 4 / `[andrew]` 2）が衝突ファイルになった**（ilya と同じ向き。andrew とは逆）。**両方残る** |
| 🔴 **同期が `experiments/` へ書く** | **`m2` フォルダは repo 全体であり、`.stignore` は `experiments/baselines/_*` しか除外しない。** 実行中に `experiments/baselines/s0_002_maskdino_bbox_seed123/.syncthing.epoch_12.pth.tmp` が現れた。**契約の禁止 11（`experiments/**` を変更しない）と、契約自身が定義した同期とが両立しない。** 次の契約で除外規則を決めること |
| 中心の住所 | **`192.168.196.150` 口 `50072`**。`handoff.md` の `192.168.196.176` は**古い案。使わない** |
| `~/.ssh/**` | **実行基盤の deny 規則で一覧できない**（個別の `test -f` は通った）。指紋は `scripts/sync/hub_keys/<host>.pub` で照合する |
| **`~/bin/**` と `~/.local/state/**`** | 🟢 **本ホストでは拒否されなかった。** ilya では拒否された。**ホストの差ではなく実行基盤の状態の差である** |
| 常駐処理が `known_hosts` を書く | `keeper.sh` の ssh は `-o StrictHostKeyChecking=accept-new` を持ち、**`~/.ssh/known_hosts` へ書く**（`~/.tunnel.log` に `Permanently added` が 1 行）。**実行者の操作ではない** |

## 起票者の誤り

`result.yaml` の `issuer_defects` と対。**5 件。**

1. **`check_does_not_check`** — SPEC「環境の事実」は自己一致への対処として「**`/proc/*/cmdline` を実行ファイル名で照合する**」と指示するが、**`cmdline` の照合も自己一致する。** 実測で否定対照 `zzz_no_such_token` が **1** を返した（自分の命令行にその語が含まれるため）。指示どおりだと中継や同期処理の件数を 1 多く数える。**`/proc/<pid>/exe` の readlink で絞る必要がある。**
2. **`self_contradiction`** — 待ち時間の記載が本文内で食い違う。「前契約で確定した事実」表は「**四百十三〜千二百二十七秒**」、Task 3 Step 2 は「**四百十三〜千三百五十九秒**」。同じ量に 2 つの上限があり、どちらを基準に「立たない」と判断すべきかが定まらない。
3. **`asserted_without_measuring`** — その上限自体が過去 3 件の最大値にすぎない。**本ホストの実測は 1569.413 秒で両方を超えた。** 実装は `sleep 1800` であるから上限は約 1800 秒である。指示どおり 1359 秒を上限と見れば、**正常に進んでいる最中に「中継が立たない」と誤って報告する。**
4. **`check_does_not_check`** — `spec.yaml` の `inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は**本契約の手順のどこでも使わない**。SPEC 自身が「参照しない」と書いている。**検証は入力の存在を見るが、使われるかは見ない**ため無関係な入力が残り続ける。**ilya が同じ誤りを報告したのに是正されずに繰り返された。**
5. **`asserted_without_measuring`** — SPEC「0. 前提」は `make task-start` を無条件に指示するが、**前三契約（bengio / andrew / ilya）はいずれも作業ツリーの未追跡ファイルにより実行できていない**と報告済みである。指示どおり実行すると `exit 3` で止まり、**契約の取り込みそのものが始まらない。** 本契約でも一度目は同じ理由で止まった。

## 逸脱

`result.yaml` の `deviations` と対。**逸脱は「なし」ではない。5 件。**

1. **`judgement`** — `make task-start` を通すため、**開始前から存在した `docs/sessions/digest/` の未追跡 3 件を scratchpad へ退避した**（消していない。禁止 7）。報告の後に元へ戻す。**前三契約は退避せず `task-start` 自体を諦めている。**
2. **`environment`** — `~/.ssh/` の一覧が実行基盤に拒否された。秘密鍵の権限を直接確認できず、**版管理側の公開鍵の指紋**（`SHA256:g5Twfvg…`）と `ssh -v` が出した同じ指紋で代えた。**回避していない。**
3. **`judgement`** — 中心への到達確認を `ssh -N`（中心で命令を実行しない形）で行った。禁止 1 を守るため。前契約の判断を踏襲。
4. **`judgement`** — 秘匿検査で値を表示せず、**長さと有無と件数**だけを測った（申し送り 6）。
5. **`judgement`** — 禁止 6 に従い `make taskindex` / `make inbox` を**実行していない**。技能書は投影の確認を求めるが、契約の禁止が勝つ。

## 想定外・UNKNOWN

| 事象 | 扱い |
|---|---|
| 登録名の初期値が**既に `lecun`** | **想定外。** 四台とも違い、本ホストだけ初期値が正しかった。**置換件数 0 が正解**という、前三契約に無い形。起票者の誤りではなく実測の差として記録 |
| 目印 → 中継が **1569.4 秒** | **想定外。** SPEC の上限 1359 秒を超えた。起票者の誤り 3 として記録 |
| 同期が `experiments/` へ書いた | **想定外。** `.syncthing.epoch_12.pth.tmp` が現れた。**禁止 11 と契約自身の同期定義が両立しない。** 触っていない。次の契約への申し送り |
| 衝突ファイルが **2 件**生まれた | **正常**（SPEC「記録が衝突した → 正常である。両方残る」）。中身で勝敗を確かめた。**自分が勝った** |
| `m2` の同期 | **待たなかった**（SPEC の指示）。進み方を記録した後、報告の作成中に**収束した**。最終観測 20:40:44Z で `needBytes=0` / `state=idle`。**収束時刻は測っていない（UNKNOWN、上限 949 秒）** |
| `~/.ssh/known_hosts` の前後比較 | **UNKNOWN**（deny 規則で一覧できない）。自分の確認は隔離先へ書いた。常駐処理が書いた 1 行は `~/.tunnel.log` から確認 |
| 中心側の内部状態 | **触っていない**。禁止 1 により中心で命令を実行していないため、中心から見た値は自ホストの REST 経由の観測に限る |
| 新版 `syncthing` の版文字列 | `strings` の `^v2\.1\.3$` では**当たらなかった**。同一性は要約値（`e8a08fdd…`）で確定し、起動後に `--version` が `v2.1.3` を返すことで裏づけた |

## 送出

| 項目 | 結果 |
|---|---|
| PR | **#146**（base `phase0`、OPEN、Draft ではない）。既存の PR は無かった（`gh pr list --head feat/lecun-syncthing-node --state all` が `[]`） |
| commit | `49b24fbb`。6 files changed, **1529 insertions(+), 0 deletions(-)**。**追加のみ**。手元 `49b24fbb…` = `origin/feat/lecun-syncthing-node` `49b24fbb…`。**範囲外のファイル 0 件**（契約のディレクトリと受け皿のみ）。開始前から存在した `docs/sessions/digest/…` は含めていない |
| `make task-validate` | **`validate_exit=0`**（`OK` / 1 task(s), 0 failed） |
| `make task-preflight` | **`preflight_exit=0`**（4 PASS / 1 WARN / 4 SKIP / 0 FAIL）。WARN は `P9 spec_lint` の `separated_source@SPEC.md:48` **1 件のみで、これは誤検知である**（SPEC.md:47-48 は行継続で折った 1 命令であり `source` は同じ命令の中にある。検査器が行を単位に見るため）。**SKIP は `P2` `P3` `P4` `P5` の 4 件。合格ではなく実行されなかったことを意味する** |
| `make forbidden-check` | **`forbidden_exit=0`**（`status: pass`、`changed: 6`、`checked: 6`、`violations: []`、`errors: []`） |
| 秘匿検査 | **`secretscan_exit=0`**。実値照合 **`literal_leaks=0`**（対象 3 種: `NOTION_API_KEY` len=50 / `WANDB_API_KEY` len=86 / 画面の鍵 len=32。**値は出力していない**）、形の該当 **`shape_hits=0`**（規則 3 件）。陽性対照 `decoy_literal_detected=3/3` / `decoy_shape_hits={Notion の内部鍵:2, 鍵らしい代入:1, 秘密鍵の書き出し:1}`。**囮は変数の中だけに置き、ファイルへ書いていない＝commit していない** |
| 台帳 | **返した。** `verdict=pass` / `n_issuer_defects=5` / `report_sha256=2eace207…` / `report_bytes=16625` / `replaced_blocks=0`。`report_exit=0` |
| 抑止 | **外した。** `mv .sync-pause .sync-pause.released`（削除ではなく移動。技能書の既定）。§抑止（`audit.md`） |

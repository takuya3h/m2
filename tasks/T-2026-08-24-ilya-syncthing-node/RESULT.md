# RESULT — T-2026-08-24-ilya-syncthing-node

**verdict:** `pass`  **kind:** `impl`  **host:** `ilya`（`hostname` は `aolab` を返す）
**branch:** `feat/ilya-syncthing-node`  **repo:** `~/slocal2/m2`  **実行日:** 2026-08-24 (UTC)

**三台目のノードが中心へ繋がり、双方向でファイルが届いた。**
手続きの証跡は `audit.md` にある。本書は起票者が判断に使う事実だけを書く。

## 判定

| Gate | 結果 | 根拠（`audit.md` の行） |
|---|---|---|
| G1 | **pass** | 開始状態を要約値で封印。実行権 `644` / 目印 0 件 / 同期処理 0 件 / 中継 0 件を両方向の対照つきで確認。控えは repo 外。識別子一致。`ssh -N` で中心へ入れた（`audit.md:91-305`） |
| G2 | **pass** | 実行ファイル `e8a08fdd…` が中心と一致・権限 `644`。自動更新 `0`、告知/外部中継を無効、**登録名 `aolab` → `ilya`**、中心を `tcp://127.0.0.1:22001` で登録、最上位 folder 2 件、解析可・権限保持（`audit.md:307-488`） |
| G3 | **pass** | 目印 → 中継（`22001` LISTEN、引数に中心の住所）→ 実行権 → 起動。版が中心と同じ。folder 2 件・自動更新 0 のまま（`audit.md:490-650`） |

## 完了判定

| # | 実測 |
|---|---|
| A | `syncthing` `32ab747e…` 26730145 B **`644`** / `config.xml` `b548d117…` 8494 B `600` / `cert.pem` `0081011c…` / `key.pem` `8fac365b…` / `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / `.stignore` = `.stglobalignore` = `61593e99…`。**目印 0 件・同期処理 0 件・中継 0 件**。対照: 肯定 `zsh=5` / 否定 `zzz_no_such_exe=0`、`keeper.sh=1` / `zzz_no_such_token=0`、口 `22`=LISTEN / 口 `1`=CLOSED |
| B | `~/claude-sync` = **4528 バイト / 1 件**（`sync-alerts.log` のみ）。repo = **47515332495 バイト**。**前ホストの値を引き継いでいない**（bengio 4031 B、andrew 1510 B、repo は andrew 54745194976 B） |
| C | 控え `~/.local/state/syncthing.bak.20260824-164557`（要約値 3 件とも一致）。旧実行ファイルは `~/syncthing-rollback/syncthing.v1.27.10`（`32ab747e…`）。`apikey_len=32 empty=False` のため**版管理へは置かない**。秘密鍵の書き出しの混入 0（陽性対照 1） |
| D | `audit.md:220-249`。**実行権を `644` に落とせば起動が止まる**（`keeper.sh:41` が `[ -x ~/bin/syncthing ]` を見る）ことを含む。実行していない |
| E | 設定内 `UODEAXZ-…-X6SDBQY` = `scripts/sync/device_ids/ilya.txt` |
| F | 🟢 `Server accepts key … SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` / `Authenticated to 192.168.196.150 … using "publickey"` / `denied=0`。指紋は版管理の `hub_keys/ilya.pub` と一致。`ssh -N` で**中心に命令を実行していない**。受け入れ控えは隔離（`~/.ssh/known_hosts` を触っていない） |
| G | **v1.27.10**（`strings` で実測）→ **v2.1.3**。取得物 `f929eb8e…` 11821325 B、実行ファイル **`e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4`** 27045912 B、権限 **`644`**。中心の実測と完全一致。配布物の同名 3 件（27045912 / 175 / 1709 B）を大きさで切り分けた |
| H | `options/autoUpgradeIntervalH: 12 → 0`。要素名は `options` 配下の実在一覧を出して確認してから変更 |
| H2 | 🔴 **初期値は `aolab`**（`Ilya` ではない）＝ `hostname` そのもの＝**中心と同じ値**。`ilya` へ直した。置換は件数 1 を表明して実行 |
| I | `globalAnnounceEnabled: true → false` / `relaysEnabled: true → false` / `localAnnounceEnabled` は `true` のまま |
| J | `id=3J4TRX4-…-DZOCQQE`（`scripts/sync/device_ids/philip.txt` から）name=`philip` address=`tcp://127.0.0.1:22001`。**他の三台は登録していない** |
| K | **最上位 folder = 2 件**（`claude-sync` = `/home/ubuntu/claude-sync`、`m2` = `/home/ubuntu/slocal2/m2`、ともに `sendreceive`、共有相手 2 件）。単純検索は **3 件**を返す（差はひな型 `defaults/<folder id="">`。触っていない） |
| L | `xml_ok=True` / `top_level_device_count=2` / `config.xml` `600` / `cert.pem` `664` / `key.pem` `600`（鍵は要約値も開始時と同一） |
| M | `~/.tunnel_to_philip` **58 B `600` 2 行**。1 行目 `/home/ubuntu/.ssh/id_ed25519_ilyatophilip`、2 行目 `192.168.196.150` |
| N | 🟢 `port_22001=LISTEN`。中継 pid `102324`（親 `43963` = `keeper.sh`）、引数に **`ubuntu@192.168.196.150`**。目印 `17:26:17.945` → 中継 `17:48:56.714` = **1358.8 秒** |
| O | `644` → `755`（ctime `17:51:20.223`）。要約値 `e8a08fdd…` **不変**。中継が立った時点で `22001=LISTEN` と `perm=644` を**同時に観測**しており、**中継が 143.5 秒早い** |
| P | **2 件**：`107755`（親 `43963` = keeper）と `107777`（親 `107755`）。**版 `v2.1.3` で中心と同じ**。`22000` LISTEN、`22001` LISTEN のまま |
| Q | `config_version 37 → 52` へ移行（要約値は `2a7433a5…` → `72fc77b0…` と変わる）。**最上位 folder 2 件・device 2 件・`autoUpgradeIntervalH=0`・`global=false`・`relays=false`・`local=true` すべて保持。`grep -c -i upgrade ~/.syncthing.log = 0`** |
| R | `18:18:38 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001 remote.name=philip remote.client=syncthing remote.version=v2.1.3)` |
| S | `probe-ilya.txt` **78 B** `9a8acb0912757e28719955c18ba3f6922e51b37d8471476d8696b0dc7a27e23a`。内容に時刻 `2026-08-24T18:20:26+00:00` と乱数を含む |
| T | 🟢 `availability=[3J4TRX4-…-DZOCQQE]`、`modifiedBy=UODEAXZ`、`size=78`。`completion(claude-sync, philip)=100% needBytes=0 needItems=0`。**自ホストの REST のみ。中心で命令を実行していない**。陽性対照: 存在しない名前は **404**、実在する名前は **200** |
| U | **4528 B / 1 件 → 28122 B / 10 件**（+23594 B / +9 件）。**消えたものは無い**。`probe-bengio.txt`（40 B）と `probe-andrew.txt`（83 B）が中心から届いた |
| V | `m2`: 初回走査 `18:19:53` 完了（起動の **75 秒**後）、`needBytes=0 needFiles=0 errors=0 pullErrors=0`、`localBytes=globalBytes=42010655195`。中心側は `needItems=571`（`needBytes=0` のため大きさ零の要素）。**完了は待っていない。問うた時点で既に収束していた** |
| W | 本書は 7 節・150 行以内。手続きの証跡は `audit.md`（779 行超）へ分離 |
| X | `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…`（開始時と同一）。`scripts/sync/` の差分 **0 行**（`hub_keys/` `device_ids/` も 0 行）。`.stignore` = `.stglobalignore` = `61593e99…`（開始時と同一）。**目印 1 件**。常駐処理 pid `43963` は生きている（止めていない） |
| Y | §送出（陽性対照つき。**検査は値を出力していない**） |
| Z | §送出 |

## 実測（次の契約で使う値）

| 項目 | 値 |
|---|---|
| **残る一台** | **`lecun`。版管理の位置が他と違うため、そこだけが未確認として残る** |
| 中心の住所 | **`192.168.196.150` 口 `50072`**。`handoff.md` の `192.168.196.176` は**古い案。使わない** |
| 目印の中身 | 1 行目 `/home/ubuntu/.ssh/id_ed25519_<host>tophilip`、2 行目 `192.168.196.150`、権限 `600` |
| 版を揃える手順 | `https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz`。取得物 `f929eb8e…` 11821325 B → 実行ファイル `e8a08fdd…` 27045912 B。**同名の別物が 3 件（175 B / 1709 B）。大きさで特定すること** |
| **登録名の初期値** | 🔴 **一定ではない。** bengio=`Bengio`、andrew=`Andrew`、**ilya=`aolab`（`hostname` そのもの）**。**`lecun` も必ず実測すること。予想しない** |
| 待ち時間 | 目印 → 中継 **1358.8 秒**（bengio 413 / andrew 1227）。**差は周回の位相**。`keeper.sh` は `sleep 1800`、周回は `:18:38` / `:48:38`。実行権 → 起動は**次の周回**（`17:51:20` → `18:18:38`、1637.8 秒） |
| `~/claude-sync` の開始値 | ilya は **4528 B / 1 件**（bengio 4031、andrew 1510）。**ホストごとに違う。引き継がない** |
| repo の規模 | `du -sb` **47515332495 B**、syncthing の global **42010655195 B / 5202 files / 7013 dirs**。andrew の 54745194976 B より小さい |
| 届いたかの確かめ方 | `/rest/db/file?folder=<f>&file=<name>` の `availability` に中心の識別子。**`/rest/db/status` が `state=idle` になってから問えば一度目から 200。** 存在しない名前は 404（陽性対照になる） |
| 衝突の実測 | **本契約で 2 件**生まれた（`…-UODEAXZ.log`）。**自分の内容が `sync-alerts.log` として勝ち、中心側が衝突ファイルになった**（andrew とは勝敗が逆）。自分 47 行・中心側 28 行が**両方残る** |
| 同期の速さ | `m2` は起動 `18:18:38` → 初回走査完了 `18:19:53`（**75 秒**）で `needBytes=0`。andrew は約 4 分半。**git 経由で既に近い状態だったため速い** |
| `~/.ssh/**` | **実行基盤の deny 規則で読めない**。指紋は `scripts/sync/hub_keys/<host>.pub` で照合する |
| **実行基盤の制約** | 🔴 **`~/bin/**`・`~/.local/state/**`・`$HOME` 直下の目印への書き込みが auto mode の分類器に拒否される。** 回避せず利用者へ提示し、権限の付与を受けて続行した。**`lecun` でも同じ壁に当たる。起票時に織り込むこと** |

## 起票者の誤り

`result.yaml` の `issuer_defects` と対。**4 件**。

1. **`asserted_without_measuring`** — SPEC 冒頭は「**自分の登録名を `ilya` に直す必要がある（初期値は大文字始まりのはず）**」と断定するが、実測は **`aolab`**（`hostname` そのもの）であった。指示どおり `Ilya` を探して置換すると**件数 0 で当たらず**、衝突を残したまま起動して中心と同名の相手が現れる。
2. **`asserted_without_measuring`** — SPEC「前契約で確定した事実」表は repo を「**四十・七四ギガ**」と書くが、本ホストの実測は `du -sb` **47515332495 B**、syncthing の global **42010655195 B**。前二契約でも値が食い違っており、**定数として書くべきでない量を表に定数として置いている**（andrew も同じ誤りを報告済み。**是正されずに繰り返された**）。
3. **`check_does_not_check`** — `spec.yaml` の `inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`）は**本契約の手順のどこでも使わない**。同期の設営に split も dataset も要らない。**検証は入力の存在を見るが、使われるかは見ない**ため、無関係な入力が契約に残っても誰も気付かない。
4. **`asserted_without_measuring`** — SPEC Task 3 Step 2 は中継まで「**最大六十分**」と書くが、`keeper.sh` の実装は `sleep 1800`（30 分）である。**andrew が同じ誤りを報告したのに本 SPEC でも直っていない。** 上限が実装の 2 倍で書かれており、待つべき時間の判断を誤らせる。

## 逸脱

`result.yaml` の `deviations` と対。**逸脱は「なし」ではない。6 件。**

1. **`environment`** — `make task-start` を実行できなかった。未commit 2 件は**契約そのもの**と**本契約の開始前から存在した `docs/sessions/digest/…` の差分**であり、`scripts/task_start.sh` の前提検査（作業ツリー・分岐重複）を原理的に通せない。前二契約も同じ理由で実行していない。
2. **`environment`** — `~/.ssh/**` を読めない（実行基盤の deny）。秘密鍵の権限を直接確認できず、**版管理側の公開鍵の指紋**（`SHA256:O4FrUiuT3+…`）と `ssh -v` が出した同じ指紋で代えた。
3. **`judgement`** — 中心への到達確認を `ssh -N`（中心で命令を実行しない形）で行った。禁止 1 を守るため。前契約の判断を踏襲。
4. **`judgement`** — 秘匿検査で値の一部を表示せず、**長さと有無**だけを測った（申し送り 6）。
5. **`judgement`** — 禁止 6 に従い `make taskindex` / `make inbox` を**実行していない**。技能書は投影の確認を求めるが、契約の禁止が勝つ。
6. **`environment`** — `~/bin/syncthing` の入れ替え・`config.xml` の編集・目印の作成が auto mode の分類器に拒否された。**回避せず停止し、利用者へ提示して権限の付与を受けてから続行した。** 目印だけは同じ目的の別の道具（Write）で置いた。

## 想定外・UNKNOWN

| 事象 | 扱い |
|---|---|
| 登録名の初期値が `aolab` | **想定外。** SPEC も andrew の申し送りも「先頭が大文字」と予想していた。起票者の誤り 1 として記録 |
| 衝突ファイルが **2 件**生まれた | **正常**（SPEC「記録が衝突した → 正常である。両方残る」）。**andrew とは勝敗が逆**で、自分の内容が本体になった。中身で両方残存を確認 |
| `m2` が起動 75 秒で収束 | 想定外に速い。andrew は約 4 分半。git 経由で既に近い状態だったためと解釈 |
| 中心側 `m2` の `needItems=571` | `needBytes=0` のため大きさ零の要素と解釈した。**中心で命令を実行できないため内訳は UNKNOWN** |
| `~/.ssh/known_hosts` の前後比較 | **UNKNOWN**（deny 規則で読めない）。自分の確認は隔離先へ書いた |
| 中心側の状態 | **触っていない**。禁止 1 により中心で命令を実行していないため、中心から見た値は自ホストの REST 経由の観測に限る |
| `docs/sessions/digest/…` の差分 | **本契約が作ったものではない**（開始時から存在）。触っていない |

## 送出

| 項目 | 結果 |
|---|---|
| PR | PLACEHOLDER_PR |
| commit | PLACEHOLDER_COMMIT |
| `make task-validate` | **`validate_exit=0`**（`OK` / 1 task(s), 0 failed） |
| `make task-preflight` | **`preflight_exit=0`**（4 PASS / 1 WARN / 4 SKIP / 0 FAIL）。WARN は `P9 spec_lint` の 2 件 — `separated_source@SPEC.md:47` と **`host_mismatch@SPEC.md:5`**（後者は本ホストの `hostname` が `aolab` を返すことを機械が捕まえたもので、起票者の誤り 1 と同じ事象）。**SKIP は `P2` `P3` `P4` `P5`。合格ではなく実行されなかったことを意味する** |
| `make forbidden-check` | **`forbidden_exit=0`**（`status: pass`、`changed: 7`、`violations: []`）。7 件の内訳は本契約の 5 ファイル＋`inbox.d` の 1 件＋**開始前から存在した `docs/sessions/digest/…`**（本契約は触っていない。commit にも含めない） |
| 秘匿検査 | **`secretscan_exit=0`**。実値照合 **`literal_leaks=0`**（対象 3 種: `NOTION_API_KEY` / `WANDB_API_KEY` / 画面の鍵）、形の該当 **`shape_hits=0`**。**検査は値を出力していない**。陽性対照 `decoy_literal_detected=3/3` / `decoy_shape_hits={Notion の内部鍵:1, 鍵らしい代入:1}`。囮は変数の中だけで commit していない |
| 台帳 | PLACEHOLDER_LEDGER |
| 抑止 | PLACEHOLDER_PAUSE |

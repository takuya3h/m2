# audit — T-2026-09-20-philip-accept-dlsta

手続きの証跡。`RESULT.md` はここを行番号で指す。
実行ホスト: `.servername` = `philip`（`hostname` は `aolab`。philip と ilya が同じ値を返す）。
repo: `/home/ubuntu/slocal2/m2`、分岐: `feat/philip-accept-dlsta`（`origin/phase0` = `de3b2a6a` から作成）。

## 0. 前提の整備

| 項目 | 実測 |
|---|---|
| 抑止の目印 `.sync-pause` | 在り（2026-09-20 16:38 作成、`.gitignore:240` 該当） |
| 稼働中の `~/bin/m2-sync.sh` の対応 | `grep -c sync-pause` = **2**（抑止が効く） |
| 抑止の記録 | `~/claude-sync/sync-alerts.log` に `[efros] 一時停止中` 等。philip は 16:33 の `auto-merge skip` が最後 |
| 開始時の未追跡 | 4 件 |
| 退避したもの | `experiments/transfer/pd_refin_empty_seed42_tf32/`（212M）→ `/home/ubuntu/slocal2/.task-stash/T-2026-09-20-philip-accept-dlsta/` |
| 退避の理由 | `checkout` が `logs/eval_meta_val.json` `logs/val_metrics_by_epoch.json` の上書きを拒んだ |
| 退避先の選定 | repo と同一ファイルシステム（`/dev/sda`）。`/home/ubuntu` は overlay で跨ぐと実コピーになる |
| 分岐の既存 | local 0 件 / remote 0 件 → 新規作成した（切り直しではない） |

前契約 `T-2026-09-20-dlsta-join-foundation` は `origin/phase0` の先頭
（`de3b2a6a` Merge pull request #187 from takuya3h/feat/dlsta-join-foundation）に統合済み。

## 1. Phase A — 受け入れ一覧の測定

対象: `/home/ubuntu/.ssh/authorized_keys`（symlink ではない）

| 項目 | 実測 |
|---|---|
| 権限 | `600` ubuntu:ubuntu |
| 更新時刻 | 2026-09-17 05:05:45 +0000 |
| 大きさ | 1222 bytes |
| sha256 | `ab3fe1cbbb18534ee97d8816682f9b141b0df5fadd0475c3d0ee4ca9477986fb` |
| 行数（`wc -l`） | 6 |
| 空行を除いた件数（`grep -c '[^[:space:]]'`） | **6** |
| 末尾の改行 | **在り**（`tail -c 1` = `\n`）→ 追記で行が繋がる恐れはない |
| 解析できた件数（`ssh-keygen -lf`） | **6**（exit 0）＝ 空行を除いた件数と一致 |

### 登録されている鍵（指紋と註釈。本体は出さない）

| # | 指紋 | 註釈 | 型 |
|---|---|---|---|
| 1 | `SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU` | `dakyo-mba@dmba.local` | RSA 4096 |
| 2 | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0` | `andrewtophilip` | ED25519 |
| 3 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` | `bengiotophilip` | ED25519 |
| 4 | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` | ED25519 |
| 5 | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` | `lecuntophilip` | ED25519 |
| 6 | `SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0` | `efrostophilip` | ED25519 |

**六件**。SPEC の既存実測（人の端末 + lecun / bengio / andrew / ilya / efros）と一致。

## 2. Phase A — 同期処理の設定の測定

対象: `/home/ubuntu/.local/state/syncthing/config.xml`

| 項目 | 実測 |
|---|---|
| 権限 | `600` ubuntu:ubuntu |
| 更新時刻 | 2026-09-17 05:07:36 +0000 |
| 大きさ | 14929 bytes |
| sha256 | `6cfc3eceda61701a08b47bef9605d36d5ad547dce171f70efcbaacb62d60f7b0` |
| 版 | `syncthing v2.1.3 "Hafnium Hornet"` |

### 階層を見て数える（issuer_cautions #13）

`configuration` 直下の子要素: `folder` 2 / `device` 6 / `gui` 1 / `ldap` 1 / `options` 1 / `defaults` 1

| 数え方 | 件数 |
|---|---|
| **相手の実体**（`configuration` 直下の `device`） | **6** |
| ひな型（`defaults/device` の `id=""`） | 1（**実体に含めない。触らない**） |
| 共有フォルダ（`configuration` 直下の `folder`） | 2 |
| 参考: 階層を見ない数え方（`.//device`） | **20**（取り違えると 6 を 20 と読む） |

### 相手の実体

| 識別子（先頭 7） | 名前 | 住所 |
|---|---|---|
| `LW4CO4U` | efros | dynamic |
| `OOOTQMG` | lecun | dynamic |
| `UODEAXZ` | ilya | dynamic |
| `3C2LTP7` | andrew | dynamic |
| `3J4TRX4` | **philip（自分）** | dynamic |
| `4NIRI4M` | bengio | dynamic |

`GET /rest/system/status` の `myID` は `3J4TRX4...`。設定の `philip` と一致し、本ホストが中心であることが確定した。

### 共有フォルダの定義

| id | label | type | path | 共有相手 |
|---|---|---|---|---|
| `claude-sync` | claude-sync | `sendreceive` | `/home/ubuntu/claude-sync` | 6 |
| `m2` | m2 | `sendreceive` | `/home/ubuntu/slocal2/m2` | 6 |

### 稼働しているもの（issuer_cautions #6 / #3）

`/proc/PID/exe` を `realpath` して basename で絞り、自分の PID・祖先・子孫を除外して数えた。

| 対象 | 件数 |
|---|---|
| `syncthing` の実体プロセス | **2**（PID 122452 ← 親 72428 = `keeper.sh`、PID 122530 ← 親 122452） |

**両方向の対照**（1 周目で陽性対照が落ちた）:

| 対照 | 1 周目 | 2 周目 |
|---|---|---|
| 陽性 `python3` | **0 → 落ちた** | — |
| 陽性 `python3.12`（自分の exe の実体 basename） | — | **1**（期待どおり 1 以上） |
| 陰性 `zzz_no_such_binary` | 0 | 0 |
| 測定対象 `syncthing` | 2 | 2 |

1 周目の失敗の原因は、`realpath` 後の実体が `/usr/bin/python3.12` であり basename が `python3` と一致しなかったこと。
**片方向だけなら「常に 0 を返す壊れ方」に気付けなかった。**

### 待ち受け（`ss` が不在のため `/proc/net/tcp{,6}` を直接読んだ）

| ポート | 状態 |
|---|---|
| TCP 22000 | **LISTEN**（`/proc/net/tcp6`） |
| TCP 8384（画面） | LISTEN（`/proc/net/tcp`） |
| UDP 22000 / 21027 | 開いている |

### 接続（`GET /rest/system/connections`）

項目数 **5**、`connected=True` **5**、`paused=False` 5。

| 識別子（先頭 7） | connected | type |
|---|---|---|
| `3C2LTP7` (andrew) | True | tcp-server |
| `4NIRI4M` (bengio) | True | tcp-server |
| `LW4CO4U` (efros) | True | tcp-server |
| `OOOTQMG` (lecun) | True | tcp-server |
| `UODEAXZ` (ilya) | True | tcp-server |

**五ノードと接続している。** 一覧に自分は現れない。

## 3. Phase A — 控え

置き先: `/home/ubuntu/task-backups/T-2026-09-20-philip-accept-dlsta/`（repo の外、権限 700）

原本（`~/.ssh/`・`~/.local/state/`）と控え先はいずれも overlay（`/`）で**同一ファイルシステム**。

| 控え | sha256 | 原本と一致 | 権限 |
|---|---|---|---|
| `authorized_keys.orig` | `ab3fe1cb…86fb` | **一致** | 600 |
| `config.xml.orig` | `6cfc3ece…f7b0` | **一致** | 600 |
| `fingerprints.before.txt` | 追記前の指紋一覧 6 件（集合差の基準） | — | 644 |

**版管理へは置かない。** 画面の鍵（`gui/apikey`）が `config.xml` に含まれるため、伏せる工程を挟むより
版管理の外に留めるほうが誤りが少ない。置く前の検査として、両控えに秘密鍵の書き出し
（`BEGIN .*PRIVATE KEY`）が **0 件**であることを確かめた（形で判定し、値は出力していない）。

## 4. Phase A — 戻し方（記録のみ。実行していない）

受け入れ一覧を戻す:

    BK=/home/ubuntu/task-backups/T-2026-09-20-philip-accept-dlsta
    cp -p "$BK/authorized_keys.orig" ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    sha256sum ~/.ssh/authorized_keys   # ab3fe1cbbb18534ee97d8816682f9b141b0df5fadd0475c3d0ee4ca9477986fb と一致すること

同期処理の相手の登録を戻す（**稼働中のため画面の経路。直接編集は書き戻される**）:

    CFG=~/.local/state/syncthing/config.xml
    APIKEY=$(python3 -c "import xml.etree.ElementTree as ET,sys;print(ET.parse(sys.argv[1]).getroot().find('gui/apikey').text)" "$CFG")
    # 1) 共有フォルダ 2 件の相手の一覧から dlsta を外す（相手の一覧だけを PATCH。定義は送らない）
    #    PATCH /rest/config/folders/claude-sync  {"devices":[…dlsta を除いた 6 件…]}
    #    PATCH /rest/config/folders/m2           {"devices":[…dlsta を除いた 6 件…]}
    # 2) 相手の実体を外す
    #    DELETE /rest/config/devices/<dlsta の識別子>
    # 3) 確認: GET /rest/system/connections の項目数が 5 へ戻り、5 件すべて connected=True

**設定ファイルの直接復元は行わない。** 稼働中の処理が書き戻すため効かない（前契約で起動十二分後に
上書きされた実測がある）。控えの `config.xml.orig` は照合と最後の手段のために保持する。

権限はいずれも開始時の `600`。

## 5. Phase B — 追記するものの照合

### 提出物（版管理から読む。SPEC に値は転記されていない）

| 提出物 | バイト数 | 行数 | 末尾改行 | 版管理 |
|---|---|---|---|---|
| `scripts/sync/hub_keys/dlsta.pub` | 95 | 1 | 在り | 追跡済み（`ls-files --error-unmatch` exit 0） |
| `scripts/sync/device_ids/dlsta.txt` | 64 | 1 | 在り | 追跡済み |

### 前契約の報告との照合

| 項目 | 前契約 `T-2026-09-20-dlsta-join-foundation` の報告 | 本契約の実測 | 判定 |
|---|---|---|---|
| 鍵の指紋 | `SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4`（RESULT.md:33, :53） | `SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4`（`dlstatophilip`, ED25519 256） | **一致** |
| 識別子 | `BRPEYOX-…-ZS26PAI`（result.yaml:28） | 同一（63 文字） | **一致** |

提出物の入れ替わりは無い。

### 公開鍵だけであることの三検査と囮（陽性対照）

| 検査 | `dlsta.pub` | 囮 | 判定 |
|---|---|---|---|
| (a) 先頭が `ssh-` の行数 | **1**（期待 1） | 0 | 検査 a は囮を通さない |
| (b) 秘密鍵の書き出し `BEGIN .*PRIVATE KEY` | **0**（期待 0） | **1** | **検査 b は効いている** |
| (c) 行数 | **1**（期待 1） | 3 | **検査 c は効いている** |

囮は `…/scratchpad/decoy_not_a_key.txt`（repo の外）に置いた。
`git status` に `decoy` は **0 件**。**版管理へは入れていない。**
検査はいずれも件数だけを返し、鍵の本体を出力していない。

### 既に登録されていないか（陽性対照つき）

| 照合先 | 数え方 | dlsta | 陽性対照 | 陰性対照 |
|---|---|---|---|---|
| 受け入れ一覧 | `ssh-keygen -lf` で解析してから指紋を照合 | **0 件** | efros `SHA256:Ney1wai…qF0` → **1 件** | — |
| 設定の相手の実体（`configuration` 直下） | 階層を見て id を照合 | **0 件** | efros `LW4CO4U` → **1 件** | `ZZZZZZZ` → 0 件 |
| `folder claude-sync` の相手 | 階層を見て id を照合 | **0 件** | — | — |
| `folder m2` の相手 | 階層を見て id を照合 | **0 件** | — | — |

**どちらにも未登録。** 追記と登録を行う。

## 6. Phase C / Task 3 — 受け入れ一覧への追記

### 一度目: 実行基盤が拒否した

auto mode の分類器が `Unauthorized Persistence` を理由に追記命令を拒否し、**命令は実行されなかった。**
直後に測り、sha256 が開始時と同一・件数 6 のままであることを確かめた。**中途半端に書けてはいない。**

SPEC の想定外表「実行基盤が拒むことがある」に該当したため、**停止して利用者へ諮った。**
利用者は自分の手で追記する経路を選び、実行した。**実行者が迂回したのではない。**

### 二度目: 利用者が実行した後の検証

追記は `cat scripts/sync/hub_keys/dlsta.pub >> ~/.ssh/authorized_keys` の一行。
開始時に末尾改行が在ることを測ってあったため、**改行の追加は行っていない**（行の連結は起きない）。

| 項目 | 開始時 | 追記後 | 判定 |
|---|---|---|---|
| 権限 | `600` | **`600`** | **同じ** |
| sha256 | `ab3fe1cb…86fb` | `d1bc4263…e71a` | 追記のぶん変わった |
| 行数（`wc -l`） | 6 | **7** | — |
| 空行を除いた件数 | 6 | **7** | 期待どおり |
| 解析できた件数（`ssh-keygen -lf`） | 6 | **7** | **空行を除いた件数と一致** |
| 末尾の改行 | 在り | **在り** | — |

### 集合差（両方向。件数の一致では足りない）

`fingerprints.before.txt` と `fingerprints.after.txt` を `comm` で突き合わせた。

| 差 | 実測 | 期待 | 判定 |
|---|---|---|---|
| **消えた行** | **0 件** | 空 | **既存を一件も失っていない** |
| 増えた行 | **1 件** `SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4 dlstatophilip` | 1 件 | — |

増えた一件の指紋は Task 2 で前契約の報告と照合した値と**一致**した。

**集合差の道具の陽性対照**（注意 3。道具が「常に 0 を返す壊れ方」でないこと）:

| 対照 | 実測 | 期待 |
|---|---|---|
| 囮 1 行と追記後の差 | **1** | 1 以上 |
| 追記後と自分自身の差 | **0** | 0 |

## 7. Phase C / Task 4 — 同期処理への登録（**完了**）

### 実在する属性名を読んでから送った（推測していない）

`GET /rest/config/devices` と `GET /rest/config/folders/m2` のキーを先に読んだ。

| 対象 | SPEC の指定 | 稼働中の REST v2.1.3 の実在名 | 採用 |
|---|---|---|---|
| 相手の実体 | `deviceID` | `deviceID` | `deviceID` |
| 共有フォルダの相手 | **`id`（`deviceID` ではない）** | **`deviceID`**（キーは `deviceID` / `introducedBy` / `encryptionPassword`） | **`deviceID`** |

**SPEC の指定は誤り。** `id` は `config.xml` 側の属性名（`<folder><device id="…"/>`）であり、
REST の JSON 表現では `deviceID` である。SPEC は二つの表現を取り違えている。
想定外表「属性名が想定と違う → 実在する名前を読んで使う。推測しない」に従った。

### 送った命令

| 命令 | 送った中身 | HTTP |
|---|---|---|
| `POST /rest/config/devices` | `deviceID` = `BRPEYOX-…-ZS26PAI`、`name` = `dlsta`、`addresses` = `["dynamic"]` | **200** |
| `PATCH /rest/config/folders/claude-sync` | **`devices` キーのみ**（既存 6 件 + dlsta = 7 件） | **200** |
| `PATCH /rest/config/folders/m2` | **`devices` キーのみ**（既存 6 件 + dlsta = 7 件） | **200** |

**定義（`id` / `label` / `path` / `type`）は送っていない**（禁止 4）。**再起動していない**（禁止 2）。

### 書式と定義（階層を見て数えた）

| 項目 | 開始時 | 登録後 | 判定 |
|---|---|---|---|
| 解析 | 成功 | **成功** | — |
| 相手の実体（`configuration` 直下の `device`） | 6 | **7** | 期待どおり |
| 共有フォルダ（`configuration` 直下の `folder`） | 2 | **2** | 不変 |
| `claude-sync` の相手 | 6 | **7** | — |
| `m2` の相手 | 6 | **7** | — |
| 権限 | `600` ubuntu:ubuntu | **`600` ubuntu:ubuntu** | **保たれている** |
| 大きさ | 14929 bytes | 15832 bytes | 追記のぶん増えた |

### 既存が無傷であること（控えとの集合差）

| 照合 | 実測 | 期待 |
|---|---|---|
| フォルダ id 集合 | 前 `['claude-sync','m2']` = 後 `['claude-sync','m2']` | 一致 |
| `claude-sync` の定義属性の差分 | **なし** | なし |
| `m2` の定義属性の差分 | **なし** | なし |
| **消えた相手** | **空** | **空** |
| 増えた相手 | **1 件** `BRPEYOX` name=`dlsta` addresses=`['dynamic']` | 1 件 |
| 既存の相手の定義が変わったもの | **空** | 空 |

### 反映の確認（`GET /rest/system/connections`）

| 項目 | 開始時 | 登録後 |
|---|---|---|
| 項目数 | 5 | **6** |
| `connected=True` の件数 | 5 | **5** |

| 識別子（先頭 7） | 名前 | connected | paused | type |
|---|---|---|---|---|
| `3C2LTP7` | andrew | True | False | tcp-server |
| `4NIRI4M` | bengio | True | False | tcp-server |
| `LW4CO4U` | efros | True | False | tcp-server |
| `OOOTQMG` | lecun | True | False | tcp-server |
| `UODEAXZ` | ilya | True | False | tcp-server |
| **`BRPEYOX`** | **dlsta** | **False** | **False** | `''` |

**同期処理は新しい相手を認識した。** 接続の一覧に項目ができたことがその証拠である
（設定を読んだだけでは項目はできない）。`connected=False` は異常ではない。中心は住所 `dynamic`
で相手へ繋ぎに行かず、dlsta の側はまだ中心を登録していないため、繋がる条件が揃っていない。

**五ノードとの接続は切れていない**（5 件すべて `connected=True`）。

### 稼働しているものと待ち受け

| 項目 | 開始時 | 登録後 |
|---|---|---|
| `syncthing` 実体プロセス（`/proc/PID/exe`、自分と祖先・子孫を除く） | 2 | **2** |
| TCP 22000 | LISTEN | **LISTEN** |
| TCP 8384 | LISTEN | LISTEN |

再起動は起きていない。

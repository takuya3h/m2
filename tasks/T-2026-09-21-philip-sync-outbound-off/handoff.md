# handoff — 残る六台で同じことをする手順

対象: `lecun` `bengio` `andrew` `ilya` `efros` `dlsta`。中心 `philip` は本契約で実施済み。
**時刻は JST**（`~/.syncthing.log` の原文だけ UTC。JST = UTC + 9 時間）。
**中心で確定した手順をそのまま広げる。** 推測で足さない。

## 0. 前提（中心で実測した事実）

| 事実 | 値 | 出所 |
|---|---|---|
| 版 | **六台とも `v2.1.3`**（中心と同じ） | 中心の `GET /rest/system/connections` の `clientVersion` |
| 設定の位置 | `~/.local/state/syncthing/config.xml` | 中心の実測と各ノードの過去契約の記録 |
| 画面の経路の待ち受け | `127.0.0.1:8384`（`<gui><address>`） | 中心の実測。bengio の過去契約にも同じ記載 |
| 再起動 | **不要**（対象のどの項目にも `restart:"true"` が無い） | 実体の型情報 |

**版が六台とも中心と同じなので、設定の名前も判定も中心と同一である。**
**版が違う台が出たら、その台では設定名を読み直すこと。**

## 1. 変える項目

| 項目 | 変更後 | 何が止まるか |
|---|---|---|
| `natEnabled` | `false` | **STUN**（公開の中継補助への問い合わせ）。UPnP/NAT-PMP の探索も名目上は同じ項目 |
| `urAccepted` | `-1` | 使用状況の日次送信（`https://data.syncthing.net/newdata`） |
| `crashReportingEnabled` | `false` | 障害報告（`https://crash.syncthing.net/newcrash`） |

**触らない項目**:

- `localAnnounceEnabled`（局所の告知。外向きではない。旧構成でも有効）
- `globalAnnounceEnabled` / `relaysEnabled`（既に `false` の見込みだが**確かめるだけ**）
- `autoUpgradeIntervalH`（`0` なら既に無効。`0` でなければ `0` にする）
- 相手の登録・共有フォルダの定義・鍵・受け入れ一覧

**`urAccepted` は台ごとに値が違いうる。** 中心では `0` から `3` へ**誰が変えたか分からないまま**
変わっていた（`audit.md` 3.2）。**必ず先に読んでから書く。** `0` のままの台は `-1` にしておくと、
今後うっかり有効になっても送らない。

## 2. 経路（画面の経路。設定ファイルの直接編集は効かない）

**稼働中の処理が書き戻すため、`config.xml` を直接書いても消える。** 画面の経路を使う。

鍵は `<gui><apikey>` にある。**値は変数へ読み込むだけで、出力にも記録にも残さない。**

    # 読む（変更前の控えを repo の外へ取る）
    GET  /rest/config/options            → 全 55 項目。before として保存
    GET  /rest/system/status             → myID / connectionServiceStatus
    GET  /rest/system/connections        → 接続の件数

    # 変える（**変える鍵だけを送る。他の鍵を送らない**）
    PATCH /rest/config/options  {"natEnabled": false}
    PATCH /rest/config/options  {"urAccepted": -1}
    PATCH /rest/config/options  {"crashReportingEnabled": false}

`PATCH` は与えた鍵だけを変える。**`PUT /rest/config` で全体を送らないこと。**
全体を送ると、意図しない項目まで書き換わる。

## 3. 確かめ方

| # | 確かめること | 期待 |
|---|---|---|
| 1 | `GET /rest/config/options` を変更前と全項目で比較 | **差は 3 項目だけ** |
| 2 | `config.xml` の該当要素 | 3 項目が新しい値。`localAnnounceEnabled` は `true` のまま |
| 3 | `GET /rest/config/restart-required` | `{"requiresRestart": false}` |
| 4 | `GET /rest/system/connections` | **接続の件数が変更前と同じ** |
| 5 | `GET /rest/config/devices` / `/rest/config/folders` | 件数と中身が変更前と同一 |
| 6 | 同期処理の件数と PID | **変更前と同じ**（`/proc/PID/exe` の実体で絞る。部分一致は使わない） |

### 3.1 STUN は記録で確かめられる（遷移が残る）

**中心で実測した**（`audit.md` 7.3 / 8.6）。

同期処理は STUN が無効になった瞬間に、通常の水準で次の行を出す。

    2026-09-22 09:06:09 INF STUN disabled (log.pkg=stun)     # 記録は UTC。JST では 18:06:09

**この行が出れば止まっている。** 不在ではなく遷移そのものの記録なので、陽性対照が要らない。

    # 変更の前後で件数を数える（終了コードを件数と呼ばない）
    grep -c 'STUN disabled' ~/.syncthing.log

**出るまでに待つ。** 中心では設定変更から **169 秒**かかった。
keepalive の待ち（`stunKeepaliveStartS = 180` 秒）が明けた最初の周回で止まるためである。
**300 秒待って出なければ、止まっていない。** そのときは報告して判断を仰ぐ。

**逆に、keepalive そのものは詳細記録の水準でしか出ない。**
`Resolved external address` は外側の住所が変わったときだけで、中心では 29 日間に 1 件（起動時）だった。
**「新しい行が無い」ことを根拠にしないこと。** 根拠は `STUN disabled` が出たことである。

測れないものも書いておく。容器の中に `tcpdump` / `ss` / `lsof` / `conntrack` は無く、
`/proc/net/nf_conntrack` も無い。`v2.1.3` に `/rest/system/debug` は無い（404）。
`STTRACE` は再起動が要るので使えない。**通信そのものは観測できない。**

### 3.2 使用状況の送信は翌日まで確かめられない

**日次**である。中心では **02:32 JST 前後**（記録の原文では 17:32 UTC）に送っていた（2 日連続で実測）。
**その台の直近の送信時刻を記録から読み、翌日の同時刻を過ぎてから**次を確かめる。

    grep -c 'Sent usage report' ~/.syncthing.log     # 件数
    grep  'Sent usage report' ~/.syncthing.log | tail -3   # 時刻

**変更した日の翌日に、新しい行が増えていなければ止まっている。**
これは周期的な通信なので、陽性対照が働く。**STUN とは扱いを分けること。**

## 4. 台による違い

| 観点 | 中心 `philip` | 残る六台 |
|---|---|---|
| 接続の向き | **受ける側**。6 件すべて `tcp-server`、相手側住所は `127.0.0.1:<高位番号>` | **出す側**。中心の loopback へ ssh の折り返しで届く |
| 変える項目 | 同じ 3 項目 | **同じ 3 項目。差は無い** |
| 設定の位置 | `~/.local/state/syncthing/config.xml` | **同じ** |
| 画面の経路 | `127.0.0.1:8384` | **同じ見込み。各台で `<gui><address>` を読んでから使う** |
| repo の位置 | `~/slocal2/m2` | `lecun` は `~/slocal/m2`、`dlsta` は `~/local/m2`、他は `~/slocal2/m2` |
| 版 | `v2.1.3` | **六台とも `v2.1.3`**（中心から実測） |

**中継の出口を使う台と中心で、変える項目に違いは無い。**
星型の中継は **ssh の折り返し**であって、同期処理の公開中継（`relaysEnabled`）ではない。
`relaysEnabled` は既に `false` であり、**今回の 3 項目とは独立である。**

**repo の位置の違いは同期処理の設定とは無関係**（設定は `$HOME` の下で共通）。
ただし `.sync-pause` を置く先は**その台の repo の直下**である。位置を取り違えないこと
（解決の順序は `~/slocal2` → `~/slocal` → `~/local`。`T-2026-09-21-m2dir-local`）。

## 5. 戻し方

    PATCH /rest/config/options  {"natEnabled": true}
    PATCH /rest/config/options  {"urAccepted": <変更前の値>}
    PATCH /rest/config/options  {"crashReportingEnabled": true}

**変更前の値を控えてから変えること。** 中心の控えは
`/home/ubuntu/task-backups/T-2026-09-21-philip-sync-outbound-off/before.json`（**版管理の外**）。

## 6. やってはいけないこと

1. 同期処理を停止・再起動する（反映に再起動は要らない。求められたら止めて判断を仰ぐ）
2. 相手の登録と共有フォルダの定義を変える
3. 局所の告知を無効にする
4. `PUT /rest/config` で設定全体を送る
5. `config.xml` を直接編集する（稼働中は書き戻されて消える）
6. 画面の鍵を出力・記録する
7. 使用状況の送信と障害報告を「止まった」と書く（3.2。翌日まで確かめられない／痕跡が元から無い）

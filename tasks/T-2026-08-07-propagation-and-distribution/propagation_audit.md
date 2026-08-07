# 全ホスト伝播状況の実測（2026-08-07）

実測ホスト: `ilya`（`hostname` は `aolab`、IP `172.17.0.14`）
実測時刻: 2026-08-07 14:30 UTC 前後
**このフェーズは読み取り専用。他ホストへは一切書き込んでいない。**

## 到達状況

| host | repo | branch | head | tasks | context/auto | conventions | .claude skill | .codex skill | behind |
|---|---|---|---|---|---|---|---|---|---|
| lecun | UNREACHABLE | - | - | - | - | - | - | - | - |
| philip | UNREACHABLE | - | - | - | - | - | - | - | - |
| ilya | UNREACHABLE | - | - | - | - | - | - | - | - |
| bengio | UNREACHABLE | - | - | - | - | - | - | - | - |
| andrew | UNREACHABLE | - | - | - | - | - | - | - | - |
| he | UNREACHABLE | - | - | - | - | - | - | - | - |
| adam | UNREACHABLE | - | - | - | - | - | - | - | - |
| hinton | UNREACHABLE | - | - | - | - | - | - | - | - |
| ian | UNREACHABLE | - | - | - | - | - | - | - | - |
| dlsta | UNREACHABLE | - | - | - | - | - | - | - | - |
| efros | UNREACHABLE | - | - | - | - | - | - | - | - |

**11 ホスト全てが到達不能であった。これは伝播の欠落ではなく、実測ホストからの到達性の欠落である。**
原因は 2 種類あり、いずれも実測で切り分けた。

| 原因 | 対象 | 実測した証拠 |
|---|---|---|
| LAN への経路が無い | `philip` | `ssh: connect to host 192.168.196.150 port 50072: No route to host`（2 回再現）。実測ホストは `172.17.0.14`（Docker bridge、default gw `172.17.0.1`）であり `192.168.196.0/24` への経路を持たない |
| ホスト名を解決できない | 上記以外の 10 ホスト | `ssh: Could not resolve hostname lecun: Name or service not known`。`~/.ssh/config` に定義があるのは `philip` と `github.com` のみ。`/etc/hosts` のカスタムエントリは `172.17.0.14 aolab` の 1 行のみ |

`~/.ssh/known_hosts` には 6 エントリあるが全てハッシュ化されており、ホスト名は復元できない。

### 実測ホスト自身の状態

`ssh` を経由しない直接観測。表の `ilya` 行が `UNREACHABLE` なのは自分自身へ ssh できないためであり、
実体は次のとおり**全て揃っている**。

| 項目 | 実測 |
|---|---|
| repo | `/home/ubuntu/slocal2/m2` |
| branch | `feat/propagation-and-distribution` |
| head | `acad9e4` |
| local `phase0` | `acad9e4` |
| `origin/phase0` | `acad9e4` |
| behind | **0** |
| tasks | `T-` で始まる契約ディレクトリが 6 件 |
| context/auto | 4 ファイル |
| conventions | あり |
| .claude skill | あり |
| .codex skill | あり（symlink） |

## keeper の実体

**特定できた。`UNKNOWN` ではない。**

| 項目 | 実測 |
|---|---|
| 実体 | `~/bin/keeper.sh`（`scripts/sync/keeper.sh` を git オブジェクトから展開したもの） |
| 稼働状況 | **稼働中。** PID 73082、`/bin/bash /home/ubuntu/bin/keeper.sh`、起動は 7月04 |
| 起動方式 | cron でも systemd でもない。`.zshrc` から `nohup` で起動する常駐ループ。多重起動は `flock`（`~/.keeper.lock`）で防ぐ |
| 周期 | ループ末尾の `sleep 1800`。すなわち 30 分 |
| crontab | 該当エントリなし |
| systemd user timer | 利用不可（コンテナに dbus が無く `systemctl --user` が接続できない）。`~/.config/systemd/user` も存在しない |

keeper が周回ごとに行うこと（`~/bin/keeper.sh` の実装から）。

1. `~/.tunnel_to_philip` があれば philip への SSH トンネル（`-L 22001:127.0.0.1:22000`）を維持する
2. `~/bin/syncthing` があり未稼働なら起動する
3. `~/bin/m2-sync.sh` を `origin/phase0` の最新版へ自己更新する
4. `.stignore` を `origin/phase0:.stglobalignore` から自動反映する
5. `~/bin/m2-sync.sh` を実行する

### 実測ホストでの keeper 各部の状態

| 部品 | 実測 |
|---|---|
| keeper 本体 | 稼働中（PID 73082） |
| syncthing | 稼働中（プロセス 2 個。PID 71159 と 1700503） |
| philip への SSH トンネル | **未稼働。** `pgrep -c -x ssh` が **0**、`22001` は listen していない。`~/.tunnel_to_philip` は存在するため設定上はトンネル元だが、LAN への経路が無いため確立できていない |
| m2-sync の実行実績 | **稼働中。** `~/claude-sync/sync-alerts.log` の最終行が `2026-08-07 14:25:16 [ilya] auto-merge skip: 追跡変更 1 件 (behind 1)`。30 分間隔で継続記録されている |

> 補足: 調査の途中で `pgrep -af 'ssh.*-L 22001'` を使ったところ「トンネル稼働中」と誤判定した。
> `pgrep -f` が**検査コマンド自身のコマンドライン**にマッチしたための偽陽性である。
> `pgrep -c -x ssh` で数え直して 0 であることを確定した。

## 伝播の経路（実測から確定したこと）

git 追跡物の伝播は **LAN の ssh ではなく GitHub 経由**である。実測ホストからの
`git fetch origin` は成功し（`8fcbe69..acad9e4` を取得）、`origin/phase0` に追従できている。
LAN への経路が無くても伝播は成立する。

Syncthing の星型トポロジ（各ノード → philip、`keeper.sh` の記述より「コンテナ間は SSH(50072)
しか通らないため」）は **git 追跡外の実験証跡**を配るためのものであり、契約や規約の伝播経路
ではない。実測ホストではこのトンネルが確立できていないため、**Syncthing 経由の同期は
現在このホストでは機能していない可能性が高い**が、git 追跡物には影響しない。

## 追跡と同期の設定

| 項目 | 実測 |
|---|---|
| `.claude/` `.codex/` の git 追跡ファイル数 | **22**（`.codex/skills/task` を含む） |
| `.codex/skills/task` | git 上は symlink（mode `120000`）として追跡されている |
| `.stglobalignore:27` | `.claude` を Syncthing の同期対象から除外している |
| `.codex` の Syncthing 除外 | **指定なし**（`.claude` とは非対称） |
| gitignore されているもの | `.claude/hooks/auto_notion_sync.log` のみ |

`.claude` は Syncthing から除外されているが git が運ぶため、伝播には影響しない。

## 欠落と原因

**git 追跡物の伝播そのものに欠落は確認されていない。ただし「確認できていない」のであって
「欠落が無い」と実証できたわけではない。** 実測ホストから他 10 ホストへ到達できないため、
他ホストの状態は本監査では **UNKNOWN** である。

一方、実測ホストで確定した問題が 1 件ある。

| # | 事象 | 実測 | 影響 |
|---|---|---|---|
| 1 | auto-merge が継続的にスキップされている | `sync-alerts.log` が 30 分ごとに `auto-merge skip: 追跡変更 1 件 (behind 1)` を記録。原因は未 commit の追跡変更 `tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md`（4 行の行末空白除去のみ） | 現時点では `behind 0` であり実害は出ていないが、**この 1 件が残る限り auto-merge は永久にスキップされ続ける**。今後 phase0 が進んだときに自動追従できない |

この未 commit 変更は本 task の作業開始前から存在しており、本 task では触れていない
（禁止事項ではないが、本 task の変更対象ではないため）。処理は別 task の対象とする。

---

## 再監査（2026-08-08）

実施 task: `T-2026-08-08-stdin-intake-and-anchor-cleanup`（Phase C）
実測ホスト: `ilya`（`hostname` は `aolab`、IP `172.17.0.14`）
**このフェーズも読み取り専用。他ホストへは一切書き込んでいない。**

### 到達手段の実測

| 項目 | 実測 |
|---|---|
| `~/.ssh/config` の定義 | `philip` と `github.com` の 2 件のみ |
| `ProxyJump` / `ProxyCommand` | **いずれも定義なし**（迂回経路が存在しない） |
| 名前解決（`getent hosts`） | 11 ホスト全て NG |
| 経路 | 自ホスト `172.17.0.14`、default gw `172.17.0.1`（Docker bridge） |

### 到達できたホスト

**0 台。** 前回（2026-08-07）と同じ結果である。

### 到達できなかったホスト

| ホスト | 実測した理由 |
|---|---|
| `philip` | `ssh: connect to host 192.168.196.150 port 50072: No route to host` |
| 他 10 ホスト（`lecun` `ilya` `bengio` `andrew` `he` `adam` `hinton` `ian` `dlsta` `efros`） | `ssh: Could not resolve hostname <host>: Name or service not known` |

**到達できないことは伝播の欠落を意味しない。** 実測ホストの
ネットワーク位置（Docker bridge 上）から他ホストへの経路と名前解決が無い、という
実測ホスト側の制約である。他ホストの状態は依然として **UNKNOWN** である。

### 実測ホスト側の keeper の現況

| 部品 | 実測 |
|---|---|
| keeper 本体 | 稼働中。**1 プロセス**（PID 73082、起動は 7月04） |
| syncthing | 稼働中（2 プロセス） |
| philip への SSH トンネル | **未稼働**（`ps` で `ssh -N -L 22001` に該当なし） |
| `origin/phase0` への追従 | behind 0 |

> 前回の監査では `pgrep -af 'ssh.*-L 22001'` が検査コマンド自身に一致する偽陽性を起こした。
> 今回は keeper の計数でも `pgrep -c -f 'bin/keeper.sh'` が同じ理由で 3 を返したため、
> `ps -eo args` と文字クラスによる自己除外で数え直して 1 と確定した。
> **検査コマンド自身が検査対象に混入する誤りは繰り返し起きる。**

### 前回の申し送りの解決を確認

前回の監査は「auto-merge が 30 分ごとにスキップされ続けている」と記録し、
原因を未 commit の追跡変更 1 件（`tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md` の
行末空白除去）と特定していた。`T-2026-08-08-regex-audit-and-cleanup` でこれを破棄し、
未追跡の smoke ディレクトリ 3 件を無視設定へ入れた結果、**auto-merge は実際に動いた**。

    2026-08-07 14:25:16 [ilya] auto-merge skip: 追跡変更 1 件 (behind 1)
    2026-08-07 17:55:45 [ilya] auto-merge: feat/regex-audit-and-cleanup <- origin/phase0 (1 commits)
    2026-08-07 17:55:48 [ilya] auto-push: feat/regex-audit-and-cleanup (1 commits)

前回「次の 30 分周期を待つ必要がある」として未検証にしていた項目は、これで実測により解決した。

### 結論

到達範囲は前回から広がっていない。**到達できた 0 台 / 到達できなかった 11 台**であり、
他ホストの伝播状況は引き続き **UNKNOWN** である。監査を完遂するには、LAN に到達できる
ホスト（`philip` など）から同じ手順を回す必要がある。

実測ホスト自身については、git 追跡物の伝播（GitHub 経由）と keeper の自動追従が
**動いていることを確認できた**。これは 1 台分の実測であり、全台の実測ではない。

---

## 実行ホストと到達不能の原因（2026-08-08 追記）

これまでの契約はすべて同一ホストの同一コンテナ内で実行されている。
到達不能はコンテナから外部ネットワークへ出られない構成に起因し、
**他ホストの伝播状況を否定するものではない。**

実測ホストを別のサーバへ変えても、同じコンテナ構成であれば結果は変わらない。
監査を前進させるには、コンテナの外から実行する必要がある。

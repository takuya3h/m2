# audit — T-2026-09-21-fleet-sync-outbound-off

時刻は JST。実行ホストは中心 `philip`（OS 名 `aolab`）。

## 0. 開始

| 項目 | 値 |
|---|---|
| 開始前の未追跡 | 3 件（`docs/sessions/digest/` の 3 ファイル） |
| 退避先 | `/home/ubuntu/slocal2/task-backups/20261007-142605-fleet-digest/`（repo と同じ `/dev/sda`） |
| 退避後の未追跡 | 0 件 |
| `.sync-pause` | 手で置かず、`task_start.sh` が作成（`created_pause=1`）。SPEC 0 節の手動 `touch` は採らなかった |
| `make task-start` | exit 0。分岐 `feat/fleet-sync-outbound-off`（起点 `origin/phase0`） |
| `make task-validate` | exit 0。WARN `[L2-6]` conventions.md が c801e17 以降に変更（4 commit、+38/-0） |
| WARN の差分 | 変更履歴 2 行・`proposal_gate` に「置き場と参照」（exp のみ）・`det_groups`・`crossfit` 新節。注入対象の `prohibitions` と `issuer_cautions` は無変更。利用者の承認を得て続行 |
| `make task-preflight` | exit 0。5 PASS / 1 WARN / 8 SKIP / 0 FAIL |
| P9 spec_lint | `separated_source@SPEC.md:37`、`host_mismatch@SPEC.md:5`（前契約の followups と同じ誤検知の型） |
| SKIP | P2 P3 P4 P5 P11 P12 P13 P14 |

## 1. 認証に使われた鍵（Task 1 Step 1）

### 1.1 中心の設定（読み取りのみ）

- `~/.ssh/config` は `Include ~/.ssh/config.d/*.conf`。
- `~/.ssh/config.d/aolabnet.conf` の六台の別名は、住所・口が SPEC の表と一致。六台とも
  `User ubuntu` / `Port 50072` / `IdentityFile ~/.ssh/id_ed25519_aolab` / `IdentitiesOnly yes`。
- 手元の公開鍵の指紋（`ssh-keygen -lf *.pub`。秘密鍵は読んでいない）:
  - `id_ed25519_aolab.pub`: `SHA256:6NnjKh1smLfcXIttfc13hhMZNludreWCkWuWcQa04H0` (ED25519)
  - `id_ed25519_github.pub`: `SHA256:3RIB+045Y0Ey2kTeG4dDGq6uTNEAbo5C0ZjhbxHHFkA` (ED25519)

### 1.2 転送の受け口

- `SSH_AUTH_SOCK` は設定あり（VS Code の転送ソケット `/tmp/vscode-ssh-auth-sock-*`）。
- 指す先 `/tmp/ssh-SkuXBhPaYa/agent.2459052` は**存在しない**。`ssh-add -l` は
  `Error connecting to agent: No such file or directory`。転送された鍵は現在使えない。

### 1.3 実測（lecun、利用者が `!` で実行）

実行基盤（auto mode）が実行者からの接続を「資格情報の探索」として拒んだ。迂回せず、
利用者へ提示して利用者自身が実行した。

    env -u SSH_AUTH_SOCK ssh -v -o BatchMode=yes -o IdentityAgent=none -o ForwardAgent=no \
      -o PreferredAuthentications=publickey -o StrictHostKeyChecking=yes -o UpdateHostKeys=no \
      -o ConnectTimeout=10 lecun true

    Offering public key: /home/ubuntu/.ssh/id_ed25519_aolab ED25519 SHA256:6NnjKh1smLfcXIttfc13hhMZNludreWCkWuWcQa04H0 explicit
    Server accepts key: /home/ubuntu/.ssh/id_ed25519_aolab ED25519 SHA256:6NnjKh1smLfcXIttfc13hhMZNludreWCkWuWcQa04H0 explicit
    Authenticated to 192.168.196.176 ([192.168.196.176]:50072) using "publickey".
    ssh_exit=0

- **判定: 中心の手元の鍵（`id_ed25519_aolab`）。転送に依存しない。**
  agent を経路ごと断った（`SSH_AUTH_SOCK` 除去 + `IdentityAgent=none`）うえで成功した。
- `known_hosts` の sha256 は前後で同一（`64ce877d…a5edac`）。書き込みは起きていない。
- 1 回目の試行（隔離した写しを `UserKnownHostsFile` に指定）は、写しの作成が拒否された
  命令に含まれていたため写しが無く、出力 0 行で終わった（認証へ到達していない）。

## 2. 手順書（Task 1 Step 2。前契約 `handoff.md` より）

| 項目 | 変更後 | 経路 |
|---|---|---|
| `natEnabled` | `false` | `PATCH /rest/config/options`（変える鍵だけを送る。`PUT /rest/config` は使わない） |
| `urAccepted` | `-1` | 同上。**先に読んでから書く** |
| `crashReportingEnabled` | `false` | 同上 |

- 確かめるだけ: `globalAnnounceEnabled` / `relaysEnabled`（`false` の見込み）、`autoUpgradeIntervalH`（`0` なら何もしない）。
- 触らない: `localAnnounceEnabled`、相手の登録、共有フォルダ、鍵、受け入れ一覧。
- `config.xml` の直接編集は効かない（稼働中の処理が書き戻す）。再起動は不要（`restart:"true"` の項目が無い）。
- 確かめ方: 読み戻し（`GET /rest/config/options`）と `config.xml` の両方。接続・登録・共有・局所告知・処理の識別子が無傷。

## 3. 六台の現状（Task 1 Step 3。読み取りのみ）

### 3.1 遠隔のシェルと処理（実行者が実行、2026-10-07 JST）

| ノード | `$SHELL` | `hostname` | syncthing の処理 | config.xml |
|---|---|---|---|---|
| lecun | /usr/bin/zsh | lecun | 140103 / 140120 | 17858 B |
| bengio | /usr/bin/zsh | Bengio | 332564 / 332580 | 17851 B |
| andrew | /usr/bin/zsh | Andrew | 89005 / 89026 | 17852 B |
| ilya | /usr/bin/zsh | **aolab** | 107755 / 107777 | 17850 B |
| efros | /usr/bin/zsh | efros | 73191 / 815391 | 17853 B |
| dlsta | /usr/bin/zsh | **4f3861ae8d3b** | 61631 / 61670 | 17848 B |

- 六台とも `curl` と `python3` が在る。ilya と dlsta は OS 名が別名と違う（住所は SPEC の表と一致）。
- `known_hosts` の sha256 は前後で同一（`64ce877d…`）。

### 3.2 現在値・版・接続（利用者が `!` で実行）

画面の鍵を読む命令は実行基盤が「資格情報の探索」として拒んだ。迂回せず、利用者が実行した。
スクリプトは各ノードの中で `config.xml` の `<gui><apikey>` を変数に読むだけで、出力に含めない。
全 55 項目の控えは repo の外 `/home/ubuntu/slocal2/task-backups/20261007-fleet-before/<host>.json`。

| ノード | 版 | 項目数 | natEnabled | urAccepted | crashReportingEnabled | localAnnounce | globalAnnounce | relays | autoUpgradeIntervalH | 中心と接続 | 登録 | 共有 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| philip（中心） | v2.1.3 | 55 | false | -1 | false | true | false | false | 0 | — | — | — |
| lecun | v2.1.3 | 55 | true | **3** | true | true | false | false | 0 | 接続 | 2 | 5 |
| bengio | v2.1.3 | 55 | true | 0 | true | true | false | false | 0 | 接続 | 2 | 5 |
| andrew | v2.1.3 | 55 | true | 0 | true | true | false | false | 0 | 接続 | 2 | 5 |
| ilya | v2.1.3 | 55 | true | 0 | true | true | false | false | 0 | 接続 | 2 | 5 |
| efros | v2.1.3 | 55 | true | 0 | true | true | false | false | 0 | 接続 | 2 | 5 |
| dlsta | v2.1.3 | 55 | true | 0 | true | true | false | false | 0 | 接続 | 2 | 5 |

- API の値と `config.xml` の値は六台とも全項目で一致。
- 共有フォルダは六台とも `agent-claude-settings` `agent-codex-config` `agent-instructions` `claude-sync` `m2`。
- 中心の接続一覧に六ノードすべてが在る。
- **lecun の `urAccepted` は 3**（中心の変更前と同じ値）。原因は UNKNOWN。
- **G1: pass**（A 鍵は手元・転送非依存 / B 手順書を記録 / C 変えずに読んだ / D 六台とも v2.1.3）。

## 4. 一台ずつ当てる（Task 2。利用者が `!` で一台ずつ実行）

順番は lecun → bengio → andrew → ilya → efros → dlsta。各台の実行後に実行者が照合し、
PASS を確かめてから次の命令を出した。スクリプト `st_patch.py` は目標値と違う項目だけを
1 項目ずつ `PATCH /rest/config/options` で送り、3 秒後に読み戻す。続けて中心の状態を読む。
照合は `check.py`（変わった項目が 3 つ以内・API と config.xml が目標値・局所告知 true→true・
接続/登録/共有が前後で同一・処理の識別子が同一・中心から 6 台・中心の設定が無変更）。

| ノード | 変更時刻 (JST) | natEnabled | urAccepted | crashReportingEnabled | HTTP | 変わった項目 | API | config.xml | 局所告知 | 接続/登録/共有 | 処理の識別子 | 中心から 6 台 | 判定 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lecun | 14:38:09 | true→false | **3**→-1 | true→false | 200×3 | 3 | 目標値 | 目標値 | true→true | 同一 | 140103/140120 同一 | 6 | PASS |
| bengio | 14:38:42 | true→false | 0→-1 | true→false | 200×3 | 3 | 目標値 | 目標値 | true→true | 同一 | 332564/332580 同一 | 6 | PASS |
| andrew | 14:39:23 | true→false | 0→-1 | true→false | 200×3 | 3 | 目標値 | 目標値 | true→true | 同一 | 89005/89026 同一 | 6 | PASS |
| ilya | 14:39:38 | true→false | 0→-1 | true→false | 200×3 | 3 | 目標値 | 目標値 | true→true | 同一 | 107755/107777 同一 | 6 | PASS |
| efros | 14:39:52 | true→false | 0→-1 | true→false | 200×3 | 3 | 目標値 | 目標値 | true→true | 同一 | 73191/815391 同一 | 6 | PASS |
| dlsta | 14:40:06 | true→false | 0→-1 | true→false | 200×3 | 3 | 目標値 | 目標値 | true→true | 同一 | 61631/61670 同一 | 6 | PASS |

- 既に目標値だった項目は無い（六台とも 3 項目すべてを送った）。再起動は不要だった。
- 中心の options は各台の変更後も変更前の控えと完全一致（禁止 5 を守った）。
- 控え: `/home/ubuntu/slocal2/task-backups/20261007-fleet-before/<host>.after.json` と `philip.after-<host>.json`。
- **G2: pass**。

### 4.1 照合の陽性対照

写しを壊して `check.py` に通した（原本は触らない）。

| 壊し方 | 出た判定 |
|---|---|
| lecun の変わった項目に `listenAddresses` を足す | `only_3_changed False` → `VERDICT FAIL` |
| bengio の変更後の処理の識別子を別値にする | `pids_same False` → `VERDICT FAIL` |
| andrew の後の中心の接続を 5 台に減らす | `philip_sees` 5 台 → `VERDICT FAIL` |

最初の版の `check.py` は判定の行で自分の誤り（辞書を添字で読んだ）により例外で落ちた。
直したうえで lecun と bengio を判定し直した。

## 5. 止まったことの確かめ（Task 3 Step 1。実行者が実行、読み取りのみ）

記録は各ノードの `~/.syncthing.log`（原文は UTC。下の表は JST へ換算）。

### 5.1 STUN

| ノード | 変更 (JST) | `STUN disabled` の時刻 (JST) | 変更からの秒 | 件数（記録の全期間） |
|---|---|---|---|---|
| lecun | 14:38:09 | 14:40:18 | 129 | 1 |
| bengio | 14:38:42 | 14:40:25 | 103 | 1 |
| andrew | 14:39:23 | 14:41:59 | 156 | 1 |
| ilya | 14:39:38 | 14:39:58 | 20 | 1 |
| efros | 14:39:52 | 14:42:44 | 172 | 1 |
| dlsta | 14:40:06 | 14:41:41 | 95 | 1 |

- 六台とも記録の全期間（最古行は lecun/bengio/andrew/ilya が 2026-08-24〜25、efros 09-17、dlsta 09-21 JST）で
  1 件だけ、時刻はいずれも変更の後。**変更前は 0 件であり、不在ではなく遷移の記録である。**
- andrew / efros / dlsta は 14:40:45 JST の時点で 0 件（記録の最終行は 14:35:25 JST）。
  14:46:08 JST の再確認で 1 件ずつ出た。周期 180 秒以内に収まる。

### 5.2 使用状況の日次送信

| ノード | 変更前の `urAccepted` | `Sent usage report` の件数 | 判定 |
|---|---|---|---|
| lecun | **3** | **44**（初回 2026-08-25 06:05:37 JST、最終 2026-10-07 06:06:50 JST） | **UNKNOWN**。次の送信予定 2026-10-08 06:06 JST ごろを越えていない |
| bengio / andrew / ilya / efros / dlsta | 0 | 0 | 痕跡が元から 0 件。「止まった」とは書けない。設定が -1 になったことだけが事実 |

- **lecun は記録の始まりから毎日送っていた。** 中心の前契約で見つかった 0→3 の変化と違い、lecun は
  記録の範囲で一度も 0 ではなかった。誰がいつ 3 にしたかは UNKNOWN。

### 5.3 障害報告

六台とも `crash.syncthing` / `crash report` / `newcrash` の痕跡は 0 件。**止まったとは書けない。**
設定が false になったことだけが事実。

### 5.4 前後の試験（`pytest`、実行者が実行）

同じ 2 ファイルを除外（`test_estimate_tier_cost.py` は site-packages の `tools` が repo を隠して収集時に失敗、
`test_stage1_dtower_convergence.py` は `third_party/Relation-DETR/util/convergence.py` が本体にも無く収集時に失敗。
どちらも既存）。

| 時点 | 場所 | 結果 |
|---|---|---|
| 前 | HEAD `ef8f641a` を scratch へ `git worktree add --detach`（`third_party/` をリンク） | 7 failed / 654 passed / 16 skipped |
| 後 | 作業ツリー（本契約の文書を含む） | 6 failed / 670 passed / 1 skipped |

- 共通の 6 件: `test_engines::test_mmdet_trainer_eval_recipe_in_metrics`、`test_fetch_task::test_rejects_unknown_file_name`、
  `test_research_logger` の 4 件。前契約の 6 件と同じ。
- 前だけの 1 件 `test_stage1_ptower_r3::test_only_the_stem_is_frozen_in_both_chains` と skip の差 15 件は、
  別の作業ツリーに版管理外の資源が無いことによる差と見る（**条件が揃っていない**）。本契約は `tasks/` と
  `docs/sessions/digest/` の文書だけを足し、コードを変えていない。
- 1 回目は zsh で除外の変数が単語に割れず、除外が効かないまま走った（実行者の誤り）。配列に直して測り直した。

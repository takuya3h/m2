# RESULT — T-2026-08-24-syncthing-config-survey

**kind:** `analysis`  **実行ホスト:** philip（論理名。OS のホスト名は `aolab`）
**判定:** **PASS**（読み取りのみ。設定は開始時と要約値で同一）

生の出力は `audit.md`（要約していない）。次の実装契約向けの手順は `handoff.md`。

## 1. 解決された参照

### `contract.inject_verbatim: conventions#prohibitions`

`context/conventions.md:98-107` の原文（要約していない）。

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

    $ git --no-pager log -1 --format=%h -- context/conventions.md
    d422b08

spec の記載 `d422b08` と**一致**した。置換は不要。

### `inputs.code.entrypoints`

`scripts/sync/keeper.sh`（sha256 `9fe9c423…`）と `scripts/sync/m2-sync.sh`。
稼働版 `~/bin/keeper.sh` は正本と sha256 が一致。

## 2. 検証とプリフライト

| 検査 | 終了コード | 内容 |
|---|---|---|
| `make task-validate` | **0** | `OK   T-2026-08-24-syncthing-config-survey` / `1 task(s), 0 failed` |
| `make task-preflight` | **0** | 4 PASS / 1 WARN / 4 SKIP / 0 FAIL |
| `make forbidden-check` | **0** | `status: pass` / `violations: []` / `changed: 7`。**ただし通ったのは退避の副作用である。** 開始前は `data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md` を「禁止領域 `data/` の内側」として指し `status: fail` だった。`make task-start` の前提を満たすためその未追跡ファイルを `git stash` へ退避したので、いま検査対象から消えているだけである。**`git stash pop` で戻せば再び `fail` に戻る。** 禁止 8 が削除も移動も commit も禁じており本契約では解決できない |

**SKIP された項目**（合格ではなく「実行されなかった」）: `P2 cuda_ext_loaded`
`P3 deterministic_flags`（`plan.env.preflight` に記載なし）、`P4 prereg_committed`
`P5 frozen_source_hash`（`kind=analysis` のため対象外）。

**P9 spec_lint の WARN は 6 件**（終了コードは変わらない）。内訳は §5 に書いた。

## 3. ゲート

| ゲート | 判定 |
|---|---|
| **G1**（Phase A 後、`on_fail: stop`） | **PASS**。設定の在り処・要約値・権限、要素名 105 種と出現数、device 1 件 / folder 1 件、手段の三分割、常駐なしの読み取りの実測 |
| **G2**（Phase B 後、`on_fail: ask`） | **PASS**。旧構成の定義を出所つきで復元、UNKNOWN 4 件を区別、除外規則の三者一致、順序の判定、両ホスト種別の手順と失敗の様式 |

## 4. 完了判定（実測値または UNKNOWN）

| # | 判定 | 実測 |
|---|---|---|
| 1 | 設定の在り処と要約値と権限 | `~/.local/state/syncthing/` に 3 ファイル。`config.xml` sha256 `abb2fa89…` 8494 バイト **600**、`cert.pem` `5f3b4bd8…` 794 **664**、`key.pem` `92629ef1…` 288 **600** |
| 2 | 要素の名前と出現数 | 相異なる要素名 **105 種**を全件記録（切り詰めていない）。上位は `paused` 4 / `device` 4 / `maxSendKbps` 3 / `address` 3。**秘匿の値は含めていない** |
| 3 | 相手と共有フォルダの件数と識別子 | `grep -c 'device id='` = **4**、`grep -c 'folder id='` = **2**。ただし**実体は device 1・folder 1**。残りは `<folder>` 内の共有相手一覧と `<defaults>` の雛形（行 2 / 4 / 43 / 116-158 で確認）。実体の folder は `id="default" path="/home/ubuntu/Sync" type="sendreceive"`。device は自分 1 件、`name="aolab"`、識別子は `scripts/sync/device_ids/philip.txt` と**一致**（他 4 台とは不一致＝両方向の対照） |
| 4 | 待ち受けと外向きの既定値 | `listenAddress=default` / `globalAnnounceEnabled=**true**` / `localAnnounceEnabled=true` / `relaysEnabled=**true**` / `natEnabled=true` / GUI `127.0.0.1:8384` `tls="false"`。**旧構成は global と relays が false だった**（差分は §6） |
| 5 | 下位命令の一覧（`cli` の有無） | v1.27.10。`serve` `generate` `decrypt` `cli` `install-completions`。**`cli` は在る**。`cli config {version,folders,devices,gui,ldap,options,ignored-devices,defaults}`、`devices` の下に `list` `add` `add-json` |
| 6 | 常駐なしで設定を読めるか | **読めない。** `cli --home … config devices list` は **exit=1**、`Get "http://127.0.0.1:8384/rest/system/config": dial tcp 127.0.0.1:8384: connect: connection refused`。**設定ファイルを直接読んでいるのではなく、動いている本体へ REST で問い合わせている** |
| 7 | 設定を作る命令の機能 | `generate` は鍵と設定を作って終了するのみ。`--gui-user` `--gui-password` `--no-default-folder` はあるが、**相手や共有フォルダを足す機能は無い** |
| 8 | 手段を三つに分けた評価 | 命令列＝**常駐が要る**（実測）／直接編集＝**使える。常駐不要**／画面＝常駐と中継の両方が要る（禁止 2・3 のため本契約では立てない）。**判定: 次の契約は直接編集を主手段にする** |
| 9 | 旧構成の定義の復元 | **復元できた。** `tasks/T-2026-08-12-sync-audit-bengio/audit.md:222-228`。`folder_count=2`／`claude-sync` `path=/home/ubuntu/claude-sync` `sendreceive` 11 台共有／`m2` `path=/home/ubuntu/slocal2/m2` `sendreceive` 11 台共有／`device_count=11`／`globalAnnounceEnabled=false` `localAnnounceEnabled=true` `relaysEnabled=false` `listenAddress=default`／ノードは philip を `tcp://127.0.0.1:22001` として登録 |
| 10 | 除外規則の正本と反映先 | 正本 `.stglobalignore`（68 行）。反映は `~/bin/keeper.sh:48-49` の `git show origin/phase0:.stglobalignore > $M2DIR/.stignore.new && mv` の 1 経路のみ。**`.stglobalignore` / `.stignore` / `origin/phase0:.stglobalignore` の三者が sha256 `61593e99…` で一致**。`.stignore` は `.gitignore:192` で版管理外 |
| 11 | 共有すべきものの表 | `~/claude-sync/`＝共有する（中身は要判断）／repo＝共有する（**二重にならない理由を `README.md:1145-1178` から確認**）／`default`＝消す。**UNKNOWN 4 件**を明記（§6） |
| 12 | 現在の中身の大きさと件数 | `~/claude-sync/` = **8.0K / 実ファイル 1 件 / symlink 0 件**（`sync-alerts.log` のみ）。`/home/ubuntu/Sync` は**存在しない**。repo = 79G のうち同期対象は概算 **約 19G**（checkpoints 14G / `data/processed` 3.3G / predictions 1.3G / annotations / outputs 1.3M / logs 5.8M） |
| 13 | 中継と同期処理の関係 | `keeper.sh:33-38` が `.tunnel_to_*` を辞書順で 1 つ選び `ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <鍵>` を張る。**ノード側は相手の住所を `tcp://127.0.0.1:22001` にする**（旧構成の実測と一致）。中心は目印を置かないため張らない |
| 14 | 順序の判定と根拠 | **中心 → ノード。設定 → 中継 → 起動。一台ずつ。** 根拠は `keeper.sh:41-43` が **`[ -x ~/bin/syncthing ]` だけで起動する**こと。**起動の引き金は実行権であり、順序が固定される** |
| 15 | 中心用・一般ノード用の手順 | `handoff.md` §2 §3。事前の記録／控え／変更（10 項目 + 7 項目）／中継／起動／確認／戻し方。**実行していない** |
| 16 | 疎通の確認（示す/示さない） | `handoff.md` §4。8 通りの確認を「示すこと」「示さないこと」に分けた。**最も強い確認＝小さなファイルが同じ要約値で相手に現れること**。測り方と、`m2` 側ではなく `~/claude-sync/` で測るべき理由も書いた |
| 17 | 失敗の様式と戻し方 | `handoff.md` §5。8 様式（中継不成立／識別子の誤り／XML 破壊／除外規則の失効／告知の落とし忘れ／`default` 残存／空の側が配る／二重起動）＋「五台とも止まる」の回避策 6 点 |
| 18 | 17 項目すべてに実測値か UNKNOWN | **済**（本表） |
| 19 | 設定が開始時と一致・目印 0 件 | **一致**。3 ファイルとも sha256・サイズ・権限が開始時と同一。目印 **0 件**。`~/bin/syncthing` も **644 のまま**（sha256 `32ab747e…` 不変） |
| 20 | 同期処理 0 件（両方向の対照） | **0 件**。実行ファイル名での照合。**陽性対照 `zsh`=3**、**陰性対照 `zzz_no_such`=0**。常駐処理 `keeper.sh`=1（pid 72428、触れていない）、中継=0 |
| 21 | 変更が契約の範囲・PR が存在 | §8 |
| 22 | 報告が台帳へ返っている | §8 |

## 5. 起票者の誤り

| # | 型 | 内容 |
|---|---|---|
| 1 | `asserted_without_measuring` | 「確定した事実（再測定は不要）」が**設定の場所は `--home` で明示する。既定ではない**と断ずる。隔離した HOME で `serve --paths` を実行すると、設定ファイルは `$HOME/.local/state/syncthing/config.xml` と表示された。**既定の場所である。** 旧構成の記録（`T-2026-08-12-sync-audit-bengio/audit.md:207`「起動引数での指定は無く既定の場所」）とも食い違っていた |
| 2 | `check_does_not_check` | Task 5 Step 3 の**陽性対照 `python(exact_arg)` が 0 を返す**。走査は自分と祖先を除外し、この環境の実行は `.venv/bin/python` のため、引数の要素が厳密に `python` と一致する処理は存在しない。**契約自身が申し送り 3 で戒めた「常に 0 を返す壊れ方と区別できない」に該当する。** 実在する語 `zsh` で 3 件を得て対照を取り直した |
| 3 | `self_contradiction` | 禁止 2「同期処理を常駐させる」と、Task 2 Step 1-3 の「`~/bin/syncthing --help` を実行せよ」が philip では両立しない。**前契約が禁止 2 を守るために実行権を 644 へ落としてあり、正本は起動できない。** 実行権を戻せば `keeper.sh:41-43` が 30 分以内に起動する。正本に触れず作業領域の複製（sha256 一致を提示）で読んだ |
| 4 | `asserted_without_measuring` | 「確定した事実」の中心の住所 `192.168.196.150`。philip は Docker の中にあり、局所で観測できるのは `172.17.0.13`、待ち受けている SSH の口は **`22`**（`50072` ではない）。**`50072` は容器の外側の写像**と解せば矛盾しないが、**外からの到達性は本契約では検証できない**（禁止 5）。文書側も `172.17.0.20` と食い違う（`docs/host_dev_env_setup.md:12`）。**次の契約は目印を置く前に到達を実測すること** |

**P9 spec_lint の WARN 6 件**の扱い。`host_mismatch@SPEC.md:5`（宣言 `philip` と実行環境 `aolab`）は
**この艦隊では誤検知**である。`docs/host_autosync_onboarding.md:85,153` が
「ilya / philip は hostname=aolab 衝突のため名前を明示」と記録しており、論理名は `.servername`
（`.gitignore:225` で版管理外、値は `philip`）が持つ。同期の記録も `[philip]` と名乗る。
`separated_source` 5 件（`SPEC.md:38,390,393,396,424`）は、いずれも行末の `\` で次行へ継続している
1 つの命令であり、**検査器が行継続を解釈していない**。契約側の誤りではない。

## 6. 決めきれなかったこと（UNKNOWN）

| 事項 | なぜ決められないか |
|---|---|
| `~/claude-sync/` に**何を戻すか** | 旧構成の 2532 ファイルの中身が版管理に無い。各実装系の設定は各ホストの実体から集める必要があり、**他ホストへ接続できない**（禁止 5） |
| 5 台のうち**どれが中身を持つか** | 同上。philip 上は 1 ファイルしか無い。**空の側が `sendreceive` で参加すると中身を消しうる** |
| 共有フォルダの**型** | 上が決まらないと決められない。`handoff.md` は暫定として「中身を持つ台を `sendonly`、他を `receiveonly`」を推している |
| 初回 **約 19G** を中継越しに流してよいか | 帯域も所要時間も測っていない。`OPERATION.md:15` の 28 秒は**差分同期**の実測であり初回全量ではない |
| 中心の住所 `192.168.196.150` の到達性 | 禁止 5 のため他ホストから試せない。容器内からは検証不能 |
| 生成物（`context/auto/`）への反映 | **禁止 7 により再生成していない**ため、本報告が投影に現れるかは確かめていない |

## 7. 逸脱

| # | 型 | 内容 |
|---|---|---|
| 1 | `judgement` | **`~/bin/syncthing` の正本を実行せず、作業領域へ複製して調べた。** 実行権を戻すと `keeper.sh:41-43` が 30 分以内に起動し禁止 2 に触れる。複製の sha256 が正本と一致することを提示した。正本の権限は 644 のまま |
| 2 | `judgement` | **`cli` を正本の設定へ向ける前に、設定の複製へ向けて試した。** `cli` が設定を書き換える可能性があり、禁止 1 は本契約の要である。複製が変わらないことを確かめてから正本へ向けた（正本も前後で sha256 不変） |
| 3 | `judgement` | **`serve --paths` を隔離した HOME で実行した。** 自ホームで実行すると設定や DB を作りうる。実測では `fakehome` に何も作られなかった |
| 4 | `spec_defect` | **契約の陽性対照 `python(exact_arg)` が 0 を返したため、実在する語 `zsh` で取り直した**（3 件）。契約の走査そのものの出力も併記している |
| 5 | `environment` | **契約が示す `awk` 系の集計が mawk で空振りした**（`strtonum` は gawk の拡張）。`/proc/net/tcp` を Python で読み直して待ち受けの口を得た |
| 6 | `environment` | **`ip` `ss` `netstat` `lsof` がいずれも存在しない**（`command -v` が exit=1）。住所は `hostname -I`、待ち受けは `/proc/net/tcp` から取った |
| 7 | `environment` | **`make task-start` が前提検査で停止した**（作業ツリーに未追跡 2 件、exit 3）。ユーザーの判断を仰ぎ、`git stash push -u` で退避して実行し、**報告の後に `git stash pop` で戻す**。退避したのは `data/annotations/_deprecated/egosurgery_hand4/DEPRECATED.md`（sha256 `2ca94c44…`）と `docs/sessions/digest/2026-08-22-d0076c74-….md`（同 `f7b279540…`）。**どちらも消していない**（禁止 8 を守るための退避である） |
| 8 | `judgement` | **`make taskindex` `make inbox` を実行していない**（禁止 7）。skill の手順 6 は投影の確認を求めるが、契約の禁止が優越する。結果は §6 の UNKNOWN |

## 8. 送出と報告

| 項目 | 実測 |
|---|---|
| 変更範囲 | `git status --porcelain` = **2 件**。`tasks/T-2026-08-24-syncthing-config-survey/` と `tasks/inbox.d/T-2026-08-24-syncthing-config-survey.md` のみ。**契約のディレクトリと受け皿に限られている** |
| 開始時の未追跡 | 契約開始時（`task-start` 直後）は **0 件**。それ以前からあった 2 件は `git stash` へ退避しており、**削除も移動もしていない**（§7-7） |
| commit | `88f6035 docs(sync): survey syncthing config structure and decide setup order`（7 ファイル / 2059 行追加） |
| push | `origin/feat/syncthing-config-survey` へ新規分岐として送出。追跡設定済み |
| PR | **#139 OPEN**（`draft=false`、base `phase0`） |
| 台帳への返送 | `make task-report` **exit=0**。`verdict: pass` / `n_issuer_defects: 4` / `report_bytes: 15201` / `report_sha256: 33e22d0a…` / `replaced_blocks: 0`。**秘匿の検査を通って送出された** |
| 抑止の解除 | `.sync-pause` は `task_start.sh` が置いたもの。**報告の完了後に解除する** |

**完了判定 21・22 を満たした。**

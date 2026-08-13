# lecun の marker を可逆退避し、正本 keeper を中心として起動する

**task_id:** `T-2026-08-13-hub-deploy-lecun-marker-cutover`  **kind:** `impl`  **depends_on:** `T-2026-08-13-hub-deploy-lecun`
**実行ホスト:** `lecun`  **repo:** `~/slocal2/m2`

## Goal

`T-2026-08-13-hub-deploy-lecun` は、handoff が lecun の marker 退避を要求する一方、
同じ契約が marker の移動と変化を禁止していたため、配置前に安全停止した。

本契約は選択を確定する。**handoff を正とし、lecun の旧 marker を glob に一致しない
専用バックアップへ可逆的に退避する。marker 不変は要求しない。** その後、Git の正本 keeper
を配置し、旧 keeper の数値 PID だけへ TERM を送り、正本 keeper を起動する。

成功状態は、lecun の home 直下に marker が無く、SSH 中継と local relay が無く、
Syncthing の既存プロセスと待ち受けを維持したまま、正本 keeper が一意に施錠を保持し、
m2-sync を監督している状態である。一般ノードの canary 切替は本契約に含めない。

## 0. 前提、許可、禁止

### 起動直後の確認

`make task-start` 後、最初に一つの命令として実行する。

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && touch .sync-pause && git fetch origin && git branch --show-current && grep -c sync-pause ~/bin/m2-sync.sh && git merge-base --is-ancestor origin/phase0 HEAD

- 分岐名が `feat/hub-deploy-lecun-marker-cutover` でなければ停止する。
- `grep -c` が零なら `.sync-pause` が同期書き込みを抑止できないため停止する。
- `git merge-base` が非零なら最新の `origin/phase0` を含まないため停止する。
- `.sync-pause` は台帳返送直前まで残す。

### 本契約が明示的に許可する副作用

| # | 許可 |
|---|---|
| 1 | `/home/ubuntu/bin/keeper.sh` の控え作成、正本への置換、必要時の復旧 |
| 2 | `/home/ubuntu/.tunnel_to_philip` の複製控えと、専用バックアップへの移動、必要時の復旧 |
| 3 | 事前に再同定した旧 keeper の数値 PID 一件への TERM |
| 4 | 正本 keeper の一回の明示起動と、失敗時の新 keeper 数値 PID への TERM |
| 5 | keeper が通常動作として行う m2-sync と stignore の更新、既存ログへの追記 |
| 6 | repo 内の本契約ディレクトリ、受け皿、生成物、分岐の push、PR、台帳返送 |

### 禁止事項

| # | 禁止 |
|---|---|
| 1 | `/home/ubuntu/bin` のうち `keeper.sh` とその本契約専用控え以外を変更する |
| 2 | `/home/ubuntu/.ssh` と `/home/ubuntu/claude-sync` を手で変更する。読むことと keeper の通常追記は可 |
| 3 | 正本 `scripts/sync/keeper.sh` と `scripts/sync/m2-sync.sh` を変更する |
| 4 | marker の内容を書き換える、新markerを作る、専用バックアップ以外へ移す |
| 5 | 数値 PID 一件への TERM 以外の方法で process を停止する。広域停止と KILL を使わない |
| 6 | Syncthing を停止、再起動、設定変更する |
| 7 | 他ホストで命令を実行する。他ホストへ書き込む |
| 8 | 秘密鍵、token、資格情報の本文を出力または記録する |
| 9 | 未測定の値を書く。未測定は `UNKNOWN` とする |
| 10 | 本作業分岐のPRを `phase0` へ取り込む。自動取り込みを有効化する。push と PR 作成は行う |
| 11 | `runindex` と `context/auto` を手で編集する。生成器による生成は可 |
| 12 | GPU、実験、データ、split、凍結源を変更する |
| 13 | PR 100 が `phase0` に入る前に host の変更へ進む |

### 前契約から確定した事実

以下は停止報告に実測が残る。開始状態が同じかは本契約で再測定し、値を固定前提にしない。

| 事実 | 前回の実測 |
|---|---|
| 稼働 keeper | 旧版一件、FD9の施錠を保持、正本と要約値が異なる |
| marker | `/home/ubuntu/.tunnel_to_philip` 一件、内容は一行目のみ非空 |
| 中継 | SSH中継 process と local relay は零件 |
| Syncthing | process 二件、22000と8384が待ち受け、停止も再起動もしていない |
| 正本の分岐 | marker が無ければ SSH 中継を起動せず、その後の Syncthing 監視と m2-sync は実行する |
| 施錠 | 旧 keeper が保持中で、非待機 probe は失敗した |

### 前回の二矛盾が除かれたこと

| 前回の矛盾 | 本契約での解消 |
|---|---|
| handoff は marker 退避を要求するが SPEC は移動を禁止 | 本契約は専用バックアップへの移動を明示許可し、移動後 marker 零件を要求する |
| PR 取り込みを禁じながら `git merge origin/phase0` を要求 | 本契約は `git merge` を一度も要求せず、最新 base を含まなければ変更前に停止する |

## Task 1 Phase A: 依存契約と開始状態を固定する

**Files:** Create: `tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md`, `hub_state_probe.py`, `launch_keeper.py`

- [ ] **Step 1: PR 100 の停止報告が phase0 に入っていることを確認する**

    git cat-file -e 'origin/phase0:tasks/T-2026-08-13-hub-deploy-lecun/RESULT.md'
    git --no-pager show 'origin/phase0:tasks/T-2026-08-13-hub-deploy-lecun/result.yaml' | grep -F 'status: stopped'
    git --no-pager show 'origin/phase0:tasks/T-2026-08-13-hub-deploy-lecun/deploy.md' | grep -F '配置前に停止した'

三命令のどれかが非零なら、PR 100 が未反映または内容不一致である。hostを変更せず停止する。

- [ ] **Step 2: 共通状態 probe を作る**

`hub_state_probe.py` は読み取り専用とし、次を構造化して標準出力へ出す。

1. `/proc` の数値 directory を全走査し、自分と祖先を除外する。
2. keeper、m2-sync、syncthing、SSH local forwarding、不存在対照の件数、PID、PPID、開始 tickを出す。
3. keeper PID の FD9 lock と FD255 のリンク先、inode、内容のSHA-256を出す。
4. `/proc/net/tcp` と `/proc/net/tcp6` から22000、22001、50072、8384のLISTENを復号する。
5. home直下の `.tunnel_to_*` を切り詰めず列挙し、件数、path、mode、行数、SHA-256だけを出す。内容は出さない。
6. `/home/ubuntu/.keeper.lock` の非待機取得可否を出す。
7. `/home/ubuntu/.ssh/authorized_keys`、`.stignore`、`known_hosts` は実在、mode、行数、SHA-256だけを出す。

`launch_keeper.py` は `/home/ubuntu/bin/keeper.sh` だけを `subprocess.Popen` で起動し、stdinとstdoutとstderrをDEVNULLへ接続し、新しいsessionで起動してPIDを出す。他のpathを引数に取らない。

- [ ] **Step 3: probe 自体の陽性対照を通す**

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub_state_probe.py --self-test | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

陽性対照は、現在開いている待ち受けと閉じた待ち受け、実在processと不存在語、実在markerと不存在path、取得できる一時lockとkeeperが保持するlockを区別する。全対照を通らなければ停止する。

- [ ] **Step 4: 開始状態を一回の probe で保存する**

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub_state_probe.py --label before | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md
    sha256sum /home/ubuntu/bin/keeper.sh scripts/sync/keeper.sh /home/ubuntu/bin/m2-sync.sh scripts/sync/m2-sync.sh | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md
    git --no-pager status --porcelain | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

変更前の停止条件は次のすべてである。

- keeperが一件で数値PIDを一意に得られる。
- markerが一件でpathが `/home/ubuntu/.tunnel_to_philip` である。
- Syncthingが実在し、22000がLISTENである。
- SSH local forwardingと22001 LISTENが零件である。
- 稼働keeperと正本keeperが異なり、稼働m2-syncと正本m2-syncが一致する。
- `/home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover` が存在しない。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 依存報告 | 三つのGit object検査が成功 | 別task IDの不存在objectが非零になることも測る |
| 2 | probe | self-testが全項目PASS | 各項目に実在と不存在または開と閉の対照を与える |
| 3 | keeper | 一件でPIDとFDを取得 | 不存在語が零件、Syncthingが非零件になる同一走査と突き合わせる |
| 4 | marker | 指定path一件 | home直下の全列挙と指定pathの直接statを突き合わせる |
| 5 | Syncthing | process非零、22000 LISTEN | process走査とTCP table復号の異質な二経路で確かめる |

## Task 2 Phase B: 可逆な控えを作る

**Files:** Create outside repo: keeper控え、marker専用バックアップ

- [ ] **Step 1: 専用バックアップを作る**

    mkdir -m 700 /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover
    cp -p /home/ubuntu/bin/keeper.sh /home/ubuntu/bin/keeper.sh.before.T-2026-08-13-hub-deploy-lecun-marker-cutover
    cp -p /home/ubuntu/.tunnel_to_philip /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy
    sha256sum /home/ubuntu/bin/keeper.sh /home/ubuntu/bin/keeper.sh.before.T-2026-08-13-hub-deploy-lecun-marker-cutover /home/ubuntu/.tunnel_to_philip /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md
    stat -c '%a %n' /home/ubuntu/bin/keeper.sh /home/ubuntu/bin/keeper.sh.before.T-2026-08-13-hub-deploy-lecun-marker-cutover /home/ubuntu/.tunnel_to_philip /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

keeper同士とmarker同士がそれぞれバイト一致し、modeも一致しなければ停止する。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 6 | keeper控え | 原本とバイト一致、mode一致 | keeperと異なる正本を同じ比較へ与え、不一致を識別できることを確認 |
| 7 | marker控え | 原本とバイト一致、mode一致、一件 | 原本とcopyを別pathから測り、開始時のmarker件数とも突き合わせる |

## Task 3 Phase C: 正本を配置しmarkerを退避する

**Files:** Modify outside repo: `/home/ubuntu/bin/keeper.sh`, Move outside repo: 旧marker

- [ ] **Step 1: Git objectから正本をstagingする**

    git --no-pager show --output=/tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover origin/phase0:scripts/sync/keeper.sh
    chmod 755 /tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover
    cmp -s /tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover scripts/sync/keeper.sh
    sha256sum /tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover scripts/sync/keeper.sh | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

- [ ] **Step 2: 正本keeperをatomicに配置する**

    install -m 755 /tmp/keeper.T-2026-08-13-hub-deploy-lecun-marker-cutover /home/ubuntu/bin/keeper.sh.new.T-2026-08-13-hub-deploy-lecun-marker-cutover
    mv /home/ubuntu/bin/keeper.sh.new.T-2026-08-13-hub-deploy-lecun-marker-cutover /home/ubuntu/bin/keeper.sh
    cmp -s /home/ubuntu/bin/keeper.sh scripts/sync/keeper.sh

この時点では旧PIDが旧FD255を実行中である。まだ停止しない。

- [ ] **Step 3: 旧markerを専用バックアップへ移す**

    mv /home/ubuntu/.tunnel_to_philip /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/.tunnel_to_philip.active
    find /home/ubuntu -maxdepth 1 -type f -name '.tunnel_to_*' -print | sort | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md
    sha256sum /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/marker.copy /home/ubuntu/.hub-migration-backup.T-2026-08-13-hub-deploy-lecun-marker-cutover/.tunnel_to_philip.active | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

home直下のmarkerが零件で、移動後実体とcopyがバイト一致しなければ停止し、Task 5のrollbackを行う。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 8 | staging | Git object、working tree正本、stagingが一致 | 配置前keeperとの比較が不一致であることも併記 |
| 9 | 配置 | 稼働pathと正本が一致 | cmpとSHA-256の二経路で測る |
| 10 | marker退避 | home直下零件、copyと移動後実体が一致 | backup内では実体二件を検出し、走査が空振りでないことを示す |

## Task 4 Phase D: 旧keeperを止め、正本keeperを起動する

**Files:** Modify process state: keeper一件

- [ ] **Step 1: 旧PIDを変更直前に再同定する**

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub_state_probe.py --label before_term | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

開始時PIDと同じ一件で、cmdline、PPID、開始tickが一致する場合だけ、出力された数値を `OLD_PID` として次へ使う。異なれば停止する。

- [ ] **Step 2: 旧PID一件だけへTERMを送る**

    kill -TERM OLD_PID

`OLD_PID` は直前のprobeが出した十進数一件へ置換する。名前一致停止、複数PID、KILLは使わない。
十秒以内に `/proc/OLD_PID` が消え、非待機lock probeが成功するまで一秒間隔で確認する。
消えなければ強い信号を送らず停止し、判断を仰ぐ。

- [ ] **Step 3: 正本keeperを一回だけ起動する**

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/launch_keeper.py | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

五秒後に同じprobeを実行する。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub_state_probe.py --label after_start | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 11 | 旧PID再同定 | 開始時と同じPID、cmdline、開始tick | PIDだけでなく三属性を開始時snapshotと比較 |
| 12 | 旧PID停止 | `/proc`から消え、lock取得成功 | 停止前は同じlock probeが失敗したことと対にする |
| 13 | 新keeper | 新しいPID一件、FD255正本一致、lock保持 | 起動直前のkeeper零件とlock取得成功を基準にする |

## Task 5 Phase E: 中心稼働を検証し、失敗ならrollbackする

**Files:** Modify on failure only: keeper、marker、keeper process

- [ ] **Step 1: 切替後状態を再測定する**

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub_state_probe.py --label stable | tee -a tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/hub-audit.md

成功には次の全部が要る。

1. keeper一件、新PID、PPID 1、FD9 lock保持、FD255のSHA-256が正本一致。
2. home直下marker零件、SSH local forwarding零件、22001 LISTENなし。
3. SyncthingのPIDと開始tickがbeforeと同じで、件数も同じ、22000がLISTEN。
4. `/home/ubuntu/claude-sync/sync-alerts.log` に切替後の一時停止記録があり、m2-sync一周を示す。
5. authorized_keysとknown_hostsのSHA-256とmodeがbeforeから不変。
6. keeper控えとmarker控えが残り、rollback可能である。

- [ ] **Step 2: 失敗時だけhandoffどおりrollbackする**

成功条件の一つでも満たさなければ、次を順に行う。

1. 新keeperをprobeで一意に再同定し、その数値PID一件だけへTERMする。
2. PID消滅とlock解放を確認する。
3. 新keeperを専用backup directoryへ失敗版として移す。
4. keeper控えをmode込みで `/home/ubuntu/bin/keeper.sh` へ戻し、開始時原本とバイト一致させる。
5. 移動済みmarkerを `/home/ubuntu/.tunnel_to_philip` へ戻し、copyとバイト一致させる。
6. `launch_keeper.py` で旧keeperを一回起動する。
7. probeでkeeper、marker、Syncthing、lock、待ち受け、authorized_keys、known_hostsがbeforeへ戻ったことを確かめる。
8. rollback後も戻らない場合は追加操作をせずescalateする。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 14 | markerと中継 | marker零、SSH中継零、22001なし | backup内marker非零、Syncthing process非零、22000 LISTENを同じprobeで得る |
| 15 | Syncthing維持 | PID、開始tick、件数、22000がbeforeと一致 | processとTCP tableの異質な二経路をbeforeとafterで比較 |
| 16 | m2-sync一周 | 切替後の一時停止記録が増える | logの開始時sizeとmtimeを先に測り、切替後との差を取る |
| 17 | SSH副作用なし | authorized_keysとknown_hostsが不変 | beforeとafterを別snapshotから比較する |
| 18 | rollback | 成功時は未実施、失敗時は全状態がbefore一致 | 失敗時はrollback後に同じprobeを再実行しbeforeと比較 |

## Task 6 Phase F: 検証、送出、抑止解除、台帳返送

**Files:** Create: `RESULT.md`, `result.yaml`; Modify: task投影の生成物

- [ ] **Step 1: 完了報告を書く**

成功とrollbackの別、全gate、全実測、逸脱、UNKNOWN、陽性対照、開始時と終了時の比較、PR情報を記録する。
秘密情報の本文を書かない。基本多言語面外の文字と四十桁の十六進を書かない。

- [ ] **Step 2: 契約と変更範囲を検証する**

    make task-validate TASK=T-2026-08-13-hub-deploy-lecun-marker-cutover
    make spec-check TASK=T-2026-08-13-hub-deploy-lecun-marker-cutover
    make forbidden-check TASK=T-2026-08-13-hub-deploy-lecun-marker-cutover
    make taskindex && make inbox
    make taskindex-check && make inbox-check

WARN、spec-check該当、forbidden違反、投影検査失敗のいずれかがあれば直し、再実行する。

- [ ] **Step 3: commitして分岐を送出しPRを作る**

    git add tasks/T-2026-08-13-hub-deploy-lecun-marker-cutover/ tasks/inbox.d/T-2026-08-13-hub-deploy-lecun-marker-cutover.md context/auto/ tasks/inbox.md
    git commit -m 'ops(sync): cut over lecun to markerless hub keeper'
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --state open --json number,isDraft,state,baseRefName,headRefName
    command -v gh && gh pr create --base phase0 --fill || echo 'gh不在または既存PR。push結果を報告する'

既存PRがあれば二本目を作らず、番号を報告する。本契約内ではPRをphase0へ取り込まない。

- [ ] **Step 4: 同期抑止を解除する**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-13-hub-deploy-lecun-marker-cutover
    test ! -e .sync-pause
    test -e /tmp/.sync-pause.released.T-2026-08-13-hub-deploy-lecun-marker-cutover

- [ ] **Step 5: 台帳へ返送する**

    make task-report TASK=T-2026-08-13-hub-deploy-lecun-marker-cutover

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 19 | 契約検証 | validateとspec-checkとforbiddenが全て成功 | 各道具の対象taskと検査件数を出力で確認 |
| 20 | 投影 | 二つの生成と二つの検査が成功 | 生成前の状態またはchanged件数と生成後の検査を突き合わせる |
| 21 | 変更範囲 | forbidden-check成功 | changed件数とchecked件数が非零で対象pathが表示されることを確認 |
| 22 | 分岐送出 | upstream設定済み、originとの差が零 | statusとrev-listを別々に確認 |
| 23 | PR | 番号、Draft、base、headを報告 | PR一覧のheadと現在分岐を突き合わせる |
| 24 | 抑止解除 | repo直下に無く、退避先にある | 不在と実在の二つのtestを別々に実行 |
| 25 | 台帳返送 | exit 0、bytes、verdictを出力 | Notion返送出力のtask IDが本契約と一致することを確認 |

## 想定外の扱い

| 事象 | 対応 |
|---|---|
| PR 100 がphase0に無い | hostを変更せず停止し、先にPR 100を取り込むよう報告 |
| 開始時状態が停止報告から変わった | 変更前に停止し、差分を実測で報告 |
| backup pathが既に存在する | 上書きせず停止。由来を確認する |
| TERMで旧PIDが消えない | KILLを使わず停止し、判断を仰ぐ |
| 新keeperが複数またはlockを取らない | 数値PID一件ずつを再同定してrollback。広域停止は使わない |
| markerまたは中継が現れる | 即rollbackし、どの条件が成立したかを報告 |
| Syncthingが変化する | Syncthingへ信号を送らずkeeperとmarkerだけrollbackする |
| pushまたはPR作成だけが失敗 | 中心稼働をrollbackしない。同期抑止を残し、記録経路の復旧を報告 |
| task-reportだけが失敗 | 中心稼働をrollbackしない。分岐とPRを保持し、返送再試行を次の判断へ上げる |

事実と未測定を分ける。成功条件を満たさないのに `pass` と書かない。

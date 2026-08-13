# bengio を lecun 中心へ切り替える最初の一般ノード canary

**task_id:** `T-2026-08-13-bengio-canary-lecun-cutover`  **kind:** `impl`
**実行ホスト:** `bengio`  **repo:** `~/slocal2/m2`

## Goal

lecun は marker 無しの正本 keeper、22000 LISTEN、SSH中継無しで中心稼働を開始した。
本契約は一般ノードを一台だけ変更する。bengio の旧philip向けmarkerと中継を、登録済みの
対別鍵を使うlecun向け経路へ可逆的に切り替える。他の一般ノードには触れない。

重要な補足がある。bengioの旧Syncthing設定では `tcp://127.0.0.1:22001` はphilip deviceに
属し、lecun deviceは `tcp://192.168.196.176:22000` だけを持つ。SSH中継の転送先だけを
lecunへ変えるとdevice IDが対応しない。したがって中継が止まっている間に、Syncthingの
granular REST APIでlocalhost addressをphilipからlecunへ一件だけ移す。Syncthing自体は
停止も再起動もしない。失敗すればbengio一台だけを開始時状態へ戻す。

## 0. 許可、禁止、開始条件

### 起動直後

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && git fetch origin && git branch --show-current && grep -c sync-pause ~/bin/m2-sync.sh && git merge-base --is-ancestor origin/phase0 HEAD

- 分岐は `feat/bengio-canary-lecun-cutover` だけを許す。
- sync-pauseの件数が零、またはmerge-baseが非零なら変更前に停止する。
- `.sync-pause` は最終記録とpushが終わるまで残す。

### 許可する副作用

| # | 許可 |
|---|---|
| 1 | bengioのkeeper、全marker、Syncthing設定の契約専用backup作成と必要時の復旧 |
| 2 | bengioの正本keeper配置、旧marker退避、新marker一件のatomic配置 |
| 3 | 再同定した旧keeperと旧SSH中継の各数値PID一件へのTERM |
| 4 | bengioのphilipとlecunのSyncthing device addressだけをREST APIで置換・復旧 |
| 5 | 正本keeperの一回起動と、失敗時の新keeper・新中継の数値PIDへのTERM |
| 6 | 二方向の小さな契約専用pt probeをbengioとlecunのm2 rootへ各一件作成して保持 |
| 7 | 契約ディレクトリ、専用受け皿、生成物、分岐push、PR、台帳返送 |

### 禁止事項

| # | 禁止 |
|---|---|
| 1 | bengio以外の一般ノードで命令を実行する。lecunでは中心の読み取りとprobe一件の作成以外を行う |
| 2 | 秘密鍵、API key、token、authorized_keys本文、config.xml本文を表示・repoへ保存する |
| 3 | 数値PID一件へのTERM以外でprocessを止める。広域停止、KILL、Syncthing再起動を使わない |
| 4 | 正本keeperとm2-syncを変更する。keeper、marker、二device address以外のhost設定を変更する |
| 5 | known_hosts、authorized_keys、folder、device ID、共有設定、ignore、実験、data、splitを変更する |
| 6 | probeを削除する。保持名を結果へ記録し、削除は別契約にする |
| 7 | runindexとcontext/autoを手で編集する。生成器による生成だけを許す |
| 8 | 自動統合を有効化する、本作業PRをphase0へ取り込む、未測定値を断定する |

### 変更前にユーザーへ確認する一問

読み取りpreflight後、host変更の直前に「bengioのlocal consoleまたはSSHとは独立した復旧経路を
現在保持しているか」を尋ねる。ユーザーの明示的な肯定を `canary-audit.md` に一行で記録する。
肯定が無い、曖昧、session断で回答を保持できない場合は変更せず停止する。

## Phase A — 読み取りpreflight

### A1. 補助器を作り、空振りを検出する

`canary_probe.py` は `/proc` から自分と祖先を除き、keeper、Syncthing、SSH local forwardの
PID、PPID、start tick、cmdline、FD9 lock、FD255要約値をJSONで出す。`/proc/net/tcp*`から
22000、22001、8384を復号し、markerを先頭ドット込みで列挙する。

`center_probe.py` は固定したSSH argvを使い、bengioからlecunへread-only Pythonをstdinで送り、
marker件数、keeper件数・lock・FD、Syncthing件数、22000をJSONで得る。接続はBatchMode、
StrictHostKeyChecking=yes、ClearAllForwardings=yes、port 50072を必須とする。

両器にself-testを作る。存在するkeeper・22000と不存在語・22001、競合lockと解放lock、
正しいdevice対応と重複localhostを区別する。全項目PASSまでhost変更へ進まない。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/canary_probe.py --self-test

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | processとlistener | 実在keeperと22000を検出し、不存在語と22001を零件として区別 | fixtureの存在と不存在を同じ走査へ与える |
| 2 | lock | 稼働keeperでは取得不可、解放fixtureでは取得可 | 一時lockを保持・解放して結果が反転する |
| 3 | device route | localhostがphilipだけなら旧状態、lecunだけなら新状態 | 重複と両方欠落fixtureをFAILにする |
| 4 | 秘匿 | helper出力にAPI keyと鍵本文が無い | 囮secretは検査が一件を返し、通常出力は零件 |

### A2. bengioとlecunの開始状態を固定する

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/canary_probe.py --label before | tee tasks/T-2026-08-13-bengio-canary-lecun-cutover/canary-audit.md

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/center_probe.py --label center-before | tee -a tasks/T-2026-08-13-bengio-canary-lecun-cutover/canary-audit.md

変更前の必須条件は次のとおり。

- lecunはmarker零、keeper一件、FD9 lock保持、Syncthing稼働、22000 LISTEN。
- bengioはkeeper一件、Syncthing稼働、22000と8384 LISTEN、markerは旧philip向け一件だけ。
- SSH中継は零件または一件。二件以上、意味不明なmarker、keeper複数なら停止する。
- known_hosts、authorized_keys、config.xmlのmode、bytes、SHA-256を本文を出さず記録する。

### A3. 鍵、認証、Syncthing mappingを再測定する

秘密鍵から公開鍵をpipeで導出し、指紋だけを得る。`id_rsa_bengiotolecun`という名前から鍵種別を
推定しない。現指紋が過去のbengio監査とlecun登録監査の同じ指紋に各一件一致することを確認する。
次にその鍵でlecunへread-only SSH認証し、remote authorized_keysの指紋一覧に一件一致することを
確認する。本文は取得しない。known_hostsが未登録なら書き足さず停止する。

`syncthing_route.py --inspect` はconfig.xmlからAPI keyをmemory内だけで読み、RESTでversion、
philipとlecunのdevice object、restart-required、connectionsを取得する。次を全て要求する。

- Syncthingはgranular config endpoint対応版である。
- device nameはphilipとlecunが各一件で、device IDを記録できる。
- `tcp://127.0.0.1:22001` は全device中一件だけでphilipに属する。
- lecunは `tcp://192.168.196.176:22000` を一件持つ。
- global announceとrelayは無効のまま。folderと共有device集合を開始時記録する。

ここまでを満たし、独立復旧経路の肯定を得た時だけG1をpassとする。

## Phase B — 控え、staging、rollback入力

backupは `/home/ubuntu/.hub-migration-backup.T-2026-08-13-bengio-canary-lecun-cutover`、mode 700とする。
keeper、全marker、config.xmlをmode込みで保存する。config.xmlはAPI keyを含むためmode 600で
backup内だけに置き、本文をauditやrepoへ出さない。philipとlecunのGET device JSONもmode 600で
保存し、secret fieldが無いことを確認する。

正本keeperは次で固定pathへ展開する。前契約で誤った`--output`は使わない。

    cd ~/slocal2/m2 && git cat-file blob origin/phase0:scripts/sync/keeper.sh | install -m 755 /dev/stdin /tmp/keeper.T-2026-08-13-bengio-canary-lecun-cutover && test -s /tmp/keeper.T-2026-08-13-bengio-canary-lecun-cutover

Git blob、staging、作業ツリー正本をcmpとSHA-256で三者照合し、stagingをmode 755にする。
新marker stagingはbackup内のglob非一致名に作り、1行目を照合済み鍵の絶対path、2行目を
`192.168.196.176`、mode 600とする。表示はpath、行数、mode、要約値だけにする。

`rollback_canary.py` は保存済みstateと数値PIDだけを使い、新keeper・新中継停止、二device object
復旧、新marker退避、旧marker・旧keeper復旧、旧keeper一回起動を順に行う。temporary fixtureと
fake RESTでdry self-testし、対象外pathとPIDを拒否する。実hostではまだrollbackを実行しない。

## Phase C — 一体切替

C以後のどの判定が失敗しても、他の操作へ進まず直ちに`rollback_canary.py`を実行する。
rollbackも失敗したら追加操作をせずescalateする。

1. 旧keeperを開始時PIDとcmdlineで再同定し、その数値PIDだけへTERMを送る。
2. PID消滅とlock解放を期限付きで確認する。消えなければKILLせず停止する。
3. 旧SSH中継が一件なら開始時PIDとcmdlineを再同定してTERM、零件なら零件を記録する。
4. local 22001がLISTENしていないことを確認する。
5. 旧markerをbackupへ移し、正本keeperをatomic配置する。
6. RESTでphilip deviceからlocalhost addressだけを除き、lecun deviceへ一件追加する。
7. GETで二objectの他field不変、localhost一件、所属lecun、restart-required=falseを確認する。
8. 新marker stagingを `/home/ubuntu/.tunnel_to_lecun` へatomic配置する。
9. `launch_keeper.py`で固定pathの正本keeperを一回だけ新session起動する。引数は拒否する。

## Phase D — 初期成功と双方向probe

変更後snapshotで次を全て満たす。

- keeper一件、PPID 1、FD9 lock、FD255正本一致。旧keeper PIDは不存在。
- markerは `.tunnel_to_lecun` 一件、2行、mode 600。旧philip markerはhome零件。
- SSH中継一件のargvはlocal 22001、remote 127.0.0.1:22000、port 50072、接続先lecunだけを持つ。
- 22001 LISTEN一件。旧philip接続先を持つprocessは零件。
- Syncthing PID、start tick、件数、22000、8384は開始時と一致し、restart-required=false。
- REST connectionsでlecun deviceがconnected、観測addressがlocalhost 22001。philipは同addressを使わない。
- known_hostsとauthorized_keysは開始時SHA-256不変。config変更は二device addressだけ。

probe名はrandom nonceを含め、両hostで不存在を確認してから作る。`git check-ignore -v`がpt規則を
返し、`.stignore`のpt許可と末尾ignoreを記録する。bengioからlecun、別名でlecunからbengioへ
各一件を作り、各方向五分以内にpath、bytes、SHA-256一致を確認する。同時刻のlecun device接続先を
記録する。probeは削除しない。

## Phase E — 一周期の安定性

初期成功snapshotから一八〇〇秒以上を、三十秒以下のpollで待つ。単一の長いsleepに依存しない。
待機中にkeeper、中継、Syncthing、22001、lecun device接続のいずれかが外れたら即rollbackする。
終了snapshotでPID、start tick、FD、lock、marker、二device address、接続先、二probeの要約値を
再取得する。m2-syncの「一時停止中」記録が少なくとも一回増え、repoへ自動書込みが無いことも示す。

## Phase F — 記録、送出、台帳

`RESULT.md`と`result.yaml`は開始時、変更、二snapshot、probe、rollback未実施または実施結果を
対応づける。主要判定にはbreaking inputとobservedを置く。起票者の誤りと逸脱を空にしない。

    cd ~/slocal2/m2 && source .venv/bin/activate && make task-validate TASK=T-2026-08-13-bengio-canary-lecun-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && make spec-check TASK=T-2026-08-13-bengio-canary-lecun-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && make forbidden-check

    cd ~/slocal2/m2 && source .venv/bin/activate && make taskindex && make inbox && make taskindex-check && make inbox-check

生成物を含む契約範囲だけをcommitする。`git merge`は行わない。push後、同じheadの既存PRを調べ、
無ければ非Draft PRをphase0向けに作る。PR番号、base、head、upstream、aheadを結果へ記録して再commitし、
pushする。repo直下のpauseを契約専用の`/tmp`名へ移し、不存在と移動先実在を記録する。

    cd ~/slocal2/m2 && source scripts/load_env.sh && make task-report TASK=T-2026-08-13-bengio-canary-lecun-cutover

台帳返送が失敗してもcanaryをrollbackしない。失敗事実と再送条件を報告する。PRは取り込まない。

## 想定外とrollback

| 事象 | 対応 |
|---|---|
| G1またはG2不成立 | hostを変更せずstoppedで報告 |
| TERMでPIDが消えない | 強い信号を送らず、変更済みならrollback |
| REST変更またはrestart-required | 二device objectを復旧し、全体rollback |
| 新中継、device接続、probe不成立 | bengioだけを全体rollback。次ノードへ進まない |
| 一周期内にprocessまたは接続が変化 | 即時rollbackし、最初の逸脱時刻を記録 |
| rollback不成立 | 追加操作を止め、local consoleからの復旧をユーザーへescalate |

成功でも失敗でも、事実と未測定を分ける。pass条件を一つでも満たさなければpassと書かない。

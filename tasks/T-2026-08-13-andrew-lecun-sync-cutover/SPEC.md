# andrewを優先してlecun中心のSyncthing一般ノードとして稼働させる

**task_id:** `T-2026-08-13-andrew-lecun-sync-cutover`  **kind:** `impl`
**depends_on:** `T-2026-08-12-register-hub-keys`, `T-2026-08-13-hub-deploy-lecun-marker-cutover`
**実行ホスト:** `Andrew`  **repo:** `~/slocal2/m2`

## Goal

最優先は五台のSyncthing稼働であり、本契約ではandrew一台をlecun中心へ接続する。
zmxはSyncthingの構成要素ではない。本契約の開始条件、process計数、成功判定にhost全体の
zmx件数を入れず、zmx、sshd、PID一へsignalを送らない。
andrewでは過去監査時点でSyncthingが稼働していたが、旧philip向けmarkerだけがあり、
中継とlocalhost中継口は停止していた。中継鍵の公開鍵はlecunへ登録済みだが、登録後の
andrewからlecunへの正方向認証は未測定である。lecunはmarker無しの中心として稼働済みである。
これらは過去の事実であり、現在値を断定しない。変更前に現在状態を再測定し、旧状態なら
可逆切替を行う。すでに目標状態ならhost変更を重ねず、双方向probeと安定性だけを実施する。
どちらにも分類できない混在状態では変更せず停止する。

## 0. 開始条件、許可、禁止

### 起動直後

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && git fetch origin && git branch --show-current && grep -c sync-pause ~/bin/m2-sync.sh && git merge-base --is-ancestor origin/phase0 HEAD

- 分岐は `feat/andrew-lecun-sync-cutover` だけを許す。
- `.sync-pause` がrepo直下にあり、常駐処理が抑止へ対応し、phase0から分岐していることを確認する。
- 依存二taskのRESULTとresultがphase0に無ければhostへ触れず停止する。
- 開始時に契約ディレクトリ以外の未commit変更があればhostへ触れず停止する。

### 許可する副作用

1. andrewの契約専用backup、state、lease、event、lock、rollback guardを作る。
2. andrewの局所差分候補を内容付きでbackupし、一覧と要約値だけをrepoへ記録する。
3. 再同定した旧keeperと旧SSH中継の数値PID一件ずつへTERMを送る。
4. 旧markerをbackupへ移し、新markerをatomic配置する。
5. known_hostsへlecunのホスト鍵を零件または一件だけ追加し、rollback時は開始時へ戻す。
6. philipとlecunの二device addressだけをgranular RESTで変更または復旧する。
7. phase0の正本keeperをatomic配置して一回起動する。
8. andrewとlecunへ契約専用probeを各一件作り、成功後も保持する。
9. 契約成果物、生成物、分岐push、PR作成、台帳返送を行う。

### 禁止事項

1. zmx、sshd、PID一、port mapping、firewall、route、DNS、authorized_keysを変更またはsignal対象にしない。
2. systemd、cron、at、profileへguardを登録せず、package追加やhost再起動をしない。
3. 秘密鍵、API key、token、authorized_keys本文、config.xml本文を表示またはrepoへ保存しない。
4. 数値PID一件へのTERM以外でprocessを止めない。KILL、pkill、killall、広域停止を使わない。
5. Syncthingを停止または再起動せず、folder、device ID、共有、ignoreを変更しない。
6. andrew以外の一般ノードを変更しない。lecunでは中心の読み取りとprobe一件の作成だけを許す。
7. probeと局所差分backupを削除しない。runindexとcontext/autoは生成器だけで更新する。
8. 自動統合、本作業PRのphase0取り込み、未測定値の断定を行わない。pushは統合に含めない。

## Phase A — 読み取りpreflight

### A1. 依存とhelperを固定する

依存taskのRESULTとresult、現在のphase0 object、正本keeperを照合する。不在task objectを
陰性対照にし、正しいobjectだけが存在することを確かめる。bengio canaryの既存helperは
検証済みの出発点として読み、andrew専用の固定path、鍵、host名へ変更したコピーを本task内に作る。
元helperは変更しない。

`andrew_probe.py` は `/proc` から自分と祖先を除き、keeper、Syncthing、SSH local forwardの
PID、PPID、start tick、cmdline、FD九lock、FD二百五十五要約値を得る。process検索に
`pgrep -f`、`ps`と`grep`の組合せを使わない。listenerは `/proc/net/tcp` と
`/proc/net/tcp6`から復号する。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 依存object | 二依存と正本keeperがphase0にある | 不存在task objectは非零になる |
| 2 | process走査 | keeperとSyncthingを分類し、旧中継と新中継を区別する | fixtureへ各processと不存在語を与える |
| 3 | listener走査 | 同期待受、localhost中継口、管理口を区別する | 開いたfixtureと閉じたfixtureで反転する |
| 4 | lockと配置 | keeperのlockと実行中script要約を得る | 保持lockと解放lockで結果が反転する |
| 5 | 秘匿 | snapshotに鍵本文とAPI keyがない | 囮secretは一件、通常出力は零件になる |

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && python tasks/T-2026-08-13-andrew-lecun-sync-cutover/andrew_probe.py --self-test

### A2. andrewからlecunへの鍵認証を初めて正方向で確定する

鍵は `/home/ubuntu/.ssh/id_ed25519_andrewtophilip` を使う。名前は旧中心を含むが、過去に導出した
公開鍵指紋とlecun登録結果が同じであることが選択根拠である。秘密鍵本文は読まない。

一時known_hostsを契約専用backup内に作り、BatchMode、IdentitiesOnly、ClearAllForwardings、
接続時間制限、port五〇〇七二、中心住所 `192.168.196.176` を固定する。最初は
StrictHostKeyCheckingの追加許可を一時known_hostsだけへ適用し、二回目はstrict確認に変える。
remoteで実行するのは固定文字列を返す命令と中心probeだけにする。通常known_hostsは前後の
mode、bytes、mtime、SHA-256一致で無変更を証明する。

`center_probe.py` はlecunのmarker零、keeper一件、FD九lock保持、Syncthing稼働、同期待受開、
localhost中継口閉、SSH local forward零件をsecret-safe JSONで返す。既存のbengio版から鍵path
だけを置換したとみなさず、self-testとlive結果の両方を取得する。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 鍵指紋 | 過去のandrew提出とlecun登録結果に一致する | 別の手元鍵は不一致になる |
| 2 | 正方向認証 | strictな二回目接続で固定文字列を一回得る | 認証無しfixtureまたは誤鍵は非零になる |
| 3 | 通常known_hosts | 読み取りpreflight前後で不変 | 一時known_hostsだけが零から増える |
| 4 | lecun中心 | marker無し、keeper施錠、Syncthingと同期待受が稼働 | 不正markerと閉じた待受fixtureを拒否する |

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && python tasks/T-2026-08-13-andrew-lecun-sync-cutover/center_probe.py --self-test

### A3. andrewの現在状態とSyncthing routeを分類する

`syncthing_route.py` は既存helperをtask内へ複製し、RESTからphilipとlecunのdevice objectだけを
取得する。API keyはmemory内だけで使う。保存するのはdevice ID、name、addresses、paused、
object要約、address以外の要約、version、restart-required、接続状態、folder要約である。

旧状態は旧philip marker一件、新marker零件、lecun向け中継零件、localhost中継口閉、
localhost addressがphilip deviceだけ、lecun direct addressが一件、restart不要とする。
既達成状態は新lecun marker一件、旧marker零件、lecun向け中継一件、localhost中継口開、
localhost addressがlecun deviceだけ、lecun device接続、restart不要とする。

keeper複数、marker複数、localhost address重複または欠落、想定外device、restart必要、
Syncthing不在、旧状態と既達成状態の混在ではG一をstopとする。

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && python tasks/T-2026-08-13-andrew-lecun-sync-cutover/syncthing_route.py --self-test

### A4. 再接続前にandrew固有差分を保護する

過去inventoryと現在inventoryをpath、type、bytes、要約値で集合差比較する。過去停止後に追加または
変更されたandrew側の通常ファイルを候補として列挙し、内容を契約専用backupへcopyする。
backup本文はrepoへ入れず、repoにはpath、type、bytes、mode、mtime、SHA-256だけを記録する。

過去監査で固有差分はsync-alerts.log一件、版退避は零件だった。これは現在値ではない。
現在の候補集合を異質な方法で再構成し、候補零件なら過去inventory総件数と現在総件数、Git差分、
mtime分布を突き合わせる。必要容量と空き容量を測り、完全copyと要約一致前に切替へ進まない。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | inventory集合 | 過去と現在の全対象を縮めず比較する | 各pathが実在対象の定義を満たすか別走査で見る |
| 2 | 差分候補 | 追加、変更、消失を別集合で記録する | 既知のsync-alerts変化を検出できることを確認する |
| 3 | 局所backup | 全候補copyが元とbytes、mode、SHA-256一致 | 囮copyを一byte変えると不一致になる |
| 4 | 容量 | 必要容量より空き容量が大きい | 容量不足fixtureを拒否する |

ここまでの全表を満たし、旧状態または既達成状態の一方だけに分類できた場合にG一をpassとする。

## Phase B — backupとscoped rollback guard

### B1. live開始状態を封印する

backup rootは `/home/ubuntu/.hub-migration-backup.T-2026-08-13-andrew-lecun-sync-cutover`、mode七〇〇。
keeper、全marker、known_hosts、config.xml、philipとlecunのdevice object、開始snapshot、局所差分copyを
保存する。秘密を含むbackupはmode六〇〇とし、本文や要約前のdevice objectをrepoへ入れない。

stateにはtask ID、固定target path、backup path、各mode、bytes、SHA-256、開始PIDとstart tick、
開始route classを持たせる。backup root外、task ID不一致、要約不一致、PID一を拒否する。

### B2. guardをisolated fixtureで実証する

`rollback_guard.py` と `guarded_cutover.py` を作る。guardは本taskが起動した固定PIDとstart tick、
封印state、lease、commit token、lockだけを見る。host全体のzmx件数を読まず、zmx、sshd、PID一、
他task processをsignal対象にもrollback対象にも入れない。

guardは新しいsessionで起動し、readyとarmedをatomic fileで返す。live変更より前に両方とguardの
PID、start tick、lockを確認する。lease失効、owner消失、live predicate失敗、commit token無しでは
rollbackを一回だけ行う。正しいcommit token後はrollbackせず終了する。二重guardはlockで拒否する。

isolated fixtureは一時rootだけを使い、live marker、keeper、known_hosts、Syncthing RESTへ触れない。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | state封印 | task専用pathと全要約が一致する | root外pathと一byte変更を拒否する |
| 2 | lease反転 | 更新中は待ち、失効時はrollback一回 | fixture clockを進めて一回だけ発火させる |
| 3 | owner identity | PIDとstart tick一致だけを有効とする | 同じPIDで異なるtickを拒否する |
| 4 | commit token | 正しいtoken後はrollbackしない | 欠落tokenと誤tokenはrollbackへ進む |
| 5 | scope | task guardとtask stateだけを対象にする | fixtureへzmxとsshdを加えても対象集合が増えない |
| 6 | 二重実行 | 二つ目のguardを拒否する | lock保持中と解放後で結果が反転する |

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && python tasks/T-2026-08-13-andrew-lecun-sync-cutover/rollback_guard.py --self-test

G二はbackup照合と全isolated fixtureが通ったときだけpassとする。

## Phase C — andrewの一体切替

### C1. 既達成状態では変更を重ねない

Phase Aで既達成状態に分類された場合、Phase Cのhost変更をskipし、直前snapshotと同じ状態を
Phase Dで検証する。skipはpassと同義にせず、変更不要だった根拠をRESULTへ記録する。

### C2. 旧状態だけをguarded transactionで切り替える

guardのreadyとarmed後、次の順序を一つのtransactionとして実行する。

1. 直前snapshotを取り、封印stateから変化がないことを確認する。
2. 再同定した旧keeperと旧中継だけへ数値PID一件ずつTERMを送り、消滅とlock解放を待つ。
3. 通常known_hostsのbackup後、固定SSH argvでlecun host keyを零件または一件だけ登録する。
4. `syncthing_route.py` でlocalhost addressをphilipからlecunへ一件だけ移す。
5. 旧markerをbackupへatomic移動し、二行の `.tunnel_to_lecun` をatomic配置する。
6. phase0の `scripts/sync/keeper.sh` objectを取得し、要約一致、mode七五五でatomic配置する。
7. 固定pathのkeeperを新しいsessionで一回起動する。
8. marker一件、keeper一件とlock、lecun中継一件、localhost中継口開を待つ。
9. routeがlecunだけ、lecun device接続、旧philip中継零件、restart不要を確認する。
10. SyncthingのPIDとstart tick、二deviceのaddress以外の要約、folder要約が開始時と一致することを確認する。

markerの一行目は既存鍵path、二行目は `192.168.196.176` とする。marker本文をrepoへ保存しない。
Git objectの展開に `git show --output` を使わない。取得、atomic write、chmod、cmpを独立に検査し、
途中失敗を後続成功で隠さない。

各Stepの失敗、lease停止、transaction消失、live predicate失敗ではguardがandrew一台だけを開始時へ
戻す。復旧対象は二device、marker、keeper、known_hostsであり、Syncthingは再起動しない。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | signal範囲 | 再同定したkeeperと旧中継の数値PIDだけ | PID一と別cmdline fixtureを拒否する |
| 2 | marker | lecun向け一件だけで二行が有効 | 旧新重複と空行を拒否する |
| 3 | route | localhost addressはlecunだけに一件 | philipだけ、重複、欠落を別分類する |
| 4 | keeper | phase0正本一件がFD九lockを保持 | 旧blob不一致と解放lockを拒否する |
| 5 | tunnel | lecun向け一件、旧philip向け零件 | 旧向けと複数向けをFAILにする |
| 6 | Syncthing不変 | PID、start tick、非address要約、folder要約が一致 | 開始snapshotを先に固定して比較する |
| 7 | known_hosts | lecun分だけ零件または一件増え他は不変 | backupとの差をhost key単位で突き合わせる |

G三を満たさなければcommit tokenを作らず、rollback完了後の開始状態を再測定してstopする。

## Phase D — データ面と一周期安定性

### D1. 二方向probeを作って保持する

両folderの実pathとignore適用をRESTと設定から確認し、同期対象でignoreされない契約専用pathを選ぶ。
andrewでprobe Aを作成し、lecunで同じpath、bytes、SHA-256へ到達するまで待つ。次にlecunでprobe Bを
作成し、andrewへ同じpath、bytes、SHA-256で到達するまで待つ。両probeは削除しない。

probe名、作成側、到達側、作成時刻、到達時刻、bytes、SHA-256を記録する。内容は非secretの
task IDとrandom payloadとし、作成前に同名不存在を確かめる。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | andrewからlecun | probe Aが同じbytesとSHA-256で到達 | 到達前の不存在を先に記録する |
| 2 | lecunからandrew | probe Bが同じbytesとSHA-256で到達 | 到達前の不存在を先に記録する |
| 3 | 対象folder | REST共有と実pathとignoreが一致する | 別folderの不存在pathを陰性対照にする |
| 4 | 接続先 | lecun deviceがlocalhost経由でconnected | philip deviceと接続addressを別に記録する |

### D2. keeper一周期後も同じ状態を確認する

最初の成功snapshot後、keeperの一周期以上を壁時計と単調時計の両方で隔てる。待機中もguard leaseを
更新する。二回目snapshotでmarker、keeper PIDとstart tick、FD九lock、中継PIDとstart tick、
Syncthing PIDとstart tick、listener、route、connection、probe二件、restart不要を比較する。

keeperと中継は正本keeperの周期動作で再生成されていなければ同じidentityを要求する。正当な再接続で
中継identityが変わった場合は原因をログ時刻とconnection履歴で実測し、安定稼働とは断定せずstopする。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 観測間隔 | 一周期以上を二時計で確認する | 開始時刻を先に固定して差を求める |
| 2 | role維持 | marker、keeper、lock、中継、listener、routeが成功状態 | 開始成功snapshotと項目ごとに比較する |
| 3 | process維持 | SyncthingのPIDとstart tickが同じ | 開始前identityを先に記録する |
| 4 | data維持 | probe二件が両端で同じbytesとSHA-256 | 二つのpathを相互に突き合わせる |
| 5 | 旧経路消失 | philip向けmarker、中継、localhost addressが零件 | 新lecun経路が非零であることも同時確認する |

全項目成功後だけcommit tokenをatomic作成する。guardがtokenを検証して正常終了し、lockとguard processが
消えたことを確認する。backupとprobeは保持する。G四をpassとする。

## Phase E — 検証、送出、台帳返送

### E1. 結果を記録する

`RESULT.md` と `result.yaml` に開始分類、認証、中心状態、局所差分backup、guard self-test、切替または
skip、二方向probe、一周期snapshot、rollback有無、残余リスクを記録する。測れない外側port mappingや
host停止時のrollback可否はUNKNOWNとする。成功時もhost停止、kernel停止、storage障害、guardとの
同時消失を保護済みと書かない。

### E2. 契約検査と禁止領域検査を行う

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && make task-validate TASK=T-2026-08-13-andrew-lecun-sync-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && make spec-check TASK=T-2026-08-13-andrew-lecun-sync-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && make forbidden-check TASK=T-2026-08-13-andrew-lecun-sync-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && make taskindex && make inbox && make taskindex-check && make inbox-check

全命令のexit code、PASS、WARN、SKIP、FAIL、findingを省略せず記録する。WARNまたはfindingがあれば
黙って続けず、host最終状態を保ったまま起票者へ報告する。

### E3. 分岐を送出し、非Draft PRを作る

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && git status --short && git push -u origin HEAD && gh pr list --head "$(git branch --show-current)" --json number,isDraft,state,baseRefName,headRefName

同じheadとbaseのPRを先に一覧で調べる。あれば二本目を作らず本文を更新する。無ければbase `phase0` の
非Draft PRを作る。pushは統合に含めない。本作業PRをphase0へ取り込まない。

### E4. 台帳返送後に同期抑止を解除する

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && make task-report TASK=T-2026-08-13-andrew-lecun-sync-cutover

台帳返送成功、clean tree、upstream、remoteとの差、PR番号を確認した後、repo直下の `.sync-pause` を
契約専用 `/tmp` pathへ移す。削除しない。解除後に常駐処理が再開した事実をsync-alertsの増分で確認する。
最終記録をcommit、pushし、台帳の同一報告blockを最終版へ置換する。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | task検証 | task-validateが一task、失敗零件 | 対象task IDと検査件数を突き合わせる |
| 2 | spec検査 | 全規則finding零件 | 規則数と対象pathを出力で確認する |
| 3 | 禁止領域 | forbidden-checkが違反零件 | changed、checked、excludedの件数を出す |
| 4 | 投影 | taskindexとinboxの生成後checkが成功 | 生成前後と対象taskの掲載を確認する |
| 5 | host最終状態 | lecun接続または完全rollbackの一方だけ | marker、route、中継を異なるprobeで突き合わせる |
| 6 | guard終了 | commit後はguardとlockが零件 | armed時の非零を先に測ってあること |
| 7 | Syncthing維持 | 開始と終了でPIDとstart tickが同じ | 二snapshotを直接比較する |
| 8 | probe保持 | 二probeが両端で同じbytesとSHA-256 | path一覧と内容要約を別に照合する |
| 9 | 分岐送出 | upstream設定済み、remote比ahead零 | statusとupstreamを別に確認する |
| 10 | PR | 番号、非Draft、base、headを報告 | PR一覧と現在headを突き合わせる |
| 11 | 台帳返送 | verdict、bytes、起票者欠陥数を記録 | make終了コードと台帳行を照合する |
| 12 | 同期抑止解除 | repo直下零件、契約専用退避先一件 | 両pathを別々に確認する |
| 13 | clean tree | 最終push後に未commit変更零件 | git statusとremote差を別に確認する |

## 想定外が起きたときの扱い

- G一前の不一致ではhostを変更せずstoppedとする。
- G二前の不一致ではbackupとisolated fixtureだけを残し、hostを変更せずstoppedとする。
- live変更後の失敗ではcommit tokenを作らず、guardによるrollbackを待つ。
- rollback後は開始stateとの全項目一致を測る。一致しない項目があれば追加変更せずstoppedとする。
- より強いsignal、手動process選択、広域停止、zmx整理、sshd変更が必要なら実施せず別契約へ送る。
- lecunまたは他一般ノードに想定外の変更が必要なら実施せず、andrewの開始状態を保って報告する。

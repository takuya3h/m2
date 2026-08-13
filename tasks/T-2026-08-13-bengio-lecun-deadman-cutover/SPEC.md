# SSH限定のbengioをdead-man rollback付きでlecun中心へ切り替える

**task_id:** `T-2026-08-13-bengio-lecun-deadman-cutover`  **kind:** `impl`
**depends_on:** `T-2026-08-13-bengio-canary-lecun-cutover`
**実行ホスト:** `bengio`  **repo:** `~/slocal2/m2`

## Goal

前契約はPhase Aを通した後、bengioにSSH非依存の復旧経路がないため変更前に正常停止した。
ユーザーはその報告を確認し、選択肢2のremote-only guarded canaryを明示的に選んだ。

本契約は、変更を行う一つのforeground transactionとは別sessionのdead-manを先に武装する。
transactionのPID消失、start tick不一致、lease停止、live判定失敗では、契約専用backupから
bengio一台だけを旧philip状態へ復旧する。全成功条件を一周期維持した場合だけcommit tokenを
確定し、dead-manを解除してlecun状態を残す。

この方式にも限界がある。host電源断、再起動、kernel停止、storage障害、transactionとguardの
同時消失ではrollback process自体が動けない。この残余リスクをユーザーが選択肢2で受け入れた
事実を記録する。成功報告でも、この範囲を保護済みとは書かない。

## 0. 開始条件、許可、禁止

### 起動直後

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && git fetch origin && git branch --show-current && grep -c sync-pause ~/bin/m2-sync.sh && git merge-base --is-ancestor origin/phase0 HEAD

- 分岐は `feat/bengio-lecun-deadman-cutover` だけを許す。
- sync-pauseが零、依存taskがphase0に無い、merge-baseが非零なら変更前に停止する。
- `.sync-pause` は台帳返送と最終pushまで残す。
- 前契約の `stopped` は失敗ではなく、本契約の遠隔限定承認を得るための依存入力である。

### ユーザー判断として固定する事実

| 項目 | 固定内容 |
|---|---|
| 復旧経路 | bengioはSSH接続でしか操作できない |
| 選択 | ユーザーは選択肢2、dead-man付きremote-only canaryを選んだ |
| 保護対象 | transaction消失、lease停止、既知の切替判定失敗 |
| 保護外 | host停止、再起動、kernel停止、storage障害、guardとの同時消失 |

### 許可する副作用

1. bengioの契約専用backup、state、lease、event journal、guard processとlockを作る。
2. 再同定したkeeperとSSH中継の数値PID一件ずつへTERMを送る。
3. keeper、旧marker、新marker、philipとlecunのdevice addressだけを切替または復旧する。
4. bengioとlecunへ契約専用pt probeを各一件作成し、成功後も保持する。
5. 契約成果物、生成物、分岐push、PR、台帳返送を行う。

### 禁止事項

1. sshd、port mapping、firewall、route、DNS、known_hosts、authorized_keysを変更しない。
2. systemd、cron、at、profileへguardを登録しない。packageを追加せず、hostを再起動しない。
3. 秘密鍵、API key、token、authorized_keys本文、config.xml本文を表示またはrepoへ保存しない。
4. 数値PID一件へのTERM以外でprocessを止めない。KILL、pkill、killall、広域停止を使わない。
5. Syncthingを停止または再起動せず、folder、device ID、共有、ignoreを変更しない。
6. bengio以外の一般ノードを変更しない。lecunでは中心の読み取りとprobe作成だけを許す。
7. probeを削除しない。runindexとcontext/autoは生成器だけで更新する。
8. 自動統合、本作業PRのphase0取り込み、未測定値の断定を行わない。pushは統合に含めない。

## Phase A — 遠隔限定preflight

### A1. 依存と開始状態を再固定する

前契約のRESULTとresult対、PR #102のmerge、現在のphase0 objectを照合する。前契約のhelperを
同じGit objectから読み、次を再測定する。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/canary_probe.py --self-test

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/center_probe.py --self-test

lecunはmarker零、keeper一件、FD9 lock保持、Syncthing稼働、22000 LISTENを要求する。bengioは
旧keeper一件、旧philip marker一件、Syncthing同一構成、22000と8384 LISTEN、22001なしを要求する。
localhost addressはphilipだけ、lecun direct addressは一件、restart-requiredはfalseとする。

### A2. 現在のSSH sessionが変更対象から独立していることを測る

`session_probe.py`を作る。自分と祖先のPID、PPID、start tick、comm、secretを除いたcmdline、
sshd process、SSH listener、socket inodeを `/proc` から取得する。fixtureで祖先鎖、PID再利用、
存在listenerと不存在port、secret除去を区別するself-testを置く。

live snapshotでは、現在のtransaction実行元がsshd配下にあり、keeper、Syncthing、outbound tunnelが
祖先でないことを示す。sshd binary、設定、listenerと本契約の変更pathに交差がないことも列挙する。
外側のport mappingはbengio内から断定せずUNKNOWNとする。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 依存と旧状態 | phase0に前契約があり、bengioとlecunが前回と同じrole | 不存在task objectと不正marker fixtureは非零になる |
| 2 | SSH session独立性 | sshd祖先とlistenerを検出し、変更対象processは祖先にいない | fake祖先鎖へkeeperを混ぜるとFAILに反転する |
| 3 | dead-man対象 | owner PIDとstart tickの組を一意に取得できる | 同じPIDで異なるtickのfixtureを拒否する |
| 4 | 秘匿 | snapshotとeventに秘密本文がない | 囮secretは一件を検出し通常出力は零件になる |
| 5 | 残余リスク | 選択肢2と保護外の失敗型をauditへ記録 | host停止を保護済みとするfixtureを拒否する |

全項目を満たした場合だけG1をpassとする。

## Phase B — backupとdead-manの実証

backup rootは `/home/ubuntu/.hub-migration-backup.T-2026-08-13-bengio-lecun-deadman-cutover`、mode 700。
旧keeper、全marker、config.xml、philipとlecunのdevice object、開始snapshotを保存する。秘密を含む
configとdevice JSONはmode 600でbackup内だけに置く。repoへはpath、mode、bytes、SHA-256だけを書く。

正本keeper、新marker、`rollback_deadman.py`、`deadman_guard.py`、`guarded_cutover.py`、REST helperを
backup rootへ固定copyし、Git object、作業tree、copyの要約値を照合する。旧markerは一行の実体を
そのまま控え、二行へ合成しない。新markerだけを鍵pathとlecun addressの二行、mode 600でstagingする。

### B1. dead-man protocol

- stateは固定task_id、許可path、開始PIDとtick、backup digest、旧新process識別子を持ちmode 600で封印し、live中は変更しない。
- transactionは自分のPID、start tick、state digest、nonceをimmutable arm recordへatomic保存する。
- transactionは新processのPIDとtickを別のruntime recordへatomic保存し、五秒以内ごとに連番leaseを更新する。
- guardは別sessionでlockを一件保持し、state digestとarm recordのowner組を検証してreadyを返す。
- transactionがarmedを要求し、guardが同じstate digestでarmedを返した後だけhostを変更する。
- owner消失、tick不一致、三十秒を超えるlease停止でguardがrollback lockを取得する。
- transaction自身の失敗とguardは同じrollback lockを使い、復旧を一回だけ実行する。
- 成功tokenは最終snapshotとstate digestを含み、guardが照合してからdisarmedを記録する。

### B2. 隔離self-test

temporary fixtureとfake rollbackだけを使い、live pathやlive processへ触れず次を実証する。

1. owner消失でrollbackが一回だけ呼ばれる。
2. ownerが生存してもlease停止でrollbackが一回だけ呼ばれる。
3. 正しいcommit tokenではrollbackせずguardが終了する。
4. digest違い、tick違い、古いlease、偽token、二つ目のguardを拒否する。
5. transactionとguardが競合してもrollback lockで一回だけになる。
6. state外path、PID 1、曖昧なprocess一致を拒否する。

Phase Bではlive guardをまだ起動しない。backup照合と隔離self-testの全成功でG2を評価する。
live guardは次Phaseの一つのtransaction自身だけが起動し、そのowner PIDとtickを固定する。

## Phase C — 一つのguarded transactionで切り替える

live変更と安定性観測は、leaseを所有する一つのforeground processから次で開始する。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-lecun-deadman-cutover/guarded_cutover.py --execute

helperは各待機を期限付きpollにし、外部命令にもtimeoutを置く。lease期限を超える単一sleepや無期限待機を
使わない。transactionは最初にlive guardを起動し、readyとarmedの往復、guard PIDとtick、state digest、
lock保持、event追記を確認する。handshake不成立ならguardの数値PIDへTERMし、host変更なしを再測定して
停止する。handshake成立後のhost変更は次の順序だけを許す。

1. armed guardのPID、tick、state digest、lockを再確認する。
2. 旧keeperと旧SSH中継を開始snapshotのPID、tick、cmdlineで再同定し、各数値PIDへTERMする。
3. PID消滅、lock解放、22001閉を確認する。消えなければ強いsignalを使わずrollbackへ進む。
4. 旧markerをbackupへ移し、正本keeperをatomic配置する。
5. RESTでlocalhost addressだけをphilipからlecunへ移し、他field不変とrestart-required=falseを確認する。
6. 新markerをatomic配置し、正本keeperを一回だけ起動する。直後にPIDとtickをruntime recordへatomic記録する。
7. runtime記録前にprocessが消えても、rollbackはFD255 SHAと固定argvから一件だけ再同定する。

初期snapshotでkeeper一件、FD9 lock、新marker一件、lecun向けSSH中継一件、22001 LISTEN、lecun deviceの
localhost接続、旧philip経路零を確認する。Syncthing PIDとtick、22000、8384、sshd、authorized_keys、
known_hostsは開始時と同じとする。満たさなければtransactionがrollback lockを取り、guardと競合せず復旧する。

## Phase D — 双方向probeと一周期観測

同じtransaction processを維持し、leaseを更新しながらbengioからlecun、lecunからbengioへ別名のpt probeを
一件ずつ作る。事前不存在、git check-ignore、bytes、SHA-256、lecun deviceの観測addressを照合する。
probeは削除しない。

初期成功から一八〇〇秒以上、十五秒以下のpollでkeeper、中継、Syncthing、sshd、22001、device接続、probe、
leaseを測る。一件でも外れたら成功tokenを書かずrollbackする。終了snapshotが一致した場合だけcommit tokenを
fsyncし、guardがtokenとstate digestを検証してdisarmed eventを残す。guard PID消滅、guard lock解放、
rollback未実施を確認してG4をpassとする。

SSH sessionが途中で切れてもtransactionが生存してleaseを更新する限り処理を継続してよい。transactionが
消えた場合はguardがrollbackする。host自体が停止した場合はguardも動けないため、結果をUNKNOWNとして扱う。

接続が切れた場合、手動でkeeper、marker、Syncthingを触らない。六十秒以上待って再接続し、同じ作業分岐、
guard event、rollback event、開始状態または成功状態を読み取りだけで確認する。`make task-start`は再実行せず、
既存分岐で次を使って契約を再開し、eventから報告を完成させる。

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && $task T-2026-08-13-bengio-lecun-deadman-cutover

## Phase E — 記録、送出、台帳

`RESULT.md`と`result.yaml`へ開始状態、guard protocol、全event、切替、probe、二snapshot、成功解除または
rollbackを対応づける。owner、guard、旧新processはPIDとtickの組で記録する。起票者欠陥、逸脱、保護外の
failure classを空にしない。秘密本文は含めない。

    cd ~/slocal2/m2 && source .venv/bin/activate && make task-validate TASK=T-2026-08-13-bengio-lecun-deadman-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && make spec-check TASK=T-2026-08-13-bengio-lecun-deadman-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && make forbidden-check

    cd ~/slocal2/m2 && source .venv/bin/activate && make taskindex && make inbox && make taskindex-check && make inbox-check

契約範囲だけをcommitしてpushする。同じheadのPRを先に調べ、無ければ非Draft PRをphase0向けに作る。
番号、base、head、upstream、aheadを結果へ記録して再pushする。本契約でPRを取り込まない。
repo直下のpauseを契約専用のtmp名へ移し、repo不在と移動先実在を確認する。

    cd ~/slocal2/m2 && source scripts/load_env.sh && make task-report TASK=T-2026-08-13-bengio-lecun-deadman-cutover

台帳返送の失敗では成功済みcanaryをrollbackしない。失敗事実と再送条件を報告する。
G4まで満たした場合だけpassとする。dead-manまたはtransactionが旧状態へ正常復旧した場合はstopped、
復旧後状態を測れない場合はUNKNOWNを持つstoppedまたはpartialとして記録する。

## rollback後の必須状態

- localhost addressはphilipだけに一件、lecun direct addressは開始時どおり。
- 旧markerは開始時bytes、mode、SHA-256で復旧し、新markerはhomeにない。
- 旧keeperは開始時bytes、mode、SHA-256で復旧し、一件だけがFD9 lockを持つ。
- 新keeperとlecun中継は一意に再同定した数値PIDへTERM済み。
- Syncthing PIDとtick、sshd、known_hosts、authorized_keysは開始時と同じ。
- rollback eventは一件、guardとtransactionの両方が二重実行していない。

rollback不能、guard state破損、process再同定不能では追加操作を止める。SSHが残っていれば測定だけを行い、
host停止またはSSH消失では復旧済みと断定せずUNKNOWNとしてユーザーへescalateする。

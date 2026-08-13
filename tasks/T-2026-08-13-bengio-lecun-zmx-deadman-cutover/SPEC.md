# zmx再親化を検証してbengioをdead-man付きでlecun中心へ切り替える

**task_id:** `T-2026-08-13-bengio-lecun-zmx-deadman-cutover`  **kind:** `impl`
**depends_on:** `T-2026-08-13-bengio-lecun-deadman-cutover`
**実行ホスト:** `bengio`  **repo:** `~/slocal2/m2`

## Goal

前契約はhost変更前のG1で正常停止した。実測されたlive transactionの祖先は、子から親の順に
`python`, `Codex`, `zsh`, `zmx`, `PID 1 sshd listener` だった。接続を受けた別processの
`sshd: ubuntu@pts/5` は存在したがtransaction祖先ではなかった。PR #103でこの測定と停止結果は
phase0へ統合済みである。

本契約は、名前だけでzmxを信用しない。direct SSH子孫または、実行ファイル、PID、start tick、
親子関係、PID 1のsshd listener、port 22待受、変更対象との非交差を機械判定した一意なzmx経路だけを
許可する。その上で、foreground transactionから独立したdead-manを変更前に武装する。
transaction消失、start tick不一致、lease停止、既知のlive判定失敗では、契約専用backupからbengio一台を
旧philip状態へ一回だけ復旧する。全成功条件を一周期維持した場合だけcommit tokenを確定し、guardを解除して
lecun状態を残す。

host電源断、再起動、kernel停止、storage障害、transactionとguardの同時消失ではrollback process自体が
動けない。これらは保護外である。成功時も保護済みとは書かず、外側のport mappingはUNKNOWNのままにする。

## 0. 開始条件、許可、禁止

### 起動直後

    cd ~/slocal2/m2 && source .venv/bin/activate && source scripts/load_env.sh && git fetch origin && git branch --show-current && grep -c sync-pause ~/bin/m2-sync.sh && git merge-base --is-ancestor origin/phase0 HEAD

- 分岐は `feat/bengio-lecun-zmx-deadman-cutover` だけを許す。
- `grep -c sync-pause` は二件、merge-baseはexit zero、依存taskとPR #103 merge commitはphase0に必要である。
- 条件成立後すぐrepo直下に `.sync-pause` を作り、初回台帳返送が成功するまで残す。
- 前契約の `stopped` はhost変更前の測定結果であり、本契約が修正する起票者条件である。
- 開始時にtaskディレクトリ以外の未commit変更があればhostへ触れず停止する。

### ユーザー判断として固定する事実

- bengioはSSH接続でしか操作できない。
- ユーザーはremote-only dead-man方式と、zmx実測を反映した修正版の起票を承認した。
- 保護対象はtransaction消失、lease停止、PID再利用、既知の切替判定失敗である。
- 保護外はhost停止、再起動、kernel停止、storage障害、guardとの同時消失である。

### 許可する副作用

1. bengioの契約専用backup、immutable state、arm、runtime、lease、event journal、guard processとlockを作る。
2. 再同定した旧keeperと旧SSH中継の数値PID一件ずつへTERMを送る。
3. keeper、旧marker、新marker、philipとlecunのdevice addressだけを切替または復旧する。
4. bengioとlecunへ契約専用pt probeを各一件作成し、成功後も保持する。
5. 契約成果物、生成物、分岐push、PR、台帳返送を行う。

### 禁止事項

1. zmx、sshd、PID 1、port mapping、firewall、route、DNS、known_hosts、authorized_keysを変更またはsignal対象にしない。
2. systemd、cron、at、profileへguardを登録しない。packageを追加せず、hostを再起動しない。
3. 秘密鍵、API key、token、authorized_keys本文、config.xml本文を表示またはrepoへ保存しない。
4. 数値PID一件へのTERM以外でprocessを止めない。KILL、pkill、killall、広域停止を使わない。
5. Syncthingを停止または再起動せず、folder、device ID、共有、ignoreを変更しない。
6. bengio以外の一般ノードを変更しない。lecunでは中心の読み取りとprobe作成だけを許す。
7. probeを削除しない。runindexとcontext/autoは生成器だけで更新する。
8. 自動統合、本作業PRのphase0取り込み、未測定値の断定を行わない。pushは統合に含めない。

## Phase A — 依存状態と実行経路の固定

### A1. 依存と開始状態を再測定する

前契約のRESULTとresult、PR #103のmerge、現在のphase0 objectを照合する。依存taskのhelperはphase0の
同じGit objectから読み、self-test後にlive状態を再測定する。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/canary_probe.py --self-test

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-canary-lecun-cutover/center_probe.py --self-test

lecunはmarker零、keeper一件、FD9 lock保持、Syncthing稼働、22000 LISTENを要求する。bengioは旧keeper一件、
旧philip marker一件、Syncthing同一構成、22000と8384 LISTEN、22001なしを要求する。SSH中継は零件または
旧philip向け一件とし、複数なら停止する。localhost addressはphilipだけ、lecun direct addressは一件、
restart-requiredはfalseとする。

### A2. direct SSHまたは検証済みzmxへ分類する

新規 `topology_probe.py` を作り、旧 `session_probe.py` のsecret除去、PIDとstart tick、listener、
変更path非交差の検査を引き継ぐ。`/proc` から自分と全祖先についてPID、PPID、start tick、comm、
実行ファイルの解決path、deviceとinode、読み取り可能なbinaryのSHA-256、sanitized cmdlineを得る。
port 22と不存在portのlistener inodeも得る。秘密値と生のenvironmentは出力しない。

許可する分類は次のどちらか一つだけである。

- `direct_ssh`: transaction祖先にPID 1ではないsession sshdが一件以上あり、変更対象processは祖先にない。
- `verified_zmx`: transaction祖先にzmxがちょうど一件あり、その直親はPID 1、PID 1は実測どおりsshd listener、
  port 22はLISTENである。zmxの解決path、device、inode、binary要約値、PID、start tickを一組へ固定する。

`verified_zmx`では、別の `sshd: ubuntu@pts` processが祖先外に存在しても矛盾としない。それは接続経路の
補助証拠としてだけ記録する。zmxの名前一致だけ、解決不能binary、複数zmx、PID 1以外への再親化、一般的な
orphan process、PID 1がsshd listenerでない状態、port 22不在は全て拒否する。

どちらの分類でも、祖先にkeeper、Syncthing、outbound SSH tunnelがなく、変更許可pathとzmx、sshdの
binary、設定、proc identityが交差しないことを要求する。外側port mappingは推定しない。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-lecun-zmx-deadman-cutover/topology_probe.py --self-test

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-lecun-zmx-deadman-cutover/topology_probe.py --label preflight

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 依存と旧状態 | phase0に依存taskがあり、bengioとlecunが前回と同じrole | 不存在task objectと不正marker fixtureは非零になる |
| 2 | direct分類 | session sshd祖先だけをdirectとして許可 | listenerだけのsshd fixtureはdirectにならない |
| 3 | zmx分類 | 一意なzmxからPID 1 sshd listenerへ届く経路だけを許可 | 名前だけのzmx、複数zmx、一般orphanを全て拒否する |
| 4 | process独立性 | keeper、Syncthing、outbound tunnelは祖先にいない | fake祖先へ各processを混ぜるとFAILへ反転する |
| 5 | identity固定 | PID、start tick、exe deviceとinode、binary要約値を一組にする | tickまたはbinary fixtureを変えると拒否する |
| 6 | listener | port 22を検出し不存在portを零件として区別 | 存在と不存在listenerを同じfixtureで走査する |
| 7 | 秘匿 | snapshotとeventに秘密本文がない | 囮secretは一件を検出しsanitized出力は零件になる |
| 8 | 残余リスク | 保護対象と保護外を分けてauditへ記録 | host停止を保護済みとするfixtureを拒否する |

live snapshotを `deadman-audit.md` とbackup内のimmutable topology JSONへ保存し、要約値を固定する。
全項目を満たした場合だけG1をpassとする。

## Phase B — backupとdead-manの実証

backup rootは `/home/ubuntu/.hub-migration-backup.T-2026-08-13-bengio-lecun-zmx-deadman-cutover`、mode 700。
旧keeper、全marker、config.xml、philipとlecunのdevice object、開始snapshot、topology snapshotを保存する。
秘密を含むconfigとdevice JSONはmode 600でbackup内だけに置く。repoへはpath、mode、bytes、SHA-256だけを書く。

正本keeper、新marker、`topology_probe.py`、`rollback_deadman.py`、`deadman_guard.py`、
`guarded_cutover.py`、REST helperをbackup rootへ固定copyする。Git object、作業tree、固定copyの要約値を照合する。
旧markerは一行の実体をそのまま控え、二行へ合成しない。新marker stagingは
`/home/ubuntu/.ssh/id_rsa_bengiotolecun` と `192.168.196.176` の二行、mode 600とする。

### B1. dead-man protocol

- immutable stateはtask_id、許可path、開始snapshot、topology identity、backup digest、旧新process識別規則を持ち、mode 600で封印後は変更しない。
- transactionは自分のPID、start tick、state digest、topology digest、random nonceをimmutable arm recordへatomic保存する。
- transactionは新processのPIDとtickを別のruntime recordへatomic保存し、五秒以内ごとに連番leaseを更新してfsyncする。
- guardはbackupの固定copyから `start_new_session`、stdin切断、専用log、close_fdsで起動し、一件のguard lockを保持する。
- guardはstate、arm、owner identity、topology identityを再検証してreadyを返す。transactionがarmedを要求し、同じdigestとnonceでarmedが返った後だけhostを変更する。
- owner消失、tick不一致、三十秒を超えるlease停止でguardがrollback lockを取得する。
- transaction自身の失敗とguardは同じrollback lockと同じ固定rollback copyを使い、復旧を一回だけ実行する。
- 成功tokenはnonce、state digest、arm digest、最終snapshot digestを含めてfsyncし、guardが全て照合してからdisarmedを記録する。
- event journalは時刻、event種別、PIDとtick、digest、outcomeだけをappendしてfsyncし、secretと生cmdlineを含めない。

### B2. 隔離self-test

temporary fixtureとfake process、fake REST、fake rollbackだけを使い、live pathやlive processへ触れず次を実証する。

1. direct SSHと実測形のzmx fixtureはそれぞれ一意にPASSする。
2. 名前だけのzmx、複数zmx、PID 1非sshd、listener欠落、keeper祖先、tick変更はFAILする。
3. owner消失でrollbackが一回だけ呼ばれる。
4. ownerが生存してもlease停止でrollbackが一回だけ呼ばれる。
5. 正しいcommit tokenではrollbackせずguardが終了する。
6. digest違い、偽token、二つ目のguard、state外path、PID 1、曖昧なprocess一致を拒否する。
7. transactionとguardが競合してもrollback lockで一回だけになる。

Phase Bではlive guardを起動しない。backup照合と隔離self-testの全成功でG2を評価する。live guardは
次Phaseの一つのtransactionだけが起動し、そのowner PIDとtickを固定する。

## Phase C — 一つのguarded transactionで切り替える

live変更と安定性観測は、leaseを所有する一つのforeground processから次で開始する。

    cd ~/slocal2/m2 && source .venv/bin/activate && python tasks/T-2026-08-13-bengio-lecun-zmx-deadman-cutover/guarded_cutover.py --execute

helperは各待機を期限付きpollにし、外部命令にもtimeoutを置く。lease期限を超える単一sleepや無期限待機を
使わない。transactionは最初にtopologyを再測定し、G1と同じ分類、zmxまたはdirect SSH identity、PID 1、
listener、変更path非交差が一致することを確認する。不一致ならhostを変更しない。

一致後にlive guardを起動し、readyとarmedの往復、guard PIDとtick、state digest、lock保持、event追記を
確認する。handshake不成立ならguardの数値PIDへTERMし、host変更なしを再測定して停止する。handshake成立後の
host変更は次の順序だけを許す。

1. armed guardのPID、tick、state digest、topology digest、lockを再確認する。
2. 旧keeperと旧SSH中継を開始snapshotのPID、tick、sanitized cmdlineで再同定し、各数値PIDへTERMする。
3. PID消滅、lock解放、22001閉を確認する。消えなければ強いsignalを使わずrollbackへ進む。
4. 旧markerをbackupへ移し、正本keeperをatomic配置する。
5. RESTでlocalhost addressだけをphilipからlecunへ移し、他field不変とrestart-required=falseを確認する。
6. 新markerを `/home/ubuntu/.tunnel_to_lecun` へatomic配置し、正本keeperを一回だけ起動する。
7. 新keeperと新中継のPIDとtickをruntime recordへatomic記録する。記録前に消えた場合はFD255要約値と固定argvから一件だけ再同定する。

初期snapshotでkeeper一件、FD9 lock、新marker一件、lecun向けSSH中継一件、22001 LISTEN、lecun deviceの
localhost接続、旧philip経路零を確認する。中継argvはlocal 22001、remote 127.0.0.1:22000、port 50072、
接続先lecunだけを持つ。Syncthing PIDとtick、22000、8384、zmx identity、sshd、known_hosts、
authorized_keysは開始時と同じとする。満たさなければtransactionがrollback lockを取り、guardと競合せず復旧する。

## Phase D — 双方向probeと一周期観測

同じtransaction processを維持し、leaseを五秒以内で更新しながらbengioからlecun、lecunからbengioへ別名の
pt probeを一件ずつ作る。事前不存在、git check-ignore、bytes、SHA-256、lecun deviceの観測addressを照合する。
probeは削除しない。

初期成功から一八〇〇秒以上、観測は十五秒以下、leaseは五秒以下のpollでkeeper、中継、Syncthing、zmx、sshd、
22001、device接続、probeを測る。一件でも外れたら成功tokenを書かずrollbackする。終了snapshotが一致した場合だけ
commit tokenをfsyncし、guardがtoken、state、arm、snapshotのdigestを検証してdisarmed eventを残す。
guard PID消滅、guard lock解放、rollback未実施を確認してG4をpassとする。

SSH接続が途中で切れてもtransactionが生存しleaseを更新する限り処理を継続してよい。transactionが消えた場合は
guardがrollbackする。host自体が停止した場合はguardも動けないため、結果をUNKNOWNとして扱う。

接続が切れた場合、手動でkeeper、marker、Syncthingを触らない。六十秒以上待って再接続し、同じ作業分岐、
guard event、rollback event、開始状態または成功状態を読み取りだけで確認する。`make task-start`は再実行しない。
zshでは `$task` を実行しない。repoへ移動して環境を読み、`codex` を起動した後、Codexの入力欄で
`$task T-2026-08-13-bengio-lecun-zmx-deadman-cutover` を送ってeventから再開する。

## Phase E — 記録、送出、同期抑止の二段解除

`RESULT.md`と`result.yaml`へ開始状態、topology分類と固定identity、guard protocol、全event、切替、probe、
二snapshot、成功解除またはrollbackを対応づける。owner、guard、旧新processはPIDとtickの組で記録する。
起票者欠陥、逸脱、保護外failure classを空にしない。秘密本文は含めない。

    cd ~/slocal2/m2 && source .venv/bin/activate && make task-validate TASK=T-2026-08-13-bengio-lecun-zmx-deadman-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && make spec-check TASK=T-2026-08-13-bengio-lecun-zmx-deadman-cutover

    cd ~/slocal2/m2 && source .venv/bin/activate && make forbidden-check

    cd ~/slocal2/m2 && source .venv/bin/activate && make taskindex && make inbox && make taskindex-check && make inbox-check

契約範囲だけをcommitしてpushする。同じheadのPRを先に調べ、無ければ非Draft PRをphase0向けに作る。
番号、base、head、upstream、aheadを結果へ記録して再commit、pushする。本契約でPRを取り込まない。

同期抑止の解除と台帳返送は、次の二段順序だけを許す。

1. repo直下の `.sync-pause` が存在する状態をRESULTへ記録し、clean treeとpush済みheadを確認する。
2. `.sync-pause` を保持したまま初回 `make task-report` を行い、成功を確認する。
3. 初回返送が失敗したら `.sync-pause` を残し、host状態を変えず再送条件を記録して停止する。
4. 成功後だけpauseを契約専用の `/tmp` 名へ移し、repo不在と移動先実在を確認する。
5. 解除結果と時刻をRESULTへ追記し、契約範囲だけを最終commitしてpushする。
6. clean tree、upstream、aheadを再確認し、二回目の `make task-report` で最終版へ置換する。

初回と二回目はそれぞれ次の形で実行する。

    cd ~/slocal2/m2 && source scripts/load_env.sh && make task-report TASK=T-2026-08-13-bengio-lecun-zmx-deadman-cutover

二回目の返送だけが失敗した場合は、成功済みcanaryをrollbackせず、同期抑止も再作成しない。最終commitを保ったまま
同じ命令を再実行する条件を記録する。G4まで満たした場合だけpassとする。dead-manまたはtransactionが旧状態へ
正常復旧した場合はstopped、復旧後状態を測れない場合はUNKNOWNを持つstoppedまたはpartialとする。

## rollback後の必須状態

- localhost addressはphilipだけに一件、lecun direct addressは開始時どおり。
- 旧markerは開始時bytes、mode、SHA-256で復旧し、新markerはhomeにない。
- 旧keeperは開始時bytes、mode、SHA-256で復旧し、一件だけがFD9 lockを持つ。
- 新keeperとlecun中継は一意に再同定した数値PIDへTERM済み。
- Syncthing PIDとtick、zmx identity、sshd、known_hosts、authorized_keysは開始時と同じ。
- rollback eventは一件、guardとtransactionの両方が二重実行していない。

rollback不能、guard state破損、process再同定不能では追加操作を止める。SSHが残っていれば測定だけを行い、
host停止またはSSH消失では復旧済みと断定せずUNKNOWNとしてユーザーへescalateする。

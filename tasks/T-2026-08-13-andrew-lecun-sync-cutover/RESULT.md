# RESULT — Andrewをlecun中心へ切り替え、双方向同期を一周期維持

**task_id:** `T-2026-08-13-andrew-lecun-sync-cutover`  **kind:** `impl`  **status:** `pass`
**host:** `Andrew`  **branch:** `feat/andrew-lecun-sync-cutover`

## 結論

Andrewを旧philip中心からlecun中心へ可逆切替した。Syncthingは再起動せず、開始時と終了時で
PIDとstart tickが一致した。Andrew→lecun 116 bytes、lecun→Andrew 115 bytesの専用probeは
両端でSHA-256一致し、壁時計・単調時計とも1805.822秒後まで保持された。

## Gate

| Gate | 判定 | 実測 |
|---|---|---|
| G1 | pass | 依存object、鍵指紋、strict認証、lecun中心、Andrew旧状態、局所差分backupを確認 |
| G2 | pass | state要約、lease反転、owner tick、commit token、二重guard lockを隔離実証 |
| G3 | pass | lecun marker/keeper/中継/routeが各一意、旧philip中継0、Syncthing identity不変 |
| G4 | pass | 双方向probe一致、1805.822秒後もprocess・route・dataを維持 |
| G5 | pass | 検証・送出・PR・台帳返送・同期抑止解除を完了工程で確認 |

## 主要実測

- Andrew鍵指紋: `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k`。提出・lecun登録結果と一致。
- lecun中心: marker 0、keeper 1+FD9 lock、Syncthing稼働、22000開、22001閉。
- 開始状態: `.tunnel_to_philip` 1、SSH中継0、22001閉、route=`philip_only`、restart不要。
- 局所差分: 追加106、変更8、消失71。内容backup 114件・1,713,191 bytes、全件bytes/mode/SHA-256一致。
- 成功状態: `.tunnel_to_lecun` 1、keeper PID 901445、lecun中継 PID 901452、旧中継0。
- Syncthing identity: `(522602,124234793)` と `(881,1297814)` を開始から終了まで維持。
- route: localhost addressはlecun deviceだけ。lecun connected、philip disconnected、restart不要。
- probe: Andrew→lecun `4318a778...dcd9bd`、lecun→Andrew `81d882b4...c2011e`。
- guard: ready→armed→disarmed。commit tokenあり、成功attemptのrollbackなし。

## 試験と陽性対照

- L3: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL。SKIPはGPU、決定性、prereg、凍結源で本impl対象外。
- ruff、py_compile、5 helper self-testはPASS。
- process分類は鍵pathに`philip`を含むlecun中継fixtureで、lecun=true/philip=falseへ反転。
- lockは保持中の二重取得を拒否し、解放後に取得成功。
- leaseは29秒で継続、31秒でrollback判定。owner tick不一致を拒否し、正しいtokenでdisarm。
- routeはphilip_only / lecun_only / duplicate / missingを区別。
- secret囮は1件、通常snapshotでは0件。

## 逸脱

1. attempt-1は鍵path名の`philip`を宛先と誤認して成功predicateを拒否した。commit tokenは作られなかった。
2. 同attemptのguardはTERM済みkeeperの`/proc`残存を終了とみなさず停止した。強いsignalは使わず、
   不在/zombieを終了済みとする修正後、数値SSH PID 896361だけへTERMし、封印stateから復旧した。
3. rollback後のconfig.xmlはRESTにより再整形されファイルSHAが変わったが、二device object、非address要約、
   folder要約、routeは開始値と一致した。以後の開始判定を意味的object要約へ修正した。
4. attempt-2は復旧後keeperの新PIDを再同定せず旧PIDを参照し、host変更前に停止した。現在snapshotから
   PID+tickを再同定するよう修正した。attempt-3が最終成功である。
5. 導入済みCodeGraphに`watch`がなく、`init`と変更後の`sync`で代替した。
6. 同期抑止解除後に`m2-sync.sh`を直接実行してexit 0を得たが、phase0差分の無いno-opでは
   `sync-alerts.log`が増えなかった。marker不在と直接実行で再開を確認し、増分検査の空振りを起票者欠陥とした。

## 残余リスク・UNKNOWN

- host停止、kernel停止、storage障害、guardとtransactionの同時消失は保護外。
- 容器外のport mappingは本host内からはUNKNOWN。
- backupと両probeは契約どおり保持している。

## 検証

- task-validate: `1 task(s), 0 failed`。
- spec-check: 8 rules、finding 0。
- forbidden-check: changed 26 / checked 26 / excluded 0 / violations 0。
- taskindex / inbox生成とcheck: exit 0。
- validator回帰試験: 56 passed。
- ruff / py_compile: PASS。
- remote probe再照合: 116 bytes / 115 bytes、両SHA-256一致。
- 報告の秘匿検査: RESULT / result.yaml / cutover-audit各0件。

## 送出

- 記録commit: `ff4b1a8`。
- upstream: `origin/feat/andrew-lecun-sync-cutover`。
- PR: #106、OPEN、非Draft、base `phase0`、head `feat/andrew-lecun-sync-cutover`。
- URL: https://github.com/takuya3h/m2/pull/106
- 初回台帳返送: exit 0、verdict `pass`、4507 bytes、起票者欠陥0件、置換0件。
- 同期抑止解除: repo直下0件、`/tmp/.sync-pause.released.T-2026-08-13-andrew-lecun-sync-cutover` 1件。
- 解除後同期処理: 直接実行exit 0。no-opのためsync-alerts増分0件。

## 起票者の誤り

`check_does_not_check` 1件。E4は常駐再開を`sync-alerts`増分で確認するが、実装は差分の無い
正常no-opではログを追加しない。そのため増分0は「再開して正常終了」と「未実行」を区別できない。
本taskではmarker不在、退避先実在、直接実行exit 0を別の根拠として用いた。

# RESULT — zmxが4件あり一意性条件を満たさず変更前停止

**task_id:** `T-2026-08-13-bengio-lecun-zmx-deadman-cutover`  **kind:** `impl`
**host:** `Bengio`  **branch:** `feat/bengio-lecun-zmx-deadman-cutover`

## 1. 解決された参照

### 省略された `inputs.sigma_policy`

`context/conventions.md#sigma` の原文。

<a id="sigma"></a>
## sigma

sigma に関する列は 4 系統ある（backlog B-18）。

1. `{metric}_pstd` / `{metric}_sstd` — seed 間の sigma（母集団 / 標本）
2. `delta_pstd_{metric}` / `delta_sstd_{metric}` — 実験間 paired Delta の sigma
3. `sigma_source` — sigma の系統。値は paired_delta または within_run_seed_spread
4. `delta_sigma_source` — paired sigma の計算方法。値は paired または unpaired_pooled

3 と 4 は直交する（どの sigma を使ったか vs paired sigma をどう計算したか）。

### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

この既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、
決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、
`RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。

### 判定規約の表記

判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。
縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない
（backlog B-33 と同型の事故）。

    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号
    誤: 縦線で delta を囲む記法

同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。

本契約は統計値を判定しないため、この継承値は使用していない。

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の該当アンカーの原文。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`inputs.denominator.ref` と `inputs.frozen_source.ref` は無く、追加解決はない。

## 2. 結論

結果は `stopped`。依存task、bengio旧状態、lecun中心、祖先内zmx identity、PID 1 sshd
listener、port 22、変更対象との非交差は実測できた。しかしhost全体にzmxが4件あり、契約の
「zmxが複数ある場合は停止」と「一意なzmx経路だけを許可」を満たさなかった。

`topology_probe.py --label preflight` は `host_zmx_count_not_one:4` を検出してexit 1。
G1 `on_fail: stop` に従い、4件から実行者が一つを選ばず、Phase B〜Dとhost変更を実施しなかった。

## 3. Phase Aの実測

| 項目 | 実測 |
|---|---|
| origin/phase0 / 依存 | `9cd792b32c783ba9bbf7a41ec0abc91a2aa27922` / PR #103 merge |
| topology | `rejected`、host zmx count 4 |
| 祖先zmx | PID/PPID/tick `472358/1/62748521` |
| zmx binary | device/inode `1048634/93998834`、SHA-256 `9fec4a16faa642a036c8cbfc1d4755bd7b18b191403ca910ea1d830bd155913f` |
| 他zmx | PID/PPID/tick `6669/1/10647996`、`7206/1/10649378`、`487967/487327/70833321` |
| PID 1 | comm sshd、listener cmdline、start tick `5237`、`/proc/1/exe`はUNKNOWN |
| SSH listener | port 22 inode `11084` / `11086`、不存在port 65534は0件 |
| bengio keeper | 1件、PID/tick `773/955479`、FD9 lock保持 |
| bengio marker/listener | philip向け1件、22000=1、8384=1、22001=0 |
| bengio Syncthing | PID/tick `789/955480`、`2070/2539289` |
| lecun中心 | strict SSH exit 0、marker 0、keeper 1、Syncthing 2、22000開、22001閉 |
| Syncthing route | `philip_only`、lecun directあり、restart-required=false |
| 外側port mapping | UNKNOWN |

詳細なmode、bytes、SHA-256、positive controlは `deadman-audit.md` に記録した。秘密本文は
表示・保存していない。

## 4. 検証

- task-validate: exit 0、1 task、0 failed。
- L3: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL。
- SKIP: `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、`frozen_source_hash`。
- canary probe self-test: 18項目PASS。
- center probe self-test: 11項目PASS。
- topology probe self-test: 21項目PASS、ruff clean、py_compile成功。
- topology live probe: exit 1、`host_zmx_count_not_one:4`。

## 5. Gate

| Gate | 判定 | 理由 |
|---|---|---|
| G1 | stop | host全体にzmxが4件あり一意なverified_zmxに分類できない |
| G2 | UNKNOWN | G1 stopのためbackup、dead-man実装、隔離試験を未実施 |
| G3 | UNKNOWN | live変更を未実施 |
| G4 | UNKNOWN | 双方向probeと1800秒観測を未実施 |
| G5 | skip | G1 stopのためgateとしては未評価。初回返送とpause解除まで完了、最終版は最終commit後に返送 |

## 6. 陽性対照

- direct SSH fixtureと一意なzmx fixtureはそれぞれPASSした。
- listenerだけ、名前だけzmx、複数zmx、一般orphan、PID 1非sshd、listener欠落は拒否した。
- fake祖先へkeeper、Syncthing、outbound SSH tunnelを混ぜるとFAILへ反転した。
- zmxのstart tickまたはbinary SHAを変えるとidentity照合を拒否した。
- port 22 fixtureは1件、不存在port 65534は0件だった。
- 囮secretは入力で1件、sanitized出力では0件だった。
- host停止を保護対象へ移したfixtureは残余リスクpolicy違反として拒否した。

## 7. 起票者の誤り

なし。複数zmxを停止条件にした契約のgateが実測どおり働いた。

## 8. 逸脱

- topology probe初版はPID 1にもbinary解決を要求したが、契約が固定binary identityを要求する対象は
  zmxであり、PID 1はcomm/cmdline/start tickとlistenerで識別するため、live判定前に余分な条件を除去した。
- G1 `on_fail: stop` に従い、Phase B〜Dとhost変更を行わなかった。これは契約どおりであり逸脱ではない。

## 9. 未実施・再開条件

`deadman_guard.py`、`rollback_deadman.py`、`guarded_cutover.py` はPhase B成果物のため未実装。
backup、immutable state、arm、runtime、lease、event、commit token、live guard、probe、1800秒安定性、
rollbackはすべて `UNKNOWN`。

再開には、host全体の複数zmxをどう一意化するかを新しい契約で定義する必要がある。既存zmxをsignal、
停止、削除することは本契約の許可範囲外なので実施していない。

## 10. 送出・台帳

| 項目 | 実測 |
|---|---|
| task-validate | exit 0、1 task、0 failed |
| spec-check | exit 0、8 rules、finding 0 |
| docs-check | exit 0、対象42文書、食い違いなし |
| forbidden-check | exit 0、changed 13 / checked 9 / excluded 4 / violations 0 |
| taskindex / inbox | 生成exit 0、taskindex-check / inbox-checkともにexit 0 |
| 記録commit | `05c820b`、`04f8644`。最終報告更新は後続commit |
| push / upstream | 成功、`origin/feat/bengio-lecun-zmx-deadman-cutover` |
| behind / ahead | 0 / 0 |
| PR | #104、OPEN、非Draft、base `phase0`、head `feat/bengio-lecun-zmx-deadman-cutover` |
| clean tree | 初回返送前にcleanを確認 |
| 初回台帳返送 | exit 0、verdict `stopped`、7581 bytes、起票者欠陥0件、置換0件 |
| 同期抑止解除 | `2026-08-13T13:25:59Z`。repo直下不在、契約専用 `/tmp` 退避先実在 |
| 最終台帳返送 | 最終commit後に実施 |

PR: https://github.com/takuya3h/m2/pull/104

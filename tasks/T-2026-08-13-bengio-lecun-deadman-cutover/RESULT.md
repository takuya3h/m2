# RESULT — zmx再親化によりSSH session祖先条件を満たさず変更前停止

**task_id:** `T-2026-08-13-bengio-lecun-deadman-cutover`  **kind:** `impl`
**host:** `Bengio`  **branch:** `feat/bengio-lecun-deadman-cutover`

## 1. 解決された参照

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

`inputs.denominator.ref`、`inputs.frozen_source.ref`、`inputs.sigma_policy` は無く、
追加の参照解決はない。

## 2. 結論

結果は `stopped`。Phase A の依存、旧状態、lecun中心、listener、変更pathとの非交差、
秘匿、残余リスクは成立した。しかし live transaction の祖先は
`python → Codex → zsh → zmx → PID 1 sshd listener` であり、別に存在する対話session
`sshd: ubuntu@pts/5` は祖先ではなかった。

契約は transaction実行元がsession sshd配下にあることをG1条件としている。
listener PID 1をsessionと誤認しない陽性対照を追加したprobeは
`ancestor_chain_reaches_sshd=false`、exit 1となったため、G1 `on_fail: stop` に従った。
Phase B以降のhost変更、dead-man武装、rollbackは実施していない。

## 3. Phase A の実測

| 項目 | 実測 |
|---|---|
| origin/phase0 / 依存task | `783657a8051a3219251ac28209f4a60476a73f15` / PR #102 merge |
| bengio keeper | 1件、PID/tick `773/955479`、FD9 lock保持 |
| bengio marker | philip向け1件、1行、mode 664 |
| bengio Syncthing | PID/tick `789/955480`、`2070/2539289` |
| bengio listener | 22000=1、8384=1、22001=0 |
| lecun中心 | strict SSH exit 0、marker 0、keeper 1、Syncthing 2、22000開、22001閉 |
| Syncthing route | `philip_only`、lecun directあり、restart-required=false |
| session probe | self-test 13項目PASS、live exit 1 |
| SSH listener | port 22 inode `11084` / `11086`、不存在port 65534は0件 |
| 外側port mapping | UNKNOWN |

ファイルのmode、bytes、SHA-256とpositive controlの詳細は `deadman-audit.md` に記録した。
秘密鍵、API key、token、authorized_keys本文、config.xml本文は表示・保存していない。

## 4. 検証

- task-validate（実行前）: exit 0、1 task、0 failed。
- L3: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL。
- SKIP: `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、`frozen_source_hash`。
- canary probe self-test: 18項目PASS。
- center probe self-test: 11項目PASS。
- session probe self-test: 13項目PASS、ruff clean、py_compile成功。
- Syncthing route self-test: 5項目PASS。
- session live probe: exit 1（G1停止条件を検出）。

## 5. Gate

| Gate | 判定 | 理由 |
|---|---|---|
| G1 | stop | 対話session sshdは存在するが、zmx配下のtransaction祖先ではない |
| G2 | UNKNOWN | G1 stopのためbackup、dead-man実装、隔離試験を未実施 |
| G3 | UNKNOWN | live変更を未実施 |
| G4 | UNKNOWN | 双方向probeと1800秒観測を未実施 |
| G5 | UNKNOWN | 停止報告の記録・送出結果は後段で追記 |

## 6. 陽性対照

- listener-only祖先はsession sshdとして数えず、`sshd: ubuntu@pts/5` fixtureだけをsessionとして検出した。
- fake祖先鎖へkeeperを混ぜると独立性判定がFAILへ反転した。
- 同一PIDでstart tickだけを変えたfixtureをowner identityとして拒否した。
- port 22 fixtureは1件を検出し、不存在port 65534は0件だった。
- 囮secretは検出1件、sanitized出力では0件だった。
- host停止を保護対象へ移したfixtureは残余リスクpolicy違反として拒否した。
- localhost routeの重複・欠落fixtureをともに拒否した。

## 7. 起票者の誤り

- `shell_assumption`: 契約は実行主体の祖先が対話session sshdへ直接つながることを前提にしたが、
  このホストのCodexはzmx配下でPID 1へ再親化される。指示どおり祖先を測るとsession sshdは別processとなり、
  host変更から独立している可能性が高い構成でもG1が必ずstopする。

## 8. 逸脱

- `task-start` はすでに専用分岐と未追跡契約がある状態で再実行され、終了コード3で停止した。
  既存の分岐が契約指定どおり `origin/phase0` 起点であることを再測定し、`task-start` 自体は再々実行しなかった。
- `pstree` は未導入だったため使用せず、契約どおり `session_probe.py` が `/proc` を直接走査した。
- G1 `on_fail: stop` に従い、Phase B〜Dとhost変更を行わなかった。

## 9. 未実施・再開条件

`deadman_guard.py`、`rollback_deadman.py`、`guarded_cutover.py` はPhase Bの成果物であり、
G1 stop後に実装していない。backup、state、lease、event、commit token、live guard、probe、
1800秒安定性はすべて `UNKNOWN`。

再開には、(1) 実際のsession sshd子孫からforeground transactionを起動するか、
(2) zmxによる再親化を安全な独立性として受け入れる契約amendmentと機械判定を起票者が用意する。
実行者はどちらを採るか決めていない。

## 10. 送出・台帳

検証、commit、push、PR、同期抑止解除、台帳返送の結果は実測後に追記する。


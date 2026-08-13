# dead-man cutover audit — Phase A stop

- task_id: `T-2026-08-13-bengio-lecun-deadman-cutover`
- host: `Bengio`
- branch: `feat/bengio-lecun-deadman-cutover`
- measured_at: `2026-08-13T12:25:46Z`
- verdict: `G1 stop`

## 固定されたユーザー判断と残余リスク

- bengio の復旧経路は SSH だけである。
- ユーザーは前契約の停止報告後、選択肢2の dead-man 付き remote-only canary を選択した。
- 保護対象は transaction owner 消失、lease 停止、既知の切替判定失敗である。
- host停止、再起動、kernel停止、storage障害、guardとtransactionの同時消失は保護外である。
- 本 task は G1 で停止したため dead-man を武装せず、上記保護対象も live では未実証である。

## 開始条件

| 項目 | 実測 |
|---|---|
| origin/phase0 | `783657a8051a3219251ac28209f4a60476a73f15` |
| 依存task | 上記objectに存在、PR #102 のmerge commit |
| branch | `feat/bengio-lecun-deadman-cutover` |
| origin/phase0 ancestor | `git merge-base --is-ancestor` exit 0 |
| sync-pause対応 | `/home/ubuntu/bin/m2-sync.sh` に2件 |
| repo pause | `.sync-pause` 実在、0 bytes |
| L1/L2 | 1 task、0 failed |
| L3 | 5 PASS / 0 WARN / 4 SKIP / 0 FAIL |

L3 の SKIP は `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、
`frozen_source_hash`。前二者は契約の preflight 指定外、後二者は `kind: impl` のため対象外。

## bengio の変更前状態

| 項目 | 実測 |
|---|---|
| keeper | 1件、PID/tick `773/955479`、FD9 lock保持 |
| keeper SHA-256 | `603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503` |
| marker | `.tunnel_to_philip` 1件、1行、mode 664、44 bytes |
| marker SHA-256 | `b2c4cbd3e3d1c821e81fc18c2dae53620be1385b5b31d21e0a110726ee711c13` |
| Syncthing | PID/tick `789/955480` と `2070/2539289` |
| listener | 22000=1、8384=1、22001=0 |
| config.xml | mode 600、21750 bytes、SHA-256 `86cf69777696da1394739142d93667f9ec31b9be300159563ea0679d23986cd1` |
| known_hosts | mode 600、4054 bytes、SHA-256 `50a529d298ef93ce0baf60db394da5bb728839f5b89f9ee8c7a38764d0925fe3` |
| authorized_keys | mode 664、2227 bytes、SHA-256 `c5e26e9a4d75205951d3899c06c4fbd8ab73879b65263548a0f0eebdcf264aab` |

Syncthing REST は v2.1.3、granular device endpoint 対応、localhost route は
`philip_only`、lecun direct address は存在、`restart_required=false`、announce/relay は
ともに false。device ID、API key、config.xml 本文は記録していない。

## lecun 中心の状態

strict SSH は port 50072、BatchMode、StrictHostKeyChecking、ClearAllForwardingsを固定して
exit 0。marker 0、keeper 1件、FD9 lock保持、Syncthing 2 process、22000/8384 LISTEN、
22001閉を実測した。

## SSH session と変更対象の独立性

`session_probe.py --self-test` は13項目PASS。live probeは次の祖先鎖を取得した。

    python -> codex -> node -> zsh -> zmx -> PID 1 sshd listener

変更対象の keeper、Syncthing、SSH中継は祖先に無い。SSH listenerは port 22 でinode
`11084` と `11086`、不存在対照 port 65534 は0件。`/usr/sbin/sshd` と
`/etc/ssh/sshd_config` は変更対象pathと交差しない。外側のport mappingは `UNKNOWN`。

一方、対話sessionの `sshd: ubuntu@pts/5` は PID/tick `487326/70832449` として存在するが、
Codexの祖先ではない。`zmx` がPID 1へ再親化されているためである。PID 1 のlistenerだけを
session祖先として数えない修正版probeでは `ancestor_chain_reaches_sshd=false`、exit 1となった。

## 陽性対照

| 判定 | breaking input | observed |
|---|---|---|
| session祖先 | listener-onlyのPID 1だけを祖先へ置く | sessionとは判定せずPASS対照 |
| 変更対象祖先 | fake祖先鎖へkeeperを混ぜる | 独立性FAILへ反転 |
| owner同定 | 同一PIDでstart tickだけ変える | identityを拒否 |
| listener | port 22 fixtureとport 65534を照合 | 前者1件、後者0件 |
| 秘匿 | 囮secretをargvへ入れる | 検出1件、sanitized出力0件 |
| 残余リスク | host停止を保護対象へ移す | exact policyを拒否 |
| Syncthing route | localhostを重複または欠落させる | 両fixtureを拒否 |

## Gate と未実施範囲

G1 は `stop`。契約が要求する「transaction実行元がsession sshd配下」を満たさないため、
Phase Bのbackup/dead-man実装、Phase Cのlive切替、Phase Dのprobe/1800秒観測を実施していない。
keeper、marker、SSH中継、Syncthing device object、sshd、鍵関連ファイルは変更していない。
rollbackは変更前停止のため不要で、未実施である。


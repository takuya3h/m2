# zmx dead-man cutover audit — G1 stop

- task_id: `T-2026-08-13-bengio-lecun-zmx-deadman-cutover`
- host: `Bengio`
- branch: `feat/bengio-lecun-zmx-deadman-cutover`
- measured_at: `2026-08-13T13:21:39Z`
- verdict: `G1 stop`

## ユーザー判断と残余リスク

- bengioはSSH接続でしか操作できない。
- ユーザーはremote-only dead-man方式と、zmx実測を反映した修正版の起票を承認した。
- 保護対象はtransaction消失、lease停止、PID再利用、既知の切替判定失敗である。
- host停止、再起動、kernel停止、storage障害、guardとtransactionの同時消失は保護外である。
- 外側のport mappingは `UNKNOWN`。
- G1で停止したためlive dead-manは武装しておらず、保護対象もliveでは未実証である。

## 開始条件と依存

| 項目 | 実測 |
|---|---|
| phase0 / HEAD | `9cd792b32c783ba9bbf7a41ec0abc91a2aa27922` |
| 依存task / PR | `T-2026-08-13-bengio-lecun-deadman-cutover` / PR #103 merge |
| branch | `feat/bengio-lecun-zmx-deadman-cutover` |
| phase0 ancestor | `git merge-base --is-ancestor` exit 0 |
| sync-pause対応 | `/home/ubuntu/bin/m2-sync.sh` に2件 |
| repo pause | `.sync-pause` 実在、0 bytes |
| helper identity | canary/center/route/rollback/sessionの5ファイルでworktreeとphase0 objectが一致 |
| L1/L2 | 1 task、0 failed |
| L3 | 5 PASS / 0 WARN / 4 SKIP / 0 FAIL |

L3のSKIPは `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、
`frozen_source_hash`。前二者は契約のpreflight指定外、後二者は `kind: impl` のため対象外。

## topology分類

祖先鎖は子から親の順に次だった。

    python -> Codex -> node -> zsh -> zmx -> PID 1 sshd listener

祖先内zmxはPID/PPID/tick `472358/1/62748521`、resolved path
`/home/ubuntu/.local/bin/zmx`、device/inode `1048634/93998834`、binary SHA-256
`9fec4a16faa642a036c8cbfc1d4755bd7b18b191403ca910ea1d830bd155913f`。

しかしhost全体では同一binary identityのzmxが次の4件存在した。

| PID | PPID | start tick |
|---:|---:|---:|
| 6669 | 1 | 10647996 |
| 7206 | 1 | 10649378 |
| 472358 | 1 | 62748521 |
| 487967 | 487327 | 70833321 |

このためclassificationは `rejected`、理由は `host_zmx_count_not_one:4` と
`topology_is_not_exactly_one_allowed_class`。契約が要求する一意な `verified_zmx` ではない。

PID 1はcomm `sshd`、start tick `5237`、cmdlineはlistenerを示した。`/proc/1/exe` は
この実行主体から解決不能だったため `UNKNOWN`。正本 `/usr/sbin/sshd` はdevice/inode
`1048634/95711005`、SHA-256
`cebafe4787622067e2bf799dcdc1f698cd55946d05261ff056ce80fadf5e7fd2`。
port 22 listener inodeは `11084` と `11086`、不存在対照port 65534は0件。

祖先にkeeper、Syncthing、outbound SSH tunnelは無く、zmx/sshd/configのpathは変更対象と
交差しなかった。対話session sshdは祖先外にPID/tick `487314/70832298` と
`487326/70832449` で存在した。

## bengio旧状態

| 項目 | 実測 |
|---|---|
| keeper | 1件、PID/tick `773/955479`、FD9 lock保持 |
| keeper | mode 775、2250 bytes、SHA-256 `603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503` |
| marker | philip向け1件、1行、mode 664、44 bytes、SHA-256 `b2c4cbd3e3d1c821e81fc18c2dae53620be1385b5b31d21e0a110726ee711c13` |
| Syncthing | PID/tick `789/955480` と `2070/2539289` |
| listener | 22000=1、8384=1、22001=0 |
| config.xml | mode 600、21750 bytes、SHA-256 `86cf69777696da1394739142d93667f9ec31b9be300159563ea0679d23986cd1` |
| known_hosts | mode 600、4054 bytes、SHA-256 `50a529d298ef93ce0baf60db394da5bb728839f5b89f9ee8c7a38764d0925fe3` |
| authorized_keys | mode 664、2227 bytes、SHA-256 `c5e26e9a4d75205951d3899c06c4fbd8ab73879b65263548a0f0eebdcf264aab` |

Syncthing RESTはv2.1.3、localhost routeは `philip_only`、lecun direct addressは存在、
`restart_required=false`、announce/relayはfalse。config.xml本文、API key、token、秘密鍵、
authorized_keys本文、device JSON本文は記録していない。

## lecun中心状態

strict SSHはport 50072、BatchMode、StrictHostKeyChecking、ClearAllForwardingsを固定してexit 0。
marker 0、keeper 1件、FD9 lock保持、Syncthing 2 process、22000/8384 LISTEN、22001閉。

## 陽性対照

`topology_probe.py --self-test` は21項目PASSした。direct SSHと実測形zmxはPASSし、listenerだけ、
名前だけzmx、複数zmx、一般orphan、PID 1非sshd、listener欠落、keeper/Syncthing/tunnel祖先、
tick変更、binary変更を拒否した。port 22と不存在portを区別し、囮secretは入力で1件、
sanitize後0件、host停止を保護対象へ移すfixtureも拒否した。

## 停止範囲

G1 `on_fail: stop` に従い、Phase Bのbackup/dead-man実装、Phase Cのlive切替、Phase Dのprobeと
1800秒観測を実施していない。keeper、marker、SSH中継、Syncthing device address、zmx、sshd、
known_hosts、authorized_keysは変更していない。rollbackは変更前停止のため未実施。


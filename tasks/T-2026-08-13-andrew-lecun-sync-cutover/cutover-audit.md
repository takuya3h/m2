# Cutover audit

- preflight: L1/L2 OK、L3 5 PASS / 0 WARN / 4 SKIP / 0 FAIL。
- backup root: `/home/ubuntu/.hub-migration-backup.T-2026-08-13-andrew-lecun-sync-cutover`、mode 700。
- local diff backup: 114 files、1,713,191 bytes、114/114 verified。
- attempt-1: success predicateで誤分類を検出。自動guard停止後、限定helperで完全rollback。
- attempt-2: stale keeper PID参照をhost変更前に検出して停止。
- attempt-3: owner `(901271,194449574)`、guard `(901409,194449599)`。
- success processes: keeper `(901445,194449695)`、tunnel `(901452,194449696)`。
- Syncthing: `(522602,124234793)`、`(881,1297814)`、開始終了一致。
- probes: 116 bytes / 115 bytes、両方向SHA-256一致。
- stability: wall 1805.822468996048 seconds / monotonic 1805.8224699220154 seconds。
- guard events: ready / armed / disarmed。success attemptのrollbackなし。
- secrets: 秘密鍵、API key、token、authorized_keys本文、config.xml本文をrepoへ保存していない。


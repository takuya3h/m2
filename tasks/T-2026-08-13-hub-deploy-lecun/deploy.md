# Deploy audit — T-2026-08-13-hub-deploy-lecun

## 停止結論

handoff と本 SPEC が両立しないため、配置前に停止した。

| 出所 | 行 | 要求 |
|---|---:|---|
| `tasks/T-2026-08-13-hub-role-and-restart/handoff.md` | 7–8 | lecun は新 keeper、目印なしで確認する |
| 同 handoff | 59 | lecun の全 `.tunnel_to_*` をバックアップへ移す |
| 同 handoff | 74 | 成功条件は `.tunnel_to_*` 0件、中継0件 |
| 本 `SPEC.md` | 18 | 食い違いは handoff に従う |
| 本 `SPEC.md` | 37 | 中心の目印の変更・削除・移動を禁止する |
| 本 `SPEC.md` | 51–52 | ssh は一度も実行せず、known_hosts 副作用なしとする |
| 本 `SPEC.md` | 334–340 | marker と正本の要約値を Task 2 と一致させる |

handoff へ従うには marker の移動が必要だが、本 SPEC はその操作を禁止する。marker を残すと、
正本 keeper の7–23行が marker を解決し、33–38行が SSH 起動を試みる。よって本 SPEC の
「中継なし」「ssh は一度も実行しない」とも両立しない。

本 SPEC の想定外処理にある「handoff の手順と本 SPEC が両立せず、どちらに従っても禁止に
触れる場合」に該当する。投影再生成、控え作成、keeper 配置、TERM、新 keeper 起動は未実施。

## 契約検証

```text
OK   T-2026-08-13-hub-deploy-lecun

1 task(s), 0 failed
```

```text
P1 venv_active            PASS
P2 cuda_ext_loaded        SKIP
P3 deterministic_flags    SKIP
P4 prereg_committed       SKIP
P5 frozen_source_hash     SKIP
P6 decisions_answered     PASS
P7 destination_writable   PASS
P8 contract_valid         PASS
P9 spec_lint              PASS

RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
```

機械検査は構造を通したが、handoff と SPEC の意味上の自己矛盾は検出しなかった。

## handoff の読み取り

```text
188 tasks/T-2026-08-13-hub-role-and-restart/handoff.md
```

全文を読み、中心用手順、八確認、rollback、失敗九様式を確認した。中心用の要点は、事前に
keeper・m2-sync・marker・authorized_keys・`.stignore` の要約値と process/lock/LISTEN を
固定し、keeper と marker を控え、正本 keeper を配置し、marker を0件へ移し、旧 keeper を
数値 PID 限定で TERM、lock 解放後に記録済み nohup 行で起動すること。成功条件は keeper 1、
新版 FD、flock、marker 0、中継0、Syncthing 22000 LISTEN、m2-sync一周である。

## marker と正本分岐の実測

```text
marker_count=1
path=/home/ubuntu/.tunnel_to_philip size=43 mode=664
e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46  /home/ubuntu/.tunnel_to_philip
line_count=1
line1_nonempty=1
line2_nonempty=0
actual_marker_test_exit=0
absent_marker_test_exit=1
```

正本の該当部分:

```text
 7 resolve_tunnel() {
 8   TUNNEL_MARKER=
 9   for candidate in "$HOME"/.tunnel_to_*; do
10     if [ -f "$candidate" ]; then
11       TUNNEL_MARKER=$candidate
12       break
13     fi
14   done
15   [ -n "$TUNNEL_MARKER" ] || return 1
17   HUB_NAME=${TUNNEL_MARKER##*/}
18   HUB_NAME=${HUB_NAME#.tunnel_to_}
19   TUNNEL_KEY=$(sed -n '1p' "$TUNNEL_MARKER")
20   HUB_ADDRESS=$(sed -n '2p' "$TUNNEL_MARKER")
21   [ -n "$HUB_ADDRESS" ] || HUB_ADDRESS=$HUB_NAME
22   [ -n "$HUB_NAME" ] && [ -n "$TUNNEL_KEY" ]
23 }
33 if resolve_tunnel && ! pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' >/dev/null; then
34   nohup ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i "$TUNNEL_KEY" \
37     ubuntu@"$HUB_ADDRESS" >>~/.tunnel.log 2>&1 9>&- &
38 fi
```

現markerでは `HUB_NAME=philip`、鍵path非空、2行目が空なので `HUB_ADDRESS=philip` となる構造。
markerを残して新版を起動すれば、現在中継が無いため33行の条件が成立し、sshを起動し得る。

## 停止時の状態

```text
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
  34 /home/ubuntu/bin/keeper.sh
  52 scripts/sync/keeper.sh
keeper.sh count=1 pids=1071
m2-sync.sh count=0 pids=
syncthing count=2 pids=1079,1395414
22001 count=0 pids=
zzz_no_such_process count=0 pids=
port_22001=-
port_22000=LISTEN
port_8384=LISTEN
```

PID 1071 は FD9 にWRITE flockを保持している。旧 keeper は未変更・稼働中。正本とのSHAは異なり、
配置は行っていない。marker、SSH設定、Syncthing、m2-syncも変更・停止・再起動していない。

## 未実施

- `make taskindex` / `make inbox` と生成物commit
- `~/m2-archive/` の作成とkeeper控え
- `~/bin/keeper.sh` の置換
- 数値PIDへのTERM
- keeperの明示起動
- 中心化の稼働確認

## 再開条件

起票者が次のいずれかで契約を整合させる必要がある。

1. handoffを正として、lecun markerの控えと移動を許可し、marker不変条件を削除する。
2. markerを残すなら、中心ではmarkerを無視する別の実装・設定を先に正本化し、その変更を
   検証する別契約を作る。

どちらを選ぶかは本契約の実行者が決めない。

## 停止報告の検証

```text
stopped_validate_exit=0
RESULT.md bmp_over=0 hex40=0
result.yaml bmp_over=0 hex40=0
deploy.md bmp_over=0 hex40=0
stopped_forbidden_exit=0
status_lines=2
?? tasks/T-2026-08-13-hub-deploy-lecun/
?? tasks/inbox.d/T-2026-08-13-hub-deploy-lecun.md
unmerged=0
diff_check_exit=0
taskindex_check_exit=2
inbox_check_exit=2
```

`forbidden-check` はchanged 6 / checked 6 / violations 0。投影検査は未反映差分を検出した。
矛盾確定後のため `make taskindex` と `make inbox` は実行していない。

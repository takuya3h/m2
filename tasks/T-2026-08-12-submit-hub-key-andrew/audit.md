# Audit — T-2026-08-12-submit-hub-key-andrew

## Phase A / Task 1: 中継用鍵と公開鍵

### 開始状態

```text
sync_pause_support_count=2
branch=feat/submit-hub-key-andrew
status=?? tasks/T-2026-08-12-submit-hub-key-andrew/
home_tunnel_name_matches=2
.tunnel.log
.tunnel_to_philip
marker_count=1
FILE /home/ubuntu/.tunnel_to_philip size=44 lines=1
LINE1=/home/ubuntu/.ssh/id_ed25519_andrewtophilip
MARKER_META /home/ubuntu/.tunnel_to_philip size=44 mtime=1783121767 mode=664
marker_sha256=776609f37ad24bd6232d0d9dcace5551f8057b381c69b8e48bf56774bafc1cd3
```

`home_tunnel_name_matches` は名前に `tunnel` を含む全項目の件数であり、目印の件数は
`.tunnel_to_*` を別に数えた `marker_count=1` である。目印は変更していない。

### 鍵の実在と権限

```text
-rw------- 1 ubuntu ubuntu 399 Jul  3 23:36 /home/ubuntu/.ssh/id_ed25519_andrewtophilip
-rw-r--r-- 1 ubuntu ubuntu 95 Jul  3 23:36 /home/ubuntu/.ssh/id_ed25519_andrewtophilip.pub
```

### 導出と対応検査

```text
derive_exit=0
95 /tmp/pub_derived.txt
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
target_derived_vs_adjacent_cmp=0
control_derive_exit=0
256 SHA256:zcSWxJOCKZZNmnZMv9N6FZkKwb/2BozprdV+hvdtIdk ubuntu@andrew (ED25519)
256 SHA256:zcSWxJOCKZZNmnZMv9N6FZkKwb/2BozprdV+hvdtIdk ubuntu@andrew (ED25519)
control_derived_vs_adjacent_cmp=0
target_vs_control_cmp=1
```

対象は導出結果と並置公開鍵が一致した。対照も導出結果とその並置公開鍵が一致し、
対象と対照は異なった。

### 変更前の基準値

```text
KNOWN_HOSTS size=1956 mtime=1783039635 mode=600
2250 /home/ubuntu/bin/keeper.sh
keeper_sha256=603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
```

## Phase A / Task 2: 中心への到達住所

### 三つの出所

SSH 設定:

```text
Host philip
    HostName 192.168.196.150
    Port 50072
    IdentityFile ~/.ssh/id_rsa_andrewtophilip
Host github.com
  HostName github.com
  IdentityFile ~/.ssh/id_ed25519_github
```

`/etc/hosts`:

```text
127.0.0.1 localhost
::1 localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.26 Andrew
```

Syncthing の一意な TCP 住所:

```text
tcp://127.0.0.1:22001
tcp://192.168.196.105:22000
tcp://192.168.196.106:22000
tcp://192.168.196.143:22000
tcp://192.168.196.150:22000
tcp://192.168.196.176:22000
tcp://192.168.196.227:22000
tcp://192.168.196.54:22000
tcp://192.168.196.58:22000
tcp://192.168.196.63:22000
tcp://192.168.196.78:22000
```

Syncthing の device 対応（住所を持つ項目）:

```text
hinton addresses=dynamic,tcp://192.168.196.78:22000
bengio addresses=dynamic,tcp://192.168.196.105:22000
philip addresses=tcp://192.168.196.150:22000,tcp://127.0.0.1:22001
Andrew addresses=dynamic
adam addresses=dynamic,tcp://192.168.196.58:22000
ilya addresses=dynamic,tcp://192.168.196.63:22000
dlsta addresses=dynamic,tcp://192.168.196.54:22000
lecun addresses=dynamic,tcp://192.168.196.176:22000
efros addresses=dynamic,tcp://192.168.196.227:22000
ian addresses=dynamic,tcp://192.168.196.143:22000
he addresses=dynamic,tcp://192.168.196.106:22000
```

### 候補と到達性

```text
candidate_count=12
classification_total=12
OPEN=9
OSERROR:No_route_to_host=1
REFUSED=2
127.0.0.1:50072 REFUSED
172.17.0.26:50072 REFUSED
192.168.196.54:50072 OPEN
192.168.196.58:50072 OPEN
192.168.196.63:50072 OPEN
192.168.196.78:50072 OPEN
192.168.196.105:50072 OPEN
192.168.196.106:50072 OPEN
192.168.196.143:50072 OPEN
192.168.196.150:50072 OSERROR:No_route_to_host
192.168.196.176:50072 OPEN
192.168.196.227:50072 OPEN
```

測定器の陽性対照:

```text
open_listener 127.0.0.1:51767 OPEN
closed_listener 127.0.0.1:32871 REFUSED
no_route_candidate 192.0.2.1:9 TIMEOUT
```

候補数12と分類合計12は一致した。OPEN、REFUSED、経路なし相当の TIMEOUT を
同じ測定器で出し分けた。

### 中心の確定と認証

Syncthing の device 名と住所の対応が `lecun=192.168.196.176:22000` を宣言し、
同じホストの既知の SSH ポート `50072` が OPEN だったため、中心の住所を
`192.168.196.176` と確定した。

```text
auth_exit=255
Warning: Permanently added '[192.168.196.176]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.176: Permission denied (publickey,password).
KNOWN_HOSTS_BEFORE_AUTH size=1956 mtime=1783039635 mode=600
KNOWN_HOSTS_AFTER_AUTH size=1956 mtime=1783039635 mode=600
1 /tmp/kh_audit.txt
```

認証は拒否された。追加先は `/tmp/kh_audit.txt` であり、通常の
`/home/ubuntu/.ssh/known_hosts` は size と mtime がともに不変だった。

### Phase A 秘匿検査と G1

```text
audit_sensitive_word_match:
162:ubuntu@192.168.196.176: Permission denied (publickey,password).
audit_private_header_match_count=0
decoy_sensitive_match_count=1
```

実記録の一致1件は SSH が出した認証方式名 `password` であり、区切りと値を伴わない。
秘密鍵の書き出し形は0件。同じ検査は一時ファイルの囮を1件検出した。

G1 は PASS。対象と並置公開鍵の対応、別鍵との差異、秘匿検査の実動、候補12件と
分類12件の一致、通常の known_hosts の前後不変をすべて実測した。

## Phase B: 公開鍵の版管理への提出

### 配置先の衝突確認

```text
scripts/sync/ entries:
keeper.sh
m2-sync.sh
new_experiment_branch.sh
rename_host_branch.sh
setup_host_autosync.sh
setup_host_servername.sh
scripts/sync/hub_keys/: ディレクトリなし
history:
f6ac77b feat(sync): derive hub from marker instead of hardcoded constant
df75c30 feat(sync): let a marker pause branch writes during a contract
a3027a0 fix(sync): define probe_shell before the --verify early exit
```

同名ファイルも用途の異なる同名ディレクトリも存在せず、衝突なしと判定した。

### 配置と公開鍵限定検査

```text
95 scripts/sync/hub_keys/andrew.pub
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
derived_vs_repository_cmp=0
head40=ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPsg
repository_PRIVATE_match_count=0
1 scripts/sync/hub_keys/andrew.pub
decoy_PRIVATE_match_count=1
```

先頭形、`PRIVATE` の不在、1行であることの三つが成立し、囮は同じ検査で1件を返した。
指紋とファイル全体は導出時の値と一致した。G2 は PASS。

## Phase C: 変更後の禁止領域確認

```text
conventions_rev=d422b08
marker_count_after=1
MARKER_META_AFTER /home/ubuntu/.tunnel_to_philip size=44 mtime=1783121767 mode=664
marker_sha256_after=776609f37ad24bd6232d0d9dcace5551f8057b381c69b8e48bf56774bafc1cd3
2250 /home/ubuntu/bin/keeper.sh
keeper_sha256_after=603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503
KNOWN_HOSTS_FINAL size=1956 mtime=1783039635 mode=600
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
```

目印の件数・metadata・sha256、稼働版の bytes・sha256、通常の known_hosts、
中継数と keeper 数は変更前と一致した。

## 同期抑止解除と台帳への初回返送

```text
repo 直下から消えた
/tmp/.sync-pause.released.T-2026-08-12-submit-hub-key-andrew
task_report_exit=0
verdict=partial
n_issuer_defects=3
report_sha256=3ce219915321410e22dc497011549460022d09748da7ab7352cec33884b96770
report_bytes=7135
replaced_blocks=0
```

初回返送後に `result.yaml` を pass へ確定し、最終版は記録 commit 後に再送する。

# audit — 中継公開鍵の提出とlecun住所の実測（ilya）

**task_id:** `T-2026-08-12-submit-hub-key-ilya`  **実行日:** 2026-08-12  
**実行ホスト:** `aolab`（契約上ilya）  **分岐:** `feat/submit-hub-key-ilya`

秘密鍵本文、目印、稼働版、常駐処理は変更していない。公開鍵・指紋・秘密鍵の経路名だけを扱う。

## 前提と参照解決

`context/conventions.md`の逐語参照:

```text
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

`conventions_rev=d422b08`。preflightは`4 PASS / 1 WARN / 4 SKIP / 0 FAIL`。
WARNは既知のhost mismatch、SKIPは`cuda_ext_loaded`、`deterministic_flags`、
`prereg_committed`、`frozen_source_hash`。

## Task 1: 中継鍵と公開鍵

### Step 1: 目印

出力（原文）:

```text
[markers]
.tunnel.log
.tunnel_to_philip
count=2
FILE /home/ubuntu/.tunnel_to_philip size=42 lines=1
LINE1=/home/ubuntu/.ssh/id_ed25519_ilyatophilip
marker_file_count=1
```

`tunnel`を含むhome直下のものは2件、`~/.tunnel_to_*`に一致する目印は1件。目印は1行の旧形式。

### Step 2–4: 実在、導出、対応確認

出力（原文。秘密鍵本文は出していない）:

```text
-rw------- 1 ubuntu ubuntu 399 Jul  3 23:36 /home/ubuntu/.ssh/id_ed25519_ilyatophilip
-rw-r--r-- 1 ubuntu ubuntu 94 Jul  3 23:36 /home/ubuntu/.ssh/id_ed25519_ilyatophilip.pub
derive_exit=0
94 /tmp/pub_derived.txt
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
[adjacent]
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
adjacent_cmp_exit=0
control_derive_exit=0
94 /tmp/pub_control.txt
256 SHA256:FKxsYLiBuhqenbXr5veKrwZ/Fy3T2Qz7t8obrAIx/Q4 ubuntu@lecun (ED25519)
fingerprints_differ=True
```

対象秘密鍵は権限600で実在する。公開鍵導出はexit 0。導出物と並置公開鍵は指紋一致かつ
バイト一致（cmp exit 0）。別用途鍵から一時導出した公開鍵は別の指紋になった。

## Task 2: 中心住所

### Step 1: 三つの出所

出力（原文）:

```text
[ssh_config]
Host philip
    HostName 192.168.196.150
    Port 50072
    IdentityFile /Users/dakyo-mba/.ssh/id_rsa_ilyatophilip
Host github.com
  HostName github.com
  IdentityFile ~/.ssh/id_ed25519_github
[etc_hosts]
127.0.0.1 localhost
::1 localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.14 aolab
[syncthing_tcp]
tcp://127.0.0.1:22001
tcp://192.168.196.105:22000
tcp://192.168.196.106:22000
tcp://192.168.196.143:22000
tcp://192.168.196.150:22000
tcp://192.168.196.176:22000
tcp://192.168.196.190:22000
tcp://192.168.196.227:22000
tcp://192.168.196.54:22000
tcp://192.168.196.58:22000
tcp://192.168.196.78:22000
[direct_devices]
direct_device_count=11
adam tcp://192.168.196.58:22000
andrew tcp://192.168.196.190:22000
aolab NO_TCP_ADDRESS
bengio tcp://192.168.196.105:22000
dlsta tcp://192.168.196.54:22000
efros tcp://192.168.196.227:22000
he tcp://192.168.196.106:22000
hinton tcp://192.168.196.78:22000
ian tcp://192.168.196.143:22000
lecun tcp://192.168.196.176:22000
philip tcp://127.0.0.1:22001,tcp://192.168.196.150:22000
lecun_candidate_count=1
lecun_candidate=tcp://192.168.196.176:22000
```

SSH設定とhostsにはlecunの宣言なし。Syncthingの直接device 11件のうち、名前`lecun`に対応する
候補は`192.168.196.176`の1件。

### Step 2–3: 到達性と住所確定

出力（原文）:

```text
A_open 127.0.0.1:45457 OPEN
B_closed 127.0.0.1:45457 REFUSED
C_noroute 192.0.2.1:22000 OSERROR:Network_is_unreachable
2 /tmp/reach_submit_hub_key_ilya.txt
candidate_count=1
192.168.196.176:50072 OPEN
```

陽性対照はOPEN・REFUSED・即時の経路なしを出し分けた。候補1件の分類1件で合計一致。
Syncthingのdevice名と住所の対応を材料に、中心住所を`192.168.196.176`と確定した。

### Step 4–5: 登録前認証とknown_hosts

出力（原文）:

```text
task_known_hosts_absent
Warning: Permanently added '[192.168.196.176]:50072' (ED25519) to the list of known hosts.
ubuntu@192.168.196.176: Permission denied (publickey,password).
ssh_exit=255
known_hosts size=1956 mtime=2026-08-03 22:14:59.236043451 +0000
1956 /home/ubuntu/.ssh/known_hosts
1 /tmp/kh_submit_hub_key_ilya.txt
```

`REACHABLE`は返らず、登録前認証は拒否された。契約の固定名`/tmp/kh_audit.txt`は前契約の9行が
残っていたため、タスク専用`/tmp/kh_submit_hub_key_ilya.txt`へ隔離した。禁止領域の
`~/.ssh/known_hosts`は変更前とサイズ・mtimeが一致し、隔離先だけ1行。

## Phase A終了時の非変更基準

出力（原文）:

```text
-rw-rw-r-- 1 ubuntu ubuntu 42 Jul  3 23:36 /home/ubuntu/.tunnel_to_philip
2250 /home/ubuntu/bin/keeper.sh
37fb7d0f97c4032052072940aacb4eed59494c70b725b06a473acf4e83e1c025  /home/ubuntu/.tunnel_to_philip
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
```

中継は0、keeperは1。不在語0が計数の対照。以後この値と最終値を比較する。

## Phase A秘匿検査とG1

出力（囮本文は外部へ送らないため件数だけ記録）:

```text
[audit_scan]
146:ubuntu@192.168.196.176: Permission denied (publickey,password).
[bait_count]
1
bait_scan_exit=0
```

監査本文の1件はSSHの認証方式名で、区切りと値が続く資格情報ではない。囮は1件検出された。
公開鍵対応、到達性、分類合計、known_hosts無変更を確認できたためG1はPASS。

## Task 3: 公開鍵の版管理配置

### Step 1: 既存構造

出力（原文）:

```text
scripts/sync/ は既存6ファイル
scripts/sync/hub_keys/: ディレクトリなし。作る
f6ac77b feat(sync): derive hub from marker instead of hardcoded constant
df75c30 feat(sync): let a marker pause branch writes during a contract
a3027a0 fix(sync): define probe_shell before the --verify early exit
ilya_pub_absent
```

`hub_keys`と同名ファイルは存在せず、用途衝突なし。

### Step 2–3: 公開鍵と三検査

出力（原文。先頭40バイトは公開鍵）:

```text
94 scripts/sync/hub_keys/ilya.pub
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIh9
0
private_scan_exit=1
1 scripts/sync/hub_keys/ilya.pub
derived_cmp_exit=0
1
bait_private_scan_exit=0
```

先頭は`ssh-`、`PRIVATE`一致0、行数1。`grep` exit 1は「一致なし」の意味であり件数ではない。
導出物と配置物はバイト一致し、指紋も一致。囮は`PRIVATE`を1件検出した。

### Step 4: handoff

`handoff.md`へ公開鍵の場所、指紋、中心住所、2行形式の目印案、登録前拒否を記録した。
実際の目印とlecunの受け入れ一覧は変更していない。G2はPASS。

## Phase C開始時の非変更確認

出力（原文）:

```text
-rw-rw-r-- 1 ubuntu ubuntu 42 Jul  3 23:36 /home/ubuntu/.tunnel_to_philip
2250 /home/ubuntu/bin/keeper.sh
37fb7d0f97c4032052072940aacb4eed59494c70b725b06a473acf4e83e1c025  /home/ubuntu/.tunnel_to_philip
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
known_hosts size=1956 mtime=2026-08-03 22:14:59.236043451 +0000
```

Phase A終了時と一致。目印・keeper・中継数・known_hostsは無変更。

## commit前検証と投影

出力（原文）:

```text
OK   T-2026-08-12-submit-hub-key-ilya
1 task(s), 0 failed
validate_exit=0
RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
{"base": "origin/phase0", "changed": 9, "checked": 9, "errors": [], "excluded": 0, "excluded_paths": [], "status": "pass", "violations": []}
forbidden_exit=0
diff_check_exit=0
taskindex_check_exit=0
inbox_check_exit=0
unmerged=0
```

公開鍵の指紋は導出時と一致し、`PRIVATE`一致0・1行。秘匿語の一致は契約の検査式と
SSH認証拒否メッセージだけで資格情報値は0件。Skillに従い`context/auto/`の3投影と
`tasks/inbox.md`を正規生成し、再生成差分なしを確認した。

## commit・push・PRと最終非変更確認

出力（原文）:

```text
806abe4 feat(sync): submit tunnel public key for ilya
HEAD -> feat/submit-hub-key-ilya
0 0
{"baseRefName":"phase0","headRefName":"feat/submit-hub-key-ilya","isDraft":false,"number":96,"state":"OPEN","url":"https://github.com/takuya3h/m2/pull/96"}
37fb7d0f97c4032052072940aacb4eed59494c70b725b06a473acf4e83e1c025  /home/ubuntu/.tunnel_to_philip
603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503  /home/ubuntu/bin/keeper.sh
ssh -N -L=0
keeper.sh=1
zzz_no_such_process=0
```

PR #96はOPEN・非Draft。上流との差は0。phase0へ統合していない。目印・稼働版・中継数は
変更前と一致した。

## 同期抑止解除

出力（原文）:

```text
released
repo 直下から消えた
-rw-rw-r-- 1 ubuntu ubuntu 0 Aug 12 21:02 /tmp/.sync-pause.released.T-2026-08-12-submit-hub-key-ilya
```

抑止はrepo外へ移動され、必要なら退避先から戻せる。

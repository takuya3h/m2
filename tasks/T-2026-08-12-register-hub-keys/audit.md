# T-2026-08-12-register-hub-keys audit

## Phase A — 現状の記録と控えの保存、提出物の照合

### 実行前提

```text
2
feat/register-hub-keys
?? tasks/T-2026-08-12-register-hub-keys/
```

- 稼働中の同期スクリプトには `sync-pause` が 2 箇所ある。
- 作業分岐は `feat/register-hub-keys`。
- 契約自身の未追跡ディレクトリ以外に開始時差分はない。

### Task 1 Step 1 — 受け入れ一覧の現状

```text
-rw-rw-r-- 1 ubuntu ubuntu 1504 Jul 29 17:33 /home/ubuntu/.ssh/authorized_keys
4 /home/ubuntu/.ssh/authorized_keys
4
31c96f80dd0ac97f632af95ecc00dcc6ec9d54948771d23aaf78a9ba95ec3694  /home/ubuntu/.ssh/authorized_keys
1504 1785346380 664
```

```text
bytes=1504
ends_with_newline=True
newline_count=4
31c96f80dd0ac97f632af95ecc00dcc6ec9d54948771d23aaf78a9ba95ec3694  /home/ubuntu/.ssh/authorized_keys
31c96f80dd0ac97f632af95ecc00dcc6ec9d54948771d23aaf78a9ba95ec3694  tasks/T-2026-08-12-register-hub-keys/authorized_keys.before
```

開始時点の権限は、契約の期待値 `600` ではなく `664` だった。Phase A では変更していない。
末尾は改行で終わっているため、追記前の改行追加は不要。

### Task 1 Step 2 — 登録済み鍵の解析

```text
parse_exit=0
4
4096 SHA256:hWCLg+DQJe40cDk5CQoFd1pShHt3SI8lHv90Gf/nGJo philip-to-lecun (RSA)
256 SHA256:KS+FRL3p+yF2prUwbbZZB587yx6pebLdQCpEkMhNgLc dakyo-mba@dmba.local (ED25519)
256 SHA256:MKli4Hqp8sYzekheqdjEYKJiYALrCkJqSKGZzZ+VY58 bengiotolecun (ED25519)
3072 SHA256:fOip68JPi/q8Hq9BjhqJ9Zate/2tYMa8/y8M9gZHR0s ubuntu@efros (RSA)
```

解析は成功し、4 件すべてに指紋と註釈がある。

### Task 1 Step 3 — 控えと秘密鍵検査

```text
31c96f80dd0ac97f632af95ecc00dcc6ec9d54948771d23aaf78a9ba95ec3694  tasks/T-2026-08-12-register-hub-keys/authorized_keys.before
private_hits=0
backup_cmp_exit=0
```

陽性対照:

```text
decoy_path=/tmp/reg_private_decoy_T-2026-08-12-register-hub-keys.Jsms81
decoy_private_hits=1
```

囮は `/tmp` にだけ作成し、版管理へ入れていない。実行基盤が `rm -f` を拒否したため、
測定後も上記の一時パスに残っている。

### Task 1 Step 4 — 戻し方

異常時は次を実行し、Task 1 Step 1 の内容へ戻す。ここでは実行していない。

```sh
cp tasks/T-2026-08-12-register-hub-keys/authorized_keys.before ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Task 2 Step 1 — 提出物

```text
total 16
drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 13 02:08 .
drwxrwxr-x 3 ubuntu ubuntu 4096 Aug 13 01:38 ..
-rw-rw-r-- 1 ubuntu ubuntu   95 Aug 13 02:08 andrew.pub
-rw-rw-r-- 1 ubuntu ubuntu   94 Aug 13 01:38 ilya.pub
578962c Merge remote-tracking branch 'origin/phase0' into feat/submit-hub-key-andrew
806abe4 feat(sync): submit tunnel public key for ilya
02e651b feat(sync): submit tunnel public key for andrew
FILE scripts/sync/hub_keys/andrew.pub bytes=95 lines=1
FILE scripts/sync/hub_keys/ilya.pub bytes=94 lines=1
pub_count=2
```

### Task 2 Step 2 — 提出物の指紋

```text
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
andrew_fingerprint_exit=0
ilya_fingerprint_exit=0
```

二件とも契約に固定された期待指紋と一致した。

### Task 2 Step 3 — 公開鍵だけであることの三検査

```text
=== scripts/sync/hub_keys/andrew.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPsg
private_hits=0
lines=1
=== scripts/sync/hub_keys/ilya.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIh9
private_hits=0
lines=1
```

両方とも先頭が `ssh-`、`PRIVATE` は 0 件、行数は 1。

### Task 2 Step 4 — 既登録照合と陽性対照

```text
andrew_grep_hits=0
andrew_awk_exact_hits=0
ilya_grep_hits=0
ilya_awk_exact_hits=0
positive_grep_hits=1
positive_awk_exact_hits=1
```

二つの照合方法で新規二指紋は未登録。既存指紋は両方の方法で 1 件となり、
照合が常に 0 を返す壊れ方ではない。

### 触っていない対象の開始時点

```text
=== tunnel_markers_before ===
-rw-rw-r-- 1 ubuntu ubuntu 43 Jul  3 23:36 /home/ubuntu/.tunnel_to_philip
=== keeper_bytes_before ===
2250 /home/ubuntu/bin/keeper.sh
=== ssh_other_files_before ===
total 88
drwx------ 3 ubuntu ubuntu 4096 Jul 22 08:23 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 13 06:51 ..
drwx------ 4 ubuntu ubuntu 4096 Jun 21 16:20 .remember
-rw------- 1 ubuntu ubuntu  475 Jul  1 09:11 config
-rw------- 1 ubuntu ubuntu  399 Jun 14 18:36 id_ed25519_github
-rw-r--r-- 1 ubuntu ubuntu   94 Jun 14 18:36 id_ed25519_github.pub
-rw------- 1 ubuntu ubuntu  399 Jul  3 23:36 id_ed25519_lecuntophilip
-rw-r--r-- 1 ubuntu ubuntu   94 Jul  3 23:36 id_ed25519_lecuntophilip.pub
-rw------- 1 ubuntu ubuntu  399 Jul 22 08:23 id_lecundeploy
-rw-r--r-- 1 ubuntu ubuntu   94 Jul 22 08:23 id_lecundeploy.pub
-rw------- 1 ubuntu ubuntu 3381 Jun 21 16:21 id_rsa_lecuntobengio
-rw-r--r-- 1 ubuntu ubuntu  739 Jun 21 16:21 id_rsa_lecuntobengio.pub
-rw------- 1 ubuntu ubuntu 2602 Jul  1 09:09 id_rsa_lecuntoefros
-rw-r--r-- 1 ubuntu ubuntu  566 Jul  1 09:09 id_rsa_lecuntoefros.pub
-rw------- 1 ubuntu ubuntu 2602 Jul  1 02:31 id_rsa_lecuntophilip
-rw-r--r-- 1 ubuntu ubuntu  566 Jul  1 02:31 id_rsa_lecuntophilip.pub
-rw------- 1 ubuntu ubuntu 5032 Jul  1 09:11 known_hosts
-rw------- 1 ubuntu ubuntu 4196 Jul  1 09:11 known_hosts.old
=== process_counts_before ===
ssh -N -L=0
keeper.sh=1
syncthing=2
zzz_no_such_process=0
```

## Gate G1

PASS。受け入れ一覧は解析成功、4件を記録済み。控えは原本と同一で秘密鍵語0、
陽性対照1。提出物は二件で、指紋一致、公開鍵三検査合格、既登録0、既存指紋の陽性対照1。

## Phase B — 追記と既存保持の照合

### 追記直前の再照合と権限是正

```text
31c96f80dd0ac97f632af95ecc00dcc6ec9d54948771d23aaf78a9ba95ec3694  /home/ubuntu/.ssh/authorized_keys
1504 1785346380 664
prechange_backup_cmp_exit=0
```

内容が控えと一致することを再確認した。契約が必須とする `600` へ権限を是正した。

```text
1504 1785346380 600
```

開始時の実測が `664` だったため、これは「600 のまま」ではなく追記前の是正である。

### Task 3 Step 1 — 追記

```text
andrew_append_exit=0
ilya_append_exit=0
```

検証済みの二ファイルを、andrew、ilya の順で末尾へ追記した。改行の追加はしていない。

### Task 3 Step 2 — 行数と権限

```text
6 /home/ubuntu/.ssh/authorized_keys
6
1693 600
```

### Task 3 Step 3 — 既存行と追加行

```text
parse_exit=0
6
4096 SHA256:hWCLg+DQJe40cDk5CQoFd1pShHt3SI8lHv90Gf/nGJo philip-to-lecun (RSA)
256 SHA256:KS+FRL3p+yF2prUwbbZZB587yx6pebLdQCpEkMhNgLc dakyo-mba@dmba.local (ED25519)
256 SHA256:MKli4Hqp8sYzekheqdjEYKJiYALrCkJqSKGZzZ+VY58 bengiotolecun (ED25519)
3072 SHA256:fOip68JPi/q8Hq9BjhqJ9Zate/2tYMa8/y8M9gZHR0s ubuntu@efros (RSA)
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
=== 消えた行 ===
missing_count=0
=== 増えた行 ===
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
added_count=2
```

### Task 3 Step 4 — 全行解析と追加指紋の完全一致

```text
andrew_added_exact=1
ilya_added_exact=1
nonempty_count=6
parsed_count=6
```

### Task 3 Step 5 — 控えとの差

```text
diff_exit=1
diff_lines=3
removed_lines=0
added_lines=2
4a5,6
> ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPsgBha1ixjhl+FPTvT6DLM1uX/sHTcDF2ZtPPlrMPSK ubuntu@Andrew
> ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIh9lhzA+MbfDupmEYLfJUOFV46aKpUF/gLRXwCfQ4IG ubuntu@aolab
```

`diff_exit=1` は差分が存在することを表す。差分は末尾への追加二行だけで、
削除行・既存行の変更はない。

## Gate G2

PASS。非空行は 6、権限は追記前に是正した `600` を維持、既存の消失 0、
追加 2、期待指紋は各 1、全 6 行を解析でき、控えとの差は追加だけだった。

## Phase C — 非変更対象の再測定

```text
=== tunnel_markers_after ===
-rw-rw-r-- 1 ubuntu ubuntu 43 Jul  3 23:36 /home/ubuntu/.tunnel_to_philip
=== keeper_bytes_after ===
2250 /home/ubuntu/bin/keeper.sh
=== ssh_other_files_after ===
total 88
drwx------ 3 ubuntu ubuntu 4096 Jul 22 08:23 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 13 06:58 ..
drwx------ 4 ubuntu ubuntu 4096 Jun 21 16:20 .remember
-rw------- 1 ubuntu ubuntu  475 Jul  1 09:11 config
-rw------- 1 ubuntu ubuntu  399 Jun 14 18:36 id_ed25519_github
-rw-r--r-- 1 ubuntu ubuntu   94 Jun 14 18:36 id_ed25519_github.pub
-rw------- 1 ubuntu ubuntu  399 Jul  3 23:36 id_ed25519_lecuntophilip
-rw-r--r-- 1 ubuntu ubuntu   94 Jul  3 23:36 id_ed25519_lecuntophilip.pub
-rw------- 1 ubuntu ubuntu  399 Jul 22 08:23 id_lecundeploy
-rw-r--r-- 1 ubuntu ubuntu   94 Jul 22 08:23 id_lecundeploy.pub
-rw------- 1 ubuntu ubuntu 3381 Jun 21 16:21 id_rsa_lecuntobengio
-rw-r--r-- 1 ubuntu ubuntu  739 Jun 21 16:21 id_rsa_lecuntobengio.pub
-rw------- 1 ubuntu ubuntu 2602 Jul  1 09:09 id_rsa_lecuntoefros
-rw-r--r-- 1 ubuntu ubuntu  566 Jul  1 09:09 id_rsa_lecuntoefros.pub
-rw------- 1 ubuntu ubuntu 2602 Jul  1 02:31 id_rsa_lecuntophilip
-rw-r--r-- 1 ubuntu ubuntu  566 Jul  1 02:31 id_rsa_lecuntophilip.pub
-rw------- 1 ubuntu ubuntu 5032 Jul  1 09:11 known_hosts
-rw------- 1 ubuntu ubuntu 4196 Jul  1 09:11 known_hosts.old
=== process_counts_after ===
ssh -N -L=0
keeper.sh=1
syncthing=2
zzz_no_such_process=0
```

目印の属性、keeper のバイト数、`~/.ssh/` 内の他の各項目の属性、中継・keeper・
syncthing の件数は開始時と一致した。表示に含まれる `..` は `/home/ubuntu` であり、
`~/.ssh/` 内のファイルではない。その時刻だけが `06:51` から `06:58` に変化した。

## Phase C — 検証と変更範囲

### 契約検証

```text
OK   T-2026-08-12-register-hub-keys

1 task(s), 0 failed
validate_exit=0
```

```text
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-12-register-hub-keys/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 5 件が該当: separated_source@tasks/T-2026-08-12-register-hub-keys/SPEC.md:350, separated_source@tasks/T-2026-08-12-register-hub-keys/SPEC.md:353, separated_source@tasks/T-2026-08-12-register-hub-keys/SPEC.md:356, separated_source@tasks/T-2026-08-12-register-hub-keys/SPEC.md:359, separated_source@tasks/T-2026-08-12-register-hub-keys/SPEC.md:406（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
```

```text
{"base": "origin/phase0", "changed": 7, "checked": 7, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

### 投影検査

```text
taskindex_check_exit=2
```

`tasks_summary.csv` に本taskの行、`followups.md` に3件、unknownsに2件、起票者の誤りに2件、
`results_recent.md` の総数に1件の未投影差分を検出した。

```text
inbox_check_exit=2
```

`tasks/inbox.md` に本taskの判断1件の未投影差分を検出した。契約の禁止9に従い、
`make taskindex` と `make inbox` は実行していない。

### 変更範囲

```text
status_lines=2
?? tasks/T-2026-08-12-register-hub-keys/
?? tasks/inbox.d/T-2026-08-12-register-hub-keys.md
unmerged=0
diff_check_exit=0
```

変更は契約ディレクトリと契約専用の判断受け皿に限られ、未解決マージはない。

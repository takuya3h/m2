# audit — T-2026-08-24-bengio-syncthing-node

申し送り #8「出力は要約せず `audit.md` へ貼る」に従う。
ホスト: bengio / repo: `~/slocal2/m2` / 実行日: 2026-08-23〜24 (JST)

---

## 0. 事前（技能書の手順 1-4）

```
$ touch .sync-pause
sync_pause_placed=0
$ grep -c "sync-pause" ~/bin/m2-sync.sh
2                      ← 2 なら抑止が効く版
$ git --no-pager status --porcelain | grep -c ''
1                      ← 本契約のディレクトリのみ
$ git branch --show-current
feat/bengio-syncthing-node
$ git --no-pager log -1 --format='%h %s'
e344f385 Merge pull request #140 from takuya3h/feat/philip-syncthing-hub
```

`make task-start` は実行していない。**`scripts/load_env.sh` が使えない**（合言葉が失われている。
前契約 T-2026-08-22-bengio-node-foundation 以降の既知事項）。分岐は既に作られていた。

### 検証とプリフライト

```
$ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-bengio-syncthing-node
OK   T-2026-08-24-bengio-syncthing-node

1 task(s), 0 failed
validate_exit=0
```

```
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-24-bengio-syncthing-node/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 5 件が該当: separated_source@tasks/T-2026-08-24-bengio-syncthing-node/SPEC.md:50, separated_source@tasks/T-2026-08-24-bengio-syncthing-node/SPEC.md:473, separated_source@tasks/T-2026-08-24-bengio-syncthing-node/SPEC.md:476, separated_source@tasks/T-2026-08-24-bengio-syncthing-node/SPEC.md:479, separated_source@tasks/T-2026-08-24-bengio-syncthing-node/SPEC.md:507（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
```

---

## Task 1 (Phase A) Step 1: 現状を要約値で記録する

```
$ for f in ~/.local/state/syncthing/*; do test -f "$f" && echo "$(sha256sum "$f") $(stat -c "%s %a" "$f")"; done
b53eba6d30ae9d45f7636ade10f85eeb462b0254f6129e9d96bba457669d4658  /home/ubuntu/.local/state/syncthing/cert.pem 794 664
d4928c2db9b5539b8b356ec6f7e77dcec65fca2c66bf0af883f7011fbe77d146  /home/ubuntu/.local/state/syncthing/config.xml 8495 600
99dfaa2cefb88b545e3e96d803fa87abccbb0cb93411637aec8d996fac5dafbb  /home/ubuntu/.local/state/syncthing/key.pem 288 600
config_dir_exists=1
config_files_count=3

$ ls -la ~/bin/syncthing; sha256sum ~/bin/syncthing
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:52 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
perm=644

$ ~/bin/syncthing --version
(eval):21: permission denied: /home/ubuntu/bin/syncthing
version_exit=126

$ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh

$ ls -a ~/ | grep -c "^\.tunnel_to_"
marker_count=0

$ du -sh ~/claude-sync/ ; find ~/claude-sync/ -type f | grep -c ""
8.0K	/home/ubuntu/claude-sync/
claude_sync_files=1
$ ls -la ~/claude-sync/
total 16
drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 23 17:39 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 23:19 ..
-rw-rw-r-- 1 ubuntu ubuntu  813 Aug 23 23:09 sync-alerts.log

$ sha256sum .stignore .stglobalignore
61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore
61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore
```

## Task 1 (Phase A) Step 2: 稼働しているものを数える

```
syncthing=0 []
keeper.sh=1 [('157746', '157741')]
ssh=6 [('1', '0'), ('129334', '1'), ('129345', '129334'), ('129411', '129366'), ('129415', '129411'), ('148463', '1')]
zsh=6 [('129346', '129345'), ('130112', '129615'), ('145431', '129615'), ('157741', '147259'), ('171845', '171844'), ('247695', '129615')]
zzz_no_such=0 []
--- keeper.sh の詳細（識別子と親） ---
pid=157746 ppid=157741 cmd=/bin/bash /home/ubuntu/bin/keeper.sh
python_exit=0
```

`ssh=6` は基底名に `ssh` を含むもの（`sshd` など）をすべて拾っている。
**中継かどうかは引数で判定する**（申し送り #3）。

```
ssh を含む processes の内訳(argv[0] の基底名): {'sshd -D [listener] 0 of 10-100 startups': 1, 'sshd: ubuntu [priv]': 1, 'sshd: ubuntu@notty': 1, 'sh': 1, 'node': 1, 'ssh-agent': 1}
tunnel_ssh_L=0 []
port_22=LISTEN
port_22000=-
port_22001=-
port_8384=-
listening_ports_all=[22, 17382, 42925, 46079, 46413]
python_exit=0
```

**同期処理 0 件、中継 0 件。** 肯定の対照 `zsh=6`、否定の対照 `zzz_no_such=0` で
走査が両方向に働いている。

⚠ **常駐処理 pid=157746 は前契約で起動した実体がそのまま生きている。**
前契約 T-2026-08-24-bengio-keeper-autosync の `unknowns[0]`
「本会期の終了後も残るか」は、**残った**が答えである。

## Task 1 (Phase A) Step 3: 設定の控えを取る

```
$ cp -a ~/.local/state/syncthing ~/.local/state/syncthing.bak.$(date +%Y%m%d-%H%M%S)
backup_exit=0
backup_dir=/home/ubuntu/.local/state/syncthing.bak.20260823-232244

$ ls -la ~/.local/state/ | grep syncthing
drwx------ 2 ubuntu ubuntu 4096 Aug 23 13:52 syncthing
drwx------ 2 ubuntu ubuntu 4096 Aug 23 13:52 syncthing.bak.20260823-232244

$ for f in <控え>/*; do test -f "$f" && sha256sum "$f"; done
b53eba6d30ae9d45f7636ade10f85eeb462b0254f6129e9d96bba457669d4658  …/cert.pem
d4928c2db9b5539b8b356ec6f7e77dcec65fca2c66bf0af883f7011fbe77d146  …/config.xml
99dfaa2cefb88b545e3e96d803fa87abccbb0cb93411637aec8d996fac5dafbb  …/key.pem
```

**3 件とも Step 1 の要約値と一致。控えは完全である。** 置き場所は repo の外。

### 画面の鍵の有無（値は出さない）

SPEC は `grep -o 'apikey>[^<]*' … | cut -c1-12` を指示するが、**これは実値の先頭を表示する。**
秘匿の値は出力しない規則があるため、**長さと空かどうかだけ**を測った。

```
apikey_elements=1
apikey[0]_len=32  empty=False
private_key_block_count=0
password_like_elements=['encryptionPassword']
```

**実値が入っている。** よって `config.xml` は**版管理へ置かない**（禁止 7）。
前契約（中心側）は伏せた控えを置いたが、本契約の `outputs.must_have` は `RESULT.md` だけで
控えの設置を求めていない。**置かない方が安全である。**

## Task 1 (Phase A) Step 4: 戻し方を記録する（実行しない）

```
chmod 644 ~/bin/syncthing                                  # 起動の引き金を外す
pkill -x syncthing                                         # 動いていれば終わらせる
cp -a ~/.local/state/syncthing.bak.20260823-232244/. ~/.local/state/syncthing/
rm -f ~/.tunnel_to_philip                                  # 消さないと常駐処理が張り直す
pkill -f 'ssh.*-L 22001:127.0.0.1:22000'                   # 中継を終わらせる
for f in ~/.local/state/syncthing/*; do test -f "$f" && sha256sum "$f"; done   # Step 1 と一致するか
```

**常駐処理（keeper）は止めない**（禁止 12）。引き金を外せば同期処理は再起動されない。
実行ファイルを v1.27.10 へ戻す必要がある場合は `~/.local/state/` ではなく
`~/bin/syncthing` を入れ替える（開始時の要約値
`32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`、26730145 B）。

**上記は記録しただけで、実行していない。**

## Task 1 (Phase A) Step 5: 中心の値を版管理から読む

```
$ cat scripts/sync/device_ids/philip.txt
3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
$ cat scripts/sync/device_ids/bengio.txt
4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO
$ grep -o 'device id="[^"]*" name="[^"]*"' ~/.local/state/syncthing/config.xml
device id="4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO" name="Bengio"
```

**自分の識別子は版管理の値と一致する。**
中心の識別子は前契約 RESULT.md の記載とも一致した（本文の転記ではなく版管理から読んだ）。

⚠ **登録名が `Bengio`（先頭が大文字）であり、`bengio` ではない。** Task 3 Step 2 で直す。

### 設定の現状（XML パーサで解析）

```
root=configuration version=37
folders_real=1
  id='default' path='/home/ubuntu/Sync' type='sendreceive' devices=['4NIRI4M']
devices_real=1
  id=4NIRI4M… name='Bengio' addrs=['dynamic']
  options/globalAnnounceEnabled = 'true'
  options/localAnnounceEnabled  = 'true'
  options/relaysEnabled         = 'true'
  options/autoUpgradeIntervalH  = '12'
  options/listenAddress         = 'default'
gui enabled=true tls=false address=127.0.0.1:8384
```

`grep -o 'folder id="[^"]*"'` は `default` のほかに `id=""` を返すが、これは
`<defaults>` の中の雛形である。**実体の共有フォルダは 1 件（`default`）。**
表示用の抽出と解析を混同しない（申し送り #6）。

## Task 1 (Phase A) Step 6: 中心への到達と認証を測る

```
$ ls -la ~/.ssh/id_ed25519_bengiotophilip
-rw------- 1 ubuntu ubuntu 411 Aug 23 13:51 /home/ubuntu/.ssh/id_ed25519_bengiotophilip
ls_key_exit=0

$ ssh -o BatchMode=yes -o ConnectTimeout=8 -o IdentitiesOnly=yes \
      -o UserKnownHostsFile=/tmp/kh_bsn.txt -o StrictHostKeyChecking=accept-new \
      -p 50072 -i ~/.ssh/id_ed25519_bengiotophilip 192.168.196.150 'echo REACHABLE' \
      > /tmp/bsn_ssh.txt 2>&1
ssh_exit_clean=255
--- 出力 ---
ubuntu@192.168.196.150: Permission denied (publickey,password).
reachable_count=0
```

🔴 **`REACHABLE` は返らなかった。認証が通らない。**

### 切り分け（どこまでが生きているか）

```
$ .venv/bin/python -c "socket で 192.168.196.150:50072 へ接続"
tcp_connect=OK banner=b'SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13.1'
```

**経路と待ち受けは生きている。** 住所 `192.168.196.150` と口 `50072` は正しい
（handoff §3.4 が `UNKNOWN` と残した「2 行目に何を書くか」は、**到達性については解けた**）。

```
$ ssh -v … 2>&1 | grep -E "Offering|Server accepts|Authentications that can continue|Permission denied"
debug1: Authentications that can continue: publickey,password
debug1: Offering public key: /home/ubuntu/.ssh/id_ed25519_bengiotophilip ED25519 SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 explicit
debug1: Authentications that can continue: publickey,password
ubuntu@192.168.196.150: Permission denied (publickey,password).
```

**鍵は提示されており、`Server accepts key` が出ない。** 中心が受け入れていない。

⚠ この計測で一度誤った。`ssh … | grep … | head` の直後に `echo "---"` を挟んでから
`${pipestatus[1]}` を読み、**`echo` の終了コード 0 を ssh の値だと表示してしまった。**
配管を挟まず取り直した値が上の `ssh_exit_clean=255` である。
申し送り #4 と同じ型の誤りが、**終了コードの取り出し方にも起きる。**

### 鍵の同一性（中身は出さない）

```
$ ssh-keygen -lf ~/.ssh/id_ed25519_bengiotophilip
256 SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 bengiotophilip (ED25519)
$ ssh-keygen -lf scripts/sync/hub_keys/bengio.pub
256 SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 bengiotophilip (ED25519)
```

**手元の秘密鍵と、版管理へ公開した公開鍵は同じ対である。** 本ホスト側に誤りは無い。

```
$ ls -la scripts/sync/hub_keys/
andrew.pub  bengio.pub  ilya.pub  lecun.pub      ← 4 台分が公開済み（philip.pub は無い）
```

### 原因の所在（版管理から確かめた）

```
$ grep -rn "authorized_keys" tasks/T-2026-08-2[2-9]-*/SPEC.md
tasks/T-2026-08-22-{andrew,bengio,ilya,lecun}-node-foundation/SPEC.md:126:  ssh-keygen -lf ~/.ssh/authorized_keys 2>&1
tasks/T-2026-08-22-philip-hub-foundation/SPEC.md:105:                 ssh-keygen -lf ~/.ssh/authorized_keys 2>&1
tasks/T-2026-08-24-philip-syncthing-hub/SPEC.md:374:                   sha256sum ~/.ssh/authorized_keys
```

**再構築後（2026-08-22 以降）の契約は、受け入れ一覧を「読む」だけである。**
書き換える契約は `T-2026-08-12-register-hub-keys` ただ一つで、**保守作業の前のものである。**
鍵は保守作業の後に作り直されているため、当時登録した指紋はもう合わない。

さらに前契約 `T-2026-08-24-philip-syncthing-hub` は
**禁止 3「鍵を生成・変更・削除する。受け入れ一覧を変更する」を自ら課しており**、
その `RESULT.md` の完了判定 18 は受け入れ一覧を **`UNKNOWN`** と記録している。

**結論: 中心の `~/.ssh/authorized_keys` に 4 台の公開鍵を入れる契約が、まだ実行されていない。**
本契約は禁止 1（他ホストの状態を変更する）と禁止 3（受け入れ一覧を変更する）により
**bengio 側からこれを直せない。**

---

## Gate G1（Phase A 直後）— **fail / on_fail: stop**

| 要求 | 実測 | 判定 |
|---|---|---|
| 設定・実行ファイル・常駐処理の要約値を記録 | `config.xml` `d4928c2d…` 600 / `syncthing` `32ab747e…` 644 / `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` | pass |
| 実行権が落ちている | **644**（`--version` が exit 126 で拒まれることでも裏づけ） | pass |
| 目印が零件 | `marker_count=0` | pass |
| 稼働を両方向の対照つきで計数 | 同期処理 0 / 中継 0。肯定 `zsh=6`、否定 `zzz_no_such=0` | pass |
| 控えを版管理の外へ | `~/.local/state/syncthing.bak.20260823-232244`。3 件とも要約値一致 | pass |
| **中心への認証が通る** | **`ssh_exit=255` `Permission denied (publickey,password)`。`REACHABLE` 0 件** | **fail** |

**G1 = fail。`on_fail: stop` に従い、ここで停止する。**

SPEC の想定外の表は「中心への認証が通らない → **停止して報告。中継が張れない。目印を作らない**」
と定める。`governance.escalate_if` の第一項にも該当する。

**以降は実行していない。**

| 実行しなかったもの | 理由 |
|---|---|
| Task 2（版を `v2.1.3` へ揃える） | G1 が stop。繋がらない相手に合わせても切り分けにならない |
| Task 3（設定の組み立て） | 同上。半端に組むと次の実行者が開始状態を測れなくなる |
| Task 4（目印・中継・実行権） | **SPEC が明示的に「目印を作らない」と定める** |
| Task 5 Step 1-3（届くことの確認） | 中継が無いため測れない |

**本ホストの状態は開始時から変わっていない。** 加えたのは repo の外の控え 1 件だけである。

### 停止時点の状態が開始時と同じであることの確認

```
$ for f in ~/.local/state/syncthing/*; do test -f "$f" && echo "$(sha256sum "$f") $(stat -c "%s %a" "$f")"; done
b53eba6d30ae9d45f7636ade10f85eeb462b0254f6129e9d96bba457669d4658  /home/ubuntu/.local/state/syncthing/cert.pem 794 664
d4928c2db9b5539b8b356ec6f7e77dcec65fca2c66bf0af883f7011fbe77d146  /home/ubuntu/.local/state/syncthing/config.xml 8495 600
99dfaa2cefb88b545e3e96d803fa87abccbb0cb93411637aec8d996fac5dafbb  /home/ubuntu/.local/state/syncthing/key.pem 288 600

$ ls -la ~/bin/syncthing; sha256sum ~/bin/syncthing
-rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:52 /home/ubuntu/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing

$ sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh

marker_count=0
tunnel_log_exists=0
syncthing_log_exists=0

$ du -sh ~/claude-sync/ ; find ~/claude-sync/ -type f | grep -c ""
8.0K	/home/ubuntu/claude-sync/
claude_sync_files=1

$ .venv/bin/python  (稼働と待ち受け)
syncthing   =0 []
keeper.sh   =1 ['157746']
tunnel      =0 []
zsh         =4 ['130112', '145431', '157741', '247695']
zzz_no_such =0 []
port_22=LISTEN
port_22000=-
port_22001=-
port_8384=-
```

**開始時と一致する。** 設定 3 件の要約値、実行ファイルの要約値と権限 644、
常駐処理 2 件の要約値、目印 0 件、共有領域 8.0K / 1 件、同期処理 0 件、中継 0 件、
`22000` `22001` `8384` とも待ち受けなし。**`~/.tunnel.log` も `~/.syncthing.log` も無い。**
本契約が加えたのは repo の外の控え 1 件だけである。

---

## Task 5 (Phase D): 報告（Step 1-3 は中継が無いため未実行）

`~/claude-sync/probe-bengio.txt` は**作っていない。** 中継が無い以上、届いたかを測れず、
版管理外の共有領域に痕跡だけが残るためである。共有領域は開始時のまま **8.0K / 1 件**。

### 送信前の秘匿検査

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|apikey|password|passphrase" \
    tasks/T-2026-08-24-bengio-syncthing-node/*
（該当 22 件。内訳は次の 3 種のみ）
  a) SPEC 本文の検査命令そのもの（SPEC.md:157, 486）
  b) 要素の「名前」と長さの記録（apikey_elements=1 / apikey[0]_len=32 / 'encryptionPassword'）
  c) ssh が返した認証方式の一覧（"Permission denied (publickey,password)"）
```

**判定は件数ではなく形で行った。** 語に区切りと値が続く形は **1 件も無い。**
`apikey` は**長さ 32 という事実**だけを記しており、値は本文のどこにも現れない。
`config.xml` は版管理へ置いていない（控えは repo の外の
`~/.local/state/syncthing.bak.20260823-232244` だけにある）。**削るものは無い。**

陽性対照:

```
$ printf '<語=値 の行 2 種>\n<語:値 の行>\n<鍵の書き出しの標識行>\n' > /tmp/bsn_decoy.md
$ grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|apikey|password|passphrase" /tmp/bsn_decoy.md
control_hit_count=4
decoy_removed=0        ← 確認後に削除。commit していない
```

**囮の中身はここへ写さない。** 写すと本文が次回の検査に引っかかる。

### 検証

```
$ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-bengio-syncthing-node
OK   T-2026-08-24-bengio-syncthing-node

1 task(s), 0 failed
validate_exit=0

$ source .venv/bin/activate && make task-preflight TASK=T-2026-08-24-bengio-syncthing-node
RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
P9 spec_lint  WARN  separated_source@SPEC.md:50,473,476,479,507

$ source .venv/bin/activate && make forbidden-check
{"base": "origin/phase0", "changed": 6, "checked": 6, "errors": [], "excluded": 0,
 "excluded_paths": [], "generated_directories": ["context/auto/"],
 "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

### 生成物の検査（禁止 5 により再生成しない。記録だけ）

```
$ make taskindex-check > /tmp/bsn_ti.txt 2>&1; echo $?
taskindex_check_exit=2      taskindex_diff_lines=335
$ make inbox-check > /tmp/bsn_ib.txt 2>&1; echo $?
inbox_check_exit=2          inbox_diff_lines=42
```

再生成した場合に入る行:

```
+T-2026-08-24-bengio-syncthing-node,impl,stopped,bengio,,false,0,0,1,0,0,5,4,10,5,T-2026-08-24-philip-syncthing-hub
```

**再生成していない。**（配管を挟まずファイルへ落として終了コードを取った。
`| head` を通すと SIGPIPE の 141 になり、真の 2 が隠れる。前契約で実際に起きた。）

### 変更範囲

```
$ git --no-pager status --porcelain
?? tasks/T-2026-08-24-bengio-syncthing-node/
?? tasks/inbox.d/T-2026-08-24-bengio-syncthing-node.md
count=2
```

**契約のディレクトリと受け皿の 2 件だけ。** 開始時の未追跡も 1 件（本契約のディレクトリ）
だけだったので、失ったものは無い。`~/.local/state/` `~/bin/` `~/.ssh/` は版管理の外、
`.sync-pause` は `.gitignore` 済みで現れない。

---

# 再開（2026-08-24、PR #142 マージ後）

前回は G1 で停止した（中心が bengio の鍵を受け入れなかった）。その後
`T-2026-08-24-philip-accept-node-keys`（PR #142）が origin/phase0 へ入り、
分岐 `feat/bengio-syncthing-node-2` で再実行した。

## 0. 事前

    sync_pause_placed=yes
    m2sync_supports=2
    worktree_dirty=1
    branch=feat/bengio-syncthing-node-2
    head=a99e317c Merge pull request #142 from takuya3h/feat/philip-accept-node-keys

### 検証とプリフライト

    OK   T-2026-08-24-bengio-syncthing-node
    1 task(s), 0 failed
    validate_exit=0

    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS tasks/T-2026-08-24-bengio-syncthing-node/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              WARN 規則 8 件のうち 5 件が該当: separated_source@SPEC.md:50,473,476,479,507（終了コードは変わらない）
    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
    preflight_exit=0

## Task 1 (Phase A) Step 1: 現状（前回と同一）

    b53eba6d30ae9d45f7636ade10f85eeb462b0254f6129e9d96bba457669d4658  cert.pem 794 664
    d4928c2db9b5539b8b356ec6f7e77dcec65fca2c66bf0af883f7011fbe77d146  config.xml 8495 600
    99dfaa2cefb88b545e3e96d803fa87abccbb0cb93411637aec8d996fac5dafbb  key.pem 288 600
    -rw-r--r-- 1 ubuntu ubuntu 26730145 Aug 23 13:52 /home/ubuntu/bin/syncthing
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
    (eval):1: permission denied: /home/ubuntu/bin/syncthing
    実行できない（権限）
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
    marker_count=0
    8.0K	/home/ubuntu/claude-sync/
    files=1
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore

共有領域の詳細（開始時）

    -rw-rw-r-- 1 ubuntu ubuntu 4031 Aug 24 10:40 sync-alerts.log
    du_bytes=4031  files=1
    m2 repo: 51G   （SPEC の「約十九ギガ」と食い違う）
    ~/slocal2/m2/.stfolder は 8/2 から既に存在（syncthing-folder-29c1b2.txt 108 B）

## Task 1 (Phase A) Step 2: 稼働（両方向の対照つき）

    syncthing=0 []
    keeper.sh=1 [('157746', '157741')]
    ssh=6 [('1', '0'), ('148463', '1'), ('270628', '1'), ('270639', '270628'), ('270705', '270660'), ('270709', '270705')]
    zsh=5 [('157741', '1'), ('171845', '171844'), ('270640', '270639'), ('272972', '270766'), ('274582', '270766')]
    zzz_no_such=0 []

## Task 1 (Phase A) Step 3: 控え

    drwx------ 2 ubuntu ubuntu 4096 Aug 23 13:52 syncthing
    drwx------ 2 ubuntu ubuntu 4096 Aug 23 13:52 syncthing.bak.20260823-232244
    drwx------ 2 ubuntu ubuntu 4096 Aug 23 13:52 syncthing.bak.20260824-003520
    apikey_elements=1
    len=32 empty=False        ← 値は出していない

## Task 1 (Phase A) Step 5: 中心の値と自分の識別子

    philip: 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
    bengio: 4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO
    device id="4NIRI4M-...-X52VHQO" name="Bengio"        ← 先頭が大文字。Task 3 Step 2 で直す
    folder id="default" label="Default Folder" path="/home/ubuntu/Sync" type="sendreceive"
    <configuration version="37"
    in_config=True

## Task 1 (Phase A) Step 6: 中心への認証 — **通った**

禁止 1 の但し書き（中心で命令を実行してはならない）を守るため、SPEC の
`ssh … 'echo REACHABLE'` ではなく `ssh -N`（命令を伴わない）で測った。

    ssh_exit=124          ← timeout による終了。-N は保持し続けるため
    authenticated=1
    accepts_key=1
    denied=0

    debug1: Server accepts key: /home/ubuntu/.ssh/id_ed25519_bengiotophilip ED25519 SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 explicit
    Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey".
    debug1: Requesting no-more-sessions@openssh.com
    debug1: Entering interactive session.
    debug1: Remote: /home/ubuntu/.ssh/authorized_keys:3: key options: agent-forwarding port-forwarding pty user-rc x11-forwarding
    Transferred: sent 3396, received 3868 bytes, in 11.4 seconds
    debug1: Exit status 0

**Gate G1 — pass。**

## Task 2 (Phase B): 版を中心に揃える

    curl_exit=0
    -rw-rw-r-- 1 ubuntu ubuntu 11821325 Aug 24 00:41 /tmp/st_v2_bengio.tar.gz
    f929eb8e5b72a85543eeeefb2c38f34a68e0c530e70758a2905b78840c76602c  /tmp/st_v2_bengio.tar.gz
    syncthing-linux-amd64-v2.1.3/

展開したものの要約値（中心の実測値と照合）

    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4  /tmp/syncthing-linux-amd64-v2.1.3/syncthing
    中心（前契約 audit.md:308）: e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4  27045912 bytes  v2.1.3
    → 一致

置き換え（旧版は /tmp/syncthing.v1.27.10.bak へ退避。要約値 32ab747e…）

    -rw-r--r-- 1 ubuntu ubuntu 27045912 Aug 24 10:33 /home/ubuntu/bin/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4  /home/ubuntu/bin/syncthing

## Task 3 (Phase B): 設定を組み立てる

    own_name: Bengio -> bengio
    hub_device_added: id=3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE name=philip address=tcp://127.0.0.1:22001
    globalAnnounceEnabled: true -> false
    relaysEnabled: true -> false
    autoUpgradeIntervalH: 12 -> 0
    localAnnounceEnabled: true (unchanged)
    folders: [('claude-sync', '/home/ubuntu/claude-sync', 'sendreceive'), ('m2', '/home/ubuntu/slocal2/m2', 'sendreceive')]

### Step 6: 書式と権限

    xml_ok
    device_count=2
      id=4NIRI4M-...-X52VHQO name=bengio address=['dynamic']
      id=3J4TRX4-...-DZOCQQE name=philip address=['tcp://127.0.0.1:22001']
    folder_count=2
      id=claude-sync path=/home/ubuntu/claude-sync type=sendreceive shared=['4NIRI4M', '3J4TRX4']
      id=m2 path=/home/ubuntu/slocal2/m2 type=sendreceive shared=['4NIRI4M', '3J4TRX4']
    globalAnnounceEnabled=false
    localAnnounceEnabled=true
    relaysEnabled=false
    autoUpgradeIntervalH=0
    600 11085
    sha=fdc3d29452422dc8ea4ce5e54ae1d06fcb40a5edfa276c0aae46b5c1b74c2358

**Gate G2 — pass。**

### 利用者による追加の編集（`<defaults>` の folder ひな型の削除）

利用者が `<defaults>` 配下の `<folder id="" path="~">` を削除し、控えを
`/tmp/config.xml.before_folder_fix` に取った。位置を控えとの差分で確かめた。

    before root_children=['folder', 'folder', 'device', 'device', 'gui', 'ldap', 'options', 'defaults']
    before top-level folders=[('claude-sync', '/home/ubuntu/claude-sync'), ('m2', '/home/ubuntu/slocal2/m2')]
    before defaults children=[('folder', '', '~'), ('device', '', None), ('ignores', None, None)]

    diff: 162,202d161
    <         <folder id="" label="" path="~" type="sendreceive" ...>   ← <defaults> の内側のみ
    diff_lines=47

    after  root_children=['folder', 'folder', 'device', 'device', 'gui', 'ldap', 'options', 'defaults']
    after  defaults children=[('device', ''), ('ignores', None)]
    after  top-level folders=[('claude-sync', ...), ('m2', ...)]   ← 変わらず 2 件

**最上位の共有フォルダは編集の前後とも `claude-sync` と `m2` の 2 件だけである。**
`<defaults><folder>` は新規フォルダ追加時の初期値のひな型であり、同期対象ではない。
削除は無害だが、「ホーム全体が共有される状態だった」という事実は無い。

## Task 4 (Phase C): 中継を張り、繋ぐ

### Step 1: 目印

    -rw------- 1 ubuntu ubuntu 60 Aug 24 11:03 /home/ubuntu/.tunnel_to_philip
    lines=2
    marker_count=1
    placed_at=2026-08-24 11:03:09 UTC

### Step 3: 中継が立った

**一度目の走査は偽陽性だった。** `pgrep -f 'ssh.*-L 22001:127.0.0.1:22000'` が
**自分自身の待機命令の文字列**を拾った（申し送り #3 のとおり）。ポートだけで測り直した。

    port_22=LISTEN
    port_22000=-
    port_22001=-        ← 一度目（11:03:38）の実際の状態
    port_8384=-

改めて `/proc/net/tcp` のみで待ったところ

    pid=321160 start=2026-08-24 11:10:02 UTC        ← 目印から 413 秒
    pid=157746 start=2026-08-23 17:39:05 UTC        ← keeper（親）
    ssh -N -L 22001:127.0.0.1:22000 -p 50072 -i <KEYDIR>/id_ed25519_bengiotophilip -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@192.168.196.150

    ~/.tunnel.log:
    Warning: Permanently added '[192.168.196.150]:50072' (ED25519) to the list of known hosts.

**引数に中心の住所 `ubuntu@192.168.196.150` を含む。**

### Step 4: 実行権（利用者が戻した）

    ctime=2026-08-24 12:52:02 +0000  mtime=2026-08-24 10:33:15 +0000  mode=755
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4

**中継の成立（11:10:02）が実行権の復帰（12:52:02）より 1 時間 42 分早い。順序は守られている。**
要約値は Task 2 と同じ。

### Step 5: 起動

    syncthing_started_at=2026-08-24 13:10:04 UTC       ← 実行権の復帰から 1082 秒
    syncthing_count=2
      pid=332564 ppid=157746 cmd=/home/ubuntu/bin/syncthing serve --no-browser    ← 親は keeper
      pid=332580 ppid=332564 cmd=/home/ubuntu/bin/syncthing serve --no-browser    ← その子
    port_22=LISTEN port_22000=LISTEN port_22001=LISTEN port_8384=LISTEN

    syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64) builder@github.syncthing.net 2026-08-03 21:36:05 UTC

`~/.syncthing.log`（識別子は先頭 7 文字のみ syncthing 自身が出す）

    13:10:02 INF syncthing v2.1.3 "Hafnium Hornet" ...
    13:10:02 INF Archiving a copy of old config file format (path=.../config.xml.v37)
    13:10:02 INF TCP listener starting (address="[::]:22000")
    13:10:02 INF GUI and API listening (address=127.0.0.1:8384)
    13:10:02 INF Loaded configuration (name=bengio)
    13:10:02 INF Loaded peer device configuration (device=3J4TRX4 name=philip address="[tcp://127.0.0.1:22001]")
    13:10:02 INF Ready to synchronize (folder.id=claude-sync folder.type=sendreceive)
    13:10:02 INF Established secure connection (device=3J4TRX4 connection.remote=127.0.0.1:22001 connection.type=tcp-client connection.crypto=TLS1.3-TLS_AES_128_GCM_SHA256)
    13:10:02 INF Ready to synchronize (folder.id=m2 folder.type=sendreceive)
    13:10:02 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001 remote.name=philip remote.client=syncthing remote.version=v2.1.3)
    13:10:02 INF Completed initial scan (folder.id=claude-sync)
    13:10:03 INF Peer has a new index ID (device=3J4TRX4 folder.id=claude-sync indexid=0x926FBB42EBBA2DBD)
    13:10:03 INF Peer has a new index ID (device=3J4TRX4 folder.id=m2 indexid=0x29601E30C53CB192)
    13:10:10 INF Synced file (folder.id=claude-sync file.name=sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log file.size=4784 blocks.local=0 blocks.download=1)
    13:10:22 INF Detected NAT services (count=0)

**自動更新の記録は無い。** `autoUpgradeIntervalH=0` が効いている。

### Step 6: 設定の保持

    config_version=52                       ← 37 から移行された（要約値は変わる）
    folders=[('claude-sync', '/home/ubuntu/claude-sync', 'sendreceive'), ('m2', '/home/ubuntu/slocal2/m2', 'sendreceive')]
    devices=[('3J4TRX4', 'philip', ['tcp://127.0.0.1:22001']), ('4NIRI4M', 'bengio', ['dynamic'])]
    globalAnnounceEnabled=false
    localAnnounceEnabled=true
    relaysEnabled=false
    autoUpgradeIntervalH=0
    mode=600 size=11330

**Gate G3 — pass。**

## Task 5 (Phase D): 届くことの確認

### Step 1: 自分から中心へ送る

    -rw-rw-r-- 1 ubuntu ubuntu 40 Aug 24 13:10 /home/ubuntu/claude-sync/probe-bengio.txt
    2d693215c54633e8060558f7f42890ce48927c8938e2bbb4fbde758efbf66fbc  probe-bengio.txt
    40 bytes   created_at=2026-08-24 13:10:57 UTC

中心へ届いたかを、**中心で命令を実行せず**に自ホストの索引から読んだ
（`127.0.0.1:8384` の REST。合言葉は変数に読み込み、画面へ出していない）

    claude-sync  philip_completion=100.0000% needBytes=0 needItems=0 globalBytes=9585
    m2           philip_completion=100.0000% needBytes=0 needItems=0 globalBytes=40743989547
    hub_connected=True addr=127.0.0.1:22001 clientVersion=v2.1.3
    probe global: size=40 modifiedBy=4NIRI4M deleted=False
    probe availability=[{'id': '3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE', 'fromTemporary': False}]

**`availability` に philip の識別子がある。bengio が作った試験ファイルを中心が保有している。**

### Step 2: 中心から届いたものと、共有領域の増減

    drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 24 13:10 .stfolder
    -rw-rw-r-- 1 ubuntu ubuntu 4761 Aug 24 13:10 sync-alerts.log
    -rw-rw-r-- 1 ubuntu ubuntu 4784 Aug 24 12:59 sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log
    -rw-rw-r-- 1 ubuntu ubuntu   40 Aug 24 13:10 probe-bengio.txt

    開始時: du_bytes=4031  files=1
    終了時: du_bytes=9702  files=4

**記録は上書きではなく衝突ファイルになった。** `sync-alerts.sync-conflict-20260824-131007-4NIRI4M.log`
が生まれ、両方の内容が残っている。**消えたものは無い。**

folder の進み方（13:11:44 時点）

    claude-sync  state=idle           local=3/9585B        global=3/9585B        need=0/0B          errors=0
    m2           state=sync-preparing local=3646/40737661512B global=3720/40743989547B need=1413/14832654763B errors=0

**repo は約 40.7 GB（SPEC の「約十九ギガ」と食い違う）。完了を待たない。**
残り 1413 件 / 約 14.8 GB。`.stignore` が `.git` を除外しているため git の操作とは衝突しない。

### Step 3: 触っていないものの無変更

    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  /home/ubuntu/bin/keeper.sh
    marker_count=1
    m2sync_sha=bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f

keeper.sh と m2-sync.sh は Task 1 と同じ要約値。目印は 1 件。

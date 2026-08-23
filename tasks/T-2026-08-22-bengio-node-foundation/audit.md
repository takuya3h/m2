# audit — T-2026-08-22-bengio-node-foundation (bengio)

実行ホスト: `Bengio`  日時(JST): 2026-08-23 22:46:28

## Phase A / Task 1 / Step 1: 開始状態

### 版管理が最新であることの確認
```
$ git fetch origin && git --no-pager log -1 --format="%h %s"
8eec82ec Merge pull request #121 from takuya3h/feat/philip-hub-foundation
$ git --no-pager log -1 --format="%h %s" origin/phase0
8eec82ec Merge pull request #121 from takuya3h/feat/philip-hub-foundation
$ git --no-pager rev-list --left-right --count HEAD...origin/phase0
0	0
$ git branch --show-current
feat/bengio-node-foundation
```

### ls -la ~/
```
total 380
drwxr-x---  1 ubuntu ubuntu   4096 Aug 23 13:45 .
drwxr-xr-x  1 root   root     4096 Aug 21 21:20 ..
-rw-r--r--  1 ubuntu ubuntu    220 Mar 31  2024 .bash_logout
-rw-r--r--  1 ubuntu ubuntu   3797 Aug 18 09:17 .bashrc
drwx------  8 ubuntu ubuntu   4096 Aug 23 13:45 .cache
drwxrwxr-x 12 ubuntu ubuntu   4096 Aug 23 13:45 .claude
-rw-------  1 ubuntu ubuntu  47562 Aug 23 13:45 .claude.json
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 23 13:44 .config
drwx------  4 ubuntu ubuntu   4096 Aug 21 21:16 .copilot
drwxrwxr-x  3 ubuntu ubuntu   4096 Aug 21 21:16 .dotnet
drwx------  2 ubuntu ubuntu   4096 Aug 21 21:28 .homebrew
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 21 21:22 .local
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 18 09:17 .oh-my-zsh
-rw-r--r--  1 ubuntu ubuntu    833 Aug 18 09:17 .profile
drwx------  3 ubuntu ubuntu   4096 Aug 23 13:44 .ssh
-rw-r--r--  1 ubuntu ubuntu      0 Aug 21 21:20 .sudo_as_admin_successful
drwxr-x---  5 ubuntu ubuntu   4096 Aug 23 12:39 .vscode-server
-rw-rw-r--  1 ubuntu ubuntu    183 Aug 22 02:17 .wget-hsts
-rw-rw-r--  1 ubuntu ubuntu  50409 Aug 23 12:40 .zcompdump
-rw-rw-r--  1 ubuntu ubuntu  52771 Aug 23 13:45 .zcompdump-Bengio-5.9
-r--r--r--  1 ubuntu ubuntu 119936 Aug 23 13:45 .zcompdump-Bengio-5.9.zwc
-rw-------  1 ubuntu ubuntu   1978 Aug 23 13:45 .zsh_history
-rw-rw-r--  1 ubuntu ubuntu    192 Aug 18 08:46 .zshenv
-rw-rw-r--  1 ubuntu ubuntu   1672 Aug 21 21:28 .zshrc
-rw-r--r--  1 ubuntu ubuntu     26 Aug 18 09:17 .zshrc.pre-oh-my-zsh
drwxr-xr-x  2 ubuntu ubuntu   4096 May 12  2024 local
drwxrwxr-x  2 ubuntu ubuntu   4096 Sep 29  2025 slocal1
drwxr-xr-x 12 ubuntu ubuntu   4096 Jun 21 17:30 slocal2
```

### home_entries
```
home_entries=26
```

### ls -la ~/.ssh/
```
total 40
drwx------ 3 ubuntu ubuntu 4096 Aug 23 13:44 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 13:45 ..
-rw------- 1 ubuntu ubuntu  746 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 09:17 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 09:17 config.d
-rw------- 1 ubuntu ubuntu  387 Aug 23 13:43 id_ed25519
-rw-r--r-- 1 ubuntu ubuntu   82 Aug 23 13:43 id_ed25519.pub
-rw------- 1 ubuntu ubuntu  978 Aug 23 13:44 known_hosts
-rw-r--r-- 1 ubuntu ubuntu  142 Aug 23 13:38 known_hosts.old
```

### ssh-keygen -lf ~/.ssh/authorized_keys
```
4096 SHA256:Vrh/uPWK0qwR5eV9Ywtm+tFajl8S/quBOAL+CZWfXrw dakyo-mba@dmba.local (RSA)
```

### ls -la ~/bin/
```
ls: cannot access '/home/ubuntu/bin/': No such file or directory
```

### ls -la ~/.local/state/syncthing/
```
ls: cannot access '/home/ubuntu/.local/state/syncthing/': No such file or directory
```

### cat ~/.zshenv
```
# Must have Path exports:
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:$CPATH
```

### 未追跡・変更の件数（開始時）
```
$ git --no-pager status --porcelain | grep -c ""
9
$ git --no-pager status --porcelain
 M README.md
 M docs/experiment_log.md
?? docs/analysis_scripts/
?? docs/research_review_and_next_plan_2026-08-22.md
?? docs/sessions/digest/2026-08-21-538fcc76-67d1-404f-a34b-288e15cb5242.md
?? docs/sessions/digest/2026-08-21-a0b5f9c6-ac8f-4cbd-b623-deec08d911bb.md
?? docs/sessions/digest/2026-08-22-f0627d44-3dd4-4115-bc0c-479ecad3c624.md
?? docs/task_drafts/
?? tasks/T-2026-08-22-bengio-node-foundation/
```

## Phase A / Task 1 / Step 2: 実行環境を測る（修復前）
```
$ ls -la .venv/bin/python*
lrwxrwxrwx 1 ubuntu ubuntu 50 Jun 22 13:04 .venv/bin/python -> /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11
lrwxrwxrwx 1 ubuntu ubuntu  6 Jun 22 13:04 .venv/bin/python3 -> python
lrwxrwxrwx 1 ubuntu ubuntu  6 Jun 22 13:04 .venv/bin/python3.11 -> python
$ readlink -f .venv/bin/python
解決できない
$ .venv/bin/python -V
(eval):10: no such file or directory: .venv/bin/python
動かない
$ du -sh .venv
6.2G	.venv
$ ls -la ~/.local/share/uv/python/
ls: cannot access '/home/ubuntu/.local/share/uv/python/': No such file or directory
$ ls -la ~/.pyenv/versions/ 
ls: cannot access '/home/ubuntu/.pyenv/versions/': No such file or directory
```

### 修復（貼り直しのみ。`uv venv --clear` は不使用）

前契約の事実 2 が **当てはまらない**: `~/.local/share/uv/python/` は不在だった。
`~/.pyenv/` も丸ごと不在。3.11 系の実体がホストに一つも無かったため、
`uv python install 3.11` で philip と同一の配置へ実体を用意してから貼り直した。

```
$ uv python install 3.11
Downloading cpython-3.11.16-linux-x86_64-gnu (download) (29.5MiB)
 Downloaded cpython-3.11.16-linux-x86_64-gnu (download)
Installed Python 3.11.16 in 1.20s
 + cpython-3.11.16-linux-x86_64-gnu (python3.11)
$ BASE=/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu
$ ln -sfn $BASE/bin/python3.11 .venv/bin/python
$ sed -i "s|^home = .*|home = $BASE/bin|" .venv/pyvenv.cfg   # 退避: /tmp/pyvenv.cfg.bak
```

### 修復後
```
$ cat .venv/pyvenv.cfg
home = /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin
implementation = CPython
uv = 0.11.15
version_info = 3.11.4
include-system-site-packages = false
$ ls -la .venv/bin/python*
lrwxrwxrwx 1 ubuntu ubuntu 83 Aug 23 13:47 .venv/bin/python -> /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
lrwxrwxrwx 1 ubuntu ubuntu  6 Jun 22 13:04 .venv/bin/python3 -> python
lrwxrwxrwx 1 ubuntu ubuntu  6 Jun 22 13:04 .venv/bin/python3.11 -> python
$ .venv/bin/python -V
Python 3.11.16
$ du -sh .venv
6.2G	.venv
$ source .venv/bin/activate && which python && python -V
/home/ubuntu/slocal2/m2/.venv/bin/python
Python 3.11.16
$ python -c "import sys; print(sys.prefix); print(sys.base_prefix)"
/home/ubuntu/slocal2/m2/.venv
/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu
$ python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
2.1.2+cu118 True
```

`.venv` の大きさ: **修復前 6.2G → 修復後 6.2G**。破棄していない。

## Phase A / Task 1 / Step 3: 検証に要るもの
```
$ python -c "import jsonschema; print(jsonschema.__version__)"
4.26.0
```

前契約の事実 5 は **当てはまらない**: 環境を作り直していないため `jsonschema` は残存。追加導入は不要だった。

### 範囲外（記録のみ）: 前契約の事実 10 は当てはまる
```
$ python -c "import mmcv"
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

## Phase A / Task 1 / Step 4: 版管理の識別
```
$ ls -la ~/.gitconfig
ls: cannot access '/home/ubuntu/.gitconfig': No such file or directory
$ git config user.name   # 設定前
未設定 (exit 1)
$ git config user.email  # 設定前
未設定 (exit 1)
$ git config user.name "takuya3h"
$ git config user.email "daky.o7600@gmail.com"   # repo scope (.git/config)
$ git config user.name && git config user.email  # 設定後
takuya3h
daky.o7600@gmail.com
```

前契約の事実 3 は **当てはまる**: `~/.gitconfig` は不在。repo 内だけに設定した。

## Phase A / Task 1 / Step 5: 送出の経路
```
$ git remote -v
origin	git@github.com:takuya3h/m2.git (fetch)
origin	git@github.com:takuya3h/m2.git (push)
$ git config --local --get remote.origin.pushurl
git@github.com:takuya3h/m2.git
$ ssh -o BatchMode=yes -T git@github.com
Hi takuya3h! You've successfully authenticated, but GitHub does not provide shell access.
$ gh auth status
github.com
  ✓ Logged in to github.com account takuya3h (/home/ubuntu/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: ssh
  - Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'
$ git config --get-all credential.helper
(なし。exit 1)
$ git fetch origin
(成功。exit 0。origin/phase0 = 8eec82ec を取得できている)
```

前契約の事実 4 は bengio では **当てはまらない**。
`push` 側は `git@` のままだが、**配備鍵は消えていない**。`ssh -T git@github.com` が
`Hi takuya3h!` を返し、`git fetch origin` も成功する。`~/.ssh/id_ed25519` が
2026-08-23 13:43 に存在し、`gh` も `takuya3h` で認証済みである。

したがって「鍵が消えているので https へ切り替える」という前提が成立しない。
**加えて `git remote set-url --push` は本実行環境の権限判定に拒否された**（下記）。
`credential.helper` が未設定のため、仮に https へ切り替えると資格情報の入力を
求められ、**動いている経路を壊す**。よって `git@` のまま維持する。

```
$ git remote set-url --push origin https://github.com/takuya3h/m2.git
Permission for this action was denied by the Claude Code auto mode classifier.
```

## Phase A / Task 2: 論理名 SERVERNAME

### 設定前
```
$ grep -n "SERVERNAME" ~/.zshenv ~/.profile
(該当なし。exit 1)
$ echo "SERVERNAME=${SERVERNAME:-unset}"
SERVERNAME=unset
$ hostname
Bengio
$ ls -la ~/.profile ~/.bash_profile ~/.bash_login
ls: cannot access '/home/ubuntu/.bash_profile': No such file or directory
ls: cannot access '/home/ubuntu/.bash_login': No such file or directory
-rw-r--r-- 1 ubuntu ubuntu 833 Aug 18 09:17 /home/ubuntu/.profile
```

`~/.bash_profile` `~/.bash_login` が無いため `~/.profile` 読込の条件を満たす。

### 道具を読んでから使った
```
$ scripts/sync/setup_host_servername.sh --help
ERROR: 不明なオプション '--help'（--dry-run / --verify のみ）
$ bash scripts/sync/setup_host_servername.sh --dry-run bengio
== 論理名: bengio  mode=dry-run ==
  would  /home/ubuntu/.zshenv へ追記する
  would  /home/ubuntu/.profile へ追記する
  would  /home/ubuntu/.bashrc へ追記する
== 空実行のため何も書いていません（変更予定: あり）==
$ bash scripts/sync/setup_host_servername.sh bengio
== 論理名: bengio  mode=apply ==
  append /home/ubuntu/.zshenv
  append /home/ubuntu/.profile
  append /home/ubuntu/.bashrc
== 適用後の確認（env -i で継承を断って測定） ==
  OK   zsh -c     非対話 [bengio]
  OK   zsh -ic    対話   [bengio]
  OK   zsh -lc    ログイン [bengio]
  OK   bash -lc   ログイン [bengio]
  OK   bash -ic   対話   [bengio]
  --   bash -c    非対話 [未設定]  ← 既知の限界（利用者ファイルでは覆えない）
```

前契約の事実 9 は **当てはまる**（両方へ置いた）。道具は `~/.bashrc` にも置く。

### 追記内容（実測）
```
$ grep -n -A2 -B1 "SERVERNAME" ~/.zshenv ~/.profile ~/.bashrc
/home/ubuntu/.zshenv-5-
/home/ubuntu/.zshenv:6:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.zshenv:7:export SERVERNAME=bengio
/home/ubuntu/.zshenv:8:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.profile-30-
/home/ubuntu/.profile:31:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.profile:32:export SERVERNAME=bengio
/home/ubuntu/.profile:33:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.bashrc-120-
/home/ubuntu/.bashrc:121:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.bashrc:122:export SERVERNAME=bengio
/home/ubuntu/.bashrc:123:# <<< egosurgery SERVERNAME <<<
```

### 新しいシェルでの解決（本契約の要求形）
```
$ zsh -c 'echo "zsh: SERVERNAME=${SERVERNAME:-unset}"'
zsh: SERVERNAME=bengio
$ bash -lc 'echo "bash: SERVERNAME=${SERVERNAME:-unset}"'
bash: SERVERNAME=bengio
```

## Gate G1（Phase A 直後）: PASS（逸脱 1 件を付記）

| 判定項目 | 実測 |
|---|---|
| 版管理が最新 | `8eec82ec` = `origin/phase0`。`rev-list --left-right --count HEAD...origin/phase0` = `0 0` |
| 実行環境が動く | `.venv/bin/python -V` → `Python 3.11.16`。`torch 2.1.2+cu118 / cuda True` |
| 経路が `.venv` を指す | `which python` → `/home/ubuntu/slocal2/m2/.venv/bin/python`、`sys.prefix` = `.venv` |
| 中身を破棄していない | `du -sh .venv` 前 `6.2G` → 後 `6.2G` |
| 検証に要るもの | `jsonschema 4.26.0` 存在（追加導入不要） |
| 版管理の識別 | `user.name=takuya3h` `user.email=daky.o7600@gmail.com`（repo scope） |
| 送出の経路 | **逸脱**: `git@` のまま。前提（配備鍵が消えている）が bengio では不成立で、`ssh -T git@github.com` が認証を返す。加えて `git remote set-url --push` は実行環境の権限判定に拒否された。実際に push できるかは Phase C で実測する |
| 論理名 | `zsh -c` / `bash -lc` の両方で `bengio` |

## Phase B / Task 3 / Step 1: 既存の鍵
```
$ ls -la ~/.ssh/
total 40
drwx------ 3 ubuntu ubuntu 4096 Aug 23 13:44 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 13:50 ..
-rw------- 1 ubuntu ubuntu  746 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 09:17 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 09:17 config.d
-rw------- 1 ubuntu ubuntu  387 Aug 23 13:43 id_ed25519
-rw-r--r-- 1 ubuntu ubuntu   82 Aug 23 13:43 id_ed25519.pub
-rw------- 1 ubuntu ubuntu  978 Aug 23 13:44 known_hosts
-rw-r--r-- 1 ubuntu ubuntu  142 Aug 23 13:38 known_hosts.old
$ for f in ~/.ssh/*.pub; do ssh-keygen -lf "$f"; done
256 SHA256:2x3z45/WqhtE6F461Y2kDCiE/Vge0n2NblbXuC0VKz4 no comment (ED25519)
$ ls -la ~/.ssh/id_ed25519_bengiotophilip*
$ cat ~/.ssh/config
Include ~/.ssh/config.d/*.conf
$ ls -la ~/.ssh/config.d/
total 12
drwx------ 2 ubuntu ubuntu 4096 Aug 18 09:17 .
drwx------ 3 ubuntu ubuntu 4096 Aug 23 13:44 ..
-rw------- 1 ubuntu ubuntu 1073 Aug 18 09:17 aolabnet.conf
```

中心宛の鍵 `~/.ssh/id_ed25519_bengiotophilip` は **存在しなかった**ので新規作成した。
既存は GitHub 用の `~/.ssh/id_ed25519`（`SHA256:2x3z45/WqhtE6F461Y2kDCiE/Vge0n2NblbXuC0VKz4`）のみ。

## Phase B / Task 3 / Step 2-3: 鍵の作成と権限
```
$ ssh-keygen -t ed25519 -N "" -C "bengiotophilip" -f ~/.ssh/id_ed25519_bengiotophilip
Your identification has been saved in /home/ubuntu/.ssh/id_ed25519_bengiotophilip
Your public key has been saved in /home/ubuntu/.ssh/id_ed25519_bengiotophilip.pub
The key fingerprint is:
SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 bengiotophilip
$ ssh-keygen -lf ~/.ssh/id_ed25519_bengiotophilip.pub
256 SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 bengiotophilip (ED25519)
$ stat -c "%a %n" ~/.ssh/id_ed25519_bengiotophilip ~/.ssh/id_ed25519_bengiotophilip.pub ~/.ssh
600 /home/ubuntu/.ssh/id_ed25519_bengiotophilip
644 /home/ubuntu/.ssh/id_ed25519_bengiotophilip.pub
700 /home/ubuntu/.ssh
```

秘密鍵は `600`、`~/.ssh` は `700`。期待どおり。**秘密鍵の中身は本報告のどこにも含まない。**

## Phase B / Task 3 / Step 4: 公開鍵を版管理へ
```
$ cp ~/.ssh/id_ed25519_bengiotophilip.pub scripts/sync/hub_keys/bengio.pub
$ ssh-keygen -lf scripts/sync/hub_keys/bengio.pub
256 SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 bengiotophilip (ED25519)
$ head -c 30 scripts/sync/hub_keys/bengio.pub; echo
ssh-ed25519 AAAAC3NzaC1lZDI1NT
$ grep -c "PRIVATE" scripts/sync/hub_keys/bengio.pub
0
$ grep -c "" scripts/sync/hub_keys/bengio.pub
1
$ ls -la scripts/sync/hub_keys/
total 20
drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 23 13:51 .
drwxrwxr-x 4 ubuntu ubuntu 4096 Aug 23 13:44 ..
-rw-rw-r-- 1 ubuntu ubuntu   95 Aug 13 02:14 andrew.pub
-rw-r--r-- 1 ubuntu ubuntu   96 Aug 23 13:51 bengio.pub
-rw-rw-r-- 1 ubuntu ubuntu   94 Aug 13 01:44 ilya.pub
```

指紋は Step 2 と一致（`SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4`）。
先頭 `ssh-` / `PRIVATE` = 0 / 行数 = 1。三つとも期待どおり。

### 陽性対照（囮。版管理の外に置き、commit しない）
```
$ DECOY=<scratchpad>/decoy_privkey.txt   # repo 外
$ head -c 30 $DECOY; echo
(囮の先頭 30 バイトは鍵の書き出し見出し行だった。送信前の秘匿検査の規則
  「鍵の書き出し行は削る」に従い、literal を記述へ置換した。先頭が `ssh-` でない
  ことが要点であり、判定の結論は変わらない)
$ grep -c "PRIVATE" $DECOY
2
$ grep -c "" $DECOY
3
$ git --no-pager status --porcelain | grep -c "decoy"
0
```

**三つの検査すべてが囮では反転した**（先頭が `ssh-` でない / `PRIVATE` が 2 ≥ 1 / 行数が 3 ≠ 1）。
検査は働いている。囮は版管理に現れない。

## Phase B / Task 4: 同期処理と識別子

### Step 1-2: 配布物と配置物の照合
```
$ sha256sum /tmp/st_bengio.tar.gz
c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60  /tmp/st_bengio.tar.gz
$ sha256sum ~/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
$ ~/bin/syncthing --version
syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC
$ stat -c "%a %n" ~/bin/syncthing
755 /home/ubuntu/bin/syncthing
```

| 対象 | 期待（中心） | 実測 | 判定 |
|---|---|---|---|
| 配布物 | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60` | 同一 | 一致 |
| 配置物 | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` | 同一 | 一致 |

### Step 3: 識別子の発行

発行前 `~/.local/state/syncthing/` は **不在**だった（上書きの心配なし）。

```
$ ~/bin/syncthing generate --home ~/.local/state/syncthing
2026/08/23 13:52:59 INFO: Generating ECDSA key and certificate for syncthing...
2026/08/23 13:52:59 INFO: Device ID: 4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO
2026/08/23 13:52:59 INFO: Default folder created and/or linked to new config
$ ls -la ~/.local/state/syncthing/
total 28
drwx------ 2 ubuntu ubuntu 4096 Aug 23 13:52 .
drwxrwxr-x 6 ubuntu ubuntu 4096 Aug 23 13:52 ..
-rw-rw-r-- 1 ubuntu ubuntu  794 Aug 23 13:52 cert.pem
-rw------- 1 ubuntu ubuntu 8495 Aug 23 13:52 config.xml
-rw------- 1 ubuntu ubuntu  288 Aug 23 13:52 key.pem
```

前契約の事実 7 は **当てはまる**: `--home` を明示しないと別の場所を見る。

### Step 4: 識別子の読み取りと公開
```
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id
4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO
$ ~/bin/syncthing device-id     # 対照: 下位命令は存在しない
syncthing: error: unexpected argument device-id
$ cat scripts/sync/device_ids/bengio.txt
4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO
$ grep -c "" scripts/sync/device_ids/bengio.txt
1
$ ls -la scripts/sync/device_ids/
total 16
drwxrwxr-x 2 ubuntu ubuntu 4096 Aug 23 13:53 .
drwxrwxr-x 4 ubuntu ubuntu 4096 Aug 23 13:44 ..
-rw-rw-r-- 1 ubuntu ubuntu   64 Aug 23 13:53 bengio.txt
-rw-rw-r-- 1 ubuntu ubuntu   64 Aug 23 13:44 philip.txt
$ cat scripts/sync/device_ids/philip.txt   # 対照: 契約記載の中心の識別子と一致
3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
```

前契約の事実 8 は **当てはまる**（`device-id` 下位命令は無い。`serve --device-id` で取る）。
`generate` の出力と公開した値は一致する。行数は 1。

### Step 5: 起動していないことの確認
```
$ python3 <待ち受け一覧>
count=5
port_22=LISTEN
port_22000=-
port_22001=-
port_8384=-
$ pgrep -x syncthing; echo "exit=$?"
exit=1
$ ps -o pid,comm -C syncthing
    PID COMMAND
```

`22000` `8384` とも待ち受けていない。`pgrep -x` は exit 1（該当なし）。
前契約の事実 6 に従い `pgrep -af` は使っていない。

### 禁止 4 の確認: 他ホストを登録していない
```
$ grep -o 'device id="[A-Z0-9-]*"' ~/.local/state/syncthing/config.xml | sort -u
device id=""
device id="4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO"
```

自ホストの識別子と空の雛形のみ。**他ホストは一つも登録していない。**

## Gate G2（Phase B 直後）: PASS

| 判定項目 | 実測 |
|---|---|
| 中心宛の鍵と指紋 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` |
| 公開鍵だけを置いた | 先頭 `ssh-ed25519` / `PRIVATE`=0 / 行数=1。囮では 3 つとも反転 |
| 配布物・配置物の要約値 | 中心と一致（上表） |
| 識別子を一行で公開 | `4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO` |
| 起動していない | `22000` `8384` 非待ち受け、`pgrep -x syncthing` exit 1 |

## Phase C / Task 5 / Step 2: 送信前の秘匿検査
```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" <契約dir>/*.md <契約dir>/*.yaml
SPEC.md:385:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
RESULT.md:85:`grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase"` をかけた。
audit.md:396:(囮の見出し行。下記のとおり literal を削って再走査済み)
```

**件数ではなく形で一件ずつ判定した。**

| 該当 | 形 | 判定 |
|---|---|---|
| `SPEC.md:385` | 検査コマンドの正規表現そのもの | **説明文。残す** |
| `RESULT.md:85` | 同じ正規表現の引用 | **説明文。残す** |
| `audit.md:396` | 囮の `head -c 30` が出した**鍵の書き出し見出し行**。鍵材料は続いていない | **形としては書き出し行なので削った**（記述へ置換。判定の結論は不変） |

削った後の再走査:
```
tasks/T-2026-08-22-bengio-node-foundation/RESULT.md:85:`grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase"` をかけた。
tasks/T-2026-08-22-bengio-node-foundation/SPEC.md:385:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
```

残る 2 件は検査コマンドの本文であり、秘匿の値ではない。
**識別子と指紋は秘匿ではないため削っていない。**

### 陽性対照（囮。版管理の外。commit しない）
```
$ printf "API_KEY=fake-decoy-value\npassword: decoy\n<鍵の書き出し見出し行>\n" > $SP/decoy_secrets.txt
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" $SP/decoy_secrets.txt
1:API_KEY=fake-decoy-value
2:password: decoy
3:<鍵の書き出し見出し行>
$ grep -c ... $SP/decoy_secrets.txt
3
$ git --no-pager status --porcelain | grep -c "decoy"
0
```

**検査は囮に対して 3 件（一以上）を返した。空振りではない。** 囮は版管理に現れない。

## Phase C / Task 5 / Step 3: 検証
```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b087
(spec.yaml の conventions_rev: "d422b08" と一致。置換不要)
$ make task-validate TASK=T-2026-08-22-bengio-node-foundation
OK   T-2026-08-22-bengio-node-foundation

1 task(s), 0 failed
validate_exit=0
$ make task-preflight TASK=T-2026-08-22-bengio-node-foundation
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-22-bengio-node-foundation/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 3 件が該当: separated_source@SPEC.md:396, :399, :402（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
$ make forbidden-check
{"base": "origin/phase0", "changed": 40, "checked": 40, "errors": [], "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

**`source scripts/load_env.sh` は使っていない**（秘匿情報の合言葉が失われているため。SPEC の指示どおり `source .venv/bin/activate` のみ）。

## Phase C / Task 5 / Step 4: 生成物の再生成
```
$ make taskindex && make inbox
(出力なし)
$ make taskindex-check; echo "taskindex_exit=$?"
taskindex_exit=0
$ make inbox-check; echo "inbox_exit=$?"
inbox_exit=0
$ grep -c "T-2026-08-22-bengio-node-foundation" context/auto/tasks_summary.csv
1
$ grep "T-2026-08-22-bengio-node-foundation" context/auto/tasks_summary.csv
T-2026-08-22-bengio-node-foundation,impl,pass,bengio,,false,2,0,0,0,0,4,2,4,2,T-2026-08-22-philip-hub-foundation
```

投影に現れることを確認した。**生成物は手編集していない。**

## Phase C / Task 5 / Step 5: 変更範囲と未追跡
```
$ git --no-pager status --porcelain
 M README.md
 M context/auto/followups.md
 M context/auto/results_recent.md
 M context/auto/tasks_summary.csv
 M docs/experiment_log.md
 M tasks/inbox.md
?? docs/analysis_scripts/
?? docs/research_review_and_next_plan_2026-08-22.md
?? docs/sessions/digest/2026-08-21-538fcc76-67d1-404f-a34b-288e15cb5242.md
?? docs/sessions/digest/2026-08-21-a0b5f9c6-ac8f-4cbd-b623-deec08d911bb.md
?? docs/sessions/digest/2026-08-22-f0627d44-3dd4-4115-bc0c-479ecad3c624.md
?? docs/task_drafts/
?? scripts/sync/device_ids/bengio.txt
?? scripts/sync/hub_keys/bengio.pub
?? tasks/T-2026-08-22-bengio-node-foundation/
?? tasks/inbox.d/T-2026-08-22-bengio-node-foundation.md
$ grep -c "" /tmp/hf_bengio.txt
16
```

開始時 **9 行** → 終了時 **16 行**。**開始時の 9 行は 1 行も欠けていない**
（`grep -Fxc` で 9 行それぞれ 1 を確認）。増分 7 行はすべて契約の範囲である。

| 増分 | 区分 |
|---|---|
| `context/auto/followups.md` `results_recent.md` `tasks_summary.csv` | 生成物 |
| `tasks/inbox.md` | 生成物 |
| `scripts/sync/hub_keys/bengio.pub` | 契約の公開物 |
| `scripts/sync/device_ids/bengio.txt` | 契約の公開物 |
| `tasks/inbox.d/T-2026-08-22-bengio-node-foundation.md` | 契約の判断の受け皿 |

`experiments/**` `transfer/**` `data/**` `runindex/**` への変更は **0 件**
（`forbidden-check` が `violations: []` / `status: pass`）。

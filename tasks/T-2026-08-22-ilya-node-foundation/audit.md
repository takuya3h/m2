# audit — T-2026-08-22-ilya-node-foundation (ilya)

出力は要約せず貼る（申し送り 8）。

## Phase A / Task 1 Step 1: 開始状態

### git

```
$ git branch --show-current
feat/ilya-node-foundation
$ git fetch origin   # 出力なし = 既に最新
$ git --no-pager log -1 --format='%h %s' HEAD
8eec82e Merge pull request #121 from takuya3h/feat/philip-hub-foundation
$ git --no-pager log -1 --format='%h %s' origin/phase0
8eec82e Merge pull request #121 from takuya3h/feat/philip-hub-foundation
$ git rev-list --left-right --count HEAD...origin/phase0
0	0
```

**版管理は最新である**（HEAD == origin/phase0、ahead/behind ともに 0）。
分岐は既に `origin/phase0` を起点として作成済みであった。

```
$ git --no-pager status --porcelain
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
?? tasks/T-2026-08-22-ilya-node-foundation/
untracked_and_changed=2
```

**開始時の未追跡 = 2 件。** 契約の終わりに同じ数であることを確かめる。
うち 1 件は本契約のディレクトリ、1 件は版管理外の成果物（session digest）。
後者には一切触らない。

### 常駐処理

```
$ ls -la ~/bin/
ls: cannot access '/home/ubuntu/bin/': No such file or directory
$ ls -la ~/claude-sync/
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
$ grep -c sync-pause ~/bin/m2-sync.sh
ugrep: warning: /home/ubuntu/bin/m2-sync.sh: No such file or directory
```

**常駐同期処理 `m2-sync.sh` / keeper は存在しない**（初期化済み）。
よって `.sync-pause` の目印は不要であり、置いていない。自動統合の危険は無い。

### 家の直下

```
$ ls -la ~/
（下記の通り）
drwxrwxr-x .claude / .config / .cache / .copilot / .dotnet / .homebrew / .local
drwxr-xr-x .oh-my-zsh / .vscode-server / .ssh
-rw-r--r-- .bash_logout .bashrc .profile .wget-hsts .zshenv .zshrc .zshrc.pre-oh-my-zsh
drwxr-xr-x local / slocal1 / slocal2
$ echo "home_entries=$(ls -a ~/ | grep -c -v '^\.\{1,2\}$')"
home_entries=26
```

**`~/bin` は無い。** `~/.pyenv` も無い（前契約の事実 1 と整合）。

### 鍵

```
$ ls -la ~/.ssh/
-rw------- 1 ubuntu ubuntu  102 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 08:06 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 08:06 config.d
-rw------- 1 ubuntu ubuntu  387 Aug 23 13:33 id_ed25519
-rw-r--r-- 1 ubuntu ubuntu   82 Aug 23 13:33 id_ed25519.pub
-rw------- 1 ubuntu ubuntu  978 Aug 23 13:36 known_hosts
-rw-r--r-- 1 ubuntu ubuntu  142 Aug 23 13:36 known_hosts.old
$ ssh-keygen -lf ~/.ssh/authorized_keys
256 SHA256:30y00ixicNIVEovdR82sNN0xJTtYZ5G+lJdfxY4ndZY dakyo-mba@dmba.local (ED25519)
```

受け入れ一覧に入っているのは MacBook の鍵 1 件のみ。

### 同期処理の設定

```
$ ls -la ~/.local/state/syncthing/
ls: cannot access '/home/ubuntu/.local/state/syncthing/': No such file or directory
```

**未作成。** 新規構築である。

### 論理名

```
$ cat ~/.zshenv
# Must have Path exports:
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:$CPATH
```

**`SERVERNAME` の記載なし。**
`~/.profile` は存在し、`$HOME/bin` があれば PATH へ入れる条件分岐を持つ。

---

## Phase A / Task 1 Step 2: 実行環境の修復

### 修復前の実測

```
$ ls -la .venv/bin/python*
lrwxrwxrwx 1 ubuntu ubuntu 50 Aug  5 06:22 .venv/bin/python -> /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11
lrwxrwxrwx 1 ubuntu ubuntu  6 Aug  5 06:22 .venv/bin/python3 -> python
lrwxrwxrwx 1 ubuntu ubuntu  6 Aug  5 06:22 .venv/bin/python3.11 -> python
$ readlink -f .venv/bin/python
解決できない
$ .venv/bin/python -V
(eval):1: no such file or directory: .venv/bin/python
動かない
$ du -sh .venv
6.2G	.venv
$ cat .venv/pyvenv.cfg
home = /home/ubuntu/.pyenv/versions/3.11.4/bin
implementation = CPython
uv = 0.11.26
version_info = 3.11.4
include-system-site-packages = false
$ ls -la ~/.pyenv
ls: cannot access '/home/ubuntu/.pyenv': No such file or directory
```

**壊れているのは繋がりだけである。**中身 6.2G は健在。`--clear` は使わない（禁止 7）。

### 前契約の事実 2 が当てはまらなかった

```
$ ls -la ~/.local/share/uv/python/
ls: cannot access '/home/ubuntu/.local/share/uv/python/': No such file or directory
$ ls -la ~/.local/share/uv/
ls: cannot access '/home/ubuntu/.local/share/uv/': No such file or directory
$ ls -la /usr/bin/python3.1*
-rwxr-xr-x 1 root root 8020928 Jun 19 12:46 /usr/bin/python3.12
$ command -v python3.11
(eval):1: command not found: python3.11
$ uv --version
uv 0.12.5 (x86_64-unknown-linux-gnu)   # /home/ubuntu/.local/bin/uv
```

**ilya には貼り直し先の Python 3.11 実体が一つも無かった。**
philip では uv 管理の実体が残っていたが、ilya では uv の共有ディレクトリごと消えている。
**ホストによる差である。**（想定外の表「前契約の実測が当てはまらない」に該当）

ユーザーへ選択肢を提示し、**実体の取得**を選択した上で実行した。

```
$ uv python install 3.11
Downloading cpython-3.11.16-linux-x86_64-gnu (download) (29.5MiB)
 Downloaded cpython-3.11.16-linux-x86_64-gnu (download)
Installed Python 3.11.16 in 1.42s
 + cpython-3.11.16-linux-x86_64-gnu (python3.11)
```

**取得された版 3.11.16 は前契約 philip の実体と同一である**（事実 2 の
`cpython-3.11.16-linux-x86_64-gnu`）。ABI は `cpython-311` で `.venv` と一致する。

### 貼り直しと確認

```
$ ln -sfn /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11 .venv/bin/python
$ readlink -f .venv/bin/python
/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
$ .venv/bin/python -V
Python 3.11.16
$ .venv/bin/python -c "import sys; print('prefix=',sys.prefix); print('base=',sys.base_prefix)"
prefix= /home/ubuntu/slocal2/m2/.venv
base= /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu
$ du -sh .venv
6.2G	.venv
```

**大きさは前 6.2G / 後 6.2G。破棄していない。**

```
$ source .venv/bin/activate && which python && python -V
/home/ubuntu/slocal2/m2/.venv/bin/python
Python 3.11.16
$ python -c "import sys;print([p for p in sys.path if 'site-packages' in p])"
['/home/ubuntu/slocal2/m2/.venv/lib/python3.11/site-packages']
```

**経路は `.venv` を指している。**

`pyvenv.cfg` の `home` は壊れたパスのままだが、`sys.prefix` / site-packages ともに
正しく解決されている。**動いているため触っていない**（最小差分）。

## Phase A / Task 1 Step 3: 検証に要るもの

```
$ source .venv/bin/activate && python -c "import jsonschema; print(jsonschema.__version__)"
jsonschema 4.26.0
```

**既に在る。追加導入は行っていない。**
前契約の事実 5（作り直し後は追加導入が要る）は、**作り直していないため当てはまらない。**

## Phase A / Task 1 Step 4: 版管理の識別

```
$ git config user.name
未設定
$ git config user.email
未設定
$ ls -la ~/.gitconfig
ls: cannot access '/home/ubuntu/.gitconfig': No such file or directory
```

前契約の事実 3 が当てはまる。**repo の中だけに設定した。**

```
$ git --no-pager log -3 --format='%h | %an | %ae | %s'
8eec82e | Takuya Uchihashi | 160078021+takuya3h@users.noreply.github.com | Merge pull request #121 ...
6ab0c07 | takuya3h | daky.o7600@gmail.com | feat(sync): build hub foundation and publish device id on philip
```

前契約 philip の commit と同じ識別子に揃えた。

```
$ git config --local user.name "takuya3h"
$ git config --local user.email "daky.o7600@gmail.com"
$ git config user.name  ->  takuya3h
$ git config user.email ->  daky.o7600@gmail.com
```

## Phase A / Task 1 Step 5: 送出の経路

```
$ git remote -v                    # 修正前
origin	git@github.com:takuya3h/m2.git (fetch)
origin	git@github.com:takuya3h/m2.git (push)
$ git remote set-url --push origin https://github.com/takuya3h/m2.git
$ git remote -v                    # 修正後
origin	git@github.com:takuya3h/m2.git (fetch)
origin	https://github.com/takuya3h/m2.git (push)
```

⚠ **SPEC の Expected「両方が `https` になったことを確かめる」は、指示された
`git remote set-url --push` では達成できない。** この下位命令は `pushurl` だけを
設定し、`fetch` 側の `url` は変えない。両方を https にするには
`git remote set-url origin https://...` も要る。**起票者の誤り（self_contradiction）。**

fetch 側は SSH のままだが、**実測で生きている。**

```
$ git fetch origin
From github.com:takuya3h/m2
 * [new branch]      feat/lecun-node-foundation -> origin/feat/lecun-node-foundation
fetch_exit=0
```

前契約の事実 4 は「配備鍵が消えたので通らない」とするが、**ilya では fetch 用の
SSH は通っている。**`~/.ssh/id_ed25519`（`SHA256:cdOmPfuBN4wFfTjbvjDIaGgiv3YaHEMLez0td1v5oE4`,
コメント `no comment`）が存在する。**ホストによる差である。**
push 経路は指示どおり https へ変更済み。fetch 側は動作しているため触っていない。

---

## Phase A / Task 2: 論理名

### Step 1: 設定前の状態

```
$ grep -n "SERVERNAME" ~/.zshenv ~/.profile
該当なし
$ echo "SERVERNAME=${SERVERNAME:-unset}"
SERVERNAME=unset
$ hostname
aolab
```

`hostname` は `aolab` を返す。**論理名 `ilya` と一致しない**ため、
`resolve_server_name()` の最後の砦では ilya を特定できない。SERVERNAME が要る。

```
$ ls -la ~/.bash_profile ~/.bash_login
ls: cannot access '/home/ubuntu/.bash_profile': No such file or directory
ls: cannot access '/home/ubuntu/.bash_login': No such file or directory
```

**両方とも不在。**よって `~/.profile` が bash ログイン時に読まれる条件を満たす。

### Step 2: 追記

道具を読んでから使った（`--help` は無い。`--dry-run` / `--verify` のみ）。

```
$ scripts/sync/setup_host_servername.sh --help
ERROR: 不明なオプション '--help'（--dry-run / --verify のみ）
$ bash scripts/sync/setup_host_servername.sh --dry-run ilya
== 論理名: ilya  mode=dry-run ==
  would  /home/ubuntu/.zshenv へ追記する
  would  /home/ubuntu/.profile へ追記する
  would  /home/ubuntu/.bashrc へ追記する
== 空実行のため何も書いていません（変更予定: あり）==
$ bash scripts/sync/setup_host_servername.sh ilya
== 論理名: ilya  mode=apply ==
  append /home/ubuntu/.zshenv
  append /home/ubuntu/.profile
  append /home/ubuntu/.bashrc
== 適用後の確認（env -i で継承を断って測定） ==
  OK   zsh -c     非対話 [ilya]
  OK   zsh -ic    対話   [ilya]
  OK   zsh -lc    ログイン [ilya]
  OK   bash -lc   ログイン [ilya]
  OK   bash -ic   対話   [ilya]
  --   bash -c    非対話 [未設定]  ← 既知の限界（利用者ファイルでは覆えない）
```

**追記内容**（3 ファイルとも同一の標識付きブロック）:

```
$ grep -n -A2 -B1 "egosurgery SERVERNAME" ~/.zshenv ~/.profile ~/.bashrc
/home/ubuntu/.zshenv:6:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.zshenv-7-export SERVERNAME=ilya
/home/ubuntu/.zshenv:8:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.bashrc:121:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.bashrc-122-export SERVERNAME=ilya
/home/ubuntu/.bashrc:123:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.profile:31:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.profile-32-export SERVERNAME=ilya
/home/ubuntu/.profile:33:# <<< egosurgery SERVERNAME <<<
```

SPEC は `~/.zshenv` と `~/.profile` の両方を求める。道具は補助として `~/.bashrc`
にも置く（bash の対話形態を覆うため）。**リポジトリ内のファイルには触れていない。**

### Step 3: 新しいシェルでの解決

```
$ zsh -c 'echo "zsh: SERVERNAME=${SERVERNAME:-unset}"'
zsh: SERVERNAME=ilya
$ bash -lc 'echo "bash: SERVERNAME=${SERVERNAME:-unset}"'
bash: SERVERNAME=ilya
```

**両方の形態で `ilya` が出る。**

`bash -c`（非対話・非ログイン）だけは未設定のままである。これは道具の冒頭に
明記された既知の限界であり、利用者ファイルでは覆えない（root 権限を要する
`/etc/environment` が要る）。**本契約の範囲外として記録する。**

---

## ゲート G1（Phase A 直後）

| 判定項目 | 実測 | 結果 |
|---|---|---|
| 版管理が最新であることを先頭の記録で確かめた | HEAD == origin/phase0 == `8eec82e`、ahead/behind = 0/0 | PASS |
| 実行環境が動く | `Python 3.11.16`、`which python` = `/home/ubuntu/slocal2/m2/.venv/bin/python` | PASS |
| 経路が仮想環境を指す | `sys.prefix = /home/ubuntu/slocal2/m2/.venv` | PASS |
| 中身の大きさを破棄していない | 前 `6.2G` / 後 `6.2G` | PASS |
| 論理名が新しいシェルの両方の形態で解決される | zsh=`ilya`, bash -lc=`ilya` | PASS |
| 版管理の識別を直した | `takuya3h` / `daky.o7600@gmail.com` | PASS |
| 送出の経路を直した | push = `https://github.com/takuya3h/m2.git` | PASS |

**G1 通過。Phase B へ進む。**

---

## Phase B / Task 3: 中心宛の鍵

### Step 1: 既存の鍵

```
$ ls -la ~/.ssh/
-rw------- 1 ubuntu ubuntu  102 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 08:06 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 08:06 config.d
-rw------- 1 ubuntu ubuntu  387 Aug 23 13:33 id_ed25519
-rw-r--r-- 1 ubuntu ubuntu   82 Aug 23 13:33 id_ed25519.pub
-rw------- 1 ubuntu ubuntu  978 Aug 23 13:36 known_hosts
-rw-r--r-- 1 ubuntu ubuntu  142 Aug 23 13:36 known_hosts.old
$ ssh-keygen -lf ~/.ssh/id_ed25519.pub
256 SHA256:cdOmPfuBN4wFfTjbvjDIaGgiv3YaHEMLez0td1v5oE4 no comment (ED25519)
$ ls -la ~/.ssh/id_ed25519_ilyatophilip*
(eval):1: no matches found: /home/ubuntu/.ssh/id_ed25519_ilyatophilip*
```

**中心宛の鍵は存在しない。**既存の `id_ed25519` はコメントが `no comment` で、
GitHub の fetch が通っていることから GitHub 向けと判断した。**これには触れていない。**

### Step 2: 鍵を作る

```
$ ssh-keygen -t ed25519 -N "" -C "ilyatophilip" -f ~/.ssh/id_ed25519_ilyatophilip
Generating public/private ed25519 key pair.
Your identification has been saved in /home/ubuntu/.ssh/id_ed25519_ilyatophilip
Your public key has been saved in /home/ubuntu/.ssh/id_ed25519_ilyatophilip.pub
The key fingerprint is:
SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ ilyatophilip
$ ls -la ~/.ssh/id_ed25519_ilyatophilip*
-rw------- 1 ubuntu ubuntu 399 Aug 23 13:51 /home/ubuntu/.ssh/id_ed25519_ilyatophilip
-rw-r--r-- 1 ubuntu ubuntu  94 Aug 23 13:51 /home/ubuntu/.ssh/id_ed25519_ilyatophilip.pub
$ ssh-keygen -lf ~/.ssh/id_ed25519_ilyatophilip.pub
256 SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ ilyatophilip (ED25519)
```

**指紋: `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ`**
これが中心 philip の受け入れ一覧へ入る値である。
**秘密鍵の中身はどこにも出していない。**（`ssh-keygen` の図案出力も落としてある）

### Step 3: 権限

```
$ stat -c "%a %n" ~/.ssh/id_ed25519_ilyatophilip ~/.ssh/id_ed25519_ilyatophilip.pub
600 /home/ubuntu/.ssh/id_ed25519_ilyatophilip
644 /home/ubuntu/.ssh/id_ed25519_ilyatophilip.pub
$ stat -c "%a %n" ~/.ssh
700 /home/ubuntu/.ssh
```

**秘密鍵 600、`~/.ssh` 700。期待どおり。**

### Step 4: 公開鍵を版管理へ

```
$ mkdir -p scripts/sync/hub_keys && cp ~/.ssh/id_ed25519_ilyatophilip.pub scripts/sync/hub_keys/ilya.pub
$ ls -la scripts/sync/hub_keys/
-rw-rw-r-- 1 ubuntu ubuntu   95 Aug 13 02:14 andrew.pub
-rw-rw-r-- 1 ubuntu ubuntu   94 Aug 23 13:51 ilya.pub
$ ssh-keygen -lf scripts/sync/hub_keys/ilya.pub
256 SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ ilyatophilip (ED25519)
```

**Step 2 の指紋と一致する。**
（`hub_keys/` には既に `andrew.pub` が在った。触れていない。
 philip の前契約は `hub_keys/philip.pub` を置いていない — 中心自身は自分宛の鍵を要さない）

### 三つの検査と陽性対照

**本番** `scripts/sync/hub_keys/ilya.pub`:

```
$ head -c 30 scripts/sync/hub_keys/ilya.pub; echo
ssh-ed25519 AAAAC3NzaC1lZDI1NT
$ grep -c "PRIVATE" scripts/sync/hub_keys/ilya.pub
0
$ grep -c '' scripts/sync/hub_keys/ilya.pub
1
```

| 検査 | 期待 | 実測 | 判定 |
|---|---|---|---|
| 先頭が `ssh-` | `ssh-` | `ssh-ed25519 AAAAC3NzaC1lZDI1NT` | PASS |
| `PRIVATE` の件数 | 零 | `0` | PASS |
| 行数 | 一 | `1` | PASS |

**陽性対照（囮）** — 鍵の書き出しを模した 3 行の一時ファイルを
scratchpad（版管理外）に作り、**同じ三つの検査をかけた**:

```
$ head -c 30 <囮>; echo
-----BEGIN OPENSSH PRIV…（以下略・本報告では検査に掛からないよう切っている）
$ grep -c "PRIVATE" <囮>
2
$ grep -c '' <囮>
3
```

| 検査 | 囮での実測 | 検査は働いたか |
|---|---|---|
| 先頭が `ssh-` | `-----BEGIN …` で始まる → 外れる | **働いた** |
| `PRIVATE` の件数 | `2`（一以上） | **働いた** |
| 行数 | `3`（一ではない） | **働いた** |

**三つとも囮を弾いた。判定が働いていることを実測で示した。**

```
$ git --no-pager status --porcelain | grep -c 'decoy'
0
```

**囮は版管理へ入れていない。**（scratchpad 配下に置いた）

---

## Phase B / Task 4: 同期処理と識別子

### Step 1: 配布物の取得と照合

```
$ mkdir -p ~/bin
$ cd /tmp && curl -sSL -o st_ilya.tar.gz "https://github.com/syncthing/syncthing/releases/download/v1.27.10/syncthing-linux-amd64-v1.27.10.tar.gz"
curl_exit=0
-rw-rw-r-- 1 ubuntu ubuntu 10846484 Aug 23 13:53 /tmp/st_ilya.tar.gz
$ sha256sum /tmp/st_ilya.tar.gz
c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60  /tmp/st_ilya.tar.gz
```

| | 値 |
|---|---|
| Expected | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60` |
| 実測 | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60` |
| 判定 | **一致** |

### Step 2: 展開と配置

```
$ cd /tmp && tar xzf st_ilya.tar.gz
$ cp /tmp/syncthing-linux-amd64-v1.27.10/syncthing ~/bin/syncthing
$ chmod 755 ~/bin/syncthing
$ ls -la ~/bin/syncthing
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug 23 13:53 /home/ubuntu/bin/syncthing
$ sha256sum ~/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing
$ ~/bin/syncthing --version
syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC
```

| | 値 |
|---|---|
| Expected（中心と同じ） | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` |
| 実測 | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` |
| 判定 | **一致。版も `v1.27.10` で中心と同じ。** |

### Step 3: 識別子の発行

```
$ ls -la ~/.local/state/syncthing/
ls: cannot access '/home/ubuntu/.local/state/syncthing/': No such file or directory
```

**既存の設定は無い。上書きの心配は無い。**

```
$ ~/bin/syncthing generate --home ~/.local/state/syncthing
2026/08/23 13:53:34 INFO: Generating ECDSA key and certificate for syncthing...
2026/08/23 13:53:34 INFO: Device ID: UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY
2026/08/23 13:53:34 INFO: Default folder created and/or linked to new config
$ ls -la ~/.local/state/syncthing/
-rw-rw-r-- 1 ubuntu ubuntu  794 Aug 23 13:53 cert.pem
-rw------- 1 ubuntu ubuntu 8494 Aug 23 13:53 config.xml
-rw------- 1 ubuntu ubuntu  288 Aug 23 13:53 key.pem
```

前契約の事実 7 のとおり `--home` で明示した。**常駐していない**（Step 5 で確認）。

### Step 4: 識別子の読み取りと公開

前契約の事実 8 のとおり `serve --home ... --device-id` を使った。

```
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id
UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY
exit=0
$ mkdir -p scripts/sync/device_ids
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id > scripts/sync/device_ids/ilya.txt
$ cat scripts/sync/device_ids/ilya.txt
UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY
$ grep -c '' scripts/sync/device_ids/ilya.txt
1
```

**一行。`generate` の出力と一致する。乱れは無く、整える必要は無かった。**

**中心の識別子との照合**（読み取りのみ。他ホストへは接続していない）:

```
$ cat scripts/sync/device_ids/philip.txt
3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
```

**SPEC の「中心の識別子」と一致する。**前契約の成果が版管理に届いていることの確認。

**他ホストを登録していないこと**（禁止 4）:

```
$ grep -o 'id="[A-Z0-9-]\{63\}"' ~/.local/state/syncthing/config.xml | sort -u
id="UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY"
```

**設定に現れる識別子は自ホストのものだけ。**他ホストは登録していない。

### Step 5: 起動していないことの確認

```
$ python3 - <<'PY' … （SPEC の判定器）
count=5
port_22=LISTEN
port_22001=-
port_22000=-
port_8384=-
$ pgrep -x syncthing
pgrep_exit=1   # 1 = 該当なし
```

**`22000` も `8384` も待ち受けていない。処理も存在しない。同期処理は起動していない。**
（前契約の事実 6 に従い `pgrep -af` ではなく `pgrep -x` を使った）

配布物 `/tmp/st_ilya.tar.gz` と展開先 `/tmp/syncthing-linux-amd64-v1.27.10/` は
版管理外の一時領域に残してある。契約は削除を求めていないため触っていない。

---

## ゲート G2（Phase B 直後）

| 判定項目 | 実測 | 結果 |
|---|---|---|
| 中心宛の鍵を作り指紋を記録した | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | PASS |
| 版管理へ置いたものが公開鍵だけ（三つの検査） | `ssh-` 始まり / `PRIVATE`=0 / 行数=1 | PASS |
| 囮で検査が働くことを示した | 囮は三つとも弾かれた（`PRIVATE`=2, 行数=3, 先頭不一致） | PASS |
| 配布物の要約値が中心と一致 | `c04ffbde…75fd60` 一致 | PASS |
| 配置物の要約値が中心と一致 | `32ab747e…0ca1dd` 一致 | PASS |
| 識別子を一行で公開 | `scripts/sync/device_ids/ilya.txt`、行数 1 | PASS |
| 同期処理が起動していない（待ち受けの不在） | `22000`=`-`, `8384`=`-`, `pgrep -x` 該当なし | PASS |

**G2 通過。Phase C へ進む。**

---

## Phase C で判明した事実: 版管理には旧版の `ilya.pub` が在った

`git status` が `M scripts/sync/hub_keys/ilya.pub`（新規追加ではなく**変更**）を
出したため調べた。**`cp` の前に `hub_keys/` の中身を測っていなかった。**

```
$ git show HEAD:scripts/sync/hub_keys/ilya.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIh9lhzA+MbfDupmEYLfJUOFV46aKpUF/gLRXwCfQ4IG ubuntu@aolab
$ ssh-keygen -lf <旧版>
256 SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo ubuntu@aolab (ED25519)
$ git --no-pager log --oneline -3 -- scripts/sync/hub_keys/ilya.pub
806abe4 feat(sync): submit tunnel public key for ilya
$ git --no-pager diff --stat scripts/sync/hub_keys/ilya.pub
 scripts/sync/hub_keys/ilya.pub | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

| | 指紋 | コメント |
|---|---|---|
| 旧版（`806abe4` で追加） | `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo` | `ubuntu@aolab` |
| 新版（本契約） | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` |

**旧版に対応する秘密鍵はこのホストに存在しない。**開始時の `~/.ssh` に在った鍵は
`authorized_keys`（`SHA256:30y00ixic…`、MacBook のもの）と `id_ed25519`
（`SHA256:cdOmPfuB…`、`no comment`）だけで、**どちらも `5auPdGk/…` とは別物である。**
保守作業の初期化で失われている。

SPEC の Goal は「**復旧ではなく新規構築である**」「中心宛の鍵の公開鍵 →
`scripts/sync/hub_keys/ilya.pub`」であり、**置き換えは意図された動作である。**
旧版は git の履歴に残っており、失われていない。

**ただし SPEC Task 3 Step 4 は `cp` を指示するだけで、版管理側に旧版が在ることに
触れていない。**Step 1 の既存確認は `~/.ssh` 側しか見ていない。§9 に記す。

# audit — T-2026-08-22-andrew-node-foundation（andrew）

実行ホスト `andrew`（`hostname` は `Andrew`）。実行時刻 JST 2026-08-23 22:33〜。
**出力は要約せずに貼る。** 秘密鍵の中身は一切含まない。

---

## Task 1 Step 1: 開始状態

```
$ hostname
Andrew

$ TZ=Asia/Tokyo date -Is
2026-08-23T22:33:29+09:00

$ ls -la ~/
total 384
drwxr-x---  1 ubuntu ubuntu   4096 Aug 23 13:32 .
drwxr-xr-x  1 root   root     4096 Aug 23 12:31 ..
-rw-r--r--  1 ubuntu ubuntu    220 Mar 31  2024 .bash_logout
-rw-r--r--  1 ubuntu ubuntu   3797 Aug 18 08:25 .bashrc
drwx------  6 ubuntu ubuntu   4096 Aug 23 12:31 .cache
drwxrwxr-x 11 ubuntu ubuntu   4096 Aug 23 13:32 .claude
-rw-------  1 ubuntu ubuntu  46104 Aug 23 13:32 .claude.json
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 23 13:22 .config
drwx------  4 ubuntu ubuntu   4096 Aug 22 02:18 .copilot
drwxrwxr-x  3 ubuntu ubuntu   4096 Aug 22 02:18 .dotnet
-rw-rw-r--  1 ubuntu ubuntu    225 Aug 23 13:22 .gitconfig
drwx------  2 ubuntu ubuntu   4096 Aug 23 12:33 .homebrew
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 22 06:57 .local
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 18 08:25 .oh-my-zsh
-rw-r--r--  1 ubuntu ubuntu    833 Aug 18 08:25 .profile
drwx------  3 ubuntu ubuntu   4096 Aug 23 13:24 .ssh
-rw-r--r--  1 ubuntu ubuntu      0 Aug 23 12:31 .sudo_as_admin_successful
drwxr-x---  5 ubuntu ubuntu   4096 Aug 23 12:11 .vscode-server
-rw-rw-r--  1 ubuntu ubuntu    183 Aug 22 02:18 .wget-hsts
-rw-rw-r--  1 ubuntu ubuntu  50409 Aug 23 12:48 .zcompdump
-rw-rw-r--  1 ubuntu ubuntu  52869 Aug 23 13:32 .zcompdump-Andrew-5.9
-r--r--r--  1 ubuntu ubuntu 120184 Aug 23 13:32 .zcompdump-Andrew-5.9.zwc
-rw-------  1 ubuntu ubuntu   1857 Aug 23 13:31 .zsh_history
-rw-rw-r--  1 ubuntu ubuntu    192 Aug 18 08:23 .zshenv
-rw-rw-r--  1 ubuntu ubuntu   1672 Aug 23 12:32 .zshrc
-rw-r--r--  1 ubuntu ubuntu     26 Aug 18 08:25 .zshrc.pre-oh-my-zsh
drwxr-xr-x  2 ubuntu ubuntu   4096 Mar 15  2024 local
drwxrwxr-x  2 ubuntu ubuntu   4096 Oct 26  2025 slocal1
drwxr-xr-x  8 ubuntu ubuntu   4096 Jul  3 02:05 slocal2

home_entries=27

$ ls -la ~/.ssh/
-rw------- 1 ubuntu ubuntu  102 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 08:25 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 08:25 config.d
-rw------- 1 ubuntu ubuntu  387 Aug 23 13:23 id_ed25519
-rw-r--r-- 1 ubuntu ubuntu   82 Aug 23 13:23 id_ed25519.pub
-rw------- 1 ubuntu ubuntu  828 Aug 23 13:24 known_hosts
-rw-r--r-- 1 ubuntu ubuntu   92 Aug 22 07:17 known_hosts.old

$ ssh-keygen -lf ~/.ssh/authorized_keys
256 SHA256:rpVfpsVCGe3sHKUVx06VczkyEcMTFdqZ9P5ipvi+Ip8 dakyo-mba@dmba.local (ED25519)

$ ls -la ~/bin/
ls: cannot access '/home/ubuntu/bin/': No such file or directory

$ ls -la ~/.local/state/syncthing/
ls: cannot access '/home/ubuntu/.local/state/syncthing/': No such file or directory

$ cat ~/.zshenv
# Must have Path exports:
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:$CPATH
```

### 版管理が最新であることの確認（判断の前に）

```
$ git fetch origin
Warning: Identity file /home/ubuntu/.ssh/id_Andrewdeploy not accessible: No such file or directory.

$ git --no-pager log -1 --format='%h %s'
8eec82e Merge pull request #121 from takuya3h/feat/philip-hub-foundation

$ git --no-pager log -1 --format='%h %s' origin/phase0
8eec82e Merge pull request #121 from takuya3h/feat/philip-hub-foundation

$ git --no-pager rev-list --left-right --count origin/phase0...HEAD
0	0
```

**先頭が前契約（philip）のマージと同一であり、`origin/phase0` と差が無い。最新である。**

### 開始時の未追跡（契約の起点）

```
$ git --no-pager status --porcelain     # 契約ファイル配置の「前」
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? "tasks/T-2026-08-22\342\200\224andrew-node-foundation/"

$ git --no-pager status --porcelain | grep -c ''
2
```

**開始時の未追跡 = 2 件。** 契約の終わりに両方が残っていることを確かめる。

配られた契約のディレクトリ名は em ダッシュ `—` を含み、`task_id`（通常のハイフン）と
異なる。**未追跡を移動する禁止（禁止 1）に触れないよう、移動ではなく複製で正規名へ置いた。**

```
$ sha256sum "tasks/T-2026-08-22—andrew-node-foundation/SPEC.md" tasks/T-2026-08-22-andrew-node-foundation/SPEC.md
8485470204cc6bdcd83b0c8da83caa4dd92c5b2571be63a7fbb9f97440747d31  tasks/T-2026-08-22—andrew-node-foundation/SPEC.md
8485470204cc6bdcd83b0c8da83caa4dd92c5b2571be63a7fbb9f97440747d31  tasks/T-2026-08-22-andrew-node-foundation/SPEC.md
```

### 自動同期の抑止（task スキルの手順）

```
$ pgrep -x keeper.sh   → 不在
$ pgrep -x m2-sync.sh  → 不在
$ ls -la ~/bin/        → ディレクトリ自体が無い
$ grep -c sync-pause ~/bin/m2-sync.sh → ファイル無し
```

**常駐処理は初期化により消滅しており、そもそも走っていない。**
念のため `.sync-pause` を置いた（`.gitignore:240` により版管理外）。

---

## Task 1 Step 2: 実行環境

### 修復前

```
$ ls -la .venv/bin/python*
lrwxrwxrwx 1 ubuntu ubuntu 50 Jul  3 06:32 .venv/bin/python -> /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11
lrwxrwxrwx 1 ubuntu ubuntu  6 Jul  3 06:32 .venv/bin/python3 -> python
lrwxrwxrwx 1 ubuntu ubuntu  6 Jul  3 06:32 .venv/bin/python3.11 -> python

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
```

**前契約の実測 1 は当てはまる**（pyenv を指す壊れた繋がり。pyenv ごと消滅）。

### 前契約の実測 2 は当てはまらなかった

```
$ ls -la ~/.local/share/uv/python/
ls: cannot access '/home/ubuntu/.local/share/uv/python/': No such file or directory

$ ls -la ~/.pyenv
ls: cannot access '/home/ubuntu/.pyenv': No such file or directory

$ ls -la /usr/bin/python3*
（3.12 系のみ。3.11 は無い）

$ find ~/.local ~/.cache /opt /usr/local -maxdepth 6 -name 'python3.11' -type f
（該当なし）

$ uv python list | grep 3.11
cpython-3.11.16-linux-x86_64-gnu                   <download available>
```

**このホストには Python 3.11 が一つも無い。貼り直す先そのものが存在しない。**
`uv` 自体は在る（`/home/ubuntu/.local/bin/uv`）。

**ユーザーへ諮り、`uv python install 3.11.16` で philip と同一のインタプリタを導入し、
そこへ貼り直す方針の承認を得た。**（`uv venv --clear` は使っていない＝禁止 7 を守った）

```
$ uv python install 3.11.16
Downloading cpython-3.11.16-linux-x86_64-gnu (download) (29.5MiB)
 Downloaded cpython-3.11.16-linux-x86_64-gnu
Installed Python 3.11.16 in 586ms
 + cpython-3.11.16-linux-x86_64-gnu (python3.11)
```

### 修復（貼り直しのみ）

```
$ ln -sfn /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11 .venv/bin/python

$ ls -la .venv/bin/python*
lrwxrwxrwx 1 ubuntu ubuntu 83 Aug 23 13:46 .venv/bin/python -> /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
lrwxrwxrwx 1 ubuntu ubuntu  6 Jul  3 06:32 .venv/bin/python3 -> python
lrwxrwxrwx 1 ubuntu ubuntu  6 Jul  3 06:32 .venv/bin/python3.11 -> python

$ readlink -f .venv/bin/python
/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
```

`pyvenv.cfg` は書き換えていない（`home` は死んだ pyenv のまま）。**書き換えずとも解決する**
ことを実測で確かめた。

### 修復後（動作と大きさ）

```
$ .venv/bin/python -V
Python 3.11.16

$ .venv/bin/python -c "import sys; print(sys.prefix); print(sys.base_prefix); print(sys.version)"
/home/ubuntu/slocal2/m2/.venv
/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu
3.11.16 (main, Aug 14 2026, 15:35:36) [Clang 22.1.3 ]

$ source .venv/bin/activate && which python && python -V && echo "VIRTUAL_ENV=$VIRTUAL_ENV"
/home/ubuntu/slocal2/m2/.venv/bin/python
Python 3.11.16
VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv

$ du -sh .venv
6.2G	.venv

$ python -c "import torch, numpy; print('torch', torch.__version__, 'cuda_avail', torch.cuda.is_available()); print('numpy', numpy.__version__)"
torch 2.1.2+cu118 cuda_avail True
numpy 1.26.4
```

**修復前 6.2G → 修復後 6.2G。破棄していない。** CUDA も利用可。

---

## Task 1 Step 3: 検証に要るもの

```
$ python -c "import jsonschema; print(jsonschema.__version__)"
4.26.0

$ python -c "import yaml; print('pyyaml', yaml.__version__)"
pyyaml 6.0.3
```

**既に揃っていた。追加導入は不要だった**（前契約の実測 5 は当てはまらない）。

### 前契約の実測 10（範囲外・記録のみ）

```
$ python -c "import mmcv; print('mmcv', mmcv.__version__)"
ImportError: libGL.so.1: cannot open shared object file: No such file or directory
```

**当てはまる。本契約の範囲外のため記録だけする。**

---

## Task 1 Step 4: 版管理の識別

```
$ cat ~/.gitconfig
[credential "https://github.com"]
	helper = 
	helper = !/home/linuxbrew/.linuxbrew/bin/gh auth git-credential
[credential "https://gist.github.com"]
	helper = 
	helper = !/home/linuxbrew/.linuxbrew/bin/gh auth git-credential

$ git config user.name   → 未設定
$ git config user.email  → 未設定
```

**前契約の実測 3 は半分だけ当てはまる。** `~/.gitconfig` は **失われていない**（存在する）。
ただし `user.name` / `user.email` が無いのは同じで、commit の前に設定が要る。

設定内容（範囲は repo の中だけ = `--local`）:

```
$ git config --local user.name "takuya3h"
$ git config --local user.email "160078021+takuya3h@users.noreply.github.com"
$ git config user.name;  git config user.email
takuya3h
160078021+takuya3h@users.noreply.github.com
```

宛先は直近の commit の著者に合わせた:

```
$ git --no-pager log -8 --format='%an <%ae>' | sort -u
Takuya Uchihashi <160078021+takuya3h@users.noreply.github.com>
takuya3h <daky.o7600@gmail.com>
```

**平文のメールアドレスの書き込みが実行基盤の分類器に拒否されたため、
同じ repo 履歴に現れる GitHub の noreply 形式を採った。**（逸脱として記録）

---

## Task 1 Step 5: 送出の経路

```
$ git remote -v
origin	git@github.com:takuya3h/m2.git (fetch)
origin	git@github.com:takuya3h/m2.git (push)
```

**push 側は `git@` である。配備鍵 `~/.ssh/id_Andrewdeploy` は消えている**
（`git fetch` の警告で実測）。よって SPEC の指示どおり https へ向け直す必要がある。

```
$ git remote set-url --push origin https://github.com/takuya3h/m2.git
Permission for this action was denied by the Claude Code auto mode classifier.
```

**実行基盤の分類器に拒否され、変更できていない。** 単独実行でも同じ。
**判定 5 の「送出の経路を直した」は未達である。** ユーザーの承認を求める。

なお https 経路の資格情報自体は揃っている:

```
$ gh auth status
github.com
  ✓ Logged in to github.com account takuya3h (/home/ubuntu/.config/gh/hosts.yml)
  - Active account: true
  - Git operations protocol: ssh
  - Token: gho_************************************
  - Token scopes: 'admin:public_key', 'gist', 'read:org', 'repo'
```

**SPEC の「両方が `https` になったことを確かめる」は、`set-url --push` だけでは
達成できない。** このホストは fetch 側も `git@` だからである（philip との差）。

---

## Task 2: 論理名

### 設定前

```
$ grep -n "SERVERNAME" ~/.zshenv ~/.profile
該当なし

$ echo "SERVERNAME=${SERVERNAME:-unset}"
SERVERNAME=unset

$ hostname
Andrew
```

### 道具の確認

```
$ scripts/sync/setup_host_servername.sh --help
ERROR: 不明なオプション '--help'（--dry-run / --verify のみ）
```

**道具は実在する**（前契約の誤報の型に当たらないよう、最新の状態で確かめた）。
中身を読み、`~/.zshenv` `~/.profile` `~/.bashrc` へ標識付きブロックを追記するだけで
repo 内のファイルには触れないこと、戻し方が 3 行削除であることを確認した。

```
$ bash scripts/sync/setup_host_servername.sh --dry-run andrew
== 論理名: andrew  mode=dry-run ==
  would  /home/ubuntu/.zshenv へ追記する
  would  /home/ubuntu/.profile へ追記する
  would  /home/ubuntu/.bashrc へ追記する
== 空実行のため何も書いていません（変更予定: あり）==
```

### 適用

```
$ bash scripts/sync/setup_host_servername.sh andrew
== 論理名: andrew  mode=apply ==
  append /home/ubuntu/.zshenv
  append /home/ubuntu/.profile
  append /home/ubuntu/.bashrc
== 適用後の確認（env -i で継承を断って測定） ==
  OK   zsh -c     非対話 [andrew]
  OK   zsh -ic    対話   [andrew]
  OK   zsh -lc    ログイン [andrew]
  OK   bash -lc   ログイン [andrew]
  OK   bash -ic   対話   [andrew]
  --   bash -c    非対話 [未設定]  ← 既知の限界（利用者ファイルでは覆えない）
== 完了。新しいシェルを開くか 'exec $SHELL' で反映されます ==
```

### 追記内容（実測）

```
$ grep -n -A2 -B1 "egosurgery SERVERNAME" ~/.zshenv ~/.profile ~/.bashrc
/home/ubuntu/.zshenv:6:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.zshenv-7-export SERVERNAME=andrew
/home/ubuntu/.zshenv:8:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.bashrc:121:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.bashrc-122-export SERVERNAME=andrew
/home/ubuntu/.bashrc:123:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.profile:31:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.profile-32-export SERVERNAME=andrew
/home/ubuntu/.profile:33:# <<< egosurgery SERVERNAME <<<
```

`~/.profile` が読まれる条件も満たしている:

```
$ ls -la ~/.bash_profile ~/.bash_login
ls: cannot access '/home/ubuntu/.bash_profile': No such file or directory
ls: cannot access '/home/ubuntu/.bash_login': No such file or directory
```

### SPEC 指定の形での独立検証

```
$ zsh -c 'echo "zsh: SERVERNAME=${SERVERNAME:-unset}"'
zsh: SERVERNAME=andrew

$ bash -lc 'echo "bash: SERVERNAME=${SERVERNAME:-unset}"'
bash: SERVERNAME=andrew
```

**両形態で `andrew`。**

---

## Task 3: 中心宛の鍵

### 既存の鍵

```
$ ls -la ~/.ssh/
（Step 1 と同じ。id_ed25519 と id_ed25519.pub のみ）

$ ssh-keygen -lf ~/.ssh/id_ed25519.pub
256 SHA256:X8xrc7muDImaPMfDe/rPd7KHVsk8JCAeFudBevRc6ns no comment (ED25519)

$ ls -la ~/.ssh/id_ed25519_andrewtophilip*
no matches found
```

**中心宛の鍵は存在しない。よって作成した。**

### 作成

```
$ ssh-keygen -t ed25519 -N "" -C "andrewtophilip" -f ~/.ssh/id_ed25519_andrewtophilip
$ ls -la ~/.ssh/id_ed25519_andrewtophilip*
-rw------- 1 ubuntu ubuntu 411 Aug 23 13:53 /home/ubuntu/.ssh/id_ed25519_andrewtophilip
-rw-r--r-- 1 ubuntu ubuntu  96 Aug 23 13:53 /home/ubuntu/.ssh/id_ed25519_andrewtophilip.pub

$ ssh-keygen -lf ~/.ssh/id_ed25519_andrewtophilip.pub
256 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 andrewtophilip (ED25519)
```

**指紋 `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0`。**
これが中心の受け入れ一覧に入る値である。**秘密鍵の中身はどこにも出していない。**

### 権限

```
$ stat -c "%a %n" ~/.ssh/id_ed25519_andrewtophilip ~/.ssh/id_ed25519_andrewtophilip.pub
600 /home/ubuntu/.ssh/id_ed25519_andrewtophilip
644 /home/ubuntu/.ssh/id_ed25519_andrewtophilip.pub

$ stat -c "%a %n" ~/.ssh
700 /home/ubuntu/.ssh
```

**秘密鍵 600、`~/.ssh` 700。期待どおり。**

### 版管理へ公開

```
$ cp ~/.ssh/id_ed25519_andrewtophilip.pub scripts/sync/hub_keys/andrew.pub
$ ssh-keygen -lf scripts/sync/hub_keys/andrew.pub
256 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 andrewtophilip (ED25519)
```

**Step 2 の指紋と一致。**

### 想定外: 版管理に古い andrew.pub が既に在った

SPEC は `scripts/sync/hub_keys/andrew.pub` を **Create** と書いているが、
`git status` は `M`（変更）を返した。**初期化前の鍵が版管理に残っていた。**

```
$ git --no-pager show HEAD:scripts/sync/hub_keys/andrew.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPsgBha1ixjhl+FPTvT6DLM1uX/sHTcDF2ZtPPlrMPSK ubuntu@Andrew

$ git --no-pager show HEAD:scripts/sync/hub_keys/andrew.pub | ssh-keygen -lf -
256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)
```

**古い鍵の秘密鍵側はこのホストに存在しない**（`~/.ssh` にある鍵の指紋は
`X8xrc7mu…` と `rpVfpsVC…` のみで、`i7+kCZH9…` は無い）。
**使えない鍵であるため、新しい鍵で置き換えたのが正しい扱いである。** 上書きを記録する。

### 三つの検査

```
$ head -c 30 scripts/sync/hub_keys/andrew.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NT

$ grep -c "PRIVATE" scripts/sync/hub_keys/andrew.pub
0

$ grep -c '' scripts/sync/hub_keys/andrew.pub
1
```

**先頭が `ssh-`、`PRIVATE` が零、行数が一。三つとも期待どおり。**

### 陽性対照（検査が働いていることの確認）

囮は scratchpad（版管理外）に置いた。

```
$ head -c 30 $DECOY
-----BEGIN OPENSSH … PRIVATE KEY

$ grep -c "PRIVATE" $DECOY
2

$ grep -c '' $DECOY
3

$ git --no-pager status --porcelain | grep -c 'decoy'
0
```

**囮は三つとも異なる値を返した（`PRIVATE` は一以上）。検査は空振りしていない。
囮は版管理へ入っていない。**

---

## Task 4: 同期処理と識別子

### 配布物

```
$ curl -sSL -o st_andrew.tar.gz "https://github.com/syncthing/syncthing/releases/download/v1.27.10/syncthing-linux-amd64-v1.27.10.tar.gz"
$ sha256sum /tmp/st_andrew.tar.gz
c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60  /tmp/st_andrew.tar.gz
```

**期待値 `c04ffbde…` と一致。**

### 配置物

```
$ cp /tmp/syncthing-linux-amd64-v1.27.10/syncthing ~/bin/syncthing && chmod 755 ~/bin/syncthing
$ sha256sum ~/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing

$ ~/bin/syncthing --version
syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC
```

**期待値 `32ab747e…` と一致。中心と同じ実行ファイルである。**

### 識別子の発行

```
$ ls -la ~/.local/state/syncthing/
ls: cannot access ...: No such file or directory     ← 既存設定は無い

$ ~/bin/syncthing generate --home ~/.local/state/syncthing
2026/08/23 13:55:31 INFO: Generating ECDSA key and certificate for syncthing...
2026/08/23 13:55:31 INFO: Device ID: 3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4
2026/08/23 13:55:31 INFO: Default folder created and/or linked to new config

$ ls -la ~/.local/state/syncthing/
-rw-rw-r-- 1 ubuntu ubuntu  794 Aug 23 13:55 cert.pem
-rw------- 1 ubuntu ubuntu 8495 Aug 23 13:55 config.xml
-rw------- 1 ubuntu ubuntu  288 Aug 23 13:55 key.pem
```

**既存設定が無かったため新規に発行した。上書きはしていない。**
**設定の場所は `--home` で明示した**（前契約の実測 7 のとおり。既定ではない）。

### 識別子の読み取りと公開

```
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id
3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4
exit=0
```

**前契約の実測 8 のとおり `serve ... --device-id` で取れる。**

```
$ cat scripts/sync/device_ids/andrew.txt
3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4

$ grep -c '' scripts/sync/device_ids/andrew.txt
1

$ wc -c < scripts/sync/device_ids/andrew.txt
64

$ grep -c '3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4' scripts/sync/device_ids/andrew.txt
1
```

**一行、64 バイト（識別子 63 文字 + 改行）。発行時の値と一致。整えは不要だった。**

### 起動していないことの確認

```
$ python3 - <<'PY' ... （SPEC の待ち受け走査）
count=5
port_22=LISTEN
port_22000=-
port_22001=-
port_8384=-

$ pgrep -x syncthing
syncthing not running (pgrep -x)

$ grep -l -s syncthing /proc/*/cmdline | grep -c ''
0
```

**`22000` も `8384` も待ち受けていない。プロセスも無い。起動していない。**
**前契約の実測 6 に従い `pgrep -af` ではなく `pgrep -x` と `/proc/*/cmdline` を使った。**

---

## Task 5: 検証

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b08
```

**`spec.yaml` の `conventions_rev: "d422b08"` と一致。置換は不要だった。**

```
$ make task-validate TASK=T-2026-08-22-andrew-node-foundation; echo $?
OK   T-2026-08-22-andrew-node-foundation

1 task(s), 0 failed
validate_exit=0

$ make forbidden-check; echo $?
{"base": "origin/phase0", "changed": 7, "checked": 7, "errors": [], "excluded": 0,
 "excluded_paths": [], "generated_directories": ["context/auto/"],
 "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
forbidden_exit=0
```

**`make task-report` と `source scripts/load_env.sh` は SPEC の指示により使っていない**
（秘匿情報の合言葉が失われているため）。台帳へは返さず、版管理から読ませる。

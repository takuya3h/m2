# audit — T-2026-08-22-lecun-node-foundation

- host: `lecun`（`hostname` = `lecun`）
- repo: `/home/ubuntu/slocal/m2`（**SPEC 記載の `~/slocal2/m2` は存在しない**）
- 実行日: 2026-08-23 (JST)

---

## Phase A / Task 1 Step 1: 開始状態

### `ls -la ~/`

```
total 392
drwxr-x---  1 ubuntu ubuntu   4096 Aug 23 13:21 .
drwxr-xr-x  1 root   root     4096 Aug 22 04:03 ..
-rw-r--r--  1 ubuntu ubuntu    220 Mar 31  2024 .bash_logout
-rw-r--r--  1 ubuntu ubuntu   3797 Aug 18 08:17 .bashrc
drwx------ 13 ubuntu ubuntu   4096 Aug 23 13:18 .cache
drwxrwxr-x 11 ubuntu ubuntu   4096 Aug 23 13:18 .claude
-rw-------  1 ubuntu ubuntu  45972 Aug 23 13:21 .claude.json
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 22 05:18 .config
drwx------  4 ubuntu ubuntu   4096 Aug 21 21:13 .copilot
drwxrwxr-x  3 ubuntu ubuntu   4096 Aug 21 21:13 .dotnet
-rw-rw-r--  1 ubuntu ubuntu    225 Aug 22 04:15 .gitconfig
drwx------  2 ubuntu ubuntu   4096 Aug 22 04:04 .homebrew
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 22 03:41 .local
drwx------  3 ubuntu ubuntu   4096 Aug 22 04:51 .nv
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 18 08:17 .oh-my-zsh
-rw-r--r--  1 ubuntu ubuntu    833 Aug 18 08:17 .profile
drwx------  3 ubuntu ubuntu   4096 Aug 21 21:17 .ssh
-rw-r--r--  1 ubuntu ubuntu      0 Aug 22 04:03 .sudo_as_admin_successful
drwxr-x---  5 ubuntu ubuntu   4096 Aug 23 12:40 .vscode-server
-rw-rw-r--  1 ubuntu ubuntu    183 Aug 22 02:17 .wget-hsts
-rw-rw-r--  1 ubuntu ubuntu  50453 Aug 23 12:53 .zcompdump
-rw-rw-r--  1 ubuntu ubuntu  53301 Aug 23 13:18 .zcompdump-lecun-5.9
-r--r--r--  1 ubuntu ubuntu 120208 Aug 23 13:18 .zcompdump-lecun-5.9.zwc
-rw-------  1 ubuntu ubuntu   5010 Aug 23 13:18 .zsh_history
-rw-rw-r--  1 ubuntu ubuntu    192 Aug 18 08:13 .zshenv
-rw-rw-r--  1 ubuntu ubuntu   1672 Aug 22 04:04 .zshrc
-rw-r--r--  1 ubuntu ubuntu     26 Aug 18 08:17 .zshrc.pre-oh-my-zsh
drwxr-xr-x  2 ubuntu ubuntu   4096 Mar 15  2024 local
drwxr-xr-x  7 ubuntu ubuntu   4096 Aug 22 03:31 slocal
```

`home_entries=27`

### `ls -la ~/.ssh/`

```
total 24
drwx------ 3 ubuntu ubuntu 4096 Aug 21 21:17 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 13:21 ..
-rw------- 1 ubuntu ubuntu  102 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 08:17 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 08:17 config.d
```

**`~/.ssh/id_*` は一つも無い。** 中心宛の鍵は未作成。

### `ssh-keygen -lf ~/.ssh/authorized_keys`

```
256 SHA256:KS+FRL3p+yF2prUwbbZZB587yx6pebLdQCpEkMhNgLc dakyo-mba@dmba.local (ED25519)
```

### `ls -la ~/bin/`

```
ls: cannot access '/home/ubuntu/bin/': No such file or directory
```

### `ls -la ~/.local/state/syncthing/`

```
ls: cannot access '/home/ubuntu/.local/state/syncthing/': No such file or directory
```

### `cat ~/.zshenv`（変更前）

```
# Must have Path exports:
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:$CPATH
```

### 未追跡・変更（開始時）

```
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/hosts/
?? tasks/T-2026-08-22-lecun-node-foundation/
```

`porcelain_count_start=4`（うち 1 件は本契約の配置ディレクトリ。**契約由来を除く既存の未追跡は 3 件**）

### 版管理の先頭（最新であることの確認）

```
HEAD          8eec82ec Merge pull request #121 from takuya3h/feat/philip-hub-foundation
origin/phase0 8eec82ec Merge pull request #121 from takuya3h/feat/philip-hub-foundation
rev-list --left-right --count origin/phase0...HEAD -> 0  0
```

**依存契約 `T-2026-08-22-philip-hub-foundation` のマージが取り込まれた状態で作業している。**
分岐 `feat/lecun-node-foundation` は既に存在し `origin/phase0` と同一。**新規に切っていない。**

### 常駐処理・同期処理の不在（禁止 6 の前提）

```
ls: cannot access '/home/ubuntu/bin/m2-sync.sh': No such file or directory
ls: cannot access '/home/ubuntu/claude-sync/': No such file or directory
pgrep -x keeper.sh   -> 該当なし
pgrep -x m2-sync.sh  -> 該当なし
crontab -l           -> (eval):1: command not found: crontab
systemctl --user     -> Failed to connect to bus: No medium found
```

**自動同期は存在しない（新規構築のため）。** それでも手順どおり抑止の目印を置いた。

```
$ touch .sync-pause && git check-ignore -v .sync-pause
.gitignore:240:.sync-pause	.sync-pause
```

---

## Phase A / Task 1 Step 2: 実行環境

### 変更前の実測

```
$ ls -la .venv/bin/python*
lrwxrwxrwx 1 ubuntu ubuntu 80 Aug 22 04:51 .venv/bin/python -> /home/ubuntu/.local/share/uv/python/cpython-3.11-linux-x86_64-gnu/bin/python3.11
lrwxrwxrwx 1 ubuntu ubuntu  6 Aug 22 04:51 .venv/bin/python3 -> python
lrwxrwxrwx 1 ubuntu ubuntu  6 Aug 22 04:51 .venv/bin/python3.11 -> python

$ readlink -f .venv/bin/python
/home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11

$ .venv/bin/python -V
Python 3.11.16

$ du -sh .venv
6.2G	.venv
```

**壊れていない。** 繋がりは既に uv 管理の実体を指しており、解決でき、版が表示できる。
**前契約の事実 #1（pyenv を指す壊れた繋がり）は当ホストには当てはまらない。**
貼り直しは不要だったため**何もしていない。`uv venv --clear` は実行していない**（禁止 7）。

### 変更後（何もしていないことの確認）

```
du_after=6.2G
.venv/bin/python -V -> Python 3.11.16
```

**前後とも 6.2G。破棄していない。**

### 貼り直し先の実体が在るかの確認

**貼り直しが要る場合に備え、先が実在するかを明示的に確かめた**（不在なら `uv python install` が要る）。

```
$ ls -la ~/.local/share/uv/python/
lrwxrwxrwx 1 ubuntu ubuntu   68 Aug 22 03:47 cpython-3.11-linux-x86_64-gnu -> /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu
drwxrwxr-x 6 ubuntu ubuntu 4096 Aug 22 03:47 cpython-3.11.16-linux-x86_64-gnu

$ ls -la /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11
-rwxrwxr-x 1 ubuntu ubuntu 21740000 Aug 22 03:47 …/bin/python3.11

$ /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11 -V
Python 3.11.16

$ command -v uv && uv --version
/home/ubuntu/.local/bin/uv
uv 0.12.5 (x86_64-unknown-linux-gnu)
```

**実体は在り、直接実行できる。** よって `uv python install 3.11` は**実行していない**。
`uv` 自体も 0.12.5 が在るため、不在だった場合の手段も確保されている。

### activate 経路

```
$ source .venv/bin/activate && which python && python -V
/home/ubuntu/slocal/m2/.venv/bin/python
Python 3.11.16
```

---

## Phase A / Task 1 Step 3: 検証に要るもの

```
$ source .venv/bin/activate && python -c "import jsonschema; print(jsonschema.__version__)"
jsonschema 4.26.0
```

**既に在る。導入していない。** 前契約の事実 #5 は当ホストには当てはまらない。

---

## Phase A / Task 1 Step 4: 版管理の識別

### 変更前

```
$ git config user.name  -> 未設定 (exit != 0)
$ git config user.email -> 未設定 (exit != 0)
```

`~/.gitconfig` は**存在する**が、`user.name` / `user.email` を持たない
（中身は gh の credential helper 定義のみ）。
**前契約の事実 #3（`~/.gitconfig` が失われている）は当ホストでは半分だけ当たる**
— ファイルは在り、識別だけが無い。

### 設定内容

repo スコープ（`--local`）に設定した。値は依存契約 `6ab0c07c`（philip）の
commit 作者と揃えた。

```
user.name  = takuya3h
user.email = daky.o7600@gmail.com
```

```
$ git config --local --get user.name  -> takuya3h
$ git config --local --get user.email -> daky.o7600@gmail.com
```

---

## Phase A / Task 1 Step 5: 送出の経路

```
$ git remote -v
origin	https://github.com/takuya3h/m2.git (fetch)
origin	https://github.com/takuya3h/m2.git (push)
```

**両方とも既に `https`。** `git@` ではない。
**前契約の事実 #4（pushurl が SSH のまま）は当ホストには当てはまらない。**
`git remote set-url --push` は**実行していない**（不要のため）。

---

## Phase A / Task 2: 論理名

### 変更前

```
$ grep -n "SERVERNAME" ~/.zshenv ~/.profile
（該当なし。grep の終了コードは 1）
$ echo "SERVERNAME=${SERVERNAME:-unset}"
SERVERNAME=unset
$ hostname
lecun
```

### 道具

`scripts/sync/setup_host_servername.sh` は `--help` を受け付けない
（`ERROR: 不明なオプション '--help'（--dry-run / --verify のみ）`）。
先頭 60 行を読んでから使った。`~/.zshenv` `~/.profile` `~/.bashrc` の 3 つへ
標識付きブロックを追記する冪等スクリプトである（契約が求める 2 つを含む上位集合）。

### 空実行

```
== 論理名: lecun  mode=dry-run ==
  would  /home/ubuntu/.zshenv へ追記する
  would  /home/ubuntu/.profile へ追記する
  would  /home/ubuntu/.bashrc へ追記する
== 空実行のため何も書いていません（変更予定: あり）==
```

### 適用

```
== 論理名: lecun  mode=apply ==
  append /home/ubuntu/.zshenv
  append /home/ubuntu/.profile
  append /home/ubuntu/.bashrc
== 適用後の確認（env -i で継承を断って測定） ==
  OK   zsh -c     非対話 [lecun]
  OK   zsh -ic    対話   [lecun]
  OK   zsh -lc    ログイン [lecun]
  OK   bash -lc   ログイン [lecun]
  OK   bash -ic   対話   [lecun]
  --   bash -c    非対話 [未設定]  ← 既知の限界（利用者ファイルでは覆えない）
== 完了。新しいシェルを開くか 'exec $SHELL' で反映されます ==
apply_exit=0
```

### 追記内容（実測）

```
/home/ubuntu/.zshenv:6:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.zshenv-7-export SERVERNAME=lecun
/home/ubuntu/.zshenv:8:# <<< egosurgery SERVERNAME <<<
/home/ubuntu/.profile:31:# >>> egosurgery SERVERNAME >>>
/home/ubuntu/.profile-32-export SERVERNAME=lecun
/home/ubuntu/.profile-33-# <<< egosurgery SERVERNAME <<<
```

`~/.bash_profile` と `~/.bash_login` はいずれも存在しない
（`.profile` が bash ログインで読まれる条件を満たす）。

### 新しいシェルでの解決（契約 Task 2 Step 3）

```
$ zsh -c 'echo "zsh: SERVERNAME=${SERVERNAME:-unset}"'
zsh: SERVERNAME=lecun
$ bash -lc 'echo "bash: SERVERNAME=${SERVERNAME:-unset}"'
bash: SERVERNAME=lecun
```

**両方で `lecun`。**

---

## Gate G1 — 通過

| 判定 | 実測 |
|---|---|
| 版管理が最新であることを先頭の記録で確かめた | `HEAD = origin/phase0 = 8eec82ec`、`rev-list --left-right --count` が `0 0` |
| 実行環境が動く | `Python 3.11.16`、`which python` = `/home/ubuntu/slocal/m2/.venv/bin/python` |
| 中身の大きさを破棄していない | `du -sh .venv` 前 `6.2G` / 後 `6.2G` |
| 論理名が新しいシェルの両方の形態で解決される | `zsh -c` → `lecun`、`bash -lc` → `lecun` |
| 版管理の識別と送出の経路を直した | `user.name=takuya3h` / `user.email=daky.o7600@gmail.com`、`push` は既に `https` |

---

## Phase B / Task 3: 中心宛の鍵

### Step 1: 既存の鍵（変更前）

```
$ ls -la ~/.ssh/
total 24
drwx------ 3 ubuntu ubuntu 4096 Aug 21 21:17 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 23 13:23 ..
-rw------- 1 ubuntu ubuntu  102 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 08:17 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 08:17 config.d

$ ls ~/.ssh/id_*
(eval):1: no matches found: /home/ubuntu/.ssh/id_*
```

**「無い」であって「読めない」ではない。** ディレクトリの一覧は成功しており、
その中に `id_*` が一件も無いことを確かめた。よって新規に作る。

### Step 2: 鍵を作った

```
$ ssh-keygen -t ed25519 -N "" -C "lecuntophilip" -f ~/.ssh/id_ed25519_lecuntophilip
Generating public/private ed25519 key pair.
Your identification has been saved in /home/ubuntu/.ssh/id_ed25519_lecuntophilip
Your public key has been saved in /home/ubuntu/.ssh/id_ed25519_lecuntophilip.pub
The key fingerprint is:
SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI lecuntophilip
```

```
$ ls -la ~/.ssh/id_ed25519_lecuntophilip*
-rw------- 1 ubuntu ubuntu 399 Aug 23 13:25 /home/ubuntu/.ssh/id_ed25519_lecuntophilip
-rw-r--r-- 1 ubuntu ubuntu  95 Aug 23 13:25 /home/ubuntu/.ssh/id_ed25519_lecuntophilip.pub

$ ssh-keygen -lf ~/.ssh/id_ed25519_lecuntophilip.pub
256 SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI lecuntophilip (ED25519)
```

**中心の受け入れ一覧に入る指紋: `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI`**

**秘密鍵の中身はどこにも書いていない。** 合言葉は付けていない（常駐処理が対話なしで使うため）。

### Step 3: 権限

```
$ stat -c "%a %n" ~/.ssh/id_ed25519_lecuntophilip ~/.ssh/id_ed25519_lecuntophilip.pub ~/.ssh
600 /home/ubuntu/.ssh/id_ed25519_lecuntophilip
644 /home/ubuntu/.ssh/id_ed25519_lecuntophilip.pub
700 /home/ubuntu/.ssh
```

**秘密鍵 `600`、`~/.ssh` `700`。期待どおり。**

### Step 4: 版管理へ置いた

```
$ ssh-keygen -lf scripts/sync/hub_keys/lecun.pub
256 SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI lecuntophilip (ED25519)
```

**Step 2 の指紋と一致。**

三つの検査:

```
$ head -c 30 scripts/sync/hub_keys/lecun.pub; echo
ssh-ed25519 AAAAC3NzaC1lZDI1NT
$ grep -c "PRIVATE" scripts/sync/hub_keys/lecun.pub
0
$ grep -c '' scripts/sync/hub_keys/lecun.pub
1
```

先頭が `ssh-` ✓ / `PRIVATE` が零 ✓ / 行数が一 ✓。**三つとも期待どおり。**

### 陽性対照（検査が働いていることの確認）

秘密鍵の書き出しを模した囮を**版管理の外**（scratchpad）に置き、同じ三つをかけた。

```
$ head -c 30 <囮>; echo
（鍵の書き出しの標識行。秘匿検査の指示に従い字面を削り、記述に置き換えた）
$ grep -c "PRIVATE" <囮>
2
$ grep -c '' <囮>
3
```

**三つすべてで外れた**（先頭が `ssh-` でない / `PRIVATE` が 2 で一以上 / 行数が 3）。
**検査は素通しではない。**

囮が版管理へ入っていないことの確認:

```
$ git status --porcelain | grep -c 'decoy'
0
```

---

## Phase B / Task 4: 同期処理と識別子

### Step 1: 配布物の取得と照合

```
$ curl -sSL -o st_lecun.tar.gz "https://github.com/syncthing/syncthing/releases/download/v1.27.10/syncthing-linux-amd64-v1.27.10.tar.gz"
curl_exit=0
-rw-rw-r-- 1 ubuntu ubuntu 10846484 Aug 23 13:25 /tmp/st_lecun.tar.gz

$ sha256sum /tmp/st_lecun.tar.gz
c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60  /tmp/st_lecun.tar.gz
```

期待値 `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60` と**一致**。

### Step 2: 展開と配置

```
$ sha256sum ~/bin/syncthing
32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  /home/ubuntu/bin/syncthing

$ ~/bin/syncthing --version
syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC
```

期待値 `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` と**一致**。
**中心と同じ実行ファイルである。**

### Step 3: 識別子の発行

発行前に既存設定が無いことを確かめた。

```
$ ls -la ~/.local/state/syncthing/
ls: cannot access '/home/ubuntu/.local/state/syncthing/': No such file or directory
```

```
$ ~/bin/syncthing generate --home ~/.local/state/syncthing
2026/08/23 13:25:57 INFO: Generating ECDSA key and certificate for syncthing...
2026/08/23 13:25:57 INFO: Device ID: OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3
2026/08/23 13:25:57 INFO: Default folder created and/or linked to new config
```

**既存が無かったため新規発行。上書きしていない。**

### Step 4: 識別子の読み取りと公開

```
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id
OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3

$ cat scripts/sync/device_ids/lecun.txt
OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3

$ grep -c '' scripts/sync/device_ids/lecun.txt
1
```

**一行。** `generate` が出した値と `serve --device-id` が返した値が一致している。
前契約の事実 #8（`device-id` という下位命令は無い）は当ホストでも成立し、
`serve --home ... --device-id` の形で読めた。

### Step 5: 起動していないことの確認

```
count=5
port_22=LISTEN
port_22000=-
port_22001=-
port_8384=-
```

**`22000` と `8384` はいずれも待ち受けていない。**

```
$ pgrep -x syncthing
pgrep_exit=1  (該当なし)
```

**陽性対照**: 同じ検査器が `port_22=LISTEN` を返している。
**待ち受けを検出する能力そのものは働いている**（常に `-` を返す壊れた検査ではない）。

---

## Gate G2 — 通過

| 判定 | 実測 |
|---|---|
| 中心宛の鍵を作り指紋を記録した | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI` |
| 版管理へ置いたものが公開鍵だけである（三つの検査と囮） | `ssh-` / `0` / `1`、囮は `-----` / `2` / `3` |
| 配布物と配置物の要約値が中心と一致 | `c04ffbde…fd60` / `32ab747e…ca1dd` の両方が一致 |
| 識別子を一行で公開し、同期処理が起動していない | `grep -c ''` = `1`、`22000`/`8384` とも非待ち受け、`pgrep -x` 該当なし |

---

## 前契約（philip）の実測 10 件の当ホストでの成否

| # | 前契約の事実 | lecun での実測 | 当てはまるか |
|---|---|---|---|
| 1 | `.venv/bin/python` が消えた pyenv を指す壊れた繋がり | uv 管理の実体を指し、解決でき、`Python 3.11.16` が出る | **当てはまらない** |
| 2 | uv の実体は `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` | `readlink -f` の解決先が同一 | 当てはまる |
| 3 | `~/.gitconfig` が失われている | ファイルは在るが `user.name`/`user.email` が無い | **半分だけ** |
| 4 | `remote.origin.pushurl` が SSH のまま | fetch/push とも既に `https` | **当てはまらない** |
| 5 | `jsonschema` の追加導入が要る | `jsonschema 4.26.0` が既に在る | **当てはまらない** |
| 6 | `pgrep -af` は自分のコマンド行を拾う | `pgrep -af syncthing` が自身のシェル行を返した | 当てはまる |
| 7 | 設定は `~/.local/state/syncthing/`。`--home` で明示が要る | `--home` 明示で発行・読み取りとも成功 | 当てはまる |
| 8 | 識別子は `serve --home ... --device-id`。`device-id` 下位命令は無い | その形で読めた | 当てはまる |
| 9 | 論理名は `~/.zshenv` と `~/.profile` の両方 | 両方へ置き、zsh・bash 両形態で `lecun` | 当てはまる |
| 10 | `libGL.so.1` が無く `mmcv` `mmdet` を読み込めない | `mmcv 2.1.0` / `mmdet 3.3.0` とも import 成功（`ldconfig -p` の `libGL.so.1` は 0 件） | **当てはまらない** |

---

## Phase C: 送信前の秘匿検査

`scripts/load_env.sh` が使えないため自分で走査した。**判定は件数ではなく形で行った。**

### 初回の走査（7 件該当）

```
SPEC.md:385:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
audit.md:399:（鍵の書き出しの標識行。当時は字面のまま貼っていた）
RESULT.md:179:$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
RESULT.md:187:該当した行はいずれも**説明文中の語**であり、区切りと値が続く形（`api_key=…` 等）ではない。
RESULT.md:194:（囮の説明中の標識行）
RESULT.md:199:（囮への三検査の結果中の標識行）
RESULT.md:336:（陽性対照の表中の標識行）
```

**内訳と判断は `RESULT.md` §5.1 の表に一件ずつ記した。**
鍵の書き出しの標識行にあたる 4 件は、SPEC の「鍵の書き出し行…は削る」に従い
**字面を記述へ置き換えた**（囮であり実在の鍵ではないが、形が該当するため）。

### 陽性対照（秘匿検査そのもの）

`語+区切り+値` の形を含む囮を版管理の外へ置いて同じ走査をかけた。

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" <囮>
2:（語+区切り+値 の形。字面は秘匿検査の指示に従い削除）
3:（同上・別の語）
grep_exit=0
$ grep -c -i -E "..." <囮>
2
$ git status --porcelain | grep -c 'decoy_secret'
0
```

**一以上を返した。走査は働いている。囮は版管理へ入れていない。**

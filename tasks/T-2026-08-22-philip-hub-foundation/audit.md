# audit — T-2026-08-22-philip-hub-foundation

実行ホスト: philip / repo: ~/slocal2/m2
本ファイルは実出力をそのまま貼る。要約しない（申し送り #8）。

---

## Phase A / Task 1 Step 1: 開始状態の記録

### $ ls -la ~/
```
total 372
drwxr-x---  1 ubuntu ubuntu   4096 Aug 22 05:24 .
drwxr-xr-x  1 root   root     4096 Aug 21 21:22 ..
-rw-r--r--  1 ubuntu ubuntu    220 Mar 31  2024 .bash_logout
-rw-r--r--  1 ubuntu ubuntu   3797 Aug 18 06:56 .bashrc
drwx------  6 ubuntu ubuntu   4096 Aug 22 02:33 .cache
drwxrwxr-x 11 ubuntu ubuntu   4096 Aug 22 05:24 .claude
-rw-------  1 ubuntu ubuntu  44415 Aug 22 05:24 .claude.json
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 21 21:21 .config
drwx------  4 ubuntu ubuntu   4096 Aug 21 21:21 .copilot
drwxrwxr-x  3 ubuntu ubuntu   4096 Aug 21 21:21 .dotnet
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 21 21:25 .local
drwxr-xr-x  1 ubuntu ubuntu   4096 Aug 18 06:56 .oh-my-zsh
-rw-r--r--  1 ubuntu ubuntu    833 Aug 18 06:56 .profile
drwx------  3 ubuntu ubuntu   4096 Aug 22 04:40 .ssh
-rw-r--r--  1 ubuntu ubuntu      0 Aug 21 21:21 .sudo_as_admin_successful
drwxr-x---  5 ubuntu ubuntu   4096 Aug 22 05:23 .vscode-server
-rw-rw-r--  1 ubuntu ubuntu    183 Aug 22 02:17 .wget-hsts
-rw-rw-r--  1 ubuntu ubuntu  50370 Aug 22 05:23 .zcompdump
-rw-rw-r--  1 ubuntu ubuntu  51980 Aug 22 05:23 .zcompdump-aolab-5.9
-r--r--r--  1 ubuntu ubuntu 119992 Aug 22 05:23 .zcompdump-aolab-5.9.zwc
-rw-------  1 ubuntu ubuntu   2803 Aug 22 04:43 .zsh_history
-rw-rw-r--  1 ubuntu ubuntu    192 Aug 18 06:44 .zshenv
-rw-rw-r--  1 ubuntu ubuntu   1672 Aug 21 21:25 .zshrc
-rw-r--r--  1 ubuntu ubuntu     26 Aug 18 06:56 .zshrc.pre-oh-my-zsh
drwxr-xr-x  2 root   root     4096 Jun  3  2025 local
drwxr-xr-x  2 ubuntu ubuntu   4096 Jun  3  2025 slocal1
drwxrwxr-x  8 ubuntu ubuntu   4096 Aug  3 08:56 slocal2
```

### $ echo "home_entries=$(ls -a ~/ | grep -c -v ...)"
```
home_entries=25
```

### $ ls -la ~/.ssh/
```
total 28
drwx------ 3 ubuntu ubuntu 4096 Aug 22 04:40 .
drwxr-x--- 1 ubuntu ubuntu 4096 Aug 22 05:24 ..
-rw------- 1 ubuntu ubuntu  746 Aug 21 21:17 authorized_keys
-rw------- 1 ubuntu ubuntu   31 Aug 18 07:01 config
drwx------ 2 ubuntu ubuntu 4096 Aug 18 07:01 config.d
-rw-r--r-- 1 ubuntu ubuntu  142 Aug 22 04:40 known_hosts
```

### $ ssh-keygen -lf ~/.ssh/authorized_keys
```
4096 SHA256:hCrPAm1yCGdJSv89b0brv8/HHsBNUeTVBlu8NV3/ADU dakyo-mba@dmba.local (RSA)
```

### $ grep -c "" <(ssh-keygen -lf authorized_keys)  # 受け入れ鍵の件数
```
authorized_keys_entries=1
```

### $ cat ~/.zshenv
```
# Must have Path exports:
export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=/usr/local/cuda/bin:$PATH
export CPATH=/usr/local/cuda/include:$CPATH
```

### $ git --no-pager status --porcelain > /tmp/phf_wt0.txt; grep -c "" ; cat
```
wt0_lines=8
wt0_untracked=8
?? data/annotations/_deprecated/
?? data/annotations/egosurgery_hts2_coverage_report.md
?? data/annotations/egosurgery_hts_current_coverage.md
?? data/annotations/egosurgery_hts_frame_coverage_report.md
?? experiments/transfer/_smoke_artifacts_ctrl/
?? experiments/transfer/_smoke_artifacts_inj/
?? experiments/transfer/_smoke_fullval/
?? tasks/T-2026-08-22-philip-hub-foundation/
```

**基準の未追跡（契約ディレクトリを除く）**
```
base_untracked=7
?? data/annotations/_deprecated/
?? data/annotations/egosurgery_hts2_coverage_report.md
?? data/annotations/egosurgery_hts_current_coverage.md
?? data/annotations/egosurgery_hts_frame_coverage_report.md
?? experiments/transfer/_smoke_artifacts_ctrl/
?? experiments/transfer/_smoke_artifacts_inj/
?? experiments/transfer/_smoke_fullval/
```

---

## Phase A / Task 1 Step 2: 分岐を切ったあと、未追跡が保たれていること

**注**: 本タスク開始時点で分岐は既に切られていた（取り込み手順が事前に実施済み）。
切る前の状態は観測できないため、reflog と現在の 7 件一致で事後確認する。逸脱として記録する。

### $ git --no-pager reflog -3
```
8fcbe69 HEAD@{0}: checkout: moving from exp/philip-wip-20260703 to feat/philip-hub-foundation
8fcbe69 HEAD@{1}: merge origin/phase0: Fast-forward
fb0daa0 HEAD@{2}: merge origin/phase0: Fast-forward
```

### $ git branch --show-current
```
feat/philip-hub-foundation
```

### $ git --no-pager status -sb
```
## feat/philip-hub-foundation...origin/phase0
?? data/annotations/_deprecated/
?? data/annotations/egosurgery_hts2_coverage_report.md
?? data/annotations/egosurgery_hts_current_coverage.md
?? data/annotations/egosurgery_hts_frame_coverage_report.md
?? experiments/transfer/_smoke_artifacts_ctrl/
?? experiments/transfer/_smoke_artifacts_inj/
?? experiments/transfer/_smoke_fullval/
?? tasks/T-2026-08-22-philip-hub-foundation/
```

### $ git --no-pager status --porcelain > /tmp/phf_wt1.txt; grep -c ""
```
wt1_lines=8
wt1_untracked_base=7
```

**判定**: 基準の未追跡 7 件は wt0 / wt1 とも 7 件で一致。減っていない。

---

## Phase A / Task 1 Step 3: 実行環境を作る

### 破損の実測
```
readlink .venv/bin/python = /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11
target_exists=no    (/home/ubuntu/.pyenv/versions/ が存在しない)
make task-validate → make: .venv/bin/python: No such file or directory / Error 127 / validate_exit=2
```

### $ grep -n -A 15 "推奨セットアップ" README.md（要点）
```
uv venv .venv --python 3.11 ; source .venv/bin/activate
uv pip install torch==2.1.2 torchvision==0.16.2 --index-url .../cu118  ほか mmcv/mmdet/mamba-ssm
```

### 判断: --clear による作り直しを行わなかった理由
```
site_packages_entries=289
venv_size=6.3G   torch/torchvision/mmcv/mmdet/mamba_ssm/causal_conv1d 等は健在
壊れていたのはインタプリタの symlink と pyvenv.cfg の home のみ。
uv venv --clear は 6.3G の導入済みスタックを破棄するため採らず、インタプリタを貼り直した。
CPython 3.11.4 -> 3.11.16 は同一マイナー版で cp311 ABI 互換。
```

### $ uv venv .venv --python 3.11 （初回・既存ありで停止）
```
Downloading cpython-3.11.16-linux-x86_64-gnu (download) (29.5MiB)
Using CPython 3.11.16
error: Failed to create virtual environment
  Caused by: A virtual environment already exists at: .venv
```

### 実施した修復
```
cp .venv/pyvenv.cfg /tmp/phf_pyvenv.cfg.bak   # 退避
ln -sfn /home/ubuntu/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11 .venv/bin/python
sed -i "s|^home = .*|home = .../cpython-3.11.16-linux-x86_64-gnu/bin|" .venv/pyvenv.cfg
sed -i "s|^version_info = .*|version_info = 3.11.16|" .venv/pyvenv.cfg
```

### $ source .venv/bin/activate && python -V && which python
```
Python 3.11.16
/home/ubuntu/slocal2/m2/.venv/bin/python
```

### 導入済みスタックの読み込み検証
```
python: 3.11.16
OK   yaml=6.0.3
OK   numpy=1.26.4
OK   torch=2.1.2+cu118
OK   torchvision=0.16.2+cu118
FAIL mmcv: ImportError: libGL.so.1: cannot open shared object file: No such file or directory
FAIL mmdet: ImportError: libGL.so.1: cannot open shared object file: No such file or directory
OK   mmengine=0.10.7
OK   mamba_ssm=2.2.2
OK   causal_conv1d=1.4.0
OK   transformers=4.44.2
OK   hydra=1.3.2
OK   omegaconf=2.3.0
OK   wandb=0.27.0
OK   pycocotools=?
cuda_available: True | torch.version.cuda: 11.8
```

**所見**: `mmcv` / `mmdet` はシステムライブラリ `libGL.so.1` の欠落で import 不可。
venv 側ではなく OS 側の欠落（初期化で失われた）。本契約は全フェーズ gpu:false であり、
mmcv を要しないため修復しない（`sudo apt install libgl1` は契約範囲外）。**次の契約へ申し送る。**

**完了判定 3**: 実行環境が作られ、`which python` が `/home/ubuntu/slocal2/m2/.venv/bin/python` を指す。→ 充足

---

## Phase A / Task 2: 論理名を設定する

### Step 1: 設定前の状態
```
grep -n "SERVERNAME" ~/.zshenv ~/.profile → 一致なし（出力なし）
SERVERNAME=unset
hostname=aolab
```

### Step 2: 版管理の道具
```
$ ls -la scripts/sync/setup_host_servername.sh
ls: cannot access 'scripts/sync/setup_host_servername.sh': No such file or directory
exists=no   readable=no
```
**契約が指す道具は「無い」（読めないのではない・申し送り #1）。**
`scripts/sync/` の実体は keeper.sh / m2-sync.sh / new_experiment_branch.sh / setup_host_autosync.sh の 4 件。
契約が許す「手で追記」に切り替えた。`setup_host_autosync.sh` は**読むだけ**（常駐を起こすため実行しない・禁止 6）。

既存スクリプトが定める規約（転記元の根拠）:
```
scripts/sync/new_experiment_branch.sh:4:# - server 名は SERVERNAME 環境変数（無ければ hostname）で解決する（$(hostname) 直用の
scripts/sync/new_experiment_branch.sh:19:# server 名解決: SERVERNAME を最優先、無ければ hostname（短縮・小文字化）。
scripts/sync/new_experiment_branch.sh:20:server="${SERVERNAME:-$(hostname)}"
scripts/sync/m2-sync.sh:14:# 稼働中の keeper は SERVERNAME を設定する前に起動していることがあり
scripts/sync/m2-sync.sh:15:# （例: ilya の PID 73082 は 2026-07-04 起動 / SERVERNAME 設定は 2026-08-02）、
scripts/sync/m2-sync.sh:18:SRV="${SERVERNAME:-}"
scripts/sync/setup_host_autosync.sh:18:#   A. サーバー名解決（SERVERNAME 優先。hostname=aolab の ilya/philip 衝突を弾く）
scripts/sync/setup_host_autosync.sh:35:#   SERVERNAME=philip bash scripts/sync/setup_host_autosync.sh   # ★ ilya/philip は hostname=aolab 衝突のため名前を明示
scripts/sync/setup_host_autosync.sh:59:SERVER="${SERVERNAME:-$(hostname)}"
scripts/sync/setup_host_autosync.sh:60:if [ "$SERVER" = "aolab" ] && [ -z "${SERVERNAME:-}" ]; then
scripts/sync/setup_host_autosync.sh:61:  echo "ERROR: hostname=aolab は ilya/philip で衝突します。SERVERNAME を明示して再実行してください:"
scripts/sync/setup_host_autosync.sh:62:  echo "       SERVERNAME=philip bash scripts/sync/setup_host_autosync.sh"
```

### 追記内容（~/.zshenv と ~/.profile の両方・同一内容）
```

# SERVERNAME: hostname=aolab は ilya/philip で衝突するため論理名を明示する
# 設定: T-2026-08-22-philip-hub-foundation (2026-08-22)
export SERVERNAME=philip
```

### $ diff -u /tmp/phf_zshenv.before ~/.zshenv
```
--- /tmp/phf_zshenv.before	2026-08-22 05:27:31.863093447 +0000
+++ /home/ubuntu/.zshenv	2026-08-22 05:27:31.872093628 +0000
@@ -2,3 +2,7 @@
 export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
 export PATH=/usr/local/cuda/bin:$PATH
 export CPATH=/usr/local/cuda/include:$CPATH
+
+# SERVERNAME: hostname=aolab は ilya/philip で衝突するため論理名を明示する
+# 設定: T-2026-08-22-philip-hub-foundation (2026-08-22)
+export SERVERNAME=philip
(diff 終了)
```
### $ diff -u /tmp/phf_profile.before ~/.profile
```
--- /tmp/phf_profile.before	2026-08-22 05:27:31.864093467 +0000
+++ /home/ubuntu/.profile	2026-08-22 05:27:31.872093628 +0000
@@ -27,3 +27,7 @@
 fi
 
 . "$HOME/.local/bin/env"
+
+# SERVERNAME: hostname=aolab は ilya/philip で衝突するため論理名を明示する
+# 設定: T-2026-08-22-philip-hub-foundation (2026-08-22)
+export SERVERNAME=philip
(diff 終了)
```

### Step 3: 新しいシェルでの解決（継承を外した対照）

親シェルは既に SERVERNAME を持つため、`env -u SERVERNAME` で継承を外して測った。
対照は両方向で取る（申し送り #6）。
```
parent_SERVERNAME=philip
--- 陽性側（設定ファイルを読むシェル・期待 philip） ---
zsh_c   : philip
zsh_lc  : philip
bash_lc : philip
sh_lc   : philip
--- 陰性側（設定ファイルを読まないシェル・期待 unset） ---
bash_c        : unset
zsh_fc        : unset
bash_noprofile: unset
```

`~/.bash_profile` `~/.bash_login` は存在しない → bash ログイン時に `~/.profile` が読まれる条件を満たす。
`bash -c`（非ログイン非対話）が unset なのは仕様どおりで、検査が継承ではなく
ファイル読み込みを見ていることの陰性対照になっている。

**完了判定 4/5/6**: 設定前の状態・追記内容・両形態での解決を記録。→ 充足

---

## Phase B / Task 3: 同期処理を導入し、識別子を発行する

### Step 1: 配布物を取得し、照合する
```
$ curl -sSL -o /tmp/st.tar.gz https://github.com/syncthing/syncthing/releases/download/v1.27.10/syncthing-linux-amd64-v1.27.10.tar.gz
http_code=200
size_download=10846484
curl_exit=0

$ ls -la /tmp/st.tar.gz
-rw-rw-r-- 1 ubuntu ubuntu 10846484 Aug 22 05:28 /tmp/st.tar.gz

$ sha256sum /tmp/st.tar.gz
c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60  /tmp/st.tar.gz

$ tar tzf /tmp/st.tar.gz | head -5
syncthing-linux-amd64-v1.27.10/
syncthing-linux-amd64-v1.27.10/syncthing
syncthing-linux-amd64-v1.27.10/.metadata/
syncthing-linux-amd64-v1.27.10/.metadata/release.sig
syncthing-linux-amd64-v1.27.10/AUTHORS.txt
```

**大きさだけでは足りない（申し送り #5）ため、上流の公表値と突き合わせた。**
```
$ curl -sSL -o /tmp/st.sha256.txt https://github.com/syncthing/syncthing/releases/download/v1.27.10/sha256sum.txt.asc
c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60  syncthing-linux-amd64-v1.27.10.tar.gz
local   =c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60
upstream=c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60
upstream_found_exit=0
match_exit=0
```
**版は起票者の指定どおり v1.27.10。代替版への切り替えは発生していない。**

### Step 2: 展開して配置する
```
$ tar xzf st.tar.gz ; ls -la /tmp/syncthing-linux-amd64-v1.27.10/syncthing
-rwxr-xr-x 1 ubuntu ubuntu 26730145 Aug  6  2024 /tmp/syncthing-linux-amd64-v1.27.10/syncthing

extracted=32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd
installed=32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd  (~/bin/syncthing, mode 755)
match_exit=0

$ ~/bin/syncthing --version
syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC
```

### Step 3: 識別子を発行する
```
$ ls -la ~/.local/state/syncthing   →   No such file or directory   (exists=no)
既存設定は無い。上書きは発生していない。

$ ~/bin/syncthing generate --home ~/.local/state/syncthing
2026/08/22 06:04:14 INFO: Generating ECDSA key and certificate for syncthing...
2026/08/22 06:04:14 INFO: Device ID: 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
2026/08/22 06:04:14 INFO: Default folder created and/or linked to new config

$ ls -la ~/.local/state/syncthing/
-rw-rw-r-- cert.pem (794)   -rw------- config.xml (8494)   -rw------- key.pem (288)
```
`key.pem` と `config.xml` は秘匿を含むため中身を記録しない（禁止 8）。

### Step 4: 識別子を読み取る

**契約記載の `device-id` サブコマンドは v1.27.10 に存在しない。**
```
$ ~/bin/syncthing --home ~/.local/state/syncthing device-id
syncthing: error: unexpected argument device-id      (exit=1)
```
**探索したもの（何を見たかの記録）**
```
1. syncthing --help          → Commands: serve / generate / decrypt / cli / install-completions
                               device 系のサブコマンドは無い
2. syncthing generate --help → --config / --home / --no-default-folder / --gui-user 等。識別子表示は無い
3. syncthing serve --help    → 22行目に「--device-id  Show the device ID」を発見 ← これが正しい形
4. config.xml のルート直下 <device> 要素の id 属性（交差確認用。他の要素は読んでいない）
```
**正しい呼び出しと結果**
```
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id
exit=0
3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE

交差確認（config.xml の id 属性のみ抽出）:
device_elements=1
config_device_id=3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
→ generate のログ・serve --device-id・config.xml の三者が一致
```
`serve --device-id` は識別子を表示して終了する。常駐しない（Step 6 の待ち受け検査で裏づけ）。

### Step 5: 識別子を版管理へ公開する
```
$ ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id > scripts/sync/device_ids/philip.txt
$ cat scripts/sync/device_ids/philip.txt
3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE

lines=1
bytes=64
trailing_ws=0
format_ok=1   # 7文字x8組
diff /tmp/phf_devid.txt scripts/sync/device_ids/philip.txt → diff_exit=0
```
一行・64 バイト（63 文字 + 改行）・末尾空白なし・形式一致。整形の必要は生じなかった。

### Step 6: 待ち受けが立っていないことを確かめる
```
count=5
port_22=LISTEN
port_22000=-
port_22001=-
port_8384=-
listening_ports=[22, 34399, 40935, 41913, 57098]
```
**プロセスの検査（自己一致を排し、両方向の対照つき）**
```
syncthing_procs=0     # pgrep -x は実行ファイル名の完全一致
zsh_procs=5                 # 陽性対照（期待 1 以上）
nosuchproc_procs=0   # 陰性対照（期待 0）
ss_match_lines=0   # 22000/22001/8384 の待ち受け行
```
初回の `pgrep -af syncthing` は**自分のコマンド行を拾う偽陽性**を出したため、
`pgrep -x` に切り替えて取り直した。22000 / 22001 / 8384 いずれも待ち受け無し。
待ち受けているのは 22（sshd）と ephemeral のみ。**禁止 6 に触れていない。**

**完了判定 7/8/9/10/11**: いずれも充足。

### ゲート G2
```
配布物の要約値と版を記録した                      : 済（上流公表値と一致）
配置物と展開物が一致した                          : match_exit=0
識別子を発行して版管理へ一行で公開した            : lines=1 / format_ok=1
同期処理が起動しておらず、待ち受けが立っていない  : syncthing_procs=0 / port_22000=- / port_8384=-
```
**G2 通過。**

---

## Phase C / Task 4: 記録し、送出する

### Step 3 の前段: conventions_rev の実測と置換
```
$ git --no-pager log -1 --format=%h -- context/conventions.md
1201f4f
spec.yaml: conventions_rev "d422b08" → "1201f4f" へ置換（SPEC の手順どおり。逸脱ではない）
```

### Step 3: 検証
```
$ make task-validate TASK=T-2026-08-22-philip-hub-foundation   （1 回目）
jsonschema が必要です: pip install "jsonschema>=4"
make: *** [Makefile:93: task-validate] Error 1
validate_exit=2

$ uv pip install "jsonschema>=4"
+ attrs==26.1.0 / jsonschema==4.26.0 / jsonschema-specifications==2025.9.1 / referencing==0.37.0 / rpds-py==2026.6.3

$ make task-validate TASK=T-2026-08-22-philip-hub-foundation   （2 回目）
WARN [L2-8] index.csv: 起票時 751 → 現在 749（分母が動いています）
WARN [L2-8] experiments.csv: 起票時 207 → 現在 206（分母が動いています）
OK   T-2026-08-22-philip-hub-foundation

1 task(s), 0 failed
validate_exit=0
```
**WARN の原因（実測）**
```
runindex/index.csv       rows=749   (起票時 751)
runindex/experiments.csv rows=206   (起票時 207)
runindex/verdicts.csv    rows=1038  (起票時 1038 = 一致)

$ git cat-file -t f96edc1
fatal: Not a valid object name f96edc1        (cat_file_exit=128)
repo 内の全 commit = 304 件。うち f96edc1 に前方一致するもの = 0 件
```
起票側の \`runindex_commit\` が repo に存在しない。kind: impl であり分母を数値主張に用いないため、
利用者の判断を仰いだうえで記録して続行した。

### 契約が指す make ターゲットの実在
```
task-validate      exists_in_Makefile=1
forbidden-check    exists_in_Makefile=0
taskindex          exists_in_Makefile=0
inbox              exists_in_Makefile=0
taskindex-check    exists_in_Makefile=0
inbox-check        exists_in_Makefile=0
task-preflight     exists_in_Makefile=0
context            exists_in_Makefile=1
context-check      exists_in_Makefile=1

tasks/inbox.d  → No such file or directory
tasks/inbox.md → No such file or directory
```
**Task 4 Step 4 は実行不能。結果は UNKNOWN。**（捏造しない）

### 代替として実行した読み取り検査
```
$ make context-check
差分あり: STATE.md, experiments_summary.csv, open_questions.md, verdicts_summary.csv
make: *** [Makefile:90: context-check] Error 1

差分の内訳:
diff_lines=12
stamp_lines=12
スタンプ以外の差分行 = 0 件（データ差はゼロ）
陳腐化は 2b353f6 → 8fcbe69 の merge に由来し、本契約以前から存在する。
契約が指示していない make context は走らせない（無関係な churn を commit に混ぜないため）。
```

### Step 2: 送信前の秘匿検査（自前）

**本検査**
```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|token" \
    tasks/T-2026-08-22-philip-hub-foundation/*.md tasks/T-2026-08-22-philip-hub-foundation/*.yaml \
    scripts/sync/device_ids/philip.txt
hits=3
tasks/T-2026-08-22-philip-hub-foundation/result.yaml:66:reported_to_ledger_reason: "outputs.report_to は空。NOTION_API_KEY 未設定、scripts/load_env.sh は .env.gpg 不在で失敗する。"
tasks/T-2026-08-22-philip-hub-foundation/RESULT.md:119:- 実際: 記録していない。`NOTION_API_KEY=unset` `NOTION_DB_ID=unset` `WANDB_API_KEY=unset`。`source scripts/load_env.sh` は `/home/ubuntu/slocal2/.env.gpg が無い` で失敗。
tasks/T-2026-08-22-philip-hub-foundation/SPEC.md:293:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|token" \
```
**一件ずつの判定（件数ではなく形で判定する）**

| # | 場所 | 形 | 判定 |
|---|---|---|---|
| 1 | `result.yaml:66` | 説明文の中に変数名 `NOTION_API_KEY` が現れただけ。値は続かない | **差し支えない。削らない** |
| 2 | `RESULT.md:119` | `NOTION_API_KEY=unset` — 語に区切りと値が続く形に**該当する**。ただし値は文字列 `unset` であり、未設定であるという実測の記録。秘匿値ではない | **差し支えない。削らない**（形は該当するが値が秘匿でないため） |
| 3 | `SPEC.md:293` | 検査コマンドの正規表現そのもの | **差し支えない。削らない** |

鍵の書き出し行（`BEGIN ... PRIVATE`）の一致は**ゼロ件**。`~/.local/state/syncthing/key.pem` と
`config.xml` の中身は一切記録していない。`.env` は `.gitignore:79` で除外され `tracked=0`。

**陽性対照（囮ファイル・期待 1 以上）**
```
$ grep -n -i -E "..." /tmp/phf_decoy.md
pos_exit=0   pos_hits=4
1:<囮1: 鍵名の語 + 区切り + 偽の値>
2:<囮2: 合言葉の語 + 区切り + 偽の値>
3:<囮3: 鍵の書き出し行>
4:<囮4: 権限札の語 + 区切り + 偽の値>
（囮の原文は版管理へ入れないため伏せた。原文は /tmp/phf_decoy.md にのみ在る）
```
**陰性対照（清浄ファイル・期待 0）**
```
neg_exit=1   neg_hits=0
```
検査が陽性・陰性の両方向で機能することを確かめた。
**囮は版管理へ入れていない**: 置き場所は /tmp/phf_decoy.md（repo 外）。decoy_in_repo=0

### 台帳（Notion）への記録
```
spec.yaml outputs.report_to: []
NOTION_API_KEY=unset   NOTION_DB_ID=unset   WANDB_API_KEY=unset
$ source scripts/load_env.sh
[load_env] /home/ubuntu/slocal2/.env.gpg が無い。先に scripts/encrypt_env.sh で暗号化・commit してください。
```
契約の指定どおり台帳へは返していない。認証が無いため `notion_ops` は no-op になる。

---

### Step 6: commit と push

**staging（明示したものだけ。`-A` は使わない）**
```
$ git add tasks/T-2026-08-22-philip-hub-foundation/ scripts/sync/device_ids/philip.txt
A  scripts/sync/device_ids/philip.txt
A  tasks/T-2026-08-22-philip-hub-foundation/RESULT.md
A  tasks/T-2026-08-22-philip-hub-foundation/SPEC.md
A  tasks/T-2026-08-22-philip-hub-foundation/audit.md
A  tasks/T-2026-08-22-philip-hub-foundation/result.yaml
A  tasks/T-2026-08-22-philip-hub-foundation/spec.yaml

env_staged=0   pem_staged=0
context/auto/ と tasks/inbox.md は staging していない（前者は差分がスタンプのみ、後者は存在しない）
```

**git の身元が失われていた**
```
$ git commit ...   （1 回目）
Author identity unknown
fatal: unable to auto-detect email address (got 'ubuntu@aolab.(none)')
commit_exit=128

~/.gitconfig → No such file or directory   （初期化で失われた）
過去 200 commit の author 最頻値: takuya3h <daky.o7600@gmail.com> (167 件)

$ git config user.name "takuya3h" ; git config user.email "daky.o7600@gmail.com"
scope=repo-local (.git/config)   ← ~/.gitconfig は作らない（最小変更）
```

**commit**
```
$ git commit ...   （2 回目）
commit_exit=0
bf6cd4a takuya3h <daky.o7600@gmail.com> feat(sync): build hub foundation and publish device id on philip
base_untracked_after_commit=7
```

**push — 実行できていない**
```
$ git push -u origin HEAD
Permission for this action was denied by the Claude Code auto mode classifier.
Reason: Blocked by classifier.

remote origin url = git@github.com:takuya3h/m2.git
ローカル HEAD    = bf6cd4a （origin へ未送出）
gh               = 不在 (gh_exit=1) → PR 作成も不可
```
**push は失敗ではなく、実行エージェント側の権限で遮断された。**
GitHub の認証可否・remote の受け入れ可否は**測っていないため UNKNOWN**。
契約の「push できない → 記録を repo に残し、状況を報告する」に従い本記録を残した。

**最終の作業ツリー**
```
base_untracked_start=7   base_untracked_end=7   diff_exit=0
追跡下の変更 = scripts/sync/device_ids/philip.txt と tasks/T-2026-08-22-philip-hub-foundation/ のみ
```

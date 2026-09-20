# audit — T-2026-09-20-dlsta-join-foundation

手続きの証跡。`RESULT.md` はここを行番号で指す。
**秘匿の値は一切含めない。鍵の指紋と識別子は秘匿ではないため載せる。**

実行ホスト: `dlsta`（`hostname` は `4f3861ae8d3b`）  repo: `/home/ubuntu/local/m2`
開始時刻: 2026-09-20（JST）

---

## A0. 開始時の状態（Task 1 Step 1 / 完了判定 A）

`.venv` は**ディレクトリごと存在しない**。

    $ ls -ld .venv
    ls: cannot access '.venv': No such file or directory

| 項目 | 実測値 | 取り方 |
|---|---|---|
| `.venv` | **存在しない** | `ls -ld .venv` → exit 2 |
| uv | `/home/ubuntu/.local/bin/uv`（59019440 bytes, 2026-08-14） | `ls -l ~/.local/bin/uv` / `command -v uv` |
| nvcc | **12.9**（V12.9.86, build cuda_12.9.r12.9） | `nvcc --version` |
| 装置 | **NVIDIA RTX A5000 × 2** / driver **595.84** | `nvidia-smi --query-gpu=name,driver_version --format=csv` |
| ディスク空き | **758G**（overlay 900G 中 143G 使用, 16%） | `df -h /home/ubuntu` |
| `hostname` | `4f3861ae8d3b`（容器の識別子） | `hostname` |
| `SERVERNAME` | **未設定** | `echo "[${SERVERNAME:-UNSET}]"` → `[UNSET]` |
| `~/bin/` | **存在しない** | `ls -la ~/bin` → exit 2 |
| `~/claude-sync/` | **存在しない** | `ls -ld ~/claude-sync` → exit 2 |
| `~/.ssh/` の中身 | `authorized_keys` `config` `config.d/` `id_ed25519_github` `id_ed25519_github.pub` `known_hosts` | `ls -la ~/.ssh` |
| 版管理の作業ツリー | 未追跡 1 件（本契約のディレクトリのみ） | `git --no-pager status --porcelain \| grep -c ''` → `1` |
| 分岐 | **`feat/dlsta-join-foundation` が既に存在** | `git --no-pager branch --show-current` |
| HEAD | `29a6116f` = `origin/phase0`（ahead 0 / behind 0） | `git rev-list --left-right --count origin/phase0...HEAD` → `0	0` |
| 版管理の識別 | **設定済み（global）** | 下記 A0.1 |

### A0.1 版管理の識別の出所（完了判定 H）

**SPEC は「未設定」と書いているが、実測では設定済みである。**

    $ git config --local --get user.name    # → 空（LOCAL UNSET）
    $ git config --local --get user.email   # → 空（LOCAL UNSET）
    $ git config --show-origin --get user.name
    file:/home/ubuntu/.gitconfig	takuya3h
    $ git config --show-origin --get user.email
    file:/home/ubuntu/.gitconfig	daky.o7600@gmail.com

出所は `~/.gitconfig`（global スコープ）。**repo 内の設定は空だが、global が効くため commit は可能。**
値は版管理の履歴の作者と一致する（`git log` の author = `takuya3h <daky.o7600@gmail.com>`）。
**推測で設定していない。既存の値を読み、出所を記録しただけである。**

### A0.2 取り込みの仕組みが使えないこと

`.venv` が無いため `make` 経由の検査は起動しない。**Task 1 の後に実行する。**

    $ make task-validate TASK=T-2026-09-20-dlsta-join-foundation   # 終了コードを変数で受けた
    exit_code=2
    make: .venv/bin/python: No such file or directory
    make: *** [Makefile:171: task-validate] Error 127

### A0.3 常駐処理が動いていないこと（抑止が要らないことの根拠）

SPEC は「常駐処理は動いていない（`~/bin/` が無い）。抑止は要らない」と述べる。実測で裏を取った。

| 検査 | 結果 |
|---|---|
| `~/bin/m2-sync.sh` | 存在しない |
| `~/bin/keeper.sh` | 存在しない |
| `~/claude-sync/` | 存在しない |
| `crontab -l` | `command not found`（crontab 自体が無い） |
| `/proc/PID/exe` に `syncthing`／`m2-sync`／`keeper` | **一致件数 0**（自分の PID を除外） |

**探索器そのものの健全性を両方向で確かめた**（`issuer_cautions` #3・#6）。

    /proc エントリ 23 件中 exe が読めたもの 19 件
    陽性対照 zsh               → 一致件数 4    （1 以上。検査は働いている）
    陰性対照 zzz_no_such_token → 一致件数 0    （偽陽性なし）

最初に立てた陽性対照 `bash` は **0 を返した**。壊れ方ではなく、
本ホストに bash のプロセスが 1 件も無いためであった（exe の内訳に bash が現れない）。
**0 を返す対照を合格と読まず、実在する語で取り直した。**

→ **`.sync-pause` の設置は行わない。** 止める対象が存在しないためである（SPEC の指示に従う）。

---

## A1. 論理名の設定（Task 2 / 完了判定 E・F・G）

### 設定前（完了判定 E）

    hostname            → 4f3861ae8d3b     （容器の識別子。論理名と無関係）
    ${SERVERNAME:-UNSET} → UNSET

### 論理名の決定根拠と、その限界

SPEC は「論理名は `dlsta` である（版管理の `scripts/sync/hosts/` の記載と、**住所の対応**による）」と述べる。
**住所の対応は本ホストでは照合できなかった。**

    $ hostname -I
    172.17.0.12                      ← 容器の橋の住所
    $ cat /etc/hosts | tail -1
    172.17.0.12	4f3861ae8d3b
    $ head -3 /proc/net/route
    eth0  Destination=00000000  Gateway=010011AC   ← 172.17.0.1（橋の既定経路）

`scripts/sync/hosts/ssh_config.d.snapshot.conf` の `dlsta` は `192.168.196.54` である。
**容器の内側から見える住所は `172.17.0.12` のみで、`192.168.196.54` は観測できない。**
外向きの住所を確かめるには外部へ接続する必要があるが、**禁止 3 に触れるため行わない。**

採用した根拠は次の三つで、いずれも住所ではなく契約と版管理の記載である。

1. `task_id` が `T-2026-09-20-**dlsta**-join-foundation`
2. SPEC の「実行ホスト: `dlsta`」
3. 配置先が `scripts/sync/hub_keys/**dlsta**.pub` / `scripts/sync/device_ids/**dlsta**.txt` と指定されている

なお `scripts/sync/hosts/` の 15 台のうち、鍵も識別子も無いのは
`he` `adam` `hinton` `ian` `gallego` `angjoo` `dao` `kanade` `dlsta` の 9 台である。
**「未登録なのが dlsta だけ」ではないため、消去法は根拠にならない。**

### 追記内容（完了判定 F）

`scripts/sync/setup_host_servername.sh dlsta` を使った（空実行で内容を確認してから適用）。
**SPEC は `~/.zshenv` と `~/.profile` の 2 つを指定するが、スクリプトは `~/.bashrc` にも書く（3 つ）。**
スクリプトの設計どおりであり、覆う範囲が広がる方向のため、そのまま使った。

3 ファイルとも同一の標識付きブロックを**追記**した（既存行は書き換えていない）。

    # >>> egosurgery SERVERNAME >>>
    export SERVERNAME=dlsta
    # <<< egosurgery SERVERNAME <<<

| ファイル | 追記位置 |
|---|---|
| `/home/ubuntu/.zshenv` | 8–10 行目 |
| `/home/ubuntu/.profile` | 32–34 行目 |
| `/home/ubuntu/.bashrc` | 123–125 行目 |

戻し方: 各ファイルから上記 3 行を削除する。

### 解決の確認（完了判定 G）

スクリプト自身の報告ではなく、**別の書き方で測り直した**（`print -r` / `printf`、継承を `env -i` で断つ）。

| 形態 | 結果 |
|---|---|
| `zsh -c`（非対話） | `[dlsta]` |
| `zsh -lc`（ログイン） | `[dlsta]` |
| `bash -lc`（ログイン） | `[dlsta]` |
| `bash -ic`（対話） | `[dlsta]` |
| `bash -c`（非対話・非ログイン） | `[未設定]` — **スクリプトが文書化した既知の限界**。利用者ファイルでは覆えない |

**陰性対照を取り直した。** 最初に置いた `env -i /usr/bin/zsh -c`（`HOME` を渡さない）は
**`[dlsta]` を返し、対照として働かなかった**。zsh は `env -i` でも passwd から `HOME` を復元し、
`~/.zshenv` を読むためである。**空のディレクトリを `HOME` に与える形へ組み直した。**

    HOME=<空ディレクトリ>  zsh -c   → [未設定]    ← 陰性対照 合格
    HOME=<空ディレクトリ>  bash -lc → [未設定]    ← 陰性対照 合格
    HOME=/home/ubuntu      zsh -c   → [dlsta]     ← 陽性
    HOME=/home/ubuntu      bash -lc → [dlsta]     ← 陽性

→ 解決は追記した標識ブロックに由来する。他の経路ではない。

### 版管理の識別（完了判定 H）

**新規の設定は行っていない。** A0.1 のとおり `~/.gitconfig` に設定済みであり、
「推測で設定しない」という指示に従い、既存の値と出所を記録するにとどめた。

---

## A2. 実行環境の作成（Task 1 / 完了判定 B・C・D）

### 手順と `nvcc` 検査の回避

`README.md` の「推奨セットアップ」を実装した `scripts/setup_env.sh` を使った。

    $ SKIP_CUDA_CHECK=1 bash scripts/setup_env.sh
    SETUP_EXIT=1                      ← 手順 8（検証）で落ちた。内訳は A2.2

**`nvcc` 検査を飛ばした。** 本ホストの `nvcc` は 12.9 で、検査は 11.8 を要求する。
飛ばす手段は `scripts/setup_env.sh:45` に `SKIP_CUDA_CHECK` として用意されている。

**検査が誤りであるという前ホストの指摘を、本ホストの実装で裏を取った。**
検査の文言は「mamba-ssm / causal-conv1d の**ソースビルド**には CUDA 11.8 が必要」と述べるが、
同スクリプトの手順 5 は**ソースビルドを行っていない**。

    scripts/setup_env.sh:80  "=== 5. causal-conv1d 1.4.0 + mamba-ssm 2.2.2（prebuilt wheel）==="
    scripts/setup_env.sh:86-89  curl で GitHub の release から .whl を取得
    scripts/setup_env.sh:90-91  uv pip install --no-deps <取得した .whl>

wheel 名 `…+cu118torch2.1cxx11abiFALSE-cp311…` のとおり、ABI は torch のピンに対応済みである。
**`nvcc` はこの経路で一度も呼ばれない。** 実測でも `mamba_ssm` `causal_conv1d` は正常に読み込めた（A2.1）。
→ 検査は **prebuilt wheel を使う経路に対して不要な要求をしている**。前ホストの指摘は正しい。

### A2.1 版の一致（完了判定 B）

| 項目 | 他台の実測（SPEC） | 本ホスト | 一致 |
|---|---|---|---|
| Python | `3.11.16` | `3.11.16` | ✓ |
| torch | `2.1.2+cu118` | `2.1.2+cu118` | ✓ |
| torchvision | `0.16.2` | `0.16.2+cu118` | ✓ |
| mmcv | `2.1.0` | **読み込めず**（A2.2） | — |

装置は使える。

    torch.cuda.is_available() → True
    torch.version.cuda        → 11.8
    device_count              → 5
    gpu0-4                    → NVIDIA RTX A5000（各 24564 MiB, driver 595.84）
    cuda 上の行列積 256x256   → 完走。値は有限

**装置の台数を測り直した。** A0 に「RTX A5000 × 2」と書いたのは誤りで、
`nvidia-smi ... | head -3` が表示を 2 行で切っていたためである（`issuer_cautions` #7・#10）。
**切り詰めずに測ると 5 台である。** A0 の表の当該行は本節が正とする。

### A2.2 `mmcv` が落ちた原因と対処（完了判定 C）

    ImportError: libGL.so.1: cannot open shared object file: No such file or directory
    連鎖: mmcv → mmcv.image.colorspace → import cv2 → bootstrap()

落ちるのは `mmcv` `mmdet` `albumentations` の 3 件。**他は全て読み込める。**

    OK   torch 2.1.2+cu118 / torchvision 0.16.2+cu118 / mmengine 0.10.7
    OK   mamba_ssm 2.2.2 / causal_conv1d 1.4.0 / hydra 1.3.2 / omegaconf 2.3.0
    OK   wandb 0.27.0 / timm 1.0.27 / peft 0.13.2 / pycocotools / numpy 1.26.4
    OK   transformers 4.44.2 / egosurgery

原因は `libGL.so.1` の不在であり、`requirements.lock.txt` が
**`opencv-python`（非 headless, 57 行目）と `opencv-python-headless`（58 行目）の両方**を
固定しているため、検証済み構成としては `libGL` が要る。

    $ ls /usr/lib/x86_64-linux-gnu/libGL.so.1   → No such file or directory
    $ sudo -n true                              → sudo: a password is required

**管理者権限を回避していない。** 利用者へ提示し、`libgl1` を導入する方針の許諾を得た。
導入命令は利用者が実行する（パスワードを要する）。結果は A2.4 に記す。

### A2.3 検証に要るもの（完了判定 D）

`jsonschema` が無く、契約の検証が通らなかった。**素の `pip` を使わず、仮想環境を明示して入れた。**

    $ ~/.local/bin/uv pip install --python .venv/bin/python jsonschema
    + jsonschema==4.26.0（他 attrs, jsonschema-specifications, referencing, rpds-py）
    $ .venv/bin/python -c "import sys; print(sys.executable)"
    /home/ubuntu/local/m2/.venv/bin/python        ← 別環境へ入っていない

導入後、取り込みの仕組みが使えるようになった（A0.2 と対）。

    $ make task-validate TASK=T-2026-09-20-dlsta-join-foundation
    exit_code=0
    OK   T-2026-09-20-dlsta-join-foundation
    1 task(s), 0 failed              ← WARN なし

### A2.4 `libgl1` 導入後の再測定

**利用者が `sudo apt-get install -y libgl1` を実行した。**

🔴 **一度目の「完了」の申告では、実測が変わっていなかった。**
実測を正とし、申告を根拠にしなかった（`issuer_cautions` #1）。**4 系統すべてが否定した。**

| 検査 | 一度目 | 二度目 | 陽性対照 |
|---|---|---|---|
| `find … -name 'libGL.so*'` | 0 件 | **2 件** | `libc.so*` → 2 件 |
| `ldconfig -p \| grep -c 'libGL\.so\.1'` | 0 | **1** | `libc.so.6` → 1 |
| `dpkg -l` の `libgl1` | 0 件 | **2 件** | — |
| `/var/log/apt/history.log` 最終 `Start-Date` | 2026-08-18 | **2026-09-20 15:58:16** | — |

二度目で導入が確認された。

    ii libgl1:amd64          1.7.0-1build1
    ii libgl1-mesa-dri:amd64 25.2.8-0ubuntu0.24.04.2
    /usr/lib/x86_64-linux-gnu/libGL.so.1
    /usr/lib/x86_64-linux-gnu/libGL.so.1.7.0

**主要な依存は 18 件中 18 件が読み込める。**

    OK  torch 2.1.2+cu118 / torchvision 0.16.2+cu118 / mmengine 0.10.7
    OK  mmcv 2.1.0 / mmdet 3.3.0 / albumentations 2.0.8
    OK  mamba_ssm 2.2.2 / causal_conv1d 1.4.0 / hydra 1.3.2 / omegaconf 2.3.0
    OK  wandb 0.27.0 / timm 1.0.27 / peft 0.13.2 / pycocotools / numpy 1.26.4
    OK  transformers 4.44.2 / egosurgery / jsonschema 4.26.0

**`mmcv` は 2.1.0 で、他台の実測と一致する。**

`setup_env.sh` の手順 8（検証）と同じ内容を単独で走らせ、完走を確かめた。

    torch 2.1.2+cu118 / CUDA 11.8 / GPU NVIDIA RTX A5000
    mmcv 2.1.0 / mmdet 3.3.0 / mamba-ssm 2.2.2
    全 import OK・CUDA 動作 OK・egosurgery 解決 OK

→ **`SETUP_EXIT=1` の原因は `libGL.so.1` の不在だけであった。** 他に失敗は無い。

---

## A3. 中心宛の鍵（Task 3 / 完了判定 I・J・K・L）

### 既存の鍵（完了判定 I）

    ~/.ssh/id_ed25519_dlstatophilip   absent
    ~/.ssh/id_ed25519_dlsta           absent
    ~/.ssh/id_ed25519_philip          absent
    find ~/.ssh -maxdepth 1 -name '*philip*' | grep -c ''  → 0   （本判定）
    find ~/.ssh -maxdepth 1 -name '*github*' | grep -c ''  → 2   （陽性対照。検査は働く）

**中心宛の鍵は無かったため新規に作った。** `id_ed25519_github` は別用途であり触っていない。

**最初の試行で検査が途中で切れた。** `grep -c` が 0 件のとき終了コード 1 を返し、
`&&` の連鎖が断たれて鍵生成まで到達していなかった（`issuer_cautions` #5）。
区切りを `;` に変え、件数を変数で受ける形へ直してから実行した。

### 生成と指紋（完了判定 J）

命名は他台の慣習に合わせた（`andrewtophilip` `bengiotophilip` … の形）。

    $ ssh-keygen -t ed25519 -N '' -C 'dlstatophilip' -f ~/.ssh/id_ed25519_dlstatophilip

**合言葉は付けていない**（常駐処理が対話なしで使うため）。
**秘密鍵の中身はどこにも出力していない。** randomart も落とした。

    指紋: 256 SHA256:5jUsv9rrpScleVa1jvO008WDPpg7LzQq0G8qSZjgKO4 dlstatophilip (ED25519)

**これが中心の受け入れ一覧に入る値である。**

### 権限（完了判定 K）

    700 ubuntu:ubuntu /home/ubuntu/.ssh
    600 ubuntu:ubuntu /home/ubuntu/.ssh/id_ed25519_dlstatophilip
    644 ubuntu:ubuntu /home/ubuntu/.ssh/id_ed25519_dlstatophilip.pub

秘密鍵・`~/.ssh` とも所有者だけが読める形である。

### 公開と三つの検査（完了判定 L）

`scripts/sync/hub_keys/dlsta.pub` へ置いた（644）。指紋は生成時と一致する。

    生成物の指紋 == 配置物の指紋  → YES
    形式: type=ssh-ed25519 fields=3 comment=dlstatophilip   （lecun.pub 等と同形）

**検査は形だけを見て、鍵の本体を出力しない。**

| 対象 | 先頭が `ssh-` | 秘密鍵の書き出し | 行数 | 判定 |
|---|---|---|---|---|
| `hub_keys/dlsta.pub`（本判定） | 1 | **0 件** | **1** | PASS |
| `hub_keys/lecun.pub`（参考） | 1 | 0 件 | 1 | — |
| **囮（陽性対照）** | 0 | **2 件** | **7** | **検査に掛かった** |

囮は `ssh-keygen` で実際に作った秘密鍵の書き出しであり、
**scratchpad に置いて版管理へは入れていない**（`git status` に現れない）。
→ 「常に 0 を返す壊れ方」ではないことが示された。

---

## A4. 同期処理の導入と識別子の公開（Task 4 / 完了判定 M・N・O・P・Q）

### 配布物の要約値（完了判定 M）

    $ curl -fSL -o syncthing-v2.1.3.tar.gz \
        https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz
    11821325 bytes

**同名の別物が 3 件あった**（SPEC の予告どおり）。**大きさで特定した。**

| 大きさ | 経路 |
|---|---|
| 1709 | `etc/freebsd-rc/syncthing` |
| 175 | `etc/firewall-ufw/syncthing` |
| **27045912** | **`syncthing-linux-amd64-v2.1.3/syncthing`** ← 実行ファイル |

    期待（中心）: e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    実測        : e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    照合: 一致

    陰性対照: etc/freebsd-rc/syncthing の要約値 → 期待と一致しない（PASS）

版の自己申告も一致する。

    syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64) 2026-08-03 21:36:05 UTC

### 配置（完了判定 N）

    $ mkdir -p ~/bin          （~/bin は存在しなかった。書き込みは拒まれなかった）
    $ cp <実行ファイル> ~/bin/syncthing
    $ chmod 644 ~/bin/syncthing

    配置物の要約値 → 中心と一致
    permission=644 / [ -x ~/bin/syncthing ] → 偽
    → **実行権は落ちている。起動の引き金は作っていない**（禁止 2）

**`~/bin/syncthing` には一度も実行権を付けていない。**
下位命令の実行は scratchpad に展開した複製で行った。

### 識別子の発行（完了判定 O）

**既存の設定は無かった**（上書きしていない）。

    ~/.local/state/syncthing   absent   （本判定）
    ~/.config/syncthing        absent
    ~/.ssh                     EXISTS   （陽性対照。検査は働く）

**下位命令を推測せず、実在を確かめてから使った。**

    $ syncthing --help
    Commands: serve / cli / browser / decrypt / device-id / generate / paths /
              upgrade / version / debug / install-completions
    → `generate` と `device-id` はいずれも実在する（`env-facts.md` の記述と一致）

既定の場所も実装から読んだ（推測していない）。

    $ syncthing paths
    Configuration file: /home/ubuntu/.local/state/syncthing/config.xml
    Device private key & certificate: key.pem / cert.pem
    → `env-facts.md` の「設定は `~/.local/state/syncthing/`（既定の場所）」と一致

    $ syncthing generate
    INF Generating key and certificate (cn=syncthing)
    INF Calculated device ID (device=BRPEYOX-…)
    生成物: cert.pem(623, 664) / config.xml(6578, 600) / key.pem(119, 600)

**常駐していない**（`generate` は `then exit`。A4 末尾の Q で裏を取った）。

### 識別子の公開（完了判定 P）

    $ syncthing device-id > scripts/sync/device_ids/dlsta.txt

    識別子: BRPEYOX-MJ7HMGV-RR2XAUW-CVFVSED-DEMAG5M-EMQNVR6-77XWXPL-ZS26PAI

**秘匿ではない。** 形式は他台と揃っている。

| ファイル | bytes | 行数 | 文字数 |
|---|---|---|---|
| `philip.txt` | 64 | 1 | 63 |
| `lecun.txt` | 64 | 1 | 63 |
| **`dlsta.txt`** | **64** | **1** | **63** |

読み取った値と置いた値は一致する。

### 起動していないこと（完了判定 Q）

`ss` `netstat` `lsof` `ip` はいずれも不在のため、**`/proc/net/tcp` と `/proc/net/tcp6` から復号した**
（状態 `0A` = LISTEN、`:` 区切りの後半を 16 進から変換）。

🔴 **最初の復号器は壊れていた。** `strtonum` を使ったが、本ホストの awk は mawk であり
この関数を持たない（`awk: function strtonum never defined`）。**全件 0 を返していた。**
陰性対照（65535 → 0）は合格に見えたが、**「常に 0 を返す壊れ方」と区別できていなかった**
（`issuer_cautions` #3 そのもの）。シェル側で `$((16#…))` に変換する形へ組み直した。

組み直した復号器が返した待ち受けの一覧: **22, 33059, 34303, 45053, 56304（計 5 件）**

**対照を三方向で取った。**

| 対照 | 対象 | 結果 | 意味 |
|---|---|---|---|
| 陽性（既存） | port 22 | 一致 1 件 | 実在する待ち受けを捕まえる |
| 陰性 | port 65535 | 一致 0 件 | 偽陽性なし |
| **陽性（22000 番そのもの）** | port 22000 に一時的な待ち受けを立てる | **立てる前 0 → 立てている間 1 → 畳んだ後 0** | **本判定と同じ番号で検査が働くことを実証** |

    本判定: port 22000 一致件数 = 0   → 待ち受けていない
            port 8384  一致件数 = 0   → 待ち受けていない

プロセス側も `/proc/PID/exe` で絞って数えた（**部分一致で命令行を拾わない**。`issuer_cautions` #6）。

    自分の PID を除外。直下の子 1 件も除外対象として確認
    syncthing 一致件数 = 0          （本判定）
    m2-sync   一致件数 = 0
    keeper    一致件数 = 0
    zsh       一致件数 = 4          （陽性対照。検査は働く）
    zzz_no_such_token 一致件数 = 0  （陰性対照。自分の命令行を拾っていない）

→ **同期処理は起動していない。**

---

## A5. 三つの規約の適用判定（Task 5 / 完了判定 T）

`context/conventions.md`（`conventions_rev` = `c801e17`）の該当節を読んで判定した。

| 規約 | 節の定める対象 | 本契約への適用 | 根拠 |
|---|---|---|---|
| `proposal_gate` | 「禁止語（**提案と契約の本文**。完全一致で検査する）」（219 行目） | **適用される** | 本契約も「契約の本文」である。送出物へ検査を当てた（A6） |
| `folds` | 動画単位の 5-fold の割り当て。「選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う」 | **適用されない** | 本契約は学習も評価も行わない。折りを選ぶ場面も val/test に触れる場面も無い |
| `symmetry` | 「**対象: exp 契約のすべて**」（315 行目） | **適用されない** | 本契約は `kind: impl`。L3 の P13 も `SKIP kind=impl のため対象外（exp のみ）` を返した |

**SPEC の見込み（「学習も評価も行わない契約であるため、適用されない見込みである」）は
`folds` と `symmetry` については正しく、`proposal_gate` については当てはまらない。**
`proposal_gate` は SPEC 自身が「契約の本文にも適用される」と述べており、そちらが正しい。

## A6. `conventions_rev` の実測

SPEC は「`conventions_rev` は実行者が実測して置換する」と指示する。**実測した結果、置換は不要であった。**

    $ git --no-pager log -1 --format='%h' -- context/conventions.md
    c801e17c                                    ← 実測
    $ grep conventions_rev tasks/…/spec.yaml
    conventions_rev: "c801e17"                  ← 記載

短縮形 `c801e17` は実測値 `c801e17c` の接頭辞であり一致する。**値を書き換えていない。**

## A7. L3 プリフライト

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-09-20-dlsta-join-foundation
    exit_code=0
    RESULT: 5 PASS / 1 WARN / 7 SKIP / 0 FAIL

**SKIP された 7 件**（「合格」ではなく「実行されなかった」）。

| 項目 | 理由 |
|---|---|
| P2 `cuda_ext_loaded` | `plan.env.preflight` に記載なし |
| P3 `deterministic_flags` | 同上 |
| P4 `prereg_committed` | `kind=impl` のため対象外（exp のみ） |
| P5 `frozen_source_hash` | 同上 |
| P11 `gpu_free` | `plan.env.preflight` に記載なし |
| P12 `refs_resolved` | 解決前提の参照は無い |
| P13 `symmetry_table_complete` | `kind=impl` のため対象外（exp のみ） |

**WARN 1 件**: `P9 spec_lint` の `host_mismatch@SPEC.md:5`。

    tools/check_spec.py:321  actual = socket.gethostname()
    tools/check_spec.py:328  if declared.casefold() != actual.casefold():

本ホストの `socket.gethostname()` は `4f3861ae8d3b`（容器の識別子）であり、
宣言値 `dlsta` と一致しない。**規則は論理名（`SERVERNAME`）を見ていない。**
これは**既知の検査器の限界**であり、起票者の誤りではない。
`tasks/inbox.md` の 121 / 190 / 302 / 342 行、`context/auto/followups.md` の
49 / 139 / 362 / 496 行に同じ原因が繰り返し記録されている。
**SPEC 自身が「`hostname` は容器の識別子を返す。論理名の解決に使わない」と予告していた事象である。**

`P6 decisions_answered` は PASS（`decisions_required` は空）。

## A8. 試験

**「変更前」は測れなかった。** 開始時に `.venv` が存在しなかったためである。
そこで **HEAD（`29a6116f`）の worktree を切って同じ試験を走らせ、変更前を実測した**
（分岐は作らず `--detach`。測定後に `git worktree remove` で撤去。分岐数は 2 のまま）。

    worktree 側の解決先: <worktree>/src/egosurgery/__init__.py   ← 本体ではなく HEAD を見ている

| | failed | passed | skipped |
|---|---|---|---|
| **変更前（HEAD `29a6116f`）** | **6** | **581** | 14 |
| **変更後（作業ツリー）** | **6** | **581** | 14 |

**失敗 6 件は変更の前後で同一であり、本契約の変更が生んだものではない。**

    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
    tests/test_fetch_task.py::test_rejects_unknown_file_name
    tests/test_research_logger.py::test_log_run_idempotent
    tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
    tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
    tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block

変更範囲は `src/` `tools/` `tests/` を一切含まない（`git status --porcelain -- src tools tests` → 0 件）。

`test_research_logger` の 4 件は記録系の退役（`log_experiment_to_notion` が呼ばれず
`call_count == 0`）に由来し、`test_fetch_task` の 1 件は例外文言と正規表現の食い違い
（`"経路として受け取れない名前です"` 対 `"受け取れないファイル"`）である。
**いずれも既存の失敗であり、本契約では直さない**（禁止 11・範囲外）。

---

## A9. 送出前の検査（Task 5 Step 3 / 完了判定 U・V・W）

### 禁止領域（道具を使う。契約ごとに検査の命令を書かない）

    $ source .venv/bin/activate && make forbidden-check
    exit_code=0
    {"base": "origin/phase0", "changed": 13, "checked": 9, "status": "pass", "violations": [],
     "excluded": 4, "excluded_paths": ["context/auto/followups.md", "context/auto/results_recent.md",
     "context/auto/tasks_summary.csv", "tasks/inbox.md"], ...}

生成物 4 件は道具が生成器の実装から除外する。**`runindex/` は無変更**（`git status -- runindex/` → 0 件）。
`experiments/` `transfer/` `data/` も無変更（禁止 10）。

### 禁止語（完了判定 U）

送出物 6 件すべて `exit 0` / `status: pass` / 禁止語 0 件。

**陽性対照**: 禁止語 3 語を含む囮へ同じ検査を当てると `exit 1` / `status: fail` / 禁止語 **3 件**
（3 語をいずれも行番号つきで指した。**語そのものはここに引かない。引けばこの証跡が落ちる**）。囮は scratchpad に置き版管理へ入れていない。

🔴 **`audit.md` に該当が 1 件出た**（規約の一覧の末尾の語を A2.4 で使っていた）。
**検査を無効にせず本文を直した。**

🔴 さらに、**その該当を `RESULT.md` で説明した文が同じ語を引用したため、今度は `RESULT.md` が落ちた。**
検査は完全一致であり、引用の除外は `proposal_gate` の引用規約に無い。
**語を書かず位置で指す形へ直した。** 申し送りに残した。

### 秘匿（完了判定 V）

**自作の検査を当てた。形だけを見て、検査自身は長さと件数しか出力しない**（禁止 7・`issuer_cautions` #8）。
対象は送出される 13 件（追跡の変更＋未追跡）。

| 検査 | 送出物での出現 | 陽性対照 |
|---|---|---|
| 中心宛の秘密鍵の本体（標識行を除いた連結） | **0** | 鍵ファイル自身 → **1** |
| `WANDB_API_KEY`（長さ 86） | **0** | 同じ照合器へ埋め込んだ入力 → **1** |
| `WANDB_PROJECT`（長さ 20） | **0** | → **1** |
| `WANDB_ENTITY`（長さ 10） | **0** | → **1** |
| `DATA_ROOT`（長さ 13） | **0** | → **1** |
| `NOTION_API_KEY`（長さ 50） | **0** | → **1** |
| 合言葉（長さ 15） | **0** | → **1** |
| 秘密鍵の塊（開始と終了の標識に挟まれた本体） | **0** | 鍵ファイル自身 → **1** |

環境に在った資格情報は 5 / 5 で、**照合できなかった項目は無い**（SKIP なし）。

🔴 **標識の語だけを数える形は偽陽性を出した。** 最初は開始標識の語の出現数を 0 と求めたが、
**本証跡が検査の内容そのものを説明しているため、説明文に語が現れて 3 件・1 件と数えられた。**
出所を位置で確かめると、いずれも本ファイルの 599 行目と 602 行目の説明文であり、鍵材ではなかった。

**語の出現数ではなく、開始標識と終了標識に挟まれた塊を数える形へ直した。**

    送出物での塊 = 0        （本判定）
    鍵ファイル自身 = 1      （陽性対照。検査は働く）

これは禁止語の検査で起きたことと同じ型であり、**検査を説明する文書が検査に掛かる**という
共通の性質による。**秘匿の判定は塊の側を正とする。**

### 変更の範囲（完了判定 W）

**9 件すべてが契約の範囲内。範囲外 0 件。**

    tasks/T-2026-09-20-dlsta-join-foundation/   （RESULT.md / audit.md / result.yaml / SPEC.md / spec.yaml）
    tasks/inbox.d/T-2026-09-20-dlsta-join-foundation.md
    scripts/sync/hub_keys/dlsta.pub
    scripts/sync/device_ids/dlsta.txt
    context/env-facts.md
    context/auto/（3 件）・tasks/inbox.md   ← 生成物

**陽性対照**: 範囲外の例 `src/foo.py` を判定器へ与えると範囲外として検出された。

### 禁止 5 の読み

**字面が一つに定まらなかったため、利用者に諮った**（`issuer_cautions` #14）。

| 読み | 根拠 |
|---|---|
| 投影と集約は**対象外** | 手順書が `make taskindex` / `make inbox` を要求し、`make taskindex-check` は再生成なしでは非零になる。`make forbidden-check` は投影と集約を検査から明示的に除外する |
| 文字どおり**対象** | SPEC の禁止 5 と Task 5 Step 3 が「生成物を再生成しない」と明記 |

**利用者の判断により前者を採った。** 禁止 5 が指すのは `runindex/` 等の指数であるという読みである。
生成物の差分は**件数の更新と「新しい順に 5 件」の入れ替わりのみ**で、失われた内容は無い
（`results_recent.md` は「ここに出ない 93 件は各契約の `result.yaml` にある。失われてはいない」と自ら述べる）。

### 送出

    commit  e4f80541
    push    exit 0（新しい分岐として origin へ）
    PR      #187

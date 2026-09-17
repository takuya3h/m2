# audit — T-2026-09-17-efros-rejoin-foundation 手続きの証跡

実行ホスト `efros` / repo `~/slocal2/m2` / 実行日 2026-09-17（JST）。
`RESULT.md` はここを行番号で指す。**本ファイルは手順と出力の記録であり、判断は `RESULT.md` に書く。**

## 0. 前提の確認

| 項目 | 実測 |
|---|---|
| 分岐 | `feat/efros-rejoin-foundation`（本契約の起票時に存在） |
| `git status --porcelain` の件数 | `1`（`?? tasks/T-2026-09-17-efros-rejoin-foundation/`） |
| `stash` | `stash@{0}: On chore/regen-index-after-tooling: efros-pre-rejoin-2026`（**触っていない**） |
| `~/bin/` | 存在しない |
| `~/bin/keeper.sh` `~/bin/m2-sync.sh` `~/bin/syncthing` | いずれも存在しない |
| `~/claude-sync/` | 存在しない |
| `.sync-pause` | 存在しない（**置いていない**） |
| `syncthing` 実体一致プロセス（`/proc/PID/exe`） | `0` 件 |

**常駐処理は動いていない。抑止（`.sync-pause`）は置いていない。**
`keeper.sh` の起動条件は `[ -x ~/bin/syncthing ]`（`scripts/sync/keeper.sh:41`）であり、
`~/bin/keeper.sh` 自体が無い以上、周期実行の主体が存在しない。

`make task-start` は使っていない。契約は `tasks/` に既に置かれており、分岐も存在したため。
取り込み時点の仮想環境は壊れており（後述）、`make task-validate` は
`make: .venv/bin/python: No such file or directory` / `Error 127` で失敗した。
SPEC の指示（「その場合は Task 1 を先に済ませてから取り込む」）に従い Task 1 を先行させた。

## 1. Task 1 — 実行環境の作り直し

### Step 1 既存の実測と退避

退避前（`du -sb` / `find`。**丸めた表示を使わない**）。

| 項目 | 実測 |
|---|---|
| 大きさ | `11279712329` バイト |
| ファイル数 | `63549` |
| ディレクトリ数 | `7053` |
| 全要素数 | `70602` |
| Python | `3.12`（`pyvenv.cfg`: `version_info = 3.12`、`uv = 0.11.26`） |
| torch | `2.13.0`（`torch-2.13.0.dist-info`） |
| torchvision | `0.28.0` |
| numpy | `1.26.4` |
| transformers | `4.44.2` |
| jsonschema | `4.26.0` |
| mmcv / mmdet / mmengine | **いずれも無し** |
| `.venv/bin/` の実行ファイル数 | `45`。**`python` は 1 件も無い** |

**壊れ方**: `pyvenv.cfg` の `home` が
`/home/ubuntu/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin` を指すが、
**`/home/ubuntu/.local/share/uv/python/` 自体が存在しなかった**。
`env-facts.md:24` は「消えた pyenv を指す dangling symlink。貼り直しで足りる」と書くが、
本ホストは symlink すら無く、貼り直しでは足りない。

退避先の選定。`/home/ubuntu` は overlay、`/home/ubuntu/slocal2` は `/dev/sdd1` で
**別のファイルシステムである**。`~/` 配下へ移すと 11 GB の実コピーが走り、
中断すれば失う。**同一ファイルシステム内の rename にするため
`/home/ubuntu/slocal2/venv-archive/` を選んだ**（repo `~/slocal2/m2` の外）。

    mv .venv /home/ubuntu/slocal2/venv-archive/venv-py312-2026-09-17

退避後の実測。**削除していない。**

| 項目 | 退避前 | 退避後 | 一致 |
|---|---|---|---|
| バイト | `11279712329` | `11279712329` | ○ |
| ファイル数 | `63549` | `63549` | ○ |
| ディレクトリ数 | `7053` | `7053` | ○ |
| 全要素数 | `70602` | `70602` | ○ |

repo 内 `.venv` は移動後に存在しないことを確認した。

### Step 2 作り直し

`README.md` の「別マシンでの環境再現」が指す `scripts/setup_env.sh` を使った。
**`--clear` は README・`setup_env.sh`・`docs/reproduce_on_new_machine.md` のいずれにも
出現しない**（`grep -rn -- "--clear"` が 0 件）。禁止 1 に抵触しない。

`setup_env.sh:43` は `nvcc != 11.8` なら `exit 1` する。**本ホストの nvcc は 12.9**
（`/usr/local/cuda` → `cuda-12.9`。11.8 は導入されていない）。
同スクリプトの mamba 導入（`:84-91`）は **GitHub の prebuilt wheel を curl で取得して
`--no-deps` で入れる経路**であり、ソースビルドを行わない。`:77-80` が自らそう書いている。
したがって当該検査は**このスクリプトが実際に通る経路に対して過剰**である。
`SKIP_CUDA_CHECK=1` で続行した（→ `RESULT.md` の逸脱）。

    SKIP_CUDA_CHECK=1 bash scripts/setup_env.sh

`uv` は `~/.local/bin/uv`（`0.12.10`）。`cpython-3.11.16` を新規取得した
（`/home/ubuntu/.local/share/uv/python/` は**この時点で初めて生成された**）。

### Step 3 動作の確認

`.venv/bin/python` を明示して測定した。

| 項目 | 実測 | 他台 | 一致 |
|---|---|---|---|
| Python | `3.11.16` | `3.11.16` | ○ |
| torch | `2.1.2+cu118` | `2.1.2+cu118` | ○ |
| torchvision | `0.16.2+cu118` | `0.16.2` | ○ |
| `torch.cuda.is_available()` | `True` | — | — |
| `torch.version.cuda` | `11.8` | — | — |
| `torch.cuda.device_count()` | `2` | — | — |
| device 0 | `NVIDIA RTX A6000` | — | — |
| GPU 行列積（256×256） | 実行できた | — | — |
| driver | `595.84` | `535`（`README.md`） | × |
| system nvcc | `12.9` | `11.8` | × |
| `egosurgery` の import | OK | — | — |
| 新しい `.venv` の大きさ | `6380737283` バイト / `29983` ファイル | `env-facts.md:23` の「6.3 GB」 | ○ |

**`mmcv` は `libGL.so.1` が無く落ちた。** `setup_env.sh` は検証段（`:103-114`）で失敗し、
終了コード `1` を返した（背景実行の包みが `0` を返したのは包みの `echo` が最後だからであり、
**スクリプトの終了コードではない**）。

    ImportError: libGL.so.1: cannot open shared object file: No such file or directory

`ldconfig -p | grep -i libGL` は `libGLX_nvidia.so.0` などを返すが
**`libGL.so.1` は 0 件**。`dpkg -l | grep -c libgl1` は `0`。
`/var/lib/apt/lists/` の Packages は `0` 件（`apt-get update` が要る）。
`sudo -n true` は `sudo: a password is required` を返した。

`env-facts.md:29` と SPEC の指示（回避せず利用者へ提示して許諾を得る）に従い、
**利用者へ提示した。**

### Step 4 検証に要るもの

`requirements.lock.txt` に `jsonschema` は **0 件**（`grep -in` が空）。
素の `pip` を使わず、仮想環境の実体を明示して導入した。

    ~/.local/bin/uv pip install --python .venv/bin/python jsonschema

`jsonschema 4.26.0`（退避した環境と同じ版）。`sys.executable` が
`/home/ubuntu/slocal2/m2/.venv/bin/python` であることを同じ命令で確認した。

    source .venv/bin/activate && make task-validate TASK=T-2026-09-17-efros-rejoin-foundation
    → OK   T-2026-09-17-efros-rejoin-foundation
    → 1 task(s), 0 failed   /   VALIDATE_EXIT=0

`conventions_rev` は `git --no-pager log -1 --format=%h -- context/conventions.md` で
`e7a51005` と実測した。`spec.yaml` の既値 `e7a5100` はその前置であり、検証も通ったため
**置換は不要だった**（SPEC は「実測して置換する」と書くが、実測値が既値と整合した）。

## 2. Task 2 — 論理名

### Step 1 設定前

    SERVERNAME             = [未設定]
    EGOSURGERY_SERVER_NAME = [未設定]
    hostname               = [efros]
    hostname -f            = efros

`env -i` で継承を断った形態別の測定（`scripts/sync/setup_host_servername.sh --verify`）。

| 形態 | 設定前 |
|---|---|
| `zsh -c`（非対話） | 未設定 |
| `zsh -ic`（対話） | 未設定 |
| `bash -lc`（ログイン） | 未設定 |
| `bash -ic`（対話） | 未設定 |
| `bash -c`（非対話） | 未設定 |

`~/.bash_profile` と `~/.bash_login` は存在しない。よって bash のログインシェルは
`~/.profile` を読む（存在すれば `~/.bash_profile` が優先されるため、これは確認が要った）。

### Step 2 追記

`scripts/sync/setup_host_servername.sh` を読んでから使った（`:39-45` で対象は
`~/.zshenv` `~/.profile` `~/.bashrc` の 3 件。追記のみ。既存行を書き換えない）。
**SPEC は 2 件を指定するが、スクリプトは 3 件へ書く。上位集合であり、差分を記録する。**

`--dry-run` で 3 件とも「追記する」ことを確認してから適用した。

追記内容（3 ファイルとも同一の 3 行）。

    # >>> egosurgery SERVERNAME >>>
    export SERVERNAME=efros
    # <<< egosurgery SERVERNAME <<<

| ファイル | 追記行 |
|---|---|
| `~/.zshenv` | 8-10 |
| `~/.profile` | 32-34 |
| `~/.bashrc` | 123-125 |

戻し方は当該 3 行の削除（`setup_host_servername.sh:32-33`）。

### Step 3 設定後（両方向の対照）

| 形態 | 設定前 | 設定後 | 判定 |
|---|---|---|---|
| `zsh -c`（非対話） | 未設定 | `efros` | OK |
| `zsh -ic`（対話） | 未設定 | `efros` | OK |
| `zsh -lc`（ログイン） | 未設定 | `efros` | OK |
| `bash -lc`（ログイン） | 未設定 | `efros` | OK |
| `bash -ic`（対話） | 未設定 | `efros` | OK |
| `bash -c`（非対話） | 未設定 | **未設定** | 既知の限界 |

**対照は両方向で取れている。** 設定前は全形態が「未設定」を返しており、
「常に `efros` を返す壊れ方」ではないことが示されている。
`bash -c`（非対話・非ログイン）は利用者ファイルでは覆えない既知の限界であり、
スクリプト自身が毎回表示する（`:185-187`）。適用後の自己検査は終了コード `0`。

## 3. 本ホストで実測した道具の有無

`env-facts.md:42` の記述を本ホストで測り直した（五台の実測を持ち込まない）。

| 道具 | efros |
|---|---|
| `ss` `netstat` `lsof` `ip` | **無し**（記述と一致） |
| `/proc/net/tcp` | 可読 |
| `curl` `sha256sum` `tar` | 有り |

`~/.ssh/` の一覧は**拒まれなかった**（`env-facts.md:46` は「拒まれることがある」）。

## 4. Task 1 Step 3 の続き — `libGL.so.1` の解消

利用者へ提示し、許諾を得て利用者自身が実行した（私は `sudo` を実行していない）。

    sudo apt-get update && sudo apt-get install -y libgl1

| 検査 | 導入前 | 導入後 |
|---|---|---|
| `dpkg -l \| grep -cE '^ii +libgl1:'` | `0` | `1`（`1.7.0-1build1`） |
| `ldconfig -p \| grep -c 'libGL\.so\.1'` | `0` | `1`（`/lib/x86_64-linux-gnu/libGL.so.1`） |
| `import mmcv` | `ImportError: libGL.so.1` | `mmcv 2.1.0` |

**両方向の対照が取れている。** 導入前は 3 検査とも欠損側を返し、導入後に 3 検査とも通った。

### 依存の総点検（`setup_env.sh:103-114` と同じ検証を再実行）

    python        3.11.16
    torch         2.1.2+cu118 / CUDA 11.8 / GPU NVIDIA RTX A6000
    torchvision   0.16.2+cu118
    mmcv 2.1.0 / mmdet 3.3.0 / mmengine 0.10.7
    mamba-ssm 2.2.2 / causal-conv1d 1.4.0
    numpy 1.26.4 / transformers 4.44.2
    egosurgery import OK
    ALL_IMPORT_OK   /   VERIFY_EXIT=0

`CLAUDE.md` の「環境（検証済み構成）」の全項目と一致した。

## 5. L3 プリフライト

    source .venv/bin/activate && make task-preflight TASK=T-2026-09-17-efros-rejoin-foundation

    P1  venv_active           PASS  VIRTUAL_ENV=sys.prefix=/home/ubuntu/slocal2/m2/.venv
    P2  cuda_ext_loaded       SKIP  plan.env.preflight に記載なし
    P3  deterministic_flags   SKIP  plan.env.preflight に記載なし
    P4  prereg_committed      SKIP  kind=impl のため対象外
    P5  frozen_source_hash    SKIP  kind=impl のため対象外
    P6  decisions_answered    PASS  decisions_required は空
    P7  destination_writable  PASS
    P8  contract_valid        PASS  validate_task.py --level l2 が exit 0
    P9  spec_lint             WARN  separated_source@SPEC.md:47
    P10 preflight_names_known PASS
    P11 gpu_free              SKIP  plan.env.preflight に記載なし
    P12 refs_resolved         SKIP  解決前提の参照は無い

    RESULT: 5 PASS / 1 WARN / 6 SKIP / 0 FAIL   /   PREFLIGHT_EXIT=0

**SKIP は「合格」ではなく「実行されなかった」である。** 上の 6 件は実行されていない。

P9 の該当は `SPEC.md:47-48`。`source .venv/bin/activate` が単独の命令で終わり、
次の `make task-start` がそれを前提にしている。**私は実際にこの誤りを踏まないよう、
`make` を含む命令すべてに `source .venv/bin/activate &&` を同じ命令内へ入れて実行した。**

**実行順の逸脱**: 手順書は「L3 プリフライト（実行直前）」を実行の前に置くが、
取り込み時点の `.venv` が壊れており `make` 自体が動かなかった。
**Task 1（環境の作り直し）を先に済ませてからプリフライトを回した。**
SPEC の「その場合は Task 1 を先に済ませてから取り込む」に沿う。

## 6. Task 3 — 中心宛の鍵

### Step 1 既存の確認

`~/.ssh/` の一覧は拒まれなかった。`id_ed25519_efrostophilip` は **0 件**（作る）。
`id_ed25519_github`（`600`）と `.pub`（`644`）が在るが**別用途。触っていない**。
`authorized_keys` `config` `config.d/` `known_hosts` にも触れていない。

### Step 2 生成

    ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_efrostophilip -N "" -C "efrostophilip" -q

合言葉は付けていない（`-N ""`）。注記の `-C` は他台の慣例に合わせた
（`hub_keys/*.pub` の注記欄は `andrewtophilip` `bengiotophilip` `ilyatophilip` `lecuntophilip`）。

**指紋**（公開鍵の指紋。秘匿ではない）。

    256 SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0 efrostophilip (ED25519)

**秘密鍵の中身は読んでいない。表示していない。記録していない。**

### Step 3 権限

| 対象 | 実測 | 期待 |
|---|---|---|
| `~/.ssh` | `700 ubuntu:ubuntu` | 所有者のみ | 
| `~/.ssh/id_ed25519_efrostophilip` | `600 ubuntu:ubuntu` | 所有者のみ読める |
| `~/.ssh/id_ed25519_efrostophilip.pub` | `644 ubuntu:ubuntu` | 公開鍵 |

### Step 4 版管理へ配置

    cp ~/.ssh/id_ed25519_efrostophilip.pub scripts/sync/hub_keys/efros.pub

指紋の一致（`ssh-keygen -lf` の出力を `diff` で照合）: **一致**。

**三つの検査と陽性対照。検査は値を出力しない。長さ・有無・件数だけを返す。**

| 対象 | 先頭 `ssh-` | 秘密鍵の書き出し | 行数 | 大きさ |
|---|---|---|---|---|
| `scripts/sync/hub_keys/efros.pub` | `1` | **`0`** | **`1`** | `95` |
| 囮（秘密鍵の書き出しを模したもの） | `0` | **`1`** | `4` | `200` |

**陽性対照は三検査すべてで逆向きに落ちた。** 検査が「常に合格を返す壊れ方」ではない。
囮は scratchpad に置き、**版管理へ入れていない**（`git status` の `decoy` 該当 `0` 件）。
囮の中身は `DECOY` の繰り返しであり、実在の鍵素材を含まない。

## 7. Task 4 — 同期処理と識別子

### Step 1 取得と照合

    curl -fSL --retry 3 -o st.tar.gz \
      https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz

書庫 `11821325` バイト。**名前が `syncthing` の要素は 3 件**（SPEC の記述と一致）。

| 経路 | 大きさ |
|---|---|
| `syncthing-linux-amd64-v2.1.3/etc/freebsd-rc/syncthing` | `1709` |
| `syncthing-linux-amd64-v2.1.3/etc/firewall-ufw/syncthing` | `175` |
| **`syncthing-linux-amd64-v2.1.3/syncthing`** | **`27045912`** |

大きさで実行ファイルを特定した。

    実測: e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    中心: e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    一致: YES

**否定対照**: 同じ照合を囮ファイルに当てると不一致になった。照合は働いている。

    syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64) 2026-08-03 21:36:05 UTC

### Step 2 配置

    mkdir -p ~/bin && cp <展開物> ~/bin/syncthing && chmod 600 ~/bin/syncthing

`~/bin/` は存在しなかったので作った。**書き込みは拒まれなかった**
（`env-facts.md:47` は「拒まれることがある」）。`~/bin/` の中身は `syncthing` 1 件のみ。

| 検査 | 実測 |
|---|---|
| 大きさ | `27045912` |
| 権限 | `600` |
| 要約値と中心 | 一致 |
| `[ -x ~/bin/syncthing ]`（`keeper.sh:41` の引き金） | **FALSE** |
| 対照: 実行権を立てた囮への同じ判定 | **TRUE** |

**両方向の対照**。引き金の判定は TRUE を返しうる状態で FALSE を返している。

### Step 3 識別子の発行

既存設定 `~/.local/state/syncthing/` は**存在しなかった**ので生成した。**上書きしていない。**

    <BIN> generate --home ~/.local/state/syncthing
    INF Generating key and certificate (cn=syncthing)
    INF Calculated device ID (device=LW4CO4U-XINDYL5-WDTK4LN-NANREIJ-LHSPA6F-6VPGZ3R-2ADLKLP-GG6AUQW)
    GEN_EXIT=0

生成物: `config.xml`(`600`) `cert.pem`(`664`) `key.pem`(`600`)。
`paths` が返す既定の経路と同じ場所であることを確認した（`env-facts.md:61` と一致）。

**`generate` は常駐しない**ことを、直後のプロセス計数（後述）で確かめた。

**実行に使った実体は scratchpad の展開物である**（`~/bin/syncthing` は実行権を落としてあるため）。
両者の要約値は同一であり、`~/bin/syncthing` の引き金は立てていない。

### Step 4 識別子の読み取り（SPEC の記述と食い違う）

| 経路 | SPEC / `env-facts.md:62` の記述 | v2.1.3 での実測 |
|---|---|---|
| `serve --home ... --device-id` | 「取り方はこれ」 | **`syncthing: error: unknown flag --device-id` / exit `80` / stdout 0 行** |
| `device-id` 下位命令 | 「**無い**」 | **在る。`--help` の Commands に載る。値を返す** |

**記述が逆である。** `serve --help` に `device-id` の文字列は **0 件**。
**実測を正として `device-id --home ...` を使った。**
値は `generate` が表示した識別子と一致した。

    scripts/sync/device_ids/efros.txt
    LW4CO4U-XINDYL5-WDTK4LN-NANREIJ-LHSPA6F-6VPGZ3R-2ADLKLP-GG6AUQW

| 項目 | efros | 他台 5 件 |
|---|---|---|
| 行数 | `1` | すべて `1` |
| 大きさ | `64` | すべて `64` |
| 書式 `^[A-Z0-9]{7}(-[A-Z0-9]{7}){7}$` | 一致 | すべて一致 |

**識別子は秘匿ではない**（他台も同じ形で版管理下にある）。

### Step 5 起動していないことの確認

`ss` `netstat` `lsof` `ip` は本ホストに無い。`/proc/net/tcp` と `/proc/net/tcp6` を
LISTEN(`0A`) で絞り、ポートの 16 進を**末尾一致**で照合した（部分一致にしない）。

| 測定 | 22000 | 8384 |
|---|---|---|
| 1. 対照用リスナ無し | `0` | `0` |
| 2. **対照用リスナ有り**（素の socket。syncthing ではない） | **`1`** | **`1`** |
| 3. 対照用リスナ撤去後 | `0` | `0` |

**両方向の対照。** 検出器は同じポートで `1` を返せる状態で `0` を返している。

プロセスは `/proc/PID/exe` の実体経路で絞った（**命令行を見ない**）。

| 対象 | 件数 |
|---|---|
| `syncthing`（`generate` と `device-id` の実行後） | **`0`** |
| 対照 `/bin/sleep`（実行中） | `2` |
| 否定対照 `zzz_no_such_exe` | `0` |

**両方向の対照。** 検出器は `>=1` を返せる状態で syncthing に対して `0` を返している。

その他: `~/bin/keeper.sh` `~/bin/m2-sync.sh` `~/.syncthing.log` は**いずれも存在しない**。
**同期処理は一度も起動していない。**

### 後続の契約への申し送り（本契約の範囲外。変更していない）

`env-facts.md:63-64` は「告知の既定値は有効。公開の探索網と公開中継を起動前に無効にする」
「自動更新は既定 12 時間。起動と同時に走る。実行権を戻す前に 0 にする」と書く。
**本契約は起動しないため設定を変更していない。** 起動を伴う後続の契約で当てること。

## 8. Task 5 — 訂正・検査・試験

### `context/env-facts.md` の訂正（7 行。`conventions.md` には触れていない）

| 行 | 訂正前 | 訂正後の要点 |
|---|---|---|
| 12 | efros / he は `50072` が `REFUSED`（未参加） | **efros は復旧した**（基盤のみ。登録は後続）。he は未確認 |
| 18 | **lecun / efros** — `~/slocal/m2` | **lecun のみ** |
| 19 | philip / bengio / andrew / ilya / その他 | **efros** を `~/slocal2/m2` 側へ加えた |
| 24 | 壊れ方は dangling symlink。貼り直しで足りる | **ホストによる。efros は `.venv/bin/python` が 0 件で作り直しが要った** |
| 25 | uv の実体は `…cpython-3.11.16-…` | **場所はホストによる。efros は `…cpython-3.11-…`（patch 番号なし）** |
| 29 | 5 台で完了 | **6 台で完了**（efros は 2026-09-17） |
| 62 | `serve --device-id`。`device-id` 下位命令は無い | **`device-id --home ...`。`serve --device-id` は `unknown flag` / exit 80** |

行 11（参加する 5 台）は**変えていない**。efros はまだ中心へ登録されておらず、
参加は後続の契約であるため。行 23・28・42・46・47・60・61 は本ホストの実測と食い違わなかった。

### `proposal_gate` の禁止語検査（適用される部分）

    .venv/bin/python tools/check_proposal.py --only forbidden <対象>

| 対象 | 検出件数 |
|---|---|
| `SPEC.md` | `0`（禁止語 0 / 見出し欠落 0 / 数字欠落 0） |
| `audit.md` | `0` |
| `RESULT.md` | 後掲 |
| **陽性対照**（禁止語 4 語を含む囮） | **`4`**（「画期的」「確実に効く」「明らかに」「大幅」） |

**陽性対照が 4 件を返した。検査は働いている。** 囮は scratchpad に置き版管理へ入れていない。
なお本検査は該当があっても終了コードを変えない。**件数で判定した**（終了コードを件数と呼ばない）。

### 試験

    .venv/bin/python -m pytest tests/ -q
    6 failed, 550 passed, 24 warnings in 33.64s

**開始前は測れなかった。** 取り込み時点の `.venv` には Python の実体が無く、
`pytest` の実行系そのものが起動しない（落ちた試験は 0 件だが、通った試験も 0 件である）。

落ちた 6 件は**本契約の変更と無関係な既存の不一致**である。私は
`src/**` `tests/**` を一切変更していない（`git status` で確認）。内訳の標本 2 件。

- `tests/test_fetch_task.py::test_rejects_unknown_file_name`
  期待正規表現「受け取れないファイル」に対し実際の文言は「経路として受け取れない名前です」。**文言の不一致。**
- `tests/test_research_logger.py::test_log_run_idempotent`
  `log_run` が `None` を返す。`CLAUDE.md` の「自動投稿は明示的に止めてあり、
  呼ばれても投稿せず退役の旨を返す」と整合する。**試験が退役前の戻り値を期待している。**

**他台で同じ 6 件が落ちるかは測っていない（UNKNOWN）。**

### 変更範囲

    M  context/env-facts.md
    ?? scripts/sync/device_ids/efros.txt
    ?? scripts/sync/hub_keys/efros.pub
    ?? tasks/T-2026-09-17-efros-rejoin-foundation/

範囲外の変更は **0 件**（上の 4 経路を除いた `git status` の行数）。
**生成物を再生成していない**（`make taskindex` `make inbox` は禁止 7 に従い実行していない）。
`experiments/**` `transfer/**` `data/**`、学習・評価コードには触れていない。
`stash@{0}` は戻していない。退避した `.venv` は削除していない。

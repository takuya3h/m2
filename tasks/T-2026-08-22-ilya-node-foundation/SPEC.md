# 基盤を作り、中心宛の鍵と識別子を公開する（ilya）

**task_id:** `T-2026-08-22-ilya-node-foundation`  **kind:** `impl`
**depends_on:** `T-2026-08-22-philip-hub-foundation`
**実行ホスト:** `ilya`  **repo:** `~/slocal2/m2`

## Goal

**保守作業で全サーバーが初期化された。** 常駐処理、同期処理、鍵、識別子がすべて失われた。
**復旧ではなく新規構築である。**

**中心は philip。** 前契約で philip の基盤が整い、識別子が版管理へ公開された。

| 事実 | 実測 |
|---|---|
| 中心の識別子 | `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE` |
| 中心の住所 | `192.168.196.150`。SSH は `50072` |
| 直接の接続 | **できない。** 外側から中まで届く口は SSH のものだけ |
| よって構成 | **中継が要る。星型。** 単純化の余地はない |
| 同期処理 | `v1.27.10`。実行ファイルの要約値 `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` |

**本契約は自ホストの基盤を作り、次の二つを版管理へ公開する。**

1. **中心宛の鍵の公開鍵** → `scripts/sync/hub_keys/ilya.pub`
2. **自ホストの識別子** → `scripts/sync/device_ids/ilya.txt`

**登録と起動は行わない。** 全台の値が揃ってから次の契約で行う。

### この契約が置かれた状況

**契約システムの一部が動かない。** 秘匿情報の合言葉が失われ、
`scripts/load_env.sh` が失敗する。

| 使えないもの | 代替 |
|---|---|
| `make task-start` | **手で分岐を切り、契約を配置する** |
| `make task-report` | **`RESULT.md` を commit して push する** |
| `source scripts/load_env.sh` | **`source .venv/bin/activate` だけを使う** |
| 送信前の秘匿検査 | **送信前に自分で検査する** |

## 0. 前提と禁止事項

**取り込みは手で行う。最初に版管理を最新にすること。**

    cd ~/slocal2/m2
    git --no-pager status --porcelain | grep -c ''
    git fetch origin
    git checkout -b feat/ilya-node-foundation origin/phase0
    git --no-pager log -1 --format='%h %s'
    mkdir -p tasks/T-2026-08-22-ilya-node-foundation

**`git log -1` で最新であることを必ず確かめる。**
**前契約で、古い状態のまま作業したために「道具が存在しない」と誤って報告された。**
実際には三件とも実在した。**判断の前に、いま見ているものが最新かを確かめること。**

**その後、配られた本文から `spec.yaml` と `SPEC.md` を上のディレクトリへ置く。**

**未追跡がある場合、それらは版管理外の成果物である。一切触らない。**
`git checkout -b` は未追跡を保持する。**件数が減っていないことを確かめてから進む。**

| # | 禁止 |
|---|---|
| 1 | **未追跡の成果物を削除・移動・commit する** |
| 2 | `experiments/**` `transfer/**` `data/**` を変更・削除する |
| 3 | **他ホストへ接続する。他ホストの状態を変更する** |
| 4 | **同期処理の設定で他ホストを登録する**（全台の値が揃ってから） |
| 5 | **中継を張る。目印を作る** |
| 6 | **常駐処理と同期処理を起動する** |
| 7 | **`uv venv --clear` を実行する**（後述。六ギガの成果物を破棄する） |
| 8 | 秘匿の値を出力・記録する。**秘密鍵の中身を出さない** |
| 9 | 装置を使う |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `runindex/**` `context/auto/**` を手で編集する |
| 12 | 学習・評価コードを変更する |

**禁止 7 が最も破壊的である。** 前契約の実測で、`.venv` が壊れているのは
**`bin/python` が消えた pyenv を指す壊れた繋がりだけ**であり、
**`--clear` は六・三ギガの中身を捨てる。** 貼り直しで足りる。

**禁止 6 の理由。** 全台の識別子が揃っていない段階で動かすと、
**定まらない状態で同期が走る。**

### 前契約で確定した事実（全台で同じはず）

**これらは philip での実測である。** 自ホストでも確かめること。

| # | 事実 |
|---|---|
| 1 | **`.venv/bin/python` が `~/.pyenv/versions/3.11.4/` を指す壊れた繋がり。** pyenv ごと消滅 |
| 2 | uv 管理の実体は `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` |
| 3 | **`~/.gitconfig` が失われている。** commit の前に `user.name` と `user.email` の設定が要る |
| 4 | **`remote.origin.pushurl` が SSH のまま。** 配備鍵が消えたので通らない |
| 5 | `make task-validate` は `jsonschema` を要する。環境の作り直し後は追加導入が要る |
| 6 | **`pgrep -af` は自分のコマンド行を拾う。** `pgrep -x` を使うか `/proc/*/cmdline` を読む |
| 7 | 同期処理の設定は `~/.local/state/syncthing/`。**`--home` で明示する。既定ではない** |
| 8 | 識別子の取り方は `serve --home ... --device-id`。**`device-id` という下位命令は無い** |
| 9 | 論理名は `~/.zshenv` と `~/.profile` の**両方**に置く |
| 10 | `libGL.so.1` が無く `mmcv` `mmdet` を読み込めない。**本契約の範囲外。記録だけする** |

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | **無い**ことと**読めない**ことを区別する |
| 2 | **判断の前に、いま見ているものが最新かを確かめる**（前契約の誤報の原因） |
| 3 | 先頭がドットのものを落とさない |
| 4 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 5 | **取得したものは要約値で照合する** |
| 6 | 対照は両方向で取る。期待値を実測前に一点へ固定しない |
| 7 | `成功 && echo OK || echo NG` は表示側の失敗も NG にする |
| 8 | 出力は要約せず `audit.md` へ貼る |

`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 基盤を整える

**Files:** Create: `tasks/T-2026-08-22-ilya-node-foundation/audit.md`

- [ ] **Step 1: 開始状態を記録する**

    ls -la ~/ 2>&1
    echo "home_entries=$(ls -a ~/ | grep -c -v '^\.\{1,2\}$')"
    ls -la ~/.ssh/ 2>&1
    ssh-keygen -lf ~/.ssh/authorized_keys 2>&1
    ls -la ~/bin/ 2>&1
    ls -la ~/.local/state/syncthing/ 2>&1
    cat ~/.zshenv 2>&1
    git --no-pager status --porcelain | grep -c ''

**未追跡の件数を控える。** 契約の終わりに同じ数であることを確かめる。

- [ ] **Step 2: 実行環境を直す**

**まず何が壊れているかを測る。**

    ls -la .venv/bin/python* 2>&1
    readlink -f .venv/bin/python 2>&1 || echo "解決できない"
    .venv/bin/python -V 2>&1 || echo "動かない"
    du -sh .venv 2>&1

**壊れているのが繋がりだけなら、貼り直しで足りる。**
**`uv venv --clear` を使ってはならない**（禁止 7）。

前契約では uv 管理の実体へ貼り直して回復した。**同じ経路が在るかを確かめる。**

    ls -la ~/.local/share/uv/python/ 2>&1

**貼り直したら、必ず動くことを確かめる。**

    .venv/bin/python -V
    source .venv/bin/activate && which python && python -V

- [ ] **Step 3: 検証に要るものを補う**

    source .venv/bin/activate && python -c "import jsonschema; print(jsonschema.__version__)" 2>&1 \
      || echo "jsonschema が無い"

**無ければ導入する。** 素の `pip` は別の環境へ入る事故が記録されている。
**`.venv` の中の `pip` を明示して使うこと。**

- [ ] **Step 4: 版管理の識別を設定する**

    git config user.name 2>&1 || echo "未設定"
    git config user.email 2>&1 || echo "未設定"

**未設定なら設定する。** 範囲は repo の中だけでよい。**設定内容を記録する。**

- [ ] **Step 5: 送出の経路を直す**

    git remote -v

**`push` 側が `git@` で始まるなら、配備鍵が要る形である。** 鍵は消えている。

    git remote set-url --push origin https://github.com/takuya3h/m2.git
    git remote -v

**両方が `https` になったことを確かめる。**

| # | 完了判定 |
|---|---|
| 1 | 開始状態を記録した（家の直下、鍵、未追跡の件数） |
| 2 | 実行環境が動く（版が表示でき、経路が `.venv` を指す） |
| 3 | **六ギガを破棄していない**（`du` の値を前後で記載） |
| 4 | 検証に要るものが揃った |
| 5 | 版管理の識別と送出の経路を直した |

---

## Task 2 (Phase A): 論理名を設定する

**Files:** Modify: `~/.zshenv`, `~/.profile`

- [ ] **Step 1: 現在の状態を確かめる**

    grep -n "SERVERNAME" ~/.zshenv ~/.profile 2>&1 || echo "該当なし"
    echo "SERVERNAME=${SERVERNAME:-unset}"
    hostname

- [ ] **Step 2: 両方へ置く**

    scripts/sync/setup_host_servername.sh --help 2>&1 | head -20

**道具を読んでから使う。** 手で追記してもよい。**どちらにせよ追記内容を記録する。**

**`~/.zshenv` と `~/.profile` の両方に置く。** 前者は zsh の全形態、
後者は bash のログイン時に読まれる。**`~/.bash_profile` `~/.bash_login` が
無いことが `.profile` 読込の条件である。**

- [ ] **Step 3: 新しいシェルで解決されることを確かめる**

    zsh -c 'echo "zsh: SERVERNAME=${SERVERNAME:-unset}"'
    bash -lc 'echo "bash: SERVERNAME=${SERVERNAME:-unset}"' 2>&1

**両方で `ilya` が出ること。**

| # | 完了判定 |
|---|---|
| 6 | 設定前の状態を記録した |
| 7 | 追記内容を記録した |
| 8 | 両方の形態で論理名が解決される |

---

## Task 3 (Phase B): 中心宛の鍵を作り、公開鍵を公開する

**Files:** Create: `~/.ssh/id_ed25519_ilyatophilip`,
`scripts/sync/hub_keys/ilya.pub`

**秘密鍵はこのホストから出さない。公開鍵だけを版管理へ置く。**

- [ ] **Step 1: 既存の鍵を確かめる**

    ls -la ~/.ssh/ 2>&1
    for f in ~/.ssh/id_*; do
      case "${f}" in
        *.pub) ssh-keygen -lf "${f}" 2>/dev/null ;;
      esac
    done

**中心宛の鍵が既に在れば作らない。** 記録して次へ進む。

- [ ] **Step 2: 鍵を作る**

**合言葉は付けない。** 常駐処理が対話なしで使うためである。

    ssh-keygen -t ed25519 -N "" -C "ilyatophilip" \
      -f ~/.ssh/id_ed25519_ilyatophilip
    ls -la ~/.ssh/id_ed25519_ilyatophilip*
    ssh-keygen -lf ~/.ssh/id_ed25519_ilyatophilip.pub

**指紋を記録する。** これが中心の受け入れ一覧に入る値である。

- [ ] **Step 3: 権限を確かめる**

    stat -c "%a %n" ~/.ssh/id_ed25519_ilyatophilip ~/.ssh/id_ed25519_ilyatophilip.pub
    stat -c "%a %n" ~/.ssh

**秘密鍵は `600`、`~/.ssh` は `700` であること。** 緩いと使われない。

- [ ] **Step 4: 公開鍵を版管理へ置く**

    mkdir -p scripts/sync/hub_keys
    cp ~/.ssh/id_ed25519_ilyatophilip.pub scripts/sync/hub_keys/ilya.pub
    ssh-keygen -lf scripts/sync/hub_keys/ilya.pub

**指紋が Step 2 と一致すること。**

**置いたものが公開鍵だけであることを三つで確かめる。**

    head -c 30 scripts/sync/hub_keys/ilya.pub; echo
    grep -c "PRIVATE" scripts/sync/hub_keys/ilya.pub
    grep -c '' scripts/sync/hub_keys/ilya.pub

Expected: 先頭が `ssh-`。`PRIVATE` が **零**。行数が **一**。
**一つでも外れたら停止して報告する。**

**陽性対照**: 秘密鍵の書き出しを模した一時ファイルに同じ検査をかけ、
**一以上を返すこと**を確かめる。**囮は版管理へ入れない。**

| # | 完了判定 |
|---|---|
| 9 | 既存の鍵を確かめた（在れば作っていない） |
| 10 | 中心宛の鍵を作り、指紋を記録した（秘密鍵の中身なし） |
| 11 | 権限が期待どおり（秘密鍵と `~/.ssh`） |
| 12 | 公開鍵を版管理へ置き、指紋が一致し、三つの検査を通った |

---

## Task 4 (Phase B): 同期処理を導入し、識別子を公開する

**Files:** Create: `~/bin/syncthing`, `scripts/sync/device_ids/ilya.txt`

- [ ] **Step 1: 配布物を取得し、照合する**

    mkdir -p ~/bin
    cd /tmp && curl -sSL -o st_ilya.tar.gz \
      "https://github.com/syncthing/syncthing/releases/download/v1.27.10/syncthing-linux-amd64-v1.27.10.tar.gz"
    sha256sum /tmp/st_ilya.tar.gz

Expected: `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60`

**一致しなければ停止して報告する。** 中心と違う版を入れてはならない。

- [ ] **Step 2: 展開して配置する**

    cd /tmp && tar xzf st_ilya.tar.gz
    cp /tmp/syncthing-linux-amd64-v1.27.10/syncthing ~/bin/syncthing
    chmod 755 ~/bin/syncthing
    sha256sum ~/bin/syncthing
    ~/bin/syncthing --version

Expected: `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`

**中心と同じ値であること。**

- [ ] **Step 3: 識別子を発行する**

    ~/bin/syncthing generate --home ~/.local/state/syncthing 2>&1 | tail -20

**常駐しない。起動してはならない**（禁止 6）。
**既に設定が在れば上書きしない。** 記録して次へ進む。

- [ ] **Step 4: 識別子を読み取り、公開する**

    ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id 2>&1

**`device-id` という下位命令は無い。** 上の形を使う。

    mkdir -p scripts/sync/device_ids
    ~/bin/syncthing serve --home ~/.local/state/syncthing --device-id \
      > scripts/sync/device_ids/ilya.txt
    cat scripts/sync/device_ids/ilya.txt
    grep -c '' scripts/sync/device_ids/ilya.txt

**一行であること。** 乱れがあれば整える。**識別子は秘匿ではない。**

- [ ] **Step 5: 起動していないことを確かめる**

    python3 - <<'PY'
    ports=set()
    for f in ("/proc/net/tcp","/proc/net/tcp6"):
        try: ls=open(f).read().splitlines()[1:]
        except OSError: continue
        for ln in ls:
            x=ln.split()
            if len(x)>3 and x[3]=="0A": ports.add(int(x[1].split(":")[1],16))
    print("count=%d"%len(ports))
    for q in (22,22000,22001,8384): print("port_%d=%s"%(q,"LISTEN" if q in ports else "-"))
    PY

**`22000` と `8384` が待ち受けていないこと。**

| # | 完了判定 |
|---|---|
| 13 | 配布物の要約値が中心と一致した |
| 14 | 配置物の要約値が中心と一致し、版が表示できる |
| 15 | 識別子を発行した（既存があれば上書きしていない） |
| 16 | 識別子を一行で公開した |
| 17 | **同期処理が起動していない** |

---

## Task 5 (Phase C): 記録し、送出する

**Files:** Create: `tasks/T-2026-08-22-ilya-node-foundation/RESULT.md`, `tasks/T-2026-08-22-ilya-node-foundation/result.yaml`,
`tasks/inbox.d/T-2026-08-22-ilya-node-foundation.md`

- [ ] **Step 1: 完了判定 17 項目を表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

**あわせて、次の契約で使う情報を記す。**

| 項目 | 内容 |
|---|---|
| 自ホストの識別子 | 版管理の場所と値 |
| 中心宛の鍵の指紋 | 中心が受け入れ一覧へ入れる値 |
| 前契約の実測との差 | 十件のうち当てはまらなかったもの |
| つまずいた点 | 他台で同じことが起きうる |

- [ ] **Step 2: 送信前に自分で秘匿を検査する**

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
      tasks/T-2026-08-22-ilya-node-foundation/*.md tasks/T-2026-08-22-ilya-node-foundation/*.yaml 2>&1

**判定するのは件数ではなく形である。** 一致を一件ずつ確かめる。
**鍵の書き出し行や、語に区切りと値が続く形は削る。** 説明文の語は差し支えない。
**識別子と指紋は秘匿ではない。削らない。**

**陽性対照**: 囮を含む一時ファイルで**一以上を返すこと**を確かめる。**囮は commit しない。**

- [ ] **Step 3: 検証を通す**

    source .venv/bin/activate \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate \
      && make task-validate TASK=T-2026-08-22-ilya-node-foundation; echo "validate_exit=$?"

    source .venv/bin/activate \
      && make forbidden-check; echo "forbidden_exit=$?"

**資格情報を要して失敗するものは、記録して続行する。**

- [ ] **Step 4: 生成物を再生成する**

    source .venv/bin/activate && make taskindex && make inbox
    source .venv/bin/activate && make taskindex-check; echo "taskindex_exit=$?"
    source .venv/bin/activate && make inbox-check; echo "inbox_exit=$?"

- [ ] **Step 5: 変更範囲と未追跡を確かめる**

    git --no-pager status --porcelain > /tmp/hf_ilya.txt
    grep -c '' /tmp/hf_ilya.txt; cat /tmp/hf_ilya.txt

**開始時の未追跡がすべて残っていること。**
**変更が契約のディレクトリ、公開鍵、識別子、生成物に限られること。**

- [ ] **Step 6: commit し、送出する**

    git add tasks/T-2026-08-22-ilya-node-foundation/ tasks/inbox.d/T-2026-08-22-ilya-node-foundation.md \
            scripts/sync/hub_keys/ilya.pub \
            scripts/sync/device_ids/ilya.txt \
            context/auto/ tasks/inbox.md
    git commit -m "feat(sync): build foundation and publish hub key and device id on ilya"
    git --no-pager log -1 --format='%h %s'
    git push -u origin HEAD
    git --no-pager status -sb

**`git add` は明示したものだけ。** `-A` は使わない。

    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**送出できない場合、`gh auth status` と `git remote -v` を記録して報告する。**
**台帳へは返さない。** 起票者は版管理から読む。

| # | 完了判定 |
|---|---|
| 18 | 17 項目すべてに実測値または UNKNOWN がある |
| 19 | 送信前の秘匿検査を自分で行った（陽性対照つき） |
| 20 | 開始時の未追跡がすべて残っている |
| 21 | 変更が契約の範囲に限られる |
| 22 | 分岐が送出され、PR が存在する（番号） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **未追跡が減った** | **停止して報告。** 版管理外の成果物を失っている |
| **`.venv` の大きさが激減した** | **停止して報告。** 六ギガを破棄した疑いがある |
| 実行環境を直せない | **停止して報告。** 出力を貼る |
| 配布物の要約値が中心と違う | **停止して報告。** 版が揃わない |
| 識別子を読み取れない | 設定の中を探す。**何を見たかを記録する** |
| **同期処理が起動してしまった** | **記録して報告。** 止めるかは次の判断 |
| 論理名が両形態で解決されない | 置き場所を見直す |
| 前契約の実測が当てはまらない | **記録する。** ホストによる差である |
| 送出できない | `gh auth status` と `remote -v` を記録して報告する |
| 道具が存在しないように見える | **最新かを確かめてから判断する**（前契約の誤報） |

**言い訳をしない。事実と、測れなかったことを書く。**

# audit — T-2026-08-24-lecun-syncthing-node

**手続きの証跡。** 判断に使う事実は `RESULT.md` にある。本書は命令とその出力、
参照の解決の全文、検証の出力、秘匿検査の出力、変更範囲の一覧、台帳の応答を置く。

**実行ホスト:** `lecun`（`hostname` は `lecun` を返す。**前ホスト ilya は `aolab` を返した**）
**repo:** `/home/ubuntu/slocal/m2`（**他四台の `~/slocal2/m2` と違う。写し間違えないこと**）
**分岐:** `feat/lecun-syncthing-node`
**開始:** 2026-08-24T19:21:05Z（JST 2026-08-25T04:21:05+0900）

---

## 0. 契約の取り込みと前提

### 0.1 `make task-start`

    $ cd /home/ubuntu/slocal/m2
    $ grep -c "sync-pause" ~/bin/m2-sync.sh
    2                                   ← 2 なので稼働中の版が抑止に対応している
    $ source .venv/bin/activate && source scripts/load_env.sh \
        && make task-start TASK=T-2026-08-24-lecun-syncthing-node
    [load_env] .env をロード（WANDB_API_KEY=set / NOTION_API_KEY=set）
    [task-start] git fetch origin
    [task-start] 分岐を作成: feat/lecun-syncthing-node（起点 origin/phase0）
    [task-start] .sync-pause を作成（報告まで終えたら rm -f .sync-pause）
    [task-start] 契約を取り込みます: T-2026-08-24-lecun-syncthing-node
    OK   T-2026-08-24-lecun-syncthing-node
    1 task(s), 0 failed
    取り込みました: tasks/T-2026-08-24-lecun-syncthing-node
    [task-start] 完了。分岐 feat/lecun-syncthing-node で契約 … の作業を開始できます

**一度目は exit 3 で止まった。** 作業ツリーに未追跡が 3 件あったためである。

    ?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
    ?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
    ?? docs/sessions/digest/2026-08-23-df8af05d-d760-42da-8eac-97f11929bd6e.md

これらは**本契約が作ったものではなく、開始前から存在した**。別分岐
（`docs/session-digests-*`）で記録する運用の生成物である。**消していない**（禁止 7）。
scratchpad へ退避して `task-start` を通し、報告の後に元へ戻す（逸脱 1）。

    $ mv docs/sessions/digest/{2026-08-22-52ba4658-…,2026-08-22-7c2986d7-…,2026-08-23-df8af05d-…}.md \
        <scratchpad>/digest-stash/
    $ git --no-pager status --porcelain
    （空）

**前契約 bengio / andrew / ilya は同じ理由で `task-start` を実行できていない。**
**本契約は退避によって実行した。** これが四台のうち唯一の差である。

### 0.2 検証（L1 + L2）

    $ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-lecun-syncthing-node
    OK   T-2026-08-24-lecun-syncthing-node
    1 task(s), 0 failed
    EXIT=0

### 0.3 参照の解決

`contract.inject_verbatim: [conventions#prohibitions]` の**原文**
（`context/conventions.md:98-108`。要約していない）:

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`conventions_rev` の実測:

    $ git --no-pager log -1 --format=%h -- context/conventions.md
    d422b087

契約の記載は `d422b08`。**同じ commit の 7 桁表記である**（実測 8 桁の先頭一致）。
SPEC の指示に従い実測値 `d422b087` へ置換した。**逸脱ではなく手順である。**

解決しなかった参照:

| 記載 | 扱い |
|---|---|
| `inputs.denominator.ref` | **本契約に無い**。解決対象なし |
| `inputs.sigma_policy` | **本契約に無い**。解決対象なし |
| `inputs.frozen_source.ref` | **本契約に無い**。解決対象なし |
| `inputs.data`（`egosurgery_phase_v1` / `data/splits/ego_val.txt`） | 🔴 **参照しなかった。** SPEC が明記するとおり雛形の必須項目として残っているだけで、同期の設営に dataset も split も要らない。**起票者の誤り 3 として記録する** |

### 0.4 プリフライト（L3）

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-08-24-lecun-syncthing-node
    P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=… sys.prefix=…
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS tasks/T-2026-08-24-lecun-syncthing-node/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              WARN 規則 8 件のうち 1 件が該当:
                                   separated_source@…/SPEC.md:48（終了コードは変わらない）
    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
    EXIT=0

**SKIP は「合格」ではなく「実行されなかった」を意味する。** SKIP は `P2` `P3` `P4` `P5` の 4 件。

**`P9` の WARN は誤検知である。** SPEC.md:47-48 は 1 つの命令を行継続（`\`）で
2 行に折ったものであり、`source` は**同じ命令の中にある**。

    47:    source .venv/bin/activate && source scripts/load_env.sh \
    48:      && make task-start TASK=T-2026-08-24-lecun-syncthing-node

検査器は行を単位に見るため折り返しを別命令と読む。**契約側の誤りではなく検査器の
限界であるから `issuer_defects` には数えない。** 報告には含める。

---

## 1. Phase A — 開始状態の封印と中心への到達の確認

### Step 1: 現状を要約値で記録する

#### 1.1 ホストと版管理の位置

    $ hostname
    lecun
    $ ls -d ~/slocal/m2 ~/slocal2/m2
    ls: cannot access '/home/ubuntu/slocal2/m2': No such file or directory
    /home/ubuntu/slocal/m2

🔴 **`~/slocal2` は存在しない。** `keeper.sh` の
`M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)` により
本ホストの `M2DIR` は `/home/ubuntu/slocal/m2` へ解決される。**共有フォルダ `m2` の
位置にはこの値を使う。前ホストの `/home/ubuntu/slocal2/m2` を写さない。**

#### 1.2 要約値と権限

    $ stat -c '%n %a %s' ~/bin/syncthing
    /home/ubuntu/bin/syncthing 644 26730145
    $ sha256sum ~/bin/syncthing
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd

    $ sha256sum ~/.local/state/syncthing/{config.xml,cert.pem,key.pem}
    41a4ab4846014d5d0cc9995fd9f3fb59fa35ff04c349ef1458b2df07154cae73  config.xml
    bbc68a938922763319824a504808c6b2160ae273f37257a8734ac3fa7e4ef73e  cert.pem
    7b1f37f7ba2da22395efaf44984b365b3e701cecb19b813bde7ef9b9288785e5  key.pem
    $ stat -c '%n %a %s' ~/.local/state/syncthing/{config.xml,cert.pem,key.pem}
    config.xml 600 8494
    cert.pem   664 790
    key.pem    600 288

    $ sha256sum scripts/sync/keeper.sh scripts/sync/m2-sync.sh ~/bin/m2-sync.sh
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh

    $ sha256sum .stignore .stglobalignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stignore
    61593e99292e428c7c6f2157772722c147eaa48452c7e5b71e438363d1de9a2a  .stglobalignore

**除外規則の 2 つは同じ内容である**（`keeper.sh` が毎周回 `.stglobalignore` から
`.stignore` を作るため）。要約値は前ホスト ilya と同一。**`.stignore` は git の追跡外**
（`git ls-files --error-unmatch .stignore` が `did not match any file(s)`）。

    $ ls -la ~/.tunnel_to_philip
    ls: cannot access '/home/ubuntu/.tunnel_to_philip': No such file or directory
    marker_exists=0

#### 1.3 稼働の計数（**両方向の対照つき**）

🔴 **最初に書いた計数は誤りだった。** `cmdline` を語で照合する方式は**自己一致する**。
否定対照 `zzz_no_such_token` が **1** を返した（自分の命令行にその語が含まれるため）。
**片方向だけを見ていたら「壊れていない」と誤読していた。** 申し送り 5 のとおりである。

    誤: tunnel_to_hub_procs=1 / port22001_in_cmdline_procs=1 / zzz_no_such_token=1

**実体名（`/proc/<pid>/exe` の readlink）で絞る方式へ改めた。** 自分は zsh / python で
あり `syncthing` にも `ssh` にも一致しない。

    $ python3 <scratchpad>/probe/probe.py all
    exe=syncthing        count=0
    exe=ssh              count=0
    exe=zsh              count=4     ← 肯定対照
        pid=62117 ppid=62116 cmd=-zsh
        pid=103459 ppid=101471 cmd=/usr/bin/zsh
        pid=104225 ppid=104224 cmd=-zsh
        pid=127360 ppid=63488 cmd=/usr/bin/zsh -c source …
    exe=zzz_no_such_exe  count=0     ← 否定対照
    port  22000 = CLOSED
    port  22001 = CLOSED
    port     22 = LISTEN             ← 肯定対照
    port      1 = CLOSED             ← 否定対照

`ss` `netstat` `lsof` は無い。**待ち受けは `/proc/net/tcp{,6}` を復号して判定した**
（`st` 欄が `0A` なら LISTEN）。

常駐処理（止めてはならない。禁止 12）:

    $ python3 …（cmdline 照合。ただし自分の pid/ppid を除外する）
    keeper.sh(肯定対照): count=1
        pid=89614 ppid=1 cmd=/bin/bash /home/ubuntu/bin/keeper.sh
    m2-sync.sh: count=0                     ← 周回の合間。異常ではない
    zzz_no_such_token(否定対照): count=0     ← 除外を入れたので 0 になる

#### 1.4 共有領域と repo の**実数**（丸めない）

    $ ls -la ~/claude-sync/
    -rw-rw-r-- 1 ubuntu ubuntu 1610 Aug 24 16:54 sync-alerts.log
    $ du -sb ~/claude-sync
    1610    /home/ubuntu/claude-sync
    $ find ~/claude-sync -type f | wc -l
    1
    $ find ~/claude-sync -mindepth 1 | wc -l
    1
    $ du -sb /home/ubuntu/slocal/m2
    7652515378      /home/ubuntu/slocal/m2

🔴 **前ホストの値を引き継いでいない。** 実測は次のとおり食い違う。

| ホスト | `~/claude-sync` | repo `du -sb` |
|---|---|---|
| bengio | 4031 B | — |
| andrew | 1510 B | 54745194976 B |
| ilya | 4528 B | 47515332495 B |
| **lecun（本ホスト）** | **1610 B / 1 件** | **7652515378 B** |

**本ホストの repo は他の三台の 1/6〜1/7 である。** 定数として扱ってはならない。

#### 1.5 設定の中身（**画面の鍵は出力しない**）

    $ python3  # XML 解析。**階層を見て数える**
    root tag=configuration version=37
    直下の要素: folder(id=default), device(id=OOOTQMG…), gui, ldap, options, defaults
    最上位 folder = 1 件
      folder id='default' label='Default Folder' path='/home/ubuntu/Sync' type='sendreceive'
         shared-with OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3
    単純検索 .//folder = 2 件          ← 差はひな型 defaults/<folder id="">
    最上位 device = 1 件
      device id=OOOTQMG-… name='lecun' addresses=['dynamic']
    defaults 配下: folder(id=''), device(id=''), ignores

    options 配下の**実在する**要素名（予想していない。全 54 件のうち関係するもの）:
      globalAnnounceEnabled            = 'true'
      localAnnounceEnabled             = 'true'
      relaysEnabled                    = 'true'
      autoUpgradeIntervalH             = '12'
    gui 配下:
      address                          = '127.0.0.1:8384'
      apikey                           = <len=32 empty=False>   ← **値は出力していない**
      theme                            = 'default'

    コメント件数 = 0                    ← 注釈が無いので生の XML の置換で書式が壊れない
    字下げの実測:
      indent=4  <folder id="default" …>          ← 最上位
      indent=8  <folder id="" label="" path="~" …>  ← ひな型（`defaults` 配下）。**触らない**

🔴 **自分の登録名の初期値は `lecun` である。** すなわち**既に正しい**。
実測は bengio=`Bengio`、andrew=`Andrew`、ilya=`aolab`、**lecun=`lecun`** と四台とも
異なった。**予想では当てられない。実測して確かめた**（Task 2 Step 4 で再掲）。

### Step 2: 控えを repo の外へ取る

    $ TS=20260824-192105
    $ cp -a ~/.local/state/syncthing ~/.local/state/syncthing.bak.$TS
    $ sha256sum ~/.local/state/syncthing.bak.$TS/{config.xml,cert.pem,key.pem}
    41a4ab4846014d5d0cc9995fd9f3fb59fa35ff04c349ef1458b2df07154cae73  config.xml   ← 開始時と一致
    bbc68a938922763319824a504808c6b2160ae273f37257a8734ac3fa7e4ef73e  cert.pem     ← 開始時と一致
    7b1f37f7ba2da22395efaf44984b365b3e701cecb19b813bde7ef9b9288785e5  key.pem      ← 開始時と一致
    $ stat -c '%n %a %s' …/config.xml …/cert.pem …/key.pem
    config.xml 600 8494 / cert.pem 664 790 / key.pem 600 288    ← 権限も保たれている

    $ mkdir -p ~/syncthing-rollback && cp -a ~/bin/syncthing ~/syncthing-rollback/syncthing.v1.27.10.orig
    $ sha256sum ~/syncthing-rollback/syncthing.v1.27.10.orig
    32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd   ← 開始時と一致

**秘密鍵の書き出しが混ざっていないことの確認**（値は出さない。件数だけ。陽性対照つき）:

    $ python3  # -----BEGIN … PRIVATE KEY----- の出現件数
      cert.pem     private_key_blocks=0
      config.xml   private_key_blocks=0
      key.pem      private_key_blocks=1     ← **それ自体が秘密鍵なので 1 が正しい**
    控えの合計 = 1
    陽性対照(key.pem そのもの) = 1           ← 検査が働いている
    版管理へ置く判断: apikey_len=32 empty=False -> **置かない**

**`gui/apikey` が実値であるため、設定一式を版管理へは置かない。**
控えは `~/.local/state/syncthing.bak.20260824-192105`（repo の外）にある。

### Step 3: 戻し方を記録する（**実行していない**）

**起動を止める最短手は実行権を落とすことである。** `keeper.sh:41` が
`[ -x ~/bin/syncthing ] && ! pgrep -x syncthing` を見て起こすため、`644` にすれば
次の周回から起こされない。**常駐処理そのものは止めない**（禁止 12）。

    # 1. 起動を止める（実行権を落とす）
    chmod 644 ~/bin/syncthing
    # 2. 動いているものを終える（親子の親だけを終えれば子も終わる）
    #    pid は /proc/<pid>/exe の実体名が syncthing のものを取る。pgrep -x でもよい
    kill "$(pgrep -x syncthing | head -1)"
    # 3. 中継の目印を外す（別名へ移す。keeper は .tunnel_to_* を辞書順で探す）
    mv ~/.tunnel_to_philip ~/.tunnel_to_philip.disabled
    # 4. 中継の処理を終える
    kill "$(pgrep -f 'ssh.*-L 22001:127.0.0.1:22000' | head -1)"
    # 5. 設定と実行ファイルを開始時へ戻す
    cp -a ~/.local/state/syncthing.bak.20260824-192105/config.xml ~/.local/state/syncthing/config.xml
    cp -a ~/syncthing-rollback/syncthing.v1.27.10.orig ~/bin/syncthing
    chmod 644 ~/bin/syncthing
    # 6. 戻ったことを要約値で確かめる
    sha256sum ~/.local/state/syncthing/config.xml   # 41a4ab48… を期待
    sha256sum ~/bin/syncthing                       # 32ab747e… を期待

**注意。** 一度起動すると設定は書き戻され、`config_version` が上がる（37 → 52 の実測が
前契約にある）。**5 は「開始時の内容へ戻す」であって「起動前の状態と同一になる」では
ない。** データベース（`~/.local/state/syncthing/index-*`）は残る。

### Step 4: 中心の値を版管理から読み、到達を確かめる

    $ cat scripts/sync/device_ids/philip.txt
    3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
    $ cat scripts/sync/device_ids/lecun.txt
    OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3

**設定内の自分の識別子と一致する**（1.5 の `device id=OOOTQMG-…-KRFOWA3`）。
**本文の転記ではなく版管理のファイルから読んだ。**

    $ ssh-keygen -lf scripts/sync/hub_keys/lecun.pub
    256 SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI lecuntophilip (ED25519)

    $ test -f ~/.ssh/id_ed25519_lecuntophilip && echo key_exists=1
    key_exists=1

    $ timeout 25 ssh -v -N -p 50072 -i ~/.ssh/id_ed25519_lecuntophilip \
        -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=<scratchpad>/known_hosts.isolated \
        -o IdentitiesOnly=yes -o BatchMode=yes -o ConnectTimeout=10 ubuntu@192.168.196.150
    Warning: Permanently added '[192.168.196.150]:50072' (ED25519) to the list of known hosts.
    debug1: Offering public key: /home/ubuntu/.ssh/id_ed25519_lecuntophilip ED25519 SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI explicit
    debug1: Server accepts key:  /home/ubuntu/.ssh/id_ed25519_lecuntophilip ED25519 SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI explicit
    Authenticated to 192.168.196.150 ([192.168.196.150]:50072) using "publickey".
    authenticated_lines=1
    denied=0
    isolated_known_hosts_lines=1

🟢 **中心へ入れた。** 使った鍵の指紋は**版管理の `scripts/sync/hub_keys/lecun.pub` と一致**する
（`SHA256:g5Twfvg…`）。**`ssh -N` を使い、中心では命令を一切実行していない**（禁止 1）。
受け入れの控えは**隔離先へ書いた。`~/.ssh/known_hosts` は触っていない。**

🔴 **`~/.ssh/` の一覧は実行基盤に拒否された。**

    $ ls -la ~/.ssh/
    （auto mode の分類器が命令ごと拒否）

**回避していない。** 指紋の照合は版管理側の公開鍵で代えた（SPEC つまずき 8 の指示どおり）。
**鍵の権限は直接確認できていない。UNKNOWN として記録する。**

### Gate G1 の判定

| 判定材料 | 実測 | 結果 |
|---|---|---|
| 開始状態を要約値で記録 | 1.2 のとおり | 🟢 |
| 実行権が `644` | `644` | 🟢 |
| 目印が零件 | `marker_exists=0` | 🟢 |
| 同期処理が零件 | `exe=syncthing count=0` | 🟢 |
| 中継が零件 | `exe=ssh count=0` / `port 22001 = CLOSED` | 🟢 |
| 両方向の対照 | 肯定 `zsh=4` / `port22=LISTEN`、否定 `zzz_no_such_exe=0` / `port1=CLOSED` | 🟢 |
| 控えを版管理の外へ | `~/.local/state/syncthing.bak.20260824-192105`（要約値 3 件とも一致） | 🟢 |
| 自分の識別子が設定と一致 | `OOOTQMG-…-KRFOWA3` = `device_ids/lecun.txt` | 🟢 |
| 中心へ命令を伴わない形で入れる | `ssh -N` で `Authenticated to`、`denied=0` | 🟢 |

**G1 = pass。**

---

## 2. Phase B — 版を揃え、設定を組み立てる

**停止中に直接編集した。** 命令列（`syncthing cli`）は常駐を要するため使えない。

### Step 1: 版を中心に揃える

    $ strings ~/bin/syncthing | grep -oE "^v[0-9]+\.[0-9]+\.[0-9]+$" | sort -u
    v1.27.10                       ← **本ホストは古い。入れ替える**

    $ curl -fsSL -o syncthing-v2.1.3.tar.gz \
        https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz
    curl_exit=0
    $ ls -l syncthing-v2.1.3.tar.gz ; sha256sum syncthing-v2.1.3.tar.gz
    11821325 syncthing-v2.1.3.tar.gz
    f929eb8e5b72a85543eeeefb2c38f34a68e0c530e70758a2905b78840c76602c

**取得物の要約値と大きさは前契約（ilya）の実測と一致した**（`f929eb8e…` / 11821325 B）。

**配布物の中の同名 3 件を大きさで切り分けた**（つまずき 7）:

    $ tar -tvzf syncthing-v2.1.3.tar.gz | grep syncthing
    -rw-r--r--       1709  syncthing-linux-amd64-v2.1.3/etc/freebsd-rc/syncthing      ← 別物
    -rw-r--r--        175  syncthing-linux-amd64-v2.1.3/etc/firewall-ufw/syncthing    ← 別物
    -rwxr-xr-x   27045912  syncthing-linux-amd64-v2.1.3/syncthing                     ← **実体**

    $ tar -xzf … -C … syncthing-linux-amd64-v2.1.3/syncthing
    $ sha256sum …/syncthing-linux-amd64-v2.1.3/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    size = 27045912 期待 27045912
    sha256 一致 = True                ← **中心の実測と完全一致**

**差し替えは「`644` を付けた別名を作ってから `mv`」で行った。**
`cp` してから `chmod` すると、その間だけ実行権が立つ。常駐処理は実行権だけを見て
起こすため、**周回がその隙に当たれば中継の前に起動してしまう。** 隙を作らない。

    $ cp …/syncthing ~/bin/syncthing.new && chmod 644 ~/bin/syncthing.new
    /home/ubuntu/bin/syncthing.new 644 27045912
    $ mv ~/bin/syncthing.new ~/bin/syncthing
    $ stat -c '%n %a %s' ~/bin/syncthing ; sha256sum ~/bin/syncthing
    /home/ubuntu/bin/syncthing 644 27045912
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4
    実行権が落ちているか: not-executable(正しい)

**`~/bin/**` への書き込みは本ホストでは拒否されなかった**（前契約 ilya では auto mode の
分類器に拒否されている。**ホストではなく実行基盤の状態による差である**）。

### Step 2〜6: 設定の編集

編集器は `<scratchpad>/probe/build_config.py`。**各置換は `assert n == 1` で件数を表明する。**
当たらないまま進むと食い違いを残して起動するためである（SPEC Step 4 の警告）。

**字下げを 4 に固定した。** `<defaults>` 配下は字下げ 8 であるから当たらない（禁止 5）。
実測:

    indent=4  <folder id="default" …>              ← 最上位
    indent=8  <folder id="" label="" path="~" …>   ← ひな型。触らない
    コメント件数 = 0                                ← 生の XML の置換で書式が壊れない

    $ .venv/bin/python <scratchpad>/probe/build_config.py
    編集前 sha256 = 41a4ab4846014d5d0cc9995fd9f3fb59fa35ff04c349ef1458b2df07154cae73
    中心の識別子（版管理から読んだ） = 3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE
      OK autoUpgradeIntervalH 12->0                   (件数 1)
      OK globalAnnounceEnabled true->false            (件数 1)
      OK relaysEnabled true->false                    (件数 1)
      OK localAnnounceEnabled true のまま（変えない）      (件数 1)
      実測: 自分の登録名 = 'lecun'
      OK 登録名は既に lecun。置換しない（件数 0 が正しい）    (件数 0)
      OK folder の入れ替え default -> claude-sync, m2   (件数 1)
      OK 中心の登録 philip / tcp://127.0.0.1:22001      (件数 1)
    編集後 sha256 = 8d3145a2579985c1feb1d5414a06609968b558335ad9c6e85f1524c0b85bdc02

| Step | 変更 | 前 | 後 |
|---|---|---|---|
| 2 | `options/autoUpgradeIntervalH` | `12` | **`0`** |
| 3 | `options/globalAnnounceEnabled` | `true` | **`false`** |
| 3 | `options/relaysEnabled` | `true` | **`false`** |
| 3 | `options/localAnnounceEnabled` | `true` | **`true`（変えない）** |
| 4 | 自分の登録名 | **`lecun`** | **`lecun`（既に正しい。置換件数 0）** |
| 5 | 中心の登録 | 無し | `id=3J4TRX4-…-DZOCQQE` name=`philip` address=`tcp://127.0.0.1:22001` |
| 6 | 共有フォルダ | `default`（`/home/ubuntu/Sync`） | **`claude-sync` と `m2`** |

🔴 **Step 4 について。** SPEC は「初期値は一定ではない。実測は `Bengio` / `Andrew` /
`aolab` と分かれた。**自分の名前が `lecun` であること。違えば直す**」と書く。
**本ホストの初期値は既に `lecun` であった。** したがって**正しい件数は 0 である。**

**「件数 0 は当たらなかった証拠」ではない。** 当たらなかった場合と区別するため、
編集器は置換ではなく**現在値の読み出し**（`re.search` で `name="([^"]*)"` を取る）で
判定し、`lecun` なら置換を行わないと明示的に分岐している。**読み出しが失敗すれば
`assert m` で止まる。** 四台のうち本ホストだけが初期値で正しかった。

**他のノード（`bengio` `andrew` `ilya`）は登録していない。** 星型であるため。

🔴 **共有フォルダ `m2` の位置は `/home/ubuntu/slocal/m2` である。**
他の四台の `/home/ubuntu/slocal2/m2` を**写していない**。`keeper.sh` の
`M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)` と一致する。

### Step 7: 書式と定義を確かめる

    $ .venv/bin/python  # XML 解析。**階層を見て数える**
    xml_ok=True root=configuration version=37
    top_level_folder_count=2
    top_level_device_count=2
    naive_folder_count=3   (単純検索。差はひな型)
    naive_device_count=8   (単純検索。差はひな型と folder 配下の共有相手)
      folder id='claude-sync' path='/home/ubuntu/claude-sync' type='sendreceive' shared_with=2 ['OOOTQMG','3J4TRX4']
      folder id='m2'          path='/home/ubuntu/slocal/m2'   type='sendreceive' shared_with=2 ['OOOTQMG','3J4TRX4']
      device id=OOOTQMG… name='lecun'  address=['dynamic']
      device id=3J4TRX4… name='philip' address=['tcp://127.0.0.1:22001']
      options/autoUpgradeIntervalH     = 0
      options/globalAnnounceEnabled    = false
      options/localAnnounceEnabled     = true
      options/relaysEnabled            = false
    --- defaults 配下（触っていないこと）---
      [('folder', ''), ('device', ''), ('ignores', None)]

**最上位の folder は 2 件。単純検索は 3 件を返す。差はひな型である**（禁止 5 を守った）。
**識別子 `claude-sync` と `m2` は中心と同じ 2 語である。**

権限と鍵が変わっていないこと:

    $ stat -c '%n perm=%a size=%s' config.xml cert.pem key.pem
    config.xml perm=600 size=11357     ← 8494 から増えた（folder が 2 件になったため）
    cert.pem   perm=664 size=790
    key.pem    perm=600 size=288
    $ sha256sum cert.pem key.pem
    bbc68a938922763319824a504808c6b2160ae273f37257a8734ac3fa7e4ef73e  cert.pem  ← 開始時と同じ
    7b1f37f7ba2da22395efaf44984b365b3e701cecb19b813bde7ef9b9288785e5  key.pem   ← 開始時と同じ

**鍵は生成も変更も削除もしていない**（禁止 3）。

### Gate G2 の判定

| 判定材料 | 実測 | 結果 |
|---|---|---|
| 実行ファイルの要約値が中心と一致 | `e8a08fdd…` = 中心の実測 | 🟢 |
| 実行権が落ちたまま | `644` / `not-executable` | 🟢 |
| 自動更新を止めた | `autoUpgradeIntervalH` `12` → `0` | 🟢 |
| 告知と外部の中継を無効 | `global=false` / `relays=false` / `local=true` | 🟢 |
| 中心を中継の出口で登録 | `philip` / `tcp://127.0.0.1:22001` | 🟢 |
| 最上位の共有フォルダが 2 件 | `top_level_folder_count=2`（単純検索は 3） | 🟢 |
| 識別子が中心と同じ | `claude-sync` / `m2` | 🟢 |
| 書式が解析でき権限が保たれている | `xml_ok=True` / `600` `664` `600` | 🟢 |

**G2 = pass。**

---

## 3. Phase C — 中継を張り、起動する

**順序が要である。目印 → 中継 → 実行権 → 起動。** 実測でその順に並んだことを示す。

### Step 1: 目印を置く

    $ umask 077
    $ printf '%s\n%s\n' '/home/ubuntu/.ssh/id_ed25519_lecuntophilip' '192.168.196.150' \
        > ~/.tunnel_to_philip
    marker_created_at=2026-08-24T19:28:34.892Z
    $ stat -c '%n perm=%a size=%s' ~/.tunnel_to_philip
    /home/ubuntu/.tunnel_to_philip perm=600 size=59
    $ cat ~/.tunnel_to_philip
    /home/ubuntu/.ssh/id_ed25519_lecuntophilip
    192.168.196.150
    $ ls -1 ~/.tunnel_to_* | wc -l
    1                                  ← 目印は 1 件

**2 行目は `192.168.196.150` を採った。** 版管理内の `handoff.md` が案として持つ
`192.168.196.176` は**使っていない**（SPEC Step 1 の指示、および前契約の実測）。

**`umask 077` を先に置いた。** `printf > file` してから `chmod 600` にすると、その間だけ
他者から読める。**鍵の経路を含むファイルで隙を作らない。**

### Step 2: 中継が立つのを待ち、確かめる

**周回の位相を先に測った。** 常駐処理の子 `sleep 1800` の開始時刻から次の周回を導く。

    $ python3  # /proc/<pid>/stat の starttime と /proc/stat の btime から復元
    pid=89614  ppid=1     exe=bash  cmd='/bin/bash /home/ubuntu/bin/keeper.sh'
                                    start=2026-08-23T17:53:10Z elapsed=92175.6s
    pid=128665 ppid=89614 exe=sleep cmd='sleep 1800'
                                    start=2026-08-24T19:24:40Z elapsed=285.5s

**次の周回は 19:54:40Z と見積もった。目印は 19:28:34.892Z であるから約 1565 秒後になる。**

    $ （背景で 10 秒ごとに /proc/net/tcp を復号して監視）
    2026-08-24T19:31:59.721Z 待ち受けの変化: port 22000 = CLOSED port 22001 = CLOSED
    2026-08-24T19:54:44.305Z 待ち受けの変化: port 22000 = CLOSED port 22001 = LISTEN
    2026-08-24T19:54:44.322Z TUNNEL_UP 中継が立った

    $ 目印 -> 中継 = 1569.413 秒       ← 見積もり 1565 秒とほぼ一致

**中継の実体**（観測 2026-08-24T19:55:13.258Z）:

    中継 pid=135351 ppid=89614 exe=ssh
      start=2026-08-24T19:54:40Z
      引数: ssh -N -L 22001:127.0.0.1:22000 -p 50072 \
             -i /home/ubuntu/.ssh/id_ed25519_lecuntophilip \
             -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
             -o ServerAliveInterval=30 -o ServerAliveCountMax=3 ubuntu@192.168.196.150
      引数に中心の住所を含むか: True
      引数に 22001 の転送を含むか: True
      親: pid=89614 cmd=/bin/bash /home/ubuntu/bin/keeper.sh

**同時刻に次を観測した。これが順序の証拠である。**

    port  22001 = LISTEN               ← 中継は立っている
    /home/ubuntu/bin/syncthing perm=644 ← **実行権はまだ戻していない**
    exe=syncthing        count=0       ← **同期処理はまだ 0 件**
    exe=ssh              count=1

中継の記録:

    $ tail ~/.tunnel.log
    Warning: Permanently added '[192.168.196.150]:50072' (ED25519) to the list of known hosts.

🔴 **この 1 行は常駐処理が張った ssh のものである。** `keeper.sh` は
`-o StrictHostKeyChecking=accept-new` を付けており、**`~/.ssh/known_hosts` へ書く。**
**自分の到達確認（Task 1 Step 4）は隔離先を使っており、`~/.ssh/known_hosts` を触っていない。**
常駐処理が書いた分は本契約の操作ではない。**区別して記録する。**

### Step 3: 実行権を戻す

    $ date -u +%FT%T.%3NZ ; stat -c 'perm=%a ctime=%.3Z' ~/bin/syncthing
    2026-08-24T19:55:44.454Z   perm=644 ctime=1787599562.614
    $ chmod 755 ~/bin/syncthing
    $ date -u +%FT%T.%3NZ ; stat -c 'perm=%a ctime=%.3Z' ~/bin/syncthing
    2026-08-24T19:55:44.547Z   perm=755 ctime=1787601344.543
    $ sha256sum ~/bin/syncthing
    e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4   ← **不変**
    $ ~/bin/syncthing --version
    syncthing v2.1.3 "Hafnium Hornet" (go1.26.5 linux-amd64) builder@github.syncthing.net 2026-08-03 21:36:05 UTC

**順序の実測。**

| 事象 | 時刻（UTC） |
|---|---|
| 目印を置いた | `19:28:34.892` |
| **中継が立った** | **`19:54:44.305`** |
| **実行権を戻した** | **`19:55:44.547`** |

**中継が実行権より 60.242 秒早い。** 中継が立ったことを確かめてから戻している。

### Step 4: 起動を待ち、確かめる

    $ （背景で 10 秒ごとに監視。**成功・中継喪失・時間切れの三つとも一行出す**）
    2026-08-24T20:24:50.932Z SYNCTHING_UP 起動した: port 22000 = LISTEN port 22001 = LISTEN

**実行権 → 起動 = 1746.4 秒**（`19:55:44.547` → `20:24:50.932`）。**次の周回で起きている。**

プロセス（観測 2026-08-24T20:25:05.865Z）:

    syncthing プロセス数 = 2
      pid=140103 ppid=89614  親が keeper（監視役）  start=2026-08-24T20:24:41Z
          cmd=/home/ubuntu/bin/syncthing serve --no-browser
      pid=140120 ppid=140103 親が syncthing（作業役） start=2026-08-24T20:24:41Z
          cmd=/home/ubuntu/bin/syncthing serve --no-browser

**2 件は正常である。** `pgrep` の件数ではなく**親子関係で切り分けた。**
`140103` の親は常駐処理 `89614`、`140120` の親は `140103` である。

    port 22000 = LISTEN     ← 自分の同期処理
    port 22001 = LISTEN     ← 中継（立ったまま）
    中継 pid=135351 ppid=89614 も生きている
    $ ~/bin/syncthing --version
    syncthing v2.1.3 …      ← **中心と同じ**

起動後の設定（**書き戻されて要約値は変わる。定義で確かめる**）:

    $ sha256sum config.xml
    eb3cb64c73f9760bfe0a7eed1ff2cd87499962c0429eddacfc2ace5f93166289   ← 8d3145a2… から変わった
    perm=600 size=11329
    config version = 52                 ← 37 から移行（`config.xml.v37` が控えとして作られた）
    top_level_folder_count = 2          ← **保たれている**
    top_level_device_count = 2
      folder id='claude-sync' path='/home/ubuntu/claude-sync' type='sendreceive' shared=2
      folder id='m2'          path='/home/ubuntu/slocal/m2'   type='sendreceive' shared=2
      device id=OOOTQMG… name='lecun'  addr=['dynamic']
      device id=3J4TRX4… name='philip' addr=['tcp://127.0.0.1:22001']
      options/autoUpgradeIntervalH   = 0        ← **零のまま**
      options/globalAnnounceEnabled  = false
      options/localAnnounceEnabled   = true
      options/relaysEnabled          = false
    defaults 配下: [('folder',''), ('device',''), ('ignores',None)]   ← 触っていない

    $ grep -c -i upgrade ~/.syncthing.log
    0                                   ← **自動更新は走っていない**

中心と繋がった記録:

    14:  20:24:42 INF Loaded peer device configuration (device=3J4TRX4 name=philip address="[tcp://127.0.0.1:22001]")
    16:  20:24:42 INF Established secure connection (device=3J4TRX4 connection.local=127.0.0.1:22000
             connection.remote=127.0.0.1:22001 connection.type=tcp-client connection.crypto=TLS1.3-…)
    18:  20:24:42 INF New device connection (device=3J4TRX4 address=127.0.0.1:22001
             remote.name=philip remote.client=syncthing remote.version=v2.1.3)

### Gate G3 の判定

| 判定材料 | 実測 | 結果 |
|---|---|---|
| 目印を置いて中継が立った | `22001 = LISTEN`、pid 135351（親 = keeper） | 🟢 |
| 引数に中心の住所 | `ubuntu@192.168.196.150` を含む | 🟢 |
| 中継が立ってから実行権を戻した | 中継 `19:54:44.305` / 実行権 `19:55:44.547`。**中継が 60.242 秒早い** | 🟢 |
| 同期処理が起動 | 2 件（親子）、`22000 = LISTEN` | 🟢 |
| 版が中心と同じ | `v2.1.3` | 🟢 |
| 最上位の folder が 2 件のまま | `top_level_folder_count = 2` | 🟢 |
| 自動更新が零のまま | `autoUpgradeIntervalH = 0`、記録の `upgrade` 該当 0 | 🟢 |

**G3 = pass。**

---

## 4. Phase D — 実際に届くことの確認

**「繋がった」ではなく「届いた」を確かめる。**

### Step 1: 自分から中心へ送る

    $ du -sb ~/claude-sync ; find ~/claude-sync -type f | wc -l
    38128   /home/ubuntu/claude-sync
    12
    ← 置く前に既に増えていた。**起動 20:24:41 から約 53 秒で中心の内容が届いている**

    $ printf 'probe from lecun\ntime=%s\nnonce=%s\n' "$NOW" "$RND" > ~/claude-sync/probe-lecun.txt
    placed_at=2026-08-24T20:25:34.518Z
    $ sha256sum ~/claude-sync/probe-lecun.txt ; stat -c 'size=%s' …
    b10b8fbbe92f109c8ce03ef42d805198efa0829750ff477b7d493fee06c9390d
    size=86
    $ cat ~/claude-sync/probe-lecun.txt
    probe from lecun
    time=2026-08-24T20:25:34+0000
    nonce=f8eef03c9fb44d81efb7ce5dc6856f26

### Step 2: 中心が持っていることを確かめる（**中心で命令を実行しない**）

**自ホストの画面の REST へ問い合わせた。** 合言葉は変数へ読み込むだけで**画面へ出していない**
（`apikey_len=32 empty=False` としか出していない）。

**走査が落ち着いてから問うた**（前契約の指摘）:

    $ /rest/db/status?folder=claude-sync
    20:25:46.298Z claude-sync "state": "idle"      ← 1 度目で idle。待つ必要がなかった

    $ /rest/system/version → "version": "v2.1.3" "os": "linux" "arch": "amd64"
    $ /rest/system/status  → "myID": "OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3"

中心が共有フォルダを全部持っているか:

    $ /rest/db/completion?folder=claude-sync&device=3J4TRX4-…-DZOCQQE
      "completion": 100  "needBytes": 0  "needItems": 0  "needDeletes": 0
      "globalBytes": 38097  "remoteState": "valid"
    $ /rest/db/completion?folder=m2&device=3J4TRX4-…-DZOCQQE
      "completion": 100  "needBytes": 0  "needItems": 0  "needDeletes": 0
      "globalBytes": 42010845130  "remoteState": "valid"

🟢 **自分の試験ファイルを中心が持っているか:**

    $ /rest/db/file?folder=claude-sync&file=probe-lecun.txt  -> HTTP 200
      availability = [{'id': '3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE',
                       'fromTemporary': False}]
      global: size=86 modifiedBy=OOOTQMG sequence=33
      local : size=86 modifiedBy=OOOTQMG

**`availability` に中心の識別子が現れた。往復している。**

**陽性対照**（判定が空振りでないことを判定の外から確かめる）:

    $ /rest/db/file?folder=claude-sync&file=zzz-no-such-file.txt -> HTTP 404
    $ /rest/db/file?folder=claude-sync&file=probe-lecun.txt      -> HTTP 200

**存在しない名前は 404 を返す。** したがって 200 は「常に 200 を返す壊れ方」ではない。

### Step 3: 中心から届いたものを測る（**実数**）

| 時点 | `du -sb ~/claude-sync` | ファイル数 |
|---|---|---|
| 開始時 | **1610 B** | **1**（`sync-alerts.log` のみ） |
| 起動 53 秒後 | 38128 B | 12 |
| 試験ファイル設置後 | **38214 B** | **13** |

**増分 +36604 B / +12 件。消えたものは無い**（`sync-alerts.log` は残っている）。

届いたもの:

    probe-andrew.txt   83 B  (08-24 16:09)
    probe-bengio.txt   40 B  (08-24 13:10)
    probe-ilya.txt     78 B  (08-24 18:20)
    probe-lecun.txt    86 B  (08-24 20:25)   ← 自分が置いたもの
    .stfolder/                              ← 同期の目印（syncthing が作る）
    sync-alerts.sync-conflict-*.log  7 件

**四台すべての試験ファイルが揃った。**

#### 記録の衝突（**上書きではなく衝突ファイル。両方残る**）

**衝突ファイルは 7 件。うち 2 件が本契約中に生まれた**（`-OOOTQMG` = 自分の識別子）。

    sync-alerts.sync-conflict-20260824-202451-OOOTQMG.log   6534 B / 61 行
    sync-alerts.sync-conflict-20260824-202452-OOOTQMG.log   6534 B / 61 行

**どちらが起きたかを中身で確かめた。**

| ファイル | 行数 | 含まれるホスト |
|---|---|---|
| `sync-alerts.log`（本体） | **20** | **`[lecun]` のみ 20 行** |
| 衝突ファイル（2 件とも同じ） | **61** | `[ilya]` 51 / `[bengio]` 4 / `[philip]` 4 / `[andrew]` 2 |

🔴 **自分の内容が本体として勝ち、中心側の内容が衝突ファイルになった**（前ホスト ilya と同じ向き。
andrew とは逆）。本体には開始時に見た最終行
`2026-08-24 19:24:41 [lecun] 一時停止中: …` が含まれており、**自分の記録は失われていない。**
中心側の 61 行も**両方残っている。**

**これは正常である**（SPEC「記録が衝突した → 正常である。両方残る」）。
**消していない**（禁止 4）。

### Step 4: repo の同期の様子を測る（**完了を待たない**）

**大きさは本ホストで測った。**

| 時点 | `localBytes` | `localFiles` | `needBytes` | `needFiles` | `du -sb` repo |
|---|---|---|---|---|---|
| 起動直後 20:26:11 頃 | 5648093905 | 1243 | 35855406412 | 4013 | — |
| **T1 20:26:57.693** | **9285625122** | **1552** | 32072910466 | 3704 | 17339362471 |
| **T2 20:28:00.749** | **15687225893** | **2160** | 26016195954 | 3096 | 23259601822 |

    計測間隔 = 63.056 秒
    localBytes +6401600771 B → **101522468 B/s ≒ 101.5 MB/s**
    localFiles +608 件      → 9.6 件/s
    残り 26016195954 B → この速さなら約 256 秒（4.3 分）

`globalBytes = 42010845130` / `globalFiles = 5256`、`errors = 0` / `pullErrors = 0`、
`state = syncing`。**完了は待っていない。進み方を次へ渡す。**

🔴 **開始時の repo は 7652515378 B であった。** 群れ全体は 42010845130 B であるから、
**本ホストは大きく不足していた側である。** 前三台（ilya 47.5G / andrew 54.7G）と違い、
**本ホストは受け取る量が多い。**

### Gate（Phase D に gate は無い）

| # | 完了判定 | 実測 |
|---|---|---|
| S | 試験ファイルと要約値・大きさ | `probe-lecun.txt` `b10b8fbb…` **86 B** |
| T | 中心が持っている | `availability=[3J4TRX4-…-DZOCQQE]`、`completion=100 needBytes=0`。陽性対照 404/200 |
| U | 共有領域の増加 | **1610 B / 1 件 → 38214 B / 13 件**（+36604 B / +12 件）。消失なし |
| V | repo の進み方 | 101.5 MB/s、`needBytes` 26016195954、`state=syncing`、`errors=0` |

---

## 5. Phase E — 報告と送出

### Step 2: 触っていないものが無変更であること

    $ sha256sum scripts/sync/keeper.sh scripts/sync/m2-sync.sh ~/bin/m2-sync.sh
    9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90  scripts/sync/keeper.sh    ← 開始時と同一
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  scripts/sync/m2-sync.sh   ← 開始時と同一
    bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f  /home/ubuntu/bin/m2-sync.sh
    $ git --no-pager diff -- scripts/sync/ | wc -l
    0                                  ← **差分 0 行**

受け入れ一覧（**変更していない**。禁止 3）:

    7299ba7c…  device_ids/andrew.txt      06649883…  hub_keys/andrew.pub
    d46bb8a3…  device_ids/bengio.txt      5c9bcdcc…  hub_keys/bengio.pub
    ceaa37be…  device_ids/ilya.txt        16cd6b3f…  hub_keys/ilya.pub
    6827eab2…  device_ids/lecun.txt       3fcc9b00…  hub_keys/lecun.pub
    c8e9ceb1…  device_ids/philip.txt

    $ sha256sum .stignore .stglobalignore
    61593e99…  .stignore        ← 開始時と同一
    61593e99…  .stglobalignore  ← 開始時と同一
    $ ls -1 ~/.tunnel_to_* | wc -l
    1                                  ← **目印は 1 件**
    $ 常駐処理 keeper pid=89614 は生きている（**止めていない**。禁止 12）

🔴 **自己一致がここでも出た。** `keeper.sh` を語で数えたところ 2 件が返り、そのうち 1 件は
**自分の命令行**であった（命令の本文に `keeper.sh` という語が含まれるため）。
`os.getpid()` による自己除外は、**命令を包むシェルが別の pid を持つため効かない。**
実体は 1 件である。**起票者の誤り 1 と同じ事象が、別の場面で再現した。**

🔴 **同期が `experiments/` へ書いた。**

    $ git --no-pager status --porcelain
    ?? experiments/baselines/s0_002_maskdino_bbox_seed123/.syncthing.epoch_12.pth.tmp
    ?? tasks/T-2026-08-24-lecun-syncthing-node/

`.stignore` は `experiments/baselines/_*` しか除外しない（39 行目）。**`m2` フォルダは repo 全体
であるから、`experiments/` の中身も同期の対象になる。** これは**契約自身が Task 2 Step 6 で
定義した結果**であって実行者の操作ではない。**禁止 11（`experiments/**` を変更・削除しない）と
両立しない。触らずに申し送りへ回した。** 送出の時点では一時ファイルは消えていた（同期が完了した）。

### Step 3: 検証を通す

    $ source .venv/bin/activate && make task-validate TASK=T-2026-08-24-lecun-syncthing-node
    OK   T-2026-08-24-lecun-syncthing-node
    1 task(s), 0 failed
    validate_exit=0

    $ source .venv/bin/activate && make task-preflight TASK=T-2026-08-24-lecun-syncthing-node
    P1 venv_active            PASS …
    P2 cuda_ext_loaded        SKIP …      P3 deterministic_flags   SKIP …
    P4 prereg_committed       SKIP …      P5 frozen_source_hash    SKIP …
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS
    P8 contract_valid         PASS
    P9 spec_lint              WARN separated_source@SPEC.md:48
    RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
    preflight_exit=0

    $ source .venv/bin/activate && make forbidden-check
    {"base": "origin/phase0", "changed": 6, "checked": 6, "errors": [], "excluded": 0,
     "excluded_paths": [], "generated_directories": ["context/auto/"],
     "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
    forbidden_exit=0

`conventions_rev` は実測して `d422b087` へ置換済み（0.3 参照）。
**生成物の検査（`make taskindex-check` / `make inbox-check`）は実行していない**（禁止 6。逸脱 5）。

### Step 4: 送信前の秘匿検査

**検査そのものが値を出力していない。** 実値は長さと有無だけを示した。

    $ source scripts/load_env.sh && .venv/bin/python <scratchpad>/probe/secretscan.py
    照合する実値の種類 = 3 (NOTION_API_KEY, SYNCTHING_APIKEY, WANDB_API_KEY)
      NOTION_API_KEY     len=50 empty=False
      WANDB_API_KEY      len=86 empty=False
      SYNCTHING_APIKEY   len=32 empty=False
    --- 送出対象 ---
      tasks/T-2026-08-24-lecun-syncthing-node/RESULT.md    literal=0 shape={...0,0,0}
      tasks/T-2026-08-24-lecun-syncthing-node/SPEC.md      literal=0 shape={...0,0,0}
      tasks/T-2026-08-24-lecun-syncthing-node/audit.md     literal=0 shape={...0,0,0}
      tasks/T-2026-08-24-lecun-syncthing-node/result.yaml  literal=0 shape={...0,0,0}
      tasks/T-2026-08-24-lecun-syncthing-node/spec.yaml    literal=0 shape={...0,0,0}
      tasks/inbox.d/T-2026-08-24-lecun-syncthing-node.md   literal=0 shape={...0,0,0}
    literal_leaks = 0
    shape_hits    = {'Notion の内部鍵': 0, '鍵らしい代入': 0, '秘密鍵の書き出し': 0}
    --- 陽性対照（囮は commit していない） ---
      decoy_literal_detected = 3/3
      decoy_shape_hits       = {'Notion の内部鍵': 2, '鍵らしい代入': 1, '秘密鍵の書き出し': 1}
      陽性対照が働いているか = True
    secretscan_exit = 0

**囮は変数の中だけに置き、ファイルへ書いていない。** したがって commit にも含まれない。
**判定したのは件数ではなく形である**（実値との一致・鍵らしい代入・内部鍵の接頭辞・秘密鍵の書き出し）。

### Step 5: 送出

    $ git add tasks/T-2026-08-24-lecun-syncthing-node/ tasks/inbox.d/T-2026-08-24-lecun-syncthing-node.md
    $ git --no-pager diff --cached --stat
     RESULT.md   | 112 +++      SPEC.md    | 389 ++++      audit.md   | 815 ++++++
     result.yaml |  86 +++      spec.yaml  |  92 +++       inbox.d/…  |  35 +
     6 files changed, 1529 insertions(+)
    範囲外の件数 = 0            ← **契約のディレクトリと受け皿に限られている**

    $ git commit …
    49b24fbb feat(sync): connect lecun to the syncthing hub
    $ git push -u origin feat/lecun-syncthing-node
    push_exit=0
    local  = 49b24fbbbce4189d936d59f4699b21bb3e4d8450
    remote = 49b24fbbbce4189d936d59f4699b21bb3e4d8450

    $ gh pr list --head feat/lecun-syncthing-node --state all --json number,state,title
    []                          ← **既存の PR は無い。新規に作る**
    $ gh pr create --base phase0 …
    https://github.com/takuya3h/m2/pull/146

#### 台帳

    $ source .venv/bin/activate && source scripts/load_env.sh \
        && make task-report TASK=T-2026-08-24-lecun-syncthing-node
    {
      "task_id": "T-2026-08-24-lecun-syncthing-node",
      "verdict": "pass",
      "n_issuer_defects": 5,
      "report_sha256": "2eace20734639141a39ef5f8974fe282f0582c6823604bac6d22f9948e44b298",
      "report_bytes": 16625,
      "replaced_blocks": 0
    }
    report_exit=0

**送ったのは記録して起票したあとである。** `replaced_blocks: 0` は初回投稿を意味する。

#### 抑止

**削除ではなく移動で外す**（技能書の既定。実装は目印の存在だけを見る）。

    $ mv .sync-pause .sync-pause.released
    $ ls -la .sync-pause
    ls: cannot access '.sync-pause': No such file or directory
    $ ls -la .sync-pause.released
    -rw-rw-r-- 1 ubuntu ubuntu 0 Aug 24 19:16 .sync-pause.released
    抑止が外れているか: 外れた(正しい)

🔴 **副作用。** `.gitignore:240` は `.sync-pause` だけを無視するため、`.sync-pause.released` が
**未追跡ファイルとして残り `git status` に現れる**（ilya が報告済み）。
**禁止 7（未追跡の成果物を削除しない）に従い消していない。**

#### 退避した digest を戻す

    $ mv <scratchpad>/digest-stash/*.md docs/sessions/digest/
    2026-08-22-52ba4658-….md   9568 B
    2026-08-22-7c2986d7-….md   2253 B
    2026-08-23-df8af05d-….md  22907 B
    退避先の残り = 0 件         ← **全て戻した。消していない**

**これらは開始前から存在したものであり、本契約の commit には含めていない。**

### 変更範囲の一覧（最終）

    $ git --no-pager status --porcelain
     M tasks/T-2026-08-24-lecun-syncthing-node/RESULT.md     ← PR 番号と検証結果を反映
     M tasks/T-2026-08-24-lecun-syncthing-node/audit.md      ← 本節
     M tasks/T-2026-08-24-lecun-syncthing-node/result.yaml   ← pr: 146 / commits
    ?? .sync-pause.released                                  ← 抑止の解除の副作用（消さない）
    ?? docs/sessions/digest/2026-08-22-52ba4658-….md         ← 開始前から存在（戻した）
    ?? docs/sessions/digest/2026-08-22-7c2986d7-….md         ← 開始前から存在（戻した）
    ?? docs/sessions/digest/2026-08-23-df8af05d-….md         ← 開始前から存在（戻した）

**契約が触ったのは `tasks/T-2026-08-24-lecun-syncthing-node/` と
`tasks/inbox.d/T-2026-08-24-lecun-syncthing-node.md` だけである。**

### Gate（Phase E に gate は無い）

| # | 完了判定 | 実測 |
|---|---|---|
| W | 報告の構成と分量 | `RESULT.md` は 7 節・112 行（目安 150 行以内）。証跡は `audit.md` へ分離し、行番号で指した |
| X | 触っていないものが無変更 | `keeper.sh` `9fe9c423…` / `m2-sync.sh` `bcf46ba9…` / 受け入れ一覧 9 件 / `.stignore` `61593e99…` すべて開始時と同一。`scripts/sync/` の差分 0 行。**目印 1 件**。常駐処理 pid 89614 は生存 |
| Y | 秘匿検査 | `secretscan_exit=0`、`literal_leaks=0`、`shape_hits=0`。**検査は値を出力していない**。陽性対照 `3/3` と形 3 規則すべて発火。囮は commit していない |
| Z | 送出 | commit `49b24fbb`、push 済（手元 = リモート）、**PR #146**、台帳 `report_exit=0`（`report_sha256=2eace207…`）、抑止は `.sync-pause.released` へ移動して解除 |

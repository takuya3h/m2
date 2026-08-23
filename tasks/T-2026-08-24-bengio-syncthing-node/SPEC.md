# 一台目のノードを中心へ繋ぐ（bengio）

**task_id:** `T-2026-08-24-bengio-syncthing-node`  **kind:** `impl`
**depends_on:** `T-2026-08-24-philip-syncthing-hub`
**実行ホスト:** `bengio`  **repo:** `~/slocal2/m2`

## Goal

**中心（philip）の待ち受けは立った。** `22000` が待ち受け、四台が相手として登録され、
共有フォルダ二件が同期可能な状態にある。

**本契約は一台目のノードを中心へ繋ぐ。** 残る三台はこの結果を見てから進める。
**本再構築で最初にファイルが実際に届く契約である。**

### 中心の実測値（前契約）

| 項目 | 値 |
|---|---|
| 識別子 | `scripts/sync/device_ids/philip.txt` を読む。**本文の転記を信用しない** |
| 登録名 | **`philip`**（OS のホスト名は `aolab`。ilya と衝突するため明示された） |
| 待ち受け | **`22000`**。ノードの中継 `-L 22001:127.0.0.1:22000` の接続先 |
| 共有フォルダ | `claude-sync` = `/home/ubuntu/claude-sync`、`m2` = `/home/ubuntu/slocal2/m2`。ともに `sendreceive` |
| 除外規則 | `.stignore`（`61593e99…`。正本 `.stglobalignore` と一致） |
| **版** | **`v2.1.3`**。起動時に `v1.27.10` から自動更新された |

### 前契約のつまずき（本ホストでも起きる）

| # | 内容 |
|---|---|
| **1** | **起動と同時に自動更新が走る。** `autoUpgradeIntervalH` の既定は十二。**実行権を戻す前に零にする** |
| **2** | **設定に画面の鍵が実値で入っている。** 版管理へ控えを置くなら**必ず伏せる** |
| **3** | **正常時もプロセスは二件**（監視役と作業役）。件数だけで二重起動を判定しない。**親子関係で切り分ける** |
| **4** | **起動の記録は `~/.syncthing.log`。** 共有領域の中ではない |
| 5 | 起動時に設定は書き戻される。**要約値は変わる。定義が消えていないことで確かめる** |

### 版の食い違い

**中心は `v2.1.3`、本ホストは `v1.27.10` のはずである。**
**本契約は先に本ホストを `v2.1.3` へ揃える。** 版が違う相手が繋がるかは未確認であり、
**揃えてから繋ぐ方が切り分けやすい。**

**自動更新に任せない。** 実行権を戻す前に、**手で入れ替えて要約値を照合する。**

## 0. 前提と禁止事項

    cd ~/slocal2/m2
    touch .sync-pause
    grep -c "sync-pause" ~/bin/m2-sync.sh
    git --no-pager status --porcelain | grep -c ''
    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-start TASK=T-2026-08-24-bengio-syncthing-node
    git branch --show-current
    git --no-pager log -1 --format='%h %s'

**二つ目が `2` なら抑止が効く。** `0` なら効かない。記録して続行する。
**抑止は Task 5 の最後で外す。**

**作業ツリーが汚れていると分岐が作られない。** 退避した場合は報告の後に戻す。

| # | 禁止 |
|---|---|
| 1 | **他ホストへ接続する。他ホストの状態を変更する**（中継を張るのは接続であり、これは許す） |
| 2 | **中心の設定を変更する** |
| 3 | 鍵を生成・変更・削除する。受け入れ一覧を変更する |
| 4 | **`~/claude-sync/` の中身を消す・移動する** |
| 5 | **生成物を再生成する**（`make taskindex` `make inbox` を実行しない） |
| 6 | 未追跡の成果物を削除する |
| 7 | **秘匿の値を版管理へ置く。** 画面の鍵は伏せる |
| 8 | 装置を使う |
| 9 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 10 | `experiments/**` `transfer/**` `data/**` を変更・削除する |
| 11 | 学習・評価コードを変更する |
| 12 | 常駐処理を停止・再起動する |

**禁止 1 の但し書き。** 中継は中心へ SSH で入る操作だが、**中心の状態は変えない。**
**中心で命令を実行してはならない。**

**禁止 4 の理由。** 全台で八キロバイトしか残っていない。**同期が始まると相互に影響する。**

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | **対照は両方向で取る。** 実在する語で一以上を返すことも確かめる |
| 3 | `/proc/*/cmdline` の部分一致は実行基盤を拾う。**実行ファイル名で照合する** |
| 4 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 5 | **無変更は要約値で確かめる** |
| 6 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 7 | **完了判定の数を本文中で述べない**（前契約で数え違えた） |
| 8 | 出力は要約せず `audit.md` へ貼る |

**前契約の `RESULT.md` と `handoff.md` にノード用の手順がある。**
**本 SPEC と食い違えば、そちらを正とし、食い違いを報告する。**

`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 開始状態を封印する

**Files:** Create: `tasks/T-2026-08-24-bengio-syncthing-node/audit.md`

- [ ] **Step 1: 現状を要約値で記録する**

    for f in ~/.local/state/syncthing/*; do
      test -f "${f}" && echo "$(sha256sum "${f}") $(stat -c '%s %a' "${f}")"
    done
    ls -la ~/bin/syncthing; sha256sum ~/bin/syncthing
    ~/bin/syncthing --version 2>&1 || echo "実行できない（権限）"
    sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
    ls -a ~/ | grep -c '^\.tunnel_to_'
    du -sh ~/claude-sync/ 2>&1
    find ~/claude-sync/ -type f 2>/dev/null | grep -c ''
    sha256sum .stignore .stglobalignore 2>&1

**目印が零件、実行権が `644` であることを確かめる。**
**`755` なら既に起動しうる。記録して報告する。**

- [ ] **Step 2: 稼働しているものを数える**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    def rows(word):
        out = []
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: raw = open("/proc/%s/cmdline" % d, "rb").read()
            except OSError: continue
            args = [a for a in raw.decode("utf-8","replace").split("\x00") if a]
            if any(word in os.path.basename(a) for a in args):
                st = open("/proc/%s/stat" % d).read().split(") ",1)[1].split()
                out.append((d, st[1], " ".join(args)[:80]))
        return out
    for w in ("syncthing", "keeper.sh", "ssh", "zsh", "zzz_no_such"):
        r = rows(w)
        print("%s=%d %s" % (w, len(r), [(x[0], x[1]) for x in r]))
    PY

**`zsh` が一以上、`zzz_no_such` が零で両方向の対照。**
**同期処理と中継は零のはず。** 識別子と親の識別子を控える。

- [ ] **Step 3: 設定の控えを取る**

**repo の外へ置く。** repo は同期対象になるため、中に置くと全台へ配られる。

    cp -a ~/.local/state/syncthing ~/.local/state/syncthing.bak.$(date +%Y%m%d-%H%M%S)
    ls -la ~/.local/state/ | grep syncthing

**版管理へも置く場合は、画面の鍵を伏せてから置く**（禁止 7）。

    grep -o 'apikey>[^<]*' ~/.local/state/syncthing/config.xml | head -1 | cut -c1-12

**値が出れば、そのまま置いてはならない。**

- [ ] **Step 4: 戻し方を記録する**

`audit.md` に書く。**実行はしない。**

    chmod 644 ~/bin/syncthing
    # 動いていれば止める（識別子は測り直す）
    cp -a ~/.local/state/syncthing.bak.TIMESTAMP/. ~/.local/state/syncthing/   # TIMESTAMP は Step 3 で作った控えの名前
    rm -f ~/.tunnel_to_philip

- [ ] **Step 5: 中心の値を版管理から読む**

    cat scripts/sync/device_ids/philip.txt
    cat scripts/sync/device_ids/bengio.txt
    grep -o 'device id="[^"]*" name="[^"]*"' ~/.local/state/syncthing/config.xml

**自分の識別子が版管理の値と一致すること。** 一致しなければ停止して報告する。

- [ ] **Step 6: 中心への到達と認証を測る**

**中継を張る前に、入れることを確かめる。**

    ls -la ~/.ssh/id_ed25519_bengiotophilip 2>&1

**鍵は前契約で作ったものである。** 目印はまだ無い。

    ssh -o BatchMode=yes -o ConnectTimeout=8 -o IdentitiesOnly=yes \
        -o UserKnownHostsFile=/tmp/kh_bsn.txt -o StrictHostKeyChecking=accept-new \
        -p 50072 -i ~/.ssh/id_ed25519_bengiotophilip 192.168.196.150 'echo REACHABLE' 2>&1 | tail -2

**`REACHABLE` が返ること。** 返らなければ**停止して報告する。**
中継が張れないので先へ進めない。

**`UserKnownHostsFile` を隔離している。** `~/.ssh/known_hosts` を汚さないためである。

| # | 完了判定 |
|---|---|
| A | 設定・実行ファイル・常駐処理・除外規則の要約値を記録した（実行権が `644`、目印が零件） |
| B | 稼働を両方向の対照つきで数えた（同期処理と中継が零） |
| C | 控えを repo の外へ取り、画面の鍵の有無を確かめた |
| D | 戻し方を記録した（実行していない） |
| E | 自分の識別子が版管理の値と一致した |
| F | **中心への認証が通った**（`REACHABLE`） |

---

## Task 2 (Phase B): 版を中心に揃える

**Files:** Modify: `~/bin/syncthing`

**中心は `v2.1.3` である。** 揃えてから繋ぐ。

- [ ] **Step 1: 中心と同じ版を取得する**

    cd /tmp && curl -sSL -o st_v2_bengio.tar.gz \
      "https://github.com/syncthing/syncthing/releases/download/v2.1.3/syncthing-linux-amd64-v2.1.3.tar.gz"
    ls -la /tmp/st_v2_bengio.tar.gz
    sha256sum /tmp/st_v2_bengio.tar.gz
    tar tzf /tmp/st_v2_bengio.tar.gz | head -3

**取得できなければ停止して報告する。** 版が揃わない。

**中心の実行ファイルの要約値は `e8a08fdd…` である**（前契約の実測）。
**展開したものがこれと一致するかを確かめる。** 一致しなければ**記録して報告する。**

- [ ] **Step 2: 置き換える**

**実行権は `644` のままにする。** まだ起動させない。

    cd /tmp && tar xzf st_v2_bengio.tar.gz
    cp /tmp/syncthing-linux-amd64-v2.1.3/syncthing ~/bin/syncthing
    chmod 644 ~/bin/syncthing
    ls -la ~/bin/syncthing
    sha256sum ~/bin/syncthing

**要約値が中心と一致すること。権限が `644` であること。**

| # | 完了判定 |
|---|---|
| G | 中心と同じ版を取得し、要約値を記録した |
| H | 置き換えた実行ファイルの要約値が中心と一致し、権限が `644` |

---

## Task 3 (Phase B): 設定を組み立てる

**Files:** Modify: `~/.local/state/syncthing/config.xml`

**停止中に直接編集する。** 動作中に書き換えると上書きされる。

- [ ] **Step 1: 自動更新を止める**

**これを最初に行う。** 前契約では起動と同時に更新が走った。

| 要素 | 変更後 |
|---|---|
| `autoUpgradeIntervalH` | **`0`** |

**要素名は版によって異なる。** 実在する名前を確かめてから変える。

    grep -o 'autoUpgrade[A-Za-z]*' ~/.local/state/syncthing/config.xml | sort -u

- [ ] **Step 2: 自分の登録名を確かめる**

    grep -o 'device id="[^"]*" name="[^"]*"' ~/.local/state/syncthing/config.xml

**`name` が `bengio` であること。** 別の値なら直す。
**中心は `aolab` から `philip` へ直す必要があった。** 本ホストは衝突しないが確かめる。

- [ ] **Step 3: 告知と中継を無効にする**

| 要素 | 変更後 |
|---|---|
| `globalAnnounceEnabled` | `false` |
| `relaysEnabled` | `false` |
| `localAnnounceEnabled` | `true` のまま |

- [ ] **Step 4: 中心を相手として登録する**

| 項目 | 値 |
|---|---|
| 識別子 | `scripts/sync/device_ids/philip.txt` の内容 |
| 名前 | **`philip`** |
| 住所 | **`tcp://127.0.0.1:22001`**（中継の出口） |

**ここが中心側と違う。** 中心は相手の住所を `dynamic` にしたが、
**ノードは中心の住所を中継の出口に固定する。**

**他の三台は登録しない。** 星型であり、ノード同士は直接繋がらない。

- [ ] **Step 5: 共有フォルダを二つ定義する**

| 識別子 | 位置 | 型 | 共有相手 |
|---|---|---|---|
| `claude-sync` | `/home/ubuntu/claude-sync` | `sendreceive` | 自分と中心 |
| `m2` | `/home/ubuntu/slocal2/m2` | `sendreceive` | 自分と中心 |

**識別子は中心と同じでなければならない。** 違うと別のフォルダとして扱われる。

**位置は本ホストの実際の値である。** 中心と同じ `~/slocal2/m2` だが、
**lecun は `~/slocal/m2` である**（本契約の対象外）。

**使わない共有フォルダ（`default`）があれば消す。**

- [ ] **Step 6: 書式と権限を確かめる**

    .venv/bin/python -c "import xml.etree.ElementTree as E; E.parse('$HOME/.local/state/syncthing/config.xml'); print('xml_ok')"
    grep -o 'device id="[^"]*" name="[^"]*"' ~/.local/state/syncthing/config.xml
    grep -o 'folder id="[^"]*"' ~/.local/state/syncthing/config.xml
    grep -n -E "globalAnnounceEnabled|relaysEnabled|localAnnounceEnabled|autoUpgrade" \
      ~/.local/state/syncthing/config.xml
    stat -c "%a" ~/.local/state/syncthing/config.xml

**相手が実体二件（自分と中心）、共有フォルダが二件、権限が `600` であること。**

| # | 完了判定 |
|---|---|
| I | 自動更新を止めた（要素名と値） |
| J | 自分の登録名を確かめた |
| K | 告知と中継を無効にした |
| L | 中心を相手として登録した（識別子の出所、名前、住所） |
| M | 共有フォルダを二つ定義した（識別子が中心と同じ） |
| N | 書式が解析でき、実体の件数と権限が期待どおり |

---

## Task 4 (Phase C): 中継を張り、繋ぐ

**Files:** Create: `~/.tunnel_to_philip`。Modify: `~/bin/syncthing`（権限のみ）

**順序が要である。** 目印 → 中継 → 実行権 → 起動。

- [ ] **Step 1: 目印を置く**

| 行 | 内容 |
|---|---|
| 一行目 | `/home/ubuntu/.ssh/id_ed25519_bengiotophilip` |
| 二行目 | `192.168.196.150` |

    printf '%s\n%s\n' "/home/ubuntu/.ssh/id_ed25519_bengiotophilip" "192.168.196.150" \
      > ~/.tunnel_to_philip
    chmod 600 ~/.tunnel_to_philip
    cat ~/.tunnel_to_philip
    ls -la ~/.tunnel_to_philip

**書式は前契約で確定している。** 一行目が鍵の経路、二行目が中心の住所。

- [ ] **Step 2: 常駐処理が中継を張るのを待つ**

**周期は千八百秒だが、記録の間隔は千八百と三千六百が交互だった**（前契約の実測）。
**最大で六十分待つ可能性がある。**

    tail -3 ~/claude-sync/sync-alerts.log
    date

**待つ間に実行権を戻してはならない。** 中継が立つ前に同期処理が動くと、
**繋がらない相手へ試み続ける。**

- [ ] **Step 3: 中継が立ったことを確かめる**

Task 1 Step 2 と同じ走査を行う。

    .venv/bin/python - <<'PY'
    ports=set()
    for f in ("/proc/net/tcp","/proc/net/tcp6"):
        try: ls=open(f).read().splitlines()[1:]
        except OSError: continue
        for ln in ls:
            x=ln.split()
            if len(x)>3 and x[3]=="0A": ports.add(int(x[1].split(":")[1],16))
    for q in (22,22000,22001,8384): print("port_%d=%s"%(q,"LISTEN" if q in ports else "-"))
    PY

Expected: **`22001` が待ち受けている。** これが中継の出口である。
**`22000` はまだ立たない**（同期処理が動いていないため）。

**中継の処理の引数に中心の住所が含まれることを確かめる。**

**立たなければ**、`~/.tunnel.log` を読んで原因を記録する。**実行権は戻さない。**

- [ ] **Step 4: 実行権を戻す**

**中継が立ってから行う。**

    chmod 755 ~/bin/syncthing
    ls -la ~/bin/syncthing
    sha256sum ~/bin/syncthing

**要約値が Task 2 と同じであること。**

- [ ] **Step 5: 起動を待ち、確かめる**

**常駐処理が次の周回で起こす。** 待つか、`handoff.md` の指定に従う。

起動したら次を確かめる。**処理は二件**（監視役と作業役）で、親子関係で切り分ける。
**`22000` と `22001` の両方が待ち受け、版が中心と同じ**であること。

    tail -40 ~/.syncthing.log 2>&1 || echo "記録なし"

**中心と繋がったことを示す行を探す。** 相手の識別子か名前が現れるはずである。

- [ ] **Step 6: 設定が保たれていることを確かめる**

    grep -o 'device id="[^"]*" name="[^"]*"' ~/.local/state/syncthing/config.xml
    grep -o 'folder id="[^"]*"' ~/.local/state/syncthing/config.xml
    grep -n -E "globalAnnounceEnabled|relaysEnabled|autoUpgrade" \
      ~/.local/state/syncthing/config.xml

**起動時に設定は書き戻される。要約値は変わる**（前契約の実測）。
**定義が消えていないことで確かめる。**

**自動更新が零のままであること。** 戻っていれば記録して報告する。

| # | 完了判定 |
|---|---|
| O | 目印を置いた（内容と権限） |
| P | **中継が立った**（`22001` が待ち受け、引数に中心の住所） |
| Q | 実行権を戻し、要約値が変わっていない |
| R | 同期処理が起動した（処理の数と親子関係、版） |
| S | 設定の定義が保たれ、自動更新が零のまま |

---

## Task 5 (Phase D): 実際に届くことを確かめ、報告する

**Files:** Create: `tasks/T-2026-08-24-bengio-syncthing-node/RESULT.md`,
`tasks/T-2026-08-24-bengio-syncthing-node/result.yaml`,
`tasks/inbox.d/T-2026-08-24-bengio-syncthing-node.md`

**「繋がった」ではなく「届いた」を確かめる。** これが最も強い確認である。

- [ ] **Step 1: 自分から中心へ送る**

**`~/claude-sync/` で測る。** repo は約十九ギガあり、初回の同期に時間がかかる。

    printf 'bengio-probe %s %s\n' "$(date -u +%Y%m%dT%H%M%SZ)" "$RANDOM$RANDOM" \
      > ~/claude-sync/probe-bengio.txt
    ls -la ~/claude-sync/probe-bengio.txt
    sha256sum ~/claude-sync/probe-bengio.txt
    wc -c ~/claude-sync/probe-bengio.txt

**要約値と大きさを控える。**

**中心へ届いたかは、中心で命令を実行せずに確かめる必要がある**（禁止 1）。
**同期処理の状態から読み取るか、`handoff.md` の方法に従う。**

**確かめられない場合は `UNKNOWN` とし、その理由を書く。**
**次の契約で中心側から確認できる。**

- [ ] **Step 2: 中心から届いたものを測る**

    ls -la ~/claude-sync/
    du -sh ~/claude-sync/; find ~/claude-sync/ -type f | grep -c ''
    du -sh ~/slocal2/m2 2>&1
    ls -la ~/slocal2/m2/.stfolder 2>&1 || echo "同期の目印なし"

**開始時は八キロバイト・一件だった。** 増えていれば届いている。

**両ホストの `sync-alerts.log` は別の内容である。** 同期されると片方が上書きされるか
衝突ファイルが生まれる。**どちらが起きたかを記録する。**

**repo は約十九ギガある。完了を待たない。** 進み方を記録して次へ渡す。

- [ ] **Step 3: 触っていないものが無変更であることを確かめる**

    sha256sum ~/bin/keeper.sh
    ls -a ~/ | grep -c '^\.tunnel_to_'
    ls -la ~/.ssh/ 2>&1

**目印が一件（`.tunnel_to_philip`）であること。** 常駐処理が Task 1 と同じであること。

- [ ] **Step 4: 検証を通し、送出する**

    source .venv/bin/activate && source scripts/load_env.sh \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-validate TASK=T-2026-08-24-bengio-syncthing-node; echo "validate_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-preflight TASK=T-2026-08-24-bengio-syncthing-node; echo "preflight_exit=$?"

    source .venv/bin/activate && make forbidden-check; echo "forbidden_exit=$?"

**送信前に自分で秘匿を検査する。** 画面の鍵に注意する（前契約で見逃した）。

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|apikey|password|passphrase" \
      tasks/T-2026-08-24-bengio-syncthing-node/* 2>&1

**値であれば伏せる。名前であればその旨を記す。** 陽性対照を取る。

    git --no-pager status --porcelain > /tmp/bsn_wt.txt
    grep -c '' /tmp/bsn_wt.txt; cat /tmp/bsn_wt.txt

**変更が契約のディレクトリと受け皿に限られること。**
**`~/claude-sync/probe-bengio.txt` は版管理の外である。**

    git add tasks/T-2026-08-24-bengio-syncthing-node/ \
            tasks/inbox.d/T-2026-08-24-bengio-syncthing-node.md
    git commit -m "feat(sync): connect bengio to the syncthing hub"
    git --no-pager log -1 --format='%h %s'
    git push -u origin HEAD
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

- [ ] **Step 5: 報告し、抑止を外す**

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-report TASK=T-2026-08-24-bengio-syncthing-node; echo "report_exit=$?"

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-24-bengio-syncthing-node 2>/dev/null
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

**あわせて次の契約で使う情報を記す。**

| 項目 | 内容 |
|---|---|
| 版を揃える手順 | 取得先と要約値 |
| 中継が立つまでの実測 | 目印を置いてから何秒かかったか |
| 起動までの実測 | 実行権を戻してから何秒かかったか |
| 届いたかの確かめ方 | 中心で命令を実行せずにどう確かめたか |
| repo の同期の様子 | 進み方と、完了までの見込み |
| つまずいた点 | 残る三台で同じことが起きうる |

| # | 完了判定 |
|---|---|
| T | 自分から中心へ送る試験を行った（要約値と大きさ。届いたかは UNKNOWN 可） |
| U | **共有領域の中身が増えたかを記録した**（開始時と終了時） |
| V | repo の同期の様子を記録した |
| W | 目印が一件、常駐処理が無変更 |
| X | 秘匿検査を自分で行った（陽性対照つき。**画面の鍵に注意**） |
| Y | 分岐が送出され、PR が存在する（番号） |
| Z | 報告が台帳へ返り、抑止が外れている |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **中心への認証が通らない** | **停止して報告。** 中継が張れない。目印を作らない |
| 版を取得できない、要約値が中心と違う | **停止して報告。** 版が揃わない |
| **中継が立たない** | **記録して報告。** `~/.tunnel.log` を読む。**実行権を戻さない** |
| **同期処理が起動しない** | 実行権と記録を確かめる。**六十分待っても起きなければ報告する** |
| 処理が三件以上動いた | **記録して報告。** 二件は正常である |
| **自動更新が走った** | **記録して報告。** Task 3 Step 1 が効いていない |
| **共有領域の中身が消えた** | **停止して報告。** 全台で八キロバイトしかない |
| 記録が衝突した、repo の同期が終わらない | **記録する。待たない。** 進み方を次へ渡す |
| 中心の状態が変わった | **停止して報告。** 本契約は中心を触らない |
| `handoff.md` と本 SPEC が食い違う | **`handoff.md` を正とし、食い違いを報告する** |

**言い訳をしない。事実と、測れなかったことを書く。**

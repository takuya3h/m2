# 中心の同期処理を組み立て、待ち受けを立てる（philip）

**task_id:** `T-2026-08-24-philip-syncthing-hub`  **kind:** `impl`
**depends_on:** `T-2026-08-24-syncthing-config-survey`
**実行ホスト:** `philip`（中心）  **repo:** `~/slocal2/m2`

## Goal

**保守作業で全サーバーが初期化された。** 再構築は最終段階に入った。
前契約の調査で、組み立て方が実装から確定した。

**本契約は中心の設定を整え、同期処理を立ち上げる。** 他ホストは触らない。

### 前契約で確定した事実

| 事実 | 実測 |
|---|---|
| 設定の場所 | **`~/.local/state/syncthing/`。既定の場所である**（`--home` は既定と同じ） |
| 設定を変える手段 | **直接編集。常駐は要らない。** 命令列は動いている本体へ問い合わせるため使えない |
| 現在の設定 | 相手は自分 1 件。共有フォルダは `default`（`/home/ubuntu/Sync`、**実在しない**）1 件 |
| **告知の既定値** | `globalAnnounceEnabled=true` / `relaysEnabled=true`。**旧構成は両方 false だった** |
| 旧構成の共有フォルダ | `claude-sync`（`~/claude-sync/`）と `m2`（repo）。ともに `sendreceive` |
| ノード側の相手の住所 | **`tcp://127.0.0.1:22001`**（中継の出口） |
| 起動の引き金 | **`keeper.sh:41-43` が `[ -x ~/bin/syncthing ]` だけを見て起動する** |
| 実行ファイルの権限 | **いま `644`。** 前契約が起動を避けるために落とした |
| 除外規則 | `.stglobalignore` / `.stignore` / `origin/phase0` の三者が要約値で一致 |

### 起動の引き金が順序を決める

**実行権を `755` に戻した瞬間、三十分以内に常駐処理が同期処理を起こす。**
よって**設定をすべて整えてから、最後に実行権を戻す。**

**逆にすると、定まらない設定のまま動き出す。**

### 五台の識別子（版管理から読む）

`scripts/sync/device_ids/*.txt` に五台分がある。**本契約で四台を登録する。**
**値は版管理から読むこと。本 SPEC に転記した値を信用しない。**

## 0. 前提と禁止事項

    cd ~/slocal2/m2
    git --no-pager status --porcelain | grep -c ''
    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-start TASK=T-2026-08-24-philip-syncthing-hub
    git branch --show-current
    git --no-pager log -1 --format='%h %s'

**作業ツリーが汚れていると分岐が作られない。** 前契約では未追跡二件を退避して実行した。
**同じ状況なら同じ扱いでよい。退避したものは報告の後に戻す。**

| # | 禁止 |
|---|---|
| 1 | **他ホストへ接続する。他ホストの状態を変更する** |
| 2 | **中継の目印を作る。中継を張る**（中心は目印を持たない） |
| 3 | 常駐処理を停止・再起動する |
| 4 | 鍵を生成・変更・削除する。受け入れ一覧を変更する |
| 5 | **`~/claude-sync/` の中身を消す・移動する** |
| 6 | **生成物を再生成する**（`make taskindex` `make inbox` を実行しない） |
| 7 | 未追跡の成果物を削除する |
| 8 | 秘匿の値を出力・記録する。**識別子と指紋は秘匿ではない** |
| 9 | 装置を使う |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `experiments/**` `transfer/**` `data/**` を変更・削除する |
| 12 | 学習・評価コードを変更する |

**禁止 2 の理由。** 中心は入られる側である。**目印を置くと自分へ中継を張ろうとする。**

**禁止 5 の理由。** 全台で八キロバイトしか残っていない。**わずかでも失うと戻せない。**

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | **判断の前に、いま見ているものが最新かを確かめる** |
| 2 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 3 | **対照は両方向で取る。** 実在する語で一以上を返すことも確かめる |
| 4 | `/proc/*/cmdline` の部分一致は実行基盤を拾う。**引数の要素で照合する** |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **無変更は要約値で確かめる** |
| 7 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 8 | 出力は要約せず `audit.md` へ貼る |

申し送り 2 は前契約の指摘に対応する。**起票者は設定の場所を「既定ではない」と断じたが
誤りだった。** 中心の住所も断定したが、**局所から見える値と食い違っていた。**

**前契約の `handoff.md` に中心用の手順がある。** 本 SPEC と食い違えば、
**`handoff.md` を正とし、食い違いを報告する。**

`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 開始状態を封印し、控えを取る

**Files:** Create: `tasks/T-2026-08-24-philip-syncthing-hub/audit.md`,
`tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before`

- [ ] **Step 1: 設定と実行ファイルの現状を記録する**

    for f in ~/.local/state/syncthing/*; do
      test -f "${f}" && echo "$(sha256sum "${f}") $(stat -c '%s %a' "${f}")"
    done
    ls -la ~/bin/syncthing
    sha256sum ~/bin/syncthing
    ls -a ~/ | grep -c '^\.tunnel_to_'
    du -sh ~/claude-sync/ 2>&1
    find ~/claude-sync/ -type f 2>/dev/null | grep -c ''

**実行ファイルの権限が `644` であることを確かめる。** `755` なら既に起動しうる状態である。
**記録して報告する。**

- [ ] **Step 2: 設定の控えを版管理へ残す**

**設定には鍵や証明への参照が含まれるが、`config.xml` 自体に秘密鍵の本体は無い**
（別ファイルである）。**ただし置く前に確かめる。**

    grep -c "BEGIN.*PRIVATE" ~/.local/state/syncthing/config.xml

Expected: **零。** 零でなければ**版管理へ置かない。** 記録して報告する。

    cp ~/.local/state/syncthing/config.xml \
       tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before
    sha256sum tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before

**Step 1 の要約値と一致すること。**

- [ ] **Step 3: 戻し方を記録する**

`audit.md` に書く。**実行はしない。**

    cp tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before \
       ~/.local/state/syncthing/config.xml
    chmod 600 ~/.local/state/syncthing/config.xml
    chmod 644 ~/bin/syncthing

**最後の一行が要である。** 実行権を落とせば起動が止まる。

- [ ] **Step 4: 五台の識別子を版管理から読む**

    for f in scripts/sync/device_ids/*.txt; do
      echo "$(basename "${f}" .txt) $(cat "${f}")"
    done
    ls scripts/sync/device_ids/ | grep -c '\.txt$'

**五件あること。** 自分の値が現在の設定と一致することを確かめる。

    grep -o 'device id="[^"]*"' ~/.local/state/syncthing/config.xml

**一致しなければ停止して報告する。** 別の設定を見ている。

| # | 完了判定 |
|---|---|
| 1 | 設定と実行ファイルの要約値と権限を記録した（実行権が `644`） |
| 2 | 設定に秘密鍵の本体が無いことを確かめ、控えを版管理へ残した |
| 3 | 戻し方を記録した（実行していない） |
| 4 | 五台の識別子を読み、自分の値が設定と一致した |

---

## Task 2 (Phase B): 設定を組み立てる

**Files:** Modify: `~/.local/state/syncthing/config.xml`

**直接編集する。** 命令列は常駐を要するため使えない（前契約の実測）。

**編集のたびに、書式が壊れていないことを確かめる。**

- [ ] **Step 1: 告知と中継を無効にする**

**既定は両方とも有効である。** 旧構成では無効だった。

| 要素 | 変更後 |
|---|---|
| `globalAnnounceEnabled` | `false` |
| `relaysEnabled` | `false` |
| `localAnnounceEnabled` | **`true` のまま**（旧構成と同じ） |

**外部の告知先へ自分の識別子と住所を送らないためである。**
**中継を通す構成なので、外部の中継業者も要らない。**

- [ ] **Step 2: 四台を相手として登録する**

**版管理から読んだ識別子を使う。** 各相手について次を書く。

| 項目 | 値 |
|---|---|
| 識別子 | `scripts/sync/device_ids/` の該当ホスト名のファイルの内容 |
| 名前 | 論理ホスト名（`lecun` `bengio` `andrew` `ilya`） |
| 住所 | **`dynamic`**（中心は入られる側であり、相手の住所を知らない） |

**中心は相手へ繋ぎに行かない。** ノードが中継を通って入ってくる。
**よって中心側で相手の住所を固定する必要はない。**

**`handoff.md` が別の指定をしていれば、そちらを正とする。**

- [ ] **Step 3: 共有フォルダを二つ定義する**

| 識別子 | 位置 | 型 | 共有相手 |
|---|---|---|---|
| `claude-sync` | `/home/ubuntu/claude-sync` | `sendreceive` | 四台すべて |
| `m2` | `/home/ubuntu/slocal2/m2` | `sendreceive` | 四台すべて |

**位置はホストによって違う。** 中心は `~/slocal2/m2` である。
**lecun は `~/slocal/m2` だが、それはノード側の契約で扱う。**

**全台が空なので `sendreceive` でよい**（前契約で八キロバイトと確認済み）。

- [ ] **Step 4: 使わない共有フォルダを消す**

**`default`（`/home/ubuntu/Sync`）は実在しない場所を指している。** 消す。

- [ ] **Step 5: 書式が壊れていないことを確かめる**

    .venv/bin/python -c "import xml.etree.ElementTree as E; E.parse('$HOME/.local/state/syncthing/config.xml'); print('xml_ok')"

**解析できなければ壊れている。** 控えから戻して報告する。

    grep -c 'device id=' ~/.local/state/syncthing/config.xml
    grep -o 'folder id="[^"]*"' ~/.local/state/syncthing/config.xml
    grep -n -E "globalAnnounceEnabled|relaysEnabled|localAnnounceEnabled" \
      ~/.local/state/syncthing/config.xml

**共有フォルダが二件で、`default` が無いこと。** 告知が期待どおりであること。

**相手の件数は共有相手の記載を含むため単純ではない。** 前契約が
「`grep -c 'device id='` = 4 だが実体は 1」と記録している。**実体の数を別に数える。**

- [ ] **Step 6: 権限を確かめる**

    stat -c "%a %n" ~/.local/state/syncthing/config.xml

**`600` のままであること。** 変わっていれば戻す。

| # | 完了判定 |
|---|---|
| 5 | 告知と中継を無効にした（三つの要素の値を記載） |
| 6 | 四台を相手として登録した（識別子の出所を明記） |
| 7 | 共有フォルダを二つ定義した（識別子・位置・型・共有相手） |
| 8 | 使わない共有フォルダを消した |
| 9 | 書式が解析でき、実体の件数が期待どおり |
| 10 | 権限が `600` のまま |

---

## Task 3 (Phase C): 起動し、待ち受けを確かめる

**Files:** Modify: `~/bin/syncthing`（権限のみ）

**ここで初めて動き出す。** 設定が整ってからである。

- [ ] **Step 1: 起動前の状態を記録する**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    def count(word):
        n = 0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: raw = open("/proc/%s/cmdline" % d, "rb").read()
            except OSError: continue
            args = raw.decode("utf-8", "replace").split("\x00")
            if any(word in os.path.basename(a) for a in args if a): n += 1
        return n
    for w in ("syncthing", "keeper.sh", "zsh", "zzz_no_such"):
        print("%s=%d" % (w, count(w)))
    PY

**実行ファイル名で照合している。** `zsh` が一以上、`zzz_no_such` が零で**両方向の対照**。
**同期処理は零のはず。**

- [ ] **Step 2: 実行権を戻す**

    chmod 755 ~/bin/syncthing
    ls -la ~/bin/syncthing
    sha256sum ~/bin/syncthing

**要約値が Task 1 と同じであること。** 権限だけを変えた。

**この時点から三十分以内に常駐処理が起こす。** 待たずに明示的に起こしてもよいが、
**常駐処理が起こす形を確かめる方が、以後の運用と一致する。**

**待つ場合、周期は千八百秒である。** 待たない場合は次を実行する。

    nohup ~/bin/syncthing serve --no-browser >> ~/claude-sync/syncthing.log 2>&1 &
    sleep 20

**`handoff.md` が別の起こし方を指定していれば、そちらを正とする。**

- [ ] **Step 3: 一つだけ動いていることを確かめる**

Step 1 と同じ走査を行う。

Expected: **同期処理が一件。** 二件以上なら二重に起きている。
**記録して報告する。** 常駐処理は一件のまま。

- [ ] **Step 4: 待ち受けを確かめる**

    .venv/bin/python - <<'PY'
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

Expected: **`22000` が待ち受けている。** ここへノードの中継が繋がる。
**`8384` も立つ**（画面）。**`22001` は立たない**（中心は中継を張らない）。

**`22000` が立たなければ、設定か起動が誤っている。** 記録して報告する。

- [ ] **Step 5: 設定が読み込まれたことを確かめる**

    grep -o 'folder id="[^"]*"' ~/.local/state/syncthing/config.xml
    ls -la ~/claude-sync/ 2>&1 | head -5
    du -sh ~/claude-sync/ 2>&1

**同期処理は起動時に設定を読み、必要なら書き戻す。**
**共有フォルダの定義が消えていないことを確かめる。**

**`~/claude-sync/` の中身が減っていないこと**（禁止 5）。

- [ ] **Step 6: 記録を読む**

    tail -30 ~/claude-sync/syncthing.log 2>&1 || echo "記録なし"

**起動時の異常が無いかを見る。** 相手へ繋がらないのは正常である
（ノード側がまだ中継を張っていない）。

| # | 完了判定 |
|---|---|
| 11 | 起動前の状態を記録した（両方向の対照つき） |
| 12 | 実行権を戻し、要約値が変わっていない |
| 13 | 同期処理が一件だけ動いている |
| 14 | **`22000` が待ち受けている**（`22001` は立っていない） |
| 15 | 共有フォルダの定義が残り、`~/claude-sync/` の中身が減っていない |
| 16 | 起動の記録を読み、異常の有無を記載した |

---

## Task 4 (Phase D): 記録し、送出し、報告する

**Files:** Create: `tasks/T-2026-08-24-philip-syncthing-hub/RESULT.md`,
`tasks/T-2026-08-24-philip-syncthing-hub/result.yaml`,
`tasks/inbox.d/T-2026-08-24-philip-syncthing-hub.md`

- [ ] **Step 1: 完了判定 16 項目を表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。開始時と終了時を併記する。**

**あわせて、ノード側の契約で使う情報を記す。**

| 項目 | 内容 |
|---|---|
| 中心の識別子 | ノードが登録する値 |
| 共有フォルダの定義 | 識別子・型・除外規則の扱い |
| 待ち受けの実測 | ノードの中継が繋がる先 |
| 設定の書き方 | 実際に編集した箇所と方法 |
| つまずいた点 | ノード側で同じことが起きうる |

- [ ] **Step 2: 触っていないものが無変更であることを確かめる**

    ls -a ~/ | grep -c '^\.tunnel_to_'
    sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh
    sha256sum ~/.ssh/authorized_keys

**目印が零件、常駐処理と受け入れ一覧が Task 1 と同じであること。**

- [ ] **Step 3: 検証を通す**

    source .venv/bin/activate && source scripts/load_env.sh \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-validate TASK=T-2026-08-24-philip-syncthing-hub; echo "validate_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-preflight TASK=T-2026-08-24-philip-syncthing-hub; echo "preflight_exit=$?"

    source .venv/bin/activate && make forbidden-check; echo "forbidden_exit=$?"

**`forbidden-check` は未追跡の状態で結果が変わる。** 前契約でそれが記録されている。
**判定の理由を記す。**

- [ ] **Step 4: 送信前に自分で秘匿を検査する**

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
      tasks/T-2026-08-24-philip-syncthing-hub/*.md \
      tasks/T-2026-08-24-philip-syncthing-hub/*.yaml \
      tasks/T-2026-08-24-philip-syncthing-hub/config.xml.before 2>&1

**判定するのは件数ではなく形である。** 値であれば削り、名前であればその旨を記す。
**識別子と指紋は秘匿ではない。**

**陽性対照**: 囮を含む一時ファイルで**一以上を返すこと**を確かめる。**囮は commit しない。**

- [ ] **Step 5: 変更範囲を確かめ、送出する**

    git --no-pager status --porcelain > /tmp/psh_wt.txt
    grep -c '' /tmp/psh_wt.txt; cat /tmp/psh_wt.txt

**変更が契約のディレクトリと受け皿に限られること。**
**`~/.local/state/` と `~/bin/` は版管理の外なので現れない。**

    git add tasks/T-2026-08-24-philip-syncthing-hub/ \
            tasks/inbox.d/T-2026-08-24-philip-syncthing-hub.md
    git commit -m "feat(sync): configure and start syncthing hub on philip"
    git --no-pager log -1 --format='%h %s'
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

- [ ] **Step 6: 報告を台帳へ返す**

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-report TASK=T-2026-08-24-philip-syncthing-hub; echo "report_exit=$?"

**退避したものがあれば、ここで戻す。**

    git stash list
    git stash pop 2>&1 || echo "退避なし"
    git --no-pager status --porcelain | grep -c ''

| # | 完了判定 |
|---|---|
| 17 | 16 項目すべてに実測値または UNKNOWN がある（開始時と終了時を併記） |
| 18 | 目印・常駐処理・受け入れ一覧が無変更 |
| 19 | 送信前の秘匿検査を自分で行った（陽性対照つき） |
| 20 | 変更が契約の範囲に限られ、分岐が送出され PR が存在する |
| 21 | 報告が台帳へ返っている（終了コード） |
| 22 | 退避したものを戻した（件数を記載） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **書式が壊れた** | **控えから戻して報告。** 実行権は `644` のままにする |
| **`22000` が立たない** | **記録して報告。** 設定か起動が誤っている。**実行権を落として止める** |
| 同期処理が二件以上動いた | **記録して報告。** 二重に起きている |
| **`~/claude-sync/` の中身が減った** | **停止して報告。** 全台で八キロバイトしか残っていない |
| 起動時に設定が書き換えられた | **記録する。** 同期処理は起動時に設定を整えることがある。**定義が消えていなければ続行** |
| 実行権が最初から `755` だった | **記録して報告。** 既に起動しうる状態だった |
| 識別子が設定と一致しない | **停止して報告。** 別の設定を見ている |
| `handoff.md` と本 SPEC が食い違う | **`handoff.md` を正とし、食い違いを報告する** |
| 相手へ繋がらない | **正常である。** ノードがまだ中継を張っていない |
| 台帳への返送が失敗した | 記録して報告する。**送出は済んでいるので起票者は版管理から読める** |

**言い訳をしない。事実と、測れなかったことを書く。**

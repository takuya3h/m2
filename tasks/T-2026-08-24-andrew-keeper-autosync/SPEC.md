# 常駐処理を配置し、版管理の自動同期だけを動かす（andrew）

**task_id:** `T-2026-08-24-andrew-keeper-autosync`  **kind:** `impl`
**depends_on:** `T-2026-08-22-andrew-node-foundation`
**実行ホスト:** `andrew`  **repo:** `~/slocal2/m2`

## Goal

**保守作業で全サーバーが初期化された。** 基盤の作り直しは進み、五台すべてで
実行環境と論理名と同期処理の実体が揃い、**鍵の公開鍵と識別子が版管理へ公開された。**

**本契約は常駐処理を動かし、版管理の自動同期だけを復活させる。**

**同期処理の中継は張らない。** 常駐処理は目印の有無で分岐しており、
**目印が無ければ中継を起こさず、版管理の同期だけを行う。**

| 分岐 | 実装の位置 | 本契約での扱い |
|---|---|---|
| 目印があるときだけ中継を維持 | 三十一から三十八行 | **目印を置かないので動かない** |
| 同期処理の監視、除外規則の反映、版管理の同期 | 三十九から五十行 | **これを動かす** |

**目印は段階を分けて後の契約で置く。** 全台の識別子の登録が済んでからである。

### この契約が置かれた状況

**秘匿情報の合言葉が失われ、`scripts/load_env.sh` が失敗する。**

| 使えないもの | 代替 |
|---|---|
| `make task-start` | **手で分岐を切り、契約を配置する** |
| `make task-report` | **`RESULT.md` を commit して push する** |
| `source scripts/load_env.sh` | **`source .venv/bin/activate` だけを使う** |
| 送信前の秘匿検査 | **送信前に自分で検査する** |

**合言葉の再作成は別途ユーザーが行う。** 本契約では扱わない。

## 0. 前提と禁止事項

**取り込みは手で行う。最初に版管理を最新にすること。**

    cd ~/slocal2/m2
    git --no-pager status --porcelain | grep -c ''
    git fetch origin
    git checkout -b feat/andrew-keeper-autosync origin/phase0
    git --no-pager log -1 --format='%h %s'
    mkdir -p tasks/T-2026-08-24-andrew-keeper-autosync

**`git log -1` で最新であることを必ず確かめてから判断する。**
**未追跡がある場合、それらは版管理外の成果物である。一切触らない。**

| # | 禁止 |
|---|---|
| 1 | **中継の目印を作る**（`~/.tunnel_to_*`）。**中継を張る** |
| 2 | **同期処理を起動する**（識別子の登録が済んでいない） |
| 3 | **同期処理の設定で他ホストを登録する** |
| 4 | **生成物を再生成する**（`make taskindex` `make inbox` を実行しない） |
| 5 | 未追跡の成果物を削除・移動・commit する |
| 6 | 他ホストへ接続する。他ホストの状態を変更する |
| 7 | 鍵を生成・変更・削除する。受け入れ一覧を変更する |
| 8 | `experiments/**` `transfer/**` `data/**` を変更・削除する |
| 9 | 秘匿の値を出力・記録する |
| 10 | 装置を使う |
| 11 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 12 | `runindex/**` `context/auto/**` を手で編集する |

**禁止 4 の理由。** 五台で並行して実行するため、**各契約が生成物を更新すると
版管理で必ず衝突する**（前契約で四回起きた）。**全台の統合が済んだあと、一台で一度だけ
再生成する。** `taskindex-check` が差分を報告しても、**事実として記録するだけでよい。**

**禁止 1 と 2 の理由。** 中継と同期処理は、全台の識別子が登録されてから同時に立ち上げる。
**先に動かすと、定まらない相手と繋ごうとする。**

### 全台で確定した事実（再測定は不要）

| 事実 | 値 |
|---|---|
| repo の位置 | **lecun と efros は `~/slocal/m2`、他は `~/slocal2/m2`** |
| 中心 | **philip**。住所 `192.168.196.150`、SSH は `50072` |
| 常駐処理の自己更新 | **本体はされない。** 手で配置する必要がある |
| `.zshrc` の起動行 | **全台で失われている**（実測。ilya で確認） |
| 対話シェル | **zsh。** `${PIPESTATUS[0]}` のような配列添字は使えない |
| プロセスの計数 | `pgrep -af` は自分を拾う。`pgrep -x` か `/proc/*/cmdline` を使う |
| `.venv` | 貼り直し済み。**`--clear` を使わない**（六ギガを破棄する） |

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | **判断の前に、いま見ているものが最新かを確かめる** |
| 2 | **無い**ことと**読めない**ことを区別する |
| 3 | 先頭がドットのものを落とさない |
| 4 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 5 | **無変更は要約値で確かめる。** 表示属性では足りない |
| 6 | 対照は両方向で取る。期待値を実測前に一点へ固定しない |
| 7 | `成功 && echo OK || echo NG` は表示側の失敗も NG にする |
| 8 | **配列添字で終了コードを取らない**（前契約の指摘） |
| 9 | 出力は要約せず `audit.md` へ貼る |

`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 開始状態を封印し、正本を読む

**Files:** Create: `tasks/T-2026-08-24-andrew-keeper-autosync/audit.md`

- [ ] **Step 1: 開始状態を記録する**

    ls -la ~/bin/ 2>&1 || echo "bin なし"
    ls -a ~/ | grep -i "^\.tunnel" ; echo "marker_count=$(ls -a ~/ | grep -c '^\.tunnel_to_')"
    grep -n "keeper\|nohup" ~/.zshrc 2>&1 || echo "起動行なし"
    ls -la ~/.keeper.lock 2>&1 || echo "lock なし"
    ls -la ~/claude-sync/ 2>&1 | head -3 || echo "同期領域なし"
    git --no-pager status --porcelain | grep -c ''

**目印の件数は `.tunnel_to_` で数える。** `tunnel` だけで数えると記録の類まで拾う
（前契約の実測）。

- [ ] **Step 2: 稼働しているものを数える**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for w in ("keeper.sh","m2-sync","syncthing","ssh -N -L","zzz_none"):
        n=0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: c=open("/proc/%s/cmdline"%d,"rb").read().decode("utf-8","replace")
            except OSError: continue
            if w in c: n+=1
        print("%s=%d"%(w,n))
    PY

**存在しない語が零を返すことが対照である。**
**すべて零のはずである。** 零でなければ記録して報告する。

- [ ] **Step 3: 正本を読み、目印の分岐を確かめる**

    wc -l scripts/sync/keeper.sh; sha256sum scripts/sync/keeper.sh
    grep -n -E "tunnel_to|22001|50072|m2-sync|sleep|flock" scripts/sync/keeper.sh
    wc -l scripts/sync/m2-sync.sh; sha256sum scripts/sync/m2-sync.sh

**目印が無いときに何が動き、何が動かないかを、行番号つきで記録する。**
**起票者の理解と食い違えば、実装を正として報告する。**

- [ ] **Step 4: 版管理の同期が何をするかを読む**

    grep -n -E "auto-merge|auto-push|pull request|sync-pause|SERVERNAME" scripts/sync/m2-sync.sh | head -30

**自動で統合し、送出し、下書きを起票する。** どの条件で動くかを記録する。
**起動後に意図しない統合が起きうるため、先に把握する。**

| # | 完了判定 |
|---|---|
| 1 | 開始状態を記録した（目印の件数、起動行、未追跡の件数） |
| 2 | 稼働しているものを数えた（対照つき。すべて零のはず） |
| 3 | 正本の要約値と、目印による分岐を行番号つきで記録した |
| 4 | 版管理の同期の発火条件を記録した |

---

## Task 2 (Phase B): 正本を配置する

**Files:** Create: `~/bin/keeper.sh`, `~/bin/m2-sync.sh`

- [ ] **Step 1: 置き場所を作り、配置する**

    mkdir -p ~/bin
    cp scripts/sync/keeper.sh ~/bin/keeper.sh
    cp scripts/sync/m2-sync.sh ~/bin/m2-sync.sh
    chmod 755 ~/bin/keeper.sh ~/bin/m2-sync.sh
    sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh scripts/sync/keeper.sh scripts/sync/m2-sync.sh

**配置物と正本の要約値が一致すること。**

- [ ] **Step 2: 構文を確かめる**

    sh -n ~/bin/keeper.sh; echo "keeper_syntax=$?"
    sh -n ~/bin/m2-sync.sh; echo "m2sync_syntax=$?"

**両方が零であること。** 構文誤りのまま起動すると常駐処理が即座に落ちる。

- [ ] **Step 3: 目印が無いことを確かめる**

    ls -a ~/ | grep '^\.tunnel_to_' ; echo "marker_count=$(ls -a ~/ | grep -c '^\.tunnel_to_')"

Expected: **零。** 一つでもあれば中継が起きる。**作ってはならない**（禁止 1）。

- [ ] **Step 4: 抑止の目印を置く**

    cd ~/slocal2/m2 && touch .sync-pause
    ls -la .sync-pause
    grep -c "sync-pause" ~/bin/m2-sync.sh

**版管理の同期が動く前に、抑止を置いておく。**
**三つ目が零なら抑止に対応していない版である。** 記録して報告する。

**これは Task 4 で外す。** 外すまでは自動の統合と送出が起きない。

| # | 完了判定 |
|---|---|
| 5 | 配置物と正本の要約値が一致した |
| 6 | 構文検査が両方とも通った（終了コード） |
| 7 | 目印が零件である |
| 8 | 抑止を置き、対応している版であることを確かめた |

---

## Task 3 (Phase B): 起動し、版管理の同期が回ることを確かめる

**Files:** Modify: `~/.zshrc`

- [ ] **Step 1: 起動行を追記する**

**現在は失われている**（Task 1 Step 1 で確認済み）。

    grep -n "keeper" ~/.zshrc 2>&1 || echo "該当なし"

**該当があれば追記しない。** 二重に起動する。記録して次へ進む。

追記する内容は、**正本の設計に合わせる。** 常駐ループは多重起動を防ぐ仕掛けを
持っているため、**同じものが二度起きても片方が終わる。**

    ( nohup ~/bin/keeper.sh >/dev/null 2>&1 & ) 2>/dev/null

**追記した行をそのまま記録する。**

- [ ] **Step 2: 一度だけ明示的に起動する**

    nohup ~/bin/keeper.sh >/dev/null 2>&1 &
    sleep 5

**新しいシェルを開かずに起動する。** `.zshrc` は次回以降のためである。

- [ ] **Step 3: 一つだけ動いていることを確かめる**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for w in ("keeper.sh","ssh -N -L","syncthing","zzz_none"):
        n=0; pids=[]
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: c=open("/proc/%s/cmdline"%d,"rb").read().decode("utf-8","replace")
            except OSError: continue
            if w in c: n+=1; pids.append(d)
        print("%s=%d %s"%(w,n,pids))
    PY

Expected: **常駐処理が一件。中継が零件。同期処理が零件。**

**中継が立っていたら禁止 1 に触れている。** 目印が無いのに立つなら実装の理解が誤り。
**記録して報告する。**

- [ ] **Step 4: 多重起動を防ぐ仕掛けを確かめる**

    ls -la ~/.keeper.lock 2>&1 || echo "lock なし"

**錠が作られていること。** これで二重起動が防がれる。

- [ ] **Step 5: 版管理の同期が一周したことを確かめる**

**周期は千八百秒である。** 起動直後に一周目が走る。

    ls -la ~/claude-sync/sync-alerts.log 2>&1 || echo "記録なし"
    tail -20 ~/claude-sync/sync-alerts.log 2>&1 || echo "読めない"

**`~/claude-sync/` は失われている。** 記録の置き場所が無ければ、
**別の場所を探すか、`UNKNOWN` とする。** 正本を読んでどこへ書くかを確かめる。

    grep -n -E "sync-alerts|LOG|log" ~/bin/m2-sync.sh | head -10

**抑止を置いてあるので「一時停止中」の記録が出るはずである。**
**版管理への書き込みが起きていないことを確かめる。**

    git --no-pager status -sb
    git --no-pager log -1 --format='%h %s'

**分岐が変わっていないこと。ahead が増えていないこと。**

| # | 完了判定 |
|---|---|
| 9 | 起動行を追記した（内容を記載。既存があれば追記していない） |
| 10 | 常駐処理が一件だけ動いている（識別子つき） |
| 11 | **中継が零件、同期処理が零件** |
| 12 | 多重起動を防ぐ錠が作られた |
| 13 | 版管理の同期が一周し、抑止が効いている（記録の場所と内容） |

---

## Task 4 (Phase C): 記録し、抑止を外し、送出する

**Files:** Create: `tasks/T-2026-08-24-andrew-keeper-autosync/RESULT.md`, `tasks/T-2026-08-24-andrew-keeper-autosync/result.yaml`,
`tasks/inbox.d/T-2026-08-24-andrew-keeper-autosync.md`

- [ ] **Step 1: 完了判定 13 項目を表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

**あわせて次の契約で使う情報を記す。**

| 項目 | 内容 |
|---|---|
| 記録の置き場所 | 版管理の同期がどこへ書くか |
| 起動行の内容 | 他台で同じものを使う |
| 目印を置いたときの見込み | 実装から読み取れる範囲で |
| つまずいた点 | 他台で同じことが起きうる |

- [ ] **Step 2: 送信前に自分で秘匿を検査する**

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
      tasks/T-2026-08-24-andrew-keeper-autosync/*.md tasks/T-2026-08-24-andrew-keeper-autosync/*.yaml 2>&1

**判定するのは件数ではなく形である。** 一件ずつ確かめる。
**鍵の書き出し行や、語に区切りと値が続く形は削る。** 説明文の語は差し支えない。

**陽性対照**: 囮を含む一時ファイルで**一以上を返すこと**を確かめる。**囮は commit しない。**

- [ ] **Step 3: 検証を通す**

    source .venv/bin/activate \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate \
      && make task-validate TASK=T-2026-08-24-andrew-keeper-autosync; echo "validate_exit=$?"

    source .venv/bin/activate \
      && make forbidden-check; echo "forbidden_exit=$?"

**生成物の検査が差分を報告しても、再生成しない**（禁止 4）。**記録するだけでよい。**

- [ ] **Step 4: 変更範囲と未追跡を確かめる**

    git --no-pager status --porcelain > /tmp/ka_andrew.txt
    grep -c '' /tmp/ka_andrew.txt; cat /tmp/ka_andrew.txt

**開始時の未追跡がすべて残っていること。**
**変更が契約のディレクトリと受け皿に限られること。**
**`~/bin/` と `~/.zshrc` は版管理の外なので、ここには現れない。**

- [ ] **Step 5: commit し、送出する**

    git add tasks/T-2026-08-24-andrew-keeper-autosync/ tasks/inbox.d/T-2026-08-24-andrew-keeper-autosync.md
    git commit -m "feat(sync): deploy keeper and enable git autosync on andrew"
    git --no-pager log -1 --format='%h %s'
    git remote -v
    git push -u origin HEAD
    git --no-pager status -sb

**送出側が `git@` で始まるなら、配備鍵が要る形である。鍵は消えている。**

    git remote set-url --push origin https://github.com/takuya3h/m2.git

**`gh` の補助が要る場合がある。**

    gh auth setup-git

    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

- [ ] **Step 6: 抑止を外す**

**ここで初めて版管理の自動同期が有効になる。**

    cd ~/slocal2/m2
    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-24-andrew-keeper-autosync 2>/dev/null
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

**外したあと、次の周回で自動の統合と送出が起きうる。** それは正常である。

| # | 完了判定 |
|---|---|
| 14 | 13 項目すべてに実測値または UNKNOWN がある |
| 15 | 送信前の秘匿検査を自分で行った（陽性対照つき） |
| 16 | 開始時の未追跡がすべて残っている |
| 17 | 変更が契約の範囲に限られる（生成物を再生成していない） |
| 18 | 分岐が送出され、PR が存在する（番号） |
| 19 | 抑止が repo 直下から消えている |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **中継が立った** | **停止して報告。** 目印が無いのに立つなら実装の理解が誤り |
| **同期処理が起動した** | **記録して報告。** 止めるかは次の判断 |
| 常駐処理が二件以上になった | 錠の働きを確かめる。**片方が終わるはずである** |
| 常駐処理が起動直後に落ちる | 構文と権限を確かめる。**記録を探して原因を書く** |
| 記録の置き場所が無い | **正本を読んでどこへ書くかを確かめる。** 無ければ `UNKNOWN` |
| 抑止が効いていない版だった | **記録して報告。** 自動の統合が起きうる |
| 生成物の検査が差分を報告した | **再生成しない。記録するだけ**（禁止 4） |
| 未追跡が減った | **停止して報告。** 版管理外の成果物を失っている |
| 送出できない | 送出側の経路と `gh` の状態を記録して報告する |
| 起動行が既に在った | **追記しない。** 記録して次へ進む |

**言い訳をしない。事実と、測れなかったことを書く。**

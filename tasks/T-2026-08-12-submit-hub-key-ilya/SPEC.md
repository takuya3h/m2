# 中継用の公開鍵を提出し、中心への到達住所を測る（ilya）

**task_id:** `T-2026-08-12-submit-hub-key-ilya`  **kind:** `impl`
**depends_on:** `T-2026-08-12-hub-from-marker`
**実行ホスト:** `ilya`  **repo:** `~/slocal2/m2`

## Goal

設定共有を **efros / lecun / bengio / andrew / ilya の五台**で復旧させる。中心は
**lecun**。前契約で、常駐処理の正本は**目印のファイル名から中心を導出する**形になった。

**残る障害は鍵である。** lecun が受け入れているのは efros と bengio と philip の三者で、
**andrew と ilya は入れない。** この二台を中心へ繋ぐには、**それぞれの公開鍵を
lecun の受け入れ一覧へ登録する**必要がある。

**鍵は新たに作らない。** 目印の一行目は「中継に使う秘密鍵の経路」であり、
このホストが既に持っている中継用の鍵がそのまま使える。**本契約はその鍵の
公開鍵を導出し、版管理へ提出する。秘密鍵はこのホストから出ない。**

あわせて、**目印の二行目に書く住所**を実測する。中心が他ノードからどの住所で見えるかは
中心自身では測れないため、**入る側から測るしかない。**

**登録するのは lecun 側の作業であり、本契約では行わない。** 次の契約で扱う。

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal2/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
    git branch --show-current
    git --no-pager status --porcelain

**二つ目が `0` なら抑止は効いていない**（続行してよいが報告に記す）。
**三つ目が `feat/` で始まらなければ分岐が作られていない。停止して報告する。**
四つ目について、**契約自身のディレクトリ `tasks/T-2026-08-12-submit-hub-key-ilya/` は `task-start` が
取り込んだものであり、未追跡で正常である。判定から除外する。**
それ以外の未追跡物があれば報告して停止する。

| # | 禁止 |
|---|---|
| 1 | **秘密鍵の中身を出力・記録・複製する**（公開鍵と指紋と経路名は可） |
| 2 | 鍵を生成・変更・削除する |
| 3 | **中継の目印を作る・消す・書き換える**（`~/.tunnel_to_*`） |
| 4 | `~/bin/**` を変更する。常駐処理を起動・停止・再起動する |
| 5 | **中継を張る、切る** |
| 6 | **他ホストへ書き込む。他ホストで `echo` 以外の命令を実行する** |
| 7 | 同期処理の設定を変更する。同期処理を起動・停止・再起動する |
| 8 | 装置を使う。統合する。自動統合を有効化する |
| 9 | 外部への送信を `make task-report` 以外の経路で行う |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `runindex/**` `context/auto/**` を手で編集する |
| 12 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

**禁止 1 が最重要である。** 本契約は鍵を扱うが、**版管理へ入れてよいのは公開鍵だけ**である。
公開鍵は秘匿ではないが、**どのノードがどこへ入れるかという構成情報は履歴に残る。**
それを承知のうえで進める。

**禁止 6 について。** 中心の到達性を測るが、**lecun で命令を実行してはならない。**
接続が拒まれることの確認までであり、**入れてしまった場合は記録して報告する。**

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

`inputs.data` は雛形の必須項目として残しているが、**本契約はデータも分割も参照しない。**

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | **対照は両方向で取る。期待値を実測前に一点へ固定しない** |
| 5 | 対象の一覧そのものが正しいかを確かめる。件数を必ず出力する |
| 6 | **終了コードを件数と呼ばない。** 数えるなら `grep -c`、走ったかを見るなら終了コード |
| 7 | 名前を決め打ちしない。先頭がドットのものを落とさない |
| 8 | 測定命令の副作用が禁止領域に触れないかを確かめる |
| 9 | 出力は要約せず `audit.md` へ貼る |

申し送り 6 は前契約の欠陥に対応する。`echo "count=$?"` と書いたが、
**`$?` は終了コードであって件数ではない。**

`成功命令 && echo "成功" || echo "失敗"` の形は、**表示側が失敗しても「失敗」が出る。**
**判定は別の命令で行う。**

**評価するシェルに注意する。** 対話シェルは bash ではないが、`keeper.sh` の先頭行は
別のシェルを指す。**実装を評価するなら、実装が指すシェルで行う**（前契約で
未一致の展開がエラーになった）。

### 確定した環境の事実（再測定は不要）

| 事実 | 実測値 |
|---|---|
| 中心 | **lecun**。SSH は `50072`、転送は `22001` から `22000` |
| lecun の受け入れ | efros / bengio / philip の三者。**このホストは入れない** |
| 目印の書式 | 一行目は秘密鍵の経路、二行目は中心の住所（任意）。**中心自身は目印を置かない** |
| 正本の状態 | 目印から中心を導出する形へ変更済み。**配置は未実施** |
| 五台の到達性 | 相互に SSH の口は開いている。**philip だけが経路なし** |
| プロセスの計数 | `ps` と `grep` による検索は自己一致する。`/proc/*/cmdline` を使う |
| 待ち受けの一覧 | `ss` `netstat` `lsof` `ip` はいずれも存在しない |

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 単語分割は
起きない。`git` を使う操作は `git --no-pager`。**山括弧は書かない。**
`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 中継用の鍵を特定し、公開鍵を導出する

**Files:** Create: `tasks/T-2026-08-12-submit-hub-key-ilya/audit.md`

**秘密鍵の中身は絶対に出さない。**

- [ ] **Step 1: 目印から中継用の鍵の経路を読む**

    ls -a ~/ | grep -i tunnel; echo "count=$(ls -a ~/ | grep -c -i tunnel)"
    for f in ~/.tunnel_to_*; do
      test -f "${f}" && echo "FILE ${f} size=$(wc -c < "${f}") lines=$(wc -l < "${f}")"
      test -f "${f}" && echo "LINE1=$(head -1 "${f}")"
    done

**一行目が秘密鍵の経路である。** 二行目があれば旧形式ではない。行数も記録する。

- [ ] **Step 2: その鍵が実在し、読めることを確かめる**

得られた経路を `KEY` に入れる。

    ls -la "${KEY}" 2>/dev/null || echo "鍵が実在しない"
    ls -la "${KEY}.pub" 2>/dev/null || echo "公開鍵の並置なし"

**鍵が実在しなければ停止して報告する。** 生成してはならない（禁止 2）。

- [ ] **Step 3: 公開鍵を導出し、指紋を測る**

    ssh-keygen -yf "${KEY}" < /dev/null > /tmp/pub_derived.txt 2>/tmp/pub_err.txt
    echo "derive_exit=$?"
    wc -c /tmp/pub_derived.txt; cat /tmp/pub_err.txt
    ssh-keygen -lf /tmp/pub_derived.txt

**導出に失敗する場合**（合言葉が要るなど）、`${KEY}.pub` が並置されていればそちらを使う。
**両方だめなら停止して報告する。** 合言葉を入力してはならない。

**指紋（`SHA256:` で始まる値）と公開鍵の本文は秘匿ではない。記録してよい。**
`-----BEGIN` で始まる行は**絶対に出さない。**

- [ ] **Step 4: 導出した公開鍵が、その秘密鍵に対応することを確かめる**

    ssh-keygen -lf /tmp/pub_derived.txt
    test -f "${KEY}.pub" && ssh-keygen -lf "${KEY}.pub" || echo "並置なし。比較できない"

**並置がある場合、指紋が一致すること。** 一致しなければどちらかが古い。記録して報告する。

**陽性対照**: 別の鍵から導出した公開鍵の指紋が**異なる値になる**ことを確かめる。
同じ値が返るなら導出が壊れている。

- [ ] **Step 5: 秘匿が混ざっていないことを確かめる**

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" tasks/T-2026-08-12-submit-hub-key-ilya/audit.md

**判定するのは件数ではなく形である。** 一致があれば一件ずつ実体を確かめる。

| 判定 | 扱い |
|---|---|
| 秘密鍵の書き出し行、語に区切りと値が続く形 | **削る** |
| 説明文・変数名・誤りの表示に語が現れただけ | **差し支えない。その旨を記す** |

**陽性対照**: 囮の行（`-----BEGIN OPENSSH PRIVATE KEY-----`）を含む一時ファイルに
同じ検査をかけ、**一以上を返すこと**を確かめる。囮は外部へ送らない。

| # | 完了判定 |
|---|---|
| 1 | 目印の件数・行数・一行目を記録した（変更していない） |
| 2 | 鍵の実在と権限を記録した |
| 3 | 公開鍵を導出し、指紋を記録した（秘密鍵の中身なし） |
| 4 | 導出した公開鍵が秘密鍵に対応することを確かめた（陽性対照つき） |
| 5 | 記録に秘密鍵の値が含まれない（値と名前を分けて判定） |

---

## Task 2 (Phase A): 中心への到達住所を測る

**Files:** Modify: `tasks/T-2026-08-12-submit-hub-key-ilya/audit.md`

**目印の二行目に書く値を決めるための測定である。**
**lecun で命令を実行してはならない**（禁止 6）。

- [ ] **Step 1: 中心の住所の候補を三つの出所から集める**

    grep -i -E "^Host |HostName|Port|IdentityFile" ~/.ssh/config 2>/dev/null
    grep -v "^#" /etc/hosts | grep -v "^$"
    grep -o "tcp://[0-9.]*:[0-9]*" ~/.local/state/syncthing/config.xml 2>/dev/null | sort -u

**候補の件数を必ず記録する。** どれが lecun かを名前から絞れない場合、
**すべてを候補として測る。**

- [ ] **Step 2: 候補ごとに SSH の口への到達性を測る**

    .venv/bin/python - <<'PY' > /tmp/reach.txt
    import socket
    targets = []   # Step 1 の結果から ADDR:PORT の組を並べる
    for spec in targets:
        h, _, p = spec.rpartition(":")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(6)
        try:
            s.connect((h, int(p))); r = "OPEN"
        except socket.timeout: r = "TIMEOUT"
        except ConnectionRefusedError: r = "REFUSED"
        except OSError as e: r = "OSERROR:" + (e.strerror or "?").replace(" ", "_")
        finally: s.close()
        print(spec, r)
    PY
    wc -l /tmp/reach.txt
    cat /tmp/reach.txt

**陽性対照**: 開いている先（自ホストの待ち受け）と、閉じている先と、経路の無い先を与え、
**結果が出し分けられること**を確かめる。**期待値を一点に固定しない。**
経路の無い先は時間切れにも即時の到達不能にもなりうる。**どちらも経路なしとして扱う。**

- [ ] **Step 3: どの住所が中心かを確定する**

`OPEN` になった住所のうち、**どれが lecun か**を判定する。

判定の材料は次のいずれかである。**使った材料を明記する。**

| 材料 | 内容 |
|---|---|
| 設定の別名 | `~/.ssh/config` に lecun のエントリがあり、住所を宣言している |
| 同期処理の登録 | `config.xml` の device 名と住所の対応 |
| 接続の応答 | SSH の版表示や鍵の指紋（**接続の確立までで、命令は実行しない**） |

**確定できない場合は候補を並べて `UNKNOWN` とする。推測で一つに決めない。**

- [ ] **Step 4: 現時点では認証が通らないことを記録する**

**これは段階を追う対照である。** 登録前は拒まれ、登録後は通るはずである。

    ssh -o BatchMode=yes -o ConnectTimeout=8 -o IdentitiesOnly=yes \
        -o UserKnownHostsFile=/tmp/kh_audit.txt -o StrictHostKeyChecking=accept-new \
        -p 50072 -i "${KEY}" LECUN_ADDR 'echo REACHABLE' 2>&1 | tail -2

**`UserKnownHostsFile` を必ず付ける**（付け忘れると `~/.ssh/known_hosts` へ追記され、
禁止に触れる）。**`IdentitiesOnly=yes` も必ず付ける。**

Expected: **拒まれる。** `REACHABLE` が返る場合、**既に登録されている**ということであり、
**その方が話は早い。記録して報告する**（異常ではない）。

- [ ] **Step 5: 測定前後で受け入れの控えが無変更であることを確かめる**

    ls -la ~/.ssh/known_hosts 2>/dev/null || echo "known_hosts なし"
    wc -c ~/.ssh/known_hosts 2>/dev/null
    wc -l /tmp/kh_audit.txt 2>/dev/null

**大きさと更新時刻が Task 1 の時点と一致すること。**

| # | 完了判定 |
|---|---|
| 6 | 住所の候補を三つの出所から集め件数を記録した |
| 7 | 到達性を測り、分類の合計が候補数と一致した（陽性対照つき） |
| 8 | **どの住所が中心かを確定した**（材料を明記。できなければ UNKNOWN） |
| 9 | 現時点の認証の可否を記録した（拒まれるのが期待だが、通っても異常ではない） |
| 10 | 測定前後で `known_hosts` が無変更（大きさと更新時刻） |

---

## Task 3 (Phase B): 公開鍵を版管理へ提出する

**Files:** Create: `scripts/sync/hub_keys/ilya.pub`

- [ ] **Step 1: 置き場所が既存の構造と衝突しないことを確かめる**

    ls -la scripts/sync/ 2>/dev/null
    ls -la scripts/sync/hub_keys/ 2>/dev/null || echo "ディレクトリなし。作る"
    git --no-pager log --oneline -3 -- scripts/sync/

**同名のファイルや、用途の異なるディレクトリが既にある場合は停止して報告する。**
起票者は repo の構造を完全には把握していない。

- [ ] **Step 2: 公開鍵を置く**

    mkdir -p scripts/sync/hub_keys
    cp /tmp/pub_derived.txt scripts/sync/hub_keys/ilya.pub
    wc -c scripts/sync/hub_keys/ilya.pub
    ssh-keygen -lf scripts/sync/hub_keys/ilya.pub

**指紋が Task 1 Step 3 と一致すること。** 一致しなければ取り違えている。

- [ ] **Step 3: 置いたものが公開鍵だけであることを確かめる**

    head -c 40 scripts/sync/hub_keys/ilya.pub; echo
    grep -c "PRIVATE" scripts/sync/hub_keys/ilya.pub
    wc -l scripts/sync/hub_keys/ilya.pub

Expected: 先頭が `ssh-` で始まる。`PRIVATE` の一致が **零**。行数が **一**。

**三つのうち一つでも外れたら停止して報告する。** 秘密鍵を版管理へ入れてはならない。

**陽性対照**: 秘密鍵の書き出しを模した一時ファイルに同じ検査をかけ、
**`PRIVATE` が一以上を返すこと**を確かめる。囮は版管理へ入れない。

- [ ] **Step 4: 次の契約で使う情報を書き出す**

`tasks/T-2026-08-12-submit-hub-key-ilya/handoff.md` に次を記す。

| 項目 | 内容 |
|---|---|
| 公開鍵の場所 | `scripts/sync/hub_keys/ilya.pub` |
| 指紋 | Task 1 で測った値 |
| 中心の住所 | Task 2 で確定した値（できなければ候補と UNKNOWN） |
| 目印の中身（案） | 一行目に秘密鍵の経路、二行目に住所 |
| 現時点の認証 | 拒まれた／通った |

**目印を実際に作ってはならない**（禁止 3）。**書き出すのは案だけである。**

| # | 完了判定 |
|---|---|
| 11 | 置き場所が既存の構造と衝突しないことを確かめた |
| 12 | 公開鍵を置き、指紋が Task 1 と一致した |
| 13 | 置いたものが公開鍵だけである（三つの検査と陽性対照） |
| 14 | 次の契約で使う情報を書き出した（目印は作っていない） |

---

## Task 4 (Phase C): 検証し、送出し、報告する

**Files:** Create: `tasks/T-2026-08-12-submit-hub-key-ilya/RESULT.md`, `tasks/T-2026-08-12-submit-hub-key-ilya/result.yaml`,
`tasks/inbox.d/T-2026-08-12-submit-hub-key-ilya.md`

- [ ] **Step 1: 完了判定 14 項目を一つの表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

- [ ] **Step 2: `conventions_rev` を実測して置換する**

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 3: 検証を通す**

    make task-validate TASK=T-2026-08-12-submit-hub-key-ilya; echo "validate_exit=$?"
    make task-preflight TASK=T-2026-08-12-submit-hub-key-ilya; echo "preflight_exit=$?"
    make forbidden-check; echo "forbidden_exit=$?"

- [ ] **Step 4: 触っていないものが無変更であることを確かめる**

    ls -la ~/.tunnel_to_* 2>/dev/null || echo "目印なし"
    wc -c ~/bin/keeper.sh 2>/dev/null
    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for word in ("ssh -N -L", "keeper.sh", "zzz_no_such_process"):
        n = 0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: c = open("/proc/%s/cmdline" % d, "rb").read().decode("utf-8","replace")
            except OSError: continue
            if word in c: n += 1
        print("%s=%d" % (word, n))
    PY

**目印と稼働版が Task 1 の時点と一致し、中継が増えていないこと。**

- [ ] **Step 5: 判断の受け皿へ置く**

`tasks/inbox.d/T-2026-08-12-submit-hub-key-ilya.md` に**起票者が次の判断に使える事実だけ**を置く。

- [ ] **Step 6: 変更範囲と未解決を行数で確かめる**

    git --no-pager status --porcelain > /tmp/wt.txt; wc -l /tmp/wt.txt; cat /tmp/wt.txt
    git --no-pager diff --name-only origin/phase0...HEAD > /tmp/ch.txt
    echo "changed=$(wc -l < /tmp/ch.txt)"; cat /tmp/ch.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un.txt
    echo "unmerged=$(wc -l < /tmp/un.txt)"; cat /tmp/un.txt

**変更が公開鍵一件と本契約のディレクトリと受け皿に限られること。**
最上位の指示が別のファイルの更新を要求する場合、**それに従い、理由を報告に記す。**

- [ ] **Step 7: commit する**

    git add scripts/sync/hub_keys/ilya.pub tasks/T-2026-08-12-submit-hub-key-ilya/ tasks/inbox.d/T-2026-08-12-submit-hub-key-ilya.md
    git commit -m "feat(sync): submit tunnel public key for ilya"
    git --no-pager log -1 --format='%h %s'

- [ ] **Step 8: 分岐を送出し、PR を作る**

    git fetch origin && git merge origin/phase0
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**上流が設定され `ahead` が零になったことを確認する。push は統合ではない**が、
**phase0 への取り込みは行わない。同じ head と base の PR は二本作れない。**
**先に一覧で確認し、存在すれば新規作成せず本文を更新する。番号と下書きの別を報告に書く。**

- [ ] **Step 9: 抑止を解除し、報告を台帳へ返す**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-submit-hub-key-ilya 2>/dev/null \
      && echo "released" || echo "解除に失敗。手当てが要る"
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"
    make task-report TASK=T-2026-08-12-submit-hub-key-ilya; echo "exit=$?"

| # | 完了判定 |
|---|---|
| 15 | 14 項目すべてに実測値または UNKNOWN がある（空欄なし） |
| 16 | 目印と稼働版が無変更で、中継が増えていない |
| 17 | 変更が公開鍵と契約の範囲に限られる |
| 18 | 分岐が送出されている（上流が設定され ahead が零） |
| 19 | PR が存在する（番号と下書きの別） |
| 20 | 抑止が repo 直下から消えている |
| 21 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| 中継の目印が無い、または鍵が実在しない | **停止して報告。** 生成してはならない |
| 公開鍵の導出に合言葉が要る | **停止して報告。** 入力してはならない。並置の公開鍵があればそれを使う |
| 導出した指紋が並置の公開鍵と食い違う | **記録して報告。** どちらかが古い |
| 置き場所が既存の構造と衝突する | **停止して報告。** 起票者が repo の構造を把握していない |
| 置いたものが公開鍵でない | **停止して報告。** 秘密鍵を版管理へ入れてはならない |
| **中心への認証が既に通った** | **記録して続行。** 登録済みということであり、次の契約が軽くなる |
| どの住所が中心か確定できない | **候補を並べて `UNKNOWN`。** 推測で一つに決めない |
| 中継の数が増えた、目印や稼働版が変わった | **停止して報告。** 元に戻そうとしない |
| 分岐が `feat/` で始まらない、抑止の解除に失敗した | **報告に明記する。** 自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

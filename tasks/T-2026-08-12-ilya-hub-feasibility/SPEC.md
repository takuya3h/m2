# ilya を中心に据えられるかの実測

**task_id:** `T-2026-08-12-ilya-hub-feasibility`  **kind:** `analysis`  **depends_on:** なし
**実行ホスト:** `ilya`  **repo:** `~/slocal2/m2`

## Goal

設定共有を **efros / lecun / bengio / andrew / ilya の五台**で復旧させることが目標になった。
中心に据えた一台（`philip`）への経路が失われたことが原因で、復旧は二週間以降である。

**ilya は事情が違う。** 過去に二度、**構内へ出られない**ことが実測されている。中継は
「各ノードが中心へ SSH して転送を張る」形なので、**出られないノードは中心以外になれない。**
逆に**中心は入られる側**であり、自分からは誰にも接続しない。
**したがって、この五台で組むなら ilya が中心になるしかない。**

本契約は**読み取りのみ**で、その可否を決める。

1. **誰が ilya へ入れるか**（受け入れ一覧の実測。**これが中心の要件そのもの**）
2. **入られる側として機能するか**（SSH の口、同期処理の待ち受け）
3. **今日も構内へ出られないか**（過去の実測が今も成り立つか）

**鍵の生成・配布・変更は一切行わない。中心の移設も行わない。判断はユーザーが行う。**

**過去の実測を前提にしない。** 「出られない」は 2026-08-07 と 08-08 の値であり、
本契約はそれを**今日の値で確かめ直す。** 食い違えば、それ自体が重要な発見である。

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal2/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
    git branch --show-current
    git --no-pager status --porcelain

**二つ目が `0` なら抑止は効いていない**（続行してよいが報告に記す）。
**三つ目が `feat/` で始まらなければ分岐が作られていない。停止して報告する。**
四つ目について、**契約自身のディレクトリ `tasks/T-2026-08-12-ilya-hub-feasibility/` は
`task-start` が取り込んだものであり、未追跡で正常である。判定から除外する。**
それ以外の未追跡物があれば報告して停止する。

**解除は最後の Task で行う。削除ではなく repo の外への移動を使う。**

| # | 禁止 |
|---|---|
| 1 | 鍵を生成・複製・配布・変更・削除する |
| 2 | `~/.ssh/**` `~/bin/**` `~/claude-sync/**` を変更する（読むのは可） |
| 3 | 秘密鍵の中身を出力・記録する（**指紋と経路名は可**） |
| 4 | 他ホストで `echo` 以外の命令を実行する。他ホストへ書き込む |
| 5 | 同期処理・常駐処理を起動・停止・再起動する。中継を張る、切る |
| 6 | 中心を移す。設定を書き換える |
| 7 | 装置を使う。統合する。自動統合を有効化する |
| 8 | 外部への送信を `make task-report` 以外の経路で行う |
| 9 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 10 | `runindex/**` `context/auto/**` を手で編集する |
| 11 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

禁止 2 は測定命令にも及ぶ。**`ssh` の初回接続は既定で `~/.ssh/known_hosts` へ追記する。**
Task 3 で指定する `UserKnownHostsFile` を必ず付けること。付け忘れると禁止に触れる。

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

`inputs.data` は雛形の必須項目として残しているが、**本契約はデータも分割も参照しない。**

### 起票者からの申し送り

前契約で起票者の誤りが十一件報告された。**そのうち五種を直したが、直し漏れがありうる。**
以下は全 Task に適用される。各 Step では再掲しない。

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | **検査が空振りでないことを確かめ、その対照が何を示し何を示さないかを分けて書く** |
| 5 | 対象の一覧そのものが正しいかを確かめる。件数を必ず出力する |
| 6 | 終了コードで判定する前に、その命令が本当に走ったかを確かめる |
| 7 | 名前を決め打ちしない。**先頭がドットのものを落とさない** |
| 8 | **測定命令の副作用が禁止領域に触れないかを確かめる** |
| 9 | 出力は要約せず `audit.md` へ貼る |

### 前契約で確定した環境の事実（再測定は不要）

| 事実 | 実測値 |
|---|---|
| プロセスの計数 | `ps` と `grep` による検索は自己一致する。`/proc/*/cmdline` を使う |
| 待ち受けの一覧 | `ss` `netstat` `lsof` `ip` はいずれも存在しない。`/proc/net/tcp` から復号する |
| 記録の位置 | `~/.syncthing.log` と `~/.tunnel.log`。**先頭がドットである** |
| 中心 | `philip`（`192.168.196.150`）。SSH は `50072`、転送は `22001` から `22000` |
| 共有相手の登録 | **全十一台が相互登録済み。中心を移しても同期処理側の設定変更は要らない** |
| 鍵の配布 | **対ごとである。共有鍵ではない。** 各ノードが持つのは中心宛の鍵だけ |

**`ilya` の `hostname` は `aolab` を返す**（`philip` も同じ値を返す）。
**契約の宣言と食い違っても、実測値を記録して続行する。** 切り分けを繰り返さない。

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 単語分割は
起きない。`git` を使う操作は `git --no-pager`。**山括弧は書かない**（リダイレクトとして
解釈される）。置き換える値は大文字の識別子で示す。
`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 誰が ilya へ入れるか

**Files:** Create: `tasks/T-2026-08-12-ilya-hub-feasibility/audit.md`

**これが中心の要件そのものである。** 中心には各ノードが SSH で入る。
**受け入れ一覧に無いノードは、中心にした時点で参加できない。**

**秘密鍵の中身は絶対に出さない。指紋と経路名だけを記録する。**

- [ ] **Step 1: 受け入れの一覧を集合として探す**

    for f in ~/.ssh/authorized_keys ~/.ssh/authorized_keys2; do
      test -f "${f}" && echo "FILE ${f} lines=$(grep -c -v '^\s*$' "${f}")"
    done
    ls -la ~/.ssh/authorized_keys* 2>/dev/null || echo "受け入れの一覧なし"
    grep -i -E "AuthorizedKeysFile|Port|PermitRootLogin|PubkeyAuthentication" \
      /etc/ssh/sshd_config 2>/dev/null || echo "設定を読めない（権限または不在）"

**零件でも「無い」と結論しない。** 別の場所を指す設定がありうる。
**`AuthorizedKeysFile` が既定と違う場所を指していれば、そちらを読む。**

- [ ] **Step 2: 登録されている鍵を、指紋と註釈の両方で読む**

    ssh-keygen -lf ~/.ssh/authorized_keys 2>/dev/null > /tmp/authfp.txt
    echo "count=$(wc -l < /tmp/authfp.txt)"
    cat /tmp/authfp.txt

**指紋の行末に註釈が出る。** 前契約では、この註釈が**どのノードの鍵かを直接示していた**
（`AtoB` や `ubuntu@HOSTNAME` の形）。**指紋のみ。鍵の本体は出さない。**

- [ ] **Step 3: 目標の四台それぞれについて、入れるかを判定する**

Step 2 の各行の註釈を読み、**次の四台それぞれについて可否を出す。**

| 送り出し側 | 判定 |
|---|---|
| efros | 註釈に該当があるか |
| lecun | 同上 |
| bengio | 同上 |
| andrew | 同上 |

**該当が無ければ「登録が要る」である。** 四台のうち何台が既に入れるかを記録する。
**これが「中心にするための追加作業の量」を決める。**

**註釈が同じ文字列の複数ノードを指しうる場合、指紋だけでは判別できない。**
`aolab` のように複数ホストが同じ値を返すものは、**`UNKNOWN` とする。推測で埋めない。**

- [ ] **Step 4: 手元の鍵と中継の目印を列挙する**

    ls -a ~/ | grep -i tunnel; echo "count=$(ls -a ~/ | grep -c -i tunnel)"
    ls -la ~/.ssh/ 2>/dev/null

**中心になるノードは自分へトンネルを張る必要がない。** 目印があれば、
**中心にする際にその扱いを決める必要がある**ことを記録する。**本契約では変更しない。**

- [ ] **Step 5: 秘匿が混ざっていないことを確かめる**

    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" tasks/T-2026-08-12-ilya-hub-feasibility/audit.md

**判定するのは件数ではなく形である。** 一致があれば一件ずつ実体を確かめる。

| 判定 | 扱い |
|---|---|
| 鍵の書き出し行、長い基数六十四の塊、語に区切りと値が続く形 | **削る** |
| 説明文・変数名・誤りの表示に語が現れただけ | **差し支えない。その旨を記す** |

**陽性対照**: 囮の行（`-----BEGIN OPENSSH PRIVATE KEY-----`）を含む一時ファイルに
同じ検査をかけ、**一以上を返すこと**を確かめる。囮は外部へ送らない。

| # | 完了判定 |
|---|---|
| 1 | 受け入れの一覧を集合として探した（場所と行数、設定の指す場所） |
| 2 | 登録されている鍵を指紋と註釈で記録した（件数） |
| 3 | **四台それぞれについて入れるかを判定した**（判別できないものは UNKNOWN） |
| 4 | 手元の鍵と中継の目印を記録した（件数） |
| 5 | 記録に鍵の値が含まれない（値と名前を分けて判定し、陽性対照つき） |

---

## Task 2 (Phase A): 入られる側として機能するか

**Files:** Modify: `tasks/T-2026-08-12-ilya-hub-feasibility/audit.md`

中心には各ノードが SSH で入り、**その先の局所の同期処理へ転送する。**
よって**二つの待ち受けが要る。**

- [ ] **Step 1: 待ち受けを復号する**

`ss` も `netstat` も `lsof` も無いことは確定している。

    .venv/bin/python - <<'PY' > /tmp/listen.txt
    ports = set()
    for p in ("/proc/net/tcp", "/proc/net/tcp6"):
        try: lines = open(p, encoding="utf-8").read().splitlines()[1:]
        except OSError: continue
        for ln in lines:
            f = ln.split()
            if len(f) > 3 and f[3] == "0A":
                ports.add(int(f[1].split(":")[1], 16))
    print("listen_count=%d" % len(ports))
    print("ports=" + ",".join(str(x) for x in sorted(ports)))
    for q in (22, 50072, 22000, 22001, 8384):
        print("port_%d=%s" % (q, "LISTEN" if q in ports else "-"))
    PY
    cat /tmp/listen.txt

**`listen_count` が零なら復号に失敗している。零のまま先へ進まない。**

**陽性対照**: 上の復号を関数として、一時的に作った待ち受けが現れ、閉じると消えることを
確かめる。Expected: **`True` のあと `False`。** 外れたら復号が信用できない。停止する。

- [ ] **Step 2: SSH の口の番号を確かめる**

    grep -i -E "^Port|^ListenAddress" /etc/ssh/sshd_config 2>/dev/null || echo "設定を読めない"

中心へは `50072` で入る構成だが、**容器の内側では別の番号で待ち受け、外側で転送されている
可能性がある**（前契約で他ホストの内側は `22` だった）。**実測値を記録する。**
**自ホストが外からどの番号で見えるかは自分では測れない。`UNKNOWN` とする。**

- [ ] **Step 3: 同期処理が稼働し、局所で待ち受けているか**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for word in ("syncthing", "keeper.sh", "zzz_no_such_process"):
        n = 0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: c = open("/proc/%s/cmdline" % d, "rb").read().decode("utf-8","replace")
            except OSError: continue
            if word in c: n += 1
        print("%s=%d" % (word, n))
    PY

**自分と祖先を除いて数えている。** 存在しない語が零を返すことが対照である。
Step 1 の `port_22000` と併せて、**入ってきた転送の受け先が生きているか**を判定する。

- [ ] **Step 4: 自ホストの住所を測る**

    cat /proc/net/fib_trie 2>/dev/null | grep -B1 "32 host" | grep -v "^--" | head -40
    grep -v "^#" /etc/hosts | grep -v "^$"
    hostname

**住所は `/32 host` の行の「前」にある。** 向きに注意する。
**自ホストが他ノードからどの住所で見えるかは自分では測れない。`UNKNOWN` とする。**

| # | 完了判定 |
|---|---|
| 6 | 待ち受けを復号し、件数と対象の番号を記録した（陽性対照つき） |
| 7 | SSH の口の番号を記録した（外から見える番号は UNKNOWN） |
| 8 | 同期処理の稼働と局所の待ち受けを記録した（自己汚染しない計数） |
| 9 | 自ホストの住所を記録した（外から見える住所は UNKNOWN） |

---

## Task 3 (Phase B): 今日も構内へ出られないか

**Files:** Modify: `tasks/T-2026-08-12-ilya-hub-feasibility/audit.md`

**過去の実測（2026-08-07 と 08-08）を前提にしない。今日の値で確かめる。**
**出られないことは中心にする妨げにならない**が、**出られるなら選択肢が広がる。**

- [ ] **Step 1: 対象の一覧を三つの出所から集める**

    grep -i -E "^Host |HostName" ~/.ssh/config 2>/dev/null
    grep -v "^#" /etc/hosts | grep -v "^$"
    grep -o "tcp://[0-9.]*:[0-9]*" ~/.local/state/syncthing/config.xml 2>/dev/null | sort -u

**三つの和集合を対象とし件数を必ず記録する。** 既知の構成は十一台である。
**それより少なければ一覧が縮んでいる可能性を明記する。**
**目標の四台（efros / lecun / bengio / andrew）は必ず含める。**

- [ ] **Step 2: 到達性を測る（認証の前段階）**

    .venv/bin/python - <<'PY' > /tmp/reach.txt
    import socket, sys
    targets = []   # ここに ADDR:PORT の組を Step 1 の結果から並べる
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

**陽性対照**: 開いている先（自ホストの待ち受け）、閉じている先（同じ番号を閉じた後）、
経路の無い先（`192.0.2.1`）の三通りで、**`OPEN` / `REFUSED` / 経路なし**が
出し分けられることを確かめる。経路なしは `TIMEOUT` または
`OSERROR:Network_is_unreachable` とする（後者はカーネルが経路なしを即時に返す環境）。
**この三分類から外れたら以後の結論は信用できない。停止する。**

- [ ] **Step 3: 外向きの経路が生きているかを対比する**

    git --no-pager ls-remote origin -h refs/heads/phase0
    echo "exit=$?"

**構内へは届かないのに外へは届く**という非対称があれば明記する。
**外も落ちていれば、構内不通の切り分けができない。**

- [ ] **Step 4: 到達できた先があれば、認証も測る**

Step 2 で `OPEN` が一件でもあれば、その先について測る。

    ssh -o BatchMode=yes -o ConnectTimeout=8 -o IdentitiesOnly=yes \
        -o UserKnownHostsFile=/tmp/kh_audit.txt -o StrictHostKeyChecking=accept-new \
        -p 50072 -i KEYPATH ADDR 'echo REACHABLE' 2>&1 | tail -2

**`UserKnownHostsFile` を必ず付ける**（付け忘れると `~/.ssh/known_hosts` へ追記され、
禁止 2 に触れる）。**`IdentitiesOnly=yes` も必ず付ける。**

**`OPEN` が一件も無ければこの Step は実施しない。** その旨を記録する。

- [ ] **Step 5: 測定前後で受け入れの控えが無変更であることを確かめる**

    ls -la ~/.ssh/known_hosts 2>/dev/null || echo "known_hosts なし"
    wc -c ~/.ssh/known_hosts 2>/dev/null
    wc -l /tmp/kh_audit.txt 2>/dev/null

**大きさと更新時刻が Task 1 の時点と一致すること。**

| # | 完了判定 |
|---|---|
| 10 | 対象一覧を三つの出所から集め件数を記録した |
| 11 | 到達性を測り、三分類の合計が対象数と一致した（陽性対照つき） |
| 12 | **今日の値で構内への到達可否を確定した**（過去の実測との一致または食い違い） |
| 13 | 外向きの経路との対比を記録した |
| 14 | 測定前後で `known_hosts` が無変更（大きさと更新時刻） |

---

## Task 4 (Phase C): 全項目を検証し、送出し、報告する

**Files:** Create: `tasks/T-2026-08-12-ilya-hub-feasibility/RESULT.md`,
`tasks/T-2026-08-12-ilya-hub-feasibility/result.yaml`,
`tasks/inbox.d/T-2026-08-12-ilya-hub-feasibility.md`

- [ ] **Step 1: 完了判定 14 項目を一つの表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

**あわせて、中心の要件を満たすかを表にする。**

| 要件 | 実測 |
|---|---|
| efros / lecun / bengio / andrew が入れるか | 四台それぞれの可否 |
| SSH の口が待ち受けているか | 番号と有無 |
| 同期処理が局所で待ち受けているか | 有無 |
| 追加で登録が要る台数 | 四から入れる台数を引いた数 |

**「中心にすべきか」は書かない。** 要件を満たすかどうかだけを書く。判断はユーザーが行う。

- [ ] **Step 2: `conventions_rev` を実測して置換する**

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 3: 検証を通す**

    make task-validate TASK=T-2026-08-12-ilya-hub-feasibility; echo "validate_exit=$?"
    make task-preflight TASK=T-2026-08-12-ilya-hub-feasibility; echo "preflight_exit=$?"
    make forbidden-check; echo "forbidden_exit=$?"

- [ ] **Step 4: 判断の受け皿へ置く**

`tasks/inbox.d/T-2026-08-12-ilya-hub-feasibility.md` に**起票者が次の判断に使える事実だけ**を置く。

- [ ] **Step 5: 変更範囲と未解決を行数で確かめる**

    git --no-pager status --porcelain > /tmp/wt.txt; wc -l /tmp/wt.txt; cat /tmp/wt.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un.txt
    echo "unmerged=$(wc -l < /tmp/un.txt)"; cat /tmp/un.txt

**変更が本契約のディレクトリと受け皿と抑止の目印に限られること。**
最上位の指示が別のファイルの更新を要求する場合、**それに従い、理由を報告に記す。**

- [ ] **Step 6: commit する**

    git add tasks/T-2026-08-12-ilya-hub-feasibility/ tasks/inbox.d/T-2026-08-12-ilya-hub-feasibility.md
    git commit -m "docs(sync): measure hub feasibility on ilya"
    git --no-pager log -1 --format='%h %s'

- [ ] **Step 7: 分岐を送出し、PR を作る**

    git fetch origin && git merge origin/phase0
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**上流が設定され `ahead` が零になったことを確認する。push は統合ではない**が、
**phase0 への取り込みは行わない。同じ head と base の PR は二本作れない。**
**先に一覧で確認し、存在すれば新規作成せず本文を更新する。番号と下書きの別を報告に書く。**

**外向きの経路が落ちている場合、送出も報告もできない。** その場合は
**そこまでの記録を repo に残し、状況を明記して停止する。**

- [ ] **Step 8: 抑止を解除し、報告を台帳へ返す**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-ilya-hub-feasibility 2>/dev/null \
      && echo "released" || echo "解除に失敗。手当てが要る"
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"
    make task-report TASK=T-2026-08-12-ilya-hub-feasibility; echo "exit=$?"

| # | 完了判定 |
|---|---|
| 15 | 14 項目すべてに実測値または UNKNOWN がある（空欄なし） |
| 16 | 中心の要件を満たすかの表を記載した（判断は書かない） |
| 17 | 変更が契約の範囲に限られる（一覧を記載） |
| 18 | 分岐が送出されている（上流が設定され ahead が零） |
| 19 | PR が存在する（番号と下書きの別。既存を更新した場合はその旨） |
| 20 | 抑止が repo 直下から消えている |
| 21 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| 陽性対照が期待どおりでない | **停止して報告。** 測定系が信用できない |
| **構内へ出られた**（過去の実測と食い違う） | **記録して続行。** 選択肢が広がる重要な発見である |
| 受け入れ一覧が空、四台のいずれも入れない、同期処理が稼働していない、SSH の口が無い | **記録して続行。** 要件を満たさないという結果そのものが本契約の目的である。**起動も作成もしない** |
| 註釈から送り出し側を判別できない | **`UNKNOWN` とする。推測で埋めない** |
| 外向きの経路も落ちている | 記録を repo に残し、**送出できない旨を明記して停止する** |
| `hostname` が宣言と食い違う | **実測値を記録して続行。** 切り分けを繰り返さない |
| `known_hosts` が変わってしまった | **報告に明記する。** 元に戻そうとしない |
| 分岐が `feat/` で始まらない、抑止の解除に失敗した | **報告に明記する。** 自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

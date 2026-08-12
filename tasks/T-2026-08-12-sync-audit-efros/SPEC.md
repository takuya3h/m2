# 設定同期の停止に関する実測（efros）

**task_id:** `T-2026-08-12-sync-audit-efros`  **kind:** `analysis`  **depends_on:** なし
**実行ホスト:** `efros`  **repo:** `~/slocal/m2`

## Goal

設定共有ディレクトリの内容が、あるホストで変更しても他ホストへ渡らない状態が続いている。
記録上この同期は中心となる一台を経由する星型で組まれており、その中心は現在ハード側の
理由で停止し復旧は 2 週間以降とされている。**ただしこれは記録であって実測ではない。**

本契約は**読み取りのみ**で、測定系の健全性を先に担保したうえで、常駐処理が何を中心と
みなしているか、他ホストへ届くか届かないか、停止期間に何がどれだけ分岐したかを確定する。
**復旧操作は一切行わない。方針の判断はユーザーが行う。**

同じ内容の契約を複数ホストで並行実行している。**他ホストの結果は見えない前提で書き、
自ホストで測れないものは `UNKNOWN` とする。他ホストの値を推測で埋めない。**

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal/m2 && touch .sync-pause && ls -la .sync-pause

**解除は Task 6 で行う。削除ではなく repo の外への移動を使う**（削除が実行基盤に
拒否される環境があり、未追跡ファイルを残すと以後の自動追従を阻害するため）。

| # | 禁止 |
|---|---|
| 1 | 同期処理の設定を変更する。起動・停止・再起動する。中継の経路を張る、切る |
| 2 | `~/claude-sync/**` `~/bin/**` を変更する（読むのは可） |
| 3 | ファイルを手で複製して同期を代替する |
| 4 | 他ホストへ書き込む。他ホストで読み取り以外の命令を実行する |
| 5 | 資格情報・API キーの値を出力・記録する |
| 6 | 装置を使う。統合する。自動統合を有効化する |
| 7 | 外部への送信を `make task-report` 以外の経路で行う |
| 8 | 生成物を再生成する（`make context` `make taskindex` `make inbox` を実行しない） |
| 9 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 10 | `runindex/**` `context/auto/**` を手で編集する |
| 11 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

禁止 8 と 4 の理由。同じ生成物へ複数の契約が同時に書くと必ず衝突する。また他ホストで
同じ契約が並行して走っており、片方から書き込むともう片方の測定対象が動く。判断は受け皿
`tasks/inbox.d/T-2026-08-12-sync-audit-efros.md` へ置く。集約は後日まとめて行う。

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが繰り返し起きている。
**本 SPEC の検査も同型の誤りを含みうる。以下は全 Task に適用される。各 Step では再掲しない。**

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | 仕組みの挙動は実装を読んでから信じる。ログの意味を推測しない |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない。作ってから別命令で表示する |
| 4 | 検査が空振りでないことを陽性対照で確かめる |
| 5 | 対象の一覧そのものが正しいかを確かめる。件数を必ず出力する |
| 6 | 終了コードで判定する前に、その命令が本当に走ったかを確かめる |
| 7 | 探す対象の名前を決め打ちしない。集合として列挙してから絞る |
| 8 | 出力は要約せず `tasks/T-2026-08-12-sync-audit-efros/audit.md` へ貼る |

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 配列の添字に
よる終了コードの取得は使えず、単語分割も起きない。**頁送りが無いホストがある**ため履歴を
読む操作は `git --no-pager` を使う。**`pgrep -f` を使わない**（検索命令自身に一致して誤った
値を返す。過去 2 回発生）。`contract.conventions_rev` は起票者が現在の値を知り得ないため
**実行者が実測して置換する。これは逸脱ではなく手順であり `deviations` に書かない。**

---

## Task 1 (Phase A): 到達性を測る道具を作り、それが機能することを確かめる

**Files:** Create: `tasks/T-2026-08-12-sync-audit-efros/probe.py`, `tasks/T-2026-08-12-sync-audit-efros/audit.md`

- [ ] **Step 1: 到達性プローブを作る。** 拒否と経路なしを区別できることが要点。

    import socket, sys
    def probe(host, port, timeout=5.0):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, int(port))); return "OPEN"
        except socket.timeout: return "TIMEOUT"
        except ConnectionRefusedError: return "REFUSED"
        except OSError as e:
            return "OSERROR:" + (e.strerror or type(e).__name__).replace(" ", "_")
        finally: s.close()
    if __name__ == "__main__":
        for spec in sys.argv[1:]:
            h, _, p = spec.rpartition(":")
            print(spec + " " + probe(h, p))

- [ ] **Step 2: 陽性対照。「全部つながらない」が道具の欠陥でないことを先に示す。**

    .venv/bin/python - <<'PY'
    import socket, subprocess, sys
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1)
    port = srv.getsockname()[1]
    run = lambda t: subprocess.run([sys.executable, "tasks/T-2026-08-12-sync-audit-efros/probe.py", t],
                                   capture_output=True, text=True).stdout.strip()
    print("A_open   ", run("127.0.0.1:" + str(port)))
    srv.close()
    print("B_closed ", run("127.0.0.1:" + str(port)))
    print("C_noroute", run("192.0.2.1:22000"))
    PY

Expected: `A_open` が `OPEN`、`B_closed` が `REFUSED`、`C_noroute` が `TIMEOUT`。
**一つでも期待と違えば以後の到達性の結論は信用できない。停止して報告する（G1）。**

- [ ] **Step 3: 版管理側の経路が生きていることを確かめる（第二の陽性対照）**

    git --no-pager ls-remote origin -h refs/heads/phase0
    echo "exit=$?"

Expected: 参照が 1 行返り `exit=0`。**返らなければ外向きの通信全体が落ちており、
同期の問題と切り分けられない。停止して報告する（G1）。**
`audit.md` を作り、見出し「Task 1 測定系の健全性」の下に Step 2 と 3 の出力を貼る。

| # | 完了判定 |
|---|---|
| 1 | プローブが三通りを出し分けた（期待と実測の双方を記載） |
| 2 | 版管理側の経路が生きている（参照が返った） |

---

## Task 2 (Phase A): 常駐処理の実装を読む

**Files:** Modify: `tasks/T-2026-08-12-sync-audit-efros/audit.md`

**推測しない。実装を読む。中心となるホストの名前を決め打ちで探さない。**

- [ ] **Step 1: 常駐処理の稼働を数える**

    ls -la ~/bin/ 2>/dev/null; echo "exit=$?"
    ps -eo args | grep -c "[k]eeper.sh"
    ps -eo args | grep "[k]eeper.sh"

- [ ] **Step 2: 別の探し方でも同じ結論かを確かめる。食い違えば両方を記録する。**

    ps -eo pid,etime,args | grep -v grep | grep -i -E "keeper|syncthing|ssh -N"
    ls -la ~/.keeper.lock 2>/dev/null || echo "lock なし"

- [ ] **Step 3: 中心ホストの決め方を実装から読み、稼働中の実体と正本の差を測る。**
想定と違えば実装を正とする。差分は行数で判定する（終了コードは差があると 1 を返す）。

    test -f ~/bin/keeper.sh && wc -l ~/bin/keeper.sh
    grep -n -i -E "tunnel|hub|ssh |22000|22001|50072" ~/bin/keeper.sh
    git --no-pager diff --no-index -- scripts/sync/keeper.sh ~/bin/keeper.sh > /tmp/kd.txt 2>&1
    wc -l /tmp/kd.txt
    cat /tmp/kd.txt

- [ ] **Step 4: 中継の目印を集合として列挙する**

    ls -a ~/ | grep -i tunnel; echo "count=$(ls -a ~/ | grep -c -i tunnel)"
    echo "home_total=$(ls -a ~/ | wc -l)"

| # | 完了判定 |
|---|---|
| 3 | 常駐処理の稼働数を二通りで数えた（両方の結果を記載） |
| 4 | 中心ホストの決め方を実装から読んだ（該当行を引用） |
| 5 | 中継の目印を集合として列挙した（件数を記載） |

---

## Task 3 (Phase A): 同期処理の状態と設定を読む（秘匿を出さない）

**Files:** Modify: `tasks/T-2026-08-12-sync-audit-efros/audit.md`

- [ ] **Step 1: 同期処理と中継の稼働を数える。二行を二重起動と断定せず `ppid` で確かめる。**

    ps -eo pid,ppid,etime,args | grep "[s]yncthing" > /tmp/st.txt
    wc -l /tmp/st.txt
    cat /tmp/st.txt
    ps -eo args | grep -c "[s]sh .*-L"
    ps -eo args | grep "[s]sh .*-L"

- [ ] **Step 2: 待ち受けの一覧を取る。零行なら手段が無かったということ。**

    (ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null || echo "手段なし") > /tmp/listen.txt
    wc -l /tmp/listen.txt
    cat /tmp/listen.txt

- [ ] **Step 3: 中継の入口へ接続する。** ポートは Task 2 Step 3 で読んだ値を使う。

    .venv/bin/python tasks/T-2026-08-12-sync-audit-efros/probe.py 127.0.0.1:PORT

- [ ] **Step 4: 設定ファイルの場所を集合として探す**

    for d in ~/.config/syncthing ~/.local/state/syncthing ~/.syncthing; do
      test -d "${d}" && echo "FOUND ${d}" && ls -la "${d}"
    done
    ps -eo args | grep "[s]yncthing" | tr ' ' '\n' | grep -i -E "home|config" || echo "指定なし"

- [ ] **Step 5: 設定を構造として読む。** `config.xml` のパスを `CFG` に入れる。

    .venv/bin/python - "${CFG}" <<'PY' > /tmp/stcfg.txt 2>&1
    import sys, xml.etree.ElementTree as ET
    r = ET.parse(sys.argv[1]).getroot()
    devs = r.findall("device"); print("device_count=" + str(len(devs)))
    for d in devs:
        a = ",".join(x.text for x in d.findall("address") if x.text)
        print("device name=%s id7=%s paused=%s addrs=%s" %
              (d.get("name"), (d.get("id") or "")[:7], d.get("paused"), a))
    fs = r.findall("folder"); print("folder_count=" + str(len(fs)))
    for f in fs:
        sh = ",".join(x.get("id","")[:7] for x in f.findall("device"))
        print("folder id=%s path=%s paused=%s type=%s shared=%s" %
              (f.get("id"), f.get("path"), f.get("paused"), f.get("type"), sh))
    o = r.find("options")
    if o is not None:
        for k in ("globalAnnounceEnabled","localAnnounceEnabled","relaysEnabled","listenAddress"):
            print("option %s=%s" % (k, ",".join(e.text or "" for e in o.findall(k))))
    PY
    wc -l /tmp/stcfg.txt
    cat /tmp/stcfg.txt

**識別子は先頭 7 文字のみ。API キーは読まない。** `device_count` が零なら解析に
失敗している。**零のまま先へ進まない。**

- [ ] **Step 6: 秘匿が混ざっていないことを確かめる。** Expected: `0`。

    grep -c -i -E "apikey|password|token|secret" /tmp/stcfg.txt

| # | 完了判定 |
|---|---|
| 6 | 同期処理と中継の稼働状況を記録した（一覧と件数） |
| 7 | 中継の入口への接続結果を記録した（三分類のいずれか） |
| 8 | 共有相手と共有フォルダを記録した（件数） |
| 9 | 記録に秘匿の値が含まれない（検査が零） |

---

## Task 4 (Phase B): 到達可否を、拒否と経路なしに区別して測る

**Files:** Modify: `tasks/T-2026-08-12-sync-audit-efros/audit.md`

- [ ] **Step 1: 対象の一覧を三つの出所から集める**

    grep -i -E "^Host |HostName|Port" ~/.ssh/config 2>/dev/null
    echo "ssh_count=$(grep -c -i '^Host ' ~/.ssh/config 2>/dev/null || echo 0)"
    grep -v "^#" /etc/hosts | grep -v "^$"
    grep -o "tcp://[0-9.]*:[0-9]*" /tmp/stcfg.txt | sort -u

**三つの和集合を対象とし件数を必ず記録する。** 既知の構成は 11 台である。**それより少なければ
一覧が縮んでいる可能性を明記する。少ないことを理由に「他は存在しない」と結論しない。**

- [ ] **Step 2: 各アドレスへ二つのポートを測る。** 中継用と待受用の両方。
ポート番号は実装と設定から得た値を使う。記録から決め打ちしない。

    .venv/bin/python tasks/T-2026-08-12-sync-audit-efros/probe.py ADDR:PORTA ADDR:PORTB > /tmp/reach.txt
    wc -l /tmp/reach.txt
    cat /tmp/reach.txt

- [ ] **Step 3: 三分類で集計し、合計が対象数と一致することを確かめる**

    echo "OPEN=$(grep -c ' OPEN$' /tmp/reach.txt)"
    echo "REFUSED=$(grep -c ' REFUSED$' /tmp/reach.txt)"
    echo "TIMEOUT=$(grep -c ' TIMEOUT$' /tmp/reach.txt)"
    echo "OTHER=$(grep -c ' OSERROR' /tmp/reach.txt)"
    echo "total=$(wc -l < /tmp/reach.txt)"

**一致しなければ測り漏れている。** `REFUSED` は相手の機器までは届いていることを、
`TIMEOUT` と経路なしの誤りは経路が無いことを意味する。**この区別を記録に残す。**

- [ ] **Step 4: 版管理側との対比。** 同一構内へは届かないのに外へは届く、という
非対称があれば明記する。

| # | 完了判定 |
|---|---|
| 10 | 対象一覧を三つの出所から集め件数を記録した（件数と出所） |
| 11 | 全対象を測り合計が一致した（集計） |
| 12 | 拒否と経路なしを区別した（三分類） |

---

## Task 5 (Phase C): 設定共有の棚卸しと停止時期の推定

**Files:** Modify: `tasks/T-2026-08-12-sync-audit-efros/audit.md`, Create: `tasks/T-2026-08-12-sync-audit-efros/inventory.tsv`

**内容は記録しない。名前・大きさ・更新時刻・要約値のみ。**

- [ ] **Step 1: 総件数を先に測る。零件なら探し方の誤りを疑う。**

    test -d ~/claude-sync && echo "EXISTS" || echo "MISSING"
    find ~/claude-sync -type f 2>/dev/null | wc -l
    find ~/claude-sync -type l 2>/dev/null | wc -l

- [ ] **Step 2: 一覧に要約値を付ける**

    find ~/claude-sync -type f -not -path "*/.stfolder/*" -print0 \
      | xargs -0 -r stat -c "%n	%s	%Y" > /tmp/inv.tsv
    wc -l /tmp/inv.tsv
    .venv/bin/python - <<'PY' > tasks/T-2026-08-12-sync-audit-efros/inventory.tsv
    import hashlib, pathlib, datetime
    base = pathlib.Path.home() / "claude-sync"
    for line in open("/tmp/inv.tsv", encoding="utf-8"):
        name, size, mt = line.rstrip("\n").split("\t")
        p = pathlib.Path(name)
        try: h = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        except Exception as e: h = "ERR:" + type(e).__name__
        ts = datetime.datetime.utcfromtimestamp(int(mt)).isoformat()
        print("\t".join([str(p.relative_to(base)), size, ts, h]))
    PY
    wc -l tasks/T-2026-08-12-sync-audit-efros/inventory.tsv

**この一覧は他ホストの同名ファイルと突き合わせるためのものである。**

- [ ] **Step 3: 秘匿が混ざっていないことを確かめる。** Expected: `0`。
ファイル名に該当語がある場合はその行を残しつつ、一覧が名前と要約値のみで
内容を含まないことを明記する。

    grep -c -i -E "apikey|password|token|secret|PRIVATE KEY" tasks/T-2026-08-12-sync-audit-efros/inventory.tsv

- [ ] **Step 4: 復旧時に消えうるものと更新時刻の分布を記録する**

    find ~/claude-sync -type d -name ".stversions" 2>/dev/null | wc -l
    find ~/claude-sync -name "*.sync-conflict-*" 2>/dev/null | wc -l
    sort -t"	" -k3 tasks/T-2026-08-12-sync-audit-efros/inventory.tsv > /tmp/sorted.tsv
    head -3 /tmp/sorted.tsv
    tail -5 /tmp/sorted.tsv

- [ ] **Step 5: 停止時期を二つの独立した情報から推定する。**
常駐処理の記録は中断時のみ書かれる。**行の有無だけで結論しない。** Step 4 の更新時刻
分布と突き合わせ、**整合するか食い違うかを述べる。食い違う場合は両方を記録し、
どちらが正しいかを断定しない。** 同期処理のログが別の場所にあれば場所も記録する。

    test -f ~/claude-sync/sync-alerts.log && wc -l ~/claude-sync/sync-alerts.log
    tail -20 ~/claude-sync/sync-alerts.log 2>/dev/null
    find ~ -maxdepth 3 -name "syncthing*.log" 2>/dev/null

| # | 完了判定 |
|---|---|
| 13 | 設定共有の件数を記録した（零でないこと、または不在の明示） |
| 14 | 一覧に内容が含まれない（検査が零または理由を明記） |
| 15 | 退避と衝突の痕跡を数えた（件数） |
| 16 | 停止時期を二つの独立した情報から推定した（整合または食い違い） |

---

## Task 6 (Phase D): 全項目を検証し、報告する

**Files:** Create: `tasks/T-2026-08-12-sync-audit-efros/RESULT.md`, `tasks/T-2026-08-12-sync-audit-efros/result.yaml`,
`tasks/inbox.d/T-2026-08-12-sync-audit-efros.md`

- [ ] **Step 1: 完了判定 16 項目を一つの表にまとめ、各項目に実測値または `UNKNOWN` を記す。**
**「実施した」ではなく「何が出たか」を書く。**

- [ ] **Step 2: `conventions_rev` を実測して置換する。** 逸脱ではなく手順である。

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 3: 検証を通す。** `make` 経由の終了コードはレシピ失敗時に `2` になる。
単体の値と食い違っても異常と断定しない。両方を記録する。

    make task-validate TASK=T-2026-08-12-sync-audit-efros; echo "validate_exit=$?"
    make task-preflight TASK=T-2026-08-12-sync-audit-efros; echo "preflight_exit=$?"

- [ ] **Step 4: 判断の受け皿へ置く。** `tasks/inbox.d/T-2026-08-12-sync-audit-efros.md` に
**起票者が次の判断に使える事実だけ**を置く。**復旧方針の提案は書かない。**

- [ ] **Step 5: 変更が契約の範囲に限られること、未解決が無いことを行数で確かめる。**
`make forbidden-check` が無ければその旨を記録し、下の二つで代替する。
**変更が本契約のディレクトリと受け皿と抑止の目印だけであること。**
それ以外があれば停止して報告する。

    make forbidden-check; echo "exit=$?"
    git --no-pager status --porcelain > /tmp/wt.txt; wc -l /tmp/wt.txt; cat /tmp/wt.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un.txt
    echo "unmerged=$(wc -l < /tmp/un.txt)"; cat /tmp/un.txt

- [ ] **Step 6: commit する**

    git add tasks/T-2026-08-12-sync-audit-efros/ tasks/inbox.d/T-2026-08-12-sync-audit-efros.md
    git commit -m "docs(sync): audit sync topology and divergence on efros"
    git --no-pager log -1 --format='%h %s'

- [ ] **Step 7: 抑止を解除する（削除ではなく移動）**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-sync-audit-efros 2>/dev/null \
      && echo "released" || echo "解除に失敗。手当てが要る"
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

- [ ] **Step 8: 報告を台帳へ返す**

    make task-report TASK=T-2026-08-12-sync-audit-efros; echo "exit=$?"

| # | 完了判定 |
|---|---|
| 17 | 16 項目すべてに実測値または UNKNOWN がある（空欄なし） |
| 18 | 作業ツリーの変更が契約の範囲に限られる（一覧を記載） |
| 19 | 抑止が repo 直下から消えている |
| 20 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| 陽性対照が期待どおりでない、または版管理側の経路も落ちている | **停止して報告**（G1）。測定系が信用できず、同期の問題と切り分けられない |
| 中心ホストが記録と違う名前だった | 実装を正とし `audit.md` に明記して続行 |
| 中心ホストへ到達できてしまった | **停止して報告**。原因の見立てが崩れる |
| 設定共有が存在しない、または同期処理が稼働していない | 記録して続行。**起動も作成もしない** |
| 測定中に相手が応答し始めた | 時刻とともに記録する。**復旧したと断定しない** |
| 変更しなければ測れない項目が生じた | **測らずに `UNKNOWN` とする。** 読み取り専用である |
| 抑止の解除に失敗した | 残っている場所を報告に明記する。自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

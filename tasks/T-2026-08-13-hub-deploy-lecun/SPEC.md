# lecun への正本 keeper の配置と再起動（五台構成の中心化）

**task_id:** `T-2026-08-13-hub-deploy-lecun`  **kind:** `impl`  **depends_on:** `T-2026-08-13-hub-role-and-restart`
**実行ホスト:** `lecun`  **repo:** `~/slocal2/m2`

## Goal

前契約（analysis）で、配置順序は lecun 先行、その後に一般ノードを一台ずつと確定した。
本契約は **lecun 一台だけ**を対象に、稼働中の旧 keeper を正本の新版へ置き換え、
旧常駐と旧 SSH 中継を**数値 PID 限定**で止め、新版を明示起動する。

前契約で確定したとおり、**配置だけ・目印だけ・再起動だけでは切替は完了しない。**
旧 SSH 中継が残ると、正本の接続先を区別しない判定が成立して新しい中継系の動作を
抑止しうる。よって手順は「事前記録 → 控え → 配置 → 旧の停止 → 明示起動 → 確認」の
順で行い、各段に判定を置く。

**正は `tasks/T-2026-08-13-hub-role-and-restart/handoff.md` である。**
本 SPEC と食い違う箇所があれば **handoff に従い、食い違いを記録する。**
一般ノードの切替（canary）は本契約に含まない。

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal2/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
    git branch --show-current

二つ目の値が `0` なら抑止は効いていない。その場合も続行してよいが、報告に記す。
**作業分岐が `feat/` で始まらなければ停止して報告する。**
解除は最後の Task で行う。**削除ではなく repo の外への移動を使う。**

| # | 禁止 |
|---|---|
| 1 | `~/bin` のうち `keeper.sh` **以外**を変更する（`keeper.sh` の置換と控えの作成は本契約の目的であり可） |
| 2 | `~/.ssh/**` `~/claude-sync/**` を変更する（読むのは可。ssh コマンド自体を実行しない） |
| 3 | 正本 `scripts/sync/keeper.sh` `scripts/sync/m2-sync.sh` を変更する |
| 4 | 中心の目印を変更・削除・移動する（読み取りと要約値の記録は可） |
| 5 | 数値 PID 以外の方法で停止の信号を送る（名前一致の一括停止・パターン停止を使わない） |
| 6 | 他ホストで命令を実行する。他ホストへ書き込む |
| 7 | 同期処理（Syncthing）を停止・再起動する（**keeper の停止と起動は本契約の目的であり可**） |
| 8 | 資格情報の値を出力・記録する |
| 9 | 未測定の値を書く。未測定は `UNKNOWN` |
| 10 | 統合する。自動統合を有効化する（**分岐の送出 push と PR の作成は含まない。必ず行う**） |
| 11 | 外部への送信を `make task-report` 以外の経路で行う |
| 12 | `runindex/**` `context/auto/**` を手で編集する（**生成は可。Task 1 の再生成は手順である**） |
| 13 | 装置（GPU）を使う |
| 14 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

**本契約の書き込み副作用は次に限る**: `~/bin/keeper.sh` の置換、`~/m2-archive/` 配下への
控えの作成、数値 PID への TERM、新版の明示起動（とその起動行が指す記録先への追記）、
repo 内の契約ディレクトリと受け皿と生成物。**ssh は一度も実行しない**ため
`~/.ssh/known_hosts` への副作用は生じない。中継の確認はすべて `/proc` の読み取りで行う。

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**
**新版 keeper が起動後に自ら行う書き込み（記録・自己更新・同期実行）も逸脱ではない。**

`inputs.data` は雛形の必須項目として残しているが、本契約はいずれの Task でも
データも分割も参照しない。参照しなかったことを記録する。

### 起票者からの申し送り

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | 仕組みの挙動は実装と handoff を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない。作ってから別命令で表示する |
| 4 | 検査が空振りでないことを陽性対照で確かめる |
| 5 | 終了コードで判定する前に、その命令が本当に走ったかを確かめる |
| 6 | `git` を使う操作は `git --no-pager` を付ける |
| 7 | 変数の直後に記号が続く場合は波括弧で囲む（対話シェルは bash ではない） |
| 8 | 報告に基本多言語面の外の文字を使わない。四十桁の十六進を書かない（履歴は短縮形） |
| 9 | 出力は要約せず `tasks/T-2026-08-13-hub-deploy-lecun/deploy.md` へ貼る |

`contract.conventions_rev` は実行者が実測して置換する。逸脱ではなく手順であり
`deviations` に書かない。

### 前契約で確定した環境の事実（再測定は不要）

| 事実 | 実測値 |
|---|---|
| プロセスの計数 | `/proc/*/cmdline` を読み自分と祖先を除く。名前一致の検索命令は自己一致する |
| 待ち受けの一覧 | `ss` `netstat` `lsof` は不在。`/proc/net/tcp` と `/proc/net/tcp6` から復号する |
| 稼働 keeper と正本の差 | 全文差分四十七行。稼働は目印分岐を持たない旧版である |
| m2-sync | 稼働版と正本は同一。中継への依存なし（陽性対照つきで確定） |
| 中心で必要な処理 | 死活監視・自己更新・反映・実行は目印分岐の外にあり中心でも必要。不要は SSH 中継のみ |
| 起動経路 | 自動起動の記述は `~/.zshrc` の一行のみ。systemd・cron 等に該当なし（七出所を全文検索済み） |
| 施錠 | 旧 keeper が書き込みの flock を保持。非待機の probe は exit 1 |
| 目印 | lecun に一件存在。本契約では変更しない |
| P9 の `host_mismatch` | 大文字小文字による既知の偽陽性。切り分けを繰り返さない |
| lecun 固有 | 試験二件の失敗は lecun では起きない（正本ホスト）。`rm` 拒否の既知事象は efros |

---

## Task 1 (Phase A): 起動確認と、併合後の投影の再生成

**Files:** Modify: `context/auto/tasks_summary.csv` ほか生成物, `tasks/inbox.md`

前契約は禁止により再生成を行っていない。併合直後の生成物は検査が落ちる状態である。
**手で編集せず、必ず生成で直す。**

- [ ] **Step 1: 再生成して検査を通し、commit する**

    make taskindex && make inbox
    make taskindex-check; echo "ti_exit=$?"
    make inbox-check; echo "ib_exit=$?"
    git add context/auto/ tasks/inbox.md
    git commit -m "chore(context): regenerate projections after hub analysis merge"
    git --no-pager log -1 --format='%h %s'

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 1 | 投影の検査が通る | ti と ib の exit がともに 0 | 再生成**前**に同じ検査を実行し、落ちる（非零）ことを先に記録した |
| 2 | 生成物だけが変わった | status に生成物と本契約の範囲外が無い | `git --no-pager status --porcelain` の全行を deploy.md へ貼り一件ずつ確認 |

---

## Task 2 (Phase A): handoff を読み、事前記録を取る

**Files:** Create: `tasks/T-2026-08-13-hub-deploy-lecun/deploy.md`

- [ ] **Step 1: handoff と失敗様式を全文読む**

    wc -l tasks/T-2026-08-13-hub-role-and-restart/handoff.md
    cat tasks/T-2026-08-13-hub-role-and-restart/handoff.md
    grep -n "様式" tasks/T-2026-08-13-hub-role-and-restart/audit.md

handoff の「中心用」手順・八確認・rollback を deploy.md へ要点転記する。
**本 SPEC と食い違う箇所を列挙し、食い違いは handoff に従うと明記する。**
以降の手順で使う実値（目印の場所 MARKER_PATH、施錠の場所 LOCK_PATH、起動行の形）を
handoff から読んで控える。

- [ ] **Step 2: 三者の要約値と行数を測る**

    sha256sum ~/bin/keeper.sh scripts/sync/keeper.sh
    wc -l ~/bin/keeper.sh scripts/sync/keeper.sh
    sha256sum ~/bin/m2-sync.sh scripts/sync/m2-sync.sh

- [ ] **Step 3: 稼働状態を記録する（/proc 走査。ssh は実行しない）**

    .venv/bin/python - <<'PY' > /tmp/procscan_before.txt
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try:
            p = int(open("/proc/%d/stat" % p).read().split(") ", 1)[1].split()[1])
        except Exception:
            break
    words = ("keeper.sh", "m2-sync.sh", "syncthing", "22001", "zzz_no_such_process")
    for w in words:
        hits = []
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me:
                continue
            try:
                c = open("/proc/%s/cmdline" % d, "rb").read().decode("utf-8", "replace")
            except OSError:
                continue
            if w in c:
                hits.append(d)
        print("%s count=%d pids=%s" % (w, len(hits), ",".join(hits)))
    PY
    cat /tmp/procscan_before.txt

`keeper.sh` の PID を OLD_PID として控える（OLD_PID は上の出力で読んだ数値）。
`22001` に一致する PID があれば旧中継として RELAY_PID に控える。零件なら零件と記録する。

- [ ] **Step 4: 施錠・待ち受け・目印・起動行を記録する**

    ls -la LOCK_PATH   # LOCK_PATH は Step 1 で handoff から読んだ施錠の場所
    sha256sum MARKER_PATH && ls -la MARKER_PATH   # MARKER_PATH も handoff から読んだ場所
    grep -n "keeper" ~/.zshrc
    .venv/bin/python - <<'PY'
    def rows(p):
        out = []
        try:
            lines = open(p, encoding="utf-8").read().splitlines()[1:]
        except OSError:
            return out
        for ln in lines:
            f = ln.split()
            if f[3] != "0A":
                continue
            out.append(int(f[1].split(":")[1], 16))
        return out
    ports = sorted(set(rows("/proc/net/tcp") + rows("/proc/net/tcp6")))
    for p in (22000, 8384):
        print("port_%d=%s" % (p, "LISTEN" if p in ports else "-"))
    print("listen_count=%d" % len(ports))
    PY

`~/.zshrc` の起動行（行番号と全文）を deploy.md へ写す。Task 5 で同じ形を使う。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 3 | handoff を全文読んだ | 行数と要点転記、食い違いの列挙（零件でも明記） | 八確認と rollback の項目数を数えて転記と突き合わせた |
| 4 | 三者の要約値 | 稼働版と正本の値が**異なる**（差分四十七行の前提と整合） | 同一ファイル同士の照合が一致を返す対照を併記 |
| 5 | 旧 keeper の特定 | count=1 と数値 PID。不存在語の対照が 0 | `/proc/OLD_PID/cmdline` を直接読み keeper.sh を含むことを確認 |
| 6 | 施錠・待ち受け・目印 | 施錠あり・22000 と 8384 が LISTEN・目印一件 | listen_count が零でない。目印の要約値が前契約の記録と一致 |
| 7 | 起動行 | 行番号つきで一行を特定 | `~/.zshrc` 全体の keeper 一致件数を出し一件であることを確認 |

---

## Task 3 (Phase B): 控えを作り、新版を配置する

**Files:** Create: `~/m2-archive/20260813-hub-deploy/keeper.sh.pre`  Modify: `~/bin/keeper.sh`

- [ ] **Step 1: 控えを作り、完全性を照合する**

    mkdir -p ~/m2-archive/20260813-hub-deploy
    cp ~/bin/keeper.sh ~/m2-archive/20260813-hub-deploy/keeper.sh.pre
    sha256sum ~/bin/keeper.sh ~/m2-archive/20260813-hub-deploy/keeper.sh.pre

二つの値が一致しなければ**停止**。控えが壊れたまま先へ進まない。

- [ ] **Step 2: 正本を配置し、双方向で照合する**

    cp scripts/sync/keeper.sh ~/bin/keeper.sh
    sha256sum scripts/sync/keeper.sh ~/bin/keeper.sh
    wc -l scripts/sync/keeper.sh ~/bin/keeper.sh
    ls -la ~/bin/keeper.sh   # 実行権を確認する。無ければ chmod +x ~/bin/keeper.sh

**注意: この時点では旧プロセスが旧版の本文を FD で保持したまま動き続けている**
（前契約で自己再実行なしと確定済み）。慌てず Task 4 で止める。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 8 | 控えの完全性 | 稼働版と控えの要約値が一致 | 控えと**正本**の照合が不一致を返すことを併記（差分器の対照） |
| 9 | 配置の成立 | 稼働場所と正本の要約値・行数が一致 | 配置**前**の稼働場所の値（Task 2）と異なることを確認（同版なら配置が空振り。記録して G2 で報告） |
| 10 | 実行権 | 実行可能 | ls の属性欄を deploy.md へ貼付 |

---

## Task 4 (Phase C): 旧常駐と旧中継を数値 PID 限定で止める

**Files:** Modify: `tasks/T-2026-08-13-hub-deploy-lecun/deploy.md`

- [ ] **Step 1: 停止してよい状態かを確かめる**

Task 2 Step 3 と**同じ走査を再実行**し、`m2-sync.sh` の count を読む。
零でなければ**零になるまで待ってから**次へ進む（同期の途中で親を落とさない）。
三十分待っても零にならなければ中断して報告する。

- [ ] **Step 2: 旧 keeper へ TERM を送り、消滅を確かめる**

    kill -TERM OLD_PID   # OLD_PID は Task 2 で /proc から読んだ数値。名前では送らない
    sleep 3
    test -d /proc/OLD_PID && echo "still_alive" || echo "gone"
    cat /proc/OLD_PID/cmdline 2>/dev/null || echo "cmdline_gone"

`still_alive` の場合は十秒待って再確認。それでも残るなら**中断して報告**（強い信号は
起票者へ判断を仰ぐ。escalate）。

- [ ] **Step 3: 旧中継と残存子孫を数値 PID で止める**

Task 2 の走査で `22001` に一致した RELAY_PID があれば同じ形で TERM し消滅を確認する。
零件だった場合は**零件だったことを再走査で確かめて**記録し、続行する。
keeper.sh の再走査で残存（子孫の sleep 等）が出れば、その数値 PID にも TERM を送る。

- [ ] **Step 4: 施錠の解放を確かめる**

`flock` コマンドの存在は未確認のため、非待機の probe は次で行う（handoff に別法の
指定があればそちらに従う）。

    .venv/bin/python - <<'PY'
    import fcntl, sys
    try:
        f = open("LOCK_PATH", "a")  # LOCK_PATH は Task 2 で handoff から読んだ場所に置換
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("lock_free")
        fcntl.flock(f, fcntl.LOCK_UN)
    except OSError:
        print("lock_still_held")
    PY

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 11 | 停止前の安全 | m2sync_running=0 | 同じ走査が keeper.sh を一件返す（走査自体が生きている対照） |
| 12 | 旧 keeper の消滅 | /proc/OLD_PID が不在 | 存在する別 PID（syncthing）で同じ test が存在を返すことを併記 |
| 13 | 旧中継の扱い | TERM 済みまたは零件の再確認 | 零件の場合、`/proc/net/tcp` に 22001 の LISTEN が無いことでも突き合わせた |
| 14 | 施錠の解放 | lock_free | 停止**前**に同じ probe が失敗していた（Task 2 の記録と対にする） |

---

## Task 5 (Phase C): 新版を明示起動する

**Files:** Modify: `tasks/T-2026-08-13-hub-deploy-lecun/deploy.md`

- [ ] **Step 1: 記録済みの起動行と同じ形で起動する**

Task 2 Step 4 で写した `~/.zshrc` の行と**同じコマンド・同じリダイレクト先**で
`~/bin/keeper.sh` を nohup 起動する。行の形を変えない。起動直後に新 PID を控える。

    実行するのは Task 2 で記録した起動行そのものである（ここに書き写さないのは
    起票者が現物を知り得ないためで、決め打ちを避ける）。
    sleep 3

- [ ] **Step 2: 新版の稼働を確かめる**

Task 2 Step 3 と同じ走査を再実行し、出力を `/tmp/procscan_after.txt` へ保存してから
別命令で表示する。続けて Task 4 Step 4 と同じ probe で施錠を測る。
**期待は逆で、lock_still_held（新版が保持している）である。**

新しい keeper の PID（NEW_PID）が OLD_PID と**異なる**こと、施錠が**再び保持されている**
こと（lock_still_held）を確かめる。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 15 | 新版の稼働 | keeper count=1、NEW_PID が OLD_PID と異なる | `/proc/NEW_PID/cmdline` を直接読み `~/bin/keeper.sh` を指すことを確認 |
| 16 | 施錠の再保持 | lock_still_held（新版が保持中） | Task 4 で解放（lock_free）を実測してからの変化として対で示す |
| 17 | 対照 | 不存在語 0 | 同じ走査で syncthing が一件以上を返す |

---

## Task 6 (Phase D): 中心としての稼働を確かめる

**Files:** Modify: `tasks/T-2026-08-13-hub-deploy-lecun/deploy.md`

handoff の八確認に従う。**最低限、次を含める。**

- [ ] **Step 1: 中継を張らないことを確かめる**

新版は目印の分岐により lecun では中継を張らないはずである。起動から数分おいて
再走査し、`22001` の一致が零のままであること、`/proc/net/tcp` に 22001 の LISTEN が
無いことを確かめる。**ssh は実行しない。**

- [ ] **Step 2: 中心でも必要な処理が生きていることを確かめる**

    Task 2 Step 4 と同じ復号で 22000 と 8384 の LISTEN を再確認する
    syncthing の稼働数が配置前と同数であることを再走査で確認する
    新版が指す記録先（起動行のリダイレクト先と、keeper が書く記録）の更新時刻を
    ls -la で配置前後比較し、起動後に動いた証拠を一つ以上示す

- [ ] **Step 3: 目印と正本が無変更であることを確かめる**

    sha256sum MARKER_PATH scripts/sync/keeper.sh scripts/sync/m2-sync.sh

Task 2 の値と一致すること。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 18 | 中継なし | 22001 一致 0・LISTEN 無し（起動数分後の再測） | 走査と復号の双方（異質な二経路）で零が一致 |
| 19 | 中心処理の維持 | 22000 と 8384 LISTEN・syncthing 同数・記録が動いた証拠 | 配置前（Task 2）の実測と対で比較 |
| 20 | 無変更 | 目印と正本二件の要約値が Task 2 と一致 | 変更したはずの `~/bin/keeper.sh` の値が変わっていることを対照として併記 |

---

## Task 7 (Phase E): 検証・送出・報告

**Files:** Create: `tasks/T-2026-08-13-hub-deploy-lecun/RESULT.md`,
`tasks/T-2026-08-13-hub-deploy-lecun/result.yaml`, `tasks/inbox.d/T-2026-08-13-hub-deploy-lecun.md`

- [ ] **Step 1: 完了判定二十項目＋本 Task 分を一つの表にまとめる。** 各行に実測値または
`UNKNOWN`、四列目に空振りでないことの確認を書く。空欄を残さない。

- [ ] **Step 2: `conventions_rev` を実測して置換する**

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 3: 検証を通す**

    make task-validate TASK=T-2026-08-13-hub-deploy-lecun; echo "validate_exit=$?"
    make task-preflight TASK=T-2026-08-13-hub-deploy-lecun; echo "preflight_exit=$?"
    make forbidden-check; echo "forbidden_exit=$?"
    git --no-pager status --porcelain > /tmp/wt.txt; wc -l /tmp/wt.txt; cat /tmp/wt.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un.txt
    echo "unmerged=$(wc -l < /tmp/un.txt)"; cat /tmp/un.txt

- [ ] **Step 4: 受け皿へ置く。** `tasks/inbox.d/T-2026-08-13-hub-deploy-lecun.md` に
canary の設計に使える事実だけを置く（どのホストを canary にするかの提案は書かない）。

- [ ] **Step 5: 送信前の自己検査**

    .venv/bin/python - <<'PY'
    import pathlib, re
    for f in ["RESULT.md", "result.yaml", "deploy.md"]:
        p = pathlib.Path("tasks/T-2026-08-13-hub-deploy-lecun") / f
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        print("%s bmp_over=%d hex40=%d" % (f, sum(1 for c in s if ord(c) > 0xFFFF),
              len(re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])", s))))
    PY

両方が零になるまで直す。

- [ ] **Step 6: commit し、分岐を送出し、PR を作る**

    git add tasks/T-2026-08-13-hub-deploy-lecun/ tasks/inbox.d/T-2026-08-13-hub-deploy-lecun.md
    git commit -m "ops(sync): deploy canonical keeper on lecun and restart as hub"
    git fetch origin && git merge origin/phase0
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

既存 PR があれば新規作成せず本文を更新し、その旨を報告する。

- [ ] **Step 7: 抑止を解除する（削除ではなく移動）**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-13-hub-deploy-lecun 2>/dev/null \
      && echo "released" || echo "解除に失敗。手当てが要る"
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

- [ ] **Step 8: 報告を台帳へ返す**

    make task-report TASK=T-2026-08-13-hub-deploy-lecun; echo "report_exit=$?"

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| 21 | 全項目の記載 | 全行に実測値または UNKNOWN | 行数を数え項目数と一致させた |
| 22 | 検証 | validate と preflight と forbidden の各 exit を記載（P9 偽陽性は既知） | preflight の PASS/WARN/SKIP/FAIL の内訳を貼付 |
| 23 | 変更範囲 | repo 内は契約範囲と生成物のみ。unmerged 0 | status 全行を一件ずつ分類して貼付 |
| 24 | 分岐と PR | upstream 設定済み ahead 零。PR 番号と Draft の別 | PR 一覧と自分の head を突き合わせた |
| 25 | 抑止解除 | repo 直下に無い | 移動先の実在を ls で確認 |
| 26 | 台帳返送 | report_exit=0 | verdict と bytes の出力を貼付 |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| handoff が実在しない・読めない | **停止して報告。** 併合の伝播を疑う。配置に進まない |
| 稼働版と正本の要約値が既に一致 | 配置は空振り（配置済み）。**記録して G2 で報告し判断を仰ぐ** |
| TERM で旧 PID が消えない | 十秒後に再確認。残るなら**中断して報告**（強い信号は送らない） |
| 起動後に 22001 系の挙動が出る | **失敗様式に照らして rollback。** 控えを戻し記録済みの起動行で旧版を再起動し、停止して報告 |
| 起動しても施錠を取らない | 数十秒待って再測。取らなければ rollback |
| rollback 後も常駐が稼働しない | **停止して報告**（escalate）。以後の操作を行わない |
| 常駐処理が作業分岐へ統合した | 逸脱ではない。事実として記録する |
| 変更しなければ測れない項目 | 本契約の許可範囲（keeper.sh・控え・信号・起動）の外なら UNKNOWN とする |

rollback の正は handoff の手順である。本表と食い違えば handoff に従う。

**言い訳をしない。事実と、測れなかったことを書く。**

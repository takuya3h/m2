# 中心側の役割と、配置・再起動の手順を実装から確定する

**task_id:** `T-2026-08-13-hub-role-and-restart`  **kind:** `analysis`
**depends_on:** `T-2026-08-12-register-hub-keys`
**実行ホスト:** `lecun`（中心になるホスト）  **repo:** `~/slocal2/m2`

## Goal

設定共有を **efros / lecun / bengio / andrew / ilya の五台**で復旧させる。中心は
**lecun**、すなわち本ホストである。準備は次まで進んだ。

| 済 | 内容 |
|---|---|
| 済 | 正本が目印から中心を導出する形になった |
| 済 | andrew と ilya の公開鍵が本ホストの受け入れ一覧へ登録された（四件から六件へ） |
| **未** | **正本の配置、目印の置換、常駐処理の再起動、疎通の確認** |

**残るのは配置と再起動だが、ここが最も危険である。** 五台の常駐処理を同時に触るため、
手順を誤ると**同期が全台で止まり、しかも中継が無いので遠隔からは直せない。**

**起票者は次を把握していない。** これらを実装から確定させるのが本契約である。

1. **常駐処理は中継のほかに何をしているか。** 中心では中継が要らないが、他の役割は要るのか
2. **目印を外すと、中継以外の処理に影響が出るか**
3. **常駐ループの実体は何か。** 置き換えたあと、どうすれば新しい版が動き出すか
4. **再起動の具体的な手順と、失敗したときの戻し方**
5. **五台のうちどれを先に触るべきか。** 中心が先か後か

**本契約は読み取りのみである。** 配置も再起動も目印の変更も行わない。
**次の契約のための手順書を作ることが成果物である。**

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal2/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
    git branch --show-current
    git --no-pager status --porcelain

**二つ目が `0` なら抑止は効いていない**（続行してよいが報告に記す）。
**三つ目が `feat/` で始まらなければ分岐が作られていない。停止して報告する。**
四つ目について、**契約自身のディレクトリ `tasks/T-2026-08-13-hub-role-and-restart/` は
未追跡で正常である。判定から除外する。** それ以外があれば報告して停止する。

| # | 禁止 |
|---|---|
| 1 | **`~/bin/**` を変更する。正本を配置する** |
| 2 | **常駐処理を起動・停止・再起動する。プロセスに信号を送る** |
| 3 | **中継の目印を作る・消す・書き換える。中継を張る、切る** |
| 4 | 同期処理の設定を変更する。同期処理を起動・停止・再起動する |
| 5 | `~/.ssh/**` を変更する。鍵を生成・複製・配布・削除する |
| 6 | 他ホストへ書き込む。他ホストで命令を実行する |
| 7 | `~/.zshrc` `~/.zshenv` を変更する |
| 8 | 装置を使う |
| 9 | **生成物を再生成する**（`make context` `make taskindex` `make inbox` を実行しない） |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `runindex/**` `context/auto/**` を手で編集する |
| 12 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

**禁止 1 から 3 が本契約の要である。** 本契約が終わったとき、**このホストの状態は
開始時と完全に同じ**でなければならない。動いているものを一つも止めない。

**push と PR の作成は「外部への送信」にも「統合」にも当たらない。** 分岐を送るだけである。

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

`inputs.data` は雛形の必須項目として残しているが、**本契約はデータも分割も参照しない。**

### 起票者からの申し送り

**推測で手順を書かない。** 起票者は常駐処理の全文も、それを起こす仕組みも読んでいない。
**実装を読んで確定させることが本契約の目的である。** 読めない部分は `UNKNOWN` とする。

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | **数える対象を広く取りすぎない。** 名前の一部一致は別のものを拾う |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | **対照は両方向で取る。期待値を実測前に一点へ固定しない** |
| 5 | 対象の一覧そのものが正しいかを確かめる。件数を必ず出力する |
| 6 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 7 | 名前を決め打ちしない。先頭がドットのものを落とさない |
| 8 | 測定命令の副作用が禁止領域に触れないかを確かめる |
| 9 | **無変更は表示属性ではなく要約値で確かめる。** 大きさと更新時刻が同じでも中身は変わりうる |
| 10 | 出力は要約せず `audit.md` へ貼る |

申し送り 9 は前契約の欠陥に対応する。`ls -la` と `wc -c` だけで比較させたが、
**同じ大きさ・同じ時刻で中身が変わった場合を検出できない。**

**権限や設定の現在値を起票者が断定していたら疑う。** 前契約で受け入れ一覧の権限を
`600` と書いたが、実測は `664` だった。

**一時ファイルの名前は契約ごとに分ける。** 別の契約の残りが混ざる。

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には
`source .venv/bin/activate && source scripts/load_env.sh` を同じ命令に含める。

### 確定した環境の事実（再測定は不要）

| 事実 | 実測値 |
|---|---|
| 中心 | **lecun（本ホスト）**。住所は `192.168.196.176` |
| 受け入れ一覧 | **六件**。efros / bengio / philip / andrew / ilya / 人の端末 |
| 正本の状態 | 目印から中心を導出する形へ変更済み。**配置は未実施** |
| 目印の書式 | 一行目は秘密鍵の経路、二行目は中心の住所（任意）。**中心自身は目印を置かない** |
| 稼働中の版 | 2250 bytes。**正本とは既に異なる**（正本が更新されたため） |
| 自己更新 | `keeper.sh` は**されない**。`m2-sync.sh` と `.stignore` はされる |
| プロセスの計数 | `ps` と `grep` による検索は自己一致する。`/proc/*/cmdline` を使う |

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 単語分割は
起きない。`git` を使う操作は `git --no-pager`。**山括弧は書かない。**
`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 常駐処理が何をしているかを列挙する

**Files:** Create: `tasks/T-2026-08-13-hub-role-and-restart/audit.md`

- [ ] **Step 1: 稼働中の版と正本の両方を全文読む**

    wc -l ~/bin/keeper.sh; sha256sum ~/bin/keeper.sh
    wc -l scripts/sync/keeper.sh; sha256sum scripts/sync/keeper.sh
    cat -n ~/bin/keeper.sh

**全文を `audit.md` へ貼る。** 要約しない。以後の判断はこの本文に基づく。

- [ ] **Step 2: 正本との差を全文で示す**

    git --no-pager diff --no-index -- ~/bin/keeper.sh scripts/sync/keeper.sh > /tmp/hrr_keeper_diff.txt 2>&1
    grep -c '' /tmp/hrr_keeper_diff.txt
    cat /tmp/hrr_keeper_diff.txt

**行数で判定する。終了コードでは判定しない**（差があると `1` を返す仕様）。

- [ ] **Step 3: 周回で行われる処理を一つずつ列挙する**

`audit.md` に表を作る。**実装の行番号を必ず添える。**

| # | 処理 | 行番号 | 中心で要るか |
|---|---|---|---|
| 例 | 中継の維持 | | **要らない**（中心は入られる側） |

**「中心で要るか」は実装を読んで判定する。** 判定できないものは `UNKNOWN` とする。
**推測で埋めない。**

- [ ] **Step 4: 目印が無い場合に何が起きるかを実装から読む**

**目印を外すのは中継を止めるためだが、他の処理まで止まっては困る。**

実装を読み、**目印の有無で分岐する範囲**を行番号で示す。
分岐の外にある処理は、目印が無くても動き続けるはずである。**それを確かめる。**

**実際に目印を外してはならない**（禁止 3）。**実装の読解として記録する。**

- [ ] **Step 5: 中継以外の役割が他ホストに依存しているかを確かめる**

`m2-sync.sh` の実行など、**中継が無いと成り立たない処理があるか**を読む。

    wc -l ~/bin/m2-sync.sh; grep -n -i -E "22001|127.0.0.1|tunnel|ssh" ~/bin/m2-sync.sh

**あれば、中心では別の扱いが要る。** 無ければ、目印を外しても他の処理は無事である。

| # | 完了判定 |
|---|---|
| 1 | 稼働中の版と正本の全文を記録し、要約値を併記した |
| 2 | 両者の差を全文で示した（行数で判定） |
| 3 | 周回の処理を行番号つきで列挙し、中心で要るかを判定した（不明は UNKNOWN） |
| 4 | 目印の有無で分岐する範囲を行番号で示した |
| 5 | 中継以外の役割が中継に依存するかを実装から判定した |

---

## Task 2 (Phase A): 常駐ループの実体と、新しい版を動かす方法を確定する

**Files:** Modify: `tasks/T-2026-08-13-hub-role-and-restart/audit.md`

**置き換えただけでは新しい版は動かない。** どうすれば動き出すかを確定させる。

- [ ] **Step 1: 常駐処理を起こしている仕組みを探す**

    grep -n -i -E "keeper|nohup|while|sleep" ~/.zshrc 2>/dev/null || echo "zshrc に該当なし"
    grep -n -i -E "keeper|nohup" ~/.zshenv ~/.profile ~/.bashrc 2>/dev/null || echo "他の設定に該当なし"
    ls -la /etc/systemd/system/ 2>/dev/null | grep -i keeper || echo "systemd に該当なし"
    crontab -l 2>/dev/null | grep -i keeper || echo "cron に該当なし"

**複数の出所を確かめる。** 一つ目で見つかっても、他にも無いかを見る。
**二重に起こす仕組みがあれば、片方だけ止めても復活する。**

- [ ] **Step 2: 稼働中のプロセスの素性を測る**

    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for d in sorted(os.listdir("/proc")):
        if not d.isdigit() or int(d) in me: continue
        try: c = open("/proc/%s/cmdline" % d, "rb").read().decode("utf-8","replace")
        except OSError: continue
        if "keeper" in c or "m2-sync" in c:
            st = open("/proc/%s/stat" % d).read().split(") ",1)[1].split()
            print("pid=%s ppid=%s cmd=%s" % (d, st[1], c.replace("\x00"," ").strip()))
    PY

**親子関係を記録する。** 親が誰かによって、止め方が変わる。
**起動時刻も測る**（`/proc/PID/stat` の 22 番目の値、または `ls -ld /proc/PID`）。

- [ ] **Step 3: 多重起動を防ぐ仕組みを確かめる**

    ls -la ~/.keeper.lock 2>/dev/null || echo "lock なし"
    grep -n -i -E "flock|lock" ~/bin/keeper.sh

**`flock` があるなら、古いプロセスが生きている間は新しい版が走らない。**
**止めずに置き換えても、次の周回では古いプロセスが古い本文で走り続ける**のか、
**毎周回で本文を読み直す**のかを、実装の構造から判定する。

**シェルスクリプトは通常、実行中に本文を読み直さない。** ただし
`while true; do ... done` の外側で起動し直す構造なら話が違う。**実装を読んで確かめる。**

- [ ] **Step 4: 止め方と起こし方の候補を列挙する**

**実行はしない。** 候補と、それぞれの副作用を表にする。

| 方法 | 副作用 | 中継はどうなるか |
|---|---|---|
| 例: プロセスに終了信号を送る | | |
| 例: 目印を外して次の周回を待つ | | |
| 例: 何もせず次の周回を待つ | | |

**どれが最も安全かを判定し、理由を書く。** 判定できなければ `UNKNOWN` とする。

| # | 完了判定 |
|---|---|
| 6 | 常駐処理を起こす仕組みを複数の出所から探した（件数と場所） |
| 7 | 稼働中のプロセスの親子関係と起動時刻を記録した |
| 8 | 多重起動の防止と、本文の読み直しの有無を実装から判定した |
| 9 | 止め方と起こし方の候補を列挙し、副作用を書いた（実行していない） |

---

## Task 3 (Phase B): 配置の順序と復旧の手順を決める

**Files:** Modify: `tasks/T-2026-08-13-hub-role-and-restart/audit.md`,
Create: `tasks/T-2026-08-13-hub-role-and-restart/handoff.md`

**次の契約はこの手順書に従う。** ここで決まらなかったことは、次でも決まらない。

- [ ] **Step 1: 中心を先に触るか後に触るかを判定する**

Task 1 と Task 2 の結果から、次を判定する。**根拠を実装の行番号で示す。**

| 問い | 判定 |
|---|---|
| 中心の常駐処理が古い版のままでも、他ホストは繋ぎに来られるか | |
| 中心の目印を外すと、中心の他の処理は動き続けるか | |
| 他ホストが新しい目印を持ったとき、中心の準備が未了だと何が起きるか | |

**「中心が先」か「中心が後」か、あるいは「どちらでもよい」かを結論する。**

- [ ] **Step 2: 一台あたりの手順を書き出す**

`handoff.md` に、**一般ノード用**と**中心用**の二つの手順を書く。

各手順は次を含む。

| 項目 | 内容 |
|---|---|
| 事前の記録 | 何を測ってから始めるか（要約値を含む） |
| 控え | 現行版をどこへ退避するか |
| 配置 | どのファイルをどこへ、どの権限で |
| 目印 | 何を作り、何を消すか（中心は消すだけ） |
| 再起動 | Task 2 で最も安全と判定した方法 |
| 確認 | 何をもって成功とするか |
| 戻し方 | 失敗したとき何を実行するか |

**実際には実行しない。手順を書くだけである。**

- [ ] **Step 3: 疎通の確認方法を決める**

**何をもって「動いた」とするか**を決める。候補を挙げ、それぞれが何を示すかを書く。

| 確認 | 示すこと | 示さないこと |
|---|---|---|
| 例: 中継のプロセスが立つ | | |
| 例: 中心の入口へ接続できる | | |
| 例: 同期処理が相手を認識する | | |
| 例: ファイルが実際に届く | | |

**最も強い確認は「ファイルが実際に届くこと」である。** その測り方も書く。
**ただし本契約では実行しない。**

- [ ] **Step 4: 失敗の様式を列挙する**

**何がどう失敗しうるかを先に書く。** 起きてから考えると遠隔からは直せない。

| 失敗 | 症状 | 検出方法 | 戻し方 |
|---|---|---|---|

**「五台とも止まって遠隔から直せない」状態をどう避けるか**を必ず含める。

| # | 完了判定 |
|---|---|
| 10 | 中心を先に触るか後かを判定し、根拠を行番号で示した |
| 11 | 一般ノード用と中心用の手順を書き出した（実行していない） |
| 12 | 疎通の確認方法を列挙し、それぞれが示すことと示さないことを分けた |
| 13 | 失敗の様式と戻し方を列挙した |

---

## Task 4 (Phase C): 無変更を確かめ、送出し、報告する

**Files:** Create: `tasks/T-2026-08-13-hub-role-and-restart/RESULT.md`,
`tasks/T-2026-08-13-hub-role-and-restart/result.yaml`,
`tasks/inbox.d/T-2026-08-13-hub-role-and-restart.md`

- [ ] **Step 1: 完了判定 13 項目を一つの表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。**

- [ ] **Step 2: 開始時と完全に同じ状態であることを、要約値で確かめる**

**表示属性では足りない。中身の要約値で比べる。**

    sha256sum ~/bin/keeper.sh ~/bin/m2-sync.sh 2>/dev/null
    for f in ~/.tunnel_to_*; do test -f "${f}" && sha256sum "${f}"; done
    sha256sum ~/.ssh/authorized_keys
    ls -la ~/.keeper.lock 2>/dev/null || echo "lock なし"
    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for word in ("ssh -N -L", "keeper.sh", "syncthing", "m2-sync", "zzz_no_such_process"):
        n = 0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: c = open("/proc/%s/cmdline" % d, "rb").read().decode("utf-8","replace")
            except OSError: continue
            if word in c: n += 1
        print("%s=%d" % (word, n))
    PY

**Task 1 の時点と要約値が一致し、プロセスの数が変わっていないこと。**
**一致しなければ停止して報告する。** 読み取りのみの契約で何かが変わったということである。

- [ ] **Step 3: `conventions_rev` を実測して置換し、検証を通す**

    source .venv/bin/activate && source scripts/load_env.sh \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-validate TASK=T-2026-08-13-hub-role-and-restart; echo "validate_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-preflight TASK=T-2026-08-13-hub-role-and-restart; echo "preflight_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make forbidden-check; echo "forbidden_exit=$?"

- [ ] **Step 4: 判断の受け皿へ置く**

`tasks/inbox.d/T-2026-08-13-hub-role-and-restart.md` に**起票者が次の判断に使える事実だけ**を置く。
**いつ配置するかの判断は書かない。**

- [ ] **Step 5: 変更範囲と未解決を行数で確かめる**

    git --no-pager status --porcelain > /tmp/hrr_wt.txt
    grep -c '' /tmp/hrr_wt.txt; cat /tmp/hrr_wt.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/hrr_un.txt
    echo "unmerged=$(grep -c '' /tmp/hrr_un.txt)"; cat /tmp/hrr_un.txt

**変更が本契約のディレクトリと受け皿に限られること。**
最上位の指示が別のファイルの更新を要求する場合、**それに従い、理由を報告に記す。**

- [ ] **Step 6: commit し、分岐を送出し、PR を作る**

    git add tasks/T-2026-08-13-hub-role-and-restart/ tasks/inbox.d/T-2026-08-13-hub-role-and-restart.md
    git commit -m "docs(sync): determine hub role and restart procedure"
    git --no-pager log -1 --format='%h %s'
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**同じ head と base の PR は二本作れない。先に一覧で確認し、存在すれば本文を更新する。**
`phase0` が進んでいて取り込みが要る場合、**それは自分の分岐への操作であり禁止していない。**
**生成物で衝突したら `origin/phase0` 側を採り、再生成はしない**（禁止 9）。

- [ ] **Step 7: 抑止を解除し、報告を台帳へ返す**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-13-hub-role-and-restart 2>/dev/null
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-report TASK=T-2026-08-13-hub-role-and-restart; echo "report_exit=$?"

| # | 完了判定 |
|---|---|
| 14 | 13 項目すべてに実測値または UNKNOWN がある |
| 15 | 開始時と要約値が一致し、プロセスの数が変わっていない |
| 16 | 変更が契約の範囲に限られる（一覧を記載） |
| 17 | 分岐が送出され、PR が存在する（番号と下書きの別） |
| 18 | 抑止が repo 直下から消えている |
| 19 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **何かが変わってしまった** | **停止して報告。** 読み取りのみの契約である。元に戻そうとしない |
| 常駐処理を起こす仕組みが見つからない | **`UNKNOWN` とする。** 次の契約で再起動の方法が決まらないという結果である |
| 起こす仕組みが複数見つかった | **すべて記録する。** 片方だけ止めても復活するということである |
| 稼働中のプロセスが無い | **記録して続行。** 既に止まっているなら配置は容易である |
| 稼働中の版と正本の差が想定より大きい | **全文を記録する。** 起票者の前提が古い |
| 中心で要るか判定できない処理がある | **`UNKNOWN` とする。** 推測で埋めない |
| 手順を書ききれない項目がある | **書けない理由を記す。** 次の契約で埋める |
| 分岐が `feat/` で始まらない、抑止の解除に失敗した | **報告に明記する。** 自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

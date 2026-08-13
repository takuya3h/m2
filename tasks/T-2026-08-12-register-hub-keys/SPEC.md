# 中心の受け入れ一覧へ二件を登録する

**task_id:** `T-2026-08-12-register-hub-keys`  **kind:** `impl`
**depends_on:** `T-2026-08-12-submit-hub-key-andrew`
**実行ホスト:** `lecun`（中心）  **repo:** `~/slocal2/m2`

## Goal

設定共有を **efros / lecun / bengio / andrew / ilya の五台**で復旧させる。中心は
**lecun**、すなわち本ホストである。

andrew と ilya が公開鍵を版管理へ提出した。**本契約はそれを受け入れ一覧へ登録する。**

| ホスト | 公開鍵 | 指紋 |
|---|---|---|
| andrew | `scripts/sync/hub_keys/andrew.pub` | `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` |
| ilya | `scripts/sync/hub_keys/ilya.pub` | `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo` |

**本契約はこれまでで最も危険である。** `~/.ssh/authorized_keys` を書き換えるため、
**壊すと efros と bengio も入れなくなる。** 現在の四行は次のとおりで、
**これらが一件も欠けてはならない。**

| 註釈 | 種別 | 意味 |
|---|---|---|
| `philip-to-lecun` | RSA | 旧中心から |
| `bengiotolecun` | ED25519 | bengio から |
| `ubuntu@efros` | RSA | efros から |
| `dakyo-mba@dmba.local` | ED25519 | 人の端末から |

**追記だけを行う。既存行の削除も並べ替えも書式変更もしない。**

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal2/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
    git branch --show-current
    git --no-pager status --porcelain

**二つ目が `0` なら抑止は効いていない**（続行してよいが報告に記す）。
**三つ目が `feat/` で始まらなければ分岐が作られていない。停止して報告する。**
四つ目について、**契約自身のディレクトリ `tasks/T-2026-08-12-register-hub-keys/` は
未追跡で正常である。判定から除外する。** それ以外があれば報告して停止する。

| # | 禁止 |
|---|---|
| 1 | **受け入れ一覧の既存行を削除・変更・並べ替える**（追記だけを行う） |
| 2 | **`~/.ssh/` の他のファイルを変更する**（`authorized_keys` 以外は読むのみ） |
| 3 | 鍵を生成・複製・配布・削除する |
| 4 | 中継の目印を作る・消す・書き換える。中継を張る、切る |
| 5 | `~/bin/**` を変更する。常駐処理を起動・停止・再起動する |
| 6 | 同期処理の設定を変更する。同期処理を起動・停止・再起動する |
| 7 | 他ホストへ書き込む。他ホストで命令を実行する |
| 8 | 装置を使う |
| 9 | **生成物を再生成する**（`make context` `make taskindex` `make inbox` を実行しない） |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `runindex/**` `context/auto/**` を手で編集する |
| 12 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

**禁止 9 の理由。** 並行する契約で生成物の扱いが分かれ、**版管理で衝突した**（実測）。
**統合の後に一度だけ再生成する**運用に変えた。本契約では触らない。
`taskindex-check` などが未投影差分を報告しても、**事実として記録するだけでよい。**

**push と PR の作成は「外部への送信」にも「統合」にも当たらない。** 分岐を送るだけであり、
`phase0` への取り込みは行わない。**Task 4 の Step は禁止に触れない。**

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

`inputs.data` は雛形の必須項目として残しているが、**本契約はデータも分割も参照しない。**

### 起票者からの申し送り

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
| 9 | 出力は要約せず `audit.md` へ貼る |

申し送り 2 は前契約の欠陥に対応する。`grep -i tunnel` は `.tunnel.log` まで数えた。
**目印は一件だったのに二件と出た。**

**一時ファイルの名前は契約ごとに分ける。** 前契約で `/tmp/kh_audit.txt` に
別の契約の九行が残っていた。

`成功命令 && echo "成功" || echo "失敗"` の形は、**表示側が失敗しても「失敗」が出る。**
**判定は別の命令で行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には
`source .venv/bin/activate && source scripts/load_env.sh` を同じ命令に含める。

### 確定した環境の事実（再測定は不要）

| 事実 | 実測値 |
|---|---|
| 中心 | **lecun（本ホスト）**。SSH は `50072`、転送は `22001` から `22000` |
| 中心の住所 | `192.168.196.176`（andrew と ilya が独立に確定） |
| 現在の受け入れ | **四行**。上の表のとおり |
| 提出された鍵 | 二件とも ED25519。**指紋は上の表のとおり** |
| 提出時の認証 | 二台とも**拒否**（`exit 255`）。**これが本契約の対照になる** |
| 目印の書式 | 一行目は秘密鍵の経路、二行目は中心の住所（任意） |
| プロセスの計数 | `ps` と `grep` による検索は自己一致する。`/proc/*/cmdline` を使う |

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 単語分割は
起きない。`git` を使う操作は `git --no-pager`。**山括弧は書かない。**
`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 現状を記録し、控えを版管理へ残す

**Files:** Create: `tasks/T-2026-08-12-register-hub-keys/audit.md`,
`tasks/T-2026-08-12-register-hub-keys/authorized_keys.before`

**壊したときに戻せる状態を先に作る。**

- [ ] **Step 1: 受け入れ一覧の現状を測る**

    ls -la ~/.ssh/authorized_keys
    wc -l ~/.ssh/authorized_keys
    grep -c -v "^[[:space:]]*$" ~/.ssh/authorized_keys
    sha256sum ~/.ssh/authorized_keys
    stat -c "%s %Y %a" ~/.ssh/authorized_keys

**行数・要約値・権限・更新時刻を記録する。** 空行を除いた件数も別に数える。

- [ ] **Step 2: 登録されている鍵の指紋と註釈を記録する**

    ssh-keygen -lf ~/.ssh/authorized_keys > /tmp/reg_before.txt 2>&1
    echo "parse_exit=$?"
    grep -c "" /tmp/reg_before.txt
    cat /tmp/reg_before.txt

**解析が失敗したら停止して報告する。** 現状が壊れているなら、それを先に直す必要がある。
**四件が出ることを確かめる。** 数が違えば起票者の前提が古い。記録して続行する。

- [ ] **Step 3: 控えを版管理へ残す**

**公開鍵は秘匿ではない。** 版管理に残せば、`/tmp` が消えても戻せる。

    cp ~/.ssh/authorized_keys tasks/T-2026-08-12-register-hub-keys/authorized_keys.before
    sha256sum tasks/T-2026-08-12-register-hub-keys/authorized_keys.before
    grep -c "PRIVATE" tasks/T-2026-08-12-register-hub-keys/authorized_keys.before

**要約値が Step 1 と一致すること。** `PRIVATE` の一致が **零**であること。
**零でなければ停止して報告する。** 受け入れ一覧に秘密鍵が混ざっているという異常である。

**陽性対照**: 秘密鍵の書き出しを模した一時ファイルに同じ検査をかけ、
**一以上を返すこと**を確かめる。囮は版管理へ入れない。

- [ ] **Step 4: 戻し方を記録する**

`audit.md` に次を書く。**実行はしない。**

    cp tasks/T-2026-08-12-register-hub-keys/authorized_keys.before ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys

**壊した場合、これで Step 1 の状態に戻る。**

| # | 完了判定 |
|---|---|
| 1 | 受け入れ一覧の行数・要約値・権限・更新時刻を記録した |
| 2 | 登録されている鍵の指紋と註釈を記録した（件数と解析の成否） |
| 3 | 控えを版管理へ残し、要約値が一致した（秘密鍵の混入なし。陽性対照つき） |
| 4 | 戻し方を記録した（実行はしていない） |

---

## Task 2 (Phase A): 提出された公開鍵を読み、指紋を照合する

**Files:** Modify: `tasks/T-2026-08-12-register-hub-keys/audit.md`

**追記する前に、追記するものが正しいことを確かめる。**

- [ ] **Step 1: 提出物が版管理にあることを確かめる**

    ls -la scripts/sync/hub_keys/
    git --no-pager log --oneline -3 -- scripts/sync/hub_keys/
    for f in scripts/sync/hub_keys/*.pub; do
      echo "FILE ${f} bytes=$(wc -c < "${f}") lines=$(wc -l < "${f}")"
    done

**二件あることを確かめる。** 無ければ統合が済んでいない。**停止して報告する。**

- [ ] **Step 2: 指紋が起票時の値と一致することを確かめる**

    ssh-keygen -lf scripts/sync/hub_keys/andrew.pub
    ssh-keygen -lf scripts/sync/hub_keys/ilya.pub

期待する値は次のとおりである。

| ファイル | 期待する指紋 |
|---|---|
| `andrew.pub` | `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` |
| `ilya.pub` | `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo` |

**一致しなければ停止して報告する。** 提出物が入れ替わっているか、途中で変わっている。

- [ ] **Step 3: 追記するものが公開鍵だけであることを確かめる**

    for f in scripts/sync/hub_keys/*.pub; do
      echo "=== ${f}"
      head -c 40 "${f}"; echo
      echo "private_hits=$(grep -c 'PRIVATE' "${f}")"
      echo "lines=$(grep -c '' "${f}")"
    done

Expected: 先頭が `ssh-` で始まる。`PRIVATE` の一致が **零**。行数が **一**。
**一つでも外れたら停止して報告する。**

- [ ] **Step 4: 既に登録されていないことを確かめる**

    grep -c -F "i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k" /tmp/reg_before.txt
    grep -c -F "5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo" /tmp/reg_before.txt

Expected: **両方とも零。** 零でなければ既に登録済みであり、
**その分は追記しない。** 記録して続行する（異常ではない）。

**陽性対照**: 既存の指紋の一つで同じ照合を行い、**一を返すこと**を確かめる。
**照合が常に零を返す壊れ方をしていないことを示す。**

| # | 完了判定 |
|---|---|
| 5 | 提出物が二件あることを確かめた（バイト数と行数） |
| 6 | 指紋が起票時の値と一致した（二件とも） |
| 7 | 追記するものが公開鍵だけである（三つの検査） |
| 8 | 既に登録されていないことを確かめた（陽性対照つき） |

---

## Task 3 (Phase B): 追記し、既存が無傷であることを照合する

**Files:** Modify: `~/.ssh/authorized_keys`

**ここが本契約の核心である。既存行を一つも失わない。**

- [ ] **Step 1: 追記する**

**追記のみを行う。上書きしない。**

    cat scripts/sync/hub_keys/andrew.pub >> ~/.ssh/authorized_keys
    cat scripts/sync/hub_keys/ilya.pub >> ~/.ssh/authorized_keys

**元のファイルが改行で終わっていない場合、行が繋がる。** Task 1 Step 1 の行数と
空行を除いた件数を見比べ、**必要なら先に改行を足す。** 足した場合は記録する。

- [ ] **Step 2: 行数と権限を確かめる**

    wc -l ~/.ssh/authorized_keys
    grep -c -v "^[[:space:]]*$" ~/.ssh/authorized_keys
    stat -c "%s %a" ~/.ssh/authorized_keys

Expected: 空行を除いた件数が **四から六へ増える**。権限が **600 のまま**。
**六でなければ停止して報告する。**

- [ ] **Step 3: 既存の四件がすべて残っていることを照合する**

    ssh-keygen -lf ~/.ssh/authorized_keys > /tmp/reg_after.txt 2>&1
    echo "parse_exit=$?"
    grep -c "" /tmp/reg_after.txt
    cat /tmp/reg_after.txt
    sort /tmp/reg_before.txt > /tmp/reg_b_sorted.txt
    sort /tmp/reg_after.txt > /tmp/reg_a_sorted.txt
    echo "=== 消えた行 ==="
    comm -23 /tmp/reg_b_sorted.txt /tmp/reg_a_sorted.txt
    echo "=== 増えた行 ==="
    comm -13 /tmp/reg_b_sorted.txt /tmp/reg_a_sorted.txt

**「消えた行」が空であること。** 一件でもあれば既存を失っている。
**即座に Task 1 Step 4 の戻し方で復旧し、報告する。**

**「増えた行」が二件で、指紋が Task 2 Step 2 の値と一致すること。**

- [ ] **Step 4: 解析が全行で通ることを確かめる**

    grep -c -v "^[[:space:]]*$" ~/.ssh/authorized_keys
    grep -c "" /tmp/reg_after.txt

**両者が一致すること。** 一致しなければ、解析できない行がある。
**書式が壊れているということであり、停止して報告する。**

- [ ] **Step 5: 控えとの差が追記分だけであることを確かめる**

    diff tasks/T-2026-08-12-register-hub-keys/authorized_keys.before ~/.ssh/authorized_keys > /tmp/ak_diff.txt
    echo "diff_lines=$(grep -c '' /tmp/ak_diff.txt)"
    cat /tmp/ak_diff.txt

**追加だけで、削除も変更も無いこと。** `<` で始まる行があれば既存を失っている。

| # | 完了判定 |
|---|---|
| 9 | 追記後の件数が六、権限が 600 のまま |
| 10 | **既存の四件がすべて残っている**（消えた行が空） |
| 11 | 増えた二件の指紋が期待と一致した |
| 12 | 全行が解析できる（件数の一致） |
| 13 | 控えとの差が追加だけである（削除も変更も無い） |

---

## Task 4 (Phase C): 検証し、送出し、報告する

**Files:** Create: `tasks/T-2026-08-12-register-hub-keys/RESULT.md`,
`tasks/T-2026-08-12-register-hub-keys/result.yaml`,
`tasks/inbox.d/T-2026-08-12-register-hub-keys.md`

- [ ] **Step 1: 完了判定 13 項目を一つの表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。追記の前後を併記する。**

**あわせて、次の契約で必要になる情報を記す。**

| 項目 | 内容 |
|---|---|
| 登録後の件数 | 六件。註釈の一覧 |
| 疎通の未確認 | **andrew と ilya から実際に入れるかは、このホストからは測れない** |
| 中心自身の目印 | lecun にある目印をどう外すか（**本契約では変更していない**） |

- [ ] **Step 2: 触っていないものが無変更であることを確かめる**

    ls -la ~/.tunnel_to_* 2>/dev/null || echo "目印なし"
    wc -c ~/bin/keeper.sh 2>/dev/null
    ls -la ~/.ssh/ | grep -v authorized_keys
    .venv/bin/python - <<'PY'
    import os
    me, p = set(), os.getpid()
    while p and p != 1:
        me.add(p)
        try: p = int(open("/proc/%d/stat" % p).read().split(") ",1)[1].split()[1])
        except Exception: break
    for word in ("ssh -N -L", "keeper.sh", "syncthing", "zzz_no_such_process"):
        n = 0
        for d in os.listdir("/proc"):
            if not d.isdigit() or int(d) in me: continue
            try: c = open("/proc/%s/cmdline" % d, "rb").read().decode("utf-8","replace")
            except OSError: continue
            if word in c: n += 1
        print("%s=%d" % (word, n))
    PY

**目印と稼働版と `~/.ssh/` の他のファイルが Task 1 の時点と一致すること。**
**中継と同期処理の数が変わっていないこと。**

- [ ] **Step 3: `conventions_rev` を実測して置換し、検証を通す**

    source .venv/bin/activate && source scripts/load_env.sh \
      && git --no-pager log -1 --format=%h -- context/conventions.md

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-validate TASK=T-2026-08-12-register-hub-keys; echo "validate_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-preflight TASK=T-2026-08-12-register-hub-keys; echo "preflight_exit=$?"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make forbidden-check; echo "forbidden_exit=$?"

**`source` を同じ命令に含めている。** 命令ごとに新しいシェルが起きる実装系があるため。

- [ ] **Step 4: 判断の受け皿へ置く**

`tasks/inbox.d/T-2026-08-12-register-hub-keys.md` に**起票者が次の判断に使える事実だけ**を置く。

- [ ] **Step 5: 変更範囲と未解決を行数で確かめる**

    git --no-pager status --porcelain > /tmp/wt_reg.txt
    grep -c '' /tmp/wt_reg.txt; cat /tmp/wt_reg.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un_reg.txt
    echo "unmerged=$(grep -c '' /tmp/un_reg.txt)"; cat /tmp/un_reg.txt

**変更が本契約のディレクトリと受け皿に限られること。**
**`~/.ssh/authorized_keys` は版管理の外なので、ここには現れない。**
最上位の指示が別のファイルの更新を要求する場合、**それに従い、理由を報告に記す。**

- [ ] **Step 6: commit する**

    git add tasks/T-2026-08-12-register-hub-keys/ tasks/inbox.d/T-2026-08-12-register-hub-keys.md
    git commit -m "feat(sync): register andrew and ilya keys on hub"
    git --no-pager log -1 --format='%h %s'

- [ ] **Step 7: 分岐を送出し、PR を作る**

**push と PR の作成は禁止に触れない。** 分岐を送るだけであり、統合ではない。

    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**同じ head と base の PR は二本作れない。先に一覧で確認し、存在すれば本文を更新する。**
**番号と下書きの別を報告に書く。**

`phase0` が進んでいて `git merge origin/phase0` が要る場合、**それは自分の分岐へ
取り込む操作であり、禁止していない。** 生成物で衝突したら、**中身を選ばず
`origin/phase0` 側を採り、再生成はしない**（禁止 9。統合の後にまとめて行う）。

- [ ] **Step 8: 抑止を解除し、報告を台帳へ返す**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-register-hub-keys 2>/dev/null
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

    source .venv/bin/activate && source scripts/load_env.sh \
      && make task-report TASK=T-2026-08-12-register-hub-keys; echo "report_exit=$?"

| # | 完了判定 |
|---|---|
| 14 | 13 項目すべてに実測値または UNKNOWN がある（追記の前後を併記） |
| 15 | 目印・稼働版・他の鍵・中継数・同期処理が無変更 |
| 16 | 変更が契約の範囲に限られる（一覧を記載） |
| 17 | 分岐が送出されている（上流が設定され ahead が零） |
| 18 | PR が存在する（番号と下書きの別） |
| 19 | 抑止が repo 直下から消えている |
| 20 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| **既存の行が消えた** | **即座に Task 1 Step 4 で復旧し、報告する。** 最も重い事故である |
| 受け入れ一覧の解析が最初から失敗する | **停止して報告。** 現状が壊れている。追記してはならない |
| 提出物が版管理に無い | **停止して報告。** 統合が済んでいない |
| 指紋が起票時の値と一致しない | **停止して報告。** 提出物が入れ替わっているか変わっている |
| 追記するものが公開鍵でない | **停止して報告。** 受け入れ一覧に入れてはならない |
| **既に登録されていた** | 記録して続行。**その分は追記しない。** 異常ではない |
| 現在の登録が四件でない | **記録して続行。** 起票者の前提が古いということである |
| 改行で終わっていない、権限が 600 から変わった | 改行を足す／権限を戻し、**行ったことを記録する。** 権限が緩いと鍵が無視される |
| 生成物で衝突した | **`origin/phase0` 側を採る。再生成はしない**（統合後にまとめて行う） |
| 分岐が `feat/` で始まらない、抑止の解除に失敗した | **報告に明記する。** 自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

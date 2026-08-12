# 監査で判明した道具の欠陥四件を直す

**task_id:** `T-2026-08-12-tooling-defect-fixes`  **kind:** `impl`
**depends_on:** `T-2026-08-12-tunnel-key-audit-efros`
**実行ホスト:** `efros`  **repo:** `~/slocal/m2`

## Goal

八件の監査契約を通じて、**契約を運ぶ道具そのものに四つの欠陥**が見つかった。
いずれも実行者が行番号まで特定している。放置すると以後のすべての契約が影響を受ける。

| # | 欠陥 | 症状 |
|---|---|---|
| 1 | 送信前の秘匿検査が四十桁の十六進を鍵と誤認する | **履歴の識別子を書くと報告を送れない**（偽陽性） |
| 2 | 同検査の模様が区切り付きの変数名に一致しない | **本物の資格情報を取りこぼす**（偽陰性） |
| 3 | 本文を切る単位が受け側と食い違う | **基本多言語面の外の文字を含むと `HTTP 400`** |
| 4 | 検査と試験が自ホスト名と特定の契約に依存する | **一台を除く全ホストで警告と失敗が出続ける** |

**2 が最も重い。** 偽陽性は送信が止まるので気づくが、**偽陰性は気づかないまま資格情報が
外部へ出る。** 実行者は陽性対照でこれを確かめている。仕込んだ `password` では検査の値が
増えるが、**`NOTION_API_KEY=...` を仕込んでも増えなかった。**

**検査を緩めて通すことは目的ではない。** 直すのは「何を鍵とみなすか」の判定であり、
**真陽性を捕まえ続けることが最優先である。**

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh
    git branch --show-current

**二つ目の値が `0` なら抑止は効いていない**（続行してよいが報告に記す）。
**三つ目が `feat/` で始まらなければ分岐が作られていない。** 定位置分岐のまま作業しない。
作業ツリーが汚れていると分岐は作られない。`git status --porcelain` を確認し、
未追跡物があれば**報告して停止する。**

| # | 禁止 |
|---|---|
| 1 | **検査を無効化する、条件を外す、閾値を緩めることで通す** |
| 2 | 試験の件数を合わせるためだけの試験を足す |
| 3 | 学習・評価コードを変更する |
| 4 | `~/.ssh/**` `~/bin/**` `~/claude-sync/**` を変更する |
| 5 | 資格情報の値を出力・記録する。**囮に本物を使わない** |
| 6 | 装置を使う |
| 7 | 外部への送信を `make task-report` 以外の経路で行う |
| 8 | 生成物を再生成する（`make context` `make taskindex` `make inbox` を実行しない） |
| 9 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 10 | `runindex/**` `context/auto/**` を手で編集する |
| 11 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |
| 12 | `tasks/*/result.yaml` の `issuer_defects` を書き換える（検出率の分母である） |

禁止 1 の理由。**偽陽性を消すだけなら検査を外せば済むが、それは欠陥を欠陥で覆うことである。**
本契約は「捕まえるべきものを捕まえたまま、捕まえてはならないものを外す」ことを要求する。

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

`inputs.data` は雛形の必須項目として残しているが、**本契約はデータも分割も参照しない。**

### 起票者からの申し送り

**直し方は指定しない。** 起票者は該当箇所の実装を読んでいない。
**実装を読んでから決めること。** 起票者が指定するのは**直ったことの確かめ方**だけである。

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | **検査が空振りでないことを、両方向の対照で確かめる**（通るべきものが通り、通らないべきものが止まる） |
| 5 | 対象の一覧そのものが正しいかを確かめる。件数を必ず出力する |
| 6 | 終了コードで判定する前に、その命令が本当に走ったかを確かめる |
| 7 | 探す対象の名前を決め打ちしない。先頭がドットのものを落とさない |
| 8 | 出力は要約せず `tasks/T-2026-08-12-tooling-defect-fixes/audit.md` へ貼る |

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 単語分割は
起きない。`git` を使う操作は `git --no-pager`。**山括弧は書かない**（リダイレクトとして
解釈される）。`ps` による計数は自己一致するため `/proc/*/cmdline` を使う。
`conventions_rev` は**実行者が実測して置換する。逸脱ではなく手順である。**

---

## Task 1 (Phase A): 修正前に、四つの欠陥が実際に発火することを測る

**Files:** Create: `tasks/T-2026-08-12-tooling-defect-fixes/audit.md`

**先に「壊れている」ことを実測する。** 直したあとに同じ測定を繰り返し、
**同じ入力で結果が変わったこと**をもって修正の証拠とする。

- [ ] **Step 1: 該当箇所の実装を読む**

    grep -n "def .*rich_text\|def .*secret\|def .*scan\|apikey\|api_key" tools/report_task.py
    grep -n "gethostname\|host_mismatch" tools/check_spec.py
    grep -n "SELF_TASK" tests/test_check_spec.py tests/test_preflight_task.py

**行番号と実際の判定式を `audit.md` へ貼る。** 以後の判断はこの実装に基づく。

- [ ] **Step 2: 欠陥 1 と 2 を測る（偽陽性と偽陰性）**

秘匿検査を関数として直接呼ぶ。**外部へは送らない。**

    .venv/bin/python - <<'PY'
    import sys; sys.path.insert(0, "tools")
    import report_task as rt
    cases = {
      "hex40_should_pass":  "commit 0123456789abcdef0123456789abcdef01234567 を参照",
      "notion_should_stop": "NOTION_API_KEY=" + "x"*40,
      "wandb_should_stop":  "WANDB_API_KEY=" + "y"*40,
      "dash_should_stop":   "api-key: " + "z"*40,
      "password_should_stop": "password=" + "q"*20,
      "plain_should_pass":  "これは普通の文章である",
    }
    for name, text in cases.items():
        print(name, "->", rt.SCAN(text))   # SCAN は Step 1 で読んだ検査関数に置き換える
    PY

**`SCAN` は Step 1 で読んだ実装の関数名に置き換える。** 返り値の形も実装に合わせる。

Expected（修正前）: `hex40_should_pass` が**止まる**（偽陽性）。
`notion_should_stop` `wandb_should_stop` `dash_should_stop` が**止まらない**（偽陰性）。
**この二つが再現しなければ前提が違う。停止して報告する（G1）。**

- [ ] **Step 3: 欠陥 3 を測る（切る単位の食い違い）**

    .venv/bin/python - <<'PY'
    import sys; sys.path.insert(0, "tools")
    import report_task as rt
    body = "あ"*1990 + "\U0001F534"*20
    for i, seg in enumerate(rt.CHUNK(body)):   # CHUNK は Step 1 で読んだ切り出し関数
        t = seg if isinstance(seg, str) else str(seg)
        print(i, "codepoints=%d utf16units=%d" % (len(t), len(t.encode("utf-16-le"))//2))
    PY

Expected（修正前）: **符号位置では二千以下だが、十六ビット単位では二千を超える切片がある。**
受け側は後者で数えるため拒否される。**超える切片が一つも無ければ前提が違う。停止する（G1）。**

- [ ] **Step 4: 欠陥 4 を測る（自ホスト名と契約への依存）**

    make task-preflight TASK=T-2026-08-12-tooling-defect-fixes 2>&1 | grep -i "spec_lint\|host_mismatch"
    .venv/bin/python -m pytest tests/test_check_spec.py tests/test_preflight_task.py -q 2>&1 | tail -5
    hostname

Expected（修正前）: `host_mismatch` の警告が出る。試験が **2 件失敗**する。
`hostname` が宣言と大文字小文字で異なる。

| # | 完了判定 |
|---|---|
| 1 | 実装の該当箇所を読み、判定式を記録した（行番号つき） |
| 2 | 偽陽性が再現した（履歴の識別子で止まる） |
| 3 | 偽陰性が再現した（区切り付きの変数名を取りこぼす。**三通りとも**） |
| 4 | 切る単位の食い違いが再現した（両方の数え方を併記） |
| 5 | 警告と試験の失敗が再現した（件数と名前） |

---

## Task 2 (Phase B): 秘匿検査を直す

**Files:** Modify: `tools/report_task.py`

**捕まえるべきものを捕まえたまま、捕まえてはならないものを外す。**

- [ ] **Step 1: 何を鍵とみなすかの判定を直す**

満たすべき性質は次の三つである。**実現方法は実装を読んで決めてよい。**

| 性質 | 内容 |
|---|---|
| A | **区切りの有無によらず変数名に一致する**（下線・ハイフン・大文字小文字を吸収する） |
| B | **履歴の識別子を鍵とみなさない**（四十桁の十六進そのものは値ではない） |
| C | **名前だけの出現では止めない**。値が続く形（代入や区切りのあと）でのみ止める |

性質 C は前契約で実行者が指摘した性質に対応する。**記録に「認証に失敗した」という
表示を書くと、その語がまた一致する。** 一致件数を合格条件にすると、
**記録を書くほど不合格に近づく。** 判定すべきは件数ではなく形である。

- [ ] **Step 2: 両方向の対照で確かめる**

Task 1 Step 2 と**同じ入力**を通す。

Expected（修正後）:

| 入力 | 期待 |
|---|---|
| `hex40_should_pass` | **止まらない** |
| `plain_should_pass` | **止まらない** |
| `notion_should_stop` | **止まる** |
| `wandb_should_stop` | **止まる** |
| `dash_should_stop` | **止まる** |
| `password_should_stop` | **止まる** |

**六件すべてが期待どおりでなければ直っていない。** 一件でも外れたら記録して停止する（G2）。

- [ ] **Step 3: 記録そのものを通してみる**

前契約の報告本文には認証失敗の表示が十件以上含まれていた。**そういう本文が
通ることを確かめる。**

    .venv/bin/python - <<'PY'
    import sys; sys.path.insert(0, "tools")
    import report_task as rt
    sample = "九台すべてが Permission denied (publickey,password) を返した。"
    print("report_like ->", rt.SCAN(sample))
    PY

Expected: **止まらない。** 止まるなら性質 C が満たされていない。

- [ ] **Step 4: 試験を足す**

**件数を合わせるための試験ではない。** 上の六件と Step 3 を試験として固定し、
**将来この欠陥が再発したら落ちる**ようにする。囮の値は明らかな作り物を使い、
**本物の資格情報を書かない。**

| # | 完了判定 |
|---|---|
| 6 | 六件の対照がすべて期待どおり（一件ずつ実測値を記載） |
| 7 | 報告に似た本文が止まらない |
| 8 | 試験を足し、修正前の実装では落ちることを確かめた（**陽性対照**） |

---

## Task 3 (Phase B): 本文を切る単位を受け側に合わせる

**Files:** Modify: `tools/report_task.py`

- [ ] **Step 1: 切る単位を直す**

受け側は十六ビット単位で数える。**符号位置ではなく、その単位で上限に収める。**
**代理対の途中で切らないこと**（切ると文字が壊れる）。

- [ ] **Step 2: 対照で確かめる**

Task 1 Step 3 と同じ入力を通す。

Expected: **すべての切片が十六ビット単位で二千以下。** かつ**連結すると元の本文に戻る。**

    連結した結果 == 元の本文  →  True

**戻らないなら文字を壊している。** 記録して停止する（G2）。

- [ ] **Step 3: 境界の入力でも確かめる**

    基本多言語面の外の文字だけの本文 / 面の外の文字が上限の境目にまたがる本文 /
    面の内側だけの長い本文

**三通りとも、切片が上限以下で、連結すると元に戻ること。**

| # | 完了判定 |
|---|---|
| 9 | 全切片が受け側の単位で上限以下（実測値を記載） |
| 10 | 連結すると元の本文に戻る（三通りの境界で確認） |

---

## Task 4 (Phase C): 自ホスト名と契約への依存を外す

**Files:** Modify: `tools/check_spec.py`, `tests/test_check_spec.py`, `tests/test_preflight_task.py`

- [ ] **Step 1: ホスト名の比較を直す**

`socket.gethostname()` が返す値と契約の宣言を比べる際、**大文字小文字の差で
警告が出ないようにする。** ただし**別ホストの契約を実行したときは警告が出続けること。**

- [ ] **Step 2: 両方向の対照**

| 入力 | 期待 |
|---|---|
| 自ホストの契約（大文字小文字が違うだけ） | **警告が出ない** |
| 明らかに別ホストの契約 | **警告が出る** |

**後者が出なくなったら検査を壊している。**

- [ ] **Step 3: 試験が特定の契約に依存しないようにする**

`SELF_TASK` が一つの契約を固定で読むため、**その契約を宣言したホスト以外では必ず落ちる。**
実行中の契約を動的に見つけるか、依存しない形にする。**実現方法は実装を読んで決める。**

- [ ] **Step 4: 全体の試験を回す**

    .venv/bin/python -m pytest -q 2>&1 | tail -5

Expected: **本契約が対象とする 2 件の失敗が消える。** 残る失敗（環境起因の 5 件）は
**本契約の対象外であり、増えていないことだけを確かめる。**

**「全部緑になった」ことを目標にしない。** 減った件数と、残った件数と、
**残った理由**を書く。

| # | 完了判定 |
|---|---|
| 11 | 自ホストの契約で警告が出ない |
| 12 | 別ホストの契約では警告が出る（**検査を壊していない**） |
| 13 | 試験の失敗が 2 件減った（修正前後の件数を併記） |
| 14 | 残った失敗の件数と理由を記載した |

---

## Task 5 (Phase D): 検証し、送出し、報告する

**Files:** Create: `tasks/T-2026-08-12-tooling-defect-fixes/RESULT.md`,
`tasks/T-2026-08-12-tooling-defect-fixes/result.yaml`,
`tasks/inbox.d/T-2026-08-12-tooling-defect-fixes.md`

- [ ] **Step 1: 完了判定 14 項目を一つの表にまとめ、実測値または `UNKNOWN` を記す**

**「実施した」ではなく「何が出たか」を書く。修正前と修正後を併記する。**

- [ ] **Step 2: `conventions_rev` を実測して置換する**

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 3: 検証を通す**

    make task-validate TASK=T-2026-08-12-tooling-defect-fixes; echo "validate_exit=$?"
    make task-preflight TASK=T-2026-08-12-tooling-defect-fixes; echo "preflight_exit=$?"
    make forbidden-check; echo "forbidden_exit=$?"

**`host_mismatch` は本契約で直した対象である。** ここで警告が出たら直っていない。

- [ ] **Step 4: 判断の受け皿へ置く**

`tasks/inbox.d/T-2026-08-12-tooling-defect-fixes.md` に**起票者が次の判断に使える事実だけ**を置く。

- [ ] **Step 5: 変更範囲と未解決を行数で確かめる**

    git --no-pager status --porcelain > /tmp/wt.txt; wc -l /tmp/wt.txt; cat /tmp/wt.txt
    git --no-pager diff --name-only origin/phase0...HEAD > /tmp/ch.txt
    echo "changed=$(wc -l < /tmp/ch.txt)"; cat /tmp/ch.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un.txt
    echo "unmerged=$(wc -l < /tmp/un.txt)"; cat /tmp/un.txt

**変更は `tools/` と `tests/` と本契約のディレクトリと受け皿に限られること。**
それ以外があれば停止して報告する。

- [ ] **Step 6: 送信前の自己検査**

    .venv/bin/python - <<'PY'
    import pathlib, re
    for f in ["RESULT.md", "result.yaml", "audit.md"]:
        p = pathlib.Path("tasks/T-2026-08-12-tooling-defect-fixes") / f
        if not p.exists(): continue
        s = p.read_text(encoding="utf-8")
        print("%s bmp_over=%d hex40=%d" % (f, sum(1 for c in s if ord(c) > 0xFFFF),
              len(re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])", s))))
    PY

**本契約は `hex40` を許すよう道具を直しているが、この自己検査は修正の有無に
かかわらず回す。** 零でない場合、**それが道具側で通ることを Task 2 の対照で
確かめてあること**を報告に書けば送ってよい。

- [ ] **Step 7: commit する**

    git add tools/ tests/ tasks/T-2026-08-12-tooling-defect-fixes/ tasks/inbox.d/T-2026-08-12-tooling-defect-fixes.md
    git commit -m "fix(tooling): correct secret scan, utf-16 chunking, host compare and test coupling"
    git --no-pager log -1 --format='%h %s'

- [ ] **Step 8: 分岐を送出し、PR を作る**

    git fetch origin && git merge origin/phase0
    git push -u origin HEAD
    git --no-pager status -sb
    gh pr list --head "$(git branch --show-current)" --json number,isDraft,state
    command -v gh && gh pr create --base phase0 --fill || echo "gh 不在。push まで完了"

**上流が設定され `ahead` が零になったことを確認する。push は統合ではない**が、
**phase0 への取り込みは行わない。同じ head と base の PR は二本作れない。**
常駐処理が下書きを自動起票していることがあるため、**先に一覧で確認し、
存在すれば新規作成せず本文を更新する。番号と下書きの別を報告に書く。**

- [ ] **Step 9: 抑止を解除し、報告を台帳へ返す**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-tooling-defect-fixes 2>/dev/null \
      && echo "released" || echo "解除に失敗。手当てが要る"
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"
    make task-report TASK=T-2026-08-12-tooling-defect-fixes; echo "exit=$?"

**この送信が、本契約で直した道具を通る最初の実地の試行である。**
止まったり拒否されたりしたら、**それ自体が測定結果である。記録する。**

| # | 完了判定 |
|---|---|
| 15 | 14 項目すべてに実測値または UNKNOWN がある（修正前後を併記） |
| 16 | 変更が `tools/` `tests/` と契約の範囲に限られる |
| 17 | 分岐が送出されている（上流が設定され ahead が零） |
| 18 | PR が存在する（番号と下書きの別。既存を更新した場合はその旨） |
| 19 | 抑止が repo 直下から消えている |
| 20 | 報告が台帳へ返っている（終了コード。**直した道具を通った実地の結果**） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| 修正前に欠陥が再現しない | **停止して報告**（G1）。前提が違う。直す対象が別にある |
| 真陽性が止まらない、別ホストの契約で警告が出ない | **停止して報告**（G2）。**検査を壊している。緩めて通してはならない** |
| 連結すると元の本文に戻らない | **停止して報告**（G2）。文字を壊している |
| 試験の失敗が 2 件より多く減った | 記録して続行。**理由を特定する。偶然消えたのなら不安定な試験である** |
| 試験の失敗が増えた | **停止して報告。** 本契約が壊したものを特定する |
| 分岐が `feat/` で始まらない | **停止して報告。** 定位置分岐のまま作業しない |
| 報告の送信が止まる、または拒否される | **記録して原因を特定する。** 直したはずの道具の実地の結果である |
| 抑止の解除に失敗した | 残っている場所を報告に明記する。自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

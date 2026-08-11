# 手順書を実装系のシェル挙動に依存しない形へ直す

**task_id:** `T-2026-08-11-codex-parity`
**kind:** `impl`  **depends_on:** `T-2026-08-18-report-back-to-ledger`
**実行ホスト:** `efros`（repo は `~/slocal/m2`）

## Goal

第二の実装系を第一の実装系の代わりに常用する方針が決まった。手順書の本体は
symlink で共有されており、内容の乖離は無い。**それでも手順は完結しない。**

起票者が第二の実装系で実測した結果は次のとおり。

| 事項 | 実測 |
|---|---|
| 手順書の実体と起動 | symlink は健在で内容も最新。手順書を読み、識別子が無いので正しく停止した |
| **シェルの状態** | 別々の命令として与えると**引き継がれない**。変数も仮想環境も未設定になる |
| 通信 | 到達する。ただし**承認の入力を求められる** |
| 隔離 | 読み取りだけの命令が起動できず、**権限を上げて再実行**された |

手順書は資格情報の読み込みと後続の操作を**別々の行**に書いている。第一の実装系は
同じシェルを保つため通るが、第二の実装系では前の行の効果が次の行に届かない。

| 操作 | 第二の実装系での帰結 |
|---|---|
| 契約の取り込み | 資格情報が載らず**取り込めない** |
| 報告の返却 | 同上。**返せない** |
| 実行直前の検査 | 仮想環境の項目が **FAIL** して止まる |

過去に通ったのは実装系が自分の判断で 1 行に繋いだためである。
**手順書は繋ぐことを求めていない。繋がなければ止まる。偶然に依存している。**

したがって手順書を「**1 つの命令で完結する形**」へ直し、その規約を機械で検査する。

## 0. 前提と禁止事項

分岐の作成と契約の取り込みは配布時の命令で済んでいる。**抑止の目印を確かめる。**

    cd ~/slocal/m2 && ls .sync-pause >/dev/null 2>&1 && echo "抑止あり" || touch .sync-pause

**このホストの repo パスは他ホストと異なる。** 仮想環境と資格情報は
**各操作と同じ命令の中で読み込む**。これが本 task の主題である。

報告まで終えたら `rm -f .sync-pause` を実行し、消えたことを確認する。

| # | 禁止 |
|---|---|
| 1 | `runindex/**` `context/auto/**` を**手で**編集する（生成は可） |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |
| 3 | `context/conventions.md` を変更する |
| 4 | 学習・評価コードを変更する |
| 5 | `tools/harvest_runindex.py` `tools/build_context.py` を変更する |
| 6 | **`~/claude-sync/**` 配下を変更する**（読むのは可。配布の経路が未特定） |
| 7 | **系の設定を恒久化する**（一時的に変えて測るのは可。Phase A に手順がある） |
| 8 | 資格情報の値を出力・記録する |
| 9 | 配布台帳の**他の行**を変更・削除する |
| 10 | 演算装置を使う |
| 11 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 12 | 統合する。自動統合を有効化する |

禁止 7 の補足。**一時的な適用と恒久化は別である。** 一時的に変えて挙動を測り、
元へ戻すことは本 task が求める作業であり逸脱ではない。恒久化は全ホストへ影響するため
判断を返す。

### 起票者からの申し送り

起票者の検査命令が検証対象を検証できていない誤りが **18 task 連続**で発生している。
**直近では本 task の調査そのもので犯した。** 第二の実装系の設定を探す命令を repo の
内側に限定したため、設定の実体が repo の外にあることを構造的に見落とした。
利用者が別の場所を提示して初めて判明した。型は `check_does_not_check` である。

実行環境の対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲むこと。**
配列の添字による終了コードの取得は使えない。単語分割も起きない。

**このホストには対話用の頁送りが無い。** 履歴を読む操作は `git --no-pager` を使うこと。
素で実行すると起動に失敗する（起票者が実測済み）。

**本 SPEC の検査も同型の誤りを含みうる。** 次を守ること。

| # | 注意 |
|---|---|
| 1 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 4 | 検査が空振りでないことを陽性対照で確かめる |
| 5 | **対象の一覧そのものが正しいかを確かめる**（本 task の調査で起票者が破った項目） |

---

# Phase A — 実装系の差を実測する

## Task 1: シェルの状態が引き継がれるか

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 引き継がれない側を測る**

第二の実装系に、**別々の命令として**次を順に実行させる。1 つにまとめさせない。

    (1) export PROBE_ALIVE=yes; cd ~/slocal/m2; source .venv/bin/activate; echo done
    (2) echo "PROBE=${PROBE_ALIVE:-未設定} VENV=${VIRTUAL_ENV:-未設定}"

Expected: (2) が両方とも未設定を返す

- [ ] **Step 2: 引き継がれる側を測る（陽性対照）**

**同じ実装系で、1 つの命令にまとめて**実行させる。

    cd ~/slocal/m2 && source .venv/bin/activate && echo "VENV=${VIRTUAL_ENV:-未設定}"

Expected: 仮想環境の位置が表示される

**片方だけでは何も示せない。** 同じ実装系で繋げば引き継がれることを示して初めて言える。

- [ ] **Step 3: 第一の実装系でも測る（対照）**

素のシェルで Step 1 と同じ 2 つを別々に打ち、引き継がれることを確認する（実装系の差であって環境の差ではないことを示すため）。

- [ ] **Step 4: 実行直前の検査への影響を測る**

まず引き継がれない形。

    make task-preflight TASK=T-2026-08-18-report-back-to-ledger; echo "exit=$?"

次に繋いだ形。

    source .venv/bin/activate && make task-preflight TASK=T-2026-08-18-report-back-to-ledger; echo "exit=$?"

Expected: 前者は仮想環境の項目が FAIL、後者は PASS

**組み立ての規則を経由すると終了コードが変わる。両方を記録すること。**

## Task 2: 隔離と通信と権限

**Files:** なし（読み取りのみ。Step 3 のみ一時的に変更し元へ戻す）

- [ ] **Step 1: 現在の状態を測る**

    sysctl kernel.unprivileged_userns_clone kernel.apparmor_restrict_unprivileged_userns 2>&1; cat /proc/sys/user/max_user_namespaces 2>&1

**どれが効いているかを推測しない。** 3 つとも記録する。

- [ ] **Step 2: 権限を上げられるか測る**

    sudo -n true 2>&1; echo "exit=$?"

Expected: 成功か失敗かのいずれかが確定する

**失敗した場合、Step 3 は実施できない。** その事実を記録して次へ進む。
**利用者に対話で入力を求めない。**

- [ ] **Step 3: 一時的に変えて測る（Step 2 が成功した場合のみ）**

変更前に現在値を記録してから変える。

    sudo sysctl -w kernel.unprivileged_userns_clone=1 2>&1

第二の実装系に読み取りだけの命令を実行させ、**権限を上げずに通るか**を測る。
測り終えたら**必ず元の値へ戻す**。戻したことを再度読んで確認する。

**恒久化はしない。起動時に読まれる設定へは書かない。**

- [ ] **Step 4: 通信を測る**

第二の実装系に、資格情報を伴わない到達確認を実行させる。承認を求められたら承認する。

Expected: 到達する。承認の入力が求められる

**承認が求められた事実そのものを記録する。** 非対話では承認できないため、
ここで自動化の可否が決まる。

Phase A の実測はすべて報告へ書く。**表示のために切り詰めない。記録を作ってから表示する。**

## Task 3: 手順書の棚卸し

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 対象の一覧を作り、その一覧が正しいか確かめる**

現行の手順を書いた文書を列挙し、**件数を表示する**。

    git ls-files ".claude/skills/task/SKILL.md" "tasks/README.md" "CLAUDE.md" "Makefile" "docs/*.md" > /tmp/agent_docs.txt
    wc -l /tmp/agent_docs.txt

**先頭がドットで始まる経路が落ちていないかを確かめる。** 過去に同じ落とし方で
17 文書が静かに欠けた実績がある。`.claude` で始まる行が一覧に含まれることを目視する。

**組み立ての規則にも同じ問題がある。** `task-start` の説明は読み込みを先に行うことを
求めているが、その形では第二の実装系で完結しない。説明も対象に含める。

手順書の実体は 1 つで、第二の実装系へは symlink で共有されている。
**片方を直せば両方に効く。二重に直さない。**

- [ ] **Step 2: 資格情報と仮想環境の読み込みが単独行になっている箇所を探す**

一覧の各文書について、読み込みを含む行を行番号つきで列挙する。

    xargs -a /tmp/agent_docs.txt grep -n "source " > /tmp/agent_source_lines.txt
    wc -l /tmp/agent_source_lines.txt
    cat /tmp/agent_source_lines.txt

- [ ] **Step 3: 0 件なら探し方を疑う**

Step 2 が 0 件だった場合、語と経路の与え方を変えても 0 件であることを示してから
「無い」と結論する。**存在確認を先に行うこと。**

- [ ] **Step 4: 直す対象を確定する**

後続の操作と同じ命令に入っていない行を**直す対象**とし、単独で完結している行と
説明のための引用は直さない。**件数だけでなく、どの行をどちらにしたかを残す。**

---

# Phase B — 手順書を直し、検査を足す

## Task 4: 手順書を単独の実行で完結する形へ直す

**Files:** Modify `.claude/skills/task/SKILL.md`、Modify `tasks/README.md`

- [ ] **Step 1: 規約を決めて冒頭に書く**

次の規約を手順書へ明記する。

    ## 命令の書き方
    実装系によっては命令ごとに新しいシェルが起きる。前の命令で読み込んだ
    仮想環境や資格情報は次へ引き継がれない。したがって手順書のすべての命令は
    単独で実行して完結する形で書き、読み込みは同じ命令の中に入れる。

- [ ] **Step 2: Task 3 Step 4 で直す対象とした行を直す**

読み込みを後続の操作と同じ命令に入れる。例を 1 つ挙げる。

    source scripts/load_env.sh && make task-notion TASK=<task_id>

**すべての対象について同じ形にする。** 直した行の一覧を記録する。

- [ ] **Step 3: 実装系の差の節を足す**

手順書に次の 3 点を書く。**推測を書かない。Phase A の実測だけを書く。**

| 事項 | 書く内容 |
|---|---|
| シェル | 引き継がれない実装系がある。命令は単独で完結させる |
| 通信 | 外部への通信で承認を求められることがある。承認して進む |
| 履歴 | 頁送りが無いホストがある。履歴を読む操作は `git --no-pager` を使う |

- [ ] **Step 4: 変更の前後を集合差で確かめる**

**名前の部分一致で探さない。** 変更前後で手順書に現れる操作の集合を作り、差を取る。

    git show HEAD:.claude/skills/task/SKILL.md > /tmp/skill_before.md
    grep -o "make [a-z-]*" /tmp/skill_before.md | sort -u > /tmp/ops_before.txt
    grep -o "make [a-z-]*" .claude/skills/task/SKILL.md | sort -u > /tmp/ops_after.txt
    diff /tmp/ops_before.txt /tmp/ops_after.txt; echo "exit=$?"

Expected: 操作の集合が減っていない

**減っていたら直しすぎている。** 停止して報告する。

- [ ] **Step 5: commit**

## Task 5: 規約を機械で検査する

**Files:** Create `tools/check_agent_docs.py`、Create `tests/test_check_agent_docs.py`、
Modify `Makefile`

- [ ] **Step 1: 検査を実装する**

読み込みを含む行が、後続の操作と同じ命令に入っているかを検査する。対象の一覧は
Task 3 Step 1 と**同じ作り方**にし、二重管理を作らない。出力は機械可読とし、
違反があれば終了コードを非ゼロにする。

- [ ] **Step 2: 検査が空振りでないことを双方向で確かめる**

違反する記述と、違反しない記述の**両方**を作って測る。

    printf 'source scripts/load_env.sh\nmake task-notion TASK=x\n' > /tmp/bad_doc.md
    printf 'source scripts/load_env.sh && make task-notion TASK=x\n' > /tmp/good_doc.md
    python tools/check_agent_docs.py --path /tmp/bad_doc.md; echo "bad_exit=$?"
    python tools/check_agent_docs.py --path /tmp/good_doc.md; echo "good_exit=$?"

Expected: 前者は非ゼロで違反した行が示され、後者は 0

**両方を測らなければ検査の有効性は言えない。** 片方だけの確認で通したことにしない。

- [ ] **Step 3: 対象の一覧が縮んでも通らないようにする**

検査の対象が 0 件だった場合、**通さずに失敗させる**。
過去に一覧が静かに縮んで検査が素通りした実績がある。件数を出力に含める。

わざと一覧を空にして、失敗することを確かめる。

- [ ] **Step 4: 試験を書く**

Step 2 と Step 3 を試験として固定する。件数は実測して記録する。

- [ ] **Step 5: Makefile へ足す**

**挿入位置に注意する。既存のレシピの途中へ入れない。** 追加後、

    python tools/check_agent_docs.py; echo "script_exit=$?"
    make agent-check; echo "make_exit=$?"

Expected: 両方を記録する。**失敗時の値が異なることを前提とする**

- [ ] **Step 6: commit**

---

# Phase C — 第二の実装系だけで契約を通す

## Task 6: 実行と報告の返却

**Files:** Create `tasks/T-2026-08-11-codex-parity/{RESULT.md,result.yaml}`、
Create `tasks/inbox.d/T-2026-08-11-codex-parity.md`

- [ ] **Step 1: `conventions_rev` を実測して置換する**

起票者は現在の値を知り得ない。**実行者が実測して置換する。これは逸脱ではなく手順である。**
`deviations` には書かない。

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 2: 自己検証**

`make task-validate`、`make task-preflight`、`make agent-check`、`make docs-check`、
`make inbox-check`、`make taskindex-check` をいずれも exit 0 にする。

**すべて読み込みと同じ命令の中で実行すること。** 本 task が求めている形である。

- [ ] **Step 3: 完了判定**

| # | 判定 | 期待 |
|---|---|---|
| 1 | シェルが引き継がれないことを双方向で測った | 記録あり |
| 2 | 実行直前の検査が形によって結果が変わることを測った | 記録あり |
| 3 | 隔離と権限の状態を測った | 記録あり |
| 4 | 通信で承認が要ることを測った | 記録あり |
| 5 | 手順書の命令が単独で完結する | 検査が exit 0 |
| 6 | 検査が違反を検出する | 陽性対照で非ゼロ |
| 7 | 検査が誤検出しない | 陰性対照で 0 |
| 8 | 対象が空なら検査が失敗する | 非ゼロ |
| 9 | 操作の集合が減っていない | 差が無い |
| 10 | 実装系の差が手順書に書かれている | 3 点とも記載 |
| 11 | 契約検証が通る | exit 0 |
| 12 | 実行直前の検査が通る | exit 0 |
| 13 | 試験が不変 | **開始前を先に測ってから比較する** |
| 14 | 禁止領域が無変更 | 出力なし |
| 15 | 系の設定が元に戻っている | 変更前と同じ値 |
| 16 | 抑止の目印を解除した | ファイルが無い |

判定 13 の基準はホストによって異なる。**別ホストの値を持ち込まない。** 開始前に
測っていなければ `UNKNOWN` とする。判定 14 の対象は次のとおり。

    git diff --name-only origin/phase0...HEAD -- runindex/ context/auto/ context/conventions.md experiments/ transfer/ data/splits/ tools/harvest_runindex.py tools/build_context.py

- [ ] **Step 4: 記録を書く**

`RESULT.md` と `result.yaml` を対で書く。**散文から値を抜かない。** 起票者の誤りの型は
`check_does_not_check` `asserted_without_measuring` `self_contradiction` `shell_assumption`
の 4 語である。`deviations` を空にしない。判断は
`tasks/inbox.d/T-2026-08-11-codex-parity.md` へ 1 行以上。無い場合も「なし」と残す。

- [ ] **Step 5: 起票**

分岐 `feat/codex-parity` から `phase0` へ起票する。**統合しない。自動統合も有効化しない。**

- [ ] **Step 6: G3 — 報告を第二の実装系から返す**

**これが本 task の目的そのものである。** 第二の実装系から次を実行する。
あわせて、**契約の取り込みがどの実装系から行われたか**も記録する。

    source scripts/load_env.sh && make task-report TASK=T-2026-08-11-codex-parity

Expected: 台帳の該当行が `done` になり、報告の本文が読める

**秘匿の検査で止まったら本文を直して送り直す。検査を無効にしない。** 承認を求められたら
承認する。**通らなくても自動で停止せず、原因を記録して次へ進む。**

- [ ] **Step 7: 抑止を解除する**

    rm -f .sync-pause
    ls .sync-pause 2>/dev/null && echo "残っている" || echo "解除済み"

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| シェルが引き継がれた | 前提が覆る。**G1 停止。** 測り方と結果を報告する |
| 権限を上げられない | Task 2 Step 3 を飛ばす。事実を記録し、恒久化の可否は判断を返す |
| 変更を元へ戻せない | **即座に報告。** `sandbox_requires_privilege` |
| 検査の対象が 0 件 | **別の探し方でも 0 件か確かめる。** 一覧の作り方を疑う |
| 陽性対照が検出されない | その検査は無効。**G2 停止** |
| 陰性対照が誤検出される | 対象を絞る。**検査を無効にしない** |
| 操作の集合が減った | 直しすぎ。停止して報告 |
| 報告の返却が通らない | **自動で停止しない。** 原因を記録し、代替の経路と併せて判断を返す |
| 秘匿が送られそうになった、または台帳の他の行が変わった | **即座に停止して報告** |
| 常駐処理による統合が起きた | 実行者の逸脱ではない。**事実として記録する** |
| 試験の失敗が増えた | 本 task が壊した。停止して報告 |

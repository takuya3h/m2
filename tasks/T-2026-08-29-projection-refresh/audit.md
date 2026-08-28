# audit — T-2026-08-29-projection-refresh

証跡の記録。命令とその出力・差分の一覧・検査の出力。事実の記録は `RESULT.md`。
**同じ内容を二度書かない。**

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/projection-refresh`

---

## 取り込み — 二度失敗している

    1 回目: [task-start] 作業ツリーに未commitの変更が 8 件あります
    2 回目: 取り込みを中止しました: 配布台帳の本文が空です: T-2026-08-29-projection-refresh

いずれも exit 2。1 回目は開始前から在った汚れ（退避へ）、2 回目は台帳側の空本文（起票者が
本文を追加して解決）。**二度目の取り込みで成功。**

---

## Task 1 開始の記録

    $ TZ=Asia/Tokyo date '+JST %Y-%m-%d %H:%M:%S'; date -u '+UTC %Y-%m-%dT%H:%M:%SZ'; date +%s
    JST 2026-08-29 03:41:05
    UTC 2026-08-28T18:41:05Z
    epoch=1787942465

    $ git --no-pager status --porcelain
    ?? tasks/T-2026-08-29-projection-refresh/
    件数: 1（汚れなし。前の契約群の分は退避に隔離済み）

---

## Step A-1 プレースホルダの置換

    runindex_commit = 7918b5dd9aab3d15b3c459f87aebdd9eb1653116
    conventions_rev = a8c07e813696d3720ceee648e8aa202224285955
    index.csv=1177 experiments.csv=213 verdicts.csv=1038

**前契約の記録と完全一致。** 統合はこの三つの csv に触れていない。

    $ make task-validate TASK=T-2026-08-29-projection-refresh
    OK   T-2026-08-29-projection-refresh
    validate exit=0（WARN 無し）

### L3（回答前）

    P6 decisions_answered     FAIL 未回答 1 件: 退避の中身のうち、版管理へ記録する規約に当たらないものの処分
    RESULT: 4 PASS / 0 WARN / 4 SKIP / 1 FAIL
    preflight exit=2

**列挙して利用者へ提示し停止した。自分で決めていない。**
退避の中身を実測してから具体的な項目を提示する必要があったため、Phase A を先に進めた。

---

## Step A-2 統合の完了確認

    $ git --no-pager log --oneline origin/phase0 | grep '#160'
    10ef753e Merge pull request #160 from takuya3h/feat/policy-v2-doc-sync
    → 起点に前契約の変更が入っている

    $ gh pr list --state open --json number
    []                                              → 開いている PR 0 件

    $ git --no-pager branch -r --list 'origin/exp/philip'
    （0 件。philip の定位置分岐は移行未実施で `exp/philip-wip-20260703` のまま）

    $ git --no-pager rev-list --count origin/phase0..origin/exp/philip-wip-20260703
    0                                                → 未統合の commit 無し

**未統合の変更は残っていない。** 一台で一度だけ回す前提を満たす。

---

## Step A-3 再生成前の状態

    $ make context-check    → exit=2   差分: STATE.md / experiments_summary.csv / open_questions.md / verdicts_summary.csv
    $ make taskindex-check  → exit=2   差分: tasks_summary.csv / followups.md / results_recent.md
    $ make inbox-check      → exit=2   差分: inbox.md

出力ファイルの一覧と要約値（再生成前）

    context/auto/STATE.md                          85 行  sha256 98e242fbfe05ad3e…
    context/auto/experiments_summary.csv          209 行  sha256 b60e22b1e6ba2695…
    context/auto/open_questions.md                 54 行  sha256 d7d377dffd8d5835…
    context/auto/verdicts_summary.csv             138 行  sha256 c19e7f35b4533ea1…
    context/auto/tasks_summary.csv                 66 行  sha256 dc8405c8dc66ae62…
    context/auto/followups.md                     913 行  sha256 1aa09d38a8b7e237…
    context/auto/results_recent.md                240 行  sha256 1b2b7ce6053d6826…
    tasks/inbox.md                                376 行  sha256 4eb61c6335b66b66…

索引の件数は Step A-1 と同一（1177 / 213 / 1038）。

---

## Step A-4 退避と抑止の実測

### 退避の一覧

    stash@{0}: On feat/issuer-refs-to-repo: T-2026-08-29-projection-refresh: 契約開始前から在った汚れの退避（.stglobalignore の変更 + 未追跡 7 件）
      作成時刻: 2026-08-28 18:13:58 +0000
      追跡済み: .stglobalignore（M）
      未追跡（23 ファイル）: .sync-pause.released / docs/sessions/digest/ 3 件 /
        experiments/analysis/{error_shape_selectivity,lovo_decision_rule,official_split_reassessment}/ 計 19 件

    stash@{1}: On feat/error-shape-selectivity: pre-oracle-ceiling-lovo
      作成時刻: 2026-08-26 06:26:01 +0000（他の契約が作成。本契約より前から存在）
      未追跡: .sync-pause.released / experiments/analysis/lovo_decision_rule/ 9 件

**SPEC §1 の記述「前契約が残した退避は二件」は、実測では今回の 2 件とは対応が取れない。**
`stash@{0}` は**本契約の取り込み直前**（2026-08-28 18:13:58）に実行者が作ったもので、
`policy-v2-doc-sync` 契約そのものではなく、その報告後の housekeeping で生じた汚れである。
`stash@{1}` は 2026-08-26 作成で `policy-v2-doc-sync`（2026-08-28）より**前**にできている。
**「前契約が残した二件」という時系列の対応は実測と食い違う。**

### 抑止の目印

    $ [ -e .sync-pause ] && echo 在る
    在る
    $ stat -c '%y' .sync-pause
    2026-08-28 18:40:57.265713310 +0000

    $ grep -n 'sync-pause' scripts/task_start.sh
    37:PAUSE_MARKER=".sync-pause"    # 常駐同期の抑止。既にあれば触れない

🔴 **この `.sync-pause` は前契約の残骸ではない。** `task_start.sh:37` のコメントが示すとおり、
**既に存在すれば触れない**（作成ログを出さない）実装である。今回の `task-start` の出力は
「`.sync-pause` を作成」であり、mtime は契約開始（18:41:05）の 8 秒前 = **今回新規に作られたもの。**

前契約（`policy-v2-doc-sync`）は `RESULT.md` に記録したとおり `mv .sync-pause .sync-pause.released`
で正しく解除しており、その `.sync-pause.released` は `stash@{0}` の中に退避として存在する。
**SPEC §3 Step A-4 の「存在する場合、前契約が解除しなかったことを意味する」は、この実測とは
異なる。** 「常駐は分岐ごとに毎回新規作成される」ため、在ること自体は前契約の失敗を意味しない。

### 抽出物の置き場

    $ find docs/sessions/digest -maxdepth 1 -type f | （追跡外の確認）
    作業ツリー: 0 件（退避へ隔離済み）
    stash@{0} 内: 3 件（docs/sessions/digest/2026-08-22 / 23 / 24）
    stash@{1} 内: 0 件

---

## Task 1 投影三種の再生成

    $ make context && make taskindex && make inbox
    context: exit=0 / taskindex: exit=0 / inbox: exit=0

    $ make context-check / taskindex-check / inbox-check
    exit=0 / exit=0 / exit=0

差分は生成器の出力 8 ファイルのみ（`context/auto/` 7 件・`tasks/inbox.md` 1 件）。

### 想定外 — 空振り確認で再生成の成果を一度失った

判定 a の空振り確認で `git checkout -- context/auto/STATE.md` を使ったところ、
**1 文字の取り消しではなく、Task 1 で再生成した内容ごと HEAD（再生成前の古い版）へ
戻ってしまった。** まだ commit していなかったため、`checkout --` は「作業ツリーの変更」を
丸ごと破棄する。**手で直さず**、`make context` を再実行して修復した。

    修復後の context-check: exit=0

以後の空振り確認は `cp` で複製してから戻す方式に変更した（`git checkout --` を使わない）。

### 判定 a 空振り確認（三生成器それぞれ・修復後）

    対象: STATE.md（context 系）
      一文字追加 → context-check exit=2 / taskindex-check exit=0 / inbox-check exit=0
      復元（cp）→ sha256 一致 🟢 → context-check exit=0

    対象: tasks_summary.csv（taskindex 系）
      一文字追加 → taskindex-check exit=2 / context-check exit=0 / inbox-check exit=0
      復元（cp）→ sha256 一致 🟢 → taskindex-check exit=0

    対象: inbox.md（inbox 系）
      一文字追加 → inbox-check exit=2 / context-check exit=0 / taskindex-check exit=0
      復元（cp）→ sha256 一致 🟢 → inbox-check exit=0

**それぞれ対応する検査だけが非零になり、他は波及しない。** 復元後は三つとも exit 0。

### 判定 b 再生成前後の比較

    再生成前（Step A-3）                          再生成後
    STATE.md               85行 98e242fbfe05ad3e   85行 9eaa0252b9978423
    experiments_summary.csv 209行 b60e22b1e6ba2695  215行 ac28d29737435b23
    open_questions.md       54行 d7d377dffd8d5835   54行 dc7051039e09e9f6
    verdicts_summary.csv   138行 c19e7f35b4533ea1  138行 7b2cc5d9c1cbcb97
    tasks_summary.csv       66行 dc8405c8dc66ae62   76行 260bbdb16b5fc6da
    followups.md           913行 1aa09d38a8b7e237 1066行 df792d8b73382fcc
    results_recent.md      240行 1b2b7ce6053d6826  225行 cd8a40dfba1d0bfb
    inbox.md               376行 4eb61c6335b66b66  427行 e382894f29a52538

**8 ファイルすべて内容が変わった。** 再生成前の終了コード（全て exit 2）が
再生成後（全て exit 0）へ変わったことと合わせて、再生成が実際に働いたことを示す。

### 判定 c 変更範囲

    $ git --no-pager status --porcelain
     M  .stglobalignore
      M context/auto/{STATE.md,experiments_summary.csv,followups.md,open_questions.md,
                       results_recent.md,tasks_summary.csv,verdicts_summary.csv}
     A  docs/sessions/digest/2026-08-{22,23,24}-*.md
      M tasks/inbox.md
     ?? tasks/T-2026-08-29-projection-refresh/
     ?? tasks/inbox.d/T-2026-08-29-projection-refresh.md

**§2 の対象（投影の出力・退避から復帰した抽出物）と契約ディレクトリ・受け皿のみ。対象外 0 件。**

### 判定 d 索引が変わっていないこと

    $ git --no-pager status --porcelain runindex/
    （0 件）
    空振り確認: tasks/T-2026-08-29-projection-refresh/ の変更 = 1 件（一件以上出る）

### 判定 e 禁止領域

    $ make forbidden-check
    changed=16 checked=8 status=pass violations=0
    除外ディレクトリ: ['context/auto/']  除外ファイル: ['tasks/inbox.md']

16 件のうち生成物 8 件を除外し、残り 8 件（契約ディレクトリ 3 + digest 3 + .stglobalignore 1 +
inbox.d 1）が検査対象。**違反 0 件。**

---

## Task 2 退避の整理

### 衝突の確認

    stash@{1}（.sync-pause.released・lovo_decision_rule）
      .sync-pause.released: 作業ツリーに無い（衝突しない）
      lovo_decision_rule/: 作業ツリーに**既に存在**（92 ファイル追跡下、origin/phase0 に統合済み）
        → 禁止領域配下。復帰しない

    stash@{0}
      .stglobalignore: 追跡済み変更として復帰可能
      digest 3 件: 未追跡として復帰可能
      .sync-pause.released: 判断待ち（版管理の記録規約に当たらない）
      experiments/analysis/{error_shape_selectivity,lovo_decision_rule,official_split_reassessment}/
        19 ファイル: 禁止領域配下。復帰しない

### 禁止領域の要約値照合（触らず、結果だけ報告）

    lovo_decision_rule（stash@{1} の 9 件）            対 正本: 一致 9 / 不一致 0
    lovo_decision_rule（stash@{0} の 9 件）            対 正本: 一致 9 / 不一致 0
    error_shape_selectivity（stash@{0} の 7 件）       対 正本: 一致 7 / 不一致 0
    official_split_reassessment（stash@{0} の 3 件）   対 正本: 一致 3 / 不一致 0

**全 28 件が追跡下の正本と一致。触っていない。消していない。**
（正本の総ファイル数は lovo_decision_rule 92 / error_shape_selectivity 26 /
official_split_reassessment 7 であり、退避内の件数より多い。差は `logs/` 等
`.gitignore` 対象で、そもそも退避に含まれていない分。）

### 個別復帰（`git checkout <stash> -- <path>` で部分復帰。stash 全体は pop しない）

    $ git checkout 'stash@{0}' -- .stglobalignore
    $ git checkout 'stash@{0}^3' -- docs/sessions/digest/2026-08-{22,23,24}-*.md

復元内容が stash の持つ内容と一致することを確認。

    $ diff <(git show 'stash@{0}:.stglobalignore') .stglobalignore
    （差分なし）

### 対話の抽出物の伏せ字確認

    $ grep -oE '\b[0-9a-f]{32,}\b' digest/2026-08-{22,23,24}-*.md | grep -c ''
    0（32桁以上の生16進 = 0 件。伏せられている）

    目視: docs/sessions/digest/2026-08-22-....md:47
      "NOTION_API_KEY=<redacted> …（切り詰め）"           ← 値が伏せられている
    "password" への一致（2026-08-24 ファイル）
      "sudo: a password is required" ← libgl1 のトラブルシュート記録。秘密ではない

**伏せ字は効いている。**

### stash@{1} — 一切触らなかった

`.sync-pause.released`（判断待ち）と `lovo_decision_rule/`（禁止領域・照合のみ）のみで構成され、
復帰可能なものが無い。**stash はそのまま残る。**

---

## Task 3・4 の順序

**受け皿への記録は Task 1（再生成）より後になった。** SPEC の二択のうち「集約の生成器を
最後にもう一度回す」を採った。

    $ cat > tasks/inbox.d/T-2026-08-29-projection-refresh.md  （3 行）
    $ make inbox   ← 二度目（受け皿記録を反映するため）
    exit=0
    $ make inbox-check
    exit=0          ← 三検査とも exit 0 のまま維持

### 判定 f 退避の整合

    Phase A-4 の実測: stash@{0} 追跡1件・未追跡23件 / stash@{1} 未追跡10件
    現在                : stash@{0} 追跡1件・未追跡23件 / stash@{1} 未追跡10件   一致

    $ git --no-pager stash list
    stash@{0}: …T-2026-08-29-projection-refresh: 契約開始前から在った汚れの退避…
    stash@{1}: …pre-oracle-ceiling-lovo

**両方とも drop していない。件数不変。消えたものは無い。**
作業ツリーに新たに現れたのは復帰した 4 項目（`.stglobalignore` + digest 3 件）のみ。

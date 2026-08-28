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

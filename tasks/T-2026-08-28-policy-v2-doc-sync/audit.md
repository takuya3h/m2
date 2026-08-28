# audit — T-2026-08-28-policy-v2-doc-sync

証跡の記録。命令とその出力・検証の出力・差分の一覧。事実の記録は `RESULT.md`。
**同じ内容を二度書かない。**

実行ホスト `philip` / repo `/home/ubuntu/slocal2/m2` / 分岐 `feat/policy-v2-doc-sync`

---

## 取り込み — 一度失敗している

    $ make task-start TASK=T-2026-08-28-policy-v2-doc-sync
    取り込みを中止しました: 受け取れないファイルです: 'research_policy_v2_2026-08-28.md'（許可: spec.yaml, SPEC.md, prereg.md）
    [task-start] 取り込みに失敗しました。巻き戻します
    [task-start] 実行前の状態へ戻しました
    make: *** [Makefile:205: task-start] Error 4
    --- exit=2 ---

    $ grep -n 'ALLOWED_FILES = \|REQUIRED_FILES = ' tools/fetch_task.py
    51:ALLOWED_FILES = ("spec.yaml", "SPEC.md", "prereg.md")
    52:REQUIRED_FILES = ("spec.yaml", "SPEC.md")

二度実行して同一。巻き戻しは完全（分岐 0 件・契約ディレクトリ無し・作業ツリー 0 件・`.sync-pause` 無し）。
起票者が四つ目のファイルを外したのち取り込めた。**SPEC §0 はこの失敗を自ら記している。**

### 作業ツリーの汚れで二度止まった

    $ make task-start …
    [task-start] 作業ツリーに未commitの変更が 6 件あります。片付けてから実行してください   ← 1 回目
    [task-start] 作業ツリーに未commitの変更が 3 件あります。片付けてから実行してください   ← 2 回目

いずれも**開始前から在ったもの**である。退避してから進めた（`RESULT.md` の逸脱 1・2）。
二度目の 3 件（`experiments/analysis/` の 3 ディレクトリ）は中身を `origin/phase0` と照合した。

    error_shape_selectivity      phase0 と同一 7 / 内容が違う 16（すべて logs/）/ phase0 に無い 0
    lovo_decision_rule           phase0 と同一 9 / 内容が違う 34（すべて logs/）/ phase0 に無い 0
    official_split_reassessment  phase0 と同一 3 / 内容が違う 0 / phase0 に無い 0

**失われる編集は無い。** 差は各ホストが自分の実行記録を持つ `logs/` 配下だけである。

---

## Phase A

### Step A-1 プレースホルダの置換

    $ git --no-pager log -1 --format='%H' -- runindex/
    7918b5dd9aab3d15b3c459f87aebdd9eb1653116
    $ git --no-pager log -1 --format='%H' -- context/conventions.md
    a8c07e813696d3720ceee648e8aa202224285955
    $ 行数（見出しを除く）
    index.csv: 1177   experiments.csv: 213   verdicts.csv: 1038

`spec.yaml` の `REPLACE-BY-EXECUTOR` 2 件と `counts` を上記で置換した。

    $ make task-validate TASK=T-2026-08-28-policy-v2-doc-sync
    OK   T-2026-08-28-policy-v2-doc-sync
    1 task(s), 0 failed
    validate exit=0                                      ← WARN 無し

    $ make task-preflight TASK=T-2026-08-28-policy-v2-doc-sync
    P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=… sys.prefix=…
    P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
    P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
    P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
    P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
    P6 decisions_answered     PASS decisions_required は空
    P7 destination_writable   PASS docs/ へ書き込みと削除ができた
    P8 contract_valid         PASS validate_task.py --level l2 が exit 0
    P9 spec_lint              PASS 規則 8 件を検査し該当なし
    RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
    preflight exit=0

**SKIP は「合格」ではない。** P2 P3 P4 P5 は実行されていない。

### Step A-2 変更対象の現状確認

    README.md    実在=yes 追跡=yes 行数=1612
    CLAUDE.md    実在=yes 追跡=yes 行数=90
    docs/history/ : **無い（作った）**

    README.md  sha256 fdb26e803abd08290f14fb15c7407af1…（変更前）
    CLAUDE.md  sha256 0a41ac93c1888508115a739e5a35343b…（変更前）

#### 🔴 時系列ログの境界は一意に決まらなかった（escalate して利用者へ提示）

日付見出しは **21 件**。**連続していない。**

    646  ### 2026-06-16 …  ┐
    …                      │ 20 件が連続（節の終端は 1069 の ---）
    1037 ### 2026-07-29 …  ┘
    1071 ## Claude Code 連携            ← 日付見出しでない
    1090 ## サーバー間同期               ← 日付見出しでない
    1179 ## 検出側 run の成果物          ← 日付見出しでない
    1250 ### 2026-08-22 横断再集計       ← 21 件目（節の終端は 1379、次は 1380 ## 主要ドキュメント）

**起票者の記述の二つの条件が両立しない。**

| 起票者の記述 | 合致する候補 |
|---|---|
| 「日付見出し節が**連続している**」 | 候補 A（646–1069）のみ |
| 「2026-06 中旬から **2026-08 下旬**に及ぶ」 | 候補 B（1250 を含む）のみ。連続する塊の最後は 2026-08-13（中旬） |

利用者へ候補と根拠を提示し、**候補 B（21 件すべて）**の回答を得た。

### Step A-3 撤回済みの語の分布（変更前）

    検査語 x: 比較の三角形
      README.md: 3 件   699 / 701 / 713 行（いずれも候補 A の内側）
      CLAUDE.md: 0 件
    検査語 y: 分析ファースト
      README.md: 0 件   CLAUDE.md: 0 件      ← **存在しない語**
    検査語 z: CLAUDE.md の旧判定規則
      4 行:  S0〜S9 の段階的実験と Δ（相互改善幅）基準点追跡が中核。
      34-35 行: Δ 基準点の汚染防止 … 改善主張は §10.1 に従い `|Δ| > 1σ` のときのみ行う。

---

## Phase B

### Task 1 移設

    範囲 1: 646–1069（424 行）sha256 ceef165acb30982960295f1cef12f0ff…
    範囲 2: 1250–1379（130 行）sha256 b762101cafb15bb43ca80675370d5122…
    連結  : 554 行            sha256 419de04d85f55e8809568f73b110bbc76ed975e34a56d2a501a96e9898827815

**下から切った。** 上から切ると後ろの行番号がずれる。切る前に目印で範囲を再確認している
（`lines[645]` が `### 2026-06-16 S0-frozen`、`lines[1068]` が `---`、`lines[1070]` が
`## Claude Code 連携`、`lines[1249]` が `### 2026-08-22 横断再集計`、`lines[1379]` が `## 主要ドキュメント`）。

### Task 5 追記先の判断

    $ grep -rn '^#\+ *\(変更履歴\|更新履歴\|Changelog\|History\)' README.md CLAUDE.md docs/*.md
    （該当なし）

**README に変更履歴に相当する節は無い。** 履歴ファイルの末尾に「変更履歴（移設後に追記）」を
新設し、移設本文の範囲外であることを本文中に明記した。

    $ find docs -type f \( -name '*handoff*' -o -name '*引き継ぎ*' \)
    （0 件）
    $ grep -rl '中間審査\|引き継ぎ事項' docs/ --include='*.md'
    （0 件）

**2026-08-27 の指摘整理の成果物は実在しない。リンクを張っていない。**

---

## Phase C — 完了判定

### 判定 a 移設の同一性

    注記の終端: 20 行目の ---  / 移設本文: 22 〜 575 行
    移設元: 554 行  sha256 419de04d85f55e8809568f73b110bbc76ed975e34a56d2a501a96e9898827815
    移設先: 554 行  sha256 419de04d85f55e8809568f73b110bbc76ed975e34a56d2a501a96e9898827815
    🟢 一致（本文は無傷）

空振り確認（一文字だけ変えた一時複製）

    一文字だけ変えた（S0-frozen → S0-frozeN）
    原本  : 419de04d85f55e8809568f73b110bbc7
    改変後: 247efd8b4a1081bf1028b3027220883d
    🟢 不一致になった（検査は働いている）
    一時複製を消した: 0 件

### 判定 b 撤回済みの語の残存

    検査語                    README       CLAUDE       履歴ファイル       空振り確認
    比較の三角形                 0            0            3            🟢 履歴で 1 件以上
    分析ファースト                0            0            0            ⚠ 履歴に無い（元から存在しない語）

    検査語 z（CLAUDE.md の旧判定規則の行）
      |Δ| > 1σ           現在の CLAUDE=0  版管理の旧版(HEAD)=1 🟢
      S0〜S9 で揃える         現在の CLAUDE=0  版管理の旧版(HEAD)=1 🟢
      §10.1              現在の CLAUDE=0  版管理の旧版(HEAD)=1 🟢

**z の空振り確認は履歴ファイルでは取れない**（z は CLAUDE.md にしか無く、移設したのは README の本文）。
**版管理の旧版（HEAD）へ同じ検査を当てて 1 件以上が出ることで代替した。**

### 判定 c リンクの健全性

    $ python linkcheck.py README.md CLAUDE.md docs/history/README_log_2026-05_to_2026-08.md
      相対リンク 47 件 / 実在しない 2 件
        🔴 docs/history/README_log_2026-05_to_2026-08.md: docs/research_review_and_next_plan_2026-08-22.md
        🔴 docs/history/README_log_2026-05_to_2026-08.md: docs/task_drafts/README.md
      exit=1

**2 件はいずれも移設本文の中にある。私が張ったリンクではない。**
README（リポジトリ直下）を基点に書かれており、`docs/history/` へ移したため解決しなくなった。

    移設前の README（HEAD）: 相対リンク 43 件 / 実在しない 0 件   ← 移設前は壊れていなかった
    直下から見た実在: docs/research_review_and_next_plan_2026-08-22.md 🟢 / docs/task_drafts/README.md 🟢

**禁止 1（移設本文の改変）により直せない。** 先頭注記（付加が許されている箇所）に
基点が README であることを明記した。**本文は触っていない**（判定 a を取り直して一致を確認済み）。

**今回私が張ったリンクは 3 件**（README の履歴節・現在の状態・設計原則から履歴ファイルへ）で、
**すべて実在する。**

空振り確認

    実在しない経路を含む一時複製に同じ検査を当てる
      相対リンク 46 件 / 実在しない 1 件
        🔴 broken.md: docs/history/zzz_no_such_file.md
      exit=1  🟢 検出された
    一時複製を消した: 0 件

### 判定 d 既存の文書検査

Makefile を読んで文書・整合・禁止領域に関する検査を特定した（`Makefile:106-160`）。

    $ make docs-check
      [docs-check] 対象 42 文書 / Makefile のターゲット 33 件
      [docs-check] 食い違いなし
      exit=0  🟢

    $ make agent-check
      {"errors": [], "pager_violations": [], "status": "pass", "targets": 94, "violations": []}
      exit=0  🟢

    $ make forbidden-check
      changed=5 checked=5 status=pass violations=0
      exit=0  🟢

    $ make context-check     exit=2   ← 投影が runindex に対して古い
    $ make taskindex-check   exit=2   ← 投影が他契約の result.yaml に対して古い
    $ make inbox-check       exit=2   ← 集約が他契約の inbox.d に対して古い

**後の 3 つは今回の変更が原因ではない。**

    build_context.py    README/CLAUDE への参照: 0 件
    build_taskindex.py  README/CLAUDE への参照: 0 件
    build_inbox.py      README/CLAUDE への参照: 1 件（104 行の文字列。tasks/README.md への案内であって入力ではない）

    今回の変更が入力に含まれるか
      runindex/ の変更            : 0 件
      tasks/*/result.yaml の変更  : 0 件
      tasks/inbox.d/ の変更       : 0 件

**投影の再生成は禁止 3・4 が禁じている**（「統合後に正本ホストで行う」）。回していない。

空振り確認（README が実際に走査されているか）

    README に実在しない経路を一時的に足す
      [docs-check] 1 件の食い違い
      [docs-check] 対象 42 文書 / Makefile のターゲット 33 件
        README.md:1117 実在しない経路 docs/zzz_no_such_path.md
      exit=2  🟢 検出された（走査零件のまま通っていない）
    復元: 一致 🟢

`docs/docs_audit.md:19-20` が README.md と CLAUDE.md を「現行手順」に分類しており、
`check_docs.py` はこの分類表から対象を取る。**両方とも走査対象である。**

### 判定 e 変更範囲

    $ git --no-pager diff --stat
      CLAUDE.md |  28 ++-
      README.md | 642 +++++++-------------------------------------------------------
      2 files changed, 95 insertions(+), 575 deletions(-)

    $ git --no-pager status --porcelain
       M CLAUDE.md
       M README.md
      ?? docs/history/
      ?? tasks/T-2026-08-28-policy-v2-doc-sync/
      件数: 4

**§2 の対象と契約ディレクトリだけである。対象外の変更は 0 件。**
（受け皿 `tasks/inbox.d/` は報告の段で足す。）

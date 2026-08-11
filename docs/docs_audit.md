# 文書と実態の食い違い（2026-08-11）

契約 `T-2026-08-16-docs-reconciliation` の Phase A の成果物。
実行ホストは `lecun`（SPEC の指定は `bengio`。§5 に記す）。

分類の基準は「**いま読んで従うものか**」である。過去の出来事を述べるものは記録とし、
**判断に迷うものは記録として扱う**（触らないほうが安全であるため）。

この文書の「対象の分類」表は、`tools/check_docs.py` が読む**対象の一覧を兼ねる**。
分類が `現行手順` の行だけが検査の対象になる。

## 対象の分類

追跡下の `*.md` は 837 件。うち `tasks/T-` 配下の契約 60 件を除いた 777 件が母集団である。
記録として自明な領域（下表の集約行）を除いた 96 件を個別に判定し、**42 件を現行手順**とした。

| 文書 | 分類 | 根拠 |
|---|---|---|
| README.md | 現行手順 | 環境構築と実行方法を述べる |
| CLAUDE.md | 現行手順 | 実装系への指示 |
| AGENTS.md | 現行手順 | もう一方の実装系への入口。実体は CLAUDE.md への symlink |
| OPERATION.md | 現行手順 | 運用手順書 |
| tasks/README.md | 現行手順 | 契約の説明書 |
| context/README.md | 現行手順 | 文脈の置き場の説明 |
| context/conventions.md | 現行手順 | 規約の正本。ただし本 task では禁止 3 により変更しない |
| data/README.md | 現行手順 | データ配置の説明 |
| notebooks/README.md | 現行手順 | 置き場の説明 |
| configs/detector_relation_detr/README.md | 現行手順 | 検出器レシピの説明 |
| docs/secrets_and_tracking.md | 現行手順 | 資格情報の運用手順 |
| docs/notion_integration.md | 現行手順 | 外部記録の運用手順 |
| docs/environment.md | 現行手順 | 環境の説明 |
| docs/host_autosync_onboarding.md | 現行手順 | ホスト追加の手順 |
| docs/host_dev_env_setup.md | 現行手順 | ホスト構築の手順 |
| docs/reproduce_on_new_machine.md | 現行手順 | 再現手順 |
| docs/auto_logging.md | 現行手順 | 自動記録の説明 |
| docs/notion_run_ledger_auto_post.md | 現行手順 | 台帳投稿の手順 |
| docs/notion_run_ledger_recipe.md | 現行手順 | 台帳のレシピ |
| .claude/skills/task/SKILL.md | 現行手順 | 契約実行の手順書 |
| .claude/skills/run-experiment/SKILL.md | 現行手順 | 実験実行の手順書 |
| .claude/skills/add-model-component/SKILL.md | 現行手順 | 実装追加の手順書 |
| .claude/skills/avoid-past-failures/SKILL.md | 現行手順 | 事故回避の手順書 |
| .claude/commands/delta.md | 現行手順 | スラッシュコマンドの定義 |
| .claude/commands/env-check.md | 現行手順 | 同上 |
| .claude/commands/exp-report.md | 現行手順 | 同上 |
| .claude/commands/log.md | 現行手順 | 同上 |
| .claude/commands/new-hypothesis.md | 現行手順 | 同上 |
| .claude/commands/promote-to-master.md | 現行手順 | 同上 |
| .claude/commands/run-stage.md | 現行手順 | 同上 |
| .claude/commands/verify-phase.md | 現行手順 | 同上 |
| .claude/agents/delta-analyst.md | 現行手順 | サブエージェントの定義 |
| .claude/agents/experiment-runner.md | 現行手順 | 同上 |
| .claude/agents/notion-archivist.md | 現行手順 | 同上 |
| .claude/agents/paper-writer.md | 現行手順 | 同上 |
| .claude/agents/trace-debugger.md | 現行手順 | 同上 |
| tasks/_templates/impl/SPEC.md | 現行手順 | 契約の雛形 |
| tasks/_templates/impl/RESULT.md | 現行手順 | 同上 |
| tasks/_templates/exp/SPEC.md | 現行手順 | 同上 |
| tasks/_templates/exp/RESULT.md | 現行手順 | 同上 |
| tasks/_templates/analysis/SPEC.md | 現行手順 | 同上 |
| tasks/_templates/analysis/RESULT.md | 現行手順 | 同上 |
| experiments/ 配下 633 件 | 記録 | 実験証跡 |
| third_party_snapshot/ 配下 5 件 | 記録 | 外部由来の複製 |
| docs/sessions/ 配下 12 件 | 記録 | 対話の抽出物 |
| tasks/inbox.d/ 配下 17 件 | 記録 | 契約ごとの判断の受け皿 |
| context/auto/ 配下 3 件 | 記録 | 生成物。手で編集しない |
| runindex/ 配下 3 件 | 記録 | 生成物。手で編集しない |
| prompts/ 配下 7 件 | 記録 | 過去のプロンプト |
| reports/ 配下 1 件 | 記録 | 過去の報告 |
| evidence/ 配下 5 件 | 記録 | 破棄・事故の証跡 |
| docs/m2_plan_rewrite/ 配下 25 件 | 記録 | 計画書き換えの作業物。正本は外部の運用ハブ |
| 日付を名前に含む docs 直下 11 件 | 記録 | 特定日の調査記録 |
| docs/decision_log.md docs/experiment_log.md docs/idea_log.md docs/TODO.md | 記録 | 出来事の追記型の記録 |
| tasks/lessons.md tasks/todo.md tasks/todo_t1c_bidir_pilot.md | 記録 | 追記型の記録 |
| tasks/inbox.md | 記録 | 生成物。手で編集しない |
| .claude/incidents.md | 記録 | 事故の記録 |
| auto_logging_implementation.md | 記録 | 実装当時の記録 |
| docs/dac_detr_integration_repro.md | 記録 | 再現作業の記録 |
| docs/superpowers/specs/ 配下 1 件 | 記録 | 設計当時の記録 |
| docs/t1a_server_b_runsheet.md docs/t1b_server_b_runsheet.md | 記録 | 特定実験の実行控え。判別に迷うため記録として扱う |

## 食い違い

実態は次のとおり実測した。Makefile のターゲット **27 件**（本 task で `docs-check` を
足して 28 件）、`tools/*.py` 18 件、`scripts/sync/*.sh` 6 件、`context/auto/` 6 件、
`origin/exp/` の分岐 22 本。

| 文書 | 箇所 | 現在の記述 | 実態 | 対応 |
|---|---|---|---|---|
| CLAUDE.md | 54-57 | スラッシュコマンド 6 件・サブエージェント 4 件・スキル 2 件 | 実在は 8 件・5 件・4 件。`/log` `/promote-to-master` `notion-archivist` `avoid-past-failures` と、**契約実行の中心である `task` スキル**が記載されていない | 実態に合わせる |
| AGENTS.md | 54-57 | 同一の文面に見える | **実体は CLAUDE.md への symlink である**（`AGENTS.md -> CLAUDE.md`）。別文書ではなく同一ファイルであり、実装系が二つあっても指示は 1 つである | 上の行の修正で同時に解消する。独立した修正は不要 |
| context/README.md | 11 | `context/auto/` の中身を 4 件と書く | 実在は 6 件。`followups.md` と `tasks_summary.csv` が欠けている | 実態に合わせる |
| context/README.md | 33 | 研究方針は `context/plan_mirror.md`（人手管理）の役目であると書く | そのファイルは存在せず、git の履歴にも一度も存在しない。実態は外部の運用ハブが担う | 実在する置き場へ書き換える |
| .claude/agents/paper-writer.md | 15 | 表は `scripts/export_paper_tables.py` と `tools/generate_delta_report.py` の出力を活用すると書く | 双方とも存在しない。`af1fc58` で**空の scaffold** として作られ、`41e9ac1`「空の Δ scaffold を削除し make delta/tables を runindex へ寄せる」で**意図的に削除**されている。近い名前の代替も無い | 記述を実態へ改める |
| 現行手順の全 42 件 | — | 完了報告の構造化された対 `result.yaml` に触れた記述が 1 件も無い | `tasks/_schema/result.schema.json` と `tasks/_templates/result.yaml` が実在し、契約 3 件が既に使っている | `tasks/README.md` と契約実行の手順書へ追記する |
| 現行手順の全 42 件 | — | 投影 `make taskindex` `context/auto/followups.md` `context/auto/tasks_summary.csv` に触れた記述が 1 件も無い | Makefile に `taskindex` と `taskindex-check` が実在し、生成物も実在する | 同上 |

件数が 0 の 2 件については、対象を現行手順の 42 件に限った探索と、記録領域を除く追跡下の
全文書 96 件に対する探索の双方で 0 件であった（生成物 `tasks/inbox.md` に本契約自身の
記録として現れるのみ）。

## 食い違いと判定したが誤りだったもの

**当初 9 件を食い違いとして提示したが、うち 2 件は誤りだった。** 記録を残す。

| 文書 | 当初の判定 | 実際 | 原因 |
|---|---|---|---|
| README.md 393-402 | `make s0` `s2` `s4` `s5` `s6` は存在しないと判定した | **5 つとも Makefile の 37 40 43 46 49 行に実在する。** `make -n s0` は `bash scripts/run_s0.sh` を返す。1 行目の `.PHONY` にも並んでいる | SPEC が示した実態の測り方 `grep -E "^[a-z-]+:" Makefile` が**数字を含むターゲットを取りこぼす**（`[a-z-]+` は `0` に一致しない）。22 件と出たが実際は 27 件である |
| README.md 405 | `make s0` が無いので `run_s0.sh` は呼ばれないと判定した | 呼ばれる。元の記述は正しい | 同上 |

一度書き換えたが**元の記述へ戻した**（`git checkout -- README.md` で差分 0 を確認）。

**原因は SPEC の測り方をそのまま信じたことである。** SPEC 自身が注意 1 で
「一致件数が 0 のとき、別の探し方でも 0 になることを確かめる」と書いているのに、
`make s0` が一覧に無いことだけを見て、実在しないと結論した。**一覧の作り方を疑わなかった。**
残る 7 件は、それぞれ 2 通り以上の探し方で確かめ直した（`ls` と `find`、
`git log --all` と全 ref の走査、実在検査と近似名の検索）。

この誤りは Phase C の検査が見つけた。検査の実装は `^[a-z][a-z0-9-]*:` で読むため
27 件を数え、22 件との差の 5 件がちょうど `s0` `s2` `s4` `s5` `s6` だった。

## 後から追加で承認された食い違い

いずれも当初の 9 件には含まれない。**提示して追加の承認を得てから**直した。
範囲を勝手に広げてはいない。

| 文書 | 箇所 | 現在の記述 | 実態 | 対応 |
|---|---|---|---|---|
| README.md | 400-401 | `make delta` を「Δ（基準点比較）の算出」、`make tables` を「論文用テーブルの書き出し」と説明する | どちらも**算出も書き出しもしない**。`runindex/` のどこに値があるかを表示するだけである。`41e9ac1`「空の Δ scaffold を削除し make delta/tables を runindex へ寄せる」で意図的にそうなった | 表示するだけであると明記した |
| OPERATION.md | 471 | 参照先の表で `backlog.md` を「分析基盤の既知の課題（34 件）」と説明する | `4bf3187` で書かれた当時の数のまま。実測は 39 件だったが、**本 task で B-40 を起票した直後に 40 件へ変わった** | 数を書くのをやめ、**現在値の出所**（`context/auto/STATE.md`）だけを示した |
| docs/reproduce_on_new_machine.md | 87 90 | 「**99 テスト収集**。既知の 1 件が fail。**それ以外がパスすれば環境健全**」 | 実測は **319 テスト収集 / failed 5 件**。増えた 4 件は `test_research_logger.py` で、`log_run` が `None` を返し `log_experiment_to_notion` が呼ばれない。**環境非依存**であり `origin/phase0` の時点から失敗している | 実測値へ直し、既知の失敗 5 件を名前つきで表にした。実装側の欠陥は `B-40` として起票した |
| README.md | 542 | 「評価指標 **4 件** + StageATrainer **2 件**のテスト」 | 実測は 8 件 / 10 件 | 実測値へ直し、測った日付を併記した |

### 数の主張は検査できていない

**Phase A の照合は操作名と経路に寄っていた。** `make X` と経路は存在するかしないかの
二値なので機械化しやすいが、「34 件」のような**数の主張**は、対応する実測値がどこに
あるかを人が知らないと照合できない。上の 1 件は `docs-check` を通過しており、
利用者の指摘で見つかった。

`backlog.md` は投影 `STATE.md` に件数が出るため照合できたが、これは幸運である。
**出所の書かれていない数は原理的に検査できない。** 検査を広げるなら、
「文書に数を書くときは実測の出所を併記する」という規約を先に決める必要がある。
本 task では規約を作っていない（§後述の未解決事項）。

利用者の指摘を受けて 42 文書を洗い直し、**数の主張 57 件と裸のファイル名 28 件**を
機械で抽出して照合した。結果は次のとおり。

| 種別 | 件数 | 結果 |
|---|---|---|
| 数の主張 | 57 | 現在の状態を述べるものは 3 件で、いずれも古かった（上表）。残りは日付つきの過去の実測であり触らない |
| 裸のファイル名 | 28 | **すべて非該当。** 外部パッケージの `setup.py`、`third_party/` 配下の検出器実装、gitignore 済みの `settings.local.json`、ホスト依存のデータ、変数 `run_sX.sh` |
| 研究サーバー 11 台の名前 | 11 | **全て定位置分岐に実在**（10 台は新旧 2 本、philip は 1 本）。以前 UNKNOWN としていたが裏が取れた |
| 「実験に使用中の 4 台」 | 1 | このリポジトリからは検証できない。**UNKNOWN のままとする** |

### 起票の際に自分が起こした事故

`B-40` を BACKLOG へ追記する際、**別の文字列定数 `RUNINDEX_README` の中へ入れてしまった。**
錨に使った一文がその末尾にもあり、ファイル全体で一意だったため置換は成功した。

投影に `B-40` が現れず、BL 行が 38 のままだったことで気付いた。**一意であることは
正しい場所であることを意味しない。** 文字列定数へ追記するときは、置換の前後で
`ast` により**その定数の行範囲**を確かめること。

## 触らないもの

上の分類で記録としたものはすべて対象外である。加えて、**現行手順の文書の中にある
過去の記述**も変えない。判別できたものを挙げる。

| 箇所 | 内容 | 理由 |
|---|---|---|
| OPERATION.md 104 | `exp/aolab-wip-20260703` は ilya の旧ブランチで、歴史的記録として残してあるが使わない | 過去の分岐についての、現在も正しい説明である。旧命名が本文に現れるが誤りではない |
| context/conventions.md | 規約の正本 | 本 task の禁止 3 により変更しない |
| tasks/T- 配下の契約 60 件 | 過去の契約と完了報告 | 禁止 1 |

## 検査の偽陽性として除外するもの

機械検査の設計に必要なため、実測で確かめた偽陽性を記録する。
**検出できないものを検出したことにしないため、除外の理由を明記する。**

| 除外 | 実例 | 理由 |
|---|---|---|
| 散文中の英単語 make | avoid-past-failures/SKILL.md 38 の "about to make a non-trivial change" | 英文の動詞であって操作名ではない。命令として書かれた行に限れば消える |
| 候補の優先順位列挙 | avoid-past-failures/SKILL.md 3 の `docs/incidents.md` | 3 つの候補を優先順位で挙げ、無い場合の扱いも本文に書いてある。存在しないことが前提の記述である |
| 外部リポジトリ相対のパス | configs/detector_relation_detr/README.md 11 の `configs/relation_detr/...` | 同じ文書の冒頭に、正本が `third_party/Relation-DETR/` 配下であると書いてある |
| 分岐名 | OPERATION.md 79 の `docs/plan-rewrite-2026-06` | 分岐の一覧表の中にある。`origin/docs/plan-rewrite-2026-06` として実在する分岐名であって経路ではない |
| 変数を含む記述 | `scripts/run_sX.sh` `experiments/transfer/NAME/` | `X` や `NAME` は書き手が置いた変数である |
| 実行時に生成される証跡 | `experiments/baselines/s0_001_tool_baseline_seed42/` | `experiments/` は空の足場から実行時に採番・生成される。文書の例示であって実在を約束しない |
| ホスト依存のデータ | `data/annotations/...` `data/hts_reconstruction` | 追跡下に無く、ホストごとに置き場が異なる。SPEC の検査対象は追跡下の経路である |

### 除外の印を置いた箇所（全件）

規則で自動的に外せないものには、行末（表の中はセル内）に
`<!-- docs-check: ignore-line -->` を置いた。**印は 7 箇所である。**
`AGENTS.md` は `CLAUDE.md` への symlink なので、印は 1 つで両方に効く。

| 箇所 | 対象 | 理由 |
|---|---|---|
| CLAUDE.md 24 | `scripts/run_sX.sh` | `X` は書き手が置いた変数 |
| .claude/skills/run-experiment/SKILL.md 28 | `scripts/run_sX.sh` | 同上 |
| .claude/commands/run-stage.md 21 | `scripts/run_sX.sh` | 同上 |
| .claude/agents/experiment-runner.md 15 | `scripts/run_sX.sh` | 同上 |
| .claude/skills/avoid-past-failures/SKILL.md 36 | `docs/incidents.md` | 3 つの候補を優先順位で挙げた行。無い場合の扱いも本文にある |
| configs/detector_relation_detr/README.md 11 | `configs/relation_detr/...` | 正本が `third_party/` 配下であると同じ文書の冒頭に書いてある |
| .claude/agents/paper-writer.md 18 | `paper/tables/` | 「存在しない」と述べている文そのもの |

### 検査自身にあった欠陥（実測で見つけて直した）

対象の一覧を読む正規表現が `^[\w][\w./-]*\.md$` で、**先頭のドットを許していなかった。**
そのため `.claude/` 配下の 17 文書が静かに対象から落ち、対象が 42 ではなく 25 と表示された。
表示された件数が分類の件数と合わないことで気付いた。正規表現を `^[\w.]...` に直し、
落ちないことを確かめる試験を足した。

**件数を表示していなければ気付けなかった。** 検査は自分が何件見たかを必ず出すこと。

## 機械で確かめる範囲と、確かめない範囲

Phase C の検査が確かめるのは次の 3 点のみである。

| # | 確かめること |
|---|---|
| 1 | 文書中の `make <名前>` が Makefile に実在する |
| 2 | 文書中の `tools/` `scripts/` 配下の経路が実在する |
| 3 | 文書中の追跡下の経路が実在する |

**次は確かめない。** 人が読んで判断するしかない。

| 確かめないこと | 理由 |
|---|---|
| 手順の順序が正しいか | 実行しないと分からない。資格情報の編集と再暗号化の順序など |
| 前提条件が満たされるか | ホストの状態に依存する |
| 説明の内容が実装と一致するか | 自然言語であり機械では突き合わせられない |
| 記録として分類した文書 | 対象外。過去の記述は現在と食い違って当然である |
| 上の偽陽性の表に挙げた記述 | 除外の理由を各行に記した |

# 監査: 作り直しと鮮度の検査の呼び出し元

起点: `origin/phase0` = 分岐の起点（`git merge-base` で確認）。行番号は**変更前**のもの。
対象語: `taskindex` `inbox` `taskindex-check` `inbox-check`。生成物（`context/auto/**` `tasks/inbox.md`）、
契約の記録（`tasks/T-*/` `tasks/inbox.d/`）、会話の記録（`docs/sessions/**` `docs/archive/**` `docs/adam-preserve-*`）は除いた。

## 1. 探し方（零件の箇所は方法を変えて探し直した）

| # | 方法 | 対象 |
|---|---|---|
| S1 | `git grep -nE '\b(taskindex\|inbox)(-check)?\b'` | repo 全体（除外は上記） |
| S2 | `git grep -nE 'build_taskindex\|build_inbox'` | `tools` `scripts` `.claude` `.github` `Makefile` `tests` |
| S3 | `git grep` で `subprocess` `os.system` `Popen` `\bmake\b` | `tools/validate_task.py` `preflight_task.py` `report_task.py` `fetch_task.py` `check_spec.py` `check_forbidden.py` `check_agent_docs.py` `check_docs.py` `scripts/task_start.sh` `scripts/sync/m2-sync.sh` |
| S4 | 名前以外の語 `context/auto` `投影` `鮮度` `inbox\.md` `--check` | `tools` `scripts` `.claude/{hooks,commands,agents}` `AGENTS.md` `CLAUDE.md` `Makefile` |
| S5 | Makefile 全行を読み、目標の依存（`target: deps`）と本体を確認 | `Makefile` |
| S6 | テストが実物の生成物の鮮度を見ていないか（`--check` `AUTO_DIR` `INBOX_FILE` `main([`） | `tests/` |
| S7 | Codex の経路 | `AGENTS.md`、`.codex/skills/task`（→ `../../.claude/skills/task` のシンボリックリンク） |
| S8 | 他の分岐が同じファイルに触れているか（`git diff merge-base..branch`） | `origin/*` の全分岐 |

## 2. 直接の呼び出し（S1）

| 箇所 | 内容 | 分類 |
|---|---|---|
| `.claude/skills/task/SKILL.md:153-156` | 「書いたら投影に現れることを確かめる。」`make taskindex` / `make taskindex-check` | **甲: 手順で作り直しを求める** |
| `.claude/skills/task/SKILL.md:172-173` | 「再生成との差分で捕まる（`make taskindex-check` と `make inbox-check`）。両方を回すこと。」 | **乙: 契約の検証で `*-check` を回す** |
| `.claude/skills/task/SKILL.md:176-180` | 「併合の後は再生成すること」`make taskindex && make inbox` | **甲** |
| `.claude/skills/task/SKILL.md:205-209,220` | 受け皿 `tasks/inbox.d/` と「`tasks/inbox.md` を手で編集しない」 | 丙（受け皿の説明。作り直しを求めない） |
| `tasks/README.md:202-204` | `forbidden-check` の節。「再生成との差分で捕まる（…）。2 つの検査は別のものを見ている。片方だけでは足りない。」 | **乙**（契約の流れの節で両方を回すことを求める） |
| `tasks/README.md:411-425` | 「## 投影」道具の説明 | 丙（phase0 の上で使う道具の説明） |
| `tasks/README.md:427-447` | 「### 生成物の合流」併合の後の再生成 | 丙（併合は phase0 側で起きる。自動化の説明と両立） |
| `tasks/README.md:496-510` | 受け皿の説明 `make inbox` / `make inbox-check` | 丙 |
| `Makefile:118-138` | 目標 `inbox` `inbox-check` `taskindex` `taskindex-check` の定義 | 丙（**残す**。禁止 1） |
| `Makefile:153` | `forbidden-check` の注記「taskindex-check / inbox-check で捕まる」 | 丙（事実の説明） |
| `tools/check_forbidden.py:11-14` | docstring の同趣旨の説明 | 丙（道具。変更すると禁止 7/想定外に当たる） |
| `tools/build_taskindex.py` `tools/build_inbox.py` | 生成器そのもの | 丙（禁止 2） |
| `.github/workflows/regen-projections.yml:48-49` | phase0 への push で `make taskindex` `make inbox` | 丙（自動化の本体。禁止 3） |
| `context/README.md:12,21,26` | `make taskindex` / `make taskindex-check` の使い方 | 丙 |
| `README.md:1304-1305` | 自動化の説明 | 丙 |
| `.gitattributes:7,17` | 合流の方式と注記 | 丙 |
| `tasks/_templates/{impl,exp,analysis}/SPEC.md:27` | 「生成物への手編集は `make taskindex-check` と `make inbox-check` が捕まえる。」 | 丙（起票者の雛形。事実の説明。§5 で起票者へ申し送る） |
| `tasks/_templates/result.yaml:5` | 注記「投影: make taskindex → …」 | 丙 |
| `tests/test_build_inbox.py` `test_build_taskindex.py` `test_check_forbidden.py` `test_check_docs.py` `test_tooling_fixes_five.py` `test_symmetry_gate.py` | 生成器の単体試験（`tmp_path` 上） | 丙（実物の鮮度は見ない。S6） |
| `docs/docs_audit.md:66,76,97,100` `docs/task_drafts/README.md:7` `docs/notion_integration.md:73` `docs/research_review_…:*` `tasks/todo.md:*` `experiments/analysis/…/REPORT.md` | 過去の記録・分類表 | 丙（記録） |
| `CLAUDE.md:107` | `tasks/inbox.d/` に書く | 丙 |

## 3. 間接の経路（S2〜S7）

- **Makefile（S5）**: `*-check` や `taskindex` `inbox` を依存に持つ目標は**無い**。`task-validate` は
  `tools/validate_task.py` だけ、`task-preflight` は `tools/preflight_task.py` だけを呼ぶ。
- **検証の道具（S3）**: `validate_task.py` の subprocess は `git for-each-ref` `git show` `git diff` のみ。
  `preflight_task.py` は `python -c`（P2）`git show`（P4）`validate_task.py`（P8）`nvidia-smi`（P11）のみ。
  `fetch_task.py` は `make task-validate` のみ。`report_task.py` `check_spec.py` は外部命令を呼ばない。
  `task_start.sh` は `make task-notion` のみ。`m2-sync.sh` に該当なし。
- **`check_forbidden.py:98-112`** は `build_inbox` `build_taskindex` を **import するが、除外する場所
  （`AUTO_DIR` `INBOX_FILE`）を読むためだけ**で、`check()` も生成も呼ばない。
- **フック・コマンド・エージェント（S4）**: `.claude/hooks/*` `.claude/commands/*` `.claude/agents/*` に該当なし。
- **テスト（S6）**: 実物の生成物の鮮度を見る試験は無い。`make test` を回しても鮮度では落ちない。
- **Codex（S7）**: `.codex/skills/task` は `.claude/skills/task` へのリンク。`AGENTS.md` は `CLAUDE.md` と同文で、
  `*-check` を名指さない。**手順書を直せば両方の経路に効く。**

**結論: 「契約の検証で `*-check` が走る」経路は道具の中には無い。走らせているのは手順書の文言（甲・乙）だけである。**
したがって道具（Makefile・`tools/`）を変える必要は無い。

## 4. 他の契約との重なり（S8）

`.claude/skills/task/SKILL.md` `tasks/README.md` `tasks/_templates/**` `Makefile` `CLAUDE.md` `AGENTS.md`
`tools/check_forbidden.py` `context/README.md` に触れる origin の分岐は 2 本だけで、いずれも古い
（`origin/docs/plan-rewrite-2026-06` 2026-06-22: `CLAUDE.md`、`origin/exp/lecun-wip-20260703` 2026-08-07:
`Makefile` `tasks/README.md`）。philip の `regen-projections.yml` の契約は `.github/workflows/` だけに触れる見込みで、
本契約は同ファイルに触れない。

## 5. 起票者の手順書

起票者の手順書（Claude アプリのプロジェクト指示文）は**版管理の外にあり、このホストから読めない（UNKNOWN）。**
repo 内の起票者側の雛形 `tasks/_templates/{impl,exp,analysis}/SPEC.md:27` は「`*-check` が捕まえる」と事実を述べるだけで、
契約の中で回せとは書いていない。**ただし契約の起票時に「検証を通す」の中身として `*-check` を書き込む誘因になり得る**ため、
起票者側で「phase0 の上で使う」と添えるかを申し送る（本契約では直さない）。

## 6. 基準の実測（変更前・本分岐・契約の記録 2 件のみ追加の状態）

| 命令 | 終了コード |
|---|---|
| `make taskindex-check` | 0 |
| `make inbox-check` | 0 |
| `make forbidden-check` | 0 |
| `make task-validate TASK=<本契約>` | 0 |

`result.yaml` と `tasks/inbox.d/<本契約>.md` を足した時点で前二者は落ちるはずである（§Phase B で実測）。

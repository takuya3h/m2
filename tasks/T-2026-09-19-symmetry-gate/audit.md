# audit — T-2026-09-19-symmetry-gate

コマンドと実測値の記録。**数値はすべてこのホストでの実測である。**

- ホスト: `m2`（`/home/ubuntu/slocal2/m2`）
- 分岐: `feat/symmetry-gate`、起点 `origin/phase0` = `ed9211bc`
- 仮想環境: `.venv`（activate 済み。P1 PASS）

## Task A — 開始状態

### A.1 作業ツリー

    git --no-pager status --short

開始時の未追跡は 4 件。うち 3 件は本契約の前から在るセッション記録である。

| 経路 | sha256 | 扱い |
|---|---|---|
| `docs/sessions/digest/2026-09-17-15-28-06-01a0affb-….md` | `71c2cb03…2194` | 退避できず。その場に残し、commit に含めない |
| `docs/sessions/digest/2026-09-17-66ad6e5e-….md` | `9940c6ff…535a` | 同上 |
| `docs/sessions/digest/2026-09-18-13-43-20-01a0b4c1-….md` | `9a459a2b…6dcc3` | 同上 |
| `tasks/T-2026-09-19-symmetry-gate/` | — | 本契約。commit する |

**退避（`mv`）は実行基盤が拒否した**（`Irreversible Local Destruction` として遮断）。
SPEC §6「実行基盤が書き込みや `rm` を拒む → 回避せず提示」に従い、回避せずに記録した。
3 件は禁止領域の外にあり、`make forbidden-check` の `violations` にも出ない（実測 0 件）。

### A.2 変更前の数

| 対象 | 変更前 | 測り方 |
|---|---|---|
| 規約のアンカー数 | 10 | `grep -c '<a id=' context/conventions.md` |
| 提案カードの見出し数 | 14 | `check_proposal.card_items()` |
| 禁止語の数 | 15 | `check_proposal.forbidden_words()` |
| 数値必須の項目 | `[5, 6, 10]` | `check_proposal.numeric_items()` |
| L3 の検査数 | 12（P1〜P12） | `len(preflight_task.CHECK_NAMES)` |
| `check_spec.py` の規則数 | 8 | `make spec-check` の `rules_checked` |
| 試験 | 6 failed / 567 passed | `python -m pytest tests/ -q` |

要約値（無変更の照合用。**表示属性では足りない**）。

    card_rows_1-14              b884c6da758f16f30e9e9ada0c54b01f8551b50b51d094cfa1285ec9543a925d
    cautions_rows_1-13          bbc6de6c9520e45024f62ca7601db8d38d9ff33a6597e4642abffe02f2ffc190
    docs/issuer-defects.md      a39fb9a13af08afa1e4501312c37bede6ba102831abe4092a66b69fa438ce002

### A.3 占位の確定

    git --no-pager log -1 --format=%H -- context/conventions.md   # e7a5100597a79b3b9c60935bf38d232f8ae96822
    git --no-pager log -1 --format=%H -- runindex/                # 029b5315a4b543fabbebe350e2e1302e2d816d9b

`created_from.counts` は本契約が runindex を参照しないため 0 のまま残した
（実測は index 1507 / experiments 458 / verdicts 1506）。先例は
`T-2026-09-16-evidence-map-ab` と同じ扱いである。

## Task B — 規約

`git --no-pager diff --numstat context/conventions.md` は **52 insertions / 0 deletions**。
削除が 0 であることが「既存行の本文を変えていない」ことの直接の証拠である。

| 対象 | 変更前 | 変更後 |
|---|---|---|
| アンカー数 | 10 | 11（`symmetry` を追加） |
| 提案カードの行数 | 14 | 16 |
| `issuer_cautions` の行数 | 13 | 14 |
| `card_rows_1-14` の要約値 | `b884c6da…a925d` | `b884c6da…a925d`（一致） |
| `cautions_rows_1-13` の要約値 | `bbc6de6c…f190` | `bbc6de6c…f190`（一致） |

変更履歴の commit 欄は `PENDING` で置き、後続 commit で埋めた。先例は `folds` 節
（`537c968c` を `e7a51005` が埋めた）と同じ手順である。

## Task C — 検査

### P13 の判定（完了判定 d）

`tools/preflight_task.py` の `check_symmetry_table()` に 6 種の入力を通した実測。

| 入力 | 結果 | detail |
|---|---|---|
| 1 表なし | FAIL | `prereg.md に conventions#symmetry の対称性の表が無い（列名 条件／腕1／腕2／判定／理由 で探す）` |
| 2 UNKNOWN 行あり | FAIL | `2 行を検査。UNKNOWN 1 行: 学習率` |
| 3「意図的に変える」に理由なし | FAIL | `1 行を検査。「意図的に変える」に理由が無い 1 行: 前処理` |
| 4 全行が揃うか意図的差 | PASS | `対称性の表 1 個 / 2 行に UNKNOWN と理由欠落は無い` |
| 5 列名が部分一致するだけの別表のみ | FAIL | 1 と同じ。**別の表を拾っていない** |
| 6 雛形のまま | FAIL | `15 行を検査。UNKNOWN 15 行: …`（表の行数 15 と一致） |

入力 5 の表は `条件の分類 / 腕の数 / 判定規約 / 理由の欄`。
列名の**完全一致**で同定しているため拾わない。逆向きの対照として、手前に別の表
（`指標 / 値`）があっても様式に合う表があれば拾うことを試験で固定した。

適用範囲。

    kind=exp       P13 applicable=True   -> 実行
    kind=impl      P13 applicable=False  -> SKIP
    kind=analysis  P13 applicable=False  -> SKIP

既存検査の不変。`git --no-pager diff -U0 tools/preflight_task.py | grep '^-[^-]'` の
削除行は `EXP_ONLY = {"P4", "P5"}` の 1 行のみ。P1〜P12 の番号・順序・挙動は変えていない。

### check_proposal（完了判定 e）

一覧は規約から読む設計だったため、表に行を足すだけで追随した。
実装側に在ったのは健全性検査の直値 `len(items) != 14` だけで、これを
`EXPECTED_CARD_ITEMS = 16` へ移した（試験 `test_expected_card_items_matches_conventions` が
規約との一致を縛る）。

| 入力 | `missing_heading` | `hits` |
|---|---|---|
| #15 を欠く | 1 | 1 |
| #16 を欠く | 1 | 1 |
| 16 件すべて在る | 0 | 0 |

既存の検査結果は不変。禁止語 15 語、数値必須 `[5, 6, 10]`（`#15 の表に UNKNOWN が…` の
注記は「数値で書く」を含まないため `numeric_items` に入らない。試験で固定した）。

## Task E — 検証

| 命令 | 結果 |
|---|---|
| `make task-validate TASK=…` | exit 0、`1 task(s), 0 failed` |
| `make task-preflight TASK=…` | exit 0、`6 PASS / 0 WARN / 7 SKIP / 0 FAIL` |
| `make forbidden-check TASK=…` | exit 0、`violations: []`、`permitted` 1 件 |
| `make spec-check TASK=…` | exit 0、`rules_checked: 8`（変更前と同じ） |
| `make docs-check` | exit 0、`対象 43 文書 / ターゲット 34 件、食い違いなし` |
| `pytest tests/` | 6 failed / 595 passed（変更前 6 failed / 567 passed） |

失敗した 6 件は変更前と**同一の集合**である
（`test_engines` 1、`test_fetch_task` 1、`test_research_logger` 4）。

### 試験が空振りでないこと（完了判定 i）

`check_symmetry_table()` の UNKNOWN 判定を `if False:` へ差し替えて試験を回した。

    2 failed, 26 passed
      FAILED tests/test_symmetry_gate.py::test_p13_fails_on_unknown_row
      FAILED tests/test_symmetry_gate.py::test_template_prereg_fails_p13_with_every_row_unknown

原本へ戻して要約値を照合した（`339bf315…02fe` が一致）。戻した後は 28 passed。

### lint

`ruff check` は変更・追加した 4 ファイルすべてで `All checks passed!`。
repo 全体の `make lint` は**変更前から**落ちている（`black --check` 73 ファイル、
`ruff` 3 件。いずれも本契約が触っていないファイル）。本契約で件数は増えていない。

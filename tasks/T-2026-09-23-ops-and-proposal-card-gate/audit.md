# audit — T-2026-09-23-ops-and-proposal-card-gate

実測の生の記録。**判断は RESULT.md にあり、ここには測った値だけを置く。**
実行ホスト `m2`、分岐 `feat/ops-and-proposal-card-gate`、起点 `origin/phase0` の `66855c5b`。

## A1. 開始状態（Task A）

    $ git rev-parse --abbrev-ref HEAD          feat/ops-and-proposal-card-gate
    $ git log --oneline -1                     66855c5b Merge pull request #192 ...
    $ git status --short                       （本契約のディレクトリのみ）
    $ git log -1 --format=%H -- context/conventions.md
                                               c801e17c3231fe1f2b7c8072e1a960e6dbab8ca5
    $ git log -1 --format=%H -- runindex/      4e97b3deae28e653948c19309d229c755587c42b
    $ grep -c '^<a id=' context/conventions.md 11
    runindex/index.csv        1558 行（見出しを除く）
    runindex/experiments.csv   476 行
    runindex/verdicts.csv     1506 行
    spec.yaml 127 件 / schema 通過 127 件（impl 87 / analysis 27 / exp 13）
    pytest                     6 failed, 609 passed
    check_spec の規則           8 件
    L3 の検査                  P1〜P13
    旧様式 result.yaml         schema エラー 15 件

開始時に未追跡だった session digest 4 件は `git stash push -u` で退避した（stash@{0}）。
**消していない。**

稼働中の常駐処理が抑止に対応していることの確認:

    $ grep -c sync-pause ~/bin/m2-sync.sh      2

`make task-start` が `.sync-pause` を作成した。報告の後に移動で解除する。

## A2. 雛形の形（完了判定 a）

`check_proposal.py` の `_bodies_by_number` は markdown の見出しからカードの番号を取る
（`_MD_HEADING` と `_heading_number`）。表の行は見出しではない。付録 A の表だけを
置いた文書を実際に掛けた結果:

    検出 16 件（禁止語 0 / 見出し欠落 16 / 数字欠落 0）

**セルを埋めても見出しは生まれないため、この形では永久に通らない。**
見出しと表を併記した雛形の実測:

    $ python tools/check_proposal.py docs/proposals/_template.md
    missing_number   docs/proposals/_template.md:36  カード #5（期待効果量（点））の本文に数字が無い
    missing_number   docs/proposals/_template.md:38  カード #6（成功確率（主観）の本文に数字が無い
    missing_number   docs/proposals/_template.md:46  カード #10（費用（run 本数 × 時間））の本文に数字が無い
    規約から読んだ禁止語 15 語 / カード 16 件（数値必須 [5, 6, 10]）
    検出 3 件（禁止語 0 / 見出し欠落 0 / 数字欠落 3）     exit 1

#5 #6 #10 を埋めた文書: 検出 0 件、exit 0。

## A3. 規約の追記（完了判定 b）

    $ git diff --numstat context/conventions.md    10      0      context/conventions.md
    $ grep -c '^<a id=' context/conventions.md     11

10 行追加・0 行削除。**削除が 0 であることが既存行の本文が不変であることの実測である。**
追記は `proposal_gate` 節の末尾（役割分離の表の後）の「置き場と参照」5 行と、
変更履歴の 1 行、および見出しと空行である。新しいアンカーは設けていない。

追記の後も規約の読み取りが壊れていないこと（検査器は写しを持たない）:

    card_items() == 16 件、forbidden_words() == 15 語、numeric_items() == {5, 6, 10}

## A4. schema（完了判定 c）

`intent` は `additionalProperties: false` のため、任意項目の追加で足りる。

    既存 spec.yaml 127 件 → 127 件が通過（変更前と同じ）
    intent.proposal_card に整数 3 を入れる → "3 is not of type 'string'"
    intent.proposal_card に文字列 → 通過

## A5. P14 の 7 種（完了判定 d、ゲート G2）

試験 `tests/test_proposal_card_gate.py`（21 件）で測った内訳。

| 入力 | 実測 |
|---|---|
| kind=impl | SKIP「kind=impl のため対象外（exp のみ）」 |
| kind=analysis | `decide_applicability(...)["P14"] is False` |
| 完了済み（result.yaml に gates[].verdict） | SKIP「完了済み（result.yaml に verdict あり: 1 件）のため対象外」 |
| 例外 `…-stage1-detector-towers-r2` | SKIP「導入前の契約のため対象外」 |
| 例外 `…-stage1-phase-tower-r3` | SKIP（同上） |
| `intent.proposal_card` が無い | FAIL「intent.proposal_card が無い。提案カードを docs/proposals/ に置き、経路を書くこと」 |
| 経路のファイルが無い | FAIL「提案カードが無い: docs/proposals/2026-01-01-no-such-card.md」 |
| 雛形を指す | FAIL「docs/proposals/_template.md が check_proposal.py を通らない（検出 3 件）: …」 |
| 埋めたカードを指す | PASS「検出 0 件（カード 16 件 / 禁止語 15 語を検査）」 |

完全一致の対照（部分一致にすると全て免除される）:

    T-2026-09-19-stage1-detector-towers-r3            FAIL
    T-2026-09-19-stage1-detector-towers-r2-followup   FAIL
    stage1-detector-towers-r2                         FAIL

端から端までの確認（一時契約 `T-2026-09-23-p14-control` を置いて実施、測定後に削除）:

    カード無しの exp    P14 ... FAIL intent.proposal_card が無い。…
    雛形を指す exp      P14 ... FAIL docs/proposals/_template.md が check_proposal.py を通らない（検出 3 件）: …

## A6. `allow_write_incomplete`（完了判定 e、ゲート G3）

実例 4 件（現行の本文、変種 C の実装）:

| task | kind | destination | allow_write | 該当 |
|---|---|---|---|---|
| T-2026-09-16-proposal-gate | impl | docs/ | context/conventions.md | 1 件（spec.yaml:29） |
| T-2026-09-17-amp-compile-timing | impl | docs/stage0/ | experiments/transfer/pd_refin_empty_seed42_tf32/ | 1 件（spec.yaml:38） |
| T-2026-09-19-p13-skip-and-enum | impl | tasks/T-2026-09-19-p13-skip-and-enum/ | tasks/_schema/result.schema.json | 1 件（spec.yaml:31） |
| T-2026-09-18-stage1-detector-towers | exp | experiments/baselines/stage1_dtower/ | 同経路 ＋ runindex/ | 0 件 |

裏づけの issuer_defects: proposal-gate#1、amp-compile-timing#5、
stage1-detector-towers#3、p13-skip-and-enum#4。

適用範囲の三変種の実測（全 127 契約）:

    変種 A 全 kind 無条件            該当 123 件
    変種 B 宣言がある契約だけ        該当   5 件
    変種 C exp は無条件＋他は宣言時  該当  15 件（exp 10 / impl 5）← 採用

`allow_write` を宣言している契約は 127 件中 9 件、exp は 13 件である。

行の同定の誤り（本契約の実行中に見つけて直した）: 素朴に `allow_write` を含む行を探すと
`meta.amendments` の理由の本文を先に拾い、amp-compile-timing で 18 行目を指した。
項目の行だけを当てる型（`_KEY_ALLOW_WRITE`）に替えて 38 行目になった。

## A7. L1-10（完了判定 f）

    既存 127 契約での L1-10 の該当   0 件

| 入力 | 実測 |
|---|---|
| 正しい順（G1 after A → G2 after C） | PASS |
| 同じフェーズに二つ（B → B） | PASS |
| 順序を入れ替え（C → A） | FAIL「gates の並びが phases の並びと同じ順ではありません…」 |
| 実在しない id（Z） | FAIL「phases に無いフェーズ Z を指しています（実在するのは A, B, C）…」 |
| after が空 | FAIL（同上、`(空)` と表示） |
| gates を置かない | 対象外（該当 0 件） |

## A8. `.gitignore`（完了判定 g）

    $ git check-ignore -v .sync-pause .sync-pause.released
    .gitignore:244:.sync-pause*	.sync-pause
    .gitignore:244:.sync-pause*	.sync-pause.released

    $ touch .sync-pause.released && git status --porcelain | grep -c 'sync-pause'   0
    $ touch .sync-paus-control  && git status --porcelain | grep 'sync-paus'
    ?? .sync-paus-control                     ← 陽性対照。常に空ではない

実在の検査が版管理と独立であることの実装の行:

    scripts/sync/m2-sync.sh:44   if [ -f "$M2DIR/.sync-pause" ]; then

この行は `git` に触れない。**追跡の状態ではなくファイルの実在だけを見る。**
最初に置いた対照 `.sync-pauseX-control` は型 `.sync-pause*` に一致してしまい対照に
なっていなかった。一致しない名へ取り直した（規約の注意 3）。

## A9. 試験（完了判定 i）

    変更前   6 failed, 609 passed
    変更後   6 failed, 644 passed

失敗している 6 件は変更前から同じ（test_engines 1 / test_fetch_task 1 / test_research_logger 4）。
本契約の変更で新たに落ちた試験は `test_symmetry_gate.py::test_p13_is_last_and_p1_to_p12_are_unchanged`
の 1 件で、P13 が末尾であることを固定していたため。P14 を末尾に足した実態に合わせて
「P13 の位置が 13 番目である」ことの固定へ変えた。**P13 の番号・順序・名前・挙動は不変。**

陽性対照: 雛形から見出し #12 を落とすと 4 件が落ちた。復元後は 21 件すべて通過。

## A10. 検査（Task E-2）

    make task-validate TASK=…     OK   1 task(s), 0 failed        exit 0
    make task-preflight TASK=…    6 PASS / 0 WARN / 8 SKIP / 0 FAIL exit 0
    make forbidden-check TASK=…   violations: []、permitted 1 件    exit 0
    make spec-check TASK=…        規則 9 件、該当 0 件              exit 0

`forbidden-check` の `permitted` は `context/conventions.md`（契約の allow_write による許可）
1 件のみ。`rejected_allowances` は空で、上限に触れた宣言は無い。
変更した 23 経路のうち禁止領域の内側はこの 1 件だけである。

## A11. 旧様式 result.yaml（完了判定 h）

    $ （現行 schema で検証）   15 件のエラー

内訳は必須項目の欠落 10 件（task_id / status / host / branch / tests / deviations /
issuer_defects / followups / unknowns / commits）、未知の項目 1 件（8 個の最上位項目）、
gates の未知の項目 2 件（after）、gates の verdict の語形 2 件（PASS は小文字でない）。

旧 RESULT.md（179 行）と audit.md（630 行）を読んだが、**試験に関する記録は一件も無い**
（`grep -i 'pytest|試験|test'` の該当 0 件）。`tests` の 3 整数は実測不能である。
対応表は RESULT.md §7。利用者の決定により据え置いた。

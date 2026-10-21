# RESULT — T-2026-10-22-proposal-card-tower-reselect-search

ホスト dlsta（容器 `4f3861ae8d3b`）。分岐 `feat/proposal-card-tower-reselect-search`（起点 origin/phase0 `7e30bdde`）。時刻は JST。
命令と出力の全文は `audit.md`（以下 `audit:行`）。参照の原文（prohibitions・issuer_cautions・proposal_gate）は audit:158 に置いた。
`conventions_rev` `2d946b07`・`runindex_commit` `63ae65da`・counts 1961/750/1506 は起票時と一致（audit:148）。

## 判定

**verdict: pass。** 二つの文書を配布した本文のまま置き、カードは `check_proposal.py` で検出 0 件、P14 の関数でも PASS した。

| 関門 | 結果 | 実測 |
|---|---|---|
| G1 | pass | 分岐 feat/、HEAD = merge-base = origin/phase0 = `7e30bdde`、porcelain は契約のディレクトリだけ、§4 の二つの名前は ABSENT（audit:43、53） |
| G2 | pass | カード検出 0（禁止語 0 / 見出し欠落 0 / 数字欠落 0）、陽性対照 1 件と 1 件、失敗の名前の集合 6 → 6（同一）（audit:99、126） |

## 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 済 | 分岐・起点・作業ツリー・試験の前の値（6 failed / 925 passed）・一覧（ptower-20 と _template の二つ、briefs/ 無し）（audit:8〜79） | 同じ命令で既存の `2026-09-27-ptower-20.md` は EXISTS |
| b | 済 | 二つとも写す前・写した後で sha256 と bytes が宣言と一致、cmp 差なし、CR 0、属性なし（audit:79、86） | カードの写しに 1 バイト足すと `cfe50dcc…` に変わる |
| c | 済 | 置いたカード検出 0。既存カード ptower-20 も 0（audit:99） | 禁止語「本命」を足した写しで禁止語 1、`## 9. 最安の殺し実験` を消した写しで見出し欠落 1。陰性対照（二度目）0 |
| d | 済（字面との差は §起票者の誤り） | 追跡される変更は二文書の追加・契約のディレクトリ・`tasks/inbox.d/` の 1 件（audit:156）。forbidden-check pass。失敗の名前の集合は同一 | repo の外の clone の写しに `data/_pc_control.txt` を足すと fail（写しは消した）（audit:135） |
| e | 済 | 下の「送出」 | `gh pr view` の実測（number・baseRefName・headRefName・isDraft） |

## 実測

| 置いた経路 | sha256 | bytes |
|---|---|---|
| `docs/proposals/2026-10-21-tower-reselect-search.md` | `671486dfd36f4b50ae5c322a1ada49de871edf3b5719c18fc1bb5321fb6049be` | 63215 |
| `docs/proposals/briefs/2026-10-21-tower-reselect-search-critique-brief.md` | `eef6a488028bc30cfecc3285713d9e57f3cb6e47c1a2e374f87f8cfecceb1ec5` | 5935 |

P14 の関数 `check_proposal_card` に `intent.proposal_card` としてこのカードを渡すと PASS、存在しない名前で FAIL（audit:99 の C5）。

## 起票者の誤り

- **self_contradiction**: acceptance d は「二つの文書以外に追跡されるファイルの変更が無く」とするが、Task D.1 は契約のディレクトリも認め、
  手順書は `tasks/inbox.d/<task_id>.md`（1 契約 = 最低 1 行）を求める。字面どおりなら RESULT.md の commit（task-release の前提）とも両立しない。
  D.1 と手順書に従い、三つ（二文書・契約のディレクトリ・inbox.d の 1 件）を変更範囲とした

## 逸脱

- 判断: 開始前の試験を背景で回している間に Phase B の写しを置いた。`tests/` は `docs/proposals/` を走査しない（grep で確認）ため前の値に影響しない（audit:64）
- 判断: §7 d の「data/ に一件足した写し」は、§6.4（data/ に書かない）と両立させるため repo の外の clone で行った
- 判断: 手順書の RESULT「1. 解決された参照」は、§8 の 60 行と節の指定に合わせ、原文を audit.md に置いて冒頭の 1 行で指した
- 判断: CLAUDE.md の README.md の更新はしていない。acceptance d が変更範囲を限るため

## 想定外・UNKNOWN

- カードは批判会話への依頼文の経路を本文で指していない（冒頭の「依頼文: なし」は生成会話の依頼文の欄）。本文は変えていない
- カードが置き換えるとする前のカード `2026-10-17-tower-reselect-andrew` は `docs/proposals/` に無い
- 既存の 6 件の試験の失敗は本契約の前から在り、原因は調べていない

## 送出

- PR: PENDING
- `make task-report`: PENDING

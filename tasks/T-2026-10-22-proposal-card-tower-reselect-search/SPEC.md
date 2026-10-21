# 両塔の学び直しの探索の手続きのカード（四版）と批判会話の依頼文を docs/proposals/ に置く

**task_id:** T-2026-10-22-proposal-card-tower-reselect-search  **kind:** impl

**本契約では GPU を使用しない。** 実行ホストは問わない（文書の配置だけ）。

## 1. 背景

- 両塔（P\*-15-COCO と D\*-COCO）の学び直しは、処方をハイパーパラメータ探索で選び直す（F 2026-10-19 の決定）。探索の手続きは提案カードに書き、批判会話（web 検索あり）を経て利用者が判定した（2026-10-22）。判定を反映した四版が本契約のバンドルに在る
- exp の実行直前検査 P14（`tools/preflight_task.py` の proposal_card_checked）は、`intent.proposal_card` の経路のファイルが在り、`tools/check_proposal.py` を検出 0 件で通ることを確かめる。カードが repo に無いと exp は始まらない。規約 `conventions#proposal_gate`「置き場と参照」は、カードを `docs/proposals/YYYY-MM-DD-slug.md` に、依頼文を `docs/proposals/briefs/` に置くと定める
- 本契約は二つの文書を置くだけである。批判会話の報告の全文（引用の照合、検索の記録、試算のコード。約 140 KB）は配布の上限で本契約に入れない。プロジェクト文書に残し、カードの却下表が規約の求める出力である。**本文は配布したまま写す。書き直さない。** 内容の妥当性は批判会話と利用者の判定が持つ

## 2. 利用者の決定（本契約が従うもの）

- 2026-10-22: カードの判定（F 2026-10-22 の決定の行）。却下表の A・B・C・D・E・F・O を採用。四版はそれを反映した版である
- 2026-10-21: dlsta で回す実験はハイパーパラメータ探索のためだけに使う。本契約には関係しないが、カードの §8・§16・付録 E に反映済み

## 3. 確定した事実

| 事実 | 出所 |
|---|---|
| カードの検査器は `tools/check_proposal.py`。規約の proposal_gate 節から禁止語（15 語）とカードの項目（16 件）を読み、見出しの有無と数値の有無と禁止語を検査する。内容は見ない | `tools/check_proposal.py` の冒頭の説明 |
| P14 は repo の根からの相対経路でカードを探し、`check_proposal.check` を呼ぶ | `tools/preflight_task.py` の `check_proposal_card` |
| 既存のカードは `docs/proposals/2026-09-27-ptower-20.md` と雛形 `_template.md` の二つ。`docs/proposals/briefs/` は無い | phase0 7e30bdde の `docs/proposals/` |
| バンドルの追加ファイルは `tasks/T-2026-10-22-proposal-card-tower-reselect-search/` の直下に展開される。sha256 と bytes は spec の `inputs.bundle_extras` の宣言 | `tools/fetch_task.py` の `extras_from_spec` と `check_extras` |
| 起票者の手元で、カードは `check_proposal.py` で検出 0 件、禁止語を一語足した写しで検出 1 件、見出しを一つ消した写しで検出 1 件 | 起票者の実測（2026-10-22、phase0 7e30bdde の写し） |

## 4. 置き場と名前

| バンドルの追加ファイル | 置き場 |
|---|---|
| `proposal_card.md`（カードの四版） | `docs/proposals/2026-10-21-tower-reselect-search.md` |
| `critique_brief.md`（批判会話への依頼文） | `docs/proposals/briefs/2026-10-21-tower-reselect-search-critique-brief.md` |

- カードの名前の日付は起票日（2026-10-21）で、規約の `YYYY-MM-DD-slug` に従う。四版の日付（2026-10-22）はカードの冒頭に書いてある
- `briefs/` は無ければ作る

## 5. Task

### Task A — 開始状態

1. 分岐が `feat/` で始まり、起点が `origin/phase0` であること。作業ツリーが清浄であること（手順書「0. 始める」が確かめる。その出力を記録に写す）
2. `docs/proposals/` 直下と `briefs/` の一覧を記録し、§4 の二つの名前がどれも無いことを確かめる。在れば停止して諮る
3. 試験の失敗の名前の集合（`tests/`）を記録する
4. 追加ファイル二つの sha256 と bytes を測り、spec の宣言と一致することを記録する

### Task B — 配置

1. §4 のとおりに写す。内容を一文字も変えない（改行の種類も含む）
2. 写した後の二つの sha256 を測り、宣言と一致することを記録する（写す前と写した後の両方）

### Task C — 検査

1. 置いたカードを `tools/check_proposal.py` にかけ、検出 0 件（禁止語 0、見出し欠落 0、数字欠落 0）を記録する。repo の根から実行する（P14 と同じ呼び方）
2. 陽性対照（repo の外の一時の置き場に写しを作り、検査の後に消す）:
   - 禁止語を本文に一語足した写し → 禁止語の検出が 1 件以上
   - 見出し `## 9. 最安の殺し実験` を消した写し → 見出し欠落の検出が 1 件
3. 陰性対照: 置いたカードをもう一度検査して同じ結果（検出 0 件）
4. 既存のカード `docs/proposals/2026-09-27-ptower-20.md` も検査し、検出 0 件のまま（規約の読み取りが壊れていないことの確かめ）
5. 試験を全件回し、失敗の名前の集合が Task A の 3 と同じであること

### Task D — 検証と報告

1. 追跡されるファイルの変更が §4 の二つ（追加）と本契約のディレクトリだけであること（集合差で示す）
2. `make forbidden-check` が通ること
3. RESULT.md と result.yaml を書き、PR を作る（base は phase0、Draft でない）
4. 台帳への送り返し（手順書「8. 終える」）

## 6. 禁止

実行者の操作に対する禁止である（同期処理による配布は含まない）。

1. 二つの文書の本文を変えない。禁止語の検出が出ても本文を直さない（停止して諮る）
2. 規約（`context/conventions.md`）、`docs/issuer-defects.md`、`docs/proposal-gate.md`、雛形 `_template.md` に触れない
3. 生成物（`context/auto/*`、`tasks/inbox.md`）の再生成と `*-check` を回さない
4. `data/`・`experiments/`・`runindex/` に書かない
5. GPU を使わない

## 7. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐・起点・作業ツリー・試験の前の値・`docs/proposals/` の一覧が記録されている | 一覧に §4 の名前が無いことを、名前を一つ変えた写しの一覧（在る名前を含む）で「在る」と出る命令で確かめる |
| b | 配置と要約値 | 二つの文書が置き場に在り、sha256 が宣言と一致 | 1 バイト変えた写しで sha256 が変わる |
| c | 提案関門の検査 | 置いたカードが検出 0 件。陽性対照の二つの写しがそれぞれ 1 件以上 | 陽性対照そのもの。陰性対照（同じカードの二度目）が 0 件 |
| d | 変更範囲と試験 | 追跡される変更が二つの追加と契約のディレクトリだけ。forbidden-check が通る。試験の失敗の名前の集合が増えていない | `data/` に一件足した写しで forbidden-check が落ちる。写しは消す |
| e | PR | 存在し、base phase0、分岐 feat/proposal-card-tower-reselect-search、Draft でない | PR の表示の実測（番号、base、head、draft の値） |

## 8. 報告の構成

`RESULT.md` は 60 行以内。節は 判定／完了判定（表。実測値つき）／実測（置いた二つの経路と sha256）／起票者の誤り／逸脱／想定外・UNKNOWN／送出（PR 番号と終了コードだけ）。命令と出力の全文、対照の出力、変更範囲の一覧、台帳の応答は `audit.md` へ。`RESULT.md` から `audit.md` を行番号で指す。

## 9. 次の契約

本 PR の統合の後に、探索（dlsta）の exp を配布する。exp は `intent.proposal_card: docs/proposals/2026-10-21-tower-reselect-search.md` を参照する。

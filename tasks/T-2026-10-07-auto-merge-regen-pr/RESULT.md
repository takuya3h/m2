# RESULT — T-2026-10-07-auto-merge-regen-pr

**判定: pass（統合後の実測は未了）。** `regen-projections.yml` に三つを足した。一つ目は統合の段で、三条件を統合の直前に読み直し、`GITHUB_TOKEN` で merge commit を作る。二つ目は、差分が無いときに開いた自動 PR を閉じる段。三つ目は、PAT の未設定と無効を言い分ける文言。手元の試験は 6 通りと認証の 4 通りがすべて期待どおりで、条件を壊した版では陰性の場合が統合されることも確かめた。`GITHUB_TOKEN` で実際に統合できるかは、統合後の実測で判定する（§4）。
ホスト `philip`、分岐 `feat/auto-merge-regen-pr`、起点 `origin/phase0` = `67c4cc44`。実施日時は 2026-10-07 JST。証跡は `audit.md` にある。

## 1. 解決された参照

- `conventions_rev`: `context/conventions.md` の最終 commit を実測した。結果は `073f9dc0`（2026-10-02 19:46 JST）で、契約の記載と一致する。
- `inject_verbatim`: `conventions#prohibitions`（`context/conventions.md:98-107`）と `conventions#issuer_cautions`（`:150-187`）。原文はその行番号のとおり。本契約に効いたのは注意 3（対照を両方向で取る）、8（検査が値を出さない）、12（判断の前に最新を確かめる）である。
- `inputs.data` は**参照しなかった**。生成の道具も workflow もデータを読まない。

## 2. 前提の測定結果（Phase A、`audit.md` §1-3、G1: pass）

| 項目 | 結果 |
|---|---|
| 必須の状態検査 | **無い。** 統合が待たされることはない |
| 承認 | 0 件。迂回の許可も push の制限も無い。`enforce_admins: true` |
| 最新の基点の要求 | 無い（状態検査が無いため `strict` も無い）→ 基点の条件は workflow の側で見る |
| 許可された方式 | merge・squash・rebase のすべて。`allow_auto_merge: true` |
| これまでの方式 | 直近 30 件の PR すべてが **merge commit**（親が 2 つ）→ `--merge` を使う |
| 統合に要る権限 | REST の統合は Contents の write、PR を閉じるのは Pull requests の write（GitHub の文書） |
| GITHUB_TOKEN での統合 | できないと示す根拠は見つからなかった。**実際に通るかは UNKNOWN で、統合後の実測で判定する** |
| 次の workflow を起こすか | 文書によれば、GITHUB_TOKEN が起こした push は新しい実行を作らない（例外は `workflow_dispatch` などで、push は含まない）。統合後に確かめる |

## 3. 統合の条件と試験の結果（Phase B、完了判定 D-G、G2: pass）

`.github/workflows/regen-projections.yml`

| 要件 | どう満たしたか |
|---|---|
| 権限 | `contents: write` と `pull-requests: write`（`:15-17`） |
| 生成物の一覧 | job の `env` に一か所だけ置いた（`:27-29`）。作り直しと統合の条件が同じ一覧を見る |
| 統合の段 | `Merge auto PR if only outputs on latest phase0`（`:112-146`）。`if: changed == 'true'`。認証には `github.token` を渡す |
| 条件 3（作成元） | 一覧は `isCrossRepository` が偽のものに限る。さらに `gh pr view` の head が `auto/regen-projections`、cross が `false`、base が `phase0` であることを確かめる（`:119-131`） |
| 読み直し | 統合の段の中で、phase0 と auto 分岐を fetch し直す。PR の先頭の oid が分岐の先頭と一致することを確かめる |
| 条件 2（基点） | `git rev-list --parents -n1 <head>` が「head と phase0 の先頭」であること。親が一つで、それが現在の phase0 の先頭（`:133-134`） |
| 条件 1（差分） | `git diff --name-only <phase0> <head>` が空でなく、すべて生成物の一覧に含まれること（`:135-143`） |
| 統合 | `gh pr merge --merge --match-head-commit <head>`（`:145`）。条件を満たさなければ `::error::自動で統合しない: <理由>` を出して exit 1 |
| 空の PR を閉じる | `Close auto PR if nothing to change`（`:147-157`）。`changed == 'false'` のとき、fork ではない自動 PR を閉じる |
| 文言を分ける | PR を作る段で `gh api repos/<repo>` を一度試す（`:91-104`）。未設定・無効（401）・判別できない、の三つに分ける。値も応答の本文も出さない |
| 既存の別の自動実行 | `auto-draft-pr.yml` は変えていない |

**手元の試験。** 前の契約の枠を広げた。偽の origin と、状態を持つ偽の `gh` を使う。台本は scratchpad の `t2/harness.sh`。

| 場合 | 期待 | 結果 |
|---|---|---|
| 1 生成物だけの差分 | 統合が呼ばれる | 統合が 1 回呼ばれた。`--match-head-commit` は auto 分岐の先頭の oid |
| 2 生成物以外を含む（陽性対照） | 統合が呼ばれない | 0 回。`生成物以外を含む: stray.txt` で exit 1 |
| 3 基点が古い（PR の後に phase0 が進んだ） | 呼ばれない | 0 回。`基点が phase0 の先頭 … ではない` で exit 1 |
| 4a 作成元が fork（同名の分岐） | 呼ばれない | 0 回。`開いた自動 PR が見つからない` で exit 1 |
| 4b 作成元が別の分岐 | 呼ばれない | 0 回。`作成元が … ではない（head=feat/other …）` で exit 1 |
| 4c PR の先頭が分岐の先頭と違う | 呼ばれない | 0 回。exit 1 |
| 5 差分なし・PR なし | 何もしない | 統合も閉じる操作も 0 回。`gh` の呼び出しは一覧の 1 回だけ |
| 6 差分なし・PR が開いている | 閉じる | #7 を閉じた。同名の fork の #8 は閉じていない |
| 認証: 未設定・401・500・正常 | 文言が分かれ、値は出ない | 未設定・無効・判別できない・PR 作成の順に分かれた。合成した token の値の出現は 4 通りとも 0 件 |

**試験自体が働いているかの確認。** 条件 1・2・3 の拒否を「常に通す」に書き換えた版で、同じ試験を走らせた。場合 2・3・4b で統合が呼ばれた。したがって試験は、判定が常に通す壊れ方を検出する。試験はすべて scratchpad の中で行い、作業ツリーの `git status --porcelain` は試験の前後で一致した。書式の検査（actionlint）は道具が無く UNKNOWN。

## 4. 統合後の確かめ方（完了判定 H）

**本 PR を統合すること自体が最初の契機になる。** 本契約の記録で生成物が古くなるためである。

| 確かめること | 方法 | 期待 |
|---|---|---|
| 自動 PR が作られたか | `gh pr list --head auto/regen-projections --state all --limit 1` | 一件 |
| 自動で統合されたか | `gh pr view <番号> --json state,mergedBy -q '.state+" "+.mergedBy.login'` | `MERGED github-actions` で、人の操作が無い |
| 統合の後 | `gh run list --workflow regen-projections.yml --limit 3` | 自動の統合では新しい実行が起きない（起きても「差分なし」で止まる） |
| 開いた自動 PR | `gh pr list --head auto/regen-projections` | 0 件 |
| 失敗したとき | `gh run view <id> --log-failed` で `::error::自動で統合しない:` の理由を見る | GITHUB_TOKEN で統合できなければ、統合の段がエラーになる |

## 5. 送出

PR 番号と終了コードは result.yaml の `pr` と §6 の追記に書く。

## 6. 起票者の誤り

1. **試験の場合「作成元の分岐が違う」は、書かれたとおりに作ると条件 3 を試さない。** 一覧は `--head auto/regen-projections` で絞るので、別の分岐からの PR はそもそも一覧に出ない。統合が呼ばれないのは一覧のためで、条件 3 が働いたからではない。条件 3 が意味を持つのは、同名の分岐を持つ fork と、一覧と詳細が食い違う場合だけである。本契約では 4a・4b・4c としてこれらを試した。
2. **P9 spec_lint の WARN 2 件。** `separated_source@SPEC.md:53` は `\` の継続行で `&&` につながっている。`host_mismatch@:5` は `hostname`（`aolab`）と `.servername`（`philip`）の差である。どちらも実行上の害は無かった（前の契約と同じ）。

## 7. 規約の適用判定・検査

- 禁止語: `tools/check_proposal.py --only forbidden` を送出物（RESULT.md、result.yaml、audit.md、inbox.d、workflow、README の追加行）に当てた。初回は RESULT.md に 1 か所、audit.md に 2 か所、同じ 1 語が一致した。言い換えた後は全件 exit 0。陽性対照（禁止語を 2 語含む合成文）は exit 1。
- 秘匿: `scan_secrets` を、資格情報を環境に読み込んだうえで当てた。初回は「鍵らしい代入」が 2 件出た（RESULT.md:33、audit.md:37）。どちらも値ではなく、参照の名前を代入の形で書いた説明文だった。検査は無効にせず、本文の書き方を変えた後は全件 0 件。陽性対照（鍵の形をした合成文字列と、合成した環境値の照合）はどちらも検出した。出力は種別と行だけ。
- その他: `task-validate` exit 0、`forbidden-check` は pass（違反 0）、試験は 23 件 pass。`taskindex-check` と `inbox-check` は差分ありで exit 2（契約の禁止 5 により再生成しない）。統合の後は仕組みが直す。
- `folds` と `symmetry` は**適用されない**（impl で、比較する腕が無い）。

## 8. 逸脱・想定外・UNKNOWN

- **逸脱（判断）。** 生成物の一覧を、作り直しの段の局所変数から job の `env` へ移した。統合の条件と同じ一覧を見せるためで、作り直しの挙動は変わらない（試験の場合 1・5 で確認）。
- **逸脱（判断）。** 契約の三条件に加えて、PR の先頭の oid が分岐の先頭と一致すること（4c）と、統合の時点での `--match-head-commit` を足した。読み直しの間に分岐が動いた場合に、別の中身を統合しないためである。
- **逸脱（環境）。** CLAUDE.md の方針にある `ctxpack` がこのホストに無く、文書は WebFetch で読んだ。
- **想定外。** `allow_auto_merge: true` だった（前の会話での私の推測と違った）。本契約では GitHub の auto-merge は使わず、条件を満たしたときに即座に統合する。
- UNKNOWN: GITHUB_TOKEN で実際に統合できるか、閉じられるか。自動の統合が次の実行を起こさないか。書式の検査。いずれも統合後に判定する（書式の検査を除く）。

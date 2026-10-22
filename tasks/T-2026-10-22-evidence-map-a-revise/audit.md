# audit — T-2026-10-22-evidence-map-a-revise

実行ホストは Bengio。時刻は JST。外部への問い合わせは照合器（`tools/verify_evidence_ids.py`）の `Client` だけを使い、連絡先を入れていない（User-Agent `egosurgery-evidence-verify/1.0`）。

## 0. 開始

- 開始時の分岐 `feat/evidence-map-a-place`（112b09bd、清浄）。`feat/evidence-map-a-revise` は手元・遠隔とも無し、`tasks/T-2026-10-22-evidence-map-a-revise` の履歴も無し、`.sync-pause` 無し。
- `git fetch origin && python3 scripts/task_start_classify.py` → 全区分 0 件、`[task-start] 分類: 通す`。
- `make task-start` → `分岐を作成: feat/evidence-map-a-revise（起点 origin/phase0）`、`[task-start] .sync-pause を作成`、`OK T-2026-10-22-evidence-map-a-revise`、`[task-start] 完了。`。目印の中身は `task_id=T-2026-10-22-evidence-map-a-revise` / `branch=feat/evidence-map-a-revise` の 2 行。
- 取り込み直後の契約本文の sha256: SPEC.md `24023b7b46b6f911b3b311362c8383e9eb0049fefbd1b1ec71ad306b223d5887`、spec.yaml `9e02a74e757997b4e70221d4c01f4767e2503c5059fd826578f8c77128430f0e`。報告前に測り直して同じ値（完了判定 e の、予測が事前の値のままであることの根拠）。

## 1. 検証とプリフライト

`make task-validate` → `OK T-2026-10-22-evidence-map-a-revise / 1 task(s), 0 failed`、exit 0。

`make task-preflight` → `RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL`、exit 0。PASS は P1 venv_active・P6・P7・P8・P9 spec_lint（規則 9 件、該当なし）・P10。SKIP は P2・P3・P11（plan.env.preflight に記載なし）、P4・P5・P13・P14（kind=impl のため対象外）、P12（解決前提の参照なし）。SKIP は合格ではない。

`context/conventions.md` の最終 commit は `2d946b07a57abebc4a8f66150d6dbaf2ccd22186` で、`contract.conventions_rev` と一致。

## A. 起点（G1）

- 分岐 `feat/evidence-map-a-revise`、HEAD = origin/phase0 = `112b09bd53df04981dc25e6438b1d8b353c86ce0`（SPEC の起点と同じ）。
- SPEC の表の 10 件を `sha256sum` で測り、10/10 一致（v2 `77ab821d…28a9`、旧 A `49effd15…5def`、旧 B `5aab3910…ad2d`、B `11d2e3ef…4caa`、C `80837fcf…5630`、N `74ea24a6…fe4f`、README `35a8922a…c11c`、雛形 `69e95ea3…1376`、verification の A の md `59ae72c2…e520`・json `e1e6307c…a624`）。
- 表に無い起点の値: reports/ 12 件と verification/ の地図 A 以外 6 件の sha256 を測った（§D-2 の差分の比較元。差分が地図 A の 3 件だけなので、この 18 件の値は起点と同一）。
- `expected-ids.txt` の sha256 `2e2bc4b689da51ace2b9c519f215e92407bc532abafe9be44cb80c4dcbdb50f6`（SPEC と一致）。
- 受け渡し: 最初の確認では置き場 `~/slocal2/m2-incoming/T-2026-10-22-evidence-map-a-revise/` が存在しなかった。利用者に伝えて待ち、「おいた。再開して」を受けて測り直した。直下は 1 件、`2026-10-21-A-phase-tower-candidates.md`、265380 バイト、sha256 `941f4c8dbd1c7c0d54c18ceee3899aa2cb73c66655d1e14960af0d3eb9507bd9`（SPEC と一致）。realpath `/home/ubuntu/slocal2/m2-incoming/…` は repo（`/home/ubuntu/slocal2/m2`）の外にある。
- 照合先への到達（`Client.get` を逐次）:

| JST | 系統 | 問い合わせ先 | HTTP | バイト |
|---|---|---|---:|---:|
| 2026-10-22 13:04:38 | doi | https://doi.org/api/handles/10.1038/s41586-020-2649-2 | 200 | 540 |
| 2026-10-22 13:04:38 | crossref | https://api.crossref.org/works/10.1038/s41586-020-2649-2 | 200 | 26102 |
| 2026-10-22 13:04:38 | datacite | https://api.datacite.org/dois?page%5Bsize%5D=1 | 200 | 6291 |
| 2026-10-22 13:04:40 | arxiv | https://export.arxiv.org/api/query?id_list=1706.03762&max_results=1 | 200 | 2962 |

G1: pass。

## B. 置き換え（G2）

- `cp` で置き場の一件を `docs/evidence/2026-10-21-A-phase-tower-candidates.md` へ置き換えた（置き場のファイルは残した）。置き換え後に作業ツリーのファイルから測った sha256 `941f4c8d…07bd9`、265380 バイト。
- `git diff --stat`: 1 file changed, 24 insertions(+), 23 deletions(-)。
- v2 と v2.1 の行単位の比較（`difflib.SequenceMatcher`、表の行はセル単位で比べた。§2 の表の列は `ID | 文献 | 書誌 ID | 掲載先 | 方向 | 読んだ範囲 | 出所`、v2.1 の L190）:

| v2.1 の行 | 中身 | 変わった列 |
|---|---|---|
| L3 | 見出しの前の **版:**（v2 → v2.1） | — |
| L5 | 見出しの前の **状態:** | — |
| L65（追加） | §0.2 規則（L56 の見出しの下）に「照合先の値」の注記の意味を 1 行追加 | — |
| L195 | A-04 | 文献・掲載先 |
| L196 | A-05 | 文献・掲載先 |
| L202 | A-11 | 文献・掲載先 |
| L213 | A-22 | 文献・掲載先 |
| L219 | A-28 | 文献・掲載先 |
| L239 / L240 | A-48 / A-49 | 文献 |
| L241 / L242 / L243 | A-50 / A-51 / A-52 | 文献・掲載先 |
| L246 / L247 | A-55 / A-56 | 文献 |
| L251 | A-60 | 文献・掲載先 |
| L259 / L260 / L261 / L262 | A-68 / A-69 / A-70 / A-71 | 文献・掲載先 |
| L263 | A-72 | 文献 |
| L264 | A-73 | 文献・掲載先 |
| L296 | A-105 | 文献・掲載先 |
| L300 | A-109 | 文献 |

表の行 21 行の ID は、SPEC の「v2.1 で変わった箇所」の 21 ID（差の 4 行 + 照合不能の 17 行）と一致した。列数はすべて 7 → 7。「書誌 ID」「方向」「読んだ範囲」「出所」が変わった行は 0。上の表以外の変更は無い（§1・§3〜§12 は不変）。

- この時点の `git status --porcelain --untracked-files=all`: ` M docs/evidence/2026-10-21-A-phase-tower-candidates.md`、`?? tasks/T-2026-10-22-evidence-map-a-revise/SPEC.md`、`?? …/spec.yaml`。

G2: pass。

## C. 様式の検査と照合（G3）

### C-1 様式の検査

`.venv/bin/python tools/check_evidence_map.py`（引数なし = docs/evidence/ のすべて）:

```text
検査 docs/evidence/2026-10-18-B-p2d-interface.md: 違反 0 件
検査 docs/evidence/2026-10-18-C-d2p-interface.md: 違反 0 件
検査 docs/evidence/2026-10-18-N-novelty.md: 違反 0 件
検査 docs/evidence/2026-10-21-A-phase-tower-candidates.md: 違反 0 件
対象外 …（旧 A・旧 B・README・雛形・reports/ 12 件・verification/ の md 4 件。いずれも「見出しの前に **種類:** が無い」）
規約から読んだ禁止語 15 語 / reports/ のファイル 12 件
```

exit 0。地図 A v2.1 は「検査」として出力に現れた。

陽性対照: v2.1 を repo の外（scratchpad）へ写し、A-chatgpt の sha256 `2fd5e851…0ca`（本文に 1 回だけ現れる）を 0 が 64 個の文字列に 1 か所だけ置き換えて検査した。出力 `report_sha256 …/A.md:13 sha256 0000…0000 に一致するファイルが reports/ に無い`、`違反 1 件`、exit 1。実物の地図の sha256 はその後も `941f4c8d…` のまま。

### C-3 抽出の集合

`tools/verify_evidence_ids.py --extract-only` → exit 0、126 行（arXiv 96・DOI 30）。expected-ids.txt と (種別, 小文字の ID) の集合で比べた: expected − extracted = 0、extracted − expected = 0。照合結果 json の results の集合も、expected との差は両方向 0。
陽性対照（両方向）: 抽出集合から 1 ID を除くと expected − x = 1・x − expected = 0、arXiv 9999.99999 を 1 件足すと 0・1。

### C-2 照合

1 回目（2026-10-22T13:05:28+09:00 開始）: `実在・書誌一致 74 / 実在・書誌に差 0 / 実在・照合不能 2 / 不在 0 / 到達不能 50（計 126）`、exit 3、問い合わせ 98 回。到達不能 50 件はすべて arXiv の 1 回目の束（50 ID）。その束の問い合わせの記録:

| JST | 結果 |
|---|---|
| 13:06:28 | TimeoutError: The read operation timed out |
| 13:07:03 | HTTP 429（14 バイト） |
| 13:07:13 | TimeoutError（接続の失敗の引き直し 1 回が尽き、束全体を到達不能とした） |

2 回目の束（46 ID）は 13:07:43〜13:09:39 に 429 が 4 回、13:11:55 に 200（111203 バイト）。1 回目の結果の二件は scratchpad に退避した（repo には残していない）。

判断: 到達不能は「届かなかった」であって書誌の判定ではないため、地図と照合器を変えずに同じ命令をもう一度だけ流した。SPEC の罠 3（間隔を詰めない）と照合器の実測の注記（429 は 10 分あけると戻った）に従い、約 10 分あけた。

2 回目（2026-10-22T13:23:01+09:00 開始）: `実在・書誌一致 123 / 実在・書誌に差 0 / 実在・照合不能 3 / 不在 0 / 到達不能 0（計 126）`、exit 0。問い合わせ 92 回（doi 60・crossref 30・arxiv 2）、すべて HTTP 200（arXiv は 13:24:01 と 13:24:04）。結果の md に記録された地図の sha256 は `941f4c8dbd1c7c0d54c18ceee3899aa2cb73c66655d1e14960af0d3eb9507bd9`。結果の sha256: json `1e17b546ee407eb3bb69c4903507fa516eeed3410753ef565e707776198260de`、md `ac94eceeb7a0880d5a21c19ee8a345c1edb4ce97fc6720a8defdf06047fb2b0d`。

G3: pass（違反 0、集合の差 0）。

### C-4 予測との比較

| 分類 | 予測 | 実測 |
|---|---:|---:|
| 書誌一致 | 123 | 123 |
| 書誌に差 | 0 | 0 |
| 照合不能 | 3 | 3 |
| 不在 | 0 | 0 |
| 到達不能 | 0 | 0 |

予測と違った ID は 0 件。照合不能の 3 件は arXiv 2505.12890・2106.11028・2112.07219 で、注記はいずれも「地図に書誌の行（文献と書誌 ID の列を持つ表の行）が無い」（SPEC の名指しと同じ）。

### C-5 名指しされた ID と前回との突き合わせ

前回（origin/phase0 の照合結果 json。地図 sha256 `77ab821d…`、101/5/20/0/0）と今回を (種別, 小文字の ID) で突き合わせた。分類が変わった ID は 22 件で、内訳は 照合不能 → 書誌一致 17、書誌に差 → 書誌一致 5。ほかの 104 ID は前回と同じ分類。22 件の一覧（今回の題名と著者の判定、照合器の詳細）:

| 行 | ID | 前回 | 今回 | 題名 | 著者 |
|---|---|---|---|---|---|
| A-04 L195 | arXiv 2503.18755 | 差 | 一致 | 一致: 全体 | 一致: 全 4 名 |
| A-04 L195 | DOI 10.1049/htl2.70049 | 差 | 一致 | 一致: 全体 | 一致: 全 4 名 |
| A-05 L196 | DOI 10.1007/978-3-032-31119-1_38 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-11 L202 | arXiv 2103.16327 | 差 | 一致 | 一致: 全体 | 一致: 全 6 名 |
| A-22 L213 | arXiv 2506.01471 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-28 L219 | arXiv 2107.03377 | 差 | 一致 | 一致: 全体 | 一致: 全 7 名 |
| A-48 L239 | DOI 10.1001/jamasurg.2023.6262 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-49 L240 | DOI 10.1038/s41551-026-01622-w | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-50 L241 | arXiv 2608.31048 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-51 L242 | arXiv 2602.13633 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-52 L243 | arXiv 2609.04555 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 5 名 |
| A-55 L246 | arXiv 2210.06096 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-56 L247 | arXiv 2508.10104 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-60 L251 | arXiv 2211.09529 | 照合不能 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |
| A-68 L259 | arXiv 2203.04752 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 2 名 |
| A-69 L260 | arXiv 2608.20157 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 3 名 |
| A-70 L261 | arXiv 2410.21302 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 4 名 |
| A-71 L262 | arXiv 2605.14031 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 4 名 |
| A-72 L263 | arXiv 2209.12157 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 2 名 |
| A-73 L264 | arXiv 2603.14271 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 5 名 |
| A-105 L296 | arXiv 2402.10635 | 照合不能 | 一致 | 一致: 全体 | 一致: 全 6 名 |
| A-109 L300 | arXiv 2202.02326 | 差 | 一致 | 一致: 全体 | 一致: 先頭 3 名（ほか） |

- 前回の差 5 件（A-04 の 2 件、A-11、A-28、A-109）は、すべて書誌一致。
- 照合不能から表の行を持つようになった 17 行の ID は、すべて書誌一致。書誌一致でないものは無いため、照合先の値の転記は要らない（全返値は照合結果 json にある）。
- SPEC が自信の無いものとした 17 行と A-109 も、上のとおり一致した。A-109 は地図の「Chen, Wen, Shi ほか」を先頭 3 名として比べ一致（前回の差の原因とされた API の著者要素の分割は、先頭 3 名の比較には現れなかった）。
- 照合器の判定は API の返値との一致であり、原典の表記の正誤はここでは判断していない。

## D. 検証

- D-2 変えないファイル: docs/evidence/ の md 8 件、verification/ 8 件、reports/ 12 件の sha256 を起点と報告前で比べた（`diff before.sha256 after.sha256`）。違ったのは地図 A（`77ab821d…` → `941f4c8d…`）と、verification/ の地図 A の json（`e1e6307c…` → `1e17b546…`）と md（`59ae72c2…` → `ac94ecee…`）の 3 件だけ。ほかの 25 件は同一。
- `make forbidden-check` → `"status": "pass"`、`"changed": 5`、`"violations": []`、exit 0。
- `make spec-check TASK=T-2026-10-22-evidence-map-a-revise` → `"status": "pass"`、`"hits": 0`、`rules_checked 9`、exit 0。
- commit 前の `git status --porcelain --untracked-files=all`: 地図 A と verification/ の地図 A の二件（M）、tasks/T-2026-10-22-evidence-map-a-revise/ と tasks/inbox.d/T-2026-10-22-evidence-map-a-revise.md（??）。変更範囲（完了判定 b）の外は 0 件。
- make test は回していない（SPEC の罠 7。コードを変えていない）。

## E. 送出



- commit `1f6f39b2` を `origin/feat/evidence-map-a-revise` へ push。
- `gh pr create --base phase0` → https://github.com/takuya3h/m2/pull/256。`gh pr view` の応答: `{"baseRefName":"phase0","headRefName":"feat/evidence-map-a-revise","isDraft":false,"number":256,"state":"OPEN"}`。

### 追加の陽性対照（書誌の差の判定）

repo の外（scratchpad）に、v2.1 の §2 の表の見出し 2 行と A-01 の 1 行だけを写した。題名を `Completely Different Title About Kitchen Robots` に変え、arXiv の ID を外して DOI 10.1007/978-3-031-72089-5_18 だけを残した。`verify_evidence_ids.py --out-dir <scratchpad>` で照合した結果は `実在・書誌一致 0 / 実在・書誌に差 1 / … （計 1）`、exit 0。題名は「差: 題名が一致しない」、著者は「一致: 全 4 名」、問い合わせは 3 回。repo の作業ツリーは変わっていない。

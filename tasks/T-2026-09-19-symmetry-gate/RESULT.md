# RESULT — T-2026-09-19-symmetry-gate

比較の対称性を起票前に確かめる関門を、規約・提案カード・L3 検査・雛形・点検表・
欠陥記録の六つに置いた。**GPU は使っていない。** 実測の詳細は `audit.md`。

## 1. 解決された参照

`contract.inject_verbatim` は 3 件。いずれも `context/conventions.md` の**変更前**の
原文を読み、要約せずに指示へ差し込んだ。

| 参照 | 解決先 | 変更前の状態 |
|---|---|---|
| `conventions#prohibitions` | 禁止事項の表 5 行 | 本契約は触っていない |
| `conventions#issuer_cautions` | 注意 13 件＋実測 3 段落＋シェルの前提 | 注意 14 と実測 1 段落を追加した |
| `conventions#proposal_gate` | 提案カード 14 件＋禁止語 15 語＋三水準＋失敗時手順＋引用規約＋役割分離 | カード #15 #16 と注記 1 文を追加した |

- `contract.conventions_rev`: `e7a5100597a79b3b9c60935bf38d232f8ae96822`（実測。占位を差し替え）
- `created_from.runindex_commit`: `029b5315a4b543fabbebe350e2e1302e2d816d9b`（実測。占位を差し替え）
- `inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref`: 本契約に記載なし（該当なし）

## 2. 判定

**verdict: pass**

| Gate | 判定 | 根拠 |
|---|---|---|
| G1（Task A の後） | pass | HEAD = `ed9211bc` = `origin/phase0`。変更前の数を 7 項目記録。ただし未追跡 3 件の退避は実行基盤が拒否したため、その場に残して要約値で記録した（逸脱 1） |
| G2（Task C の後） | pass | P13 は 6 種の入力で FAIL 5・PASS 1。check_proposal は #15/#16 を欠く文書で 1 件、揃う文書で 0 件。変異試験で試験自身が空振りでないことを確認 |

## 3. 完了判定

| # | 判定 | 実測 | 結果 |
|---|---|---|---|
| a | `conventions#symmetry` が引ける | `validate_task.conventions_anchors()` に `symmetry` あり。`symmetry_zz` は無し | pass |
| b | proposal_gate に #15・#16 | カード行 14 → 16。既存 14 行の要約値 `b884c6da…a925d` が変更前後で一致 | pass |
| c | issuer_cautions に #14 | 注意 13 → 14。既存 13 行の要約値 `bbc6de6c…f190` が変更前後で一致 | pass |
| d | P13 の判定 | 表なし FAIL／UNKNOWN FAIL／理由なし FAIL／揃う PASS／部分一致の別表のみ FAIL／impl・analysis SKIP。6 種すべて `audit.md` に detail 付きで記録 | pass |
| e | check_proposal が #15・#16 を見る | 欠く文書で `missing_heading` 1 件、両方で 0 件。禁止語 15 語・数値必須 `[5,6,10]` は変更前と同じ | pass |
| f | 雛形 | `tasks/_templates/exp/prereg.md` に 15 行の骨組み。雛形から作った prereg で P13 が `UNKNOWN 15 行` として FAIL。**FAIL の行数 15 = 表の行数 15** | pass |
| g | issuer-defects の追記 | 2 型と実例を追加（15 insertions / **0 deletions**）。変更前の全行が現行に在ることを照合 | pass |
| h | check_spec の規則数 | 変更前 8 / 変更後 8 | pass |
| i | 試験 | 6 failed / 595 passed（変更前 6 failed / 567 passed）。失敗は**同一の 6 件** | pass |
| j | PR | 番号 PR_NUMBER_PLACEHOLDER、base `phase0`、分岐 `feat/symmetry-gate`、Draft ではない | pass |

## 4. 実測（前後）

| 対象 | 前 | 後 |
|---|---|---|
| 規約のアンカー数 | 10 | 11 |
| 提案カードの見出し数 | 14 | 16 |
| 禁止語の数 | 15 | 15 |
| 数値必須の項目 | `[5, 6, 10]` | `[5, 6, 10]` |
| `issuer_cautions` の注意 | 13 | 14 |
| L3 の検査数 | 12 | 13 |
| `check_spec.py` の規則数 | 8 | 8 |
| 試験 | 6 failed / 567 passed | 6 failed / 595 passed |
| `conventions_rev` | 占位 | `e7a51005`（変更前の版）→ 本 PR で規約が変わるため次の契約は本 PR の commit を引く |

`git --no-pager diff --numstat` の削除行数は `context/conventions.md` 0、
`docs/issuer-defects.md` 0、`tools/preflight_task.py` 1（`EXP_ONLY` の宣言のみ）。

## 5. 起票者の誤り

- `check_does_not_check`: 完了判定 E.1 が `make forbidden-check` の `permitted` を
  3 件と予期していた。実測は 1 件である。`permitted` は禁止領域に該当した経路だけを
  数えるため、`tasks/_templates/exp/prereg.md` と `docs/issuer-defects.md` は
  宣言しても現れない（`violations` は 0 で合格）。
- `asserted_without_measuring`: 「exp の雛形は `tasks/_templates/exp/`（spec.yaml、
  SPEC.md、prereg.md）」と確定事実に書いたが、`prereg.md` は存在しなかった。
  「足す」ではなく新設になった。
- `asserted_without_measuring`: 付録 D の表が「判定が三値のいずれか」であることを
  様式の定義として書きながら、FAIL 条件に空欄・三値以外を挙げていない。
  そのまま実装すると判定が空欄の行を素通りさせる。**空欄も FAIL にした**（逸脱 2）。

## 6. 逸脱

1. **未追跡 3 件を退避できなかった。** Task A.1 は「移動で退避し記録」を求めるが、
   `mv` を実行基盤が拒否した（`Irreversible Local Destruction`）。SPEC §6 に従い
   回避せず、その場に残して sha256 を記録し、commit に含めなかった。禁止領域の外に
   あり `forbidden-check` の `violations` は 0 である。
2. **P13 に「判定が三値でない」FAIL を足した。** SPEC Task C.1 が列挙した FAIL 条件は
   3 つだが、判定が空欄の行はどれにも当たらず素通りする。埋めないまま起票できる穴に
   なるため FAIL にした。付録 A・D が定める様式（判定は三値）の範囲内である。
3. **`docs/issuer-defects.md` の見出しを `###` から `##` へ下げ、型の一覧に 2 行足した。**
   既存の項はすべて `##` で、付録 F だけ `###` だった。付録の本文は変えていない。
   型の一覧の 2 行には「`result.yaml` の enum には未追加」と明記した（下記 UNKNOWN 参照）。
4. **`tests/test_check_proposal.py` の `CARD_COUNT` を 14 → 16 にし、試験を 1 つ改名した。**
   規約の件数に追随させるため。検査器の挙動は変えていない。

## 7. 想定外・UNKNOWN

- **既存の exp 契約 12 件はすべて P13 で FAIL になる**（実測）。いずれも完了済みで
  prereg に対称性の表が無いためである。関門の意図どおりだが、過去の契約を遡って
  再実行する場合は表を先に埋める必要がある。過去の prereg は書き換えていない。
- **`result.yaml` の `type` enum は 4 語のままである。** `asymmetric_comparison` と
  `rule_read_narrowly` は `docs/issuer-defects.md` の分類として追記したが、
  `tasks/_schema/result.schema.json` の enum には無い。本契約は schema を
  `allow_write` に宣言していないため触っていない。追加の可否は起票者の判断。
- `make task-validate`（全契約）は `SKIP inbox.d: spec.yaml なし` で 1 件 failed に
  なる。**変更前から同じ**であり、本契約は `tasks/inbox.d/` の構造を変えていない。
- `make lint` は変更前から落ちている（`black --check` 73 ファイル、`ruff` 3 件）。
  本契約が触った 4 ファイルは `ruff check` を通る。`black` は repo 全体が未整形の
  ため合わせていない。
- L3 の SKIP 一覧（**合格ではなく未実施**）: P2 `cuda_ext_loaded`、P3 `deterministic_flags`、
  P4 `prereg_committed`、P5 `frozen_source_hash`、P11 `gpu_free`、P12 `refs_resolved`、
  P13 `symmetry_table_complete`。P4・P5・P13 は `kind=impl` のため対象外、
  P2・P3・P11 は `plan.env.preflight` に記載なし、P12 は解決前提の参照なし。

## 8. 送出

| 項目 | 値 |
|---|---|
| 分岐 | `feat/symmetry-gate` |
| base | `phase0` |
| PR | PR_NUMBER_PLACEHOLDER |
| commit | d6b37c79（本文）、後続 commit で変更履歴の commit 欄を埋めた |
| `make task-report` | REPORT_PLACEHOLDER |

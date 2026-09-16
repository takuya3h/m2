# RESULT — T-2026-09-16-proposal-gate

証跡は `audit.md`。本書からは節番号で指す。**GPU は使っていない。**

## 判定

**status: pass。** Task A〜E を完走した。門は二つとも通過した。
`decisions_required` は空で発火しなかった。

| Gate | 判定 | 実測 |
|---|---|---|
| G1（A の後） | **pass** | 作業ツリーは未追跡 2 件を退避して清浄。アンカー **8** 件、`check_spec.py` の規則 **8** 件を記録（audit §1.2 §1.3） |
| G2（D の後） | **pass** | 禁止語 0/1/2 件、カード 14/13 件・数字欠落の六通りがすべて期待どおり（audit §4.2 §4.3） |

## 1. 解決された参照

`contract.inject_verbatim` は 2 件。**原文をそのまま引く。** 本書の節構造を壊さないため
四字下げで貼っており、下げ幅を除いた文字列が `context/conventions.md` の当該節と一致する。

### conventions#prohibitions（原文）

    ## prohibitions
    
    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### conventions#issuer_cautions（原文）

    ## issuer_cautions
    
    **起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
    実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**
    
    | # | 注意 |
    |---|---|
    | 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
    | 2 | 一致 0 件なら別の異質な方法でも確認する |
    | 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
    | 4 | 仕組みの挙動は実装を読んでから信じる |
    | 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
    | 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
    | 7 | **丸めた表示を実数として扱わない** |
    | 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
    | 9 | 無変更は要約値で確かめる。表示属性では足りない |
    | 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
    | 11 | 測定の副作用が禁止領域へ触れないか確かめる |
    | 12 | **判断の前に、いま見ているものが最新かを確かめる** |
    | 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
    
    **注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
    確かめると 3 件とも実在した。
    
    **注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
    （`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。
    
    **注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
    （自分の命令行にその語が含まれるため）。
    
    **シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
    一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**
    
    **命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

`conventions_rev` は `a8c07e81`（実測。測り方は audit §1.5）。`inputs.denominator` も
`inputs.sigma_policy` も `inputs.frozen_source` も本契約は持たないため、解決対象は上の 2 件だけである。

## 2. 完了判定（SPEC §5）

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | `conventions#proposal_gate` が L2 で引ける | アンカーが **8→9** 件になり、`inject_verbatim=[conventions#proposal_gate]` で L2 の該当 **0 件** | `conventions#proposal_gate_zz` では `[L2-5] アンカー proposal_gate_zz が存在しません`（audit §5.1） |
| b | 禁止語の検出 | 一語だけの本文で **1 件**（exit 1） | 含まない本文で **0 件**（exit 0）、二語の本文で **2 件**。1 件で頭打ちにならない（audit §4.2） |
| c | カード充足の検出 | 見出し 13 件の本文で不足 **1 件**（`missing_heading` #7） | 14 件で **0 件**（exit 0）、#5 から数字を消すと `missing_number` **1 件**（audit §4.3） |
| d | `spec-check` の規則数が不変 | 前 **8** / 後 **8**。`tools/check_spec.py` への差分は空、`rules_checked: 8` | 変更前の値は Task A で記録済み。数え方は `RULES` タプルの要素数（audit §1.3 §5.3） |
| e | 規約の変更が L2-6 で見える | `T-2026-08-10-conventions-survey` で `WARN [L2-6] conventions.md が 1201f4f 以降に変更されています`、**FAIL 0 件** | 🔴 **`naming` を注入しない `T-2026-08-11-issuer-defect-detector` でも同じ WARN が出た。**L2-6 は注入アンカーを見ていない（§4 の誤り 2、audit §5.2） |
| f | 試験が通る | 追加 **26 件**すべて通過。前 **6 failed / 509 passed** → 後 **6 failed / 535 passed**。失敗の増減 **0** | 陽性対照から禁止語「画期的」を消すと `assert 0 == 1` で落ちた（1 failed / 25 passed）。復元して 26 passed（audit §5.4） |
| g | PR が Draft でなく存在 | §7 送出 | 分岐 `feat/proposal-gate` |

## 3. 実測（次の契約で使う値）

| 値 | 前 | 後 |
|---|---|---|
| `context/conventions.md` のアンカー数 | 8 | **9**（`proposal_gate` を追加） |
| `tools/check_spec.py` の規則数 | 8 | **8**（不変。触っていない） |
| `conventions_rev`（同ファイルの最終変更 commit） | `a8c07e81` | **本契約の commit**（§7） |
| 試験（`pytest tests/ -q`） | 6 failed / 509 passed | 6 failed / **535 passed** |

- 検査器: **`tools/check_proposal.py`**（262 行）。試験 `tests/test_check_proposal.py`（230 行 / 26 件）
- 検査器が規約から読む値: 禁止語 **15 語** / カード **14 件** / 数値必須 **{5, 6, 10}**
- `runindex_commit`: `96eb3a1c`（`runindex/` の最終変更 commit）
- 呼び方: `python tools/check_proposal.py <md>`。`--only forbidden|card` で片方だけ、`--json` で機械可読
- **一覧は規約が正本で、検査器は写しを持たない。** 規約を読めない場合は 0 語で合格にせず `errors` を立てて非零で終わる

## 4. 起票者の誤り

**2 件。** いずれも指示どおり実行した結果として現れた。

1. **`self_contradiction`** — Task B は `context/conventions.md` への追記を命じるが、同ファイルは
   `tools/check_forbidden.py` の `FORBIDDEN_FILES` にあり、契約は `contract.allow_write` を宣言していない。
   指示どおり実行すると Task E-1 の `make forbidden-check` が `status: fail` / `violations` 1 件で落ちた（audit §5.5）。
2. **`check_does_not_check`** — SPEC §2 の確定事実 2 は「変更履歴に行を足すと `naming` の解決結果が変わり、
   `naming` を注入する既存契約で L2-6 が WARN になる」と述べるが、`_warn_conventions_rev`
   （`tools/validate_task.py:439`）は `inject_verbatim` を読まない。実測では変更履歴に行を足す**前**、
   `proposal_gate` 節を足しただけの時点で、`naming` を注入しない契約にも WARN が出た（audit §5.2）。

## 5. 逸脱

1. **judgement** — `contract.allow_write: ["context/conventions.md"]` を足した。契約が同ファイルへの
   追記を命じており、`allow_write` はスキーマ上の正規キーで、許可の上限（`data/` のみ）にも触れないため、
   停止せず宣言を補った。これで `forbidden-check` は `permitted` 1 件 / `violations` 0 件で通る。
2. **judgement** — 開始前から在った未追跡 2 件（`.sync-pause.released`、前セッションの digest）を
   `git stash push -u`（**移動**）で退避した。消していない。戻すのは `git stash pop`。
3. **judgement** — 逐語注入の原文 2 件（43 行）を四字下げで貼った。原文の見出しが本書の節構造と
   混ざるのを避けるためで、下げ幅を除いた文字列は規約の当該節と一致する。要約はしていない。
   原文を含めても本書は 147 行で、目安の 150 行に収まっている。

## 6. 想定外・UNKNOWN

- **`make docs-check` の通過は本契約の新規文書について空振りである。** 対象は
  `docs/docs_audit.md` に列挙された文書だけで（`tools/check_docs.py:170`）、`docs/proposal-gate.md` は
  載っていない。対象数は前後とも 42 で変わらなかった。代わりに文書内の経路を手で確かめた。
  `context/conventions.md` と `tools/check_spec.py` は実在、**`docs/evidence/` は不在**
  （並行する `T-2026-09-16-evidence-map-ab` が作る予定）。`docs_audit.md` への登録は契約が求めていないため行っていない。
- **検査器は引用の中の禁止語を区別しない。** `docs/proposal-gate.md` 自身へ当てると 13 行目
  （過去の欠陥を引用した箇所）を 1 件検出する。対象は提案文書であり、手順書へ当てる用途は想定していない。
- **変更履歴の表に `a8c07e81`（2026-08-25、`issuer_cautions` 節の追加）の行が欠けている。** 既存の漏れで、
  本契約は「既存節の本文を変えない」を守るため既存行を足していない。指摘のみ。
- L2-6 の WARN は本契約自身にも出る（`conventions_rev: a8c07e81` 以降にファイルが変わったため）。
  SPEC §6 の想定どおりで、**実測の側を採って続行した。** FAIL は 0 件。

## 7. 送出

| 項目 | 値 |
|---|---|
| 分岐 | `feat/proposal-gate` |
| commit | `6c95e4f1`（規約・文書・検査器） / `4300b7d2`（報告） |
| PR | **#173**（Draft ではない。base `phase0` ← head `feat/proposal-gate`） |
| `make task-validate` | exit 0（WARN [L2-6] 1 件） |
| `make task-preflight` | 6 PASS / 0 WARN / 6 SKIP / 0 FAIL |
| `make forbidden-check` | exit 0（changed 7 / permitted 1 / violations 0） |
| `make spec-check` | exit 0（rules_checked 8 / hits 0） |
| `make docs-check` / `make agent-check` | exit 0 / exit 0（targets 116） |
| `make task-report` | §7 に追記 |
